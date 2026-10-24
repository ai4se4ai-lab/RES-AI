#!/bin/bash
#SBATCH --job-name=resai-chatdev-native-preflight
#SBATCH --account=def-mbabaei
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:15:00
#SBATCH --output=chatdev-preflight-%j.out
set -euo pipefail
cd /project/def-mbabaei/mbabaei/resai-campaign-20261024
module load StdEnv/2023 apptainer python/3.11
work=/scratch/mbabaei/resai-campaign-20261024
source_dir=/campaign/selected-sources/chatdev/source
overlay=/work/overlays/chatdev-httpx-0.27.2
base=/work/environments/chatdev-legacy/container-attempt-1/bin/python
apptainer exec --cleanenv --containall --bind "$PWD:/campaign,$work:/work,$SLURM_TMPDIR:/runwork" \
  --env "OPENAI_API_KEY=job-local-unused,BASE_URL=http://127.0.0.1:18939/v1,PYTHONPATH=$overlay:$source_dir" \
  containers/python311.sif "$base" /campaign/experiments/campaign/prepare_chatdev_validation.py
python experiments/campaign/submit_chatdev_validation.py
