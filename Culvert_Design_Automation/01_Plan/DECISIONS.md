# DECISIONS – Box Culvert Design Automation (single cell)

The permanent decision log. Newest first. "You" = Muhammed Fasil.
Each entry: **decision** – why. *Rejected:* alternatives, where there were any.
Replaced entries stay in the log, marked **Superseded on <date> by <entry>**.

Built on 12 Nov 2026 from `_archive/Decisions_Log.md` (28 Sep – 17 Oct), the old "Decisions"
section of `CLAUDE.md` (16 – 31 Oct), `_archive/Important_Changes_2026-10-16.md` and the
answered items of `04_Open_Questions.md`.

---

## 31 Oct 2026 – Vehicle loading (pilot: 70R wheeled)

- **D31-1 Water on the base slab is confirmed.** Load case 7 puts γw·Hw downward on the base slab
  between the inner wall faces, as well as the triangular pressure on both walls. You confirmed it
  ("water on bottom slab required"). This answers the 16 Oct question (old Q2) and closes the
  `WATER_ON_BASE = True` default.
- **D31-2 SIDL split and water-in-combinations are deferred to Stage 4.** You want to study load
  combinations first. They are listed in `04_Open_Questions.md` as reminders for the start of Stage 4.
- **D31-3 Next work = vehicle loads, pilot 70R wheeled.** The impact factor (IRC:6 cl 208) goes into
  each vehicle load case's intensity, not into braking.
