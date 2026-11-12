# Vehicle live loading – how it works and how the tool will do it

**Status:** explanation only. Nothing is implemented yet. We agree on this first; then the logic is lifted from **your vehicle-loading Excel and STAAD model**. Your sheet is the source and the IRC codes are the cross-check. Wherever this note says *verify*, the figure was not readable from the IRC:6 text extract I could reach, so take it from your Excel or your IRC:6 copy.

---

## 1. The five vehicle cases (your list, 16 Oct)

| # | Case | What it is | Key figures |
|---|---|---|---|
| V1 | **IRC Class 70R tracked (70T)** | 70 t tracked vehicle on two tracks | Each track about 0.84 m wide × 4.57 m long; tracks about 2.06 m c/c *(verify, IRC:6 Fig. 1)* |
| V2 | **IRC Class 70R wheeled – bogie (40T)** | Two 20 t axles not more than 1.22 m apart (IRC:6 Fig. 1, Note 3) | 4 wheels × 10 t; contact ≈ 0.86 m (across) × 0.263 m (along) |
| V3 | **IRC Class 70R wheeled** | Full 100 t, 7-axle vehicle | Axles 8, 12, 12, 17, 17, 17, 17 t; spacings 3.96, 1.52, 2.13, 1.37, 3.05, 1.37 m (checked on IRC:6 Fig. 1, 31 Oct). 17 t wheel contact ≈ 0.86 × 0.224 m |
| V4 | **IRC Class A – single lane** | One train of Class A vehicles | Axles 2.7, 2.7, 11.4, 11.4, 6.8, 6.8, 6.8, 6.8 t; spacings 1.1, 3.2, 1.2, 4.3, 3.0, 3.0, 3.0 m *(verify)* |
| V5 | **IRC Class A – two lane** | Two Class A trains side by side | Gap between trains g, and kerb clearance f (below) |

**Class A wheel contact (IRC:6 Table 2), B along traffic × W across traffic:**
- 11.4 t axle: 250 × 500 mm
- 6.8 t axle: 200 × 380 mm
- 2.7 t axle: 150 × 200 mm

Transverse wheel spacing is 1.8 m c/c *(verify)*.

**Clearances (IRC:6 Table 3 and Fig. 1 notes)**
- Class A: kerb to outer wheel edge **f = 150 mm**. Gap between two trains **g = 1.2 m** where clear width is above 6.1 m; between 0.4 and 1.2 m for 5.3–6.1 m.
- 70R: kerb to outer edge of wheel or track **C = 1.2 m**. Minimum carriageway 5.3 m.

**Which cases apply (IRC:6 Table 6)**
- Carriageway under 5.3 m: one lane of Class A, plus 500 kg/m² on the rest of the width.
- Carriageway 5.3 m to under 9.6 m: **one lane of 70R OR two lanes of Class A**.

So for a two-lane road, V1, V2 and V3 are each checked alone, and V5 is the Class A alternative. V4 governs only for narrow single-lane carriageways, or as a check.

**70R tyre contact (from the 11 Oct chat)**
- IRC:6 gives max tyre pressure 5.273 kg/cm².
- Contact length = wheel load ÷ (5.273 × 72 cm), counting only the two 36 cm tyres and not the 14 cm gap.
- 8.5 t wheel → 0.224 m; 10 t wheel → 0.263 m.
- Your office may divide by 86 or 76 cm instead. Use your Excel's convention.

---

## 2. Impact factor (IRC:6 cl. 208), spans under 9 m

| Vehicle | Impact | Clause |
|---|---|---|
| Class A (RCC) | 4.5 / (6 + L) | 208.2 |
| 70R tracked | 25% up to 5 m span, reducing linearly to 10% at 9 m | 208.3(a) |
| 70R wheeled (incl. bogie) | 25% | 208.3(a) |
| **Fill ≥ 0.6 m (incl. road crust)** | **half** of the above | 208.6 |

