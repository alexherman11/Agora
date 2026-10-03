"""test_visit (a2844): `visit <commission>` and `home` are the door's words, and a visit never reaches home's store.

    python test_visit.py

Builds the rooms world (roomworld.py) as home's world, and two pretend commissions' worktrees: small git repositories
of their own (in a temporary folder) holding this checkout's lab files. a9001's rooms.py says something home's does
not (the one thing it changes); a9002's deskd.py exits at once. A real door.py is started on a free port with its own
state folder and --trees pointing at them. Then, through the door, as the house sends a resident's lines:
  (i)   pike visits a9001, uses what it changes, makes a note there, and comes home: home's world has no new event,
        its file is not written, and while away the door's record (which scene.py and rooms.py read) says where pike
        is; `home` says what pike leaves behind;
  (iii) a9002 refuses entry and quotes its error; a9001's deskd, killed, brings its visitors home: each one's next
        line is refused, told, and run nowhere;
  (iv)  sable joins pike in a9001 and finds pike's note there; home never has it. Once the worker has committed, the
        door does not pick for a newcomer (Juniper c3167): it names who is in which commit, `with=<name>` joins them
        and `new` takes the newest;
  (v)   a commit in a9001's worktree mid-visit leaves the visit as it was and is said once; `visit a9001 new` pins the
        new commit and names it; sable, who did not visit again, is still on the old one;
  and: a door word beside another command, a line for another world while away, and `visit` from a page are refused;
  a door started again brings pike home, told; explore.py refuses an away actor's line when no door answered.
Everything is removed after. No browser.
"""
import json
import os
import pickle
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"

import roomworld   # noqa: E402
import explore     # noqa: E402
import rooms       # noqa: E402
import scene       # noqa: E402

WORLD = f"roomworld-visit-{os.getpid()}-try"
NOTATION = HERE.relative_to(HERE.parents[2]).as_posix()
SAYS = "go <room> takes you there, by id or a word of its title"
fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:1500]}"))
    if not ok:
        fails.append(name)


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def get(url, timeout=60):
    with urllib.request.urlopen(url, timeout=timeout) as f:
        return json.loads(f.read())


def git(tree, *args):
    r = subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid", "-c", "core.autocrlf=false",
                        *args], cwd=tree, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"test_visit: git {' '.join(args)} failed in {tree}: {r.stderr[-300:]}")
    return r.stdout.strip()


def worktree(trees, cid, change):
    """A pretend commission's worktree: a git repository holding this checkout's lab files, changed by `change`."""
    tree = trees / cid
    lab = tree / NOTATION
    lab.mkdir(parents=True)
    for p in HERE.iterdir():
        if p.is_file() and p.suffix in (".py", ".json", ".md", ".txt"):
            shutil.copyfile(p, lab / p.name)
    change(lab)
    git(tree, "init", "-q")
    git(tree, "add", "-A")
    git(tree, "commit", "-q", "-m", f"{cid}: its first commit")
    return tree


def rewrite(path, old, new):
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"test_visit: {path.name} no longer holds {old!r}")
    path.write_text(text.replace(old, new), encoding="utf-8", newline="")


t0 = time.time()
D, R = roomworld.build()
D._session = WORLD
saved = HERE / "sessions" / f"{WORLD}.pickle"
saved.write_bytes(pickle.dumps(D))
tmp = Path(tempfile.mkdtemp(prefix="test-visit-"))
state, trees = tmp / "state", tmp / "trees"
port = free_port()
base = f"http://127.0.0.1:{port}"
door = None


def say(who, line, session=WORLD, headers=None, whole=True):
    """One line through the door, as house.deskd_do sends a resident's > line. -> what a receipt would print."""
    body = json.dumps({"session": session, "as": who, "line": line, "whole": whole}).encode()
    req = urllib.request.Request(base + "/api/do", body, {"Content-Type": "application/json", **(headers or {})})
    with urllib.request.urlopen(req, timeout=300) as f:
        r = json.loads(f.read())
    return r.get("text") or ("ERR " + str(r.get("error")))