- **D31-4 IRC:112 Annex B-3 inputs.** l0 = effective span = centre-to-centre of the walls
  = B + tw/2 + tw/2 (= `model.L`, 5.4 m in the example), per IRC:112 cl 7.6.1.1 (2)/(3). Already
  in the tool. **b = width of the top slab perpendicular to l0** (the culvert's out-to-out length
  along the road), per B3.2 "b is the width of the slab". b becomes a new input of the vehicle
  stage, not of Stage 1. *Rejected:* b = carriageway width (the twin-cell Excel's choice). It is
  conservative but not what the code defines. The tool may print α for both so you can compare.
- **D31-5 Transverse position of the vehicle** (IRC:6-2017, checked in the PDF):
  - 70R kerb clearance C = 1.2 m (Fig. 1 Note 4).
  - Two 70R vehicles passing on a multi-lane deck: 1.2 m between outer edges (Note 5). Not
    needed now.
  - Class A: f = 0.15 m for all carriageway widths. g varies with the clear carriageway W
    (Table 3): g = W − 4.9 for W = 5.3 – 6.1 m, and 1.2 m above 6.1 m.
  - The vehicle sits hard against the minimum clearance (cl 204.1.2).
  - Edge-wheel centre from the slab free edge = barrier width + C + tyre width/2
    = 0.5 + 1.2 + 0.43 = 2.13 m (as the twin-cell Excel).
  - The twin-cell "overhang" check is the IRC:112 B3.2 free-edge rule.
  - Clearance is an input for each vehicle.
- **D31-6 Slab extension beyond the crash barrier** is a new input, default 0. The outer face of
  the barrier is taken as the free edge of the top slab unless you set it. You agreed.
- **D31-7 'L', 'M', 'N' are the 70R wheeled wheel arrangements** of IRC:6 Fig. 1 (all 2.79 m
  overall), not crash-barrier types. L type is built now; M and N come later.
- **D31-8 Vehicle loads live in a reusable package `02_Python/irc_live_load/`**, with no STAAD and
  no culvert logic, so other tools can use it:
  - `vehicles.py`: IRC vehicles as data.
  - `deck_slab.py`: one axle → line load (IRC:112 B-3 and IRC:6 cl 208).
  - `moving_load.py`: steps the vehicle.

  You asked for it as a separate script that future tools can use.
- **D31-9 Position search: the whole vehicle is stepped, and only the worst positions are kept.**
  - The full 100 t vehicle (7 axles, spacings checked on Fig. 1) moves in 0.05 m steps, both
    directions.
  - Only axles whose centre is on the span count; their patches are clipped at the supports.
  - Each axle gets its own a and b_eff (IRC:112 B3.2(1)(ii)).
  - Simple beam screening picks the worst sagging (SAG), hogging (HOG) and shear (SHEAR)
    positions. Only those go to STAAD and to the EDRC sheet.

  You agreed ("this version looks good"). *Rejected:* fixed hand positions with only the 1.37 m
  axle pair (the twin-cell approach). On a 5.4 m span, three axles fit at once. Rejected too:
  counting axles centred over a wall, which gave an inflated 5 cm sliver. Hand positions stay as
  a check only.
- **D31-10 Tyre contact length comes from IRC:6 Annex A by default**, with an override. Tyre
  0.41 × 0.61 = overall width × rim diameter. Tread = 0.41 − 0.05 = 0.36 m. That gives
  17 t → 0.224 m, 12 t → 0.158 m and 8 t → 0.105 m. The twin-cell Excel used 0.263 m (the 10 t
  wheel value); the override can reproduce it. Which value to use for design is **still open**
  (`04_Open_Questions.md`).
- **D31-11 Impact follows the code wording.** Half impact when the fill including road crust is
  not less than 0.6 m (IRC:6 cl 208.6). It is checked on the total fill, not the LL-dispersion
  fill. The span for impact is the effective span of the member (cl 208.5 Note).
- **D31-12 Code PDFs are kept in `IRC codes/`** (IRC:112-2020, IRC:6-2017). They are the
  cross-check source for clauses.

## 17 Oct 2026 – Corrections after the first STAAD run

- **D17-1 Base slab from wall centreline to wall centreline, with no overhang.** Only the base is
  split; the top slab and both walls are single members.
  - Nodes: 1–4 corners (1 bottom-left, 2 top-left, 3 top-right, 4 bottom-right). 5–6 sit on the
    base at the inner wall faces (tw/2 from the corners) and are called "junction". 7 onwards
    are the N intermediate nodes across the clear span, s = B/(N+1).
  - Members: 1 top slab (2→3), 2 left wall (1→2), 3 right wall (4→3), 4 onwards the base
    pieces from left to right.
  - Everything is created explicitly with CreateNode / CreateBeam.
  - Example B 5.0, tw 0.4, N 9: x = 0, 0.2, 0.7 … 4.7, 5.2, 5.4.

  You asked for this. *Rejected:* base to the outer wall faces with extra slab-face nodes on the
  walls and top slab (16 Oct).
- **D17-2 Origin = bottom-left corner** (left wall centreline, base centreline). *Rejected:*
  origin at the left outer-face end (16 Oct).
- **D17-3 Spring tributary lengths:**
  - End (wall centreline) = tw/2 + tw/4. The unmodelled outer half wall is added, giving 0.30 m
    in the example.
  - Junction = tw/4 + s/2 = 0.35 m.
  - Intermediate = s = 0.50 m.
  - Check: 2 × 0.30 + 2 × 0.35 + 9 × 0.50 = 5.8 m = B + 2tw.

  *Rejected:* end tributary 0.10 m with a 5.4 m total (16 Oct).
- **D17-4 Support releases** (you confirmed; same as the twin-cell STAAD):
  - End nodes: FX and FZ fixed, FY spring (FIXED BUT MX MY MZ KFY).
  - Junction and intermediate nodes: FY spring only (FIXED BUT FX FZ MX MY MZ KFY).

  This also settles the horizontal restraint: FX is fixed at the two end nodes. It answers the
  16 Oct question (old Q1). *Rejected:* "end FX and FZ released, everything else fixed" (16 Oct
  note), and "fix FX at one node" (original plan).
- **D17-5 OpenSTAAD support codes are opposite in the two functions.**
  - `CreateSupportFixedBut`: 1 = released, 0 = fixed, FY = −1 with KFY in the spring array.
  - `GetSupportInformation`: 0 = released, 1 = fixed.

  This was proved by the 16 Oct run, where every support came out inverted. The Bentley help
  text for Create states the Get convention, which is wrong for Create.
- **D17-6 Stage 3 does not call `UpdateStructure`.** STAAD crashed ("remote procedure call failed")
  there right after the loads were added. `staad_api.call` now turns a lost-STAAD error into a
  clear stop message.
- **D17-7 Stages 1–3 ran successfully in STAAD.** 15 nodes / 15 members, density 25 read back,
  13 of 13 supports match, and all 7 load cases read back OK. A follow-up check added load 7
  with Hw = 3 m to the open file. It read back exactly: TRAP from 30 kN/m at y = 0.2 to 0 at
  y = 3.2, plus 30 kN/m on the base. The same function works for any Hw up to the clear
  height. STAAD help TR.32.2 confirms TRAP f10/f11 are the load's own start and end values.

## 16 Oct 2026 – Stages 1–3 coded (Claude Code session)

- **D16-1 Every OpenSTAAD call is checked against the local help** of STAAD CE 22.00.00.15
  (`Help\OSAPP`) and tagged [L] in the code. STAAD command syntax comes from `Help\STD_*.html`,
  tagged [H].
- **D16-2 Twin-cell STAAD read live (read-only):**
  - Material CONCRETE: E 3.1e7, DENSITY 25 (DEFINE MATERIAL).
  - Supports: end = FIXED BUT MX MY MZ KFY; the others = FIXED BUT FX FZ MX MY MZ KFY.
  - 14 primary cases (load type None) and 64 LOAD COMB. It has no REPEAT LOAD and no
    SPRING COMPRESSION, because its springs are linear.
- **D16-3 Concrete density 25 kN/m³ is set as a user material named CONCRETE**
  (`CreateIsotropicMaterialProperties`), the same way as the twin-cell DEFINE MATERIAL. It is
  assigned after all sections, and the density is read back. This answers old Q3.
- **D16-4 Compression-only springs are a manual step.** The local OpenSTAAD help has no function
  for it, so Stage 2 prints the `SPRING COMPRESSION <nodes> KFY` line to paste after the SUPPORTS
  block (TR.27.5). This answers old Q4. With compression-only springs, combinations must be
  REPEAT LOAD cases.
- **D16-5 Only three supports are created in STAAD** (end, junction, intermediate). K = ks ×
  tributary length × 1 m, with ks = 40 × FOS × SBC (Bowles). The springs stay compression-only.
- **D16-6 Load cases for this version:**
  1. DL: SELFWEIGHT Y −1 (density 25).
  2. SIDL: max of (a) and (b). (a) = Σ(hᵢγᵢ) × 1.0. (b) = A_cb·γc + Σ(hᵢγᵢ) × (1 − b_cb).
     STAAD gets the larger; the calc sheet shows both.
  3. Earth pressure on both walls, at rest K0 = 1 − sin φ. The calculated values are used
     (4.59 / 48.34). *Rejected:* the twin-cell STAAD's rounded 5 / 49.
  4. LL surcharge on both walls, K0·γ·1.2 m.
  5. LL surcharge on one side (the left wall).
  6. Braking: a joint load FX at the top-left corner, as the twin-cell file. Its q and dL per
     vehicle are placeholders from the twin-cell Excel until the vehicle stage exists.
  7. Water inside the cell: triangular on both inner wall faces, 0 at t_bot/2 + Hw, γw·Hw at
     t_bot/2 (on the base: see D31-1).
- **D16-7 Not in this version:** seismic (the tool flags spans above 10 m) and temperature (next
  version).
- **D16-8 The load calculation is written in your EDRC Excel format**, not the twin-cell Excel's
  layout. It uses live formulas, and a column outside the print area cross-checks every value
  against Python.
- **D16-9 Load combinations: study and explain only, no implementation yet.** Because the springs
  are compression-only, they will be built as primary cases with REPEAT LOAD.
- **D16-10 The twin-cell Excel and STAAD files show the method only.** The tool stays single cell.
- **D16-11 Run setup:** `setup.bat` (venv with comtypes, openpyxl, pillow), `run.bat`,
  `build_loadcalc.bat`. `CLAUDE.md` holds the project rules.
- **D16-12 Base slab to the outer wall faces, with junction nodes on the wall centrelines.**
  End tributary 0.10 m; total 5.4 m. **Superseded on 17 Oct by D17-1 and D17-3.**
- **D16-13 Walls get nodes at the slab faces and the top slab at the inner wall faces.**
  **Superseded on 17 Oct by D17-1** (single members).
- **D16-14 Origin = left outer-face end.** **Superseded on 17 Oct by D17-2.**
- **D16-15 End supports "FX and FZ released, everything else fixed"; junction and intermediate
  "FY only, everything else fixed"** (16 Oct note, marked "to confirm"). **Superseded on 17 Oct
  by D17-4.**
- **D16-16 Release code convention 0 = released / 1 = fixed** (as written in the help).
  **Superseded on 17 Oct by D17-5**, which applies only to `GetSupportInformation`; creation uses
  the opposite.
- **D16-17 Scope agreed for the session:** the new base layout, the seven load cases above, the
  EDRC output, and studying the combinations only. Vehicle loading has five cases: 70R tracked,
  70R bogie, 70R wheeled, Class A 1-lane and Class A 2-lane. Each is dispersed through
  fill / SIDL / wearing coat, uses b_eff from IRC:112-2020 Annex B-3, and goes on the 1 m strip
  as a line load.

## 12 Oct 2026 – Code structure ("Stage 1 and 2 Python restructuring")

- **D12-1 One folder, `culvert_tool/`.** You run `run.py` only (now via `run.bat`).
- **D12-2 `run.py` finds the `stageN_*.py` files and runs them in order,** pausing after each
  (Enter = next, Q = stop).
- **D12-3 Shared files:** `staad_api.py` (STAAD helpers) and `model.py` (results passed between
  stages). They change only when a stage needs something new.
- **D12-4 Stage outputs pass to the next stage through `model.py`.** Geometry is never read back
  from STAAD.
- **D12-5 New stages are delivered as full replacement files,** with a list of which files to
  add or replace.
- **D12-6 Scripts never create or save a STAAD file.** You open STAAD, set kN-m, save the file
  and keep it open; the scripts model into it. Stage 1 stops if the model is not empty.

## 12 Oct 2026 – Calculation and report approach ("Automated culvert design planning")

- **D12-7 Python holds each calculation; Excel is the report Python writes** (*suggested, agreed
  in principle*). One module per calculation, each producing one EDRC sheet with live formulas,
  and Python cross-checks every cell. One workbook per culvert.
- **D12-8 Live-load modules run before STAAD:** fill depth → 45° dispersion → b_eff (IRC:112
  Annex B-3) → pressure per 1 m strip → STAAD load case.
- **D12-9 The logic comes from your approved Excel**, with the IRC codes as the cross-check. Any
  mismatch is flagged, never silently changed.
- **D12-10 Pilot live-load module: 70R wheeled.**

## 11 Oct 2026 – IRC 70R facts ("IRC 70R wheeled vehicles specifications")

- **D11-1 0.86 m is the dual-tyre width across traffic** (360 + 140 + 360 mm treads and gap).
- **D11-2 Contact length along traffic = wheel load ÷ (5.273 kg/cm² × 72 cm tread):** 8.5 t
  wheel ≈ 0.224 m; 10 t wheel ≈ 0.263 m. Confirmed from the code on 31 Oct (D31-10, Annex A
  Note 3). Some offices divide by 86 or 76 cm; your convention is still open.
- **D11-3 Max single axle 20 t; max bogie 40 t** (2 × 20 t at 1.22 m).

## 28 Sep – 7 Oct 2026 – Original plan chat

- **D07-1 Pipeline:** Inputs → STAAD model (OpenSTAAD) → Loads → Run / extract → Design (IRC:112)
  → Detailing → AutoCAD drawing → Review.
- **D07-2 STAAD is driven live through OpenSTAAD + `comtypes`,** with STAAD open beside the tool.
  Each stage adds to the model.
- **D07-3 Every OpenSTAAD call is checked against Bentley documentation before use,** with source
  tags in each file (now [L]/[H]/[R]/[B]/[M]/[T]/[S]).
- **D07-4 1 m strip line model on the centrelines; Winkler springs ks = 40 × FOS × SBC.**
- **D07-5 Stage 2 then:** a geometric end spring, FX fixed at one node, compression-only springs.
  **Superseded on 16–17 Oct by D16-5, D17-3 and D17-4** (only "compression-only" still stands).
- **D07-6 Compression-only cannot be set via OpenSTAAD,** so it is applied manually (One-way
  Spring tool or `SPRING COMPRESSION … KFY`). Confirmed on 16 Oct (D16-4).
- **D07-7 Drawings start with `ezdxf` (DXF)**, with AutoCAD COM as an option later. AutoCAD LT has
  no ActiveX.
- **D07-8 A desktop UI comes later.** The module structure is built now so the UI can plug in.
  The input window comes after all stages are verified.
