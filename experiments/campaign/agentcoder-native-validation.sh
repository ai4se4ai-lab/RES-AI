#!/bin/bash
#SBATCH --job-name=resai-agentcoder-native-validation
#SBATCH --account=def-mbabaei_gpu
#SBATCH --gpus=h100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=00:40:00
#SBATCH --output=agentcoder-validation-%j.out
set -euo pipefail
cd /project/def-mbabaei/mbabaei/resai-campaign-20261024
out="$PWD/validation/agentcoder-$SLURM_JOB_ID"
mkdir -p "$out"
module load StdEnv/2023 apptainer
export OLLAMA_HOST=127.0.0.1:18939 OLLAMA_MODELS=/scratch/mbabaei/ollama_models
export OLLAMA_NO_CLOUD=1 OLLAMA_NUM_PARALLEL=1 OLLAMA_MAX_LOADED_MODELS=1
/project/def-mbabaei/mbabaei/resai-model-downloads/ollama-v0.40.10/bin/ollama serve > "validation/ollama-agentcoder-$SLURM_JOB_ID.log" 2>&1 &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true' EXIT
ready=0
for i in $(seq 1 60); do
  if curl -sf http://127.0.0.1:18939/api/version >/dev/null; then ready=1; break; fi
  kill -0 "$server_pid" || break
  sleep 1
done
[ "$ready" -eq 1 ] || exit 2
work=/scratch/mbabaei/resai-campaign-20261024
# Inputs/environments are read-only inside the native evaluator's container.
# Only this attempt's outputs and private job-local storage are writable.
timeout --kill-after=15s 2280s apptainer exec --cleanenv --containall \
  --bind "$PWD:/campaign:ro,$out:/results,$work:/work:ro,$SLURM_TMPDIR:/runwork,/scratch/mbabaei/ollama_models:/models:ro" \
  --env "SLURM_JOB_ID=$SLURM_JOB_ID,OPENAI_API_KEY=job-local-unused" \
  containers/python311.sif /work/environments/agentcoder/container-attempt-1/bin/python \
  /campaign/experiments/campaign/agentcoder_validation.py --out /results/attempt
