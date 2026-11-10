# health: room test (health.py runs every test_*.py with this line among its first ten)
"""test_shared: shared files stay safe for many hands (a5296, from a5261 points 3-5).

    python test_shared.py

A small world in memory (roomworld.py), a stand-in house, and a git repository of its own standing for the main
checkout; the workshop's own step() runs, with the worker's process and world copy stubbed (as test_worker_pool does).
  1. shared.check on that repository: a new, never-committed file the card names holds it; one with uncommitted edits is
     a note; a file a card says it is in (in_files=) is a note naming that card; words that only look like files
     (e.g., v1.2) and files the card does not name are nothing
  2. an asked card naming hud.py, new in the checkout, hears so in the same pass, even with every slot taken, and does
     not start; a second pass says nothing again; uncommitted=ok starts it; committing the file starts another
  3. a card naming a file with uncommitted edits starts, and its worker is told
  4. rooms tests are found by the line each carries, not a list: a new marked file is one, an unmarked one is not
  5. a row source is a file of its own: dropped in a folder, `rows <name>` reads it, its ARG is kept, an OPEN source
     prints the fields its rows bring; a file never takes over a source the table has
  6. two branches, one adding a rooms test and the other a row source (each also a new file of the other kind), merge
     with no conflict and touch neither health.py nor scene.py
  7. after a landing, every worker's -try copy is the live world again, taken under its own lock
"""
import atexit
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"
os.environ.setdefault("HOUSE_CLAUDE", "claude")

import roomworld   # noqa: E402
import house       # noqa: E402,F401
import workshop    # noqa: E402
import door        # noqa: E402
import shared      # noqa: E402
import health      # noqa: E402
import scene       # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:1500]}"))
    if not ok:
        fails.append(name)


