"""Actual allocated-device positive control and real CPU-only model negative control."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import traceback
from ollama_transport import OllamaModel

root=Path(__file__).resolve().parents[2]
out=root/'validation'/('resource-amendment-'+os.environ['SLURM_JOB_ID'])
out.mkdir(exist_ok=True)
record=dict(subject='ChatDev',stage='RESOURCE_FAULT_AMENDMENT_VALIDATION',comparative_episode=False,
    status='RUNNING',job_id=os.environ['SLURM_JOB_ID'],model_calls=0,
    started_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
try:
    plan_path=root/'experiments/campaign/resource-amendment-validation-plan-v2.json'
    plan=json.loads(plan_path.read_text())
    record['validation_plan_sha256']=hashlib.sha256(plan_path.read_bytes()).hexdigest()
    for name,expected in plan['inputs'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected:
            raise RuntimeError('frozen resource preflight input changed: '+name)
    positive=subprocess.check_output(['nvidia-smi','--query-gpu=name,uuid','--format=csv,noheader'],text=True,timeout=10)
    (out/'allocated-device.txt').write_text(positive)
    if 'H100' not in positive:
        raise RuntimeError('positive control did not observe the allocated H100')
    isolation=json.loads((out/'device-isolation.json').read_text())
    if isolation['accelerator_devices']:
        raise RuntimeError('negative control still has accelerator device nodes')
    science=dict(plan['scientific'])
    science['model_path']='/scratch/mbabaei/ollama_models/manifests/registry.ollama.ai/library/qwen3.8/27b'
    model=OllamaModel(science,out,[])
    model.check_identity()
    try:
        from resource_fault_warmup import warmup
        warmup(model)
    except RuntimeError as exc:
        if str(exc)!='model did not load fully into GPU memory':
            raise
        running=json.loads((out/'loaded-model.json').read_text())
        if not any(m['name']==science['model'] and m.get('size_vram')==0 for m in running):
            raise RuntimeError('no actual CPU-resident model observed')
        record.update(status='PASSED',allocated_h100_visible=True,accelerator_devices_hidden=True,
            cpu_model_loaded=True,native_gpu_residency_guard_rejected=True,negative_control_error=str(exc))
    else:
        raise RuntimeError('fault ineffective: model passed GPU residency')
except BaseException as exc:
    record.update(status='FAILED',error=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc())
finally:
    record['ended_at_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
    (out/'validation.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))
raise SystemExit(0 if record['status']=='PASSED' else 1)
