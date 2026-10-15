"""test_knock (a3150; Sable c2705 on a1941): a knock leaves a record, one event per line, said once.

    python test_knock.py [world]      default frontier-try; it CHANGES the world it is given, so give it a copy

When the house decides about a line's addressees it writes one knock event (target and cause: the line's own event)
saying per name what happened: woken / in a turn, held for its end / asleep / not a member, not knocked / a person or
an agent, not knocked. A plain line that calls no one adds nothing. The record is said once per line: a second pass, a
new house, and a house that lost its own state all find it in the world and write nothing. `history <corner>`,
`history <line>` and `examine <line>` show it, and the message that ends a rest begins with the line that caused it.

It drives House.step with test_waiting's stand-in residents (no model is called, no worker is started). The world
needs three residents (pike, juniper, sable) and the rooms of frontier.
"""
import os
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"
os.environ.setdefault("HOUSE_CLAUDE", "claude")     # the house looks for a claude binary; none is started here
import house   # noqa: E402
import rooms   # noqa: E402

WORLD = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "frontier-try"
if not WORLD.endswith("-try") and "--yes" not in sys.argv:
    sys.exit(f"test_knock changes the world it runs on; {WORLD} is not a -try copy (add --yes to insist)")
shutil.rmtree(house.STATE / WORLD, ignore_errors=True)      # a clean house for this copy: no cursors from before


class Stand(house.Resident):
    """A resident whose process is always up and never busy unless the test says so; what it is sent is kept."""
    def __init__(self, h, rid):
        super().__init__(h, rid)
        self.sent, self.up = [], True

    def start(self, model):
        self.busy, self.up = False, True

    def stop(self):
        self.up = False

    def alive(self):
        return self.up

    def turns_ended(self):
        return []

    def send(self, text, kind="news", carry=None):
        self.sent.append((kind, text))
        self.state["last_sent"] = house.now()


house.Resident = Stand


def new_house():
    h = house.House(WORLD)
    h.workshop.step = lambda *a, **k: None               # no workers in a test
    return h


H = new_house()
w = H.load()
by_actor = {(n.get("props") or {}).get("actor"): fid for fid, n in H.corners(w).items()}
PIKE, JUNIPER, SABLE = by_actor["pike"], by_actor["juniper"], by_actor["sable"]


def app_titled(title):
    return next(a["id"] for a in w.nodes.values() if a["type"] == "appearance"
                and (w.subjects.get(a.get("subject")) or {}).get("title") == title)


LOUNGE = app_titled("Lounge talk")
BOOK = (w.nodes[PIKE].get("props") or {}).get("talk")                 # Pike's visitors' book
STALK = app_titled("Talk with Alex, Sable")
DESKTOP = next(f for f, n in w.nodes.items() if n["type"] == "surface" and n["title"] == "Desktop")
fails = []


def check(name, ok, detail=""):
    ok = bool(ok) and "the desk process failed" not in str(detail)
    print(("ok   " if ok else "FAIL ") + name + ("" if ok and "--show" not in sys.argv else f"\n     {str(detail)[:1800]}"))
    if not ok:
        fails.append(name)


def res(rid):
    return H.residents[rid]


def sent(rid):
    out = "\n---\n".join(t for _, t in res(rid).sent)
    res(rid).sent.clear()
    return out


def say(who, line, where=LOUNGE):
    """-> (the event id of the line, its m id or None, the receipt)"""
    # a5068: a resident's line is judged on its turn's view, which the house passes (as_of); here, a turn begun now
    turn = len(H.load().events) if who in ("pike", "juniper", "sable") else None
    got = H.act(who, f"do append {where} line={house.json.dumps(line)}", as_of=turn)
    e = next(x for x in reversed(H.load().events) if (x.get("args") or {}).get("append") is not None and x["by"] == who)
    return e["id"], (e.get("args") or {}).get("line_id"), got


def rest(rid, seconds=3600):
    H.rest(res(rid), seconds, "a test")
    res(rid).state["last_turn"] = house.now()
    H.step()
    res(rid).sent.clear()


def knocks(eid=None):
    return [e for e in H.load().events if e["verb"] == "knock" and (eid is None or e.get("cause") == eid)]


