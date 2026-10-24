# RES-AI - Experiment Execution Plan and Status

Read the live snapshot below to see where the project stands. Section 14 is the append-only update history. All timestamps use UTC. The snapshot is generated from collected evidence; the remaining sections record scope, decisions, and operating instructions.

<!-- experiment-status:start -->
**Last checked: 2026-10-24T04:40:18Z (UTC).**

**Where we are: PILOT MILESTONE COMPLETE — broader campaign needs review.**

The implemented controller, CUDA, and one-artifact/two-model pipelines have collected results. The twelve-artifact comparative campaign has not been executed. No experiment is currently recorded as running in the collected status files.

| Experiment / deliverable | Status | Verified evidence |
|---|---|---|
| Controller study and analyses | COMPLETE | 1,040 synthetic decisions; 20 variants; 12 fault families; analysis CSVs present |
| Nibi CUDA integration | COMPLETE | 8 records; clean pair admitted; all 3 injected fault modes blocked (expected results) |
| MapCoder / Qwen2.5-Coder-7B | COMPLETE | 2/2 HumanEval/0 repeats solved; 16 calls; collection-time gate passed; 335.276 timed process seconds |
| MapCoder / Qwen3.8-27B Q4_K_M | COMPLETE | 2/2 HumanEval/0 repeats solved; 16 calls; collection-time gate passed; 454.072 timed process seconds |
| Collected data integrity | COMPLETE | 4 collected archive SHA-256 checksums verified, including the failed attempt and retired-run history |
| Twelve-artifact comparison | NOT STARTED | 12 candidates inventoried; runnable configurations and comparative results remain pending |

**Current next step:** review the pilot evidence and manuscript; agree on eligible subjects, comparison conditions, budgets, and acceptance criteria before implementing the larger campaign.

**Accounting:** CUDA pilot: 81 MIG-instance seconds. Original MapCoder pilot: 383 H100 seconds. Qwen3.8: 548 successful H100 seconds plus 86 for the retained failed attempt (634 total). These are historical collected measurements with different accounting boundaries; this is not a resource-savings comparison.

**Data:** [experiments/results/COLLECTION.md](../../../experiments/results/COLLECTION.md); [experiments/results/mapcoder-attempts.csv](../../../experiments/results/mapcoder-attempts.csv); [experiments/results/mapcoder-qwen38/provenance/sacct-final.psv](../../../experiments/results/mapcoder-qwen38/provenance/sacct-final.psv).

**Hourly updater:** Windows Task Scheduler `RES-AI-Experiment-Status-Hourly`; every 1 hour; next nominal update 2026-10-24T05:39:15Z; registration verified 2026-10-24T04:39:17.5174681Z; computer on and user signed in required. Checks collected local evidence and appends section 14 on every invocation, including unchanged checks. It does not authenticate to Nibi, collect new remote outputs, launch jobs, or independently verify the live queue. Future remote runs must supply updated local evidence/status files; queued/running or missing records are flagged for investigation. An hourly document timestamp is an evidence-check timestamp, not a new experiment execution timestamp.
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

**Current milestone:** execution and collection complete, subject to the live evidence checks above. **Overall research project:** needs author review before expansion. The prospective twelve-artifact campaign has no reported comparative execution results.

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

Completion means outputs and acceptance checks agree, not merely that a job was submitted or exited zero. Future larger-study requirements must be agreed and added before that study can be marked complete.

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
| Author review and protocol agreement | NEEDS HUMAN REVIEW | Review pilot; agree budgets, comparators, eligibility, metrics, fault design |
| Twelve-artifact implementation/execution | NOT STARTED | Implement eligible runnable configurations after protocol review |
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
| Scope expansion mistaken for completion | Larger campaign remains NOT STARTED until its own execution evidence exists | Review checklist and candidate inventory |
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
- [Original MapCoder data](../../../experiments/results/mapcoder/): traces, source, logs, and assessment.
- [Qwen3.8 data](../../../experiments/results/mapcoder-qwen38/): corrected and failed runs, traces, source, setup provenance, accounting.
- [Compiled manuscript](../main.pdf): review draft, with original MapCoder completion status updated. The additional Qwen3.8 data is documented in the collection/operating guide; full manuscript integration remains an author-review task.
- [Operating guide](../../../hpc/docs/hpc-guide.md): run identities and reproducible execution/collection procedures.

## 11. Current decisions and next actions

1. **Author review:** inspect the manuscript, raw traces, two-model pilot evidence, and failed-attempt costs. Decide what to integrate into the manuscript.
2. **Campaign design:** confirm eligible subjects/models/sandboxes, budgets, comparison conditions, failure penalties, equivalence margins, artifact-level analysis, and independent fault design.
3. **Campaign implementation:** turn agreed prospective conditions into runnable configurations, execute bounded validation, then collect actual comparison data before reporting campaign outcomes.

There is no recorded blocker to the completed pilot collection. The larger campaign depends on protocol decisions and implementation; it is not silently queued by this hourly schedule.

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
