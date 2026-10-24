#!/bin/bash
#SBATCH --job-name=resai-chatdev-httpx-repair
#SBATCH --account=def-mbabaei
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:10:00
#SBATCH --output=chatdev-repair-%j.out
set -euo pipefail
cd /project/def-mbabaei/mbabaei/resai-campaign-20261024
module load StdEnv/2023 apptainer
work=/scratch/mbabaei/resai-campaign-20261024
apptainer exec --cleanenv --containall --bind "$PWD:/campaign,$work:/work" \
  --env "SLURM_JOB_ID=$SLURM_JOB_ID" containers/python311.sif \
  python /campaign/experiments/campaign/repair_chatdev_environment.py
