"""Freeze the native ChatDev subset and prove setup/oracles on CPU before submission."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import shlex
import subprocess
import sys

from resai.core import digest
from chatdev_validation import TASK,CASES

root=Path(__file__).resolve().parents[2]
os.chdir(root)
campaign=json.loads((root/'experiments/campaign/plan.json').read_text())
out=root/'comparison/chatdev'
if (out/'protocol.json').exists():
    raise ValueError('refusing to overwrite a frozen comparison protocol')
out.mkdir(parents=True,exist_ok=True)
native=json.loads((root/'validation/chatdev-24906078/validation.json').read_text())
if not all(native.get(k) is True for k in ('native_workflow_passed','oracle_passed','model_endpoint_verified')):
    raise ValueError('native ChatDev model/workflow/oracle validation has not passed')
science=json.loads((root/'experiments/campaign/chatdev-validation-plan.json').read_text())['scientific']
bank=json.loads((root/'experiments/campaign/chatdev-benchmark.json').read_text())
probe=dict(task_id='authored-normalization-setup',module='text_tools.py',entry_point='normalize_words',
    prompt=TASK,oracle='\n'.join(f'assert normalize_words({s!r}) == {" ".join(s.split()).lower()!r}' for s in CASES))
source_names=['controller.py','chatdev_episode.py','chatdev_episode_worker.py','run_chatdev_phase.py',
    'upstream_bridge.py','chatdev-comparison.sh','ollama_transport.py','safe_exec.py','chatdev-benchmark.json',
    'advance_chatdev_comparison.py','collect-chatdev-comparison.sh']
inputs={'experiments/campaign/'+name:hashlib.sha256((root/'experiments/campaign'/name).read_bytes()).hexdigest() for name in source_names}
for name in ('src/resai/core.py','src/resai/pipeline.py','src/resai/__init__.py','hpc/scripts/hpclib.py',
             'hpc/scripts/run_stage.py','hpc/UPSTREAM.json','selected-sources/chatdev/source.tar.gz'):
    inputs[name]=hashlib.sha256((root/name).read_bytes()).hexdigest()
order=random.Random(20261024)
rows=[]
for subject in campaign['subjects']:
    for seed in campaign['paired_seeds']:
        for fault in campaign['episode_classes']:
            conditions=campaign['conditions'][:]
            order.shuffle(conditions)
            if subject['name']!='ChatDev':
                continue
            task=bank['tasks'][seed]
            production=dict(task_id=task['task_id'],module='solution.py',entry_point=task['entry_point'],
                prompt='Create a pure Python 3 module named solution.py implementing the function below. Keep it self-contained; imports from typing are allowed, with no other imports or external packages. Include a minimal main.py demonstration. Use no GUI, file access or network access.\n\n'+task['prompt'],
                oracle=task['test']+'\ncheck('+task['entry_point']+')\n')
            for condition in conditions:
                episode_id=f'chatdev-{seed}-{fault}-{condition}'
                case_dir=out/'cases'/episode_id
                config=case_dir/'hpc/config'
                config.mkdir(parents=True)
                case_file=case_dir/'case.json'
                scientific=dict(artifact='ChatDev',source_revision='31fd994416a251ecdeb1f0a73c329271743bfb56',
                    backend=science,paired_seed=seed,tasks_hash=digest({'probe':probe,'production':production}),batch_invariant=False)
                resources=dict(gpus='h100:1',nodes=1,cpus=4,mem='48G',time='00:15:00')
                stages=[]
                for phase in ('probe','production'):
                    command=shlex.join([sys.executable,str(root/'experiments/campaign/run_chatdev_phase.py'),
                        '--case',str(case_file),'--phase',phase,'--index','0'])
                    stages.append(dict(name='smoke' if phase=='probe' else 'production',resources=resources,
                        steps=[dict(name='native_'+phase,cmd=command,always=True,critical=True,
                            produces=[phase+'-0/'+(probe if phase=='probe' else production)['module']])]))
                graph=dict(project='resai-chatdev-comparison',vars={'BATCH_SIZE':'1'},resai_scientific=scientific,stages=stages)
                graph_file=config/'experiments.json'
                graph_file.write_text(json.dumps(graph,indent=2)+'\n')
                env_file=config/'cluster.env'
                env_file.write_text('ACCOUNT="def-mbabaei_gpu"\nWORK="/scratch/mbabaei/resai-campaign-20261024/upstream"\n')
                os.environ['HPC_DIR']=str(case_dir/'hpc')
                module=importlib.util.spec_from_file_location('case_engine',root/'hpc/scripts/hpclib.py')
                engine=importlib.util.module_from_spec(module)
                module.loader.exec_module(engine)
                resolved=engine.resolve(graph,False)
                if errors:=engine.validate(resolved):
                    raise ValueError(errors)
                bound=dict(inputs)
                for path in (graph_file,env_file):
                    bound[path.relative_to(root).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
                plan=dict(scientific=scientific,execution=dict(nodes=1,gpus_per_node=1,batch_size=1,
                    wall_seconds=900,partition='site-default',graph_hash=digest(resolved),episode_class=fault),
                    required_probes=['imports','model_init','native_workflow','output_schema','heldout_oracle'],
                    budget_gpu_seconds=900,max_attempts=4,memory_limit=.9,stability_epsilon=.05,
                    evidence_ttl_seconds=3600,inputs=bound)
                case=dict(episode_id=episode_id,artifact='ChatDev',paired_seed=seed,episode_class=fault,
                    condition=condition,scientific=science,tasks={'probe':probe,'production':production},policy_plan=plan)
                case_file.write_text(json.dumps(case,indent=2)+'\n')
                rows.append(dict(episode_id=episode_id,case=str(case_file.relative_to(root)),
                    case_sha256=hashlib.sha256(case_file.read_bytes()).hexdigest(),status='PLANNED'))
assert len(rows)==140
# Oracle calibration uses canonical programs and known wrong programs, not model outcomes.
for task in bank['tasks']:
    for body,expected in ((task['canonical_solution'],True),('    return None\n',False)):
        code=task['prompt']+body+'\n'+task['test']+'\ncheck('+task['entry_point']+')'
        proc=subprocess.run(['apptainer','exec','--cleanenv','--containall','--bind',str(root)+':/campaign:ro',
            str(root/'containers/python311.sif'),'python','/campaign/experiments/campaign/safe_exec.py'],
            input=json.dumps({'code':code}),text=True,capture_output=True,timeout=20)
        if (proc.returncode==0)!=expected:
            raise ValueError('oracle calibration failed: '+task['task_id']+' '+proc.stderr)
protocol=dict(campaign_id=campaign['campaign_id'],artifact='ChatDev',potential_episodes=140,
    master_protocol_sha256=hashlib.sha256((root/'experiments/campaign/plan.json').read_bytes()).hexdigest(),
    production_tasks_by_seed=[t['task_id'] for t in bank['tasks']],heldout_task=probe['task_id'],
    model_server_lifecycle='one server per episode; fresh native processes/workspaces per probe and production; all costs charged',
    faults=dict(environment_fault='remove native RoleConfig and replay two actual earlier clean probe receipts; no raw telemetry fabrication',
        resource_fault='hide CUDA devices from the local model server inside the allocated one-H100 job; GPU residency check must fail before inference',
        output_contract_fault='replace persisted target-function body with return None after native generation; retain original and diff'),
    ablations=dict(no_coverage='ignore coverage reason only; preserve schema/status/identity/memory/budget checks',
        no_identity_freshness='ignore plan matching and age; retain two distinct actual observations and all outcome/resource checks',
        no_refinement='disable only the prototype permitted batch-size proposal; batch invariance is false for this adapter'),
    stage_wall_seconds=900,reservation_seconds=960,queue=rows,inputs=inputs,
    readiness_bindings='full policies verify declared input hashes, resolved graph identity, scientific metadata and resource mapping',
    status='FROZEN_CPU_ORACLES_PASSED_NATIVE_STARTUP_PENDING')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
print(json.dumps({'episodes':140,'oracle_calibration':'PASSED','protocol':str(out/'protocol.json')}))
