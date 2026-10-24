"""Collect exactly two current-plan pilot records and assess before dry dispatch."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/"src"))
from resai.core import digest, readiness


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--plan", type=Path, default=ROOT/"experiments/mapcoder/plan.json")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    plan = json.loads(args.plan.read_text())
    paths = sorted((args.results/"mapcoder").glob("rep*/attempt-*/evidence.json"))
    rows = [json.loads(p.read_text()) for p in paths]
    matching = [r for r in rows if r["plan_hash"] == digest(plan)]
    if len(matching) != 2 or {r["rep"] for r in matching} != {0,1} or len({r["attempt_id"] for r in matching}) != 2:
        raise ValueError("missing current-plan repeated pilot records")
    evidence = {"attempts": rows}
    (args.out/"evidence.json").write_text(json.dumps(evidence, indent=2)+"\n")
    result = readiness(plan, evidence)
    result["scientific_task_solved"] = [r.get("scientific_task_solved") for r in rows]
    result["scope"] = "one MapCoder task with a local-model adapter; no comparative effectiveness claim"
    (args.out/"assessment.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))
    return 0 if result["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
