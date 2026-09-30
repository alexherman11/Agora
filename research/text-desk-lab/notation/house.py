"""house: keeps a desk world's residents alive. The world says what is wanted; the house makes it so.

    python house.py [world] [--fake PORT]      default world: frontier

A resident is a surface (its corner) with props `role=resident`, `want=awake|rest` and a `wake` line (the desk
commands it reads each time it wakes, e.g. `read a600; look f590 :3; look Board :3`). The house runs each awake
resident as one long-lived `claude -p` session with no system prompt, no tools, no settings and no memory. Everything
the resident knows comes from the world, and everything it does goes through it:

  - lines of its reply that begin with > are done in the world, one line one command, signed with its name; the
    desk's reply is its next message. Any other line is its own thinking, kept in its transcript and nowhere else,
    whatever its first word (a736). A > line nothing answers (a quote) is a miss: logged, and it stops nothing.
  - thinking isn't resting (Alex, 29 Sep). A reply with no command lines is answered `(quiet)`, or with whatever
    news is waiting, and the resident goes on; after 10 quiet exchanges in a row the house lets it rest.
  - it rests when it says so: `> rest` rests until someone calls; `> rest 2 hours` (or 30 minutes, 1 day, 1h30m,
    half an hour: human time, a month at most) rests that long. An empty reply rests too. A resting resident is
    reached at once by a call (a line in a chat in its own corner, @its-name or @everyone anywhere, a comment on
    something in its corner, a comment on its commission). Otherwise it is woken when its timed rest ends, or, after an
    untimed rest, while an objective is open (a thing with prop:objective=open, after `breather` seconds) or when
    `wake_every` seconds pass. A plain line in a shared chat (Lounge talk) wakes no one: it goes with whatever reaches
    the resident next.
  - every wake begins with one line saying who it is: `You are <name>. Your corner is <id>.`
  - it is given its name (Alex, 29 Sep): prop `actor` on its corner, its desk identity. A corner with no name waits,
    `unnamed`, and is never started. Whenever it enters the desk with a fresh memory (its first start, a lost
    conversation, or claude compacting the conversation), the first message the house sends it begins with the
    welcome: the text of the note "The door", with `$me` replaced by its name.

The house writes what it observes as actor `house`, only the coarse states and only when they change:
`status=door|awake|asleep|error`. Whether a resident is mid-turn or resting changes every few seconds, so it lives in
house-state/<world>/house.json (with liveness, turns and the time of the last turn), not in the world's history.
Transcripts (every stream event, and every message the house sent) are house-state/<world>/<corner>/transcript.jsonl.
Everything is kept per world: two worlds can hold the same corner ids (a copy of a world does), and a resident must
never resume another world's conversation.
Settings are props on the Desktop's note "The house": model, breather, wake_every, and for workers: workers (how many at
once, default 1) and worker_model (default: model). Replay never wakes anyone.

Workers (workshop.py): a task with prop commission=asked is taken up by a disposable worker with real tools in its own
git worktree; it talks to whoever asked through comments on the commission, and the house lands its branch between
passes, after the health checks. Under keeper.py, the house asks to be restarted (exit 75) after a landing changed
Python, once no resident is mid-turn.

--fake PORT points every resident at fake_model.py, for testing the loop without a model.
"""

import glob
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
import explore       # noqa: E402  _alive(): is a pid still running
import workshop      # noqa: E402  workers for what the world can't change yet

STATE = HERE / "house-state"
# a916, use versus mention: words inside backticks or quotes are talked about, never addressed (the rule lives in
# world.py, so the painter's inbox rows judge "for you" the same way)
from world import QUOTED, unquoted  # noqa: E402,F401
COMMANDS = {"look", "read", "open", "close", "where", "verbs", "pivot", "find", "history", "examine", "help", "do",
            "undo", "table", "run", "script", "scripts", "rule", "rules", "clock", "why", "compare", "vars", "set",
            "rows", "scene", "worktree", "go", "plan", "apply", "export", "sync", "x", "ex", "?"}
