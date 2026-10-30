"""Versioned fault amendment; preserve v1, carry fourteen qualified cases, rerun the faulty block."""
import copy
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from resai.core import digest

root=Path(__file__).resolve().parents[2]
os.chdir(root)
old=root/'comparison/chatdev'
out=root/'comparison/chatdev-v2'
if out.exists():
    raise RuntimeError('refusing to replace an amendment workspace')
parent=json.loads((old/'protocol.json').read_text())
status=json.loads((old/'status.json').read_text())
if status['status']!='STOPPED_FOR_AUDIT' or status['comparative_episodes_completed']!=14:
    raise RuntimeError('unexpected original audit state; review before amendment')
validation=[]
for p in (root/'validation').glob('resource-amendment-*/validation.json'):
    r=json.loads(p.read_text())
    if r['status']=='PASSED' and all(r.get(k) is True for k in ('allocated_h100_visible','accelerator_devices_hidden','cpu_model_loaded','native_gpu_residency_guard_rejected')):
        validation.append((p,r))
if len(validation)!=1:
    raise RuntimeError('one successful actual resource negative control required')
validation_path,validated=validation[0]
validation_plan=root/'experiments/campaign/resource-amendment-validation-plan-v3.json'
if hashlib.sha256(validation_plan.read_bytes()).hexdigest()!=validated['validation_plan_sha256']:
    raise RuntimeError('resource validation plan identity differs')
for name,h in json.loads(validation_plan.read_text())['inputs'].items():
    if hashlib.sha256((root/name).read_bytes()).hexdigest()!=h:
        raise RuntimeError('validated resource implementation changed: '+name)
inputs=dict(parent['inputs'])
for name in ['experiments/campaign/chatdev-comparison.sh','experiments/campaign/advance_chatdev_comparison.py','experiments/campaign/collect-chatdev-comparison.sh',
    'experiments/campaign/chatdev_episode.py','experiments/campaign/chatdev_episode_worker.py','experiments/campaign/run_chatdev_phase.py']:
    inputs.pop(name)
for name in ['chatdev-comparison-v2.sh','advance_chatdev_comparison_v2.py','collect-chatdev-comparison-v2.sh',
    'resource_fault_server.py','start-resource-fault-server.sh','resource_fault_evidence.py','prepare_chatdev_v2.py',
    'resource_fault_warmup_v3.py','chatdev_episode_v2.py','chatdev_episode_worker_v2.py','run_chatdev_phase_v2.py']:
    key='experiments/campaign/'+name
    inputs[key]=hashlib.sha256((root/key).read_bytes()).hexdigest()
inputs['containers/python311-tools.sif']=hashlib.sha256((root/'containers/python311-tools.sif').read_bytes()).hexdigest()
for name,h in inputs.items():
    if hashlib.sha256((root/name).read_bytes()).hexdigest()!=h:
        raise RuntimeError('unchanged scientific/native source differs from v1: '+name)
out.mkdir()
rows=[]
resolved={'PRODUCTION_VALID','PRODUCTION_INVALID','POLICY_BLOCKED'}
for prior in status['queue']:
    if prior['status'] in resolved:
        row=copy.deepcopy(prior)
        row['carry_forward_from_revision']=1
        rows.append(row)
        continue
    original=root/prior['case']
    case=json.loads(original.read_text())
    case['original_episode_id']=case['episode_id']
    case['episode_id']+='-r2'
    case['protocol_revision']=2
    directory=out/'cases'/case['episode_id']
    config=directory/'hpc/config'
    config.mkdir(parents=True)
    path=directory/'case.json'
    graph=json.loads((original.parent/'hpc/config/experiments.json').read_text())
    for stage in graph['stages']:
        for step in stage['steps']:
            step['cmd']=step['cmd'].replace(str(original),str(path)).replace('run_chatdev_phase.py','run_chatdev_phase_v2.py')
    graph_path=config/'experiments.json'
    graph_path.write_text(json.dumps(graph,indent=2)+'\n')
    env_path=config/'cluster.env'
    env_path.write_bytes((original.parent/'hpc/config/cluster.env').read_bytes())
    os.environ['HPC_DIR']=str(directory/'hpc')
    spec=importlib.util.spec_from_file_location('v2_engine',root/'hpc/scripts/hpclib.py')
    engine=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    resolved_graph=engine.resolve(graph,False)
    if errors:=engine.validate(resolved_graph):
        raise RuntimeError(errors)
    case['policy_plan']['execution']['graph_hash']=digest(resolved_graph)
    case['policy_plan']['inputs']=dict(inputs)
    for p in (graph_path,env_path):
        case['policy_plan']['inputs'][p.relative_to(root).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
    path.write_text(json.dumps(case,indent=2)+'\n')
    rows.append(dict(episode_id=case['episode_id'],original_episode_id=case['original_episode_id'],
        case=str(path.relative_to(root)),case_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),status='PLANNED'))
if len(rows)!=140 or sum(r.get('carry_forward_from_revision')==1 for r in rows)!=14:
    raise RuntimeError('amended matrix lost or duplicated cases')
protocol=copy.deepcopy(parent)
protocol.update(protocol_revision=2,inputs=inputs,queue=rows,retained_prior_qualified=14,
    parent_protocol_sha256=hashlib.sha256((old/'protocol.json').read_bytes()).hexdigest(),
    historical_quarantined_jobs=['24950514','24951292','24951623'],
    amendment='Only resource unavailability initialization changes: real Ollama server in a contained CPU-only Apptainer without accelerator device nodes; empty initialization uses num_batch=32 and num_thread=4 to bound CPU warmup. No generation proceeds under this fault. Native algorithms, sampling/task parameters, conditions, original condition order, oracles and scientific configurations retained. Fourteen qualified v1 cases retained; all seven affected resource-block conditions get distinct r2 case identities.',
    resource_control_receipt=str(validation_path.relative_to(root)),
    resource_control_sha256=hashlib.sha256(validation_path.read_bytes()).hexdigest(),
    amended_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),status='FROZEN_V2_RESOURCE_CONTROL_PASSED')
protocol['faults']['resource_fault']='Real model server inside CPU-only contained Apptainer; assert no accelerator device nodes and actual CPU backend logs, retaining raw API memory estimates. Existing native GPU residency guard rejects actual CPU-loaded model before generation. Allocated H100 remains visible to the external monitor.'
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
# Check the actual graph/native bindings for both an amended resource case and
# a later clean case. The original native startup/oracles remain byte-identical.
for fault in ['resource_fault','clean']:
    row=next(r for r in rows if not r.get('carry_forward_from_revision') and json.loads((root/r['case']).read_text())['episode_class']==fault)
    proc=subprocess.run([sys.executable,str(root/'experiments/campaign/upstream_bridge.py'),'--case',str(root/row['case']),'--binding'],check=True,capture_output=True,text=True)
    if json.loads(proc.stdout):
        raise RuntimeError(proc.stdout)
proof=json.loads((old/'preflight.json').read_text())
proof.update(protocol_revision=2,resource_fault_control_passed=True,
    resource_validation_source=str(validation_path),resource_validation_sha256=protocol['resource_control_sha256'],
    validated_protocol_sha256=hashlib.sha256((out/'protocol.json').read_bytes()).hexdigest())
(out/'preflight.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps({'amendment':2,'carried':14,'remaining':126,'resource_control_job':validated['job_id']}))
