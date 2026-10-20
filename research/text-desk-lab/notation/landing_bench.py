"""Ten real Git landings on isolated current-main source, before/after this patch.

python landing_bench.py before|after [--fixture] [--broken] [--keep]

Default runs real health beside a tool-made copy of frontier-try (needs a
browser-capable environment). --fixture substitutes 24 subprocess checks,
identical on both sides: scheduling evidence, NOT real-suite acceptance.
No shared Git writes, models, host queries or services.
"""
import argparse
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NOTATION = "research/text-desk-lab/notation"
OVERLAY = ("landing.py", "health.py", "test_landing_queue.py",
           "test_landing_wait.py", "test_health_runner.py",
           "test_landing_return.py", "test_house_merge.py")


def git(*args, cwd):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr or r.stdout}")
    return r.stdout.strip()


FIXTURE = '''import json, os, pathlib, subprocess, sys, time
here = pathlib.Path(__file__).resolve().parent
keys = ["test_broken"] + ["test_fixture_" + str(i) for i in range(23)]
only = sys.argv[sys.argv.index("--only")+1].split(",") if "--only" in sys.argv else []
checks = [(k, [k + ".py"], 300, "room tests") for k in keys if not only or k in only]
start = time.perf_counter()
if (here / "bench_parallel").exists():
    from bench_health_original import run_scripts
    result, stopped = run_scripts(checks, 4, {"test_broken": 0}, "--fail-fast" in sys.argv)
else:
    result, stopped = {}, False
    for k, args, timeout, group in checks:
        r = subprocess.run([sys.executable, *args], capture_output=True, text=True)
        result[k] = (r.returncode, r.stdout + r.stderr, 0)
bad = [k for k, (code, out, secs) in result.items() if code]
partial = bool(only) or stopped
data = {"ok": not bad, "failed": [k + ": BROKEN fixture" for k in bad],
        "failed_checks": bad, "lenses_ok": ["fixture"] if not partial else [],
        "ran": list(result), "partial": partial, "stopped": stopped,
        "seconds": {"total": round(time.perf_counter()-start, 3)}}
with open(os.environ["LANDING_BENCH_RECORD"], "a") as f:
    f.write(json.dumps(data) + "\\n")
print(json.dumps(data))
'''
CALLER = '''import json, pathlib, sys, landing
pathlib.Path(sys.argv[2]).write_text("ready")
r = landing.land([sys.argv[1]], world=sys.argv[3], who="bench")
print(json.dumps(r))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("which", choices=("before", "after"))
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument("--broken", action="store_true")
    parser.add_argument("--keep", action="store_true")
    opts = parser.parse_args()
    baseline = git("rev-parse", "main", cwd=ROOT)
    # Frozen-print basenames are long; leave room below Windows MAX_PATH.
    tmp = ROOT / ".worktrees" / ("lb-" + uuid.uuid4().hex[:12])
    live, room = tmp / "live", tmp / "room"
    os.makedirs(live)
    scratch = room / "research/window-lab/.tmp-agora"
    env = {**os.environ, "LANDING_LIVE": str(live), "LANDING_ROOM": str(room), "DESKD": "off",
           "LANDING_BENCH_RECORD": str(tmp / "judgements.jsonl"),
           **{k: str(scratch) for k in ("AGORA_TMP", "TMP", "TEMP", "TMPDIR")}}
    procs = []
    try:
        raw = subprocess.check_output(["git", "archive", "--format=zip", baseline], cwd=ROOT)
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            for entry in archive.infolist():
                path = Path(entry.filename)
                if entry.is_dir() or path.name.startswith(".env"):
                    continue
                out = live / path
                os.makedirs(out.parent, exist_ok=True)
                out.write_bytes(archive.read(entry))
        lab = live / NOTATION
        if opts.which == "after":
            for name in OVERLAY:
                (lab / name).write_bytes((HERE / name).read_bytes())
        if opts.fixture:
            (lab / "bench_health_original.py").write_bytes((lab / "health.py").read_bytes())
            if opts.which == "after":
                (lab / "bench_parallel").write_text("fixture scheduler")
            (lab / "health.py").write_text(FIXTURE, encoding="utf-8")
            for key in ["test_broken"] + ["test_fixture_" + str(i) for i in range(23)]:
                (lab / (key + ".py")).write_text(
                    "import pathlib, sys, time\ntime.sleep(.05)\n"
                    "bad = pathlib.Path('BROKEN').exists() and " + repr(key == "test_broken") + "\n"
                    "print('FAIL BROKEN fixture' if bad else 'all passed')\nsys.exit(int(bad))\n")
        with (live / ".gitignore").open("a") as f:
            f.write("\nhouse-state-bench.jsonl\nresearch/window-lab/.tmp-agora/\n")
        git("init", "-q", "-b", "main", cwd=live)
        git("config", "user.email", "bench@example.invalid", cwd=live)
        git("config", "user.name", "landing fixture", cwd=live)
        git("config", "core.autocrlf", "false", cwd=live)
        git("add", "-A", cwd=live)
        git("commit", "-q", "-m", "isolated landing benchmark", cwd=live)
        for k in range(10):
            git("checkout", "-q", "-b", f"bench/{k}", "main", cwd=live)
            if opts.broken and k == 2 and not opts.fixture:
                p = lab / "kinds.py"
                p.write_text(p.read_text(encoding="utf-8") + "\ndef is_lens(s):\n    return False\n", encoding="utf-8")
            else:
                (lab / ("BROKEN" if opts.broken and k == 2 else f"bench{k}.txt")).write_text(f"change {k}\n")
            git("add", "-A", cwd=live)
            git("commit", "-q", "-m", f"small change {k}", cwd=live)
            git("checkout", "-q", "main", cwd=live)
        world = "fixture" if opts.fixture else "frontier-try"
        if not opts.fixture:
            import landing
            old_live = landing.LIVE
            landing.LIVE = ROOT
            try:
                landing.copy_world(world, lab)
            finally:
                landing.LIVE = old_live
        prime = ("import landing; k=landing._kept(); "
                 "b=landing.git('rev-parse','HEAD',cwd=landing.LIVE).stdout.strip(); "
                 "landing.room_at(b); h=landing.judged(" + repr(world) + ",b,k); "
                 "landing._keep(k); print(h)")
        os.makedirs(lab / "house-state", exist_ok=True)
        r = subprocess.run([sys.executable, "-c", prime], cwd=lab, env=env,
                           capture_output=True, text=True, timeout=1800)
        if r.returncode:
            raise RuntimeError("baseline judge failed to report: " + (r.stderr or r.stdout)[-1500:])
        print("baseline judgement:", r.stdout[-1500:], flush=True)
        state, start = lab / "house-state", time.perf_counter()
        lock = state / "landing.lock"
        lock.write_text(str(os.getpid()))  # our fixture gate, never a live/shared lock
        for k in range(10):
            procs.append(subprocess.Popen(
                [sys.executable, "-c", CALLER, f"bench/{k}", str(tmp / f"caller-{k}"), world],
                cwd=lab, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8"))
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            markers = len(list(tmp.glob("caller-*")))
            queued = 0
            if markers == 10 and opts.which == "after":
                # Use the queue's own short lock; an external file reader can
                # interfere with Windows atomic replacement.
                q = subprocess.run(
                    [sys.executable, "-c", "import landing; print(landing._queue(lambda q: len(q['waiting'])))"],
                    cwd=lab, env=env, capture_output=True, text=True, timeout=30)
                if q.returncode:
                    raise RuntimeError("fixture queue receipt unavailable: " + q.stderr[-500:])
                queued = int(q.stdout.strip())
            if markers == 10 and (opts.which == "before" or queued == 10):
                break
            time.sleep(.05)
        else:
            raise RuntimeError("fixture callers did not reach gate")
        lock.unlink()
        answers = []
        for p in procs:
            out, err = p.communicate(timeout=1800)
            if p.returncode:
                raise RuntimeError("caller failed: " + (err or out)[-1000:])
            answers.append(json.loads(out.splitlines()[-1]))
        total = round(time.perf_counter() - start, 3)
        kept = json.loads((state / "landing.json").read_text())
        records = tmp / "judgements.jsonl"
        judges = [json.loads(l) for l in records.read_text().splitlines()] if records.exists() else []
        full = [j for j in judges if not j["partial"]]
        landed = sum(len(r["landed"]) for r in answers)
        refused = [item for r in answers for item in r["refused"]]
        if opts.fixture:
            required = {"test_broken"} | {"test_fixture_" + str(i) for i in range(23)}
            assert full and len(full) == len(kept["health"]), "missing fixture judgement evidence"
            assert all(set(j["ran"]) == required for j in full), "incomplete full fixture judgement"
            assert all(any(key.split(":")[-1].startswith(entry["head"]) for key in kept["health"])
                       for entry in kept["landed"]), "main advanced without kept full judgement"
            assert landed == (9 if opts.broken else 10), (landed, refused)
            assert len(refused) == int(opts.broken), refused
        print(json.dumps({
            "mode": opts.which, "baseline": baseline, "fixture": opts.fixture, "broken": opts.broken,
            "seconds": total, "landed": landed, "refused": refused,
            "full_judgements_after_prime": len(full)-1 if opts.fixture else len(kept.get("health", {}))-1,
            "partial_judgements": sum(j["partial"] for j in judges),
            "all_full_fixture_judges_ran_24_checks": bool(opts.fixture),
            "repository": str(live),
        }), flush=True)
    finally:
        for p in procs:
            if p.poll() is None:
                p.kill()
                p.wait()
        if not opts.keep:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
