"""listeners: how a call reaches an agent the house does not run (Claude, Codex), and a listener that carries it.

    python listeners.py listen <world> --as claude [--door http://127.0.0.1:8794]    carry calls into this session
    python listeners.py stop <world> --as claude                                      ask a running listener to end
    python listeners.py status <world> --as claude                                    what its witnessed row says

(Not the reaches of verbs.py, a3806: those are lines the desk did not do.)

a5267 (15 Oct; Alex: Claude and Codex reachable like the residents). A resident has a corner, and the house runs it, so a
call wakes it and the receipt can say 'woken'. Claude and Codex are sessions the house does not run: Claude Code
sessions with Alex, and one Codex app chat. A corner would make the house try to run them, so their equivalent is a
listener: a program outside the desk that hears the house's knock records naming its agent and carries each one into
that agent's live session. It says it is there as witnessed rows (witnessed.py, a5052), one source per agent,

    witnessed:listener-<actor> one row: actor, carries (where it takes a call, in its own words), hears, delivered
                               (the line events it has handed on, oldest first, at most 200), error

which, as every witnessed source, has no rows once its writer's process has ended. So the house's knock record and the
speaker's receipt can say, truthfully: knocked (a listener is running and carries it; only it can confirm delivery),
not knocked (no listener, and nothing else carries it), or delivery unknown (something outside the desk may carry it
and says nothing here: the Codex event watcher before it publishes this row). `examine <line>` adds 'it says
delivered' while the listener that marked it still runs; what it marked is not kept in the world.

A listener writes its row only when something changes (it starts, it hands a line on, an error starts or ends), never
on a timer: a witnessed file that changes is a repaint on every open page (door.py).

`listen` is for a Claude Code session to run under its Monitor tool: each call is one printed line, which the session
receives as a notification. One listener per agent per world (an operating-system lock); a second says who holds it and
ends. It hears only knock records whose word for its agent begins 'knocked': a line said while no listener ran was
recorded 'not knocked', and is not replayed when one starts (it waits in For you, inbox:<actor>). Off switch: end the
process (stop the Monitor), or `listeners.py stop`.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import witnessed  # noqa: E402

KNOCKED = "knocked"
DOOR = "http://127.0.0.1:8794"
KEEP = 200          # delivered ids kept in the row


def source(actor):
    return "listener-" + str(actor).split("/")[0].strip().lower()


def listener(world, actor):
    """The running listener's row for `actor` (with its pid and age), or None when none runs."""
    doc = witnessed.read(world, source(actor))
    if not doc or not doc["rows"] or not isinstance(doc["rows"][0], dict):
        return None
    return dict(doc["rows"][0], pid=doc.get("pid"), age=doc.get("age"))


def word(world, actor, own=None):
    """What a call to `actor` came to, as the house records it and the receipt says it -> (state, words), state one of
    'knocked', 'not knocked', 'unknown'; or None for an agent with no listener and no word of its own (`own`, the
    agent's own word on how a line reaches them when nothing here carries it: rooms.REACH)."""
    row = listener(world, actor)
    if row:
        failing = f" (it is failing just now: {row['error']})" if row.get("error") else ""
        return KNOCKED, (f"knocked: their listener carries it to {row.get('carries') or 'their session'}{failing}; "
                         f"only it can confirm delivery")
    if own:
        return ("not knocked" if own.startswith("not knocked") else "unknown"), own
    return None


def delivered(world, actor, eid):
    """Has `actor`'s running listener said it handed on the line event `eid`? True, False, or None (no listener runs,
    so nothing here can say)."""
    row = listener(world, actor)
    if row is None:
        return None
    return eid in str(row.get("delivered", "")).split()


