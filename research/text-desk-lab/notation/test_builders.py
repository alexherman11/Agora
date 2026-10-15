"""test_builders: standing builders (a5378, Alex 15 Oct: persistent compacting workers with shared memory; the workers
can do everything Claude has been able to do).

    python test_builders.py

A small world in memory (roomworld.py) and a stand-in house, as test_worker_pool; the workshop's own step() runs with git,
the world copy and every process stubbed (Popen is caught: each start is a command line read, each message a line read).
  1. with "2 claude" in the pool, two cards in a row go to builder-1; the second start resumes the first's conversation,
     moved into the second card's worktree folder, and is told it is a new commission; the builder's state names both
  2. a worker_fresh=yes card gets a disposable worker, told it is one, never a builder
  3. one builder: an idle waiting card is set down for an asked one (its stop is not a failure); words for the waiting
     card keep it parked while the builder works; when the builder is free again it goes back, told it is back
  4. hand_to=builder-2 on a card: its builder sets it down at the end of its turn, builder-2 takes it, told who began it;
     the card says builder=builder-2 and hand_to is gone
  5. a house restart: a working builder card is resumed parked, then by its own builder, told its cut message is above
  6. a refused landing on a parked card waits for a builder, who is told the failure
  7. carry_conversation: the newest copy (and what claude keeps beside it) goes to the folder claude will look in
  8. a conversation that cannot be found: the builder starts fresh and is told so
  9. the protocol: the notebook rule (found by role), Alex's screen and the demo rule; a builder is told who it is
"""
import json
import os
import re
import sys
import tempfile
import time
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"
os.environ.setdefault("HOUSE_CLAUDE", "claude")     # the house looks for a claude binary at import; none is started here

import roomworld   # noqa: E402
import house       # noqa: E402,F401
import workshop    # noqa: E402
import door        # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:1500]}"))
    if not ok:
        fails.append(name)


D, R = roomworld.build(say=False)
W = D.world
B = R.BOARD
tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)     # the stubbed starts leave stderr.log open
TMP = Path(tmp.name)


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
    fake = None
    claude = "claude.exe"

    def __init__(self):
        self.dir = TMP / "house-state"
        self.dir.mkdir(exist_ok=True)

    def load(self):
        return W

    def settings(self, w):
        return dict(POOL)

    def act(self, who, line):
        from desk import split_batch
        out = say(who, *[p.strip() for p in split_batch(line)])
        if "ERR" in out or "refused" in out.lower():
            print("house refused:", line[:120], "->", out[-300:])
        return out


workshop.git = lambda *a, **k: SimpleNamespace(returncode=0, stdout="", stderr="")
workshop.TREES = TMP / "trees"
workshop.CLAUDE_PROJECTS = TMP / "projects"
workshop.Workshop.real_tree = staticmethod(lambda tree: True)
door.copy_locked = lambda a, b: None
procs = []


def new_proc(*a, **k):
    p = mock.MagicMock()
    p.poll.return_value = None          # alive until stopped
    p.pid = 4000 + len(procs)
    procs.append((a[0], p))
    return p


popen = mock.patch.object(workshop.subprocess, "Popen", side_effect=new_proc).start()
mock.patch.object(workshop.threading, "Thread").start()

H = House()
WS = workshop.Workshop(H)
WS.land = lambda w, cid, s, wk, wait=True: None
POOL = {"model": "claude-opus-5-5", "workers": "4", "worker_model": "", "worker_pool": "2 claude, 2 codex gpt-6-astra"}


def card(title, **props):
    extra = "".join(f" {k}={v}" for k, v in props.items())
    t = say("pike", f"look {B} :1", f'do create {B} kind=task title="{title}" owner=pike status=open{extra}')
    cid = re.findall(r"created (a\d+)", t)[-1]
    say("pike", f"look {cid} :1", f"do prop {cid} commission=asked")
    return cid


def props(cid):
    return W.subjects[W.nodes[cid]["subject"]].get("props") or {}


def setp(cid, **kv):
    say("pike", f"look {cid} :1", f"do prop {cid} " + " ".join(f"{k}={v}" for k, v in kv.items()))


