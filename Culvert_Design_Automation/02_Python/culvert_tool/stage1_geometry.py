"""
STAGE 1 - BOX CULVERT GEOMETRY, SECTIONS AND MATERIAL
=====================================================

Runs from run.py. Models into the STAAD file YOU have open - it does not
create or save any file.

Version 17 Oct 2026 (replaces the 16 Oct version)
-------------------------------------------------
Centreline frame, 1 m strip. The base slab runs wall centreline to wall
centreline (it does NOT extend past the walls). Only the base slab is split.

    2 ------------- member 1 (top) -------------- 3
    |                                             |
 member 2 (left wall)                    member 3 (right wall)
    |                                             |
    1 --5-- 7 -- 8 -- ... -- (6+N) --6-- 4      base members 4, 5, ...
    x=0  tw/2   intermediate nodes    L-tw/2  L

  Nodes 1-4 : corners (wall centreline x slab centreline)     -> "end"
  Nodes 5, 6: base slab at the INNER FACE of each wall (tw/2) -> "junction"
  Nodes 7.. : N intermediate nodes, equally spaced across the clear span
              between nodes 5 and 6, numbered left to right   -> "intermediate"
  Example: B = 5.0, tw = 0.4, N = 9 -> L = 5.4
           x = 0, 0.2, 0.7, 1.2 ... 4.7, 5.2, 5.4

  The outer half of each wall (tw/2 beyond the centreline) is not modelled;
  Stage 2 adds it to the END node's spring, so the springs cover the full
  overall width B + 2 tw.

Member directions: top slab and base LEFT -> RIGHT, walls BOTTOM -> TOP.
Origin (0,0) = bottom-left corner (left wall centreline, base centreline).

Concrete is defined as a user material (E, Poisson, DENSITY 25 ...),
exactly like the twin-cell file's DEFINE MATERIAL block, then assigned to all
members AFTER the sections. Density is read back and checked.

OpenSTAAD functions used here (connection/units/view: see staad_api.py)
-----------------------------------------------------------------------
[L] = Bentley OpenSTAAD Help installed with your STAAD.Pro CE 22.00.00.15
[T] = tested live on your PC (16-17 Oct 2026 runs)

  Geometry.CreateNode(nNodeNo, fCoordX, fCoordY, fCoordZ)                 [L][T]
  Geometry.CreateBeam(nBeamNo, nNodeA, nNodeB)                            [L][T]
  Geometry.GetNodeCount() / GetMemberCount()                              [L][T]
  Property.CreatePrismaticRectangleProperty(fYD, fZD)  -> property ref    [L][T]
  Property.AssignBeamProperty(nBeamNo, nProperty)                         [L][T]
  Property.CreateIsotropicMaterialProperties(Name, E, Poisson, G,
                                             Density, Alpha, CrDamp)      [L][T]
  Property.AssignMaterialToMember(MaterialName, MemberNo)                 [L][T]
  Property.GetMaterialProperty(Name, E, Poisson, Density, Alpha, Damp)    [L][T]
  Property.GetBeamMaterialName(nBeamNo)                                   [L][T]

Notes from Bentley's live testing [M]
-------------------------------------
N1. CreateNode uses the current INPUT units -> staad_api.set_units_m_kn().
N2. AssignBeamProperty silently drops a member's material, so material is
    assigned AFTER all section assignments.
N3. Some calls report failure even when they worked, so success is checked
    by counting / reading back, not by return values.
"""

import staad_api as sa
from model import Member

TITLE = "Stage 1 - Geometry, sections and material"

# =============================================================================
# INPUTS  (edit only this block)
# =============================================================================
CLEAR_SPAN_B     = 5.00   # m   inside width between wall faces
CLEAR_HEIGHT_D   = 4.00   # m   inside height between slab faces
T_TOP            = 0.35   # m   top slab thickness
T_WALL           = 0.40   # m   side wall thickness     (both walls equal)
T_BOT            = 0.40   # m   base slab thickness
STRIP_WIDTH      = 1.00   # m   width into the page (1 m strip)

