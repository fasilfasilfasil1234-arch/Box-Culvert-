"""
!! REFERENCE ONLY - SUPERSEDED. DO NOT PUT THIS FILE IN culvert_tool/ !!
=======================================================================
Old standalone Stage 2 (written before the run.py / model.py structure and
before the 16 Oct 2026 support decision). Kept because its OpenSTAAD
support calls were verified against Bentley's documentation and will be
reused in the new stage2_springs.py.

What changed since (see 01_Plan/Important_Changes_2026-10-16.md):
  - Geometry now comes from model.py (Stage 1), NOT read back from STAAD.
  - Only THREE supports: end (outer face), wall junction, intermediate.
  - The "FX fixed at one node" rule is replaced by the release pattern
    decided for the three supports (still to confirm).

-----------------------------------------------------------------------------
STAGE 2 - SOIL SPRINGS UNDER THE BASE SLAB (live in STAAD.Pro via OpenSTAAD)

OpenSTAAD functions used and where each one was checked
[R] = OpenSTAAD Reference Manual (Bentley, V8i SS4), Section 4.
[B] = Bentley STAAD.Pro Help, "Write an OpenSTAAD Program in Python".
[H] = Bentley STAAD.Pro Help, modelling / technical reference pages.
[M] = Bentley openstaad-mcp notes (live-tested against STAAD).
[S] = Secondary source only - CONFIRM in your local OpenSTAAD help.

  Geometry.GetNodeCount()                                  [R][B]
  Geometry.GetNodeList(NodeNumberArray)                    [R]
  Geometry.GetNodeCoordinates(NodeNo, X, Y, Z)             [R]
  Support.CreateSupportFixedBut(ReleaseArray, SpringArray) [R]  6 values each: FX FY FZ MX MY MZ
  Support.AssignSupportToNode(NodeNo, SupportNo)           [H]
  SaveModel(1)                                             [S][M]

  STAAD rules (Bentley STAAD.Pro Help):
  - A spring and a release cannot be in the same direction.   [H]
  - SPRING COMPRESSION joint-list KFY                          [H] TR.27.5
  - Compression-only cases: no LOAD COMBINATION; use REPEAT LOAD. [H] TR.27.5
  - Compression-only via OpenSTAAD: function exists but name not confirmed
    -> applied manually (One-way Spring tool or editor command).
"""

import sys

# =============================================================================
# INPUTS
# =============================================================================
SBC_KPA         = 150.0   # kPa   safe bearing capacity - example only
FOS             = 3.0     # -     factor of safety       - example only
BOWLES_FACTOR   = 40.0    # -     40 = Bowles
T_WALL          = 0.40    # m
STRIP_WIDTH     = 1.00    # m
FX_FIXED_NODE   = "middle"
BASE_Y_TOLERANCE = 1e-4
# =============================================================================

UNIT_METER = 4
UNIT_KILONEWTON = 5
LABEL_SUPPORT = 4


def flag(obj, *names):
    for n in names:
        obj._FlagAsMethod(n)


def api(obj, name, *args):
    try:
        return getattr(obj, name)(*args)
    except Exception as exc:
        print(f"\nOpenSTAAD call failed: {name}\n  Error: {exc}")
        raise


def _automation():
    from comtypes import automation
    return automation


def make_variant_vt_ref(obj, var_type):
    import ctypes
    automation = _automation()
    var = automation.VARIANT()
    var._.c_void_p = ctypes.addressof(obj)
    var.vt = var_type | automation.VT_BYREF
    return var


def safe_array(ctype, values):
    return _automation()._midlSAFEARRAY(ctype).create(list(values))


def read_array(variant, safearr, size):
    for getter in (lambda: variant.value, lambda: list(variant), lambda: safearr.unpack()):
        try:
            vals = list(getter())
            if len(vals) == size:
                return vals
        except Exception:
            continue
    raise RuntimeError("Could not read the array returned by OpenSTAAD.")


