#!/bin/bash
#SBATCH --job-name=resai-agentcoder-native-preflight
#SBATCH --account=def-mbabaei
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:15:00
#SBATCH --output=agentcoder-preflight-%j.out
set -euo pipefail
cd /project/def-mbabaei/mbabaei/resai-campaign-20261024
module load StdEnv/2023 apptainer python/3.11
work=/scratch/mbabaei/resai-campaign-20261024
apptainer exec --cleanenv --containall --bind "$PWD:/campaign,$work:/work:ro,$SLURM_TMPDIR:/runwork" \
  containers/python311.sif /work/environments/agentcoder/container-attempt-1/bin/python \
  /campaign/experiments/campaign/prepare_agentcoder_validation.py
python experiments/campaign/submit_native_validation.py \
  --plan experiments/campaign/agentcoder-validation-plan.json --proof agentcoder-validation-preflight.json
