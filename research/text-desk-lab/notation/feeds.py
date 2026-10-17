"""feeds: what an agent of the house is doing, as short rows a lens can follow (a5988, Alex 16 Oct: 'clicking on At work
should allow me a view into their live conversation feed, all their thoughts and actions taken').

The house already keeps every stream event of each resident and worker, and every message it sent them, in
house-state/<world>/<dir>/transcript.jsonl (house.Resident.log). A feed is that transcript made readable and safe:

    witnessed:feed-<id>         the feed of the agent of thing <id> (a card's worker=, a resident's corner): rows, oldest
                                first, the last CAP events: n (1, 2, ... in the order they came), at (HH:MM:SS), kind
                                (said, thought, read, run, edit, commit, desk, comment, ask, web, tool, result, error,
                                heard, start, end, rest), group (thoughts, actions, errors, life), text (trimmed,
                                redacted); first one row kind=head: who, card, title, state, since, for, last (the
                                newest n), events (lines kept), from and newest (the earliest and newest kept
                                lines' times)

It is a witnessed source (witnessed.py), so the door tells every painter when it changes and a lens repaints with no
reload. The house writes a feed only while someone watches it: a note that stands the lens home-feed on a thing
(with=home-feed viewing=<id>: the home base's viewer, which At work opens so), or a thing with watching=<id>.
Unwatched, nothing is read or written, and the file is removed; watching again reads the transcript's tail afresh.
Each pass reads only the bytes added since the last (a file offset), and a feed is written at most every GAP seconds,
since every write repaints every open painter.

What a feed cannot show, and says so: an agent's hidden reasoning. Claude's stream-json gives a thinking block's
signature and duration but no words, and Codex's reasoning items arrive with empty summary and content, so a thought
is 'thought for N s' and the words of a thought are the words the agent wrote between its actions.

Redaction (redact()): whatever looks like a secret is replaced by [redacted ...] before it is kept: private key
blocks, known key and token shapes, bearer and basic credentials, a password or token given as name=value or
'password is', credentials in a URL, and any long run of mixed letters and digits. It refuses rather than guesses: a
commit hash may be cut, a key is never shown. A tool call that touches a .env file has its result withheld whole.

    python feeds.py <world> [--from <house-state dir of another world>] [--for <seconds>] [--once]

runs the same writer outside the house (a copy of a world has no house: it reads another world's transcripts, never
writing there). Ctrl+C, the end of --for, or --once stops it, and its feeds go with it (a witnessed file whose writer
has stopped reads as no rows).
"""
import collections
import json
import math
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAP = 500                    # rows kept per feed
SEED = 6_000_000             # bytes of a transcript's tail read when a feed is first watched (tool results are big)
WORDS = 600                  # characters of what an agent wrote
ARGS = 200                   # characters of a tool call's arguments
RESULT = 200                 # characters of a tool's result
GROUPS = {"said": "thoughts", "thought": "thoughts", "error": "errors",
          "start": "life", "end": "life", "rest": "life", "heard": "life"}

# ---- redaction ------------------------------------------------------------------------------------------------
R = "[redacted]"
_PEM = re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?(-----END [A-Z0-9 ]*PRIVATE KEY-----|\Z)", re.S)
_SHAPES = re.compile(r"""(
      sk-ant-[A-Za-z0-9_\-]{8,}            # Anthropic
    | sk-(?:proj-|live-|test-)?[A-Za-z0-9_\-]{16,}   # OpenAI, Stripe and the like
    | (?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{16,} | github_pat_[A-Za-z0-9_]{16,}
    | glpat-[A-Za-z0-9_\-]{16,} | npm_[A-Za-z0-9]{24,} | xox[abposr]-[A-Za-z0-9\-]{10,}
    | (?:AKIA|ASIA)[0-9A-Z]{16} | AIza[0-9A-Za-z_\-]{30,}
    | eyJ[A-Za-z0-9_\-]{8,}\.eyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}   # a JWT
    )""", re.X)
_AUTH = re.compile(r"(?i)\b(bearer|basic)\s+([A-Za-z0-9._~+/=\-]{8,})")
# a secret's name ends the name, or is followed by _ or - (auth_token, my-password), so `author:` is no secret
_SECRET_NAME = (r"(?:pass(?:word|wd|phrase)?|pwd|secret|token|api[_\-]?key|apikey|access[_\-]?key|private[_\-]?key"
                r"|client[_\-]?secret|auth(?:orization)?|credentials?|cookie|session[_\-]?(?:key|token))s?")
