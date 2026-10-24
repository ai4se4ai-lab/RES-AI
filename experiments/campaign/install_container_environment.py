"""CPU-only native dependency checks in the pinned site-compatible container.

This is installation evidence, not a successful artifact workflow or eligibility.
Run inside Apptainer with the campaign root bound to /campaign and scratch to /work.
"""
import argparse
import datetime as dt
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


SUBJECTS = {
    'agentcoder': ('feasibility/agentcoder/source', ['-r', 'requirements.txt', 'numpy', 'tqdm'], ['openai', 'datasets', 'numpy']),
    'chatdev-legacy': ('selected-sources/chatdev/source', ['-r', 'requirements.txt'], ['camel.model_backend', 'chatdev.chat_chain']),
    'metagpt': ('feasibility/metagpt/source', ['.'], ['metagpt.team']),
    'swe-agent': ('feasibility/swe-agent/source', ['.'], ['sweagent.agent.agents', 'swerex.deployment']),
}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('subject',choices=SUBJECTS)
    args=parser.parse_args()
    root=Path('/campaign')
    name=args.subject
    source, requirements, modules=SUBJECTS[name]
    source=root/source
    out=root/'environments'/name/'container-attempt-1'
    out.mkdir(parents=True,exist_ok=False)
    venv=Path('/work/environments')/name/'container-attempt-1'
    record=dict(subject=name,status='INSTALLING',native_workflow_passed=False,
        eligible_for_comparison=False,job_id=os.environ.get('SLURM_JOB_ID'),
        started_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        source=str(source),environment=str(venv),python=sys.version,
        container_sha256=hashlib.sha256((root/'containers/python311.sif').read_bytes()).hexdigest())
    receipt=out/'installation.json'
    receipt.write_text(json.dumps(record,indent=2)+'\n')
    env=dict(os.environ,PIP_CONFIG_FILE='/dev/null',PIP_DISABLE_PIP_VERSION_CHECK='1',
        OPENAI_API_KEY='job-local-unused',BASE_URL='http://127.0.0.1:18939/v1',
        OPENAI_API_BASE='http://127.0.0.1:18939/v1',PYTHONPATH=str(source))
    env.pop('PIP_CONSTRAINT',None)
    start=time.monotonic()
    try:
        subprocess.run([sys.executable,'-m','venv','--copies',str(venv)],check=True,timeout=120,env=env)
        python=str(venv/'bin/python')
        subprocess.run([python,'-m','pip','install','--upgrade','pip'],check=True,timeout=180,env=env)
        subprocess.run([python,'-m','pip','install',*requirements],cwd=source,check=True,timeout=1800,env=env)
        with (out/'pip-freeze.txt').open('w') as stream:
            subprocess.run([python,'-m','pip','freeze'],stdout=stream,check=True,env=env)
        subprocess.run([python,'-c','import importlib; '+ '; '.join(f'importlib.import_module({m!r})' for m in modules)],
            cwd=source,check=True,timeout=120,env=env)
        record.update(status='DEPENDENCY_IMPORT_PASSED_NATIVE_WORKFLOW_PENDING',imported_modules=modules)
    except Exception as exc:
        record.update(status='DEPENDENCY_CHECK_FAILED',error=type(exc).__name__+': '+str(exc))
    finally:
        record.update(elapsed_cpu_job_process_seconds=time.monotonic()-start,
            ended_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
        receipt.write_text(json.dumps(record,indent=2)+'\n')
        print(json.dumps(record,indent=2))
    return 0 if record['status'].startswith('DEPENDENCY_IMPORT_PASSED') else 1


if __name__=='__main__':
    raise SystemExit(main())
