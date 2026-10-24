# RES-AI Nibi operating and evidence guide

The one-artifact/two-model pilot and Qwen3.8 manuscript integration are complete.
On 2026-10-24 the author authorized the twelve-artifact campaign with an initial
24 H100 GPU-hour cap. CPU feasibility checks are underway; comparative episodes
have not run. Current observations and the append-only journal are maintained in
`docs/EMSE/support/AI_AGENT_PROJECT_EXECUTION_PLAN.md`.

## Execution layers

`hpc/` reuses the upstream templates at commit
`f9dc7d66ad8df3c202f6b72b02630e14fd148756`. `hpc/UPSTREAM.json` identifies
local configuration changes. `hpc/mapcoder/` is an isolated instance of the same
templates. Its `hpclib.py` repository root and `common.sh` root calculation are
adjusted for the nested directory. The inherited submission, runner, audit and
collection logic is otherwise retained.

Nibi associations discovered for this user are `def-mbabaei_gpu` and
`def-mbabaei_cpu`. No priority-changing privilege is assumed. Small accurate
walltimes affect backfill feasibility, not the scheduler's priority policy.

## Experiment inventory

| Item | Execution | Raw output | Interpretation |
|---|---|---|---|
| Controller conformance | `python experiments/run_local.py` | `experiments/results/local/decisions.csv`, summary and source manifest | Synthetic input decisions, not natural fault frequency |
| CUDA integration | `hpc/config/experiments.json` | `experiments/results/nibi/results/gpu/*.json` | Two repeats of four synthetic-tensor modes |
| Nibi allocation accounting | `sacct`, captured after completion | `experiments/results/nibi/logs/sacct.psv` | Allocation elapsed time; exclude `.batch`/`.extern` duplicates |
| One-artifact self-application | `hpc/mapcoder/config/experiments.json` | `mapcoder/rep*/attempt-*/{evidence.json,task-results.jsonl,calls.json,strategy.log}` under the run results | MapCoder local-model deployment on HumanEval/0 |
| Readiness before/after | `resai.pipeline`, `experiments/mapcoder/assess.py` | admission decision JSON and complete evidence bundle | Bounded gate decision for the declared plan |
| Twelve-artifact campaign | authorized; CPU feasibility underway | frozen `experiments/campaign/plan.json`; collected `experiments/results/campaign/STATUS.json` | No comparative performance results yet; initial 24 H100 GPU-hour cap |

## Completed CUDA integration

Run `resai-smoke-20261023-2315`: array `24888989`, dependent analysis `24888990`.
Two MIG 1g.10gb instances were requested for at most fifteen minutes each.
Both array cells and analysis completed, with thirteen successful pipeline steps.
Injected failures were recorded as evidence rather than aborting the collection
stage. The clean evidence pair passed; all three faulty modes blocked readiness.

Slurm reports 39 and 42 allocated instance-seconds for the GPU cells (81 total),
with 159 seconds of queue delay per cell. Process timings sum to approximately
3.723 seconds and exclude imports/environment installation. These are costs of
this integration check, not avoided production costs or full-GPU hours. The CPU
analysis ran for 44 allocated seconds on two cores.

Reanalysis on the workstation:

```bash
python experiments/analyze_gpu.py --results experiments/results/nibi/results \
  --out experiments/results/nibi/reanalysis
python experiments/make_paper_artifacts.py
```

The original collected analysis is retained separately from reanalysis using the
reviewed final policy. The same per-mode outcomes result. The original Nibi source
tree remains at `/project/def-mbabaei/mbabaei/resai-20261023-2308`; its source is
not overwritten by subsequent pilot revisions.

## MapCoder self-application

The source is pinned to `c87e6d914d196e12fa2b144882122459a4b98007`.
The MIT license and upstream source are retained in `experiments/vendor/mapcoder`.
`experiments/mapcoder/humaneval-only.patch` documents removal of unused competitive
dataset imports and the corresponding inactive branch. This avoids an eager
11 MB xCodeEval test-database dependency irrelevant to HumanEval.

