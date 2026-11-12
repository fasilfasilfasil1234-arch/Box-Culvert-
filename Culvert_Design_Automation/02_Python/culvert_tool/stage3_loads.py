"""
STAGE 3 - PRIMARY LOAD CASES (version 1, no vehicles yet)
=========================================================

Runs from run.py after Stages 1 and 2. Geometry comes from model.py.
Models into the open STAAD file; never saves.

Load cases (method from the twin-cell Excel / STAAD; decisions of 16 Oct)
------------------------------------------------------------------------
  1 DEAD LOAD                 SELFWEIGHT Y -1 (density 25 from Stage 1)
  2 SIDL                      max(case a, case b) as UNI GY on the top slab
                                a: sum(h x gamma) x 1.0
                                b: A_cb x gamma_conc + sum(h x gamma) x (1 - b_cb)
  3 EARTH PRESSURE            at-rest K0 = 1 - sin(phi), TRAP GX on both walls,
                              base centreline to top centreline, pushing inward
                                p_top = K0 x gamma x (fill + t_top/2)
                                p_bot = K0 x gamma x (fill + t_top/2 + H)
  4 LL SURCHARGE BOTH SIDES   p = K0 x gamma x 1.2, UNI GX on both walls
  5 LL SURCHARGE ONE SIDE     same, left wall only (as the twin-cell file)
  6 BRAKING                   joint load FX at the top-left corner (as twin-cell)
                                F = max over vehicles of 0.2 x q x dL x (3 - fill)/3
                                (0 if fill > 3 m)  - twin-cell Excel cl 8.6
  7 WATER INSIDE CELL         triangular, outward on both inner wall faces:
                              0 at y = t_bot/2 + Hw, gamma_w x Hw at y = t_bot/2;
                              optional UNI GY gamma_w x Hw on the base between
                              inner faces (WATER_ON_BASE)

Sign convention: global axes. Left wall inward = +GX, right wall inward = -GX.
Gravity loads are -GY.

OpenSTAAD functions used
------------------------
[L] = Bentley OpenSTAAD Help installed with your STAAD.Pro CE 22.00.00.15

  Load.CreateNewPrimaryLoadEx(Title, LoadType) -> load no.   [L]  22 = None (as twin-cell)
  Load.SetLoadActive(LoadNo)                                  [L]
  Load.AddSelfWeightInXYZ(Direction, Factor)                  [L]  direction 4/5/6 = X/Y/Z
  Load.AddMemberUniformForce(Beam, Dir, W, d1, d2, d3)        [L]  dir 4 = GX, 5 = GY
  Load.AddMemberTrapezoidal(Beam, Dir, W1, W2, d1, d2)        [L]
  Load.AddNodalLoad(Node, FX, FY, FZ, MX, MY, MZ)             [L]
  Load.GetUDLLoadCount(Beam) / GetTrapLoadCount(Beam)         [L]  read-back
  Load.GetNodalLoadCount(Node)                                [L]  read-back
  Load.GetPrimaryLoadCaseCount()                              [L][T]

Members (Stage 1, 17 Oct): 1 top slab, 2 left wall, 3 right wall (walls run
bottom -> top), 4.. base. Walls are single members, so earth pressure is one
TRAP per wall and the water load is one partial TRAP per wall starting
t_bot/2 above the base centreline.
"""

import math

import staad_api as sa

TITLE = "Stage 3 - Load cases 1 to 7"

# =============================================================================
# INPUTS  (edit only this block)
# =============================================================================
# --- Soil (twin-cell Excel cl 6c) ---
GAMMA_SOIL        = 20.0   # kN/m3  unit weight of fill
PHI_DEG           = 30.0   # deg    angle of internal friction
SURCHARGE_HEIGHT  = 1.2    # m      equivalent fill for LL surcharge (IRC:6 cl 214.1)

