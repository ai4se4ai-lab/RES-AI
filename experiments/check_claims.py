"""Consistency audit for observed counts, dependencies, citations and frozen pilot."""
import csv
import hashlib
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"src"))
from resai.pipeline import load_engine, verify_correspondence, verify_inputs


if __name__ == "__main__":
    result = ROOT/"experiments/results/local"
    rows = list(csv.DictReader((result/"decisions.csv").open()))
    summary = json.loads((result/"summary.json").read_text())
    assert len(rows) == summary["decisions"]
    for name, record in summary["conditions"].items():
        subset = [r for r in rows if r["condition"] == name]
        assert len(subset) == summary["cases_per_condition"]
        assert sum(r["admitted"] == "0" and r["fault"] != "clean" for r in subset) == record["blocked_faults"]
        assert sum(r["admitted"] == "0" and r["fault"] == "clean" for r in subset) == record["false_blocks"]
    # Controller analyses must agree with the mutation study and with the bounds stated in the paper.
    ablation = list(csv.DictReader((result/"ablation.csv").open()))
    resai = {(r["seed"], r["fault"]): r["admitted"] for r in rows if r["condition"] == "resai"}
    assert all(resai[(r["seed"], r["fault"])] == r["full"] for r in ablation) and len(ablation) == len(resai)
    refinement = list(csv.DictReader((result/"refinement.csv").open()))
    assert not any(int(r["scientific_changed"]) for r in refinement)
    assert all(float(r["charged_seconds"]) <= 60*int(r["max_attempts"]) for r in refinement)
    assert not any(int(r["proposals"]) for r in refinement if r["batch_invariant"] == "0")
    paper = ROOT/"docs/EMSE"
    files = [paper/name for name in ("main.tex", "approach.tex", "evaluation.tex", "results.tex", "discussion.tex")]+list((paper/"generated").glob("*.tex"))
    text = "\n".join(p.read_text(encoding="utf-8") for p in files)
    keys = {k.strip() for value in re.findall(r"\\cite\{([^}]+)\}", text) for k in value.split(",")}
    bib = (paper/"bibliography.bib").read_text(encoding="utf-8")+(paper/"generated/artifact_refs.bib").read_text(encoding="utf-8")
    assert not keys-set(re.findall(r"@\w+\{([^,]+),", bib))
    for relative in re.findall(r"\\input\{([^}]+)\}", text):
        assert (paper/(relative+".tex")).is_file(), relative
    for relative in re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", text):
        assert (paper/relative).is_file(), relative
    # Curves must describe actual archived allocations and probe records.
    timeline = json.loads((paper/"generated/gpu_cost_timeline.json").read_text())
    accounting = list(csv.DictReader((ROOT/"experiments/results/nibi/logs/sacct.psv").open(), delimiter="|"))
    cells = [r for r in accounting if "." not in r["JobID"] and r["JobID"].startswith("24888989_")]
    assert timeline["total_allocated_instance_seconds"] == sum(int(r["ElapsedRaw"]) for r in cells)
    probes = [json.loads(p.read_text()) for p in (ROOT/"experiments/results/nibi/results/gpu").glob("*.json")]
    assert math.isclose(timeline["total_probe_process_seconds"], sum(r["gpu_seconds"] for r in probes))
    plotted = list(csv.DictReader((paper/"generated/gpu_cost_timeline.csv").open()))
    assert len(plotted) == len(probes) == 8
    assert {(r["mode"], int(r["rep"])) for r in plotted} == {(r["mode"], r["rep"]) for r in probes}
    for rep in (0, 1):
        final = next(r for r in plotted if int(r["rep"]) == rep and int(r["mode_order"]) == 4)
        assert math.isclose(float(final["cumulative_process_seconds"]), sum(r["gpu_seconds"] for r in probes if r["rep"] == rep))
    hpc = ROOT/"hpc/mapcoder"
    plan = json.loads((ROOT/"experiments/mapcoder/plan.json").read_text())
    assert not verify_inputs(plan, hpc_relative="hpc/mapcoder")
    engine = load_engine(hpc)
    graph = engine.resolve(engine.load_experiments(hpc/"config/experiments.json"), False)
    assert not verify_correspondence(plan, graph)
    provenance = json.loads((ROOT/"experiments/mapcoder/provenance.json").read_text())
    task_hash = hashlib.sha256((ROOT/"experiments/mapcoder/task.jsonl").read_bytes()).hexdigest()
    assert task_hash == plan["scientific"]["task_sha256"] == provenance["task_sha256"]
    print(f"Verified {len(rows)} decisions, {len(keys)} citations, TeX/figure inputs, GPU curves, and frozen MapCoder identities.")
