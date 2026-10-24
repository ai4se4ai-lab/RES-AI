"""One comparative episode, using genuine native execution and the upstream runner."""
import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

from controller import execute

parser=argparse.ArgumentParser()
parser.add_argument('--case',type=Path,required=True)
args=parser.parse_args()
root=Path(__file__).resolve().parents[2]
spec=json.loads(args.case.read_text())
case_dir=args.case.parent
results=case_dir/'results'
results.mkdir(exist_ok=True)
cache=case_dir.parent.parent/'cache'/('seed-'+str(spec['paired_seed'])+'.json')

class MissingCache(Exception):
    pass
class NativeAdapter:
    def validate_binding(self,plan):
        proc=subprocess.run([sys.executable,str(root/'experiments/campaign/upstream_bridge.py'),
            '--case',str(args.case),'--binding'],text=True,capture_output=True)
        (results/'resai-binding.stdout').write_text(proc.stdout)
        (results/'resai-binding.stderr').write_text(proc.stderr)
        try:
            return json.loads(proc.stdout)
        except Exception:
            return ['binding validation failed: '+proc.stderr]
    def validate_upstream(self,plan):
        proc=subprocess.run([sys.executable,str(root/'experiments/campaign/upstream_bridge.py'),'--case',str(args.case)],text=True,capture_output=True)
        (results/'upstream-static.stdout').write_text(proc.stdout)
        (results/'upstream-static.stderr').write_text(proc.stderr)
        try:
            return json.loads(proc.stdout)
        except Exception:
            return ['upstream validator failed: '+proc.stderr]
    def remember(self,row):
        if spec['episode_class']!='clean' or row.get('status')!='ok' or not row.get('scientific_task_solved') or not row.get('output_valid'):
            return
        cache.parent.mkdir(parents=True,exist_ok=True)
        rows=json.loads(cache.read_text()) if cache.exists() else []
        if len(rows)<2 and not any(r['attempt_id']==row['attempt_id'] for r in rows):
            rows.append(copy.deepcopy(row))
            cache.write_text(json.dumps(rows,indent=2)+'\n')
    def upstream_smoke(self,plan):
        command=[sys.executable,str(root/'experiments/campaign/upstream_bridge.py'),'--case',str(args.case),'--smoke']
        with (results/'upstream-smoke.log').open('w') as stream:
            proc=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT)
        path=results/'probe-0/measured-evidence.json'
        if path.exists():
            self.remember(json.loads(path.read_text()))
        return dict(returncode=proc.returncode,outputs_present=(results/'probe-0'/spec['tasks']['probe']['module']).is_file(),
            raw_trace=str(results/'upstream-smoke.log'))
    def native(self,phase,index):
        command=[sys.executable,str(root/'experiments/campaign/run_chatdev_phase.py'),
            '--case',str(args.case),'--phase',phase,'--index',str(index)]
        with (results/(phase+'-'+str(index)+'.controller.log')).open('w') as stream:
            proc=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT)
        path=results/(phase+'-'+str(index))/'measured-evidence.json'
        if not path.exists():
            raise RuntimeError('native adapter did not produce measured evidence; returncode='+str(proc.returncode))
        row=json.loads(path.read_text())
        if phase=='probe':
            self.remember(row)
        return row
    def probe(self,plan,index):
        if spec['episode_class']=='environment_fault':
            rows=json.loads(cache.read_text()) if cache.exists() else []
            if len(rows)<2:
                raise MissingCache('two real earlier clean observations are required for the frozen stale-environment operator')
            (results/('replayed-source-'+str(index)+'.json')).write_text(json.dumps({'cache':str(cache),'source_attempt_id':rows[index]['attempt_id']},indent=2)+'\n')
            return copy.deepcopy(rows[index])
        return self.native('probe',index)
    def production(self,plan):
        if spec['condition']=='direct_native':
            return self.native('production',0)
        command=[sys.executable,str(root/'experiments/campaign/upstream_bridge.py'),
            '--case',str(args.case),'--production-stage']
        with (results/'upstream-production.log').open('w') as stream:
            proc=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT)
        path=results/'production-0/measured-evidence.json'
        if not path.exists():
            raise RuntimeError('upstream production did not produce measured native evidence')
        row=json.loads(path.read_text())
        row['upstream_production_returncode']=proc.returncode
        return row

record=dict(episode_id=spec['episode_id'],artifact='ChatDev',condition=spec['condition'],
    paired_seed=spec['paired_seed'],episode_class=spec['episode_class'],job_id=os.environ.get('SLURM_JOB_ID'),
    started_at=time.time(),status='RUNNING',comparative_episode=True)
try:
    decision=execute(spec['condition'],spec['policy_plan'],NativeAdapter(),time.time)
    record['execution']=decision
    if not decision['admitted']:
        record['status']='POLICY_BLOCKED'
    else:
        production=decision['production']
        valid=production['status']=='ok' and production['output_valid'] and production.get('scientific_task_solved') is True
        record.update(status='PRODUCTION_VALID' if valid else 'PRODUCTION_INVALID',valid_completion=valid)
except MissingCache as exc:
    record.update(status='UNEXECUTED_MISSING_CLEAN_CACHE',error=str(exc))
except BaseException as exc:
    record.update(status='IMPLEMENTATION_ERROR',error=type(exc).__name__+': '+str(exc))
    (results/'controller-failure.log').write_text(traceback.format_exc())
finally:
    record['ended_at']=time.time()
    (results/'episode.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))
raise SystemExit(0 if record['status'] in ('POLICY_BLOCKED','PRODUCTION_VALID','PRODUCTION_INVALID') else 1)
