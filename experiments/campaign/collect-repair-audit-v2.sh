#!/bin/bash
#SBATCH --job-name=resai-repair-audit-collection
#SBATCH --account=def-mbabaei
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:10:00
#SBATCH --output=repair-audit-collection-%j.out
set -euo pipefail
cd /project/6108124/mbabaei/resai-campaign-20261024
module load StdEnv/2023 python/3.11
PYTHONPATH=src:experiments/campaign python experiments/campaign/report_progress.py
python - <<'PY'
from pathlib import Path
import datetime as dt
import hashlib,json,os,subprocess,tarfile
root=Path.cwd();out=root/'collected-repair-audit';out.mkdir(exist_ok=True)
job=os.environ['SLURM_JOB_ID']
paths=[]
for folder in ['validation-cpu/sweagent-25176140','validation-cpu/sweagent-schema-25176140','environments/repairagent/container-attempt-3','environments/repairagent/container-attempt-4']:
 paths.extend(p for p in (root/folder).rglob('*') if p.is_file())
for pattern in ['experiments/campaign/*v2*','experiments/campaign/*v3*','experiments/campaign/*v4*','sweagent-preflight-25176140.out','repairagent-env-v3-25176216.out','repairagent-env-v4-25176490.out','sweagent-validation-25176198.out','native-validation-collection-25176199.out','sweagent-validation-preflight-v2.json','campaign-status.json','gpu-budget-ledger.json']:
 paths.extend(p for p in root.glob(pattern) if p.is_file())
ledger=json.loads((root/'gpu-budget-ledger.json').read_text())
ids=list(dict.fromkeys(['25176140','25176216','25176490']+[r['job_id'] for r in ledger['reservations'] if r.get('job_id')]+[r['collector_job_id'] for r in ledger['reservations'] if r.get('collector_job_id')]))
query=subprocess.run(['sacct','-j',','.join(ids),'-X','--parsable2','--format=JobID,JobName,State,ElapsedRaw,ExitCode'],text=True,capture_output=True,check=True,timeout=30)
accounting=out/('accounting-'+job+'.psv');accounting.write_text(query.stdout);paths.append(accounting)
archive=out/('repair-audit-'+job+'.tar.gz')
with tarfile.open(archive,'x:gz') as t:
 for p in sorted(set(paths)):t.add(p,arcname=str(p.relative_to(root)),recursive=False)
digest=hashlib.sha256(archive.read_bytes()).hexdigest()
with (out/'SHA256SUMS').open('a') as stream:stream.write(digest+'  '+archive.name+'\n')
print(json.dumps(dict(archive=str(archive),sha256=digest,scope='CPU preparation, schema and environment repairs; model results separate',collected_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())))
PY
