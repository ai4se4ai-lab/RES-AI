#!/bin/bash
# CPU-only dependent job: collect evidence, assess, and print a dry dispatch.
set -uo pipefail
run_id="${1:?run id required}"
smoke_job="${2:-}"   # job ID of the smoke allocation for this run, if not already listed below
module load StdEnv/2023 python/3.11
export PYTHONPATH="$PWD/src"
out="hpc/mapcoder/logs/$run_id/assessment"
mkdir -p "$out"
results=$(python3 - "$run_id" <<'PY'
import sys
sys.path.insert(0,'hpc/mapcoder/scripts')
import hpclib as h
print(h.results_dir(sys.argv[1], h.cluster(sys.argv[1])))
PY
)
python3 experiments/mapcoder/assess.py --results "$results" --out "$out" > "$out/assessment-console.txt" 2>&1
assess_rc=$?
if [ -f "$out/evidence.json" ]; then
    python3 -m resai.pipeline --hpc-dir hpc/mapcoder \
      --plan experiments/mapcoder/plan.json --evidence "$out/evidence.json" \
      > "$out/admission-after.txt" 2>&1
fi
sacct -j "24889793,24890017,24890605,24890766${smoke_job:+,$smoke_job}" --parsable2 \
  --format=JobID,State,Submit,Start,End,ElapsedRaw,AllocTRES,ExitCode \
  > "$out/sacct.psv"
printf '%s\n' "$results" > "$out/results-path.txt"
exit "$assess_rc"
