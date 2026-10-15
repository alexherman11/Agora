# health: room test (health.py runs every test_*.py with this line among its first ten)
"""test_landing_queue: code reaches main only judged, and uncommitted edits never stop it (landing.py, Alex 14 Oct:
"main should only be good working code ... uncommitted changes not blocking new code arriving ... minimal clobbering").

    python test_landing_queue.py

A git repository of its own in a temporary folder stands in for the live checkout, with the lab's layout and a health.py
of its own: it fails when the code it is judging holds a file BROKEN, and lists the lenses named in LENSES as compiling.
Builders' branches are made beside it, and someone's uncommitted edits are left in it, as people leave them.
  1. a good branch lands: main moves by fast-forward, to the commit the room judged
  2. a branch that breaks health never reaches main, and says why
  3. an uncommitted edit elsewhere in the live checkout is left exactly as it was
  4. an uncommitted edit in a file the landing changes, on other lines: kept on a parked/ branch, and put back on top
     of the landing, so its writer finds it where they left it
  5. the same lines: main has the landing's lines, the edit is only on its parked branch, and the answer says so
  6. three branches at once, one broken: the other two land, the broken one is named
  7. a branch that does not merge into main is refused, main untouched
  8. main moves while a landing is judged: it is judged again on the new main, and lands on top of it
  9. health is run once per commit: a second landing on the same main does not judge main again
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTATION = "research/text-desk-lab/notation"
fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:1500]}"))
    if not ok:
        fails.append(name)


TMP = Path(tempfile.mkdtemp(prefix="landing-queue-"))
LIVE = TMP / "live"
os.environ["LANDING_LIVE"] = str(LIVE)
os.environ["LANDING_ROOM"] = str(TMP / "room")
os.environ["HEALTH_RUNS"] = str(TMP / "health-runs.txt")


def g(*args, cwd=LIVE):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr or r.stdout}")
    return r.stdout.strip()


HEALTH = '''import json, sys, pathlib
here = pathlib.Path(__file__).resolve().parent
import os
runs = pathlib.Path(os.environ["HEALTH_RUNS"])
n = int(runs.read_text()) if runs.exists() else 0
runs.write_text(str(n + 1))
broken = (here / "BROKEN").exists()
lenses = (here / "LENSES").read_text().split() if (here / "LENSES").exists() else []
print("stub health")
print(json.dumps({"ok": not broken, "lenses_ok": lenses, "failed": ["BROKEN is here"] if broken else []}))
'''

LIVE.mkdir()
n = LIVE / NOTATION
(n / "sessions").mkdir(parents=True)
(n / "health.py").write_text(HEALTH, encoding="utf-8")
(n / "LENSES").write_text("notes board\n", encoding="utf-8")
(n / "deskd.py").write_text("".join(f"line {i}\n" for i in range(1, 21)), encoding="utf-8")
(n / "lens.js").write_text("// painter\n", encoding="utf-8")
(LIVE / ".gitignore").write_text(f"{NOTATION}/sessions/\n{NOTATION}/house-state/\nhealth-runs.txt\n", encoding="utf-8")
g("init", "-q", "-b", "main")
g("config", "user.email", "test@example.com")
g("config", "user.name", "test")
g("config", "core.autocrlf", "false")
g("add", "-A")
g("commit", "-q", "-m", "start")
(n / "sessions" / "frontier.pickle").write_bytes(b"a world")
(n / "sessions" / "frontier.log.jsonl").write_bytes(b"{}\n")

sys.path.insert(0, str(HERE))
import landing   # noqa: E402  (reads LANDING_LIVE and LANDING_ROOM as it loads)


def branch(name, edits, base="main"):
    """A builder's branch: from `base`, with `edits` {path under notation: text or None to remove} committed."""
    g("branch", name, base)
    wt = TMP / f"wt-{name.replace('/', '-')}"
    g("worktree", "add", "-q", str(wt), name)
    for p, text in edits.items():
        f = wt / NOTATION / p
        if text is None:
            f.unlink()
        else:
            f.write_text(text, encoding="utf-8")
    g("add", "-A", cwd=wt)
    g("commit", "-q", "-m", f"{name}: work", cwd=wt)
    return name


