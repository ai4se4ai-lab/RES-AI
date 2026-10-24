"""Pure readiness decision; telemetry is trusted operator evidence, not attestation."""
from __future__ import annotations
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def validate(plan):
    if not isinstance(plan, dict):
        return ["plan_not_object"]
    errors = []
    for field in ("scientific", "execution", "required_probes", "budget_gpu_seconds", "max_attempts"):
        if field not in plan:
            errors.append("missing:" + field)
    if errors:
        return errors
    if not isinstance(plan["scientific"], dict) or not plan["scientific"]:
        errors.append("invalid_scientific_contract")
    probes = plan["required_probes"]
    if not isinstance(probes, list) or not probes or any(not isinstance(x, str) or not x for x in probes):
        errors.append("invalid_probe_contract")
    elif len(set(probes)) != len(probes):
        errors.append("empty_or_duplicate_contract")
    def finite(value):
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    if not finite(plan["budget_gpu_seconds"]) or plan["budget_gpu_seconds"] <= 0 or not isinstance(plan["max_attempts"], int) or isinstance(plan["max_attempts"], bool) or plan["max_attempts"] < 2:
        errors.append("invalid_budget")
    for key, default, lower, upper in (("memory_limit", .9, 0, 1), ("stability_epsilon", .05, 0, 1), ("evidence_ttl_seconds", 3600, 1, float("inf"))):
        value = plan.get(key, default)
        if not finite(value) or not lower <= value <= upper:
            errors.append("invalid_policy:"+key)
    ex = plan["execution"]
    if not isinstance(ex, dict):
        return errors+["execution_not_object"]
    for key in ("nodes", "gpus_per_node", "batch_size", "wall_seconds"):
        if not isinstance(ex.get(key), int) or isinstance(ex.get(key), bool) or ex[key] <= 0:
            errors.append("invalid:" + key)
    if not isinstance(ex.get("partition"), str) or not ex["partition"]:
        errors.append("missing:partition")
    return errors


def readiness(plan, evidence, now=None):
    """Require two distinct successful recorded probes of the exact current plan.

    GPU-seconds cover all attempts, including failed and obsolete configurations.
    Memory evidence is a ratio of peak allocated to device capacity, not utilization.
    """
    errors = validate(plan)
    if errors:
        return {"ready": False, "reasons": errors}
    now = now or datetime.now(timezone.utc).timestamp()
    reasons = []
    fingerprint = digest(plan)
    if not isinstance(evidence, dict) or not isinstance(evidence.get("attempts"), list) or any(not isinstance(r, dict) for r in evidence["attempts"]):
        return {"ready": False, "reasons": ["invalid_evidence_structure"]}
    rows = evidence["attempts"]
    for row in rows:
        for field in ("gpu_seconds", "timestamp", "peak_memory_fraction"):
            value = row.get(field)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
                return {"ready": False, "reasons": ["invalid_telemetry:"+field]}
        if not isinstance(row.get("attempt_id"), str) or not isinstance(row.get("passed_probes"), list):
            return {"ready": False, "reasons": ["invalid_evidence_structure"]}
    if len(rows) > plan["max_attempts"]:
        reasons.append("attempt_budget")
    spent = sum(float(r.get("gpu_seconds", 0)) for r in rows)
    if any(not math.isfinite(float(r.get("gpu_seconds", -1))) or float(r.get("gpu_seconds", -1)) <= 0 for r in rows):
        reasons.append("invalid_accounting")
    if not math.isfinite(spent) or spent < 0 or spent > plan["budget_gpu_seconds"]:
        reasons.append("compute_budget")
    identifiers = [r.get("attempt_id") for r in rows]
    if any(not identifier for identifier in identifiers) or len(set(identifiers)) != len(identifiers):
        reasons.append("duplicate_or_missing_attempt_id")
    matches = sorted([r for r in rows if r.get("plan_hash") == fingerprint], key=lambda r: float(r.get("timestamp", 0)))
    recent = matches[-2:]
    if len(recent) != 2 or len({r.get("attempt_id") for r in recent}) != 2 or any(not r.get("attempt_id") for r in recent):
        reasons.append("two_distinct_attempts")
    for row in recent:
        if row.get("status") != "ok":
            reasons.append("execution_failure")
        if not set(plan["required_probes"]).issubset(row.get("passed_probes", [])):
            reasons.append("coverage")
        if row.get("output_valid") is not True:
            reasons.append("output_contract")
        age = now - float(row.get("timestamp", 0))
        if not math.isfinite(age) or not 0 <= age <= plan.get("evidence_ttl_seconds", 3600):
            reasons.append("stale_evidence")
        ratio = float(row.get("peak_memory_fraction", 2))
        if not math.isfinite(ratio) or not 0 <= ratio <= plan.get("memory_limit", 0.9):
            reasons.append("memory_headroom")
        cost = float(row.get("gpu_seconds", -1))
        if not math.isfinite(cost) or cost <= 0:
            reasons.append("invalid_accounting")
    if len(recent) == 2:
        a, b = [float(r.get("peak_memory_fraction", 2)) for r in recent]
        if abs(a-b) > plan.get("stability_epsilon", 0.05):
            reasons.append("unstable_memory")
    return {"ready": not reasons, "reasons": sorted(set(reasons)), "plan_hash": fingerprint,
            "evidence_hash": digest(evidence), "gpu_seconds": spent,
            "scope": "declared probes only; no production reliability guarantee"}


def refine(plan, evidence):
    """One operational proposal only; never rewrite scientific parameters."""
    import copy
    if validate(plan):
        return None
    candidate = copy.deepcopy(plan)
    if not evidence.get("attempts"):
        return None
    rows = evidence["attempts"]
    if len(rows) >= plan["max_attempts"] or sum(float(r.get("gpu_seconds", 0)) for r in rows) >= plan["budget_gpu_seconds"]:
        return None
    last = max(rows, key=lambda r: float(r.get("timestamp", 0)))
    if last.get("plan_hash") != digest(plan):
        return None
    if last.get("fault") == "oom" and plan["execution"]["batch_size"] > 1 and plan["scientific"].get("batch_invariant") is True:
        candidate["execution"]["batch_size"] = max(1, plan["execution"]["batch_size"] // 2)
        return candidate
    return None


def discover():
    """Read scheduler-reported inventory; unknown bandwidth is never invented."""
    commands = {"nodes": ["sinfo", "--json"], "partitions": ["scontrol", "show", "partition", "--oneliner"],
                "topology": ["scontrol", "show", "topology", "--oneliner"]}
    result = {"observed_at": datetime.now(timezone.utc).isoformat(), "bandwidth": "unknown", "latency": "unknown"}
    for key, argv in commands.items():
        try:
            proc = subprocess.run(argv, capture_output=True, text=True, timeout=20)
            result[key] = {"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}
        except (OSError, subprocess.TimeoutExpired) as exc:
            result[key] = {"unavailable": type(exc).__name__}
    return result