def what(eid):
    k = knocks(eid)
    return {a: v for a, v in k[0]["args"].items() if a != "line"} if len(k) == 1 else {"knock events": len(k)}


out = H.act("alex", f"look {DESKTOP} :1; do prop {DESKTOP} person=alex")
if (H.load().subjects[H.load().nodes[STALK]["subject"]].get("props") or {}).get("members") != "alex":
    H.act("alex", f"look {STALK} :1; do prop {STALK} members=alex")          # as the live world has it
n0 = len(knocks())                          # a copy that was tested on before may hold some
H.step()                                    # everyone arrives: each resident's first wake
first_wake = sent(PIKE)
check("a1941: a wake the house starts on its own says so: '(the house started you; no one called)'",
      "(the house started you; no one called)" in first_wake.splitlines()[1:3], first_wake[:300])
H.step()
for rid in H.residents:
    res(rid).sent.clear()
check("a house with no knocks.json starts at the end: no old line is recorded", len(knocks()) == n0, len(knocks()) - n0)

# 1. a resting resident is @'d: one event, with the line's id, in their corner's history; the wake names the line
rest(PIKE)
eid, mid, got = say("juniper", "@pike the lens you asked about is on the board")
H.step()
k = knocks(eid)
check("Juniper's @pike: one knock event, target and cause her line's event, line=<m id>, pike=woken, by house",
      len(k) == 1 and k[0]["target"] == eid and k[0]["cause"] == eid and k[0]["args"] == {"line": mid, "pike": "woken"}
      and k[0]["by"] == "house" and k[0]["knocked"] == [PIKE], k)
got = sent(PIKE)
IT_IS = r" · it is \d{1,2} [A-Z][a-z]{2}, \d\d:\d\d"       # a4473: the time now ends the wake's first line
check("Pike's wake begins with the line that caused it, by id, and the time now; 'for you while you rested' follows",
      re.fullmatch(re.escape(f"~ woken by juniper's line {mid} ({eid}) in \"Lounge talk\"") + IT_IS, got.splitlines()[0])
      and got.splitlines()[1] == "for you while you rested (1):" and "@pike the lens" in got, got[:500])
hist = H.act("sable", f"history {PIKE}")
check("history <Pike's corner> shows the knock with the line's id", f"knock {eid} line={mid} pike=woken by house" in hist, hist)
ex = H.act("sable", f"examine {mid}")
check("examine <line> shows it: 'knock (eN, the house's record): Pike: woken'",
      f"knock ({k[0]['id']}, the house's record): Pike: woken" in ex, ex)
ex = H.act("sable", f"examine {eid}")
check("examine <the line's event> shows it too", f"knock ({k[0]['id']}, the house's record): Pike: woken" in ex, ex)
hist = H.act("sable", f"history {mid}")
check("history <line> lists the knock under the line", f"{k[0]['id']} knock {eid}" in hist, hist)

# 2. said once: a later pass, a new house, and a house that lost its state write nothing more
n = len(knocks())
H.step()
H.step()
check("later passes add no event", len(knocks()) == n and len(knocks(eid)) == 1, len(knocks()))
H2 = new_house()
H2.step()
check("a new house (a restart) finds the record in the world and adds none", len(knocks()) == n, len(knocks()))
st = house.json.loads((house.STATE / WORLD / "knocks.json").read_text(encoding="utf-8"))
(house.STATE / WORLD / "knocks.json").write_text(house.json.dumps({"cursor": 0}), encoding="utf-8")
ev0 = len(H.load().events)
H3 = new_house()
H3.record_knocks(H3.load(), H3.corners(H3.load()))
check("a house whose place was wrongly set to 0 records nothing old: no line every awake resident has heard",
      len(knocks()) == n and len(knocks(eid)) == 1, len(knocks()) - n)
(house.STATE / WORLD / "knocks.json").write_text(house.json.dumps({"cursor": ev0}), encoding="utf-8")
refused = H.act("house", f"knocked {eid} " + house.json.dumps({"pike": "woken"}))
check("the desk itself keeps it once: a second record of the same line writes nothing",
      "already has its knock record" in refused and len(knocks(eid)) == 1, refused)
