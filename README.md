# RES-AI

RES-AI is an evidence-bound readiness prototype for experiments on shared Slurm
clusters. It builds on the pinned [use-hpc execution templates](https://github.com/ai4se4ai-lab/use-hpc).

The current review milestone is **one research-artifact pilot**, following a
controller study and a small CUDA integration check. Expansion to twelve artifacts
requires the author's review of this milestone.

- `src/resai/`: readiness policy, discovery, refinement proposal, dispatch wrapper,
  and restricted MCP stdio server.
- `hpc/`: original integration-pilot pipeline; `hpc/mapcoder/`: isolated MapCoder
  pilot pipeline. Both reuse upstream execution/audit code.
- `experiments/`: raw results, generation/analysis scripts, provenance and candidate inventory.
- `docs/EMSE/main.tex`: Springer manuscript, with approach/evaluation/discussion inputs.
- `docs/EMSE/main.pdf`: compiled review draft. It distinguishes observations from
  the prospective twelve-artifact protocol.

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
The review-milestone restrictions below describe the earlier pilot boundary;
the new authorization permits campaign preparation and execution within its cap.
Source feasibility is in progress; no comparative campaign outcome is asserted.

See [the operating guide](hpc/docs/hpc-guide.md) for exact run IDs, commands,
accounting boundaries, and claim-to-evidence mappings. Do not rerun the complete
prospective twelve-artifact campaign from this review milestone.

Production assessment is separate from smoke submission:

```bash
PYTHONPATH=src python -m resai.pipeline --hpc-dir hpc/mapcoder \
  --plan experiments/mapcoder/plan.json --evidence /path/to/collected/evidence.json
```

This performs a **dry run** after checking evidence, declared files, graph identity
and the supported resource mapping. Explicit `--submit` invokes the inherited
submitter. The review milestone does not authorize the twelve-artifact expansion.
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

The existing `sn-jnl.cls`, `sn-mathphys-num.bst` and `bibliography.bib` are retained.
Additional candidate-paper metadata is archived and generated from primary arXiv
records. The supplied support manuscript is context; its results are not reused
as new RES-AI observations.

The focused TSE/EMSE evaluation-design review is documented in
`experiments/PAPER_DESIGN_REVIEW.md`. New diagnostic tables, the grouped fault
heatmap and allocation/process line charts are regenerated from archived records;
the figure data and accounting boundaries are supplied alongside the artwork.
