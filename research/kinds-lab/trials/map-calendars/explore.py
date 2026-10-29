"""Look around the copy of the live desktop world before building the trial: who the steward is, which kinds,
which map/board words and lenses exist. Read-only on a scratch copy; never the live world."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, "C:/Projects/Agora4/research/kernel-lab")
from kernel.kernel import Kernel, Actor  # noqa: E402

world = Path(sys.argv[1])
t0 = time.perf_counter()
k = Kernel(world)
print("open", round(time.perf_counter() - t0, 2), "s;", len(k.state.things), "things;", len(k.log.records), "records")
stewards = [t for t, a in k.state.things.items() if a.get("kind") == "person" and k.is_steward(t)]
print("stewards", [(t, k.state.get(t, "name")) for t in stewards])
print("accounts", list(getattr(k, "accounts", {}).items())[:5])
p = stewards[0]
A = Actor(p, p, "person")


def run(line):
    out = k.run(A, line)
    return out


print("--- kinds")
for t, a in k.state.things.items():
    if a.get("kind") == "kind" and not a.get("forgotten"):
        print(" ", t, {x: a.get(x) for x in ("name", "needs", "extends", "fields", "required", "groups") if a.get(x)},
              "groups", k.groups_of(t))
print("--- map/board words")
for e in k.entries():
    a = k.state.things[e]
    w = str(a.get("word"))
    if w.startswith(("map.", "board.")) or w in ("done", "rows", "mark", "actions", "set", "claim", "post"):
        print(" ", e, w, a.get("word_kind"), "takes=", a.get("takes"), "acts_on=", a.get("acts_on"),
              "needs=", a.get("needs"), "status=", a.get("status"), "from=", a.get("from"))
print("--- maps, map-layers, spots, structures, events, posts")
from collections import Counter
c = Counter(a.get("kind") for a in k.state.things.values() if not a.get("forgotten"))
for kd in ("map", "map-layer", "spot", "structure", "event", "post", "meeting", "board-channel", "lens", "component",
           "module", "grant", "place", "group"):
    print(" ", kd, c.get(kd))
for t, a in k.state.things.items():
    if a.get("kind") in ("map", "map-layer") and not a.get("forgotten"):
        print(" ", t, {x: v for x, v in a.items() if not x.startswith(("in:", "member:"))})
for t, a in k.state.things.items():
    if a.get("kind") == "lens" and "tag:" in str(a.get("text")) and not a.get("forgotten"):
        import re
        print("  lens", t, a.get("name"), a.get("painter"), sorted(set(re.findall(r"tag:[a-z0-9_-]+", a.get("text")))))
print("--- modules")
for t, a in k.state.things.items():
    if a.get("kind") == "module":
        print(" ", t, a.get("name"), a.get("publishes"), a.get("status"))
print("top kinds", c.most_common(40))
