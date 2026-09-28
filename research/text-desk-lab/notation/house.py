"""house: keeps a desk world's residents alive. The world says what is wanted; the house makes it so.

    python house.py [world] [--fake PORT]      default world: frontier

A resident is a surface (its corner) with props `role=resident`, `want=awake|rest` and a `wake` line (the desk
commands it reads each time it wakes, e.g. `read a600; look f590 :3; look Board :3`). The house runs each awake
resident as one long-lived `claude -p` session with no system prompt, no tools, no settings and no memory. Everything
the resident knows comes from the world, and everything it does goes through it:

  - lines of its reply that begin with a desk command are done in the world, signed with its name; the desk's
    reply is its next message. Any other line is its own thinking, kept in its transcript and nowhere else.
  - a reply with no command lines ends its turn. It is resting until someone speaks to it (a line in a chat it is a
    member of, a mention, a comment on something in its corner), an objective is open (a thing with
    prop:objective=open; then it is woken again after `breather` seconds), or `wake_every` seconds pass.
  - its first pass is the door: the text of the Porch note "The door". It names itself with a line `i am <name>`,
    and that name is its desk identity from then on (prop `actor` on its corner).

The house writes what it observes as actor `house`, only the coarse states and only when they change:
`status=door|awake|asleep|error`. Whether a resident is mid-turn or resting changes every few seconds, so it lives in
house-state/<world>/house.json (with liveness, turns and the time of the last turn), not in the world's history.
Transcripts (every stream event, and every message the house sent) are house-state/<world>/<corner>/transcript.jsonl.
Everything is kept per world: two worlds can hold the same corner ids (a copy of a world does), and a resident must
never resume another world's conversation.
Settings are props on the Porch note "The house": model, breather, wake_every. Replay never wakes anyone.

--fake PORT points every resident at fake_model.py, for testing the loop without a model.
"""

import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import desk_mcp      # noqa: E402  the same path a desk tool call takes
import export_docs   # noqa: E402  load(): the world under its lock, read only

STATE = HERE / "house-state"
COMMANDS = {"look", "read", "open", "close", "where", "verbs", "pivot", "find", "history", "examine", "help", "do",
            "undo", "table", "run", "script", "scripts", "rule", "rules", "clock", "why", "compare", "vars", "set",
            "rows", "scene", "worktree"}
NAME = re.compile(r"^[a-z][a-z0-9-]{1,19}$")
RESERVED = {"alex", "house", "harness", "jeff", "claude", "all", "everyone"}
DEFAULTS = {"model": "claude-opus-5-5", "breather": "120", "wake_every": "14400"}


def now():
    return time.time()


def clean_env(fake):
    """A resident inherits nothing of its launcher's Claude session (F4): no entrypoint, no messaging socket."""
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("CLAUDE")}
    env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"
    env["DESKD"] = os.environ.get("DESKD", "")
    if fake:
        env["ANTHROPIC_BASE_URL"] = f"http://127.0.0.1:{fake}"
    return env


def commands_in(reply):
    """The command lines of a reply, in order. A command line begins with a desk command word; a quoted value left
    open continues onto the next lines. Wrapping backticks and code fences are allowed."""
    out, cur, open_q = [], None, False
    for raw in reply.splitlines():
        line = raw.strip()
        if cur is not None and open_q:
            cur += "\n" + raw
            open_q = cur.count('"') % 2 == 1
            if not open_q:
                out.append(cur)
                cur = None
            continue
        if line.startswith("```"):
            continue
        if len(line) > 1 and line.startswith("`") and line.endswith("`"):
            line = line[1:-1].strip()
        first = line.split(" ", 1)[0].lower() if line else ""
        if first in COMMANDS:
            if line.count('"') % 2 == 1:
                cur, open_q = line, True
            else:
                out.append(line)
    if cur is not None:
        out.append(cur)
    return out


def door_name(reply):
    for line in reply.splitlines():
        m = re.match(r"^\s*`?i am ([A-Za-z][A-Za-z0-9-]*)`?\s*\.?\s*$", line.strip(), re.I)
        if m:
            return m.group(1).lower()
    return None