# --- Layers above the top slab, top to bottom: (name, thickness m, density kN/m3) ---
# Twin-cell Excel: total fill 0.284 m = 0.1095 wearing coat @25 + rest soil @20.
# The total thickness is also the fill depth used for earth pressure.
SIDL_LAYERS = [
    ("Wearing coat (future overlay)", 0.1095, 25.0),
    ("Earth fill / road crust",       0.1745, 20.0),
]

# --- Crash barrier, SIDL case (b) (twin-cell Excel J29, J110) ---
CRASH_BARRIER_WIDTH = 0.50   # m   width b inside the 1 m strip
CRASH_BARRIER_AREA  = 0.309  # m2  cross-section area (IRC:5 Fig 2)

# --- Braking (twin-cell Excel cl 8.6) ---
FILL_FOR_LL = 0.065          # m   fill used for live-load dispersion (Excel "FILL")
# (vehicle, load intensity q BEFORE impact kN/m2, dispersed length dL m)
# PLACEHOLDERS = twin-cell Excel values. Replace with this culvert's vehicle
# results until the vehicle module produces them.
BRAKING_VEHICLES = [
    ("70R tracked (70T)",   24.971380812752727, 5.400),
    ("70R bogie (40T)",     31.234208121314886, 2.751),
    ("70R wheeled",         35.86384296615022,  2.186),
    ("Class A - 1 lane",    28.879768961848303, 2.160),
    ("Class A - 2 lane",    22.358640437758645, 2.680),
]

# --- Water inside the cell (new case) ---
GAMMA_WATER   = 10.0         # kN/m3
WATER_DEPTH   = None         # m above top of base slab; None = full clear height D
WATER_ON_BASE = True         # True = also gamma_w x Hw downward on the base (TO CONFIRM)

LOAD_TYPE_NONE = 22          # OpenSTAAD load type "None", as the twin-cell file [L]
# =============================================================================

DIR_GX, DIR_GY = 4, 5        # AddMember... direction codes [L]
SW_Y = 5                     # AddSelfWeightInXYZ direction code for Y [L]


def check_inputs(model):
    errors = []
    for name, val in {"GAMMA_SOIL": GAMMA_SOIL, "PHI_DEG": PHI_DEG,
                      "SURCHARGE_HEIGHT": SURCHARGE_HEIGHT, "GAMMA_WATER": GAMMA_WATER,
                      "CRASH_BARRIER_AREA": CRASH_BARRIER_AREA}.items():
        if not isinstance(val, (int, float)) or val <= 0:
            errors.append(f"{name} must be a positive number (got {val!r})")
    if not 0 <= CRASH_BARRIER_WIDTH < model.strip_width:
        errors.append("CRASH_BARRIER_WIDTH must be between 0 and the strip width")
    if not SIDL_LAYERS or any(h < 0 or g <= 0 for _, h, g in SIDL_LAYERS):
        errors.append("SIDL_LAYERS: each layer needs thickness >= 0 and density > 0")
    if not BRAKING_VEHICLES:
        errors.append("BRAKING_VEHICLES must list at least one vehicle")
    hw = model.clear_height if WATER_DEPTH is None else WATER_DEPTH
    if not 0 < hw <= model.clear_height + 1e-9:
        errors.append(f"WATER_DEPTH must be > 0 and <= clear height {model.clear_height} m")
    if errors:
        raise sa.StopRun("INPUT ERRORS in stage3_loads.py:\n  - " + "\n  - ".join(errors))


