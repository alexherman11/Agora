"""health: is the host still whole? Run before and after a change lands (tier 2 of live building).

    python health.py <world> [--json] [--jobs N] [--changed <path>,<path>] [--fail-fast [--excuse <check>,...]]
                     [--only <check>,...]

The script checks run N at once (default half this machine's processors, at most 8; --jobs 1 runs them one after
another). --changed names what a change touched: the checks it can reach start first (affected()). --fail-fast stops
the run at the first failing check not named in --excuse (a landing names those already failing on main), so a broken
change costs seconds; a stopped run says so ("stopped" in --json) and is never a full judgement. --only runs just the
named checks (keys as in "failed_checks"), with the compiling they need: how a landing finds which branch of several
broke a check. Every run without --only and not stopped runs every check below.

Checks, from this checkout:
  - every lab Python file compiles, and every desk-shell script parses (node --check, when node is here)
  - test_scene.py passes, and every test_*_paint.py when a browser is here (CSS rules only a painter can test)
  - the rooms tests pass (test_room_verbs, test_room_look, test_room_reads, test_blanks, test_prop_fields,
    test_house_words, test_house_cols, test_persons, test_persons_stored, test_lines, test_help_notes, test_promises,
    test_lived, test_rules, test_lanes, test_bound_words, test_calls, test_sayings, test_due_any), each on a small world it builds itself (roomworld.py), so a failure is
    the code's and not today's world's
  - test_door.py passes: deskd is swapped three times behind a door (and once refused) with no event lost or doubled
  - test_visit.py passes (a3204): `visit` and `home` through a real door, a version killed, one line written home
  - calm.style and every style note in <world> read by the one style reader (style.py; 8 Oct: the painter is handed
    the looks, so there is no second reader to agree with)
  - the frozen session prints are unchanged in the golden form (suite/sessions.py --check)
  - every lens in <world> that the desk can find still compiles; the list of lenses that compile is printed, so a
    landing can be judged against the list from before it (a lens that was already broken is not the change's fault)
  - the Help binder in <world> is true to this checkout's code (helpnotes.check, a1595): every command and built-in
    verb has a note, each names the arguments the code takes and shows none it doesn't. Each problem is a failed entry
    beginning "help note: "; the house excuses one that was there before the landing

Prints one line per check, each ending in the seconds it took, then a total line; with --json, a last line
{"ok": bool, "lenses_ok": [...], "failed": [...], "seconds": {check: s, ..., "total": s}}.
It reads the world under the desk's lock and never writes it.
"""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
ROOM_TESTS = (
    # one a line (14 Oct): every builder adds here, and one long line made every two branches conflict
    "test_room_verbs.py",
    "test_room_look.py",
    "test_room_reads.py",
    "test_blanks.py",
    "test_prop_fields.py",
    "test_house_words.py",
    "test_house_cols.py",
    "test_persons.py",
    "test_persons_stored.py",
    "test_lines.py",
    "test_kinds.py",
    "test_help_notes.py",
    "test_promises.py",
    "test_lived.py",
    "test_rules.py",
    "test_lanes.py",
    "test_bound_words.py",
    "test_rule_bound.py",
    "test_calls.py",
    "test_sayings.py",
    "test_due_any.py",
    "test_kept.py",
    "test_queries.py",
    "test_table.py",
    "test_house_verbs.py",
    "test_nearest.py",
    "test_reach.py",
    "test_wake_fold.py",
    "test_settled.py",
    "test_comment_reply.py",
    "test_design_talk.py",
    "test_landing_wait.py",
    "test_worker_pool.py",
    "test_landing_queue.py",
    "test_witnessed.py",
    "test_bench_talk.py",
    "test_builder_asks.py",
    "test_line_waits.py",
    "test_captures.py",
)
HELP_FAIL = "help note: "      # each help problem's failed entry starts so; the house excuses one it had before a landing


def check_help(world):
    """a1595: the Help binder in <world> against this checkout's code (helpnotes.check). -> (problems, notes count)."""
    import export_docs
    import helpnotes
    desk = export_docs.load(world)
    desk.world.me = "health"
    desk.seen, desk.open = {}, {desk.world.root}
    return helpnotes.check(desk), len(helpnotes.entries(desk.world))


def check_python():
    bad = []
    for p in sorted(HERE.glob("*.py")) + sorted((HERE / "suite").glob("*.py")):
        try:
            compile(p.read_text(encoding="utf-8"), str(p), "exec")      # parse only: nothing is written
        except (SyntaxError, ValueError) as e:
            bad.append(f"{p.name}: {type(e).__name__}: {e}"[:220])
    return bad


