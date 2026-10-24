#!/bin/bash
#SBATCH --job-name=resai-container-native-env
#SBATCH --account=def-mbabaei
#SBATCH --cpus-per-task=4
#SBATCH --mem=12G
#SBATCH --time=00:40:00
#SBATCH --array=0-3%2
#SBATCH --output=container-install-%A_%a.out
set -euo pipefail
cd /project/def-mbabaei/mbabaei/resai-campaign-20261024
module load StdEnv/2023 apptainer
names=(agentcoder chatdev-legacy metagpt swe-agent)
name=${names[$SLURM_ARRAY_TASK_ID]}
work=/scratch/mbabaei/resai-campaign-20261024
mkdir -p "$work/environments"
export APPTAINER_CACHEDIR="$work/apptainer-cache"
apptainer exec --cleanenv --containall --bind "$PWD:/campaign,$work:/work" \
  --env "SLURM_JOB_ID=$SLURM_JOB_ID" containers/python311.sif \
  python /campaign/experiments/campaign/install_container_environment.py "$name"
