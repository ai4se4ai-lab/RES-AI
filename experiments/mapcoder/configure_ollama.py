"""Configure the Qwen3.8 variant in a separate source copy, then freeze its plan."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--isolated-copy", action="store_true", required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--listing", type=Path, required=True,
                        help="Archived /api/tags response from the pinned Ollama version")
    args = parser.parse_args()
    manifest = args.manifest.resolve()
    revision = hashlib.sha256(manifest.read_bytes()).hexdigest()
    listing = json.loads(args.listing.read_text())
    advertised = next(m for m in listing["models"] if m["name"] == "qwen3.8:27b")
    (ROOT/"experiments/mapcoder/model-listing.json").write_text(json.dumps(listing, indent=2)+"\n")
    archived = ROOT/"experiments/mapcoder/model-manifest.json"
    archived.write_bytes(manifest.read_bytes())
    graph_path = ROOT/"hpc/mapcoder/config/experiments.json"
    graph = json.loads(graph_path.read_text())
    graph["project"] = "resai-mapcoder-qwen38"
    graph["resai_scientific"].update(model="qwen3.8:27b", model_revision=revision,
        model_path=str(manifest), backend="ollama", quantization="Q4_K_M",
        thinking=False, ollama_version="0.40.10", model_api_digest=advertised["digest"].removeprefix("sha256:"))
    for step in graph["stages"][0]["steps"]:
        if "cmd" in step:
            step["cmd"] = step["cmd"].replace("mapcoder/run.py", "mapcoder/ollama_run.py")
    graph_path.write_text(json.dumps(graph, indent=2)+"\n", newline="\n")
    plan_path = ROOT/"experiments/mapcoder/plan.json"
    plan = json.loads(plan_path.read_text())
    for name in ("experiments/mapcoder/ollama_run.py", "experiments/mapcoder/ollama_backend.py",
                 "experiments/mapcoder/model-manifest.json", "experiments/mapcoder/configure_ollama.py",
                 "experiments/mapcoder/model-listing.json",
                 "experiments/mapcoder/prepare_smoke.py", "experiments/mapcoder/archive_run.py",
                 "hpc/mapcoder/slurm/ollama-smoke.sh"):
        plan["inputs"][name] = hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    plan_path.write_text(json.dumps(plan, indent=2)+"\n", newline="\n")
    subprocess.run([sys.executable, str(ROOT/"experiments/mapcoder/freeze_plan.py")], check=True)


if __name__ == "__main__":
    main()
