"""Refresh file and graph identities after a reviewed change; never fabricate evidence."""
import hashlib
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/"src"))
from resai.core import digest
from resai.pipeline import load_engine, verify_correspondence


if __name__ == "__main__":
    path = ROOT/"experiments/mapcoder/plan.json"
    plan = json.loads(path.read_text())
    hpc = ROOT/"hpc/mapcoder"
    engine = load_engine(hpc)
    graph = engine.resolve(engine.load_experiments(hpc/"config/experiments.json"), False)
    task_hash = hashlib.sha256((ROOT/"experiments/mapcoder/task.jsonl").read_bytes()).hexdigest()
    if task_hash != graph["resai_scientific"]["task_sha256"]:
        raise ValueError("Task changed: review scientific graph declaration before freezing")
    plan["scientific"] = graph["resai_scientific"]
    plan["execution"]["graph_hash"] = digest(graph)
    for relative in plan["inputs"]:
        plan["inputs"][relative] = hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()
    errors = verify_correspondence(plan, graph)
    if errors:
        raise ValueError(errors)
    path.write_text(json.dumps(plan, indent=2)+"\n", newline="\n")
    print("Frozen plan", digest(plan), "-- all previous-plan evidence is invalid for readiness")
