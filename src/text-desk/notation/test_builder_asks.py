# health: room test (health.py runs every test_*.py with this line among its first ten)
"""test_builder_asks: a builder's comment wakes its asker only when it asks; the landing wakes them too (a5007).

    python test_builder_asks.py

Alex approved the Workbench (a4934): 'The asker is woken for two things only: the builder has a question, or it has
landed.' Pike (e9702): any agent counts as a builder, Claude sessions included, and a reply follows the same rule.
A small world in memory (roomworld.py). Whether pike would be woken while resting is read twice, as the house reads
it: by house.news (what wakes, and what the wake says) and by rooms.reached (the knock record). The story:
  1. a builder's progress comment, and its done report, on pike's commission: pike is not woken;
  2. the same builder's comment marked mark=ask: pike is woken, and the wake names it a question; read shows the mark;
  3. the house says it landed: pike is woken, once;
  4. a reply under a thread pike opened: unmarked, not woken; marked, woken and named a question;
  5. what still calls: a builder's comment opening with @pike or saying to=pike; a resident's plain comment;
  6. a commission card in pike's own corner: a builder's unmarked comment does not wake pike there either;
  7. a card that is not a commission is as before: an agent's comment on a thing in pike's corner wakes pike.
"""
import os
import re
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"

import roomworld   # noqa: E402
import house       # noqa: E402
import rooms       # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:1500]}"))
    if not ok:
        fails.append(name)


D, R = roomworld.build(say=False)
W = D.world
B = R.BOARD


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


def pike_rests(since):
    """-> (would news() wake pike from a rest, the lines it gathered, the wake's first line), for events since `since`."""
    h = house.House.__new__(house.House)
    r = SimpleNamespace(rid=rooms.corner_of(W, "pike"), state={"cursor": since}, save=lambda: None)
    woke = h.news(W, r, "pike", resting=True)
    lines = [x["text"] for x in r.state.get("for_you", [])] + list(r.state.get("inbox", []))
    return woke, lines, h.woken_by(r)


def knocks_pike(since):
    """-> the events since `since` that the knock record says call pike."""
    return [e["id"] for e in W.events[since:] if (rooms.reached(W, e) or {}).get("pike") == "call"]


def card(where, title, commission=True):
    t = say("pike", f"look {where} :1", f'do create {where} kind=task title="{title}" owner=pike asked_by=pike status=open')
    k = re.findall(r"created (a\d+)", t)[-1]
    if commission:
        say("pike", f"look {k} :1", f"do prop {k} commission=asked")
        say("house", f"look {k} :1", f"do prop {k} commission=working worker=worker-{k}")
    return k


K = card(B, "Doors")
WK = f"worker-{K}"


def builder(line, who=WK, on=K):
    return say(who, f"look {on} :1", f"do comment {on} {line}")


# ---- 1. progress and done, unmarked: not woken ----------------------------------------------------------------------
at = len(W.events)
out = builder('line="read the code; building the knock rule now"')
out2 = builder('line="done: changed rooms.py; ran the tests, all passed"')
woke, lines, first = pike_rests(at)
check("1. a builder's progress comment and done report are kept on the card", "ERR" not in out + out2
      and sum(c["by"] == WK for c in W.subjects[W.nodes[K]["subject"]]["comments"]) == 2, (out, out2))
check("1. and pike, resting, is not woken by them (RED before a5007)", not woke, lines)
check("1. nor does the knock record say they called pike", not knocks_pike(at), knocks_pike(at))
check("1. the builder's receipt says it wakes nobody, and how to ask", "it wakes nobody" in out and "mark=ask" in out, out)

# ---- 2. a question: woken, and named a question ----------------------------------------------------------------------
at = len(W.events)
out = builder('line="the brief says X; did you mean Y?" mark=ask')
woke, lines, first = pike_rests(at)
check("2. a comment marked mark=ask wakes pike", woke and len(lines) == 1, (out, lines))
check("2. the gathered line says it asks", "asks you a question" in " ".join(lines) and "mark" not in " ".join(lines)
      and "did you mean Y?" in " ".join(lines), lines)
check("2. the wake's first line names it a question", first and f"{WK}'s question" in first[0], first)
check("2. the knock record says it called pike", len(knocks_pike(at)) == 1, knocks_pike(at))
c = W.subjects[W.nodes[K]["subject"]]["comments"][-1]
check("2. the comment keeps its mark, and its event too", c.get("mark") == "ask" and W.events[-1]["args"].get("mark") == "ask",
      (c, W.events[-1]["args"]))
