# RES-AI - Experiment Execution Plan and Status

Read the live snapshot below to see where the project stands. Section 14 is the append-only update history. All timestamps use UTC. The snapshot is generated from collected evidence; the remaining sections record scope, decisions, and operating instructions.

<!-- experiment-status:start -->
**Last checked: 2026-10-25T02:39:16Z (UTC).**

**Where we are: ATTENTION — evidence needs investigation.**

The implemented controller, CUDA, and one-artifact/two-model pipelines have collected results. The full campaign is authorized and underway; completed comparative episodes are reported separately below. Last recorded active work (live Nibi state not checked): twelve-artifact campaign: FEASIBILITY_AND_COMPARISON.

| Experiment / deliverable | Status | Verified evidence |
|---|---|---|
| Controller study and analyses | COMPLETE | 1,040 synthetic decisions; 20 variants; 12 fault families; analysis CSVs present |
| Nibi CUDA integration | COMPLETE | 8 records; clean pair admitted; all 3 injected fault modes blocked (expected results) |
| MapCoder / Qwen2.5-Coder-7B | COMPLETE | 2/2 HumanEval/0 repeats solved; 16 calls; collection-time gate passed; 335.276 timed process seconds |
| MapCoder / Qwen3.8-27B Q4_K_M | COMPLETE | 2/2 HumanEval/0 repeats solved; 16 calls; collection-time gate passed; 454.072 timed process seconds |
| Collected data integrity | COMPLETE | 4 collected archive SHA-256 checksums verified, including the failed attempt and retired-run history |
| Campaign collection integrity | COMPLETE | 23 collected archive SHA-256 checksums verified, including the failed attempt and retired-run history |
| Twelve-artifact comparison | FEASIBILITY_AND_COMPARISON | 14/1680 potential comparative episodes reported complete; H100 allocated 5960 s, reserved 0 s; initial cap 24 GPU-hours; last campaign report 2026-10-25T02:01:59.351709+00:00 |

**Campaign preparation:** 12/12 source snapshots acquired; 4 dependency import checks passed. These are preparation checks, not completed comparative episodes.

| Candidate | Source check | Latest dependency check | Native validation | Comparative episodes |
|---|---|---|---|---|
| SWE-agent | SOURCE_ACQUIRED_ADAPTER_PENDING | DEPENDENCY_IMPORT_PASSED_LOCAL_RUNTIME_PASSED_NATIVE_WORKFLOW_PENDING | FAILED | 0 |
| OpenHands | SOURCE_ACQUIRED_ADAPTER_PENDING | NOT_VALIDATED | NOT_RUN | 0 |
| AutoCodeRover | SOURCE_ACQUIRED_ADAPTER_PENDING | NOT_VALIDATED | NOT_RUN | 0 |
| MetaGPT | SOURCE_ACQUIRED_ADAPTER_PENDING | DEPENDENCY_CHECK_FAILED | NOT_RUN | 0 |
| ChatDev | SOURCE_ACQUIRED_ADAPTER_PENDING | DEPENDENCY_IMPORT_PASSED_NATIVE_WORKFLOW_PENDING | PASSED | 14 |
| AgentCoder | SOURCE_ACQUIRED_ADAPTER_PENDING | DEPENDENCY_IMPORT_PASSED_NATIVE_WORKFLOW_PENDING | PASSED | 0 |
| MapCoder | SOURCE_ACQUIRED_ADAPTER_PENDING | NOT_VALIDATED | NOT_RUN | 0 |
| RepairAgent | SOURCE_ACQUIRED_ADAPTER_PENDING | DEPENDENCY_CHECK_FAILED | NOT_RUN | 0 |
| ExecutionAgent | SOURCE_ACQUIRED_ADAPTER_PENDING | DEPENDENCY_IMPORT_PASSED_NATIVE_WORKFLOW_PENDING | NOT_RUN | 0 |
| CodeAct | SOURCE_ACQUIRED_ADAPTER_PENDING | NOT_VALIDATED | NOT_RUN | 0 |
| HyperAgent | SOURCE_ACQUIRED_ADAPTER_PENDING | NOT_VALIDATED | NOT_RUN | 0 |
| AgileCoder | SOURCE_ACQUIRED_ADAPTER_PENDING | DEPENDENCY_CHECK_FAILED | NOT_RUN | 0 |

**ChatDev comparative subset:** STOPPED_FOR_AUDIT; 14/140 episodes resolved; 17 submitted. Resource fault mask ineffective: CUDA_VISIBLE_DEVICES=-1 but GPU_DEVICE_ORDINAL/ROCR_VISIBLE_DEVICES=0 remain; Ollama logs show 66/66 layers offloaded to GPU.

**ChatDev data audit:** 16 completed execution receipts retained; 3 fault-affected attempts quarantined, including any aborted attempt. Quarantined attempts are excluded from the completed comparative count above.

