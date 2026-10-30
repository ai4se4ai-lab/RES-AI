"""Bounded native SWE-agent feasibility; deterministic CPU fixture is marked separately."""
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

from ollama_transport import OllamaModel
from sweagent_adapter import setup
from sweagent_transport_v2 import NativeToolTransport

parser=argparse.ArgumentParser()
parser.add_argument('--out',type=Path,required=True)
parser.add_argument('--cpu-fixture',action='store_true')
args=parser.parse_args()
root=Path('/campaign')
out=args.out
out.mkdir(parents=True,exist_ok=False)
started=time.monotonic()
calls=[]
record=dict(subject='SWE-agent',status='RUNNING',comparative_episode=False,
    stage='CPU_CONTROL_FIXTURE_ONLY' if args.cpu_fixture else 'NATIVE_FEASIBILITY_ONLY',
    native_workflow_passed=False,oracle_passed=False,model_endpoint_verified=False,
    job_id=os.environ.get('SLURM_JOB_ID'),started_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
    source_revision='3ea751c087f32b16e039a2233dd6eefecef325d5',
    fixture_revision='7bef0c62cce60a2cb6df0c80f18b3054e1c23630')
runner=None
try:
    if args.cpu_fixture:
        # Same science configuration as the frozen campaign's validated model.
        scientific=json.loads((root/'experiments/campaign/agentcoder-validation-plan.json').read_text())['scientific']
    else:
        plan_path=root/'experiments/campaign/sweagent-validation-plan-v2.json'
        plan=json.loads(plan_path.read_text())
        record['validation_plan_sha256']=hashlib.sha256(plan_path.read_bytes()).hexdigest()
        for name,expected in plan['inputs'].items():
            if hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected:
                raise RuntimeError('frozen SWE-agent input changed: '+name)
        scientific=plan['scientific']
    config,repo,base=setup(root,out)
    record.update(native_configuration=config,fixture_local_commit=base)
    import litellm
    backend=OllamaModel(scientific,out,calls)
    if args.cpu_fixture:
        def fixture_request(path,body):
            if path!='/api/chat':
                raise RuntimeError('CPU fixture must never access model server')
            if any(not isinstance(m.get('content'),str) for m in body['messages']):
                raise RuntimeError('Ollama message content must be a string')
            names={tool['function']['name'] for tool in body['tools']}
            if not {'bash','submit'}<=names:
                raise RuntimeError('expected native tools missing: '+repr(names))
            if not calls:
                command="python - <<'PY'\nfrom pathlib import Path\np=Path('/testrepo/src/testpkg/missing_colon.py')\np.write_text(p.read_text().replace('-> float\\n','-> float:\\n'))\nPY"
                tool=dict(name='bash',arguments={'command':command})
            else:
                tool=dict(name='submit',arguments={})
            return dict(done=True,done_reason='stop',prompt_eval_count=1,eval_count=1,
                message=dict(role='assistant',content='',tool_calls=[dict(function=tool)]))
        backend.request=fixture_request
    else:
        backend.check_identity()
        backend.warmup()
        record['model_endpoint_verified']=True
    litellm.completion=NativeToolTransport(backend,32)
    from sweagent.run.run_single import RunSingle,RunSingleConfig
    runner=RunSingle.from_config(RunSingleConfig.model_validate(config))
    runner.run()
    info=runner.agent.info
    record.update(native_exit_status=info.get('exit_status'),native_submission=info.get('submission'))
    if info.get('exit_status')!='submitted' or not info.get('submission'):
        raise RuntimeError('native workflow did not submit a nonempty patch: '+str(info.get('exit_status')))
    generated=(repo/'src/testpkg/missing_colon.py').read_text()
    (out/'missing_colon.py').write_text(generated)
    record['generated_source_sha256']=hashlib.sha256(generated.encode()).hexdigest()
    # Oracle code/test cases are never included in the native model's prompt.
    result=subprocess.run([sys.executable,str(root/'experiments/campaign/sweagent_oracle.py')],
        input=json.dumps({'source':generated}),text=True,capture_output=True,timeout=7)
    (out/'oracle-stderr.txt').write_text(result.stderr)
    record['oracle_passed']=result.returncode==0
    record['native_workflow_passed']=not args.cpu_fixture
    if not record['oracle_passed']:
        raise RuntimeError('independent division behavior oracle failed')
    record['status']='CPU_NATIVE_CONTROL_FIXTURE_PASSED' if args.cpu_fixture else 'PASSED'
except BaseException as exc:
    record.update(status='FAILED',error=type(exc).__name__+': '+str(exc))
    (out/'failure.log').write_text(traceback.format_exc())
finally:
    if runner is not None:
        try:
            runner.env.close()
        except Exception:
            pass
    record.update(model_calls=0 if args.cpu_fixture else len(calls),
        fixture_transport_calls=len(calls) if args.cpu_fixture else 0,
        process_seconds=time.monotonic()-started,ended_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    (out/('cpu-control.json' if args.cpu_fixture else 'validation.json')).write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))
raise SystemExit(0 if record['status'].endswith('PASSED') else 1)
