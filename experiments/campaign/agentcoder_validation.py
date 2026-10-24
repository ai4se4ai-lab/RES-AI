"""One bounded native AgentCoder feasibility execution with the pinned local model."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

from agentcoder_adapter import load,run_native
from ollama_transport import OllamaModel

parser=argparse.ArgumentParser()
parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args()
root=Path('/campaign')
out=args.out
out.mkdir(parents=True,exist_ok=False)
start=time.monotonic()
record=dict(subject='AgentCoder',stage='NATIVE_FEASIBILITY_ONLY',status='RUNNING',
    job_id=os.environ.get('SLURM_JOB_ID'),comparative_episode=False,
    native_workflow_passed=False,oracle_passed=False,model_endpoint_verified=False,
    started_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
calls=[]
class CallBudgetExhausted(BaseException):
    pass
try:
    plan_path=root/'experiments/campaign/agentcoder-validation-plan.json'
    plan=json.loads(plan_path.read_text())
    record['validation_plan_sha256']=hashlib.sha256(plan_path.read_bytes()).hexdigest()
    for name,expected in plan['inputs'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('frozen validation input changed: '+name)
    task,programmer,designer,executor,patch=load(root,Path('/runwork/agentcoder-native'))
    record.update(task_id=task['task_id'],benchmark_import_patch=patch,
        source_revision='d8538d63675c2b805855e6deb7ddc39fefb5723d',
        evaluator_revision='2838420b7b4492cf3d16bce5320e26e65960c9e2',
        evaluator_schema_adaptation='Native full_code supplied as test_code/generation; evaluator and scoring unchanged')
    backend=OllamaModel(plan['scientific'],out,calls)
    backend.check_identity()
    backend.warmup()
    record['model_endpoint_verified']=True
    import openai
    def local_create(*args,**kwargs):
        if len(calls)>=plan['max_calls']:
            raise CallBudgetExhausted('96-call native feasibility cap exhausted')
        text,inputs,outputs=backend.prompt(kwargs['messages'])
        calls[-1]['native_requested_model']=kwargs.get('model')
        (out/'calls.json').write_text(json.dumps(calls,indent=2)+'\n')
        return openai.util.convert_to_openai_object({'choices':[{'message':{'content':text}}],
            'usage':{'prompt_tokens':inputs,'completion_tokens':outputs,'total_tokens':inputs+outputs}})
    openai.ChatCompletion.create=local_create
    def persist(data,phase):
        (out/(phase+'.json')).write_text(json.dumps(data,indent=2)+'\n')
    data,epochs=run_native(task,programmer,designer,executor,persist)
    record['native_workflow_passed']=True
    code=data[0]['completion']+'\n'+task['test']+'\ncheck('+task['entry_point']+')\n'
    result=subprocess.run([sys.executable,str(root/'experiments/campaign/safe_exec.py')],
        input=json.dumps({'code':code}),text=True,capture_output=True,timeout=10)
    (out/'oracle-stderr.txt').write_text(result.stderr)
    record.update(oracle_passed=result.returncode==0,native_repair_epochs=len(epochs),
        generated_test_acceptance=data[0].get('need_reproduce') is False,
        native_max_correct=data[0].get('max_correct'),
        generated_source_sha256=hashlib.sha256(data[0]['completion'].encode()).hexdigest())
    record['status']='PASSED' if record['oracle_passed'] else 'ORACLE_FAILED'
except BaseException as exc:
    record.update(status='FAILED',error=type(exc).__name__+': '+str(exc))
    (out/'failure.log').write_text(traceback.format_exc())
finally:
    record.update(calls=len(calls),process_seconds=time.monotonic()-start,
        ended_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    (out/'validation.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))
raise SystemExit(0 if record['status']=='PASSED' else 1)