**Current next step:** ChatDev comparative subset: STOPPED_FOR_AUDIT. Finish remaining artifact native environment/workflow and oracle checks; collect comparative data under the frozen per-artifact protocols and initial GPU cap.

**Accounting:** CUDA pilot: 81 MIG-instance seconds. Original MapCoder pilot: 383 H100 seconds. Qwen3.8: 548 successful H100 seconds plus 86 for the retained failed attempt (634 total). These are historical collected measurements with different accounting boundaries; this is not a resource-savings comparison.

**Data:** [experiments/results/COLLECTION.md](../../../experiments/results/COLLECTION.md); [experiments/results/mapcoder-attempts.csv](../../../experiments/results/mapcoder-attempts.csv); [experiments/results/mapcoder-qwen38/provenance/sacct-final.psv](../../../experiments/results/mapcoder-qwen38/provenance/sacct-final.psv).

**Hourly updater:** Windows Task Scheduler `RES-AI-Experiment-Status-Hourly`; every 1 hour; next nominal update 2026-10-25T03:39:15Z; registration verified 2026-10-24T04:39:17.5174681Z; computer on and user signed in required. Checks collected local evidence and appends section 14 on every invocation, including unchanged checks. It does not authenticate to Nibi, collect new remote outputs, launch jobs, or independently verify the live queue. Future remote runs must supply updated local evidence/status files; queued/running or missing records are flagged for investigation. An hourly document timestamp is an evidence-check timestamp, not a new experiment execution timestamp.

**Issues found:**
- ChatDev automatic queue stopped for audit: Resource fault mask ineffective: CUDA_VISIBLE_DEVICES=-1 but GPU_DEVICE_ORDINAL/ROCR_VISIBLE_DEVICES=0 remain; Ollama logs show 66/66 layers offloaded to GPU.
<!-- experiment-status:end -->

## 1. Project identity

- **Project:** RES-AI - evidence-bound readiness for experiments on shared Slurm clusters.
- **Owner:** Majid Babaei / project author.
- **Workspace:** `C:/Users/babaei/Desktop/Research/Ai4SE4AI/RES-AI`.
- **Recorded baseline:** branch `dev`, commit `775e6017a9fb0639f4b68720a3b86597ea70e106`; subsequent working-tree changes exist.
- **Environments:** Windows analysis workstation; Nibi Slurm GPU/CPU allocations.
- **Authority:** [README](../../../README.md), [Nibi operating guide](../../../hpc/docs/hpc-guide.md), [review checklist](../../../experiments/REVIEW_CHECKLIST.md), and the user's accepted scope: finish the existing pipelines and additionally use `qwen3.8:27b`.

## 2. Project brief and current scope

RES-AI checks whether execution evidence is adequate for a declared experiment plan. The current milestone comprises synthetic controller conformance, a real CUDA integration check, and one MapCoder task deployed with two local models. Its purpose is to establish bounded execution/readiness behavior before a larger comparative study.

**Pilot milestone:** execution, collection and Qwen3.8 paper integration complete, subject to the evidence checks above. **Overall research project:** full campaign authorized and in feasibility. The user authorized the full twelve-artifact campaign on 2026-10-24 with an initial 24 H100 GPU-hour cap. Comparative results are not yet available.

The additional model is Ollama `qwen3.8:27b`, Q4_K_M, Ollama 0.40.10, thinking disabled, greedy decoding. MapCoder uses HumanEval/0, k=3, t=5, one outer attempt, at most 12,288 input and 4,096 generated tokens per call, and two fresh repeated processes.

## 3. Requirements and acceptance criteria

| ID | Requirement | Acceptance / evidence |
|---|---|---|
| REQ-01 | Collect existing controller and CUDA experiments | Raw decisions, eight CUDA records, analyses, configuration, logs, and accounting available locally |
| REQ-02 | Finish original MapCoder pilot | Two independent records; required probes, correctness outcomes, call traces, and assessment collected |
| REQ-03 | Add Qwen3.8-27B deployment run | Separate frozen plan and run identity; two fresh repeated processes; raw traces and accounting collected |
| REQ-04 | Preserve unsuccessful attempts | Earlier canceled runs and the failed model-identity check remain in logs and accounting |
| REQ-05 | Maintain one readable status file | This document shows current scope, verified status, limitations, next actions, and evidence links |
| REQ-06 | Refresh every hour and retain a record | Registered scheduled task; successful updater receipt; a new section-14 journal row on every invocation |
| REQ-07 | Integrate collected Qwen3.8 evidence into the paper | Generated two-model results, methods, failure cost and limitations in the rebuilt, visually checked PDF; complete |
| REQ-08 | Execute the authorized larger campaign | Native adapters, held-out probes and artifact-specific oracles validated before comparative runs; all conditions use the same frozen scientific configuration; currently in feasibility |
| REQ-09 | Enforce the initial 24 H100 GPU-hour cap | Charge new setup, failures, retries and pending reservations; retain Slurm parent-allocation accounting; report CPU costs separately |

