"""P2. How connected is the desktop world's content, edge source by edge source? Components of a graph over content things."""
import collections, re
from world import load, fam, INFRA, PATH
live, recs = load(PATH)
ID = re.compile(r"\bdk\d+\b")
WHO = {"made_by", "for", "via_actor", "by", "visibility_of", "sees", "in", "to", "member", "where", "lives"}
content = {t for t, a in live.items() if a["kind"] not in INFRA and t != "world"}
names = collections.defaultdict(set)
for t, a in live.items():
    if a["kind"] in ("word", "grant"): continue
    for f in ("name", "title", "label"):
        v = str(a.get(f, "")).strip()
        if v: names[v.casefold()].add(t)
def comps(edges):
    parent = {t: t for t in content}
    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for a, b in edges:
        if a in content and b in content: parent[find(a)] = find(b)
    c = collections.Counter(find(t) for t in content)
    return len(c), sum(1 for v in c.values() if v == 1), max(c.values())
E = {}
# 1 explicit links that say what a thing is about (not who made it or where it sits)
E["links"] = [(t, i) for t, a in live.items() for k, v in a.items() if fam(k) not in WHO and fam(k) != "kind"
              for i in (set(ID.findall(k)) | (set(ID.findall(v)) if isinstance(v, str) and len(v) < 300 else set())) if i in live and i != t]
# 2 name-valued aspects: a short value equal to another thing's name (lane=Now)
E["named values"] = [(t, o) for t, a in live.items() for k, v in a.items() if fam(k) not in ("name", "title", "label", "kind", "text")
                     and isinstance(v, str) and 2 < len(v) < 40 for o in names.get(v.casefold(), ()) if o != t]
# 3 id mentions in long text
E["id mentions"] = [(t, i) for t, a in live.items() for k, v in a.items() if isinstance(v, str) and len(v) >= 300
                    for i in set(ID.findall(v)) if i in live and i != t]
# 4 acts: things touched together in one record (more than one content thing, fewer than 6, so bulk acts don't glue everything)
acts = []
for r in recs:
    ts = sorted({f[0] for p in r.get("parts", []) for f in p.get("facts", []) if f[0] in content})
    if 1 < len(ts) < 6: acts += [(ts[0], x) for x in ts[1:]]
E["same act"] = acts
# 5 shelf: same kind (what a flat kind gives you)
first = {}
E["same kind"] = []
for t in sorted(content):
    k = live[t]["kind"]
    if k in first: E["same kind"].append((first[k], t))
    else: first[k] = t
print(f"content things: {len(content)} (kinds not counted as content: {sorted(INFRA)})")
for k, v in E.items(): print(f"  edges from {k}: {len(v)}")
acc = []
print("components, isolated, largest:")
print("  nothing", comps([]))
for k in ["links", "named values", "id mentions", "same act"]:
    acc += E[k]; print(f"  + {k}", comps(acc))
print("  + same kind (flat shelves)", comps(acc + E["same kind"]))
iso_after_links = comps(E["links"])
