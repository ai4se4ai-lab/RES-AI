# Twelve-artifact campaign

The author requested this campaign on 2026-10-24 after integration of the Qwen3.8
pilot into the paper, with an **initial cap of 24 H100 GPU-hours**. The frozen
inventory/design is `plan.json`; current observations belong in
`../results/campaign/STATUS.json`. The project status entry point is
`../../docs/EMSE/support/AI_AGENT_PROJECT_EXECUTION_PLAN.md`.

The intended design is twelve candidate artifacts, seven conditions, five paired
seeds, and four episode classes: 1,680 potential episodes. A planned matrix row
is not an execution result. Source acquisition and dependency import success do
not establish that an artifact's native workflow, oracle, sandbox, or model
adaptation works. Ineligible and budget-limited cases must stay visible.

Current stages:

1. `initialize.py` preserves the original campaign authorization, source inventory,
   model identity and compute cap. Do not rerun it over an existing plan.
2. `feasibility.py` runs in CPU jobs, archives exact source revisions and checksums,
   and records dependency manifests and native entrypoints. It never declares a
   candidate eligible from static source availability.
3. Build isolated native environments and validate model transport, a held-out
   probe, the artifact-specific oracle and a site-compatible sandbox. Keep
   source/version corrections as separate, justified selections before comparative
   outcomes are inspected. ChatDev's `chatdev1.0` branch is the documented legacy
   implementation; current HEAD describes a different architecture.
4. Implement and validate all native conditions, including actual upstream smoke
   execution, and freeze per-artifact tasks, prompts, limits, faults and scoring.
   A generic code-generation replacement is not an execution of twelve artifacts.
5. `budget.py` reserves GPU allocation time before submission. Setup, failed jobs,
   retries and pending reservations count; CPU costs are reported separately.
   One-H100 requests reserve walltime plus 60 seconds of termination headroom.
   The initial per-artifact reservation ceiling is two hours. Never launch an
   allocation unless both global and artifact budgets admit it. This guard is an
   operator workflow, not a scheduler security boundary.
   Use reservation purpose `native_validation` for the first GPU smoke, with
   source, dependency, sandbox and local transport evidence. Only purpose
   `comparison` requires an already successful native model smoke and oracle.
   Validation allocations count against the same cap.
6. `make_matrix.py` enumerates intended pairs and randomizes condition order within
   artifact/seed/fault blocks. Execute only with validated native adapters and
   preserve statuses for unexecuted, failed, timed-out and completed cases.
7. Collect raw traces, adapter/source identities, per-condition outcomes, actual
   parent-allocation accounting and failed-attempt history before statistical
   analysis or manuscript claims. Stop new GPU submissions at the initial cap.

Earlier pilot allocations are archived separately and excluded from the newly
authorized campaign budget. The pilot does not constitute a completed comparison
for MapCoder in this seven-condition design.

`prepare-chatdev-validation.sh` performs CPU checks and submits one 20-minute
one-H100 native ChatDev feasibility allocation after reserving 1,260 seconds.
The native legacy role prompts and chain are retained; the text-only task turns
GUI design off and replaces model transport with the pinned local Qwen backend.
The authored normalization task and restricted positive/negative oracle check
are held-out setup checks, not benchmark or comparative outcomes. Upstream
example projects are excluded from the fresh output workspace. Native output,
all model calls and completion/oracle outcomes are archived. A 48-call and
18-minute process limit fits inside the allocation. A separate dependent CPU
collector reconciles Slurm accounting and archives success or failure.

The seven-condition controller and ChatDev comparative adapter are implemented.
`prepare-chatdev-comparison.sh` freezes 140 episode specifications, checks the
production oracles on canonical and corrupted programs, checks both native
startup paths without making model requests, and executes a real inherited
upstream CPU stage before permitting GPU submission. Production tasks are
HumanEval/2--6, mapped to paired seeds 0--4; normalization is held out for probes.
The child `comparison/chatdev/protocol.json` declares fault operators, ablation
semantics, one server per episode, fresh native processes/workspaces, 900-second
allocation ceilings and the source hashes. All seven conditions share the
native worker. Baseline smoke and non-direct production execute the actual
inherited upstream runner. Full-policy bindings check input/graph/scientific and
resource correspondence. No model success is fabricated by the CPU fixtures.

