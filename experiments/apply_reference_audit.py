"""Apply reviewed publisher metadata and documented primary-source overrides.

Stable citation keys are retained even when a publication year changes.
Crossref search candidates are never accepted on search rank alone.
"""
import copy
import html
import json
from pathlib import Path
import re
import bibtexparser
from bibtexparser.latexenc import string_to_latex
from manuscript_assets import read_paper_source, STAGING

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / 'docs/EMSE'
CACHE = ROOT / 'tmp/reference-audit'


def first(value):
    return value[0] if isinstance(value, list) and value else value if isinstance(value, str) else ''


def latex(value):
    return string_to_latex(html.unescape(str(value)))


def metadata(row):
    result = copy.deepcopy(row)
    kind = row.get('type')
    result['ENTRYTYPE'] = {'journal-article': 'article', 'proceedings-article': 'inproceedings',
                           'book': 'book', 'book-chapter': 'incollection'}.get(kind)
    assert result['ENTRYTYPE'], kind
    title = first(row.get('title'))
    subtitle = first(row.get('subtitle'))
    if subtitle:
        title += ': ' + subtitle
    entry = {'ENTRYTYPE': result['ENTRYTYPE'], 'title': '{' + latex(title) + '}',
             'doi': row['DOI'], 'url': 'https://doi.org/' + row['DOI']}
    authors = []
    for author in row.get('author', []):
        if author.get('name'):
            authors.append('{' + latex(author['name']) + '}')
        elif author.get('given') == 'The CWL':
            authors.append('{The CWL Community}')
        else:
            authors.append(latex(author.get('family', '')) + ', ' + latex(author.get('given', '')))
    if authors:
        entry['author'] = ' and '.join(authors)
    for field in ['published-print', 'published', 'issued', 'published-online']:
        if row.get(field, {}).get('date-parts'):
            entry['year'] = str(row[field]['date-parts'][0][0])
            break
    venue = first(row.get('container-title'))
    if venue:
        entry['journal' if entry['ENTRYTYPE'] == 'article' else 'booktitle'] = latex(venue)
    for src, dst in [('volume', 'volume'), ('issue', 'number'), ('page', 'pages'), ('publisher', 'publisher')]:
        if row.get(src):
            entry[dst] = latex(row[src])
    if 'pages' in entry:
        entry['pages'] = re.sub(r'(?<=\d)-(?=\d)', '--', entry['pages'])
    if not entry.get('pages') and row.get('article-number') and not row['DOI'].startswith('10.1145/'):
        entry['pages'] = str(row['article-number'])
    return entry


def page_authors(name):
    page = (CACHE / name).read_text(encoding='utf-8')
    authors = re.findall(r'<meta name="citation_author" content="([^"]+)"', page)
    assert authors
    return ' and '.join(latex(author) for author in authors)