# -----------------------------------------------------------------------------
# Calculation (pure Python - also used by the load-calc Excel builder)
# -----------------------------------------------------------------------------
def compute_values(model):
    """All load intensities. Keys are used by the Excel builder too."""
    v = {}
    p_layers = sum(h * g for _, h, g in SIDL_LAYERS)
    fill = sum(h for _, h, _g in SIDL_LAYERS)
    v["p_layers"] = p_layers
    v["fill_total"] = fill
    v["w_sidl_a"] = p_layers * 1.0
    v["w_cb"] = CRASH_BARRIER_AREA * model.density
    v["w_sidl_b"] = v["w_cb"] + p_layers * (1.0 - CRASH_BARRIER_WIDTH)
    v["w_sidl"] = max(v["w_sidl_a"], v["w_sidl_b"])
    v["sidl_governs"] = "a" if v["w_sidl_a"] >= v["w_sidl_b"] else "b"

    v["K0"] = 1.0 - math.sin(math.radians(PHI_DEG))
    v["z_top"] = fill + model.t_top / 2
    v["z_bot"] = v["z_top"] + model.H
    v["p_ep_top"] = v["K0"] * GAMMA_SOIL * v["z_top"]
    v["p_ep_bot"] = v["K0"] * GAMMA_SOIL * v["z_bot"]
    v["p_ls"] = v["K0"] * GAMMA_SOIL * SURCHARGE_HEIGHT

    brk = []
    for name, q, dL in BRAKING_VEHICLES:
        f = 0.0 if FILL_FOR_LL > 3 else 0.2 * q * dL * (3 - FILL_FOR_LL) / 3
        brk.append((name, q, dL, f))
    v["braking_list"] = brk
    v["F_brake"] = max(f for *_x, f in brk)

    hw = model.clear_height if WATER_DEPTH is None else WATER_DEPTH
    v["Hw"] = hw
    v["y_water_base"] = model.t_bot / 2
    v["y_water_top"] = model.t_bot / 2 + hw
    v["p_water"] = GAMMA_WATER * hw
    return v


def _ep(model, v, y):
    """Earth pressure at height y above the base centreline (linear, kN/m)."""
    return v["p_ep_bot"] + (v["p_ep_top"] - v["p_ep_bot"]) * y / model.H


def _water(v, y):
    return max(0.0, GAMMA_WATER * (v["y_water_top"] - y))


def build_cases(model, v):
    """
    [{no, title, items}] where items are:
      ("self",)                              selfweight Y -1
      ("udl",  beam, dir, w, d1, d2)         d1 = d2 = 0 -> full length
      ("trap", beam, dir, w1, w2, d1, d2)
      ("node", node, fx, fy)
    """
    top = model.members_in("top")
    walls = {"left_wall": +1.0, "right_wall": -1.0}       # inward sign in GX
    base = model.members_in("base")

    def wall_ends(m):
        (_, ya), (_, yb) = model.member_ends(m)
        return ya, yb

    c2 = [("udl", m.no, DIR_GY, -v["w_sidl"], 0.0, 0.0) for m in top]

    c3 = []
    for zone, s in walls.items():
        for m in model.members_in(zone):
            ya, yb = wall_ends(m)
            c3.append(("trap", m.no, DIR_GX, s * _ep(model, v, ya), s * _ep(model, v, yb),
                       0.0, yb - ya))

    c4 = [("udl", m.no, DIR_GX, s * v["p_ls"], 0.0, 0.0)
          for zone, s in walls.items() for m in model.members_in(zone)]
    c5 = [("udl", m.no, DIR_GX, +v["p_ls"], 0.0, 0.0) for m in model.members_in("left_wall")]

    c6 = [("node", model.corner_nodes["top_left"], v["F_brake"], 0.0)]

    c7 = []
    y0, y1 = v["y_water_base"], v["y_water_top"]
    for zone, s in walls.items():
        for m in model.members_in(zone):
            ya, yb = wall_ends(m)
            lo, hi = max(ya, y0), min(yb, y1)
            if hi - lo <= 1e-9:
                continue
            # outward = -inward sign
            c7.append(("trap", m.no, DIR_GX, -s * _water(v, lo), -s * _water(v, hi),
                       lo - ya, hi - ya))
    if WATER_ON_BASE:
        x0 = model.t_wall / 2                             # inner face, left  (node 5)
        x1 = model.L - model.t_wall / 2                   # inner face, right (node 6)
        for m in base:
            (xa, _), (xb, _) = model.member_ends(m)
            lo, hi = max(xa, x0), min(xb, x1)
            if hi - lo <= 1e-9:
                continue
            full = abs(lo - xa) < 1e-9 and abs(hi - xb) < 1e-9
            c7.append(("udl", m.no, DIR_GY, -v["p_water"],
                       0.0 if full else lo - xa, 0.0 if full else hi - xa))

    return [
        {"no": 1, "title": "DEAD LOAD", "items": [("self",)]},
        {"no": 2, "title": f"SIDL (MAX OF CASE A AND B - CASE {v['sidl_governs'].upper()})",
         "items": c2},
        {"no": 3, "title": "EARTH PRESSURE", "items": c3},
        {"no": 4, "title": "LIVE LOAD SURCHARGE BOTH SIDES", "items": c4},
        {"no": 5, "title": "LIVE LOAD SURCHARGE ON ONE SIDE", "items": c5},
        {"no": 6, "title": "BRAKING LOAD", "items": c6},
        {"no": 7, "title": "WATER INSIDE CELL", "items": c7},
    ]