_NAMED = re.compile(r"(?i)(\b[A-Za-z0-9_\-]*?" + _SECRET_NAME + r"(?:[_\-][A-Za-z0-9_\-]*)?)"
                    r"""(["']?\s*[=:]\s*["']?)([^\s"',;)\]}]+)""")
_SAID = re.compile(r"(?i)(\b(?:password|passwd|passphrase|pwd)\s+(?:is|was|=)\s+[\"']?)([^\s\"',;)\]}]+)")
_URLCRED = re.compile(r"(?i)\b([a-z][a-z0-9+.\-]*://[^\s/:@]+:)([^\s/@]+)(@)")
_RUN = re.compile(r"[A-Za-z0-9+/=_\-]{20,}")


def _wordy(part):
    """A piece of a name, not of a key: letters, digits, or a word with a number (Agora4, a5820, ffmpeg8)."""
    return (not part or part.isdigit() or (part.isalpha() and len(part) <= 24)
            or bool(re.fullmatch(r"[A-Za-z]{1,12}\d{1,6}[a-z]?|\d{1,6}[A-Za-z]{1,12}", part)))


def _random(seg):
    """A long piece between slashes (a path's segments are words) that reads like a key: hex longer than a commit's
    40, or, once its word-like parts joined by - or _ are set aside, a part of mixed case with digits, or of digits
    with high entropy. A 40-character commit hash and C--Projects-Agora4--worktrees-a5820 pass."""
    core = seg.strip("=")
    if len(core) < 20:
        return False
    if re.fullmatch(r"[0-9a-f]+", core):
        return len(core) > 40                            # sha1 passes; longer hex (a sha256, a hex key) does not
    for p in re.split(r"[_\-]", core):
        if _wordy(p):
            continue
        upper, lower, digit = (any(c.isupper() for c in p), any(c.islower() for c in p), any(c.isdigit() for c in p))
        entropy = -sum(c / len(p) * math.log2(c / len(p)) for c in collections.Counter(p).values())
        if (len(p) >= 16 and upper and lower and digit) or (len(p) >= 24 and digit and entropy >= 4.0):
            return True
    return False


def _runs(m):
    return "/".join(R if _random(seg) else seg for seg in m.group(0).split("/"))


def redact(text):
    """-> text with anything secret-looking replaced. Applied to every word a feed keeps."""
    if not text:
        return ""
    text = _PEM.sub("[redacted private key]", str(text))
    text = _SHAPES.sub(R, text)
    text = _URLCRED.sub(lambda m: m.group(1) + R + m.group(3), text)
    text = _AUTH.sub(lambda m: m.group(1) + " " + R, text)
    text = _NAMED.sub(lambda m: m.group(1) + m.group(2) + (m.group(3) if m.group(3).startswith("[redacted") or
                                                            _harmless(m.group(1), m.group(3)) else R), text)
    text = _SAID.sub(lambda m: m.group(1) + R, text)
    return _RUN.sub(_runs, text)


def _harmless(name, value):
    """`max_tokens=4000`, `thinking_tokens: 12`, `token=none`: a count or an empty word is no secret. A password is
    always taken, whatever it is."""
    if re.search(r"(?i)pass|pwd|secret|private|cred|cookie", name):
        return False
    return bool(re.fullmatch(r"\d{1,7}|none|null|true|false|\$\w+|<\w+>|\*+|\.\.\.|…", value, re.I))


def trim(text, n):
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text if len(text) <= n else text[:n - 1].rstrip() + "…"


