# Open questions and inputs still needed

Updated 12 Nov 2026. Answered items have moved to `01_Plan/DECISIONS.md`.

## Vehicle stage – inputs needed before it is built

1. **Slab width b** (top slab width perpendicular to l0 = the culvert's out-to-out length along
   the road), for α (b/l0), b_eff ≤ b and the free-edge check. The 31 Oct test used the
   carriageway width 10.25 m as a placeholder.
2. **Effective depth d** of the top slab, for the shear check section (wall face + d). The test
   used 0.30 m.
3. **Tyre contact length:** the code value from IRC:6 Annex A (17 t axle → 0.224 m), or your office
   value 0.263 m (twin-cell Excel)?
4. **Stage numbering:** a new `stage4_vehicle_loads.py`, with the combinations moved to Stage 5?
   (`run.py` only accepts whole stage numbers.)

Also wanted: your **70R intensity sheet** (and the vehicle STAAD model, if any), to check the
tool against it.

## Remind at Stage 4 (load combinations) – asked by you on 31 Oct

- **SIDL:** keep one case (max of a, b), or split into barrier + fill (× 1.35) and wearing coat
  (× 1.75), as the twin-cell file did?
- **Water inside (load case 7):** which ULS / SLS combinations include it, and with which factors?

## Still open from the plan

| Question | Status |
|---|---|
| FOS in 40 × FOS × SBC | Open. The tool uses 2.5 (twin-cell Excel, IRC:78 cl 706.3.1.1) as the default |
| Haunches | Open (none for now) |
| Exposure class, cover, crack-width combination | Open |
| Walls: bending only or with axial force | Open |
| "Points rebars" meaning | Open |
| Full AutoCAD or AutoCAD LT | Open |
| STAAD version | **STAAD.Pro CONNECT Edition 22.00.00.15** (known) |

## Files still needed

- **Vehicle loading Excel + STAAD model** (see above)
- **Design docs** mentioned on 16 Oct
- One finished **drawing + BBS** (for Stage 7)
- Your **EDRC template**, if it differs from the format the tool already writes
