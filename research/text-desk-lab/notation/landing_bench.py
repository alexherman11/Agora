"""landing_bench (a5288): how long ten small landings take, on a throwaway clone, with this branch's landing or main's.

    python landing_bench.py before|after together|staggered [--broken]

A clone of this repository in a temporary folder stands in for the live checkout, beside a copy of this worktree's
world (sessions/frontier-try.pickle, as frontier). Ten branches each add one comment line to a different lab file, as
a small change does; with --broken, the third (kinds.py) instead makes kinds.is_lens say no to every note (a real
break: lenses stop compiling and test_kinds fails). Main is judged once first, untimed, as the last landing leaves it judged.

  before     main's landing.py and health.py (one landing at a time, health one check after another), with only
             the hand/parked name fix, so that main's test_landing_queue does not fail on its own collision
  after      this branch's: the queue and its batches, health's checks at once, nearest the change first, fail-fast
  together   the ten are asked at once (ten cards set ready in one pass)
  staggered  one every 20 s

Each landing runs as `python landing.py <branch>` in its own process, as a builder or the house runs it. Prints each
landing's answer and when it came, the number of health runs, and the total; the clone is removed after.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTATION = "research/text-desk-lab/notation"
FILES = ["rooms.py", "style.py", "kinds.py", "scene.py", "door.py", "deskd.py", "world.py", "helpnotes.py", "store.py",
         "promises.py"]


def git(*args, cwd):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr or r.stdout}")
    return r.stdout.strip()


def main(argv):
    which, when = argv[0], argv[1]
    broken = "--broken" in argv
    repo = Path(git("rev-parse", "--show-toplevel", cwd=HERE))
    tmp = Path(tempfile.mkdtemp(prefix="landing-bench-"))
    live, room = tmp / "live", tmp / "room"
    env = {**os.environ, "LANDING_LIVE": str(live), "LANDING_ROOM": str(room), "DESKD": "off"}
    try:
        git("clone", "-q", "--shared", str(repo), str(live), cwd=tmp)
        git("checkout", "-q", "-B", "main", git("rev-parse", "HEAD", cwd=repo), cwd=live)
        git("config", "user.email", "bench@example.com", cwd=live)
        git("config", "user.name", "bench", cwd=live)
        lab = live / NOTATION
        if which == "before":
            for f in ("landing.py", "health.py", "test_landing_queue.py", "test_landing_wait.py"):
                (lab / f).write_text(git("show", f"main:{NOTATION}/{f}", cwd=repo) + "\n", encoding="utf-8")
            src = (lab / "landing.py").read_text(encoding="utf-8")
            stamp = 'stamp = time.strftime("%Y%m%d-%H%M%S")'
            assert stamp in src
            (lab / "landing.py").write_text(src.replace(stamp, stamp + ' + f"-{time.time_ns() % 1000000}"'), encoding="utf-8")
            git("commit", "-q", "-am", "bench: main's landing and health", cwd=live)
        branches = []
        for k, f in enumerate(FILES):
            b = f"bench/{k}-{Path(f).stem}"
            git("checkout", "-q", "-b", b, "main", cwd=live)
            p = lab / f
            if broken and f == "kinds.py":
                p.write_text(p.read_text(encoding="utf-8") + "\n\ndef is_lens(s):          # bench: a real break\n"
                             "    return False\n", encoding="utf-8")
            else:
                p.write_text(p.read_text(encoding="utf-8") + f"\n# bench {k}: a small change\n", encoding="utf-8")
            git("commit", "-q", "-am", f"bench {k}", cwd=live)
            git("checkout", "-q", "main", cwd=live)
            branches.append(b)
        # after the branches: sessions/frontier.pickle is tracked (an old one), and a copy made before went into one
        (lab / "sessions").mkdir(exist_ok=True)
        for ext in (".pickle", ".log.jsonl"):
            if (HERE / "sessions" / f"frontier-try{ext}").exists():
                shutil.copyfile(HERE / "sessions" / f"frontier-try{ext}", lab / "sessions" / f"frontier{ext}")
        (lab / "house-state").mkdir(exist_ok=True)
        t0 = time.time()
        prime = ("import landing; k = landing._kept(); b = landing.git('rev-parse', 'HEAD', cwd=landing.LIVE).stdout.strip(); "
                 "landing.room_at(b); h = landing.judged('frontier', b, k); landing._keep(k); print(h.get('ok'), h.get('failed'))")
        r = subprocess.run([sys.executable, "-c", prime], cwd=lab, env=env, capture_output=True, text=True, timeout=1800)
        print(f"main judged first (untimed): {r.stdout.strip()[-300:]} {r.stderr.strip()[-300:]} ({time.time() - t0:.0f} s)")
        procs, start = [], time.time()
        for k, b in enumerate(branches):
            if when == "staggered" and k:
                time.sleep(max(0.0, start + 20 * k - time.time()))
            procs.append((b, time.time(), subprocess.Popen([sys.executable, "landing.py", b, "--as", f"bench-{k}"], cwd=lab,
                                                            env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                                            text=True, encoding="utf-8", errors="replace")))
        ends = {}
        while len(ends) < len(procs):
            for b, asked, p in procs:
                if b not in ends and p.poll() is not None:
                    ends[b] = (time.time(), p.stdout.read())
            time.sleep(0.2)
        total = max(t for t, _ in ends.values()) - start
        for b, asked, p in procs:
            t, out = ends[b]
            said = " | ".join(l for l in out.strip().splitlines() if l.startswith(("landed", "not landed", "judged in")))
            print(f"{b}: asked at {asked - start:5.0f} s, answered at {t - start:5.0f} s (waited {t - asked:4.0f} s): {said[:300]}")
        logf = lab / "house-state" / "landing-log.jsonl"
        for line in (logf.read_text(encoding="utf-8").splitlines() if logf.exists() else []):
            print("  log", line[:400])
        kept = json.loads((lab / "house-state" / "landing.json").read_text(encoding="utf-8"))
        runs = len(kept.get("health", {}))
        landed = sum(len(x["branches"]) for x in kept.get("landed", []))
        print(f"{which} {when}{' broken' if broken else ''}: {landed} landed, {runs - 1} whole health runs kept after "
              f"main's (stopped and some-checks-only runs are not kept), total {total:.0f} s")
    finally:
        subprocess.run(["git", "worktree", "prune"], cwd=live, capture_output=True)
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1:])
