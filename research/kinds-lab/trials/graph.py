import json, collections, re, sys
st = collections.defaultdict(dict)
for line in open(sys.argv[1], encoding="utf-8"):
    if not line.strip(): continue
    r = json.loads(line)
    for p in r.get("parts", []):
        for f in p.get("facts", []):
            if len(f) > 3: st[f[0]][f[1]] = f[3]
live = {t:a for t,a in st.items() if a.get("kind") and not a.get("forgotten")}
ID = re.compile(r"\bdk\d+\b")
edges = collections.Counter(); out = collections.defaultdict(set); inn = collections.defaultdict(set)
for t,a in live.items():
    for k,v in a.items():
        ids = set(ID.findall(k)) | (set(ID.findall(v)) if isinstance(v,str) and len(v)<200 else set())
        for i in ids:
            if i in live and i!=t:
                lab = re.split(r"[:.]", k)[0]
                edges[lab]+=1; out[t].add(i); inn[i].add(t)
print("edge labels", edges.most_common(30))
# structural-only edges (made_by, in, for, by) vs meaning edges
struct = {"made_by","in","for","to","by","via_actor","visibility_of","lives","bound","where"}
mean = collections.defaultdict(set)
for t,a in live.items():
    for k,v in a.items():
        lab = re.split(r"[:.]", k)[0]
        if lab in struct: continue
        ids = set(ID.findall(k)) | (set(ID.findall(v)) if isinstance(v,str) and len(v)<200 else set())
        for i in ids:
            if i in live and i!=t: mean[t].add(i); mean[i].add(t)
cont = [t for t,a in live.items() if a["kind"] not in ("word","grant","topic","component","kind","module","widget","button")]
print("content-ish things", len(cont), "with no meaning edge", sum(1 for t in cont if not mean[t]))
print("by kind with no meaning edge", collections.Counter(live[t]["kind"] for t in cont if not mean[t]).most_common(20))
for kd in ("post","note","document","said","map-layer","window","chat","ask-request","taskboard-task"):
    ex = [t for t,a in live.items() if a["kind"]==kd][:2]
    for t in ex: print(kd, t, {k:str(v)[:60] for k,v in live[t].items()})
