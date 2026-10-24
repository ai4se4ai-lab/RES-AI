"""Merge a scheduler snapshot into the latest ledger without dropping new reservations."""
import copy

TERMINAL={'COMPLETED','FAILED','CANCELLED','TIMEOUT','NODE_FAIL','OUT_OF_MEMORY',
          'PREEMPTED','BOOT_FAIL','DEADLINE','REVOKED'}


def reconcile(latest,parent_rows,stamp):
    ledger=copy.deepcopy(latest)
    allocated=reserved=0
    for entry in ledger['reservations']:
        row=parent_rows.get(entry.get('job_id'))
        if row and not entry.get('settled'):
            state=row['State'].split()[0]
            entry['last_observed_state']=row['State']
            if state in TERMINAL:
                entry.update(settled=True,allocated_seconds=int(row['ElapsedRaw']),
                    accounting=copy.deepcopy(row),settled_at_utc=stamp)
        if entry.get('settled'):
            allocated+=entry['allocated_seconds']
        elif row and row['State'].split()[0] not in TERMINAL|{'PENDING'}:
            elapsed=int(row['ElapsedRaw'])
            allocated+=elapsed
            reserved+=max(0,entry['reserved_seconds']-elapsed)
        else:
            # A reservation created after the query remains fully reserved.
            reserved+=entry['reserved_seconds']
    return ledger,allocated,reserved
