"""Execute one genuine native process in its private container and measure it."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

from resai.core import digest

parser=argparse.ArgumentParser()
parser.add_argument('--case',type=Path,required=True)
parser.add_argument('--phase',choices=('probe','production'),required=True)
parser.add_argument('--index',type=int,required=True)
args=parser.parse_args()
spec=json.loads(args.case.read_text())
root=Path(__file__).resolve().parents[2]
case_dir=args.case.parent
results=case_dir/'results'
results.mkdir(exist_ok=True)
key=args.phase+'-'+str(args.index)
out=results/key
if out.exists():
    raise ValueError('refusing to reuse a native attempt directory')
samples=[]
stop=threading.Event()
def monitor():
    while not stop.is_set():
        try:
            raw=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,memory.total',
                '--format=csv,noheader,nounits','--id='+os.environ.get('RESAI_ALLOCATED_GPU',os.environ.get('CUDA_VISIBLE_DEVICES','0'))],text=True,timeout=5)
            used,total=map(float,raw.splitlines()[0].split(','))
            samples.append(dict(timestamp=time.time(),used_mib=used,total_mib=total))
        except Exception as exc:
            samples.append(dict(timestamp=time.time(),error=str(exc)))
        stop.wait(.5)
thread=threading.Thread(target=monitor,daemon=True)
thread.start()
work='/scratch/mbabaei/resai-campaign-20261024'
command=['apptainer','exec','--cleanenv','--containall','--bind',
    f'{root}:/campaign:ro,{case_dir}:/case:ro,{results}:/outputs,{work}:/work:ro,'+
    os.environ['SLURM_TMPDIR']+':/runwork,/scratch/mbabaei/ollama_models:/models:ro',
    '--env','OPENAI_API_KEY=job-local-unused,BASE_URL=http://127.0.0.1:18939/v1',
    str(root/'containers/python311.sif'),'/work/environments/chatdev-legacy/container-attempt-1/bin/python',
    '/campaign/experiments/campaign/chatdev_episode_worker_v2.py','--case','/case/case.json',
    '--phase',args.phase,'--index',str(args.index),'--out','/outputs/'+key]
# Keep the proven OpenAI/httpx compatibility overlay without changing base packages.
command[command.index('--env')+1]+=',PYTHONPATH=/work/overlays/chatdev-httpx-0.27.2'
start=time.monotonic()
try:
    with (results/(key+'.stdout.log')).open('w') as stream:
        try:
            proc=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,timeout=600)
            returncode=proc.returncode
        except subprocess.TimeoutExpired:
            returncode=124
finally:
    duration=time.monotonic()-start
    stop.set()
    thread.join(timeout=6)
out.mkdir(exist_ok=True)
raw=json.loads((out/'evidence.json').read_text()) if (out/'evidence.json').exists() else {}
record=dict(raw)
record.update(attempt_id=f"{os.environ['SLURM_JOB_ID']}-{key}",job_id=os.environ['SLURM_JOB_ID'],
    plan_hash=digest(spec['policy_plan']),timestamp=time.time(),gpu_seconds=duration,
    memory_measurement='whole-device nvidia-smi samples every 0.5 seconds; timed process duration is not allocation accounting',
    peak_memory_fraction=max((r['used_mib']/r['total_mib'] for r in samples if 'used_mib' in r),default=2),
    passed_probes=raw.get('passed_probes',[]),output_valid=raw.get('output_valid') is True,
    status='ok' if returncode==0 and raw.get('native_workflow_passed') is True else 'failed',
    returncode=returncode,native_process_command=command)
if returncode:
    record['fault']=raw.get('fault') or ('timeout' if returncode==124 else 'native_process_failure')
(out/'measured-evidence.json').write_text(json.dumps(record,indent=2)+'\n')
(out/'memory-samples.json').write_text(json.dumps(samples,indent=2)+'\n')
print(json.dumps(record,indent=2))
raise SystemExit(0 if record['status']=='ok' else 1)
