# Compact Overleaf manuscript

Upload `../RES-AI-Overleaf.zip` as a new Overleaf project. Set the main document to
`main.tex` and the compiler to **pdfLaTeX**. Upload the ZIP, rather than main.tex alone.
For a local build from `docs/EMSE`: `pdflatex main; bibtex main; pdflatex main; pdflatex main`. Overleaf runs BibTeX automatically.

The project contains:

- `main.tex`: all manuscript text, tables and the TikZ architecture diagram.
- `bibliography.bib`: all 82 audited reference records, including artifact citations.
- `sn-mathphys-num.bst`: the journal bibliography style; missing optional locations are omitted.
- `sn-jnl.cls`: the original journal class.
- `figures/`: the five exact figure PDFs used by the manuscript.
- `OVERLEAF_README.txt`: short build instructions.

The manuscript is approximately 130 KB (previously 4 MB). No hexadecimal payloads,
Lua decoder, shell escape or research datasets are needed for compilation.
Sections and tables remain inline; the former `generated/` and `sections/` folders
are unnecessary. Edit `bibliography.bib` to change references; citation keys remain unchanged.
After editing, regenerate the upload ZIP with `python experiments/package_overleaf.py`.

The previous embedded evidence is preserved in `MANUSCRIPT_DATA.zip`, with its
original manifest and SHA-256 identities. The archive contains complete audited
bibliography databases, analysis datasets, pilot evidence/accounting and qualified
ChatDev receipts. `experiments/manuscript_assets.py` reads these archived records.
The archive and other support documents are excluded from the Overleaf project.
Full raw model-call bundles and model weights remain separate research artifacts.

Validation on 2026-10-30: extracted the ten-file upload ZIP into an empty directory
and completed pdfLaTeX, BibTeX and two further pdfLaTeX passes. The result has 38 pages, no undefined references
or overflowing boxes, and no missing-location placeholders. The title, figure,
ChatDev table and reference pages were visually checked. The claim audit verifies
1,040 controller decisions, 33 citation keys, input figures and GPU curves. See
`REFERENCE_AUDIT.md` for all 82 reference decisions and the two access-limited
external documentation sources.
