"""Step 0: what the real world copy holds for tasks. Prints counts, words, rules, grants, lenses, kinds."""
from collections import Counter
from common import open_world, steward, say, short

k, dt = open_world("w-explore")
print(f"open: {dt:.2f}s, records={len(k.log.records)}, things={len(k.state.things)}")
s = steward(k)
print("steward", s.person, k.name(s.person))
persons = list(k.things("person"))
print("persons", [(p, k.name(p), k.is_steward(p)) for p in persons])
kinds = Counter(a.get("kind") for a in k.state.things.values() if not a.get("forgotten"))
print("top kinds", kinds.most_common(30))
tasks = [t for t in k.things("taskboard-task") if not k.state.get(t, "forgotten")]
print("taskboard-task live", len(tasks))
fields = Counter(f for t in tasks for f in k.state.things[t])
print("task fields", fields.most_common(60))
print("lanes", Counter(k.state.get(t, "lane") for t in tasks))
print("who", Counter(k.state.get(t, "who") for t in tasks))
print("lane things", [(t, k.state.things[t]) for t in k.things("taskboard-lane")])
for e in k.entries():
    a = k.state.things[e]
    w = str(a.get("word"))
    if w.startswith(("task", "house", "summarize", "issue")) or a.get("acts_on") or a.get("needs") or w.split(".")[-1] in ("done", "close", "open", "move", "assign"):
        print("WORD", e, w, a.get("from"), "takes=", a.get("takes"), "may=", a.get("may"), "acts_on=", a.get("acts_on"), "needs=", a.get("needs"), "lives=", a.get("lives"), "steps=", str(a.get("steps", ""))[:80])
for t in k.things("rule"):
    a = k.state.things[t]
    if not a.get("forgotten"):
        print("RULE", t, {x: a.get(x) for x in ("name", "on", "of_kind", "do", "on_entry")})
for t in k.things("grant"):
    a = k.state.things[t]
    print("GRANT", t, {x: a.get(x) for x in ("to", "words", "only", "forgotten")})
for t in k.things("kind"):
    a = k.state.things[t]
    print("KIND", t, {x: a.get(x) for x in ("name", "needs", "extends", "help", "forgotten")})
for t in k.things("lens"):
    a = k.state.things[t]
    if "taskboard" in str(a.get("text", "")) or "task" in str(a.get("name", "")):
        print("LENS", t, a.get("name"), a.get("painter"), len(str(a.get("text", ""))), "forgotten" if a.get("forgotten") else "")
for t in k.things("module"):
    a = k.state.things[t]
    print("MODULE", t, a.get("name"), a.get("on"), a.get("publishes"))
print(short(say(k, s, "rows taskboard-task", mode="see"), 400))
print(short(say(k, s, "kinds " + tasks[0], mode="see")))
print(short(say(k, s, "actions " + tasks[0], mode="see"), 2000))
