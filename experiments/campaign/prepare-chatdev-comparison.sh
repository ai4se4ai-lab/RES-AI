#!/bin/bash
#SBATCH --job-name=resai-chatdev-comparison-preflight
#SBATCH --account=def-mbabaei
#SBATCH --cpus-per-task=2
#SBATCH --mem=6G
#SBATCH --time=00:25:00
#SBATCH --output=chatdev-comparison-preflight-%j.out
set -euo pipefail
cd /project/def-mbabaei/mbabaei/resai-campaign-20261024
module load StdEnv/2023 python/3.11 apptainer
export PYTHONPATH="$PWD/src:$PWD/experiments/campaign"
python experiments/campaign/prepare_chatdev_comparison.py
python experiments/campaign/check_chatdev_comparison_setup.py
python experiments/campaign/advance_chatdev_comparison.py
python experiments/campaign/report_progress.py
