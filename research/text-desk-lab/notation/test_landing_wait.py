# health: room test (health.py runs every test_*.py with this line among its first ten)
"""test_landing_wait: a commission's landing never waits on anyone's uncommitted edits, and what it comes to is said
once (landing.py, Alex 14 Oct: "uncommitted changes not blocking new code arriving"; before: a4644, Pike c4717).

    python test_landing_wait.py

A small world in memory (roomworld.py) and a git repository of its own in a temporary folder, standing in for the
main checkout, laid out as the lab is. The workshop's own land() runs with a stand-in house whose lines go through the
desk's dispatch; it lands through landing.py, whose health is stubbed (it fails when the judged code holds a file
BROKEN); the docs export and finish are stubbed too. Who a house comment knocks is read by rooms.reached.
  1. pike's commission is ready while the main checkout has an uncommitted edit elsewhere: it lands at once, says so
     once, knocks pike once, and the edit is untouched (until 14 Oct it waited until the edit was committed)
  2. an uncommitted edit in a file the branch changes, other lines: it lands, the card says the edit was kept on a
     parked/ branch and put back, and the edit is in the file over the landing
  3. a branch that fails the checks: commission=reverted, the card says main never had it, main has not moved
  4. a branch with nothing beyond main: back to working, said once
  5. a branch that does not merge: back to working, told to merge main into it
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
NOTATION = "research/text-desk-lab/notation"
tmp = tempfile.TemporaryDirectory()
REPO = Path(tmp.name) / "live"
os.environ["LANDING_LIVE"] = str(REPO)
os.environ["LANDING_ROOM"] = str(Path(tmp.name) / "room")

import roomworld   # noqa: E402
import house       # noqa: E402
import rooms       # noqa: E402
import workshop    # noqa: E402
import landing     # noqa: E402

fails = []
WAITING = "ready, and waiting to land"     # how the house began a wait on a card until 14 Oct


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
        from desk import split_batch           # ; outside quotes, as the house's own act splits a line
        out = say(who, *[p.strip() for p in split_batch(line)])
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


ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def git(*args):
    r = subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, env=ENV)
    assert r.returncode == 0, (args, r.stdout, r.stderr)
    return r.stdout.strip()


def write(name, text, msg=None):
    p = REPO / NOTATION / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    if msg:
        git("add", "--", f"{NOTATION}/{name}")
        git("commit", "-q", "-m", msg)


def read(name):
    return (REPO / NOTATION / name).read_text(encoding="utf-8")


REPO.mkdir()
git("init", "-q", "-b", "main")
git("config", "core.autocrlf", "false")
write("a.py", "a = 1\n")
write("b.js", "".join(f"b{i} = {i}\n" for i in range(12)))
write(".gitignore", "house-state/\nsessions/\n")
git("add", "-A")
git("commit", "-q", "-m", "start")

_git = workshop.git
workshop.git = lambda *a, cwd=REPO, **k: _git(*a, cwd=cwd, **k)     # its default cwd is the real checkout
workshop.REPO = REPO
landing.health = lambda world, cwd: ({"ok": False, "lenses_ok": [], "failed": ["BROKEN is here"], "text": "broken"}
                                     if (Path(cwd) / "BROKEN").exists() else
                                     {"ok": True, "lenses_ok": [], "failed": [], "text": "all well"})
WS = workshop.Workshop(House())
WS.export_docs = lambda cid: ""
WS.compare_lived = lambda w: None
WS.finish = lambda cid, wk, keep_branch: None


def commission(title, files, base="main"):
    t = say("pike", f"look {B} :1", f'do create {B} kind=task title="{title}" owner=pike asked_by=pike status=open')
    card = re.findall(r"created (a\d+)", t)[-1]
    say("pike", f"look {card} :1", f"do prop {card} commission=asked")
    say("house", f"look {card} :1", f"do prop {card} commission=ready")
    git("checkout", "-q", "-b", f"worker/{card}", base)
    for name, text in files.items():
        write(name, text)
    git("add", "-A")
    git("commit", "-q", "-m", f"{card}: {title}")
    git("checkout", "-q", "main")
    return card, W.nodes[card]["subject"], Wk(card)


def house_said(sid, since):
    """-> (the house's comments on the card since event `since`, how many of them knock pike)."""
    said = [e for e in W.events[since:] if e["by"] == "house" and e["verb"] == "comment"
            and (e["target"] == sid or (W.nodes.get(e["target"]) or {}).get("subject") == sid)]
    knocks = [e for e in said if (rooms.reached(W, e) or {}).get("pike") == "call"]
    return said, knocks


def text(e):
    return " ".join(str(v) for v in (e.get("args") or {}).values() if isinstance(v, str))


def state(sid):
    return (W.subjects[sid].get("props") or {}).get("commission")


def land(card, sid, wk):
    WS.land(W, card, W.subjects[sid], wk)


# ---- 1. ready, with someone's uncommitted edit elsewhere: lands at once ----------------------------------------------
K1, S1, wk1 = commission("Doors", {"doors.py": "# Doors\n"})
start = len(W.events)
write("a.py", "a = 2  # Alex, by hand, not committed\n")
land(K1, S1, wk1)
said, knocks = house_said(S1, start)
check("1. it lands at once: commission=landed, and the card says so once", state(S1) == "landed" and len(said) == 1
      and text(said[0]).startswith("landed as ") and not any(WAITING in text(e) for e in said), [text(e) for e in said])
check("1. pike is knocked once, for the landing", len(knocks) == 1, [text(e) for e in knocks])
check("1. the uncommitted edit is untouched, and main has the landing", read("a.py").startswith("a = 2  # Alex")
      and read("doors.py") == "# Doors\n", read("a.py"))

# ---- 2. an uncommitted edit in a file the branch changes, on other lines ---------------------------------------------
K2, S2, wk2 = commission("Bees", {"b.js": read("b.js").replace("b1 = 1\n", "b1 = 'one'\n")})
write("b.js", read("b.js").replace("b10 = 10\n", "b10 = 'ten, by hand'\n"))
mark = len(W.events)
land(K2, S2, wk2)
said, _ = house_said(S2, mark)
check("2. it lands, and the card says the edit was kept on a parked/ branch and put back", state(S2) == "landed"
      and "parked/" in text(said[0]) and "put back" in text(said[0]), [text(e) for e in said])
check("2. the edit is in the file, over the landing", "b1 = 'one'" in read("b.js") and "b10 = 'ten, by hand'" in read("b.js"),
      read("b.js"))
git("checkout", "--", f"{NOTATION}/b.js")

# ---- 3. a branch that fails the checks ------------------------------------------------------------------------------
was = git("rev-parse", "HEAD")
K3, S3, wk3 = commission("Broken", {"BROKEN": "x\n"})
mark = len(W.events)
land(K3, S3, wk3)
said, knocks = house_said(S3, mark)
check("3. commission=reverted, the card says main never had it, and why", state(S3) == "reverted" and len(said) == 1
      and "Main never had it" in text(said[0]) and "BROKEN is here" in text(said[0]), [text(e) for e in said])
check("3. main has not moved", git("rev-parse", "HEAD") == was and not (REPO / NOTATION / "BROKEN").exists())
check("3. the worker is told, and pike knocked once", any("did not land" in h for h in wk3.heard) and len(knocks) == 1,
      (wk3.heard, [text(e) for e in knocks]))

# ---- 4. nothing beyond main ------------------------------------------------------------------------------------------
K4, S4, wk4 = commission("Nothing", {"nothing.txt": "n\n"})
git("branch", "-q", "-f", f"worker/{K4}", "main")
mark = len(W.events)
land(K4, S4, wk4)
said, _ = house_said(S4, mark)
check("4. nothing to land: back to working, said once", state(S4) == "working" and len(said) == 1
      and "nothing to land" in text(said[0]), [text(e) for e in said])

# ---- 5. does not merge -----------------------------------------------------------------------------------------------
K5, S5, wk5 = commission("Clash", {"doors.py": "# a different door\n"}, base=git("rev-list", "--max-parents=0", "HEAD"))
mark = len(W.events)
land(K5, S5, wk5)
said, _ = house_said(S5, mark)
check("5. does not merge: back to working, told to merge main into the branch", state(S5) == "working"
      and "does not merge" in text(said[0]) and "git merge main" in text(said[0]), [text(e) for e in said])

# ---- 6. the house's pass does not wait on the judging ---------------------------------------------------------------
# Codex e9951, 14 Oct: the house's beat stopped for the minutes a landing's health ran inside its pass
import time   # noqa: E402
K6, S6, wk6 = commission("Slow", {"slow.py": "# slow\n"})
wk6.busy, wk6.alive, wk6.turns_ended = False, (lambda: True), (lambda: [])
WS.workers[K6] = wk6
fast = landing.health
landing.health = lambda world, cwd: (time.sleep(1.5), fast(world, cwd))[1]
try:
    mark = len(W.events)
    t0 = time.perf_counter()
    WS.step(W, {"workers": "1"})
    took = time.perf_counter() - t0
    check("6. a pass that starts a landing returns before it is judged; the card says landing", took < 1.0
          and state(S6) == "landing" and K6 in WS.landing, (round(took, 2), state(S6)))
    WS.landing[K6]["thread"].join(30)
    WS.step(W, {"workers": "1"})
    said, knocks = house_said(S6, mark)
    check("6. the pass after it ends says the outcome, once: landed", state(S6) == "landed" and K6 not in WS.landing
          and [text(e) for e in said if text(e).startswith("landed as ")] and len(knocks) == 1, [text(e) for e in said])
finally:
    landing.health = fast
    WS.workers.pop(K6, None)

print(f"{len(fails)} FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
