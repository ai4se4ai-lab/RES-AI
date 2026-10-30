"""Bound legacy dependency resolution in a fresh CPU-only environment."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

root=Path('/campaign')
source=root/'feasibility/repairagent/source/repair_agent'
out=root/'environments/repairagent/container-attempt-4'
out.mkdir(parents=True,exist_ok=False)
venv=Path('/work/environments/repairagent/container-attempt-4')
constraints=root/'experiments/campaign/repairagent-constraints-v4.txt'
record=dict(subject='repairagent',status='INSTALLING',job_id=os.environ['SLURM_JOB_ID'],
    model_calls=0,native_workflow_passed=False,eligible_for_comparison=False,
    environment=str(venv),started_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
    constraints_sha256=hashlib.sha256(constraints.read_bytes()).hexdigest(),
    archive_sha256=hashlib.sha256((source.parent.parent/'source.tar.gz').read_bytes()).hexdigest(),
    adaptation='Constrain unbounded dependencies to the generations exposing native legacy APIs; unchanged upstream requirements/source and previous failed environments retained.')
receipt=out/'installation.json'
receipt.write_text(json.dumps(record,indent=2)+'\n')
env=dict(os.environ,PIP_CONFIG_FILE='/dev/null',PIP_DISABLE_PIP_VERSION_CHECK='1',
    OPENAI_API_KEY='job-local-unused',OPENAI_API_BASE='http://127.0.0.1:18939/v1',
    PYTHONPATH=str(source))
env.pop('PIP_CONSTRAINT',None)
try:
    if venv.exists():raise RuntimeError('refusing existing environment')
    subprocess.run([sys.executable,'-m','venv','--copies',str(venv)],env=env,check=True,timeout=900)
    python=str(venv/'bin/python')
    subprocess.run([python,'-m','pip','install','--upgrade','pip'],env=env,check=True,timeout=180)
    subprocess.run([python,'-m','pip','install','-c',str(constraints),'-r','requirements-core.txt'],cwd=source,env=env,check=True,timeout=1200)
    subprocess.run([python,'-m','pip','check'],env=env,check=True,timeout=60)
    with (out/'pip-freeze.txt').open('w') as stream:
        subprocess.run([python,'-m','pip','freeze'],env=env,stdout=stream,check=True,timeout=60)
    subprocess.run([python,'-c','import autogpt.app.main; import autogpt.commands.defects4j_static; print("NATIVE_IMPORTS_PASSED_NO_MODEL_CALLS")'],cwd=source,env=env,check=True,timeout=120)
    record.update(status='DEPENDENCY_IMPORT_PASSED_NATIVE_WORKFLOW_PENDING')
except Exception as exc:
    record.update(status='DEPENDENCY_CHECK_FAILED',error=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc())
finally:
    record['ended_at_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
    receipt.write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))
raise SystemExit(0 if record['status'].startswith('DEPENDENCY_IMPORT_PASSED') else 1)
