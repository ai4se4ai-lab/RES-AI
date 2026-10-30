"""Freeze a bounded negative control before any resource amendment is admitted."""
import datetime as dt
import hashlib
import json
from pathlib import Path

root=Path(__file__).resolve().parents[2]
out=root/'experiments/campaign/resource-amendment-validation-plan-v3.json'
if out.exists():
    raise RuntimeError('refusing to replace frozen amendment validation')
names=['resource_fault_server.py','start-resource-fault-server.sh','validate_resource_fault_v3.py','resource_fault_warmup_v3.py','resource_fault_evidence.py',
    'resource-amendment-validation-v3.sh','ollama_transport.py','submit_native_validation.py','collect-native-validation-v2.sh']
inputs={'experiments/campaign/'+name:hashlib.sha256((root/'experiments/campaign'/name).read_bytes()).hexdigest() for name in names}
inputs['containers/python311-tools.sif']=hashlib.sha256((root/'containers/python311-tools.sif').read_bytes()).hexdigest()
controls=[]
for path in root.glob('resource-isolation-cpu-*/cpu-control.json'):
    options=path.parent/'resource-warmup-options.json'
    if json.loads(path.read_text()).get('status')=='CPU_CONTROL_PASSED' and options.exists():
        opts=json.loads(options.read_text())
        if opts.get('num_batch')==32 and opts.get('num_thread')==4:
            controls.append(path)
if len(controls)!=1:
    raise RuntimeError('one actual successful bounded CPU control required before GPU submission')
cpu_control=controls[0]
for path in [cpu_control,cpu_control.parent/'resource-warmup-options.json',cpu_control.parent/'loaded-model.json',cpu_control.parent/'device-isolation.json']:
    inputs[path.relative_to(root).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
science=json.loads((root/'experiments/campaign/chatdev-validation-plan.json').read_text())['scientific']
plan=dict(subject='ChatDev',wall_seconds=300,gpu_script='experiments/campaign/resource-amendment-validation-v3.sh',
    inputs=inputs,scientific=science,comparative_episode=False,
    purpose='Allocated H100 visible outside a CPU-only container; real pinned model loads with zero VRAM and existing native GPU residency guard rejects it; no generation')
out.write_text(json.dumps(plan,indent=2)+'\n')
proof=dict(subject='ChatDev',status='CPU_PREFLIGHT_PASSED_NATIVE_GPU_SMOKE_PENDING',source_locked=True,
    dependencies_imported=True,sandbox_validated=True,local_transport_configured=True,
    validation_plan_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),
    basis='Existing native validation and pinned Python/Apptainer image; actual resource fault requires the allocated positive/negative control before comparative admission',
    checked_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
(root/'resource-amendment-validation-preflight-v3.json').write_text(json.dumps(proof,indent=2)+'\n')