The queue submits one episode at a time, collects success/failure, reconciles
actual allocation time and reserves the next ceiling before submission. It
stops on a budget limit or an unresolved execution issue. Cache replay uses
actual prior clean probe records, not generated telemetry. Inputs and an episode
checksum are verified before execution. Remaining artifact-specific comparison
adapters are pending. A successful native feasibility run never increments the
comparative count.

`prepare-sweagent-validation.sh` checks the actual native local deployment,
tool loop, repair, review and submission with three labeled CPU fixture
responses, then checks a positive and incorrect division program with an
independent restricted oracle. Only a passing preflight freezes the source,
official example, container and adapter hashes and admits one 20-minute H100
native validation. The default native prompts, tool schemas and review process
are retained. The local transport maps tool-call argument objects and IDs to
the native LiteLLM response schema, preserves raw requests/responses, and
enforces the pinned model identity, GPU residency, token envelope and 32-call
limit. This small official example is feasibility evidence, not SWE-bench or a
comparative episode. CPU fixture responses never count as model observations.

`install-additional-environments.sh` screens RepairAgent's official core
requirements and the native ExecutionAgent/AgileCoder packages on CPU. The
AgileCoder import check disables only its inactive Vertex credential startup
in memory, recording the adaptation; it creates no cloud credentials. Native
workflow and local-model compatibility still require subsequent validation.
`collect-preparation-v2.sh` archives preparation receipts, labeled CPU control
traces, frozen campaign source/protocol inputs and logs under a unique job ID.

The original resource mask was ineffective on Nibi because other GPU selectors
remained active. Its three affected attempts are quarantined in the immutable
v1 audit. Revision 2 uses `start-resource-fault-server.sh` to run real Ollama
inside contained Apptainer without GPU device nodes or `--nv`. A bounded H100
control must show the allocated GPU outside that container, real CPU residency
inside it, and rejection by the unchanged native GPU-residency guard before
`prepare-chatdev-v2.sh` can freeze and submit the amendment. Its Slurm dependency
is `afterok`, so failed controls cannot resume comparison automatically.

Revision 2 lives in `comparison/chatdev-v2/`; the original directory, source,
protocol and raw receipts remain unchanged. Fourteen qualified clean/environment
cases are carried forward with their original identities. All remaining cases
use distinct `-r2` identities, retaining original condition order, tasks, seeds,
native code, model configuration and oracles. Every amended resource case must
contain both an empty accelerator-device list and actual loaded-model records
with CPU backend logs and no GPU offload. This pinned server reports estimated
nonzero size_vram even on CPU; raw memory reports remain unchanged. The
coordinator stops again if physical fault evidence is missing. All
control, failed, quarantined and rerun allocations count against the existing
global and per-artifact budget guards.

The CPU-only empty warmup sets `num_batch=32` and `num_thread=4`; these options
bound initialization under the injected fault, with no generation permitted.
Default CPU warmup exceeded the first five-minute control's process limit; that
232-second H100 allocation and its logs remain charged and retained. Original
non-fault worker behavior, sampling and native task execution remain unchanged.
An intermediate batch-one CPU check hit a native runner assertion; its queued
H100 test was canceled before execution. Successful real CPU control evidence
and its hashes are required before admitting the next H100 control.

The Windows hourly task refreshes the project document from collected local
status/evidence and appends its last section. While working on Nibi, explicitly
collect current campaign observations into local `STATUS.json` so the hourly
report can display them. Its timestamp does not imply a live remote queue query.

## Prospective candidate staging allocation

The immutable master plan retains its original two-hour candidate staging limit.
The separately hashed `budget-allocations/20261026-chatdev-stage-2.json` records
the user-authorized continuation on 2026-10-26: ChatDev receives a cumulative
eight-hour admission ceiling, including all previous charges. Other candidates
retain their original ceiling. These maxima are not advance reservations; the
unchanged global 24 H100-hour guard always takes precedence.