# -----------------------------------------------------------------------------
# STAAD steps
# -----------------------------------------------------------------------------
def create_cases(staad, cases):
    load = staad.Load
    sa.flag(load, "CreateNewPrimaryLoadEx", "SetLoadActive", "AddSelfWeightInXYZ",
            "AddMemberUniformForce", "AddMemberTrapezoidal", "AddNodalLoad",
            "GetPrimaryLoadCaseCount")
    if int(sa.call(load, "GetPrimaryLoadCaseCount") or 0):              # [L][T]
        raise sa.StopRun("The open model already has load cases. Start from a blank "
                         "file and run all stages again.")

    def r6(x):
        return round(float(x), 6) + 0.0          # no 0.4999999 / -0.0 in the editor

    made = {}
    for c in cases:
        print(f"  creating LOAD {c['no']} {c['title']} ({len(c['items'])} items) ...", flush=True)
        no = sa.call(load, "CreateNewPrimaryLoadEx", c["title"], LOAD_TYPE_NONE)  # [L]
        made[c["no"]] = int(no)
        sa.call(load, "SetLoadActive", int(no))                         # [L]
        for it in c["items"]:
            kind = it[0]
            if kind == "self":
                sa.call_ok(load, "AddSelfWeightInXYZ", SW_Y, -1.0)       # [L]
            elif kind == "udl":
                _, beam, d, w, d1, d2 = it
                sa.call_ok(load, "AddMemberUniformForce", beam, d, r6(w),
                           r6(d1), r6(d2), 0.0)                    # [L]
            elif kind == "trap":
                _, beam, d, w1, w2, d1, d2 = it
                sa.call_ok(load, "AddMemberTrapezoidal", beam, d, r6(w1), r6(w2),
                           r6(d1), r6(d2))                         # [L]
            elif kind == "node":
                _, node, fx, fy = it
                sa.call_ok(load, "AddNodalLoad", node, r6(fx), r6(fy),
                           0.0, 0.0, 0.0, 0.0)                           # [L]
    return made


def read_back(staad, cases, made):
    """Count member/joint loads per case and compare with what was sent."""
    load = staad.Load
    sa.flag(load, "SetLoadActive", "GetUDLLoadCount", "GetTrapLoadCount",
            "GetNodalLoadCount")
    out = []
    for c in cases:
        exp = {}
        for it in c["items"]:
            if it[0] in ("udl", "trap", "node"):
                exp[(it[0], it[1])] = exp.get((it[0], it[1]), 0) + 1
        if not exp:
            out.append((c["no"], made[c["no"]], None, "selfweight - check in STAAD"))
            continue
        sa.call(load, "SetLoadActive", made[c["no"]])                   # [L]
        got_ok = True
        for (kind, obj), n in exp.items():
            fn = {"udl": "GetUDLLoadCount", "trap": "GetTrapLoadCount",
                  "node": "GetNodalLoadCount"}[kind]
            got = int(sa.call(load, fn, obj) or 0)                       # [L]
            if got != n:
                got_ok = False
        out.append((c["no"], made[c["no"]], got_ok, f"{sum(exp.values())} load items"))
    return out


