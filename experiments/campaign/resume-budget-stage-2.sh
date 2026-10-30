#!/bin/bash
#SBATCH --job-name=resai-budget-stage-2-resume
#SBATCH --account=def-mbabaei
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:10:00
#SBATCH --output=budget-stage-2-resume-%j.out
set -euo pipefail
cd /project/def-mbabaei/mbabaei/resai-campaign-20261024
module load StdEnv/2023 python/3.11
export PYTHONPATH="$PWD/src:$PWD/experiments/campaign"
python experiments/campaign/report_progress.py
python experiments/campaign/activate_budget_allocation.py
python experiments/campaign/advance_chatdev_comparison_v2.py
python experiments/campaign/report_progress.py
python experiments/campaign/collect_budget_activation.py
