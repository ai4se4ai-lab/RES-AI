#!/bin/bash
#SBATCH --job-name=resai-chatdev-v2-preflight
#SBATCH --account=def-mbabaei
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:15:00
#SBATCH --output=chatdev-v2-preflight-%j.out
set -euo pipefail
cd /project/def-mbabaei/mbabaei/resai-campaign-20261024
module load StdEnv/2023 python/3.11
export PYTHONPATH="$PWD/src:$PWD/experiments/campaign"
python experiments/campaign/prepare_chatdev_v2.py
python experiments/campaign/advance_chatdev_comparison_v2.py
python experiments/campaign/report_progress.py
