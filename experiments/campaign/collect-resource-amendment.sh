#!/bin/bash
#SBATCH --job-name=resai-resource-amendment-collection
#SBATCH --account=def-mbabaei
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:10:00
#SBATCH --output=resource-amendment-collection-%j.out
set -euo pipefail
cd /project/def-mbabaei/mbabaei/resai-campaign-20261024
module load StdEnv/2023 python/3.11
python experiments/campaign/report_progress.py
python - <<'PY'
import hashlib,json,os,tarfile
from pathlib import Path
root=Path('.')
patterns=['experiments/campaign/*','resource-isolation-cpu-*/*','resource-isolation-cpu-*.out',
 'resource-control-reassessment-*.out','resource-amendment-*.out','resource-amendment*preflight*.json',
 'validation/resource-amendment-*/**/*','gpu-budget-ledger.json','campaign-status.json','preparation-jobs.json']
paths={p for pattern in patterns for p in root.glob(pattern) if p.is_file() and not p.is_symlink()}
if sum(p.stat().st_size for p in paths)>50*1024**2:
 raise RuntimeError('amendment collection exceeds declared ceiling')
out=root/'collected-resource-amendment';out.mkdir(exist_ok=True)
archive=out/('resource-amendment-'+os.environ['SLURM_JOB_ID']+'.tar.gz')
with tarfile.open(archive,'x:gz') as bundle:
 for path in sorted(paths):bundle.add(path,arcname=str(path),recursive=False)
sha=hashlib.sha256(archive.read_bytes()).hexdigest()
with (out/'SHA256SUMS').open('a') as stream:stream.write(sha+'  '+archive.name+'\n')
print(json.dumps(dict(archive=str(archive),sha256=sha,bytes=archive.stat().st_size,files=len(paths))))
PY
