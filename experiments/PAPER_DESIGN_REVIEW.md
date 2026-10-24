# Evaluation and figure design review

Reviewed on 24 October 2026. This is a focused design review, not a systematic
literature review or evidence of RES-AI effectiveness. Author manuscripts can
differ from published versions. No figure or numerical result is copied.

## TSE: Anchor Attention, Small Cache (2025)

Xiangyu Zhang et al., *Anchor Attention, Small Cache: Code Generation With Large
Language Models*, IEEE Transactions on Software Engineering 51(6), 2025.
[DOI](https://doi.org/10.1109/TSE.2025.3570680),
[author-hosted published PDF](https://chentaolue.github.io/pub-papers/tse25.pdf).

Inspected experimental design (Section IV), RQ-organized results (Section V),
resource and ablation Tables IV–V, attention heatmaps (Figure 9), and architecture.
The important pattern is joint reporting of quality, cost, and component effects,
with metric-specific units. For RES-AI, separate allocated instance time from
timed probe computation and display blocking reasons alongside aggregate counts.
An attention heatmap does not justify a heatmap of arbitrary unrelated metrics.

## TSE: Chain-of-Thought in Neural Code Generation (2024)

Guang Yang et al., *Chain-of-Thought in Neural Code Generation: From and for
Lightweight Language Models*, TSE, DOI 10.1109/TSE.2024.3440503.
[Author manuscript](https://chentaolue.github.io/pub-papers/tse24.pdf).
The manuscript's template header is stale; venue/year identity follows the DOI,
not its placeholder “2015” header.

Inspected Section 4, especially dataset Table 1, metrics Section 4.3,
Implementation Details and Running Platform Section 4.4, and the multi-stage
architecture. This motivates a dedicated implementation subsection and a separate
setup subsection, plus clearly identified data objects and internal modules in
the RES-AI architecture. Software pins and platform settings belong with evaluation
reproducibility, rather than interrupting the conceptual approach.

## EMSE: Bugs in large language models generated code (2025)

Florian Tambon et al., EMSE 30, article 65, 2025.
[Publisher record](https://doi.org/10.1007/s10664-025-10614-4),
[author preprint](https://arxiv.org/pdf/2403.08937).

Inspected study-design Section 3 and diagnostic results, including the preprint's
Figure 3 and Table 3. The task-by-bug-pattern heatmap has an explicit normalization
and is interpreted alongside examples and dependency strata. Its preprint and
published sample/survey totals differ; none are imported into our manuscript.
For RES-AI, show exact per-family blocked-case denominators, group faults by
contract concern, and explain the mechanism behind each difference. Do not treat
synthetic variants as independent artifacts.

## EMSE: PROBE (online 2026; assigned to volume 32, 2027)

Rodrigo Pato Nogueira, Marco Vieira, João R. Campos, *PROBE: Benchmarking code
generation in large language models*.
[Publisher full text](https://link.springer.com/article/10.1007/s10664-026-10904-5).

Inspected Experimental Setup Section 4, Experimental Settings Table 1,
dimension-organized Section 5, Figure 2, and error analysis. The line chart varies
an ordered quantity (sample count); setup records workload/model choices and their
limitations. For RES-AI, use an allocation-time curve and a cumulative process-time
curve over the actual probe sequence. Do not draw a convergence curve from two
repeats or suggest that fabricated benchmark outcomes have been measured.

## Changes applied

- Dedicated implementation and experimental-setup subsections.
- RQ-to-evidence table, configuration table, explicit threshold table.
- Contract-domain heatmap with counts and consistent color scale.
- Two-panel allocation/process timeline from sacct and raw CUDA observations.
- Per-mode diagnostic table with both repetitions, coverage and blocking reasons.
- Hierarchical architecture with nested modules, data objects, control boundary,
  and explicit ready/blocked/refinement paths.

All quantitative displays are regenerated from archived records; prospective
campaign evidence remains clearly marked as not executed.
