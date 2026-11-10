"""Try the world half on a loaded copy in memory; never save it or start models."""
from pathlib import Path
import sys
import time
from types import SimpleNamespace

import apply
sys.path.insert(0, str(apply.NOTATION))
import export_docs
import desk
import scene
import usage
import plan_usage


def verify(world, source=None):
    d = export_docs.load(world)
    w = d.world
    last = w.events[-1]
    print(f'Copy at {last["id"]}: {len(w.events)} events')
    w.me = "worker-a6646"
    d.seen, d.open = {}, {w.root}
    commands = []

    def act(who, line):
        w.me = who
        for part in desk.split_batch(line):
            result = d.dispatch("desk", {"line": part, "whole": True})
            if result.get("error") or (result.get("text") or "").startswith(("MISS ", "ERR ")):
                raise RuntimeError(f'{part[:120]}: {result.get("error") or result.get("text")}')
            commands.append(part)
        return result.get("text", "")

    for line in apply.lines(w):
        act("worker-a6646", line)
    h = SimpleNamespace(dir=Path("unused-inmemory-plan-state"), load=lambda: w, act=act)
    if source:
        h.usage = usage.Usage(world, source)
    p = plan_usage.Plans(h)
    p.save = lambda: None  # the copy's native facts are tested, no state file is needed
    p.publish()
    for title in ("home-usage", "plan-usage-glance", "plan-usage-reader", "home-glance", "home-board"):
        w.me = "alex"
        sc, words = scene.scene_for(d, title)
        assert sc["def"]["status"] == "current", sc["def"]
        print(f"{title}: current")
        if title == "plan-usage-reader":
            assert "Source:" in words
    for s in w.subjects.values():
        if (s.get("props") or {}).get("role") == "usage-window":
            print(s["text"])
    # Same-provider cards share a notice; reset retries get one resumed notice.
    targets = [n["id"] for n in w.nodes.values() if n.get("subject")
               and (w.subjects.get(n["subject"]) or {}).get("kind") == "task"][:2]
    count = lambda: sum(line.startswith("notify ") for line in commands)
    before = count()
    for target in targets:
        p.paused("claude", target, time.time() + 60)
    assert count() - before == 1
    for target in targets:
        p.resumed("claude", target)
    assert count() - before == 2
    assert all(notice["sent"] for entry in p.state["pauses"].values() for notice in entry["notices"])
    print("Two cards: one limit notice, one resume notice; native states cleared.")
    return d, p, commands


if __name__ == "__main__":
    verify(sys.argv[1], Path(sys.argv[2]) if len(sys.argv) > 2 else None)
