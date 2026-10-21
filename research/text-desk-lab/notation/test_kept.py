# health: room test (health.py runs every test_*.py with this line among its first ten)
"""test_kept (7 Oct 2026): the copies undo keeps, out of the world file (kept.py).

    python test_kept.py

Saves the rooms world as sessions/roomworld-kept-<pid>-try.pickle after a long chat was written in it, and asks:

  - `kept.py begin` moves the copies beside the file, the file shrinks, and nothing the world says has changed;
  - an event made before that is still undone the verb's own way (its copy is read from the archive), and the readers
    that ask what an edit changed still get their answer;
  - from then on the file does not grow by a chat for every line said in it;
  - a fork reads its base's copies and keeps its own; `kept.py restore` puts every copy back.

The world, its lock, its archive and its fork are removed at the end.
"""
import os
import pickle
import subprocess
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"
os.environ["DESK_LOG"] = "off"
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:      # noqa: BLE001
    pass

fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:2000]}"))
    if not ok:
        fails.append(name)


import explore     # noqa: E402
import kept        # noqa: E402
import roomworld   # noqa: E402
import store       # noqa: E402
import world as world_mod   # noqa: E402

WORLD = f"roomworld-kept-{os.getpid()}-try"
SESS = HERE / "sessions"
SAVED = SESS / f"{WORLD}.pickle"
ENV = dict(os.environ, DESKD="off", DESK_LOG="off", PYTHONIOENCODING="utf-8")

D, R = roomworld.build()
D._session = WORLD
W = D.world
TALK, CARD = R.TALK[R.LOUNGE], R.CARDS[0]


def say(me, line):
    W.me = me
    D.seen, D.open, D.last_event_seen = (getattr(D, "_per", None) or {}).get(me) or ({}, {W.root}, len(W.events))
    r = D.dispatch("desk", {"line": line, "whole": True, "reply": uuid.uuid4().hex})
    D._per = dict(getattr(D, "_per", None) or {}, **{me: (D.seen, D.open, D.last_event_seen)})
    assert not r.get("error"), (line, r.get("error"))
    return r.get("text") or ""


for i in range(200):
    say(("sable", "pike")[i % 2], f'do append {TALK} line="line {i}: ' + "a long evening of talk in the lounge, " * 3 + '"')
say("alex", f"look {CARD} :1")
say("alex", f"do prop {CARD} status=before")
PROP = W.events[-1]["id"]
say("alex", f"read {R.NOTE}")
say("alex", f'do rewrite {R.NOTE} text="Dear all, a short letter.\\n@pike: a line for you"')
EDIT = W.events[-1]["id"]
W.me = "jeff"
explore.save_desk(SAVED, D)
size0 = SAVED.stat().st_size
flat0 = store.flatten(W)


def cli(who, *lines, name=WORLD):
    r = subprocess.run([sys.executable, "explore.py", name, "--as", who, "--whole"], input="\n".join(lines) + "\n", cwd=HERE, env=ENV,
                       capture_output=True, text=True, encoding="utf-8")
    return r.stdout + r.stderr


def tool(*args):
    r = subprocess.run([sys.executable, "kept.py", *args], cwd=HERE, env=ENV, capture_output=True, text=True, encoding="utf-8")
    return r.returncode, r.stdout + r.stderr


def load(name=WORLD):
    return pickle.loads((SESS / f"{name}.pickle").read_bytes()).world


try:
    check("a world without an archive keeps its copies on its events, as ever", not kept.on(SAVED) and "restore_subject" in W.event_by_id(PROP)["undo"])
    code, out = tool("begin", WORLD)
    size1 = SAVED.stat().st_size
    w = load()
    check(f"kept.py begin moves them beside the file: {size0 // 1000} KB becomes {size1 // 1000} KB (under a quarter)",
          code == 0 and size1 * 4 < size0 and kept.on(SAVED) and (SESS / f"{WORLD}.pickle.before-kept").exists(), out)
    check("   what the world says has not changed by a single fact", not store.diff(flat0, store.flatten(w)), store.diff(flat0, store.flatten(w))[:5])
    e = w.event_by_id(PROP)
    check("   an event now says where its copy is, and of which subject, in place of the copy",
          "restore_subject" not in e["undo"] and e["undo"].get("kept") == WORLD and e["undo"].get("kept_id") == w.nodes[CARD]["subject"], e["undo"])
    check("   and the copy is read back whole", (kept.copy_of(e) or {}).get("id") == w.nodes[CARD]["subject"]
          and "status" not in (kept.copy_of(e) or {}).get("props", {}), kept.copy_of(e))
    code, out = tool("check", WORLD)
    check("   kept.py check: every event finds its copy", code == 0 and "0 not found" in out, out)
    calls, _mentions = world_mod.written(w.event_by_id(EDIT))
    check("a reader that asks what an edit added still gets it (the line it added calls pike)", calls == ["pike"], calls)

    out = cli("alex", f"look {CARD} :1", f"undo {PROP}")
    w = load()
    check("an event made before the move is undone the verb's own way, from the archive",
          "ok" in out and "status" not in w.subjects[w.nodes[CARD]["subject"]]["props"], out[-400:])

    before = SAVED.stat().st_size
    for k in range(5):
        cli("juniper", *[f'do append {TALK} line="after the move, line {k}-{j}: ' + "more talk, " * 6 + '"' for j in range(8)])
    grew = (SAVED.stat().st_size - before) / 40
    w = load()
    check(f"forty more lines in a chat of 240: the file grows by {grew:.0f} bytes a line, not by a chat a line (it grew {int((size0 - 0) / 200)} a line before)",
          grew < 1500 and not [e_ for e_ in w.events if "restore_subject" in (e_.get("undo") or {})], grew)
    last = w.events[-1]
    out = cli("juniper", f"undo {last['id']}")
    check("   a line said after the move is undone too", "ok" in out and "after the move, line 4-7" not in load().subjects[w.nodes[TALK]["subject"]]["text"], out[-300:])

    out = cli("alex", "worktree fork sketch")
    fork = f"{WORLD}@sketch"
    check("a fork gets an archive of its own", kept.on(SESS / f"{fork}.pickle"), out[-200:])
    cli("alex", f"look {CARD} :1", f"do prop {CARD} status=in-the-fork", name=fork)
    wf = load(fork)
    fe = wf.events[-1]
    check("   what it makes is kept in its own, what it had from before is still read from its base's",
          fe["undo"].get("kept") == fork and kept.copy_of(fe) is not None and kept.copy_of(wf.event_by_id(EDIT)) is not None, fe["undo"])
    out = cli("alex", f"read {R.NOTE}", f"undo {EDIT}", name=fork)
    check("   and it can undo an event from before the fork", "ok" in out and "@pike" not in load(fork).subjects[wf.nodes[R.NOTE]["subject"]]["text"], out[-300:])

    code, out = tool("restore", WORLD)
    w = load()
    check("kept.py restore puts every copy back on its event (the way back)",
          code == 0 and not [e_ for e_ in w.events if (e_.get("undo") or {}).get("kept")] and not kept.on(SAVED)
          and "restore_subject" in w.event_by_id(EDIT)["undo"], out)
finally:
    for p in list(SESS.glob(f"{WORLD}*")):
        try:
            p.unlink()
        except OSError:
            pass
    import shutil
    shutil.rmtree(HERE / "house-state" / WORLD, ignore_errors=True)

print()
print("FAILED: " + "; ".join(fails) if fails else "all passed")
sys.exit(1 if fails else 0)
