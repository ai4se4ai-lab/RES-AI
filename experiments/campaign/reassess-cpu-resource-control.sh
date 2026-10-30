#!/bin/bash
#SBATCH --job-name=resai-resource-control-reassessment
#SBATCH --account=def-mbabaei
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:05:00
#SBATCH --output=resource-control-reassessment-%j.out
set -euo pipefail
cd /project/def-mbabaei/mbabaei/resai-campaign-20261024
module load StdEnv/2023 python/3.11
python experiments/campaign/reassess_cpu_resource_control.py
sbatch --parsable experiments/campaign/prepare-resource-amendment-v3.sh