refused = H.act("juniper", f"knocked {eid} " + house.json.dumps({"pike": "woken"}))
check("knocked is the house's line: to anyone else it is no command", len(knocks(eid)) == 1 and "ok e" not in refused, refused)
undo = H.act("juniper", f"undo {k[0]['id']}")
check("undo leaves the record, and says why", "the house's record" in undo and len(knocks(eid)) == 1, undo)
for rid in H.residents:
    res(rid).sent.clear()

# 3. a line said while no house ran is recorded once by the house that follows
rest(PIKE)
eid, mid, got = say("juniper", "@pike said while the house was down")
H = new_house()
H.step()
check("a line said before a house started is recorded by it, once", what(eid) == {"pike": "woken"}, what(eid))
H.step()
check("and not again on its next pass", len(knocks(eid)) == 1, len(knocks(eid)))
for rid in H.residents:
    res(rid).sent.clear()

# 4. a plain line that calls no one adds no event (Claude e5528 (1))
n = len(knocks())
eid, mid, got = say("juniper", "a plain line in the lounge, for no one in particular")
H.step()
check("a plain Lounge line: no knock event", len(knocks()) == n, knocks()[n:])
eid, mid, got = say("juniper", "thanks, as @pike said yesterday")
H.step()
check("a mid-line @pike is a mention: no knock event, and Pike is sent nothing as a call", len(knocks()) == n, knocks()[n:])

# 5. per name: in a turn, asleep, not a member, a person, an agent
rest(PIKE)
rest(SABLE)
res(SABLE).busy = True
eid, mid, got = say("juniper", "@pike @sable @alex @claude four of you")
H.step()
check("'@pike @sable @alex @claude': Pike woken, Sable in a turn, Alex a person, Claude an agent, in one event",
      what(eid) == {"pike": "woken", "sable": "in a turn, held for its end",
                    "alex": "a person, not knocked (it waits in their For you)",
                    "claude": "not knocked (no Claude session is listening)"}, what(eid))   # a5267: no listener runs
check("and the record agrees with what the house did: Pike was sent it, Sable nothing yet",
      "four of you" in sent(PIKE) and not res(SABLE).sent, res(SABLE).sent)
res(SABLE).busy = False
H.step()
sent(SABLE)
rest(PIKE)
eid, mid, got = say("alex", "@pike a word in Sable's talk, not for you", STALK)
H.step()
check("a line to a non-member: 'pike: not a member, not knocked' on the line, and Pike sleeps on",
      what(eid).get("pike") == "not a member, not knocked" and not res(PIKE).sent and res(PIKE).state.get("rest_until"),
      (what(eid), sent(PIKE)[:200]))
ex = H.act("sable", f"examine {mid}")
check("examine <that line> says 'Pike: not a member, not knocked'", "Pike: not a member, not knocked" in ex, ex)
hist = H.act("sable", f"history {PIKE}")
check("and Pike's corner's history has it", f"knock {eid}" in hist, hist)
H.act("alex", f"look {JUNIPER} :1; do prop {JUNIPER} want=rest")
H.step()
eid, mid, got = say("sable", "@juniper are you there")
H.step()
check("a line to someone asleep (want=rest): 'asleep (want=rest), kept for their wake'",
      what(eid) == {"juniper": "asleep (want=rest), kept for their wake"}, what(eid))
H.act("alex", f"look {JUNIPER} :1; do prop {JUNIPER} want=awake")
H.step()
sent(JUNIPER)
H.step()

# 6. @everyone is spread to the residents it calls; the writer is not in it
rest(PIKE)
rest(SABLE)
rest(JUNIPER)
eid, mid, got = say("juniper", "@everyone the board moved")
H.step()
check("@everyone: one event naming each resident it called, not the writer",
      what(eid) == {"pike": "woken", "sable": "woken"} or set(what(eid)) >= {"pike", "sable"} and "juniper" not in what(eid)
      and what(eid)["pike"] == "woken" and what(eid)["sable"] == "woken", what(eid))
sent(PIKE), sent(SABLE)

