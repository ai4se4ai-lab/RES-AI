"""Reserve the full one-H100 ceiling before one native-validation submission."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

from budget import reserve

root=Path(__file__).resolve().parents[2]
os.chdir(root)
proof=json.loads((root/'chatdev-validation-preflight.json').read_text())
validation=root/'experiments/campaign/chatdev-validation-plan.json'
if proof.get('status')!='CPU_PREFLIGHT_PASSED_NATIVE_GPU_SMOKE_PENDING':
    raise ValueError('CPU preflight has not passed')
if hashlib.sha256(validation.read_bytes()).hexdigest()!=proof['validation_plan_sha256']:
    raise ValueError('validation plan changed')
for name,expected in json.loads(validation.read_text())['inputs'].items():
    if hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected:
        raise ValueError('validation input changed: '+name)
ledger_path=root/'gpu-budget-ledger.json'
lock=root/'gpu-budget-ledger.lock'
descriptor=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
try:
    ledger=json.loads(ledger_path.read_text()) if ledger_path.exists() else {'reservations':[]}
    plan=json.loads((root/'experiments/campaign/plan.json').read_text())
    record=reserve(plan,ledger,'ChatDev',1200,proof,purpose='native_validation')
    def save():
        temporary=ledger_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(ledger,indent=2)+'\n')
        os.replace(temporary,ledger_path)
    save()
    try:
        result=subprocess.run(['sbatch','--parsable','experiments/campaign/chatdev-native-validation.sh'],
            capture_output=True,text=True,timeout=30,check=True)
        job_id=result.stdout.strip().split(';')[0]
        if not job_id.isdigit():
            raise ValueError('unexpected scheduler response: '+result.stdout)
        record['job_id']=job_id
        record['submission_stderr']=result.stderr
        print(json.dumps({'ticket':record['ticket'],'job_id':job_id,'reserved_h100_seconds':record['reserved_seconds']}))
        save()
        collector=subprocess.run(['sbatch','--parsable','--dependency=afterany:'+job_id,
            'experiments/campaign/collect-native-validation.sh'],capture_output=True,text=True,timeout=30,check=True)
        record['collector_job_id']=collector.stdout.strip().split(';')[0]
    except Exception as exc:
        record['submission_error']=type(exc).__name__+': '+str(exc)
        if isinstance(exc,subprocess.CalledProcessError):
            record['submission_stdout']=exc.stdout
            record['submission_stderr']=exc.stderr
        # Keep the reservation until scheduler reconciliation; a timeout may
        # occur after submission. Never retry an ambiguous submission silently.
        raise
    finally:
        save()
finally:
    os.close(descriptor)
    lock.unlink()