def head():
    return g("rev-parse", "HEAD")


def text(p):
    return (n / p).read_text(encoding="utf-8")


def runs():
    f = TMP / "health-runs.txt"
    return int(f.read_text()) if f.exists() else 0


# 1
b = branch("claude/one", {"lens.js": "// painter, better\n"})
r = landing.land([b], who="claude")
check("1. a good branch lands: main moves by fast-forward to the commit the room judged",
      r["landed"] == [b] and not r["refused"] and head().startswith(r["head"]) and text("lens.js") == "// painter, better\n"
      and g("rev-parse", "HEAD^2") == g("rev-parse", b), r)

# 2
was = head()
b = branch("worker/two", {"BROKEN": "x\n"})
r = landing.land([b], who="worker-a2")
check("2. a branch that breaks health never reaches main, and says why",
      not r["landed"] and r["refused"] and "BROKEN is here" in r["refused"][0][1] and head() == was
      and not (n / "BROKEN").exists(), r)

# 3
(n / "notes.md").write_text("alex is writing\n", encoding="utf-8")
(n / "lens.js").write_text("// painter, better\n// codex is mid-edit\n", encoding="utf-8")
b = branch("codex/three", {"deskd.py": text("deskd.py").replace("line 3\n", "line three\n")})
r = landing.land([b], who="codex")
check("3. uncommitted edits elsewhere in the live checkout are left exactly as they were",
      r["landed"] == [b] and text("notes.md") == "alex is writing\n" and text("lens.js").endswith("codex is mid-edit\n")
      and "line three" in text("deskd.py") and not r["parked"], r)

# 4
(n / "deskd.py").write_text(text("deskd.py").replace("line 18\n", "line eighteen, by someone at work\n"), encoding="utf-8")
b = branch("claude/four", {"deskd.py": text("deskd.py").replace("line eighteen, by someone at work\n", "line 18\n").replace("line 2\n", "line two\n")})
r = landing.land([b], who="claude")
d = text("deskd.py")
check("4. an edit in a file the landing changes, on other lines: put back on top of the landing, kept on parked/ too",
      r["landed"] == [b] and "line two" in d and "line eighteen, by someone at work" in d and r["parked"]
      and not r["parked"][0]["conflicts"] and r["parked"][0]["branch"] in g("branch", "--list", "parked/*"), (r, d))
g("checkout", "--", f"{NOTATION}/deskd.py")         # its writer commits it elsewhere; the test goes on from main

# 5
(n / "deskd.py").write_text(text("deskd.py").replace("line 5\n", "line 5, mine\n"), encoding="utf-8")
b = branch("worker/five", {"deskd.py": text("deskd.py").replace("line 5, mine\n", "line 5\n").replace("line 5\n", "line five, theirs\n")})
r = landing.land([b], who="worker-a5")
d = text("deskd.py")
pb = r["parked"][0]["branch"] if r["parked"] else None
check("5. the same lines: main has the landing's, the edit only on its parked branch, and the answer names the file",
      r["landed"] == [b] and "line five, theirs" in d and "line 5, mine" not in d and pb
      and r["parked"][0]["conflicts"] == [f"{NOTATION}/deskd.py"]
      and "line 5, mine" in g("show", f"{pb}:{NOTATION}/deskd.py"), (r, d))

# 6
bs = [branch("a/six", {"one.txt": "1\n"}), branch("b/six", {"BROKEN": "x\n"}), branch("c/six", {"three.txt": "3\n"})]
r = landing.land(bs, who="house")
check("6. three branches at once, one broken: the other two land, the broken one is named",
      sorted(r["landed"]) == ["a/six", "c/six"] and [x[0] for x in r["refused"]] == ["b/six"]
      and (n / "one.txt").exists() and (n / "three.txt").exists() and not (n / "BROKEN").exists(), r)

# 7
was = head()
b = branch("worker/seven", {"lens.js": "// a different painter\n"}, base=g("rev-list", "--max-parents=0", "HEAD"))
r = landing.land([b], who="worker-a7")
check("7. a branch that does not merge into main is refused, main untouched",
      not r["landed"] and r["refused"] and "does not merge" in r["refused"][0][1] and head() == was, r)

