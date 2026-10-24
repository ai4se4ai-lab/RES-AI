#!/bin/bash
# Two independent Ollama servers in one bounded GPU allocation.
set -uo pipefail
export HPC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export RUN_ID="${1:?run id required}" STAGE=mapcoder
source "$HPC_DIR/slurm/common.sh"
setup_traps
print_job_header
require_gpu || exit 5
setup_python || exit 4
setup_distributed
start_gpu_monitor
export OLLAMA_HOST=127.0.0.1:18939 OLLAMA_API=http://127.0.0.1:18939
export OLLAMA_MODELS=/scratch/mbabaei/ollama_models OLLAMA_NO_CLOUD=1
export OLLAMA_NUM_PARALLEL=1 OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_BIN=/project/def-mbabaei/mbabaei/resai-model-downloads/ollama-v0.40.10/bin/ollama
failed=0
for CELL_ID in 0 1; do
    export CELL_ID
    "$OLLAMA_BIN" serve > "$LOG_ROOT/ollama-rep$CELL_ID.log" 2>&1 &
    server_pid=$!
    SERVICE_PIDS=("$server_pid")
    healthy=0
    for i in $(seq 1 60); do
        if curl -sf "$OLLAMA_API/api/version" > /dev/null; then healthy=1; break; fi
        kill -0 "$server_pid" || break
        sleep 1
    done
    if [ "$healthy" -eq 1 ]; then run_stage || failed=1; else failed=1; fi
    curl -sf "$OLLAMA_API/api/generate" -d '{"model":"qwen3.8:27b","keep_alive":0}' > /dev/null || true
    kill "$server_pid" 2>/dev/null || true
    wait "$server_pid" 2>/dev/null || true
    SERVICE_PIDS=()
done
exit "$failed"
