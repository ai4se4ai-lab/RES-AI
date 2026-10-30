#!/bin/bash
#SBATCH --job-name=resai-resource-amendment-prepare
#SBATCH --account=def-mbabaei
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:10:00
#SBATCH --output=resource-amendment-prepare-%j.out
set -euo pipefail
cd /project/def-mbabaei/mbabaei/resai-campaign-20261024
module load StdEnv/2023 python/3.11
python experiments/campaign/prepare_resource_amendment.py
python experiments/campaign/submit_native_validation.py --plan experiments/campaign/resource-amendment-validation-plan.json --proof resource-amendment-validation-preflight.json
python experiments/campaign/report_progress.py
