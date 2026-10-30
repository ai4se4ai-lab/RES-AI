#!/bin/bash
#SBATCH --job-name=resai-resource-amendment-prepare
#SBATCH --account=def-mbabaei
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:10:00
#SBATCH --output=resource-amendment-prepare-%j.out
set -euo pipefail
cd /project/def-mbabaei/mbabaei/resai-campaign-20261024
module load StdEnv/2023 python/3.11
python experiments/campaign/prepare_resource_amendment_v3.py
python experiments/campaign/submit_native_validation.py --plan experiments/campaign/resource-amendment-validation-plan-v3.json --proof resource-amendment-validation-preflight-v3.json
python experiments/campaign/report_progress.py
python - <<'PY'
import hashlib,json,subprocess
from pathlib import Path
h=hashlib.sha256(Path('experiments/campaign/resource-amendment-validation-plan-v3.json').read_bytes()).hexdigest()
entries=[r for r in json.loads(Path('gpu-budget-ledger.json').read_text())['reservations'] if r.get('validation_plan_sha256')==h]
assert len(entries)==1 and entries[0].get('job_id')
result=subprocess.run(['sbatch','--parsable','--dependency=afterok:'+entries[0]['job_id'],'experiments/campaign/prepare-chatdev-v2.sh'],check=True,capture_output=True,text=True)
job=result.stdout.strip().split(';')[0]
p=Path('preparation-jobs.json');d=json.loads(p.read_text());d['job_ids']=list(dict.fromkeys(d['job_ids']+[job]));p.write_text(json.dumps(d,indent=2)+'\n')
print('Gated amendment preparation',job)
PY
