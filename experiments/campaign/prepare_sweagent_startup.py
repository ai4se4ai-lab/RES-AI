"""CPU-only native SWE-agent setup to the first model boundary, using official example 1."""
import datetime as dt
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import traceback

root=Path('/campaign')
source=root/'feasibility/swe-agent/source'
proof=dict(subject='SWE-agent',status='CPU_SETUP_RUNNING',model_calls=0,native_workflow_passed=False,
    fixture_repository='SWE-agent/test-repo',fixture_revision='7bef0c62cce60a2cb6df0c80f18b3054e1c23630',
    job_id=os.environ.get('SLURM_JOB_ID'),started_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
try:
    repo=Path('/testrepo')
    with tarfile.open(root/'selected-sources/sweagent-fixture/source.tar.gz','r:gz') as bundle:
        for member in bundle:
            if not member.isfile():
                continue
            dest=repo.joinpath(*Path(member.name).parts[1:]).resolve()
            if not dest.is_relative_to(repo.resolve()):
                raise ValueError('fixture archive path escaped')
            dest.parent.mkdir(parents=True,exist_ok=True)
            with bundle.extractfile(member) as stream,dest.open('wb') as target:
                shutil.copyfileobj(stream,target)
    subprocess.run(['git','init',str(repo)],check=True)
    subprocess.run(['git','-C',str(repo),'add','.'],check=True)
    subprocess.run(['git','-C',str(repo),'-c','user.name=RESAI fixture','-c','user.email=resai-fixture@invalid',
        'commit','-m','Pinned official example fixture'],check=True)
    base=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    subprocess.run(['/usr/local/bin/python','-m','venv','/runwork/tools-venv'],check=True)
    site=Path('/runwork/tools-venv/lib/python3.11/site-packages')
    (site/'base-dependencies.pth').write_text('/work/environments/swe-agent/container-attempt-1/lib/python3.11/site-packages\n')
    Path('/root/.bashrc').write_text('export PATH=/runwork/tools-venv/bin:$PATH\n')
    os.environ['PATH']='/runwork/tools-venv/bin:'+os.environ['PATH']
    os.chdir(source)
    sys.path.insert(0,str(source))
    import yaml,litellm
    from sweagent.run.run_single import RunSingleConfig,RunSingle
    config=yaml.safe_load((source/'config/default.yaml').read_text())
    config['env']=dict(deployment={'type':'local'},repo={'type':'preexisting','repo_name':'testrepo','base_commit':base})
    config['agent']['model']=dict(name='openai/qwen3.8:27b',api_base='http://127.0.0.1:18939/v1',
        api_key='job-local-unused',max_input_tokens=12288,max_output_tokens=4096,
        per_instance_call_limit=32,per_instance_cost_limit=0,temperature=0)
    config['problem_statement']=dict(type='text',id='official-example-1',
        text=(repo/'problem_statements/1.md').read_text()+'\nFor this run the affected file is src/testpkg/missing_colon.py. Fix the syntax error while preserving ordinary division behavior.')
    config['output_dir']='/runwork/native-trajectory'
    class ModelBoundaryReached(KeyboardInterrupt):
        pass
    def boundary(*args,**kwargs):
        if not kwargs.get('messages') or not kwargs.get('tools'):
            raise ValueError('native call missing messages/tool schema')
        proof['native_tool_count']=len(kwargs['tools'])
        raise ModelBoundaryReached()
    litellm.completion=boundary
    runner=RunSingle.from_config(RunSingleConfig.model_validate(config))
    try:
        runner.run()
    except ModelBoundaryReached:
        proof.update(status='CPU_NATIVE_SETUP_TO_MODEL_BOUNDARY_PASSED',native_setup_to_first_model_call=True,
            native_configuration=config,fixture_local_commit=base)
    else:
        raise ValueError('native setup did not reach model boundary')
    finally:
        runner.env.close()
except BaseException as exc:
    proof.update(status='CPU_SETUP_FAILED',error=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc())
finally:
    proof['ended_at_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
    (root/'sweagent-setup-preflight.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof,indent=2))
raise SystemExit(0 if proof['status'].endswith('_PASSED') else 1)
