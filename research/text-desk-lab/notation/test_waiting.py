"""test_waiting (a1062, talk step 3e): a mention waits for waking; waking is its own act.

    python test_waiting.py [world]      default frontier-try; it CHANGES the world it is given, so give it a copy

It drives House.step, the house's own pass, with stand-in residents that keep what the house would send instead of
writing to a claude process (no model is called, no worker is started). The house's heartbeat is written as it runs,
so the desk's receipts read the same presence the live house would give them. The world needs three residents
(pike, juniper, sable) and the rooms of frontier; a person is recorded as the Desktop's person=alex.
"""
import os
import re
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"
os.environ.setdefault("HOUSE_CLAUDE", "claude")     # the house looks for a claude binary; none is started here
import house   # noqa: E402

WORLD = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "frontier-try"
if not WORLD.endswith("-try") and "--yes" not in sys.argv:
    sys.exit(f"test_waiting changes the world it runs on; {WORLD} is not a -try copy (add --yes to insist)")
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
H = house.House(WORLD)
H.workshop.step = lambda *a, **k: None               # no workers in a test
w = H.load()
by_actor = {(n.get("props") or {}).get("actor"): fid for fid, n in H.corners(w).items()}
PIKE, JUNIPER = by_actor["pike"], by_actor["juniper"]


def app_titled(title):
    return next(a["id"] for a in w.nodes.values() if a["type"] == "appearance"
                and (w.subjects.get(a.get("subject")) or {}).get("title") == title)


LOUNGE = app_titled("Lounge talk")
BOOK = (w.nodes[PIKE].get("props") or {}).get("talk")                 # Pike's visitors' book
DESKTOP = next(f for f, n in w.nodes.items() if n["type"] == "surface" and n["title"] == "Desktop")
fails = []


def check(name, ok, detail=""):
    ok = ok and "the desk process failed" not in str(detail)
    print(("ok   " if ok else "FAIL ") + name + ("" if ok and "--show" not in sys.argv else f"\n     {str(detail)[:1800]}"))
    if not ok:
        fails.append(name)


def res(rid):
    return H.residents[rid]


def sent(rid):
    """What the house sent this resident since the last call, and forget it."""
    out = "\n---\n".join(t for _, t in res(rid).sent)
    res(rid).sent.clear()
    return out


def say(who, line, where=LOUNGE):
    return H.act(who, f"do append {where} line={house.json.dumps(line)}")


def rest(rid, seconds):
    H.rest(res(rid), seconds, "a test")
    res(rid).state["last_turn"] = house.now()
    H.step()


t0 = time.time()
out = H.act("alex", f"look {DESKTOP} :1; do prop {DESKTOP} person=alex")
check("the Desktop records its person (person=alex)", "person=alex" in out or "already has that" in out, out)
H.step()                                    # everyone arrives: each resident's first wake
H.step()
for rid in H.residents:
    res(rid).sent.clear()

# 1. Pike rests an hour; Juniper says a line with @pike; Pike stays resting
rest(PIKE, 3600)
until = time.strftime("%H:%M", time.localtime(res(PIKE).state["rest_until"]))
got = say("juniper", "@pike the lens you asked about is on the board")
check("Juniper's receipt says Pike is resting and when he'll see it",
      f"Pike is resting until {until}; they'll see this when they wake" in got and "wake pike" in got
      and "no need to say so" in got, got)
H.step()
check("Pike stays resting: nothing sent, the line is kept for him", not res(PIKE).sent
      and len(res(PIKE).state.get("for_you") or []) == 1 and res(PIKE).state.get("rest_until"), res(PIKE).state)

# 2. at Pike's next wake the line is first, marked for you, with its chat and time
res(PIKE).state["rest_until"] = house.now() - 1
H.step()
got = sent(PIKE)
lines = got.splitlines()
check("at the wake: 'for you while you rested' comes first, before the wake's own look",
      len(lines) > 3 and lines[0].startswith("You are pike.") and lines[1].startswith("(you rested")
      and lines[2] == "for you while you rested (1):" and "Lounge talk" in lines[3] and "@pike the lens" in lines[3]
      and re.search(r"~ \d\d:\d\d in chat", lines[3]), got[:900])

# 3. wake pike ends his rest; his wake names Juniper and the line
rest(PIKE, 0)
got = say("juniper", "@pike one more thing, when you're up")
check("an untimed rest: the receipt says the latest the line waits", re.search(r"Pike is resting, until \S+ at the latest; they'll see", got), got)
H.step()
check("still resting before the wake", not res(PIKE).sent, sent(PIKE))
got = H.act("juniper", "wake pike")
check("wake pike: signed by Juniper, the house calls them now", re.search(r"ok e\d+: you wake Pike", got) and "calls them now" in got, got)
ev = H.load().events[-1]
check("the wake is a call= on Pike's corner, by juniper, via=wake", ev["verb"] == "prop" and ev["target"] == PIKE
      and ev["by"] == "juniper" and ev.get("via") == "wake" and ev["args"].get("call") == "juniper", ev)
H.step()
got = sent(PIKE)
check("Pike's wake names Juniper and the line she left", got.startswith("~ juniper woke you (wake, e")
      and "for the line they left you:" in got.splitlines()[0] and "one more thing" in got.splitlines()[1], got[:600])
