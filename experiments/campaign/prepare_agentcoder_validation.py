"""CPU native-control fixture and independent-oracle checks before GPU admission."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback

from agentcoder_adapter import load,run_native
import subprocess

root=Path('/campaign')
proof=dict(subject='AgentCoder',status='PREFLIGHT_RUNNING',model_calls=0)
try:
    task,programmer,designer,executor,patch=load(root,Path('/runwork/agentcoder-native'))
    proof.update(source_locked=True,dependencies_imported=True,benchmark_import_patch=patch,
        evaluator_schema_adaptation='test_code and generation supplied from native full_code; native evaluator unchanged')
    canonical=task['prompt']+task['canonical_solution']
    complete=canonical+'\n'+task['test']+'\ncheck('+task['entry_point']+')\n'
    good=dict(task,full_code=complete)
    bad=dict(task,full_code=task['prompt']+'    return 0.0\n'+task['test']+'\ncheck('+task['entry_point']+')\n')
    if not executor.check_correctness(task['task_id'],good,'python',3,'./tmp')['passed']:
        raise ValueError('native evaluator rejected canonical solution')
    if executor.check_correctness(task['task_id'],bad,'python',3,'./tmp')['passed']:
        raise ValueError('native evaluator accepted intentionally wrong solution')
    for code,expected in ((complete,True),(bad['full_code'],False)):
        result=subprocess.run([sys.executable,str(root/'experiments/campaign/safe_exec.py')],
            input=json.dumps({'code':code}),text=True,capture_output=True,timeout=10)
        if (result.returncode==0)!=expected:
            raise ValueError('independent oracle self-check failed: '+result.stderr)
    proof['sandbox_validated']=True
    import openai
    fixture_calls=[]
    def fixture_create(*args,**kwargs):
        fixture_calls.append(kwargs['messages'])
        designing='code developer assistant' in kwargs['messages'][0]['content']
        text=('assert truncate_number(3.5) == 0.5\nassert truncate_number(5.75) == 0.75\nassert truncate_number(2.0) == 0.0') if designing else canonical
        return openai.util.convert_to_openai_object({'choices':[{'message':{'content':'```python\n'+text+'\n```'}}]})
    openai.ChatCompletion.create=fixture_create
    data,epochs=run_native(task,programmer,designer,executor)
    if len(fixture_calls)!=15 or not data[0].get('need_reproduce') is False:
        raise ValueError('native 5-candidate/10-test/5-epoch control fixture failed')
    proof.update(native_control_fixture_passed=True,fixture_transport_calls=len(fixture_calls),
        fixture_epochs=len(epochs),local_transport_configured=True,
        status='CPU_PREFLIGHT_PASSED_NATIVE_GPU_SMOKE_PENDING')
    # These fixture responses test control flow; they are not model observations.
    names=['agentcoder_adapter.py','prepare_agentcoder_validation.py','agentcoder_validation.py',
        'agentcoder-native-validation.sh','ollama_transport.py','safe_exec.py','agentcoder-task.jsonl',
        'agentcoder-task-provenance.json','submit_native_validation.py','collect-native-validation-v2.sh']
    inputs={'experiments/campaign/'+name:hashlib.sha256((root/'experiments/campaign'/name).read_bytes()).hexdigest() for name in names}
    for name in ('feasibility/agentcoder/source.tar.gz','selected-sources/agentcoder-submodules/codegeex/source.tar.gz'):
        inputs[name]=hashlib.sha256((root/name).read_bytes()).hexdigest()
    scientific=dict(model='qwen3.8:27b',model_revision='b45285c1cc1fafaf0272e840a7b799cb11e1b4597c2dc47a2dc58a61942f408c',
        model_api_digest='aaee06c39dcf2437cde036998d960e1fc1494b8191be7cc9657d01e509097813',
        model_path='/models/manifests/registry.ollama.ai/library/qwen3.8/27b',ollama_version='0.40.10',
        thinking=False,max_input_tokens=12288,max_new_tokens=4096)
    plan=dict(subject='AgentCoder',stage='native_feasibility_only',inputs=inputs,scientific=scientific,
        task_id=task['task_id'],candidates=5,generated_tests=10,repair_epochs=5,max_calls=96,
        wall_seconds=2400,gpu_script='experiments/campaign/agentcoder-native-validation.sh',comparative_episode=False)
    path=root/'experiments/campaign/agentcoder-validation-plan.json'
    if path.exists():
        raise ValueError('refusing to replace frozen native validation plan')
    path.write_text(json.dumps(plan,indent=2)+'\n')
    proof['validation_plan_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
except BaseException as exc:
    proof.update(status='PREFLIGHT_FAILED',error=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc())
finally:
    proof['checked_at_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
    (root/'agentcoder-validation-preflight.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof,indent=2))
raise SystemExit(0 if proof['status'].startswith('CPU_PREFLIGHT_PASSED') else 1)
