#!/bin/bash
#SBATCH --job-name=resai-sweagent-source-runtime
#SBATCH --account=def-mbabaei
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:10:00
#SBATCH --output=sweagent-source-runtime-%j.out
set -euo pipefail
cd /project/def-mbabaei/mbabaei/resai-campaign-20261024
module load StdEnv/2023 apptainer
work=/scratch/mbabaei/resai-campaign-20261024
apptainer exec --cleanenv --containall --bind "$PWD:/campaign,$work:/work" \
  --env "SLURM_JOB_ID=$SLURM_JOB_ID,PYTHONPATH=/campaign/feasibility/swe-agent/source" \
  containers/python311-tools.sif /work/environments/swe-agent/container-attempt-1/bin/python \
  /campaign/experiments/campaign/check_sweagent_runtime.py
