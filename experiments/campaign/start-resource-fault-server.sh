#!/bin/bash
# Source this from an allocated job. The caller owns server_pid and cleanup.
fault_evidence=${1:?fault evidence directory required}
mkdir -p "$fault_evidence"
apptainer exec --cleanenv --containall --pwd /tmp \
 --bind "$PWD/experiments/campaign/resource_fault_server.py:/resource_fault_server.py:ro,$fault_evidence:/fault-evidence,/project/def-mbabaei/mbabaei/resai-model-downloads/ollama-v0.40.10:/ollama:ro,/scratch/mbabaei/ollama_models:/models:ro" \
 --env "OLLAMA_HOST=127.0.0.1:18939,OLLAMA_MODELS=/models,OLLAMA_NO_CLOUD=1,OLLAMA_NUM_PARALLEL=1,OLLAMA_MAX_LOADED_MODELS=1,OLLAMA_VULKAN=false" \
 containers/python311-tools.sif python /resource_fault_server.py > "$fault_evidence/ollama.log" 2>&1 &
server_pid=$!