def total():
    return get(f"{base}/api/events?session={WORLD}&since=999999999")["total"]


def start_door():
    p = subprocess.Popen([sys.executable, "door.py", str(port), "--no-git", "--world", WORLD, "--state", str(state),
                          "--trees", str(trees)], cwd=HERE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t = time.time() + 60
    while time.time() < t:
        try:
            if get(base + "/door/status", 3).get("up"):
                return p
        except OSError:
            time.sleep(0.2)
    raise SystemExit("test_visit: the door did not answer within 60 s")


try:
    a1 = worktree(trees, "a9001", lambda lab: rewrite(lab / "rooms.py", SAYS, SAYS + " (VERSION ONE)"))
    worktree(trees, "a9002", lambda lab: (lab / "deskd.py").write_text("raise SystemExit('broken on purpose')\n", encoding="utf-8"))
    sha1 = git(a1, "rev-parse", "HEAD")
    one = f"a9001@{sha1[:7]}"
    door = start_door()
    n0 = total()

    # ---- (i) go, use the one thing it changes, home ------------------------------------------------------------
    t = say("pike", "go")
    check("at home `go` alone is the desk's own word, and says what home's code says", SAYS in t and "VERSION" not in t and "~ in" not in t, t)
    t = say("pike", "visit")
    check("`visit` alone says which commissions can be visited, and who is away", "a9001, a9002" in t and "Away now: nobody" in t, t)
    t = say("pike", "visit a7777")
    check("a commission with no living worktree is refused, naming those that have one",
          t.startswith("ERR [door] no commission a7777") and "a9001, a9002" in t and get(base + "/door/status")["away"] == {}, t)
    t1 = time.time()
    t = say("pike", "visit a9001")
    took = time.time() - t1
    check(f"visit a9001: the door's one line names the commission, the commit, the world and its events, and full rights ({took:.1f} s)",
          t.startswith(f"[door] you are in a9001 at {sha1[:7]}") and f"a copy of {WORLD} made now, from e" in t and f"({n0} events)" in t
          and "full rights" in t and "`home` brings you back" in t and "\n" not in t, t)
    st = get(base + "/door/status")
    check("the door says who is away, and in which version", st.get("away") == {"pike": one}, st.get("away"))
    scene.HOUSE_STATE = state                     # the door's record, where home's desk reads it
    check("home's desk shows pike away (rooms.presences, read from the door's record; no event)",
          rooms.presences(D)("pike") == f"away in {one}" and rooms.presences(D)("sable") != f"away in {one}",
          rooms.presences(D)("pike"))
    corner = rooms.corner_of(D.world, "pike")
    (state / WORLD).mkdir()
    (state / WORLD / "house.json").write_text(json.dumps({"world": WORLD, "beat": time.time(), "residents": {
        corner: {"actor": "pike", "doing": "resting"}}}), encoding="utf-8")
    row = scene.house_rows(D, corner)
    check("the house's row for pike (what the Desktop paints) says away, where the room was", row and row[0]["room"] == f"away in {one}", row)
    written = saved.stat().st_mtime_ns
    t = say("pike", "go")
    check("in the version, the thing it changes is there, and the receipt is labelled", "(VERSION ONE)" in t and t.endswith(f"~ in {one}, not home"), t)
    t = say("pike", f"look {R.SHELF} :1")
    t = say("pike", f'do create {R.SHELF} kind=note title="made while away"')
    check("an act in the version is done there, labelled", "created" in t and f"~ in {one}, not home" in t, t)
    check("home's world file was not written by any of it (reading writes, but not here)", saved.stat().st_mtime_ns == written)
    t = say("pike", "do nonsense-verb x")
    check("a refusal in the version still begins as a refusal, and is labelled", t.startswith(("ERR", "MISS")) and one in t, t)
    t = say("pike", "look", session="roomworld-other")
    check("away, a line for another world is refused: `home` first", t.startswith("ERR [door]") and "`home` first" in t, t)
    t = say("pike", "visit a9001; look", whole=False)
    check("a door word beside another command is refused: a line of its own", t.startswith("ERR [door]") and "line of its own" in t, t)

    # ---- (iv) two in one version ---------------------------------------------------------------------------------
    t = say("sable", "visit a9001")
    check("sable joins the same version, and is told pike is there and that the world is pike's copy, not today's home",
          f"a9001 at {sha1[:7]}" in t and "Here too: pike" in t and "when pike came in (not today's home), from e" in t, t)
    t = say("sable", 'find "made while away"')
    check("sable sees pike's note in the version", "1 hit" in t and one in t, t)
    t = say("juniper", 'find "made while away"')
    check("juniper, at home, does not: nothing of the visit is at home", "1 hit" not in t and "~ in" not in t, t)

    # ---- (v) the worker commits mid-visit ------------------------------------------------------------------------
    rewrite(a1 / NOTATION / "rooms.py", "(VERSION ONE)", "(VERSION TWO)")
    git(a1, "commit", "-q", "-am", "a9001: says TWO now")
    sha2 = git(a1, "rev-parse", "HEAD")
    time.sleep(5.5)                               # the door asks the worktree's commit at most every 5 s
    t = say("pike", "go")
    check("a commit mid-visit leaves the visit unchanged, and tells pike",
          "(VERSION ONE)" in t and f"a9001 has moved on since you came in (1 commit(s), now {sha2[:7]})" in t, t)
    t = say("pike", "go")
    check("it is said once", "moved on" not in t and "(VERSION ONE)" in t, t)
    t = say("pike", "visit a9001")
    check("visit a9001 again, with sable still in the old commit: the door doesn't pick, it names both ways in",
          t.startswith(f"ERR [door] a9001 is at {sha2[:7]} now") and f"sable in {one} (world from e" in t
          and "`visit a9001 with=<name>`" in t and f"`visit a9001 new` takes {sha2[:7]}" in t and "Nothing was changed" in t, t)
    t = say("pike", "visit a9001 new")
    check("visit a9001 new pins the new commit, names what moved, and says what pike left in the old one",
          f"you are in a9001 at {sha2[:7]}" in t and f"Since you were last here ({sha1[:7]}): 1 commit(s): {sha2[:7]} a9001: says TWO now" in t
          and f"You left {one}. You leave behind: 1 note made" in t, t)
    t = say("pike", "go")
    check("pike is on the new code", "(VERSION TWO)" in t and f"a9001@{sha2[:7]}" in t, t)
    t = say("sable", "go")
    check("sable, who did not visit again, is still on the commit she came in to", "(VERSION ONE)" in t and one in t, t)
    t = say("juniper", "visit a9001")
    check("juniper, arriving now, is told who is in which commit and is not put in either (Juniper c3167)",
          t.startswith(f"ERR [door] a9001 is at {sha2[:7]} now, where pike is") and f"sable in {one}" in t
          and "juniper" not in get(base + "/door/status")["away"], t)
    t = say("juniper", "visit a9001 with=sable")
    check("with=sable joins sable's, the earlier commit", f"you are in a9001 at {sha1[:7]}" in t and "Here too: sable" in t, t)
    t = say("juniper", "home")
    check("juniper comes home having made nothing, and is told so", "back from " + one in t and "You made and changed nothing there" in t, t)
    t = say("juniper", "visit a9001 with=rowan")
    check("with= someone who isn't there is refused", t.startswith("ERR [door] rowan is not in a9001"), t)

    # ---- (iii) a version that won't start; a version killed mid-visit -------------------------------------------
    t = say("juniper", "visit a9002")
    check("a version whose deskd won't start refuses entry and quotes its error",
          t.startswith("ERR [door] a9002") and "can't be entered" in t and "broken on purpose" in t and "You are still home" in t, t)
    t = say("juniper", "go")
    check("and juniper never left", "VERSION" not in t and "~ in" not in t and SAYS in t, t)
    t = say("juniper", "home")
    check("`home` at home is answered by the door", t == "[door] you are home already, in no version.", t)
    vs = get(base + "/door/status")["versions"]
    pid = vs[one]["pid"]
    subprocess.run(["taskkill", "/F", "/PID", str(pid)] if sys.platform == "win32" else ["kill", "-9", str(pid)], capture_output=True)
    time.sleep(1)
    before = total()
    t = say("sable", f'do create {R.SHELF} kind=note title="typed after it died"')
    check("a version killed mid-visit: the next line is refused, told, and run nowhere",
          t.startswith("ERR [door]") and f"{one}'s desk stopped" in t and "You are home" in t and "not run anywhere" in t, t)
    check("nothing was sent home", total() == before, (before, total()))
    t = say("sable", "go")
    check("sable is home again, on home's code", "VERSION" not in t and "~ in" not in t and SAYS in t, t)

    # ---- home, and what home gained -------------------------------------------------------------------------------
    say("pike", f"look {R.SHELF} :1")
    say("pike", f'do create {R.SHELF} kind=note title="made in the second"')
    say("pike", f'do create {R.SHELF} kind=note title="and another"')
    t = say("pike", "home")
    check("home: the door says where pike was, what pike leaves behind, and how to report it",
          t.startswith(f"[door] you are home, back from a9001@{sha2[:7]}") and f'do prop a9001 lived="a9001@{sha2[:7]}:' in t
          and "You leave behind: 2 notes made; it is gone with the version" in t, t)
    t = say("pike", "go")
    check("pike's lines are home's again", "VERSION" not in t and "~ in" not in t, t)
    check("home's world gained no event from any of it", total() == n0, (n0, total()))
    check("home's desk no longer shows pike away", not rooms.presences(D)("pike").startswith("away"), rooms.presences(D)("pike"))
    lived = json.loads((state / "visits.json").read_text(encoding="utf-8"))["lived"]
    check("the door kept who lived which commit (for a landing to compare)",
          [(v["who"], v["commit"]) for v in lived if v["who"] == "pike"] == [("pike", sha1), ("pike", sha2)]
          and any(v.get("fell") for v in lived if v["who"] == "sable"), lived)
    time.sleep(3)
    left = [p.name for p in (state / "visits").iterdir()] if (state / "visits").exists() else []
    check("the versions' folders are removed when nobody is in them", left == [], left)

    # ---- a page; a door started again; no door at all -------------------------------------------------------------
    t = say("pike", "visit a9001", headers={"Origin": base})
    check("`visit` from a page is refused for now", t.startswith("ERR [door]") and "not built" in t and get(base + "/door/status")["away"] == {}, t)
    say("pike", "visit a9001")
    check("explore.py refuses an away actor's line when the door did not answer it",
          explore.away_in(WORLD, "pike", state) == f"a9001@{sha2[:7]}" and explore.away_in(WORLD, "sable", state) is None
          and explore.away_in("another-world", "pike", state) is None)
    door.terminate()
    door.wait()
    time.sleep(3.5)                               # its deskds go on their own (DESKD_PARENT)
    door = start_door()
    t = say("pike", f'do create {R.SHELF} kind=note title="typed after the door restarted"')
    check("a door started again brings pike home, told, and the line is run nowhere",
          t.startswith("ERR [door] the door was started again while you were in a9001") and "not run anywhere" in t and total() == n0, t)
    t = say("pike", "go")
    check("and the line after is home's", "VERSION" not in t and "~ in" not in t and SAYS in t, t)
finally:
    if door is not None:
        door.terminate()
        door.wait()
        time.sleep(3.5)
    for p in (saved, saved.with_suffix(".lock")):
        p.unlink(missing_ok=True)
    shutil.rmtree(tmp, ignore_errors=True)

print(f"{len(fails)} failed" if fails else "all passed", f"({time.time() - t0:.0f} s, world {WORLD})")
sys.exit(1 if fails else 0)