class Resident:
    """One corner, one claude -p process at most, one turn at a time."""

    def __init__(self, house, rid):
        self.house, self.rid = house, rid
        self.dir = house.dir / rid
        self.dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.dir / "state.json"
        self.state = json.loads(self.state_path.read_text(encoding="utf-8")) if self.state_path.exists() else {}
        self.proc = None
        self.events = queue.Queue()
        self.busy = False          # a message is out and its turn has not ended
        self.reply = []            # text of the turn in progress
        self.status = None         # last status written to the world
        self.failed = False        # this process has already been judged failed (a result error, then its exit)

    # ---- persistence -----------------------------------------------------------------------------------------
    def save(self):
        self.state_path.write_text(json.dumps(self.state, indent=1), encoding="utf-8")

    def log(self, kind, data):
        with (self.dir / "transcript.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"at": now(), "kind": kind, "data": data}, ensure_ascii=False) + "\n")

    # ---- the process -----------------------------------------------------------------------------------------
    def start(self, model):
        claude = shutil.which("claude")
        cmd = [claude, "-p", "--input-format", "stream-json", "--output-format", "stream-json", "--verbose",
               "--system-prompt", "", "--tools", "", "--strict-mcp-config", "--setting-sources", "", "--model", model]
        if self.state.get("session"):
            cmd += ["--resume", self.state["session"]]
        self.proc = subprocess.Popen(cmd, cwd=self.dir, env=clean_env(self.house.fake), stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=open(self.dir / "stderr.log", "a", encoding="utf-8"),
                                     text=True, encoding="utf-8", errors="replace", bufsize=1)
        threading.Thread(target=self._read, args=(self.proc,), daemon=True).start()
        self.busy, self.reply, self.failed = False, [], False
        self.log("start", {"cmd": cmd[1:], "pid": self.proc.pid})

    def stop(self):
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.stdin.close()
                self.proc.wait(timeout=20)
            except Exception:
                self.proc.kill()
        self.proc = None
        self.log("stop", {})

    def alive(self):
        return self.proc is not None and self.proc.poll() is None

    def _read(self, proc):
        for raw in proc.stdout:
            try:
                ev = json.loads(raw)
            except json.JSONDecodeError:
                continue
            self.log("event", ev)
            self.events.put(ev)
        code = proc.wait()
        self.log("exit", {"code": code, "pid": proc.pid})
        self.events.put({"type": "exit", "code": code})

    def send(self, text, kind="news", carry=None):
        """`kind` is door, wake, news or receipt; `carry` is the part that must survive a lost conversation (news and
        receipts: all of it; a wake: only the news it brought, since the wake itself is simply done again). What is
        out is recorded before it is written, so a process that died under us (its failure may already be in the
        queue) loses nothing: the pipe error is logged and the failure is judged from the process's own events."""
        if carry is None and kind in ("news", "receipt"):
            carry = text
        self.state["last_sent"] = now()
        self.state["pending"] = {"kind": kind, "carry": carry or ""}      # cleared when its turn ends well
        self.save()
        msg = {"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": text}]}}
        try:
            self.proc.stdin.write(json.dumps(msg, ensure_ascii=False) + "\n")
            self.proc.stdin.flush()
        except (OSError, ValueError, AttributeError) as e:      # a closed pipe, a closed file, no process
            self.log("unsent", {"why": f"{type(e).__name__}: {e}", "kind": kind, "text": text})
            self.busy = False
            return
        self.log("sent", text)
        self.busy, self.reply = True, []

    def turns_ended(self):
        """Drain stream events; return the text of each turn that ended."""
        ended = []
        while True:
            try:
                ev = self.events.get_nowait()
            except queue.Empty:
                return ended
            t = ev.get("type")
            if t == "system" and ev.get("subtype") == "init" and ev.get("session_id"):
                if self.state.get("session") != ev["session_id"]:
                    self.state["session"] = ev["session_id"]
                    self.save()
            elif t == "assistant":
                for c in ev.get("message", {}).get("content", []):
                    if c.get("type") == "text":
                        self.reply.append(c["text"])
            elif t == "result" and ev.get("is_error"):
                self.busy = False
                ended.append({"error": ev.get("subtype") or "error", "detail": str(ev.get("result") or "")[:300]})
                self.reply = []
            elif t == "result":
                self.busy = False
                self.state["turns"] = self.state.get("turns", 0) + 1
                self.state["last_turn"] = now()
                for k in ("pending", "failures", "retry_at"):
                    self.state.pop(k, None)
                self.save()
                ended.append("\n".join(self.reply))
                self.reply = []
            elif t == "exit":
                self.busy = False
                self.proc = None
                ended.append(None)

    def lost_conversation(self):
        """Did the last start fail because `--resume` found no conversation? claude keeps a conversation under its
        own folder, keyed by the working directory, so moving house-state (or clearing claude's folder) loses it."""
        sid = self.state.get("session")
        try:
            tail = (self.dir / "stderr.log").read_text(encoding="utf-8", errors="replace")[-2000:]
        except OSError:
            return False
        return bool(sid) and f"No conversation found with session ID: {sid}" in tail


