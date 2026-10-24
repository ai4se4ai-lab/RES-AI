"""Validate frozen CPU proof, reserve one H100 ceiling, then submit once."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

from budget import reserve

parser=argparse.ArgumentParser()
parser.add_argument('--plan',type=Path,required=True)
parser.add_argument('--proof',type=Path,required=True)
args=parser.parse_args()
root=Path(__file__).resolve().parents[2]
os.chdir(root)
proof=json.loads(args.proof.read_text())
plan=json.loads(args.plan.read_text())
if proof.get('status')!='CPU_PREFLIGHT_PASSED_NATIVE_GPU_SMOKE_PENDING':
    raise ValueError('native CPU preflight has not passed')
if hashlib.sha256(args.plan.read_bytes()).hexdigest()!=proof['validation_plan_sha256']:
    raise ValueError('native validation plan changed')
for name,expected in plan['inputs'].items():
    path=(root/name).resolve()
    if not path.is_relative_to(root.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
        raise ValueError('frozen native validation input changed: '+name)
script=plan['gpu_script']
if script not in plan['inputs']:
    raise ValueError('GPU script is not frozen')
ledger_path=root/'gpu-budget-ledger.json'
lock=ledger_path.with_suffix('.lock')
descriptor=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
try:
    ledger=json.loads(ledger_path.read_text()) if ledger_path.exists() else {'reservations':[]}
    campaign=json.loads((root/'experiments/campaign/plan.json').read_text())
    record=reserve(campaign,ledger,plan['subject'],plan['wall_seconds'],proof,purpose='native_validation')
    record['validation_plan_sha256']=proof['validation_plan_sha256']
    def save():
        temporary=ledger_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(ledger,indent=2)+'\n')
        os.replace(temporary,ledger_path)
    save()
    try:
        wall=plan['wall_seconds']
        request=['sbatch','--parsable','--account=def-mbabaei_gpu','--gpus=h100:1',
            '--cpus-per-task=4','--mem=48G',f'--time={wall//3600:02}:{wall//60%60:02}:{wall%60:02}',script]
        result=subprocess.run(request,text=True,capture_output=True,timeout=30,check=True)
        job_id=result.stdout.strip().split(';')[0]
        if not job_id.isdigit():
            raise ValueError('ambiguous GPU submission response: '+result.stdout)
        record.update(job_id=job_id,submission_request=request,submission_stderr=result.stderr)
        save()
        collector=subprocess.run(['sbatch','--parsable','--dependency=afterany:'+job_id,
            'experiments/campaign/collect-native-validation-v2.sh'],text=True,capture_output=True,timeout=30,check=True)
        record['collector_job_id']=collector.stdout.strip().split(';')[0]
        print(json.dumps(record,indent=2))
    except Exception as exc:
        record['submission_error']=type(exc).__name__+': '+str(exc)
        if isinstance(exc,subprocess.CalledProcessError):
            record.update(submission_stdout=exc.stdout,submission_stderr=exc.stderr)
        raise
    finally:
        save()  # Ambiguous submissions retain their reservation until reconciled.
finally:
    os.close(descriptor)
    lock.unlink()
