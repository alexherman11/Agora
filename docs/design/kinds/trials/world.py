"""Load a kernel world log (a copy) into {thing: {aspect: value}}, plus the records. Read-only."""
import json, collections, re, sys
def load(path):
    st, recs = collections.defaultdict(dict), []
    for line in open(path, encoding="utf-8"):
        if not line.strip(): continue
        r = json.loads(line); recs.append(r)
        for p in r.get("parts", []):
            for f in p.get("facts", []):
                if len(f) > 3: st[f[0]][f[1]] = f[3]
    live = {t: a for t, a in st.items() if a.get("kind") and not a.get("forgotten")}
    return live, recs
fam = lambda k: re.split(r"[:.]", k)[0]
BOOK = {"kind", "made_by", "in", "for", "via_actor", "visibility_of", "by", "sees"}
INFRA = {"word", "grant", "component", "module", "widget", "button", "kind", "topic"}
PATH = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\Alex\AppData\Local\Temp\claude\C--Projects-Agora4\45efab53-5a79-437b-8a53-7bdb042688d7\scratchpad\dk.jsonl"