def check_js():
    node = shutil.which("node")
    if not node:
        return [], "node not found; scripts not checked"
    bad = []
    for p in sorted((HERE / "desk-shell").glob("*.js")) + sorted((HERE / "desk-shell" / "style").glob("*.js")):
        r = subprocess.run([node, "--check", str(p)], capture_output=True, text=True)
        if r.returncode:
            bad.append(f"{p.name}: {(r.stderr.strip().splitlines() or ['?'])[0][:200]}")
    return bad, None


def style_reads(srcs):
    """8 Oct: one reader of a style (style.py). Each (name, text) must read, and the line says how many of its
    properties the painter draws nothing for. -> (failures, note)."""
    import style
    bad, drawn_nothing = [], 0
    for name, src in srcs:
        c = style.check(src)
        if c["refusal"]:
            bad.append(f"{name}: {c['refusal']}")
        drawn_nothing += len(c["unread"])
    return bad, f"{len(srcs)} read; {drawn_nothing} properties the painter draws nothing for"


def world_styles(world):
    import export_docs
    w = export_docs.load(world).world
    return [(f"style {s['title']} ({s['id']})", s["text"]) for s in w.subjects.values() if "style" in (s.get("tags") or [])]


def run(args, timeout=600):
    r = subprocess.run([sys.executable] + args, cwd=HERE, capture_output=True, text=True, timeout=timeout,
                       env={**shutil.os.environ, "DESKD": "off"})
    return r.returncode, (r.stdout + r.stderr)


# ------------------------------------------------------------------------------------------------- the checks, at once
# 15 Oct (a5288; a5261 point 2): health took about 140 s, one script after another, and a landing holds the one landing
# room for all of it. Each script check already builds its own world (roomworld.py, named by its pid) and serves on a
# free port, so they run side by side now (--jobs, default below; --jobs 1 is the old order). Every check still runs,
# and its line and its failed entry are worded as before, so a landing judged now compares with one judged then.

def script_checks():
    """Every check that is a script of its own: (key, args, timeout, group), in the order the lines are printed."""
    from screen import BROWSERS
    out = [("test_scene", ["test_scene.py"], 600, "test_scene")]
    out += [(Path(n).stem, [n], 300, "room tests") for n in ROOM_TESTS]
    out += [("test_store", ["test_store.py", "--quick"], 300, "test_store"),
            ("test_door", ["test_door.py"], 300, "door test"),
            ("test_visit", ["test_visit.py"], 400, "visit test")]
    if any(Path(b).exists() for b in BROWSERS):
        out += [(p.stem, [p.name], 180, "paint") for p in sorted(HERE.glob("test_*_paint.py"))]
    out += [("session prints", ["suite/sessions.py", "--check"], 600, "session prints")]
    return out


SLOW = ("test_visit", "test_door", "test_store", "test_landing_queue", "test_captures")   # started first: the run ends sooner


def verdict(key, group, code, out):
    """What a script check's line shows, and its failed entry (None when it passed), as health has always worded them."""
    if group == "session prints":
        line = next((l for l in out.splitlines() if "compiler on the working tree" in l), out.strip()[-200:])
        return line, (f"session prints: {line}" if code or " 0 differ in the golden form" not in line else None)
    last = (out.strip().splitlines() or ["?"])[-1]
    if not code:
        return last, None
    if group == "test_scene":
        return last, f"test_scene: {last}"
    # a5288: a failure names its cause: the test's own FAIL lines follow its last line (test_visit's did already)
    bad = [l[5:].strip() for l in out.splitlines() if l.startswith("FAIL ")]
    why = f": {'; '.join(bad)}" if bad and last.strip() not in ("; ".join(bad), f"FAIL {bad[-1]}") else ""
    if group == "visit test":
        return last, f"test_visit: {last}{why}"[:300]
    if group == "paint":
        return last, f"paint {key}: {last}"
    return last, f"{key}: {last}{why}"[:300]


