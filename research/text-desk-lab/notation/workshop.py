"""workshop: disposable workers for code the world can't change yet (tier 2 of live building, Alex 28 Sep).

A **commission** is a task in the world with prop `commission=asked`. Whoever writes it is who the worker answers to.
Alex's standing trust is the grant: nothing waits for approval. The house (this module, called from house.py each
pass) takes it through:

    asked -> working -> (waiting <-> working) -> ready -> landing -> landed | reverted | failed
    anyone can set commission=cancelled; the worker stops and its worktree goes

**The worker** is one `claude -p` process with real tools, confined to its own git worktree (.worktrees/<id>, branch
worker/<id>) so the live world never sees half-done code. It gets Claude Code's own prompt, plus the protocol below
appended, and the desk as a tool (desk_mcp.py), signed `worker-<id>`. It talks to whoever asked by commenting on the
commission:
  - to widen its scope, to put a design decision to them, or to say it's stuck;
  - their comments come back to it as messages, the way news reaches a resident;
  - waiting costs nothing: an idle process uses no model.

**Landing** happens between passes, so no resident's desk call is in flight:
  1. the branch may touch code and docs, never worlds (sessions/) or .env;
  2. health is taken before, then the branch is merged (--no-ff, one commit per commission), then health again;
  3. the lenses that compiled before must still compile, and every check must pass, or the merge is reverted
     (git revert: history keeps both);
  4. the result goes back as a comment and the worktree is removed.
Under keeper.py the new code takes effect at once: keeper restarts deskd when HEAD moves, and the house asks to be
restarted once no resident is mid-turn.
"""
import json
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]                    # the checkout the house runs from: landings merge here
NOTATION = HERE.relative_to(REPO).as_posix()
TREES = REPO / ".worktrees"
PY = Path(sys.executable)

PROTOCOL = """You are a worker in Agora's house: a disposable builder for one commission, then gone.

Where you are: your own git worktree, {tree} (branch {branch}). The live world and its residents keep running while
you work; nothing you do reaches them until the house lands your branch. The lab is {notation}/ inside it.

Before anything: read AGENTS.md at the root of your worktree. Its house principles and evidence labels (ran / read /
imagined) apply to you.

Talking: whoever commissioned you is {asked_by}. Speak to them through the desk tool, as a comment on the commission:
  do comment {task} line="..."
Do this when you need to widen your scope, when a design decision should not be yours alone, or when you are stuck.
Then end your turn; their answer comes back to you as a message. Short progress notes are welcome too.

Never: touch {notation}/sessions/ (the worlds) or any .env file; push; delete what you did not make; edit
src/agora3/prompts/jeff.md.

Running things: the house has copied the live world into your worktree as {notation}/sessions/{world}-try.pickle.
Run one command per call, from your worktree root, with no cd and no chaining (; && |): the permission check approves
single commands only. `python` is the lab's interpreter, and the lab's scripts find their own files, e.g.
  python {notation}/explore.py {world}-try --as {actor}      (it reads desk lines from stdin; DESKD is off)
  python {notation}/test_scene.py
  python {notation}/health.py {world}-try
  python {notation}/suite/sessions.py --check
Don't commit the -try world. If something you need is refused, say so on the commission rather than working around it.

Finishing: commit your change on your branch (git add the files you changed; git commit). Then, through the desk:
  do comment {task} line="done: what changed; what you ran and what it printed; what you did not check"
  do prop {task} commission=ready
The house lands it: merges into main, checks the host is still whole, reverts if not, and tells you both."""


def git(*args, cwd=REPO, check=False, timeout=120):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=timeout)
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip() or r.stdout.strip()}")
    return r


