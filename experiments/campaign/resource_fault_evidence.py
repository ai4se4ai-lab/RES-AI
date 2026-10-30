"""Require observed device isolation and actual CPU residency for each resource case."""
import json
import re


def cpu_backend_observed(isolation,models,log,model_name='qwen3.8:27b'):
    if isolation.get('accelerator_devices')!=[] or not any(m.get('name')==model_name for m in models):
        return False
    # Keep /api/ps unchanged: this pinned server estimates nonzero size_vram
    # even for its AMX/CPU backend. Device access and real runner logs establish
    # the physical fault; the existing native residency guard must still reject.
    cpu=bool(re.search(r'(?:CPU|AMX)\s+model buffer size',log))
    gpu=bool(re.search(r'offloaded\s+[1-9][0-9]*/[0-9]+ layers to GPU',log))
    return cpu and not gpu


def established(case_directory,model_name='qwen3.8:27b'):
    isolation=case_directory/'resource-isolation/device-isolation.json'
    if not isolation.exists() or json.loads(isolation.read_text()).get('accelerator_devices')!=[]:
        return False
    models=[]
    for path in (case_directory/'results').rglob('loaded-model.json'):
        models.extend(json.loads(path.read_text()))
    log=case_directory/'resource-isolation/ollama.log'
    return log.exists() and cpu_backend_observed(json.loads(isolation.read_text()),models,log.read_text(),model_name)
