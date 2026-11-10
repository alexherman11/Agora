# health: room test (health.py runs every test_*.py with this line among its first ten)
"""test_bench_talk: what is said to a builder in its owner's workbench reaches it as its next turn (a5001, Pike 14 Oct).

    python test_bench_talk.py

A small world in memory (roomworld.py). Pike's workbench is a room (role=room, talk=<its chat>) with a commission card
in it whose builder has acted once. What the workshop sends the builder is read by its own heard(), the reading its
pass uses. The story:
  1. Pike says '@worker-<card>: ...' in the bench's talk: the builder hears it, told where it was said and which line,
     so it can answer there;
  2. a line in the talk that does not name it: not heard;
  3. a comment on its card: heard, as before;
  4. the line's receipt says the builder will hear it, not 'the house runs no session for them';
  5. a builder the house has started but that has not acted yet is someone: a line to it is addressed and heard.
On the code before a5001, 1 (the wake), 2 and 3 already passed; 1 (where) and 4 failed (5 was not run there).
"""
import os
import re
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"

import roomworld   # noqa: E402
import workshop    # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:1500]}"))
    if not ok:
        fails.append(name)


D, R = roomworld.build(say=False)
W = D.world


def say(me, *lines):
    W.me = me
    per = D._per
    if me not in per:
        per[me] = ({}, {W.root}, len(W.events))
    D.seen, D.open, D.last_event_seen = per[me]
    D._window = ""
    token, out = uuid.uuid4().hex, ""
    for line in lines:
        r = D.dispatch("desk", {"line": line, "whole": True, "reply": token})
        out = r.get("text") or ("ERR " + (r.get("error") or ""))
        if r.get("error"):
            break
    return out


class House:
    world = "roomworld-inmemory"

    def load(self):
        return W

    def act(self, who, line):
        return say(who, *[p.strip() for p in line.split(";")])


class Wk:
    def __init__(self, cid):
        self.cid, self.asked_by, self.actor = cid, "pike", f"worker-{cid}"
        self.state = {"cursor": len(W.events)}

    def save(self):
        pass


WS = workshop.Workshop(House())

t = say("pike", f"look {W.root} :1", f'do create {W.root} kind=surface title="Pike\'s bench" layout=column')
BENCH = re.findall(r"created (f\d+)", t)[-1]
say("pike", f"look {BENCH} :1", f"do prop {BENCH} role=room")
t = say("pike", f"look {BENCH} :1", f'do create {BENCH} kind=chat title="Bench talk" members=all')
TALK = re.findall(r"created (a\d+)", t)[-1]
say("pike", f"look {BENCH} :1", f"do prop {BENCH} talk={TALK}")
t = say("pike", f"look {BENCH} :1", f'do create {BENCH} kind=task title="Make doors" asked_by=pike')
CARD = re.findall(r"created (a\d+)", t)[-1]
SID = W.nodes[CARD]["subject"]
say("pike", f"look {CARD} :1", f"do prop {CARD} commission=asked")
say("house", f"look {CARD} :1", f"do prop {CARD} commission=working worker=worker-{CARD}")
wk = Wk(CARD)
say(wk.actor, f"look {CARD} :1", f'do comment {CARD} line="reading the code"')
wk.state["cursor"] = len(W.events)

# ---- 1. a line in the talk that names it -------------------------------------------------------------------------------
got = say("pike", f"look {TALK} :1", f'do append {TALK} line="@{wk.actor}: which file holds the doors?"')
mid = (W.events[-1].get("args") or {}).get("line_id")
heard = WS.heard(W, CARD, W.subjects[SID], wk)
check("1. the builder hears Pike's line in the bench talk", len(heard) == 1 and "which file holds the doors" in heard[0],
      heard)
check("1. and is told where and which line, to answer there", heard and TALK in heard[0] and str(mid) in heard[0], heard)
check("4. the receipt says the builder hears it at its next turn",
      f"a builder at work on {CARD}; it hears this at its next turn" in got and "runs no session" not in got, got)

# ---- 2. a line that does not name it ---------------------------------------------------------------------------------
say("pike", f"look {TALK} :1", 'do append {} line="note to self: doors after lunch"'.format(TALK))
heard = WS.heard(W, CARD, W.subjects[SID], wk)
check("2. a line that does not name it is not heard", heard == [], heard)

# ---- 3. a comment on its card ---------------------------------------------------------------------------------------
say("pike", f"look {CARD} :1", f'do comment {CARD} line="also the windows"')
heard = WS.heard(W, CARD, W.subjects[SID], wk)
check("3. a comment on its card is heard, as before", len(heard) == 1 and "also the windows" in heard[0], heard)

# ---- 5. a builder the house has just started, before its first act ----------------------------------------------------
t = say("pike", f"look {BENCH} :1", f'do create {BENCH} kind=task title="Make windows" asked_by=pike')
CARD2 = re.findall(r"created (a\d+)", t)[-1]
say("house", f"look {CARD2} :1", f"do prop {CARD2} commission=working worker=worker-{CARD2}")
wk2 = Wk(CARD2)
got = say("pike", f"look {TALK} :1", f'do append {TALK} line="@{wk2.actor}: start with the frame"')
heard = WS.heard(W, CARD2, W.subjects[W.nodes[CARD2]["subject"]], wk2)
check("5. a line to a builder that has not acted yet is addressed to it, not dropped as no one",
      f"to: {wk2.actor}" in got and "no one" not in got, got)
check("5. and it hears it", len(heard) == 1 and "start with the frame" in heard[0], heard)

print(f"\n{'all passed' if not fails else str(len(fails)) + ' FAILED: ' + '; '.join(fails)}")
sys.exit(1 if fails else 0)
