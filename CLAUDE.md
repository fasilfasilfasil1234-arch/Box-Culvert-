# CLAUDE.md – Box Culvert Design Automation (single cell)

Python tool that models a **single-cell RCC box culvert** in STAAD.Pro through OpenSTAAD
(`comtypes`), writes the load calculation in the **EDRC Excel format**, and later designs to
IRC:112. User: Muhammed Fasil (structural engineer). Read `Culvert_Design_Automation/00_README.md`
and `01_Plan/Important_Changes_2026-10-16.md` (final decisions, override the plan PDF).

## Rules (always)

1. **Verify every OpenSTAAD call against Bentley documentation before using it, and tag its
   source in the code.** Never guess a function name or argument order.
   - First source: the local help for the user's STAAD (CONNECT Edition **22.00.00.15**):
     `C:\Program Files\Bentley\Engineering\STAAD.Pro CONNECT Edition\Help\OSAPP\*.html`
     (Doxygen pages, e.g. `group___property_load_mem.html`). Tag `[L]`.
   - STAAD command syntax: `...\Help\STD_*.html` (e.g. TR.27.5). Tag `[H]`.
   - Tags: `[L]` local OpenSTAAD help, `[H]` STAAD help, `[R]` OpenSTAAD Ref Manual V8i,
     `[B]` Bentley Python help page, `[M]` Bentley openstaad-mcp notes, `[T]` tested live
     read-only on the user's PC, `[S]` secondary – confirm before relying on it.
2. **Keep the `culvert_tool/` structure**: `run.py` (never edited; runs `stageN_*.py` in order and
   pauses), `staad_api.py` (shared helpers), `model.py` (results passed between stages; geometry is
   never read back from STAAD), one `stageN_<name>.py` per stage with an `INPUTS` block at the top
   and a `run(staad, model)` function.
3. **Scripts never create, open or save STAAD files.** The user opens a blank file (kN, m), saves it,
   keeps it open; the stages model into it. Stage 1 stops if the model is not empty.
4. **Deliver full replacement files** (never partial patches) and list which files to add/replace.
5. Each stage confirms its own work by **read-back** (counts, `GetSupportInformation`,
   `GetMaterialProperty`, load counts) – Bentley notes some calls return failure when they worked.
6. **Never write to a model the user did not open for modelling** (e.g. a reference file). Reading
   reference models is read-only.
7. Engineering logic comes from the user's approved Excel/STAAD (method only – the tool is single
   cell). IRC codes are the cross-check. Mismatches are flagged, never silently changed.
8. The `.bat` files stay unchanged after setup unless a delivery says otherwise.
9. Inputs stay in each stage's INPUTS block for now; an input window comes after all stages are verified.

## Workflow

- `setup.bat` once (creates `.venv` with Python 3.13 64-bit; installs comtypes, openpyxl, pillow).
- `run.bat`: STAAD open with a blank saved file → stages run with pauses → user checks STAAD.
- `build_loadcalc.bat`: writes `Culvert_Design_Automation/05_Output/Load_Calculation_Single_Cell.xlsx`
  from the stage INPUTS (no STAAD). Recalculates via Excel COM and reports formula errors and
  MISMATCH stamps (column L cross-check against the Python stage values).
- Error loop: user pastes the console output → fix the code (full files) → user re-runs the same .bat.
- Use `py -3.13` (the plain `python` command is the Microsoft Store stub on this PC).

## OpenSTAAD facts confirmed on this PC (16 Oct 2026)

- comtypes arrays out: pass `_midlSAFEARRAY(...).create([...])` wrapped as a VT_BYREF VARIANT,
  then read the **SAFEARRAY with `.unpack()`** (`staad_api.read_array`). `[T]`
- Support release codes are **opposite** in the two functions (proved on the 16 Oct run):
  `CreateSupportFixedBut` release spec **1 = released, 0 = fixed**, FY = −1 with KFY in the spring
  array; `GetSupportInformation` returns **0 = released, 1 = fixed**, FY −1 (integer array).
  The help text for Create states the Get convention – it is wrong for Create.
- STAAD crashed (COM "remote procedure call failed") at `UpdateStructure` right after Stage 3 added
  loads. Stage 3 no longer calls it; `staad_api.call` turns RPC-lost errors into a clear stop.
- No OpenSTAAD function for compression-only springs. Manual editor line after SUPPORTS:
  `SPRING COMPRESSION <nodes> KFY` (TR.27.5). With it, combinations must be **REPEAT LOAD**.