def sent(p):
    """What the house wrote to one process, as text."""
    out = []
    for c in p.stdin.write.call_args_list:
        msg = json.loads(c.args[0])
        out.append("\n".join(b.get("text", "") for b in msg["message"]["content"]))
    return out


def last_proc(cid):
    return next(p for cmd, p in reversed(procs) if WS.workers[cid].proc is p) if WS.workers[cid].proc else None


def started_since(n):
    return procs[n:]


def end_turn(cid, session=None):
    wk = WS.workers[cid]
    if session:
        wk.events.put({"type": "system", "subtype": "init", "session_id": session})
    wk.events.put({"type": "result", "result": "done"})
    wk.turns_ended()


def conversation(session, tree):
    d = workshop.CLAUDE_PROJECTS / re.sub(r"[^A-Za-z0-9]", "-", str(Path(tree).resolve()))
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{session}.jsonl").write_text('{"remembers": "' + session + '"}\n', encoding="utf-8")
    return d / f"{session}.jsonl"


def builder_state(name):
    return workshop.Builder(H, name).state


def reset():
    for wk in list(WS.workers.values()):
        wk.stop()
    WS.workers.clear()
    for cid in list(WS.commissions(W)):
        setp(cid, commission="cancelled")
    WS.step(W, POOL)


# ---- 1. two cards in a row go to one builder, which remembers --------------------------------------------------------
first = card("Make the clock say noon")
n = len(procs)
WS.step(W, POOL)
cmd1, p1 = procs[n]
check("1. the first card goes to builder-1: the card says builder=builder-1 and worker=worker-<card>",
      props(first).get("builder") == "builder-1" and props(first).get("worker") == f"worker-{first}"
      and WS.workers[first].builder == "builder-1", props(first))
check("1. a fresh builder starts with no --resume, and is told it is builder-1 on a new commission",
      "--resume" not in cmd1 and "You are builder-1, on a new commission" in sent(p1)[0], (cmd1[-3:], sent(p1)[:1]))
conversation("S1", WS.workers[first].tree)
end_turn(first, session="S1")
check("1. the builder keeps its conversation, not only the card", builder_state("builder-1").get("session") == "S1",
      builder_state("builder-1"))
setp(first, commission="landed")
WS.finish(first, WS.workers[first], keep_branch=False)
second = card("Make the clock say midnight")
n = len(procs)
WS.step(W, POOL)
cmd2, p2 = procs[n]
check("1. the second card goes to builder-1 too, resuming S1",
      props(second).get("builder") == "builder-1" and cmd2[-2:] == ["--resume", "S1"], (props(second), cmd2[-2:]))
moved = workshop.CLAUDE_PROJECTS / re.sub(r"[^A-Za-z0-9]", "-", str(WS.workers[second].tree.resolve())) / "S1.jsonl"
check("1. its conversation was moved where claude looks from the second worktree", moved.exists(), moved)
check("1. it is told this is a new commission, in its own worktree", "on a new commission" in sent(p2)[0]
      and str(WS.workers[second].tree) in sent(p2)[0], sent(p2)[:1])
check("1. the builder's state names both cards, and it is on the second",
      builder_state("builder-1").get("cards") == [first, second] and builder_state("builder-1").get("on") == second,
      builder_state("builder-1"))
prompt2 = cmd2[cmd2.index("--append-system-prompt") + 1]
check("1. its system prompt says it is a standing builder signing as the card's worker",
      "You are builder-1, one of Agora's standing builders" in prompt2 and f"sign as worker-{second}" in prompt2,
      prompt2[-3000:][:600])
reset()

# ---- 2. worker_fresh=yes gets a disposable worker ------------------------------------------------------------------
fresh = card("Review it with fresh eyes", worker_fresh="yes")
n = len(procs)
WS.step(W, POOL)
cmd, p = procs[n]
fprompt = cmd[cmd.index("--append-system-prompt") + 1] if "--append-system-prompt" in cmd else ""
check("2. a worker_fresh card gets a disposable Claude worker: no builder, no resume, told it is disposable",
      WS.workers[fresh].builder is None and "builder" not in props(fresh) and "--resume" not in cmd
      and "a disposable builder for one commission" in fprompt and "standing builders" not in fprompt, (props(fresh), cmd[:3]))
