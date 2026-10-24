"""Bounded native legacy ChatDev feasibility run, not a comparative episode.

Retains the upstream role prompts and default chain, with GUI disabled for a
declared text-only task. Only model transport is replaced by the pinned local
Qwen backend. Native completion and an independent function oracle are separate.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tarfile
import time
import traceback

TASK = ("Create a pure Python 3 module named text_tools.py with a function "
    "normalize_words(text: str) -> str. Strip leading and trailing whitespace, "
    "collapse all runs of whitespace to one ASCII space, and lowercase the text. "
    "Use only built-in string methods, no imports in text_tools.py. Include a "
    "minimal main.py demonstration that prints normalize_words('  HELLO   world  '). "
    "Use no GUI, external packages, file access or network access.")
CASES=['','   ','HELLO','  HELLO   world  ','a\tb\nc','  Mixed CASE\r\n More  ',
       'one','A  B C','123  XYZ','already normalized','\t\n','Ä Ö']


def oracle(python, evaluator, code, cwd):
    checks='\n'.join(f'assert normalize_words({s!r}) == {" ".join(s.split()).lower()!r}' for s in CASES)
    return subprocess.run([python,str(evaluator)],input=json.dumps({'code':code+'\n'+checks}),
        text=True,capture_output=True,timeout=10,cwd=cwd).returncode==0


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    root=Path('/campaign')
    out=args.out
    out.mkdir(parents=True,exist_ok=False)
    started=time.monotonic()
    record=dict(stage='NATIVE_FEASIBILITY_ONLY',subject='ChatDev',status='RUNNING',
        comparative_episode=False,job_id=os.environ.get('SLURM_JOB_ID'),
        task=TASK,oracle_cases=CASES,source_revision='31fd994416a251ecdeb1f0a73c329271743bfb56',
        native_workflow_passed=False,oracle_passed=False,model_endpoint_verified=False,
        started_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    calls=[]
    try:
        config=json.loads((root/'experiments/campaign/chatdev-validation-plan.json').read_text())
        for name,expected in config['inputs'].items():
            if hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected:
                raise RuntimeError('validation input changed: '+name)
        source=Path('/runwork/chatdev-native')
        source.mkdir(parents=True,exist_ok=False)
        with tarfile.open(root/'selected-sources/chatdev/source.tar.gz','r:gz') as bundle:
            for item in bundle:
                if not item.isfile():
                    continue
                parts=Path(item.name).parts[1:]
                if not parts or parts[0]=='WareHouse':
                    continue  # Upstream example projects are not fresh run outputs.
                dest=source.joinpath(*parts).resolve()
                if not dest.is_relative_to(source.resolve()):
                    raise ValueError('native archive path escaped working directory')
                dest.parent.mkdir(parents=True,exist_ok=True)
                with bundle.extractfile(item) as stream, dest.open('wb') as target:
                    shutil.copyfileobj(stream,target)
        os.chdir(source)
        (source/'WareHouse').mkdir()
        sys.path.insert(0,str(source))
        sys.path.insert(0,str(root/'experiments/campaign'))
        chain=source/'CompanyConfig/Default/ChatChainConfig.json'
        chain_config=json.loads(chain.read_text())
        chain_config['gui_design']='False'
        chain.write_text(json.dumps(chain_config,indent=2)+'\n')
        from ollama_transport import OllamaModel
        from openai.types.chat import ChatCompletion
        import camel.model_backend as native
        backend=OllamaModel(config['scientific'],out,calls)
        backend.check_identity()
        backend.warmup()
        record['model_endpoint_verified']=True
        class LocalModel:
            def run(self,*args,**kwargs):
                if len(calls)>=48:
                    raise RuntimeError('predeclared 48-call feasibility cap exhausted')
                text,inputs,outputs=backend.prompt(kwargs['messages'])
                return ChatCompletion(id='local-'+str(len(calls)),created=int(time.time()),
                    model='qwen3.8:27b',object='chat.completion',
                    choices=[{'index':0,'finish_reason':'stop','message':{'role':'assistant','content':text}}],
                    usage={'prompt_tokens':inputs,'completion_tokens':outputs,'total_tokens':inputs+outputs})
        native.ModelFactory.create=staticmethod(lambda model_type, model_config_dict: LocalModel())
        sys.argv=['run.py','--config','Default','--org','RESAI','--name','TextToolsValidation',
            '--model','GPT_4O_MINI','--task',TASK]
        runpy.run_path(str(source/'run.py'),run_name='__main__')
        record['native_workflow_passed']=True
        # Native directory timestamps are generated by the upstream workflow.
        candidates=list((source/'WareHouse').glob('*/text_tools.py'))
        if len(candidates)!=1:
            raise RuntimeError(f'expected one native text_tools.py, found {len(candidates)}')
        code=candidates[0].read_text()
        record['generated_source_sha256']=hashlib.sha256(code.encode()).hexdigest()
        record['oracle_passed']=oracle(sys.executable,root/'experiments/campaign/safe_exec.py',code,out)
        record['status']='PASSED' if record['oracle_passed'] else 'ORACLE_FAILED'
    except BaseException as exc:
        record.update(status='FAILED',error=type(exc).__name__+': '+str(exc))
        (out/'failure.log').write_text(traceback.format_exc())
    finally:
        native_dir=Path('/runwork/chatdev-native')
        if native_dir.exists():
            with tarfile.open(out/'native-output.tar.gz','w:gz') as bundle:
                for name in ('WareHouse','CompanyConfig','run.py'):
                    path=native_dir/name
                    if path.exists():
                        bundle.add(path,arcname='native/'+name)
        record.update(calls=len(calls),process_seconds=time.monotonic()-started,
            ended_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
        (out/'validation.json').write_text(json.dumps(record,indent=2)+'\n')
        print(json.dumps(record,indent=2))
    return 0 if record['status']=='PASSED' else 1


if __name__=='__main__':
    raise SystemExit(main())
