"""Executed controller analyses beyond the mutation study: ablation, threshold
sensitivity, bounded refinement and assessment overhead.

All inputs are synthetic fixtures evaluated by the actual policy code. No GPU,
Slurm, model, queue-time or saved-compute measurement is produced here.
"""
import argparse
import copy
import csv
import json
import platform
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "experiments"))
from resai.core import digest, readiness, refine
from resai.pipeline import load_engine
from run_local import FAULTS, fixture, mutate

NOW = 10010
# Reason codes grouped by the conjunct of Equation (1) that emits them.
COMPONENTS = {
    "identity": {"two_distinct_attempts", "duplicate_or_missing_attempt_id"},
    "outcome": {"execution_failure", "coverage", "output_contract"},
    "freshness": {"stale_evidence"},
    "memory": {"memory_headroom", "unstable_memory"},
    "budget": {"attempt_budget", "compute_budget", "invalid_accounting"},
}


def component(reason):
    if reason.startswith("invalid_telemetry"):
        return "budget"
    return next(name for name, codes in COMPONENTS.items() if reason in codes)


def write(path, rows):
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def rehash(plan, evidence):
    for row in evidence["attempts"]:
        row["plan_hash"] = digest(plan)


def ablation(seeds, engine):
    """Leave-one-component-out: a variant admits when only its removed conjunct objects."""
    rows = []
    for seed in range(seeds):
        for fault in FAULTS:
            plan, evidence, graph = fixture(seed)
            mutate(fault, plan, evidence, graph)
            static_ok = not engine.validate(engine.resolve(graph, False))
            reasons = readiness(plan, evidence, now=NOW)["reasons"]
            groups = {component(r) for r in reasons}
            row = {"seed": seed, "fault": fault, "static_ok": int(static_ok),
                   "reasons": ";".join(reasons), "full": int(static_ok and not groups)}
            for name in COMPONENTS:
                row["without_"+name] = int(static_ok and groups <= {name})
            rows.append(row)
    return rows


def sensitivity(seeds):
    """Admission as one evidence property crosses its declared threshold."""
    sweeps = {
        "evidence_ttl_seconds": ([1800, 3600, 7200], [i*250 for i in range(41)]),
        "memory_limit": ([0.8, 0.9, 0.95], [round(1+i*0.025, 3) for i in range(33)]),
        "stability_epsilon": ([0.02, 0.05, 0.1], [round(i*0.005, 3) for i in range(31)]),
        "budget_gpu_seconds": ([600, 1200, 1800], [i*50 for i in range(1, 49)]),
    }
    rows = []
    for parameter, (settings, values) in sweeps.items():
        for setting in settings:
            for x in values:
                admitted = 0
                for seed in range(seeds):
                    plan, evidence, _ = fixture(seed)
                    plan[parameter] = setting
                    a, b = evidence["attempts"]
                    if parameter == "evidence_ttl_seconds":
                        a["timestamp"], b["timestamp"] = NOW-x-1, NOW-x
                    elif parameter == "memory_limit":
                        # x scales the seed's baseline footprint, as a larger boundary input would.
                        a["peak_memory_fraction"] *= x
                        b["peak_memory_fraction"] = a["peak_memory_fraction"]
                    elif parameter == "stability_epsilon":
                        b["peak_memory_fraction"] = a["peak_memory_fraction"]+x
                    else:
                        a["gpu_seconds"] = b["gpu_seconds"] = x/2
                    rehash(plan, evidence)
                    admitted += readiness(plan, evidence, now=NOW)["ready"]
                rows.append({"parameter": parameter, "setting": setting, "x": x,
                             "admitted": admitted, "seeds": seeds})
    return rows


