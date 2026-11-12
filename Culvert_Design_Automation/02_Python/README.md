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

## `irc_live_load/` – reusable IRC vehicle loads (no STAAD, no culvert logic)

| File | What it is | You edit it? |
|---|---|---|
| `vehicles.py` | IRC vehicles as data (70R wheeled L type so far) | Only when a delivery says so |
| `deck_slab.py` | One axle → line load on a 1 m strip (IRC:112 Annex B-3, IRC:6 cl 208) | Only when a delivery says so |
| `moving_load.py` | Steps the whole vehicle across a span, keeps the worst SAG / HOG / SHEAR positions | Only when a delivery says so |
| `__init__.py` | Makes the folder importable as `irc_live_load` | Never |

**Setup (once):** double-click `setup.bat` in the project root (creates `.venv`, installs comtypes, openpyxl, pillow).

**Each run**
1. Open STAAD, start a blank file in **kN and m**, save it where you want, and keep it open.
2. Edit the INPUTS block of the stage files.
3. Double-click `run.bat`. Check STAAD after each pause (Enter = next stage, Q = stop).
   After Stage 2, paste the printed `SPRING COMPRESSION ... KFY` line into the STAAD editor.
4. Save the model in STAAD yourself. The scripts never save.

**Adding a stage:** drop in the new `stageN_*.py`. Each delivery says exactly which files to add or replace.

## Status

Stage status and next steps: see `../01_Plan/Master_Planning.md`.

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
