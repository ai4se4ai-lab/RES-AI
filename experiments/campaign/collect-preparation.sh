#!/bin/bash
# Submit with --dependency=afterany:<CPU source and environment jobs>.
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
from pathlib import Path
import hashlib,json,tarfile
root=Path('.')
out=root/'collected-preparation'
out.mkdir(exist_ok=True)
paths=set(root.glob('*.out'))|set(root.glob('*.sh'))|set(root.glob('*.json'))
paths|=set(root.glob('experiments/campaign/*'))
paths|=set(root.glob('feasibility/*/feasibility.json'))
paths|=set(root.glob('feasibility/environment.json'))
paths|=set(root.glob('feasibility/summary.json'))
paths|=set(root.glob('selected-sources/*/feasibility.json'))
paths|=set(root.glob('environments/*/*/*.json'))
paths|=set(root.glob('environments/*/*/*.txt'))
paths|=set(root.glob('containers/SHA256SUMS'))
archive=out/'native-preparation.tar.gz'
with tarfile.open(archive,'w:gz') as bundle:
    for path in sorted(paths):
        if path.is_file():
            bundle.add(path,arcname=str(path),recursive=False)
sha=hashlib.sha256(archive.read_bytes()).hexdigest()
(out/'SHA256SUMS').write_text(sha+'  '+archive.name+'\n')
print(json.dumps({'archive':str(archive),'sha256':sha,'files':sum(p.is_file() for p in paths),
                  'scope':'CPU preparation evidence only; no comparative episodes'}))
PY