The scientific contract fixes HumanEval/0, k=3, t=5, one outer attempt, greedy
decoding, maximum input 12,288 tokens and maximum generated output 4,096 tokens.
The cached local Qwen2.5-Coder-7B-Instruct revision is
`c03e6d358207e414f1eca0bb1891e29f1db0e242`. This backend adaptation is not a
reproduction of MapCoder's published cloud-model accuracy.

The current smoke backend requests one full H100, four CPU cores,
48 GB host memory and fifteen minutes through documented interactive debugging
allocation. Two fresh model processes execute sequentially under this allocation,
using the inherited step runner and ledgers. Its ceiling is fifteen H100
minutes. Initialization and inference remain on the allocated node. Cached model
weights and the Alliance wheelhouse avoid model/package downloads on login nodes.

Before inference the adapter checks all declared file hashes, graph correspondence
and site-variable control characters. It writes into a fresh attempt directory;
cached outputs cannot satisfy a new first execution. It records prompt/response
traces and checks output schema separately from task correctness. Resume reloads
persisted results into new strategy objects and must perform no additional model
calls. This tests persisted-result reuse, not recovery of a live distributed job.

Array `24889793` was canceled while pending after detecting CRLF in Bash values.
Corrected array `24890017` was also canceled while pending when the documented
short interactive debug route was selected. These submissions consumed no GPU
allocation. MIG interactive job `24890605` was subsequently canceled while pending:
resource profiling found most MIG nodes draining and healthy 20/40 GB slices fully
allocated. Current full-H100 interactive job `24890766` has a separate plan identity
and requests `gpubase_interac`; the site's job-submit policy can add a backfill
fallback. Dependent CPU collector `24890918` assesses evidence and prints a dry
dispatch when the allocation ends. Retain canceled submissions in accounting rather than
treating them as executed failures or omitting workflow history. The plan's
partition is explicit: readiness does not transfer to a different partition or a
larger batch-production plan.

Collection on 2026-10-24 confirmed that allocation `24890766` and collector
`24890918` completed. Both fresh processes made eight model calls and solved
HumanEval/0. The collection-time assessment and wrapper dry run passed. The
allocation consumed 383 H100 seconds; the two timed processes consumed
335.276 seconds in total. Archived evidence is historical and is not a fresh
authorization for a later dispatch. Raw results, traces, assessment, accounting,
and declared source are collected in `experiments/results/mapcoder/`.
Earlier retired-run logs are retained in `experiments/results/nibi-history/`.

### Additional Qwen3.8 backend

The additional `qwen3.8:27b` run uses Ollama 0.40.10 and Q4_K_M weights, with
thinking disabled and temperature zero. It retains HumanEval/0, k=3, t=5,
the input/output envelopes, and two independent repeats. This is a distinct
scientific/model identity from the Qwen2.5-Coder pilot. Each repeat starts its
own Ollama server. Memory is sampled with nvidia-smi every 0.5 seconds because
PyTorch allocator statistics cannot measure a separate inference process.

Prepare this variant in a **separate source copy**, after downloading the model:

```bash
python experiments/mapcoder/configure_ollama.py --isolated-copy \
  --manifest /scratch/mbabaei/ollama_models/manifests/registry.ollama.ai/library/qwen3.8/27b \
  --listing /path/to/archived-api-tags.json
python experiments/mapcoder/prepare_smoke.py --run-id NEW_RUN_ID \
  --launch-script ollama-smoke.sh
# Execute the printed bounded salloc command, then collect:
python experiments/mapcoder/archive_run.py --run-id NEW_RUN_ID --jobs JOB_IDS
```

The adapter checks the manifest digest, served model identity, Ollama version,
GPU loading, response completion, and token limits. It retains full API responses,
including unsuccessful responses. The archive includes declared source files,
raw results, logs, assessments, and Slurm records. New-run status and downloaded
data are stored separately in `experiments/results/mapcoder-qwen38/`.
The raw manifest checksum and the digest advertised by `/api/tags` are bound
separately; they differ for this Ollama manifest format. The initial identity-check
failure is preserved under run `resai-mapcoder-qwen38-20261024`; the corrected
runner uses fresh run `resai-mapcoder-qwen38-v2-20261024`.