def main():
    files = ['bibliography.bib', 'generated/artifact_refs.bib']
    databases = {name: bibtexparser.loads(read_paper_source(name)) for name in files}
    entries = {e['ID']: e for db in databases.values() for e in db.entries}
    originals = {key: json.loads((CACHE / (key + '.json')).read_text(encoding='utf-8'))['original']
                 for key in entries}
    decisions = {}
    manually_verified = {'vitek2011repeatability', 'wilkinson2016fair', 'stodden2016enhancing',
                         'resaiartifact8', 'resaiartifact12', 'wohlin2012experimentation', 'li2024ircoco'}
    # Explicit DOI relations with shortened publisher main titles are also valid.
    for key, entry in entries.items():
        record = json.loads((CACHE / (key + '.json')).read_text(encoding='utf-8'))
        candidates = sorted(record.get('candidates', []), key=lambda x: x['title_similarity'], reverse=True)
        if candidates and (candidates[0]['title_similarity'] > .95 or key in manually_verified
                           or (entry.get('doi') and candidates[0].get('DOI', '').lower() == entry['doi'].lower())):
            chosen = candidates[0]
            # Never mistake a same-title book chapter for the authored book.
            if key == 'wohlin2012experimentation':
                assert chosen['type'] == 'book' and chosen['DOI'] == '10.1007/978-3-642-29044-2'
            corrected = metadata(chosen)
            entry.clear()
            entry.update(ID=key, **corrected)
            decisions[key] = {'status': 'VERIFIED_PUBLISHER_METADATA', 'source': record['source'],
                              'doi': chosen['DOI']}
    # Conference-series metadata deposited via a proceedings distributor omits volume.
    for key, volume in [('yang2024sweagent', '37'), ('liu2023evalplus', '36'), ('hu2025repo2run', '38')]:
        entries[key]['volume'] = volume
        entries[key]['booktitle'] = 'Advances in Neural Information Processing Systems'
    entries['yoo2003slurm'].update(booktitle='Job Scheduling Strategies for Parallel Processing',
                                  series='Lecture Notes in Computer Science', volume='2862')
    entries['wohlin2012experimentation']['title'] = 'Experimentation in Software Engineering'

    def setentry(key, source, status='VERIFIED_PRIMARY_SOURCE', **fields):
        entries[key].clear()
        entries[key].update(ID=key, **fields)
        decisions[key] = {'status': status, 'source': source}

    def update(key, source, **fields):
        entries[key].update(fields)
        decisions[key] = {'status': 'VERIFIED_PRIMARY_SOURCE', 'source': source}

    for key, filename in [('bogin2024super', 'acl-super.bib'), ('resaiartifact5', 'acl-chatdev.bib'),
                          ('resaiartifact7', 'acl-mapcoder.bib')]:
        fields = bibtexparser.loads((CACHE / filename).read_text(encoding='utf-8')).entries[0]
        fields.pop('ID')
        setentry(key, fields['url'], **fields)

    update('jimenez2024swebench', 'https://openreview.net/pdf?id=VTF8yNQM66',
           url='https://openreview.net/forum?id=VTF8yNQM66')
    update('pineau2021improving', 'https://www.jmlr.org/papers/v22/20-303.html',
           url='https://www.jmlr.org/papers/v22/20-303.html')
    for key, page, slug, year in [('wang2025openhands', 'iclr-openhands.html',
            '2025/hash/a4b6ad6b48850c0c331d1259fc66a69c-Abstract-Conference.html', '2025'),
            ('resaiartifact4', 'iclr-metagpt.html',
             '2024/hash/6507b115562bb0a305f1958ccc87355a-Abstract-Conference.html', '2024')]:
        source = 'https://proceedings.iclr.cc/paper_files/paper/' + slug
        title = originals[key]['title']
        setentry(key, source, ENTRYTYPE='inproceedings', title=title, author=page_authors(page),
                 booktitle='International Conference on Learning Representations', year=year, url=source)
    for key, page, url, pages, volume, year in [
            ('huang2024mlagentbench', 'pmlr-mlagentbench.html', 'v235/huang24y.html', '20271--20309', '235', '2024'),
            ('starace2025paperbench', 'pmlr-paperbench.html', 'v267/starace25a.html', '56843--56873', '267', '2025'),
            ('resaiartifact10', 'pmlr-codeact.html', 'v235/wang24h.html', '50208--50232', '235', '2024')]:
        source = 'https://proceedings.mlr.press/' + url
        setentry(key, source, ENTRYTYPE='inproceedings', title=originals[key]['title'],
                 author=page_authors(page), booktitle='Proceedings of the ' + ('42nd' if year == '2025' else '41st')
                 + ' International Conference on Machine Learning', series='Proceedings of Machine Learning Research',
                 volume=volume, year=year, pages=pages, publisher='PMLR', url=source)
    setentry('siegel2024corebench', 'https://openreview.net/pdf?id=BsMMc4MEGS',
             ENTRYTYPE='article', title='{CORE-Bench}: Fostering the Credibility of Published Research Through a Computational Reproducibility Agent Benchmark',
             author=originals['siegel2024corebench']['author'], journal='Transactions on Machine Learning Research',
             year='2025', url='https://openreview.net/forum?id=BsMMc4MEGS')
    setentry('eliseeva2025envbench', 'https://github.com/JetBrains-Research/EnvBench',
             ENTRYTYPE='inproceedings', title='{EnvBench}: A Benchmark for Automated Environment Setup',
             author=originals['eliseeva2025envbench']['author'],
             booktitle='ICLR 2025 Third Workshop on Deep Learning for Code', year='2025',
             url='https://openreview.net/forum?id=izy1oaAOeX')
    # Authors report acceptance, but no version-of-record DOI/pages are available.
    accepted = originals['baltes2025guidelines'].copy()
    accepted.update(ENTRYTYPE='article', journal='Empirical Software Engineering', year='2026',
                    author=latex('Sebastian Baltes and Florian Angermeir and Chetan Arora and Marvin Muñoz Barón and Chunyang Chen and Lukas Böhme and Fabio Calefato and Neil Ernst and Davide Falessi and Brian Fitzgerald and Davide Fucci and Junda He and Christoph Treude and Marcos Kalinowski and Stefano Lambiase and Daniel Russo and Mircea Lungu and Cristina Martinez Montes and Lutz Prechelt and Paul Ralph and Rijnard van Tonder and Stefan Wagner'),
                    note='Accepted for publication; author preprint', url='https://arxiv.org/abs/2508.15503')
    accepted.pop('howpublished', None)
    accepted.pop('ID')
    setentry('baltes2025guidelines', 'https://llm-guidelines.org/', status='VERIFIED_ACCEPTED_FINAL_METADATA_PENDING', **accepted)
    for key, cache, arxiv in [('priem2022openalex', 'openalex-arxiv.html', '2205.01833'),
                              ('ralph2021standards', 'ralph-arxiv-page.html', '2010.03525'),
                              ('resaiartifact6', 'agentcoder-arxiv-page.html', '2312.13010'),
                              ('resaiartifact11', 'hyperagent-arxiv-page.html', '2409.16299')]:
        fields = originals[key].copy()
        fields.update(author=page_authors(cache), ENTRYTYPE='misc', howpublished='arXiv:' + arxiv,
                      url='https://arxiv.org/abs/' + arxiv)
        if key == 'ralph2021standards':
            fields['url'] += 'v2'
        fields.pop('ID')
        setentry(key, fields['url'], status='VERIFIED_PREPRINT_NO_PUBLISHED_VERSION_CONFIRMED', **fields)

    # Use the actual journal publication for both of ExecutionAgent's stable keys.
    for alias, canonical in [('resaiartifact1', 'yang2024sweagent'), ('resaiartifact2', 'wang2025openhands'),
                              ('bouzenia2025executionagent', 'resaiartifact9')]:
        fields = entries[canonical].copy()
        fields['ID'] = alias
        entries[alias].clear()
        entries[alias].update(fields)
        decisions[alias] = dict(decisions[canonical], alias_of=canonical)
    for key in ['anthropic2025skills', 'nvidia2023mig', 'usehpc2026repo', 'usehpc2026eval',
                'schedmdScheduling', 'mcp2024transport']:
        source = re.search(r'https?://[^}\s]+', entries[key]['howpublished'])[0]
        decisions[key] = {'status': 'VERIFIED_OFFICIAL_WEB_RESOURCE', 'source': source}
        entries[key]['note'] = 'Accessed 2026-10-30'
    entries['anthropic2025skills']['author'] = 'Barry Zhang and Keith Lazuka and Mahesh Murag'
    entries['nvidia2023mig']['year'] = '2026'
    for key in ['acm2020badges', 'alliance2026docs']:
        decisions[key] = {'status': 'ACCESS_LIMITED_OFFICIAL_RESOURCE',
                          'source': re.search(r'https?://[^}\s]+', entries[key]['howpublished'])[0],
                          'limitation': 'Official page blocked automated retrieval; content/version could not be freshly verified.'}
    assert set(entries) == set(decisions), sorted(set(entries) - set(decisions))
    report = []
    for key, entry in entries.items():
        delta = {k: {'before': originals[key].get(k), 'after': entry.get(k)}
                 for k in originals[key].keys() | entry.keys() if originals[key].get(k) != entry.get(k)}
        report.append(dict(key=key, **decisions[key], changes=delta, corrected_entry=entry))
    for name, db in databases.items():
        # Preserve the original inputs once for audit/reversal; do not replace later.
        backup = CACHE / (Path(name).name + '.before-audit')
        if not backup.exists():
            backup.write_text(read_paper_source(name), encoding='utf-8')
        db.comments = []
        writer = bibtexparser.bwriter.BibTexWriter()
        writer.order_entries_by = None
        writer.indent = '  '
        STAGING.mkdir(parents=True, exist_ok=True)
        (STAGING / Path(name).name).write_text('% Metadata audited 2026-10-30. Stable citation keys retained.\n'
                                  '% See support/REFERENCE_AUDIT.md for sources and remaining limitations.\n'
                                  + bibtexparser.dumps(db, writer), encoding='utf-8', newline='\n')
    (PAPER / 'support/REFERENCE_AUDIT.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    md = ['# Bibliography audit (2026-10-30 UTC)', '',
          f'Reviewed all {len(databases[files[0]].entries)} bibliography records and {len(databases[files[1]].entries)} artifact citation records. '
          'Verification concerns bibliographic identity and publication metadata, not an endorsement of paper findings. '
          'Search hits were candidates only; unmatched results were never substituted.', '',
          'Published venue versions replace preprints when a publisher/proceedings or official author record establishes the match. '
          'CORE-Bench is TMLR 2025; EnvBench is the ICLR 2025 Deep Learning for Code workshop; ExecutionAgent is PACMSE 2(ISSTA), 2025. '
          'MetaGPT and OpenHands use their published proceedings author lists. Missing authors, identifiers and pagination were corrected from publisher metadata. '
          'Stable keys can contain the former preprint year.', '',
          'The Baltes guidelines are accepted at EMSE according to the authors; no final DOI/pages were verified, so the record explicitly retains an author-preprint link. '
          'OpenAlex, AgentCoder, HyperAgent and the version-2 empirical standards retain preprint records: no published replacement was established. '
          'An ICLR submission alone is not proof of publication. The HyperAgent repository contains a conflicting arXiv identifier, so arXiv metadata takes precedence.', '',
          '**Remaining limits:** the ACM badging page and Alliance documentation site block automated access. '
          'Their existing official-resource records are retained and marked access-limited, not certified as freshly verified. '
          'No unmatched scholarly record was labeled verified, and no record was declared fabricated merely because a service blocked retrieval.', '',
          '| Key | Disposition | Primary / deposited metadata source | Changed fields |', '|---|---|---|---|']
    for row in report:
        md.append('| `' + row['key'] + '` | ' + row['status'] + ' | [source](' + row['source'] + ') | '
                  + ', '.join(sorted(row['changes'])) + ' |')
    (PAPER / 'support/REFERENCE_AUDIT.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print(f'Audited {len(report)} records; {sum(bool(r["changes"]) for r in report)} updated; two official web resources remain access-limited.')


if __name__ == '__main__':
    main()