# ---- one record -> rows ------------------------------------------------------------------------------------------
class Reader:
    """Turns transcript records into feed rows, remembering what it needs across records: each tool call's name and
    whether it touched a .env file (by id), and whether the stream is Codex's (whose last assistant event repeats its
    messages)."""

    def __init__(self):
        self.tools = {}
        self.codex = False

    def rows(self, rec):
        """-> [(kind, text)] for one transcript record ({"at", "kind", "data"})."""
        k, d = rec.get("kind"), rec.get("data")
        if k == "start":
            return [("start", "process started" + (f" (pid {d.get('pid')})" if isinstance(d, dict) and d.get("pid") else ""))]
        if k == "exit":
            code = (d or {}).get("code") if isinstance(d, dict) else None
            return [("end" if code in (0, None) else "error", f"process ended (code {code})")]
        if k == "stop":
            return [("end", "stopped by the house")]
        if k == "rest":
            return [("rest", "rests" + (f": {trim(d.get('why'), 80)}" if isinstance(d, dict) and d.get("why") else ""))]
        if k == "failed":
            why = (d or {}).get("why") if isinstance(d, dict) else d
            if isinstance(why, dict):
                why = f"{why.get('error', '')} {why.get('detail', '')}"
            return [("error", "failed: " + trim(why, RESULT))]
        if k == "sent":
            return [("heard", trim(d, RESULT))]
        if k == "unsent":
            return [("error", "a message did not reach it: " + trim((d or {}).get("why"), RESULT))]
        if k != "event" or not isinstance(d, dict):
            return []
        t = d.get("type")
        if t == "codex_event":
            self.codex = True
            return self._codex(d)
        if t == "assistant":
            if self.codex:
                return []
            return [r for b in _blocks(d) for r in self._said(b, d)]
        if t == "user":
            return [r for b in _blocks(d) if b.get("type") == "tool_result" for r in self._result(b)]
        if t == "result":
            if d.get("is_error"):
                return [("error", f"turn failed: {d.get('subtype') or ''} {trim(d.get('result'), RESULT)}".strip())]
            return [("end", "turn ended" + (f" after {d['num_turns']} steps" if d.get("num_turns") else ""))]
        return []                   # permission_denied is said again by its tool_result, as an error

    def _said(self, b, ev):
        bt = b.get("type")
        if bt == "text":
            out = []
            words = [l for l in (b.get("text") or "").splitlines()]
            prose = [l for l in words if not l.lstrip().startswith(">")]
            if any(l.strip() for l in prose):
                out.append(("said", trim("\n".join(prose), WORDS)))
            for l in words:                     # a resident's > lines are its acts in the desk
                if l.lstrip().startswith(">") and l.lstrip()[1:].strip():
                    out.append(self._desk(l.lstrip()[1:].strip()))
            return out
        if bt == "thinking":
            if (b.get("thinking") or "").strip():
                return [("thought", trim(b["thinking"], WORDS))]
            ms = ev.get("thinking_duration_ms")
            return [("thought", f"thought for {ms / 1000:.0f} s (the words are not kept)" if ms else
                                "thought (the words are not kept)")]
        if bt == "tool_use":
            name, inp = b.get("name") or "tool", b.get("input") or {}
            self.tools[b.get("id")] = (name, ".env" in json.dumps(inp))
            return [self._call(name, inp)]
        return []

    def _call(self, name, inp):
        if name == "mcp__desk__desk" or name.endswith("__desk"):
            return self._desk(inp.get("line") or "")
        if name in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
            return ("edit", f"{name} {_short_path(inp.get('file_path') or inp.get('notebook_path'))}")
        if name in ("Bash", "PowerShell"):
            cmd = str(inp.get("command") or "")
            return ("commit" if re.search(r"\bgit\s+commit\b", cmd) else "run", trim(cmd, ARGS))
        if name in ("Read", "Glob", "Grep"):
            what = inp.get("file_path") or inp.get("pattern") or ""
            return ("read", f"{name} {trim(_short_path(what), ARGS)}" + (f" in {_short_path(inp['path'])}" if inp.get("path") else ""))
        if name in ("WebSearch", "WebFetch"):
            return ("web", f"{name} {trim(inp.get('query') or inp.get('url'), ARGS)}")
        if name in ("Agent", "Task"):
            return ("tool", f"{name}: {trim(inp.get('description') or inp.get('prompt'), ARGS)}")
        return ("tool", f"{name} {trim(json.dumps(inp, ensure_ascii=False), ARGS)}")

    def _desk(self, line):
        kind = "desk"
        if re.search(r"\bdo\s+comment\b", line):
            kind = "ask" if re.search(r"\bmark=ask\b", line) else "comment"
        return (kind, trim(line, ARGS if kind == "desk" else WORDS))

    def _result(self, b):
        name, env = self.tools.pop(b.get("tool_use_id"), ("tool", False))
        c = b.get("content")
        if isinstance(c, list):
            c = " ".join(x.get("text", "") if isinstance(x, dict) and x.get("type") == "text" else
                         f"[{x.get('type')}]" if isinstance(x, dict) else str(x) for x in c)
        c = str(c or "")
        if env:
            c = "(it touched a .env file: the result is not shown)"
        elif name.endswith("__desk"):
            c = _desk_reply(c)
        elif name == "Read" and not b.get("is_error"):
            c = f"{len(c.splitlines())} lines"
        elif name == "Glob" and not b.get("is_error"):
            c = f"{len([l for l in c.splitlines() if l.strip()])} files"
        return [("error" if b.get("is_error") else "result", f"{_tool_word(name)}: {trim(c, RESULT)}")]

    def _codex(self, d):
        if d.get("method") != "item/completed":
            return []
        it = (d.get("data") or {}).get("item") or {}
        t = it.get("type")
        if t == "agentMessage":
            text = it.get("text") or ""
            return self._said({"type": "text", "text": text}, {}) if text.strip() else []
        if t == "reasoning":
            words = " ".join(str(x.get("text", x) if isinstance(x, dict) else x)
                             for x in (it.get("summary") or []) + (it.get("content") or []))
            return [("thought", trim(words, WORDS) if words.strip() else "thought (the words are not kept)")]
        if t == "commandExecution":
            cmd = it.get("command") or ""
            if isinstance(cmd, list):
                cmd = " ".join(map(str, cmd))
            env = ".env" in cmd
            code = it.get("exitCode")
            out = "(it touched a .env file: the result is not shown)" if env else (it.get("aggregatedOutput") or "")
            return [("commit" if re.search(r"\bgit\s+commit\b", cmd) else "run", trim(cmd, ARGS)),
                    ("error" if code not in (0, None) else "result", f"exit {code}: {trim(out, RESULT)}")]
        if t == "fileChange":
            paths = [_short_path(c.get("path")) for c in it.get("changes") or [] if isinstance(c, dict)]
            return [("edit", "changed " + (", ".join(paths) or "files"))]
        if t == "mcpToolCall":
            args = it.get("arguments") or {}
            if isinstance(args, dict) and args.get("line"):
                return [self._desk(args["line"])]
            return [("tool", f"{it.get('tool') or 'tool'} {trim(json.dumps(args, ensure_ascii=False), ARGS)}")]
        if t == "webSearch":
            return [("web", f"search {trim(it.get('query'), ARGS)}")]
        return []


