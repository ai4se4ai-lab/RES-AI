"""Operator-facing admission wrapper around the pinned use-hpc executor."""
import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from .core import readiness, digest, validate

ROOT = Path(__file__).resolve().parents[2]


def load_engine(hpc_dir=None):
    spec = importlib.util.spec_from_file_location("resai_upstream", (hpc_dir or ROOT/"hpc") / "scripts/hpclib.py")
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    return engine


def verify_inputs(plan, root=ROOT, hpc_relative="hpc"):
    errors = []
    inputs = plan.get("inputs", {})
    if not inputs:
        return ["missing_input_hashes"]
    for relative, expected in inputs.items():
        path = (root / relative).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            errors.append("missing_or_external_input:" + relative)
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            errors.append("changed_input:" + relative)
    # Must bind both the execution graph and the site configuration.
    for required in (hpc_relative+"/config/experiments.json", hpc_relative+"/config/cluster.env"):
        if required not in inputs:
            errors.append("unbound:" + required)
    return errors


def verify_correspondence(plan, graph):
    """Conservative mapping for homogeneous GPU stages and a declared batch.

    Scientific metadata is an operator assertion, not inferred command semantics.
    """
    errors = []
    execution = plan["execution"]
    if execution.get("graph_hash") != digest(graph):
        errors.append("execution_graph_identity")
    if graph.get("resai_scientific") != plan["scientific"]:
        errors.append("scientific_graph_declaration")
    if str(graph.get("vars", {}).get("BATCH_SIZE")) != str(execution["batch_size"]):
        errors.append("batch_mapping")
    stages = [s for s in graph["stages"] if not s.get("cpu_only")]
    if not stages:
        errors.append("no_supported_gpu_stage")
    for stage in stages:
        overrides = stage.get("sbatch_extra", [])
        # No raw GPU-stage flags: short aliases and separate option/value tokens
        # would otherwise bypass inspection of the structured resources.
        if overrides:
            errors.append("resource_override:"+stage["name"])
        resources = stage.get("resources", {})
        nodes = int(resources.get("nodes", 1))
        per_node = resources.get("gpus_per_node")
        count = int(str(per_node or resources.get("gpus") or "0").split(":")[-1])
        if not per_node:
            if count % nodes:
                errors.append("nonuniform_gpu_shape")
            count //= nodes
        time_parts = str(resources.get("time", "")).split(":")
        seconds = sum(int(v)*factor for v, factor in zip(time_parts, (3600, 60, 1))) if len(time_parts) == 3 else -1
        if (nodes != execution["nodes"] or count != execution["gpus_per_node"] or seconds != execution["wall_seconds"] or resources.get("partition", "site-default") != execution["partition"]):
            errors.append("resource_mapping:"+stage["name"])
    return errors


def validate_site_config(config):
    return ["control_character_in_site_config:"+name for name,value in config.items()
            if "\r" in str(value) or "\n" in str(value)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--submit", action="store_true", help="invoke upstream Slurm submission; otherwise dry run")
    parser.add_argument("--hpc-dir", type=Path, default=ROOT/"hpc")
    args = parser.parse_args()
    plan, evidence = [json.loads(p.read_text()) for p in (args.plan, args.evidence)]
    result = readiness(plan, evidence)
    if validate(plan):
        print(json.dumps(result, indent=2))
        return 2
    hpc_dir = args.hpc_dir.resolve()
    hpc_relative = hpc_dir.relative_to(ROOT).as_posix()
    result["reasons"].extend(verify_inputs(plan, hpc_relative=hpc_relative))
    engine = load_engine(hpc_dir)
    result["reasons"].extend(validate_site_config(engine.cluster()))
    graph = engine.resolve(engine.load_experiments(hpc_dir / "config/experiments.json"), False)
    result["reasons"].extend(engine.validate(graph))
    result["reasons"].extend(verify_correspondence(plan, graph))
    result["ready"] = not result["reasons"]
    print(json.dumps(result, indent=2), flush=True)
    if not result["ready"]:
        return 2
    # Snapshotting/TOCTOU and duplicate submissions remain documented limitations.
    cmd = [sys.executable, str(hpc_dir / "slurm/submit.py")]
    if not args.submit:
        cmd.append("--dry-run")
    return subprocess.run(cmd, cwd=ROOT).returncode


if __name__ == "__main__":
    raise SystemExit(main())