txt = say("pike", f"read {K}")
check("2. read shows the mark", f"{c['id']} {WK}: the brief says X; did you mean Y? (open, mark=ask)" in txt, txt)
txt = say("pike", f"examine {K}")
check("2. examine shows it too", "open, mark=ask)" in txt, txt)

# ---- 3. the landing: woken, once ---------------------------------------------------------------------------------
at = len(W.events)
say("house", f"read {K}", f'do comment {K} line="landed as abc1234; health ok"')
woke, lines, first = pike_rests(at)
check("3. the house's landed comment wakes pike, once", woke and len(lines) == 1 and "landed as" in lines[0], lines)
check("3. and the knock record says so", len(knocks_pike(at)) == 1, knocks_pike(at))

# ---- 4. replies under pike's own thread -----------------------------------------------------------------------------
K2 = card(B, "Windows")
WK2 = f"worker-{K2}"
say("pike", f"look {K2} :1", f'do comment {K2} line="@{WK2} which window manager first?"')
cid = W.subjects[W.nodes[K2]["subject"]]["comments"][-1]["id"]
at = len(W.events)
out = builder(f'id={cid} line="noted, starting with the simplest"', who=WK2, on=K2)
woke, lines, _ = pike_rests(at)
check("4. an unmarked reply under pike's thread does not wake pike", "ERR" not in out and not woke and not knocks_pike(at),
      (out, lines, knocks_pike(at)))
check("4. its receipt says it wakes nobody, not 'to: pike'", "it wakes nobody" in out and "to: pike" not in out
      and W.events[-1].get("to") == [], out)
at = len(W.events)
out = builder(f'id={cid} line="should it tile or float?" mark=ask', who=WK2, on=K2)
woke, lines, first = pike_rests(at)
check("4. a reply marked mark=ask wakes pike, in the thread, as a question", woke and "asks you (a question)" in " ".join(lines)
      and "in your thread" in " ".join(lines) and len(knocks_pike(at)) == 1, (out, lines))
check("4. and its receipt says to: pike", "to: pike" in out and "wakes nobody" not in out, out)
txt = say("pike", f"read {K2}")
check("4. read shows the reply's mark", "should it tile or float? (mark=ask)" in txt, txt)

# ---- 5. what still calls --------------------------------------------------------------------------------------------
at = len(W.events)
builder('line="@pike the host is down, look now"')
woke, lines, _ = pike_rests(at)
check("5. a builder's comment opening with @pike still calls pike", woke and "as @pike" in " ".join(lines), lines)
at = len(W.events)
builder('line="calling you by address" to=pike')
check("5. and one saying to=pike", pike_rests(at)[0] and len(knocks_pike(at)) == 1, knocks_pike(at))
at = len(W.events)
say("sable", f"look {K} :1", f'do comment {K} line="I can help with this one"')
check("5. a resident's plain comment on pike's commission still wakes pike", pike_rests(at)[0] and len(knocks_pike(at)) == 1)
at = len(W.events)
say("claude", f"look {K} :1", f'do comment {K} line="a Claude session, building by hand"')
check("5. a Claude session is a builder too: its plain comment does not wake pike", not pike_rests(at)[0] and not knocks_pike(at))

# ---- 6. a commission in pike's corner ------------------------------------------------------------------------------
corner = rooms.corner_of(W, "pike")
K3 = card(corner, "In my corner")
at = len(W.events)
builder('line="progress, in your corner"', who=f"worker-{K3}", on=K3)
check("6. a builder's unmarked comment on a commission in pike's corner does not wake pike", not pike_rests(at)[0]
      and not knocks_pike(at), pike_rests(at)[1])
at = len(W.events)
builder('line="a question, in your corner" mark=ask', who=f"worker-{K3}", on=K3)
woke, lines, _ = pike_rests(at)
check("6. a marked one does", woke and len(knocks_pike(at)) == 1, lines)

# ---- 7. not a commission: as before ---------------------------------------------------------------------------------
K4 = card(corner, "A note-like task", commission=False)
at = len(W.events)
builder('line="an agent passing by"', who="claude", on=K4)
woke, lines, _ = pike_rests(at)
check("7. an agent's comment on a plain thing in pike's corner still wakes pike", woke and "commented on" in " ".join(lines), lines)

print(f"\n{'all passed' if not fails else str(len(fails)) + ' FAILED: ' + '; '.join(fails)}")
sys.exit(1 if fails else 0)
