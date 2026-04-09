# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
One-off: backfill proxy_mean + smoke_scores into an already-assembled cases JSON
by reading the stage5 smoke files still sitting in pipeline/run/.

Must be run before the next batch clears pipeline/run/.

Usage:
    uv run pipeline/patch_smoke_scores.py --input cases_100-199.json
"""

import argparse
import json
from pathlib import Path

PIPELINE_DIR = Path(__file__).parent
RUN_DIR = PIPELINE_DIR / "run"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="Assembled cases JSON to patch in place")
    args = p.parse_args()

    input_path = Path(args.input)
    cases: list[dict] = json.loads(input_path.read_text(encoding="utf-8"))

    # Build case_id → mechanism_id from pipeline/run/stage4/
    case_id_to_mech: dict[str, str] = {}
    for f in (RUN_DIR / "stage4").glob("mech_*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            cid = data.get("case_id")
            if cid:
                case_id_to_mech[cid] = f.stem
        except Exception:
            pass

    # Build mechanism_id → smoke scores from pipeline/run/stage5/
    mech_to_smoke: dict[str, dict] = {}
    for f in (RUN_DIR / "stage5").glob("mech_*_smoke.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            mech_id = data.get("mechanism_id") or f.stem.replace("_smoke", "")
            mech_to_smoke[mech_id] = {
                "proxy_mean": data.get("proxy_mean"),
                "smoke_scores": data.get("scores", {}),
            }
        except Exception:
            pass

    patched = 0
    for case in cases:
        cid = case.get("case_id", "")
        mech = case_id_to_mech.get(cid)
        if mech and mech in mech_to_smoke:
            case.setdefault("_pipeline", {}).update(mech_to_smoke[mech])
            patched += 1

    input_path.write_text(json.dumps(cases, indent=2), encoding="utf-8")
    print(f"Patched {patched}/{len(cases)} cases with smoke scores → {input_path.name}")


if __name__ == "__main__":
    main()
