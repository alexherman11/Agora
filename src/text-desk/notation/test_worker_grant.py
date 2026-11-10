# health: room test (health.py runs every test_*.py with this line among its first ten)
"""test_worker_grant: a card grants its own worker named extra commands (a5750, Alex 15 Oct: talking with JEFF is the
same authority as talking to Alex), and nothing more.

    python test_worker_grant.py

A small world in memory (roomworld.py) and a stand-in house, as test_worker_pool: the workshop's own step() runs, with
git, the world copy and the worker's process stubbed, so each start is a command line read, never a model.
  1. extra_tools set by jeff: that card's worker gets each command, exactly, in PowerShell and Bash, on top of the usual
     tools; the card says which were granted, once, and the worker on the card beside it gets none
  2. set by anyone else, or changed by anyone else after jeff, or set by a rule's act: nothing is granted; the card says why
  3. undone: nothing is granted
  4. a wildcard or a compound command (; & $ ` < > or parentheses) grants nothing at all, not even the good ones
  5. alex may grant; a codex card is not granted (the grant is Claude's --allowedTools)
  6. a worker's desk tool signs only as itself (DESK_PIN): as=jeff is refused, its own name passes the check
"""
import os
import re
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"
os.environ.setdefault("HOUSE_CLAUDE", "claude")

import roomworld   # noqa: E402
import house       # noqa: E402,F401
import workshop    # noqa: E402
import door        # noqa: E402
import desk_mcp    # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:1500]}"))
    if not ok:
        fails.append(name)


D, R = roomworld.build(say=False)
W = D.world
B = R.BOARD
sys.path.insert(0, str(HERE.parents[1] / "desktop"))
import agora_tmp
TMP = Path(agora_tmp.directory("worker-grant-test-"))  # inherited ACL; stub leaves stderr open


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
        return say(who, *[p.strip() for p in split_batch(line)])


workshop.git = lambda *a, **k: SimpleNamespace(returncode=0, stdout="", stderr="")
workshop.TREES = TMP / "trees"
workshop.Workshop.real_tree = staticmethod(lambda tree: True)
door.copy_locked = lambda a, b: None
popen = mock.patch.object(workshop.subprocess, "Popen").start()
popen.return_value.poll.return_value = None
popen.return_value.pid = 4242
mock.patch.object(workshop.threading, "Thread").start()

H = House()
WS = workshop.Workshop(H)
WS.land = lambda w, cid, s, wk, wait=True: None
SETTINGS = {"model": "claude-opus-5-5", "workers": "4", "worker_model": "", "worker_pool": ""}


def card(title, **props):
    extra = "".join(f" {k}={v}" for k, v in props.items())
    t = say("jeff", f"look {B} :1", f'do create {B} kind=task title="{title}" owner=jeff status=open{extra}')
    return re.findall(r"created (a\d+)", t)[-1]


def setby(who, cid, value):
    return say(who, f"look {cid} :1", f'do prop {cid} extra_tools="{value}"')


def ask(cid):
    say("jeff", f"look {cid} :1", f"do prop {cid} commission=asked")


def started(cid):
    """The command line the card's worker started with, and the comments on its card."""
    popen.reset_mock()
    WS.step(W, SETTINGS)
    cmd = next((c.args[0] for c in popen.call_args_list), None)
    sid = W.nodes[cid]["subject"]
    said = [c.get("text", "") for c in (W.subjects[sid].get("comments") or [])]
    return cmd, said


def tools_of(cmd):
    i = cmd.index("--allowedTools") + 1
    j = next(k for k in range(i, len(cmd)) if cmd[k].startswith("--"))
    return cmd[i:j]


CHECKS = "powercfg /lastwake | powercfg /waketimers | powercfg /a"

# ---- 0. a card with no extra_tools: the usual tools -----------------------------------------------------------------
plain = card("Plain")
ask(plain)
cmd, said = started(plain)
BASE = tools_of(cmd)
check("0. no extra_tools: the usual tools, nothing said about a grant",
      "Read" in BASE and not any("powercfg" in t for t in BASE) and not any("extra" in s for s in said), (BASE, said))

# ---- 1. granted by jeff ---------------------------------------------------------------------------------------------
g = card("Granted")
setby("jeff", g, CHECKS)
ask(g)
cmd, said = started(g)
got = tools_of(cmd)
want = [f"{sh}({c})" for c in ("powercfg /lastwake", "powercfg /waketimers", "powercfg /a") for sh in ("PowerShell", "Bash")]
check("1. jeff's grant: each command exactly, in PowerShell and Bash, on top of the usual tools",
      got == BASE + want, got[len(BASE):])
check("1. the card says what was granted", any(s.startswith("granted worker-" + g) and "powercfg /lastwake | "
                                                 "powercfg /waketimers | powercfg /a" in s for s in said), said)
