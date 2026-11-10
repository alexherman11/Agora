"""Golden prints: every lens of every frozen world, printed by the working-tree compiler, compared with the prints
that were agreed.

    python suite/sessions.py                 print every lens of every frozen world, writing the prints
    python suite/sessions.py --check         print again and list what differs from the agreed prints
    python suite/sessions.py --rebase <world>/<lens> ...   accept an intended change: rewrite those prints and say so
    python suite/sessions.py --freeze <session> [--at <rev>]   freeze a session's world, read from its pickle in git
                                             (HEAD unless --at), as plain JSON in suite/golden/worlds/<session>.json
    python suite/sessions.py --convert       rewrite every frozen lens in the one-word-per-line form (scene.to_lines);
                                             the prints must not change, which --check then shows

Why they exist (Alex, 5 Oct: rethink them, decide if we need them at all). The unit tests each build a small world
and ask one thing. These prints are the only net over the whole vocabulary at once: calendars, budgets, grids, folds,
spreads, the attack lenses of the early rounds and their refusals, over worlds that were lived in. They are a change
detector, not a proof: a difference is read, and either the compiler is wrong or the print is rebased with a word
about why (INDEX.txt keeps those words). What changed on 5 Oct: the worlds are plain JSON in the repo, no longer
pickles read from git at a pinned revision. A pickle needs every class it was made with to still exist; a plain
world needs only World's fields, and it is the first form of the store the versions design asks for (a1960). The
lens texts live inside the worlds, so --convert can move the corpus to the current grammar in place, with the prints
as the proof that nothing moved. Two tiers of difference, as before: in the golden form (keys and gesture lines kept,
reads and world @N dropped), or in reads only.

A frozen world is a resident's or Alex's lived world: it is kept for printing, and never grepped or quoted (AGENTS.md).
"""
import io
import json
import pathlib
import pickle
import re
import subprocess
import sys
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
HERE = pathlib.Path(__file__).resolve().parent
LAB = HERE.parent
REPO_PATH = "src/text-desk/notation/sessions"
OUT = HERE / "golden" / "sessions"
WORLDS = HERE / "golden" / "worlds"
sys.path.insert(0, str(LAB))
sys.path.insert(0, str(HERE))
from run import normalise  # noqa: E402
import tempfile  # noqa: E402

import reports  # noqa: E402

# 14 Oct (a4869 landed again): painter reports are kept by the house beside a world of the same name; a frozen world
# is named like the live one, so its prints read the live house's reports and its start time. Frozen worlds have no
# viewers: their reports are read from an empty folder of their own
reports.ROOT = pathlib.Path(tempfile.mkdtemp(prefix="frozen-reports-"))


def git(*args, binary=False):
    r = subprocess.run(["git", "-C", str(LAB.parents[2]), *args], capture_output=True)
    if r.returncode:
        raise RuntimeError(r.stderr.decode("utf-8", "replace").strip())
    return r.stdout if binary else r.stdout.decode("utf-8").strip()


def slug(title):
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "untitled"


def lens_titles(world):
    import kinds
    seen = {}
    for s in world.subjects.values():
        if kinds.is_lens(s):
            seen.setdefault(s["title"].lower(), s["title"])
    return sorted(seen.values(), key=str.lower)


# ---------------------------------------------------------------- frozen worlds

def load_world(path):
    """A World from its plain form: the fields World keeps, nothing else."""
    from world import World
    w = World.__new__(World)
    vars(w).update(json.loads(path.read_text(encoding="utf-8")))
    return w


def save_world(path, world):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(vars(world), ensure_ascii=False, sort_keys=True, indent=0) + "\n", encoding="utf-8", newline="\n")


def desk_for(world, name):
    """A reading desk over a frozen world, as explore.fresh makes one, read as the day the world recorded."""
    from desk_knife import DeskKnife
    d = DeskKnife(world, "lean")
    d.batch = True
    d.lean = True
    d.read_cap = 4
    d.ids = {}
    world.me = "golden"             # a reader of its own: no since-your-last-look banner
    d.seen, d.open, d.last_event_seen = {}, {world.root}, len(world.events)
    d._session, d._window = name, ""
    # Jeff (25 Sep): the wall clock leaked into the prints. A frozen world is read at the date it recorded: following
    # the wall clock would move today, run the day's rules and print an arrival line, none of which is the compiler's.
    d.follow = False
    # the once-per-world migrations (a1156 bindings, a1587 promises, a1590 persons) are changes to a living world,
    # recorded as house events; a frozen world is printed as it was frozen
    world._binds_version = 1
    world._promises_version = 1
    world._persons_version = 2
    return d


def freeze(session, rev="HEAD"):
    """-> the path written. The pickle is read from git, never from the working tree, so a session someone is using
    cannot move under the freeze. Only the world is kept: a desk's own state (what a viewer looked at, per-reader
    positions) is not the world and never printed as a world fact."""
    blob = git("show", f"{rev}:{REPO_PATH}/{session}.pickle", binary=True)
    desk = pickle.loads(blob)
    world = getattr(desk, "world", None)
    if world is None:
        raise SystemExit(f"{session}: not a desk")
    if not isinstance(getattr(world, "_ids", 0), int):      # a world pickled before the counter became an int
        world._ids = next(world._ids) - 1
    path = WORLDS / f"{session}.json"
    save_world(path, world)
    short = git("rev-parse", "--short", rev)
    note = f"{session} · frozen from sessions/{session}.pickle at {short} ({git('rev-parse', f'{rev}:{REPO_PATH}/{session}.pickle')[:12]})"
    marks = WORLDS / "FROZEN.txt"
    lines = [l for l in (marks.read_text(encoding="utf-8").splitlines() if marks.exists() else []) if not l.startswith(session + " ·")]
    marks.write_text("\n".join(sorted(lines + [note])) + "\n", encoding="utf-8", newline="\n")
    return path


