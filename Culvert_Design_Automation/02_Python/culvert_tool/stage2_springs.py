"""
STAGE 2 - SOIL SPRINGS UNDER THE BASE SLAB (three supports only)
================================================================

Runs from run.py after Stage 1. Base nodes come from model.py (Stage 1),
NOT read back from STAAD. Models into the open STAAD file; never saves.

What it does
------------
1. ks = BOWLES_FACTOR x FOS x SBC  (Bowles; twin-cell Excel cl 7.2: 40 x 2.5 x 120)
2. Tributary length of each base node = half the gap on each side, and the
   END nodes (wall centrelines) also carry the unmodelled outer half wall:
     END node          : tw/2 + (tw/2)/2  = tw/2 + tw/4
     JUNCTION node     : (tw/2)/2 + s/2   = tw/4 + s/2     (inner wall face)
     INTERMEDIATE node : s                                  (s = B/(N+1))
   Check: tributary lengths add up to the overall width B + 2 tw.
   Example B 5.0, tw 0.4, N 9: 2x0.30 + 2x0.35 + 9x0.50 = 5.8 m
3. K = ks x tributary length x strip width (kN/m) per node.
4. Creates EXACTLY THREE supports in STAAD (end, junction, intermediate),
   assigns them, then reads every support back and compares.
5. Prints the one line you paste into the STAAD editor to make the springs
   compression-only (there is no OpenSTAAD function for it - see below).

Releases (INPUT below) - written like the STAAD "Fixed But" dialog
-------------------------------------------------------------------
List the RELEASED (ticked) directions. FY is always the spring.
  end           : MX MY MZ released  -> FX FZ fixed      FIXED BUT MX MY MZ KFY
  junction      : FX FZ MX MY MZ     -> only FY (spring) FIXED BUT FX FZ MX MY MZ KFY
  intermediate  : FX FZ MX MY MZ     -> only FY (spring) FIXED BUT FX FZ MX MY MZ KFY
(same as the twin-cell STAAD file).

The two OpenSTAAD functions use OPPOSITE codes (found on your 16 Oct run):
  CreateSupportFixedBut  release spec : 1 = released, 0 = fixed, FY -1 + KFY  [T]
  GetSupportInformation  release spec : 0 = released, 1 = fixed, FY -1        [L][T]
The help text for CreateSupportFixedBut states the Get convention; your run
proved creation uses the opposite, so this file converts for each one.

Compression-only springs
------------------------
Your OpenSTAAD help (OSSupportUI) has no compression-only function [L].
Paste the printed  SPRING COMPRESSION <nodes> KFY  line into the editor
straight after the SUPPORTS block  [H] TR.27.5. With compression-only
springs, combinations must be REPEAT LOAD cases (Stage 4).

OpenSTAAD functions used
------------------------
[L] = Bentley OpenSTAAD Help installed with your STAAD.Pro CE 22.00.00.15
[T] = tested live on your PC
[H] = STAAD.Pro Help (local), TR.27.5 Spring Tension/Compression Specification

  Support.CreateSupportFixedBut(varReleaseSpec, varSpringSpec) -> ref    [L][T]
  Support.AssignSupportToNode(nNodeNo, nSupportNo)                       [L][T]
  Support.GetSupportCount() / GetSupportNodes(NodeNos)                   [L][T]
  Support.GetSupportInformation(Node, ReleaseSpec, SpringSpec)           [L][T]
"""

import staad_api as sa

TITLE = "Stage 2 - Soil springs (3 supports, compression-only)"

# =============================================================================
# INPUTS  (edit only this block)
# =============================================================================
SBC_KPA        = 120.0   # kN/m2  safe bearing capacity (qa)   - twin-cell Excel J47
FOS            = 2.5     # -      factor of safety (IRC:78 cl 706.3.1.1) - twin-cell Excel J116
BOWLES_FACTOR  = 40.0    # -      ks = 40 x FOS x qa  (Bowles)

# RELEASED (ticked) directions per support. FY is always the spring - don't list it.
RELEASED = {
    "end":          ["MX", "MY", "MZ"],               # FX FZ fixed
    "junction":     ["FX", "FZ", "MX", "MY", "MZ"],   # only FY (spring)
    "intermediate": ["FX", "FZ", "MX", "MY", "MZ"],   # only FY (spring)
}
# =============================================================================

