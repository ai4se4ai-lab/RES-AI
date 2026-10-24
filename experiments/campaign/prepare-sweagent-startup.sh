#!/bin/bash
#SBATCH --job-name=resai-sweagent-native-startup
#SBATCH --account=def-mbabaei
#SBATCH --cpus-per-task=2
#SBATCH --mem=6G
#SBATCH --time=00:20:00
#SBATCH --output=sweagent-native-startup-%j.out
set -euo pipefail
cd /project/def-mbabaei/mbabaei/resai-campaign-20261024
module load StdEnv/2023 python/3.11 apptainer
python - <<'PY'
import pathlib,sys
sys.path.insert(0,'experiments/campaign')
from feasibility import inspect
path=pathlib.Path('selected-sources/sweagent-fixture')
if not (path/'feasibility.json').exists():
 result=inspect({'name':'SWEAgent-Fixture','repository':'https://github.com/SWE-agent/test-repo','retrieved_head':'7bef0c62cce60a2cb6df0c80f18b3054e1c23630'},pathlib.Path('selected-sources'))
 if result['status']!='SOURCE_ACQUIRED_ADAPTER_PENDING': raise RuntimeError(result)
PY
mkdir -p "$SLURM_TMPDIR/root" "$SLURM_TMPDIR/testrepo"
work=/scratch/mbabaei/resai-campaign-20261024
apptainer exec --cleanenv --containall \
 --bind "$PWD:/campaign,$work:/work:ro,$SLURM_TMPDIR:/runwork,$SLURM_TMPDIR/root:/root,$SLURM_TMPDIR/testrepo:/testrepo" \
 --env "SLURM_JOB_ID=$SLURM_JOB_ID,PYTHONPATH=/campaign/feasibility/swe-agent/source,LITELLM_LOCAL_MODEL_COST_MAP=True" \
 containers/python311-tools.sif /work/environments/swe-agent/container-attempt-1/bin/python \
 /campaign/experiments/campaign/prepare_sweagent_startup.py
