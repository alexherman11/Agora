# health: room test (health.py runs every test_*.py with this line among its first ten)
"""test_landing_return: a landing that does not land is never a dead end (a5292). It goes back to its worker with the
failure, started again if its process is gone; if the worker cannot come back, the card is the asker's, with the
failure and the branch named. The keeper's revert names the landing it reverts, never HEAD (a4919).

    python test_landing_return.py

As test_landing_wait: a small world in memory (roomworld.py) and a git repository of its own in a temporary folder,
laid out as the lab is, landed through landing.py with health stubbed (it fails when the judged code holds a file
BROKEN). The worker is a stand-in that keeps its state as state.json would (a restart of the house keeps it), whose
process can be stopped, and which says when its turn ends. Who a house comment knocks is read by rooms.reached.
  1. a branch that fails: commission=reverted, the worker is told the failure, pike knocked once
  2. its turn ends with no ready and no question: commission=waiting, and pike is told once, with its last words;
     a worker that asked (mark=ask) is not reported again
  3. a4869: reverted, the failure delivered, then the house restarts mid-turn: the new house resumes the worker, tells
     it to carry on, and a comment to it is heard
  4. ready again while its process is gone: refused, started again on its conversation and told
  5. the same card once its worker is stopped and gone (no worktree, no conversation): commission=failed, pike knocked
     once, the card names the failure, the branch at its commit, and what to do
  6. re-asked: its worker starts on the branch and is told the failure first
  7. three refusals in a row: handed to the asker, the worker stopped
  8. the keeper: a landing with a docs commit on top is reverted by its hash (HEAD is not it), the commit names it,
     and reverts.jsonl records it; the house returns the card (reverted, branch put back) and the worker hears the
     keeper's failure, with what the house printed
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"
NOTATION = "research/text-desk-lab/notation"
sys.path.insert(0, str(HERE.parents[1] / "window-lab"))
import agora_tmp
from types import SimpleNamespace
import atexit
import shutil
tmp = SimpleNamespace(name=agora_tmp.directory("landing-regression-"))
atexit.register(shutil.rmtree, tmp.name, ignore_errors=True)
TMP = Path(tmp.name)
REPO = TMP / "live"
os.environ["LANDING_LIVE"] = str(REPO)
os.environ["LANDING_ROOM"] = str(TMP / "room")

import roomworld   # noqa: E402
import house       # noqa: E402,F401  (Worker's machinery; never started here)
import rooms       # noqa: E402
import workshop    # noqa: E402
import landing     # noqa: E402
import keeper      # noqa: E402
import door        # noqa: E402

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


class House:
    world = "roomworld-inmemory"
    dir = TMP / "house-state"

    def load(self):
        return W

    def act(self, who, line):
        from desk import split_batch
        out = say(who, *[p.strip() for p in split_batch(line)])
        if "ERR" in out:
            print("house refused:", line[:120], "->", out[-300:])
        return out

    def settings(self, w):
        return {"model": "stand-in"}


STORE = {}     # cid -> a worker's saved state, as house-state/worker-<cid>/state.json outlives its process


class Wk:
    """A worker as the workshop uses one: its saved state, a process that runs or not, what it was sent, its turns."""
    def __init__(self, house_, cid, tree, branch, asked_by):
        self.cid, self.tree, self.branch, self.asked_by, self.actor = cid, Path(tree), branch, asked_by, f"worker-{cid}"
        self.state = STORE.setdefault(cid, {})
        self.running, self.busy, self.heard, self.ended, self.starts = False, False, [], [], 0

    def save(self):
        pass

    def log(self, *a):
        pass

    def alive(self):
        return self.running

    def start(self, model, world, s):
        self.running, self.busy, self.starts = True, False, self.starts + 1
        self.state.setdefault("session", f"session-{self.cid}")     # its init event names one

    def stop(self):
        self.running = False

    def send(self, text, kind="news", carry=None):
        self.state["pending"] = {"carry": text, "delivered": False}
        if not self.running:
            return
        self.state["pending"]["delivered"] = True
        self.heard.append(text)
        self.busy = True

    def end_turn(self, text):
        self.busy = False
        self.state["turns"] = self.state.get("turns", 0) + 1
        self.state.pop("pending", None)
        self.state.setdefault("said", []).append({"text": text})
        self.ended.append(text)

    def turns_ended(self):
        out, self.ended = self.ended, []
        return out


ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def git(*args):
    r = subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, env=ENV)
    assert r.returncode == 0, (args, r.stdout, r.stderr)
    return r.stdout.strip()


def write(name, text):
    p = REPO / NOTATION / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


REPO.mkdir()
git("init", "-q", "-b", "main")
git("config", "core.autocrlf", "false")
for k in ("user.name", "user.email"):
    git("config", k, "t@t" if k.endswith("email") else "t")
write("a.py", "a = 1\n")
write(".gitignore", "house-state/\nsessions/\n")
git("add", "-A")
git("commit", "-q", "-m", "start")

TREES = TMP / "trees"
TREES.mkdir()
_git = workshop.git
workshop.git = lambda *a, cwd=REPO, **k: _git(*a, cwd=cwd, **k)     # its default cwd is the real checkout
workshop.REPO = REPO
workshop.TREES = TREES
workshop.Worker = Wk
workshop.REVERTS = TMP / "keeper" / "house-state" / "reverts.jsonl"
door.copy_locked = lambda src, to: "not copied in this test"          # never a lock in the lab's own sessions/
landing.health = lambda world, cwd, **how: ({"ok": False, "lenses_ok": [], "failed": ["BROKEN is here"], "text": "broken"}
                                     if (Path(cwd) / "BROKEN").exists() else
                                     {"ok": True, "lenses_ok": [], "failed": [], "text": "all well"})


def finish(ws):
    def f(cid, wk, keep_branch):        # as Workshop.finish, with no real worktree to commit or remove
        wk.stop()
        ws.workers.pop(cid, None)
        if wk.tree.exists() and not (wk.tree / ".git").exists():
            shutil.rmtree(wk.tree)
        f.calls.append((cid, keep_branch))
    f.calls = []
    return f


def workshop_():
    ws = workshop.Workshop(House())
    ws.export_docs = lambda cid: ""
    ws.compare_lived = lambda w: None
    ws.finish = finish(ws)
    ws.real_tree = lambda tree: Path(tree).exists()
    return ws


WS = workshop_()
CFG = {"workers": "4", "model": "stand-in"}


def commission(title, files):
    """A card asked by pike, its worker running in its worktree, its branch committed, commission=ready."""
    t = say("pike", f"look {B} :1", f'do create {B} kind=task title="{title}" owner=pike asked_by=pike status=open')
    card = re.findall(r"created (a\d+)", t)[-1]
    say("pike", f"look {card} :1", f"do prop {card} commission=asked")
    say("house", f"look {card} :1", f"do prop {card} commission=ready worker=worker-{card}")
    git("checkout", "-q", "-b", f"worker/{card}", "main")
    for name, text in files.items():
        write(name, text)
    git("add", "-A")
    git("commit", "-q", "-m", f"{card}: {title}")
    git("checkout", "-q", "main")
    (TREES / card).mkdir()
    wk = Wk(None, card, TREES / card, f"worker/{card}", "pike")
    wk.start("stand-in", House.world, None)
    wk.state["cursor"] = len(W.events)          # begin sets where its hearing starts
    WS.workers[card] = wk
    return card, W.nodes[card]["subject"], wk


def on_branch(card, files, delete=()):
    git("checkout", "-q", f"worker/{card}")
    for name, text in files.items():
        write(name, text)
    for name in delete:
        (REPO / NOTATION / name).unlink()
    git("add", "-A")
    git("commit", "-q", "-m", f"{card}: again")
    git("checkout", "-q", "main")


def house_said(sid, since):
    said = [e for e in W.events[since:] if e["by"] == "house" and e["verb"] == "comment"
            and (e["target"] == sid or (W.nodes.get(e["target"]) or {}).get("subject") == sid)]
    knocks = [e for e in said if (rooms.reached(W, e) or {}).get("pike") == "call"]
    return said, knocks


def text(e):
    return " ".join(str(v) for v in (e.get("args") or {}).values() if isinstance(v, str))


def state(sid):
    return (W.subjects[sid].get("props") or {}).get("commission")


def ready(card):
    say("house", f"look {card} :1", f"do prop {card} commission=ready")


def land(card, sid, wk):
    WS.land(W, card, W.subjects[sid], wk)


# ---- 1. a branch that fails: back to its worker -----------------------------------------------------------------------
K1, S1, wk1 = commission("Broken one", {"BROKEN": "x\n"})
mark = len(W.events)
land(K1, S1, wk1)
said, knocks = house_said(S1, mark)
check("1. commission=reverted, the card says why, pike knocked once", state(S1) == "reverted" and len(said) == 1
      and "BROKEN is here" in text(said[0]) and len(knocks) == 1, [text(e) for e in said])
check("1. its worker is told the failure, and it counts as told", len(wk1.heard) == 1 and "BROKEN is here" in wk1.heard[0]
      and wk1.state["failure"]["told"] is True, wk1.heard)

# ---- 2. its turn ends with no ready and no question --------------------------------------------------------------------
wk1.end_turn("I looked at it.\nI am not sure what BROKEN is.")
mark = len(W.events)
WS.step(W, CFG)
WS.step(W, CFG)
said, knocks = house_said(S1, mark)
check("2. commission=waiting, and pike is told once, with its last words", state(S1) == "waiting" and len(said) == 1
      and len(knocks) == 1 and "It waits on you" in text(said[0]) and "not sure what BROKEN is" in text(said[0]),
      [text(e) for e in said])

K2, S2, wk2 = commission("Broken two", {"BROKEN": "w\n"})
land(K2, S2, wk2)
asked = say(wk2.actor, f"look {K2} :1", f'do comment {K2} line="is BROKEN meant to be there?" mark=ask')
wk2.end_turn("Asked pike.")
mark = len(W.events)
WS.step(W, CFG)
said, _ = house_said(S2, mark)
check("2. a worker that asked (mark=ask) is waiting, and the house adds nothing", state(S2) == "waiting" and not said
      and "ERR" not in asked, (asked[-200:], [text(e) for e in said]))

# ---- 3. a4869: the house restarts while the worker is on its failure --------------------------------------------------
K3, S3, wk3 = commission("Broken three", {"BROKEN": "y\n"})
land(K3, S3, wk3)
check("3. (set up) reverted, the failure delivered and its turn under way",
      state(S3) == "reverted" and wk3.busy and wk3.state["pending"]["delivered"])
wk3.stop()                                          # the house's restart takes its process with it
WS.workers.pop(K3)
WS = workshop_()                                    # the new house: it has no workers yet
WS.workers.update({K1: wk1})
mark = len(W.events)
WS.step(W, CFG)
back = WS.workers.get(K3)
check("3. the new house resumes it, and tells it to carry on from the failure", back is not None and back.alive()
      and any("My last message to you is above" in h for h in back.heard), back and back.heard)
back.end_turn("Fixing it now.")
say("pike", f"look {K3} :1", f'do comment {K3} line="take BROKEN out, it was a probe"')
WS.step(W, CFG)
check("3. a comment to it after the restart is heard", any("take BROKEN out" in h for h in back.heard), back.heard)
wk3 = back

# ---- 4. ready again while its process is gone ---------------------------------------------------------------------------
wk3.end_turn("Not yet.")
wk3.stop()
ready(K3)
starts = wk3.starts
mark = len(W.events)
land(K3, S3, wk3)
said, knocks = house_said(S3, mark)
check("4. refused, started again on its conversation and told", state(S3) == "reverted" and wk3.alive()
      and wk3.starts == starts + 1 and "process had stopped" in wk3.heard[-1] and "BROKEN is here" in wk3.heard[-1]
      and WS.workers.get(K3) is wk3, wk3.heard[-1:])
check("4. pike is knocked once, for the refusal", len(knocks) == 1, [text(e) for e in said])

# ---- 5. the same card once its worker is stopped and gone ----------------------------------------------------------------
wk3.end_turn("Stopping here.")
wk3.stop()
shutil.rmtree(wk3.tree)
wk3.state.pop("session")
wk3.state["returns"] = 0           # this step is about a worker that is gone, not about how many times it failed
ready(K3)
mark = len(W.events)
land(K3, S3, wk3)
said, knocks = house_said(S3, mark)
sha = git("rev-parse", "--short", f"worker/{K3}")
check("5. commission=failed: it is the asker's, said once, pike knocked once", state(S3) == "failed" and len(said) == 1
      and len(knocks) == 1, [text(e) for e in said])
check("5. the card says why, what failed, the branch at its commit, and what to do",
      said and "handed back to pike" in text(said[0]) and "worktree is gone" in text(said[0])
      and "BROKEN is here" in text(said[0]) and f"worker/{K3} is kept at {sha}" in text(said[0])
      and "commission=asked" in text(said[0]), said and text(said[0]))
WS.step(W, CFG)
check("5. nothing more is said on it", len(house_said(S3, mark)[0]) == 1)

# ---- 6. re-asked: its worker starts on the branch and is told the failure first ---------------------------------------
STORE[K3]["session"] = f"session-{K3}"
say("pike", f"look {K3} :1", f"do prop {K3} commission=asked")
WS.step(W, CFG)
again = WS.workers.get(K3)
check("6. its worker starts in a new worktree on its branch, told the commission and the failure", again is not None
      and state(S3) == "working" and again.heard and "Your commission" in again.heard[0]
      and "did not land" in again.heard[0] and "BROKEN is here" in again.heard[0], again and again.heard)
check("6. the worktree is on the kept branch", (TREES / K3 / NOTATION / "BROKEN").exists())

# ---- 7. three refusals in a row -----------------------------------------------------------------------------------------
K7, S7, wk7 = commission("Broken seven", {"BROKEN": "z\n"})
for i in range(3):
    if i:
        wk7.end_turn("tried")
        ready(K7)
    mark = len(W.events)
    land(K7, S7, wk7)
said, _ = house_said(S7, mark)
check("7. the third refusal hands it to the asker and stops the worker", state(S7) == "failed" and not wk7.alive()
      and said and "refused 3 times in a row" in text(said[-1]), said and text(said[-1]))

# ---- 8. the keeper reverts a landing by its hash ------------------------------------------------------------------------
K8, S8, wk8 = commission("Lands then breaks the house", {"crash.py": "raise SystemExit(1)\n"})
land(K8, S8, wk8)
check("8. (set up) it landed", state(S8) == "landed", state(S8))
landed_at = (W.subjects[S8].get("props") or {}).get("landed")
write("notes.md", "docs export after the landing\n")
git("add", "-A")
git("commit", "-q", "-m", f"docs: Current Implementation after land {K8}")
docs = git("rev-parse", "HEAD")
git("branch", "-D", f"worker/{K8}")                 # a landing removes its branch
khere = TMP / "keeper"
(khere / "house-state").mkdir(parents=True)
(khere / "house-state" / "house.out").write_text("Traceback ...\nSystemExit: 1 from crash.py\n", encoding="utf-8")
keeper.REPO, keeper.HERE, keeper.LOG = REPO, khere, khere / "house-state" / "keeper.log"
found = keeper.last_landing()
check("8. the keeper finds the landing, not HEAD (the docs commit)", found and found["hash"].startswith(landed_at)
      and found["hash"] != docs, (found, docs))
entry = keeper.revert(found, "the house died 3 times in the 40 s after it landed", House.world)
body = git("log", "-1", "--format=%s%n%b")
check("8. the revert names the landing's hash and keeps the docs commit", entry and found["hash"] in body
      and K8 in body and not (REPO / NOTATION / "crash.py").exists() and (REPO / NOTATION / "notes.md").exists(), body)
check("8. a reverted landing is not found again", (keeper.last_landing() or {}).get("hash") != found["hash"])
rec = [json.loads(l) for l in workshop.REVERTS.read_text(encoding="utf-8").splitlines()]
check("8. reverts.jsonl records it: the card, the hash, the tip, the house's last words", len(rec) == 1
      and rec[0]["cid"] == K8 and rec[0]["hash"] == found["hash"] and rec[0]["tip"] and "crash.py" in rec[0]["tail"], rec)
mark = len(W.events)
WS.step(W, CFG)
said, knocks = house_said(S8, mark)
went = [e["args"].get("commission") for e in W.events[mark:] if e["verb"] == "prop" and e["args"].get("commission")]
check("8. the house returns the card: reverted, then asked for its worker, the branch put back at the tip, pike "
      "knocked once", went == ["reverted", "asked"] and git("rev-parse", f"worker/{K8}") == rec[0]["tip"] and len(knocks) == 1
      and said and "keeper reverted this landing" in text(said[0]), [text(e) for e in said])
for _ in range(3):
    WS.step(W, CFG)
back8 = WS.workers.get(K8)
check("8. its worker comes back on the branch and hears the keeper's failure, with what the house printed",
      back8 is not None and back8.heard and "reverted by the keeper" in back8.heard[0]
      and "crash.py" in back8.heard[0] and (TREES / K8 / NOTATION / "crash.py").exists(), back8 and back8.heard)
WS.step(W, CFG)
check("8. the card is returned once", sum("keeper reverted" in text(e) for e in house_said(S8, mark)[0]) == 1)

print(f"{len(fails)} FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
