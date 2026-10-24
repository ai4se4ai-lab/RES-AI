"""Submit one frozen ChatDev episode at a time, after actual budget reconciliation."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from budget import reserve

root=Path(__file__).resolve().parents[2]
os.chdir(root)
folder=root/'comparison/chatdev'
protocol=json.loads((folder/'protocol.json').read_text())
proof=json.loads((folder/'preflight.json').read_text())
if proof.get('status')!='COMPARATIVE_ADAPTER_PREFLIGHT_PASSED':
    raise ValueError('native comparative adapter CPU checks have not passed')
for name,expected in protocol['inputs'].items():
    if hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected:
        raise ValueError('frozen comparative implementation changed: '+name)
ledger_path=root/'gpu-budget-ledger.json'
lock=ledger_path.with_suffix('.lock')
descriptor=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
try:
    ledger=json.loads(ledger_path.read_text())
    campaign=json.loads((root/'experiments/campaign/plan.json').read_text())
    case_entries={e['episode_id']:e for e in ledger['reservations'] if e.get('episode_id')}
    rows=[]
    for planned in protocol['queue']:
        row=dict(planned)
        entry=case_entries.get(row['episode_id'])
        path=root/row['case']
        result_path=path.parent/'results/episode.json'
        if entry:
            row.update(job_id=entry.get('job_id'),collector_job_id=entry.get('collector_job_id'))
            if result_path.exists():
                row['status']=json.loads(result_path.read_text())['status']
            elif entry.get('settled'):
                row['status']='ALLOCATION_ENDED_WITHOUT_EPISODE_RECEIPT'
            else:
                row['status']='SUBMITTED'
        rows.append(row)
    def report(status,error=None):
        data=dict(status=status,artifact='ChatDev',potential_episodes=140,
            comparative_episodes_completed=sum(r['status'] in ('POLICY_BLOCKED','PRODUCTION_VALID','PRODUCTION_INVALID') for r in rows),
            comparative_episodes_submitted=sum(r.get('job_id') is not None for r in rows),
            queue=rows,error=error,updated_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
        (folder/'status.json').write_text(json.dumps(data,indent=2)+'\n')
    if any(r['status']=='SUBMITTED' for r in rows):
        report('RUNNING_OR_QUEUED')
        raise SystemExit(0)
    problematic=[r for r in rows if r['status'] in ('IMPLEMENTATION_ERROR','UNEXECUTED_MISSING_CLEAN_CACHE','ALLOCATION_ENDED_WITHOUT_EPISODE_RECEIPT')]
    if problematic:
        report('STOPPED_FOR_AUDIT','No automatic resubmission after unresolved protocol execution: '+problematic[0]['episode_id'])
        raise SystemExit(1)
    remaining=[r for r in rows if r['status']=='PLANNED']
    if not remaining:
        report('SUBSET_RESOLVED')
        raise SystemExit(0)
    row=remaining[0]
    path=root/row['case']
    if hashlib.sha256(path.read_bytes()).hexdigest()!=row['case_sha256']:
        raise ValueError('frozen episode specification changed')
    admission={k:proof.get(k) for k in ('native_smoke_passed','oracle_passed','sandbox_validated','model_endpoint_verified')}
    try:
        entry=reserve(campaign,ledger,'ChatDev',900,admission,purpose='comparison')
    except ValueError as exc:
        report('INITIAL_BUDGET_LIMITED',str(exc))
        raise SystemExit(0)
    entry.update(episode_id=row['episode_id'],case=row['case'],case_sha256=row['case_sha256'])
    def save():
        temp=ledger_path.with_suffix('.tmp')
        temp.write_text(json.dumps(ledger,indent=2)+'\n')
        os.replace(temp,ledger_path)
    save()
    try:
        submit=subprocess.run(['sbatch','--parsable','--output='+str(path.parent/'slurm.out'),
            'experiments/campaign/chatdev-comparison.sh',str(path),row['case_sha256']],
            capture_output=True,text=True,timeout=30,check=True)
        entry['job_id']=submit.stdout.strip().split(';')[0]
        if not entry['job_id'].isdigit():
            raise ValueError('ambiguous scheduler response')
        save()
        collector=subprocess.run(['sbatch','--parsable','--dependency=afterany:'+entry['job_id'],
            'experiments/campaign/collect-chatdev-comparison.sh',str(path)],
            capture_output=True,text=True,timeout=30,check=True)
        entry['collector_job_id']=collector.stdout.strip().split(';')[0]
        row.update(status='SUBMITTED',job_id=entry['job_id'],collector_job_id=entry['collector_job_id'])
        report('RUNNING_OR_QUEUED')
        print(json.dumps(entry,indent=2))
    except Exception as exc:
        entry['submission_error']=str(exc)
        if isinstance(exc,subprocess.CalledProcessError):
            entry.update(submission_stdout=exc.stdout,submission_stderr=exc.stderr)
        report('SUBMISSION_REQUIRES_RECONCILIATION',str(exc))
        raise
    finally:
        save()
finally:
    os.close(descriptor)
    lock.unlink()