def double_array_in(values):
    import ctypes
    automation = _automation()
    sa = safe_array(ctypes.c_double, values)
    return make_variant_vt_ref(sa, automation.VT_ARRAY | automation.VT_R8), sa


def connect():
    from comtypes import client
    return client.GetActiveObject("StaadPro.OpenSTAAD")


def read_nodes(staad):
    import ctypes
    automation = _automation()
    geo = staad.Geometry
    flag(geo, "GetNodeCount", "GetNodeList", "GetNodeCoordinates")
    n = api(geo, "GetNodeCount")
    sa = safe_array(ctypes.c_long, [0] * n)
    var = make_variant_vt_ref(sa, automation.VT_ARRAY | automation.VT_I4)
    api(geo, "GetNodeList", var)
    node_nos = [int(v) for v in read_array(var, sa, n)]
    coords = {}
    for nd in node_nos:
        x, y, z = ctypes.c_double(), ctypes.c_double(), ctypes.c_double()
        vx = make_variant_vt_ref(x, automation.VT_R8)
        vy = make_variant_vt_ref(y, automation.VT_R8)
        vz = make_variant_vt_ref(z, automation.VT_R8)
        geo.GetNodeCoordinates(nd, vx, vy, vz)
        coords[nd] = (x.value, y.value, z.value)
    return coords


def find_base_nodes(coords):
    y_min = min(c[1] for c in coords.values())
    base = [(nd, c[0]) for nd, c in coords.items() if abs(c[1] - y_min) <= BASE_Y_TOLERANCE]
    base.sort(key=lambda t: t[1])
    return base, y_min


def compute_springs(base):
    ks = BOWLES_FACTOR * FOS * SBC_KPA
    xs = [x for _, x in base]
    rows = []
    for i, (nd, x) in enumerate(base):
        left = (x - xs[i - 1]) / 2 if i > 0 else T_WALL / 2
        right = (xs[i + 1] - x) / 2 if i < len(base) - 1 else T_WALL / 2
        trib = left + right
        rows.append({"node": nd, "x": x, "trib": trib, "K": ks * trib * STRIP_WIDTH,
                     "end": i in (0, len(base) - 1)})
    return ks, rows


def pick_fx_node(rows):
    if FX_FIXED_NODE != "middle":
        return FX_FIXED_NODE
    mid = (rows[0]["x"] + rows[-1]["x"]) / 2
    return min(rows, key=lambda r: abs(r["x"] - mid))["node"]


def assign_springs(staad, rows, fx_node):
    flag(staad, "SetInputUnits", "UpdateStructure", "SaveModel")
    api(staad, "SetInputUnits", UNIT_METER, UNIT_KILONEWTON)
    sup = staad.Support
    flag(sup, "CreateSupportFixedBut", "AssignSupportToNode")
    # Release flags  FX  FY  FZ  MX  MY  MZ   (1 = released)
    release_free_fx = [1.0, 0.0, 0.0, 0.0, 0.0, 1.0]
    release_fixed_fx = [0.0, 0.0, 0.0, 0.0, 0.0, 1.0]
    cache = {}
    for r in rows:
        fx_fixed = (r["node"] == fx_node)
        key = (round(r["K"], 3), fx_fixed)
        if key not in cache:
            rel, _k1 = double_array_in(release_fixed_fx if fx_fixed else release_free_fx)
            spr, _k2 = double_array_in([0.0, r["K"], 0.0, 0.0, 0.0, 0.0])
            cache[key] = api(sup, "CreateSupportFixedBut", rel, spr)
        api(sup, "AssignSupportToNode", r["node"], cache[key])
    api(staad, "UpdateStructure")
    api(staad, "SaveModel", 1)
    return cache


def main():
    staad = connect()
    coords = read_nodes(staad)
    base, y_min = find_base_nodes(coords)
    ks, rows = compute_springs(base)
    fx_node = pick_fx_node(rows)
    if input("Assign springs now? [y/N]: ").strip().lower() != "y":
        sys.exit(0)
    assign_springs(staad, rows, fx_node)
    for r in rows:
        print(r)


if __name__ == "__main__":
    main()
