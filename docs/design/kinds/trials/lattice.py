"""P1. Formal concept analysis over kinds x aspects, raw and with aspect meanings cleaned. Which concepts appear?"""
import collections, itertools
from world import load, fam, BOOK, PATH
live, _ = load(PATH)
n = collections.Counter(a["kind"] for a in live.values())
per = collections.defaultdict(collections.Counter)
for a in live.values():
    for k in {fam(x) for x in a}: per[a["kind"]][k] += 1
def shapes(clean):
    out = {}
    for kd in n:
        s = {k for k, c in per[kd].items() if c >= max(1, n[kd] * 0.6) and k not in BOOK and k != "name"}
        if clean:
            s = {("name" if k in ("title", "label") else "colour" if k == "color" else k) for k in s}
            # 'text' is prose only where people read it; elsewhere it is code or style source
            if "text" in s and kd in ("style", "theme", "lens", "part-style", "rule"): s = (s - {"text"}) | {"code_text"}
            if "shows" in s and kd == "map-layer": s = (s - {"shows"}) | {"reading"}
            if "order" in s and kd == "map-layer": s = (s - {"order"}) | {"layer_order"}
        if s: out[kd] = frozenset(s)
    return out
def concepts(sh):
    # closed aspect sets: intersections of kinds' shapes, with the kinds that have all of them
    cand = set(sh.values())
    for a, b in itertools.combinations(list(sh.values()), 2):
        i = a & b
        if i: cand.add(frozenset(i))
    changed = True
    while changed:
        changed = False
        for a, b in itertools.combinations(list(cand), 2):
            i = a & b
            if i and i not in cand: cand.add(i); changed = True
    res = []
    for intent in cand:
        ext = sorted(k for k, s in sh.items() if intent <= s)
        if len(ext) >= 2 and len(intent) >= 1: res.append((sorted(intent), ext))
    return sorted(res, key=lambda x: (-len(x[1]), x[0]))
for clean in (False, True):
    sh = shapes(clean); cs = concepts(sh)
    print(f"\n{'CLEANED' if clean else 'RAW'}: {len(sh)} kinds, {len(cs)} concepts shared by 2+ kinds (name left out: nearly everything has one)")
    for intent, ext in cs: print(f"  {intent} <- {', '.join(ext)}")
