"""health: is the host still whole? Run before and after a change lands (tier 2 of live building).

    python health.py <world> [--json]

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
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
ROOM_TESTS = ("test_room_verbs.py", "test_room_look.py", "test_room_reads.py", "test_blanks.py", "test_prop_fields.py",
              "test_house_words.py", "test_house_cols.py", "test_persons.py", "test_persons_stored.py", "test_lines.py", "test_kinds.py",
              "test_help_notes.py", "test_promises.py", "test_lived.py", "test_rules.py", "test_lanes.py", "test_bound_words.py", "test_rule_bound.py", "test_calls.py", "test_sayings.py", "test_due_any.py", "test_kept.py", "test_queries.py", "test_table.py", "test_house_verbs.py", "test_nearest.py", "test_reach.py", "test_wake_fold.py", "test_settled.py", "test_comment_reply.py", "test_design_talk.py", "test_landing_wait.py", "test_landing_queue.py", "test_bench_talk.py", "test_builder_asks.py")
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


def main():
    world = next((a for a in sys.argv[1:] if not a.startswith("--")), "frontier")
    failed = []
    seconds = {}                     # check -> seconds it took; printed on its line, and in --json
    start = time.perf_counter()

    def took(check, t0):
        seconds[check] = round(time.perf_counter() - t0, 1)
        return f" ({seconds[check]:.1f}s)"

    t0 = time.perf_counter()
    bad = check_python()
    print(f"python: {'ok' if not bad else 'FAILED'}{took('python', t0)}" + "".join(f"\n  {b}" for b in bad))
    failed += [f"python {b}" for b in bad]
    t0 = time.perf_counter()
    bad, note = check_js()
    print(f"scripts: {note or ('ok' if not bad else 'FAILED')}{took('scripts', t0)}" + "".join(f"\n  {b}" for b in bad))
    failed += [f"script {b}" for b in bad]
    if not failed:                   # the rest needs code that at least compiles
        t0 = time.perf_counter()
        code, out = run(["test_scene.py"])
        last = (out.strip().splitlines() or ["?"])[-1]
        print(f"test_scene: {last}{took('test_scene', t0)}")
        if code:
            failed.append(f"test_scene: {last}")
        # a1190 (Sable e2546; strand 3's lesson a1142): the rooms tests build their own world (roomworld.py), so a
        # failure here is the code's, and it shows at the landing that causes it instead of drifting where no one looks
        t0 = time.perf_counter()
        outs = []
        for name in ROOM_TESTS:
            code, out = run([name], timeout=300)
            last = (out.strip().splitlines() or ["?"])[-1]
            outs.append(f"{Path(name).stem}: {last}")
            if code:
                failed.append(f"{Path(name).stem}: {last}"[:300])
        print(f"room tests: {'; '.join(outs)}{took('room tests', t0)}")
        # 7 Oct: the log beside the world (store.py). The in-memory part: several hundred lines of every kind, then the
        # log replayed must say what the world says, a world rebuilt from its facts the same facts, and a command put
        # back by its facts must be the world before it. (test_store.py without --quick also runs the CLI and deskd.)
        t0 = time.perf_counter()
        code, out = run(["test_store.py", "--quick"], timeout=300)
        last = (out.strip().splitlines() or ["?"])[-1]
        print(f"test_store: {last}{took('test_store', t0)}")
        if code:
            failed.append(f"test_store: {last}"[:300])
        # a1505: the door swaps deskd under the live page; a deskd that no longer answers what the door asks (health,
        # events by index, gesture ids) would make every landing visible again
        t0 = time.perf_counter()
        code, out = run(["test_door.py"], timeout=300)
        last = (out.strip().splitlines() or ["?"])[-1]
        print(f"door test: {last}{took('door test', t0)}")
        if code:
            failed.append(f"test_door: {last}"[:300])
        # a3204 (a3029: a test outside health fails unseen): visits go through the same door, into versions of this
        # code; it runs at every health, with no condition on which files changed, since a condition can miss
        t0 = time.perf_counter()
        code, out = run(["test_visit.py"], timeout=400)
        last = (out.strip().splitlines() or ["?"])[-1]
        print(f"visit test: {last}{took('visit test', t0)}")
        if code:
            bad = [l[5:] for l in out.splitlines() if l.startswith("FAIL ")]
            failed.append(f"test_visit: {last}{': ' + '; '.join(bad) if bad else ''}"[:300])
        # Pike a611, 30 Sep: some painter rules live only in CSS (peek's nesting, a1032), and only a browser can test
        # them. When one is here, every test_*_paint.py runs (about 3 s each); without one, the line says so
        t0 = time.perf_counter()
        from screen import BROWSERS
        paints = sorted(HERE.glob("test_*_paint.py"))
        if not any(Path(b).exists() for b in BROWSERS):
            print(f"paint tests: no browser here; {len(paints)} not run{took('paint', t0)}")
        elif paints:
            outs = []
            for p in paints:
                code, out = run([p.name], timeout=180)
                last = (out.strip().splitlines() or ["?"])[-1]
                outs.append(f"{p.stem}: {last}")
                if code:
                    failed.append(f"paint {p.stem}: {last}")
            print(f"paint tests: {'; '.join(outs)}{took('paint', t0)}")
        t0 = time.perf_counter()
        srcs = [("calm.style (seed)", (HERE / "desk-shell" / "style" / "calm.style").read_text(encoding="utf-8"))]
        try:
            srcs += world_styles(world)
        except Exception as e:           # the world's own styles are the best evidence; the seed still counts
            print(f"  (the world's styles could not be read: {type(e).__name__}: {e})")
        bad, note = style_reads(srcs)
        print(f"styles: {note}{' FAILED' if bad else ''}{took('styles', t0)}" + "".join(f"\n  {b}" for b in bad))
        failed += [f"style {b}" for b in bad]
        t0 = time.perf_counter()
        code, out = run(["suite/sessions.py", "--check"])
        line = next((l for l in out.splitlines() if "compiler on the working tree" in l), out.strip()[-200:])
        print(f"session prints: {line}{took('session prints', t0)}")
        if code or " 0 differ in the golden form" not in line:
            failed.append(f"session prints: {line}")
    # a1595: help's words are notes in the world's Help binder; the code must still be what they say. A problem names
    # the note, who made it and last changed it, and the code's place. It fails health; the house excuses a problem the
    # world already had before a landing (workshop.land), so a note's edit never reverts someone else's code
    t0 = time.perf_counter()
    try:
        probs, n = check_help(world)
        print(f"help notes in {world}: {n} notes, " + ("true to the code" if not probs else f"{len(probs)} FAILED")
              + took("help notes", t0) + "".join(f"\n  {p}" for p in probs))
        failed += [HELP_FAIL + p for p in probs]
    except Exception as e:
        failed.append(f"{HELP_FAIL}the world could not be read: {type(e).__name__}: {e}")
        print(f"help notes in {world}: could not read the world ({e}){took('help notes', t0)}")
    lenses_ok, bad, expected = [], [], []
    t0 = time.perf_counter()
    try:
        lenses_ok, bad, expected = check_lenses(world)
        # Pike a611: a refusal printed on every landing that nobody can read is on its way to noise; name it and why
        why = "; ".join(b.split(". It can say")[0].replace(": LensRefusal: ", ": ")[:90] for b in bad)
        print(f"lenses in {world}: {len(lenses_ok)} compile, {len(bad)} unexpected refusals" + (f" ({why})" if bad else "")
              + (f", {len(expected)} expected ({', '.join(expected)})" if expected else "") + took("lenses", t0))
    except Exception as e:
        failed.append(f"lenses: the world could not be read: {type(e).__name__}: {e}")
        print(f"lenses in {world}: could not read the world ({e}){took('lenses', t0)}")
    total = round(time.perf_counter() - start, 1)
    print(f"total: {total:.1f}s")
    if "--json" in sys.argv:
        print(json.dumps({"ok": not failed, "lenses_ok": lenses_ok, "lenses_bad": bad, "failed": failed,
                          "seconds": {**seconds, "total": total}}))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