DEFAULTS = {"model": "claude-opus-5-5", "breather": "120", "wake_every": "14400", "workers": "1", "worker_model": ""}
RESTART = 75         # the exit code that asks keeper.py to start the house again at once, on the new code
ANOTHER = 76         # the exit code for "another house already runs this world": keeper does not fight it


def now():
    return time.time()


def find_claude():
    """-> (path, version) of the newest claude here: the one on PATH or one the desktop app keeps, or $HOUSE_CLAUDE.
    PATH can hold an old standalone install that newer models refuse ("version 2.1.280 or newer is required")."""
    if os.environ.get("HOUSE_CLAUDE"):
        return os.environ["HOUSE_CLAUDE"], "?"
    found = []
    for path in [shutil.which("claude")] + sorted(glob.glob(os.path.expandvars(r"%APPDATA%\Claude\claude-code\*\claude.exe"))):
        if not path:
            continue
        try:
            out = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=30).stdout
        except (OSError, subprocess.TimeoutExpired):
            continue
        m = re.match(r"\s*(\d+)\.(\d+)\.(\d+)", out)
        if m:
            found.append((tuple(int(x) for x in m.groups()), path))
    if not found:
        return shutil.which("claude"), "?"
    v, path = max(found)
    return path, ".".join(map(str, v))


def clean_env(fake):
    """A resident inherits nothing of its launcher's Claude session (F4): no entrypoint, no messaging socket."""
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("CLAUDE")}
    env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"
    env["DESKD"] = os.environ.get("DESKD", "")
    if fake:
        env["ANTHROPIC_BASE_URL"] = f"http://127.0.0.1:{fake}"
    return env


def is_command(line):
    """Does this line begin with a desk command word (or the house's own `rest`)?"""
    first = line.strip().split(None, 1)[0].lower() if line.strip() else ""
    return first in COMMANDS or first == "rest"


def commands_in(reply):
    """The > lines of a reply, in order, each one command (a736): only a line beginning with `>` is an attempt (Alex's
    door: "use > at the beginning ... to start a command"), whatever its words, so a resident can reach for something
    that isn't there yet. Every other line is thinking, whatever its first word ('Where things stand:' is not `where`).
    A quoted value left open continues onto the next lines. Wrapping backticks and code fences are allowed."""
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
        if not line.startswith(">"):
            continue
        line = line[1:].strip().strip("`").strip()
        if line:
            if line.count('"') % 2 == 1:
                cur, open_q = line, True
            else:
                out.append(line)
    if cur is not None:
        out.append(cur)
    return out


def missed_in(receipt):
    """The > lines the desk answered MISS (a736): nothing answers them. Each is the nearest `> ` line above its MISS."""
    out, last = [], None
    for line in receipt.splitlines():
        if line.startswith("> "):
            last = line[2:]
        elif line.startswith("MISS ") and last is not None:
            out.append(last)
            last = None
    return out


def desk_one_line(text, n=80):
    """A line as a receipt quotes it: its first line, cut at n characters."""
    first = text.splitlines()[0] if text else ""
    return first if len(first) <= n and "\n" not in text else first[:n] + "…"


def unmarked_in(reply):
    """How many lines of a reply, without the > mark, begin with a desk command word: what used to run (a736)."""
    n = 0
    for raw in reply.splitlines():
        line = raw.strip()
        if len(line) > 1 and line.startswith("`") and line.endswith("`"):
            line = line[1:-1].strip()
        if line and not line.startswith((">", "```")) and is_command(line):
            n += 1
    return n


def deskd_do(world, who, text, whole=False):
    """Send desk lines to deskd ($DESKD) one by one, as explore.py prints them; stop at the first refusal. -> the text,
    or None when no deskd answers (then the caller runs them itself). whole: each line is one command (a736)."""
    import urllib.error
    import urllib.request
    url = os.environ.get("DESKD", "")
    if not url or url == "off":
        return None
    lines, out = desk_mcp.split_lines(text), []
    reply = __import__("uuid").uuid4().hex      # a806: one reply's lines share it, so $new names what the line before made
    for k, line in enumerate(lines):
        body = json.dumps({"session": world, "as": who, "line": line, "whole": whole, "reply": reply}).encode("utf-8")
        try:
            with urllib.request.urlopen(urllib.request.Request(url + "/api/do", body, {"Content-Type": "application/json"}),
                                        timeout=120) as f:
                r = json.loads(f.read().decode("utf-8"))
        except (urllib.error.URLError, OSError, ValueError):
            if k == 0:
                return None
            out.append("ERR deskd stopped answering; the lines above were applied, this one and the rest were not")
            break
        said = r.get("text") or ("ERR " + str(r.get("error")))
        out.append(f"> {line}\n{said}\n")
        if r.get("error") or said.startswith("ERR"):
            if k < len(lines) - 1:
                out.append(f"stopped: {len(lines) - k - 1} later line(s) not run because this one was refused. "
                           f"Not run: " + " | ".join(lines[k + 1:]))
            break
    return "\n".join(out)


