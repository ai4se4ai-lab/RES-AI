"""Resolve the observed OpenAI 1.47.1 / httpx 0.28 import incompatibility.

Keep the initial environment and its failure receipt intact; use a separate
httpx overlay and record the dependency repair before native workflow testing.
"""
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys


root=Path('/campaign')
out=root/'environments/chatdev-legacy/container-attempt-2'
out.mkdir(parents=True,exist_ok=False)
overlay=Path('/work/overlays/chatdev-httpx-0.27.2')
base=Path('/work/environments/chatdev-legacy/container-attempt-1/bin/python')
source=root/'selected-sources/chatdev/source'
record=dict(subject='chatdev-legacy',status='INSTALLING',job_id=os.environ.get('SLURM_JOB_ID'),
    native_workflow_passed=False,eligible_for_comparison=False,environment=str(base.parent.parent),
    overlay=str(overlay),dependency_repair='httpx==0.27.2; initial OpenAI 1.47.1 client failed with unexpected proxies argument',
    started_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
receipt=out/'installation.json'
receipt.write_text(json.dumps(record,indent=2)+'\n')
env=dict(os.environ,PIP_CONFIG_FILE='/dev/null',OPENAI_API_KEY='job-local-unused',
    BASE_URL='http://127.0.0.1:18939/v1',PYTHONPATH=str(overlay)+':'+str(source))
try:
    subprocess.run([str(base),'-m','pip','install','--no-deps','--target',str(overlay),'httpx==0.27.2'],
        check=True,timeout=300,env=env)
    subprocess.run([str(base),'-c',"import httpx; assert httpx.__version__=='0.27.2'; import camel.model_backend, chatdev.chat_chain; print('native imports passed')"],
        cwd=source,check=True,timeout=120,env=env)
    record.update(status='DEPENDENCY_IMPORT_PASSED_NATIVE_WORKFLOW_PENDING',imported_modules=['camel.model_backend','chatdev.chat_chain'])
except Exception as exc:
    record.update(status='DEPENDENCY_CHECK_FAILED',error=type(exc).__name__+': '+str(exc))
finally:
    record['ended_at_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
    receipt.write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))
sys.exit(0 if record['status'].startswith('DEPENDENCY_IMPORT_PASSED') else 1)
