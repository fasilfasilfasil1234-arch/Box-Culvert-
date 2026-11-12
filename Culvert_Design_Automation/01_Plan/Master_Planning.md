# Master planning – Box Culvert Design Automation (single cell)

**Goal:** type a single-cell RCC box culvert's size and loads once, and get the STAAD.Pro model
(via Python + OpenSTAAD), the load calculation in the EDRC Excel format, the IRC:112 design and
an AutoCAD section drawing.

Updated 12 Nov 2026. All decisions: `01_Plan/DECISIONS.md`. Open items: `04_Open_Questions.md`.
Live plan with comments (16 Oct version): https://claude.ai/code/artifact/1e7becd1-8e0f-4a8d-8b37-02e38864aa70

---

## Stage status

| Stage | What | Files | Status |
|---|---|---|---|
| 1 | Geometry, sections, material | `culvert_tool/stage1_geometry.py` | **Done.** 17 Oct version: 4 corners, single members for the top slab and walls, base split at the wall faces plus N intermediate nodes, density 25. Ran successfully in STAAD on 17 Oct. |
| 2 | Soil springs (3 supports) | `culvert_tool/stage2_springs.py` | **Done.** Ran successfully in STAAD on 17 Oct; 13 of 13 supports read back OK. Compression-only is still the manual `SPRING COMPRESSION` line. |
| 3 | Load cases 1–7 | `culvert_tool/stage3_loads.py` | **Done.** Ran successfully in STAAD on 17 Oct; water with Hw = 3 m also checked. |
| 3 | Load calculation sheet (EDRC) | `culvert_tool/build_loadcalc_excel.py` → `05_Output/Load_Calculation_Single_Cell.xlsx` | **Done.** 0 formula errors; 18 of 18 values cross-checked VERIFIED. |
| – | Vehicle loads (reusable) | `02_Python/irc_live_load/` | **Half-done.** Built 31 Oct: 70R wheeled L type, the whole-vehicle position search, and the IRC:112 B-3 / IRC:6 cl 208 rules. Reproduces the twin-cell Excel exactly. The culvert STAAD stage and the EDRC sheet for vehicles are not built yet; the stage number is open. |
| 4 | Load combinations (REPEAT LOAD) | – | Studied and explained on 16 Oct; **not implemented.** The Stage 4 reminders are in `04_Open_Questions.md`. |
| 5 | Run and extract results | – | Later. `MySTAADLibrary` results helpers can be reused. |
| 6 | Design (IRC:112-2020) | – | Later. |
| 7 | Detailing and AutoCAD drawing | – | Later. |
| – | Input window | – | After all stages are verified. |

## Next steps

1. You answer the four vehicle-stage inputs (slab width b, effective depth d, contact length
   0.224 or 0.263 m, stage numbering) and share your 70R intensity sheet.
2. Build the vehicle STAAD stage (SAG / HOG / SHEAR load cases for 70R wheeled) and its EDRC sheet.
   Check them against your sheet.
3. Add the other vehicles: 70R bogie, 70R tracked, Class A 1-lane and 2-lane, and the 70R M and
   N wheel types. Replace the braking placeholders with real vehicle values.
4. Stage 4 combinations. Start by asking the two Stage 4 reminders (SIDL split; water in
   combinations).

## Folder tree (the only one in the project)

```
Box Culvert Design/
├── CLAUDE.md                    rules for Claude + list of project files
├── SETUP_NOTES.md               setup pattern from the PM_Interaction_Tool project
├── setup.bat                    one-time: .venv + comtypes, openpyxl, pillow
├── run.bat                      runs the STAAD stages (STAAD open with a blank saved file)
├── build_loadcalc.bat           writes the EDRC load calculation Excel
├── Culvert_Design_Automation/
│   ├── 01_Plan/
│   │   ├── DECISIONS.md         all decisions, newest first
│   │   ├── Master_Planning.md   this file
│   │   └── Project_Plan.pdf     historic snapshot, 16 Oct – some details superseded, see DECISIONS.md
│   ├── 02_Python/
│   │   ├── README.md            how to set up and run the tool
│   │   ├── culvert_tool/        run.py, staad_api.py, model.py,
│   │   │                        stage1_geometry.py, stage2_springs.py, stage3_loads.py,
│   │   │                        build_loadcalc_excel.py, edrc_sheet.py, lt_logo.png
│   │   ├── irc_live_load/       __init__.py, vehicles.py, deck_slab.py, moving_load.py (reusable)
│   │   └── legacy_reference/    stage2_springs_OLD_standalone.py (reference only, do not run)
│   ├── 03_Loads/
│   │   ├── Load_Cases_v1.md     load cases 1–7
│   │   └── Vehicle_Loading_IRC.md  vehicle loading rules (IRC:6, IRC:112 Annex B-3)
│   ├── 04_Open_Questions.md     open items and Stage 4 reminders
│   ├── 05_Output/
│   │   └── Load_Calculation_Single_Cell.xlsx
│   └── _archive/                retired notes (Decisions_Log.md, Important_Changes_2026-10-16.md, 00_README.md)
├── IRC codes/                   IRC 112 2020 CONCRETE ROAD BRIDGE.pdf, IRC 6 2017.pdf
├── Load calculation of twin cell/  reference Excel (method only)
├── Staad file for twin cell/    reference STAAD (method only, read-only)
├── Single cell staad file/      your single-cell STAAD model from the test runs (Box culvert.STD)
├── MySTAADLibrary/              your pywin32 OpenSTAAD wrapper (results helpers, for Stage 5)
└── LinkedIn_Post/               post and voice-over text
```

