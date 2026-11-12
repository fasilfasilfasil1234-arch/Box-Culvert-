# Open questions and inputs still needed

## To confirm (blocks Stage 2 / Stage 3 code)

1. **End supports (default now = twin-cell pattern, see Stage 2 INPUTS):** does "release X and Z" mean FX and FZ released and everything else fixed? And does "FY only" on the junction and intermediate supports mean all other directions are fixed? This replaces the old "fix FX at one node".
2. **Water case:** do we also apply γw·H downward on the base slab, or only the wall pressure?
3. ~~Concrete density 25~~ **Answered 16 Oct:** the twin-cell file uses DEFINE MATERIAL (ISOTROPIC CONCRETE, DENSITY 25). Stage 1 does the same.
4. ~~Compression-only via OpenSTAAD~~ **Answered 16 Oct:** your local help (CE 22.00.00.15) has no such function. Stage 2 prints the `SPRING COMPRESSION ... KFY` line to paste.
5. **New:** SIDL as one case (max a/b) loses the twin-cell split (head wall x1.35 / surfacing x1.75). Keep one case, or split into barrier+fill (1.35) and wearing coat (1.75)?

## Remind at Stage 4 (load combinations) – asked by you on 31 Oct

- SIDL as one case (max a/b) or split into barrier + fill (x1.35) and wearing coat (x1.75)?
- Water inside (case 7): which ULS / SLS combinations, which factors?
- (Answered 31 Oct: water also loads the base slab - yes, keep it.)

## Earlier plan questions – status

| Question | Status |
|---|---|
| End spring rule | Superseded – three supports, tributary lengths (16 Oct) |
| Horizontal restraint | Pending – see Q1 above |
| Linear vs compression-only | **Compression-only** |
| FOS in 40 × FOS × SBC | Open |
| Haunches | Open (none for now) |
| Live-load dispersion / effective width | **45° through fill/SIDL/WC; b_eff per IRC:112 Annex B-3**; details from your Excel |
| Vehicle classes | **5 cases:** 70R tracked, 70R bogie, 70R wheeled, Class A 1-lane, Class A 2-lane |
| Temperature & shrinkage | Next version |
| Seismic | Not applied; flag spans > 10 m |
| Exposure class, cover, crack-width combination | Open |
| Walls: bending only or with axial force | Open |
| "Points rebars" meaning | Open |
| STAAD version; full AutoCAD or LT | Open |

## Files still needed

- Twin-cell **load calculation Excel** (formulas intact)
- Sample twin-cell **STAAD .std**
- **Design docs** mentioned on 16 Oct
- **Vehicle loading Excel + STAAD model**
- One finished **drawing + BBS** (for Stage 7)
- Your **EDRC template** (for the report format)
