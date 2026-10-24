#!/bin/bash
#SBATCH --job-name=resai-sweagent-runtime-repair
#SBATCH --account=def-mbabaei
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=sweagent-runtime-repair-%j.out
set -euo pipefail
cd /project/def-mbabaei/mbabaei/resai-campaign-20261024
module load StdEnv/2023 apptainer
work=/scratch/mbabaei/resai-campaign-20261024
export APPTAINER_CACHEDIR="$work/apptainer-cache" APPTAINER_TMPDIR="$SLURM_TMPDIR"
apptainer pull containers/python311-tools.sif docker://python:3.11-bookworm
sha256sum containers/python311-tools.sif > containers/python311-tools.sha256
apptainer exec --cleanenv --containall --bind "$PWD:/campaign,$work:/work" \
  --env "SLURM_JOB_ID=$SLURM_JOB_ID" containers/python311-tools.sif \
  /work/environments/swe-agent/container-attempt-1/bin/python \
  /campaign/experiments/campaign/check_sweagent_runtime.py
