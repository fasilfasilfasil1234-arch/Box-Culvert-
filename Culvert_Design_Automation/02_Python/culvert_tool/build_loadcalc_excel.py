"""
BUILD_LOADCALC_EXCEL.PY - load calculation sheet in the EDRC format
===================================================================

Run with  build_loadcalc.bat  (no STAAD needed).

- Reads the INPUTS blocks of stage1_geometry.py, stage2_springs.py and
  stage3_loads.py - the same numbers STAAD gets. Nothing is typed twice.
- Writes  Culvert_Design_Automation/05_Output/Load_Calculation_Single_Cell.xlsx
  in the L&T EDRC format: red = input, black = formula, working strings
  with substituted numbers, live formulas everywhere.
- Shows BOTH SIDL cases (a) and (b) and marks the governing one.
- Column I onwards (outside the print area) holds the Python cross-check:
  every key value is compared with the value the STAAD stages calculate.
- If Excel is installed it recalculates and saves the file, so the numbers
  show in any viewer, and counts formula errors.
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import stage1_geometry as s1        # noqa: E402
import stage2_springs as s2         # noqa: E402
import stage3_loads as s3           # noqa: E402
from edrc_sheet import EDRCSheet    # noqa: E402
from model import BoxModel          # noqa: E402

OUT_DIR = HERE.parents[1] / "05_Output"
OUT_FILE = OUT_DIR / "Load_Calculation_Single_Cell.xlsx"
LOGO = HERE / "lt_logo.png"

# Title-block entries (edit if needed)
SHEET_TITLE = "LOAD CALCULATION FOR SINGLE CELL RCC BOX CULVERT"
PROJECT = "SINGLE CELL RCC BOX CULVERT - DESIGN AUTOMATION"
DOC_NO = "-"
DESIGNED = "MF"
CHECKED = ""


def T(ref, fmt="General"):
    """Working-string piece: TEXT(Fnn, fmt)."""
    return f'TEXT(F{ref},"{fmt}")'


def python_model():
    """Same calculation the STAAD stages run, without STAAD."""
    m = BoxModel()
    s1.fill_model(m, s1.build_geometry())
    ks, rows = s2.compute_springs(m)
    per_role = s2.spring_per_role(rows)
    v = s3.compute_values(m)
    return m, ks, per_role, v


def build():
    s1.check_inputs()
    s2.check_inputs()
    m, ks_py, per_role, v = python_model()
    s3.check_inputs(m)

    s = EDRCSheet(title=SHEET_TITLE, sheet_name="Load cal", project=PROJECT,
                  doc_no=DOC_NO, designed=DESIGNED, checked=CHECKED,
                  logo=str(LOGO) if LOGO.exists() else None)
    checks = []          # (row of main value, python value, label)

    def chk(r, py, label):
        checks.append((r, py, label))

    # ------------------------------------------------------------------ 1
    s.section("1", "Design data")
    s.head("1.1", "Dimensions (1 m strip, single cell)")
    rB = s.row(ref="GAD", desc="Clear span (B)", val=s1.CLEAR_SPAN_B, unit="m", fmt="0.000", inp=True)
    rD = s.row(ref="GAD", desc="Clear height (D)", val=s1.CLEAR_HEIGHT_D, unit="m", fmt="0.000", inp=True)
    rtt = s.row(ref="GAD", desc="Top slab thickness", val=s1.T_TOP, unit="m", fmt="0.000", inp=True)
    rtw = s.row(ref="GAD", desc="Side wall thickness", val=s1.T_WALL, unit="m", fmt="0.000", inp=True)
    rtb = s.row(ref="GAD", desc="Bottom slab thickness", val=s1.T_BOT, unit="m", fmt="0.000", inp=True)
    rsw = s.row(desc="Width of strip considered", val=s1.STRIP_WIDTH, unit="m", fmt="0.00", inp=True)
    rL = s.row(desc="C/C span (L) = B + tw",
               work=f'="="&{T(rB,"0.000")}&"+"&{T(rtw,"0.000")}',
               val=f"=F{rB}+F{rtw}", unit="m", fmt="0.000")
    chk(rL, m.L, "C/C span L")
    rH = s.row(desc="C/C height (H) = D + tt/2 + tb/2",
               work=f'="="&{T(rD,"0.000")}&"+"&{T(rtt,"0.000")}&"/2+"&{T(rtb,"0.000")}&"/2"',
               val=f"=F{rD}+F{rtt}/2+F{rtb}/2", unit="m", fmt="0.000")
    chk(rH, m.H, "C/C height H")
    rLb = s.row(desc="Overall width (outer face to outer face) = B + 2 tw",
                work=f'="="&{T(rB,"0.000")}&"+2×"&{T(rtw,"0.000")}',
                val=f"=F{rB}+2*F{rtw}", unit="m", fmt="0.000")
    chk(rLb, m.overall_width, "Overall width")
    s.status(f'=IF(F{rL}>{s1.SEISMIC_FLAG_SPAN},"NOTE: seismic","OK")')

    s.head("1.2", "Materials")
    rgc = s.row(ref="Decision 16 Oct", desc="Unit weight of concrete", val=s1.DENSITY,
                unit="kN/m3", fmt="0.00", inp=True)
    s.row(ref="IRC:112\nTable 6.5", desc="Modulus of elasticity (M30)", val=s1.E_CONCRETE,
          unit="kN/m2", fmt="0.00E+00", inp=True)
    rgs = s.row(ref="Geotechnical\nreport", desc="Unit weight of soil fill", val=s3.GAMMA_SOIL,
                unit="kN/m3", fmt="0.00", inp=True)
    rphi = s.row(ref="Geotechnical\nreport", desc="Angle of internal friction (φ)", val=s3.PHI_DEG,
                 unit="deg", fmt="0.0", inp=True)
    rsbc = s.row(ref="Geotechnical\nreport", desc="Safe bearing capacity (qa)", val=s2.SBC_KPA,
                 unit="kN/m2", fmt="0.0", inp=True)
    rgw = s.row(desc="Unit weight of water", val=s3.GAMMA_WATER, unit="kN/m3", fmt="0.00", inp=True)

    # ------------------------------------------------------------------ 2
    s.blank()
    s.section("2", "Modelling and idealisation of supports")
    s.note("Line model on the member centrelines, 1 m strip, analysed in STAAD.Pro. Top slab and "
           "walls are single members; the base slab (wall centreline to wall centreline) is split at "
           "the inner wall faces and at N intermediate nodes, with a Winkler spring "
           "(compression-only) at every base node. The outer half wall (tw/2) is not modelled; its "
           "soil contact is added to the end spring.")
    rfos = s.row(ref="IRC:78\nCl 706.3.1.1", desc="Factor of safety (SF)", val=s2.FOS, fmt="0.00", inp=True)
    rbw = s.row(ref="Bowles", desc="Bowles factor", val=s2.BOWLES_FACTOR, fmt="0.0", inp=True)
    rks = s.row(ref="Bowles,\nFoundation\nAnalysis & Design",
                desc="Modulus of subgrade reaction ks = 40 × SF × qa",
                work=f'="="&{T(rbw)}&"×"&{T(rfos)}&"×"&{T(rsbc)}',
                val=f"=F{rbw}*F{rfos}*F{rsbc}", unit="kN/m2/m", fmt="0.0")
    chk(rks, ks_py, "ks")
    rN = s.row(desc="No. of intermediate spring nodes (N)", val=s1.N_BASE_INTERMEDIATE,
               unit="nos", fmt="0", inp=True)
    rs = s.row(desc="Spacing of intermediate nodes s = B/(N+1)",
               work=f'="="&{T(rB,"0.000")}&"/("&{T(rN)}&"+1)"',
               val=f"=F{rB}/(F{rN}+1)", unit="m", fmt="0.000")
    rte = s.row(desc="Tributary length - end node (wall centreline) = tw/2 + tw/4",
                work=f'="="&{T(rtw,"0.000")}&"/2+"&{T(rtw,"0.000")}&"/4"',
                val=f"=F{rtw}/2+F{rtw}/4", unit="m", fmt="0.000")
    rtj = s.row(desc="Tributary length - junction node (inner wall face) = tw/4 + s/2",
                work=f'="="&{T(rtw,"0.000")}&"/4+"&{T(rs,"0.000")}&"/2"',
                val=f"=F{rtw}/4+F{rs}/2", unit="m", fmt="0.000")
    rti = s.row(desc="Tributary length - intermediate node = s", val=f"=F{rs}", unit="m", fmt="0.000")
    rsum = s.row(desc="Sum of tributary lengths = 2×end + 2×junction + N×intermediate",
                 work=f'="=2×"&{T(rte,"0.000")}&"+2×"&{T(rtj,"0.000")}&"+"&{T(rN)}&"×"&{T(rti,"0.000")}',
                 val=f"=2*F{rte}+2*F{rtj}+F{rN}*F{rti}", unit="m", fmt="0.000")
    s.status(f'=IF(ABS(F{rsum}-F{rLb})<0.0005,"VERIFIED","CHECK")')
    rows_k = {}
    for role, rt in (("end", rte), ("junction", rtj), ("intermediate", rti)):
        r = s.row(desc=f"Spring stiffness KFY - {role} support = ks × trib × strip",
                  work=f'="="&{T(rks,"0.0")}&"×"&{T(rt,"0.000")}&"×"&{T(rsw,"0.00")}',
                  val=f"=F{rks}*F{rt}*F{rsw}", unit="kN/m", fmt="0.00", key=True)
        rows_k[role] = r
        chk(r, per_role[role][1], f"K {role}")
    s.note("Only three supports are defined in STAAD. End nodes: FX FZ fixed, FY spring "
           "(FIXED BUT MX MY MZ KFY); junction and intermediate: only FY spring "
           "(FIXED BUT FX FZ MX MY MZ KFY). "
           "Springs made compression-only with SPRING COMPRESSION ... KFY (STAAD TR.27.5).")

    # ------------------------------------------------------------------ 3
    s.blank()
    s.section("3", "Load calculation")
    s.note("Loads as per IRC:6-2017. Load case numbers are the STAAD primary load case numbers.")

    s.head("3.1", "Dead load (DL) - LOAD 1")
    for name, rt in (("top slab", rtt), ("side wall", rtw), ("bottom slab", rtb)):
        s.row(desc=f"Self weight of {name}",
              work=f'="="&{T(rt,"0.000")}&"×"&{T(rsw,"0.00")}&"×"&{T(rgc,"0.00")}',
              val=f"=F{rt}*F{rsw}*F{rgc}", unit="kN/m", fmt="0.000")
    s.note("(SELFWEIGHT Y -1 command is used in STAAD; density 25 kN/m3 in DEFINE MATERIAL)")

    s.head("3.2", "Superimposed dead load (SIDL) - LOAD 2")
    layer_rows = []
    for i, (name, h, g) in enumerate(s3.SIDL_LAYERS, 1):
        rh = s.row(desc=f"Thickness - {name}", val=h, unit="m", fmt="0.0000", inp=True)
        rg = s.row(desc=f"Density - {name}", val=g, unit="kN/m3", fmt="0.00", inp=True)
        rp = s.row(desc=f"Pressure - {name} = h × γ",
                   work=f'="="&{T(rh,"0.0000")}&"×"&{T(rg,"0.00")}',
                   val=f"=F{rh}*F{rg}", unit="kN/m2", fmt="0.000")
        layer_rows.append((rh, rp))
    rfill = s.row(desc="Total depth of fill above top slab", val="=" + "+".join(f"F{a}" for a, _ in layer_rows),
                  unit="m", fmt="0.0000")
    chk(rfill, v["fill_total"], "Fill depth")
    rp = s.row(desc="Total layer pressure p = Σ h × γ", val="=" + "+".join(f"F{b}" for _, b in layer_rows),
               unit="kN/m2", fmt="0.000")
    chk(rp, v["p_layers"], "Layer pressure p")

    s.row(desc="Case (a): layers over the full 1 m strip", bold_desc=True)
    rwa = s.row(desc="wa = p × 1.0", work=f'="="&{T(rp,"0.000")}&"×"&{T(rsw,"0.00")}',
                val=f"=F{rp}*F{rsw}", unit="kN/m", fmt="0.000", key=True)
    chk(rwa, v["w_sidl_a"], "SIDL case (a)")
    s.row(desc="Case (b): crash barrier within the 1 m strip", bold_desc=True)
    rbcb = s.row(ref="GAD", desc="Width of crash barrier (b)", val=s3.CRASH_BARRIER_WIDTH,
                 unit="m", fmt="0.000", inp=True)
    racb = s.row(ref="IRC:5\nFig 2", desc="Area of crash barrier", val=s3.CRASH_BARRIER_AREA,
                 unit="m2", fmt="0.000", inp=True)
    rwcb = s.row(desc="Weight of crash barrier = A × γc",
                 work=f'="="&{T(racb,"0.000")}&"×"&{T(rgc,"0.00")}',
                 val=f"=F{racb}*F{rgc}", unit="kN/m", fmt="0.000")
    rwb = s.row(desc="wb = A×γc + p × (1.0 - b)",
                work=f'="="&{T(rwcb,"0.000")}&"+"&{T(rp,"0.000")}&"×("&{T(rsw,"0.00")}&"-"&{T(rbcb,"0.000")}&")"',
                val=f"=F{rwcb}+F{rp}*(F{rsw}-F{rbcb})", unit="kN/m", fmt="0.000", key=True)
    chk(rwb, v["w_sidl_b"], "SIDL case (b)")
    rw = s.row(desc="SIDL applied in STAAD = max(wa, wb)",
               work=f'="=max("&{T(rwa,"0.000")}&", "&{T(rwb,"0.000")}&")"',
               val=f"=MAX(F{rwa},F{rwb})", unit="kN/m", fmt="0.000", key=True)
    chk(rw, v["w_sidl"], "SIDL to STAAD")
    s.status(f'=IF(F{rwa}>=F{rwb},"NOTE: (a) governs","NOTE: (b) governs")')
    s.note("Applied as UNI GY (downward) on all top slab members.")

    s.head("3.3", "Earth pressure (EP) - LOAD 3")
    s.note("Walls are restrained against movement: at-rest pressure, K0 = 1 - sin φ (Jaky).")
    rk0 = s.row(ref="IRC:6\nCl 214.1", desc="K0 = 1 - sin φ",
                work=f'="=1-sin("&{T(rphi,"0.0")}&"°)"',
                val=f"=1-SIN(RADIANS(F{rphi}))", fmt="0.0000")
    chk(rk0, v["K0"], "K0")
    rzt = s.row(desc="Depth to top slab centreline = fill + tt/2",
                work=f'="="&{T(rfill,"0.0000")}&"+"&{T(rtt,"0.000")}&"/2"',
                val=f"=F{rfill}+F{rtt}/2", unit="m", fmt="0.000")
    rzb = s.row(desc="Depth to base slab centreline = above + H",
                work=f'="="&{T(rzt,"0.000")}&"+"&{T(rH,"0.000")}',
                val=f"=F{rzt}+F{rH}", unit="m", fmt="0.000")
    rept = s.row(desc="Earth pressure at top = K0 × γ × z",
                 work=f'="="&{T(rk0,"0.000")}&"×"&{T(rgs,"0.0")}&"×"&{T(rzt,"0.000")}',
                 val=f"=F{rk0}*F{rgs}*F{rzt}", unit="kN/m2", fmt="0.000", key=True)
    chk(rept, v["p_ep_top"], "EP top")
    repb = s.row(desc="Earth pressure at bottom = K0 × γ × z",
                 work=f'="="&{T(rk0,"0.000")}&"×"&{T(rgs,"0.0")}&"×"&{T(rzb,"0.000")}',
                 val=f"=F{rk0}*F{rgs}*F{rzb}", unit="kN/m2", fmt="0.000", key=True)
    chk(repb, v["p_ep_bot"], "EP bottom")
    s.note("Applied as one TRAP GX on each wall member (base to top centreline), pushing inward, × 1 m strip.")
    s.note("Calculated values are used (the twin-cell STAAD had rounded 5 / 49 kN/m2).")

    s.head("3.4", "Live load surcharge (LS) - LOAD 4 (both sides), LOAD 5 (one side)")
    rhs = s.row(ref="IRC:6\nCl 214.1.1.3", desc="Equivalent height of fill",
                val=s3.SURCHARGE_HEIGHT, unit="m", fmt="0.00", inp=True)
    rls = s.row(desc="Surcharge pressure = K0 × γ × h",
                work=f'="="&{T(rk0,"0.000")}&"×"&{T(rgs,"0.0")}&"×"&{T(rhs,"0.00")}',
                val=f"=F{rk0}*F{rgs}*F{rhs}", unit="kN/m2", fmt="0.000", key=True)
    chk(rls, v["p_ls"], "LL surcharge")
    s.note("LOAD 4: UNI GX on both walls, inward.  LOAD 5: left wall only (EP-leading case).")

    s.head("3.5", "Braking force - LOAD 6")
    rfl = s.row(desc="Fill for live load dispersion (incl. wearing coat)", val=s3.FILL_FOR_LL,
                unit="m", fmt="0.000", inp=True)
    s.note("F = 0.2 × q × dL × (3 - fill)/3  per m width (0 if fill > 3 m); q before impact.")
    brk_rows = []
    for name, q, dL in s3.BRAKING_VEHICLES:
        s.row(desc=name, bold_desc=True)
        rq = s.row(ref="Vehicle\nload calc", desc="Load intensity q (before impact)", val=q,
                   unit="kN/m2", fmt="0.000", inp=True)
        rdl = s.row(ref="Vehicle\nload calc", desc="Dispersed length dL", val=dL,
                    unit="m", fmt="0.000", inp=True)
        rf = s.row(desc="Braking force F",
                   work=f'="=0.2×"&{T(rq,"0.00")}&"×"&{T(rdl,"0.000")}&"×(3-"&{T(rfl,"0.000")}&")/3"',
                   val=f"=IF(F{rfl}>3,0,0.2*F{rq}*F{rdl}*(3-F{rfl})/3)", unit="kN/m", fmt="0.000")
        brk_rows.append(rf)
    rF = s.row(desc="Braking force applied = max of the above",
               val=f"=MAX({','.join(f'F{r}' for r in brk_rows)})", unit="kN/m", fmt="0.000", key=True)
    chk(rF, v["F_brake"], "Braking force")
    s.note("Applied as JOINT LOAD FX at the top-left corner node (as the twin-cell STAAD).")
    s.note("q and dL above are PLACEHOLDERS from the twin-cell Excel until the vehicle module exists.")
    s.status('="NOTE: placeholder"')

    s.head("3.6", "Water inside the cell - LOAD 7")
    hw = s1.CLEAR_HEIGHT_D if s3.WATER_DEPTH is None else s3.WATER_DEPTH
    rhw = s.row(desc="Water depth above top of base slab (Hw)",
                val=(f"=F{rD}" if s3.WATER_DEPTH is None else hw), unit="m", fmt="0.000",
                inp=s3.WATER_DEPTH is not None)
    rpw = s.row(desc="Water pressure at top of base slab = γw × Hw",
                work=f'="="&{T(rgw,"0.00")}&"×"&{T(rhw,"0.000")}',
                val=f"=F{rgw}*F{rhw}", unit="kN/m2", fmt="0.000", key=True)
    chk(rpw, v["p_water"], "Water pressure")
    s.note("Triangular, outward on both inner wall faces: 0 at Hw above the top of the base slab, "
           "γw·Hw at the top of the base slab (tb/2 above the base centreline).")
    if s3.WATER_ON_BASE:
        s.note("Also γw·Hw downward on the base slab between the inner wall faces.")
    s.status('="NOTE: confirm"')

    # ------------------------------------------------------------------ 4
    s.blank()
    s.section("4", "Summary of primary load cases (to STAAD)")
    summary = [
        ("1", "Dead load", "SELFWEIGHT Y -1", None, ""),
        ("2", "SIDL (max of a, b)", "UNI GY top slab", f"=F{rw}", "kN/m"),
        ("3", "Earth pressure - top", "TRAP GX both walls", f"=F{rept}", "kN/m"),
        ("3", "Earth pressure - bottom", "", f"=F{repb}", "kN/m"),
        ("4", "LL surcharge both sides", "UNI GX both walls", f"=F{rls}", "kN/m"),
        ("5", "LL surcharge one side", "UNI GX left wall", f"=F{rls}", "kN/m"),
        ("6", "Braking", "JOINT FX top-left", f"=F{rF}", "kN"),
        ("7", "Water inside cell", "TRAP GX walls (+base)", f"=F{rpw}", "kN/m"),
    ]
    for no, name, how, val, unit in summary:
        s.row(ref=f"LOAD {no}", desc=name, work=how, workcol="D",
              val=val, unit=unit or None, fmt="0.000")

    # ------------------------------------------------------------------ 5
    s.blank()
    s.section("5", "Notes and limitations")
    for t in ("1. Seismic not applied; spans above 10 m are flagged.",
              "2. Temperature and shrinkage: next version.",
              "3. Vehicle live load (5 cases): next version. Braking q and dL are placeholders.",
              "4. SIDL goes to STAAD as one case; the twin-cell file split it into head wall "
              "(×1.35) and surfacing (×1.75) for the ULS factors - to be decided.",
              "5. Water load on the base slab - to confirm.",
              "6. Base springs compression-only: combinations by REPEAT LOAD (TR.27.5)."):
        s.note(t)

    # ------------------------------------------------- supporting: cross-check
    first = checks[0][0]
    s.support_header(first - 1, "PYTHON CROSS-CHECK  (value used by the STAAD stages)", "I", "M")
    for r, py, label in checks:
        s.cell(f"I{r}", val=label)
        s.ws.merge_cells(f"I{r}:J{r}")
        s.cell(f"K{r}", val=round(py, 6), fmt="0.000")
        s.cell(f"L{r}", val=f'=IF(ABS(F{r}-K{r})<=0.0005*MAX(1,ABS(K{r})),"VERIFIED","MISMATCH")')
    s.status_format([f"F9:F{s.cursor}", f"L9:L{s.cursor}"])

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        s.finish(str(OUT_FILE))
    except PermissionError:
        raise SystemExit(f"Could not save {OUT_FILE.name} - it is open in Excel. Close it and run again.")
    return len(checks)


def excel_recalc(path):
    """Recalculate and save through Excel (if installed) so cached values exist."""
    try:
        from comtypes import client
    except ImportError:
        return "comtypes not installed - open the file in Excel to calculate it."
    xl = None
    try:
        xl = client.CreateObject("Excel.Application")
        xl.Visible = False
        xl.DisplayAlerts = False
        wb = xl.Workbooks.Open(str(path))
        xl.CalculateFull()
        wb.Save()
        wb.Close(False)
    except Exception as exc:  # Excel missing or COM issue - file is still valid
        return f"Excel recalculation skipped ({exc}). Excel will calculate on open."
    finally:
        if xl is not None:
            try:
                xl.Quit()
            except Exception:
                pass

    # Count formula errors and MISMATCH stamps in the cached values Excel wrote.
    from openpyxl import load_workbook
    ws = load_workbook(path, data_only=True).worksheets[0]
    errors = mismatches = 0
    for row in ws.iter_rows(values_only=True):
        for c in row:
            if isinstance(c, str) and c.startswith("#"):
                errors += 1
            elif c == "MISMATCH":
                mismatches += 1
    return f"Excel recalculated: {errors} formula errors, {mismatches} MISMATCH."


if __name__ == "__main__":
    n = build()
    print(f"saved {OUT_FILE}")
    print(f"{n} values cross-checked against the Python stage calculations (column L).")
    print(excel_recalc(OUT_FILE))
