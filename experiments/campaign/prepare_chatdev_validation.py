"""CPU preflight and budgeted submission of one native feasibility allocation."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import shutil
import runpy
import sys
import tarfile
import traceback

from budget import reserve
from chatdev_validation import oracle,TASK

root=Path('/campaign')
os.chdir(root)
proof={}
receipt=root/'chatdev-validation-preflight.json'
try:
    imported=json.loads((root/'environments/chatdev-legacy/container-attempt-2/installation.json').read_text())
    if imported['status']!='DEPENDENCY_IMPORT_PASSED_NATIVE_WORKFLOW_PENDING':
        raise ValueError('repaired native imports have not passed')
    selected_root=root/'selected-sources/chatdev'
    archive=selected_root/'source.tar.gz'
    selected=json.loads((selected_root/'feasibility.json').read_text())
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=selected['archive_sha256']:
        raise ValueError('source archive changed')
    inputs={str(archive.relative_to(root)):selected['archive_sha256']}
    source=Path('/runwork/chatdev-preflight-native')
    source.mkdir(parents=True,exist_ok=False)
    with tarfile.open(archive,'r:gz') as bundle:
        for item in bundle:
            if not item.isfile():
                continue
            relative=Path(*Path(item.name).parts[1:])
            if relative.parts[0]=='WareHouse':
                continue
            path=(source/relative).resolve()
            if not path.is_relative_to(source.resolve()):
                raise ValueError('archive path escaped native preflight directory')
            path.parent.mkdir(parents=True,exist_ok=True)
            with bundle.extractfile(item) as stream, path.open('wb') as target:
                shutil.copyfileobj(stream,target)
    proof['source_locked']=True
    sys.path.insert(0,str(source))
    os.chdir(source)
    import camel.model_backend, chatdev.chat_chain
    (source/'WareHouse').mkdir()
    chain_path=source/'CompanyConfig/Default/ChatChainConfig.json'
    chain=json.loads(chain_path.read_text())
    chain['gui_design']='False'
    chain_path.write_text(json.dumps(chain,indent=2)+'\n')
    class ModelBoundaryReached(BaseException):
        pass
    class BoundaryBackend:
        def run(self,*args,**kwargs):
            if not kwargs.get('messages'):
                raise ValueError('native model call has no messages')
            raise ModelBoundaryReached()
    camel.model_backend.ModelFactory.create=staticmethod(lambda model_type,model_config_dict: BoundaryBackend())
    sys.argv=['run.py','--config','Default','--org','RESAI','--name','CPUStartupCheck',
              '--model','GPT_4O_MINI','--task',TASK]
    try:
        runpy.run_path(str(source/'run.py'),run_name='__main__')
    except ModelBoundaryReached:
        proof['native_startup_to_first_model_call']=True
    else:
        raise ValueError('native startup did not reach the declared model boundary')
    os.chdir(root)
    proof['dependencies_imported']=True
    evaluator=root/'experiments/campaign/safe_exec.py'
    good="def normalize_words(text: str) -> str:\n    return ' '.join(text.split()).lower()\n"
    bad="def normalize_words(text: str) -> str:\n    return text\n"
    if not oracle(sys.executable,evaluator,good,root) or oracle(sys.executable,evaluator,bad,root):
        raise ValueError('independent restricted oracle self-check failed')
    proof['sandbox_validated']=True
    from ollama_transport import OllamaModel
    science=dict(model='qwen3.8:27b',model_revision='b45285c1cc1fafaf0272e840a7b799cb11e1b4597c2dc47a2dc58a61942f408c',
        model_api_digest='aaee06c39dcf2437cde036998d960e1fc1494b8191be7cc9657d01e509097813',
        model_path='/models/manifests/registry.ollama.ai/library/qwen3.8/27b',ollama_version='0.40.10',
        thinking=False,max_input_tokens=12288,max_new_tokens=4096)
    OllamaModel(science,root,[])
    proof['local_transport_configured']=True
    for name in ('chatdev_validation.py','ollama_transport.py','safe_exec.py','chatdev-native-validation.sh',
                 'prepare_chatdev_validation.py','submit_chatdev_validation.py','prepare-chatdev-validation.sh',
                 'collect-native-validation.sh'):
        path=root/'experiments/campaign'/name
        inputs[str(path.relative_to(root))]=hashlib.sha256(path.read_bytes()).hexdigest()
    validation_plan=dict(stage='native_feasibility_only',scientific=science,inputs=inputs,
        source_revision=selected['source_revision'],gui_design=False,max_calls=48,
        wall_seconds=1200,comparative_episode=False)
    plan_path=root/'experiments/campaign/chatdev-validation-plan.json'
    if plan_path.exists():
        raise ValueError('refusing to overwrite an existing validation plan')
    plan_path.write_text(json.dumps(validation_plan,indent=2)+'\n')
    # GPU submission is performed outside the clean container by the CPU launcher.
    proof.update(status='CPU_PREFLIGHT_PASSED_NATIVE_GPU_SMOKE_PENDING',
        validation_plan_sha256=hashlib.sha256(plan_path.read_bytes()).hexdigest(),
        checked_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
except Exception as exc:
    proof.update(status='PREFLIGHT_FAILED',error=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc())
finally:
    receipt.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof,indent=2))
sys.exit(0 if proof['status'].startswith('CPU_PREFLIGHT_PASSED') else 1)
