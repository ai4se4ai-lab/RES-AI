#!/bin/bash
#SBATCH --job-name=resai-additional-native-env
#SBATCH --account=def-mbabaei
#SBATCH --cpus-per-task=2
#SBATCH --mem=10G
#SBATCH --time=00:45:00
#SBATCH --array=0-2%2
#SBATCH --output=additional-install-%A_%a.out
set -euo pipefail
cd /project/def-mbabaei/mbabaei/resai-campaign-20261024
module load StdEnv/2023 apptainer
names=(repairagent executionagent agilecoder)
work=/scratch/mbabaei/resai-campaign-20261024
mkdir -p "$work/environments"
apptainer exec --cleanenv --containall --bind "$PWD:/campaign,$work:/work" \
 --env "SLURM_JOB_ID=$SLURM_JOB_ID" containers/python311-tools.sif \
 python /campaign/experiments/campaign/install_additional_environments.py "${names[$SLURM_ARRAY_TASK_ID]}" --attempt "${1:-container-attempt-1}"
