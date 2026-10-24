"""Allocation reservation guard for the initial author-approved campaign budget."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import uuid


def reserve(plan, ledger, subject, wall_seconds, proof, purpose='comparison'):
    if subject not in {s['name'] for s in plan['subjects']}:
        raise ValueError('unknown campaign subject')
    requirements = {
        'comparison': ('native_smoke_passed','oracle_passed','sandbox_validated','model_endpoint_verified'),
        'native_validation': ('source_locked','dependencies_imported','sandbox_validated','local_transport_configured'),
    }
    if purpose not in requirements:
        raise ValueError('unknown reservation purpose')
    required = requirements[purpose]
    if not all(proof.get(k) is True for k in required):
        raise ValueError('native adapter eligibility evidence incomplete; static source availability is insufficient')
    if not isinstance(wall_seconds,int) or wall_seconds <= 0:
        raise ValueError('walltime must be positive integer seconds')
    # Reserve one accelerator plus termination grace; the native submitter must request one H100.
    commitment = wall_seconds+60
    entries = ledger.get('reservations',[])
    charged = lambda r: r['allocated_seconds'] if r.get('settled') else r['reserved_seconds']
    if sum(charged(r) for r in entries)+commitment > plan['initial_h100_budget_seconds']:
        raise ValueError('initial 24 H100 GPU-hour allocation budget would be exceeded')
    if sum(charged(r) for r in entries if r['subject']==subject)+commitment > plan['maximum_reserved_h100_seconds_per_artifact']:
        raise ValueError('per-artifact reservation cap would be exceeded')
    record = dict(ticket=uuid.uuid4().hex,subject=subject,purpose=purpose,wall_seconds=wall_seconds,
        reserved_seconds=commitment,settled=False,allocated_seconds=None,
        reserved_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    ledger.setdefault('reservations',[]).append(record)
    return record


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--plan',type=Path,required=True)
    parser.add_argument('--ledger',type=Path,required=True)
    parser.add_argument('--proof',type=Path,required=True)
    parser.add_argument('--subject',required=True)
    parser.add_argument('--wall-seconds',type=int,required=True)
    parser.add_argument('--purpose',choices=('comparison','native_validation'),default='comparison')
    args=parser.parse_args()
    args.ledger.parent.mkdir(parents=True,exist_ok=True)
    lock=args.ledger.with_suffix('.lock')
    descriptor=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    try:
        plan=json.loads(args.plan.read_text())
        proof=json.loads(args.proof.read_text())
        ledger=json.loads(args.ledger.read_text()) if args.ledger.exists() else {'reservations':[]}
        record=reserve(plan,ledger,args.subject,args.wall_seconds,proof,args.purpose)
        temporary=args.ledger.with_suffix('.tmp')
        temporary.write_text(json.dumps(ledger,indent=2)+'\n')
        os.replace(temporary,args.ledger)
        print(json.dumps(record))
    finally:
        os.close(descriptor)
        lock.unlink()


if __name__=='__main__':
    main()
