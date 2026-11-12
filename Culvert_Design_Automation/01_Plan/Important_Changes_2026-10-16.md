# Important changes – 16 Oct 2026

These decisions are **final** unless marked *To confirm*. They override the earlier plan where they differ. The stage numbering is unchanged.

---

## Stage 1 – Modelling and properties

> **Superseded 17 Oct 2026:** the base slab does NOT extend past the walls. It runs wall centreline
> to wall centreline (L = B + tw). Nodes: corners 1–4, inner-face nodes 5–6 (tw/2 from the corners),
> N intermediate nodes across the clear span. Top slab and walls are single members. The end spring
> carries tw/2 + tw/4, so the springs cover B + 2tw. See `Decisions_Log.md` (17 Oct).

**Base slab layout (overrides the old "split the base into n equal segments" rule)**

- The base slab runs to the **outer face** of the walls. It extends t_wall/2 past each wall centreline.
- The wall–slab **junction nodes** sit on the wall centrelines.
- Input: **number of intermediate spring nodes (N)**. These are equally spaced between the two junction nodes.

```
Example: centreline span 5.0 m, t_wall 0.4 m, N = 9

 x (m):  0    0.2   0.7  1.2  1.7  2.2  2.7  3.2  3.7  4.2  4.7   5.2   5.4
         |-----|-----|----|----|----|----|----|----|----|----|-----|-----|
        END  JUNC  <-------------- 9 intermediate @ 0.5 m ------------> JUNC  END
 Effective base length = 5.0 + 0.4 = 5.4 m
```

- **Concrete density = 25 kN/m³.** Set it the same way the sample STAAD file does.
- The twin-cell Excel and STAAD files show the **method only**. The tool stays **single cell**.
- **Code status:** `stage1_geometry.py` (12 Oct version) does **not** include this yet. It needs two short end members on the base slab and the new node rule.

## Stage 2 – Springs and supports

**Only three supports are created in STAAD. No extra supports.**

| Support | Nodes | Spring / releases | Tributary length (example) |
|---|---|---|---|
| End | 2 outer-face nodes (x = 0, 5.4) | KFY; FX and FZ released | 0.10 m |
| Wall junction | 2 junction nodes (x = 0.2, 5.2) | KFY only | 0.10 + 0.25 = 0.35 m |
| Intermediate | all N intermediate nodes | KFY only | 0.50 m |

- K = ks × tributary length × 1 m, with ks = 40 × FOS × SBC (kN/m³).
- Tributary length = half the gap on each side of the node.
- Check: tributary lengths add up to the effective base length (2×0.10 + 2×0.35 + 9×0.50 = 5.4 m ✔).
- Springs stay **compression-only** (decided earlier).
- *To confirm:* "release X and Z" on the end supports means FX and FZ released and everything else fixed. "FY only" on the other two means all other directions are fixed. This replaces the earlier "fix FX at one node" choice.
- **Code status:** Stage 2 will be rewritten for this layout, inside the `culvert_tool` structure.

## Stage 3 – Loads (this version)

| # | Load case | How |
|---|---|---|
| 1 | Dead load | STAAD SELFWEIGHT command (density 25 kN/m³) |
| 2 | SIDL / fill / wearing coat / crash barrier | Calculate both (a) and (b) below; load the **max** into STAAD; show both in the calc sheet |
| 3 | Earth pressure | Excel method, on **both** walls |
| 4 | LL surcharge, both sides | Same as Excel / sample STAAD |
| 5 | LL surcharge, one side | Same as Excel / sample STAAD |
| 6 | Braking | Positions as in sample STAAD, values as in Excel |
| 7 | Water inside the cell | **New** (not in the Excel or STAAD) – see below |

**SIDL – two cases, max goes to STAAD**

- **(a)** SIDL / wearing coat / fill over the full 1 m strip: w_a = Σ(hᵢ × γᵢ) × 1.0 m → UDL (kN/m).
- **(b)** Crash barrier width b (e.g. 0.5 m): w_b = (barrier area × γ_conc) + Σ(hᵢ × γᵢ) × (1.0 − b) → UDL (kN/m).
- STAAD gets max(w_a, w_b). The calc sheet shows both.

**Earth pressure:** the Excel is correct. The sample STAAD used rounded, conservative values (5 / 49 vs 4.59 / 48.34 kN/m²). The tool loads the **calculated** values.

**Water inside the cell:** a triangular load on both inner wall faces. It is 0 at height H above the top of the base slab and rises to γw·H at the top of the base slab, which is t_bot/2 above the base centreline node.
- *To confirm:* does this case also put γw·H downward on the base slab?

**Not in this version**
- Seismic: not applied. The tool **flags spans above 10 m**.
- Temperature: handled separately in the next version.

**Vehicle live load:** next session. There are five cases (see `03_Loads/Vehicle_Loading_IRC.md`). Explain first, implement once agreed.

**Output format:** the load calculation is produced in **your EDRC format**, not the twin-cell Excel's layout.

## Stage 4 – Load combinations

- This session: study the combinations in the sample STAAD file and explain them. **No implementation yet.**
- Because the springs are compression-only, combinations are built as **primary cases with REPEAT LOAD**, not LOAD COMBINATION (STAAD TR.27.5).

## Files still needed from you

- Twin-cell **load calculation Excel** (formulas intact).
- Sample twin-cell **STAAD file** (.std).
- **Design docs** referred to in the 16 Oct note.
- For vehicles: the **STAAD model and Excel sheet for vehicle loading**.
