# health: room test (health.py runs every test_*.py with this line among its first ten)
"""test_agent_reach (a5267): @claude and @codex are knocked like the residents when a listener of theirs runs, and the
receipt and the knock record say truthfully what happened when none does.

    python test_agent_reach.py

A small world in memory (roomworld.py); the witnessed rows and the house's heartbeat go to a temporary folder.
Claude and Codex are sessions the house does not run. A listener (listeners.py; for Codex, research/codex-residents)
says it runs as the witnessed row listener-<name>. With none: Claude 'not knocked', Codex 'delivery unknown' (its old
watcher may run and says nothing here). With one: the receipt and the house's knock record say 'knocked: their
listener carries it to ...; only it can confirm delivery', the listener hears that record and hands the call on, and
`examine <line>` adds 'it says delivered'. A listener that has ended has no row, and the words go back. The knock
record is written as the house writes it: rooms.reached, then house.knock_word per name, then the house's `knocked`.
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"

import roomworld   # noqa: E402
import house       # noqa: E402
import listeners   # noqa: E402
import rooms       # noqa: E402
import scene       # noqa: E402
import witnessed   # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="agent-reach-"))
witnessed.ROOT = TMP
scene.HOUSE_STATE = TMP
WORLD = "agentreach"
fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok and "--show" not in sys.argv else f"\n     {str(detail)[:1800]}"))
    if not ok:
        fails.append(name)


D, R = roomworld.build(say=False)
D._session = WORLD
W = D.world
TALK = R.TALK[R.LOUNGE]
H = house.House.__new__(house.House)        # only what the knock record asks: the world's name, no residents running
H.world, H.residents = WORLD, {}


def say(me, line):
    W.me = me
    per = D._per
    if me not in per:
        per[me] = ({}, {W.root}, len(W.events))
    D.seen, D.open, D.last_event_seen = per[me]
    D._window = ""
    r = D.dispatch("desk", {"line": line, "whole": True, "reply": uuid.uuid4().hex})
    per[me] = (D.seen, D.open, D.last_event_seen)
    return r.get("text") or ("ERR " + (r.get("error") or ""))


def line(who, words):
    """-> (the line's event id, its m id, the receipt)"""
    say(who, f"look {TALK} :1")
    got = say(who, f"do append {TALK} line={json.dumps(words)}")
    e = next(x for x in reversed(W.events) if (x.get("args") or {}).get("append") is not None and x["by"] == who)
    return e["id"], (e.get("args") or {}).get("line_id"), got


def record(eid):
    """The house's knock record for the line `eid` made, as house.record_knocks writes it. -> {name: what happened}"""
    e = W.event_by_id(eid)
    how = rooms.reached(W, e)
    say("house", f"knocked {eid} " + json.dumps({a: H.knock_word(W, a, h) for a, h in how.items()}))
    k = rooms.knock_of(W, eid)
    return {a: v for a, v in (k.get("args") or {}).items() if a != "line"} if k else {}


def beat(age=0):
    (TMP / WORLD).mkdir(parents=True, exist_ok=True)
    (TMP / WORLD / "house.json").write_text(json.dumps({"world": WORLD, "beat": time.time() - age, "residents": {
        R.corner["pike"]: {"actor": "pike", "doing": "resting"}}}), encoding="utf-8")


def fetch(since):
    return {"events": [{k: v for k, v in e.items() if k != "undo"} for e in W.events[since:]], "total": len(W.events)}


beat()
for who in ("claude", "codex"):          # each has acted here before, so each is someone (rooms.someone)
    line(who, "here")
check("Claude and Codex are agents here", rooms.kind_of(W, "claude") == "agent" and rooms.kind_of(W, "codex") == "agent",
      (rooms.kind_of(W, "claude"), rooms.kind_of(W, "codex")))

# 1. no listener: Claude not knocked, Codex unknown, in the receipt and in the house's record
eid, mid, got = line("alex", "@claude @codex is either of you there")
check("no listener: the receipt says Claude is not knocked (no Claude session is listening)",
      "Claude: not knocked (no Claude session is listening)" in got, got)
check("no listener: the receipt says Codex's delivery is unknown, and why",
      "Codex: delivery unknown: a separate event watcher can notify its Codex chat" in got and "it says nothing here" in got, got)
k = record(eid)
check("the house records one knock for the line, with the same words for each",
      k.get("claude") == "not knocked (no Claude session is listening)" and str(k.get("codex", "")).startswith("delivery unknown"), k)

# 2. a Claude listener runs (in this process): the receipt and the record say knocked; it hands the call on
heard = []
L = listeners.Listen(WORLD, "claude", fetch, heard.append, carries="the Claude Code session that runs it (Monitor), as a notification")
row = listeners.listener(WORLD, "claude")
check("a running listener has a witnessed row listener-claude, alive while its process lives",
      row and row["actor"] == "claude" and row["pid"] == os.getpid(), row)
eid, mid, got = line("alex", "@claude the board needs you")
check("with a listener: the receipt says 'Claude: knocked: their listener carries it to ...; only it can confirm delivery'",
      "Claude: knocked: their listener carries it to the Claude Code session that runs it (Monitor), as a notification; "
      "only it can confirm delivery" in got, got)
check("the listener hears nothing before the house records the knock", L.step() == [] and not heard, heard)
k = record(eid)
check("the house's record says knocked too", str(k.get("claude", "")).startswith("knocked: their listener carries it"), k)
out = L.step()
check("the listener hears the record and hands the call on: one line, naming who called, the line's id and its words",
      out == [eid] and len(heard) == 1 and heard[0].startswith(f"[desk {WORLD}] @claude called by alex ({mid}, {eid} on ")
      and "the board needs you" in heard[0] and f"examine {mid}" in heard[0], heard)
check("and says so in its row", eid in listeners.listener(WORLD, "claude")["delivered"].split(), listeners.listener(WORLD, "claude"))
ex = say("sable", f"examine {mid}")
check("examine <line>: 'Claude: knocked: ...; only it can confirm delivery; it says delivered'",
      "only it can confirm delivery; it says delivered" in ex and "Claude: knocked: their listener" in ex, ex)
check("a second step hands nothing on again", L.step() == [] and len(heard) == 1, heard)
line("alex", "a plain line, calling no one")
check("a plain line is not carried", L.step() == [] and len(heard) == 1, heard)

# 3. the house not running: the line waits for its knock, and says so
beat(age=3600)
eid3, mid3, got = line("alex", "@claude while the house is down")
check("house not running: 'Claude: not knocked yet: the house is not running, so no knock is recorded'",
      "Claude: not knocked yet: the house is not running, so no knock is recorded; their listener carries it once one is" in got, got)
beat()
k = record(eid3)
L.step()
check("the house that follows records it, and the listener then carries it",
      str(k.get("claude", "")).startswith("knocked") and "while the house is down" in heard[-1], (k, heard[-1:]))

# 4. a listener that has ended has no row: back to 'not knocked'; its delivered marks are gone with it
subprocess.run([sys.executable, "-c", "import sys, pathlib, witnessed; witnessed.ROOT = pathlib.Path(sys.argv[2]); "
                "witnessed.write(sys.argv[1], 'listener-claude', [{'actor': 'claude', 'carries': 'x', 'delivered': ''}], "
                "by='gone')", WORLD, str(TMP)], cwd=HERE, check=True)
check("a listener whose process ended: no row", listeners.listener(WORLD, "claude") is None)
eid4, mid4, got = line("alex", "@claude after the listener ended")
check("and the receipt says not knocked again", "Claude: not knocked (no Claude session is listening)" in got, got)
ex = say("sable", f"examine {mid}")
check("examine of the earlier line keeps the record but no longer says delivered (nothing here can say)",
      "Claude: knocked:" in ex and "it says delivered" not in ex, ex)

# 5. a Codex listener's row (as visual_event_listener publishes it): knocked, carried to its chat; failing is said
witnessed.write(WORLD, "listener-codex", [{"actor": "codex", "carries": "its Codex app chat",
                                           "hears": "@codex in event text, and the house's knock records", "delivered": "",
                                           "error": ""}], by="test")
eid5, mid5, got = line("alex", "@codex a question for you")
check("with Codex's row: 'Codex: knocked: their listener carries it to its Codex app chat; only it can confirm delivery'",
      "Codex: knocked: their listener carries it to its Codex app chat; only it can confirm delivery" in got, got)
k = record(eid5)
check("and the house's record says knocked for codex", str(k.get("codex", "")).startswith("knocked"), k)
witnessed.write(WORLD, "listener-codex", [{"actor": "codex", "carries": "its Codex app chat", "delivered": eid5,
                                           "error": "Codex app bridge did not answer"}], by="test")
ex = say("sable", f"examine {mid5}")
check("its delivered mark shows on examine", "Codex: knocked: their listener carries it to its Codex app chat; only it can "
      "confirm delivery; it says delivered" in ex, ex)
eid6, mid6, got = line("alex", "@codex another")
check("a listener that is failing says so in the receipt", "(it is failing just now: Codex app bridge did not answer)" in got, got)

# 6. one listener per agent: a second `listeners.py listen` ends at once, naming the first
if os.name == "nt":
    import msvcrt
    witnessed.write(WORLD, "listener-claude", [{"actor": "claude", "carries": "x", "delivered": ""}], by="test")
    lock = witnessed.path(WORLD, "listener-claude").with_suffix(".lock")
    with lock.open("a+b") as fh:
        fh.write(b"0")
        fh.flush()
        fh.seek(0)
        msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
        try:
            listeners.main(["listen", WORLD, "--as", "claude", "--door", "http://127.0.0.1:9"])
            said = "it ran"
        except SystemExit as x:
            said = str(x.code)
        fh.seek(0)
        msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
    check("a second listener for claude ends, naming the one that holds it",
          f"another listener carries claude's calls in {WORLD} (pid {os.getpid()})" in said, said)

print(f"\n{len(fails)} failed" if fails else "\nall ok")
sys.exit(1 if fails else 0)
