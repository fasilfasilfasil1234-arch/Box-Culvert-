# HANDOFF – last session state (12 Nov 2026)

## Goal
A Python tool for a single-cell RCC box culvert: it models the box in STAAD.Pro through OpenSTAAD
(comtypes), writes the EDRC load-calc Excel, and later does the IRC:112 design and the AutoCAD drawing.

## Current state
Full stage table: `Master_Planning.md`. Decisions with reasons: `DECISIONS.md`.

**Done**
- **Stages 1–3** (geometry, 3 springs, load cases 1–7) ran successfully in STAAD on 17 Oct. Water
  with Hw = 3 m was also checked in STAAD.
- **EDRC load-calc Excel** built: 0 formula errors, 18 of 18 cross-checks VERIFIED.
- **`irc_live_load/`** (reusable, built 31 Oct): 70R wheeled L type. It steps the whole 100 t
  vehicle both ways and keeps the worst SAG / HOG / SHEAR positions. It reproduces the twin-cell
  Excel Case 3 exactly (44.83 kN/m²).

**Half-done**
- The vehicle **STAAD stage** and its **EDRC sheet** are not built yet.

**Discussed and agreed with you**
- Base slab from wall centreline to wall centreline, no overhang. Only the base is split.
- End tributary tw/2 + tw/4; end FX and FZ fixed.
- Water also loads the base slab.
- l0 = c/c of the walls, and b = slab width (a new input).
- 70R clearance 1.2 m; Class A f = 0.15 m, with g from Table 3.
- Slab extension beyond the barrier: an input, default 0.
- L, M and N are 70R wheel types (L built now).
- Whole-vehicle search, with only the worst positions going to STAAD and the sheet.
- Vehicle code kept as a separate reusable package.

**Folder reorganisation (12 Nov)**
- All decisions were merged into `DECISIONS.md`; `Master_Planning.md` now holds the status, next
  steps and the only folder tree.
- `CLAUDE.md` now lists the project files instead of holding decisions.
- `04_Open_Questions.md` was trimmed to the truly open items.
- Archived to `Culvert_Design_Automation/_archive/`: `Decisions_Log.md`,
  `Important_Changes_2026-10-16.md`, `00_README.md`.

## Files touched (not a git repo)
- `culvert_tool/`: stage1_geometry.py, stage2_springs.py, stage3_loads.py, model.py,
  staad_api.py, build_loadcalc_excel.py, edrc_sheet.py.
- `02_Python/irc_live_load/`: vehicles.py, deck_slab.py, moving_load.py, `__init__.py`.
- Project root: setup.bat, run.bat, build_loadcalc.bat, CLAUDE.md, SETUP_NOTES.md.
- `01_Plan/`: DECISIONS.md, Master_Planning.md, HANDOFF.md.
- 04_Open_Questions.md, `03_Loads/*.md`, 02_Python/README.md.

## Next 3 steps
1. Get your answers to the **last unanswered question**, the four vehicle-stage inputs:
   - (a) slab width b along the road (10.25 m carriageway used as a placeholder);
   - (b) top-slab effective depth d for the shear section (0.30 m used);
   - (c) tyre contact length: 0.224 m (IRC:6 Annex A) or 0.263 m (your twin-cell Excel);
   - (d) stage numbering: new `stage4_vehicle_loads.py` and combinations moved to Stage 5?

   Also ask for your 70R intensity sheet.
2. Build the vehicle STAAD stage (SAG / HOG / SHEAR load cases, 70R wheeled) and its EDRC sheet,
   and check them against your sheet.
3. Add the other vehicles (70R bogie, tracked, Class A, the M and N types) and replace the braking
   placeholders. Then Stage 4 combinations: ask the two Stage 4 reminders first.

## Dead ends
- **Using the `CreateSupportFixedBut` help text code (0 = released):** every support came out
  inverted. Creation uses 1 = released.
- **Calling `UpdateStructure` after adding loads** crashed STAAD (RPC failed). It has been removed.
- **Base slab extended to the outer wall faces, with many nodes on the top slab and walls:**
  rejected by you. You wanted single members and no overhang.
- **Counting axles whose centre sits over a wall:** it gave an inflated 5 cm load sliver. Only
  axles centred on the span count.

## Open questions
- The four vehicle inputs above (the last unanswered question).
- Stage 4: keep SIDL as one case or split it (× 1.35 / × 1.75)? Which combinations include water,
  and with which factors?
- FOS (default 2.5), haunches, exposure / cover / crack combination, walls with axial force,
  "points rebars", full AutoCAD or LT. All are listed in `04_Open_Questions.md`.
- A stale pointer to the archived `Important_Changes` is left in
  `legacy_reference/stage2_springs_OLD_standalone.py`; it wasn't fixed because it's a code file.
