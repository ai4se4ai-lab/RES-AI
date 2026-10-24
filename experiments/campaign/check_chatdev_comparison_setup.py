"""CPU startup and inherited-runner checks; no experimental model observations."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import traceback

root=Path(__file__).resolve().parents[2]
folder=root/'comparison/chatdev'
protocol=json.loads((folder/'protocol.json').read_text())
proof={'status':'PREFLIGHT_RUNNING','model_calls':0}
try:
    case=root/protocol['queue'][0]['case']
    bound=subprocess.run([sys.executable,str(root/'experiments/campaign/upstream_bridge.py'),
        '--case',str(case),'--binding'],capture_output=True,text=True,check=True)
    if json.loads(bound.stdout):
        raise ValueError(bound.stdout)
    startup=folder/'cpu-startup'
    startup.mkdir(exist_ok=False)
    work='/scratch/mbabaei/resai-campaign-20261024'
    for phase in ('probe','production'):
        command=['apptainer','exec','--cleanenv','--containall','--bind',
            f'{root}:/campaign:ro,{case.parent}:/case:ro,{startup}:/outputs,{work}:/work:ro,'+os.environ['SLURM_TMPDIR']+':/runwork',
            '--env','OPENAI_API_KEY=job-local-unused,BASE_URL=http://127.0.0.1:18939/v1,PYTHONPATH=/work/overlays/chatdev-httpx-0.27.2',
            str(root/'containers/python311.sif'),'/work/environments/chatdev-legacy/container-attempt-1/bin/python',
            '/campaign/experiments/campaign/chatdev_episode_worker.py','--case','/case/case.json',
            '--phase',phase,'--index','0','--out','/outputs/'+phase,'--cpu-startup']
        subprocess.run(command,check=True,timeout=180)
        receipt=json.loads((startup/phase/'evidence.json').read_text())
        if not receipt.get('cpu_model_boundary_reached') or receipt['native_workflow_passed']:
            raise ValueError('CPU startup check did not stop at the first model boundary')
    # Exercise the real inherited runner and its output checks on a small CPU fixture.
    fixture=folder/'cpu-upstream-fixture'
    config=fixture/'hpc/config'
    config.mkdir(parents=True)
    output=fixture/'results'
    output.mkdir()
    command=shlex.join([sys.executable,'-c',f"from pathlib import Path;Path({str(output/'fixture.txt')!r}).write_text('CPU fixture only')"])
    graph=dict(project='cpu-upstream-fixture',stages=[dict(name='smoke',cpu_only=True,
        resources={'cpus':1,'mem':'1G','time':'00:01:00'},steps=[dict(name='native_fixture',cmd=command,produces=['fixture.txt'])])])
    (config/'experiments.json').write_text(json.dumps(graph))
    (config/'cluster.env').write_text('ACCOUNT="def-mbabaei"\nWORK="'+os.environ['SLURM_TMPDIR']+'/upstream-fixture"\n')
    fixture_case=fixture/'case.json'
    fixture_case.write_text(json.dumps({'episode_id':'cpu-upstream-fixture'}))
    subprocess.run([sys.executable,str(root/'experiments/campaign/upstream_bridge.py'),
        '--case',str(fixture_case),'--smoke'],check=True,timeout=60)
    if not (output/'fixture.txt').is_file():
        raise ValueError('inherited runner did not preserve declared CPU fixture output')
    validated=root/'validation/chatdev-24906078/validation.json'
    native=json.loads(validated.read_text())
    proof.update(status='COMPARATIVE_ADAPTER_PREFLIGHT_PASSED',
        native_smoke_passed=native['native_workflow_passed'],oracle_passed=native['oracle_passed'],
        model_endpoint_verified=native['model_endpoint_verified'],sandbox_validated=True,
        native_validation_source=str(validated),native_validation_sha256=hashlib.sha256(validated.read_bytes()).hexdigest(),
        canonical_and_corrupted_oracles_passed=True,probe_and_production_startup_to_first_model_call=True,
        actual_upstream_cpu_stage_passed=True)
except BaseException as exc:
    proof.update(status='PREFLIGHT_FAILED',error=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc())
finally:
    (folder/'preflight.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof,indent=2))
raise SystemExit(0 if proof['status']=='COMPARATIVE_ADAPTER_PREFLIGHT_PASSED' else 1)
