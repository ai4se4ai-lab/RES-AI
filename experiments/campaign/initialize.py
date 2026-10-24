"""Freeze the author-requested campaign inventory, design, and initial compute cap."""
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    subjects = json.loads((ROOT/'experiments/subjects.json').read_text())['subjects']
    plan = {
        'campaign_id': 'resai-campaign-20261024',
        'authorized_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'authorization': 'User requested paper integration followed by the full experiment; initial cap 24 H100 GPU-hours.',
        'initial_h100_budget_seconds': 86400,
        'maximum_reserved_h100_seconds_per_artifact': 7200,
        'budget_scope': 'New campaign GPU allocations, including setup, validation, failures and retries; earlier archived pilots excluded. CPU allocations reported separately.',
        'conditions': ['direct_native', 'upstream_static', 'upstream_smoke_then_production', 'resai_full', 'no_coverage', 'no_identity_freshness', 'no_refinement'],
        'paired_seeds': [0, 1, 2, 3, 4],
        'episode_classes': ['clean', 'environment_fault', 'resource_fault', 'output_contract_fault'],
        'potential_episodes': len(subjects)*7*5*4,
        'primary_local_model': 'qwen3.8:27b',
        'model_api_digest': 'aaee06c39dcf2437cde036998d960e1fc1494b8191be7cc9657d01e509097813',
        'ollama_version': '0.40.10',
        'execution_policy': 'Native artifact adapters and artifact-specific oracles must pass feasibility before comparative submission. No generic stand-in algorithm. Missing source, dependencies, sandbox or model compatibility remains visible. Stop submitting at the initial GPU cap.',
        'status': 'FEASIBILITY',
        'subjects': [{**s, 'campaign_status':'PENDING_FEASIBILITY', 'comparative_episodes_completed':0} for s in subjects],
    }
    path = ROOT/'experiments/campaign/plan.json'
    if path.exists():
        raise FileExistsError('Campaign already initialized; preserve its original protocol and update status separately')
    path.write_text(json.dumps(plan,indent=2)+'\n',newline='\n')
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    (path.parent/'plan.sha256').write_text(digest+'  plan.json\n')
    out = ROOT/'experiments/results/campaign'
    out.mkdir(parents=True, exist_ok=True)
    status = dict(campaign_id=plan['campaign_id'],status='FEASIBILITY',protocol_sha256=digest,
        initial_h100_budget_seconds=86400, h100_allocated_seconds=0, h100_reserved_seconds=0,
        potential_episodes=plan['potential_episodes'],comparative_episodes_completed=0,
        paper_qwen38_integration='COMPLETE',next_action='Fetch exact source revisions and inspect native entrypoints, dependencies, datasets, model endpoints and sandbox support on Nibi.',
        updated_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),subjects=plan['subjects'])
    (out/'STATUS.json').write_text(json.dumps(status,indent=2)+'\n',newline='\n')
    print(json.dumps({'campaign_id':plan['campaign_id'],'potential_episodes':plan['potential_episodes'],'h100_hours_cap':24,'protocol_sha256':digest}))


if __name__ == '__main__':
    main()
