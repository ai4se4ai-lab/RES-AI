"""Archive public repository availability and revisions. No execution eligibility claim."""
import concurrent.futures
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SUBJECTS = [
    ("SWE-agent", "SWE-agent/SWE-agent", "2405.15793", "repository repair"),
    ("OpenHands", "OpenHands/OpenHands", "2407.16741", "software development"),
    ("AutoCodeRover", "AutoCodeRoverSG/auto-code-rover", "2404.05427", "structure-aware repair"),
    ("MetaGPT", "FoundationAgents/MetaGPT", "2308.00352", "role-based development"),
    ("ChatDev", "OpenBMB/ChatDev", "2307.07924", "communicative development"),
    ("AgentCoder", "huangd1999/AgentCoder", "2312.13010", "generation and testing"),
    ("MapCoder", "Md-Ashraful-Pramanik/MapCoder", "2405.11403", "competitive programming"),
    ("RepairAgent", "sola-st/RepairAgent", "2403.17134", "Java repair"),
    ("ExecutionAgent", "sola-st/ExecutionAgent", "2412.10133", "test environment setup"),
    ("CodeAct", "xingyaoww/code-act", "2402.01030", "executable code actions"),
    ("HyperAgent", "FSoft-AI4Code/HyperAgent", "2409.16299", "generalist SE"),
    ("AgileCoder", "FSoft-AI4Code/AgileCoder", "2406.11912", "sprint-based development")]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "RES-AI-research-artifact"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def verify(subject):
    name, repo, paper, area = subject
    row = {"name": name, "repository": "https://github.com/"+repo, "paper": "https://arxiv.org/abs/"+paper,
           "area": area, "execution_status": "not_run", "selection": "purposive candidate; feasibility screening pending"}
    try:
        metadata = fetch("https://api.github.com/repos/"+repo)
        commit = fetch("https://api.github.com/repos/"+repo+"/commits/"+metadata["default_branch"])
        row.update(available=True, default_branch=metadata["default_branch"], retrieved_head=commit["sha"],
                   license=(metadata.get("license") or {}).get("spdx_id"), archived=metadata["archived"])
    except Exception as exc:
        row.update(available=False, error=str(exc))
    return row


if __name__ == "__main__":
    out = Path(__file__).resolve().parent/"subjects.json"
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(verify, SUBJECTS))
    out.write_text(json.dumps({"retrieved_at": datetime.now(timezone.utc).isoformat(),
        "selection_method": "Purposive expert candidate set, not a systematic literature search or completed screening funnel",
        "subjects": rows}, indent=2)+"\n")
    print(f"{sum(r['available'] for r in rows)}/{len(rows)} repositories available; saved {out}")
