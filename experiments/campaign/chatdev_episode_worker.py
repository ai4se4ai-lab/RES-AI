"""A fresh native ChatDev execution shared by every comparative condition.

The independent oracle is observational. The native process exit status remains
separate from schema validity and oracle success, so the upstream comparator
uses its own actual process/output checks rather than the full RES-AI decision.
"""
import argparse
import ast
import difflib
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys
import time
import traceback

from ollama_transport import OllamaModel

parser=argparse.ArgumentParser()
parser.add_argument('--case',type=Path,required=True)
parser.add_argument('--phase',choices=('probe','production'),required=True)
parser.add_argument('--index',type=int,required=True)
parser.add_argument('--out',type=Path,required=True)
parser.add_argument('--cpu-startup',action='store_true')
args=parser.parse_args()
spec=json.loads(args.case.read_text())
out=args.out
out.mkdir(parents=True,exist_ok=False)
work=Path('/runwork')/(args.phase+'-'+str(args.index))
start=time.monotonic()
passed=[]
calls=[]
record=dict(status='failed',passed_probes=passed,output_valid=False,scientific_task_solved=None,
    native_workflow_passed=False,fault=None,phase=args.phase,index=args.index,cpu_startup_only=args.cpu_startup)
def checkpoint():
    record.update(process_seconds=time.monotonic()-start,calls=len(calls))
    (out/'evidence.json').write_text(json.dumps(record,indent=2)+'\n')
class SetupFailure(BaseException):
    pass
class CallLimit(BaseException):
    pass
class CPUModelBoundary(KeyboardInterrupt):
    pass
try:
    # Exclude upstream example projects to prevent stale output reuse.
    import tarfile,shutil
    work.mkdir()
    with tarfile.open('/campaign/selected-sources/chatdev/source.tar.gz','r:gz') as bundle:
        for member in bundle:
            parts=Path(member.name).parts[1:]
            if not member.isfile() or not parts or parts[0]=='WareHouse':
                continue
            dest=work.joinpath(*parts).resolve()
            if not dest.is_relative_to(work.resolve()):
                raise ValueError('source archive escaped private workspace')
            dest.parent.mkdir(parents=True,exist_ok=True)
            with bundle.extractfile(member) as stream,dest.open('wb') as target:
                shutil.copyfileobj(stream,target)
    (work/'WareHouse').mkdir()
    chain_path=work/'CompanyConfig/Default/ChatChainConfig.json'
    chain=json.loads(chain_path.read_text())
    chain['gui_design']='False'
    chain_path.write_text(json.dumps(chain,indent=2)+'\n')
    if spec['episode_class']=='environment_fault':
        (work/'CompanyConfig/Default/RoleConfig.json').unlink()
        (out/'fault.json').write_text(json.dumps({'operator':'remove native RoleConfig.json after source extraction; replay old clean receipts only for evidence-based policies'})+'\n')
    os.chdir(work)
    sys.path.insert(0,str(work))
    import camel.model_backend as native
    from openai.types.chat import ChatCompletion
    passed.append('imports')
    class SeededBackend(OllamaModel):
        def request(self,path,body=None):
            if path=='/api/chat':
                body['options']['seed']=spec['paired_seed']
            return super().request(path,body)
    backend=SeededBackend(spec['scientific'],out,calls)
    loaded=False
    class LocalModel:
        def run(self,*positional,**kwargs):
            global loaded
            if args.cpu_startup:
                record['cpu_model_boundary_reached']=True
                raise CPUModelBoundary('CPU setup test; no model request made')
            if not loaded:
                try:
                    backend.check_identity()
                    backend.warmup()
                except Exception as exc:
                    raise SetupFailure(str(exc)) from exc
                loaded=True
                passed.append('model_init')
                checkpoint()
            if len(calls)>=48:
                raise CallLimit('predeclared 48-call native workflow limit')
            text,inputs,outputs=backend.prompt(kwargs['messages'])
            return ChatCompletion(id='local-'+str(len(calls)),created=int(time.time()),
                model='qwen3.8:27b',object='chat.completion',
                choices=[{'index':0,'finish_reason':'stop','message':{'role':'assistant','content':text}}],
                usage={'prompt_tokens':inputs,'completion_tokens':outputs,'total_tokens':inputs+outputs})
    native.ModelFactory.create=staticmethod(lambda model_type,model_config_dict:LocalModel())
    task=spec['tasks'][args.phase]
    sys.argv=['run.py','--config','Default','--org','RESAI','--name','Episode',
        '--model','GPT_4O_MINI','--task',task['prompt']]
    checkpoint()
    runpy.run_path(str(work/'run.py'),run_name='__main__')
    record.update(native_workflow_passed=True,status='ok')
    passed.append('native_workflow')
    projects=[p for p in (work/'WareHouse').iterdir() if p.is_dir()]
    candidates=[p/task['module'] for p in projects if (p/task['module']).is_file()]
    if len(candidates)==1:
        code=candidates[0].read_text()
        (out/'original-source.py').write_text(code)
        if spec['episode_class']=='output_contract_fault':
            tree=ast.parse(code)
            selected=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name==task['entry_point']]
            if len(selected)!=1:
                raise ValueError('cannot apply frozen output corruption to missing/ambiguous target function')
            selected[0].body=[ast.Return(value=ast.Constant(value=None))]
            ast.fix_missing_locations(tree)
            corrupted=ast.unparse(tree)+'\n'
            (out/'fault.diff').write_text(''.join(difflib.unified_diff(code.splitlines(True),corrupted.splitlines(True),fromfile='native-output',tofile='corrupted-output')))
            candidates[0].write_text(corrupted)
            code=corrupted
        (out/task['module']).write_text(code)
        tree=ast.parse(code)
        record['output_valid']=any(isinstance(node,ast.FunctionDef) and node.name==task['entry_point'] for node in tree.body)
        if record['output_valid']:
            passed.append('output_schema')
        import subprocess
        checked=subprocess.run([sys.executable,'/campaign/experiments/campaign/safe_exec.py'],
            input=json.dumps({'code':code+'\n'+task['oracle']}),text=True,capture_output=True,timeout=10)
        (out/'oracle.stderr').write_text(checked.stderr)
        record['scientific_task_solved']=checked.returncode==0
        if checked.returncode==0:
            passed.append('heldout_oracle')
    checkpoint()
except BaseException as exc:
    record.update(status='failed',fault=type(exc).__name__+': '+str(exc))
    (out/'failure.log').write_text(traceback.format_exc())
finally:
    import tarfile
    if (work/'WareHouse').exists():
        with tarfile.open(out/'native-output.tar.gz','w:gz') as archive:
            archive.add(work/'WareHouse',arcname='WareHouse')
    checkpoint()
raise SystemExit(0 if record['native_workflow_passed'] or (args.cpu_startup and record.get('cpu_model_boundary_reached')) else 1)