def health(world, cwd=HERE):
    r = subprocess.run([str(PY), "health.py", world, "--json"], cwd=cwd, capture_output=True, text=True, timeout=900,
                       env={**os.environ, "DESKD": "off"})
    lines = (r.stdout or "").strip().splitlines()
    try:
        data = json.loads(lines[-1])
    except (IndexError, ValueError):
        data = {"ok": False, "lenses_ok": [], "failed": [f"health.py did not report: {(r.stderr or r.stdout)[-300:]}"]}
    data["text"] = "\n".join(lines[:-1])
    return data


class Workshop:
    def __init__(self, house):
        self.house = house
        self.workers = {}              # commission appearance id -> Worker
        self.restart_wanted = False    # a landing changed code this process imported

    # ---- the world ---------------------------------------------------------------------------------------------
    def commissions(self, w):
        out = {}
        for s in w.subjects.values():
            state = str((s.get("props") or {}).get("commission", "")).strip()
            apps = w.appearances_of(s["id"])
            if state and apps:
                out[apps[0]] = (s, state)
        return out

    def asked_by(self, w, s):
        by = (s.get("props") or {}).get("asked_by")
        if by:
            return by
        for e in w.events:
            if e["verb"] == "create" and isinstance(e.get("undo"), dict):
                made = e["undo"].get("delete")
                if made == s["id"] or (made in w.nodes and w.nodes[made].get("subject") == s["id"]):
                    return e.get("by")
        return "alex"

    def say(self, cid, line):
        self.house.act("house", f"read {cid}; do comment {cid} line={json.dumps(line, ensure_ascii=False)}")

    def set_state(self, cid, state, **more):
        extra = "".join(f" {k}={json.dumps(str(v), ensure_ascii=False)}" for k, v in more.items())
        self.house.act("house", f"look {cid} :1; do prop {cid} commission={state}{extra}")

    # ---- one pass ----------------------------------------------------------------------------------------------
    def step(self, w, cfg):
        for cid, (s, state) in self.commissions(w).items():
            wk = self.workers.get(cid)
            if state == "cancelled":
                if wk:
                    self.finish(cid, wk, keep_branch=True)
                continue
            if state == "asked" and not wk:
                running = sum(1 for x in self.workers.values() if x.alive())
                if running < int(cfg.get("workers", "1")):
                    self.begin(w, cid, s, cfg)
                continue
            if not wk:
                continue
            for text in wk.turns_ended():
                if text is None or isinstance(text, dict):
                    self.failed(cid, wk, text)
                    break
                wk.log("turn", {"state": state})
            w = self.house.load()
            s2, state = self.commissions(w).get(cid, (s, state))
            if state == "ready" and not wk.busy:
                self.land(w, cid, s2, wk)
                continue
            if not wk.alive() or wk.busy:
                continue
            heard = self.heard(w, cid, s2, wk)
            if heard:
                if state == "waiting":
                    self.set_state(cid, "working")
                wk.send("\n".join(heard))
            elif state == "working" and wk.state.get("turns", 0) > 0:
                self.set_state(cid, "waiting")          # its turn ended without finishing: it waits on someone

    def heard(self, w, cid, s, wk):
        """Comments on its commission by anyone but itself and the house, and mentions of it anywhere."""
        start = wk.state.get("cursor", len(w.events))
        out = []
        for e in w.events[start:]:
            if e.get("by") in (wk.actor, "house") or e.get("undone"):
                continue
            sid = e["target"]
            if sid in w.nodes and w.nodes[sid]["type"] == "appearance":
                sid = w.nodes[sid]["subject"]
            said = " ".join(str(v) for v in (e.get("args") or {}).values() if isinstance(v, str))
            if e["verb"] == "comment" and sid == s["id"]:
                out.append(f"~ {e['by']} on your commission ({e['id']}): {said[:2000]}")
            elif f"@{wk.actor}" in said.lower():
                out.append(f"~ {e['by']} mentioned you ({e['id']}): {said[:2000]}")
        wk.state["cursor"] = len(w.events)
        wk.save()
        return out

    # ---- a worker's life ---------------------------------------------------------------------------------------
    def begin(self, w, cid, s, cfg):
        asked_by = self.asked_by(w, s)
        branch, tree = f"worker/{cid}", TREES / cid
        TREES.mkdir(exist_ok=True)
        if not tree.exists():
            r = git("worktree", "add", str(tree), "-b", branch, "HEAD")
            if r.returncode and "already exists" in (r.stderr or ""):
                r = git("worktree", "add", str(tree), branch)
            if r.returncode:
                self.set_state(cid, "failed")
                self.say(cid, f"the house could not make a worktree for this: {r.stderr.strip()[:300]}")
                return
        try:                              # a copy of the world to try things on, inside the worktree it may touch
            import shutil
            shutil.copyfile(HERE / "sessions" / f"{self.house.world}.pickle",
                            tree / NOTATION / "sessions" / f"{self.house.world}-try.pickle")
        except OSError as e:
            self.say(cid, f"(the house could not copy the world for trying things: {e})")
        wk = Worker(self.house, cid, tree, branch, asked_by)
        self.workers[cid] = wk
        wk.state["cursor"] = len(w.events)
        wk.start(cfg.get("worker_model") or cfg["model"], self.house.world, s)
        self.set_state(cid, "working", asked_by=asked_by, worker=wk.actor)
        first = (f"Your commission ({cid}), asked by {asked_by}:\n\n{s['title']}\n\n{s.get('text') or '(no text)'}\n\n"
                 f"Start by reading AGENTS.md, then the code you need. Comment on {cid} if anything is unclear.")
        wk.send(first)

    def failed(self, cid, wk, why):
        wk.state["failures"] = wk.state.get("failures", 0) + 1
        wk.save()
        detail = (why or {}).get("detail", "the process ended") if isinstance(why, dict) else "the process ended"
        if wk.state["failures"] >= 2:
            self.set_state(cid, "failed")
            self.say(cid, f"the worker stopped twice ({detail}); its branch {wk.branch} is kept. Set commission=asked to try again.")
            self.finish(cid, wk, keep_branch=True)
        else:
            wk.stop()
            wk.log("restart", {"why": detail})
            wk.start(self.house.settings(self.house.load()).get("worker_model") or self.house.settings(self.house.load())["model"],
                     self.house.world, None)

    def finish(self, cid, wk, keep_branch):
        wk.stop()
        self.workers.pop(cid, None)
        if wk.tree.exists():
            git("worktree", "remove", "--force", str(wk.tree))
        if not keep_branch:
            git("branch", "-D", wk.branch)

    def land(self, w, cid, s, wk):
        """Between passes: merge, check, keep or revert. Every outcome is said on the commission."""
        self.set_state(cid, "landing")
        changed = [p for p in git("diff", "--name-only", f"HEAD...{wk.branch}").stdout.split() if p]
        banned = [p for p in changed if p.startswith(f"{NOTATION}/sessions/") or p.endswith(".env") or p == ".env"]
        if not changed or banned:
            why = "nothing to land: the branch has no commits beyond main" if not changed else \
                  f"the branch touches what workers may not: {', '.join(banned)}. Take those out of the branch and set ready again"
            self.set_state(cid, "working")
            self.say(cid, why)
            wk.send(f"~ house: {why}")
            return
        before = health(self.house.world)
        title = re.sub(r"\s+", " ", s["title"])[:80]
        r = git("merge", "--no-ff", wk.branch, "-m",
                f"land {cid}: {title}\n\nasked by {wk.asked_by}, built by {wk.actor} (commission {cid}); landed by the house "
                f"after the health checks.")
        if r.returncode:
            git("merge", "--abort")
            why = f"the branch does not merge into main: {(r.stdout + r.stderr).strip()[-400:]}"
            self.set_state(cid, "working")
            self.say(cid, why + ". Rebase your branch onto main (git rebase main), then set ready again.")
            wk.send(f"~ house: {why}. Rebase onto main (git rebase main) and set ready again.")
            return
        after = health(self.house.world)
        lost = sorted(set(before.get("lenses_ok") or []) - set(after.get("lenses_ok") or []))
        if not after.get("ok") or lost:
            reasons = list(after.get("failed") or []) + [f"lens {x} compiled before and no longer does" for x in lost]
            git("revert", "-m", "1", "--no-edit", "HEAD")
            self.set_state(cid, "reverted")
            self.say(cid, "landed, then reverted: " + "; ".join(reasons)[:1500] + f". The branch {wk.branch} is kept; fix it and set ready again.")
            wk.send("~ house: your merge failed the health checks and was reverted:\n" + "\n".join(reasons)
                    + "\nFix it on your branch and set the commission ready again.")
            return
        head = git("rev-parse", "--short", "HEAD").stdout.strip()
        self.set_state(cid, "landed", landed=head)
        self.say(cid, f"landed as {head}: {len(changed)} file(s). Health after: " + " · ".join(after.get("text", "").splitlines())[:600])
        self.finish(cid, wk, keep_branch=False)
        if any(p.endswith(".py") for p in changed):
            self.restart_wanted = True


