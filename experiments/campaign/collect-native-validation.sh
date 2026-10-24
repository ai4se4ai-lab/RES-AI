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
import hashlib,json,tarfile
root=Path('.')
out=root/'collected-native-validation'
out.mkdir(exist_ok=True)
paths=set(root.glob('validation/**/*'))|set(root.glob('chatdev-validation-*.out'))
paths|=set(root.glob('chatdev-*.json'))|set(root.glob('gpu-budget-ledger.json'))
paths|=set(root.glob('campaign-status.json'))|set(root.glob('experiments/campaign/*'))
archive=out/'native-validation.tar.gz'
with tarfile.open(archive,'w:gz') as bundle:
    for path in sorted(paths):
        if path.is_file():
            bundle.add(path,arcname=str(path),recursive=False)
sha=hashlib.sha256(archive.read_bytes()).hexdigest()
(out/'SHA256SUMS').write_text(sha+'  '+archive.name+'\n')
print(json.dumps({'archive':str(archive),'sha256':sha,'scope':'Native feasibility validation; zero comparative episodes'}))
PY
