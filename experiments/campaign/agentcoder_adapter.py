"""Native AgentCoder loader; preserve prompts, candidate counts and repair loops.

The benchmark-only CodeGeeX import patch removes inactive model imports. The
schema shim supplies the pinned evaluator's test_code/generation fields from
AgentCoder's full_code field; evaluator execution and scoring remain native.
"""
import copy
import hashlib
import json
from pathlib import Path
import os
import shutil
import sys
import tarfile


def extract(archive,dest):
    dest.mkdir(parents=True,exist_ok=False)
    with tarfile.open(archive,'r:gz') as bundle:
        for member in bundle:
            if not member.isfile():
                continue
            path=dest.joinpath(*Path(member.name).parts[1:]).resolve()
            if not path.is_relative_to(dest.resolve()):
                raise ValueError('archive escaped native workspace')
            path.parent.mkdir(parents=True,exist_ok=True)
            with bundle.extractfile(member) as source,path.open('wb') as target:
                shutil.copyfileobj(source,target)


def load(root,work):
    archive=root/'feasibility/agentcoder/source.tar.gz'
    subroot=root/'selected-sources/agentcoder-submodules/codegeex'
    for file,receipt in ((archive,archive.parent/'feasibility.json'),(subroot/'source.tar.gz',subroot/'feasibility.json')):
        expected=json.loads(receipt.read_text())['archive_sha256']
        if hashlib.sha256(file.read_bytes()).hexdigest()!=expected:
            raise ValueError('source archive changed: '+str(file))
    extract(archive,work)
    extract(subroot/'source.tar.gz',work/'CodeGeeX')
    initializer=work/'CodeGeeX/codegeex/__init__.py'
    patch=dict(path='CodeGeeX/codegeex/__init__.py',original_sha256=hashlib.sha256(initializer.read_bytes()).hexdigest(),
        reason='Benchmark-only import path; inactive tokenizer and model-generation imports require unused Torch dependencies')
    initializer.write_text('"""Benchmark-only import adaptation; upstream evaluator files unchanged."""\n')
    patch['adapted_sha256']=hashlib.sha256(initializer.read_bytes()).hexdigest()
    task=json.loads((root/'experiments/campaign/agentcoder-task.jsonl').read_text())
    for name in ('humaneval_prompt_update.txt','test_designer_humaneval_prompt_update.txt'):
        if task['entry_point'] in (work/'prompts'/name).read_text():
            raise ValueError('selected held-out task occurs in native few-shot examples')
    os.chdir(work)
    sys.path.insert(0,str(work/'src'))
    sys.path.insert(0,str(work/'CodeGeeX'))
    import datasets
    original_loader=datasets.load_dataset
    def selected_dataset(name,*args,**kwargs):
        if name!='openai_humaneval' or kwargs.get('split')!='test':
            raise ValueError('unexpected native dataset request')
        return [copy.deepcopy(task)]
    datasets.load_dataset=selected_dataset
    try:
        import programmer_humaneval as programmer
        import test_designer_humaneval as designer
        import test_executor_humaneval as executor
    finally:
        datasets.load_dataset=original_loader
    native_check=executor.check_correctness
    def schema_check(task_id,sample,language,timeout,tmp_dir):
        adapted=dict(sample,test_code=sample['full_code'],generation=sample['full_code'])
        return native_check(task_id,adapted,language,timeout,tmp_dir)
    executor.check_correctness=schema_check
    return task,programmer,designer,executor,patch


def run_native(task,programmer,designer,executor,persist=None):
    data=[copy.deepcopy(task)]
    data=programmer.call_fetch_completion_helper(data,'qwen3.8:27b','python')
    data=designer.call_fetch_test_completion_helper(data,'qwen3.8:27b','python')
    if persist:
        persist(data,'initial')
    epochs=[]
    for epoch in range(5):
        data=executor.test_agent_concurrency(data,'python')
        executor.test_report(data,'python')
        epochs.append(copy.deepcopy(data))
        if persist:
            persist(data,'epoch-'+str(epoch))
        data=programmer.call_fetch_completion_helper(data,'qwen3.8:27b','python')
        data=designer.call_fetch_test_completion_helper(data,'qwen3.8:27b','python')
    data=executor.test_agent_concurrency(data,'python')
    executor.test_report(data,'python')
    if persist:
        persist(data,'final')
    return data,epochs
