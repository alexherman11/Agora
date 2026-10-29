"""Second look: the two board cards, live windows, the JEFF chat lens, model/summarize grants and words."""
import sys
sys.path.insert(0, "C:/Projects/Agora4/research/kernel-lab")
from kernel.kernel import Kernel, Actor

k = Kernel(sys.argv[1])
for t in ("dk1031", "dk1140"):
    a = k.state.things.get(t, {})
    print("CARD", t, {x: str(v)[:600] for x, v in a.items() if not x.startswith("in:")})
for t in k.things("window"):
    a = k.state.things[t]
    if not a.get("forgotten"):
        print("LIVEWIN", t, {x: str(v)[:50] for x, v in a.items() if not x.startswith("in:")})
lens = next(t for t in k.things("lens") if k.state.get(t, "name") == "jeff-chat")
print("JEFF LENS", lens, "\n", str(k.state.get(lens, "text"))[:3000])
for kd in ("conversation-draft", "house-agent"):
    print(kd, len(k.things(kd)), [{x: str(v)[:40] for x, v in k.state.things[t].items() if not x.startswith("in:")} for t in k.things(kd)[:2]])
s = next(iter(k.things("said")))
print("SAID sample keys", sorted(k.state.things[s].keys()))
for m in k.things("module"):
    a = k.state.things[m]
    print("MOD", m, {x: str(v)[:80] for x, v in a.items() if not x.startswith("in:")})