> Correction: the plan's Stage 3 table had only the wheeled 70R rule. It now also shows the tracked rule (25 → 10%).

---

## 3. From a wheel to a STAAD line load – step by step

```
 Wheel/track load P (+ impact)
        │
        ▼
 (1) Contact patch:   B (along span) × W (across)
        │   45° dispersion through wearing coat + SIDL + fill  (depth h)
        ▼
 (2) Dispersed patch: B' = B + 2h   (along span)
                      W' = W + 2h   (across, = b1 in Annex B-3)
        │
        ▼
 (3) Effective width across traffic, IRC:112-2020 Annex B-3:
        b_eff = α · a · (1 − a / l0) + b1
        a  = distance of load centre from the nearer support (along span)
        l0 = effective span of the top slab
        α  = from the Annex B-3 table (depends on B/l0 and on
             simply supported vs continuous) – take from your Excel
        Limits: b_eff ≤ available width; near a free edge,
                b_eff = b_eff/2 + distance to edge;
                overlapping widths of adjacent wheels are combined.
        │
        ▼
 (4) Load on the 1 m design strip:
        w = P(1+IF) / (b_eff × B')     [kN/m per 1 m strip]
        applied as a partial UDL of length B' on the top-slab members
        │
        ▼
 (5) One STAAD primary load case per vehicle position
```

**Where the vehicle is placed along the span** (one STAAD case each):
- Maximum **sagging** at mid-span of the top slab.
- Maximum **hogging** at the corners (load near the wall).
- Maximum **shear**, with load at about d from the wall face.
- Optionally, maximum **base pressure**.

The tool will step each vehicle across the span. Your Excel's chosen positions are the reference, and the tool must reproduce them first.

**Deep fill:** when B' becomes larger than the span, the load spreads over the whole top slab and acts almost like a uniform load. The tool will cap the patch at the slab length, the same way your Excel does.

**Braking** (IRC:6 cl. 211) belongs with each vehicle case: 20% of the first train load, applied 1.2 m above the road, with no impact. It is already in this version's load list.

---

## 4. How it fits the tool

- **Reusable package `02_Python/irc_live_load/`** (built 31 Oct): `vehicles.py` holds the vehicles as data, `deck_slab.py` turns one axle into a line load, `moving_load.py` finds the worst positions. The culvert's vehicle stage will use it to produce the STAAD load intensities **and** one EDRC sheet, from the same numbers.
- **Pilot:** 70R wheeled, the hardest case. Then the bogie, tracked, Class A single and Class A two-lane.
- **Combinations:** because the springs are compression-only, each vehicle case enters the ULS/SLS combinations as a **primary case with REPEAT LOAD**.
- **Acceptance test:** for your approved culvert, Python must reproduce your Excel's b_eff and line-load values exactly before the module counts as done.

## 5. What I need from you for this

1. The vehicle-loading **Excel** (formulas intact) and the matching **STAAD model**.
2. Your office conventions: tyre-width divisor, the α table you use, the critical positions you pick by eye, and how you treat overlapping wheels.
3. Carriageway width and crash-barrier/kerb layout for the reference culvert.

---

Sources: IRC:6-2017 text (cl. 204, 208, 211; Tables 2, 3, 6; Fig. 1 notes) – https://law.resource.org/pub/in/bis/irc/irc.gov.in.006.2017.pdf. Figures marked *verify* are commonly quoted values that were not legible in that extract.

---

## Checked against the code PDFs (31 Oct 2026, `IRC codes/` folder)

