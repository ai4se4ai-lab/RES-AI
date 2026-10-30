"""Read and verify archived manuscript evidence without bloating its TeX source."""
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / 'docs/EMSE'
STAGING = ROOT / 'tmp/manuscript-generated'


def read_embedded_assets(source):
    assets = {}
    pattern = r'^% RESAI_ASSET_BEGIN (\S+) (\d+) ([0-9a-f]{64})\n(.*?)^% RESAI_ASSET_END$'
    for name, length, digest, payload in re.findall(pattern, source, re.M | re.S):
        assert name not in assets
        data = bytes.fromhex(''.join(line.removeprefix('% ') for line in payload.splitlines()))
        assert len(data) == int(length) and hashlib.sha256(data).hexdigest() == digest, name
        assets[name] = data
    return assets


def embedded_sources():
    # Retain support for the former standalone format, but prefer the compact
    # project's separate evidence archive. It is excluded from the Overleaf ZIP.
    archive = PAPER / 'support/MANUSCRIPT_DATA.zip'
    if archive.exists():
        with zipfile.ZipFile(archive) as stream:
            assets = {name: stream.read(name) for name in stream.namelist()}
    else:
        assets = read_embedded_assets((PAPER / 'main.tex').read_text(encoding='utf-8'))
    manifest = json.loads(assets['resai-data-manifest.json'])
    for row in manifest['assets']:
        assert hashlib.sha256(assets[row['name']]).hexdigest() == row['sha256'], row['name']
    return {row['origin']: assets[row['name']] for row in manifest['assets']}


def read_paper_source(relative):
    """Return an archived historical input without recreating obsolete folders."""
    current = (PAPER / relative).resolve()
    assert current.is_relative_to(PAPER.resolve())
    if current.is_file():
        return current.read_text(encoding='utf-8')
    origin = 'docs/EMSE/' + relative
    return embedded_sources()[origin].decode('utf-8')
