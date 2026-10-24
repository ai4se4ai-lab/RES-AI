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

The Windows hourly task refreshes the project document from collected local
status/evidence and appends its last section. While working on Nibi, explicitly
collect current campaign observations into local `STATUS.json` so the hourly
report can display them. Its timestamp does not imply a live remote queue query.
