#!/bin/bash
#SBATCH --job-name=resai-chatdev-native-validation
#SBATCH --account=def-mbabaei_gpu
#SBATCH --gpus=h100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=00:20:00
#SBATCH --output=chatdev-validation-%j.out
set -euo pipefail
cd /project/def-mbabaei/mbabaei/resai-campaign-20261024
module load StdEnv/2023 apptainer
out="$PWD/validation/chatdev-$SLURM_JOB_ID"
mkdir -p validation
export OLLAMA_HOST=127.0.0.1:18939 OLLAMA_MODELS=/scratch/mbabaei/ollama_models
export OLLAMA_NO_CLOUD=1 OLLAMA_NUM_PARALLEL=1 OLLAMA_MAX_LOADED_MODELS=1
server=/project/def-mbabaei/mbabaei/resai-model-downloads/ollama-v0.40.10/bin/ollama
"$server" serve > "validation/ollama-chatdev-$SLURM_JOB_ID.log" 2>&1 &
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
base=/work/environments/chatdev-legacy/container-attempt-1/bin/python
overlay=/work/overlays/chatdev-httpx-0.27.2
set +e
timeout --kill-after=15s 1080s apptainer exec --cleanenv --containall \
  --bind "$PWD:/campaign,$work:/work,$SLURM_TMPDIR:/runwork,/scratch/mbabaei/ollama_models:/models:ro" \
  --env "SLURM_JOB_ID=$SLURM_JOB_ID,OPENAI_API_KEY=job-local-unused,BASE_URL=http://127.0.0.1:18939/v1,PYTHONPATH=$overlay" \
  containers/python311.sif "$base" /campaign/experiments/campaign/chatdev_validation.py \
  --out "/campaign/validation/chatdev-$SLURM_JOB_ID"
rc=$?
if [ -d "$SLURM_TMPDIR/chatdev-native" ] && [ ! -f "$out/native-output.tar.gz" ]; then
  tar -czf "$out/native-output.tar.gz" -C "$SLURM_TMPDIR/chatdev-native" --ignore-failed-read WareHouse CompanyConfig run.py
fi
exit "$rc"
