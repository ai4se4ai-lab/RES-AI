"""Generate descriptive ChatDev results from qualified, collected episode receipts.

Run from any directory with Python. Historical quarantined attempts are excluded
by matching the frozen subset's episode/job/outcome identities, not by glob count.
"""
import collections
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONDITIONS = {
    "direct_native": "Direct native",
    "upstream_static": "Upstream static",
    "upstream_smoke_then_production": "Upstream smoke",
    "resai_full": r"Full \tool{}",
    "no_coverage": "No coverage",
    "no_identity_freshness": "No identity/freshness",
    "no_refinement": "No refinement",
}


def main():
    source = ROOT / "experiments/results/campaign"
    status = json.loads((source / "STATUS.json").read_text())
    subset = status["comparative_subsets"]["ChatDev"]
    assert subset["status"] == "SUBSET_RESOLVED"
    receipts = {}
    for folder in ("comparison", "comparison-v2"):
        for path in (source / folder).rglob("episode.json"):
            row = json.loads(path.read_text())
            key = (row["episode_id"], row["job_id"], row["status"])
            assert key not in receipts, f"Duplicate receipt: {key}"
            receipts[key] = row
    rows = []
    cells = set()
    for queued in subset["queue"]:
        key = (queued["episode_id"], queued["job_id"], queued["status"])
        row = receipts[key]
        assert row["artifact"] == "ChatDev" and row["comparative_episode"]
        cell = (row["condition"], row["paired_seed"], row["episode_class"])
        assert cell not in cells
        cells.add(cell)
        rows.append(row)
    expected = {(c, s, f) for c in CONDITIONS for s in range(5)
                for f in ("clean", "environment_fault", "resource_fault", "output_contract_fault")}
    assert cells == expected and len(rows) == subset["comparative_episodes_completed"] == 140
    assert all(r["status"] in ("PRODUCTION_VALID", "PRODUCTION_INVALID", "POLICY_BLOCKED") for r in rows)
    out = ROOT / "tmp/manuscript-generated"
    out.mkdir(parents=True, exist_ok=True)
    fields = ("episode_id", "job_id", "condition", "paired_seed", "episode_class", "status")
    with (out / "chatdev_episodes.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    tex = [r"\begin{tabular}{lrrrr}", r"\toprule",
           r"Condition & Clean valid & Clean blocked & Fault blocked & Fault invalid \\", r"\midrule"]
    summary = {}
    for condition, label in CONDITIONS.items():
        counts = collections.Counter((r["episode_class"] == "clean", r["status"])
                                     for r in rows if r["condition"] == condition)
        values = [counts[True, "PRODUCTION_VALID"], counts[True, "POLICY_BLOCKED"],
                  counts[False, "POLICY_BLOCKED"], counts[False, "PRODUCTION_INVALID"]]
        assert sum(values) == 20
        summary[condition] = dict(zip(("clean_valid", "clean_blocked", "fault_blocked", "fault_invalid"), values))
        tex.append(label + " & " + " & ".join(map(str, values)) + r" \\")
    tex += [r"\bottomrule", r"\end{tabular}"]
    (out / "chatdev_table.tex").write_text("\n".join(tex) + "\n", encoding="utf-8")
    (out / "chatdev_summary.json").write_text(json.dumps({
        "source_report_utc": status["updated_at_utc"],
        "qualified_episodes": len(rows), "conditions": summary,
        "outcomes": dict(collections.Counter(r["status"] for r in rows)),
        "historical_quarantined_attempts": subset["historical_quarantined_episodes"],
        "campaign_allocated_h100_seconds": status["h100_allocated_seconds"],
        "campaign_reserved_h100_seconds": status["h100_reserved_seconds"],
    }, indent=2) + "\n", encoding="utf-8")
    print("Verified 140 qualified ChatDev receipts and all 7 x 5 x 4 cells; generated table, CSV and summary.")


if __name__ == "__main__":
    main()
