"""Collect campaign preparation observations without promoting them to experiment results."""
import csv
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import time
from reconcile_budget import reconcile
from budget import allocation_for

ROOT=Path(__file__).resolve().parents[2]


def main():
    plan_path=ROOT/'experiments/campaign/plan.json'
    plan=json.loads(plan_path.read_text())
    registry=ROOT/'preparation-jobs.json'
    jobs=json.loads(registry.read_text())['job_ids'] if registry.exists() else ['24904387','24904527','24904649','24904650','24904849']
    ledger_path=ROOT/'gpu-budget-ledger.json'
    ledger=json.loads(ledger_path.read_text()) if ledger_path.exists() else {'reservations':[]}
    jobs+= [r['job_id'] for r in ledger['reservations'] if r.get('job_id')]
    jobs+= [r['collector_job_id'] for r in ledger['reservations'] if r.get('collector_job_id')]
    jobs=list(dict.fromkeys(jobs))
    query=subprocess.run(['sacct','-j',','.join(jobs),'--parsable2',
        '--format=JobID,JobIDRaw,JobName,State,Submit,Start,End,ElapsedRaw,AllocTRES,ExitCode'],
        text=True,capture_output=True,timeout=20)
    accounting=list(csv.DictReader(io.StringIO(query.stdout),delimiter='|')) if query.returncode==0 else []
    job_states={r['JobIDRaw']:r['State'] for r in accounting if '.' not in r['JobID']}
    parent_rows={r['JobID']:r for r in accounting if '.' not in r['JobID']}
    allocated=reserved=0
    if ledger_path.exists():
        lock=ledger_path.with_suffix('.lock')
        for attempt in range(51):
            try:
                descriptor=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
                break
            except FileExistsError:
                if attempt==50:
                    raise
                time.sleep(.1)
        try:
            # A concurrent submission may have added a reservation after sacct.
            # Merge only known accounting into the latest ledger under its lock.
            current=json.loads(ledger_path.read_text())
            ledger,allocated,reserved=reconcile(current,parent_rows,dt.datetime.now(dt.timezone.utc).isoformat())
            temporary=ledger_path.with_suffix('.tmp')
            temporary.write_text(json.dumps(ledger,indent=2)+'\n')
            os.replace(temporary,ledger_path)
        finally:
            os.close(descriptor)
            lock.unlink()
    native_records=[json.loads(p.read_text()) for p in sorted((ROOT/'validation').glob('**/validation.json'))]
    amended_comparison=ROOT/'comparison/chatdev-v2/status.json'
    comparison_path=amended_comparison if amended_comparison.exists() else ROOT/'comparison/chatdev/status.json'
    comparison=json.loads(comparison_path.read_text()) if comparison_path.exists() else None
    records=[]
    for subject in plan['subjects']:
        slug=re.sub('[^a-z0-9]+','-',subject['name'].lower())
        record=dict(name=subject['name'],campaign_status='SOURCE_ACQUISITION_PENDING',
                    comparative_episodes_completed=0,eligible_for_comparison=False)
        path=ROOT/'feasibility'/slug/'feasibility.json'
        if path.exists():
            record.update(json.loads(path.read_text()))
            record['campaign_status']=record.pop('status')
        imported=ROOT/'environments'/slug/'attempt-2/imports.json'
        if imported.exists():
            record['dependency_import_check']=json.loads(imported.read_text())
        environment_name='chatdev-legacy' if slug=='chatdev' else slug
        installs=ROOT/'environments'/environment_name
        record['environment_attempts']=[json.loads(p.read_text()) for p in sorted(installs.glob('*/installation.json'))]
        for attempt in record['environment_attempts']:
            state=job_states.get(attempt.get('job_id'))
            if attempt['status']=='INSTALLING' and state and state not in ('RUNNING','PENDING','CONFIGURING','COMPLETING'):
                attempt.update(status='INSTALL_JOB_ENDED_WITHOUT_SUCCESS_RECEIPT',slurm_state=state)
        if record['environment_attempts']:
            record['latest_dependency_status']=record['environment_attempts'][-1]['status']
        elif 'dependency_import_check' in record:
            record['latest_dependency_status']=record['dependency_import_check']['status']
        else:
            record['latest_dependency_status']='NOT_VALIDATED'
        subject_native=[r for r in native_records if r.get('subject')==subject['name']]
        record['latest_native_status']=subject_native[-1]['status'] if subject_native else 'NOT_RUN'
        record['native_validation_passed']=any(r.get('native_workflow_passed') and r.get('oracle_passed') for r in subject_native)
        pending_native=[r for r in ledger['reservations'] if r.get('subject')==subject['name'] and r.get('purpose')=='native_validation' and r.get('job_id') and not r.get('settled')]
        if pending_native:
            record['latest_native_status']='GPU_'+pending_native[-1].get('last_observed_state','STATE_UNKNOWN')
        if subject['name']=='ChatDev' and comparison:
            record['comparative_episodes_completed']=comparison['comparative_episodes_completed']
            record['comparative_status']=comparison['status']
            record['eligible_for_comparison']=record['native_validation_passed']
            record['comparative_admission_scope']='Frozen ChatDev subset only; other artifacts require independent validation'
        if subject['name']=='ChatDev':
            legacy=ROOT/'selected-sources/chatdev/feasibility.json'
            if legacy.exists():
                record['paper_legacy_source']=json.loads(legacy.read_text())
        records.append(record)
    validations=[r for r in ledger['reservations'] if r.get('purpose')=='native_validation' and r.get('job_id') and not r.get('settled')]
    native_action=('Inspect native feasibility '+', '.join('job '+r['job_id']+' ('+r.get('last_observed_state','state unknown')+')' for r in validations)+'. ') if validations else ''
    state='FEASIBILITY_AND_COMPARISON' if comparison else 'FEASIBILITY'
    comparison_action=('ChatDev comparative subset: '+comparison['status']+'. ') if comparison else ''
    data=dict(campaign_id=plan['campaign_id'],status=state,
        protocol_sha256=hashlib.sha256(plan_path.read_bytes()).hexdigest(),
        initial_h100_budget_seconds=plan['initial_h100_budget_seconds'],
        artifact_allocation_ceilings_seconds={s['name']:allocation_for(plan,s['name'])[0] for s in plan['subjects']},
        budget_allocation_amendment=allocation_for(plan,'ChatDev')[1],
        h100_allocated_seconds=allocated,h100_reserved_seconds=reserved,
        potential_episodes=plan['potential_episodes'],comparative_episodes_completed=comparison['comparative_episodes_completed'] if comparison else 0,
        source_audit_job_id='24904387',environment_array_job_id='24904649',
        chatdev_legacy_source_job_id='24904650',paper_qwen38_integration='COMPLETE',
        source_snapshots_acquired=sum(r['campaign_status']=='SOURCE_ACQUIRED_ADAPTER_PENDING' for r in records),
        dependency_import_checks_passed=sum('IMPORT_PASSED' in r['latest_dependency_status'] for r in records),
        remote_root=str(ROOT),subjects=records,
        cpu_job_accounting=[r for r in accounting if r['JobID'].split('.')[0] not in {e.get('job_id') for e in ledger['reservations']}],
        comparative_execution_implemented=comparison is not None,
        comparative_subsets={'ChatDev':comparison} if comparison else {},
        native_validation_records=native_records,
        gpu_budget_ledger=ledger,
        accounting_query_error=query.stderr if query.returncode else None,
        slurm_accounting_time_zone=str(dt.datetime.now().astimezone().tzinfo),
        next_action=native_action+comparison_action+'Finish remaining artifact native environment/workflow and oracle checks; collect comparative data under the frozen per-artifact protocols and initial GPU cap.',
        updated_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    out=ROOT/'campaign-status.json'
    out.write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps({'source_snapshots_acquired':data['source_snapshots_acquired'],
                      'dependency_import_checks_passed':data['dependency_import_checks_passed'],
                      'potential_episodes':data['potential_episodes'],'h100_allocated_seconds':allocated,'h100_reserved_seconds':reserved}))


if __name__=='__main__':
    main()
