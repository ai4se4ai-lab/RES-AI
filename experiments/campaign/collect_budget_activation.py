"""Archive the operational budget amendment separately from frozen scientific inputs."""
import hashlib
import json
import os
from pathlib import Path
import tarfile

root=Path(__file__).resolve().parents[2]
out=root/'collected-budget-amendment'
out.mkdir(exist_ok=True)
archive=out/('budget-amendment-'+os.environ['SLURM_JOB_ID']+'.tar.gz')
paths=[root/n for n in ['budget-allocation-active.json','gpu-budget-ledger.json','campaign-status.json',
    'experiments/campaign/budget.py','experiments/campaign/activate_budget_allocation.py',
    'experiments/campaign/resume-budget-stage-2.sh','experiments/campaign/collect_budget_activation.py',
    'experiments/campaign/plan.json','comparison/chatdev-v2/protocol.json','comparison/chatdev-v2/status.json']]
paths+=list((root/'experiments/campaign/budget-allocations').glob('*.json'))
with tarfile.open(archive,'x:gz') as bundle:
    for path in paths:
        bundle.add(path,arcname=path.relative_to(root).as_posix(),recursive=False)
sha=hashlib.sha256(archive.read_bytes()).hexdigest()
with (out/'SHA256SUMS').open('a') as stream:
    stream.write(sha+'  '+archive.name+'\n')
print(json.dumps(dict(archive=str(archive),sha256=sha,bytes=archive.stat().st_size)))