def _blocks(ev):
    m = ev.get("message")
    c = m.get("content") if isinstance(m, dict) else None
    return [b for b in c if isinstance(b, dict)] if isinstance(c, list) else []


def _short_path(p):
    """A path inside a worktree as the repository names it: research/..., not C:/Projects/Agora4/.worktrees/a1/research/..."""
    p = str(p or "").replace("\\", "/")
    m = re.search(r"/\.worktrees/[^/]+/(.*)$", p) or re.search(r"/Agora4/(.*)$", p)
    return m.group(1) if m else p


def _desk_reply(text):
    """The desk's answer without its echo of the command (> ...) and its 'since your last look' news (!! and the
    indented lines under it): what the command did."""
    out, news = [], False
    for l in text.splitlines():
        if l.startswith("!!"):
            news = True
            continue
        if news and l.startswith("   "):
            continue
        news = False
        if l.startswith("> ") or not l.strip():
            continue
        out.append(l.strip())
    return " ".join(out) or text


def _tool_word(name):
    return "desk" if name.endswith("__desk") else name


# ---- a feed: one transcript, followed ------------------------------------------------------------------------------
class Feed:
    def __init__(self, path):
        self.path = Path(path)
        self.offset = None
        self.rows = collections.deque(maxlen=CAP)
        self.n = 0
        self.reader = Reader()
        self.started = None              # when its current process started (the last start record)
        self.head = None                 # the head row as last written

    def read(self):
        """Take what the transcript gained since the last read -> how many rows were added."""
        try:
            size = self.path.stat().st_size
        except OSError:
            return 0
        if self.offset is None or size < self.offset:        # first look, or the file was replaced
            self.offset = max(0, size - SEED)
            skip = self.offset > 0
        else:
            skip = False
        if size == self.offset:
            return 0
        with self.path.open("rb") as f:
            f.seek(self.offset)
            data = f.read(size - self.offset)
        if skip:                                             # began mid-line: start at the next whole one
            cut = data.find(b"\n")
            data = data[cut + 1:] if cut >= 0 else b""
            self.offset += cut + 1 if cut >= 0 else 0
        end = data.rfind(b"\n")
        if end < 0:
            return 0
        self.offset += end + 1
        added = 0
        for raw in data[:end].splitlines():
            try:
                rec = json.loads(raw)
            except ValueError:
                continue
            if not isinstance(rec, dict):
                continue
            if rec.get("kind") == "start":
                self.started = rec.get("at")
            for kind, text in self.reader.rows(rec):
                self.n += 1
                at = rec.get("at")
                self.rows.append({"n": self.n, "at": time.strftime("%H:%M:%S", time.localtime(at)) if at else "",
                                  "kind": kind, "group": GROUPS.get(kind, "actions"), "text": redact(text)})
                added += 1
        return added


