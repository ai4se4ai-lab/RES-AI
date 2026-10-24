"""Fresh pinned SWE-agent source and official example; native tools and loop retained."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile


def extract(archive,directory):
    directory.mkdir(parents=True,exist_ok=False)
    with tarfile.open(archive,'r:gz') as bundle:
        for member in bundle:
            if not member.isfile():
                continue
            dest=directory.joinpath(*Path(member.name).parts[1:]).resolve()
            if not dest.is_relative_to(directory.resolve()):
                raise RuntimeError('archive path escaped extraction root')
            dest.parent.mkdir(parents=True,exist_ok=True)
            with bundle.extractfile(member) as stream,dest.open('wb') as target:
                shutil.copyfileobj(stream,target)
            dest.chmod(member.mode & 0o777)


def setup(root,out):
    source=Path('/runwork/sweagent-native')
    extract(root/'feasibility/swe-agent/source.tar.gz',source)
    repo=Path('/testrepo')
    # The bind mount already exists; extraction itself uses a private child.
    fixture=Path('/runwork/fixture')
    extract(root/'selected-sources/sweagent-fixture/source.tar.gz',fixture)
    shutil.copytree(fixture,repo,dirs_exist_ok=True)
    subprocess.run(['git','init',str(repo)],check=True)
    subprocess.run(['git','-C',str(repo),'add','.'],check=True)
    subprocess.run(['git','-C',str(repo),'-c','user.name=RESAI fixture',
        '-c','user.email=resai-fixture@invalid','commit','-m','Pinned official example fixture'],check=True)
    base=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    subprocess.run(['/usr/local/bin/python','-m','venv','/runwork/tools-venv'],check=True)
    site=Path('/runwork/tools-venv/lib/python3.11/site-packages')
    (site/'base-dependencies.pth').write_text('/work/environments/swe-agent/container-attempt-1/lib/python3.11/site-packages\n')
    Path('/root/.bashrc').write_text('export PATH=/runwork/tools-venv/bin:$PATH\n')
    os.environ['PATH']='/runwork/tools-venv/bin:'+os.environ['PATH']
    os.environ['PYTHONPATH']=str(source)
    os.chdir(source)
    sys.path.insert(0,str(source))
    import yaml
    config=yaml.safe_load((source/'config/default.yaml').read_text())
    config['env']=dict(deployment={'type':'local'},repo={'type':'preexisting','repo_name':'testrepo','base_commit':base})
    config['agent']['model']=dict(name='openai/qwen3.8:27b',api_base='http://127.0.0.1:18939/v1',
        api_key='job-local-unused',max_input_tokens=12288,max_output_tokens=4096,
        per_instance_call_limit=32,per_instance_cost_limit=0,total_cost_limit=0,temperature=0)
    config['problem_statement']=dict(type='text',id='official-example-1',
        text=(repo/'problem_statements/1.md').read_text()+'\nFor this run the affected file is src/testpkg/missing_colon.py. Fix the syntax error while preserving ordinary division behavior.')
    config['output_dir']=str(out/'native-trajectory')
    config['actions']=dict(open_pr=False,apply_patch_locally=False)
    return config,repo,base