- `AddSelfWeightInXYZ` direction 4/5/6 = X/Y/Z (Y = 5). Member load directions 1–9 =
  local X/Y/Z, global X/Y/Z (GX = 4, GY = 5), projected X/Y/Z.
- `CreateNewPrimaryLoadEx(title, 22)` = load type None (as the twin-cell file).
- Material: `CreateIsotropicMaterialProperties(name, E, nu, G, density, alpha, damp)`, then
  `AssignMaterialToMember` after all `AssignBeamProperty` calls.

## Decisions (keep updated)

- 17 Oct (replaces 16 Oct): base slab wall centreline to wall centreline, **no overhang**. Only the base
  is split. Nodes 1–4 corners (1 BL, 2 TL, 3 TR, 4 BR), 5–6 base at the inner wall faces (tw/2 from
  the corners) = "junction", 7.. N intermediate across the clear span (s = B/(N+1)).
  Members: 1 top slab (2→3), 2 left wall (1→2), 3 right wall (4→3), 4.. base pieces left→right.
  Created explicitly with CreateNode/CreateBeam. Origin = bottom-left corner.
- 16 Oct: concrete density 25 via user-defined material named CONCRETE (as twin-cell DEFINE MATERIAL).
- 17 Oct: exactly 3 supports, K = 40 × FOS × SBC × tributary × strip; compression-only.
  Tributary: end = tw/2 + tw/4 (outer half wall added), junction = tw/4 + s/2, intermediate = s;
  sum = B + 2 tw. Releases (user confirmed 17 Oct, = twin-cell): end FX FZ fixed + KFY
  (FIXED BUT MX MY MZ KFY); junction and intermediate only KFY (FIXED BUT FX FZ MX MY MZ KFY).
- 16 Oct: load cases 1 DL, 2 SIDL max(a,b), 3 EP, 4 LS both, 5 LS one side (left), 6 braking
  (joint FX at top-left corner), 7 water inside (walls + base; base CONFIRMED 31 Oct). Vehicles next session.
- Load combinations: study/explain only (not implemented).
- **REMIND THE USER at the start of Stage 4 (combinations)** – they asked on 31 Oct:
  1. SIDL: keep one case (max a/b) or split into barrier+fill (x1.35) and wearing coat (x1.75)?
  2. Water case 7: which ULS/SLS combinations include it, and with which factors?
- 31 Oct: next = vehicle loads, pilot 70R wheeled; impact factor (IRC:6 cl 208) applied per vehicle
  case. User is sharing their 70R intensity sheet; method discussed in chat first, code after.
- 31 Oct: IRC:112 Annex B-3 — l0 = c/c of walls = model.L (cl 7.6.1.1); b = width of top slab
  perpendicular to l0 (culvert out-to-out length along the road) = NEW INPUT of the vehicle stage.
  Code PDFs are in `IRC codes/` (IRC:112-2020, IRC:6-2017).
- 31 Oct: vehicle loads live in a REUSABLE package `02_Python/irc_live_load/` (no STAAD, no culvert
  logic): vehicles.py (IRC vehicles as data), deck_slab.py (IRC:112 B-3 + IRC:6 cl 208 per axle),
  moving_load.py (steps the WHOLE vehicle both ways, keeps only the worst SAG / HOG / SHEAR).
  70R wheeled 'L' type done (L/M/N = 70R wheel arrangements in IRC:6 Fig. 1, not crash barriers).
  Contact length from Annex A (tread = 0.41-0.05 = 0.36; 17 t axle -> 0.224 m); override allowed
  (twin Excel used 0.263). Axle counts only if its centre is on the span. Reproduces twin Excel
  Case 3 exactly (44.83 kN/m2). Culvert STAAD stage + EDRC sheet for it: not built yet.

## Folder map

```
Box Culvert Design/
├── setup.bat, run.bat, build_loadcalc.bat, CLAUDE.md, SETUP_NOTES.md (from the PM tool project)
├── Culvert_Design_Automation/
│   ├── 00_README.md, 01_Plan/, 03_Loads/, 04_Open_Questions.md
│   ├── 02_Python/culvert_tool/   run.py staad_api.py model.py stage1..3 build_loadcalc_excel.py edrc_sheet.py
│   ├── 02_Python/irc_live_load/  reusable IRC vehicle loads (vehicles, deck_slab, moving_load)
│   └── 05_Output/                Load_Calculation_Single_Cell.xlsx
├── Load calculation of twin cell/   reference Excel (method only)
├── Staad file for twin cell/        reference STAAD (method only, read-only)
└── MySTAADLibrary/                  user's pywin32 OpenSTAAD wrapper (results helpers – useful for Stage 5)
```