# 7. a visitors' book: a resident's plain line waits; a person's knocks
if BOOK:
    rest(PIKE)
    eid, mid, got = say("juniper", "a plain line in your book", BOOK)
    H.step()
    check("a resident's plain line in Pike's own chat: recorded as not knocked, waiting for his next wake; nothing sent",
          what(eid) == {"pike": "not knocked: a plain line in their own chat waits for their next wake"} and not res(PIKE).sent,
          (what(eid), sent(PIKE)[:200]))
    eid, mid, got = say("alex", "a person's plain line in your book", BOOK)
    H.step()
    got = sent(PIKE)
    check("a person's plain line there: 'woken', and the wake names it first",
          what(eid) == {"pike": "woken"} and got.splitlines()[0].startswith(f"~ woken by alex's line {mid} ({eid}) in "), (what(eid), got[:300]))

# 8. outside a chat: an @header in a comment, and a comment on a thing in someone's corner
rest(PIKE)
note = H.act("juniper", f"do create {LOUNGE.replace(LOUNGE, w.nodes[LOUNGE]['parent'])} kind=note title=\"a3150 knock test\" text=\"a note\"")
nid = re.search(r"created (a\d+)", note)
if nid:
    got = H.act("juniper", f"do comment {nid.group(1)} line=\"@pike see this note\"")
    e = H.load().events[-1]
    H.step()
    got = sent(PIKE)
    check("an @pike header in a comment: 'pike: woken', and the wake begins '~ woken by juniper's comment (eN) on ...'",
          what(e["id"]) == {"pike": "woken"} and re.fullmatch(re.escape(f"~ woken by juniper's comment ({e['id']}) on \"a3150 knock test\"") + IT_IS, got.splitlines()[0]),
          (what(e["id"]), got[:300]))
    n = len(knocks())
    H.act("juniper", f"do comment {nid.group(1)} line=\"a comment that names no one\"")
    H.step()
    check("a comment that names no one, on a thing in no one's corner: no event", len(knocks()) == n, knocks()[n:])
    got = H.act("sable", "look")
    check("not a notification: the knock records are in no one's 'since your last look'", "house" not in got.splitlines()[1]
          and "knock e" not in got and "knock in" not in got, got[:600])
else:
    check("made a note to comment on", False, note)

# 8b. a4473: every wake by a call ends its first line with the time now and adds no line: a comment on a thing in his
# own corner, a worker's comment on his commission, wake <name>
mine = re.search(r"created (a\d+)", H.act("pike", f"do create {PIKE} kind=note title=\"a4473 mine\" text=\"a note\""))
job = re.search(r"created (a\d+)", H.act("pike", f"do create {w.nodes[LOUNGE]['parent']} kind=task title=\"a4473 job\" asked_by=pike"))
for name, who, target, first, rows in (
        ("a comment on a thing in his own corner", "juniper", mine, r"~ woken by juniper's comment \(e\d+\) on \"a4473 mine\"", 2),
        ("a worker's comment on his commission", "worker-a1", job, r"~ woken by worker-a1's comment \(e\d+\) on \"a4473 job\"", 2)):
    rest(PIKE)
    got = H.act(who, f"look {target.group(1)} :1; do comment {target.group(1)} line=\"a word on it\"") if target else "not made"
    H.step()
    lines = sent(PIKE).splitlines()
    check(f"{name}: the wake's first line ends with the time now, and the wake is {rows} lines, as before",
          len(lines) == rows and re.fullmatch(first + IT_IS, lines[0]) and "a word on it" in lines[1], (got[-300:], lines))
rest(PIKE)
H.act("juniper", "wake pike")
H.step()
lines = sent(PIKE).splitlines()
check("wake pike: its one line '~ juniper woke you (wake, eN)' ends with the time now",
      len(lines) == 1 and re.fullmatch(r"~ juniper woke you \(wake, e\d+\)" + IT_IS, lines[0]), lines)

# 9. the reading the record uses is the knock's own: every 'woken' was sent something, across this whole run
wl = H.load()
check("reached(): a plain shared-chat line reaches no one; the house's own events reach no one",
      all(rooms.reached(wl, e) == {} for e in wl.events[-40:] if e["by"] == "house" and e["verb"] != "comment"))
check("every knock event has one cause, and no line has two", len({e["cause"] for e in knocks()}) == len(knocks()), len(knocks()))

print(f"\n{len(fails)} failed" if fails else "\nall ok")
sys.exit(1 if fails else 0)