def worlds():
    return sorted(WORLDS.glob("*.json"))


# ---------------------------------------------------------------- prints

def prints():
    """-> {world name: {title: print}}, every lens of every frozen world through `scene <title>`."""
    out = {}
    for path in worlds():
        name = path.stem
        world = load_world(path)
        desk = desk_for(world, name)
        out[name] = {}
        for title in lens_titles(world):
            try:
                r = desk.dispatch("desk", {"line": f"scene {title}"})
                text = r.get("text") or ("ERR " + str(r.get("error")))
            except Exception as e:
                text = f"CRASH {type(e).__name__}: {e}"
            out[name][title] = text
    return out


def write():
    found = prints()
    if OUT.exists():
        for f in OUT.rglob("*.txt"):
            f.unlink()
    index = ["prints of the frozen worlds in suite/golden/worlds (see FROZEN.txt there for where each came from)", ""]
    total = 0
    for name, lenses in found.items():
        d = OUT / name
        index.append(f"{name} · {len(lenses)} lens(es)")
        for title, text in lenses.items():
            d.mkdir(parents=True, exist_ok=True)
            (d / f"{slug(title)}.txt").write_text(text + "\n", encoding="utf-8", newline="\n")
            first = text.splitlines()[0] if text else ""
            index.append(f"  {slug(title)}.txt · {title}" + ("" if first.startswith("scene ") else f" · {first[:90]}"))
            total += 1
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "INDEX.txt").write_text("\n".join(index) + "\n", encoding="utf-8", newline="\n")
    print(f"{total} print(s) of {len(found)} world(s) -> suite/golden/sessions/")


def check():
    found = prints()
    golden_form, reads_only, same, missing = [], [], 0, []
    for name, lenses in found.items():
        for title, text in lenses.items():
            f = OUT / name / f"{slug(title)}.txt"
            if not f.exists():
                missing.append(f"{name}/{slug(title)}")
                continue
            old = f.read_text(encoding="utf-8").rstrip("\n")
            if old == text:
                same += 1
            elif normalise(old) == normalise(text):
                reads_only.append(f"{name}/{slug(title)}")
            else:
                a, b = normalise(old).splitlines(), normalise(text).splitlines()
                i = next((k for k, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
                golden_form.append((f"{name}/{slug(title)}", i + 1, a[i] if i < len(a) else "(none)", b[i] if i < len(b) else "(none)"))
    print(f"frozen worlds, compiler on the working tree: {same} same, {len(reads_only)} differ in reads only, "
          f"{len(golden_form)} differ in the golden form, {len(missing)} new")
    for name in reads_only:
        print(f"  reads only: {name}")
    for name, line, was, now in golden_form:
        print(f"  differs: {name}, line {line}\n    was {was.strip()}\n    now {now.strip()}")
    for name in missing:
        print(f"  new: {name}")
    return not golden_form and not missing


def rebase(names, why=""):
    idx = (OUT / "INDEX.txt").read_text(encoding="utf-8").splitlines()
    found = prints()
    for name in names:
        world, _, lens = name.partition("/")
        hit = [(t, x) for t, x in found.get(world, {}).items() if slug(t) == lens]
        if not hit:
            print(f"no lens {name}")
            continue
        (OUT / world / f"{lens}.txt").write_text(hit[0][1] + "\n", encoding="utf-8", newline="\n")
        idx.append(f"rebased {name} with the working-tree compiler at {git('rev-parse', '--short', 'HEAD')}" + (f": {why}" if why else " (an intended change)"))
        print(f"rebased {name}")
    (OUT / "INDEX.txt").write_text("\n".join(idx) + "\n", encoding="utf-8", newline="\n")


def convert():
    """Every frozen lens text to the one-word-per-line form, in place. A lens that does not parse (the corpus keeps
    refusals on purpose) is left as it is."""
    import scene
    n_done = n_kept = 0
    for path in worlds():
        world = load_world(path)
        desk = desk_for(world, path.stem)
        changed = False
        for s in world.subjects.values():
            if "lens" not in (s.get("tags") or []):
                continue
            style = (s.get("props") or {}).get("style")
            try:
                lines = scene.to_lines(s.get("text") or "", scene.style_roles(desk, style), style)
            except scene.LensRefusal:
                n_kept += 1
                continue
            if lines != (s.get("text") or ""):
                s["text"] = lines
                changed = True
                n_done += 1
        if changed:
            save_world(path, world)
    print(f"converted {n_done} lens(es) to lines; {n_kept} left as written (they do not parse)")


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    argv = sys.argv[1:]
    if "--freeze" in argv:
        rev = argv[argv.index("--at") + 1] if "--at" in argv else "HEAD"
        for name in argv[argv.index("--freeze") + 1:]:
            if name.startswith("--"):
                break
            print(f"frozen {freeze(name, rev)}")
    elif "--rebase" in argv:
        names = []
        for a in argv[argv.index("--rebase") + 1:]:
            if a.startswith("--"):
                break
            names.append(a)
        why = argv[argv.index("--why") + 1] if "--why" in argv else ""
        rebase(names, why)
    elif "--convert" in argv:
        convert()
    elif "--check" in argv:
        sys.exit(0 if check() else 1)
    else:
        write()
