# Box Culvert Design Automation – project pack

**Single-cell RCC box culvert:** STAAD.Pro (via Python/OpenSTAAD) → loads → design (IRC:112) → AutoCAD drawing.

Pack date: 16 Oct 2026. It brings together all the project chats (28 Sep – 16 Oct).

## What's inside

```
Culvert_Design_Automation/
├── 00_README.md                     ← this file
├── 01_Plan/
│   ├── Project_Plan.pdf             ← full plan with diagrams (export of the live plan)
│   ├── Important_Changes_2026-10-16.md  ← latest decisions (READ FIRST)
│   └── Decisions_Log.md             ← every decision, all chats, newest first
├── 02_Python/
│   ├── README.md                    ← how to run, stage status
│   ├── culvert_tool/                ← the live tool: copy this folder to your PC
│   │   ├── run.py                   ← click Run on this
│   │   ├── staad_api.py
│   │   ├── model.py
│   │   └── stage1_geometry.py
│   └── legacy_reference/
│       └── stage2_springs_OLD_standalone.py   ← reference only, do not run
├── 03_Loads/
│   ├── Load_Cases_v1.md             ← DL, SIDL (max a/b), earth pressure, surcharges, braking, water
│   └── Vehicle_Loading_IRC.md       ← 5 vehicle cases, impact, dispersion, b_eff, STAAD line load
└── 04_Open_Questions.md             ← things to confirm + files still needed
```

The live plan (with comments) is here: https://claude.ai/code/artifact/1e7becd1-8e0f-4a8d-8b37-02e38864aa70

## Where we are

| Stage | Status |
|---|---|
| 1 Model + properties | 16 Oct code delivered (new base-slab rule, density 25); **check in STAAD** |
| 2 Springs + supports | 16 Oct code delivered (3 supports); **check in STAAD** |
| 3 Loads | Cases 1–7 delivered + EDRC load-calc Excel; **check in STAAD**. Vehicle loads: next session |
| 4 Combinations | Study the sample STAAD and explain only |
| 5–8 | Per plan, later |

## Next steps

1. Confirm the 4 items at the top of `04_Open_Questions.md`.
2. Share the twin-cell Excel, the STAAD file and the design docs.
3. I update Stage 1, rewrite Stage 2 and build Stage 3. You run each in STAAD and check.
4. Write the load calculation sheet in EDRC format.
5. Then vehicle loading (pilot: 70R wheeled), from your vehicle Excel and STAAD model.
