#!/bin/bash
#SBATCH --job-name=resai-chatdev-comparison-collection
#SBATCH --account=def-mbabaei
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:10:00
set -euo pipefail
cd /project/def-mbabaei/mbabaei/resai-campaign-20261024
export PYTHONPATH="$PWD/src:$PWD/experiments/campaign"
module load StdEnv/2023 python/3.11
case_file=${1:?case file required}
python experiments/campaign/report_progress.py
python - "$case_file" <<'PY'
import hashlib,json,os,sys,tarfile
from pathlib import Path
root=Path.cwd()
case=Path(sys.argv[1])
spec=json.loads(case.read_text())
dest=root/'comparison/chatdev-v2/archives'
dest.mkdir(exist_ok=True)
archive=dest/(spec['episode_id']+'-collector-'+os.environ['SLURM_JOB_ID']+'.tar.gz')
with tarfile.open(archive,'x:gz') as bundle:
 bundle.add(case.parent,arcname='episode')
 for name in ['comparison/chatdev-v2/protocol.json','comparison/chatdev-v2/preflight.json','gpu-budget-ledger.json','campaign-status.json']:
  bundle.add(root/name,arcname=name)
 for name in json.loads((root/'comparison/chatdev-v2/protocol.json').read_text())['inputs']:
  path=root/name
  if path.stat().st_size<2*1024*1024:
   bundle.add(path,arcname='source/'+name)
h=hashlib.sha256(archive.read_bytes()).hexdigest()
with (dest/'SHA256SUMS').open('a') as stream: stream.write(h+'  '+archive.name+'\n')
print(json.dumps({'archive':str(archive),'sha256':h}))
PY
python experiments/campaign/advance_chatdev_comparison_v2.py
python experiments/campaign/report_progress.py
