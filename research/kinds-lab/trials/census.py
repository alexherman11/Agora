import json, collections, re, sys
st = collections.defaultdict(dict)
for line in open(sys.argv[1], encoding="utf-8"):
    if not line.strip(): continue
    r = json.loads(line)
    for p in r.get("parts", []):
        for f in p.get("facts", []):
            if len(f) > 3: st[f[0]][f[1]] = f[3]
live = {t:a for t,a in st.items() if a.get("kind") and not a.get("forgotten")}
C = collections.Counter(a["kind"] for a in live.values())
print("things", len(live), "kinds", len(C))
print(C.most_common(80))
# aspect families per kind (strip :suffix)
fam = lambda k: re.split(r"[:.]", k)[0]
per = collections.defaultdict(collections.Counter)
for t,a in live.items():
    for k in a: per[a["kind"]][fam(k)] += 1
for kd,n in C.most_common(45):
    common = [k for k,c in per[kd].most_common() if c >= max(1, n*0.5)]
    print(f"{kd} ({n}):", " ".join(common[:22]))
# kind declarations
print("\nDECLARED KINDS")
for t,a in live.items():
    if a["kind"]=="kind": print(t, {k:(str(v)[:70]) for k,v in a.items() if k not in ("kind",)})
