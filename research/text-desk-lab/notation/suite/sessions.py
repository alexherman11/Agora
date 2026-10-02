"""Golden prints of every lens in every lab session, for comparing compilers over the same worlds.

    python suite/sessions.py                 print every lens of every session as committed at HEAD
    python suite/sessions.py --at <rev>      ... as committed at <rev>
    python suite/sessions.py --check         print again with the current compiler over the SAME worlds (the rev
                                             recorded in golden/sessions/INDEX.txt) and list what differs
    python suite/sessions.py --rebase <session>/<lens> ...   accept an intended change: rewrite those prints with the
                                             current compiler over the same worlds, and say so in INDEX.txt

Worlds are read from git (`git show <rev>:.../sessions/<name>.pickle`), never from the working tree, so a
session someone is using right now cannot move under the comparison, and nothing is written back. Each print is
kept whole (reads included, since the world is frozen); --check reports a difference in two tiers: in the
agreed golden form (keys and gesture lines kept, reads and world @N dropped), or in reads only.
"""
import io
import pathlib
import pickle
import re
import subprocess
import sys
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
HERE = pathlib.Path(__file__).resolve().parent
LAB = HERE.parent
REPO_PATH = "research/text-desk-lab/notation/sessions"
OUT = HERE / "golden" / "sessions"
sys.path.insert(0, str(LAB))
sys.path.insert(0, str(HERE))
from run import normalise  # noqa: E402


def git(*args, binary=False):
    r = subprocess.run(["git", "-C", str(LAB.parents[2]), *args], capture_output=True)
    if r.returncode:
        raise RuntimeError(r.stderr.decode("utf-8", "replace").strip())
    return r.stdout if binary else r.stdout.decode("utf-8").strip()


def slug(title):
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "untitled"


def lens_titles(desk):
    seen = {}
    for s in desk.world.subjects.values():
        if "lens" in (s.get("tags") or []):
            seen.setdefault(s["title"].lower(), s["title"])
    return sorted(seen.values(), key=str.lower)


def prints_at(rev):
    """-> {session: {"blob": sha, "lenses": {title: print}, "error": str|None}}"""
    names = [p for p in git("ls-tree", "--name-only", f"{rev}:{REPO_PATH}").splitlines() if p.endswith(".pickle")]
    out = {}
    for name in sorted(names):
        session = name[:-len(".pickle")]
        entry = out[session] = {"blob": git("rev-parse", f"{rev}:{REPO_PATH}/{name}")[:12], "lenses": {}, "error": None}
        try:
            desk = pickle.loads(git("show", f"{rev}:{REPO_PATH}/{name}", binary=True))
        except Exception as e:  # an old or foreign pickle
            entry["error"] = f"does not load: {type(e).__name__}: {e}"
            continue
        world = getattr(desk, "world", None)
        if world is None or not hasattr(desk, "dispatch"):
            entry["error"] = "not a desk"
            continue
        world.me = "golden"             # a reader of its own, as explore.py makes a visitor: no since-your-last-look banner
        desk.seen, desk.open, desk.last_event_seen = {}, {world.root}, len(world.events)
        desk._session, desk._window = session, ""
        # Jeff (25 Sep): the wall clock leaked into the prints. A world printed at a revision is read at the date it
        # recorded: following the wall clock would move today, run the day's rules and print an arrival line, none
        # of which is the compiler's doing.
        desk.follow = False
        # a1156: likewise the one-time binding of stored lines saved before bindings (verbs.bind_unbound) is a change
        # to a living world, recorded as a house event; a frozen world is printed as it was frozen
        world._binds_version = 1
        world._promises_version = 1     # a1587: and so is the once-per-world migration of owe= and awaiting=
        for title in lens_titles(desk):
            try:
                r = desk.dispatch("desk", {"line": f"scene {title}"})
                text = r.get("text") or ("ERR " + str(r.get("error")))
            except Exception as e:
                text = f"CRASH {type(e).__name__}: {e}"
            entry["lenses"][title] = text
    return out


