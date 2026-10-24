"""Summarize real GPU probe outputs and apply readiness policy to paired repeats."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/"src"), str(ROOT/"experiments")]
from run_local import fixture
from resai.core import digest, readiness


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(p.read_text()) for p in sorted((args.results/"gpu").glob("*.json"))]
    expected = {(mode, rep) for mode in ("clean", "corrupt_output", "missing_checkpoint", "runtime_failure") for rep in (0, 1)}
    observed = [(r["mode"], r["rep"]) for r in rows]
    if len(observed) != len(expected) or set(observed) != expected:
        raise ValueError(f"Incomplete or duplicate pilot: expected {expected}, observed {observed}")
    if len({r["attempt_id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate attempt identifiers")
    summary = {"evidence_type": "real CUDA synthetic-tensor smoke probe", "attempts": len(rows), "modes": {}}
    for mode in sorted({r["mode"] for r in rows}):
        subset = [r for r in rows if r["mode"] == mode]
        plan, _, _ = fixture()
        plan["scientific"] = {"workload": "synthetic MLP 512-1024-64", "input": "128x512", "batch_invariant": False}
        plan["execution"]["batch_size"] = 128
        plan["execution"]["partition"] = "Nibi default selection"
        for row in subset:
            row["plan_hash"] = digest(plan)
        # Hash binding here is an analysis identity assigned to the known probe,
        # not a claim that an admission certificate existed before execution.
        assessment = readiness(plan, {"attempts": subset}, now=max(r["timestamp"] for r in rows))
        summary["modes"][mode] = {"attempts": len(subset), "ready": assessment["ready"], "reasons": assessment["reasons"],
            "process_instance_seconds": sum(r["gpu_seconds"] for r in subset),
            "max_memory_fraction": max(r["peak_memory_fraction"] for r in subset)}
    (args.out/"gpu-summary.json").write_text(json.dumps(summary, indent=2)+"\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
