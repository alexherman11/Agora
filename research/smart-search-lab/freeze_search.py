"""Freeze only, no tests/inference/temp directories. Never reads held-out cases."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research/kernel-lab/modules/model"))
import smart_search as S

corpus = json.loads((HERE / "development-corpus.json").read_text(encoding="utf-8"))
assert len(corpus) == 36 and len({r["id"] for r in corpus}) == 36
records = S.descriptors(corpus)
template = S.prompt("QUERY_PLACEHOLDER", records)
paths = [
    "research/smart-search-lab/development-corpus.json",
    "research/kernel-lab/modules/model/smart_search.py",
    "research/kernel-lab/modules/model/search_time.py",
    "research/kernel-lab/modules/model/model.py",
    "research/kernel-lab/apps/smart-search/search.js",
    "research/kernel-lab/apps/smart-search/search.lens",
]
manifest = dict(version=S.VERSION, records=len(records), time_reference="2026-11-02T20:00:00+00:00",
                sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
                prompt_template_sha256=hashlib.sha256(template.encode("utf-8")).hexdigest(),
                evaluation="Independent author must hold blind queries/labels; builder must not tune on failures.",
                transport="Full slice requires reviewed model.search in broker. Existing model.ask truncates questions at 2000 characters and output at 96 tokens; smaller probes are transport-limited smoke checks only.")
out = HERE / "freeze-manifest.json"
if out.exists():
    raise SystemExit("Already frozen; never overwrite a freeze")
out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(manifest, indent=2))