**IRC:112-2020 Annex B-3**
- B3.2(1)(i): b_eff = α·a·(1 − a/l0) + b1. **b = width of the slab** (not the carriageway). b_eff ≤ actual slab width; near an unsupported edge, b_eff ≤ b_eff/2 + distance of the load from that edge.
- α table: the continuous-slab column reaches 2.60 at b/l0 = 1.8; the simply-supported column reaches 3.00 at 1.9. Box top slab → continuous column (as the twin-cell Excel).
- B3.2(1)(ii): loads in a line along the span → each load gets **its own** b_eff with its own a. (The twin-cell Excel uses one a per position - to discuss.)
- B3.2(1)(iii): loads side by side with overlapping b_eff → sum minus overlap (as the Excel).
- B3.3: along the span = contact length + 2 × overall slab depth incl. wearing surface. B3.4: 45° through fill and wearing coat, both directions.

**IRC:6-2017 cl 208**
- 208.2 Class A: 4.5/(6+L), valid 3–45 m (below 3 m: Fig. 9). 208.3: 70R wheeled 25% (< 9 m); tracked 25% to 5 m → 10% at 9 m.
- 208.5 Note: for a deck slab, L = effective span of that member.
- 208.6: fill **not less than 0.6 m including road crust** → half impact. Twin-cell Excel checks the 0.065 m LL fill and uses `<=0.6` for wheeled (gives full impact at exactly 0.6) - to discuss.

**Agreed 31 Oct:**
- l0 = effective span = centre-to-centre of walls = B + tw/2 + tw/2 (= model.L, 5.4 m in the example). IRC:112 cl 7.6.1.1 (2)/(3): a member framing into supports, or continuous → distance between centres of supports. Already in the tool, no new input.
- b = width of the top slab perpendicular to l0 (the culvert's out-to-out length along the road). **New input** in the vehicle-load stage (not in Stage 1, which models a 1 m strip). Also used for the code limits: b_eff ≤ b, and the free-edge check.

**Transverse position of the vehicle (checked 31 Oct, IRC:6-2017):**
- 70R: kerb (roadway face) to outer edge of wheel/track C = **1.2 m** (Fig. 1 Note 4); carriageway ≥ 5.3 m.
  Passing vehicles on multi-lane: 1.2 m between outer edges (Note 5).
- Class A: f = **0.15 m** for all carriageway widths; g = 1.2 m above 6.1 m, 0.4–1.2 m for 5.3–6.1 m (Table 3).
- 204.1.2: any position giving maximum stress, without encroaching these clearances → vehicle hard against the barrier.
- From the slab free edge (outer face of the crash barrier, assumed = slab edge): edge-wheel centre at
  barrier width + C + tyre width/2 = 0.5 + 1.2 + 0.86/2 = 2.13 m (70R wheeled, twin-cell Excel H796);
  second wheel 1.93 m further in (2.79 − 0.86).
- Overhang check (Excel) = IRC:112 B3.2 free-edge rule: if b_eff/2 > 2.13, the part beyond the edge is cut
  off (b_eff,edge = b_eff/2 + 2.13).
- Clearance is per vehicle (1.2 m for 70R, 0.15 m for Class A) → per-vehicle input in the tool.

## 31 Oct - built: `02_Python/irc_live_load/` (reusable)

- Whole 70R wheeled vehicle (7 axles, 100 t) stepped 0.05 m across the span, both directions.
  Only axles whose centre is on the span count; each gets its own a and b_eff (B3.2(1)(ii)).
- Screening picks SAG (mid-span, SS beam), HOG (support, fixed-ended beam), SHEAR (at x_v, SS beam).
  Only those positions go to STAAD and the sheet.
- Contact length from IRC:6 Annex A Notes 2-3 (L type: 2 tyres x 0.36 m tread): 17 t -> 0.224 m,
  12 t -> 0.158 m, 8 t -> 0.105 m. Override possible (twin Excel 0.263).
- Check: twin-cell Excel Case 3 position 2 reproduced exactly (b_eff 2.4068, bP 4.3368, 44.830 kN/m2).
- Correction: 'L', 'M', 'N' are the 70R wheeled wheel arrangements of IRC:6 Fig. 1 (L done; M, N later).
