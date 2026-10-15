"""test_worker_pool: the house's worker pool (a5284, Alex 15 Oct: two Claude workers and two Astra workers) and slots
that count only workers running a model (a5261 point 1: a ready or landing card held one, and runs none).

    python test_worker_pool.py

A small world in memory (roomworld.py) and a stand-in house; the workshop's own step() and begin() run, with git,
the world copy and the worker's process stubbed: Popen is caught, so each start is a command line read, never a model.
  1. "2 claude, 2 codex gpt-6-astra" with workers=4 and five asked cards: one pass starts four, two `claude -p` and two
     codex_worker.py --model gpt-6-astra; each card says the provider it got; the fifth waits
  2. a ready card and a landing card hold no slot: the fifth starts in the lane they free; a busy ready worker (a landing
     sent it back to work) still holds one
  3. a card that names worker_provider=codex waits while the codex lane is full, even with Claude room free
  4. a re-asked card goes back to the provider its saved conversation belongs to, never the other lane
  5. no worker_pool: every card runs as it says, Claude unless it names codex, bounded by workers alone (as before)
  6. a codex card that names no model runs the adapter's own (gpt-6.1-sol), never the house's Claude model
  7. worker_pool it cannot read is no pool; one lane per provider
  8. a Codex worker's uncommitted work is committed to its branch by the house when it lands (its sandbox cannot)
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"
os.environ.setdefault("HOUSE_CLAUDE", "claude")     # the house looks for a claude binary at import; none is started here

import roomworld   # noqa: E402
import house       # noqa: E402
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
tmp = tempfile.TemporaryDirectory()
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

    def act(self, who, line):
        from desk import split_batch
        out = say(who, *[p.strip() for p in split_batch(line)])
        if "ERR" in out:
            print("house refused:", line[:120], "->", out[-300:])
        return out


# ---- stubs: no worktree, no world copy, no process -------------------------------------------------------------------
real_git = workshop.git
workshop.git = lambda *a, **k: SimpleNamespace(returncode=0, stdout="", stderr="")
workshop.TREES = TMP / "trees"
workshop.Workshop.real_tree = staticmethod(lambda tree: True)
door.copy_locked = lambda a, b: None
popen = mock.patch.object(workshop.subprocess, "Popen").start()
popen.return_value.poll.return_value = None          # alive
popen.return_value.pid = 4242
mock.patch.object(workshop.threading, "Thread").start()

H = House()
WS = workshop.Workshop(H)
landed = []
WS.land = lambda w, cid, s, wk, wait=True: landed.append(cid)      # what a ready card would do: not this test's


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


def commands():
    return [c.args[0] for c in popen.call_args_list]


def provider_of_cmd(cmd):
    if cmd[0] == "claude.exe" and cmd[1] == "-p":
        return "claude", cmd[cmd.index("--model") + 1]
    if Path(cmd[1]).name == "codex_worker.py":
        return "codex", cmd[cmd.index("--model") + 1]
    return "?", ""


def reset():
    """Every worker gone and every commission so far cancelled: the next part starts with an empty pool."""
    WS.workers.clear()
    popen.reset_mock()
    for cid in list(WS.commissions(W)):
        setp(cid, commission="cancelled")


POOL = {"model": "claude-opus-5-5", "workers": "4", "worker_model": "", "worker_pool": "2 claude, 2 codex gpt-6-astra"}

# ---- 1. four start at once, two on each provider; the fifth waits ---------------------------------------------------
cards = [card(f"Pooled {i}") for i in range(5)]
WS.step(W, POOL)
got = [provider_of_cmd(c) for c in commands()]
check("1. one pass starts four workers: two claude -p, two codex_worker.py on gpt-6-astra",
      sorted(got) == [("claude", "claude-opus-5-5")] * 2 + [("codex", "gpt-6-astra")] * 2, got)
check("1. each started card says the provider (and the Astra model) it got, and is working",
      sorted((props(c).get("worker_provider"), props(c).get("worker_model"), props(c).get("commission")) for c in cards[:4])
      == [("claude", None, "working")] * 2 + [("codex", "gpt-6-astra", "working")] * 2,
      [(props(c).get("worker_provider"), props(c).get("worker_model"), props(c).get("commission")) for c in cards])
check("1. the fifth waits, asked, with no provider chosen", props(cards[4]).get("commission") == "asked"
      and "worker_provider" not in props(cards[4]) and cards[4] not in WS.workers, props(cards[4]))
claude_cmd = next(c for c in commands() if c[0] == "claude.exe")
check("1. a Claude worker is claude -p with stream-json, acceptEdits, its allowed tools and the desk MCP only",
      all(f in claude_cmd for f in ("-p", "--input-format", "--permission-mode", "acceptEdits", "--allowedTools",
                                    "--strict-mcp-config", "--append-system-prompt")), claude_cmd[:12])

# ---- 2. ready and landing hold no slot ------------------------------------------------------------------------------
claude_cards = [c for c in cards[:4] if props(c).get("worker_provider") == "claude"]
codex_cards = [c for c in cards[:4] if props(c).get("worker_provider") == "codex"]
for c in cards[:4]:
    WS.workers[c].busy = False                       # every turn ended
for c in claude_cards + codex_cards:
    setp(c, commission="waiting")
setp(claude_cards[0], commission="working")
setp(claude_cards[1], commission="ready")
setp(codex_cards[0], commission="landing")
setp(codex_cards[1], commission="working")
WS.landing = {codex_cards[0]: {"thread": SimpleNamespace(is_alive=lambda: True), "result": None}}    # being judged
popen.reset_mock()
WS.step(W, POOL)
check("2. with one ready (idle) Claude card, the fifth starts, on Claude (the lane the ready card freed)",
      cards[4] in WS.workers and props(cards[4]).get("worker_provider") == "claude"
      and [provider_of_cmd(c)[0] for c in commands()] == ["claude"], (props(cards[4]), commands()))
WS.landing = {}
sixth = card("Pooled 5")
popen.reset_mock()
WS.step(W, POOL)
check("2. the landing Codex card held no slot either: the sixth starts on codex",
      sixth in WS.workers and props(sixth).get("worker_provider") == "codex", props(sixth))
seventh = card("Pooled 6")
WS.workers[claude_cards[1]].busy = True               # the landing sent its worker back to work: a turn is out
popen.reset_mock()
WS.step(W, POOL)
check("2. a ready card whose worker is mid-turn holds its slot: the seventh waits (all four slots taken)",
      seventh not in WS.workers and props(seventh).get("commission") == "asked", sorted(WS.workers))

# ---- 3. a card held to codex waits while codex is full ---------------------------------------------------------------
reset()
popen.reset_mock()
a, b2, c3 = card("Sol one", worker_provider="codex"), card("Sol two", worker_provider="codex"), card("Sol three", worker_provider="codex")
WS.step(W, POOL)
check("3. three cards that name codex: two start (the codex lane), the third waits though Claude has room",
      [provider_of_cmd(c)[0] for c in commands()] == ["codex", "codex"] and c3 not in WS.workers
      and props(c3).get("commission") == "asked", commands())
check("3. a card that named its provider keeps its own props: no worker_model written over it",
      "worker_model" not in props(a), props(a))

# ---- 4. a re-asked card goes back to its conversation's provider ------------------------------------------------------
reset()
back = card("Back again")
d = H.dir / f"worker-{back}"
d.mkdir(parents=True, exist_ok=True)
(d / "state.json").write_text(json.dumps({"session": "s-1", "session_provider": "codex"}), encoding="utf-8")
fill = [card(f"Claude fill {i}") for i in range(2)]
popen.reset_mock()
WS.step(W, POOL)
check("4. a card whose saved conversation is Codex's starts on codex, resuming it",
      props(back).get("worker_provider") == "codex" and WS.workers[back].state.get("session_provider") == "codex"
      and any(provider_of_cmd(c)[0] == "codex" and c[-2:] == ["--resume", "s-1"] for c in commands()), commands())
check("4. the provider_of reading: explicit prop, then saved conversation, then none",
      WS.provider_of(back, {"props": {}}) == "codex"
      and WS.provider_of(back, {"props": {"worker_provider": "claude"}}) == "claude"
      and WS.provider_of("a0", {"props": {}}) is None)

# ---- 5. no pool: as before ------------------------------------------------------------------------------------------
reset()
OLD = {"model": "claude-opus-5-5", "workers": "2", "worker_model": "", "worker_pool": ""}
plain = [card("Plain one"), card("Plain two", worker_provider="codex", worker_model="gpt-6.1-sol"), card("Plain three")]
popen.reset_mock()
WS.step(W, OLD)
got = [provider_of_cmd(c) for c in commands()]
check("5. no worker_pool: the first two start as they say (Claude by default, the codex card on Sol), the third waits",
      got == [("claude", "claude-opus-5-5"), ("codex", "gpt-6.1-sol")] and plain[2] not in WS.workers
      and "worker_provider" not in props(plain[0]), got)

# ---- 6. a codex card naming no model ------------------------------------------------------------------------------
reset()
nm = card("No model", worker_provider="codex")
popen.reset_mock()
WS.step(W, OLD)
check("6. a codex card that names no model runs gpt-6.1-sol (the adapter's own), not claude-opus-5-5",
      [provider_of_cmd(c) for c in commands()] == [("codex", "gpt-6.1-sol")], commands())
prompt = (WS.workers[nm].dir / "worker-prompt.txt").read_text(encoding="utf-8")
check("6. a Codex worker is told its sandbox cannot commit, and that the house commits for it at ready",
      "cannot write .git" in prompt and "the house commits" in prompt, prompt[-600:])

# ---- 7. reading worker_pool -----------------------------------------------------------------------------------------
P = workshop.Workshop.pool
check("7. worker_pool readings", P({"worker_pool": "2 claude, 2 codex gpt-6-astra"})
      == [{"n": 2, "provider": "claude", "model": ""}, {"n": 2, "provider": "codex", "model": "gpt-6-astra"}]
      and P({"worker_pool": ""}) == [] and P({"worker_pool": "two claude"}) == [] and P({}) == []
      and P({"worker_pool": "1 codex gpt-6-astra, 3 codex gpt-6.1-sol"}) == [{"n": 1, "provider": "codex", "model": "gpt-6-astra"}],
      [P({"worker_pool": x}) for x in ("2 claude, 2 codex gpt-6-astra", "two claude")])
reset()
mock.patch.stopall()          # workshop.subprocess is subprocess: git below must really run

# ---- 8. the house commits a Codex worker's work at landing --------------------------------------------------------------
repo = TMP / "repo"
repo.mkdir()
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
for args in (["init", "-q", "-b", "main"], ["config", "user.name", "t"], ["config", "user.email", "t@t"],
             ["commit", "-q", "--allow-empty", "-m", "start"]):
    subprocess.run(["git", *args], cwd=repo, env=ENV, check=True)
(repo / "made.py").write_text("x = 1\n", encoding="utf-8")
(repo / workshop.NOTATION / "sessions").mkdir(parents=True)
(repo / workshop.NOTATION / "sessions" / "w-try.pickle").write_text("world", encoding="utf-8")
workshop.git = real_git
wk = SimpleNamespace(tree=repo, actor="worker-a9", state={}, log=lambda *a: None)
n = WS.commit_for(wk, "a9: committed by the house")
log = subprocess.run(["git", "log", "--name-only", "--format=%s"], cwd=repo, capture_output=True, text=True).stdout
check("8. commit_for commits the worker's file to its branch, never the world copy in sessions/",
      n == 1 and "a9: committed by the house" in log and "made.py" in log and "pickle" not in log, log)
check("8. nothing uncommitted: nothing committed", WS.commit_for(wk, "again") == 0)

print(f"{len(fails)} FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
