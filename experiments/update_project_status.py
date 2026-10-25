"""Refresh the project status document from local evidence; append one journal row."""
import argparse
import csv
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import tempfile
import traceback

ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = Path("docs/EMSE/support/AI_AGENT_PROJECT_EXECUTION_PLAN.md")
BEGIN = "<!-- experiment-status:start -->"
END = "<!-- experiment-status:end -->"
HISTORY = "## 14. Hourly update history"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def evidence_link(path):
    return f"[{path}](../../../{path})"


def inspect_evidence(root):
    results = root/"experiments/results"
    checks, problems, active = [], [], []

    def check(name, operation):
        try:
            detail = operation()
            checks.append({"name": name, "status": "COMPLETE", "detail": detail})
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            checks.append({"name": name, "status": "ATTENTION", "detail": message})
            problems.append(name+": "+message)

    def controller():
        summary = read_json(results/"local/summary.json")
        with (results/"local/decisions.csv").open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        if len(rows) != summary["decisions"]:
            raise ValueError("decision CSV disagrees with summary")
        for name in ("ablation", "refinement", "sensitivity", "overhead"):
            if not (results/f"local/{name}.csv").is_file():
                raise FileNotFoundError(name+" analysis")
        return f"{len(rows):,} synthetic decisions; {summary['seeds']} variants; {summary['fault_families']} fault families; analysis CSVs present"

    def cuda():
        rows = [read_json(p) for p in (results/"nibi/results/gpu").glob("*.json")]
        expected = {(mode, rep) for mode in ("clean", "corrupt_output", "missing_checkpoint", "runtime_failure") for rep in (0, 1)}
        if len(rows) != 8 or {(r['mode'], r['rep']) for r in rows} != expected:
            raise ValueError("expected four modes times two repeats")
        summary = read_json(results/"nibi/reanalysis/gpu-summary.json")
        if not summary["modes"]["clean"]["ready"] or any(v["ready"] for k, v in summary["modes"].items() if k != "clean"):
            raise ValueError("clean/fault admission results disagree with the contract")
        return "8 records; clean pair admitted; all 3 injected fault modes blocked (expected results)"

    def model(folder):
        status = read_json(results/folder/"STATUS.json")
        if status["status"] != "completed":
            if status["status"] in ("queued", "running", "pending", "downloading"):
                active.append(folder+": "+status["status"])
            raise ValueError("last recorded run state: "+status["status"])
        evidence = read_json(results/folder/"assessment/evidence.json")["attempts"]
        if len(evidence) != 2 or {r["rep"] for r in evidence} != {0, 1}:
            raise ValueError("missing independent repeated records")
        required = {"imports", "model_init", "task_execution", "output_schema", "resume"}
        if any(r["status"] != "ok" or not r["output_valid"] or not required.issubset(r["passed_probes"]) for r in evidence):
            raise ValueError("one or more execution probes failed")
        calls = 0
        for p in (results/folder/"results/mapcoder").glob("rep*/attempt-*/calls.json"):
            calls += len(read_json(p))
        if calls != sum(r["calls"] for r in evidence):
            raise ValueError("recorded call counts disagree with raw traces")
        assessment = read_json(results/folder/"assessment/assessment.json")
        solved = sum(r.get("scientific_task_solved") is True for r in evidence)
        seconds = sum(r["gpu_seconds"] for r in evidence)
        return f"{solved}/2 HumanEval/0 repeats solved; {calls} calls; collection-time gate {'passed' if assessment['ready'] else 'blocked'}; {seconds:.3f} timed process seconds"

    def archives(directory=results):
        count = 0
        for line in (directory/"COLLECTED-SHA256SUMS.txt").read_text().splitlines():
            digest, name = line.split("  ", 1)
            path = (directory/name).resolve()
            if not path.is_relative_to(directory.resolve()):
                raise ValueError("archive path escapes results directory")
            with path.open("rb") as stream:
                if hashlib.file_digest(stream, "sha256").hexdigest() != digest:
                    raise ValueError("checksum mismatch: "+name)
            count += 1
        if not count:
            raise ValueError("empty archive checksum inventory")
        return f"{count} collected archive SHA-256 checksums verified, including the failed attempt and retired-run history"

    check("Controller study and analyses", controller)
    check("Nibi CUDA integration", cuda)
    check("MapCoder / Qwen2.5-Coder-7B", lambda: model("mapcoder"))
    check("MapCoder / Qwen3.8-27B Q4_K_M", lambda: model("mapcoder-qwen38"))
    check("Collected data integrity", archives)
    if (results/'campaign/COLLECTED-SHA256SUMS.txt').exists():
        check("Campaign collection integrity", lambda: archives(results/'campaign'))
    try:
        subjects = read_json(root/"experiments/subjects.json")["subjects"]
    except Exception as exc:
        subjects = []
        problems.append("Candidate inventory unavailable: "+str(exc))
    candidates = ", ".join(s["name"] for s in subjects)
    campaign = None
    campaign_path = results/'campaign/STATUS.json'
    if campaign_path.exists():
        campaign = read_json(campaign_path)
        if campaign.get('accounting_query_error'):
            problems.append('Nibi accounting query failed; current allocation state is unknown: '+campaign['accounting_query_error'])
        for name,subset in campaign.get('comparative_subsets',{}).items():
            if subset.get('status')=='STOPPED_FOR_AUDIT':
                problems.append(name+' automatic queue stopped for audit: '+str(subset.get('error')))
        plan_path = root/'experiments/campaign/plan.json'
        if hashlib.sha256(plan_path.read_bytes()).hexdigest() != campaign['protocol_sha256']:
            problems.append('Campaign protocol differs from its frozen status identity')
        if campaign.get('h100_allocated_seconds',0)+campaign.get('h100_reserved_seconds',0) > campaign['initial_h100_budget_seconds']:
            problems.append('Campaign allocation/reservation exceeds the initial GPU budget')
        if campaign['status'] not in ('COMPLETE','NOT_STARTED'):
            active.append('twelve-artifact campaign: '+campaign['status'])
    # Inventory entries describe prospective subjects, not completed executions.
    return {"checks": checks, "problems": problems, "candidates": candidates,
            "candidate_count": len(subjects), "active": active, "campaign": campaign}


