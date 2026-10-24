"""Freeze a reviewed MapCoder plan and print its bounded interactive command.

The recorded pilot used the equivalent explicit freeze steps. This helper makes
that preparation reproducible without copying commands from a terminal transcript.
"""
import argparse
import json
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/"src"))
from resai.core import readiness
from resai.pipeline import load_engine, verify_inputs, verify_correspondence, validate_site_config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.run_id):
        parser.error("run ID must contain only letters, digits, underscores and hyphens")
    plan = json.loads((ROOT/"experiments/mapcoder/plan.json").read_text())
    hpc = ROOT/"hpc/mapcoder"
    engine = load_engine(hpc)
    cluster = engine.cluster()
    original = engine.load_experiments(hpc/"config/experiments.json")
    graph = engine.resolve(original, False)
    errors = verify_inputs(plan, hpc_relative="hpc/mapcoder")+verify_correspondence(plan, graph)+validate_site_config(cluster)+engine.validate(graph)
    if errors:
        raise ValueError(errors)
    log = engine.log_root(args.run_id)
    config = log/"config"
    config.mkdir(parents=True, exist_ok=False)
    for name in ("cluster.env", "experiments.json", "requirements.txt"):
        shutil.copy(hpc/"config"/name, config/name)
    (config/"experiments.resolved.json").write_text(json.dumps(engine.resolve(original, True), indent=2)+"\n", newline="\n")
    (log/"admission-before.json").write_text(json.dumps(readiness(plan, {"attempts": []}), indent=2)+"\n")
    subprocess.run([sys.executable, str(hpc/"scripts/manifest.py"), args.run_id], check=True)
    resources = graph["stages"][0]["resources"]
    command = ["salloc", "--account="+cluster["ACCOUNT"], "--partition="+resources["partition"],
        "--gpus="+resources["gpus"], "--cpus-per-task="+str(resources["cpus"]),
        "--mem="+resources["mem"], "--time="+resources["time"], "srun", "--ntasks=1", "bash",
        str(hpc/"slurm/interactive-smoke.sh"), args.run_id]
    (log/"launch-command.json").write_text(json.dumps(command, indent=2)+"\n")
    print(shlex.join(command))
    print("Prepared only; no allocation or production job submitted.")


if __name__ == "__main__":
    main()
