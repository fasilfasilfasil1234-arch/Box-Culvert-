# Load cases – version 1 (to implement and verify this session)

Single cell, 1 m strip. Units: kN, m. Formulas show the method. Exact rounding and order follow your Excel once it is shared.

| Case | Title | Applied on | Load shape | Source of value |
|---|---|---|---|---|
| 1 | Dead load | all members | STAAD SELFWEIGHT Y −1 | density 25 kN/m³ |
| 2 | SIDL (max of a, b) | top slab | UDL, kN/m | calc below |
| 3 | Earth pressure | both walls (outer faces) | trapezoidal, kN/m | Excel method |
| 4 | LL surcharge – both sides | both walls | uniform, kN/m | Excel method |
| 5 | LL surcharge – one side | one wall | uniform, kN/m | Excel method |
| 6 | Braking | top slab | as sample STAAD | Excel value |
| 7 | Water inside cell | both walls (inner faces) | triangular, kN/m | new |

## Case 2 – SIDL / wearing coat / fill / crash barrier

Let the layers above the top slab be wearing coat, SIDL and fill, with thickness hᵢ and density γᵢ. The layer pressure is p = Σ hᵢ·γᵢ (kN/m²).

- **(a)** w_a = p × 1.0 (kN/m)
- **(b)** Crash barrier width b, area A_cb: w_b = A_cb·γ_conc + p × (1.0 − b)

Example with b = 0.5 m: barrier weight over its 0.5 m, plus the layer pressure over the other 0.5 m.

**STAAD gets max(w_a, w_b).** The EDRC sheet prints both and marks the governing one.

## Case 3 – Earth pressure

- At-rest coefficient K0 = 1 − sin φ (IRC:6 cl. 214.1.3, closed box).
- Pressure at depth z below the finished level: p(z) = K0·γ_soil·z.
- It is applied to both walls between the top and bottom centreline nodes, pushing inward, with the same magnitude on each side.
- The values come from the Excel method. The sample STAAD's rounded 5 / 49 kN/m² is not used; the calculated values (e.g. 4.59 / 48.34) are.

## Cases 4 and 5 – Live-load surcharge

- p_s = K·γ_soil·1.2 m (IRC:6 cl. 214.1.1.3), uniform over the wall height.
- Case 4 loads both walls. Case 5 loads one wall only.

## Case 6 – Braking

- Positions as in the sample STAAD; values as in the Excel (IRC:6 cl. 211).

## Case 7 – Water inside the cell (new)

- H = water depth above the **top** of the base slab (input).
- Wall coordinates run from the base centreline (y = 0). The top of the base slab is at y = t_bot/2.
- Triangular load on each inner wall face:
  - 0 kN/m at y = t_bot/2 + H
  - γw·H kN/m at y = t_bot/2 (γw ≈ 10 kN/m³)
- Direction: outward on both walls (water pushes out).
- **Confirmed 31 Oct:** γw·H also acts downward on the base slab, between the inner wall faces (DECISIONS D31-1).

## Not in this version

- Seismic: the tool flags spans above 10 m.
- Temperature: next version.
- Vehicle live load: see `Vehicle_Loading_IRC.md`.

## Combinations

- Study the sample STAAD combinations and explain them only.
- With compression-only springs, combinations become primary cases with **REPEAT LOAD**.