def render_snapshot(snapshot, stamp, scheduler):
    state = "ATTENTION — evidence needs investigation" if snapshot["problems"] else "PILOT MILESTONE COMPLETE — broader campaign needs review"
    campaign = snapshot.get('campaign')
    campaign_state = campaign['status'] if campaign else 'NOT STARTED'
    if campaign and not snapshot['problems']:
        state = 'PILOTS COMPLETE; TWELVE-ARTIFACT CAMPAIGN '+campaign_state
    lines = [BEGIN, f"**Last checked: {stamp} (UTC).**", "",
             f"**Where we are: {state}.**", "",
             "The implemented controller, CUDA, and one-artifact/two-model pipelines have collected results. "
             +("The full campaign is authorized and underway; completed comparative episodes are reported separately below. " if campaign else "The twelve-artifact comparative campaign has not been executed. ")
             +("Last recorded active work (live Nibi state not checked): "+", ".join(snapshot["active"])+"." if snapshot["active"] else "No experiment is currently recorded as running in the collected status files."), "",
             "| Experiment / deliverable | Status | Verified evidence |",
             "|---|---|---|"]
    for row in snapshot["checks"]:
        detail = row["detail"].replace("|", "/").replace("\n", " ")
        lines.append(f"| {row['name']} | {row['status']} | {detail} |")
    campaign_detail = (f"{campaign.get('comparative_episodes_completed',0)}/{campaign['potential_episodes']} potential comparative episodes reported complete; H100 allocated {campaign.get('h100_allocated_seconds',0)} s, reserved {campaign.get('h100_reserved_seconds',0)} s; initial cap {campaign['initial_h100_budget_seconds']/3600:g} GPU-hours; last campaign report {campaign['updated_at_utc']}" if campaign else f"{snapshot['candidate_count']} candidates inventoried; runnable configurations and comparative results remain pending")
    lines += [f"| Twelve-artifact comparison | {campaign_state} | {campaign_detail} |", ""]
    if campaign and campaign.get('subjects'):
        lines += [f"**Campaign preparation:** {campaign.get('source_snapshots_acquired',0)}/{len(campaign['subjects'])} source snapshots acquired; {campaign.get('dependency_import_checks_passed',0)} dependency import checks passed. These are preparation checks, not completed comparative episodes.","",
                  '| Candidate | Source check | Latest dependency check | Native validation | Comparative episodes |',
                  '|---|---|---|---|---|']
        for subject in campaign['subjects']:
            values=[subject['name'],subject['campaign_status'],subject.get('latest_dependency_status','NOT_VALIDATED'),subject.get('latest_native_status','NOT_RUN'),str(subject.get('comparative_episodes_completed',0))]
            lines.append('| '+' | '.join(v.replace('|','/').replace('\n',' ') for v in values)+' |')
        lines.append('')
        pending=[r for r in campaign.get('gpu_budget_ledger',{}).get('reservations',[]) if r.get('job_id') and not r.get('settled') and r.get('purpose')=='native_validation']
        if pending:
            lines += ['**Native feasibility allocations (not comparative episodes):** '+ '; '.join(f"{r['subject']} job `{r['job_id']}`: {r.get('last_observed_state','unknown')}; {r['reserved_seconds']} H100 seconds originally reserved including termination headroom; collector `{r.get('collector_job_id','not recorded')}`" for r in pending)+'.', '']
        for name,subset in campaign.get('comparative_subsets',{}).items():
            lines += [(f"**{name} comparative subset:** {subset['status']}; {subset['comparative_episodes_completed']}/{subset['potential_episodes']} episodes resolved; {subset['comparative_episodes_submitted']} submitted. "+(subset.get('error') or '')).rstrip(),'']
            if subset.get('quarantined_episodes'):
                lines += [f"**{name} data audit:** {subset['execution_receipts_completed']} completed execution receipts retained; {subset['quarantined_episodes']} fault-affected attempts quarantined, including any aborted attempt. Quarantined attempts are excluded from the completed comparative count above.",'']
    if campaign:
        observed=dt.datetime.fromisoformat(campaign['updated_at_utc'].replace('Z','+00:00'))
        checked=dt.datetime.fromisoformat(stamp.replace('Z','+00:00'))
        age=max(0,(checked-observed).total_seconds())
        if age > 7200 and campaign_state not in ('COMPLETE','NOT_STARTED'):
            lines += [f'**Nibi observation is stale:** the latest collected campaign report is {age/3600:.1f} hours old. Current queue state and progress are unknown until a fresh report is collected.', '']
    lines += [
              "**Current next step:** "+(campaign['next_action'] if campaign else 'review the pilot evidence and manuscript; agree on eligible subjects, comparison conditions, budgets, and acceptance criteria before implementing the larger campaign.'), "",
              "**Accounting:** CUDA pilot: 81 MIG-instance seconds. Original MapCoder pilot: 383 H100 seconds. "
              "Qwen3.8: 548 successful H100 seconds plus 86 for the retained failed attempt (634 total). "
              "These are historical collected measurements with different accounting boundaries; this is not a resource-savings comparison.", "",
              "**Data:** "+evidence_link("experiments/results/COLLECTION.md")+"; "+evidence_link("experiments/results/mapcoder-attempts.csv")+"; "+evidence_link("experiments/results/mapcoder-qwen38/provenance/sacct-final.psv")+".", "",
              f"**Hourly updater:** {scheduler}. Checks collected local evidence and appends section 14 on every invocation, including unchanged checks. "
              "It does not authenticate to Nibi, collect new remote outputs, launch jobs, or independently verify the live queue. "
              "Future remote runs must supply updated local evidence/status files; queued/running or missing records are flagged for investigation. "
              "An hourly document timestamp is an evidence-check timestamp, not a new experiment execution timestamp."]
    if snapshot["problems"]:
        lines += ["", "**Issues found:**"]+["- "+p for p in snapshot["problems"]]
    lines += [END]
    return "\n".join(lines)


