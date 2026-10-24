"""Archive primary arXiv citation metadata for the purposive candidate set."""
import concurrent.futures
import json
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = {}
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta" and attrs.get("name", "").startswith("citation_"):
            self.values.setdefault(attrs["name"], []).append(attrs.get("content", ""))


def fetch(row):
    parser = Metadata()
    with urllib.request.urlopen(urllib.request.Request(row["paper"], headers={"User-Agent": "RES-AI research artifact"}), timeout=30) as r:
        parser.feed(r.read().decode())
    return {"name": row["name"], "source": row["paper"], "metadata": parser.values}


if __name__ == "__main__":
    subjects = json.loads((ROOT/"experiments/subjects.json").read_text())["subjects"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(fetch, subjects))
    (ROOT/"experiments/papers.json").write_text(json.dumps(records, indent=2)+"\n")
    entries = []
    for i, row in enumerate(records, 1):
        meta = row["metadata"]
        title = meta["citation_title"][0].replace("&", r"\&")
        authors = " and ".join(meta["citation_author"])
        year = meta.get("citation_date", meta.get("citation_publication_date", ["2024"]))[0][:4]
        entries.append(f"@misc{{resaiartifact{i},\n  author = {{{authors}}},\n  title = {{{{{title}}}}},\n  year = {{{year}}},\n  howpublished = {{\\url{{{row['source']}}}}}\n}}\n")
    (ROOT/"docs/EMSE/generated/artifact_refs.bib").write_text("\n".join(entries), encoding="utf-8")
    print(f"Archived primary metadata for {len(records)} papers.")
