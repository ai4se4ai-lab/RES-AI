"""Collect publisher-deposited Crossref metadata; candidates require human review."""
import concurrent.futures
import difflib
import json
from pathlib import Path
import re
import unicodedata
import urllib.parse
import urllib.request
import bibtexparser
from manuscript_assets import read_paper_source

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tmp/reference-audit"


def normal(value):
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", value).lower())


def fetch(entry):
    key = entry['ID']
    path = OUT / (key + '.json')
    if path.exists():
        cached = json.loads(path.read_text(encoding='utf-8'))
        if not cached.get('error'):
            return cached
    result = {'key': key, 'original': entry}
    title = entry.get('title', '')
    try:
        if entry.get('doi'):
            url = 'https://api.crossref.org/works/' + urllib.parse.quote(entry['doi'], safe='/')
        else:
            url = 'https://api.crossref.org/works?' + urllib.parse.urlencode({'query.bibliographic': re.sub(r'[{}\\]', '', title), 'rows': 3})
        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
        with urllib.request.urlopen(request, timeout=40) as response:
            message = json.load(response)['message']
        candidates = message['items'] if 'items' in message else [message]
        for item in candidates:
            item.pop('abstract', None)
            item['title_similarity'] = difflib.SequenceMatcher(None, normal(title), normal(item.get('title', [''])[0])).ratio()
        result.update(source=url, candidates=candidates)
    except Exception as exc:
        result['error'] = str(exc)
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    entries = []
    for name in ['bibliography.bib', 'generated/artifact_refs.bib']:
        entries += bibtexparser.loads(read_paper_source(name)).entries
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(fetch, entries))
    for row in results:
        candidates = sorted(row.get('candidates', []), key=lambda x: x['title_similarity'], reverse=True)
        if not candidates:
            print(row['key'], row.get('error', 'NO MATCH'))
            continue
        best = candidates[0]
        print(row['key'], round(best['title_similarity'], 3), best.get('DOI'),
              best.get('title'), best.get('container-title'), best.get('published'))
