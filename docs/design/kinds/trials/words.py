import json, collections, re, sys
st = collections.defaultdict(dict)
for line in open(sys.argv[1], encoding="utf-8"):
    if not line.strip(): continue
    r = json.loads(line)
    for p in r.get("parts", []):
        for f in p.get("facts", []):
            if len(f) > 3: st[f[0]][f[1]] = f[3]
live = {t:a for t,a in st.items() if a.get("kind") and not a.get("forgotten")}
kinds = collections.Counter(a["kind"] for a in live.values())
ns = collections.Counter(); usek = collections.Counter(); generic=[]
for t,a in live.items():
    if a["kind"]!="word": continue
    w = str(a.get("word"))
    ns[w.rsplit(".",1)[0] if "." in w else "(plain)"] += 1
    first = (str(a.get("help") or "").splitlines() or [""])[0]
    m = re.search(r"<([a-z][a-z0-9-]*)", first)
    k = m.group(1) if m else "-"
    usek[k]+=1
    if k in ("id","thing"): generic.append(w)
print("namespaces", ns.most_common(40))
print("usage kinds", usek.most_common(40))
print("generic <id>/<thing> words:", " ".join(sorted(generic)))
print("plain words:", " ".join(sorted(str(a.get('word')) for a in live.values() if a['kind']=='word' and '.' not in str(a.get('word')))))
# same last part across namespaces: the "family" verbs
last = collections.defaultdict(list)
for a in live.values():
    if a["kind"]=="word" and "." in str(a.get("word")): w=str(a["word"]); last[w.rsplit(".",1)[1]].append(w)
print("shared verbs:", {k:v for k,v in last.items() if len(v)>1})
