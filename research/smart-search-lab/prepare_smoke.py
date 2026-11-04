"""Prepare a small development probe for the existing model.ask transport.

No inference, source queries or held-out cases. This is not the 36-record gate.
"""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "research/kernel-lab/modules/model"))
import smart_search as S

corpus = json.loads((HERE / "development-corpus.json").read_text(encoding="utf-8"))
# Deliberately no key-word admission; a cloud distractor and an injection are present.
ids = {"ss1", "ss2", "ss5", "ss15", "ss23"}
records = S.descriptors([r for r in corpus if r["id"] in ids])
query = "cut the subject free but keep the pixels here"
prompt = S.prompt(query, records)
assert len(prompt) <= 2000, len(prompt)
out = dict(query=query, records=records, prompt=prompt,
           lexical_ids=[r["id"] for r in S.lexical(query, records)],
           expected="ss1", scope="Development transport smoke only; independent blind evaluation remains separate")
(HERE / "development-smoke.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
print(json.dumps(dict(prompt_characters=len(prompt), records=len(records), lexical_ids=out["lexical_ids"])))