class Listen:
    """One agent's listener over one world. fetch(since) -> {"events", "total"}, as the door's /api/events answers;
    say(text) hands one call on (print, for a session's Monitor)."""

    def __init__(self, world, actor, fetch, say, carries, hears="the house's knock records"):
        self.world, self.actor = world, str(actor).lower()
        self.fetch, self.say = fetch, say
        self.row = {"actor": self.actor, "carries": carries, "hears": hears, "delivered": "", "error": ""}
        self.seen = {}           # event id -> event, for a knock's cause said before it
        r = fetch(10 ** 9)
        self.since = r["total"]
        for e in fetch(max(0, self.since - 300))["events"]:
            self.seen[e["id"]] = e
        self.publish()

    def publish(self):
        witnessed.write(self.world, source(self.actor), [self.row], by=f"listeners.py listen ({os.getpid()})")

    def call(self, k):
        """The one line a knock record becomes."""
        e = self.seen.get(k.get("cause")) or {}
        args = e.get("args") or {}
        words = str(args.get("append") or args.get("line") or args.get("text") or "").replace("\n", " ")
        words = words[:400] + ("..." if len(words) > 400 else "")
        ref = (k.get("args") or {}).get("line") or k.get("cause")
        by = str(e.get("by") or "someone").split("/")[0]
        return (f"[desk {self.world}] @{self.actor} called by {by} ({ref}, {k.get('cause')} on {e.get('target', '?')}): "
                f"{words or '(examine it for its words)'} -- examine {ref}, answer in the desk as {self.actor}")

    def step(self):
        """Read what is new; hand on each call. -> the calls handed on."""
        try:
            r = self.fetch(self.since)
        except Exception as x:      # the door down, a timeout: said in the row, tried again
            if self.row["error"] != str(x)[:200]:
                self.row["error"] = str(x)[:200]
                self.publish()
            raise
        out = []
        for e in r["events"]:
            self.seen[e["id"]] = e
            if e.get("verb") == "knock" and str((e.get("args") or {}).get(self.actor, "")).startswith(KNOCKED):
                line = self.call(e)
                self.say(line)
                out.append(e.get("cause"))
        if len(self.seen) > 2000:
            for eid in list(self.seen)[:1000]:
                del self.seen[eid]
        self.since += len(r["events"])
        if out or self.row["error"]:
            ids = (self.row["delivered"].split() + out)[-KEEP:]
            self.row.update(delivered=" ".join(ids), error="")
            self.publish()
        return out


def door_fetch(door, world, actor):
    def fetch(since):
        q = urllib.parse.urlencode({"session": world, "as": actor, "since": since})
        with urllib.request.urlopen(f"{door}/api/events?{q}", timeout=30) as resp:
            return json.load(resp)
    return fetch


def main(argv):
    if len(argv) < 2 or argv[0] not in ("listen", "stop", "status") or "--as" not in argv[:-1]:
        sys.exit(__doc__.split("\n\n")[0])
    what, world = argv[0], argv[1]
    actor = argv[argv.index("--as") + 1].lower()
    door = argv[argv.index("--door") + 1] if "--door" in argv[:-1] else DOOR
    p = witnessed.path(world, source(actor))
    if p is None:
        sys.exit(f"not a world and name: {world!r} {actor!r}")
    stop = p.with_suffix(".stop")
    if what == "stop":
        p.parent.mkdir(parents=True, exist_ok=True)
        stop.write_text(str(time.time()))
        print(f"asked {actor}'s listener in {world} to end (within a few seconds)")
        return
    if what == "status":
        print(json.dumps(listener(world, actor) or {"listening": False}))
        return
    import msvcrt
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.with_suffix(".lock").open("a+b") as lock:
        if lock.tell() == 0:
            lock.write(b"0")
            lock.flush()
        lock.seek(0)
        try:
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            row = listener(world, actor) or {}
            sys.exit(f"another listener carries {actor}'s calls in {world} (pid {row.get('pid', '?')}); this one ends")
        stop.unlink(missing_ok=True)     # starting it is asking for it: an old stop does not end a new listener

        def say(text):
            print(text, flush=True)

        fetch = door_fetch(door, world, actor)
        while True:
            try:
                ln = Listen(world, actor, fetch, say, carries="the Claude Code session that runs it (Monitor), as a "
                            "notification" if actor == "claude" else f"the session that runs it ({actor})")
                break
            except OSError as x:
                print(f"[listener] the door at {door} does not answer ({x}); trying again in 10 s", flush=True)
                time.sleep(10)
        print(f"[listener] listening for calls to {actor} in {world} from event {ln.since}; stop: python listeners.py stop "
              f"{world} --as {actor}", flush=True)
        failures = 0
        try:
            while not stop.exists():
                try:
                    ln.step()
                    failures = 0
                except Exception:
                    failures += 1
                time.sleep(2 if not failures else min(60, 2 ** min(failures, 6)))
        finally:
            witnessed.clear(world, source(actor))
            stop.unlink(missing_ok=True)


if __name__ == "__main__":
    main(sys.argv[1:])
