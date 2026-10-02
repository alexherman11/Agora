"""test_private_to (a3025, Pike e5281): a private chat's unaddressed line goes to its other members, and says so.

    python test_private_to.py [world]      default frontier-try; it CHANGES the world it is given, so give it a copy

In a chat whose members= names people (not members=all), a line with no @ header and no to= is addressed to every
other member, the resident whose corner holds it counting as one (Pike's Talk with Alex says members=alex): to= is
stored as them, the receipt says 'to: alex (this chat's other member)', and a resting resident member is knocked by
the house's own reading of to= (a2662; house.py unchanged). An @ header narrows or widens it, as written; to=nobody
still says no one. A shared chat (members=all, or no members=) keeps a plain line to nobody. Lines said before keep
their stored to=. It drives House.step with stand-in residents, as test_waiting does; no model is called.
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
os.environ.setdefault("HOUSE_CLAUDE", "claude")
import house   # noqa: E402

WORLD = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "frontier-try"
if not WORLD.endswith("-try") and "--yes" not in sys.argv:
    sys.exit(f"test_private_to changes the world it runs on; {WORLD} is not a -try copy (add --yes to insist)")
shutil.rmtree(house.STATE / WORLD, ignore_errors=True)


class Stand(house.Resident):
    """A resident whose process is always up and never busy; what it is sent is kept."""
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
H.workshop.step = lambda *a, **k: None
w = H.load()
by_actor = {(n.get("props") or {}).get("actor"): fid for fid, n in H.corners(w).items()}
PIKE, JUNIPER, SABLE = by_actor["pike"], by_actor["juniper"], by_actor["sable"]
fails = []


def check(name, ok, detail=""):
    ok = ok and "the desk process failed" not in str(detail)
    print(("ok   " if ok else "FAIL ") + name + ("" if ok and "--show" not in sys.argv else f"\n     {str(detail)[:1800]}"))
    if not ok:
        fails.append(name)


def app_titled(title):
    return next(a["id"] for a in H.load().nodes.values() if a["type"] == "appearance"
                and (H.load().subjects.get(a.get("subject")) or {}).get("title") == title)


def say(who, line, where, extra=""):
    return H.act(who, f"do append {where} line={house.json.dumps(line)}{extra}")


def to_line(got):
    m = re.search(r"line (m\d+) · to: ([^\n]*)", got)
    return (m.group(1), m.group(2)) if m else (None, None)


def stored(mid):
    wl = H.load()
    return next((l.get("to") for s in wl.subjects.values() for l in s.get("lines") or () if l["id"] == mid), None)


def sent(rid):
    out = "\n---\n".join(t for _, t in H.residents[rid].sent)
    H.residents[rid].sent.clear()
    return out


def rest(rid, seconds=3600):
    H.rest(H.residents[rid], seconds, "a test")
    H.residents[rid].state["last_turn"] = house.now()
    H.step()
    H.residents[rid].sent.clear()


t0 = time.time()
TAG = int(t0)                       # this run's chats, so a second run on the same copy finds its own
DESKTOP = next(f for f, n in w.nodes.items() if n["type"] == "surface" and n["title"] == "Desktop")
H.act("alex", f"look {DESKTOP} :1; do prop {DESKTOP} person=alex")
H.step()
H.step()
for rid in H.residents:
    sent(rid)
before = {l["id"]: list(l.get("to") or []) for s in H.load().subjects.values() for l in s.get("lines") or ()}

# (i) Pike's Talk with Alex (members=alex, in Pike's corner): Pike's 'Alex, are you there?' is to: alex, and says why
TALK = app_titled("Talk with Alex, Pike")
talk_members = (H.load().subjects[H.load().nodes[TALK]["subject"]].get("props") or {}).get("members")
got = say("pike", "Alex, are you there?", TALK)
mid, to = to_line(got)
check("(i) in a members=alex chat, Pike's 'Alex, are you there?' is to: alex, and the receipt names why",
      to == "alex (this chat's other member)" and stored(mid) == ["alex"]
      and "Alex: a member of this chat; it waits in their For you" in got,          # a2692: Sable's words
      (talk_members, got))
rest(PIKE)
got = say("alex", "yes, here", TALK)
mid, to = to_line(got)
H.step()
check("Alex's plain line there is to: pike (his corner holds it), and wakes him",
      to == "pike (this chat's other member)" and stored(mid) == ["pike"] and "Pike: woken" in got
      and "yes, here" in sent(PIKE) and not H.residents[PIKE].state.get("rest_until"), got)

# (ii) a chat with members=juniper,pike: Juniper's plain line knocks a resting Pike
ROOM = H.load().nodes[app_titled("Lounge talk")]["parent"]          # a room no resident's corner holds
made = H.act("juniper", f"look {ROOM} :1; do create {ROOM} kind=chat title=\"Pair talk {TAG}\" members=juniper,pike")
PAIR = app_titled(f"Pair talk {TAG}")
rest(PIKE)
got = say("juniper", "the board is tidy now", PAIR)
mid, to = to_line(got)
H.step()
check("(ii) members=juniper,pike: Juniper's unaddressed line is to: pike, and the house knocks him",
      to == "pike (this chat's other member)" and stored(mid) == ["pike"] and "Pike: woken" in got
      and "the board is tidy now" in sent(PIKE) and not H.residents[PIKE].state.get("rest_until"), (made, got))
got = say("juniper", "@sable: a look at this?", PAIR)
check("an @ header in a private chat still says whom, as written: to: sable (not a member, so not knocked)",
      to_line(got)[1] == "sable" and "Sable: not a member of this chat" in got, got)
got = say("juniper", "thinking out loud", PAIR, " to=nobody")
check("to=nobody in a private chat is still no one", to_line(got)[1] == "nobody", got)
got = say("juniper", "thanks, @sable, noted", PAIR)
check("a mid-line @ there is still a mention; the line goes to the other member",
      to_line(got)[1].startswith("pike (this chat's other member); a mid-line @ is a mention (@sable)"), got)
H.act("juniper", f"look {PAIR} :1; do prop {PAIR} members=juniper,pike,sable")
got = say("juniper", "all three of us now", PAIR)
check("three members: to: pike, sable (this chat's other members)",
      to_line(got)[1] == "pike, sable (this chat's other members)", got)
H.step()
for rid in H.residents:
    sent(rid)

# (iii) a shared chat (members=all) with no @ stays to: nobody
H.act("juniper", f"look {ROOM} :1; do create {ROOM} kind=chat title=\"Open talk {TAG}\" members=all")
got = say("juniper", "anyone around?", app_titled(f"Open talk {TAG}"))
check("(iii) a members=all chat with no @ stays to: nobody", to_line(got)[1] == "nobody", got)
H.act("juniper", f"look {ROOM} :1; do create {ROOM} kind=chat title=\"Loose talk {TAG}\"")
got = say("juniper", "anyone around?", app_titled(f"Loose talk {TAG}"))
check("and so does a chat with no members=", to_line(got)[1] == "nobody", got)

# (iv) lines said before keep their stored to=
after = {l["id"]: list(l.get("to") or []) for s in H.load().subjects.values() for l in s.get("lines") or ()}
changed = [k for k, v in before.items() if after.get(k) != v]
check(f"(iv) the {len(before)} lines said before keep their stored to=", not changed, changed[:10])

shutil.rmtree(house.STATE / WORLD, ignore_errors=True)
print(f"{len(fails)} failed" if fails else "all passed", f"({time.time() - t0:.0f} s, world {WORLD})")
sys.exit(1 if fails else 0)
