"""Activate a prospective staging allocation without changing scientific inputs or global cap."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
from budget import validate_allocation

root=Path(__file__).resolve().parents[2]
plan_path=root/'experiments/campaign/plan.json'
plan=json.loads(plan_path.read_text())
ledger_path=root/'gpu-budget-ledger.json'
lock=ledger_path.with_suffix('.lock')
descriptor=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
try:
    pointer_path=root/'budget-allocation-active.json'
    if pointer_path.exists():
        raise RuntimeError('active allocation already exists; review rather than overwrite')
    ledger=json.loads(ledger_path.read_text())
    report=json.loads((root/'campaign-status.json').read_text())
    observed=dt.datetime.fromisoformat(report['updated_at_utc'])
    if report.get('accounting_query_error') or (dt.datetime.now(dt.timezone.utc)-observed).total_seconds()>300:
        raise RuntimeError('successful fresh Slurm accounting required before activation')
    protocol_path=root/'comparison/chatdev-v2/protocol.json'
    if json.loads(protocol_path.read_text())['master_protocol_sha256']!=hashlib.sha256(plan_path.read_bytes()).hexdigest():
        raise RuntimeError('frozen master protocol changed; no budget activation permitted')
    if any(not r.get('settled') for r in ledger['reservations']):
        raise RuntimeError('reconcile outstanding allocations before activation')
    folder=root/'experiments/campaign/budget-allocations'
    folder.mkdir(exist_ok=True)
    path=folder/'20261026-chatdev-stage-2.json'
    if path.exists():
        raise RuntimeError('refusing to replace a budget amendment')
    charges={s['name']:sum(r['allocated_seconds'] for r in ledger['reservations'] if r['subject']==s['name']) for s in plan['subjects']}
    before=folder/'20261026-chatdev-stage-2-ledger-before.json'
    with before.open('x') as stream:
        stream.write(ledger_path.read_text())
    amendment=dict(amendment_id='20261026-chatdev-stage-2',campaign_id=plan['campaign_id'],
        master_protocol_sha256=hashlib.sha256(plan_path.read_bytes()).hexdigest(),
        global_h100_cap_seconds=plan['initial_h100_budget_seconds'],artifact_ceilings_seconds={'ChatDev':28800},
        authorization='User: do what is required and continue; existing initial 24 H100-hour global cap remains in force.',
        reason='Initial per-candidate staging guard stopped after 29 qualified cases despite unused global allowance. Prospectively allocate an eight-hour cumulative ceiling to the validated runnable ChatDev subset; no episode, model, task, source or case ordering changes.',
        allocation_semantics='Ceilings are admission maxima, not reservations or guaranteed shares. The unchanged global cap supersedes all candidate ceilings; past setup, failures and quarantined runs remain charged. Other candidate ceilings remain unchanged.',
        activated_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        ledger_before_activation_sha256=hashlib.sha256(ledger_path.read_bytes()).hexdigest(),
        scientific_protocol_sha256=hashlib.sha256(protocol_path.read_bytes()).hexdigest(),
        budget_guard_sha256=hashlib.sha256((root/'experiments/campaign/budget.py').read_bytes()).hexdigest(),
        charged_seconds_at_activation=charges,global_charged_seconds_at_activation=sum(charges.values()))
    validate_allocation(plan,amendment,amendment['master_protocol_sha256'])
    path.write_text(json.dumps(amendment,indent=2)+'\n')
    pointer=dict(path=path.relative_to(root).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    with pointer_path.open('x') as stream:
        stream.write(json.dumps(pointer,indent=2)+'\n')
    print(json.dumps(dict(activation=pointer,amendment=amendment),indent=2))
finally:
    os.close(descriptor)
    lock.unlink()
