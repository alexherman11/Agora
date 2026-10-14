"""test_landing_wait: a landing that waits says so once, and knocks its asker once (a4644, Pike and Juniper 13 Oct).

    python test_landing_wait.py

A small world in memory (roomworld.py) and a git repository of its own in a temporary folder, standing in for the
main checkout. The workshop's own land() runs with a stand-in house whose lines go through the desk's dispatch; health
and the docs export are stubbed (they run the lab's real world), and so is finish (it removes a worktree). Who a house
comment knocks is read by rooms.reached, the reading the house's knock record uses. The story:
  1. pike's commission is ready and main has an uncommitted edit: one comment saying it waits and on what, to=nobody,
     so it wakes no one (Pike c4717: the asker cannot act on a wait; the outcome still calls them);
  2. passes go by with the same edit, then with another file edited too, then with only that other file: nothing said;
  3. a new house (the worker's state from before this change, without held=) meets the same wait: nothing said;
  4. the edits are committed and it lands: the card says landed, and pike is knocked once for it;
  5. a second commission waits, is refused (nothing to land), and waits again: each wait is said once, and only the
     refusal knocks.
"""
import os
import re
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"

import roomworld   # noqa: E402
import house       # noqa: E402
import rooms       # noqa: E402
import workshop    # noqa: E402

fails = []
WAITING = "ready, and waiting to land"     # how the house begins a wait on a card (workshop.WAITING; spelled out, so
                                           # this runs on the code from before it, to show what it was)


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


class House:
    world = "roomworld-inmemory"

    def load(self):
        return W

    def act(self, who, line):
        out = say(who, *[p.strip() for p in line.split(";")])
        if "ERR" in out:
            print("house refused:", line[:120], "->", out[-300:])
        return out


class Wk:
    """What land() needs of a worker: its branch, names and saved state."""
    def __init__(self, cid):
        self.cid, self.branch, self.asked_by, self.actor = cid, f"worker/{cid}", "pike", f"worker-{cid}"
        self.state, self.saves, self.heard = {}, 0, []

    def save(self):
        self.saves += 1

    def send(self, text):
        self.heard.append(text)


tmp = tempfile.TemporaryDirectory()
REPO = Path(tmp.name)
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def git(*args):
    r = subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, env=ENV)
    assert r.returncode == 0, (args, r.stdout, r.stderr)
    return r.stdout.strip()


def write(name, text, msg=None):
    (REPO / name).parent.mkdir(parents=True, exist_ok=True)
    (REPO / name).write_text(text, encoding="utf-8")
    if msg:
        git("add", "--", name)
        git("commit", "-q", "-m", msg)


git("init", "-q", "-b", "main")
write("lab/a.py", "a = 1\n")
write("lab/b.js", "b = 1\n")
write("lab/c.py", "c = 1\n")
git("add", "-A")
git("commit", "-q", "-m", "start")

_git = workshop.git
workshop.git = lambda *a, cwd=REPO, **k: _git(*a, cwd=cwd, **k)     # its default cwd is the real checkout
workshop.REPO = REPO
workshop.health = lambda world, cwd=None: {"ok": True, "lenses_ok": [], "failed": [], "text": "all well"}
WS = workshop.Workshop(House())
WS.export_docs = lambda cid: ""
WS.compare_lived = lambda w: None
WS.finish = lambda cid, wk, keep_branch: None


def commission(title, branch_file):
    t = say("pike", f"look {B} :1", f'do create {B} kind=task title="{title}" owner=pike asked_by=pike status=open')
    card = re.findall(r"created (a\d+)", t)[-1]
    say("pike", f"look {card} :1", f"do prop {card} commission=asked")
    say("house", f"look {card} :1", f"do prop {card} commission=ready")
    git("checkout", "-q", "-b", f"worker/{card}")
    write(branch_file, f"# {title}\n", f"{card}: {title}")
    git("checkout", "-q", "main")
    return card, W.nodes[card]["subject"], Wk(card)


def house_said(sid, since):
    """-> (the house's comments on the card since event `since`, how many of them knock pike)."""
    said = [e for e in W.events[since:] if e["by"] == "house" and e["verb"] == "comment"
            and (e["target"] == sid or (W.nodes.get(e["target"]) or {}).get("subject") == sid)]
    knocks = [e for e in said if (rooms.reached(W, e) or {}).get("pike") == "call"]
    return said, knocks