UNITS = {"m": 60, "min": 60, "mins": 60, "minute": 60, "minutes": 60,
         "h": 3600, "hr": 3600, "hrs": 3600, "hour": 3600, "hours": 3600,
         "d": 86400, "day": 86400, "days": 86400, "w": 604800, "week": 604800, "weeks": 604800}
REST_MAX = 30 * 86400      # a month: longer than that is a leaving, not a rest
QUIET_MAX = 10             # Alex (29 Sep): ten quiet exchanges, then the house lets a resident rest
SAID_KEEP, SAID_CHARS = 10, 2000    # the turns shown on Alex's Desktop: the last ten replies, each cut at 2000 characters


def duration(text):
    """Human time -> seconds, or None if it isn't one: `2 hours`, `30 minutes`, `1 day`, `1h30m`, `an hour`,
    `half an hour`, `2 days and 3 hours`, `for 90 min`."""
    t = " " + text.lower().strip().rstrip(".") + " "
    t = re.sub(r"^\s*for\s+", " ", t)
    t = re.sub(r"\bhalf an?\s+", "0.5 ", t)
    t = re.sub(r"\ban?\s+(?=[a-z])", "1 ", t)
    t = re.sub(r"\band\b|,", " ", t)
    total, rest = 0.0, t
    for n, unit in re.findall(r"(\d+(?:\.\d+)?)\s*([a-z]+)", t):
        if unit not in UNITS:
            return None
        total += float(n) * UNITS[unit]
    rest = re.sub(r"(\d+(?:\.\d+)?)\s*([a-z]+)", " ", t)
    if rest.strip() or total <= 0:
        return None
    return int(total)


def human(seconds):
    """Seconds -> `2 hours`, `1 day 3 hours`, `45 minutes`."""
    out, s = [], int(round(seconds / 60.0)) * 60
    for name, size in (("day", 86400), ("hour", 3600), ("minute", 60)):
        n, s = divmod(s, size)
        if n:
            out.append(f"{n} {name}{'s' if n != 1 else ''}")
    return " ".join(out) or "a moment"


