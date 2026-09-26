"""Probe for knife's group and moo's reveal: same results before and after the box() patch, switch off and on."""
import sys, json
sys.path.insert(0, sys.argv[1])
from world import World
import knife, moo
out = {}
w = World()
root = w.root
free = w.add_surface("Board", root, "free", 0, 0, 600, 400)
col = w.add_surface("List", root, "column", 600, 0, 300, 400)
a = [w.place(w.add_subject("note", f"n{i}"), free, 40 + 90 * i, 60 + 20 * i, 80, 50) for i in range(3)]
b = [w.place(w.add_subject("task", f"t{i}"), col, 0, 0, 100, 40) for i in range(3)]
stray = w.place(w.add_subject("note", "stray"), free, 580, 390, 80, 50)
r = knife.group_around(w, a[:2], {"as": "free", "title": "pair"})
g = r["created"]
out["group"] = [w.nodes[g][k] for k in "xywh"] + [[w.nodes[i][k] for k in "xy"] for i in a[:2]]
r2 = moo.v_reveal(w, stray, {})
out["reveal"] = [w.nodes[stray][k] for k in "xyz"]
r3 = knife.group_around(w, b[:2], {"as": "column", "title": "colgroup"})
out["colgroup"] = sorted((w.nodes[i]["parent"] == r3["created"]) for i in b[:2])
out["colboxes"] = [[w.nodes[i][k] for k in "xywh"] for i in b]
print(json.dumps(out))
