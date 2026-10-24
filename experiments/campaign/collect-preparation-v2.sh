#!/bin/bash
#SBATCH --job-name=resai-preparation-collection
#SBATCH --account=def-mbabaei
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:10:00
#SBATCH --output=preparation-collection-%j.out
set -euo pipefail
cd /project/def-mbabaei/mbabaei/resai-campaign-20261024
module load StdEnv/2023 python/3.11
python experiments/campaign/report_progress.py
python - <<'PY'
import datetime as dt
import hashlib,json,os,tarfile
from pathlib import Path
root=Path('.')
patterns=['experiments/campaign/*','feasibility/*/feasibility.json',
 'selected-sources/*/feasibility.json','selected-sources/*/*/feasibility.json',
 'environments/**/*.json','environments/**/pip-freeze.txt','validation-cpu/**/*',
 '*preflight*.json','*jobs.json','gpu-budget-ledger.json','campaign-status.json',
 '*.out','comparison/chatdev/*.json','comparison/chatdev/cases/**/case.json',
 'hpc/scripts/hpclib.py','hpc/scripts/run_stage.py','hpc/UPSTREAM.json','src/resai/*.py']
paths={p for pattern in patterns for p in root.glob(pattern) if p.is_file() and not p.is_symlink()}
if any(p.stat().st_size>50*1024**2 for p in paths) or sum(p.stat().st_size for p in paths)>250*1024**2:
 raise RuntimeError('preparation collection exceeds declared size ceiling; audit required')
out=root/'collected-preparation';out.mkdir(exist_ok=True)
archive=out/('preparation-'+os.environ['SLURM_JOB_ID']+'.tar.gz')
with tarfile.open(archive,'x:gz') as bundle:
 for path in sorted(paths): bundle.add(path,arcname=str(path),recursive=False)
sha=hashlib.sha256(archive.read_bytes()).hexdigest()
with (out/'SHA256SUMS').open('a') as stream: stream.write(sha+'  '+archive.name+'\n')
receipt=dict(archive=str(archive),sha256=sha,bytes=archive.stat().st_size,files=len(paths),
 collected_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
 scope='Preparation evidence and labeled CPU fixtures; not model comparative outcomes')
(out/(archive.name+'.json')).write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
PY