ROLES = ("end", "junction", "intermediate")
DIRS = ("FX", "FY", "FZ", "MX", "MY", "MZ")


def check_inputs():
    errors = []
    for name, val in {"SBC_KPA": SBC_KPA, "FOS": FOS, "BOWLES_FACTOR": BOWLES_FACTOR}.items():
        if not isinstance(val, (int, float)) or val <= 0:
            errors.append(f"{name} must be a positive number (got {val!r})")
    for role in ROLES:
        dirs = RELEASED.get(role)
        if dirs is None or any(d not in DIRS or d == "FY" for d in dirs):
            errors.append(f"RELEASED['{role}'] may only list FX FZ MX MY MZ (FY is the spring)")
    if errors:
        raise sa.StopRun("INPUT ERRORS in stage2_springs.py:\n  - " + "\n  - ".join(errors))


def create_spec(role):
    """Release spec for CreateSupportFixedBut: 1 released, 0 fixed, FY -1  [T]."""
    return [-1 if d == "FY" else (1 if d in RELEASED[role] else 0) for d in DIRS]


def readback_spec(role):
    """Expected GetSupportInformation spec: 0 released, 1 fixed, FY -1  [L][T]."""
    return [-1 if d == "FY" else (0 if d in RELEASED[role] else 1) for d in DIRS]


# -----------------------------------------------------------------------------
# Calculation (pure Python - also used by the load-calc Excel builder)
# -----------------------------------------------------------------------------
def compute_springs(model):
    """Returns ks and one row per base node: node, x, role, trib, K."""
    if not model.base_roles:
        raise sa.StopRun("No base-slab data in the model. Stage 1 must run first "
                         "(run all stages from run.py in one go).")
    ks = BOWLES_FACTOR * FOS * SBC_KPA
    base = model.base_nodes()
    xs = [x for _, x in base]
    rows = []
    for i, (n, x) in enumerate(base):
        left = (x - xs[i - 1]) / 2 if i > 0 else 0.0
        right = (xs[i + 1] - x) / 2 if i < len(base) - 1 else 0.0
        outer = model.t_wall / 2 if model.base_roles[n] == "end" else 0.0
        trib = left + right + outer
        rows.append({"node": n, "x": x, "role": model.base_roles[n], "trib": trib,
                     "K": ks * trib * model.strip_width})
    return ks, rows


def spring_per_role(rows):
    """{role: (trib, K, [nodes])}; stops if one role has two different K values."""
    out = {}
    for role in ROLES:
        rr = [r for r in rows if r["role"] == role]
        ks_ = {round(r["K"], 6) for r in rr}
        if len(ks_) != 1:
            raise sa.StopRun(f"'{role}' nodes have different stiffness {sorted(ks_)} - "
                             "three supports are not enough. Check Stage 1 spacing.")
        out[role] = (rr[0]["trib"], rr[0]["K"], [r["node"] for r in rr])
    return out


# -----------------------------------------------------------------------------
# STAAD steps
# -----------------------------------------------------------------------------
def assign_supports(staad, per_role):
    sup = staad.Support
    sa.flag(sup, "CreateSupportFixedBut", "AssignSupportToNode")
    refs = {}
    for role in ROLES:
        _, K, nodes = per_role[role]
        rel, keep1 = sa.double_array_in(create_spec(role))
        spr, keep2 = sa.double_array_in([0.0, K, 0.0, 0.0, 0.0, 0.0])
        refs[role] = sa.call(sup, "CreateSupportFixedBut", rel, spr)    # [L][T]
        del keep1, keep2
        for n in nodes:
            sa.call(sup, "AssignSupportToNode", n, refs[role])          # [L][T]
    return refs