def head_row(who, card, title, state, started, last, events, first="", newest=""):
    """The feed's first row: who, the card it works on (a worker's commission, a resident's corner) and its title,
    what the house observes (working, waiting, resting, stopped), when its current process started and how long ago
    (since, for: empty when the start is older than the tail read), the newest line's n, how many lines are kept, and
    the times of the earliest and newest kept (from, newest)."""
    since = time.strftime("%H:%M", time.localtime(started)) if started else ""
    took = ""
    if started:
        m = int((time.time() - started) // 60)
        took = f"{m} min" if m < 60 else f"{m // 60} h {m % 60} min"
    return {"n": 0, "at": "", "kind": "head", "group": "head", "text": "", "who": who, "card": card or "",
            "title": redact(trim(title, 120)), "state": state or "", "since": since, "for": took,
            "last": last, "events": events, "from": first, "newest": newest}


# ---- the writer: the house's pass, or the command line -------------------------------------------------------------
FEED_LENS = "home-feed"      # a viewer note standing this lens on a thing (with=home-feed, viewing=<id>) watches it
GAP = 2.0                    # seconds between two writes of one feed: each write repaints every open painter


def _props(w, tid):
    node = w.nodes.get(tid) or {}
    return {**((w.subjects.get(node.get("subject")) or {}).get("props") or {}), **(node.get("props") or {})}


def agent_of(w, tid):
    """The agent a thing stands for: a card's worker (worker=), a corner's resident (actor=), or none."""
    p = _props(w, tid)
    return str(p.get("worker") or (p.get("actor") if p.get("role") == "resident" else "") or "").strip().lower() or None


class Feeds:
    """One per house: follows the transcripts of the agents someone watches, and writes their feeds. A feed is named
    by the thing it is watched through (a card, a corner): witnessed:feed-<id>, so a lens stood on that thing reads
    witnessed:feed-$item."""

    def __init__(self, world, state_dir):
        self.world, self.dir = world, Path(state_dir)
        self.feeds = {}                  # thing id -> Feed
        self.written = {}                # thing id -> when last written

    @staticmethod
    def watched(w):
        """The things watched now: what a note stands home-feed on (with=home-feed viewing=<id>, the home base's
        viewer), and any thing named by a watching=<id> prop (for another lens or tool). When the viewer moves on (×,
        Back, a pin, another lens), the thing is no longer watched and its feed goes."""
        out = set()
        for s in w.subjects.values():
            p = s.get("props") or {}
            if str(p.get("with") or "").strip() == FEED_LENS and str(p.get("viewing") or "").strip():
                out.add(str(p["viewing"]).strip())
            if str(p.get("watching") or "").strip():
                out.add(str(p["watching"]).strip())
        return {t for t in out if t in w.nodes}

    def where(self, w, tid, corners):
        """-> (agent, transcript folder or None, title) of the thing watched."""
        actor = agent_of(w, tid)
        node = w.nodes.get(tid) or {}
        title = node.get("title") or (w.subjects.get(node.get("subject")) or {}).get("title") or tid
        if not actor:
            return None, None, title
        for rid, c in corners.items():
            if str((c.get("props") or {}).get("actor") or "").lower() == actor:
                return actor, self.dir / rid, title
        return actor, (self.dir / actor if actor.startswith("worker-") else None), title

    def step(self, w, corners, states=None):
        """One pass. states: actor -> what the house observes of it now (working, waiting, resting, stopped); None
        when no house runs here (the command line)."""
        import witnessed
        want = self.watched(w)
        for tid in list(self.feeds):
            if tid not in want:
                del self.feeds[tid]
        for tid in list(self.written):
            if tid not in want:
                witnessed.clear(self.world, f"feed-{tid}")
                del self.written[tid]
        for tid in sorted(want):
            if witnessed.path(self.world, f"feed-{tid}") is None:
                continue                                     # not a name a source can carry
            actor, folder, title = self.where(w, tid, corners)
            feed = self.feeds.get(tid)
            if feed is not None and folder is not None and feed.path != folder / "transcript.jsonl":
                feed = None                                  # the card was handed to another worker
            if feed is None and folder is not None:
                feed = self.feeds[tid] = Feed(folder / "transcript.jsonl")
            if tid in self.written and time.time() - self.written[tid] < GAP:
                continue                                     # what came meanwhile waits for the next write
            added = feed.read() if feed else 0
            state = (states or {}).get(actor or "") or (
                "no agent on it" if not actor else
                "not kept by this house" if folder is None or not (folder / "transcript.jsonl").exists()
                else "stopped" if states is not None else "recorded")
            head = head_row(actor or "", tid, title, state, feed.started if feed else None,
                            feed.n if feed else 0, len(feed.rows) if feed else 0,
                            feed.rows[0]["at"] if feed and feed.rows else "",
                            feed.rows[-1]["at"] if feed and feed.rows else "")
            if added or head != (feed.head if feed else None) or tid not in self.written:
                witnessed.write(self.world, f"feed-{tid}", [head] + (list(feed.rows) if feed else []), by="house")
                self.written[tid] = time.time()
                if feed:
                    feed.head = head


def house_states(house, corners):
    """What a running house observes of each agent, by actor (house.beat's words)."""
    out = {}
    for rid, r in house.residents.items():
        actor = ((corners.get(rid) or {}).get("props") or {}).get("actor")
        if actor:
            out[str(actor).lower()] = "working" if r.busy else ("resting" if r.alive() else "stopped")
    for cid, wk in house.workshop.workers.items():
        out[wk.actor] = "working" if wk.busy else ("waiting" if wk.alive() else "stopped")
    return out


def main(argv):
    import export_docs
    import house as H
    if not argv or argv[0].startswith("-"):
        print(__doc__)
        return 2
    pattern = argv[0]           # a world, or a pattern of worlds: frontier-try-screen-* follows screen.py's copies
    until = time.time() + float(argv[argv.index("--for") + 1]) if "--for" in argv else None
    print(f"feeds: writing witnessed:feed-<actor> for {pattern}"
          + (f", reading transcripts in {argv[argv.index('--from') + 1]}" if "--from" in argv else "") + "; "
          + (f"stops in {argv[argv.index('--for') + 1]} s" if until else "Ctrl+C stops"), flush=True)
    worlds = {}                 # name -> [Feeds, mtime, desk]
    try:
        while until is None or time.time() < until:
            for p in sorted((HERE / "sessions").glob(f"{pattern}.pickle")):
                world = p.stem
                src = Path(argv[argv.index("--from") + 1]) if "--from" in argv else H.STATE / world
                f, mtime, desk = worlds.setdefault(world, [Feeds(world, src), None, None])
                try:
                    m = p.stat().st_mtime
                    if m != mtime:
                        desk = export_docs.load(world)
                        worlds[world][1:] = [m, desk]
                    w = desk.world
                except Exception as e:           # a copy being made or removed under us
                    print(f"feeds: {world}: {type(e).__name__}: {e}", flush=True)
                    continue
                corners = {sid: n for sid, n in w.nodes.items()
                           if n.get("type") == "surface" and (n.get("props") or {}).get("role") == "resident"}
                before = set(f.written)
                f.step(w, corners)
                if set(f.written) != before:
                    print(f"feeds: {world}: watched {', '.join(sorted(f.written)) or 'none'}", flush=True)
            if "--once" in argv:
                return 0
            time.sleep(0.5)
    except KeyboardInterrupt:
        return 0
    finally:
        import witnessed
        for world, (f, _, _) in worlds.items():
            for actor in f.written:
                witnessed.clear(world, f"feed-{actor}")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
