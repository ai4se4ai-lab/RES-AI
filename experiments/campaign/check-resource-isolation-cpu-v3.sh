#!/bin/bash
#SBATCH --job-name=resai-resource-isolation-cpu
#SBATCH --account=def-mbabaei
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=00:05:00
#SBATCH --output=resource-isolation-cpu-%j.out
set -euo pipefail
cd /project/def-mbabaei/mbabaei/resai-campaign-20261024
module load StdEnv/2023 python/3.11 apptainer
out="$PWD/resource-isolation-cpu-$SLURM_JOB_ID"
source experiments/campaign/start-resource-fault-server.sh "$out"
trap 'kill "$server_pid" 2>/dev/null || true' EXIT
ready=0
for i in $(seq 1 60); do
 if curl -sf http://127.0.0.1:18939/api/version >/dev/null; then ready=1; break; fi
 kill -0 "$server_pid" || break
 sleep 1
done
[ "$ready" -eq 1 ] || exit 2
python - "$out" <<'PY'
import json,sys
from pathlib import Path
sys.path.insert(0,'experiments/campaign')
from ollama_transport import OllamaModel
out=Path(sys.argv[1])
science=json.loads(Path('experiments/campaign/chatdev-validation-plan.json').read_text())['scientific']
science['model_path']='/scratch/mbabaei/ollama_models/manifests/registry.ollama.ai/library/qwen3.8/27b'
model=OllamaModel(science,out,[])
model.check_identity()
try:
 from resource_fault_warmup_v3 import warmup
 warmup(model)
except RuntimeError as exc:
 if str(exc)!='model did not load fully into GPU memory':raise
 running=json.loads((out/'loaded-model.json').read_text())
 assert any(m['name']==science['model'] and m.get('size_vram')==0 for m in running)
 (out/'cpu-control.json').write_text(json.dumps({'status':'CPU_CONTROL_PASSED','model_calls':0,'native_gpu_residency_guard_rejected':True})+'\n')
 print('CPU_CONTROL_PASSED: actual model loaded with zero VRAM; no generation')
else:raise RuntimeError('CPU-only negative control did not reject GPU residency')
PY
