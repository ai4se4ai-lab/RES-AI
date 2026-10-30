#!/bin/bash
#SBATCH --job-name=resai-agilecoder-import-repair
#SBATCH --account=def-mbabaei
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:15:00
#SBATCH --output=agilecoder-import-repair-%j.out
set -euo pipefail
cd /project/def-mbabaei/mbabaei/resai-campaign-20261024
module load StdEnv/2023 apptainer python/3.11
work=/scratch/mbabaei/resai-campaign-20261024
apptainer exec --cleanenv --containall --bind "$PWD:/campaign,$work:/work" \
 --env "SLURM_JOB_ID=$SLURM_JOB_ID,PIP_CONFIG_FILE=/dev/null,PIP_DISABLE_PIP_VERSION_CHECK=1" \
 containers/python311-tools.sif /work/environments/agilecoder/container-attempt-2/bin/python \
 /campaign/experiments/campaign/repair_agilecoder_environment.py
python experiments/campaign/report_progress.py
