# AI-assisted critical review and revisions

Three AI reviewers examined empirical methods, architecture, and literature. They
provided methodological critique rather than independent human peer review.

| Concern | Revision |
|---|---|
| Plausible numbers requested in support notes | Report only executed measurements; mark the twelve-artifact campaign prospective |
| Synthetic seeds mistaken for studies | Descriptive counts only; artifact-level analysis reserved for the campaign |
| Static-only comparator too weak | Distinguish the local modeled smoke proxy from the planned full upstream smoke comparator |
| Scope/priority exaggeration | Preserve unknown topology attributes; no autonomous priority or turnaround claim |
| Reordered evidence hiding new failure | Sort observations by timestamp and require unique attempt IDs |
| Refinement after exhaustion | Enforce attempt/compute limits in the proposal function |
| Graph differs from validated resource plan | Bind resolved graph and declarations; verify supported resource mapping; reject raw GPU-stage flags |
| Malformed policy values | Validate numeric types, finite telemetry and policy ranges |
| Incomplete GPU records | Require all four modes and both repeats before reporting completion |
| Unsupported accounting prose | Derive counts/timing from raw records and sacct, avoiding batch/extern double counting |
| Stale corpus/paper identities | Archive public revisions and primary citation metadata; retain paper-version caveats |
| Cached outputs appearing fresh | Use per-attempt output directories and require first-pass inference calls |
| Resume check only reused memory state | Reload persisted results into fresh strategy objects |
| Source identity asserted but unchecked at probe start | Verify declared files and graph before model execution |
| Windows CRLF changes Bash values | Normalize configurations and reject carriage returns/newlines in site variables |
| Failure penalties confused with actual cost | Retain actual allocation metrics separately from imputed capped endpoints |
| Weak equivalence null | Specify non-equivalence null and two one-sided tests in the prospective protocol |

The final consistency review also checks generated tables/figures against raw
records. All strong generality, production-scale reliability and compute-saving
claims remain unestablished at this milestone. The author requested a stop for
review after the one-artifact pilot, before expansion to twelve artifacts.

On 24 October 2026, a focused design review of two TSE and two EMSE papers
informed the evaluation reorganization and figure redesign; sources and limits
are recorded in PAPER_DESIGN_REVIEW.md and presentation_review_sources.json.
Implementation details are consolidated in Evaluation, separate from experimental
setup. Diagnostic tables and a grouped heatmap retain all raw denominators.
The new line charts reconstruct allocated MIG-instance time and cumulative timed
probe computation, with different accounting boundaries explicitly marked.
They do not estimate savings, convergence or cross-artifact effectiveness.
