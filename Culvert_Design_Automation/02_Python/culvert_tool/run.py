"""
RUN.PY - click Run on this file (you never need to edit it)
===========================================================

Before you click Run
-------------------
1. Open STAAD.Pro, start a new blank file in kN and metres,
   save it wherever you want, and keep it open.
2. Edit the INPUTS block at the top of each stage file you want to change.

What happens
------------
- run.py finds every file named  stage<number>_<name>.py  in this folder
  and runs them in number order: stage1 -> stage2 -> stage3 ...
- After each stage it prints that stage's summary and PAUSES so you can
  check the model in STAAD:  Enter = next stage,  Q = stop here.
- To add a stage, just drop its file into this folder. Nothing else changes.

Nothing is saved by the scripts. Save the model in STAAD yourself.

Folder
------
  run.py            <- click Run on this
  staad_api.py      <- shared STAAD helpers
  model.py          <- results passed from stage to stage
  stage1_geometry.py
  stage2_....py     <- later, just drop in
"""

import importlib
import re
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

PAUSE_AFTER_EACH_STAGE = True     # False = run all stages without stopping
STAGE_FILE = re.compile(r"stage(\d+)_\w+\.py")


def find_stages():
    """Return [(number, module_name)] sorted by stage number."""
    found = {}
    for p in HERE.glob("stage*.py"):
        m = STAGE_FILE.fullmatch(p.name)
        if not m:
            continue
        n = int(m.group(1))
        if n in found:
            raise SystemExit(f"Two files for Stage {n}: {found[n]}.py and {p.name}. "
                             "Keep only one.")
        found[n] = p.stem
    return sorted(found.items())


def main():
    import staad_api
    from model import BoxModel

    stages = find_stages()
    if not stages:
        print("No stage files found (expected names like stage1_geometry.py).")
        return

    numbers = [n for n, _ in stages]
    print("Stages found: " + ", ".join(f"{n} ({name})" for n, name in stages))
    if numbers != list(range(1, len(numbers) + 1)):
        print("WARNING: stage numbers are not 1, 2, 3... in sequence. "
              "Check no stage file is missing.")

    try:
        staad = staad_api.connect()
        model = BoxModel()

        for i, (n, name) in enumerate(stages):
            module = importlib.import_module(name)
            if not hasattr(module, "run"):
                raise staad_api.StopRun(f"{name}.py has no run(staad, model) function.")
            title = getattr(module, "TITLE", name)

            print("\n" + "=" * 64)
            print(f"  {title}")
            print("=" * 64)
            module.run(staad, model)
            model.stages_done.append(n)

            is_last = (i == len(stages) - 1)
            if PAUSE_AFTER_EACH_STAGE and not is_last:
                next_n = stages[i + 1][0]
                ans = input(f"\nStage {n} done. Check STAAD.  "
                            f"Enter = go to Stage {next_n},  Q = stop: ")
                if ans.strip().lower() == "q":
                    print(f"Stopped after Stage {n}.")
                    return

        print(f"\nAll stages done ({', '.join(map(str, model.stages_done))}). "
              "Save the model in STAAD when you are happy.")

    except staad_api.StopRun as stop:
        print(f"\nSTOPPED: {stop}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as exc:
        if exc.code not in (None, 0):
            print(f"\nSTOPPED: {exc.code}")
    except Exception:
        print("\nUNEXPECTED ERROR - send me everything below:\n")
        traceback.print_exc()
    finally:
        input("\nPress Enter to close...")
