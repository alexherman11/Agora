"""landing: the one way code reaches main (Alex, 14 Oct 2026: "main should only be good working code, and things should
land as fast as possible, with uncommitted changes not blocking new code arriving ... many need to be able to work at
the same time").

    python landing.py <branch> [<branch> ...] [--as <who>] [--why <words>] [--world frontier]
    python landing.py --files <path> [<path> ...] --as <who> --why <words>    a hand landing: those files, as they
                                                     stand in the live checkout, judged and landed with no branch made
                                                     by hand (14 Oct: for whoever must work in the live checkout itself)
    python landing.py --status

Three kinds of room. The live checkout (C:/Projects/Agora4, on main) is what the door, the house and the worlds run;
nobody edits code there, and it moves only by a landing. Each builder works in a worktree of their own, on a branch.
The landing room (.worktrees/house-landing, the house's only) is where a landing is judged: main's newest commit with
the branch merged into it, beside a copy of the live world (its file and its log), through health.py, which compiles
the lab, runs its tests and the golden prints, and compiles every lens of the world. A landing that fails is never in
main; one that passes moves main by fast-forward. Health's answer for each commit is kept (house-state/landing.json),
so a landing usually costs one run of it.

Uncommitted edits never stop a landing. One in the live checkout in a file the landing changes is parked first: kept
as a commit on a branch parked/<when>, the file put back, and said in the answer; anything else there is left alone
(git moves only the files a landing changes). If main moves while a landing is judged, it is judged again on the new
main. Several branches given at once are merged and judged together; when they fail together they are split in halves
and each half judged, so the one that broke is found and the others land.

One landing at a time (house-state/landing.lock); the house's own landings (workshop.land) come through here too.
"""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def git(*args, cwd, env=None, check=False):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env={**os.environ, **(env or {})})
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {(r.stderr or r.stdout).strip()[-400:]}")
    return r


def live_checkout():
    """The checkout the desk runs: the one holding the repository's own .git, wherever this file was run from (a
    builder's worktree shares it). LANDING_LIVE names another (a test's repository)."""
    if os.environ.get("LANDING_LIVE"):
        return Path(os.environ["LANDING_LIVE"]).resolve()
    common = git("rev-parse", "--path-format=absolute", "--git-common-dir", cwd=HERE, check=True).stdout.strip()
    return Path(common).resolve().parent


LIVE = live_checkout()
NOTATION = HERE.relative_to(HERE.parents[2]).as_posix()      # research/text-desk-lab/notation in any checkout
ROOM = Path(os.environ.get("LANDING_ROOM") or (LIVE / ".worktrees" / "house-landing"))
STATE = LIVE / NOTATION / "house-state"
BANNED = (f"{NOTATION}/sessions/",)                           # worlds are never landed; .env never committed


def _lock(wait=20 * 60):
    """One landing at a time. 15 Oct: this took the sessions' lock (explore.take_lock), which removes any lock older
    than a minute even when its holder is alive (a session's lock is held for a moment). A landing holds it for minutes,
    so a second landing broke in after 60 s and both used the one landing room at once: a5062 was judged again and again
    on 14 Oct, a landing's record was lost, and a judgement could have run on a tree the other had just reset. Now only
    a holder whose process has gone gives the lock up; a living one is waited for, however long it takes."""
    sys.path.insert(0, str(HERE))
    import explore
    STATE.mkdir(parents=True, exist_ok=True)
    lock = STATE / "landing.lock"
    end = time.time() + wait
    while True:
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except (FileExistsError, PermissionError):
            try:
                pid = lock.read_text().strip()
            except OSError:
                pid = ""
            if pid.isdigit() and not explore._alive(pid):
                lock.unlink(missing_ok=True)          # its landing died with it
                continue
            if time.time() > end:
                raise SystemExit(f"a landing (pid {pid or '?'}) has held {lock.name} for over {wait // 60} minutes; still waiting is a choice for a person")
            time.sleep(0.2)
            continue
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return lock


def _unlock(lock):
    import explore
    explore.release_lock(lock)


