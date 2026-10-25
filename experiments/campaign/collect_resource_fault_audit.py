"""Preserve a failed fault injection without changing frozen raw episode receipts."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import tarfile

root=Path(__file__).resolve().parents[2]
folder=root/'comparison/chatdev'
audit=json.loads((folder/'RESOURCE_FAULT_AUDIT.json').read_text())
status_path=folder/'status.json'
status=json.loads(status_path.read_text())
finished=quarantined=qualified=0
for row in status['queue']:
    receipt=(root/row['case']).parent/'results/episode.json'
    if not receipt.exists():
        if '-resource_fault-' in row['episode_id'] and row.get('job_id'):
            row.update(status='QUARANTINED_ABORTED_FAULT_NOT_ESTABLISHED')
            quarantined+=1
        continue
    raw=json.loads(receipt.read_text())
    if raw['status'] in ('PRODUCTION_VALID','PRODUCTION_INVALID','POLICY_BLOCKED'):
        finished+=1
        if '-resource_fault-' not in row['episode_id']:
            qualified+=1
    if '-resource_fault-' in row['episode_id']:
        row.update(observed_execution_status=raw['status'],status='QUARANTINED_FAULT_NOT_ESTABLISHED')
        quarantined+=1
status.update(status='STOPPED_FOR_AUDIT',error=audit['reason'],
    execution_receipts_completed=finished,quarantined_episodes=quarantined,
    comparative_episodes_completed=qualified,
    updated_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
status_path.write_text(json.dumps(status,indent=2)+'\n')
out=root/'collected-resource-audit'
out.mkdir(exist_ok=True)
archive=out/('resource-audit-'+os.environ['SLURM_JOB_ID']+'.tar.gz')
with tarfile.open(archive,'x:gz') as bundle:
    for name in ['RESOURCE_FAULT_AUDIT.json','status.json','status-before-resource-audit-20261025.json','protocol.json']:
        bundle.add(folder/name,arcname='audit/'+name)
    bundle.add(root/'campaign-status.json',arcname='campaign-status.json')
    bundle.add(root/'gpu-budget-ledger.json',arcname='gpu-budget-ledger.json')
    for row in status['queue']:
        if '-resource_fault-' in row['episode_id'] and row.get('job_id'):
            bundle.add((root/row['case']).parent,arcname='episodes/'+row['episode_id'])
sha=hashlib.sha256(archive.read_bytes()).hexdigest()
with (out/'SHA256SUMS').open('a') as stream:
    stream.write(sha+'  '+archive.name+'\n')
print(json.dumps(dict(archive=str(archive),sha256=sha,bytes=archive.stat().st_size,
    finished=finished,quarantined=quarantined,qualified=qualified)))