again = workshop.Worker(H, g, TMP / "trees" / g, f"worker/{g}", "jeff")
again.start("claude-opus-5-5", "w", None)
sid = W.nodes[g]["subject"]
check("1. started again on the same grant: said once, not again",
      sum(c.get("text", "").startswith("granted") for c in W.subjects[sid]["comments"]) == 1, W.subjects[sid]["comments"])
check("1. the plain card's worker has none of it", not any("powercfg" in t for t in BASE))

# ---- 2. not jeff, or changed after jeff ------------------------------------------------------------------------------
p = card("Pike grants")
setby("pike", p, "powercfg /a")
ask(p)
cmd, said = started(p)
check("2. set by pike: nothing granted, and the card says only jeff or alex may grant",
      tools_of(cmd) == BASE and any("only jeff or alex may grant" in s and "pike" in s for s in said), said)
c2 = card("Changed after")
setby("jeff", c2, "powercfg /a")
setby("pike", c2, "powercfg /a | Get-ScheduledTask")
ask(c2)
cmd, said = started(c2)
check("2. jeff set it, pike widened it: nothing granted", tools_of(cmd) == BASE and any("pike" in s for s in said), said)
s2 = {"id": "s0", "props": {"extra_tools": "powercfg /a"}}
fake = SimpleNamespace(appearances_of=lambda sid: ["a0"], events=[
    {"id": "e1", "verb": "prop", "target": "a0", "args": {"extra_tools": "powercfg /a"}, "by": "jeff", "via": "rule a9"}])
check("2. set by a rule (via=), even one signed jeff: nothing granted",
      workshop.extra_tools(fake, s2)[0] == [] and "via rule a9" in workshop.extra_tools(fake, s2)[3],
      workshop.extra_tools(fake, s2))
fake.events[0]["via"] = "prop kind:task"
check("2. set across a selection: nothing granted", workshop.extra_tools(fake, s2)[0] == [], workshop.extra_tools(fake, s2))

# ---- 3. undone ------------------------------------------------------------------------------------------------------
u = card("Undone")
t = setby("jeff", u, "powercfg /a")
ev = re.findall(r"\[(e\d+)\]", t)[-1]
say("jeff", f"undo {ev}")
s = W.subjects[W.nodes[u]["subject"]]
check("3. undone: no extra_tools left, nothing granted", workshop.extra_tools(W, s)[0] == [], workshop.extra_tools(W, s))

# ---- 4. not exact commands ------------------------------------------------------------------------------------------
for bad in ("powercfg *", "schtasks /query; del x", "powercfg /a & calc", "Get-ScheduledTask $x",
            "Set-ScheduledTask -Settings (New-ScheduledTaskSettingsSet)", "type a > b"):
    x = card("Bad " + str(len(fails)) + bad[:8].replace('"', ""))
    setby("jeff", x, "powercfg /lastwake | " + bad)
    r = workshop.extra_tools(W, W.subjects[W.nodes[x]["subject"]])
    check(f"4. {bad!r} with a good one beside it: nothing granted", r[0] == [] and r[1] == [] and "not exact" in r[3], r)

# ---- 5. alex may grant; codex is not granted ------------------------------------------------------------------------
a = card("Alex grants")
setby("alex", a, "powercfg /a")
r = workshop.extra_tools(W, W.subjects[W.nodes[a]["subject"]])
check("5. alex's grant counts", r[0] == ["PowerShell(powercfg /a)", "Bash(powercfg /a)"], r)
# This test isolates grants, not concurrency. Finish the stand-in turns before
# asking another card; the production scheduler now enforces four for every start.
for cid, wk in WS.workers.items():
    wk.busy = False
    WS.set_state(cid, "waiting")
cx = card("Codex", worker_provider="codex")
setby("jeff", cx, "powercfg /a")
ask(cx)
cmd, said = started(cx)
check("5. a codex card: not granted, and the card says so",
      "powercfg" not in " ".join(cmd) and any("for claude workers" in s for s in said), (cmd, said))

# ---- 6. the worker's desk tool signs only as itself ------------------------------------------------------------------
with mock.patch.dict(os.environ, {"DESK_AS": "worker-a1", "DESK_PIN": "1"}):
    out, err = desk_mcp.run_desk({"line": "look", "as": "jeff"})
    check("6. a pinned desk tool refuses as=jeff", err and "signs only as worker-a1" in out, out)
    with mock.patch.object(desk_mcp.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout="ok", stderr="")):
        out, err = desk_mcp.run_desk({"line": "look", "as": "worker-a1"})
    check("6. its own name passes", "signs only" not in str(out), out)
mcp = (TMP / "house-state" / f"worker-{g}" / "mcp.json").read_text(encoding="utf-8")
check("6. a worker's mcp.json pins its desk tool", '"DESK_PIN": "1"' in mcp and f'"DESK_AS": "worker-{g}"' in mcp, mcp)

mock.patch.stopall()
print(f"{len(fails)} FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
