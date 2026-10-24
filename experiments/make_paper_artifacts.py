"""Regenerate all reported counts and plots from archived observations."""
import csv
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
from datetime import datetime
from paper_visuals import (ABLATIONS, POLICY_GROUPS, fault_heatmap, gpu_diagnostics, overhead_plot,
                           refinement_plot, sensitivity_plot, style)
style()

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/"docs/EMSE/generated"
OUT.mkdir(exist_ok=True)
LABELS = {"direct": "Direct", "upstream_static": "Static", "upstream_smoke": "Smoke proxy", "resai": "RES-AI"}


def main():
    summary = json.loads((ROOT/"experiments/results/local/summary.json").read_text())
    rows = list(csv.DictReader((ROOT/"experiments/results/local/decisions.csv").open()))
    assert len(rows) == summary["decisions"]
    commands = {"LocalDecisions": summary["decisions"], "LocalSeeds": summary["seeds"],
        "FaultFamilies": summary["fault_families"], "CasesPerCondition": summary["cases_per_condition"]}
    commands.update(MutationFaultCases=summary["conditions"]["resai"]["fault_cases"],
        MutationCleanCases=summary["conditions"]["resai"]["clean_cases"],
        StaticBlocked=summary["conditions"]["upstream_static"]["blocked_faults"],
        SmokeAdditional=summary["conditions"]["upstream_smoke"]["blocked_faults"]-summary["conditions"]["upstream_static"]["blocked_faults"])
    table = [r"\begin{tabular}{lrrrr}", r"\toprule Policy & \shortstack{Blocked\\faults} & \shortstack{Admitted\\faults} & \shortstack{Detection\\(\%)} & \shortstack{False\\blocks} \\", r"\midrule"]
    for name, values in summary["conditions"].items():
        subset = [r for r in rows if r["condition"] == name]
        assert sum(r["admitted"] == "0" and r["fault"] != "clean" for r in subset) == values["blocked_faults"]
        escaped=values['fault_cases']-values['blocked_faults']
        detection=100*values['blocked_faults']/values['fault_cases']
        table.append(f"{LABELS[name]} & {values['blocked_faults']}/{values['fault_cases']} & {escaped}/{values['fault_cases']} & {detection:.1f} & {values['false_blocks']}/{values['clean_cases']} " + r"\\")
    table += [r"\bottomrule", r"\end{tabular}"]
    (OUT/"local_table.tex").write_text("\n".join(table)+"\n")
    local = ROOT/"experiments/results/local"
    ablation_rows = list(csv.DictReader((local/"ablation.csv").open()))
    faults, counts, ab_counts = fault_heatmap(rows, summary, LABELS, OUT, ablation_rows)
    commands.update(analysis_tables(local, faults, counts, ab_counts, summary["seeds"]))
    (OUT/"counts.tex").write_text("\n".join("\\newcommand{\\"+name+"}{"+str(value)+"}" for name,value in commands.items())+"\n")
    subjects = json.loads((ROOT/"experiments/subjects.json").read_text())["subjects"]
    assert len(subjects) == 12 and all(r["available"] for r in subjects)
    lines=[r"\begin{tabularx}{\textwidth}{lXl}", r"\toprule Artifact & Intended workflow & Observed HEAD \\", r"\midrule"]
    for i, r in enumerate(subjects, 1):
        citation = {1: "yang2024sweagent", 2: "wang2025openhands", 9: "bouzenia2025executionagent"}.get(i, "resaiartifact"+str(i))
        lines.append(r"\href{"+r["repository"]+"}{"+r["name"]+r"}~\cite{"+citation+"} & "+r["area"]+r" & \texttt{"+r["retrieved_head"][:8]+"} "+r"\\")
    lines += [r"\bottomrule",r"\end{tabularx}"]
    (OUT/"subjects.tex").write_text("\n".join(lines)+"\n")
    gpu_root = ROOT/"experiments/results/nibi"
    gpu_file = gpu_root/"reanalysis/gpu-summary.json"
    if gpu_file.exists():
        cell_seconds = gpu_diagnostics(gpu_root, OUT)
        overhead_plot(list(csv.DictReader((local/"overhead.csv").open())), OUT, min(cell_seconds))
        gpu = json.loads(gpu_file.read_text())
        assert gpu["attempts"] == 8
        expected = {"clean": True, "corrupt_output": False, "missing_checkpoint": False, "runtime_failure": False}
        assert {k: v["ready"] for k,v in gpu["modes"].items()} == expected
        accounting = list(csv.DictReader((gpu_root/"logs/sacct.psv").open(), delimiter="|"))
        allocations = [r for r in accounting if "." not in r["JobID"] and r["JobID"].startswith("24888989_")]
        assert len(allocations) == 2 and all(r["State"] == "COMPLETED" for r in allocations)
        assert any(r["JobID"] == "24888990" and r["State"] == "COMPLETED" for r in accounting)
        allocated = sum(int(r["ElapsedRaw"]) for r in allocations)
        queue = [(datetime.fromisoformat(r["Start"])-datetime.fromisoformat(r["Submit"])).total_seconds() for r in allocations]
        assert len(set(queue)) == 1
        process = sum(r["process_instance_seconds"] for r in gpu["modes"].values())
        text = (f"All eight CUDA probe records were collected from the two completed GPU array cells (job \\code{{24888989}}), and the dependent analysis job \\code{{24888990}} completed. "
            f"The clean pair passed the retrospective readiness assessment; corrupted-output, missing-checkpoint and runtime-failure pairs were blocked. "
            f"Slurm reports {allocated} allocated MIG-instance seconds across the two cells, with {int(queue[0])} seconds of queue delay for each. "
            f"The timed probe computations sum to {process:.3f} instance-seconds; the difference includes environment setup, imports and job overhead. "
            "These are measurements of this small integration workload, not saved production compute or evidence about an agent's task accuracy.\n")
        (OUT/"gpu_status.tex").write_text(text)
        table=[r"\begin{tabular}{lrrl}",r"\toprule Mode & Attempts & Process seconds & Assessment \\",r"\midrule"]
        for name, row in gpu["modes"].items():
            table.append(name.replace("_", " ")+f" & {row['attempts']} & {row['process_instance_seconds']:.3f} & "+("ready" if row["ready"] else "blocked")+r" \\")
        table += [r"\bottomrule",r"\end{tabular}"]
        (OUT/"gpu_table.tex").write_text("\n".join(table)+"\n")
    map_root = ROOT/"experiments/results/mapcoder"
    if (map_root/"STATUS.json").exists():
        status = json.loads((map_root/"STATUS.json").read_text())
        if status["status"] in ("queued", "running"):
            (OUT/"mapcoder_status.tex").write_text(
                "The initial MapCoder arrays were canceled while pending: first to repair carriage-return configuration defects, then to use the site's documented interactive debugging route after batch admission had no estimated start. "
                +"A MIG interactive request was also canceled after resource inspection found drained nodes and occupied eligible slices. "
                +"At the archived status check, full-H100 interactive allocation \\code{"+status["job_id"]+"} was "+status["status"]+" for two sequential smoke executions under a separate plan identity. No task-success or readiness result is asserted before collection.\n")
    if (map_root/"assessment/assessment.json").exists():
        assessment = json.loads((map_root/"assessment/assessment.json").read_text())
        evidence = json.loads((map_root/"assessment/evidence.json").read_text())["attempts"]
        assert len(evidence) == 2 and {r["rep"] for r in evidence} == {0,1}
        assert all(r["calls"] > 0 for r in evidence if r["status"] == "ok")
        calls = [r["calls"] for r in evidence]
        solved = [r.get("scientific_task_solved") for r in evidence]
        ready = "passed" if assessment["ready"] else "blocked"
        text = ("The corrected MapCoder pilot produced two current-plan records after the first array was canceled while pending to fix carriage-return configuration defects. "
            f"The two fresh executions made {calls[0]} and {calls[1]} local-model calls; their task-correctness outcomes were {str(solved[0]).lower()} and {str(solved[1]).lower()}. "
            f"The evidence assessment {ready}. "
            "These observations concern one HumanEval task under a local-model adaptation and do not reproduce aggregate published accuracy. ")
        dispatch = map_root/"assessment/admission-after.txt"
        if dispatch.exists():
            content = dispatch.read_text()
            decision, _ = json.JSONDecoder().raw_decode(content[content.index("{"):])
            if decision["ready"]:
                assert "dry run: nothing submitted" in content
                text += "The input/graph-verifying wrapper also passed and printed a production dry run; no production campaign was dispatched. "
            else:
                text += "The input/graph-verifying wrapper blocked dispatch, so evidence assessment alone did not authorize production. "
        (OUT/"mapcoder_status.tex").write_text(text+"\n")
    if (ROOT/"experiments/results/mapcoder-qwen38/assessment/assessment.json").exists():
        from make_mapcoder_results import generate
        generate(ROOT, OUT)
    implementation_table()
    print("Verified raw counts; generated local results, analyses, subject inventory and plots.")