Completion means outputs and acceptance checks agree, not merely that a job was submitted or exited zero. Source/dependency checks are preparation. Full-study reporting must preserve ineligible, failed, timed-out and budget-limited cases and distinguish them from completed comparisons.

## 4. Architecture and design

- `src/resai/`: readiness policy, discovery/refinement, guarded dispatch, and MCP interface.
- `hpc/`: CUDA integration pipeline; `hpc/mapcoder/`: MapCoder execution templates.
- `experiments/mapcoder/`: pinned task, model adapters, preparation, evidence assessment, and archival scripts.
- `experiments/results/`: collected data, logs, immutable run archives, and status receipts; ignored by Git, so preserve/backup separately.
- `docs/EMSE/`: manuscript, generated figures/tables, compiled review draft.
- `experiments/update_project_status.py`: hourly document maintenance from local evidence; preserves all text outside its marked snapshot and appends history.

Scientific identity, execution identity, model manifest bytes, and Ollama's advertised model digest are recorded separately. A historical readiness pass is not fresh authorization for a future dispatch.

## 5. Execution phases

| Phase | State at the 2026-10-24 collection milestone | Exit criterion / next step |
|---|---|---|
| Discovery and baseline | COMPLETE | Repository and Nibi environment established |
| Controller conformance and analyses | COMPLETE | Synthetic decisions and supplementary CSVs collected |
| CUDA integration | COMPLETE | Four modes times two repeats; intended faults block readiness |
| Original MapCoder deployment | COMPLETE | Qwen2.5-Coder-7B repeated task, traces, assessment, accounting |
| Additional Qwen3.8 deployment | COMPLETE | Corrected run repeated task, traces, assessment, accounting |
| Collection and evidence audit | COMPLETE | Four downloaded archives checksum-verified; unsuccessful attempts retained |
| Hourly status maintenance | See live snapshot and section 14 | Hourly scheduled execution and append-only history |
| Full campaign authorization | COMPLETE | User authorized full execution with an initial 24 H100 GPU-hour cap; scientific eligibility and adapter checks still apply |
| Twelve-artifact implementation/execution | CHATDEV QUEUE STOPPED FOR AUDIT | Fourteen clean/environment ChatDev episodes completed; three resource-fault attempts quarantined because the injection did not remove GPU access. Remaining artifact validation and a versioned fault correction are pending |
| Full comparative analysis and publication handover | NOT STARTED | Requires comparative campaign data and author declarations |

The phase table describes the dated milestone. The generated snapshot takes precedence if current evidence checks identify missing or inconsistent data.

## 6. Experiment and job tracker