N_BASE_INTERMEDIATE = 9   # nos  intermediate spring nodes between the two wall faces

# Concrete - set the same way as the twin-cell STAAD (DEFINE MATERIAL)
MATERIAL_NAME    = "CONCRETE"
E_CONCRETE       = 3.1e7  # kN/m2  (M30, IRC:112 Table 6.5 - twin-cell Excel J36)
POISSON          = 0.2
DENSITY          = 25.0   # kN/m3  (decided 16 Oct)
ALPHA            = 1.2e-5 # /degC  (IRC:112 / twin-cell Excel J38; the twin-cell STAAD had 5e-6)
DAMPING          = 0.05

SEISMIC_FLAG_SPAN = 10.0  # m   spans above this are flagged (seismic not applied)
# =============================================================================


# -----------------------------------------------------------------------------
# Input check
# -----------------------------------------------------------------------------
def check_inputs():
    errors = []
    for name, val in {"CLEAR_SPAN_B": CLEAR_SPAN_B, "CLEAR_HEIGHT_D": CLEAR_HEIGHT_D,
                      "T_TOP": T_TOP, "T_WALL": T_WALL, "T_BOT": T_BOT,
                      "STRIP_WIDTH": STRIP_WIDTH, "E_CONCRETE": E_CONCRETE,
                      "DENSITY": DENSITY}.items():
        if not isinstance(val, (int, float)) or val <= 0:
            errors.append(f"{name} must be a positive number (got {val!r})")
    if not isinstance(N_BASE_INTERMEDIATE, int) or N_BASE_INTERMEDIATE < 1:
        errors.append(f"N_BASE_INTERMEDIATE must be a whole number >= 1 "
                      f"(got {N_BASE_INTERMEDIATE!r})")
    if not 0 <= POISSON < 0.5:
        errors.append(f"POISSON must be between 0 and 0.5 (got {POISSON!r})")
    if errors:
        raise sa.StopRun("INPUT ERRORS in stage1_geometry.py:\n  - " + "\n  - ".join(errors))


# -----------------------------------------------------------------------------
# Geometry (pure Python - no STAAD needed, easy to hand-check)
# -----------------------------------------------------------------------------
def build_geometry():
    """
    Returns a dict with nodes {no: (x, y)}, members [Member], base_roles,
    corner_nodes, L, H, overall_width. Numbering is fixed (see the docstring).
    """
    L = CLEAR_SPAN_B + T_WALL                      # centre-to-centre of walls
    H = CLEAR_HEIGHT_D + T_TOP / 2 + T_BOT / 2     # centre of base to centre of top
    xf_left = T_WALL / 2                           # inner face of the left wall
    xf_right = L - T_WALL / 2                      # inner face of the right wall
    n = N_BASE_INTERMEDIATE
    s = CLEAR_SPAN_B / (n + 1)                     # intermediate spacing

    def r(v):
        return round(v, 6)

    nodes = {
        1: (0.0, 0.0),            # bottom-left corner
        2: (0.0, r(H)),           # top-left corner
        3: (r(L), r(H)),          # top-right corner
        4: (r(L), 0.0),           # bottom-right corner
        5: (r(xf_left), 0.0),     # base at left inner wall face
        6: (r(xf_right), 0.0),    # base at right inner wall face
    }
    inter = list(range(7, 7 + n))
    for i, no in enumerate(inter, 1):
        nodes[no] = (r(xf_left + i * s), 0.0)

    members = [
        Member(1, 2, 3, "top"),            # top slab, left -> right
        Member(2, 1, 2, "left_wall"),      # bottom -> top
        Member(3, 4, 3, "right_wall"),     # bottom -> top
    ]
    chain = [1, 5] + inter + [6, 4]        # base slab, left -> right
    for a, b in zip(chain[:-1], chain[1:]):
        members.append(Member(len(members) + 1, a, b, "base"))

    base_roles = {1: "end", 4: "end", 5: "junction", 6: "junction"}
    base_roles.update({no: "intermediate" for no in inter})

    corners = {"bottom_left": 1, "top_left": 2, "top_right": 3, "bottom_right": 4}

    return {"nodes": nodes, "members": members, "base_roles": base_roles,
            "corner_nodes": corners, "L": L, "H": H,
            "overall_width": CLEAR_SPAN_B + 2 * T_WALL, "spacing": s}