reset()

# ---- 3. one builder: a waiting card is set down for an asked one, and taken back -------------------------------------
ONE = {**POOL, "worker_pool": "1 claude"}
POOL_SAVED, POOL = POOL, ONE
a = card("Card A waits on its asker")
WS.step(W, POOL)
end_turn(a, session="S3")
conversation("S3", WS.workers[a].tree)
setp(a, commission="waiting")
b = card("Card B is asked")
n = len(procs)
q_a = WS.workers[a].events                          # the queue card A's process says things into
WS.step(W, POOL)
check("3. the asked card takes the one builder; the waiting card is set down (no process) and keeps builder-1",
      props(b).get("builder") == "builder-1" and not WS.workers[a].alive() and WS.workers[a].builder == "builder-1"
      and len(procs) == n + 1 and procs[n][0][-2:] == ["--resume", "S3"], (props(b), len(procs) - n))
q_a.put({"type": "exit", "code": 0})        # what the stopped process says on its way out, late, into its own queue
say("pike", f"look {a} :1", f'do comment {a} line="Answer for A: noon, local time."')
n = len(procs)
WS.step(W, POOL)
check("3. words for the parked card while the builder works: it stays parked, and its set-down was no failure",
      not WS.workers[a].alive() and len(procs) == n and props(a).get("commission") == "waiting"
      and not WS.workers[a].state.get("failures"), (len(procs) - n, props(a), WS.workers[a].state.get("failures")))
end_turn(b)
setp(b, commission="waiting")
n = len(procs)
WS.step(W, POOL)
pa = WS.workers[a].proc
check("3. the builder is free: the parked card takes it back, is working, and hears the answer, told it is back",
      WS.workers[a].alive() and not WS.workers[b].alive() and props(a).get("commission") == "working"
      and any("back on commission " + a in t and "Answer for A" in t for t in sent(pa)), sent(pa) if pa else None)
reset()
POOL = POOL_SAVED

# ---- 4. hand_to ------------------------------------------------------------------------------------------------------
h = card("Handed on")
WS.step(W, POOL)
end_turn(h, session="S4")
conversation("S4", WS.workers[h].tree)
setp(h, hand_to="builder-2")
n = len(procs)
WS.step(W, POOL)
ph = WS.workers[h].proc
check("4. hand_to=builder-2: builder-2 takes it, told who began it; builder=builder-2, hand_to gone",
      props(h).get("builder") == "builder-2" and "hand_to" not in props(h) and WS.workers[h].builder == "builder-2"
      and len(procs) == n + 1 and any("taking over commission " + h in t and "builder-1 handed it to you" in t
                                      for t in sent(ph)), (props(h), [t[:200] for t in sent(ph)] if ph else None))
check("4. builder-2 starts on its own conversation (none yet), not builder-1's", "--resume" not in procs[n][0],
      procs[n][0][-2:])
reset()

# ---- 5. a house restart --------------------------------------------------------------------------------------------
r = card("Cut by a restart")
WS.step(W, POOL)
end_turn(r, session="S5")
conversation("S5", WS.workers[r].tree)
WS.workers[r].tree.mkdir(parents=True, exist_ok=True)     # its worktree (git is stubbed): a restart finds it
say("pike", f"look {r} :1", f'do comment {r} line="Please also check the tests."')
WS.step(W, POOL)                                    # it hears the comment: a message is out, delivered
check("5. (setup) the comment went out to builder-1", WS.workers[r].busy and (WS.workers[r].state.get("pending") or {}).get("delivered"),
      WS.workers[r].state.get("pending"))
WS2 = workshop.Workshop(H)                          # the house restarted: no process here
WS2.land = WS.land
n = len(procs)
WS2.step(W, POOL)
pr = WS2.workers[r].proc
check("5. after a restart the card goes back to its own builder, on S5, told its last message is above",
      WS2.workers[r].builder == "builder-1" and len(procs) == n + 1 and procs[n][0][-2:] == ["--resume", "S5"]
      and any("My last message to you is above" in t for t in sent(pr)), [t[:200] for t in sent(pr)] if pr else None)