| Experiment / run | Jobs | Outcome at collection | Evidence |
|---|---|---|---|
| Controller mutations and analyses | Local scripts; mutations also collected in Nibi CPU analysis | 1,040 synthetic decisions, 20 variants, 12 fault families | [Controller summary](../../../experiments/results/local/summary.json) |
| `resai-smoke-20261023-2315` | GPU array `24888989`; CPU analysis `24888990` | Completed; eight CUDA probe records | [CUDA status](../../../experiments/results/nibi/STATUS.json) |
| `resai-mapcoder-h100-20261023` | GPU `24890766`; collector `24890918` | Both repeats solved HumanEval/0; gate passed | [Original assessment](../../../experiments/results/mapcoder/assessment/assessment.json) |
| `resai-mapcoder-qwen38-20261024` | GPU `24900967`; collector `24902502` | Failed before inference: incorrect digest-identity comparison; retained | [Failed-attempt evidence](../../../experiments/results/mapcoder-qwen38/failed-24900967/assessment/evidence.json) |
| `resai-mapcoder-qwen38-v2-20261024` | Identity preflight `24902704`; GPU `24902711`; collector `24902997` | Both repeats solved HumanEval/0; gate passed | [Qwen3.8 assessment](../../../experiments/results/mapcoder-qwen38/assessment/assessment.json) |
| Qwen3.8 preparation | Download `24900715`, `24900729`; resume/check `24900970`; prepare `24900907`; inspection `24902522` | Download/version and identity problems recovered; provenance retained | [Final accounting](../../../experiments/results/mapcoder-qwen38/provenance/sacct-final.psv) |
| Campaign exact-source audit | CPU `24904387`; ChatDev legacy selection `24904650` | Source acquisition and static inventory; native workflow validation pending | [Campaign snapshot](../../../experiments/results/campaign/STATUS.json) |
| Native dependency preparation | CPU `24904527`; array `24904649` | Failed setup attempts retained; AgentCoder package import passed; native workflow pending | [Campaign snapshot](../../../experiments/results/campaign/STATUS.json) |
| Site-compatible native environments | CPU image `24904849`; environment array `24905002` | Apptainer Python smoke passed; four isolated dependency checks submitted | [Campaign snapshot](../../../experiments/results/campaign/STATUS.json) |
| ChatDev dependency repair | CPU `24905241` | OpenAI client imports passed with a separate `httpx==0.27.2` overlay; initial failure preserved | [Campaign snapshot](../../../experiments/results/campaign/STATUS.json) |
| Native ChatDev / Qwen3.8 feasibility | Failed GPU `24905744`; corrected CPU `24906075`, GPU `24906078`, collector `24906079` | PASSED: 12 model calls and independent 12-case oracle. Allocation 199 H100 seconds; retained startup failure 238 seconds. These are native validations, not comparative episodes | [Collected native validation](../../../experiments/results/campaign/native-validation/24906078/collected/) |
| Native AgentCoder / Qwen3.8 feasibility | CPU `24925673`; GPU `24925674`; collector `24925675` | PASSED: 90 actual model calls, all five native repair epochs completed, independent HumanEval/2 oracle passed. Raw archive collected and checksum-verified. This is native feasibility, not a comparative episode | [Collected AgentCoder validation](../../../experiments/results/campaign/native-validation/24925674/collected/) |
| Native SWE-agent setup and validation | Startup CPU `24926368`; full control CPU `24927831`; GPU `24927834`; collector `24927835` | GPU validation FAILED after repeated HTTP 400 responses from the local model endpoint; zero completed model calls, no submitted patch. Model identity/residency checks passed. Failed allocation cost 1,031 H100 seconds; raw archive collected and checksum-verified. CPU fixture success does not establish model compatibility | [Collected failed validation](../../../experiments/results/campaign/failed-native-validation/24927834/collected/) |
| ChatDev clean/environment comparative blocks | Seventeen submitted allocations recorded in the campaign ledger; sixteen completed raw receipts, one affected run aborted | All seven clean seed-0 conditions PRODUCTION_VALID. Environment fault: full, no_coverage, no_refinement and upstream smoke blocked; direct_native, upstream_static and no_identity_freshness attempted invalid production. Fourteen qualified completed episodes collected. One paired seed/task only; no aggregate study claim | [Collected comparison data](../../../experiments/results/campaign/comparison/) |
| ChatDev resource-fault audit | Affected GPUs `24950514`, `24951292`, `24951623`; advance collector `24951624` canceled; audit CPU `24951786` | GPU mask was ineffective: CUDA mask -1 coexisted with GPU_DEVICE_ORDINAL/ROCR mask 0; logs show all 66 model layers offloaded to GPU. Two completed runs quarantined, third run canceled to avoid further invalid measurement. Automatic queue stopped; all raw and partial outputs retained. Frozen source/protocol unchanged | [Collected resource audit](../../../experiments/results/campaign/resource-fault-audit/24951786/collected/) |
| Additional native dependency screening | CPU array `24927936`; retry array `24927985` (RepairAgent, ExecutionAgent, AgileCoder) | ExecutionAgent dependency imports passed; native workflow pending. RepairAgent retry failed pip resolution (resolution-too-deep); AgileCoder retry import failed on missing tenacity. Initial environment-creation timeouts and both retries retained. Four artifact dependency checks now pass; no additional model results implied | [Campaign snapshot](../../../experiments/results/campaign/STATUS.json) |
| CPU preparation collection | CPU `24905179` | Runs after the original source/environment jobs, preserving successful and failed preparation attempts | [Campaign snapshot](../../../experiments/results/campaign/STATUS.json) |

The twelve prospective subjects are SWE-agent, OpenHands, AutoCodeRover, MetaGPT, ChatDev, AgentCoder, MapCoder, RepairAgent, ExecutionAgent, CodeAct, HyperAgent, and AgileCoder; see the [candidate inventory](../../../experiments/subjects.json). This inventory is not a completed screening funnel or proof of execution eligibility. The bounded MapCoder pilot does not mean the prospective MapCoder campaign condition has been executed.

## 7. Verification and evidence policy

Every completion claim needs readable outputs and matching acceptance checks. The hourly updater recounts decision rows, checks CUDA mode/repeat coverage and admission outcomes, verifies repeated MapCoder records and trace counts, and validates the collected archive checksums. It flags missing or inconsistent evidence as ATTENTION.

The final experiment handover verified four successful MapCoder records, 32 model calls, both frozen source inventories, both admission dry runs, eight CUDA records, and archive checksums. The implementation suite passed 16 tests at that handover. On 2026-10-24, all 18 tests passed after adding maintenance tests for preserving manual notes/history and refusing unsafe overwrites. A real Task Scheduler invocation refreshed the file and appended history successfully (LastTaskResult 0). Hourly maintenance does not rerun GPU experiments or the implementation test suite.

Remote status is historical unless a new authenticated scheduler observation is explicitly collected. Nibi requires MFA; the hourly local updater does not request Duo pushes or assume unattended access. Missing evidence, failed execution, expected injected failure, unstarted work, and a valid zero measurement must remain distinct.

## 8. Risks, failures, and recovery history

