"""CPU-only native import and SWE-ReX local-deployment check inside Apptainer."""
import asyncio
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import traceback

root=Path('/campaign')
out=root/'environments/swe-agent/container-attempt-3'
out.mkdir(parents=True,exist_ok=False)
record=dict(subject='swe-agent',status='INSTALLING',native_workflow_passed=False,
    eligible_for_comparison=False,job_id=os.environ.get('SLURM_JOB_ID'),
    environment='/work/environments/swe-agent/container-attempt-1',
    dependency_repair='Pinned tools image provides git; PYTHONPATH selects the pinned native source tree including its config directory, as required by source-based installation; earlier receipts preserved',
    started_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
try:
    record['container_sha256']=hashlib.sha256((root/'containers/python311-tools.sif').read_bytes()).hexdigest()
    record['git_version']=subprocess.check_output(['git','--version'],text=True).strip()
    import sweagent.agent.agents
    from swerex.deployment.local import LocalDeployment
    from swerex.runtime.abstract import CreateBashSessionRequest,BashAction
    async def check():
        deployment=LocalDeployment()
        await deployment.start()
        try:
            assert (await deployment.is_alive()).is_alive
            await deployment.runtime.create_session(CreateBashSessionRequest(session='resai'))
            observation=await deployment.runtime.run_in_session(BashAction(session='resai',command='printf RESAI_RUNTIME_OK',timeout=8))
            if observation.exit_code!=0 or 'RESAI_RUNTIME_OK' not in observation.output:
                raise RuntimeError(str(observation))
            return observation.model_dump()
        finally:
            await deployment.stop()
    record['local_deployment_probe']=asyncio.run(check())
    record.update(status='DEPENDENCY_IMPORT_PASSED_LOCAL_RUNTIME_PASSED_NATIVE_WORKFLOW_PENDING',
        imported_modules=['sweagent.agent.agents','swerex.deployment.local'])
except Exception as exc:
    record.update(status='DEPENDENCY_CHECK_FAILED',error=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc())
finally:
    record['ended_at_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
    (out/'installation.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))
raise SystemExit(0 if record['status'].startswith('DEPENDENCY_IMPORT_PASSED') else 1)
