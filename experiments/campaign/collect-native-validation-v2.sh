#!/bin/bash
#SBATCH --job-name=resai-native-validation-collection
#SBATCH --account=def-mbabaei
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:10:00
#SBATCH --output=native-validation-collection-%j.out
set -euo pipefail
cd /project/def-mbabaei/mbabaei/resai-campaign-20261024
module load StdEnv/2023 python/3.11
python experiments/campaign/report_progress.py
python - <<'PY'
from pathlib import Path
import hashlib,json,tarfile,os
root=Path('.')
out=root/'collected-native-validation'
out.mkdir(exist_ok=True)
paths=set(root.glob('validation/**/*'))|set(root.glob('*-validation-*.out'))
paths|=set(root.glob('*validation*.json'))|set(root.glob('gpu-budget-ledger.json'))
paths|=set(root.glob('campaign-status.json'))|set(root.glob('experiments/campaign/*'))
archive=out/('native-validation-'+os.environ['SLURM_JOB_ID']+'.tar.gz')
with tarfile.open(archive,'x:gz') as bundle:
    for path in sorted(paths):
        if path.is_file():
            bundle.add(path,arcname=str(path),recursive=False)
sha=hashlib.sha256(archive.read_bytes()).hexdigest()
with (out/'SHA256SUMS').open('a') as stream:
    stream.write(sha+'  '+archive.name+'\n')
print(json.dumps({'archive':str(archive),'sha256':sha,'scope':'Native feasibility validation; no comparative episodes'}))
PY