| Incident | Resolution / current state | Retained evidence |
|---|---|---|
| Windows CRLF in Bash configuration | Pending array `24889793` canceled; corrected submission `24890017` later canceled for interactive route | Original assessment accounting and `nibi-history/` |
| Unavailable MIG capacity | Pending allocation `24890605` canceled; bounded full-H100 pilot completed | Original pilot status and accounting |
| Ollama too old for Qwen3.8 | Initial download failed; isolated Ollama 0.40.10 installed with release checksum verification | Qwen3.8 `provenance/download/` |
| Download exceeded initial walltime estimate | Partial bytes preserved; continuation job completed and verified the download | Download and continuation logs |
| Manifest checksum confused with API model digest | First GPU attempt failed before inference; both identities separately pinned; CPU regression/preflight passed; fresh GPU run succeeded | Failed archive plus corrected source and traces |
| Scope expansion mistaken for completion | Campaign preparation and executed comparative episodes have separate statuses and counts | Campaign status, native receipts and candidate inventory |
| Workstation asleep/off or user signed out | Hourly local updates cannot run; Task Scheduler catches up when available | Check last-updated timestamp and scheduler state |

Do not erase failed records after recovery. Additional experiments or changes to scientific settings require explicit scope/plan updates; this maintenance schedule does not authorize them.

## 9. Results and measurements

| Measurement | Collected result | Boundary / limitation |
|---|---|---|
| Controller decisions | 1,040 synthetic decisions | Not 1,040 independent studies; modeled comparators |
| CUDA probe records | 8 across 4 modes times 2 repeats | Synthetic tensors; expected injected faults are retained |
| CUDA allocation | 81 MIG-instance seconds | Keep separate from full-H100 accounting |
| Original MapCoder outcomes | 2/2 solved; 8 calls each | One HumanEval task, local Qwen2.5-Coder adaptation |
| Original MapCoder time | 383 H100 allocation-seconds; 335.276 timed process-seconds | Initialization/setup boundaries differ |
| Qwen3.8 outcomes | 2/2 solved; 8 calls each | One HumanEval task; quantized model; thinking off |
| Qwen3.8 time | 548 successful H100 seconds + 86 unsuccessful = 634 total; 454.072 successful process-seconds | Preserve failed-work cost; CPU setup/download/collection accounted separately |
| Comparative resource savings / broad adoption | NOT MEASURED | Requires the prospective comparative campaign |

Repeated correctness on one task is not aggregate benchmark accuracy. Memory statistics differ between backends (PyTorch allocator peak versus sampled whole-device memory) and must not be compared as identical measurements.

## 10. Deliverables and artifact inventory

- [Collection index](../../../experiments/results/COLLECTION.md): entry point for all collected data.
- [Attempt-level CSV](../../../experiments/results/mapcoder-attempts.csv): four successful repeated-run records.
- [Archive checksum inventory](../../../experiments/results/COLLECTED-SHA256SUMS.txt): four downloaded archives, including unsuccessful/retired history.
- [Campaign snapshot](../../../experiments/results/campaign/STATUS.json): source, environment, native validation, reservations and accounting; fourteen qualified completed comparative episodes, three quarantined fault attempts and an explicit audit stop at the 2026-10-25 check.
- [Campaign preparation and validation checksums](../../../experiments/results/campaign/COLLECTED-SHA256SUMS.txt): initial 82-file preparation archive, a new 357-file preparation archive (CPU repair/control traces and frozen comparative inputs), plus failed and successful ChatDev native-validation archives. Includes calls, generated code, oracles, logs and accounting. Large upstream caches and pending results remain on Nibi.
- [Original MapCoder data](../../../experiments/results/mapcoder/): traces, source, logs, and assessment.
- [Qwen3.8 data](../../../experiments/results/mapcoder-qwen38/): corrected and failed runs, traces, source, setup provenance, accounting.
- [Compiled manuscript](../main.pdf): review draft, with original MapCoder completion status updated. Qwen3.8 methods, outcomes, allocation/process costs, recovery, and limitations are now integrated; the rebuilt 35-page PDF was visually checked.
- [Operating guide](../../../hpc/docs/hpc-guide.md): run identities and reproducible execution/collection procedures.

## 11. Current decisions and next actions

1. **Paper integration (complete):** both model configurations, all four successful repeats, failed-attempt cost and measurement limitations are integrated into the rebuilt manuscript.
2. **Campaign feasibility:** all twelve source snapshots acquired; four dependency import checks passed. ChatDev and AgentCoder native GPU validations passed; AgentCoder's 90-call/five-epoch result and independent oracle are collected. SWE-agent still requires endpoint/tool compatibility repair after its HTTP 400 failure. Resolve RepairAgent dependency resolution and AgileCoder's undeclared tenacity dependency; ExecutionAgent still needs native workflow validation. The approved initial cap remains 24 H100 GPU-hours, including setup and failed allocations.
3. **Campaign execution requires a fault-injection correction:** fourteen seed-0 clean/environment episodes are complete and collected. Three resource-fault attempts are quarantined (two completed with the intended fault absent; one aborted). Automatic advancement is stopped by canceling its dependent collector. Preserve original source, plans, results and accounting; validate and freeze a versioned resource-fault amendment before rerunning that paired block and resuming the remaining queue. Do not silently replace the original protocol or classify these resource runs as valid fault evidence. As of 2026-10-25 02:02 UTC, 5,960 H100 seconds (1h39m20s) are allocated and none reserved, within the 24-hour cap. Full campaign progress is 14/1,680 qualified completed episodes; no aggregate effectiveness or savings claims follow from one seed/task.