def fill_model(model, g):
    """Copy inputs and pure-Python geometry into the shared model (no STAAD)."""
    model.clear_span, model.clear_height = CLEAR_SPAN_B, CLEAR_HEIGHT_D
    model.t_top, model.t_wall, model.t_bot = T_TOP, T_WALL, T_BOT
    model.strip_width = STRIP_WIDTH
    model.L, model.H, model.overall_width = g["L"], g["H"], g["overall_width"]
    model.nodes, model.members = g["nodes"], g["members"]
    model.base_roles, model.corner_nodes = g["base_roles"], g["corner_nodes"]
    model.material, model.density = MATERIAL_NAME, DENSITY


# -----------------------------------------------------------------------------
# STAAD steps
# -----------------------------------------------------------------------------
def create_geometry(staad, nodes, members):
    """Corners and the three single members first, then the split base slab."""
    geo = staad.Geometry
    sa.flag(geo, "CreateNode", "CreateBeam", "GetNodeCount", "GetMemberCount")

    for no in sorted(nodes):
        x, y = nodes[no]
        sa.call(geo, "CreateNode", no, float(x), float(y), 0.0)        # [L][T]
    for m in members:
        sa.call(geo, "CreateBeam", m.no, m.a, m.b)                      # [L][T]

    # N3: verify by counting, not by return values.
    return sa.call(geo, "GetNodeCount"), sa.call(geo, "GetMemberCount")  # [L][T]


def create_sections(staad, members):
    prop = staad.Property
    sa.flag(prop, "CreatePrismaticRectangleProperty", "AssignBeamProperty")

    # YD = depth in member local y (= thickness), ZD = width (1 m strip)
    refs = {}
    for label, t in (("top", T_TOP), ("wall", T_WALL), ("base", T_BOT)):
        refs[label] = sa.call(prop, "CreatePrismaticRectangleProperty",
                              float(t), float(STRIP_WIDTH))              # [L][T]

    def ref_for(zone):
        return refs["wall"] if "wall" in zone else refs[zone]

    for m in members:
        sa.call(prop, "AssignBeamProperty", m.no, ref_for(m.zone))      # [L][T]
    return refs


def create_and_assign_material(staad, members):
    """Define the concrete (density 25) and assign it AFTER the sections (N2)."""
    prop = staad.Property
    sa.flag(prop, "CreateIsotropicMaterialProperties", "AssignMaterialToMember",
            "GetMaterialProperty", "GetBeamMaterialName")

    G = E_CONCRETE / (2.0 * (1.0 + POISSON))
    sa.call(prop, "CreateIsotropicMaterialProperties", MATERIAL_NAME,
            float(E_CONCRETE), float(POISSON), float(G), float(DENSITY),
            float(ALPHA), float(DAMPING))                               # [L][T]

    for m in members:
        sa.call(prop, "AssignMaterialToMember", MATERIAL_NAME, m.no)    # [L][T]

    # Read back: the material on member 1 and its density.
    on_member = sa.call(prop, "GetBeamMaterialName", members[0].no)     # [L][T]
    outs = [sa.double_out() for _ in range(5)]                          # E, POI, DEN, ALP, DAMP
    sa.call(prop, "GetMaterialProperty", MATERIAL_NAME, *[v for v, _ in outs])  # [L][T]
    e_back, _, den_back, _, _ = (d.value for _, d in outs)
    return on_member, e_back, den_back