WS2.workers.clear()
WS.workers[r].proc = None
reset()

# ---- 6. a refused landing on a parked card -----------------------------------------------------------------------------
POOL = ONE
f = card("Not landed")
WS.step(W, POOL)
end_turn(f, session="S6")
conversation("S6", WS.workers[f].tree)
setp(f, commission="ready")
other = card("Takes the builder meanwhile")
WS.step(W, POOL)
check("6. (setup) the ready card's builder went to the other card", not WS.workers[f].alive()
      and props(other).get("builder") == "builder-1", props(other))
WS.returned(f, W.subjects[W.nodes[f]["subject"]], WS.workers[f], "reverted", "it failed the checks",
            "~ house: your branch failed the checks in the landing room")
check("6. the refused card waits, parked: no worker started over the builder's head",
      not WS.workers[f].alive() and props(f).get("commission") == "reverted", props(f))
end_turn(other)
setp(other, commission="waiting")
WS.step(W, POOL)
pf = WS.workers[f].proc
check("6. when the builder is free it takes the card back and is told the failure",
      WS.workers[f].alive() and any("failed the checks in the landing room" in t for t in sent(pf)),
      [t[:200] for t in sent(pf)] if pf else None)
reset()
POOL = POOL_SAVED

# ---- 7. carry_conversation ---------------------------------------------------------------------------------------------
proj = TMP / "proj7"
old = proj / "C--old" / "S7.jsonl"
new = proj / "C--newer" / "S7.jsonl"
for path, text in ((old, "old"), (new, "new")):
    path.parent.mkdir(parents=True)
    path.write_text(text, encoding="utf-8")
os.utime(old, (time.time() - 100, time.time() - 100))
(proj / "C--newer" / "S7" / "tool-results").mkdir(parents=True)
(proj / "C--newer" / "S7" / "tool-results" / "r.txt").write_text("kept", encoding="utf-8")
tree = TMP / "trees" / "a7"
ok = workshop.carry_conversation("S7", tree, proj)
here = proj / re.sub(r"[^A-Za-z0-9]", "-", str(tree.resolve()))
check("7. the newest copy is put in the folder named for the worktree, with what claude keeps beside it",
      ok and (here / "S7.jsonl").read_text(encoding="utf-8") == "new" and (here / "S7" / "tool-results" / "r.txt").exists(),
      sorted(p.name for p in proj.iterdir()))
check("7. no conversation anywhere: False", workshop.carry_conversation("nope", tree, proj) is False)

# ---- 8. a lost conversation ---------------------------------------------------------------------------------------------
st = workshop.Builder(H, "builder-1")
st.state["session"] = "gone-for-good"
st.save()
lost = card("After the conversation was lost")
n = len(procs)
WS.step(W, POOL)
cmd, p = procs[n]
check("8. a builder whose conversation cannot be found starts fresh, is told so, and forgets the old id",
      "--resume" not in cmd and any("fresh memory" in t for t in sent(p)) and "session" not in builder_state("builder-1"),
      ([t[:300] for t in sent(p)], builder_state("builder-1")))
reset()

# ---- 9. the protocol ---------------------------------------------------------------------------------------------------
P = workshop.PROTOCOL
check("9. the protocol reads the notebook rule: found by role, read before, an entry before the done comment",
      "find role=builders-notebook" in P and "Before you start, read it" in P and "Before your done comment, add" in P
      and "your notebook entry" in P, P[:200])
check("9. the protocol says how to see and record Alex's screen, and the demo rule",
      "screen_tools.py look" in P and "screen_tools.py record" in P and "research/window-lab/demos/" in P
      and "say on the card what will appear" in P and "names its recording" in P)
codex = card("A Codex card", worker_provider="codex")
WS.step(W, POOL)
cp = (WS.workers[codex].dir / "worker-prompt.txt").read_text(encoding="utf-8")
check("9. a Codex worker's prompt has the notebook rule too, and is a disposable worker",
      "find role=builders-notebook" in cp and "a disposable builder" in cp and WS.workers[codex].builder is None)
reset()

mock.patch.stopall()
print(f"{len(fails)} FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