def affected(changed):
    """The script checks nearest a change (a5288) -> {check: distance}: 0 when its script is among `changed` (paths
    in the repo or in the lab), 1 when it imports or names a changed file (\"door.py\" in a test that starts the door),
    2 through one file between; a painter file is 1 from the paint tests and test_scene. This only orders the run:
    every check runs whether it is near or not, so a dependency this misses costs time, never a check."""
    import ast
    import re
    files = {p.relative_to(HERE).as_posix(): p for p in list(HERE.glob("*.py")) + list((HERE / "suite").glob("*.py"))}
    stems = {Path(f).stem: f for f in files if "/" not in f}
    byname = {**{Path(f).name: f for f in files if "/" in f}, **{Path(f).name: f for f in files if "/" not in f}}
    names = re.compile(r"[\w./-]+\.(?:py|js|css|html|style)\b")
    uses = {}
    for f, p in files.items():
        try:
            src = p.read_text(encoding="utf-8")
            tree = ast.parse(src)
        except (OSError, SyntaxError, ValueError):
            uses[f] = set()
            continue
        mods = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods.add(node.module.split(".")[0])
        uses[f] = {stems[m] for m in mods if m in stems} | {byname.get(Path(m).name, Path(m).name) for m in names.findall(src)}
    lab = "research/text-desk-lab/notation/"
    touched = {Path(c[len(lab):] if c.startswith(lab) else c).name for c in changed}
    painter = any("desk-shell/" in c for c in changed)
    # nearly every lab file reaches every other in a few steps (roomworld, explore, the house), so what a change can
    # reach is all of it; how near it is orders the run. Distance 0: the script itself changed; 1: it imports or names
    # a changed file; 2: through one file between
    used_by = {}
    for f, us in uses.items():
        for u in us:
            used_by.setdefault(Path(u).name, set()).add(f)
    dist = {f: 0 for f in files if Path(f).name in touched}
    for name in touched - {Path(f).name for f in files}:       # a changed file that is not Python (lens.js): who names it
        for g in used_by.get(name, ()):
            dist.setdefault(g, 1)
    for step in (1, 2):
        for f in [f for f, d in dist.items() if d == step - 1]:
            for g in used_by.get(Path(f).name, ()):
                dist.setdefault(g, step)
    out = {}
    for key, args, _, group in script_checks():
        d = dist.get(args[0])
        if painter and group in ("paint", "test_scene"):
            d = min(d if d is not None else 1, 1)
        if d is not None:
            out[key] = d
    return out


def kill_tree(p):
    """A check stopped early takes the processes it started with it (a door test's door and deskd)."""
    if p.poll() is not None:
        return
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
    else:
        import os
        import signal
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except OSError:
            p.kill()


def run_scripts(checks, jobs, first=(), fail_fast=False, excuse=()):
    """Run the script checks, `jobs` at once: those in `first` before the rest, the slow ones first within each. With
    fail_fast, the first failure of a check not in `excuse` stops the run: nothing more starts and what runs is ended.
    -> {key: (code, output, seconds)} for every check that finished, and whether the run was stopped."""
    import threading
    first = first if isinstance(first, dict) else {k: 0 for k in first}
    order = sorted(checks, key=lambda c: (first.get(c[0], 9), c[0] not in SLOW, SLOW.index(c[0]) if c[0] in SLOW else 0))
    results, running, lock, stop = {}, {}, threading.Lock(), threading.Event()
    todo = list(order)

    def worker():
        while not stop.is_set():
            with lock:
                if not todo:
                    return
                key, args, timeout, group = todo.pop(0)
            t0 = time.perf_counter()
            p = subprocess.Popen([sys.executable] + args, cwd=HERE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True, encoding="utf-8", errors="replace", env={**shutil.os.environ, "DESKD": "off"},
                                 start_new_session=sys.platform != "win32")
            with lock:
                running[key] = p
            if stop.is_set():
                kill_tree(p)
            try:
                out, _ = p.communicate(timeout=timeout)
                code = p.returncode
            except subprocess.TimeoutExpired:
                kill_tree(p)
                out = (p.communicate()[0] or "") + f"\ntimed out after {timeout} s"
                code = -1
            with lock:
                running.pop(key, None)
                if stop.is_set() and code:
                    continue                  # ended by the stop, not by itself: it said nothing about the code
                results[key] = (code, out or "", round(time.perf_counter() - t0, 1))
                failed = verdict(key, group, code, out or "")[1]
                if fail_fast and failed and key not in excuse and not stop.is_set():
                    stop.set()
                    for q in list(running.values()):
                        kill_tree(q)
    threads = [threading.Thread(target=worker, daemon=True) for _ in range(max(1, jobs))]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return results, stop.is_set()


