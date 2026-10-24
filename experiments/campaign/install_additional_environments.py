"""CPU dependency screening for additional pinned native artifacts, with no model calls."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

subjects={
    'repairagent':('repair_agent',['-r','requirements-core.txt'],['autogpt.app.main']),
    'executionagent':('.',['.'],['execution_agent.main']),
    'agilecoder':('.',['.','anthropic[vertex]'],[]),
}
parser=argparse.ArgumentParser()
parser.add_argument('subject',choices=subjects)
parser.add_argument('--attempt',default='container-attempt-1')
args=parser.parse_args()
root=Path('/campaign')
source=root/'feasibility'/args.subject/'source'
relative,requirements,modules=subjects[args.subject]
cwd=source/relative
previous=root/'environments'/args.subject/'container-attempt-1/installation.json'
if args.attempt=='container-attempt-2' and previous.exists() and json.loads(previous.read_text())['status'].startswith('DEPENDENCY_IMPORT_PASSED'):
    print('Previous isolated dependency/import check passed; skipping duplicate installation.')
    raise SystemExit(0)
if args.attempt not in ('container-attempt-1','container-attempt-2'):
    raise ValueError('unsupported environment attempt')
out=root/'environments'/args.subject/args.attempt
out.mkdir(parents=True,exist_ok=False)
venv=Path('/work/environments')/args.subject/args.attempt
record=dict(subject=args.subject,status='INSTALLING',native_workflow_passed=False,eligible_for_comparison=False,
    job_id=os.environ.get('SLURM_JOB_ID'),model_calls=0,environment=str(venv),python=sys.version,
    started_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
    archive_sha256=hashlib.sha256((source.parent/'source.tar.gz').read_bytes()).hexdigest(),
    container_sha256=hashlib.sha256((root/'containers/python311-tools.sif').read_bytes()).hexdigest(),
    requirements=requirements)
receipt=out/'installation.json'
receipt.write_text(json.dumps(record,indent=2)+'\n')
env=dict(os.environ,PIP_CONFIG_FILE='/dev/null',PIP_DISABLE_PIP_VERSION_CHECK='1',
    OPENAI_API_KEY='job-local-unused',OPENAI_API_BASE='http://127.0.0.1:18939/v1',
    OPENAI_BASE_URL='http://127.0.0.1:18939/v1',LITELLM_LOCAL_MODEL_COST_MAP='True',
    PYTHONPATH=str(source/'src')+':'+str(cwd))
env.pop('PIP_CONSTRAINT',None)
started=time.monotonic()
try:
    # Shared scratch can take several minutes to create pip's small files.
    subprocess.run([sys.executable,'-m','venv','--copies',str(venv)],check=True,timeout=900,env=env)
    python=str(venv/'bin/python')
    subprocess.run([python,'-m','pip','install','--upgrade','pip'],check=True,timeout=300,env=env)
    subprocess.run([python,'-m','pip','install',*requirements],cwd=cwd,check=True,timeout=2100,env=env)
    with (out/'pip-freeze.txt').open('w') as stream:
        subprocess.run([python,'-m','pip','freeze'],check=True,stdout=stream,env=env)
    if args.subject=='agilecoder':
        # Upstream imports its inactive cloud backend and reads credentials at
        # module import. Disable only that initialization during this CPU check.
        # Do not create cloud credentials or make a provider/model request.
        code="""
import builtins,io
from unittest.mock import patch
from google.oauth2.service_account import Credentials
original_open=builtins.open
def private_open(name,*args,**kwargs):
    return io.StringIO('{}') if str(name)=='../key.json' else original_open(name,*args,**kwargs)
with patch.object(Credentials,'from_service_account_info',return_value=None),patch('builtins.open',private_open):
    import agilecoder.camel.model_backend
    import agilecoder.components.chat_chain
"""
        record['inactive_provider_adaptation']='Only during import: Vertex credential constructor returns None; ../key.json read supplied as empty in-memory JSON. Native source unchanged; no cloud calls.'
    else:
        code='import importlib; '+'; '.join(f'importlib.import_module({name!r})' for name in modules)
    subprocess.run([python,'-c',code],cwd=cwd,env=env,check=True,timeout=180)
    record.update(status='DEPENDENCY_IMPORT_PASSED_NATIVE_WORKFLOW_PENDING',imported_modules=modules or ['agilecoder.camel.model_backend','agilecoder.components.chat_chain'])
except Exception as exc:
    record.update(status='DEPENDENCY_CHECK_FAILED',error=type(exc).__name__+': '+str(exc))
finally:
    record.update(elapsed_cpu_job_process_seconds=time.monotonic()-started,
        ended_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    receipt.write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))
raise SystemExit(0 if record['status'].startswith('DEPENDENCY_IMPORT_PASSED') else 1)