---

## Summary of `Project_Plan.pdf`

**Status: historic snapshot, 16 Oct – some details superseded, see DECISIONS.md.** For example,
"fix FX at one node", the base slab to the outer wall faces, and the 0.10 m end tributary are
all replaced by the 17 Oct decisions.

Scope of version 1: single-cell RCC box, 1 m strip, line model on Winkler springs, IRC:6-2017
loads, IRC:112 design, one standard cross-section drawing. Python drives STAAD.Pro through
OpenSTAAD (`comtypes`); the drawing is written as DXF (`ezdxf`) or through AutoCAD COM.

| Stage | Plan in short |
|---|---|
| 1 Geometry and model | Closed 2D frame on the centrelines, 1 m strip. Rectangular sections (depth = thickness, width 1 m) and concrete; plot to confirm before loading. |
| 2 Soil springs | ks = 40 × FOS × SBC (Bowles), K = ks × tributary × 1 m. After analysis, check base pressure ≤ SBC. |
| 3 Loads (IRC:6-2017) | One tick-box line per load (see the clause list below). Box empty / box full, surcharge one side / both, live load for max sagging, max hogging and max shear. |
| 4 Load combinations (IRC:6 Annex B) | One factor table (ULS basic, SLS rare / frequent / quasi-permanent) multiplied out automatically. With compression-only springs: REPEAT LOAD. |
| 5 Run and extract | OpenSTAAD over COM; forces at the wall faces, mid-span and d from the face for the slabs; top, bottom and maximum for the walls (with N); enveloped. |
| 6 Design (IRC:112-2020) | Three zones (top slab, walls, base slab). Bending (Section 8), walls with axial force, shear without stirrups (10.3.2), minimum steel (16.5.1.1), stress limits (12.2), crack width (12.3.4, Table 12.1), cover (14.3.2, Table 14.2), base pressure ≤ SBC. You accept or change the proposed bars. |
| 7 Detailing and AutoCAD | Drawn from the accepted bar table: outline, bars by mark, distribution dots, labels, dimensions, bar bending schedule; DXF first, AutoCAD COM optional (full AutoCAD only). |

**IRC:6-2017 clause list (plan's load table)**

| # | Load | Rule | Clause |
|---|---|---|---|
| 1 | Self-weight | RCC 2.5 t/m³ | 203 |
| 2 | Wearing coat / SIDL | asphalt 2.2 t/m³ | 203 |
| 3 | Earth fill on top | compacted earth 2.0 t/m³ × fill depth | 203 |
| 4 | Earth pressure | at rest, K0 = 1 − sin φ | 214.1.3 |
| 5 | LL surcharge | K × γ × 1.2 m | 214.1.1.3 |
| 6 | Vehicle live load | 70R, Class A, SV if needed; lanes by carriageway | 204.1, Table 6, 204.5 |
| 7 | Impact | Class A 4.5/(6+L); 70R tracked 25 → 10 %; 70R wheeled 25 %; halved for fill ≥ 0.6 m | 208.2, 208.3, 208.6, 204.5.4 |
| 8 | Braking | 20 % of first train, no impact (the tool applies it as the twin-cell file does: a joint load at the top-left corner) | 211.2, 211.3, 211.7 |
| 9 | Water | inside (box full); hydrostatic behind the walls if there is no drainage | 214.3, 214.4 |
| 10 | Temperature, shrinkage | shrinkage strain 2 × 10⁻⁴ | 215, 216.3 |
| 11 | Seismic | not needed for culverts up to 10 m span | 218.1.1 |

The plan also lists a 5-phase roadmap with these check tests:
- dead-load reactions equal the self-weight;
- symmetric loads give symmetric results;
- one 4 × 4 box matches your existing STAAD;
- the design matches your sheet for a 4 × 4 and a 4 × 5 box;
- drawing dimensions and bar-schedule totals match.