class Worker:
    """A worker's process, stream and transcript: the resident's machinery (house.Resident), launched with tools."""

    def __new__(cls, house, cid, tree, branch, asked_by):
        import house as H

        class _Worker(H.Resident):
            def start(self, model, world, s):
                mcp = self.dir / "mcp.json"
                mcp.write_text(json.dumps({"mcpServers": {"desk": {
                    "command": str(PY), "args": [str(HERE / "desk_mcp.py")],
                    "env": {"DESK_AS": self.actor, "DESK_SESSION": world, "DESKD": os.environ.get("DESKD", "off")}}}}),
                    encoding="utf-8")
                prompt = PROTOCOL.format(tree=self.tree, branch=self.branch, notation=NOTATION, asked_by=self.asked_by,
                                         task=self.cid, live=HERE.as_posix(), world=world, actor=self.actor)
                # the worker may use either shell (on Windows its default is PowerShell), and may call the interpreter
                # by name or by its full path (trial help-list: every run was refused for want of these)
                runs = ["git status", "git diff", "git add", "git commit", "git log", "git show", "git rebase", "node --check",
                        "python", str(PY).replace("\\", "/"), str(PY)]
                tools = ["Read", "Edit", "Write", "Glob", "Grep", "mcp__desk__desk"] + [
                    f"{shell}({r}:*)" for shell in ("Bash", "PowerShell") for r in runs]
                cmd = [self.house.claude, "-p", "--input-format", "stream-json", "--output-format", "stream-json", "--verbose",
                       "--model", model, "--permission-mode", "acceptEdits", "--allowedTools", *tools,
                       "--mcp-config", str(mcp), "--strict-mcp-config", "--setting-sources", "",
                       "--append-system-prompt", prompt]
                if self.state.get("session"):
                    cmd += ["--resume", self.state["session"]]
                env = H.clean_env(self.house.fake)
                env["PATH"] = str(PY.parent) + os.pathsep + env.get("PATH", "")     # `python` is the pinned interpreter
                env["DESKD"] = "off"
                self.proc = subprocess.Popen(cmd, cwd=self.tree, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                             stderr=open(self.dir / "stderr.log", "a", encoding="utf-8"),
                                             text=True, encoding="utf-8", errors="replace", bufsize=1)
                threading.Thread(target=self._read, args=(self.proc,), daemon=True).start()
                self.busy, self.reply, self.failed = False, [], False
                self.log("start", {"cmd": [c if len(c) < 200 else c[:200] + "…" for c in cmd[1:]], "pid": self.proc.pid})

        wk = _Worker(house, f"worker-{cid}")
        wk.cid, wk.tree, wk.branch, wk.asked_by, wk.actor = cid, Path(tree), branch, asked_by, f"worker-{cid}"
        return wk
