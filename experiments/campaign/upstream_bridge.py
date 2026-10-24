"""Use the inherited upstream validator/runner, never a smoke-result proxy."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

parser=argparse.ArgumentParser()
parser.add_argument('--case',type=Path,required=True)
parser.add_argument('--smoke',action='store_true')
parser.add_argument('--binding',action='store_true')
parser.add_argument('--production-stage',action='store_true')
args=parser.parse_args()
root=Path(__file__).resolve().parents[2]
case=json.loads(args.case.read_text())
hpc=args.case.parent/'hpc'
os.environ['HPC_DIR']=str(hpc)
spec=importlib.util.spec_from_file_location('upstream_campaign_hpclib',root/'hpc/scripts/hpclib.py')
engine=importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
graph=engine.resolve(engine.load_experiments(hpc/'config/experiments.json'),False)
errors=engine.validate(graph)
if args.binding:
    from resai.pipeline import verify_inputs,verify_correspondence,validate_site_config
    errors+=verify_inputs(case['policy_plan'],root=root,hpc_relative=hpc.relative_to(root).as_posix())
    errors+=verify_correspondence(case['policy_plan'],graph)
    errors+=validate_site_config(engine.cluster())
if not args.smoke and not args.production_stage:
    print(json.dumps(errors))
    raise SystemExit(0 if not errors else 2)
if errors:
    raise ValueError(errors)
env=dict(os.environ,HPC_DIR=str(hpc),RESULTS=str(args.case.parent/'results'),
    RUN_ID=case['episode_id'])
raise SystemExit(subprocess.run([sys.executable,str(root/'hpc/scripts/run_stage.py'),
    '--stage','production' if args.production_stage else 'smoke','--cell','0','--run-id',case['episode_id']],env=env).returncode)
