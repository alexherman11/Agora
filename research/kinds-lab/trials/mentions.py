import json, collections, re, sys
st = collections.defaultdict(dict)
for line in open(sys.argv[1], encoding="utf-8"):
    if not line.strip(): continue
    r = json.loads(line)
    for p in r.get("parts", []):
        for f in p.get("facts", []):
            if len(f) > 3: st[f[0]][f[1]] = f[3]
live = {t:a for t,a in st.items() if a.get("kind") and not a.get("forgotten")}
SKIP = ("word","grant","component","module","widget","button","kind")
cont = [t for t,a in live.items() if a["kind"] not in SKIP]
names = {}
for t,a in live.items():
    if a["kind"] in ("word","grant"): continue
    for f in ("name","title","label"):
        v = str(a.get(f,"")).strip()
        if len(v)>=5 and not v.startswith("dk"): names.setdefault(v.casefold(), set()).add(t)
ID = re.compile(r"\b(dk\d+|a\d{3,6})\b")
idm=collections.Counter(); nm=collections.Counter(); oldref=0; gained=set()
for t in cont:
    txt = " ".join(str(v) for k,v in live[t].items() if k in ("text","note","about","title","body","short"))
    low = txt.casefold()
    for i in ID.findall(txt):
        if i.startswith("a"): oldref+=1
        elif i in live and i!=t: idm[t]+=1; gained.add(t)
    for nmv, ts in names.items():
        if nmv in low and t not in ts: nm[t]+=1; gained.add(t)
print("content things", len(cont))
print("with an id mention of a live thing", len(idm), "| old-desk ids mentioned", oldref)
print("with a name mention of another thing", len(nm))
print("gain at least one implicit edge", len(gained))
lanes = collections.Counter(a.get("lane") for a in live.values() if a["kind"]=="taskboard-task")
print("task lanes held as text:", dict(lanes))
