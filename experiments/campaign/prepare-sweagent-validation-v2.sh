#!/bin/bash
#SBATCH --job-name=resai-sweagent-native-preflight
#SBATCH --account=def-mbabaei
#SBATCH --cpus-per-task=2
#SBATCH --mem=6G
#SBATCH --time=00:20:00
#SBATCH --output=sweagent-preflight-%j.out
set -euo pipefail
cd /project/def-mbabaei/mbabaei/resai-campaign-20261024
module load StdEnv/2023 apptainer python/3.11
schema_dir="$PWD/validation-cpu/sweagent-schema-$SLURM_JOB_ID"
mkdir -p "$schema_dir" "$SLURM_TMPDIR/empty-models"
export OLLAMA_HOST=127.0.0.1:18939 OLLAMA_MODELS="$SLURM_TMPDIR/empty-models" OLLAMA_NO_CLOUD=1
/project/def-mbabaei/mbabaei/resai-model-downloads/ollama-v0.40.10/bin/ollama serve > "$schema_dir/ollama.log" 2>&1 &
schema_pid=$!
trap 'kill "$schema_pid" 2>/dev/null || true' EXIT
for i in $(seq 1 60); do
 if curl -sf http://127.0.0.1:18939/api/version >/dev/null; then break; fi
 kill -0 "$schema_pid" || exit 2
 sleep 1
done
python experiments/campaign/check_sweagent_request_v2.py "$schema_dir/schema-check.json"
kill "$schema_pid"
wait "$schema_pid" || true
trap - EXIT
mkdir -p "$SLURM_TMPDIR/root" "$SLURM_TMPDIR/testrepo" validation-cpu
work=/scratch/mbabaei/resai-campaign-20261024
apptainer exec --cleanenv --containall \
 --bind "$PWD:/campaign,$work:/work:ro,$SLURM_TMPDIR:/runwork,$SLURM_TMPDIR/root:/root,$SLURM_TMPDIR/testrepo:/testrepo" \
 --env "SLURM_JOB_ID=$SLURM_JOB_ID,LITELLM_LOCAL_MODEL_COST_MAP=True" \
 containers/python311-tools.sif /work/environments/swe-agent/container-attempt-1/bin/python \
 /campaign/experiments/campaign/sweagent_validation_v2.py --cpu-fixture --out "/campaign/validation-cpu/sweagent-$SLURM_JOB_ID"
apptainer exec --cleanenv --containall --bind "$PWD:/campaign,$work:/work:ro" \
 --env "SLURM_JOB_ID=$SLURM_JOB_ID" containers/python311-tools.sif \
 /work/environments/swe-agent/container-attempt-1/bin/python /campaign/experiments/campaign/prepare_sweagent_validation_v2.py
python experiments/campaign/submit_native_validation.py \
 --plan experiments/campaign/sweagent-validation-plan-v2.json --proof sweagent-validation-preflight-v2.json