def read_back(staad, per_role):
    """Read every support node back; returns (count, [(node, role, ok, text)], extra)."""
    sup = staad.Support
    sa.flag(sup, "GetSupportCount", "GetSupportNodes", "GetSupportInformation")
    count = int(sa.call(sup, "GetSupportCount"))                        # [L][T]
    var, keep = sa.long_array_out(count)
    sa.call(sup, "GetSupportNodes", var)                                # [L][T]
    in_staad = set(int(n) for n in sa.read_array(keep))

    results = []
    for role in ROLES:
        _, K, nodes = per_role[role]
        for n in nodes:
            if n not in in_staad:
                results.append((n, role, False, "no support found"))
                continue
            rv, rkeep = sa.long_array_out(6)
            kv, kkeep = sa.double_array_out(6)
            sa.call(sup, "GetSupportInformation", n, rv, kv)            # [L][T]
            rel = [int(v) for v in sa.read_array(rkeep)]
            spr = sa.read_array(kkeep)
            ok = rel == readback_spec(role) and abs(spr[1] - K) <= max(0.01, 1e-4 * K)
            released = [d for d, c in zip(DIRS, rel) if c == 0]
            results.append((n, role, ok, f"reads FIXED BUT {' '.join(released)} KFY {spr[1]:.2f}"))
    extra = in_staad - {n for r in ROLES for n in per_role[r][2]}
    return count, results, extra


# -----------------------------------------------------------------------------
# Report
# -----------------------------------------------------------------------------
def staad_text(role, K):
    """'FIXED BUT FX FZ MX MY MZ KFY 2933.82' (as the editor should read)."""
    released = [d for d in DIRS if d in RELEASED[role]]
    txt = "FIXED BUT " + " ".join(released) if released else "FIXED BUT"
    return f"{txt} KFY {K:.2f}"


def print_summary(model, ks, rows, per_role, refs, check):
    line = "-" * 64
    print(line)
    print("STAGE 2 SUMMARY - compare with STAAD")
    print(line)
    print(f"ks = {BOWLES_FACTOR:g} x {FOS:g} x {SBC_KPA:g} = {ks:.1f} kN/m2/m")
    print("\n node      x     role           trib (m)    K (kN/m)")
    for r in rows:
        print(f" {r['node']:>4}  {r['x']:7.4f}  {r['role']:<13}  {r['trib']:8.4f}  {r['K']:10.2f}")
    total = sum(r["trib"] for r in rows)
    ok = abs(total - model.overall_width) < 1e-6
    print(f"\nSum of tributary lengths = {total:.4f} m  vs overall width B + 2tw = "
          f"{model.overall_width:.4f} m  {'OK' if ok else 'MISMATCH'}")

    print("\nThe three supports (as they should read in the STAAD editor):")
    for role in ROLES:
        trib, K, nodes = per_role[role]
        print(f"  {role:<13} ref {refs[role]}: {sa.staad_list(nodes):<22} {staad_text(role, K)}")

    count, results, extra = check
    bad = [r for r in results if not r[2]]
    print(f"\nRead-back: {count} support nodes in STAAD, {len(results) - len(bad)} of "
          f"{len(results)} match  {'OK' if not bad and not extra else 'MISMATCH'}")
    for n, role, _, txt in bad:
        print(f"  !! node {n} ({role}): {txt}")
    if extra:
        print(f"  !! extra support nodes not made by this stage: {sorted(extra)}")

    all_nodes = [r["node"] for r in rows]
    print("\n" + "=" * 64)
    print("MANUAL STEP (no OpenSTAAD function exists for this):")
    print("  STAAD editor -> paste this line straight AFTER the SUPPORTS block:")
    print(f"\n      SPRING COMPRESSION {sa.staad_list(all_nodes)} KFY\n")
    print("  This makes the base springs compression-only (TR.27.5).")
    print("=" * 64)
    print("CHECK IN STAAD: Specification > Supports shows 3 support types;")
    print("  end nodes 1, 4: FX FZ fixed; nodes 5, 6 and intermediate: only FY spring.")
    print("  (Model is NOT saved by the script - save in STAAD when happy.)")
    print(line)


# -----------------------------------------------------------------------------
# Entry point called by run.py
# -----------------------------------------------------------------------------
def run(staad, model):
    check_inputs()
    ks, rows = compute_springs(model)
    per_role = spring_per_role(rows)

    sa.set_units_m_kn(staad)
    refs = assign_supports(staad, per_role)
    sa.refresh_view(staad, sa.LABEL_SUPPORT)
    check = read_back(staad, per_role)

    model.ks, model.springs, model.support_refs = ks, rows, refs
    print_summary(model, ks, rows, per_role, refs, check)