`activate_budget_allocation.py` requires fresh successful Slurm accounting,
a fully reconciled ledger and the unchanged frozen master protocol. It writes
an exclusive active pointer and preserves the pre-activation ledger. Each new
reservation records the amendment identity and effective ceiling. Scientific
case order, source hashes, model settings and oracles remain frozen.
CPU 25045598 activated this amendment and submitted GPU 25045607 / collector
25045608. The activation archive is collected separately from episode results.

## Live audit and SWE-agent transport repair, 2026-10-28

The live Nibi audit found ChatDev's frozen subset resolved at 140/140 episodes
(five complete paired seed blocks), while the local collection still showed 57.
The remaining 83 revision-2 archives have been collected. All 155 campaign archive
checksums verify; all 140 qualified receipts match episode/job/outcome identities,
all 35 corrected resource-fault cases establish physical CPU isolation, and
parent-allocation accounting matches the settled ledger. Historical quarantined
attempts remain excluded. Completion of this subset does not complete the other
eleven artifact comparisons or the 1,680-episode campaign.

SWE-agent's earlier HTTP 400 failure was reproduced against the pinned real
Ollama server: native cache processing wraps content in text blocks, whereas
`/api/chat` requires string content. The original transport and frozen failed
validation plan are preserved. `sweagent_transport_v2.py` converts only text
blocks to their exact concatenated string and rejects unsupported content.
`check_sweagent_request_v2.py` demonstrates the original decoding failure and
corrected schema using a nonexistent model in an empty model directory; it
performs no model inference. The complete native CPU fixture also checks the
outgoing content schema and must repair, review, submit, and pass its oracle.

CPU preflight 25176140 passed both real-server schema and native fixture checks,
then froze a separate revision-2 plan and reserved 1,260 H100 seconds before
submitting GPU validation 25176198 and dependent collector 25176199. This is
native feasibility, with no comparative completion inferred from submission.
Previous costs and the existing global/per-artifact budget limits remain active.

RepairAgent CPU job 25176216 tests a new isolated environment with explicit
compatibility constraints for the legacy LangChain/Pydantic imports, retaining
its upstream requirements and the two earlier failures. Dependency/import
success alone does not establish native or comparative eligibility. MetaGPT's
pinned `lancedb==0.4.0` remains unavailable in its earlier installation attempt;
changing that pinned dependency needs a separately recorded compatibility
validation. Other artifact-specific comparative adapters remain pending.

RepairAgent's first constrained CPU attempt (25176216) exposed a conflict with
the original `orjson==3.8.10` pin and was stopped with an explicit abort audit.
The separate revision-4 constraints and CPU job 25176490 select compatible older
LangChain/LangSmith metadata without changing that upstream pin. Audit collector
25176545 waits for that CPU attempt and SWE-agent collector 25176199, preserves
both success and failure evidence, and refreshes accounting. These jobs must
finish and their receipts be inspected before any successful workflow is claimed.

SWE-agent revision-2 GPU 25176198 subsequently **PASSED**: 22 real model calls,
a native submitted syntax repair, and the independent oracle passed. Slurm
reports 149 H100 seconds and exit 0; collector 25176199 also completed. The
collected archive is verified locally. Campaign GPU charges are 24,752 seconds,
none reserved. Native validation is separate from comparative execution, so
the completed comparative count remains 140/1,680.

RepairAgent CPU 25176490 subsequently reached its installation process timeout.
CPU continuation 25177827 recorded the prior partial inventory/receipt identity,
resumed that unfrozen preparation environment without bytecode compilation,
and passed installation, package consistency and native application/repair-module
imports. It made zero model calls; native task execution remains pending. Final
audit collector 25177882 completed and its archive is verified locally. The final
live queue was empty; 158 campaign archives verify. MetaGPT's pinned dependency
and the remaining native comparative adapters are still unresolved campaign work.