# -----------------------------------------------------------------------------
# Report
# -----------------------------------------------------------------------------
def print_summary(model, g, counts, mat_check):
    line = "-" * 64
    L, H = model.L, model.H
    print(line)
    print("STAGE 1 SUMMARY - compare with STAAD")
    print(line)
    print(f"Clear size      : {CLEAR_SPAN_B:g} m wide x {CLEAR_HEIGHT_D:g} m high")
    print(f"Thickness       : top {T_TOP:g} | walls {T_WALL:g} | base {T_BOT:g} m")
    print(f"Centreline L    : {L:.4f} m  (= B + tw, modelled base length)")
    print(f"Centreline H    : {H:.4f} m  (= D + t_top/2 + t_bot/2)")
    print(f"Overall width   : {model.overall_width:.4f} m  (= B + 2 tw, soil contact width)")
    if L > SEISMIC_FLAG_SPAN:
        print(f"!! FLAG: centreline span {L:.2f} m > {SEISMIC_FLAG_SPAN:g} m - "
              "seismic is NOT applied by this tool. Check it separately.")

    print("\nMembers:")
    for m in model.members:
        (xa, ya), (xb, yb) = model.member_ends(m)
        print(f"  member {m.no:>2}  {m.zone:<10}  node {m.a:>2} ({xa:.3f},{ya:.3f}) -> "
              f"node {m.b:>2} ({xb:.3f},{yb:.3f})  length {model.member_length(m):.4f}")

    print("\nBase slab nodes (x from the left wall centreline):")
    for n, x in model.base_nodes():
        print(f"  node {n:>3}  x = {x:7.4f}  {model.base_roles[n]}")
    print(f"  intermediate spacing = B/(N+1) = {CLEAR_SPAN_B:g}/{N_BASE_INTERMEDIATE + 1} "
          f"= {g['spacing']:.4f} m")

    got_nodes, got_mem = counts
    exp_nodes, exp_mem = len(model.nodes), len(model.members)
    print(f"\nNodes in STAAD  : {got_nodes}  (expected {exp_nodes})  "
          f"{'OK' if got_nodes == exp_nodes else 'MISMATCH'}")
    print(f"Members in STAAD: {got_mem}  (expected {exp_mem})  "
          f"{'OK' if got_mem == exp_mem else 'MISMATCH'}")

    r = model.section_refs
    print("\nSection property refs (YD x ZD, metres):")
    print(f"  top  -> ref {r['top']}  : {T_TOP:g} x {STRIP_WIDTH:g}")
    print(f"  wall -> ref {r['wall']}  : {T_WALL:g} x {STRIP_WIDTH:g}")
    print(f"  base -> ref {r['base']}  : {T_BOT:g} x {STRIP_WIDTH:g}")

    on_member, e_back, den_back = mat_check
    ok = abs(den_back - DENSITY) < 1e-3 and str(on_member).upper() == MATERIAL_NAME.upper()
    print(f"\nMaterial        : {on_member} on member 1 | E read back {e_back:.4g} kN/m2 | "
          f"density read back {den_back:.3f} kN/m3  {'OK' if ok else 'MISMATCH'}")
    if not ok:
        print("  !! Density/material read-back does not match the INPUTS. Check "
              "Materials in STAAD (Specification > Material) before going on.")

    print("\nCHECK IN STAAD:")
    print("  1. Geometry: one member each for top slab and walls; base split as listed.")
    print("  2. Base runs centreline to centreline (no overhang); nodes 5, 6 at the wall faces.")
    print(f"  3. Editor: DEFINE MATERIAL has {MATERIAL_NAME} with DENSITY {DENSITY:g}.")
    print("  (Model is NOT saved by the script - save in STAAD when happy.)")
    print(line)


# -----------------------------------------------------------------------------
# Entry point called by run.py
# -----------------------------------------------------------------------------
def run(staad, model):
    check_inputs()
    g = build_geometry()

    sa.require_empty_model(staad)        # stop before touching a non-empty model
    sa.set_units_m_kn(staad)             # N1
    counts = create_geometry(staad, g["nodes"], g["members"])
    refs = create_sections(staad, g["members"])
    mat_check = create_and_assign_material(staad, g["members"])
    sa.refresh_view(staad, sa.LABEL_NODE_NUMBER, sa.LABEL_MEMBER_NUMBER)

    # Hand results to later stages
    fill_model(model, g)
    model.section_refs = refs

    print_summary(model, g, counts, mat_check)