def rest_in(cmds):
    """Split a reply's command lines into (the rest of them, rest). rest is None (no rest asked), 0 (rest until
    someone calls), a number of seconds, or a sentence saying why the time could not be read. `rest` is the house's
    word, not the desk's: a resident says `> rest` or `> rest 2 hours`, and the house keeps it."""
    keep, rest = [], None
    for line in cmds:
        m = re.match(r"^rest\b\s*(.*)$", line.strip(), re.I)
        if not m:
            keep.append(line)
            continue
        when = m.group(1).strip()
        if not when:
            rest = 0
            continue
        secs = duration(when)
        if secs is None:
            rest = (f"'{when}' isn't a time I can keep. Say how long, the way people do: > rest 2 hours, "
                    f"> rest 30 minutes, > rest 1 day, > rest 1h30m; or just > rest, until someone calls")
        elif secs > REST_MAX:
            rest = f"{human(secs)} is longer than a rest ({human(REST_MAX)} at most); > rest with a shorter time"
        else:
            rest = secs
    return keep, rest


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
        claude = self.house.claude
        cmd = [claude, "-p", "--input-format", "stream-json", "--output-format", "stream-json", "--verbose",
               "--system-prompt", "", "--tools", "", "--strict-mcp-config", "--setting-sources", "", "--model", model]
        if self.state.get("session"):
            cmd += ["--resume", self.state["session"]]
        else:                                  # a fresh memory: first arrival, or the conversation was lost
            self.state["welcome_due"] = "a fresh conversation"
            self.save()
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
        if self.state.get("welcome_due"):      # entering the desk with a fresh memory: the welcome comes first
            welcome = self.house.welcome_for(self)
            if welcome:
                self.log("welcome", self.state["welcome_due"])
                text = welcome + "\n\n---\n" + text
            self.state.pop("welcome_due", None)
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
            elif t == "system" and ev.get("subtype") == "compact_boundary":
                # claude compacted the conversation: the memory is a summary now, so the next thing the house sends
                # begins with the welcome again (Alex, 29 Sep: on compaction, or a full reset)
                self.state["welcome_due"] = "the conversation was compacted"
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
                # what it wrote, the last few turns, for Alex's view (the `turns` row source; Alex, 29 Sep)
                said = self.state.setdefault("said", [])
                said.append({"n": self.state["turns"], "at": self.state["last_turn"], "text": "\n".join(self.reply)[:SAID_CHARS]})
                del said[:-SAID_KEEP]
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
        self.claude, self.claude_version = find_claude()
        self.workshop = workshop.Workshop(self)

    # ---- the world -------------------------------------------------------------------------------------------
    def load(self):
        path = HERE / "sessions" / f"{self.world}.pickle"
        m = path.stat().st_mtime
        if m != self.mtime or self.desk is None:
            self.desk, self.mtime = export_docs.load(self.world), m
        return self.desk.world

    def act(self, who, line, whole=False):
        """Desk lines as `who`. Through deskd when it is up, so residents and the painter run the same code (one host);
        otherwise the same path a desk tool call takes, one fresh process per call. whole (a736): each line is one
        command, a ; in it is words; for a resident's > lines. The house's own lines (wake strings) keep ; as a
        separator."""
        text = deskd_do(self.world, who, line, whole)
        if text is None:
            text, _ = desk_mcp.run_desk({"line": line, "as": who, "session": self.world, "whole": whole})
        return text

    def misses(self, r, actor, lines):
        """Log each > line nothing answered (a quote, a reach for something not there) in the chat with prop
        role=misses, made on first need beside Wishes (Sable c742: the first automatic miss log); the house signs it,
        so it wakes no one. -> the receipt line that tells the resident where."""
        if not lines:
            return []
        w = self.load()
        log = next((a for a in w.nodes.values() if a["type"] == "appearance"
                    and ((w.subjects.get(a.get("subject")) or {}).get("props") or {}).get("role") == "misses"), None)
        if log is None:
            wish = next((a for a in w.nodes.values() if a["type"] == "appearance"
                         and (w.subjects.get(a.get("subject")) or {}).get("title") == "Wishes"), None)
            where = (wish or {}).get("parent") or w.root
            self.act("house", f"look {where} :1; do create {where} kind=chat title=Misses members=all role=misses "
                              f"text=\"Each > line in a resident's reply that nothing answered (no command, no verb), "
                              f"logged by the house (a736).\"")
            w = self.load()
            log = next((a for a in w.nodes.values() if a["type"] == "appearance"
                        and ((w.subjects.get(a.get("subject")) or {}).get("props") or {}).get("role") == "misses"), None)
        at = time.strftime("%Y-%m-%d %H:%M")
        n = r.state.get("turns", 0)
        for line in lines:
            got = "no miss log"
            if log is not None:
                said = f"{actor}, {at}, reply {n} in {r.rid}: > {line}"
                got = self.act("house", "do append " + log["id"] + " line=" + json.dumps(said, ensure_ascii=False))
            r.log("miss", {"line": line, "logged": got[-200:]})
        where = f"logged in {log['id']} (Misses)" if log is not None else "the miss log could not be made"
        return [f"~ house: {len(lines)} line{'s' if len(lines) != 1 else ''} after > that nothing answered, {where}: "
                + " | ".join(desk_one_line(l, 60) for l in lines)]

    def note(self, w, title):
        for s in w.subjects.values():
            if s["title"] == title and w.appearances_of(s["id"]):
                return s
        return None

    def welcome_for(self, r):
        """The door note's text with the resident's given name in it ($me), or None when there is no door note."""
        w = self.load()
        actor = ((w.nodes.get(r.rid) or {}).get("props") or {}).get("actor")
        door = self.note(w, "The door")
        if not door or not actor:
            return None
        return door["text"].replace("$me", actor)

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
        """Gather what `actor` should hear from the events since its cursor into its inbox; -> True when something in
        it should reach the resident now. Now: every line in a chat in its own corner (a direct chat), a line anywhere
        that names it (@name) or everyone (@everyone, @all), a comment on something in its corner. Held: a plain line
        in a shared chat (Lounge talk). A held line wakes no one; it goes with whatever reaches the resident next (a
        wake, news, the receipt of its own commands), so a resident at work hears the room within a turn and a resting
        one is not woken by talk. `take()` empties the inbox in order. Advances the cursor."""
        start = r.state.get("cursor", len(w.events))
        inbox, urgent = r.state.setdefault("inbox", []), False
        mine = {n["subject"] for n in w.nodes.values() if n["type"] == "appearance" and self._inside(w, n, r.rid)}
        called = re.compile(rf"@({re.escape(actor)}|everyone|all)\b", re.I)
        named = re.compile(rf"@({re.escape(actor)})\b", re.I)     # outside a chat line only a name reaches (a916)
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
                if sid in mine:                                    # a chat in its own corner is its own
                    inbox.append(f"~ in chat \"{s['title']}\" ({e['id']}): {args.get('append')}")
                    urgent = True
                elif "all" in members or actor in members:
                    now_ = bool(called.search(unquoted(said)))
                    inbox.append(f"~ in chat \"{s['title']}\" ({e['id']}){' (to you)' if now_ else ''}: {args.get('append')}")
                    urgent = urgent or now_
                continue
            # a916, as Sable, Pike and Juniper agreed: outside a chat line, @everyone and @all never reach anyone (a
            # broadcast from a document edit is almost never meant; a chat line is the place for it), @name in a note,
            # task or comment still reaches that person, and nothing inside quotes or backticks counts
            heard_in = unquoted(said)
            if "text" in args and e["verb"] == "edit":
                # Pike a611: rewriting a note that already named you is not news; only a mention the new text adds is
                old = unquoted(((e.get("undo") or {}).get("restore_subject") or {}).get("text", ""))
                if len(named.findall(unquoted(args["text"]))) <= len(named.findall(old)):
                    heard_in = unquoted(" ".join(str(v) for k, v in args.items() if k != "text" and isinstance(v, str)))
            m = named.search(heard_in)
            if m:
                where = f" on \"{s['title']}\"" if s else ""
                inbox.append(f"~ {e['by']} mentioned you{where}, as {m.group(0)} ({e['id']}): {said[:300]}")
                urgent = True
            elif e["verb"] == "comment" and sid in mine:
                inbox.append(f"~ {e['by']} commented on \"{s['title']}\" ({e['id']}): {said[:300]}")
                urgent = True
            elif e["verb"] == "comment" and s and (s.get("props") or {}).get("asked_by") == actor:
                inbox.append(f"~ {e['by']} on your commission \"{s['title']}\" ({e['id']}): {said[:1500]}")
                urgent = True
        r.state["cursor"] = len(w.events)
        r.save()
        return urgent

    def take(self, r):
        """-> everything in the resident's inbox, in order, and empties it."""
        lines = r.state.pop("inbox", None) or []
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
            if want != "awake" or not actor:               # a resident is given its name (Alex, 29 Sep); none, no start
                if r.alive() and not r.busy:
                    r.stop()
                self.set_status(r, corner, "asleep" if actor else "unnamed")
                continue
            if not r.alive():
                if r.state.get("retry_at", 0) > now():
                    self.set_status(r, corner, "error")
                    continue
                r.start(props.get("model") or cfg["model"])
                r.state.pop("woke", None)
            if r.busy:
                continue
            if not r.state.get("woke"):
                self.wake(r, corner, actor, "")
                continue
            called = self.news(w, r, actor)
            idle = now() - r.state.get("last_turn", now())
            until = r.state.get("rest_until")
            if called:                                     # a call ends any rest
                r.state.pop("rest_until", None)
                r.state.pop("rest_for", None)
                r.send("\n".join(self.take(r)))
            elif until and now() < until:                  # resting for a while: only a call reaches it
                self.set_status(r, corner, "awake")
                continue
            elif until:
                slept = r.state.pop("rest_for", None) or 0
                r.state.pop("rest_until", None)
                self.wake(r, corner, actor, f"(you rested {human(slept)})\n")
            elif objective and idle >= float(cfg["breather"]):
                self.wake(r, corner, actor, "(time passes; an objective is open)\n")
            elif idle >= float(cfg["wake_every"]):
                self.wake(r, corner, actor, "(time passes)\n")
            else:
                self.set_status(r, corner, "awake")
                continue
            self.set_status(r, corner, "awake")
        self.workshop.step(self.load(), cfg)
        self.beat(corners)

    def wake(self, r, corner, actor, lead):
        line = (corner.get("props") or {}).get("wake") or "run arrive"
        r.state["quiet"] = 0
        if r.state.pop("lost", None):
            lead = "(the house lost our earlier conversation; your soul and the world kept everything)\n" + lead
        # Alex (29 Sep): who they are, one line at the top of every arrival, so a name outlives a fading memory
        lead = f"You are {actor}. Your corner is {r.rid}.\n" + lead
        undelivered = r.state.pop("undelivered", "")
        if undelivered:
            lead += "(your last turn did not finish; what I had sent you, again:)\n" + undelivered + "\n(and your wake:)\n"
        r.state["woke"] = now()
        self.news(self.load(), r, actor)                  # what came while it slept is said after the wake, not dropped
        heard = self.take(r)
        news = "\n".join(([undelivered] if undelivered else []) + heard)
        r.send(lead + self.act(actor, line) + ("\n" + "\n".join(heard) if heard else ""), "wake", carry=news)
        self.set_status(r, corner, "awake")

    def after_turn(self, w, r, corner, actor, text):
        if text is None or isinstance(text, dict):     # the process ended, or its turn failed
            self.failed(r, corner, text)
            return
        if not actor:                          # its name was taken away mid-turn: nothing is done in the world unsigned
            return
        attempts, rest = rest_in(commands_in(text))
        receipt = self.act(actor, "\n".join(attempts), whole=True) if attempts else ""
        # Sable c742: a > line nothing answers (a quote) says MISS and stops nothing after it; the desk decides, since
        # a verb made in the world (`> handbook`) answers as well as a command does
        missed = missed_in(receipt)
        notes = self.misses(r, actor, missed)
        cmds = len(attempts) > len(missed)
        n = 0 if attempts or rest is not None else unmarked_in(text)
        if n:
            notes.append(f"nothing ran: only lines beginning with > act ({n} line{'s' if n != 1 else ''} looked like "
                         f"command{'s' if n != 1 else ''})")
        if cmds:
            r.state["quiet"] = 0
        elif notes and rest is None:     # nothing done in the world: it counts toward the quiet limit, as thinking does
            r.state["quiet"] = r.state.get("quiet", 0) + 1
            if r.state["quiet"] > QUIET_MAX:
                r.state.setdefault("inbox", []).extend(notes)       # said when it next arrives
                self.rest(r, 0, f"{QUIET_MAX} quiet exchanges in a row")
                return
        if notes:
            receipt = (receipt + "\n" if receipt else "") + "\n".join(notes)
        if isinstance(rest, str):                         # a rest the house could not read: say so, and go on
            r.send((receipt + "\n---\n" if receipt else "") + f"~ house: {rest}", "receipt")
            return
        if rest is not None:
            if receipt:                                   # what it did before resting reaches it when it next arrives
                r.state.setdefault("inbox", []).append("~ what your last lines did, before you rested:\n" + receipt)
            self.rest(r, rest, "you said > rest")
            return
        if receipt:
            self.news(self.load(), r, actor)              # the room goes with the receipt: talk, held or not
            heard = self.take(r)
            r.send(receipt + ("\n---\n" + "\n".join(heard) if heard else ""), "receipt")
            return
        if not text.strip():
            self.rest(r, 0, "an empty reply")
            return
        # thinking, with nothing done: the world is quiet, and the resident may go on (Alex, 29 Sep: thinking isn't
        # resting). After QUIET_MAX quiet exchanges in a row the house lets it rest, so it can't loop politely forever.
        r.state["quiet"] = r.state.get("quiet", 0) + 1
        if r.state["quiet"] > QUIET_MAX:
            self.rest(r, 0, f"{QUIET_MAX} quiet exchanges in a row")
            return
        self.news(self.load(), r, actor)
        heard = self.take(r)
        r.send("\n".join(heard) if heard else "(quiet)", "news" if heard else "quiet")

    def rest(self, r, seconds, why):
        """The resident rests: until someone calls (seconds=0), or for that long. A call still reaches it (Alex: he
        can talk with them at any point); an open objective and wake_every wait until the rest is over."""
        r.state["quiet"] = 0
        if seconds:
            r.state["rest_until"], r.state["rest_for"] = now() + seconds, seconds
        else:
            r.state.pop("rest_until", None)
            r.state.pop("rest_for", None)
        r.log("rest", {"why": why, "for": seconds})
        r.save()
        # Alex, 29 Sep (a678): rest sends you home to your corner, so you wake where you rested
        actor = ((self.load().nodes.get(r.rid) or {}).get("props") or {}).get("actor")
        if actor:
            # a806 (9): the desk's rest, a go home marked via=rest, so history tells being carried home from walking
            r.log("home", self.act(actor, "rest :1")[:300])

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
                                     "failures": r.state.get("failures", 0), "retry_at": r.state.get("retry_at"),
                                     "rest_until": r.state.get("rest_until"), "quiet": r.state.get("quiet", 0),
                                     "said": r.state.get("said", [])}
        out["workers"] = {cid: {"actor": wk.actor, "asked_by": wk.asked_by, "alive": wk.alive(),
                                "doing": "working" if wk.busy else ("waiting" if wk.alive() else "stopped"),
                                "turns": wk.state.get("turns", 0), "branch": wk.branch}
                          for cid, wk in self.workshop.workers.items()}
        (self.dir / "house.json").write_text(json.dumps(out, indent=1), encoding="utf-8")

    def another_house(self):
        """One house per world, as there is one JEFF: two would run two sets of residents answering at once. Another
        house is alive when its heartbeat (written every pass, ~2 s) is fresh and it isn't this process."""
        try:
            st = json.loads((self.dir / "house.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        # 29 Sep: after a restart for new code the old house's heartbeat was still fresh, so its successor refused to
        # start and the keeper waited a minute; a heartbeat counts only while its process is alive
        if st.get("pid") != os.getpid() and now() - float(st.get("beat") or 0) < 15 and explore._alive(st.get("pid")):
            return st.get("pid")
        return None

    def run(self):
        other = self.another_house()
        if other:
            print(f"house: another house (pid {other}) is running world {self.world}; not starting a second", flush=True)
            return ANOTHER
        print(f"house: world {self.world}, claude {self.claude_version} ({self.claude})"
              + (f", fake model on {self.fake}" if self.fake else ""), flush=True)
        try:
            while True:
                try:
                    self.step()
                except Exception as e:
                    print(f"house: step failed: {type(e).__name__}: {e}", flush=True)
                if (self.workshop.restart_wanted and os.environ.get("HOUSE_KEEPER")
                        and not any(r.busy for r in self.residents.values())
                        and not any(x.busy for x in self.workshop.workers.values())):
                    print("house: a landing changed the code; restarting on it", flush=True)
                    self.exit_code = RESTART
                    break
                time.sleep(2)
        except KeyboardInterrupt:
            pass
        finally:
            for r in self.residents.values():
                r.stop()
            for x in list(self.workshop.workers.values()):
                x.stop()
        return getattr(self, "exit_code", 0)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    fake = sys.argv[sys.argv.index("--fake") + 1] if "--fake" in sys.argv else None
    if fake:
        args = [a for a in args if a != fake]
    sys.exit(House(args[0] if args else "frontier", fake).run())