# -----------------------------------------------------------------------------
# Report
# -----------------------------------------------------------------------------
def print_summary(model, v, cases, made, check):
    line = "-" * 64
    print(line)
    print("STAGE 3 SUMMARY - compare with STAAD (and with the load-calc Excel)")
    print(line)
    print(f"SIDL layers p = sum(h x gamma) = {v['p_layers']:.4f} kN/m2  "
          f"(fill depth {v['fill_total']:.4f} m)")
    print(f"  case (a) full strip       w_a = {v['w_sidl_a']:.3f} kN/m")
    print(f"  case (b) crash barrier    w_b = {v['w_cb']:.3f} + {v['p_layers']:.4f} x "
          f"(1 - {CRASH_BARRIER_WIDTH:g}) = {v['w_sidl_b']:.3f} kN/m")
    print(f"  -> STAAD gets case ({v['sidl_governs']}) = {v['w_sidl']:.3f} kN/m on the top slab")
    print(f"Earth pressure  K0 = {v['K0']:.4f}  top {v['p_ep_top']:.3f}  "
          f"bottom {v['p_ep_bot']:.3f} kN/m  (depths {v['z_top']:.3f} / {v['z_bot']:.3f} m)")
    print(f"LL surcharge    p = {v['p_ls']:.3f} kN/m")
    print("Braking         F = 0.2 x q x dL x (3 - fill)/3:")
    for name, q, dL, f in v["braking_list"]:
        print(f"    {name:<20} q {q:7.3f}  dL {dL:6.3f}  -> {f:7.3f} kN/m")
    print(f"  -> {v['F_brake']:.3f} kN at node {model.corner_nodes['top_left']} (top-left), +FX")
    print(f"Water           Hw = {v['Hw']:.3f} m, base pressure {v['p_water']:.3f} kN/m, "
          f"wall: 0 at y={v['y_water_top']:.3f} -> {v['p_water']:.3f} at y={v['y_water_base']:.3f}"
          f"{'  + on base' if WATER_ON_BASE else ''}")

    print("\nLoad cases in STAAD (read-back):")
    for no, got_no, ok, txt in check:
        flag = "check" if ok is None else ("OK" if ok else "MISMATCH")
        renum = "" if no == got_no else f"  (STAAD numbered it {got_no})"
        title = next(c["title"] for c in cases if c["no"] == no)
        print(f"  LOAD {no}  {title:<46} {txt:<28} {flag}{renum}")

    print("\nCHECK IN STAAD (Loading page, load value labels on):")
    print("  1 SELFWEIGHT Y -1 | 2 UNI GY on top slab | 3 TRAP GX both walls, inward")
    print("  4 UNI GX both walls | 5 UNI GX left wall | 6 JOINT LOAD FX top-left")
    print("  7 TRAP GX outward from the top of the base slab"
          f"{' + UNI GY on the base' if WATER_ON_BASE else ''}")
    print("  No combinations yet (Stage 4). Model NOT saved - save in STAAD.")
    print(line)


# -----------------------------------------------------------------------------
# Entry point called by run.py
# -----------------------------------------------------------------------------
def run(staad, model):
    if not model.members:
        raise sa.StopRun("No geometry in the model. Stage 1 must run first "
                         "(run all stages from run.py in one go).")
    check_inputs(model)
    v = compute_values(model)
    cases = build_cases(model, v)

    sa.set_units_m_kn(staad)
    made = create_cases(staad, cases)
    # No UpdateStructure / view refresh here: on the 16 Oct run STAAD stopped
    # responding at UpdateStructure right after the loads were added.
    print("  reading the loads back ...", flush=True)
    check = read_back(staad, cases, made)

    model.load_cases = {c["no"]: c["title"] for c in cases}
    model.load_values = {k: val for k, val in v.items() if isinstance(val, (int, float))}
    print_summary(model, v, cases, made, check)
