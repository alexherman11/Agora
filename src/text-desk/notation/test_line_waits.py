# health: room test (health.py runs every test_*.py with this line among its first ten)
"""test_line_waits (a9369): chat additions land with a receipt of crossing lines.

    python test_line_waits.py [world]      on roomworld (built in memory); with a world (frontier-try), its copy,
                                           read into memory and never saved, which also measures its longest chat

Alex, 21 Oct: send the line, then show missed lines in its receipt. Agent A reads a chat, agent B adds a
line, A's append lands with B's line shown; the same for a reply in a chat's comment thread. A resident's
turn view (as_of, the house's news cursor) still identifies crossings, but a receipt acknowledges them
immediately within the same turn. Overwriting edits remain fenced.
Every line is a desk line, as each actor would type it.
"""
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"
import explore    # noqa: E402
import rooms      # noqa: E402

WORLD = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else None
if WORLD:
    desk = explore.load_desk(explore.SESSIONS / f"{WORLD}.pickle")
else:
    import roomworld
    desk, R = roomworld.build()
    desk.dispatch("desk", {"line": f"look {R.DESKTOP} :1"})
    desk.dispatch("desk", {"line": f"do prop {R.DESKTOP} person=alex"})     # Alex sits at the Desktop, as live
w = desk.world
fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok and "--show" not in sys.argv else f"\n     {str(detail)[:1600]}"))
    if not ok:
        fails.append(name)


per = getattr(desk, "_per", None) or {}
desk._per = per


def run(who, line, as_of=None):
    """One desk line as `who`, with that reader's own record of what it has seen (as explore keeps it per slot)."""
    w.me = who
    if who not in per:
        per[who] = ({}, {w.root}, len(w.events))
    desk.seen, desk.open, desk.last_event_seen = per[who]
    desk._as_of = as_of
    try:
        r = desk.dispatch("desk", {"line": line})
    finally:
        desk._as_of = None
        per[who] = (desk.seen, desk.open, desk.last_event_seen)
    out = r.get("text") or ("ERR " + str(r.get("error")))
    # the '!! since your last look' header is the look's, not the act's: the act's own words follow it
    err, rows = out.startswith("ERR "), (out[4:] if out.startswith("ERR ") else out).split("\n")
    while rows and (rows[0].startswith("!! ") or (rows[0].startswith("   ") and len(rows) > 1)):
        rows.pop(0)
    return ("ERR " if err else "") + "\n".join(rows)


residents = {(n.get("props") or {}).get("actor"): fid for fid, n in w.nodes.items()
             if n["type"] == "surface" and (n.get("props") or {}).get("role") == "resident"}
RES = next(a for a in ("pike", "juniper", "sable") if a in residents)
HUMAN = next(a for a in ("alex",) if rooms.kind_of(w, a) == "person")
A, B = "worker-t1", "worker-t2"           # agents: no corner, no person= surface
check("the actors are of the kinds the test needs", rooms.kind_of(w, A) == "agent" and rooms.kind_of(w, RES) == "resident"
      and rooms.kind_of(w, HUMAN) == "person", (rooms.kind_of(w, A), RES, HUMAN))

out = run(A, f'look {w.root} :1')
out = run(A, f'do create {w.root} kind=chat title="Hold test" text="Start."')
CHAT = next(a["id"] for a in w.nodes.values() if a["type"] == "appearance"
            and (w.subjects.get(a.get("subject")) or {}).get("title") == "Hold test")
SID = w.nodes[CHAT]["subject"]


def lines():
    return [l["text"] for l in w.subjects[SID]["lines"]]


# 1. A reads, B speaks, A's line waits with B's shown; the same line again goes as written
run(A, f"read {CHAT}")
run(B, f'do append {CHAT} line="B: the build is red, do not merge"')
held = run(A, f'do append {CHAT} line="merging now"')
check("A's line on an old view lands immediately", held.startswith("ok") and lines()[-1].endswith("merging now"),
      held)
check("the receipt prints B's short line, with who and its ids",
      "the build is red, do not merge" in held and "Worker-t2" in held.replace("worker-t2", "Worker-t2")
      and "m" in held and "(e" in held, held)
check("the receipt confirms sent and marked read, with no retry instruction",
      "Sent." in held and "marked read" in held and "send the same command again" not in held, held)
again = run(A, f'do append {CHAT} line="merging now"')
check("another send goes through without showing the same crossing again", again.startswith("ok")
      and "new line" not in again and lines()[-1].endswith("merging now"),
      again)

# 2. a changed line is a new line, judged afresh: after B speaks again it waits; with nothing new it goes
run(B, f'do append {CHAT} line="B: wait, one more check"')
h2 = run(A, f'do append {CHAT} line="ok, waiting"')
check("a later line by B is shown with the next successful send, only what is new", h2.startswith("ok") and "one more check" in h2
      and "do not merge" not in h2, h2)
c2 = run(A, f'do append {CHAT} line="ok, waiting for your check"')
check("a changed line also goes with nothing new since", c2.startswith("ok"), c2)

# 3. a line to a chat nobody else wrote in since goes at once; and what the check costs
t0 = time.perf_counter()
for k in range(20):
    o = run(A, f'do append {CHAT} line="note {k}"')
dt = (time.perf_counter() - t0) / 20
desk_hold = desk._chat_moved
t1 = time.perf_counter()
for k in range(200):
    desk_hold(CHAT, {"line": "x"})
