"""CPU-only missing-import repair in an overlay; preserve the original environment/source."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import traceback

root=Path('/campaign')
attempt=os.environ.get('RESAI_IMPORT_ATTEMPT','4')
out=root/('environments/agilecoder/container-attempt-'+attempt)
out.mkdir(parents=True,exist_ok=False)
source=root/'feasibility/agilecoder/source'
overlay=Path('/work/overlays/agilecoder-import-extras-'+attempt)
dependencies=['tenacity==8.2.3','Flask==2.3.3','numpy==1.26.4']
if overlay.exists():
    raise RuntimeError('refusing to reuse an import overlay')
python='/work/environments/agilecoder/container-attempt-2/bin/python'
record=dict(subject='agilecoder',status='INSTALLING',job_id=os.environ.get('SLURM_JOB_ID'),
    model_calls=0,native_workflow_passed=False,eligible_for_comparison=False,
    base_environment=str(Path(python).parents[1]),dependency_overlay=str(overlay),
    added_import_dependencies=dependencies,
    source_archive_sha256=hashlib.sha256((source.parent/'source.tar.gz').read_bytes()).hexdigest(),
    started_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
receipt=out/'installation.json'
receipt.write_text(json.dumps(record,indent=2)+'\n')
started=time.monotonic()
try:
    subprocess.run([python,'-m','pip','install','--target',str(overlay),*dependencies],check=True,timeout=600)
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
print('NATIVE_IMPORTS_PASSED_NO_MODEL_CALLS')
"""
    env=dict(os.environ,PYTHONPATH=str(overlay)+':'+str(source),OPENAI_API_KEY='job-local-unused')
    subprocess.run([python,'-c',code],cwd=source,env=env,check=True,timeout=120)
    with (out/'overlay-packages.json').open('w') as stream:
        subprocess.run([python,'-m','pip','list','--path',str(overlay),'--format=json'],stdout=stream,check=True)
    record.update(status='DEPENDENCY_IMPORT_PASSED_NATIVE_WORKFLOW_PENDING',
        inactive_provider_adaptation='During imports only: inactive Vertex credential constructor disabled in memory; no source edits, credential files or cloud/model calls.',
        imported_modules=['agilecoder.camel.model_backend','agilecoder.components.chat_chain'])
except Exception as exc:
    record.update(status='DEPENDENCY_CHECK_FAILED',error=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc())
finally:
    record.update(elapsed_cpu_job_process_seconds=time.monotonic()-started,
        ended_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    receipt.write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))
raise SystemExit(0 if record['status'].startswith('DEPENDENCY_IMPORT_PASSED') else 1)
