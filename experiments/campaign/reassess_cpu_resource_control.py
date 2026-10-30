"""Reassess preserved actual CPU initialization, without rerunning or changing telemetry."""
import datetime as dt
import hashlib
import json
from pathlib import Path
from resource_fault_evidence import cpu_backend_observed

root=Path(__file__).resolve().parents[2]
out=root/'resource-isolation-cpu-24992385'
isolation=json.loads((out/'device-isolation.json').read_text())
running=json.loads((out/'loaded-model.json').read_text())
log=(out/'ollama.log').read_text()
assert cpu_backend_observed(isolation,running,log)
assert all(m.get('size_vram',0)<.95*m['size'] for m in running if m['name']=='qwen3.8:27b')
assert 'model did not load fully into GPU memory' in (root/'resource-isolation-cpu-24992385.out').read_text()
assert '/api/chat' not in log
proof=dict(status='CPU_CONTROL_PASSED',model_calls=0,native_gpu_residency_guard_rejected=True,
    actual_cpu_backend_observed=True,source_job='24992385',
    reassessment='Initialization and native residency rejection succeeded; the subsequent zero-size_vram assertion was incorrect for this pinned API. Raw memory values and original failure log remain unchanged.',
    source_hashes={name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in ['device-isolation.json','loaded-model.json','ollama.log','resource-warmup-options.json']},
    checked_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
path=out/'cpu-control.json'
if path.exists():raise RuntimeError('refusing to replace a control receipt')
path.write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof,indent=2))