check("the call is cleared once delivered", "call" not in (H.load().nodes[PIKE].get("props") or {}), H.load().nodes[PIKE].get("props"))
got = H.act("juniper", "wake juniper")
check("waking yourself is refused", "ERR" in got and "you are awake" in got, got)
got = H.act("juniper", "wake nobody")
check("waking no one is refused, and says why", "ERR" in got and "no resident called 'nobody'" in got, got)

# 4. a person's @pike still wakes Pike at once
rest(PIKE, 3600)
got = say("alex", "@pike can you look at this now?")
check("Alex's receipt: his line calls Pike now", "Pike was resting; your line calls them now" in got, got)
H.step()
got = sent(PIKE)
check("Alex's @pike reaches Pike at once, and his rest ends", "(to you)" in got and "can you look at this now" in got
      and not res(PIKE).state.get("rest_until"), got[:600])

# 5. a resident writing to an awake resident (in a turn) is unchanged
res(PIKE).busy = True
H.step()                                                   # the heartbeat now says Pike is working
got = say("juniper", "@pike while you're at it")
check("to someone in a turn, the receipt says nothing about resting", "resting" not in got and "asleep" not in got, got)
res(PIKE).busy = False
H.after_turn(H.load(), res(PIKE), H.load().nodes[PIKE], "pike", "Thinking, nothing done yet.")
got = sent(PIKE)
check("it goes with what reaches him when his turn ends, marked to you, not kept", "(to you)" in got
      and "while you're at it" in got and not res(PIKE).state.get("for_you"), got[:600])

# 6. a visitors' book line from a resident is a note at the door; from a person, a knock
rest(PIKE, 3600)
if BOOK:
    got = say("juniper", "left you the notes from this morning", BOOK)
    check("a resident's line in Pike's own book: the receipt says he's resting", "Pike is resting until" in got, got)
    H.step()
    check("the book line waits for his wake", not res(PIKE).sent and any("left you the notes" in h["text"] for h in res(PIKE).state.get("for_you") or []), res(PIKE).state.get("for_you"))
else:
    print("skip Pike's corner has no talk= chat")
TALK = app_titled("Talk with Alex, Pike")
got = say("alex", "are you there?", TALK)
H.step()
got = sent(PIKE)
check("Alex's line in Pike's own chat wakes him at once, the held book line first", "are you there?" in got
      and (not BOOK or got.index("for you while you rested") < got.index("are you there?")), got[:800])

# 7. @everyone: resting residents get it at their next wake
rest(PIKE, 3600)
SABLE = by_actor["sable"]
rest(SABLE, 3600)
got = say("juniper", "@everyone the suite is green again")
check("@everyone: the receipt names each resting resident", "Pike is resting until" in got and "Sable is resting until" in got, got)
H.step()
check("@everyone waits for both", not res(PIKE).sent and not res(SABLE).sent
      and any("suite is green" in h["text"] for h in res(SABLE).state.get("for_you") or []), (res(PIKE).sent, res(SABLE).sent))

# 8. an agent (no corner, no person record) waits too; a plain line wakes no one and is not marked for you
got = say("claude", "@pike a note from outside")
check("an agent's @pike: the receipt says Pike is resting", "Pike is resting until" in got, got)
got = say("juniper", "a plain line in the lounge")
check("a line that calls no one says nothing about resting", "resting" not in got, got)
H.step()
held = [h["text"] for h in res(PIKE).state.get("for_you") or []]
check("the agent's line is held; the plain line is not marked for him", not res(PIKE).sent
      and any("a note from outside" in h for h in held) and not any("a plain line" in h for h in held), held)
res(PIKE).state["rest_until"] = house.now() - 1
H.step()
got = sent(PIKE)
first = got.split("for you while you rested", 1)
check("at his wake: both held lines first, the plain lounge line after the wake's look",
      len(first) == 2 and "suite is green" in got and "a note from outside" in got
      and got.index("a note from outside") < got.index("a plain line in the lounge"), got[:1200])

# 9. asleep (want=rest): a line waits, and a wake waits for someone to set want=awake; the call is then delivered,
# first, and cleared, so the next wake is a change again
H.act("alex", f"look {PIKE} :1; do prop {PIKE} want=rest")
H.step()
got = say("juniper", "@pike for when you're back")
check("to someone asleep, the receipt says so", "Pike is asleep" in got and "they'll see this when they wake" in got, got)
got = H.act("juniper", "wake pike")
check("wake pike while asleep: the call waits for want=awake, and says so", "asleep (want=rest)" in got and "waits" in got, got)
H.step()
check("asleep: nothing sent", not res(PIKE).sent, sent(PIKE))
H.act("alex", f"look {PIKE} :1; do prop {PIKE} want=awake")
H.step()
got = sent(PIKE)
lines = got.splitlines()
check("woken: Juniper's call and her line come first, after who he is", len(lines) > 2 and lines[0].startswith("You are pike.")
      and lines[1].startswith("~ juniper woke you (wake, e") and "for when you're back" in lines[2], got[:700])
check("the call delivered at a wake is cleared", "call" not in (H.load().nodes[PIKE].get("props") or {}), H.load().nodes[PIKE].get("props"))

shutil.rmtree(house.STATE / WORLD, ignore_errors=True)
print(f"{len(fails)} failed" if fails else "all passed", f"({time.time() - t0:.0f} s, world {WORLD})")
sys.exit(1 if fails else 0)
