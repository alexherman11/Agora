"""usage: how full each agent's context window is, and how much of Alex's limit is used (a6265, Alex 17 Oct: 'more
detailed visualization into who is working ... per person task, status, context usage'; the limit had run out twice).

The house already keeps every stream event of each resident and worker in house-state/<world>/<dir>/transcript.jsonl
(house.Resident.log), and the numbers are in it, unread until now:

  Claude   every assistant event's message.usage: input_tokens + cache_creation_input_tokens + cache_read_input_tokens
           is what the model was given for that message, i.e. how full its context is, until an init names another
           session (a resumed one keeps it; Codex's adapter names its thread the same way) (an event with a
           parent_tool_use_id is a sub-agent's, with its own context, and is passed over). Each result's
           modelUsage[<model>].contextWindow is the window. Each rate_limit_event's rate_limit_info.unifiedWindows
           holds the ACCOUNT's limit: five_hour and seven_day utilization (0..1) and resetsAt (unix time).
  Codex    the app server's thread/tokenUsage/updated notification (a codex_event): tokenUsage.last.totalTokens is the
           context of the last turn, tokenUsage.modelContextWindow the window. It sends no limit.

What it writes, a witnessed source (witnessed.py), so the door tells every painter when it changes:

    witnessed:usage    one row kind=limit (Claude's account limit, newest reading of any transcript): five, week
                       (whole per cent), five_resets, week_resets (HH:MM, or a weekday and time), seen (when it was read);
                       a window whose reset time has passed is left empty, its use is unknown until the next reading.
                       Then one row kind=agent per resident and per live worker of the house: corner (a resident's
                       corner, a worker's card), actor, provider (claude, codex), model, doing (as the house observes:
                       working, waiting, resting), ctx (whole per cent), ctxpct ('62%'), tokens, window, ctxwords ('623k
                       of 1M tokens'), window_from (own:
                       this agent's own result said it; house: another agent of this house on the same model said it),
                       since (HH:MM today, else the weekday: a working agent's turn began then, else its last
                       record), quiet (minutes since its
                       last record, only while working and only from STUCK on: '15m'), held (HH:MM: held by a usage
                       limit until then).

A number with no source is left out of its row, never guessed: a Claude agent whose model has never ended a turn in
this house has no window, so no ctx; a Codex agent has no limit. A lens shows nothing for a field that is not there.

Each pass reads only what each transcript gained (a file offset; the first look reads its last SEED bytes), and the
source is written at most every GAP seconds and only when its rows changed, since every write repaints every painter.

    python usage.py <world or pattern> [--from <house-state dir of another world>] [--once] [--print] [--for <s>] [--gap <s>]

runs the same writer outside the house: a copy of a world has no house, so it reads another world's house.json and
transcripts, never writing there; a pattern (frontier-try-screen-*) follows screen.py's copies as they come. --print
prints the rows (and, with --once, writes nothing). Ctrl+C or the end of --for stops it, and its rows go with it.
"""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEED = 3_000_000             # bytes of a transcript's tail read on first look (tool results are big)
GAP = 10.0                   # seconds between two writes
STUCK = 10                   # minutes without a record before a working agent is said to be quiet
QUIET_STEPS = (10, 15, 20, 30, 45, 60, 90, 120, 180, 240)


def clock(t, now=None, day=False):
    """HH:MM today, else a weekday and HH:MM within a week (day: the weekday alone, for a narrow column), else the
    date."""
    if not t:
        return ""
    now = now or time.time()
    lt, ln = time.localtime(t), time.localtime(now)
    if lt[:3] == ln[:3]:
        return time.strftime("%H:%M", lt)
    if abs(t - now) < 6 * 86400:
        return time.strftime("%a" if day else "%a %H:%M", lt)
    return time.strftime("%d %b", lt).lstrip("0")