class House:
    def __init__(self, world, fake=None):
        self.world, self.fake = world, fake
        self.residents = {}
        self.mtime = None
        self.desk = None
        self.dir = STATE / world
        self.dir.mkdir(parents=True, exist_ok=True)

    # ---- the world -------------------------------------------------------------------------------------------
    def load(self):
        path = HERE / "sessions" / f"{self.world}.pickle"
        m = path.stat().st_mtime
        if m != self.mtime or self.desk is None:
            self.desk, self.mtime = export_docs.load(self.world), m
        return self.desk.world

    def act(self, who, line):
        text, _ = desk_mcp.run_desk({"line": line, "as": who, "session": self.world})
        return text

    def note(self, w, title):
        for s in w.subjects.values():
            if s["title"] == title and w.appearances_of(s["id"]):
                return s
        return None

    def settings(self, w):
        s = self.note(w, "The house")
        props = dict(DEFAULTS)
        if s:
            props.update({k: str(v) for k, v in (s.get("props") or {}).items()})
        return props

    def corners(self, w):
        return {n["id"]: n for n in w.nodes.values() if n["type"] == "surface" and (n.get("props") or {}).get("role") == "resident"}

    def set_status(self, r, corner, status):
        if r.status == status or (corner.get("props") or {}).get("status") == status and r.status is None:
            r.status = status
            return
        out = self.act("house", f"look {r.rid} :1; do prop {r.rid} status={status}")
        if "ERR" not in out:
            r.status = status

    # ---- what a resident should hear --------------------------------------------------------------------------
    def news(self, w, r, actor):
        """Lines for `actor` from events since its cursor: chat lines where it is a member, mentions, comments on
        things in its corner. Advances the cursor."""
        start = r.state.get("cursor", len(w.events))
        lines = []
        mine = {n["subject"] for n in w.nodes.values() if n["type"] == "appearance" and self._inside(w, n, r.rid)}
        for e in w.events[start:]:
            if e.get("by") in (actor, "house") or e.get("undone"):
                continue
            sid = e["target"]
            if sid in w.nodes and w.nodes[sid]["type"] == "appearance":
                sid = w.nodes[sid]["subject"]
            s = w.subjects.get(sid)
            args = e.get("args") or {}
            said = " ".join(str(v) for v in args.values() if isinstance(v, str))
            if s and s["kind"] == "chat" and "append" in args:
                members = {m.strip().lower() for m in str((s.get("props") or {}).get("members", "")).split(",")}
                if "all" in members or actor in members or sid in mine:   # a chat in its own corner is its own
                    lines.append(f"~ in chat \"{s['title']}\" ({e['id']}): {args.get('append')}")
                    continue
            if f"@{actor}" in said.lower():
                where = f" on \"{s['title']}\"" if s else ""
                lines.append(f"~ {e['by']} mentioned you{where} ({e['id']}): {said[:300]}")
            elif e["verb"] == "comment" and sid in mine:
                lines.append(f"~ {e['by']} commented on \"{s['title']}\" ({e['id']}): {said[:300]}")
        r.state["cursor"] = len(w.events)
        r.save()
        return lines

    def _inside(self, w, node, fid):
        p = node.get("parent")
        while p:
            if p == fid:
                return True
            p = w.nodes.get(p, {}).get("parent")
        return False

    # ---- one pass ----------------------------------------------------------------------------------------------
    def step(self):
        w = self.load()
        cfg = self.settings(w)
        corners = self.corners(w)
        objective = any((s.get("props") or {}).get("objective") == "open" for s in w.subjects.values())
        for rid, corner in corners.items():
            r = self.residents.setdefault(rid, Resident(self, rid))
            props = corner.get("props") or {}
            actor, want = props.get("actor"), props.get("want", "awake")
            for text in r.turns_ended():
                self.after_turn(w, r, corner, actor, text)
                w = self.load()
                corner = w.nodes.get(rid, corner)
                actor = (corner.get("props") or {}).get("actor")
            if want != "awake":
                if r.alive() and not r.busy:
                    r.stop()
                self.set_status(r, corner, "asleep")
                continue
            if not r.alive():
                if r.state.get("retry_at", 0) > now():
                    self.set_status(r, corner, "error")
                    continue
                r.start(props.get("model") or cfg["model"])
                r.state.pop("woke", None)
            if r.busy:
                continue
            if not actor:
                if not r.state.get("door_sent"):
                    door = self.note(w, "The door")
                    r.send(door["text"] if door else "What is your name? Write: i am <name>", "door")
                    r.state["door_sent"] = True
                    r.save()
                    self.set_status(r, corner, "door")
                continue
            if not r.state.get("woke"):
                self.wake(r, corner, actor, "")
                continue
            heard = self.news(w, r, actor)
            idle = now() - r.state.get("last_turn", now())
            if heard:
                r.send("\n".join(heard))
            elif objective and idle >= float(cfg["breather"]):
                self.wake(r, corner, actor, "(time passes; an objective is open)\n")
            elif idle >= float(cfg["wake_every"]):
                self.wake(r, corner, actor, "(time passes)\n")
            else:
                self.set_status(r, corner, "awake")
                continue
            self.set_status(r, corner, "awake")
        self.beat(corners)

    def wake(self, r, corner, actor, lead):
        line = (corner.get("props") or {}).get("wake") or "run arrive"
        if r.state.pop("lost", None):
            lead = "(the house lost our earlier conversation; your soul and the world kept everything)\n" + lead
        undelivered = r.state.pop("undelivered", "")
        if undelivered:
            lead += "(your last turn did not finish; what I had sent you, again:)\n" + undelivered + "\n(and your wake:)\n"
        r.state["woke"] = now()
        heard = self.news(self.load(), r, actor)          # what came while it slept is said after the wake, not dropped
        news = "\n".join(([undelivered] if undelivered else []) + heard)
        r.send(lead + self.act(actor, line) + ("\n" + "\n".join(heard) if heard else ""), "wake", carry=news)
        self.set_status(r, corner, "awake")

    def after_turn(self, w, r, corner, actor, text):
        if text is None or isinstance(text, dict):     # the process ended, or its turn failed
            self.failed(r, corner, text)
            return
        if not actor:                          # at the door
            name = door_name(text)
            taken = RESERVED | {(n.get("props") or {}).get("actor") for n in self.corners(w).values()} | {e.get("by") for e in w.events}
            if not name or not NAME.match(name) or name in taken:
                why = ("that name is taken" if name in taken else "that is not a name the desk can carry") if name else "I did not hear a name"
                r.send(f"The door waits ({why}). Write your name on its own line: i am <name>. One word, lower case "
                       f"letters, digits or -, 2 to 20 long.", "door")
                return
            self.act("house", f"look {r.rid} :1; do prop {r.rid} actor={name}")
            r.log("named", name)
            return                            # the next step wakes it under its name
        cmds = commands_in(text)
        if cmds:
            r.send(self.act(actor, "\n".join(cmds)), "receipt")

    def failed(self, r, corner, why):
        """One judgement per process (a failed turn is followed by the process's exit). A lost conversation is not
        a failure of the resident: the world holds its soul and its history, so it starts fresh from the world.
        Anything else backs off, 1 min doubling to 1 h, so a broken resident never spins."""
        if r.failed:
            return
        r.failed = True
        if r.alive():
            r.stop()
        carry = (r.state.pop("pending", None) or {}).get("carry")
        if carry:                                          # said again with the next wake, whatever the failure
            r.state["undelivered"] = (r.state.get("undelivered", "") + "\n" + carry).strip("\n")
        if not (corner.get("props") or {}).get("actor"):
            r.state.pop("door_sent", None)                 # still at the door: the door is said again
        if r.lost_conversation():
            r.log("lost", {"session": r.state.pop("session", None)})
            r.state["lost"] = True
            r.save()
            return
        n = r.state.get("failures", 0) + 1
        r.state["failures"], r.state["retry_at"] = n, now() + min(60 * 2 ** (n - 1), 3600)
        r.log("failed", {"why": why, "failures": n, "retry_in": int(r.state["retry_at"] - now())})
        r.save()
        self.set_status(r, corner, "error")

    def beat(self, corners):
        out = {"pid": os.getpid(), "beat": now(), "world": self.world, "residents": {}}
        for rid, r in self.residents.items():
            out["residents"][rid] = {"actor": ((corners.get(rid) or {}).get("props") or {}).get("actor", ""),
                                     "alive": r.alive(), "doing": "working" if r.busy else ("resting" if r.alive() else "stopped"),
                                     "turns": r.state.get("turns", 0), "last_turn": r.state.get("last_turn"),
                                     "last_sent": r.state.get("last_sent"), "status": r.status,
                                     "failures": r.state.get("failures", 0), "retry_at": r.state.get("retry_at")}
        (self.dir / "house.json").write_text(json.dumps(out, indent=1), encoding="utf-8")

    def run(self):
        print(f"house: world {self.world}" + (f", fake model on {self.fake}" if self.fake else ""), flush=True)
        try:
            while True:
                try:
                    self.step()
                except Exception as e:
                    print(f"house: step failed: {type(e).__name__}: {e}", flush=True)
                time.sleep(2)
        except KeyboardInterrupt:
            pass
        finally:
            for r in self.residents.values():
                r.stop()


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    fake = sys.argv[sys.argv.index("--fake") + 1] if "--fake" in sys.argv else None
    if fake:
        args = [a for a in args if a != fake]
    House(args[0] if args else "frontier", fake).run()