def _kept():
    try:
        return json.loads((STATE / "landing.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _keep(data):
    tmp = STATE / "landing.json.tmp"
    tmp.write_text(json.dumps(data, indent=1), encoding="utf-8")
    os.replace(tmp, STATE / "landing.json")


# ---------------------------------------------------------------------------------------------------------------- room

def room_at(base):
    """The landing room, at commit `base`, with nothing else in it (untracked and ignored files too)."""
    if not (ROOM / ".git").exists():
        ROOM.parent.mkdir(parents=True, exist_ok=True)
        git("worktree", "prune", cwd=LIVE)
        git("worktree", "add", "--detach", str(ROOM), base, cwd=LIVE, check=True)
    git("merge", "--abort", cwd=ROOM)
    git("checkout", "--detach", "--force", base, cwd=ROOM, check=True)
    git("reset", "--hard", base, cwd=ROOM, check=True)
    git("clean", "-ffdxq", cwd=ROOM, check=True)
    return ROOM / NOTATION


def merge_in(branches, why):
    """Merge each branch into the room, in order. -> (merged branches, [(branch, why it does not merge)])."""
    merged, refused = [], []
    for b in branches:
        r = git("merge", "--no-ff", b, "-m", (why.get(b) if isinstance(why, dict) else None) or f"land {b}", cwd=ROOM)
        if r.returncode:
            git("merge", "--abort", cwd=ROOM)
            refused.append((b, (r.stdout + r.stderr).strip()[-400:] or "it does not merge"))
        else:
            merged.append(b)
    return merged, refused


def copy_world(world, into):
    """The live world (its file and its log, and its kept undo copies) beside the room's code, read under its lock, so
    file and log are one moment. A world server holding it in memory has its records on the log already."""
    sys.path.insert(0, str(HERE))
    import explore
    src = LIVE / NOTATION / "sessions"
    dst = into / "sessions"
    dst.mkdir(parents=True, exist_ok=True)
    if not (src / f"{world}.pickle").exists():
        return                     # a world that is not on disk (a test's, in memory): health builds its own
    lock = src / f"{world}.lock"
    explore.take_lock(lock, tries=1200, pause=0.05)
    try:
        for name in (f"{world}.pickle", f"{world}.log.jsonl", f"{world}.undo.sqlite"):
            if (src / name).exists():
                shutil.copyfile(src / name, dst / name)
    finally:
        explore.release_lock(lock)


def health(world, cwd):
    """health.py in the room, on the room's code and the copied world. -> its JSON, or a failure saying why not."""
    r = subprocess.run([sys.executable, "health.py", world, "--json"], cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=1200, env={**os.environ, "DESKD": "off"})
    lines = (r.stdout or "").strip().splitlines()
    try:
        data = json.loads(lines[-1])
    except (IndexError, ValueError):
        data = {"ok": False, "lenses_ok": [], "failed": [f"health.py did not report: {(r.stderr or r.stdout)[-300:]}"]}
    data["text"] = "\n".join(lines[:-1])
    return data


def judged(world, sha, kept):
    """Health of commit `sha` (the room is at it), from what is kept or by running it."""
    if sha in kept.get("health", {}):
        return kept["health"][sha]
    copy_world(world, ROOM / NOTATION)
    h = health(world, ROOM / NOTATION)
    kept.setdefault("health", {})[sha] = {k: h.get(k) for k in ("ok", "lenses_ok", "failed", "text", "seconds")}
    while len(kept["health"]) > 40:
        kept["health"].pop(next(iter(kept["health"])))
    return h


def faults(before, after):
    """What the landing broke: a check failing that did not fail on main, or a lens that compiled and no longer does
    (a lens or help note broken before the landing is the world's, not the landing's; workshop's rule since a1595)."""
    lost = sorted(set(before.get("lenses_ok") or []) - set(after.get("lenses_ok") or []))
    had = set(before.get("failed") or [])
    out = [f for f in after.get("failed") or [] if f not in had]
    if not after.get("ok") and not out and not lost and not after.get("failed"):
        out.append("health did not pass and said nothing about why")
    return out + [f"lens {x} compiled before and no longer does" for x in lost]


# ---------------------------------------------------------------------------------------------------------------- main

def dirty_in_live():
    """Paths with uncommitted changes in the live checkout (tracked or new), the worlds aside."""
    out = []
    for line in git("status", "--porcelain", "--untracked-files=all", cwd=LIVE).stdout.splitlines():
        p = line[3:].strip().strip('"')
        if " -> " in p:
            p = p.split(" -> ", 1)[1]
        if p and not p.startswith(BANNED):
            out.append(p)
    return out


def park(paths, why):
    """Keep someone's uncommitted edits to `paths` (in the live checkout) as a commit on a branch of their own, then put
    those files back as main has them. Nothing is lost; the landing goes ahead. -> the branch."""
    stamp = time.strftime("%Y%m%d-%H%M%S")
    branch = f"parked/{stamp}"
    idx = STATE / f"park-{stamp}.index"
    env = {"GIT_INDEX_FILE": str(idx)}
    try:
        git("read-tree", "HEAD", cwd=LIVE, env=env, check=True)
        git("add", "-A", "--", *paths, cwd=LIVE, env=env, check=True)
        tree = git("write-tree", cwd=LIVE, env=env, check=True).stdout.strip()
        c = git("commit-tree", tree, "-p", "HEAD", "-m", f"parked: uncommitted edits in the live checkout, {stamp}\n\n{why}",
                cwd=LIVE, check=True).stdout.strip()
        git("branch", branch, c, cwd=LIVE, check=True)
    finally:
        idx.unlink(missing_ok=True)
    tracked = set(git("ls-files", "--", *paths, cwd=LIVE).stdout.splitlines())
    if tracked:
        git("checkout", "HEAD", "--", *sorted(tracked), cwd=LIVE, check=True)
    for p in paths:
        if p not in tracked and (LIVE / p).is_file():
            (LIVE / p).unlink()
    return branch


def _holds(p, sha):
    """Does the live checkout's file `p` hold exactly what commit `sha` has (or both lack it)?"""
    f = LIVE / p
    there = subprocess.run(["git", "show", f"{sha}:{p}"], cwd=LIVE, capture_output=True)
    if there.returncode:
        return not f.exists()
    return f.is_file() and f.read_bytes().replace(b"\r\n", b"\n") == there.stdout.replace(b"\r\n", b"\n")


def hand(paths, who="?", words=""):
    """A hand landing (Codex e9779: some builders must work in the live checkout itself): the named files as they stand
    there now become one commit on main's newest, on a branch hand/<who>-<when>, which lands as any branch does. Nothing
    in the live checkout is touched first; if it lands, those files are simply clean, since main now holds them. -> the
    branch, or raises ValueError naming what cannot go."""
    rel = []
    for p in paths:
        q = Path(p)
        q = (Path.cwd() / q).resolve() if not q.is_absolute() else q.resolve()
        try:
            r = q.relative_to(LIVE.resolve()).as_posix()
        except ValueError:
            raise ValueError(f"{p} is not in the live checkout ({LIVE})")
        if r.startswith(BANNED) or r.endswith(".env"):
            raise ValueError(f"{r} may not land")
        rel.append(r)
    if not rel:
        raise ValueError("no files named")
    STATE.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    branch = f"hand/{''.join(c if c.isalnum() or c in '-_' else '-' for c in who)}-{stamp}"
    # a5245, 15 Oct: two hand landings by one builder in the same second asked for the same name, and the second failed
    k, base = 1, branch
    while git("rev-parse", "--verify", "--quiet", f"refs/heads/{branch}", cwd=LIVE).returncode == 0:
        k += 1
        branch = f"{base}-{k}"
    idx = STATE / f"hand-{stamp}-{k}.index"
    env = {"GIT_INDEX_FILE": str(idx)}
    try:
        git("read-tree", "HEAD", cwd=LIVE, env=env, check=True)
        git("add", "-A", "--", *rel, cwd=LIVE, env=env, check=True)
        tree = git("write-tree", cwd=LIVE, env=env, check=True).stdout.strip()
        if tree == git("rev-parse", "HEAD^{tree}", cwd=LIVE, check=True).stdout.strip():
            raise ValueError("those files are as main has them: nothing to land")
        msg = f"{words or 'by hand'}\n\nlanded by hand from the live checkout by {who}: {', '.join(rel)}"
        c = git("commit-tree", tree, "-p", "HEAD", "-m", msg, cwd=LIVE, check=True).stdout.strip()
        git("branch", branch, c, cwd=LIVE, check=True)
    finally:
        idx.unlink(missing_ok=True)
    return branch


def advance(sha, base, why):
    """Move main in the live checkout to `sha` (a descendant of `base`) by fast-forward. -> (moved, parked branch or
    None, why not). Not moved when main is no longer `base` (someone landed meanwhile)."""
    head = git("rev-parse", "HEAD", cwd=LIVE, check=True).stdout.strip()
    if head != base:
        return False, None, "main moved while this was judged"
    changed = set(git("diff", "--name-only", base, sha, cwd=LIVE, check=True).stdout.split("\n")) - {""}
    # a file that already holds what lands (a hand landing's own files) is not in the way: nothing to park
    dirty = [p for p in dirty_in_live() if p in changed]
    overlap = sorted(p for p in dirty if not _holds(p, sha))
    same = [p for p in dirty if p not in overlap]
    if same:
        # git will not fast-forward over a changed file even when it already holds what comes; staged, it sees that the
        # file is as the landing has it. Only the staging changes: the file itself is not touched
        git("add", "--", *same, cwd=LIVE, check=True)
    # what each overlapping file holds now (its writer's words), read before it is put back
    theirs = {p: (LIVE / p).read_bytes() if (LIVE / p).is_file() else None for p in overlap}
    parked = park(overlap, why) if overlap else None
    r = git("merge", "--ff-only", sha, cwd=LIVE)
    if r.returncode:
        return False, parked, (r.stdout + r.stderr).strip()[-400:]
    conflicts = reapply(theirs, base)
    return True, (parked, conflicts) if parked else None, ""


def reapply(theirs, base):
    """Put each parked edit back on top of the new main: a three-way merge of main's new file, the file as main had it
    when the edit was made (`base`), and the edit. Clean: the writer finds their edit where they left it, now over the
    landing. A conflict leaves main's file, and the edit stays on its parked branch. -> paths that conflicted."""
    import tempfile
    conflicts = []
    for p, mine in theirs.items():
        now = (LIVE / p).read_bytes() if (LIVE / p).is_file() else None
        was = git("show", f"{base}:{p}", cwd=LIVE)
        if mine is None or now is None or was.returncode:
            conflicts.append(p)        # made or removed on one side: no common ground to merge on
            continue
        with tempfile.TemporaryDirectory() as d:
            fa, fb, fc = (Path(d) / n for n in ("now", "was", "mine"))
            fa.write_bytes(now)
            fb.write_bytes(subprocess.run(["git", "show", f"{base}:{p}"], cwd=LIVE, capture_output=True).stdout)
            fc.write_bytes(mine)
            m = subprocess.run(["git", "merge-file", "-p", str(fa), str(fb), str(fc)], capture_output=True)
        if m.returncode == 0:
            (LIVE / p).write_bytes(m.stdout)
        else:
            conflicts.append(p)
    return conflicts


def land(branches, world="frontier", who="?", why=None, _depth=0):
    """Judge `branches` together on main and land them if they pass. -> {"landed": [...], "refused": [(branch, why)],
    "head": short sha or None, "parked": [...], "text": health's lines}. Takes the landing lock unless called inside."""
    branches = [b for b in dict.fromkeys(branches) if b]
    lock = _lock() if _depth == 0 else None
    try:
        return _land(branches, world, who, why or {}, _depth)
    finally:
        if lock:
            _unlock(lock)


def _land(branches, world, who, why, depth):
    out = {"landed": [], "refused": [], "head": None, "parked": [], "text": ""}
    if not branches:
        return out
    kept = _kept()
    for attempt in range(4):
        base = git("rev-parse", "HEAD", cwd=LIVE, check=True).stdout.strip()
        # what each branch would bring: nothing (already in main) or something a landing may not carry
        todo = []
        for b in branches:
            if git("rev-parse", "--verify", "--quiet", f"{b}^{{commit}}", cwd=LIVE).returncode:
                out["refused"].append((b, "no such branch"))
                continue
            files = [p for p in git("diff", "--name-only", f"{base}...{b}", cwd=LIVE).stdout.split("\n") if p]
            banned = [p for p in files if p.startswith(BANNED) or p.endswith(".env")]
            if not files:
                out["refused"].append((b, "nothing to land: the branch has no changes beyond main"))
            elif banned:
                out["refused"].append((b, f"the branch touches what may not land: {', '.join(banned[:6])}"))
            else:
                todo.append(b)
        if not todo:
            return out
        room_at(base)
        merged, refused = merge_in(todo, why)
        out["refused"] += [(b, f"does not merge into main: {w}") for b, w in refused]
        if not merged:
            _keep(kept)
            return out
        sha = git("rev-parse", "HEAD", cwd=ROOM, check=True).stdout.strip()
        after = judged(world, sha, kept)
        # 14 Oct (Codex e9993: a5062 judged again and again from 16:42 while main moved by hand under it): main alone is
        # judged only when the landing fails, to tell what it broke from what was already broken. A landing that passes
        # costs one run of health, so it is less often overtaken
        before = {"ok": True, "failed": []}
        if not after.get("ok", True) or after.get("failed"):
            room_at(base)
            before = judged(world, base, kept)
        _keep(kept)
        bad = faults(before, after)
        if bad:
            if len(merged) == 1:
                out["refused"].append((merged[0], "judged and not landed: " + "; ".join(bad)[:1500]))
                out["text"] = after.get("text", "")
                return out
            # together they broke something: judge each half alone, so the one that broke is found
            half = len(merged) // 2
            for part in (merged[:half], merged[half:]):
                r = _land(part, world, who, why, depth + 1)
                for k in ("landed", "refused", "parked"):
                    out[k] += r[k]
                out["head"] = r["head"] or out["head"]
                out["text"] = r["text"] or out["text"]
            return out
        moved, pk, whynot = advance(sha, base, f"parked by the landing of {', '.join(merged)} (asked by {who})")
        parked = None
        if pk:
            parked = {"branch": pk[0], "conflicts": pk[1]}
            out["parked"].append(parked)
        if moved:
            out["landed"] += merged
            out["head"] = sha[:7]
            out["text"] = after.get("text", "")
            out["main_failing"] = [f for f in after.get("failed") or [] if f in set(before.get("failed") or [])]
            kept.setdefault("landed", []).append({"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "head": sha[:7],
                                                  "branches": merged, "by": who, "parked": parked})
            kept["landed"] = kept["landed"][-200:]
            _keep(kept)
            return out
        if "main moved" not in whynot:
            out["refused"] += [(b, f"judged, but main could not take it: {whynot}") for b in merged]
            return out
        out["refused"] = [r for r in out["refused"] if r[0] not in branches]       # judged again on the new main
    out["refused"] += [(b, "main kept moving while it was judged (4 tries); ask again") for b in branches
                       if b not in out["landed"] and b not in [r[0] for r in out["refused"]]]
    return out


def status():
    kept = _kept()
    lines = [f"live checkout {LIVE}, main at {git('rev-parse', '--short', 'HEAD', cwd=LIVE).stdout.strip()}; landing room {ROOM}"]
    for x in kept.get("landed", [])[-10:]:
        lines.append(f"  {x['at']} landed {x['head']}: {', '.join(x['branches'])} (by {x['by']})" + (f"; parked {x['parked']['branch']}" if x.get("parked") else ""))
    dirty = dirty_in_live()
    lines.append(f"uncommitted in the live checkout: {len(dirty)} path(s)" + (": " + ", ".join(dirty[:8]) if dirty else ""))
    return "\n".join(lines)


def main(argv):
    if "--status" in argv:
        print(status())
        return 0
    opt = lambda k, d: argv[argv.index(k) + 1] if k in argv[:-1] else d      # noqa: E731
    skip = {opt("--as", None), opt("--why", None), opt("--world", None)}
    who, words = opt("--as", os.environ.get("DESK_AS") or "?"), opt("--why", "")
    files = []
    if "--files" in argv:
        rest = argv[argv.index("--files") + 1:]
        files = rest[:next((k for k, a in enumerate(rest) if a.startswith("--")), len(rest))]
        try:
            branch = hand(files, who, words)
        except ValueError as e:
            print(f"not landed: {e}")
            return 1
        print(f"the files as they stand are {branch}; judging it")
        argv = [a for a in argv if a not in files] + [branch]
    branches = [a for a in argv if not a.startswith("--") and a not in skip]
    if not branches:
        print(__doc__.split("\n\n")[1])
        return 2
    why = {b: f"land {b}" + (f": {words}" if words else "") + f"\n\nasked by {who}; judged in the landing room on main "
              f"with a copy of the live world, and landed by fast-forward." for b in branches}
    t0 = time.time()
    r = land(branches, world=opt("--world", "frontier"), who=who, why=why)
    for b in r["landed"]:
        print(f"landed {b} as {r['head']}")
        if b.startswith("hand/"):
            git("branch", "-D", b, cwd=LIVE)          # main holds it now; a hand branch that did not land is kept
    for b, w in r["refused"]:
        print(f"not landed {b}: {w}")
    if r.get("main_failing"):
        print(f"main was already failing these, and still is (not this landing's): {'; '.join(r['main_failing'])[:600]}")
    for p in r["parked"]:
        print(f"uncommitted edits in the live checkout, in files this landing changed, are kept on {p['branch']} and put "
              f"back on top of it" + (f"; these conflicted and stay only on that branch: {', '.join(p['conflicts'])}"
                                      if p["conflicts"] else ""))
    print(f"({time.time() - t0:.0f} s)")
    return 0 if r["landed"] and not r["refused"] else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