dh = (time.perf_counter() - t1) / 200
check("lines to a chat nobody else wrote in since go at once", o.startswith("ok") and lines()[-1].endswith("note 19"), o)
print(f"     cost: one append {dt * 1000:.1f} ms in all; crossing receipt check {dh * 1e6:.0f} us of it "
      f"({len(w.events)} events, {len(lines())} lines)")

# 4. a person is never held
run(HUMAN, f"read {CHAT}")
run(B, f'do append {CHAT} line="B: Alex, are you there?"')
hu = run(HUMAN, f'do append {CHAT} line="here"')
check("a person's line is never held: their painter shows lines as they arrive", hu.startswith("ok"), hu)

# 5. an agent who never read the chat has no view to be behind: the line goes, and its receipt says it is unread
nv = run("worker-t3", f'do append {CHAT} line="first word here"')
check("an agent with no read of the chat is not held; the receipt says it hasn't read it",
      nv.startswith("ok") and "haven't read this chat" in nv, nv)

# 6. reply_to= names what you answer: that line and what came before it count as shown
run(A, f"read {CHAT}")
run(B, f'do append {CHAT} line="B: question for A?"')
mid = w.subjects[SID]["lines"][-1]["id"]
rt = run(A, f'do append {CHAT} line="answer" reply_to={mid}')
check("a reply_to= the new line itself goes: you answer what you were shown", rt.startswith("ok"), rt)

# 7. a reply in a comment thread
run(A, f"look {CHAT} :1")
run(A, f'do comment {CHAT} line="Should the chat be archived?"')
cid = w.subjects[SID]["comments"][-1]["id"]
run(A, f"read {CHAT}")
run(B, f"look {CHAT} :1")
run(B, f'do comment {CHAT} id={cid} line="No: Alex still uses it"')
th = run(A, f'do comment {CHAT} id={cid} line="archiving it then"')
check("A's reply on an old chat thread lands with B's reply in its receipt",
      th.startswith("ok") and "Alex still uses it" in th and cid in th
      and any(r["text"] == "archiving it then" for c in w.subjects[SID]["comments"] for r in c["replies"]), th)
th2 = run(A, f'do comment {CHAT} id={cid} line="archiving it then"')
check("the same reply again goes through", th2.startswith("ok"), th2)
run(B, f'do comment {CHAT} id={cid} line="B: please do not"')
run(A, f"examine {cid}")
th3 = run(A, f'do comment {CHAT} id={cid} line="understood, leaving it"')
check("examine c<n> shows the thread, so a reply after it goes at once", th3.startswith("ok"), th3)
run(B, f'do comment {CHAT} id={cid} line="thanks"')
hu2 = run(HUMAN, f'do comment {CHAT} id={cid} line="all settled"')
check("a person's thread reply is never held", hu2.startswith("ok"), hu2)

# 8. a resident is judged on its turn's view: as_of, the house's news cursor when the turn's input was sent
run(RES, f"read {CHAT}", as_of=len(w.events))
turn = len(w.events)                     # the house sends this turn's input now
run(B, f'do append {CHAT} line="B: said while the resident was thinking"')
rr = run(RES, f'do append {CHAT} line="my answer"', as_of=turn)
check("a resident's line lands and shows what arrived after its turn began", rr.startswith("ok") and "while the resident" in rr, rr)
rr2 = run(RES, f'do append {CHAT} line="my answer"', as_of=turn)
check("in the same turn a second send lands and does not repeat the crossing",
      rr2.startswith("ok") and "while the resident" not in rr2, rr2)
rr3 = run(RES, f'do append {CHAT} line="my answer"', as_of=len(w.events))
check("its next turn (as_of past the line) sends the same line as written", rr3.startswith("ok"), rr3)
run(B, f'do append {CHAT} line="B: also, lunch?"')
rr4 = run(RES, f'do append {CHAT} line="and one more thing"', as_of=len(w.events))
check("a line before its turn in a chat the house does not tell it of is shown after sending",
      rr4.startswith("ok") and "lunch" in rr4, rr4)
run(A, f"look {CHAT} :1")
run(A, f"do prop {CHAT} members=all")
run(B, f'do append {CHAT} line="B: dinner too?"')
rr5 = run(RES, f'do append {CHAT} line="yes to both"', as_of=len(w.events))
check("one in a chat the house tells it of (members=all), said before its turn, does not hold: the house sent it",
      rr5.startswith("ok"), rr5)

# 9. what the check costs where it does the most: a resident's turn, on the longest chat in this world
big = max((s for s in w.subjects.values() if s["kind"] == "chat" and s.get("lines")), key=lambda s: len(s["lines"]))
BIG = next(iter(w.appearances_of(big["id"])))
run(RES, f"read {BIG} :3", as_of=len(w.events))
w.me = RES
desk._as_of = len(w.events)
t2 = time.perf_counter()
for k in range(20):
    desk._chat_moved(BIG, {"line": "x"})
dr = (time.perf_counter() - t2) / 20
desk._as_of = None
w.me = A
desk._as_of = None
run(A, f"read {BIG} :3")
t3 = time.perf_counter()
for k in range(200):
    desk._chat_moved(BIG, {"line": "x"})
da = (time.perf_counter() - t3) / 200
print(f"     cost on \"{big['title']}\" ({len(big['lines'])} lines): a resident's check {dr * 1000:.2f} ms, "
      f"another agent's {da * 1e6:.0f} us")
check("the check on the longest chat costs under 20 ms for a resident and under 1 ms for any other agent",
      dr < 0.02 and da < 0.001, (dr, da))

print(f"\n{len(fails)} failed" if fails else "\nall passed")
sys.exit(1 if fails else 0)