def check_lenses(world):
    import export_docs
    import scene
    desk = export_docs.load(world)
    w = desk.world
    import kinds
    lenses = {s["title"]: s for s in w.subjects.values() if kinds.is_lens(s) and w.appearances_of(s["id"])}
    ok, bad, expected = [], [], []
    for name in sorted(lenses):
        # Pike a611: a lens kept to refuse (a probe, prop expect=refuse on its note) is counted apart, so a refusal in
        # the health line always means look at this
        meant = str((lenses[name].get("props") or {}).get("expect", "")) == "refuse"
        try:
            scene.scene_for(desk, name)
            (bad if meant else ok).append(name if not meant else f"{name}: expected to refuse, and it compiled")
        except Exception as e:        # a lens that refuses, or a compiler that breaks: both mean not whole
            (expected if meant else bad).append(name if meant else f"{name}: {type(e).__name__}: {str(e)[:160]}")
    return ok, bad, expected


def opt_list(name):
    a = sys.argv[1:]
    return [x for x in a[a.index(name) + 1].split(",") if x] if name in a[:-1] else []


def main():
    world = next((a for a in sys.argv[1:] if not a.startswith("--")
                  and sys.argv[sys.argv.index(a) - 1] not in ("--jobs", "--changed", "--only", "--excuse")), "frontier")
    jobs = int(opt_list("--jobs")[0]) if opt_list("--jobs") else min(8, max(1, (os.cpu_count() or 2) // 2))
    only = set(opt_list("--only"))         # a5288: just these checks (and the compiling, which they need)
    fail_fast = "--fail-fast" in sys.argv
    excuse = set(opt_list("--excuse"))     # checks that fail already (on main): never a reason to stop early
    failed = []                      # (check, its failed entry)
    seconds = {}                     # check -> seconds it took; printed on its line, and in --json
    start = time.perf_counter()
    wanted = lambda key: not only or key in only        # noqa: E731

    def took(check, t0):
        seconds[check] = round(time.perf_counter() - t0, 1)
        return f" ({seconds[check]:.1f}s)"

    t0 = time.perf_counter()
    bad = check_python()
    print(f"python: {'ok' if not bad else 'FAILED'}{took('python', t0)}" + "".join(f"\n  {b}" for b in bad))
    failed += [("python", f"python {b}") for b in bad]
    t0 = time.perf_counter()
    bad, note = check_js()
    print(f"scripts: {note or ('ok' if not bad else 'FAILED')}{took('scripts', t0)}" + "".join(f"\n  {b}" for b in bad))
    failed += [("scripts", f"script {b}") for b in bad]
    first, stopped, ran = {}, False, set()
    if not failed:                   # the rest needs code that at least compiles
        # a1190 (Sable e2546; strand 3's lesson a1142): the rooms tests build their own world (roomworld.py), so a
        # failure here is the code's, and it shows at the landing that causes it instead of drifting where no one looks.
        # 7 Oct: test_store --quick is the log beside the world (store.py): the log replayed must say what the world
        # says. a1505: test_door, the door swapping deskd under the live page. a3204 (a3029: a test outside health fails
        # unseen): test_visit, visits through the same door, at every health, with no condition on which files changed.
        # Pike a611, 30 Sep: some painter rules live only in CSS, and only a browser can test them: every
        # test_*_paint.py runs when one is here. The frozen session prints, in the golden form (suite/sessions.py).
        # a5288: all of them at once, those the change can reach first (--changed), so a broken one shows soonest
        from screen import BROWSERS
        checks = [c for c in script_checks() if wanted(c[0])]
        changed = opt_list("--changed")
        first = affected(changed) if changed else {}
        import threading
        inproc = {}

        def in_process():             # the checks that read the world, beside the scripts
            t1 = time.perf_counter()
            srcs = [("calm.style (seed)", (HERE / "desk-shell" / "style" / "calm.style").read_text(encoding="utf-8"))]
            note = ""
            try:
                srcs += world_styles(world)
            except Exception as e:       # the world's own styles are the best evidence; the seed still counts
                note = f"  (the world's styles could not be read: {type(e).__name__}: {e})"
            try:
                inproc["styles"] = (style_reads(srcs), note, round(time.perf_counter() - t1, 1))
            except Exception as e:       # noqa: BLE001  (before, this ended health with a traceback)
                inproc["error"] = f"{type(e).__name__}: {e}"
        side = threading.Thread(target=in_process, daemon=True)
        if wanted("styles"):
            side.start()
        results, stopped = run_scripts(checks, jobs, first=first, fail_fast=fail_fast, excuse=excuse)
        if wanted("styles"):
            side.join()
        groups = {}
        for key, args, timeout, group in checks:
            groups.setdefault(group, []).append(key)

        def print_styles():
            if not wanted("styles"):
                return
            ran.add("styles")
            if "styles" not in inproc:     # the reader itself broke
                failed.append(("styles", f"style: the styles could not be read: {inproc.get('error', '?')}"))
                print(f"styles: could not be read ({inproc.get('error', '?')}) FAILED")
                return
            (bad, note), why, s = inproc["styles"]
            seconds["styles"] = s
            if why:
                print(why)
            print(f"styles: {note}{' FAILED' if bad else ''} ({s:.1f}s)" + "".join(f"\n  {b}" for b in bad))
            failed.extend(("styles", f"style {b}") for b in bad)
        for group, keys in groups.items():
            if group == "session prints":
                print_styles()
            done = [k for k in keys if k in results]
            ran |= set(done)
            shown = []
            for k in done:
                code, out, s = results[k]
                last, fault = verdict(k, group, code, out)
                shown.append(f"{k}: {last}" if group in ("room tests", "paint") else last)
                if fault:
                    failed.append((k, fault))
            if len(done) < len(keys):
                shown.append(f"{len(keys) - len(done)} not run: the run stopped at a failure")
            seconds[group] = round(sum(results[k][2] for k in done), 1)
            label = {"paint": "paint tests"}.get(group, group)
            print(f"{label}: {'; '.join(shown)} ({seconds[group]:.1f}s)")
            if group == "visit test" and not only and not any(Path(b).exists() for b in BROWSERS):
                print(f"paint tests: no browser here; {len(list(HERE.glob('test_*_paint.py')))} not run (0.0s)")
        if "session prints" not in groups:
            print_styles()
    # a1595: help's words are notes in the world's Help binder; the code must still be what they say. A problem names
    # the note, who made it and last changed it, and the code's place. It fails health; the house excuses a problem the
    # world already had before a landing (workshop.land), so a note's edit never reverts someone else's code
    if wanted("help notes"):
        ran.add("help notes")
        t0 = time.perf_counter()
        try:
            probs, n = check_help(world)
            print(f"help notes in {world}: {n} notes, " + ("true to the code" if not probs else f"{len(probs)} FAILED")
                  + took("help notes", t0) + "".join(f"\n  {p}" for p in probs))
            failed += [("help notes", HELP_FAIL + p) for p in probs]
        except Exception as e:
            failed.append(("help notes", f"{HELP_FAIL}the world could not be read: {type(e).__name__}: {e}"))
            print(f"help notes in {world}: could not read the world ({e}){took('help notes', t0)}")
    lenses_ok, bad, expected = [], [], []
    if wanted("lenses"):
        ran.add("lenses")
        t0 = time.perf_counter()
        try:
            lenses_ok, bad, expected = check_lenses(world)
            # Pike a611: a refusal printed on every landing that nobody can read is on its way to noise; name it and why
            why = "; ".join(b.split(". It can say")[0].replace(": LensRefusal: ", ": ")[:90] for b in bad)
            print(f"lenses in {world}: {len(lenses_ok)} compile, {len(bad)} unexpected refusals" + (f" ({why})" if bad else "")
                  + (f", {len(expected)} expected ({', '.join(expected)})" if expected else "") + took("lenses", t0))
        except Exception as e:
            failed.append(("lenses", f"lenses: the world could not be read: {type(e).__name__}: {e}"))
            print(f"lenses in {world}: could not read the world ({e}){took('lenses', t0)}")
    total = round(time.perf_counter() - start, 1)
    print(f"total: {total:.1f}s ({jobs} at once" + (f"; the checks' own times add to {sum(v for v in seconds.values()):.0f}s"
                                                  if jobs > 1 else "") + (f"; only {', '.join(sorted(only))}" if only else "")
          + ("; STOPPED at the first failure" if stopped else "") + ")")
    if "--json" in sys.argv:
        print(json.dumps({"ok": not failed, "lenses_ok": lenses_ok, "lenses_bad": bad, "failed": [f for _, f in failed],
                          "failed_checks": sorted({k for k, _ in failed}), "ran": sorted(ran | {"python", "scripts"}),
                          "first": sorted(k for k, d in first.items() if d <= 1), "stopped": stopped, "partial": bool(only) or stopped,
                          "seconds": {**seconds, "total": total}}))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
