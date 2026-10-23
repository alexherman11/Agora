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
    half an hour: human time, a month at most) rests that long; `> rest until 13:00` (9:30pm, noon) until the clock
    next reads that. An empty reply rests too. A resting resident is
    reached at once by a call: `wake <name>` or the Desktop's wake (call= on its corner), a comment on something in
    its corner, a comment on its commission, a chat line addressed to it (the line's stored to=, a2662: never its
    words read again) or @everyone in a chat it is in, @its-name outside quotes in a comment or note, from anyone
    (a1566: a resident's @ knocks, as a person's does), and, from a person at a keyboard (a surface says person=<them>), any line in a chat
    in its own corner. A line from a resident or an agent is kept for it and said first at that wake, under 'for you
    while you rested', with chat and time (a1062); their plain line in its own corner's chat waits for its next wake.
    The speaker's receipt says whom the line took and, per name, what happened. A knock leaves a record (a3150): one
    knock event per line that named or reached someone (target and cause: the line's event), saying per name what
    happened (woken / in a turn, held for its end / asleep / not a member, not knocked / a person or an agent, not
    knocked), written once per line whatever house runs (record_knocks); `history <corner>` and `examine <line>`
    show it, and the message that ends a rest begins `~ woken by <who>'s line <m id> (<event>) in "<chat>" · it is 13 Oct, 10:46`
    (a4473: the time now, on the first line of every wake by a call; `~ <who> woke you (wake, eN) · it is ...` too). A wake
    the house starts with no one calling says `(the house started you; no one called)`. Otherwise it is woken when its
    timed rest ends, or, after an untimed rest, while an objective is open (a thing with prop:objective=open, after `breather` seconds) or when
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
Settings are props on the Desktop's note "The house": model, breather, wake_every, timers (off, the default since
a8980: no open objective or wake_every wakes a resident; 13 Oct), rest_wakes (on, the default: a resident's own timed
rest ends at its deadline, on the first house pass at or after it, so after the computer resumes if it slept then;
never an OS wake timer; Alex 21 Oct, a8980), and for workers: workers (how many at once, default 1), worker_model (default: model) and worker_pool (a5284: each provider's share of them, e.g.
"2 claude, 2 codex gpt-6-astra"; a card's own worker_provider and worker_model win). Replay never wakes anyone.

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
import charter
import conversation_policy
import resident_continuity
import host_route_parent
import explore       # noqa: E402  _alive(): is a pid still running
import feeds         # noqa: E402  a5988: what a watched agent is doing, as rows a lens follows
import usage         # noqa: E402  a6265: how full each agent's context is, and Alex's limit, as rows a lens reads
import plan_usage    # noqa: E402  a6646: provider plan windows and durable pause episodes
import scripts_mirror  # noqa: E402  a6249: Alex's scripts as notes, kept in step with their files
import workshop      # noqa: E402  workers for what the world can't change yet
import task_flow
import guard_context
import house_restart  # noqa: E402  a10269: a restart asked for from the world

STATE = HERE / "house-state"
# a916, use versus mention: words inside backticks or quotes are talked about, never addressed (the rule lives in
# world.py, so the painter's inbox rows judge "for you" the same way). 30 Sep: a house running since before the rule
# moved still holds the old world module, and the workshop imports this file fresh inside it; the fallback keeps that
# import working (it failed every pass for 40 minutes, and no worker could start) until the house restarts.
try:
    from world import ADDRESS, QUOTED, unquoted  # noqa: E402,F401
except ImportError:
    ADDRESS = re.compile(r"(?<![\w@])@([A-Za-z][\w]*(?:-[\w]+)*)")     # a1581's rule, as world.py has it
    QUOTED = re.compile(r"`[^`]*`|\"[^\"\n]*\"|(?<![\w])'[^'\n]*'(?![\w])")

    def unquoted(text):
        return QUOTED.sub(" ", str(text))
COMMANDS = {"look", "read", "open", "close", "where", "verbs", "pivot", "find", "history", "examine", "help", "do",
            "undo", "table", "run", "script", "scripts", "rule", "rules", "clock", "why", "compare", "vars", "set",
            "rows", "scene", "worktree", "go", "wake", "plan", "apply", "export", "sync", "x", "ex", "?"}
DEFAULTS = {"model": "claude-opus-5-5", "breather": "120", "wake_every": "14400", "workers": "1", "worker_model": "", "worker_pool": "",
            "timers": "off", "rest_wakes": "on", "claude_start_threshold": "off"}
RESTART = 75         # the exit code that asks keeper.py to start the house again at once, on the new code
# Alex, 30 Sep ("changes shouldn't need everyone resting"; "I'd rather be able to change the code while they work"):
# only the files the house itself runs (workshop.HOUSE_FILES) ask it to restart, and a restart waits this long for
# turns to end (no new one starts), then goes: a turn it cuts is said again when the resumed conversation next wakes
RESTART_GRACE = 90
ANOTHER = 76         # the exit code for "another house already runs this world": keeper does not fight it


def now():
    return time.time()


def it_is():
    """a4473: the date and time now, as the end of a wake's first line: ' · it is 13 Oct, 10:46' (the day as look's
    'It is 13 Oct, 10:46.' writes it; the house's own time, the clock the '~ 10:45 in chat' stamps are read from)."""
    t = time.localtime()
    return f" · it is {t.tm_mday} {time.strftime('%b, %H:%M', t)}"


def points_at(w, e, s):
    """a6638 (Alex, 20 Oct: 'anything I comment on gets routed to the right person'): what a chat line points at, said
    after its words when it is handed to someone, since the words alone lose it: the thing it is about by its name and
    id (' [about "Proposal reader" (a6460)'), the words it quotes and the section they stood in. '' when it points at
    nothing. The line's fields are the writer's (world.py append); nothing here is guessed."""
    mid = (e.get("args") or {}).get("line_id")
    line = next((ln for ln in (s or {}).get("lines") or () if ln.get("id") == mid), None) if mid else None
    if not line:
        return ""
    fields = dict((line.get("fields") or {}), **{k: line[k] for k in ("about", "quote") if line.get(k)})
    said = []
    about = str(fields.get("about") or "").strip()
    if about:
        n = w.nodes.get(about)
        title = w.title(n) if n else (w.subjects.get(about) or {}).get("title", "")
        said.append(f"about \"{title}\" ({about})" if title else f"about {about}")
    quote = " ".join(str(fields.get("quote") or "").split())
    if quote:
        heading = str(fields.get("heading") or "").strip()
        said.append(f"on the words \"{quote[:300]}{'…' if len(quote) > 300 else ''}\""
                    + (f" under § {heading}" if heading else ""))
    return f"  [{'; '.join(said)}]" if said else ""


def limit_reset(detail):
    """'You've hit your session limit · resets 5:30pm (...)' -> the next 5:30pm as a time, else None. 30 Sep: residents
    stopped by the limit at 15:06 backed off to an hour at a time and were still waiting at 17:39, after it reset."""
    m = re.search(r"limit\b.*?resets (\d{1,2})(?::(\d\d))?\s*([ap]m)", detail or "", re.I)
    if not m:
        return None
    h = int(m.group(1)) % 12 + (12 if m.group(3).lower() == "pm" else 0)
    t = time.localtime()
    at = time.mktime((t.tm_year, t.tm_mon, t.tm_mday, h, int(m.group(2) or 0), 0, 0, 0, -1))
    return at if at > now() - 60 else at + 86400


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


def deskd_do(world, who, text, whole=False, stored=None, kind=None, as_of=None):
    """Send desk lines to deskd ($DESKD) one by one, as explore.py prints them; a refused line refuses only itself (a6437,
    carry_on: the desk skips a later line that depends on it, and the text ends saying what ran). -> the text,
    or None when no deskd answers (then the caller runs them itself). whole: each line is one command (a736).
    kind (a3204): the line is signed `who` but is the house's own, 'rest' or 'wake'; it is sent as by=house with that
    kind. A line without it is `who`'s own."""
    import urllib.error
    import urllib.request
    url = os.environ.get("DESKD", "")
    if not url or url == "off":
        return None
    import carry_on
    lines, out, tally = desk_mcp.split_lines(text), [], carry_on.Tally()
    reply = __import__("uuid").uuid4().hex      # a806: one reply's lines share it, so $new names what the line before made
    for k, line in enumerate(lines):
        body = json.dumps({"session": world, "as": who, "line": line, "whole": whole, "reply": reply,
                           **({"stored": stored} if stored else {}),
                           **({"as_of": as_of} if as_of is not None else {}),
                           **({"by": "house", "kind": kind} if kind else {})}).encode("utf-8")
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
        tally.add(line, said, r.get("error"))
    if tally.summary():
        out.append(tally.summary() + "\n")
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


def until(text, at=None):
    """`until 13:00` -> seconds from now to the next time the clock reads that, or a sentence saying why not, or None
    when `text` is not an until (3 Oct, Pike: receipts print 'resting until 16:25', so a resident may say it back).
    `13:00`, `09:30`, `0:15` are the 24-hour clock. `9:30pm`, `9pm`, `noon`, `midnight` say themselves. `1:30` with no am/pm
    is whichever of 1:30 and 13:30 comes first. A time already past today is tomorrow. A bare `9` is refused (an
    hour or a duration?)."""
    import datetime
    m = re.match(r"^until\s+(.+?)\.?$", text.strip(), re.I)
    if not m:
        return None
    w = m.group(1).lower().replace(" ", "")
    words = {"noon": "12:00pm", "midday": "12:00pm", "midnight": "12:00am"}
    w = words.get(w, w)
    c = re.match(r"^(\d{1,2})(?::(\d{2}))?(am|pm)?$", w)
    if not c or not (c.group(2) or c.group(3)):
        return (f"'until {m.group(1)}' isn't a time of day I can read. Say it as the clock does: > rest until 13:00, "
                f"> rest until 9:30pm, > rest until noon; or how long: > rest 2 hours")
    h, mi, half = int(c.group(1)), int(c.group(2) or 0), c.group(3)
    if mi > 59 or h > 23 or (half and not 1 <= h <= 12):
        return f"'until {m.group(1)}' isn't a time on a clock"
    if half:
        h = h % 12 + (12 if half == "pm" else 0)
    now = at or datetime.datetime.now()
    hours = [h] if half or h == 0 or h > 12 or c.group(1).startswith("0") else [h, (h + 12) % 24]
    best = None
    for hh in hours:
        t = now.replace(hour=hh, minute=mi, second=0, microsecond=0)
        if t <= now:
            t += datetime.timedelta(days=1)
        best = t if best is None or t < best else best
    # local clock, so a daylight-saving night is right; rounded up, or the house's 'now' a moment later says 12:59 (Pike)
    return max(60, int(best.timestamp() - now.timestamp()) + 1)


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
        if not when or re.match(r"^until\s+(someone\s+calls|called|i'?m\s+called)\.?$", when, re.I):
            rest = 0
            continue
        clock = until(when)
        secs = clock if isinstance(clock, int) else duration(when)
        if isinstance(clock, str):
            rest = clock
        elif secs is None:
            rest = (f"'{when}' isn't a time I can keep. Say how long, the way people do: > rest 2 hours, "
                    f"> rest 30 minutes, > rest 1 day, > rest 1h30m, or until when: > rest until 13:00; "
                    f"or just > rest, until someone calls")
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
        self.wakes_at = None       # a1062: when the house would next wake it on its own, while it rests
        self.started = False       # this house process has started it once (the first start after a restart is special)
        self.reply_source = None   # parent pipe provenance; never taken from child JSON/world actor

    # ---- persistence -----------------------------------------------------------------------------------------
    def save(self):
        temp = self.state_path.with_suffix(".tmp")
        temp.write_text(json.dumps(self.state, indent=1), encoding="utf-8")
        os.replace(temp, self.state_path)

    def log(self, kind, data):
        with (self.dir / "transcript.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"at": now(), "kind": kind, "data": data}, ensure_ascii=False) + "\n")

    # ---- the process -----------------------------------------------------------------------------------------
    def hold_unanswered(self, pending, why):
        """A turn that never finished. If its message reached the conversation (delivered) and the conversation goes
        on, it is already there: count it, and the next wake says so in one line instead of sending it again (1 Oct:
        every failed retry re-sent the whole wake into the same conversation, and they stacked, four and five deep).
        Only what never arrived is carried to be sent in full."""
        if pending.get("delivered") and self.state.get("session"):
            self.state["unanswered"] = self.state.get("unanswered", 0) + 1
            self.state["unanswered_why"] = why
            # Same-provider resume already has this input; a different provider
            # does not. Keep the complete unresolved text/refs separately from
            # bounded historical excerpts until a turn completes successfully.
            if pending.get("carry"):
                self.state["unanswered_inputs"] = list(dict.fromkeys(
                    self.state.get("unanswered_inputs", []) + [pending["carry"]]))
            for key in ("image_comments", "message_contexts"):
                self.state["unanswered_" + key] = list(dict.fromkeys(
                    self.state.get("unanswered_" + key, []) + pending.get(key, [])))
        elif pending.get("carry"):
            self.state["undelivered"] = (self.state.get("undelivered", "") + "\n" + pending["carry"]).strip("\n")
        if not (pending.get("delivered") and self.state.get("session")):
            self.state.setdefault("image_comments", []).extend(pending.get("image_comments") or [])
            self.state.setdefault("message_contexts", []).extend(
                pending.get("message_contexts") or [])
        self.save()

    def recover_delivery(self):
        """Recover a staged inbox batch or unfinished pipe write after restart.

        Pipe flush is only a local delivery boundary, not a model acknowledgement.
        A crash between flush and its saved marker can replay; never promise exactly once.
        """
        for key in ("pending", "handoff"):
            pending = self.state.pop(key, None)
            if pending:
                self.hold_unanswered(pending, "the house restarted while delivering or answering")

    def start(self, model):
        # 30 Sep: a turn the last process never finished (a restart cut it) is said at the next wake, with why
        props = (self.house.load().nodes.get(self.rid) or {}).get("props") or {}
        # Reject a mismatched/non-opted-in configuration before consuming pending
        # input. A portable switch archives that intact state and never reuses its token.
        resident_continuity.validate(self.state, props, model)
        resident_continuity.prepare(self, props, model)
        self.recover_delivery()
        provider = props.get("provider", "claude")
        # A plain process resume retains the charter. Fresh memory reads start= once.
        if not self.state.get("session") or "charter_text" not in self.state:
            self.state["charter_text"] = charter.collect(
                self.house.load(), self.house.act, self.rid, props.get("actor", self.rid), "start")
        charter_file = self.dir / "charter.txt"
        charter_file.write_text(self.state.get("charter_text", ""), encoding="utf-8")
        if provider == "codex":
            adapter = HERE.parents[1] / "codex-residents" / "codex_resident.py"
            cmd = [sys.executable, str(adapter), "--model", model,
                   "--reasoning", props.get("reasoning", "medium"),
                   "--charter-file", str(charter_file), "--world", self.house.world,
                   "--target", self.rid, "--actor", props.get("actor", self.rid)]
        elif provider == "claude":
            self._charter_channel()
            cmd = [self.house.claude, "-p", "--input-format", "stream-json", "--output-format", "stream-json", "--verbose",
                   "--system-prompt", self.state.get("charter_text", ""), "--tools", "",
                   "--strict-mcp-config", "--setting-sources", "", "--model", model,
                   "--settings", json.dumps(charter.claude_hook(
                       sys.executable, self.house.world, self.rid, props.get("actor", self.rid),
                       self.charter_channel))]
        else:
            raise ValueError(f"{self.rid}: unknown resident provider {provider}")
        self.state["session_provider"] = provider
        self.state["session_model"] = model
        if self.state.get("session"):
            cmd += ["--resume", self.state["session"]]
        else:                                  # a fresh memory: first arrival, or the conversation was lost
            self.state["welcome_due"] = "a fresh conversation"
            self.save()
        self.proc = subprocess.Popen(cmd, cwd=self.dir, env=clean_env(self.house.fake), stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=open(self.dir / "stderr.log", "a", encoding="utf-8"),
                                     text=True, encoding="utf-8", errors="replace", bufsize=1)
        source = self._bind_child(self.proc)
        threading.Thread(target=self._read, args=(self.proc, source), daemon=True).start()
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
        if route := getattr(self.house, "host_route", None):
            route.retire(self)
        self.log("stop", {})

    def alive(self):
        return self.proc is not None and self.proc.poll() is None

    def _bind_child(self, proc):
        self.reply, self.reply_source = [], None
        route = getattr(self.house, "host_route", None)
        return route.bind(self, proc) if route else None

    def _charter_channel(self):
        charter.drain_channel(self)
        self.charter_channel = charter.prepare_channel(self.dir)
        self.state["charter_channel"] = self.charter_channel.name
        self.save()
        return self.charter_channel

    def _read(self, proc, source=None):
        for raw in proc.stdout:
            try:
                ev = json.loads(raw)
            except json.JSONDecodeError:
                continue
            self.log("event", ev)
            self.events.put(host_route_parent.ChildEvent(source, ev) if source else ev)
        code = proc.wait()
        self.log("exit", {"code": code, "pid": proc.pid})
        event = {"type": "exit", "code": code}
        self.events.put(host_route_parent.ChildEvent(source, event) if source else event)

    def send(self, text, kind="news", carry=None):
        """`kind` is door, wake, news or receipt; `carry` is the part that must survive a lost conversation (news and
        receipts: all of it; a wake: only the news it brought, since the wake itself is simply done again). What is
        out is recorded before it is written, so a process that died under us (its failure may already be in the
        queue) loses nothing: the pipe error is logged and the failure is judged from the process's own events."""
        props = (self.house.load().nodes.get(self.rid) or {}).get("props") or {}
        if props.get("role") == "resident" and resident_continuity.switching(self.state, props):
            # The current turn may finish, but no receipt/news starts an extra
            # turn on the old provider. Preserve the complete packet for the new
            # conversation (or for operator repair if portable handover is absent).
            self.state["undelivered"] = "\n\n".join(
                part for part in (self.state.get("undelivered", ""), text) if part)
            self.state.pop("at_rest", None)
            self.save()
            self.busy = False
            self.log("provider_deferred", {"from": resident_continuity.provider_of(self.state),
                                           "to": props.get("provider", "claude"), "kind": kind})
            return
        self.state.pop("at_rest", None)        # anything said to a resident ends its rest (house.rest begins one)
        if carry is None and kind in ("news", "receipt"):
            carry = text
        previous = self.state.get("pending") or {}
        if previous.get("delivered"):
            previous = {}
        if previous.get("carry"):
            text = previous["carry"] + "\n\n" + text
            carry = "\n".join(part for part in (previous["carry"], carry) if part)
        if self.state.get("welcome_due"):      # entering the desk with a fresh memory: the welcome comes first
            welcome = self.house.welcome_for(self)
            if welcome:
                self.log("welcome", self.state["welcome_due"])
                text = welcome + "\n\n---\n" + text
            self.state.pop("welcome_due", None)
        self.state["last_sent"] = now()
        handoff = self.state.pop("handoff", {})
        refs = list(dict.fromkeys(previous.get("image_comments", [])
                                  + handoff.get("image_comments", [])
                                  + self.state.pop("image_comments", [])))
        contexts = list(dict.fromkeys(previous.get("message_contexts", [])
                                      + handoff.get("message_contexts", [])
                                      + self.state.pop("message_contexts", [])))
        self.state["pending"] = {"kind": kind, "carry": carry or handoff.get("carry", ""),
                                 "image_comments": refs, "message_contexts": contexts}
        resident_continuity.remember(self.state, kind, text)
        if self.state.get("handover_due"):
            text = self.state["handover_due"] + "\n\n---\n" + text
            self.state["pending"]["handover_generation"] = self.state.get("provider_generation")
        self.save()
        from image_comments import content
        blocks = [{"type": "text", "text": text}] + (content(self.house.load(), refs) if refs else [])
        if contexts:
            from message_context import model_content
            from world import Refusal
            world = self.house.load()
            for mid in dict.fromkeys(contexts):
                _, line = world.find_line(mid)
                saved = (line or {}).get("fields", {}).get("context")
                if saved:
                    try:
                        attached = model_content(world, saved, session=self.house.world)
                        for block in attached:
                            if block.get("type") == "text":
                                block["text"] = (
                                    f"Attached to native message {mid}:\n" + block["text"])
                        blocks.extend(attached)
                    except (ValueError, Refusal) as exc:
                        blocks.append({"type": "text",
                                       "text": f"{mid}: saved context unavailable: {exc}"})
                else:
                    blocks.append({"type": "text",
                                   "text": f"{mid}: saved context is no longer available."})
        msg = {"type": "user", "message": {"role": "user", "content": blocks}}
        try:
            self.proc.stdin.write(json.dumps(msg, ensure_ascii=False) + "\n")
            self.proc.stdin.flush()
        except (OSError, ValueError, AttributeError) as e:      # a closed pipe, a closed file, no process
            self.log("unsent", {"why": f"{type(e).__name__}: {e}", "kind": kind, "text": text})
            self.busy = False
            return
        # 1 Oct (Sable e4659, Pike a1660, Juniper e4662): claude keeps a message it was sent in the conversation even
        # when the turn then fails, so a delivered message is never sent again into the same conversation (see wake)
        self.state["pending"]["delivered"] = True
        self.save()
        if plans := getattr(self.house, "plans", None):
            try:
                plans.restarting(getattr(self, "cid", self.rid))
            except Exception as e:
                self.log("plan_usage", f"{type(e).__name__}: {e}"[:200])
        self.log("sent", text)
        self.busy, self.reply = True, []

    def turns_ended(self):
        """Drain stream events; return the text of each turn that ended."""
        ended = []
        charter.drain_channel(self)
        while True:
            try:
                ev = self.events.get_nowait()
            except queue.Empty:
                return ended
            source = None
            if isinstance(ev, host_route_parent.ChildEvent):
                route = getattr(self.house, "host_route", None)
                if not route or not route.current(self, ev.source):
                    continue  # old child's result/exit must not finish the new child's turn
                source, ev = ev.source, ev.event
            t = ev.get("type")
            if plans := getattr(self.house, "plans", None):
                try:
                    plans.observe(ev)
                    if t == "result" and not ev.get("is_error"):
                        plans.resumed(self.state.get("session_provider", "claude"), getattr(self, "cid", self.rid))
                    if t == "result":
                        plans.dirty = True
                        plans.publish()
                except Exception as e:  # quota display failure must never eat a completed turn
                    self.log("plan_usage", f"{type(e).__name__}: {e}"[:200])
            if t == "system" and ev.get("subtype") == "init" and ev.get("session_id"):
                if self.state.get("session") != ev["session_id"]:
                    self.state["session"] = ev["session_id"]
                    self.save()
            elif t == "system" and ev.get("subtype") == "compact_boundary":
                # claude compacted the conversation: the memory is a summary now, so the next thing the house sends
                # begins with the welcome again (Alex, 29 Sep: on compaction, or a full reset)
                self.state["welcome_due"] = "the conversation was compacted"
                self.state["compactions"] = self.state.get("compactions", 0) + 1
                self.save()
            elif t == "system" and ev.get("subtype") in ("charter_read", "charter_unavailable"):
                charter.parent_receipt(self, ev)
            elif t == "assistant":
                for c in ev.get("message", {}).get("content", []):
                    if c.get("type") == "text":
                        previous = getattr(self, "reply_source", None)
                        self.reply_source = source if not self.reply else previous if previous is source else None
                        self.reply.append(c["text"])
            elif t == "result" and ev.get("is_error"):
                self.busy = False
                ended.append({"error": ev.get("subtype") or "error", "detail": str(ev.get("result") or "")[:300]})
                self.reply = []
                self.reply_source = None
            elif t == "result":
                self.busy = False
                self.state["turns"] = self.state.get("turns", 0) + 1
                self.state["last_turn"] = now()
                pending = self.state.get("pending") or {}
                if (pending.get("handover_generation") is not None
                        and pending["handover_generation"] == self.state.get("provider_generation")):
                    self.state.pop("handover_due", None)
                    self.state.pop("handover_unanswered", None)
                for key in ("unanswered_inputs", "unanswered_image_comments", "unanswered_message_contexts"):
                    self.state.pop(key, None)
                resident_continuity.remember(self.state, "completed reply", "\n".join(self.reply))
                for k in ("pending", "failures", "retry_at", "retry_kind"):
                    self.state.pop(k, None)
                # what it wrote, the last few turns, for Alex's view (the `turns` row source; Alex, 29 Sep)
                said = self.state.setdefault("said", [])
                said.append({"n": self.state["turns"], "at": self.state["last_turn"], "text": "\n".join(self.reply)[:SAID_CHARS]})
                del said[:-SAID_KEEP]
                self.save()
                text = "\n".join(self.reply)
                # A queued human stop/correction invalidates this turn's effects,
                # including host intents, before the ordinary command batch runs.
                world = self.house.load()
                actor = (world.nodes.get(self.rid, {}).get("props") or {}).get("actor", "")
                interrupted = conversation_policy.queued_interrupts(world, actor, self.state.get("cursor"))
                if not interrupted and (route := getattr(self.house, "host_route", None)):
                    text = route.intercept(source if source is getattr(self, "reply_source", None) else None, text)
                ended.append(text)
                self.reply = []
                self.reply_source = None
            elif t == "exit":
                self.busy = False
                if route := getattr(self.house, "host_route", None):
                    route.retire(self)
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
        self.feeds = feeds.Feeds(world, self.dir)
        self.usage = usage.Usage(world, self.dir)
        self.plans = plan_usage.Plans(self)
        self.scripts = scripts_mirror.Scripts(world, self.dir, allowed=None if not fake else False)
        self.charter_state = {}
        # No setting/world property can enable this; no journal/backend opened.
        self.host_route = host_route_parent.ParentDispatcher(house=None if fake else self)   # a8191: artifact-view only

    # ---- the world -------------------------------------------------------------------------------------------
    def load(self):
        path = HERE / "sessions" / f"{self.world}.pickle"
        m = path.stat().st_mtime
        if m != self.mtime or self.desk is None:
            self.desk, self.mtime = export_docs.load(self.world), m
        return self.desk.world

    def act(self, who, line, whole=False, stored=None, kind=None, as_of=None):
        """Desk lines as `who`. Through deskd when it is up, so residents and the painter run the same code (one host);
        otherwise the same path a desk tool call takes, one fresh process per call. whole (a736): each line is one
        command, a ; in it is words; for a resident's > lines. The house's own lines (wake strings) keep ; as a
        separator. stored (a1156): the node whose stored line this is (a corner, for its wake): it stands there and
        its words mean what they were bound to when it was set. kind (a3204): a line the house sends as a resident
        that is not the resident's own: 'rest' (its answer is only logged) or 'wake' (its answer opens their wake).
        as_of (a5068): where the resident's turn began, the event count its news had reached when the turn's input was
        sent; its chat lines and thread replies are judged on what that turn was shown."""
        text = deskd_do(self.world, who, line, whole, stored, kind, as_of)
        if text is None:
            text, _ = desk_mcp.run_desk({"line": line, "as": who, "session": self.world, "whole": whole, "stored": stored,
                                         **({"as_of": as_of} if as_of is not None else {})})
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

    def toasts(self, w):
        """a5824: each new line of the Notifications sent chat (role=notifications; the house verb `notify` writes
        them) becomes a Windows toast on Alex's PC (research/window-lab/notify.py), once, in a thread so a pass never
        waits on PowerShell. Only for the world frontier under the keeper and with a real model: a copy of the world, a
        test house or a fake one never reaches his screen. Toasted line ids are kept in house-state/<world>/toasts.json;
        what was shown or refused is logged there and printed."""
        if self.world != "frontier" or self.fake or not os.environ.get("HOUSE_KEEPER") \
                or os.environ.get("AGORA_TOASTS", "").lower() == "off":
            return
        try:
            lab = str(HERE.parents[1] / "window-lab")
            if lab not in sys.path:
                sys.path.append(lab)
            import notify
            path = self.dir / "toasts.json"
            try:
                st = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                st = {"done": [], "log": []}
            done = set(st["done"])
            new = notify.pending(w, done, time.strftime("%Y-%m-%dT%H:%M:%S"))
            if not new:
                return
            for mid, who, words, sound in new:
                st["done"] = (st["done"] + [mid])[-500:]

                def send(mid=mid, who=who, words=words, sound=sound):
                    try:
                        got = notify.show(words, sound=sound, by=who)
                    except Exception as e:
                        got = f"not shown: {type(e).__name__}: {e}"
                    print(f"house: toast {mid} from {who}: {got}", flush=True)
                    with self._toast_lock:
                        try:
                            s2 = json.loads(path.read_text(encoding="utf-8"))
                        except (OSError, ValueError):
                            s2 = {"done": [], "log": []}
                        s2["log"] = (s2.get("log", []) + [{"line": mid, "by": who, "at": time.strftime("%Y-%m-%d %H:%M:%S"),
                                                            "got": got}])[-200:]
                        path.write_text(json.dumps(s2, indent=1), encoding="utf-8")
                threading.Thread(target=send, daemon=True).start()
            with self._toast_lock:
                try:
                    st["log"] = json.loads(path.read_text(encoding="utf-8")).get("log", [])
                except (OSError, ValueError):
                    pass
                path.write_text(json.dumps(st, indent=1), encoding="utf-8")
        except Exception as e:        # a toast must never stop a pass
            print(f"house: toasts failed: {type(e).__name__}: {e}", flush=True)

    _toast_lock = threading.Lock()

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
    def news(self, w, r, actor, resting=False):
        """Gather what `actor` should hear from the events since its cursor into its inbox; -> True when something in
        it should reach the resident now. Now: every line in a chat in its own corner (a direct chat), a line anywhere
        that names it (@name) or everyone (@everyone, @all), a comment on something in its corner. Held: a plain line
        in a shared chat (Lounge talk). A held line wakes no one; it goes with whatever reaches the resident next (a
        wake, news, the receipt of its own commands), so a resident at work hears the room within a turn and a resting
        one is not woken by talk. `take()` empties the inbox in order. Advances the cursor.
        a1062: while it is `resting`, a line that would call it from a resident or agent is kept for you (for_you) and
        said first at its next wake, marked for it. a1566 (Alex, e3710, e3802: 'a resident's @ should knock'): an @name
        or @everyone from anyone ends the rest now, as a person's does; only a resident's or agent's plain line in its
        own corner's chat (a visitors' book) still waits for the next wake. An @ counts only outside quotes and
        backticks (unquoted, a916), and only as a header (a2715 for a line, a2733 for a comment or a note's added
        lines: world.written). wake <name> (a call= on the corner) calls."""
        import persons
        import rooms
        from world import written      # here, not at the top: the workshop imports this file into an older house
        start = r.state.get("cursor", len(w.events))
        inbox, urgent = r.state.setdefault("inbox", []), False

        def asked(s):
            # a1590: asked_by= holds the person once a world has persons (p2919), a name before: by person when it
            # can, by name when it can't (Claude c2998 (1))
            return bool(s) and persons.holds(w, (s.get("props") or {}).get("asked_by") or "", actor)
        mine = {n["subject"] for n in w.nodes.values() if n["type"] == "appearance" and self._inside(w, n, r.rid)}
        for e in w.events[start:]:
            if rooms.same_person(w, str(e.get("by") or "").split("/")[0], actor) or e.get("undone"):
                continue
            sid = e["target"]
            if sid in w.nodes and w.nodes[sid]["type"] == "appearance":
                sid = w.nodes[sid]["subject"]
            s = w.subjects.get(sid)
            args = e.get("args") or {}
            # Ownership and material task transitions are addressed facts, not
            # prose @mentions. The same routing also produces native knock receipts.
            notices = task_flow.notices(w, e)
            if notices:
                for notice in notices:
                    if rooms.same_person(w, notice["recipient"], actor):
                        inbox.append(task_flow.delivery_text(notice))
                        urgent = True
                        self._knocked(r, e, s, resting)
                continue
            if e.get("by") == "house":
                # Alex, 30 Sep ("make it so they get woken when something is there for them"): the house's own word on
                # your commission (landed, landed then reverted, the worker stopped, failed) reaches you as the worker's
                # does; everything else the house writes is its bookkeeping. Sable's a1062 and a1101 failed this
                # morning, and the only sign was their absence from a view that hides failures.
                if not (e["verb"] == "comment" and asked(s)):
                    continue
            said = " ".join(str(v) for k, v in args.items() if isinstance(v, str) and k != "mark")   # a5007: a mark is said in words
            waits = resting and rooms.kind_of(w, e.get("by")) != "person"     # kept, first and marked for it
            if e["verb"] == "prop" and e["target"] == r.rid and args.get("call"):
                # Alex, 30 Sep: the Desktop's wake button sets call=<who> on the corner (want=awake alone changed
                # nothing for a resident resting by choice, so it was refused as a no-op). A call ends a rest the
                # resident chose, as an @name would; the house clears the prop once it's delivered (step).
                # a1062: `wake <name>` sets the same prop, marked via=wake; the wake says who and why
                how = f"woke you (wake, {e['id']})" if e.get("via") == "wake" else f"called you from the Desktop ({e['id']})"
                r.state.setdefault("calls", []).append({"by": e["by"], "text": f"~ {e['by']} {how}"})
                urgent = True
                continue
            at = str(e.get("at") or "")[11:16]
            if s and s["kind"] == "chat" and "append" in args:
                members = rooms.members_of(s)
                # a2662: whom the line calls is its stored address (to=, a1581), never its words read again; a line
                # with none (from before lines) is read once by the same rule. The receipt asks the same question.
                to, _ = rooms.line_to(e)
                now_ = rooms.calls(w, s, to, actor)
                # Ordinary follow-ups in a queued conversation are addressed work
                # even without @ syntax. Otherwise reply + rest can strand them in
                # the inbox forever when timed wakes are disabled.
                now_ = now_ or (conversation_policy.queue_enabled(s)
                               and conversation_policy.human_event(w, e)
                               and conversation_policy.receives(w, s, e, actor))
                words = f"{args.get('append')}{points_at(w, e, s)}"      # a6638: and what it points at
                if sid in mine:                                    # a chat in its own corner is its own
                    if waits:                                      # a1062 (5): a book line is a note at the door,
                        self._hold(r, e, f"~ {at} in chat \"{s['title']}\" ({e['id']}): {words}")
                        urgent = urgent or now_                    # a1566: and a line addressed to it knocks
                        if now_:
                            self._knocked(r, e, s, resting)
                        continue
                    inbox.append(f"~ in chat \"{s['title']}\" ({e['id']}): {words}")
                    urgent = True
                    self._knocked(r, e, s, resting)
                elif "all" in members or actor in members or now_:
                    if now_ and waits:                             # a1566: kept, first and marked, and it knocks
                        self._hold(r, e, f"~ {at} in chat \"{s['title']}\" ({e['id']}): {words}")
                        urgent = True
                        self._knocked(r, e, s, resting)
                        continue
                    inbox.append(f"~ in chat \"{s['title']}\" ({e['id']}){' (to you)' if now_ else ''}: {words}")
                    urgent = urgent or now_
                    if now_:
                        self._knocked(r, e, s, resting)
                continue
            # a916, as Sable, Pike and Juniper agreed: outside a chat line, @everyone and @all never reach anyone (a
            # broadcast from a document edit is almost never meant; a chat line is the place for it). a2733: @name in a
            # note, task or comment reaches that person only as a header, the rule a chat line has (a2715): a comment by
            # the @names that open it, a note edit by the headers of the lines it added, never the rest of the note
            # again (Pike a611, Claude e4918, Sable c2804). A mid-line @ is a mention, and calls no one.
            # a5007 (Alex, a4934): a builder's comment on a commission wakes its asker only when it asks (mark=ask); one
            # unmarked reaches only whom it names itself (rooms.builder_quiet, which the knock record asks too)
            quiet = rooms.builder_quiet(w, e, s)
            asks = e["verb"] == "comment" and args.get("mark") == "ask"
            to = rooms.named_to(e) if quiet else rooms.comment_to(e) if e["verb"] == "comment" else written(e)[0]
            m = [n for n in to if n not in rooms.EVERYONE and rooms.same_person(w, n, actor)]
            if m:
                where = f" on \"{s['title']}\"" if s else ""
                address = "in your thread" if e["verb"] == "comment" and args.get("id") else f"as @{m[0]}"
                how = "asks you (a question)" if asks else "called you"
                if waits:                                          # a1566: a call is kept first, and knocks
                    self._hold(r, e, f"~ {at} {e['by']} {how}{where}, {address} ({e['id']}): {said[:300]}")
                    urgent = True
                    self._knocked(r, e, s, resting)
                    continue
                inbox.append(f"~ {e['by']} {how}{where}, {address} ({e['id']}): {said[:300]}")
                urgent = True
                self._knocked(r, e, s, resting)
            elif quiet:
                continue
            elif rooms.comment_falls_back(e) and sid in mine:
                inbox.append(f"~ {e['by']} {'asks a question' if asks else 'commented'} on \"{s['title']}\" ({e['id']}): {said[:300]}")
                urgent = True
                self._knocked(r, e, s, resting)
            elif rooms.comment_falls_back(e) and asked(s):
                inbox.append(f"~ {e['by']}{' asks you a question' if asks else ''} on your commission \"{s['title']}\" "
                             f"({e['id']}): {said[:1500]}")
                urgent = True
                self._knocked(r, e, s, resting)
        r.state["cursor"] = len(w.events)
        r.save()
        return urgent

    @staticmethod
    def stage_delivery(r, lines):
        """Move consumed input and attachment references into a durable send handoff.

        send replaces this journal with pending in the same state save. A crash
        before send therefore recovers the consumed batch through undelivered.
        """
        if not lines:
            return
        draft = r.state.setdefault("handoff", {"kind": "news", "carry": ""})
        draft["carry"] = "\n".join(([draft["carry"]] if draft["carry"] else []) + list(lines))
        for key in ("image_comments", "message_contexts"):
            draft[key] = list(dict.fromkeys(draft.get(key, []) + r.state.pop(key, [])))
        r.save()

    def take(self, r, at=""):
        """Return the ordered inbox, durably staged until send records pending."""
        first = self.first(r, at)
        lines = r.state.pop("inbox", None) or []
        self.stage_delivery(r, lines)
        return first + lines

    def first(self, r, at=""):
        """a1062: what is said first when a resident is reached, and empties it: who woke it (and why: the last line
        the waker left that was held, if any), then what was kept for it while it rested, each with its chat and time.
        a4473: `at` (it_is()) goes on the first 'woke you' line, when no woken_by line came before to carry it."""
        calls = r.state.pop("calls", None) or []
        held = r.state.pop("for_you", None) or []
        head = []
        for c in calls:
            why = next((h for h in reversed(held) if h["by"] == c["by"]), None)
            if why is not None:
                held.remove(why)
            head.append(c["text"] + ("" if head else at) + (", for the line they left you:\n  " + why["text"] if why else ""))
        if held:
            head.append(f"for you while you rested ({len(held)}):\n" + "\n".join("  " + h["text"] for h in held))
        self.stage_delivery(r, head)
        return head

    def _hold(self, r, e, text):
        """a1062: keep a line for the resident's next wake, marked for it."""
        r.state.setdefault("for_you", []).append({"by": e.get("by"), "id": e["id"], "text": text})

    def _knocked(self, r, e, s, resting):
        """a3150: remember which line ended this rest, for the wake's first line (woken_by). Only while it rests: a
        line heard with a receipt woke no one."""
        mid = (e.get("args") or {}).get("line_id")
        if mid and s:
            line = next((line for line in s.get("lines", []) if line["id"] == mid), None)
            if line and (line.get("fields") or {}).get("context"):
                # A corner's owner hears its chat even when a line calls someone
                # else. Attachments follow the stored address, not that ambient feed.
                import rooms
                world = self.load()
                actor = (world.nodes.get(r.rid, {}).get("props") or {}).get("actor")
                if actor and rooms.calls(world, s, rooms.line_to(e)[0], actor):
                    refs = r.state.setdefault("message_contexts", [])
                    if mid not in refs:
                        refs.append(mid)
        cid = (e.get("undo") or {}).get("drop_comment") or (e.get("args") or {}).get("id")
        if e.get("verb") in ("comment", "resolve") and cid and s:
            c = next((c for c in s.get("comments", []) if c["id"] == cid), None)
            if c and c.get("image"):
                refs = r.state.setdefault("image_comments", [])
                if cid not in refs:
                    refs.append(cid)
        if not resting:
            return
        mid = (e.get("args") or {}).get("line_id")
        line = bool(s) and s["kind"] == "chat" and "append" in (e.get("args") or {})
        asks = e.get("verb") == "comment" and (e.get("args") or {}).get("mark") == "ask"      # a5007: it names a question
        what = (f"line {mid} ({e['id']})" if mid else f"line ({e['id']})") if line \
            else f"{'question' if asks else 'comment' if e['verb'] in ('comment', 'resolve') else e['verb']} ({e['id']})"
        where = (f" in \"{s['title']}\"" if line else f" on \"{s['title']}\"") if s else ""
        r.state.setdefault("knocked_by", []).append(f"{e['by']}'s {what}{where}")

    def woken_by(self, r, word="woken by"):
        """a3150 (Claude e5528 (2)): the first line of a wake a line caused, naming it by id, or []; and forgets it.
        '~ woken by juniper's line m12 (e5511) in "Lounge talk"'. At a wake that came for another reason (a timed
        rest's end, a start) the lines that called it meanwhile are said as 'called by'.
        a4473 (Alex, 13 Oct: 'all agents should know the time ... dont make it like annoying'): the line ends with the
        time now, ' · it is 13 Oct, 10:46', since a wake by a call runs no look and its lines say only when each was
        sent."""
        by = list(dict.fromkeys(r.state.pop("knocked_by", None) or []))
        return [f"~ {word} " + "; ".join(by) + it_is()] if by else []

    def record_knocks(self, w, corners):
        """a3150 (Sable c2705 on a1941): one knock event per line that named or reached someone, saying per name what
        happened: woken / in a turn, held for its end / asleep / not a member, not knocked / an agent, not knocked.
        Decided here, once, before any resident is served this pass, by the reading the knock itself uses
        (rooms.reached). A plain line that calls no one adds nothing (Claude e5528 (1)).
        Once per line, across house restarts (the lesson of e07531f: what was said is remembered in the world, not in
        the house): the record is an event whose cause is the line, and a line that has one is never recorded again,
        by this house or the next (the desk refuses a second, too). knocks.json holds only where to go on from, so a
        line said while no house ran is recorded by the one that follows; with no such file (the first house with this
        code, or a lost state folder) it starts at the end: old lines are not gone over, and never one that every
        awake resident has already heard. -> the world, loaded again
        when something was written."""
        import rooms
        path = self.dir / "knocks.json"
        try:
            st = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            st = {}
        # never further back than a line some awake resident has still to hear: what all of them heard was decided
        # long ago, and a record made now would say 'woken' of today's house (a cursor wrongly low went over 5,000
        # old lines in a test). No resident with a place kept: from the end.
        heard = [r.state["cursor"] for rid, c in corners.items() for r in [self.residents.setdefault(rid, Resident(self, rid))]
                 if (c.get("props") or {}).get("want", "awake") == "awake" and "cursor" in r.state]
        floor = min(min(heard), len(w.events)) if heard else len(w.events)
        start, end, wrote = max(min(int(st.get("cursor", len(w.events))), len(w.events)), floor), len(w.events), False
        for k in range(start, end):
            e = w.events[k]
            how = rooms.reached(w, e)
            if not how or rooms.knock_of(w, e["id"]) is not None:
                continue
            out = self.act("house", "knocked " + e["id"] + " " + json.dumps({a: self.knock_word(w, a, h) for a, h in how.items()}))
            wrote = True
            if not re.search(r"^ok e\d+: knock recorded", out, re.M) and "already has" not in out:
                # refused (a desk older than this house): tried again next pass, three times, then left unrecorded
                st["tries"] = st.get("tries", 0) + 1 if st.get("at") == e["id"] else 1
                st["at"] = e["id"]
                print(f"house: knock record for {e['id']} refused ({st['tries']}): {out[-200:]}", flush=True)
                if st["tries"] < 3:
                    end = k
                    break
        if st.get("cursor") != end or wrote:
            st["cursor"] = end
            path.write_text(json.dumps(st), encoding="utf-8")
        return self.load() if wrote else w

    def knock_word(self, w, actor, how):
        """a3150: what happened to a resident a line reached, as the house sees them at this moment."""
        import rooms
        if how == "an agent, not knocked":
            # a5267: an agent the house does not run is knocked when a listener of theirs runs (listeners.py), which
            # hears this record and carries it; with none, their own word (rooms.REACH) or the house's
            import listeners
            said = listeners.word(self.world, actor, rooms.REACH.get(str(actor).lower()))
            return said[1] if said else how
        if how not in ("call", "book"):
            return how
        rid = rooms.corner_of(w, actor)
        r = self.residents.get(rid)
        props = (w.nodes.get(rid) or {}).get("props") or {}
        if props.get("want", "awake") != "awake":
            return "asleep (want=rest), kept for their wake"
        if r is not None and r.busy:
            return "in a turn, held for its end"
        if r is not None and not r.alive() and r.state.get("retry_at", 0) > now() and not props.get("call"):
            return "not running (backing off after a failure), kept for their next start"
        return "woken" if how == "call" else "not knocked: a plain line in their own chat waits for their next wake"

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
        if self.world == "frontier" and not self.fake:
            try:
                charter.sync(w, self.act, HERE.parents[2] / "AGENTS.md", self.charter_state)
            except Exception as exc:
                print(f"house: charter mirror: {type(exc).__name__}: {exc}", flush=True)
            w = self.load()
        cfg = self.settings(w)
        corners = self.corners(w)
        open_ = [s for s in w.subjects.values() if (s.get("props") or {}).get("objective") == "open"]
        objective = bool(open_)
        # 9 Oct (a3806; Juniper: 'no word of which objective; I guessed'): the timed wake names what is open
        self.objectives = "; ".join(f"{(w.appearances_of(s['id']) or [s['id']])[0]} \"{str(s.get('title', ''))[:60]}\""
                                    for s in open_[:3]) + (f" and {len(open_) - 3} more" if len(open_) > 3 else "")
        if not (self.workshop.restart_wanted and os.environ.get("HOUSE_KEEPER")):
            # a3150: who each new line knocks is recorded before anyone is served, so 'in a turn' is as the line found
            # them; while a restart waits no one is knocked, so the house that follows records it (as it does the news)
            w = self.record_knocks(w, corners)
        self.toasts(w)
        for rid, corner in corners.items():
            r = self.residents.setdefault(rid, Resident(self, rid))
            props = corner.get("props") or {}
            actor, want = props.get("actor"), props.get("want", "awake")
            for text in r.turns_ended():
                self.after_turn(w, r, corner, actor, text)
                w = self.load()
                corner = w.nodes.get(rid, corner)
                actor = (corner.get("props") or {}).get("actor")
            props = corner.get("props") or {}
            actor, want = props.get("actor"), props.get("want", "awake")
            if want != "awake" or not actor:               # a resident is given its name (Alex, 29 Sep); none, no start
                if r.alive() and not r.busy:
                    r.stop()
                if r.state.pop("at_rest", None) is not None:    # asleep is not a rest: want=awake wakes it in full
                    r.save()
                self.set_status(r, corner, "asleep" if actor else "unnamed")
                continue
            if resident_continuity.switching(r.state, props):
                if r.busy:
                    continue  # let the in-flight turn finish; send() parks its follow-up
                model = props.get("model") or cfg["model"]
                try:
                    resident_continuity.validate(r.state, props, model)
                    if r.alive():
                        r.stop()
                    resident_continuity.prepare(r, props, model)
                except ValueError as exc:
                    detail = str(exc)
                    if r.state.get("provider_error") != detail:
                        r.state["provider_error"] = detail
                        r.save()
                        r.log("provider_error", detail)
                    self.set_status(r, corner, "error")
                    continue
            if not r.alive():
                provider = props.get("provider", "claude")
                held = self.plans.wait_until(provider)
                if held > now():
                    self.plans.paused(provider, rid, held)
                    self.set_status(r, corner, "paused")
                    continue
                if props.get("call") and r.state.get("retry_at", 0) > now() and r.state.get("retry_kind") != "limit":
                    # a press of wake overrides a back-off, once: the call is used up, so a failure after it backs off again
                    r.state.pop("retry_at")
                    r.log("retry", {"why": f"called by {props['call']} while backing off"})
                    self.act("house", f"look {rid} :1; do prop {rid} remove=call")
                if r.state.get("retry_at", 0) > now():
                    self.set_status(r, corner, "paused" if r.state.get("retry_kind") == "limit" else "error")
                    continue
                first = not r.started
                r.start(props.get("model") or cfg["model"])
                r.started = True
                # 3 Oct (Pike e5914, Sable e5917): a restart for new code started every resident's process and woke each
                # one for a whole turn with no caller, at every landing of a house file, through any rest. A resident
                # resting when the house stopped, whose conversation resumes with nothing unanswered, keeps resting:
                # its rest ends as it would have (a call, its time, the house's own wake), on the resumed conversation
                resting = bool(r.state.get("at_rest") or r.state.get("rest_until"))     # (a rest from older code)
                keep = first and resting and r.state.get("session") and \
                    not any(r.state.get(k) for k in ("unanswered", "undelivered", "lost", "door", "welcome_due"))
                if keep:
                    r.log("restart", {"why": "resting when the house restarted; not woken"})
                else:
                    r.state.pop("woke", None)
            if r.busy:
                continue
            if self.workshop.restart_wanted and os.environ.get("HOUSE_KEEPER"):
                # 30 Sep (a1062 landed at 14:41 and the house was still on older code at 15:00): the restart waits for a
                # moment with no one mid-turn, and with three residents and three workers that moment never came. While
                # it waits, no new turn starts; news stays unread (the cursor isn't moved) for the house that follows
                continue
            if not r.state.get("woke"):
                self.wake(r, corner, actor, "")
                continue
            called = self.news(w, r, actor, resting=True)     # between turns: a line from a resident waits (a1062)
            idle = now() - r.state.get("last_turn", now())
            until = r.state.get("rest_until")
            # a1062: when the house would wake it on its own, the latest a held line waits (said in a speaker's receipt)
            last = r.state.get("last_turn", now())
            # 9 Oct (a3806; Sable woken about ten times, Juniper five in seven minutes, by an open objective with
            # nothing new): each timed wake that its resident answered without changing anything doubles the wait
            # before the next, up to wake_every; a turn that changes the world, or a call, makes it short again. A
            # resident at work on the objective is still asked every `breather`; one who looked and rested is let be
            breather = min(float(cfg["breather"]) * 2 ** min(int(r.state.get("idle_wakes", 0)), 12), float(cfg["wake_every"]))
            # a8980: chosen rest deadlines are promises, separate from periodic wakes.
            # No OS timer: if the machine sleeps, the next ordinary pass handles overdue rests.
            timers = str(cfg.get("timers", "off")).strip().lower() == "on"
            rest_wakes = str(cfg.get("rest_wakes", "on")).strip().lower() == "on"
            r.wakes_at = ((until if rest_wakes else None) if until else
                          (last + breather if objective else last + float(cfg["wake_every"])) if timers else None)
            if called:                                     # a call ends any rest
                r.state["idle_wakes"] = 0
                r.state.pop("rest_until", None)
                r.state.pop("rest_for", None)
                r.wakes_at = None
                head = self.woken_by(r)                    # a3150: its first line names the line, a4473: and the time
                r.send("\n".join(head + self.take(r, "" if head else it_is())))
                if props.get("call"):                      # delivered: clear it, so the next press is a change again
                    self.act("house", f"look {rid} :1; do prop {rid} remove=call")
            elif until and rest_wakes and now() >= until:
                slept = r.state.pop("rest_for", None) or 0
                r.state.pop("rest_until", None)
                r.wakes_at = None
                self.wake(r, corner, actor, f"(you rested {human(slept)})\n")
            elif until or not timers:  # pending/disabled chosen rest, or no periodic wakes
                self.set_status(r, corner, "awake")
                continue
            elif objective and idle >= breather:
                r.state["idle_wakes"] = int(r.state.get("idle_wakes", 0)) + 1
                self.wake(r, corner, actor, f"(time passes; an objective is open: {self.objectives}. If nothing in it is "
                                            f"yours to move now, > rest: I ask again after twice as long each time)\n")
            elif idle >= float(cfg["wake_every"]):
                self.wake(r, corner, actor, "(time passes)\n")
            else:
                self.set_status(r, corner, "awake")
                continue
            self.set_status(r, corner, "awake")
        self.workshop.step(self.load(), cfg)
        self.beat(corners)
        try:     # a5988: the feeds someone watches (At work, in the home base); a feed never stops a pass
            self.feeds.step(self.load(), corners, feeds.house_states(self, corners))
        except Exception as e:
            print(f"house: feeds: {type(e).__name__}: {e}", flush=True)
        try:     # a6265: context and limit use for At work (written at most every usage.GAP s, only when changed)
            self.usage.step()
            self.plans.publish()
        except Exception as e:
            print(f"house: usage: {type(e).__name__}: {e}", flush=True)
        try:     # a6249: Alex's scripts (notes role=script) kept in step with their files; only the live world's house
            self.scripts.step(self.load(), lambda line: self.act("house", line, whole=True))
        except Exception as e:
            print(f"house: scripts: {type(e).__name__}: {e}", flush=True)

    def wake(self, r, corner, actor, lead):
        line = (corner.get("props") or {}).get("wake") or "look"       # a1027: scripts retired; arrive was the old tree
        r.state["quiet"] = 0
        started = not lead                                # no reason given: the house started its process
        if r.state.get("lost") or r.state.get("welcome_due"):
            r.state.pop("wake_read", None)                # a memory that begins again is shown its notes whole again
        if r.state.pop("lost", None):
            lead = "(the house lost our earlier conversation; your soul and the world kept everything)\n" + lead
        # Alex (29 Sep): who they are, one line at the top of every arrival, so a name outlives a fading memory
        lead = f"You are {actor}. Your corner is {r.rid}.\n" + lead
        undelivered = r.state.pop("undelivered", "")
        self.stage_delivery(r, [undelivered] if undelivered else [])
        r.state.pop("cut_by_restart", None)              # older state: now said through unanswered
        if undelivered:                                  # it never reached this conversation: said in full, once
            lead += "(a message I had for you never reached you; here it is:)\n" + undelivered + "\n(and your wake:)\n"
        unanswered, why_not = r.state.pop("unanswered", 0), r.state.pop("unanswered_why", "")
        r.state["woke"] = now()
        if unanswered and not undelivered:
            # 1 Oct (Sable e4659, Pike a1660, Juniper e4662): what was sent is already in this conversation, unanswered.
            # One line says so, and only what is new since follows; the wake itself is not sent again, so failures
            # never make the next turn longer. A resident acts only through > lines run after its turn, so none ran
            self.news(self.load(), r, actor, resting=True)
            callers = {c["by"] for c in r.state.get("calls") or []}
            head = self.woken_by(r, "called by")
            first, heard = head + self.first(r, "" if head else it_is()), self.take(r)
            note =(f"(your last {unanswered} turn{'s' if unanswered != 1 else ''} did not finish: {why_not[:200]}. "
                    f"What I sent you is above in this conversation, unanswered, and none of its > lines ran. "
                    f"Answer the newest of it now; below is only what is new since.)")
            r.send(lead + note + "".join("\n" + x for x in first + heard), "wake", carry="\n".join(first + heard))
            if ((self.load().nodes.get(r.rid) or {}).get("props") or {}).get("call") in callers:
                self.act("house", f"look {r.rid} :1; do prop {r.rid} remove=call")
            self.set_status(r, corner, "awake")
            return
        # what came while it slept is said with the wake, not dropped; a1062: a line kept for it (or that would have
        # called it, from a resident) comes first, marked for it, before the wake's own look
        self.news(self.load(), r, actor, resting=True)
        callers = {c["by"] for c in r.state.get("calls") or []}
        head = self.woken_by(r, "called by")              # a3150: the line that called it, by id, comes first
        first = head + self.first(r, "" if head else it_is())
        heard = self.take(r)
        news = "\n".join(([undelivered] if undelivered else []) + first + heard)
        if started and not first:
            # a1941 (Pike, 2 Oct: woken minutes into a two-hour rest, 'no caller, silent about why'): a house that
            # starts a resident's process wakes it, mid-rest or not; the wake now says that this is why
            lead += "(the house started you; no one called)\n"
        lead += "".join(x + "\n" for x in first)
        stored = r.rid if (corner.get("props") or {}).get("wake") else None      # a1156: a wake is stored text
        woke = self.fold_reads(r, line, self.act(actor, line, stored=stored, kind="wake"))
        r.send(lead + woke + ("\n" + "\n".join(heard) if heard else ""), "wake", carry=news)
        # a1062: a call delivered by a wake (a resident started from want=rest) is cleared too, so the next is a change
        if ((self.load().nodes.get(r.rid) or {}).get("props") or {}).get("call") in callers:
            self.act("house", f"look {r.rid} :1; do prop {r.rid} remove=call")
        self.set_status(r, corner, "awake")

    def fold_reads(self, r, line, text):
        """A wake line's `read <note>` whose note has not changed since this conversation was last shown it prints one
        line instead of the note. 9 Oct (a3806): each corner's wake reads its soul or letter (8 to 16 thousand
        characters) into a conversation that already holds it; Pike, Juniper and Sable each named it first among what
        they skip. What was read is kept by the note's revision (state wake_read), and forgotten when the conversation
        begins again (lost, compacted, fresh), so a memory that lost the note is shown it whole. A chat is left alone:
        its read already shows only what is new. `read <id> :3`, typed by the resident, always prints the note."""
        import desk
        try:
            w = self.load()
            parts = desk.split_batch(line)
            blocks = re.split(r"(?m)^(?=\[\d+\] )", text) if len(parts) > 1 else ["", text]
            if len(blocks) != len(parts) + 1:
                return text
            seen = r.state.setdefault("wake_read", {})
            for k, part in enumerate(parts, 1):
                m = re.match(r"read\s+([afs]\d+)\b", part.strip())
                node = w.nodes.get(m.group(1)) if m else None
                s = w.subjects.get((node or {}).get("subject") or (m.group(1) if m else ""))
                if not s or s.get("kind") == "chat":
                    continue
                mark, was = [s["id"], s["rev"]], seen.get(part)
                seen[part] = mark
                rows = blocks[k].splitlines()
                at = next((i for i, l in enumerate(rows) if l.startswith(s["id"] + " ")), None)
                words = len(str(s.get("text", "")).split())
                if was == mark and at is not None and words > 60:      # a short note costs less than saying so
                    blocks[k] = "\n".join(rows[:at] + [
                        f"{m.group(1)} {s['kind']} \"{s['title']}\" · {words}w · unchanged since I last showed it to you in "
                        f"this conversation, so not printed again (read {m.group(1)} :3 prints it)"]) + "\n\n"
            return "".join(blocks).rstrip("\n")
        except Exception as e:        # a wake must arrive whatever the fold thought
            r.log("fold_reads", f"{type(e).__name__}: {e}"[:200])
            return text

    def after_turn(self, w, r, corner, actor, text):
        if text is None or isinstance(text, dict):     # the process ended, or its turn failed
            self.failed(r, corner, text)
            return
        if not actor:                          # its name was taken away mid-turn: nothing is done in the world unsigned
            return
        interrupts = conversation_policy.queued_interrupts(self.load(), actor, r.state.get("cursor"))
        if interrupts:
            # Do not replay stale actions after a stop/correction. The original
            # output remains in the transcript; the next turn receives all queued
            # messages and decides afresh with the person's current direction.
            r.log("turn_interrupted", {"messages": [x["message"] for x in interrupts],
                                       "events": [x["event"] for x in interrupts]})
            self.news(self.load(), r, actor)
            heard = self.take(r)
            r.send("Your previous turn's pending commands were not executed because a new human "
                   "stop/cancellation/correction arrived. Follow the latest direction below; do not "
                   "automatically repeat the held commands.\n" + "\n".join(heard), "news")
            return
        attempts, rest = rest_in(commands_in(text))
        n0 = len(w.events)
        # a5068: news runs only between turns, so the cursor is where this turn's input left off (a2870 Revision 2)
        receipt = self.act(actor, "\n".join(attempts), whole=True, as_of=r.state.get("cursor")) if attempts else ""
        host_receipts = getattr(text, "host_receipts", ())
        if host_receipts:
            receipt = "\n".join(([receipt] if receipt else []) + list(host_receipts))
        if attempts and any(e.get("by") == actor and e.get("verb") != "go" for e in self.load().events[n0:]):
            r.state["idle_wakes"] = 0         # it changed something: an open objective asks again after `breather`
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
        r.state["quiet"], r.state["at_rest"] = 0, True
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
            # a3204 (Pike lived it, 3 Oct): this line is the house's, sent as the resident, and its answer goes only to
            # the log; it says so, so that whoever answers keeps a word meant for the resident for a line they will see
            r.log("home", self.act(actor, "rest :1", kind="rest")[:300])

    def failed(self, r, corner, why):
        """One judgement per process (a failed turn is followed by the process's exit). A lost conversation is not
        a failure of the resident: the world holds its soul and its history, so it starts fresh from the world.
        Anything else backs off, 1 min doubling to 1 h, so a broken resident never spins."""
        if r.failed:
            return
        r.failed = True
        if r.alive():
            r.stop()
        pending = r.state.pop("pending", None) or {}
        carry = pending.get("carry")
        if r.lost_conversation():
            r.log("lost", {"session": r.state.pop("session", None)})
            r.state["lost"] = True
            if carry:                                      # a fresh conversation has none of it: said again in full
                r.state["undelivered"] = (r.state.get("undelivered", "") + "\n" + carry).strip("\n")
            for key in ("image_comments", "message_contexts"):
                r.state[key] = list(dict.fromkeys(r.state.get(key, []) + pending.get(key, [])))
            r.save()
            return
        r.hold_unanswered(pending, (why or {}).get("detail") if isinstance(why, dict) else "the process ended")
        n = r.state.get("failures", 0) + 1
        reset = limit_reset((why or {}).get("detail") if isinstance(why, dict) else "")
        detail = (why or {}).get("detail", "") if isinstance(why, dict) else ""
        if reset or workshop.usage_limited(detail):
            provider = r.state.get("session_provider", "claude")
            plans = getattr(self, "plans", None)
            reset = (plans.reset(provider) if plans else 0) or reset
            retry_at = reset + 60 if reset else now() + 300
            r.state.update(retry_at=retry_at, retry_kind="limit")
            r.save()
            if plans:
                plans.paused(provider, r.rid, retry_at)
            self.set_status(r, corner, "paused")
            return
        # a usage limit is not the resident failing: try again a minute after the reset it names, not on a doubling
        r.state["failures"], r.state["retry_at"] = n, (reset + 60 if reset else now() + min(60 * 2 ** (n - 1), 3600))
        r.state["retry_kind"] = "process"
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
                                     "wakes_at": r.wakes_at, "held": len(r.state.get("for_you") or []),
                                     "said": r.state.get("said", [])}
        out["workers"] = {cid: {"actor": wk.actor, "asked_by": wk.asked_by, "alive": wk.alive(),
                                "doing": "working" if wk.busy else ("waiting" if wk.alive() else "stopped"),
                                "turns": wk.state.get("turns", 0), "branch": wk.branch,
                                "builder": getattr(wk, "builder", None)}
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
        # 30 Sep: a commit by hand (not a landing) that changed the lab's Python left the house on old code for hours,
        # and once half-imported new code (the QUOTED import error). A commit that changes a file the house runs
        # (workshop.HOUSE_FILES) asks for the same restart a landing does. Checked every 30 passes (about a minute).
        def head():
            r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=HERE, capture_output=True, text=True)
            return r.stdout.strip() if r.returncode == 0 else ""
        started_on, passes = head(), 0
        checked_on = started_on       # the HEAD-watch's baseline; started_on stays what this process imported
        # a10269: a restart asked for from the world; the one that brought this house up says so on its note
        self.restarts = house_restart.Restarts(self)
        try:
            self.restarts.started_up(self.load())
        except Exception as e:
            print(f"house: restart notes unreadable at start: {type(e).__name__}: {e}", flush=True)
        # No timer: startup requests one full comparison from the live writer.
        try:
            self.act("house", "log-world check", whole=True)
        except Exception as e:
            print(f"house: log-world startup request unavailable: {type(e).__name__}: {e}", flush=True)
        guard_publisher = None
        if self.world == "frontier" and not self.fake:
            guard_publisher = guard_context.Publisher()
        try:
            if guard_publisher:
                guard_publisher.start()
            while True:
                if guard_publisher:
                    try:
                        guard_publisher.update(self.settings(self.load()).get("guard_nongame", ""))
                    except Exception as exc:
                        guard_publisher.update("")
                        print(f"house: guard policy unavailable: {type(exc).__name__}", flush=True)
                try:
                    self.step()
                except Exception as e:
                    print(f"house: step failed: {type(e).__name__}: {e}", flush=True)
                    # the house still holds the world.py/desk.py it started with (export_docs.load unpickles in this
                    # process); if newer code is committed under a failing step, that may be why: restart onto it
                    if started_on and not self.workshop.restart_wanted and head() not in ("", started_on):
                        print("house: a step failed and the code has changed since I started; restarting onto it", flush=True)
                        self.workshop.restart_wanted = True
                passes += 1
                if started_on and passes % 30 == 0 and not self.workshop.restart_wanted:
                    now_on = head()
                    if now_on and now_on != checked_on:
                        d = subprocess.run(["git", "diff", "--name-only", checked_on, now_on, "--", "."], cwd=HERE,
                                           capture_output=True, text=True).stdout.split()
                        if any(Path(p).name in workshop.HOUSE_FILES for p in d):
                            print(f"house: the code under me changed ({checked_on[:7]} -> {now_on[:7]}); restarting within {RESTART_GRACE} s", flush=True)
                            self.workshop.restart_wanted = True
                        else:
                            checked_on = now_on       # nothing the house runs changed: deskd and the next command have it
                busy = ([r.rid for r in self.residents.values() if r.busy]
                        + [c for c, x in self.workshop.workers.items() if x.busy]
                        + [f"landing {c}" for c in self.workshop.landing])      # a landing being judged is never cut
                try:
                    w = self.load()
                    cfg = self.settings(w)
                    self.restarts.step(w, cfg, busy, keeper=bool(os.environ.get("HOUSE_KEEPER")))
                except Exception as e:
                    cfg = {}
                    print(f"house: restart notes: {type(e).__name__}: {e}", flush=True)
                if self.workshop.restart_wanted and os.environ.get("HOUSE_KEEPER"):
                    self.restart_since = getattr(self, "restart_since", None) or now()
                    # a10269: a restart the world asked for waits for idle and cuts nothing; a landing's still cuts
                    # after RESTART_GRACE, as before
                    if house_restart.should_exit(self.restarts.owns, busy, now() - self.restart_since, RESTART_GRACE):
                        if not self.restarts.leaving(cfg):
                            print("house: a requested restart was refused at the last moment (the guard)", flush=True)
                            self.restart_since = None
                            time.sleep(2)
                            continue
                        print("house: " + ("restarting as asked in the world" if self.restarts.owns
                                           else "the code changed; restarting on it")
                              + (f" (cutting {', '.join(busy)}: each resumes, and is told)" if busy else ""), flush=True)
                        self.exit_code = RESTART
                        break
                else:
                    self.restart_since = None
                time.sleep(2)
        except KeyboardInterrupt:
            pass
        finally:
            if guard_publisher and guard_publisher.thread.ident is not None:
                guard_publisher.close()
            everyone = list(self.residents.values()) + list(self.workshop.workers.values())
            for x in everyone:          # every pipe closed first, so the waits in stop() overlap (not 20 s each)
                try:
                    if x.proc:
                        x.proc.stdin.close()
                except Exception:
                    pass
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