def short(n):
    """623419 -> '623k', 1000000 -> '1M', 258400 -> '258k'."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}".rstrip("0").rstrip(".") + "M"
    return f"{round(n / 1000)}k" if n >= 1000 else str(n)


def quiet_word(minutes):
    """Minutes as a coarse word, so the row (and every painter) changes only now and then: 15m, 1h30m."""
    step = max([s for s in QUIET_STEPS if s <= minutes] or [0])
    if step < STUCK:
        return ""
    if minutes >= QUIET_STEPS[-1]:
        step = int(minutes // 60) * 60
    return f"{step}m" if step < 60 else f"{step // 60}h" + (f"{step % 60}m" if step % 60 else "")


class Track:
    """One transcript, followed: what its newest records say about context and limit."""

    def __init__(self, path):
        self.path = Path(path)
        self.offset = None
        self.provider = self.model = self.session = None
        self.ctx = self.window = None            # tokens in the context now, the window (own result's, or Codex's)
        self.ctx_session = None                  # the Claude session the ctx reading belongs to
        self.last_at = self.started = self.sent_at = None
        self.limit = None                        # newest rate_limit_event of this transcript: (at, info)

    def read(self, windows):
        """Take what the transcript gained. windows: model -> context window, learned from every result seen."""
        try:
            size = self.path.stat().st_size
        except OSError:
            return
        skip = False
        if self.offset is None or size < self.offset:
            self.offset, skip = max(0, size - SEED), size > SEED
        if size == self.offset:
            return
        with self.path.open("rb") as f:
            f.seek(self.offset)
            data = f.read(size - self.offset)
        if skip:
            cut = data.find(b"\n")
            data = data[cut + 1:] if cut >= 0 else b""
            self.offset += cut + 1 if cut >= 0 else 0
        end = data.rfind(b"\n")
        if end < 0:
            return
        self.offset += end + 1
        for raw in data[:end].splitlines():
            try:
                rec = json.loads(raw)
            except ValueError:
                continue
            if isinstance(rec, dict):
                self.take(rec, windows)

    def take(self, rec, windows):
        at, kind = rec.get("at"), rec.get("kind")
        if at:
            self.last_at = at
        if kind == "start":
            self.started = at
        elif kind == "sent":
            self.sent_at = at
        if kind != "event" or not isinstance(rec.get("data"), dict):
            return
        ev = rec["data"]
        t = ev.get("type")
        if t == "system" and ev.get("subtype") == "init":
            self.model = ev.get("model") or self.model
            sid = ev.get("session_id")
            if sid and sid != self.session:
                self.session = sid
                if self.ctx is not None and self.ctx_session != sid:
                    self.ctx = None               # another conversation (or one the tail began inside): unknown
        elif t == "assistant" and not ev.get("parent_tool_use_id"):
            msg = ev.get("message") or {}
            u = msg.get("usage") or {}
            if "input_tokens" in u:
                self.provider = "claude"
                self.model = msg.get("model") or self.model
                self.ctx = int(u.get("input_tokens") or 0) + int(u.get("cache_creation_input_tokens") or 0) \
                    + int(u.get("cache_read_input_tokens") or 0)
                self.ctx_session = self.session
        elif t == "result":
            for name, m in (ev.get("modelUsage") or {}).items():
                if isinstance(m, dict) and m.get("contextWindow"):
                    windows[name] = int(m["contextWindow"])
                    if name == self.model:
                        self.window = int(m["contextWindow"])
        elif t == "rate_limit_event":
            info = ev.get("rate_limit_info") or {}
            if info.get("unifiedWindows"):
                self.limit = (at, info)
        elif t == "codex_event" and ev.get("method") == "thread/tokenUsage/updated":
            tu = (ev.get("data") or {}).get("tokenUsage") or {}
            last = tu.get("last") or {}
            self.provider = "codex"
            if last.get("totalTokens") is not None:
                self.ctx = int(last["totalTokens"])
                # the adapter's init names the thread as its session_id: a resumed thread keeps this reading,
                # another thread drops it (the init rule above)
                self.ctx_session = (ev.get("data") or {}).get("threadId") or self.session
            if tu.get("modelContextWindow"):
                self.window = int(tu["modelContextWindow"])


def limit_row(reading, now=None):
    """The kind=limit row from the newest (at, rate_limit_info), or one with no numbers."""
    now = now or time.time()
    row = {"kind": "limit", "provider": "claude"}
    if not reading:
        return row
    at, info = reading
    row["seen"] = clock(at, now)
    for name, key in (("five_hour", "five"), ("seven_day", "week")):
        w = (info.get("unifiedWindows") or {}).get(name) or {}
        util, resets = w.get("utilization"), w.get("resetsAt")
        if util is None or not resets or float(resets) <= now:
            continue                              # unread, or the window has turned over since: unknown, not 0
        row[key] = int(round(float(util) * 100))
        row[key + "_resets"] = clock(float(resets), now)
    return row


class Usage:
    """One per house (or per copy, on the command line): follows the transcripts of the agents house.json names."""

    def __init__(self, world, state_dir):
        self.world, self.dir = world, Path(state_dir)
        self.tracks = {}                          # transcript folder name -> Track
        self.windows = {}                         # model -> context window, from every result seen
        self.written = 0.0
        self.seeded = False

    def seed(self):
        """Learn windows from the newest transcripts of the house (agents that have ended a turn), once."""
        self.seeded = True
        try:
            recent = sorted(self.dir.glob("*/transcript.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)[:12]
        except OSError:
            return
        for p in recent:
            if p.parent.name not in self.tracks:
                Track(p).read(self.windows)

    def agents(self, st):
        """(corner, actor, folder, house's word, its record) for each resident and live worker in house.json."""
        out = []
        for cid, r in sorted((st.get("residents") or {}).items()):
            if r.get("actor") and r.get("doing") != "stopped":
                out.append((cid, r["actor"], cid, r.get("doing") or "", r))
        for cid, wk in sorted((st.get("workers") or {}).items()):
            if wk.get("actor") and wk.get("doing") != "stopped":
                out.append((cid, wk["actor"], wk["actor"], wk.get("doing") or "", wk))
        return out

    def rows(self, now=None):
        now = now or time.time()
        try:
            st = json.loads((self.dir / "house.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        if not self.seeded:
            self.seed()
        agents = self.agents(st)
        live = {folder for _, _, folder, _, _ in agents}
        for name in list(self.tracks):
            if name not in live:
                del self.tracks[name]
        out = []
        for corner, actor, folder, doing, rec in agents:
            tr = self.tracks.get(folder)
            if tr is None:
                tr = self.tracks[folder] = Track(self.dir / folder / "transcript.jsonl")
            tr.read(self.windows)
            row = {"kind": "agent", "corner": corner, "actor": actor, "doing": doing}
            if tr.provider:
                row["provider"] = tr.provider
            if tr.model:
                row["model"] = tr.model
            window, whence = tr.window, "own"
            if not window and tr.provider == "claude" and tr.model in self.windows:
                window, whence = self.windows[tr.model], "house"
            if tr.ctx is not None and window:
                pct = int(round(100 * tr.ctx / window))
                row.update(ctx=pct, ctxpct=f"{pct}%", tokens=tr.ctx, window=window, window_from=whence,
                           ctxwords=f"{short(tr.ctx)} of {short(window)} tokens")
            began = tr.sent_at if doing == "working" and tr.sent_at else tr.last_at
            if began:
                row["since"] = clock(began, now, day=True)
            if doing == "working" and tr.last_at:
                q = quiet_word((now - tr.last_at) / 60)
                if q:
                    row["quiet"] = q
            retry = rec.get("retry_at") or self.retry_of(folder)
            if retry and float(retry) > now:
                row["held"] = clock(float(retry), now)
            out.append(row)
        newest = max((tr.limit for tr in self.tracks.values() if tr.limit), key=lambda r: r[0] or 0, default=None)
        return [limit_row(newest, now)] + out

    def retry_of(self, folder):
        """A worker's retry_at is in its own state.json, not house.json."""
        try:
            return json.loads((self.dir / folder / "state.json").read_text(encoding="utf-8")).get("retry_at")
        except (OSError, ValueError, AttributeError):
            return None

    def step(self, force=False):
        """One pass: read, and write witnessed:usage when GAP has passed and the rows changed."""
        import witnessed
        if not force and time.time() - self.written < GAP:
            return None
        rows = self.rows()
        if rows is None:
            return None
        self.written = time.time()
        witnessed.write(self.world, "usage", rows, by="house", changed_only=True)
        return rows


def main(argv):
    if not argv or argv[0].startswith("-"):
        print(__doc__)
        return 2
    import witnessed
    pattern = argv[0]           # a world, or a pattern of worlds: frontier-try-screen-* follows screen.py's copies
    until = time.time() + float(argv[argv.index("--for") + 1]) if "--for" in argv else None
    gap = float(argv[argv.index("--gap") + 1]) if "--gap" in argv else GAP

    def src(world):
        return Path(argv[argv.index("--from") + 1]) if "--from" in argv else HERE / "house-state" / world

    if "--once" in argv and "--print" in argv:
        rows = Usage(pattern, src(pattern)).rows()
        print(json.dumps(rows, indent=1) if rows is not None else f"usage: no house.json in {src(pattern)}")
        return 0
    worlds = {}
    try:
        while True:
            names = {p.stem for p in (HERE / "sessions").glob(f"{pattern}.pickle")} if any(c in pattern for c in "*?[") \
                else {pattern}
            for world in sorted(names):
                if world not in worlds:
                    worlds[world] = Usage(world, src(world))
                    print(f"usage: writing witnessed:usage for {world} from {src(world)}", flush=True)
                rows = worlds[world].step(force=True)
                if "--print" in argv:
                    print(json.dumps(rows), flush=True)
            if "--once" in argv or (until is not None and time.time() >= until):
                return 0
            time.sleep(gap)
    except KeyboardInterrupt:
        return 0
    finally:
        if "--once" not in argv:
            for world in worlds:
                witnessed.clear(world, "usage")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
