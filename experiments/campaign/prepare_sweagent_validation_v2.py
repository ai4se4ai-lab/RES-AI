"""Freeze native GPU validation only after real native CPU control and oracle checks."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

root=Path('/campaign')
fixture=root/'validation-cpu'/('sweagent-'+os.environ['SLURM_JOB_ID'])
result=json.loads((fixture/'cpu-control.json').read_text())
if result['status']!='CPU_NATIVE_CONTROL_FIXTURE_PASSED' or result['fixture_transport_calls']!=3:
    raise RuntimeError('native CPU repair/submission control fixture did not pass')
schema=root/'validation-cpu'/('sweagent-schema-'+os.environ['SLURM_JOB_ID'])/'schema-check.json'
if json.loads(schema.read_text())['status']!='REAL_OLLAMA_SCHEMA_CHECK_PASSED':
    raise RuntimeError('real Ollama request schema check did not pass')
for source,expected in [('def division(a,b):\n    return a/b\n',True),
                        ('def division(a,b):\n    return a*b\n',False),
                        ('def division(a,b):\n    return 0\n',False)]:
    probe=subprocess.run([sys.executable,str(root/'experiments/campaign/sweagent_oracle.py')],
        input=json.dumps({'source':source}),text=True,capture_output=True,timeout=7)
    if (probe.returncode==0)!=expected:
        raise RuntimeError('independent oracle positive/negative self-check failed')
names=['sweagent_adapter.py','sweagent_transport_v2.py','sweagent_oracle.py','sweagent_validation_v2.py',
    'sweagent-native-validation-v2.sh','prepare_sweagent_validation_v2.py','ollama_transport.py',
    'submit_native_validation.py','collect-native-validation-v2.sh']
inputs={'experiments/campaign/'+name:hashlib.sha256((root/'experiments/campaign'/name).read_bytes()).hexdigest() for name in names}
for name in ['check_sweagent_request_v2.py','prepare-sweagent-validation-v2.sh','sweagent_transport.py']:
    inputs['experiments/campaign/'+name]=hashlib.sha256((root/'experiments/campaign'/name).read_bytes()).hexdigest()
for name in ['feasibility/swe-agent/source.tar.gz','selected-sources/sweagent-fixture/source.tar.gz','containers/python311-tools.sif']:
    inputs[name]=hashlib.sha256((root/name).read_bytes()).hexdigest()
science=json.loads((root/'experiments/campaign/agentcoder-validation-plan.json').read_text())['scientific']
plan=dict(subject='SWE-agent',stage='native_feasibility_only',comparative_episode=False,
    scientific=science,inputs=inputs,max_calls=32,wall_seconds=1200,
    gpu_script='experiments/campaign/sweagent-native-validation-v2.sh',
    oracle_scope='Official example syntax repair and six division cases plus ZeroDivisionError; restricted supported AST')
path=root/'experiments/campaign/sweagent-validation-plan-v2.json'
if path.exists():
    raise RuntimeError('refusing to replace frozen native validation plan')
path.write_text(json.dumps(plan,indent=2)+'\n')
proof=dict(subject='SWE-agent',status='CPU_PREFLIGHT_PASSED_NATIVE_GPU_SMOKE_PENDING',
    source_locked=True,dependencies_imported=True,sandbox_validated=True,local_transport_configured=True,
    model_calls=0,fixture_transport_calls=3,native_control_receipt=str(fixture/'cpu-control.json'),
    native_control_sha256=hashlib.sha256((fixture/'cpu-control.json').read_bytes()).hexdigest(),
    schema_control_receipt=str(schema),schema_control_sha256=hashlib.sha256(schema.read_bytes()).hexdigest(),
    validation_plan_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    checked_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
(root/'sweagent-validation-preflight-v2.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof,indent=2))
