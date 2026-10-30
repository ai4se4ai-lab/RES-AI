RES-AI Overleaf project
=======================

Upload RES-AI-Overleaf.zip using Overleaf: New Project > Upload Project.
Main document: main.tex
Compiler: pdfLaTeX

The project contains main.tex, bibliography.bib, sn-jnl.cls,
sn-mathphys-num.bst and five figure PDFs in figures/.
Text, tables and the architecture diagram are inline in main.tex.
Edit references in bibliography.bib. Overleaf runs BibTeX automatically.
For a local build: pdflatex main; bibtex main; pdflatex main; pdflatex main.
No LuaLaTeX, shell escape or research datasets are required.

Research datasets and the reference-audit report remain in the repository's
support/ directory; they are deliberately excluded from this upload package.
