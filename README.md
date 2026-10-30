# RES-AI

RES-AI is an evidence-bound readiness prototype for experiments on shared Slurm
clusters. It builds on the pinned [use-hpc execution templates](https://github.com/ai4se4ai-lab/use-hpc).

The controller study, CUDA integration pilot, two-model MapCoder deployment pilot
and **140-case ChatDev comparative subset are complete**. The authorized
twelve-artifact campaign remains incomplete: **140/1,680 potential episodes** are
resolved, and the other eleven artifact comparisons have not started.

These results reflect the latest collected Nibi report, **2026-10-28 04:38 UTC**.
The live SSH check on 2026-10-30 failed authentication; current queue state and any
subsequent progress are unverified. The
[execution plan and status history](docs/EMSE/support/AI_AGENT_PROJECT_EXECUTION_PLAN.md)
is the project status entry point.

- `src/resai/`: readiness policy, discovery, refinement proposal, dispatch wrapper,
  and restricted MCP stdio server.
- `hpc/`: original integration-pilot pipeline; `hpc/mapcoder/`: isolated MapCoder
  pilot pipeline. Both reuse upstream execution/audit code.
- `experiments/`: raw results, generation/analysis scripts, provenance and candidate inventory.
- `docs/EMSE/main.tex`: manuscript with inline sections, tables and architecture diagram;
  references are maintained in `docs/EMSE/bibliography.bib`.
- `docs/EMSE/main.pdf`: compiled review draft incorporating the completed ChatDev
  subset and distinguishing it from the unfinished cross-artifact campaign.

## Collected experiment results

| Study | Verified result | Scope |
|---|---|---|
| Controller conformance | 1,040 synthetic decisions across 20 variants and 12 fault families; full policy blocks all 240 faulty variants and admits all 20 clean controls | Constructed inputs, not natural failure rates |
| CUDA integration | Eight records across four modes and two repeats; clean pair admitted and all three injected fault modes blocked | Small synthetic workload on Nibi |
| MapCoder / Qwen2.5-Coder-7B | 2/2 HumanEval/0 repeats solved; 16 model calls; collection-time readiness gate passed | One task under a local-model adaptation |
| MapCoder / quantized Qwen3.8-27B | 2/2 HumanEval/0 repeats solved; 16 model calls; collection-time readiness gate passed | Separate scientific configuration; failed identity-check attempt retained |
| ChatDev comparison | 140/140 required cases resolved across seven conditions, five paired task/seed blocks and four episode classes | One completed artifact comparison |
| Full campaign | 140/1,680 potential episodes resolved; eleven comparisons not started | Cross-artifact analysis remains pending |

The completed ChatDev subset contains 34 valid production outcomes, 61 policy
blocks and 45 invalid production outcomes. Completion means every required case
has a qualified resolved outcome; it does not mean every generated program passed.

| ChatDev condition | Clean production valid / 5 | Injected faults blocked / 15 | Invalid production under injected faults / 15 |
|---|---|---|---|
| Direct native | 5 | 0 | 15 |
| Upstream static | 5 | 0 | 15 |
| Upstream smoke-then-production | 5 | 10 | 5 |
| Full RES-AI | 5 | 15 | 0 |
| No coverage | 5 | 10 | 5 |
| No identity/freshness | 5 | 10 | 5 |
| No refinement | 4 | 15 | 0 |

The remaining no-refinement clean case was blocked after an HTTP 500 setup failure
with zero completed model calls. This is not evidence of a refinement benefit:
the adapter declares batch invariance false and permits no operational refinement.
Tasks and paired seeds vary together; these are descriptive results from one artifact.

All 35 corrected resource-fault cases have verified physical CPU-isolation evidence.
Three historical attempts with ineffective fault injection remain quarantined and
excluded from qualified outcomes. Revision 2 carries forward 14 qualified cases
and adds 126 amended cases. All 158 collected campaign archives passed checksum
verification at the recorded audit.

Campaign accounting records **24,752 H100 allocation-seconds (6h52m32s)** and no
outstanding reservations at the latest report, within the initial 24-hour cap.
This total includes feasibility, controls, failures, quarantined attempts and
comparative execution; it is not ChatDev condition-level cost or measured savings.
Earlier pilot allocations have separate accounting boundaries. Cross-artifact
generality, semantic equivalence and comparative resource savings remain unestablished.

Native model/oracle validations passed for ChatDev, AgentCoder and SWE-agent.
All twelve source snapshots are acquired and six dependency import checks passed.
RepairAgent has passed dependency/import checks but still needs native task
validation; MetaGPT remains blocked by unavailable pinned `lancedb==0.4.0`.
Remaining adapters, native workflows and oracles must pass before their comparisons.

Evidence: [collection index](experiments/results/COLLECTION.md),
[campaign report](experiments/results/campaign/STATUS.json),
[ChatDev audit](experiments/results/campaign/live-check-20261028/verified-audit.json)
and [final recovery/accounting audit](experiments/results/campaign/live-check-20261028/issue-status.json).
Raw results under `experiments/results/` are ignored by Git and require separate
preservation. The manuscript data snapshot is also retained in
[`MANUSCRIPT_DATA.zip`](docs/EMSE/support/MANUSCRIPT_DATA.zip).

## Local checks

Python 3.11 or newer is required. The policy and MCP server use the standard
library; figure generation additionally needs matplotlib and numpy.

```powershell
$env:PYTHONPATH = 'src'
python -m unittest discover -s tests -v
python experiments/run_local.py
python experiments/run_analyses.py
python experiments/analyze_gpu.py --results experiments/results/nibi/results --out experiments/results/nibi/reanalysis
python experiments/make_paper_artifacts.py
python experiments/check_claims.py
```

The mutation study uses synthetic records and does not execute the twelve
candidate studies. Its smoke comparator is a modeled status/file-presence proxy.

## Agent interface

```powershell
$env:PYTHONPATH = 'src'
python -m resai.mcp
```

The server uses newline-delimited MCP 2024-11-05 JSON-RPC. Its tools are
`cluster_snapshot`, `assess_readiness`, and `propose_refinement`. Run it with the
repository as the working directory. Tools read workspace-scoped JSON files and
expose no shell or submission capability. This is a single-user prototype.

## Nibi

On 2026-10-24 the author requested the twelve-artifact campaign after Qwen3.8
paper integration, with an initial 24 H100 GPU-hour cap. See
[`experiments/campaign/`](experiments/campaign/README.md) and the current
[execution status](docs/EMSE/support/AI_AGENT_PROJECT_EXECUTION_PLAN.md).
This authorization covers campaign preparation and execution within the cap,
subject to per-artifact native validation and budget admission. ChatDev's separately
recorded staging amendment permits an eight-hour cumulative ceiling; other
candidates retain two-hour staging ceilings, and the global cap always dominates.

See [the operating guide](hpc/docs/hpc-guide.md) for exact run IDs, commands,
accounting boundaries, and claim-to-evidence mappings. For current completion and
remaining work, use the execution status above; the guide also retains historical
pilot observations. Preserve frozen protocols, failed attempts and accounting when
continuing the campaign.

Production assessment is separate from smoke submission:

```bash
PYTHONPATH=src python -m resai.pipeline --hpc-dir hpc/mapcoder \
  --plan experiments/mapcoder/plan.json --evidence /path/to/collected/evidence.json
```

This performs a **dry run** after checking evidence, declared files, graph identity
and the supported resource mapping. Explicit `--submit` invokes the inherited
submitter. The campaign's authorization, artifact-specific eligibility checks and
allocation-budget guards still govern each comparative submission.
The wrapper can be bypassed by invoking upstream directly and is not a scheduler
security boundary. Hashes bind declared inputs; they do not verify arbitrary
scientific semantics or prevent concurrent filesystem changes.

## Manuscript

```bash
cd docs/EMSE
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

`main.tex` contains the text, tables and architecture diagram. References are in
`bibliography.bib`, using `sn-mathphys-num.bst`. Five figure PDFs in `figures/` and
`sn-jnl.cls` complete the project assets. Upload `docs/EMSE/RES-AI-Overleaf.zip` as a new Overleaf project and select
pdfLaTeX; Overleaf runs BibTeX automatically. No Lua loader, shell escape or
network access is needed for local compilation.
Manuscript datasets are preserved separately in `support/MANUSCRIPT_DATA.zip`,
which is excluded from the Overleaf upload. The reference audit and build
instructions are in `docs/EMSE/support/`.
Generation scripts write review outputs to `tmp/manuscript-generated/`; they do not
overwrite the authoritative manuscript. The supplied support manuscript remains
context; its results are not reused as new RES-AI observations.

The focused TSE/EMSE evaluation-design review is documented in
`experiments/PAPER_DESIGN_REVIEW.md`. New diagnostic tables, the grouped fault
heatmap and allocation/process line charts are regenerated from archived records;
the figure data and accounting boundaries are supplied alongside the artwork.