def update_text(text, block, stamp, summary):
    if text.count(BEGIN) != 1 or text.count(END) != 1 or text.count(HISTORY) != 1:
        raise ValueError("status/history markers missing or duplicated; refusing to overwrite manual content")
    start, end = text.index(BEGIN), text.index(END)+len(END)
    text = text[:start]+block+text[end:]
    # The journal is deliberately the last section; never replace its earlier rows.
    return text.rstrip()+f"\n| {stamp} | {summary.replace('|', '/').replace(chr(10), ' ')} |\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reason", default="hourly scheduled evidence check")
    args = parser.parse_args()
    stamp = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    state_dir = ROOT/"experiments/results/status-maintenance"
    state_dir.mkdir(parents=True, exist_ok=True)
    receipt = {"timestamp_utc": stamp, "reason": args.reason}
    try:
        snapshot = inspect_evidence(ROOT)
        scheduler_path = state_dir/"scheduler.json"
        scheduler = "registration pending"
        if scheduler_path.exists():
            config = read_json(scheduler_path)
            first = dt.datetime.fromisoformat(config['next_run_utc'].replace('Z', '+00:00'))
            now = dt.datetime.now(dt.timezone.utc)
            next_due = first+dt.timedelta(hours=max(0, int((now-first).total_seconds()//3600)+1))
            nominal = next_due.isoformat(timespec='seconds').replace('+00:00', 'Z')
            scheduler = f"Windows Task Scheduler `{config['task_name']}`; every 1 hour; next nominal update {nominal}; registration verified {config['registered_at_utc']}; computer on and user signed in required"
        fingerprint = hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()
        previous_path = state_dir/"last-update.json"
        previous = read_json(previous_path) if previous_path.exists() else {}
        change = "evidence changed" if previous.get("fingerprint") != fingerprint else "no evidence changes"
        completed = sum(c["status"] == "COMPLETE" for c in snapshot["checks"])
        campaign = snapshot.get('campaign')
        campaign_note = (f"{campaign['status']}, {campaign.get('comparative_episodes_completed',0)}/{campaign['potential_episodes']} potential episodes, cap {campaign['initial_h100_budget_seconds']/3600:g} H100 hours" if campaign else 'NOT STARTED')
        summary = f"{args.reason}; {change}; {completed}/{len(snapshot['checks'])} evidence checks complete; twelve-artifact campaign {campaign_note}"
        if snapshot["problems"]:
            summary += "; ATTENTION: "+"; ".join(snapshot["problems"])
        document = ROOT/DOCUMENT
        before = document.read_bytes()
        updated = update_text(before.decode("utf-8"), render_snapshot(snapshot, stamp, scheduler), stamp, summary)
        # Avoid overwriting an IDE edit made while the evidence checks ran.
        with tempfile.NamedTemporaryFile(dir=document.parent, suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(updated.encode("utf-8"))
        try:
            if document.read_bytes() != before:
                raise RuntimeError("document changed concurrently; retry on the next scheduled check")
            os.replace(temporary, document)
        finally:
            temporary.unlink(missing_ok=True)
        receipt.update(ok=True, fingerprint=fingerprint, checks=snapshot["checks"], summary=summary)
    except Exception as exc:
        receipt.update(ok=False, error=str(exc), traceback=traceback.format_exc())
    (state_dir/"last-update.json").write_text(json.dumps(receipt, indent=2)+"\n", encoding="utf-8")
    if __import__("sys").stdout is not None:
        print(json.dumps(receipt))
    return 0 if receipt["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
