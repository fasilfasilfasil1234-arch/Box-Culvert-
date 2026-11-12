# Python – how to use

## `culvert_tool/` – the live tool (copy this whole folder to your PC)

| File | What it is | You edit it? |
|---|---|---|
| `run.py` | **Click Run on this.** It finds `stageN_*.py` files and runs them in order, pausing after each one. | Never |
| `staad_api.py` | Shared STAAD helpers: connect, units, clear error messages, array passing | Only when a delivery says so |
| `model.py` | The "results form" passed from stage to stage | Only when a delivery says so |
| `stage1_geometry.py` | Stage 1: frame, sections, material (density 25) | INPUTS block only |
| `stage2_springs.py` | Stage 2: three spring supports | INPUTS block only |
| `stage3_loads.py` | Stage 3: load cases 1-7 | INPUTS block only |
| `build_loadcalc_excel.py` | Load calculation sheet (EDRC format) - run `build_loadcalc.bat` | No |
| `edrc_sheet.py`, `lt_logo.png` | EDRC format module (copy from the PM tool project) | No |

**Setup (once):** double-click `setup.bat` in the project root (creates `.venv`, installs comtypes, openpyxl, pillow).

**Each run**
1. Open STAAD, start a blank file in **kN and m**, save it where you want, and keep it open.
2. Edit the INPUTS block of the stage files.
3. Double-click `run.bat`. Check STAAD after each pause (Enter = next stage, Q = stop).
   After Stage 2, paste the printed `SPRING COMPRESSION ... KFY` line into the STAAD editor.
4. Save the model in STAAD yourself. The scripts never save.

**Adding a stage:** drop in the new `stageN_*.py`. Each delivery says exactly which files to add or replace.

## Status

| Stage | File | Status |
|---|---|---|
| 1 | `stage1_geometry.py` | 17 Oct version: 4 corners, single top/wall members, base split at wall faces + N intermediate nodes, density 25. **Re-run in STAAD pending** |
| 2 | `stage2_springs.py` | 16 Oct: three supports, read-back check. Mock-tested; **run in STAAD pending** |
| 3 | `stage3_loads.py` | 16 Oct: cases 1-7, read-back check. Values match the twin-cell Excel. **Run in STAAD pending** |
| 4+ | – | Combinations: study only for now |

## `legacy_reference/`

`stage2_springs_OLD_standalone.py` is the old standalone Stage 2, kept **for reference only**. Its `CreateSupportFixedBut` codes (1 = released) were right; note that `GetSupportInformation` reads them back the opposite way (0 = released). **Do not put it in `culvert_tool/`**, or `run.py` would pick it up.

## OpenSTAAD verification tags used in every file

- [L] Local OpenSTAAD help of your STAAD CE 22.00.00.15 (Help\OSAPP) - first source
- [T] Tested live on your PC (read-only)
- [R] OpenSTAAD Reference Manual
- [B] Bentley Python help page
- [H] STAAD.Pro Help
- [M] Bentley openstaad-mcp notes
- [S] secondary source; confirm in local help