def wakes_pike(since):
    """-> whether what happened since event `since` would wake pike from a rest, by the house's own news()."""
    from types import SimpleNamespace
    h = house.House.__new__(house.House)
    r = SimpleNamespace(rid=rooms.corner_of(W, "pike"), state={"cursor": since}, save=lambda: None)
    return h.news(W, r, "pike", resting=True)


def text(e):
    return " ".join(str(v) for v in (e.get("args") or {}).values() if isinstance(v, str))


def land(card, sid, wk):
    WS.land(W, card, W.subjects[sid], wk)


# ---- 1. ready, and main has an uncommitted edit: said once, knocked once -------------------------------------------
K1, S1, wk1 = commission("Doors", "lab/doors.py")
start = len(W.events)
write("lab/a.py", "a = 2  # Alex, by hand\n")
land(K1, S1, wk1)
said, knocks = house_said(S1, start)
check("1. one comment says it waits, and on what", len(said) == 1 and WAITING in text(said[0])
      and "lab/a.py" in text(said[0]), [text(e) for e in said])
check("1. pike is not woken by it (to=nobody: the asker cannot act on a wait, Pike c4717)", not knocks
      and said[0].get("to") == [], [(text(e), e.get("to")) for e in said])
check("1. it is still ready, not landed", (W.subjects[S1].get("props") or {}).get("commission") == "ready",
      W.subjects[S1].get("props"))

# ---- 2. passes with the same edit, then a different file in the way: nothing said ----------------------------------
for _ in range(3):
    land(K1, S1, wk1)
write("lab/b.js", "b = 2  # and another\n")
land(K1, S1, wk1)
git("checkout", "-q", "--", "lab/a.py")
land(K1, S1, wk1)
land(K1, S1, wk1)
said, knocks = house_said(S1, start)
check("2. same edit, a file added, a file put back: still the one comment", len(said) == 1, [text(e) for e in said])
check("2. and nobody knocked", not knocks, [text(e) for e in knocks])
check("2. the house's news() would not wake pike for any of it", not wakes_pike(start))
check("2. the worker's state follows what is in the way", wk1.state.get("held") == ["lab/b.js"], wk1.state)

# ---- 3. a new house, its worker's state without held= (from before, or lost): the card's word is asked ---------------
wk1.state.pop("held")
land(K1, S1, wk1)
said, _ = house_said(S1, start)
check("3. a state without held= does not say it again: the card already says it waits", len(said) == 1,
      [text(e) for e in said])

# ---- 4. committed: it lands, said once, knocked once --------------------------------------------------------------
git("add", "-A")
git("commit", "-q", "-m", "Alex's edit")
mark = len(W.events)
land(K1, S1, wk1)
said, knocks = house_said(S1, mark)
check("4. the card says it landed", len(said) == 1 and text(said[0]).startswith("landed as "), [text(e) for e in said])
check("4. pike is knocked once for that", len(knocks) == 1, [text(e) for e in knocks])
check("4. and news() wakes pike for it", wakes_pike(mark))
check("4. the wait is forgotten", "held" not in wk1.state, wk1.state)
check("4. commission=landed", (W.subjects[S1].get("props") or {}).get("commission") == "landed", W.subjects[S1].get("props"))

# ---- 5. every wait is its own: a later wait on another commission begins afresh, and one after a refusal too --------
K2, S2, wk2 = commission("Windows", "lab/windows.py")
start2 = len(W.events)
write("lab/c.py", "c = 2\n")
land(K2, S2, wk2)
land(K2, S2, wk2)
said, knocks = house_said(S2, start2)
check("5. a second commission's wait is said once on its own card", len(said) == 1 and WAITING in text(said[0]),
      [text(e) for e in said])
git("checkout", "-q", "--", "lab/c.py")
git("branch", "-q", "-f", "worker/" + K2, "main")          # its branch has nothing beyond main: refused, back to working
land(K2, S2, wk2)
say("house", f"look {K2} :1", f"do prop {K2} commission=ready")
write("lab/c.py", "c = 3\n")
land(K2, S2, wk2)
land(K2, S2, wk2)
said, knocks = house_said(S2, start2)
check("5. after the pass went ahead (refused), a new wait is news, said once",
      [WAITING in text(e) for e in said] == [True, False, True], [text(e) for e in said])
check("5. the refusal, which the asker acts on, is the one knock", [text(e) for e in knocks]
      == ["nothing to land: the branch has no commits beyond main"], [text(e) for e in knocks])

workshop.git = _git
print(f"\n{'all passed' if not fails else str(len(fails)) + ' FAILED: ' + '; '.join(fails)}")
sys.exit(1 if fails else 0)