def write(rev):
    found = prints_at(rev)
    if OUT.exists():
        for f in OUT.rglob("*.txt"):
            f.unlink()
    index = [f"rev {git('rev-parse', '--short', rev)}", ""]
    total = 0
    for session, e in found.items():
        d = OUT / session
        if e["error"]:
            index.append(f"{session} · pickle {e['blob']} · {e['error']}")
            continue
        index.append(f"{session} · pickle {e['blob']} · {len(e['lenses'])} lens(es)")
        for title, text in e["lenses"].items():
            d.mkdir(parents=True, exist_ok=True)
            (d / f"{slug(title)}.txt").write_text(text + "\n", encoding="utf-8", newline="\n")
            first = text.splitlines()[0] if text else ""
            index.append(f"  {slug(title)}.txt · {title}" + ("" if first.startswith("scene ") else f" · {first[:90]}"))
            total += 1
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "INDEX.txt").write_text("\n".join(index) + "\n", encoding="utf-8", newline="\n")
    print(f"{total} print(s) of {sum(1 for e in found.values() if not e['error'])} session(s) at {index[0][4:]} -> suite/golden/sessions/")
    bad = [s for s, e in found.items() if e["error"]]
    if bad:
        print(f"{len(bad)} session(s) did not load: {', '.join(bad)} (see INDEX.txt)")


def check():
    idx = (OUT / "INDEX.txt").read_text(encoding="utf-8").splitlines()
    rev = idx[0].split()[1]
    found = prints_at(rev)
    golden_form, reads_only, same, missing = [], [], 0, []
    for session, e in found.items():
        for title, text in e["lenses"].items():
            f = OUT / session / f"{slug(title)}.txt"
            if not f.exists():
                missing.append(f"{session}/{slug(title)}")
                continue
            old = f.read_text(encoding="utf-8").rstrip("\n")
            if old == text:
                same += 1
            elif normalise(old) == normalise(text):
                reads_only.append(f"{session}/{slug(title)}")
            else:
                a, b = normalise(old).splitlines(), normalise(text).splitlines()
                i = next((k for k, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
                golden_form.append((f"{session}/{slug(title)}", i + 1, a[i] if i < len(a) else "(none)", b[i] if i < len(b) else "(none)"))
    print(f"worlds at {rev}, compiler on the working tree: {same} same, {len(reads_only)} differ in reads only, "
          f"{len(golden_form)} differ in the golden form, {len(missing)} new")
    for name in reads_only:
        print(f"  reads only: {name}")
    for name, line, was, now in golden_form:
        print(f"  differs: {name}, line {line}\n    was {was.strip()}\n    now {now.strip()}")
    for name in missing:
        print(f"  new: {name}")


def rebase(names):
    idx = (OUT / "INDEX.txt").read_text(encoding="utf-8").splitlines()
    rev = idx[0].split()[1]
    found = prints_at(rev)
    for name in names:
        session, _, lens = name.partition("/")
        hit = [(t, x) for t, x in found.get(session, {}).get("lenses", {}).items() if slug(t) == lens]
        if not hit:
            print(f"no lens {name} at {rev}")
            continue
        (OUT / session / f"{lens}.txt").write_text(hit[0][1] + "\n", encoding="utf-8", newline="\n")
        idx.append(f"rebased {name} with the working-tree compiler at {git('rev-parse', '--short', 'HEAD')} (an intended change)")
        print(f"rebased {name}")
    (OUT / "INDEX.txt").write_text("\n".join(idx) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if "--rebase" in sys.argv:
        rebase(sys.argv[sys.argv.index("--rebase") + 1:])
    elif "--check" in sys.argv:
        check()
    else:
        write(sys.argv[sys.argv.index("--at") + 1] if "--at" in sys.argv[:-1] else "HEAD")
