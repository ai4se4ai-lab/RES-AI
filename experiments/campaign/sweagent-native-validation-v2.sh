#!/bin/bash
#SBATCH --job-name=resai-sweagent-native-validation-v2
#SBATCH --account=def-mbabaei_gpu
#SBATCH --gpus=h100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=00:20:00
#SBATCH --output=sweagent-validation-%j.out
set -euo pipefail
cd /project/def-mbabaei/mbabaei/resai-campaign-20261024
out="$PWD/validation/sweagent-$SLURM_JOB_ID"
mkdir -p "$out" "$SLURM_TMPDIR/root" "$SLURM_TMPDIR/testrepo"
module load StdEnv/2023 apptainer
export OLLAMA_HOST=127.0.0.1:18939 OLLAMA_MODELS=/scratch/mbabaei/ollama_models
export OLLAMA_NO_CLOUD=1 OLLAMA_NUM_PARALLEL=1 OLLAMA_MAX_LOADED_MODELS=1
/project/def-mbabaei/mbabaei/resai-model-downloads/ollama-v0.40.10/bin/ollama serve > "$out/ollama.log" 2>&1 &
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
timeout --kill-after=15s 1080s apptainer exec --cleanenv --containall \
 --bind "$PWD:/campaign:ro,$out:/results,$work:/work:ro,$SLURM_TMPDIR:/runwork,$SLURM_TMPDIR/root:/root,$SLURM_TMPDIR/testrepo:/testrepo,/scratch/mbabaei/ollama_models:/models:ro" \
 --env "SLURM_JOB_ID=$SLURM_JOB_ID,LITELLM_LOCAL_MODEL_COST_MAP=True" \
 containers/python311-tools.sif /work/environments/swe-agent/container-attempt-1/bin/python \
 /campaign/experiments/campaign/sweagent_validation_v2.py --out /results/attempt