# Mutation applied by run_local.mutate, the Equation (1) term it violates and the component it belongs to.
OPERATORS = {
    "missing_gpu": ("Remove the stage GPU request", r"$\operatorname{Valid}(P)$", "graph"),
    "bad_dependency": ("Depend on a nonexistent stage", r"$\operatorname{Valid}(P)$", "graph"),
    "runtime_failure": ("Set last status to failed", r"$\operatorname{OK}(e_i)$", "outcome"),
    "missing_probe": ("Drop the checkpoint obligation", r"$O\subseteq C_i$", "outcome"),
    "malformed_output": ("Mark the present output invalid", r"$\operatorname{OutputValid}(e_i)$", "outcome"),
    "stale_identity": ("Change the scientific model", r"$h_i=h$", "identity"),
    "duplicate_attempt": ("Reuse the first attempt ID", "distinct IDs", "identity"),
    "stale_time": ("Move the last record to $t=1$", r"$t-t_i\leq T$", "freshness"),
    "oom": ("Set peak memory to 0.98 (OOM)", r"$m_i\leq m_{\max}$", "memory"),
    "unstable_memory": ("Add 0.12 to the last peak", r"$\Delta_{\mathrm{smoke}}\leq\epsilon$", "memory"),
    "over_budget": ("Charge 1,300 s to the last record", r"$\sum c_i\leq C$", "budget"),
    "missing_accounting": ("Delete the last cost $c_i$", r"finite $c_i>0$", "budget"),
}


