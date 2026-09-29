"""health: is the host still whole? Run before and after a change lands (tier 2 of live building).

    python health.py <world> [--json]

Checks, from this checkout:
  - every lab Python file compiles, and every desk-shell script parses (node --check, when node is here)
  - test_scene.py passes
  - the frozen session prints are unchanged in the golden form (suite/sessions.py --check)
  - every lens in <world> that the desk can find still compiles; the list of lenses that compile is printed, so a
    landing can be judged against the list from before it (a lens that was already broken is not the change's fault)

Prints one line per check; with --json, a last line {"ok": bool, "lenses_ok": [...], "failed": [...]}.
It reads the world under the desk's lock and never writes it.
"""
import json
import shutil
import subprocess
import sys
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


def run(args, timeout=600):
    r = subprocess.run([sys.executable] + args, cwd=HERE, capture_output=True, text=True, timeout=timeout,
                       env={**shutil.os.environ, "DESKD": "off"})
    return r.returncode, (r.stdout + r.stderr)


def check_lenses(world):
    import export_docs
    import scene
    desk = export_docs.load(world)
    w = desk.world
    names = sorted({s["title"] for s in w.subjects.values() if "lens" in (s.get("tags") or []) and w.appearances_of(s["id"])})
    ok, bad = [], []
    for name in names:
        try:
            scene.scene_for(desk, name)
            ok.append(name)
        except Exception as e:        # a lens that refuses, or a compiler that breaks: both mean not whole
            bad.append(f"{name}: {type(e).__name__}: {str(e)[:160]}")
    return ok, bad


def main():
    world = next((a for a in sys.argv[1:] if not a.startswith("--")), "frontier")
    failed = []
    bad = check_python()
    print(f"python: {'ok' if not bad else 'FAILED'}" + "".join(f"\n  {b}" for b in bad))
    failed += [f"python {b}" for b in bad]
    bad, note = check_js()
    print(f"scripts: {note or ('ok' if not bad else 'FAILED')}" + "".join(f"\n  {b}" for b in bad))
    failed += [f"script {b}" for b in bad]
    if not failed:                   # the rest needs code that at least compiles
        code, out = run(["test_scene.py"])
        last = (out.strip().splitlines() or ["?"])[-1]
        print(f"test_scene: {last}")
        if code:
            failed.append(f"test_scene: {last}")
        code, out = run(["suite/sessions.py", "--check"])
        line = next((l for l in out.splitlines() if "worlds at" in l), out.strip()[-200:])
        print(f"session prints: {line}")
        if code or " 0 differ in the golden form" not in line:
            failed.append(f"session prints: {line}")
    lenses_ok, bad = [], []
    try:
        lenses_ok, bad = check_lenses(world)
        print(f"lenses in {world}: {len(lenses_ok)} compile" + (f", {len(bad)} refuse" if bad else ""))
    except Exception as e:
        failed.append(f"lenses: the world could not be read: {type(e).__name__}: {e}")
        print(f"lenses in {world}: could not read the world ({e})")
    if "--json" in sys.argv:
        print(json.dumps({"ok": not failed, "lenses_ok": lenses_ok, "lenses_bad": bad, "failed": failed}))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
