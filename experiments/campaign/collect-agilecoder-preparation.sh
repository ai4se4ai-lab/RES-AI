#!/bin/bash
#SBATCH --job-name=resai-agilecoder-prep-collection
#SBATCH --account=def-mbabaei
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:05:00
#SBATCH --output=agilecoder-prep-collection-%j.out
set -euo pipefail
cd /project/def-mbabaei/mbabaei/resai-campaign-20261024
module load StdEnv/2023 python/3.11
python experiments/campaign/report_progress.py
python - <<'PY'
import hashlib,os,tarfile
from pathlib import Path
root=Path.cwd();out=root/'collected-agilecoder-preparation';out.mkdir(exist_ok=True)
p=out/('agilecoder-preparation-'+os.environ['SLURM_JOB_ID']+'.tar.gz')
files=list((root/'environments/agilecoder').glob('container-attempt-[34]/*.json'))
files+=list(root.glob('agilecoder-import-repair-25045*.out'))
files += [root/n for n in ['campaign-status.json','preparation-jobs.json','experiments/campaign/repair_agilecoder_environment.py','experiments/campaign/repair-agilecoder-environment.sh','experiments/campaign/collect-agilecoder-preparation.sh','feasibility/agilecoder/source/setup.py','feasibility/agilecoder/source/agilecoder/camel/model_backend.py','feasibility/agilecoder/source/agilecoder/components/statistics.py']]
with tarfile.open(p,'x:gz') as t:
 for f in files:t.add(f,arcname=f.relative_to(root).as_posix(),recursive=False)
h=hashlib.sha256(p.read_bytes()).hexdigest()
(out/'SHA256SUMS').open('a').write(h+'  '+p.name+'\n')
print(p.name,p.stat().st_size);print(h[:32]);print(h[32:])
PY