The pilot collection and Qwen3.8 manuscript integration are complete. The full campaign is now explicitly authorized and in feasibility under the 24 GPU-hour initial cap. Native adapters, datasets/oracles, and environment compatibility must pass before comparative GPU submission. Source acquisition is not a completed comparative experiment.

## 12. AI agent operating instructions

Treat this file as the project status entry point. Read actual source/evidence before changing claims. Preserve source, unsuccessful attempts, and user edits. Update manual sections when scope or milestones change; the hourly script changes only the marked snapshot and appends section 14.

On new experiments, record run ID, model/task/config identity, Slurm job IDs, raw output location, collection status, outcome, and cost accounting. Register new evidence checks in `experiments/update_project_status.py` when the project scope changes. Do not infer completion from a planned filename or a launched command. Record unknowns explicitly.

The hourly task is reporting maintenance only. It must not submit experiments, alter model settings, send messages, request MFA, or publish results. A new snapshot is not new scientific evidence. If an updater failure occurs, inspect `experiments/results/status-maintenance/last-update.json` and the Windows task's LastTaskResult; a stale timestamp means freshness is unknown.

## 13. Scheduler and manual operation

- **Task name:** `RES-AI-Experiment-Status-Hourly` in Windows Task Scheduler.
- **Schedule:** every 1 hour, indefinitely, with missed-start catch-up; current-user task, no stored password, hidden Python process.
- **Availability:** this computer must be on and the user signed in. Missed hours are not fabricated as checks. The next actual invocation appends one truthful record.
- **Updater:** `python experiments/update_project_status.py --reason "manual evidence check"`.
- **Inspect task:** `Get-ScheduledTask -TaskName RES-AI-Experiment-Status-Hourly` and `Get-ScheduledTaskInfo -TaskName RES-AI-Experiment-Status-Hourly`.
- **Disable:** `Disable-ScheduledTask -TaskName RES-AI-Experiment-Status-Hourly`.
- **Reinstall/refresh registration:** `powershell -NoProfile -File experiments/register_status_schedule.ps1`.
- **Scheduler receipt:** `experiments/results/status-maintenance/scheduler.json`.
- **Last update receipt:** `experiments/results/status-maintenance/last-update.json`.

## 14. Hourly update history

Every real updater invocation appends one record below, even when the evidence is unchanged. Earlier records are preserved. This is the last section of the document.

