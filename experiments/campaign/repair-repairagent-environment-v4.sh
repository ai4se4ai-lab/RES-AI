#!/bin/bash
#SBATCH --job-name=resai-repairagent-env-v4
#SBATCH --account=def-mbabaei
#SBATCH --cpus-per-task=2
#SBATCH --mem=10G
#SBATCH --time=00:40:00
#SBATCH --output=repairagent-env-v4-%j.out
set -euo pipefail
cd /project/6108124/mbabaei/resai-campaign-20261024
module load StdEnv/2023 apptainer
apptainer exec --cleanenv --containall --bind "$PWD:/campaign,/scratch/mbabaei/resai-campaign-20261024:/work" --env "SLURM_JOB_ID=$SLURM_JOB_ID" containers/python311-tools.sif python /campaign/experiments/campaign/repair_repairagent_environment_v4.py
