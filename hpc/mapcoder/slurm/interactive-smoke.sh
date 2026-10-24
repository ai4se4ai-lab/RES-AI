#!/bin/bash
# Run two logical smoke cells sequentially inside one genuine salloc/srun job.
# Frozen configuration is prepared before requesting the allocation.
set -uo pipefail
export HPC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export RUN_ID="${1:?run id required}" STAGE=mapcoder
source "$HPC_DIR/slurm/common.sh"
setup_traps
print_job_header
require_gpu || exit 5
setup_python || exit 4
setup_distributed
start_gpu_monitor
python3 - "$LOG_ROOT/interactive-allocation.json" <<'PY'
import json,os,sys
from pathlib import Path
keys=('SLURM_JOB_ID','SLURM_JOB_PARTITION','SLURM_JOB_NODELIST','SLURM_CPUS_PER_TASK','SLURM_GPUS_ON_NODE')
Path(sys.argv[1]).write_text(json.dumps({'backend':'interactive salloc/srun','environment':{k:os.environ.get(k) for k in keys}},indent=2)+'\n')
PY
failed=0
for CELL_ID in 0 1; do
    export CELL_ID
    run_stage || failed=1
done
exit "$failed"
