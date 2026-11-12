# Decisions log – all project chats

Newest first. "You" = Muhammed Fasil. Items marked *suggested* were Claude's suggestions, not yet confirmed by you.

## 17 Oct 2026 – Corrections after the first STAAD run

- Geometry: base slab wall centreline to centreline, no overhang. Only the base is split.
  Nodes 1-4 corners, 5-6 inner wall faces, 7.. intermediate (s = B/(N+1)). Members 1 top, 2 left wall,
  3 right wall, 4.. base. Example B 5.0, tw 0.4, N 9: x = 0, 0.2, 0.7 ... 5.2, 5.4.
- Springs: end tributary = tw/2 + tw/4 (outer half wall); sum = B + 2tw (5.8 m in the example).
- Releases confirmed: end FX FZ fixed + KFY; junction and intermediate only KFY (= twin-cell).
- `CreateSupportFixedBut` uses 1 = released (opposite of `GetSupportInformation`). The 16 Oct code
  sent the wrong codes; fixed. (The legacy Stage 2 was right for creation.)
- STAAD crashed at `UpdateStructure` after the loads were added; Stage 3 no longer calls it.

## 16 Oct 2026 – Stages 1-3 coded (Claude Code session)

- OpenSTAAD functions verified against the **local** help of STAAD CE 22.00.00.15 (Help\OSAPP); tag [L].
- Twin-cell STAAD read live (read-only): material CONCRETE E 3.1e7, DENSITY 25 (DEFINE MATERIAL);
  supports end = FIXED BUT MX MY MZ KFY, others = FIXED BUT FX FZ MX MY MZ KFY; 14 primary cases (type None),
  64 LOAD COMB (no REPEAT LOAD; linear springs, no SPRING COMPRESSION).
- Release codes: 0 released / 1 fixed / -1 spring in GetSupportInformation (*corrected 17 Oct: Create uses the opposite*).
- Stage 2 default release pattern = twin-cell pattern (*to confirm*, the note above said the reverse).
- No OpenSTAAD compression-only function: manual `SPRING COMPRESSION ... KFY` line, printed by Stage 2.
- Walls get nodes at slab faces, top slab at inner wall faces (as twin-cell). Origin = left outer-face end.
- Braking applied as joint FX at the top-left corner; q, dL per vehicle are placeholders from the twin-cell Excel.
- Water: + gamma_w x Hw on the base by default (`WATER_ON_BASE`, *to confirm*).
- Run setup: setup.bat / run.bat / build_loadcalc.bat; CLAUDE.md holds the project rules.

## 16 Oct 2026 – Session scope and loads (this chat)

- New base slab node layout, with only three supports. See `Important_Changes_2026-10-16.md`.
- Load list for this version: DL, SIDL (max of a/b), earth pressure, LL surcharge on both sides and on one side, braking, and water inside.
- Earth pressure uses the Excel values; the sample STAAD was conservative.
- Seismic is out (flag spans > 10 m). Temperature comes in the next version.
- Vehicle loading has five cases. Each is dispersed through fill/SIDL/wearing coat, b_eff per IRC:112-2020 Annex B-3, then applied as a line load on the 1 m strip. Next session.
- Load calc output goes in your EDRC format.
- Load combinations: study and explain only; no implementation yet.

## 12 Oct 2026 – Code structure ("Stage 1 and 2 Python restructuring")

- One folder, `culvert_tool/`. You click **Run on `run.py`** only.
- `run.py` finds `stageN_*.py` files and runs them in order. It pauses after each stage (Enter = next, Q = stop).
- Shared files: `staad_api.py` (STAAD helpers) and `model.py` (results passed between stages). They change only if a stage needs something new.
- Stage outputs pass to the next stage through `model.py`. Geometry is **not** read back from STAAD.
- New stages are always delivered as **full replacement files**, with a list of which files to add or replace.
- **Stage 1 does not create or save a file.** You open STAAD, set kN-m, save it where you want, and keep it open. The script models into that open file. If the model isn't empty, it stops.

## 12 Oct 2026 – Calculation and report approach ("Automated culvert design planning")

- *Suggested, agreed in principle:* **Python is where each calculation lives; Excel is the report Python writes.** One module per calculation, each module producing one sheet in EDRC format with live formulas, and Python cross-checking every cell. One workbook per culvert, built only from the modules that apply.
- Live-load modules run **before** STAAD: fill depth → 45° dispersion → b_eff (IRC:112 Annex B-3) → pressure per 1 m strip → STAAD load case.
- **Logic comes from your approved Excel** (formulas intact), with IRC codes used as a cross-check. Any mismatch gets flagged, never silently changed.
- Pilot module: **70R wheeled**.

## 11 Oct 2026 – IRC 70R facts ("IRC 70R wheeled vehicles specifications")

- 0.86 m is the dual-tyre width **across** traffic (360 + 140 + 360 mm).
- Contact length along traffic = wheel load ÷ (5.273 kg/cm² × 72 cm tyre width):
  - 17 t axle (8.5 t wheel): ≈ 0.224 m
  - 20 t axle / bogie (10 t wheel): ≈ 0.263 m
- Max single axle 20 t; max bogie 40 t (2 × 20 t at 1.22 m).
- Some offices divide by 86 cm or 76 cm instead. Use your office convention.

## Earlier (28 Sep – 7 Oct 2026) – Original plan chat

- Pipeline: Inputs → STAAD model (OpenSTAAD) → Loads → Run/extract → Design (IRC:112) → Detailing → AutoCAD drawing → Review.
- STAAD is driven **live** through OpenSTAAD + `comtypes`, with STAAD open beside the tool. Each stage adds to the model.
- **Every OpenSTAAD call is verified against Bentley documentation** before use, with source tags [R]/[B]/[H]/[M]/[S] in each file.
- 1 m strip line model; 4 members on the centreline; Winkler springs ks = 40 × FOS × SBC.
- Stage 2 choices then: geometric end spring, FX fixed at one node, compression-only springs. *Spring layout superseded on 16 Oct.*
- Compression-only via OpenSTAAD: function name not confirmed, so it's applied manually for now (One-way Spring tool or `SPRING COMPRESSION … KFY`).
- Drawings: start with `ezdxf` (DXF), with optional AutoCAD COM later. AutoCAD LT has no ActiveX.
- Desktop UI comes later. The module structure is built now so the UI can plug in.