# 8
b = branch("claude/eight", {"eight.txt": "8\n"})
other = branch("codex/meanwhile", {"meanwhile.txt": "m\n"})
real, once = landing.health, []


def health_while_main_moves(world, cwd):
    if not once:
        once.append(1)
        g("merge", "-q", "--ff-only", other)       # someone lands while this one is judged
    return real(world, cwd)


landing.health = health_while_main_moves
try:
    r = landing.land([b], who="claude")
finally:
    landing.health = real
check("8. main moves while a landing is judged: judged again on the new main, and lands on top of it",
      r["landed"] == [b] and (n / "meanwhile.txt").exists() and (n / "eight.txt").exists()
      and g("merge-base", "--is-ancestor", other, "HEAD") == "", r)

# 9
b = branch("claude/nine", {"nine.txt": "9\n"})
r0 = runs()
r = landing.land([b], who="claude")
check("9. health runs once for a landing on a main already judged (the main it lands on was judged as the last landing)",
      r["landed"] == [b] and runs() - r0 == 1, (runs() - r0, r))

# 10
(n / "byhand.txt").write_text("committed by hand\n", encoding="utf-8")
g("add", f"{NOTATION}/byhand.txt")
g("commit", "-q", "-m", "a commit straight onto main, never judged")
b = branch("claude/ten", {"ten.txt": "10\n"})
r0 = runs()
r = landing.land([b], who="claude")
check("10. on a main moved by hand (never judged), a landing that passes runs health once, not twice (Codex e9993)",
      r["landed"] == [b] and runs() - r0 == 1, (runs() - r0, r))

# 11
(n / "deskd.py").write_text(text("deskd.py").replace("line 7\n", "line seven, by hand\n"), encoding="utf-8")
(n / "lens.js").write_text("// painter\n// someone else, mid-edit\n", encoding="utf-8")
was = head()
hb = landing.hand([str(n / "deskd.py")], who="codex", words="line seven")
r = landing.land([hb], who="codex")
dirty = g("status", "--porcelain")
check("11. a hand landing: the named file as it stands lands, is clean after, and nothing is parked; another edit stays",
      r["landed"] == [hb] and "line seven, by hand" in g("show", f"HEAD:{NOTATION}/deskd.py") and "deskd.py" not in dirty
      and not r["parked"] and "lens.js" in dirty and text("lens.js").endswith("mid-edit\n") and g("rev-parse", "HEAD^1") == was,
      (r, dirty))

# 12
(n / "BROKEN").write_text("x\n", encoding="utf-8")
was = head()
hb = landing.hand([str(n / "BROKEN")], who="codex")
r = landing.land([hb], who="codex")
check("12. a hand landing that breaks health: main unmoved, the file still there as it was, the reason given",
      not r["landed"] and "BROKEN is here" in r["refused"][0][1] and head() == was and (n / "BROKEN").exists(), r)
(n / "BROKEN").unlink()
try:
    landing.hand([str(n / "deskd.py")], who="codex")
    check("12. a hand landing of files main already has is refused", False)
except ValueError as e:
    check("12. a hand landing of files main already has is refused", "nothing to land" in str(e), e)

# 13
import time   # noqa: E402
lockf = landing.STATE / "landing.lock"
holder = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
lockf.write_text(str(holder.pid), encoding="utf-8")
os.utime(lockf, (time.time() - 300, time.time() - 300))        # held five minutes, as a long judgement holds it
try:
    landing._lock(wait=2)
    check("13. a landing's lock held by a living landing, for minutes, is waited for, never broken", False, "it was taken")
except SystemExit as e:
    check("13. a landing's lock held by a living landing, for minutes, is waited for, never broken",
          lockf.read_text(encoding="utf-8").strip() == str(holder.pid), e)
holder.kill()
holder.wait()
got = landing._lock(wait=5)
check("13. a lock whose holder has died is taken", lockf.read_text(encoding="utf-8").strip() == str(os.getpid()))
landing._unlock(got)

print(landing.status())
print(f"{len(fails)} failed" if fails else "all passed")
subprocess.run(["git", "worktree", "prune"], cwd=LIVE, capture_output=True)
sys.exit(1 if fails else 0)
