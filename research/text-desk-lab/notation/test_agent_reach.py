"""test_agent_reach (a5267): @claude and @codex are knocked like the residents when a listener of theirs runs, and the
receipt and the knock record say truthfully what happened when none does.

    python test_agent_listeners.py [world]      default frontier-try; it CHANGES the world it is given, so give it a copy

Claude and Codex are sessions the house does not run. A listener (listeners.py; for Codex, research/codex-residents) says it
runs as the witnessed row listener-<name>. With none: Claude 'not knocked', Codex 'delivery unknown' (its old watcher may
run and says nothing here). With one: the receipt and the house's knock record say 'knocked: their listener carries
it to ...; only it can confirm delivery', the listener hears that record and hands the call on, and `examine <line>`
adds 'it says delivered'. A listener that has ended has no row, and the words go back.

It drives House.step with test_knock's stand-in residents (no model is called); a listener runs in this process.
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"
os.environ.setdefault("HOUSE_CLAUDE", "claude")
import house      # noqa: E402
import listeners  # noqa: E402
import witnessed  # noqa: E402

WORLD = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "frontier-try"
if not WORLD.endswith("-try") and "--yes" not in sys.argv:
    sys.exit(f"test_agent_reach changes the world it runs on; {WORLD} is not a -try copy (add --yes to insist)")
shutil.rmtree(house.STATE / WORLD, ignore_errors=True)


class Stand(house.Resident):
    def __init__(self, h, rid):
        super().__init__(h, rid)
        self.sent, self.up = [], True

    def start(self, model):
        self.busy, self.up = False, True

    def stop(self):
        self.up = False

    def alive(self):
        return self.up

    def turns_ended(self):
        return []

    def send(self, text, kind="news", carry=None):
        self.sent.append((kind, text))
        self.state["last_sent"] = house.now()


house.Resident = Stand
H = house.House(WORLD)
H.workshop.step = lambda *a, **k: None
w = H.load()
LOUNGE = next(a["id"] for a in w.nodes.values() if a["type"] == "appearance"
              and (w.subjects.get(a.get("subject")) or {}).get("title") == "Lounge talk")
fails = []


def check(name, ok, detail=""):
    ok = bool(ok) and "the desk process failed" not in str(detail)
    print(("ok   " if ok else "FAIL ") + name + ("" if ok and "--show" not in sys.argv else f"\n     {str(detail)[:1800]}"))
    if not ok:
        fails.append(name)


def say(who, line):
    got = H.act(who, f"do append {LOUNGE} line={house.json.dumps(line)}")
    e = next(x for x in reversed(H.load().events) if (x.get("args") or {}).get("append") is not None and x["by"] == who)
    return e["id"], (e.get("args") or {}).get("line_id"), got


def what(eid):
    k = [e for e in H.load().events if e["verb"] == "knock" and e.get("cause") == eid]
    return {a: v for a, v in k[0]["args"].items() if a != "line"} if len(k) == 1 else {"knock events": len(k)}


def fetch(since):
    evs = H.load().events
    return {"events": [{k: v for k, v in e.items() if k != "undo"} for e in evs[since:]], "total": len(evs)}


for a in ("claude", "codex"):
    witnessed.clear(WORLD, listeners.source(a))
H.step()                      # everyone arrives; house.json is written, so the house is running
H.step()

# 1. no listener: Claude not knocked, Codex unknown, in the receipt and in the house's record
eid, mid, got = say("alex", "@claude @codex is either of you there")
check("no listener: the receipt says Claude is not knocked (no Claude session is listening)",
      "Claude: not knocked (no Claude session is listening)" in got, got)
check("no listener: the receipt says Codex's delivery is unknown, and why",
      "Codex: delivery unknown: a separate event watcher can notify its Codex chat" in got and "it says nothing here" in got, got)
H.step()
k = what(eid)
check("the house records one knock for the line, with the same words for each",
      k.get("claude") == "not knocked (no Claude session is listening)" and str(k.get("codex", "")).startswith("delivery unknown"), k)

# 2. a Claude listener runs (in this process): the receipt and the record say knocked; it hands the call on
heard = []
L = listeners.Listen(WORLD, "claude", fetch, heard.append, carries="the Claude Code session that runs it (Monitor), as a notification")
row = listeners.listener(WORLD, "claude")
check("a running listener has a witnessed row listener-claude, alive while its process lives",
      row and row["actor"] == "claude" and row["pid"] == os.getpid(), row)
eid, mid, got = say("alex", "@claude the board needs you")
check("with a listener: the receipt says 'Claude: knocked: their listener carries it to ...; only it can confirm delivery'",
      re.search(r"Claude: knocked: their listener carries it to the Claude Code session that runs it \(Monitor\), as a "
                r"notification; only it can confirm delivery", got), got)
check("the listener hears nothing before the house records the knock", L.step() == [] and not heard, heard)
H.step()
check("the house's record says knocked too", str(what(eid).get("claude", "")).startswith("knocked: their listener carries it"),
      what(eid))
out = L.step()
check("the listener hears the record and hands the call on: one line, naming who called, the line's id and its words",
      out == [eid] and len(heard) == 1 and heard[0].startswith(f"[desk {WORLD}] @claude called by alex ({mid}, {eid} on ")
      and "the board needs you" in heard[0] and f"examine {mid}" in heard[0], heard)
check("and says so in its row", eid in listeners.listener(WORLD, "claude")["delivered"].split(), listeners.listener(WORLD, "claude"))
ex = H.act("sable", f"examine {mid}")
check("examine <line>: 'Claude: knocked: ...; only it can confirm delivery; it says delivered'",
      re.search(r"Claude: knocked: their listener carries it to [^;]+; only it can confirm delivery; it says delivered", ex), ex)
check("a second step hands nothing on again", L.step() == [] and len(heard) == 1, heard)
eid2, mid2, got = say("alex", "a plain line, calling no one")
H.step()
check("a plain line is not carried", L.step() == [] and len(heard) == 1, heard)

# 3. the house not running: the line waits for its knock, and says so
hj = house.STATE / WORLD / "house.json"
st = house.json.loads(hj.read_text(encoding="utf-8"))
beat = st["beat"]
st["beat"] = beat - 3600
hj.write_text(house.json.dumps(st), encoding="utf-8")
eid3, mid3, got = say("alex", "@claude while the house is down")
check("house not running: 'Claude: not knocked yet: the house is not running, so no knock is recorded'",
      "Claude: not knocked yet: the house is not running, so no knock is recorded; their listener carries it once one is" in got, got)
H.step()
L.step()
check("the house that follows records it, and the listener then carries it",
      str(what(eid3).get("claude", "")).startswith("knocked") and "while the house is down" in heard[-1], (what(eid3), heard[-1:]))

# 4. a listener that has ended has no row: back to 'not knocked'; its delivered marks are gone with it
p = subprocess.Popen([sys.executable, "-c", "import sys, witnessed; witnessed.write(sys.argv[1], 'listener-claude', "
                      "[{'actor': 'claude', 'carries': 'x', 'delivered': ''}], by='gone')", WORLD], cwd=HERE)
p.wait()
check("a listener whose process ended: no row", listeners.listener(WORLD, "claude") is None)
eid4, mid4, got = say("alex", "@claude after the listener ended")
check("and the receipt says not knocked again", "Claude: not knocked (no Claude session is listening)" in got, got)
H.step()
ex = H.act("sable", f"examine {mid}")
check("examine of the earlier line keeps the record but no longer says delivered (nothing here can say)",
      "Claude: knocked:" in ex and "it says delivered" not in ex, ex)

# 5. a Codex listener's row (as visual_event_listener publishes it): knocked, carried to its chat; failing is said
witnessed.write(WORLD, "listener-codex", [{"actor": "codex", "carries": "its Codex app chat",
                                        "hears": "@codex in event text, and the house's knock records", "delivered": "",
                                        "error": ""}], by="test")
eid5, mid5, got = say("alex", "@codex a question for you")
check("with Codex's row: 'Codex: knocked: their listener carries it to its Codex app chat; only it can confirm delivery'",
      "Codex: knocked: their listener carries it to its Codex app chat; only it can confirm delivery" in got, got)
H.step()
check("and the house's record says knocked for codex", str(what(eid5).get("codex", "")).startswith("knocked"), what(eid5))
witnessed.write(WORLD, "listener-codex", [{"actor": "codex", "carries": "its Codex app chat", "delivered": eid5,
                                        "error": "Codex app bridge did not answer"}], by="test")
ex = H.act("sable", f"examine {mid5}")
check("its delivered mark shows on examine", "Codex: knocked: their listener carries it to its Codex app chat; only it can "
      "confirm delivery; it says delivered" in ex, ex)
eid6, mid6, got = say("alex", "@codex another")
check("a listener that is failing says so in the receipt", "(it is failing just now: Codex app bridge did not answer)" in got, got)

# 6. one listener per agent: a second listeners.py listen ends at once, naming the first
witnessed.write(WORLD, "listener-claude", [{"actor": "claude", "carries": "x", "delivered": ""}], by="test")
lock = witnessed.path(WORLD, "listener-claude").with_suffix(".lock")
import msvcrt  # noqa: E402
with lock.open("a+b") as fh:
    if fh.tell() == 0:
        fh.write(b"0")
        fh.flush()
    fh.seek(0)
    msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
    r = subprocess.run([sys.executable, str(HERE / "listeners.py"), "listen", WORLD, "--as", "claude", "--door", "http://127.0.0.1:9"],
                       capture_output=True, text=True, timeout=30)
    fh.seek(0)
    msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
check("a second listener for claude ends, naming the one that holds it",
      r.returncode != 0 and f"another listener carries claude's calls in {WORLD} (pid {os.getpid()})" in r.stderr, r.stderr)

for a in ("claude", "codex"):
    witnessed.clear(WORLD, listeners.source(a))
print(f"\n{len(fails)} failed" if fails else "\nall ok")
sys.exit(1 if fails else 0)