D, R = roomworld.build(say=False)
W = D.world
B = R.BOARD
sys.path.insert(0, str(HERE.parents[1] / "desktop"))
import agora_tmp
TMP = Path(agora_tmp.directory("shared-"))
atexit.register(shutil.rmtree, TMP, ignore_errors=True)  # stubbed worker logs may remain open
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def g(*args, cwd):
    """git, through the Popen held at import (part 2 stubs the module's for the workers it starts)."""
    p = shared._POPEN(["git", *args], cwd=cwd, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    out = p.stdout.read()                     # and no thread: part 2 stubs those too
    p.wait()
    return SimpleNamespace(returncode=p.returncode, stdout=out, stderr="")


def say(me, *lines):
    W.me = me
    per = D._per
    if me not in per:
        per[me] = ({}, {W.root}, len(W.events))
    D.seen, D.open, D.last_event_seen = per[me]
    D._window = ""
    token, out = uuid.uuid4().hex, ""
    for line in lines:
        r = D.dispatch("desk", {"line": line, "whole": True, "reply": token})
        out = r.get("text") or ("ERR " + (r.get("error") or ""))
        if r.get("error"):
            break
    return out


# ---- the main checkout: a repository of its own ------------------------------------------------------------------
REPO = TMP / "live"
LAB = REPO / shared.NOTATION
LAB.mkdir(parents=True)
for args in (["init", "-q", "-b", "main"], ["config", "user.name", "t"], ["config", "user.email", "t@t"]):
    g(*args, cwd=REPO)
(LAB / "lens.js").write_text("// painter\n", encoding="utf-8")
(LAB / "scene.py").write_text("x = 1\n", encoding="utf-8")
g("add", "-A", cwd=REPO)
g("commit", "-q", "-m", "start", cwd=REPO)
(LAB / "hud.py").write_text("# made by hand, never committed\n", encoding="utf-8")          # new
(LAB / "lens.js").write_text("// painter, Codex is in it\n", encoding="utf-8")              # changed
(LAB / "sessions").mkdir()
(LAB / "sessions" / "w.pickle").write_text("a world", encoding="utf-8")                      # never source

# ---- 1. shared.check ---------------------------------------------------------------------------------------------
dirty = shared.uncommitted(REPO)
check("1. uncommitted: hud.py new, lens.js changed, the world in sessions/ not counted",
      dirty == {f"{shared.NOTATION}/hud.py": "new", f"{shared.NOTATION}/lens.js": "changed"}, dirty)
c = shared.check({"id": "s0", "title": "Spotify on the HUD", "text": "edit hud.py so the HUD shows the song"}, REPO)
check("1. a card naming hud.py by its base name is held, with the file named in what is said",
      c["hold"] == [f"{shared.NOTATION}/hud.py"] and "hud.py" in c["text"] and c["text"].startswith("held:")
      and "landing.py --files" in c["text"] and "uncommitted=ok" in c["text"], c)
c = shared.check({"id": "s0", "title": "Painter fix", "text": "in desk-shell/lens.js, e.g. the fold; v1.2 too"}, REPO)
check("1. a card naming lens.js by a longer path is a note, not a hold, and the worker is told",
      c["hold"] == [] and c["note"] == [f"{shared.NOTATION}/lens.js"] and c["text"].startswith("note:")
      and "lens.js (changed)" in c["worker"], c)
c = shared.check({"id": "s0", "title": "Something else", "text": "scene.py only; hudxpy and lens.jsx are not files here"}, REPO)
check("1. a committed file, and words that only look like the dirty ones, are nothing", c["key"] == "" and c["text"] == "", c)
claim_t = say("pike", f"look {B} :1", f'do create {B} kind=task title="Codex in the painter" owner=codex status=open in_files="scene.py, lens.js"')
claimer = re.findall(r"created (a\d+)", claim_t)[-1]
c = shared.check({"id": "s0", "title": "Rows", "text": "add a row source in scene.py"}, REPO, W)
check("1. a file a card says it is in (in_files) is a note naming that card and its owner",
      c["hold"] == [] and [x[1] for x in c["claimed"]] == [claimer] and claimer in c["text"] and "(codex)" in c["text"]
      and claimer in c["worker"], c)
say("pike", f"look {claimer} :1", f"do prop {claimer} in_files=none")
c = shared.check({"id": "s0", "title": "Rows", "text": "add a row source in scene.py, none of it hard"}, REPO, W)
check("1. in_files=none: out of every file again", c["claimed"] == [] and c["key"] == "", c)

# ---- 2 and 3. the house at ask time -----------------------------------------------------------------------------------


class House:
    world = "roomworld-inmemory"
    fake = None
    claude = "claude.exe"

    def __init__(self):
        self.dir = TMP / "house-state"
        self.dir.mkdir(exist_ok=True)

    def load(self):
        return W

    def act(self, who, line):
        from desk import split_batch
        out = say(who, *[p.strip() for p in split_batch(line)])
        if "ERR" in out:
            print("house refused:", line[:120], "->", out[-300:])
        return out


real_git = workshop.git
workshop.git = lambda *a, **k: SimpleNamespace(returncode=0, stdout="", stderr="")
workshop.TREES = TMP / "trees"
workshop.REPO = REPO
workshop.Workshop.real_tree = staticmethod(lambda tree: True)
door_copy = door.copy_locked
door.copy_locked = lambda a, b: None
popen = mock.patch.object(workshop.subprocess, "Popen").start()
popen.return_value.poll.return_value = None
popen.return_value.pid = 4242
mock.patch.object(workshop.threading, "Thread").start()
H = House()
WS = workshop.Workshop(H)
WS.land = lambda *a, **k: None


def card(title, text="", **props):
    extra = "".join(f" {k}={v}" for k, v in props.items())
    t = say("pike", f"look {B} :1", f'do create {B} kind=task title="{title}" owner=pike status=open{extra}')
    cid = re.findall(r"created (a\d+)", t)[-1]
    if text:
        say("pike", f"look {cid} :1", f'do append {cid} line="{text}"')
    say("pike", f"look {cid} :1", f"do prop {cid} commission=asked")
    return cid


def props(cid):
    return W.subjects[W.nodes[cid]["subject"]].get("props") or {}


def comments(cid):
    return [x["text"] for x in W.subjects[W.nodes[cid]["subject"]].get("comments") or []]


FULL = {"model": "claude-opus-5-5", "workers": "1", "worker_model": "", "worker_pool": ""}
busy = card("Something already running")
WS.step(W, FULL)
check("2. (the one slot is taken)", busy in WS.workers, sorted(WS.workers))
spot = card("Spotify controller", "make hud.py show the playing song")
WS.step(W, FULL)
said = comments(spot)
check("2. with every slot taken, the card naming hud.py hears at once that hud.py is uncommitted, and is held",
      len(said) == 1 and "hud.py" in said[0] and said[0].startswith("held:") and props(spot).get("commission") == "asked"
      and props(spot).get("uncommitted") == f"{shared.NOTATION}/hud.py:new", (said, props(spot)))
FREE = {**FULL, "workers": "4"}
WS.step(W, FREE)
check("2. with a slot free it still does not start, and nothing is said twice",
      spot not in WS.workers and len(comments(spot)) == 1, (sorted(WS.workers), comments(spot)))
say("pike", f"look {spot} :1", f"do prop {spot} uncommitted=ok")
WS.step(W, FREE)
check("2. uncommitted=ok (it only mentions the file): it starts", spot in WS.workers and props(spot).get("commission") == "working",
      props(spot))
later = card("Spotify, round two", "hud.py again")
WS.step(W, FREE)
held = later not in WS.workers
g("add", f"{shared.NOTATION}/hud.py", cwd=REPO)
g("commit", "-q", "-m", "hud.py landed by hand", cwd=REPO)
WS.step(W, FREE)
check("2. a second card is held until hud.py is committed, then starts on its own",
      held and later in WS.workers and props(later).get("commission") == "working", (held, props(later)))

popen.reset_mock()
paint = card("Fold fix in the painter", "lens.js folds wrongly")
WS.step(W, FREE)
sent = " ".join(str(c) for c in popen.return_value.stdin.write.call_args_list)
check("3. a card naming a changed file is a note, said once, and it starts",
      paint in WS.workers and len([c for c in comments(paint) if c.startswith("note:")]) == 1,
      comments(paint))
WS.step(W, FREE)
check("3. another pass does not repeat the shared-file note",
      len([c for c in comments(paint) if c.startswith("note:")]) == 1, comments(paint))
check("3. its worker's first message says what the house found", "lens.js (changed)" in sent, sent[-800:])

mock.patch.stopall()
workshop.git = real_git
door.copy_locked = door_copy

# ---- 4. rooms tests by their line ---------------------------------------------------------------------------------
lab = TMP / "lab"
lab.mkdir()
(lab / "test_marked.py").write_text('# health: room test (says so)\n"""a rooms test"""\n', encoding="utf-8")
(lab / "test_late.py").write_text('"""a docstring first"""\n# health: room test\n', encoding="utf-8")
(lab / "test_other.py").write_text('"""not a rooms test: # health: room test inside a string"""\n', encoding="utf-8")
(lab / "helper.py").write_text("# health: room test\n", encoding="utf-8")
check("4. rooms tests are the test_*.py files carrying the line, and no others",
      health.room_tests(lab) == ("test_late.py", "test_marked.py"), health.room_tests(lab))
check("4. this checkout's rooms tests include this test and the 39 there were in the list",
      "test_shared.py" in health.ROOM_TESTS and len(health.ROOM_TESTS) >= 40, len(health.ROOM_TESTS))

# ---- 5. a row source as a file --------------------------------------------------------------------------------------
src = TMP / "sources"
src.mkdir()
(src / "probe.py").write_text('USAGE = "probe[:<word>]"\nFIELDS = ("word", "n")\nARG = "optional"\n'
                              'def rows(desk, arg, session):\n    return [{"word": arg or "none", "n": 1}]\n', encoding="utf-8")
(src / "bring.py").write_text('USAGE = "bring:<name>"\nFIELDS = ("order",)\nARG = "needed"\nOPEN = True\n'
                              'def rows(desk, arg, session):\n    return [{"order": 1, "colour": arg}]\n', encoding="utf-8")
(src / "events.py").write_text('USAGE = "x"\nFIELDS = ()\ndef rows(desk, arg, session):\n    return [{"taken": 1}]\n',
                               encoding="utf-8")
scene._load_sources(src)
check("5. a source file is read: rows probe and probe:hello", scene.rows(D, "probe") == [{"word": "none", "n": 1}]
      and scene.rows(D, "probe:hello") == [{"word": "hello", "n": 1}], scene.rows(D, "probe"))
check("5. ARG needed: bring alone is no source, bring:red is", scene.rows(D, "bring") is None
      and scene.rows(D, "bring:red") == [{"order": 1, "colour": "red"}])
text = scene.rows_text(D, "bring:red")
check("5. an OPEN source prints the fields its rows brought after its own", "$order $colour" in text, text)
check("5. a file named like a source of the table does not take it over", scene.rows(D, "events") != [{"taken": 1}]
      and "events" not in scene.SOURCE_FILES)
check("5. the moved sources are files: windows, witnessed, reaches",
      {"windows", "witnessed", "reaches"} <= set(scene.SOURCE_FILES) and scene.SOURCE_FILES["witnessed"]["open"])
for name in ("probe", "bring"):
    scene.SOURCES.pop(name, None)
    scene.SOURCE_FILES.pop(name, None)

# ---- 6. two branches, each adding a test and a source: no conflict -----------------------------------------------------
m = TMP / "merge"
(m / "sources").mkdir(parents=True)
for args in (["init", "-q", "-b", "main"], ["config", "user.name", "t"], ["config", "user.email", "t@t"]):
    g(*args, cwd=m)
shutil.copyfile(HERE / "health.py", m / "health.py")
shutil.copyfile(HERE / "scene.py", m / "scene.py")
g("add", "-A", cwd=m)
g("commit", "-q", "-m", "base", cwd=m)
for b, test, source in (("one", "test_alpha.py", "alpha.py"), ("two", "test_beta.py", "beta.py")):
    g("checkout", "-q", "-b", b, "main", cwd=m)
    (m / test).write_text("# health: room test\nprint('all passed')\n", encoding="utf-8")
    (m / "sources").mkdir(exist_ok=True)          # git keeps no empty folder: each branch makes it
    (m / "sources" / source).write_text('USAGE = "x"\nFIELDS = ()\ndef rows(d, a, s):\n    return []\n', encoding="utf-8")
    g("add", "-A", cwd=m)
    g("commit", "-q", "-m", b, cwd=m)
g("checkout", "-q", "main", cwd=m)
r1, r2 = g("merge", "--no-ff", "-q", "-m", "land one", "one", cwd=m), g("merge", "--no-ff", "-q", "-m", "land two", "two", cwd=m)
touched = g("diff", "--name-only", "HEAD~2", "HEAD", cwd=m).stdout.split()
check("6. two branches adding a rooms test and a source each merge with no conflict, touching neither shared file",
      r1.returncode == 0 and r2.returncode == 0 and "health.py" not in touched and "scene.py" not in touched
      and health.room_tests(m) == ("test_alpha.py", "test_beta.py"), (r1.stdout + r1.stderr, r2.stdout + r2.stderr, touched))

# ---- 7. a worker's copy refreshed at a landing ------------------------------------------------------------------------
live = TMP / "w.pickle"
live.write_bytes(b"the world after the landing")
copies = []
for i in range(2):
    tree = TMP / "trees" / f"a{i}"
    (tree / workshop.NOTATION / "sessions").mkdir(parents=True, exist_ok=True)
    to = tree / workshop.NOTATION / "sessions" / f"{H.world}-try.pickle"
    to.write_bytes(b"a stale copy")
    copies.append(to)
WS.workers = {f"a{i}": SimpleNamespace(tree=TMP / "trees" / f"a{i}") for i in range(2)}
WS.workers["a9"] = SimpleNamespace(tree=TMP / "trees" / "a9")        # no copy: not given one here
why = WS.refresh_copies(live)
check("7. every worker's -try copy is the live world again; one with no copy is left alone",
      why == {} and all(p.read_bytes() == b"the world after the landing" for p in copies)
      and not (TMP / "trees" / "a9").exists(), (why, [p.read_bytes() for p in copies]))
check("7. no lock or half-made copy is left behind",
      not any(p.with_suffix(".lock").exists() or p.with_name(p.name + ".fresh").exists() for p in copies)
      and not live.with_suffix(".lock").exists())

print(f"{len(fails)} FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
