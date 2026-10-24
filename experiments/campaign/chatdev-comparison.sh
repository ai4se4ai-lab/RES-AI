#!/bin/bash
#SBATCH --job-name=resai-chatdev-comparison
#SBATCH --account=def-mbabaei_gpu
#SBATCH --gpus=h100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=00:15:00
set -euo pipefail
cd /project/def-mbabaei/mbabaei/resai-campaign-20261024
case_file=${1:?frozen episode file required}
expected_sha=${2:?frozen episode checksum required}
module load StdEnv/2023 python/3.11 apptainer
export PYTHONPATH="$PWD/src:$PWD/experiments/campaign"
python -c 'import hashlib,pathlib,sys;assert hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest()==sys.argv[2],"episode specification changed"' "$case_file" "$expected_sha"
export OLLAMA_HOST=127.0.0.1:18939 OLLAMA_MODELS=/scratch/mbabaei/ollama_models
export OLLAMA_NO_CLOUD=1 OLLAMA_NUM_PARALLEL=1 OLLAMA_MAX_LOADED_MODELS=1
case_dir=$(dirname "$case_file")
export RESAI_ALLOCATED_GPU=${CUDA_VISIBLE_DEVICES:-0}
if [ "$(python -c 'import json,sys;print(json.load(open(sys.argv[1]))["episode_class"])' "$case_file")" = resource_fault ]; then
  export CUDA_VISIBLE_DEVICES=-1
fi
/project/def-mbabaei/mbabaei/resai-model-downloads/ollama-v0.40.10/bin/ollama serve > "$case_dir/ollama.log" 2>&1 &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true' EXIT
for i in $(seq 1 60); do
  if curl -sf http://127.0.0.1:18939/api/version >/dev/null; then break; fi
  kill -0 "$server_pid" || break
  sleep 1
done
python experiments/campaign/chatdev_episode.py --case "$case_file"
