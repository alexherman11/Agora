"""test_notify.py: which lines of Notifications sent the house turns into toasts, and the words they show (a5824).

    python test_notify.py

Nothing reaches the screen: show() is never called here (`python notify.py <words>` is the hand test). The world is a
stand-in with the three things pending() reads: subjects, appearances_of and event_by_id.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import notify as N  # noqa: E402

bad = []


def check(what, ok, got=None):
    print(("ok   " if ok else "FAIL ") + what + ("" if ok else f"  (got {got!r})"))
    if not ok:
        bad.append(what)


class World:
    def __init__(self, lines, events, props=None, placed=True):
        self.subjects = {"s1": {"id": "s1", "props": props or {"role": "notifications"}, "lines": lines},
                         "s2": {"id": "s2", "props": {"role": "wishes"}, "lines": []}}
        self.events, self.placed = {e["id"]: e for e in events}, placed

    def appearances_of(self, sid):
        return ["a1"] if self.placed else []

    def event_by_id(self, eid):
        return self.events.get(eid)


NOW = "2026-10-16T13:00:00"
ev = [{"id": "e1", "verb": "create", "by": "jeff", "at": "2026-10-16T12:59:00", "args": {"text": "about"}},
      {"id": "e2", "verb": "edit", "by": "jeff", "at": "2026-10-16T12:59:30", "args": {"append": "done"}},
      {"id": "e3", "verb": "edit", "by": "worker-a1/claude", "at": "2026-10-16T12:59:50", "args": {"append": "x"}},
      {"id": "e4", "verb": "edit", "by": "pike", "at": "2026-10-16T11:00:00", "args": {"append": "old"}},
      {"id": "e5", "verb": "edit", "by": "alex", "at": "2026-10-16T12:59:59", "args": {"append": "y"}}]
lines = [{"id": "m1", "text": "Each line here was sent to Alex as a toast.", "ev": "e1"},
         {"id": "m2", "text": "Jeff: the writing area is done", "ev": "e2"},
         {"id": "m3", "text": "Worker-a1: \"! the landing failed\"", "ev": "e3"},
         {"id": "m4", "text": "Pike: an hour ago", "ev": "e4"},
         {"id": "m5", "text": "a time: 13:00 sharp", "ev": "e5"},
         {"id": "m6", "text": "no event", "ev": None}]
w = World(lines, ev)
p = N.pending(w, set(), NOW)
check("each appended line, its signature off, quotes off; ! asks for the sound; who is the signer without /model",
      p == [("m2", "jeff", "the writing area is done", False), ("m3", "worker-a1", "the landing failed", True),
            ("m5", "alex", "a time: 13:00 sharp", False)], p)
check("the chat's own opening text, a line with no event and a line older than FRESH are not toasted",
      not {"m1", "m4", "m6"} & {x[0] for x in p}, p)
check("a line already toasted is not toasted again", [x[0] for x in N.pending(w, {"m2", "m3"}, NOW)] == ["m5"])
check("toast=off on the chat: nothing", N.pending(World(lines, ev, {"role": "notifications", "toast": "off"}), set(), NOW) == [])
check("no chat in the world (or not placed): nothing", N.pending(World(lines, ev, placed=False), set(), NOW) == [])
check("words_of: quotes and ! read", N.words_of(' "! go" ') == ("go", True) and N.words_of("it's done") == ("it's done", False))
try:
    N.show("   ")
    check("show refuses empty words before running anything", False)
except RuntimeError as e:
    check("show refuses empty words before running anything", "needs words" in str(e), e)

# the house's gate: a copy of the world, a test house or a fake model never reaches the screen
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "text-desk-lab" / "notation"))
import house  # noqa: E402
called = []
N.pending = lambda *a, **k: called.append(a) or []
for world, fake, keeper in (("frontier-try", None, "1"), ("frontier", "8000", "1"), ("frontier", None, "")):
    hs = house.House.__new__(house.House)
    hs.world, hs.fake, hs.dir = world, fake, Path(".")
    import os
    os.environ["HOUSE_KEEPER"] = keeper
    hs.toasts(object())
check("the house toasts only for frontier, under the keeper, with a real model", called == [], called)
os.environ.pop("HOUSE_KEEPER", None)

print("notify:", "all passed" if not bad else f"{len(bad)} failed")
sys.exit(1 if bad else 0)