The corrected allocation `24902711` and collector `24902997` completed on
2026-10-24. Both repeats solved HumanEval/0, made eight model calls, and passed
all five probes. The collection-time readiness assessment and wrapper dry run
passed. Successful allocation time was 548 H100 seconds, with 454.072 timed
process seconds. Initial failed allocation `24900967` consumed 86 H100 seconds
before inference; include it for a total of 634 H100 seconds for the Qwen3.8
workflow. Download, preparation, inspection, and collection CPU jobs are accounted
separately in `provenance/sacct-final.psv`. The final downloaded archive includes
their logs and checksum records. Neither model's two repeated executions of one
task establish aggregate benchmark accuracy or comparative resource savings.

Operating commands from the MapCoder project root on Nibi:

```bash
bash hpc/mapcoder/scripts/selftest.sh
PYTHONPATH=src python -m resai.pipeline --hpc-dir hpc/mapcoder \
  --plan experiments/mapcoder/plan.json \
  --evidence experiments/mapcoder/evidence-empty.json
# Expected: blocked, no evidence. Smoke collection itself is still permitted.
# Freeze configuration and create the manifest; the helper prints the command.
python experiments/mapcoder/prepare_smoke.py --run-id RUN_ID
# interactive-smoke.sh uses the frozen files and inherited runner.
salloc --account=def-mbabaei_gpu --partition=gpubase_interac \
  --gpus=h100:1 --cpus-per-task=4 --mem=48G \
  --time=00:15:00 srun --ntasks=1 bash hpc/mapcoder/slurm/interactive-smoke.sh RUN_ID
python experiments/mapcoder/assess.py --results /actual/run/results --out /assessment
PYTHONPATH=src python -m resai.pipeline --hpc-dir hpc/mapcoder \
  --plan experiments/mapcoder/plan.json --evidence /assessment/evidence.json
# Last command is an admission check and dry run, not production dispatch.
```

Do not resubmit finished work into a reused run ID when collecting fresh evidence.
Never poll Slurm more often than once per minute. Use the actual frozen run's
`WORK` value rather than guessing the scratch path. Do not copy a configuration
with Windows CRLF line endings into a Bash environment file.

`freeze_plan.py` refreshes identities after reviewed edits. It does not create
evidence, and all previous-plan evidence becomes ineligible for readiness.
Retain earlier attempt records for cost accounting. A graph can be smoke-tested
when production readiness is blocked; production uses the separate wrapper.

## Claim-to-evidence matrix

| Manuscript claim | Source | Generated manuscript artifact | Decision rule |
|---|---|---|---|
| 1,040 policy decisions, 12 fault families | `results/local/decisions.csv` | `generated/counts.tex`, `local_table.tex` | Recount rows by policy/fault |
| Fault-family blocks | same CSV | `fault_detection.pdf` | Counts per 20 deterministic variants |
| Eight CUDA records | Nibi `results/gpu/*.json` | `gpu_table.tex`, `gpu_status.tex` | Exact four modes × two reps; gate on matching records |
| Actual allocation use | Nibi `logs/sacct.psv` | `gpu_status.tex` | Sum parent array-task rows only |
| Candidate availability | `subjects.json`, `papers.json` | `subjects.tex`, `artifact_refs.bib` | Twelve available public repositories, not execution eligibility |
| MapCoder readiness | frozen plan, raw attempts, input checks, assessment | `mapcoder_status.tex` | Fresh exact-plan pair, all obligations, budget, memory limits |
| Resource savings/general adoption | prospective protocol only | no observed result | Requires comparative campaign after author review |

## Limits

The controller is not a hardened accounting or authorization service. Records are
operator-provided. Hashes support declared identity rather than numerical
determinism or authenticity. The wrapper supports conservative homogeneous GPU
shape mappings and rejects raw GPU-stage sbatch overrides. It does not infer
scientific semantics from arbitrary shell commands. Direct upstream submission
bypasses the readiness wrapper; verification-to-execution races and repeated
production dispatch are not solved here. The pilot tests one adapted task, not
all MapCoder benchmarks, arbitrary generated-code compatibility, or distributed
production reliability. Full twelve-artifact execution is deliberately deferred
for the author's review.
