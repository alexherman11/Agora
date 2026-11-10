"""Look at the world copy before building: kinds present, chats, said, windows, words with shapes, grants.
Run: .venv/Scripts/python.exe explore.py <world_dir>"""
import sys, time
from collections import Counter
sys.path.insert(0, "C:/Projects/Agora4/src/agora")
from kernel.kernel import Kernel, Actor

d = sys.argv[1]
t0 = time.perf_counter()
k = Kernel(d)
print("load", round(time.perf_counter() - t0, 2), "s; records", len(k.log.records), "things", len(k.state.things))
steward = next(p for p in k.things("person") if k.is_steward(p))
A = Actor(steward, steward, "person")
print("steward", steward, k.name(steward))
c = Counter(a.get("kind") for a in k.state.things.values() if not a.get("forgotten"))
print(c.most_common(60))
for kd in ("chat",):
    for t in k.things(kd):
        a = k.state.things[t]
        print("CHAT", t, {x: (str(v)[:50]) for x, v in a.items() if not x.startswith("in:")})
print("said per chat", Counter(k.state.get(t, "chat") for t in k.things("said")))
ws = k.things("window")
print("windows", len(ws))
for t in ws[:40]:
    a = k.state.things[t]
    print("WIN", t, {x: str(v)[:40] for x, v in a.items() if not x.startswith(("in:",))})
for t in k.things("kind"):
    print("KIND", t, {x: str(v)[:60] for x, v in k.state.things[t].items() if not x.startswith("in:")})
shaped = [(k.state.get(e, "word"), k.state.get(e, "acts_on"), k.state.get(e, "needs")) for e in k.entries()
          if k.state.get(e, "acts_on") or k.state.get(e, "needs")]
print("shaped words", shaped)
fam = Counter(str(k.state.get(e, "word")).split(".")[0] for e in k.entries() if "." in str(k.state.get(e, "word")))
print("families", fam.most_common(50))
for e in k.entries():
    w = str(k.state.get(e, "word"))
    if w.split(".")[0] in ("window", "model", "summarize", "chat", "twitch", "jeff", "reply", "say") or w in ("say", "chat", "mark", "actions", "kinds", "rows", "close", "open", "reply"):
        print("WORD", e, w, "|", k.state.get(e, "takes"), "|", k.state.get(e, "from"), "|", str(k.state.get(e, "help") or "").splitlines()[:1])
for t in k.things("grant"):
    a = k.state.things[t]
    print("GRANT", t, a.get("module") or a.get("to"), "|", str(a.get("words"))[:120], "|", a.get("only"))
for t in k.things("module"):
    a = k.state.things[t]
    print("MOD", t, a.get("name"), a.get("for"))
lenses = [(t, k.state.get(t, "name")) for t in k.things("lens")]
print("lenses", len(lenses), [n for _, n in lenses][:80])
import re
for t, n in lenses:
    tx = str(k.state.get(t, "text") or "")
    if "chat" in tx or "said" in tx:
        print("LENS-CHAT", t, n, re.findall(r"(?:tag|reading):[^\s,]+", tx)[:6])
print("rules", [(t, k.state.get(t, "on"), k.state.get(t, "of_kind")) for t in k.things("rule")])
