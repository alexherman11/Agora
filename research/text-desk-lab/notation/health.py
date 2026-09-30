"""health: is the host still whole? Run before and after a change lands (tier 2 of live building).

    python health.py <world> [--json]

Checks, from this checkout:
  - every lab Python file compiles, and every desk-shell script parses (node --check, when node is here)
  - test_scene.py passes, and every test_*_paint.py when a browser is here (CSS rules only a painter can test)
  - the Python mirror of style.js that style receipts use (scene.style_check) agrees with style.js under node, on
    test_scene's samples, calm.style and every style note in <world>; without node the line says it was not checked
  - the frozen session prints are unchanged in the golden form (suite/sessions.py --check)
  - every lens in <world> that the desk can find still compiles; the list of lenses that compile is printed, so a
    landing can be judged against the list from before it (a lens that was already broken is not the change's fault)

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


def style_mirror(srcs):
    """a1101 (Sable c1212: two parsers of one language is how receipts start to lie): scene.style_check, which the
    receipts use, against desk-shell/style/style.js run under node, on each (name, text). -> (disagreements, note)."""
    import json
    import scene
    node = shutil.which("node")
    if not node:
        return [], "node not found; the Python mirror of style.js is NOT checked, so style receipts may drift unseen"
    bad = []
    for name, src in srcs:
        py = scene.style_check(src)
        r = subprocess.run([node, str(HERE / "desk-shell" / "checks" / "style-read.js")], input=src, capture_output=True,
                           text=True, encoding="utf-8")
        if r.returncode:
            bad.append(f"{name}: style-read.js failed: {(r.stderr.strip().splitlines() or ['?'])[-1][:160]}")
            continue
        js = json.loads(r.stdout)
        if (py["refusal"] or "").split(":")[0] != (js["refusal"] or ""):
            bad.append(f"{name}: refusal: mirror {py['refusal']!r}, style.js {js['refusal']!r}")
        mine, theirs = sorted([rl, p] for rl, p, _l, _w in py["unread"]), sorted(js["unread"])
        if mine != theirs:
            bad.append(f"{name}: unreadable props differ: mirror only {[x for x in mine if x not in theirs][:3]}, "
                       f"style.js only {[x for x in theirs if x not in mine][:3]}")
    return bad, None


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
    lenses = {s["title"]: s for s in w.subjects.values() if "lens" in (s.get("tags") or []) and w.appearances_of(s["id"])}
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
        import test_scene
        srcs = [(f"sample {k + 1}", s) for k, s in enumerate(test_scene.STYLE_SAMPLES)]
        srcs.append(("calm.style (seed)", (HERE / "desk-shell" / "style" / "calm.style").read_text(encoding="utf-8")))
        try:
            srcs += world_styles(world)
        except Exception as e:           # the world's own styles are the best evidence, but the samples still count
            print(f"  (the world's styles could not be read: {type(e).__name__}: {e})")
        bad, note = style_mirror(srcs)
        print(f"style mirror: {note or (f'agrees with style.js on {len(srcs)} styles' if not bad else 'FAILED')}{took('style mirror', t0)}"
              + "".join(f"\n  {b}" for b in bad))
        failed += [f"style mirror {b}" for b in bad]
        t0 = time.perf_counter()
        code, out = run(["suite/sessions.py", "--check"])
        line = next((l for l in out.splitlines() if "worlds at" in l), out.strip()[-200:])
        print(f"session prints: {line}{took('session prints', t0)}")
        if code or " 0 differ in the golden form" not in line:
            failed.append(f"session prints: {line}")
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