| Checked at (UTC) | Record |
|---|---|
| 2026-10-24T04:39:13Z | initial project status reconciliation; evidence changed; 5/5 evidence checks complete; twelve-artifact campaign NOT STARTED |
| 2026-10-24T04:39:45Z | hourly scheduled evidence check; no evidence changes; 5/5 evidence checks complete; twelve-artifact campaign NOT STARTED |
| 2026-10-24T04:40:18Z | scheduler verified; 18 tests passed; initial setup complete; no evidence changes; 5/5 evidence checks complete; twelve-artifact campaign NOT STARTED |
| 2026-10-24T05:10:18Z | Qwen3.8 paper integration complete; campaign feasibility running as Nibi job 24904387; initial cap 24 H100 GPU-hours; evidence changed; 5/5 evidence checks complete; twelve-artifact campaign FEASIBILITY, 0/1680 potential episodes, cap 24 H100 hours |
| 2026-10-24T05:22:17Z | Collected Nibi feasibility and CPU accounting snapshot; evidence changed; 5/5 evidence checks complete; twelve-artifact campaign FEASIBILITY, 0/1680 potential episodes, cap 24 H100 hours |
| 2026-10-24T05:30:34Z | Added per-candidate preparation reporting and recorded container-native environment jobs; no evidence changes; 5/5 evidence checks complete; twelve-artifact campaign FEASIBILITY, 0/1680 potential episodes, cap 24 H100 hours |
| 2026-10-24T05:31:45Z | Collected current container-native preparation status; comparative execution remains pending; evidence changed; 5/5 evidence checks complete; twelve-artifact campaign FEASIBILITY, 0/1680 potential episodes, cap 24 H100 hours |
| 2026-10-24T05:39:15Z | hourly scheduled evidence check; no evidence changes; 5/5 evidence checks complete; twelve-artifact campaign FEASIBILITY, 0/1680 potential episodes, cap 24 H100 hours |
| 2026-10-24T05:46:24Z | All twelve sources acquired; ChatDev native GPU validation 24905744 submitted under budget; no comparative episodes yet; evidence changed; 5/5 evidence checks complete; twelve-artifact campaign FEASIBILITY, 0/1680 potential episodes, cap 24 H100 hours |
| 2026-10-24T05:49:45Z | Collected 82 preparation evidence files; native ChatDev validation queued; hourly task verified successful at 05:39 UTC; no evidence changes; 5/5 evidence checks complete; twelve-artifact campaign FEASIBILITY, 0/1680 potential episodes, cap 24 H100 hours |
| 2026-10-24T06:39:16Z | hourly scheduled evidence check; no evidence changes; 5/5 evidence checks complete; twelve-artifact campaign FEASIBILITY, 0/1680 potential episodes, cap 24 H100 hours |
| 2026-10-24T07:39:16Z | hourly scheduled evidence check; no evidence changes; 5/5 evidence checks complete; twelve-artifact campaign FEASIBILITY, 0/1680 potential episodes, cap 24 H100 hours |
| 2026-10-24T08:39:16Z | hourly scheduled evidence check; no evidence changes; 5/5 evidence checks complete; twelve-artifact campaign FEASIBILITY, 0/1680 potential episodes, cap 24 H100 hours |
| 2026-10-24T09:39:16Z | hourly scheduled evidence check; no evidence changes; 5/5 evidence checks complete; twelve-artifact campaign FEASIBILITY, 0/1680 potential episodes, cap 24 H100 hours |
| 2026-10-24T10:39:16Z | hourly scheduled evidence check; no evidence changes; 5/5 evidence checks complete; twelve-artifact campaign FEASIBILITY, 0/1680 potential episodes, cap 24 H100 hours |
| 2026-10-24T11:39:16Z | hourly scheduled evidence check; no evidence changes; 5/5 evidence checks complete; twelve-artifact campaign FEASIBILITY, 0/1680 potential episodes, cap 24 H100 hours |
| 2026-10-24T12:39:16Z | hourly scheduled evidence check; no evidence changes; 5/5 evidence checks complete; twelve-artifact campaign FEASIBILITY, 0/1680 potential episodes, cap 24 H100 hours |
| 2026-10-24T13:39:16Z | hourly scheduled evidence check; no evidence changes; 5/5 evidence checks complete; twelve-artifact campaign FEASIBILITY, 0/1680 potential episodes, cap 24 H100 hours |
| 2026-10-24T14:39:16Z | hourly scheduled evidence check; no evidence changes; 5/5 evidence checks complete; twelve-artifact campaign FEASIBILITY, 0/1680 potential episodes, cap 24 H100 hours |
| 2026-10-24T15:39:16Z | hourly scheduled evidence check; no evidence changes; 5/5 evidence checks complete; twelve-artifact campaign FEASIBILITY, 0/1680 potential episodes, cap 24 H100 hours |
| 2026-10-24T15:40:35Z | Collected successful native ChatDev validation: 12 model calls, independent oracle passed; total campaign 437 H100 seconds including failure; evidence changed; 5/5 evidence checks complete; twelve-artifact campaign FEASIBILITY, 0/1680 potential episodes, cap 24 H100 hours |
| 2026-10-24T16:39:16Z | hourly scheduled evidence check; no evidence changes; 5/5 evidence checks complete; twelve-artifact campaign FEASIBILITY, 0/1680 potential episodes, cap 24 H100 hours |
| 2026-10-24T16:40:43Z | ChatDev native validation collected; AgentCoder native and first ChatDev comparative episode queued; SWE-agent CPU setup passed; 437 H100 seconds allocated and 3420 reserved; evidence changed; 5/5 evidence checks complete; twelve-artifact campaign FEASIBILITY_AND_COMPARISON, 0/1680 potential episodes, cap 24 H100 hours |
| 2026-10-24T16:44:43Z | SWE-agent native tool transport and independent repair oracle implemented; 32 local verification tests passed; preparing CPU control-flow validation; no evidence changes; 5/5 evidence checks complete; twelve-artifact campaign FEASIBILITY_AND_COMPARISON, 0/1680 potential episodes, cap 24 H100 hours |
| 2026-10-24T16:45:59Z | SWE-agent CPU native repair/review/submission fixture passed; GPU 24927834 and collector 24927835 queued; campaign budget reconciled; evidence changed; 5/5 evidence checks complete; twelve-artifact campaign FEASIBILITY_AND_COMPARISON, 0/1680 potential episodes, cap 24 H100 hours |
| 2026-10-24T16:51:33Z | Additional dependency screening CPU array 24927936 submitted; shared-filesystem environment-creation timeouts preserved and separate retries prepared; campaign archives now included in integrity checks; evidence changed; 6/6 evidence checks complete; twelve-artifact campaign FEASIBILITY_AND_COMPARISON, 0/1680 potential episodes, cap 24 H100 hours |
| 2026-10-24T16:56:44Z | Collected and checksum-verified 357-file preparation archive; SWE-agent native GPU validation queued; three GPU jobs pending in 16:55 UTC report; 437 H100 seconds allocated and 4680 reserved; 32 tests and paper claims check passed; evidence changed; 6/6 evidence checks complete; twelve-artifact campaign FEASIBILITY_AND_COMPARISON, 0/1680 potential episodes, cap 24 H100 hours |
| 2026-10-24T16:57:43Z | Final Nibi queue/accounting refresh; ChatDev subset eligibility recorded separately from remaining artifact preparation; zero comparative outcomes complete; evidence changed; 6/6 evidence checks complete; twelve-artifact campaign FEASIBILITY_AND_COMPARISON, 0/1680 potential episodes, cap 24 H100 hours |
| 2026-10-24T17:39:16Z | hourly scheduled evidence check; no evidence changes; 6/6 evidence checks complete; twelve-artifact campaign FEASIBILITY_AND_COMPARISON, 0/1680 potential episodes, cap 24 H100 hours |
| 2026-10-24T18:39:16Z | hourly scheduled evidence check; no evidence changes; 6/6 evidence checks complete; twelve-artifact campaign FEASIBILITY_AND_COMPARISON, 0/1680 potential episodes, cap 24 H100 hours |
| 2026-10-24T19:39:16Z | hourly scheduled evidence check; no evidence changes; 6/6 evidence checks complete; twelve-artifact campaign FEASIBILITY_AND_COMPARISON, 0/1680 potential episodes, cap 24 H100 hours |
| 2026-10-24T20:39:16Z | hourly scheduled evidence check; no evidence changes; 6/6 evidence checks complete; twelve-artifact campaign FEASIBILITY_AND_COMPARISON, 0/1680 potential episodes, cap 24 H100 hours |
| 2026-10-24T21:39:16Z | hourly scheduled evidence check; no evidence changes; 6/6 evidence checks complete; twelve-artifact campaign FEASIBILITY_AND_COMPARISON, 0/1680 potential episodes, cap 24 H100 hours |
| 2026-10-24T22:39:16Z | hourly scheduled evidence check; no evidence changes; 6/6 evidence checks complete; twelve-artifact campaign FEASIBILITY_AND_COMPARISON, 0/1680 potential episodes, cap 24 H100 hours |
| 2026-10-24T22:46:48Z | Nibi recheck 22:43 UTC: collected three valid ChatDev comparative episodes and failed SWE-agent HTTP-400 validation; eight campaign archives checksum-verified; 2367 H100 seconds allocated, 3420 reserved; AgentCoder and next ChatDev case pending; evidence changed; 6/6 evidence checks complete; twelve-artifact campaign FEASIBILITY_AND_COMPARISON, 3/1680 potential episodes, cap 24 H100 hours |
| 2026-10-24T23:39:16Z | hourly scheduled evidence check; no evidence changes; 6/6 evidence checks complete; twelve-artifact campaign FEASIBILITY_AND_COMPARISON, 3/1680 potential episodes, cap 24 H100 hours |
| 2026-10-25T00:39:17Z | hourly scheduled evidence check; no evidence changes; 6/6 evidence checks complete; twelve-artifact campaign FEASIBILITY_AND_COMPARISON, 3/1680 potential episodes, cap 24 H100 hours |
| 2026-10-25T01:39:16Z | hourly scheduled evidence check; no evidence changes; 6/6 evidence checks complete; twelve-artifact campaign FEASIBILITY_AND_COMPARISON, 3/1680 potential episodes, cap 24 H100 hours |
| 2026-10-25T02:03:47Z | Nibi recheck: AgentCoder native validation passed with 90 calls; 14 clean/environment comparative episodes qualified; three ineffective resource-fault attempts quarantined, automatic advancement stopped and affected allocation canceled; 23 campaign archives verified; 5960 H100 seconds allocated, none reserved; evidence changed; 6/6 evidence checks complete; twelve-artifact campaign FEASIBILITY_AND_COMPARISON, 14/1680 potential episodes, cap 24 H100 hours; ATTENTION: ChatDev automatic queue stopped for audit: Resource fault mask ineffective: CUDA_VISIBLE_DEVICES=-1 but GPU_DEVICE_ORDINAL/ROCR_VISIBLE_DEVICES=0 remain; Ollama logs show 66/66 layers offloaded to GPU. |
| 2026-10-25T02:39:16Z | hourly scheduled evidence check; no evidence changes; 6/6 evidence checks complete; twelve-artifact campaign FEASIBILITY_AND_COMPARISON, 14/1680 potential episodes, cap 24 H100 hours; ATTENTION: ChatDev automatic queue stopped for audit: Resource fault mask ineffective: CUDA_VISIBLE_DEVICES=-1 but GPU_DEVICE_ORDINAL/ROCR_VISIBLE_DEVICES=0 remain; Ollama logs show 66/66 layers offloaded to GPU. |
