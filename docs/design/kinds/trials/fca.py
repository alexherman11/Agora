import json, collections, re, sys
st = collections.defaultdict(dict)
for line in open(sys.argv[1], encoding="utf-8"):
    if not line.strip(): continue
    r = json.loads(line)
    for p in r.get("parts", []):
        for f in p.get("facts", []):
            if len(f) > 3: st[f[0]][f[1]] = f[3]
live = {t:a for t,a in st.items() if a.get("kind") and not a.get("forgotten")}
BOOK = {"kind","made_by","in","for","via_actor","visibility_of","by"}
fam = lambda k: re.split(r"[:.]", k)[0]
per = collections.defaultdict(collections.Counter); n = collections.Counter()
for t,a in live.items():
    n[a["kind"]]+=1
    for k in {fam(x) for x in a}: per[a["kind"]][k]+=1
shape = {kd: frozenset(k for k,c in per[kd].items() if c>=max(1,n[kd]*0.6) and k not in BOOK) for kd in n}
shape = {k:v for k,v in shape.items() if len(v)>=1}
pairs=[]
for a,sa in shape.items():
    for b,sb in shape.items():
        if a!=b and sa < sb and len(sa)>=2: pairs.append((a,b,sorted(sa)))
print("kinds with a shape:", len(shape))
print("structural nestings (outer < inner, outer has >=2 aspects):", len(pairs))
by = collections.defaultdict(list)
for a,b,s in pairs: by[(a,tuple(s))].append(b)
for (a,s),bs in sorted(by.items(), key=lambda x:-len(x[1])): print(f"  {a} {list(s)} contains: {', '.join(sorted(bs))}")
eq = collections.defaultdict(list)
for k,s in shape.items(): eq[s].append(k)
print("same shape (structure can't tell apart):", [v for v in eq.values() if len(v)>1])
# synonyms
allk = collections.Counter(fam(x) for a in live.values() for x in a)
for grp in (("name","title","label"),("color","colour"),("text","body"),("about","source")):
    print("synonym group", {g:allk[g] for g in grp})
