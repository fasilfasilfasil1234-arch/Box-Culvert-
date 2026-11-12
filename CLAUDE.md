# CLAUDE.md – Box Culvert Design Automation (single cell)

Python tool that models a **single-cell RCC box culvert** in STAAD.Pro through OpenSTAAD
(`comtypes`), writes the load calculation in the **EDRC Excel format**, and later designs to
IRC:112. User: Muhammed Fasil (structural engineer). At session start read the files marked
"read at session start" in **Project files** below.

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

## Decisions

All decisions (newest first, superseded ones marked): `Culvert_Design_Automation/01_Plan/DECISIONS.md`.

## Project files

Paths are under `Culvert_Design_Automation/` unless they start at the project root.

| File | What | When to read it |
|---|---|---|
| `01_Plan/DECISIONS.md` | all decisions | check before changing any modelling or loading rule |
| `01_Plan/Master_Planning.md` | stage status, next steps and folder tree | read at session start |
| `04_Open_Questions.md` | open items and Stage 4 reminders | read at session start |
| `03_Loads/Load_Cases_v1.md` | load cases 1–7 | read when working on `stage3_loads.py` |
| `03_Loads/Vehicle_Loading_IRC.md` | vehicle loading rules | read when working on `irc_live_load/` |
| `02_Python/README.md` | how to set up and run the tool | when setting up or running |
| `SETUP_NOTES.md` (project root) | pattern source only (other project, pywin32) | only for .bat / venv patterns |
| `01_Plan/Project_Plan.pdf` | historic 16 Oct snapshot | don't use for current rules |

Folder tree: see `01_Plan/Master_Planning.md` (the only folder tree in the project).