REMOVED = {"without_identity": r"$h_i=h$; distinct IDs", "without_outcome": r"$\operatorname{OK}$; $O\subseteq C_i$; output",
           "without_freshness": r"$t-t_i\leq T$", "without_memory": r"$m_i\leq m_{\max}$; $\Delta_{\mathrm{smoke}}\leq\epsilon$",
           "without_budget": r"$|E|\leq K$; $\sum c_i\leq C$; valid $c_i$"}


def analysis_tables(local, faults, counts, ab_counts, seeds):
    names = {f: label for _, fs in POLICY_GROUPS for f, label in fs}
    ablation = list(csv.DictReader((local/"ablation.csv").open()))
    reasons = {f: {r["reasons"] for r in ablation if r["fault"] == f} for f in faults}
    assert all(len(v) == 1 for v in reasons.values())
    code = lambda text: ", ".join(r"\code{"+c.replace("_", r"\_\allowbreak{}")+"}" for c in text.split(";")) if text else r"--- (graph validator)"
    lines = [r"\begin{tabularx}{\textwidth}{>{\raggedright\arraybackslash}p{2.1cm}>{\raggedright\arraybackslash}Yll>{\raggedright\arraybackslash}p{2.9cm}l}",
             r"\toprule Fault family & Mutation & Violated term & Component & Emitted reason codes & First blocker \\", r"\midrule"]
    policies = ["Static", "Smoke proxy", r"\tool{}"]
    for i, f in enumerate(faults):
        mutation, term, part = OPERATORS[f]
        assert counts[i, 0] == 0 and all(counts[i, j] in (0, seeds) for j in (1, 2, 3))
        first = next(policies[j-1] for j in (1, 2, 3) if counts[i, j] == seeds)
        lines.append(f"{names[f]} & {mutation} & {term} & {part.title()} & {code(next(iter(reasons[f])))} & {first}" + r" \\")
    lines += [r"\bottomrule", r"\end{tabularx}"]
    (OUT/"fault_operators.tex").write_text("\n".join(lines)+"\n")
    fault_total = len(faults)*seeds
    lines = [r"\begin{tabularx}{\textwidth}{llrrY}",
             r"\toprule Variant & Removed terms of Eq.~(\ref{eq:ready}) & Blocked & Det.\ (\%) & Fault families that escape \\", r"\midrule",
             rf"Full \tool{{}} & none & {counts[:, 3].sum()}/{fault_total} & {100*counts[:, 3].sum()/fault_total:.1f} & none \\"]
    for j, (key, label) in enumerate(ABLATIONS.items()):
        escaped = [names[f] for i, f in enumerate(faults) if ab_counts[i, j] < seeds]
        false_blocks = sum(r[key] == "0" for r in ablation if r["fault"] == "clean")
        assert false_blocks == 0
        lines.append(f"{label} & {REMOVED[key]} &{ab_counts[:, j].sum()}/{fault_total} & {100*ab_counts[:, j].sum()/fault_total:.1f} & "
                     + "; ".join(escaped) + r" \\")
    lines += [r"\bottomrule", r"\end{tabularx}"]
    (OUT/"ablation_table.tex").write_text("\n".join(lines)+"\n")
    sensitivity = list(csv.DictReader((local/"sensitivity.csv").open()))
    sensitivity_plot(sensitivity, OUT)
    refinement = list(csv.DictReader((local/"refinement.csv").open()))
    refinement_plot(refinement, OUT)
    assert not any(int(r["scientific_changed"]) for r in refinement)
    lines = [r"\begin{tabular}{lrrrrrrrr}", r"\toprule & \multicolumn{4}{c}{$K=4$ (study setting)} & \multicolumn{4}{c}{$K=8$} \\",
             r"\cmidrule(lr){2-5}\cmidrule(lr){6-9} Initial batch & Ready & \shortstack{No\\prop.} & \shortstack{Cap\\hit} & \shortstack{Cost\\(s)} & Ready & \shortstack{No\\prop.} & \shortstack{Cap\\hit} & \shortstack{Cost\\(s)} \\", r"\midrule"]
    for invariant, title in (("1", "Batch-invariant contract"), ("0", "Batch invariance not declared")):
        lines.append(r"\multicolumn{9}{l}{\emph{"+title+r"}} \\")
        for batch in (8, 16, 32, 64, 128):
            cells = []
            for cap in (4, 8):
                subset = [r for r in refinement if r["batch_invariant"] == invariant and int(r["initial_batch"]) == batch and int(r["max_attempts"]) == cap]
                outcome = lambda d: sum(r["decision"] == d for r in subset)
                cells += [outcome("ready"), outcome("blocked_no_refinement"), outcome("blocked_budget"),
                          f"{sum(float(r['charged_seconds']) for r in subset)/len(subset):.0f}"]
            lines.append(f"\\quad {batch} & " + " & ".join(str(c) for c in cells) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (OUT/"refinement_table.tex").write_text("\n".join(lines)+"\n")
    overhead = list(csv.DictReader((local/"overhead.csv").open()))
    manifest = json.loads((local/"analyses-manifest.json").read_text())
    gap = {r["seed"] for r in refinement if r["batch_invariant"] == "1" and r["max_attempts"] == "8" and r["decision"] == "blocked_no_refinement"}
    return {"AblationVariants": len(ABLATIONS), "SensitivityAssessments": sum(int(r["seeds"]) for r in sensitivity),
            "SensitivitySettings": len({(r["parameter"], r["setting"]) for r in sensitivity}),
            "RefinementEpisodes": len(refinement), "RefinementProposals": sum(int(r["proposals"]) for r in refinement),
            "RefinementScienceChanged": sum(int(r["scientific_changed"]) for r in refinement), "HeadroomGapSeeds": len(gap),
            "OverheadRepeats": overhead[0]["repeats"], "OverheadMinAttempts": overhead[0]["attempts"],
            "OverheadMaxAttempts": overhead[-1]["attempts"], "OverheadMinMs": f"{float(overhead[0]['median_ms']):.3f}",
            "OverheadMaxMs": f"{float(overhead[-1]['median_ms']):.1f}", "AnalysisPython": manifest["python"]}


def implementation_table():
    """Module inventory with nonblank line counts measured from the archived sources."""
    modules = [
        ("src/resai/core.py", r"Canonical identity, plan validation, readiness (Eq.~\ref{eq:ready}), refinement, discovery", "New"),
        ("src/resai/pipeline.py", r"Input binding, graph/resource correspondence, dry-run or explicit dispatch", "New"),
        ("src/resai/mcp.py", r"Stdio JSON-RPC server exposing three read/propose tools", "New"),
        ("src/resai/cli.py", r"\code{discover}, \code{gate} and \code{refine} commands", "New"),
        ("hpc/scripts/hpclib.py", r"Matrix expansion, dependency resolution and static graph validation", "Inherited"),
        ("hpc/scripts/run_stage.py", r"Step execution, completion markers and manifests", "Inherited"),
        ("hpc/scripts/audit.py", r"Audit ledger and job watcher", "Inherited"),
        ("hpc/scripts/collect_results.py", r"Result collection across array cells", "Inherited"),
        ("experiments/run_local.py", r"Level A mutation generator and comparator policies", "Study"),
        ("experiments/run_analyses.py", r"Ablation, sensitivity, refinement and overhead analyses", "Study"),
        ("experiments/probe_gpu.py", r"Level B CUDA probes with five obligations", "Study"),
    ]
    lines = [r"\begin{tabularx}{\textwidth}{llrY}", r"\toprule Module & Origin & LOC & Responsibility \\", r"\midrule"]
    for path, role, origin in modules:
        source = ROOT/path
        loc = sum(1 for line in source.read_text(encoding="utf-8").splitlines() if line.strip())
        lines.append(r"\code{"+source.name.replace("_", r"\_")+"} & "+origin+f" & {loc} & {role} "+r"\\")
    lines += [r"\bottomrule", r"\end{tabularx}"]
    (OUT/"implementation_table.tex").write_text("\n".join(lines)+"\n")


if __name__ == "__main__":
    main()
