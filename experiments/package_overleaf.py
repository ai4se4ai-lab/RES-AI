"""Package only the compact manuscript and its required Overleaf source assets."""
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / 'docs/EMSE'


def main():
    source = (PAPER / 'main.tex').read_text(encoding='utf-8')
    assert '\\directlua' not in source and 'RESAI_ASSET_BEGIN' not in source
    assert not re.search(r'\\input\{', source)
    assert re.findall(r'\\bibliography\{([^}]+)\}', source) == ['bibliography']
    figures = re.findall(r'\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}', source)
    files = ['main.tex', 'bibliography.bib', 'sn-jnl.cls', 'sn-mathphys-num.bst', 'OVERLEAF_README.txt'] + list(dict.fromkeys(figures))
    for name in files:
        path = (PAPER / name).resolve()
        assert path.is_relative_to(PAPER.resolve()) and path.is_file(), name
    destination = PAPER / 'RES-AI-Overleaf.zip'
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in files:
            archive.write(PAPER / name, name)
    print(f'Packaged {len(files)} source files; {destination.stat().st_size:,} bytes: {destination}')


if __name__ == '__main__':
    main()
