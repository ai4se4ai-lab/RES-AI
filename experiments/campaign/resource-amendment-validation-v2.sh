#!/bin/bash
#SBATCH --job-name=resai-resource-amendment-validation
#SBATCH --account=def-mbabaei_gpu
#SBATCH --gpus=h100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=00:05:00
#SBATCH --output=resource-amendment-validation-%j.out
set -euo pipefail
cd /project/def-mbabaei/mbabaei/resai-campaign-20261024
module load StdEnv/2023 python/3.11 apptainer
out="$PWD/validation/resource-amendment-$SLURM_JOB_ID"
source experiments/campaign/start-resource-fault-server.sh "$out"
trap 'kill "$server_pid" 2>/dev/null || true' EXIT
ready=0
for i in $(seq 1 60); do
 if curl -sf http://127.0.0.1:18939/api/version >/dev/null; then ready=1; break; fi
 kill -0 "$server_pid" || break
 sleep 1
done
[ "$ready" -eq 1 ] || exit 2
timeout --kill-after=10s 220s python experiments/campaign/validate_resource_fault_v2.py
