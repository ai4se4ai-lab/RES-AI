#!/bin/bash
#SBATCH --job-name=resai-sweagent-native-preflight
#SBATCH --account=def-mbabaei
#SBATCH --cpus-per-task=2
#SBATCH --mem=6G
#SBATCH --time=00:20:00
#SBATCH --output=sweagent-preflight-%j.out
set -euo pipefail
cd /project/def-mbabaei/mbabaei/resai-campaign-20261024
module load StdEnv/2023 apptainer python/3.11
mkdir -p "$SLURM_TMPDIR/root" "$SLURM_TMPDIR/testrepo" validation-cpu
work=/scratch/mbabaei/resai-campaign-20261024
apptainer exec --cleanenv --containall \
 --bind "$PWD:/campaign,$work:/work:ro,$SLURM_TMPDIR:/runwork,$SLURM_TMPDIR/root:/root,$SLURM_TMPDIR/testrepo:/testrepo" \
 --env "SLURM_JOB_ID=$SLURM_JOB_ID,LITELLM_LOCAL_MODEL_COST_MAP=True" \
 containers/python311-tools.sif /work/environments/swe-agent/container-attempt-1/bin/python \
 /campaign/experiments/campaign/sweagent_validation.py --cpu-fixture --out "/campaign/validation-cpu/sweagent-$SLURM_JOB_ID"
apptainer exec --cleanenv --containall --bind "$PWD:/campaign,$work:/work:ro" \
 --env "SLURM_JOB_ID=$SLURM_JOB_ID" containers/python311-tools.sif \
 /work/environments/swe-agent/container-attempt-1/bin/python /campaign/experiments/campaign/prepare_sweagent_validation.py
python experiments/campaign/submit_native_validation.py \
 --plan experiments/campaign/sweagent-validation-plan.json --proof sweagent-validation-preflight.json
