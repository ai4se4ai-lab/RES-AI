"""CPU-only exact-source acquisition and static feasibility evidence; never infer eligibility."""
import argparse
import ast
import concurrent.futures
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import urllib.request


def inspect(subject, root):
    slug = re.sub('[^a-z0-9]+','-',subject['name'].lower())
    out = root/slug
    out.mkdir(parents=True,exist_ok=True)
    row = {'name':subject['name'],'source_revision':subject['retrieved_head'],
           'status':'SOURCE_CHECK_RUNNING','eligible_for_comparison':False}
    try:
        repo = subject['repository'].removeprefix('https://github.com/')
        url = f"https://codeload.github.com/{repo}/tar.gz/{subject['retrieved_head']}"
        archive = out/'source.tar.gz'
        request = urllib.request.Request(url,headers={'User-Agent':'RES-AI-campaign-feasibility'})
        with urllib.request.urlopen(request,timeout=90) as response, archive.open('wb') as stream:
            total = 0
            while chunk := response.read(1024*1024):
                total += len(chunk)
                if total > 400*1024*1024:
                    raise ValueError('source download exceeded 400 MiB acquisition cap')
                stream.write(chunk)
        row['source_url'] = url
        with archive.open('rb') as stream:
            row['archive_sha256'] = hashlib.file_digest(stream,'sha256').hexdigest()
        source = out/'source'
        source.mkdir(exist_ok=True)
        total = 0
        with tarfile.open(archive,'r:gz') as bundle:
            for item in bundle:
                if not item.isfile():
                    continue
                parts = Path(item.name).parts[1:]
                dest = source.joinpath(*parts).resolve()
                if not dest.is_relative_to(source.resolve()):
                    raise ValueError('archive path escaped source directory')
                total += item.size
                if total > 2*1024**3:
                    raise ValueError('unpacked source exceeded 2 GiB cap')
                dest.parent.mkdir(parents=True,exist_ok=True)
                with bundle.extractfile(item) as src, dest.open('wb') as dst:
                    shutil.copyfileobj(src,dst)
        manifests = [str(p.relative_to(source)) for p in source.rglob('*') if p.is_file() and p.name in ('pyproject.toml','requirements.txt','environment.yml','setup.py','package.json','Dockerfile','README.md')]
        row['dependency_manifests'] = manifests[:150]
        row['python_entrypoints'] = [str(p.relative_to(source)) for p in source.rglob('*.py') if p.name in ('run.py','main.py','repairagent.py','programmer_humaneval.py','test_designer_humaneval.py','test_executor_humaneval.py','launcher.py')][:100]
        row['source_files'] = sum(1 for p in source.rglob('*') if p.is_file())
        row['status'] = 'SOURCE_ACQUIRED_ADAPTER_PENDING'
        row['remaining_checks'] = ['paper-version correspondence','native dependency installation','site-compatible isolated execution','local Qwen3.8 endpoint capability','held-out probe and production dataset/oracle','paired fault/condition implementation','allocation-budget admission']
    except Exception as exc:
        row.update(status='SOURCE_ACQUISITION_FAILED',error=type(exc).__name__+': '+str(exc))
    row['checked_at_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
    (out/'feasibility.json').write_text(json.dumps(row,indent=2)+'\n')
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    args.out.mkdir(parents=True,exist_ok=True)
    environment = {name:shutil.which(name) for name in ('python3','apptainer','docker','podman','java','perl','git','go','universal-ctags','srun','sbatch')}
    environment['slurm_job_id'] = __import__('os').environ.get('SLURM_JOB_ID')
    (args.out/'environment.json').write_text(json.dumps(environment,indent=2)+'\n')
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(lambda s: inspect(s,args.out),plan['subjects']))
    report = {'subjects':rows,'source_acquired':sum(r['status']=='SOURCE_ACQUIRED_ADAPTER_PENDING' for r in rows),
        'eligible_for_comparison':0,'comparative_episodes_completed':0,'gpu_seconds':0,'environment':environment}
    (args.out/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return 0 if report['source_acquired']==len(rows) else 2


if __name__=='__main__':
    raise SystemExit(main())