def episode(seed, batch, max_attempts, invariant=True, probe_seconds=60):
    """Algorithm 2 with an operator who adopts every proposal; memory scales with batch."""
    plan, seeded, _ = fixture(seed)
    per_item = seeded["attempts"][0]["peak_memory_fraction"]/plan["execution"]["batch_size"]
    plan["execution"]["batch_size"] = batch
    plan["max_attempts"] = max_attempts
    plan["scientific"]["batch_invariant"] = invariant
    science = digest(plan["scientific"])
    evidence = {"attempts": []}
    trace, proposals = [], 0
    while True:
        result = readiness(plan, evidence, now=NOW)
        spent = sum(r["gpu_seconds"] for r in evidence["attempts"])
        if result["ready"]:
            decision = "ready"
            break
        if len(evidence["attempts"]) >= max_attempts or spent >= plan["budget_gpu_seconds"]:
            decision = "blocked_budget"
            break
        proposal = refine(plan, evidence)
        last = evidence["attempts"][-1] if evidence["attempts"] else None
        matching = sum(r["plan_hash"] == digest(plan) for r in evidence["attempts"])
        if proposal is not None:
            assert digest(proposal["scientific"]) == science
            plan, proposals = proposal, proposals+1
        elif last is not None and (last.get("fault") == "oom" or matching >= 2):
            decision = "blocked_no_refinement"
            break
        peak = per_item*plan["execution"]["batch_size"]
        oom = peak > 1
        evidence["attempts"].append({"attempt_id": str(len(evidence["attempts"])), "plan_hash": digest(plan),
            "timestamp": NOW-100+len(evidence["attempts"]), "status": "failed" if oom else "ok",
            "passed_probes": [] if oom else plan["required_probes"][:], "output_valid": not oom,
            "peak_memory_fraction": min(peak, 1.0), "gpu_seconds": probe_seconds,
            **({"fault": "oom"} if oom else {})})
        trace.append(sum(r["gpu_seconds"] for r in evidence["attempts"]))
    return {"seed": seed, "initial_batch": batch, "max_attempts": max_attempts, "batch_invariant": int(invariant),
            "decision": decision, "attempts": len(evidence["attempts"]), "proposals": proposals,
            "final_batch": plan["execution"]["batch_size"], "charged_seconds": spent,
            "scientific_changed": int(digest(plan["scientific"]) != science),
            "trace": " ".join(str(int(x)) for x in trace), "memory_per_item": round(per_item, 6)}


def refinement(seeds):
    rows = []
    for invariant in (True, False):
        for batch in (8, 16, 32, 64, 128):
            for cap in range(2, 9):
                rows += [episode(seed, batch, cap, invariant) for seed in range(seeds)]
    return rows


def overhead(repeats):
    """Wall-clock cost of one assessment as the evidence ledger grows."""
    rows = []
    for n in [2**k for k in range(1, 12)]:
        plan, evidence, _ = fixture(0)
        plan.update(max_attempts=n, budget_gpu_seconds=60*n+1)
        template = evidence["attempts"][0]
        evidence["attempts"] = [dict(template, attempt_id=str(i), timestamp=NOW-n+i, plan_hash=digest(plan)) for i in range(n)]
        assert readiness(plan, evidence, now=NOW)["ready"]
        samples = []
        for _ in range(repeats):
            start = time.perf_counter()
            readiness(plan, evidence, now=NOW)
            samples.append((time.perf_counter()-start)*1000)
        q = statistics.quantiles(samples, n=4)
        rows.append({"attempts": n, "median_ms": statistics.median(samples), "q1_ms": q[0], "q3_ms": q[2],
                     "max_ms": max(samples), "repeats": repeats})
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT/"experiments/results/local")
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--repeats", type=int, default=200)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    engine = load_engine()
    outputs = {"ablation": ablation(args.seeds, engine), "sensitivity": sensitivity(args.seeds),
               "refinement": refinement(args.seeds), "overhead": overhead(args.repeats)}
    for name, rows in outputs.items():
        write(args.out/(name+".csv"), rows)
    (args.out/"analyses-manifest.json").write_text(json.dumps({
        "python": sys.version.split()[0], "platform": platform.platform(), "processor": platform.processor(),
        "seeds": args.seeds, "overhead_repeats": args.repeats, "now": NOW,
        "rows": {k: len(v) for k, v in outputs.items()},
        "sources": {str(p.relative_to(ROOT)): digest(p.read_text()) for p in
                    [Path(__file__), ROOT/"experiments/run_local.py", ROOT/"src/resai/core.py"]}}, indent=2)+"\n")
    print({k: len(v) for k, v in outputs.items()})


if __name__ == "__main__":
    main()
