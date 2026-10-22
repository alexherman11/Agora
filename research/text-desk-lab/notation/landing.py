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

15 Oct (a5288), so that many can land at once: a landing asked is written into a queue (house-state/landing-queue.json),
and whoever holds the lock judges everything waiting there as one batch, then answers each asker. Health runs its
checks side by side, those nearest the change first, and stops at the first failure main did not already have, so a
broken branch is refused in seconds; main moves only to a commit a whole health passed. When a batch fails, each of its
branches alone runs just the checks that failed: the ones that break them are refused with their own failure, and the
rest are judged again together (halves only when none breaks it alone).
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
    end = time.time() + wait
    while True:
        lock = _try_lock()
        if lock:
            return lock
        if time.time() > end:
            try:
                pid = (STATE / "landing.lock").read_text().strip()
            except OSError:
                pid = ""
            raise SystemExit(f"a landing (pid {pid or '?'}) has held landing.lock for over {wait // 60} minutes; still waiting is a choice for a person")
        time.sleep(0.2)


def _try_lock():
    """The landing lock if it is free, or held by a process that has died (its landing died with it); else None."""
    sys.path.insert(0, str(HERE))
    import explore
    STATE.mkdir(parents=True, exist_ok=True)
    lock = STATE / "landing.lock"
    for _ in range(3):
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except (FileExistsError, PermissionError):
            try:
                pid = lock.read_text().strip()
            except OSError:
                pid = ""
            if pid.isdigit() and not explore._alive(pid):
                lock.unlink(missing_ok=True)
                continue
            return None
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return lock
    return None


def _unlock(lock):
    import explore
    explore.release_lock(lock)


def _kept():
    try:
        return json.loads((STATE / "landing.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _keep(data):
    STATE.mkdir(parents=True, exist_ok=True)
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
    clean_room()
    return ROOM / NOTATION


def clean_room():
    """Ignore only isolated tool scratch, not untracked source contamination."""
    from fixture_cleanup import remove_tree
    scratch = ROOM / "research/window-lab/.tmp-agora"
    errors = remove_tree(scratch)
    if errors:
        log("cleanup-warning", path=str(scratch), errors=errors)
        print("landing: retained tool scratch; could not remove:\n" + "\n".join(errors), file=sys.stderr)
    # Old tests can still be letting go of scratch. Git must not race their
    # recursive deletion. The exclusion is rooted, not a repository-wide glob.
    args = ("clean", "-ffdxq", "-e", "/research/window-lab/.tmp-agora/")
    result = git(*args, cwd=ROOM)
    if result.returncode:
        # A concurrent remover may have finished between Git's scan and unlink.
        # Retry once; any persistent failure outside scratch still refuses.
        result = git(*args, cwd=ROOM)
        if result.returncode:
            raise RuntimeError(f"landing clean could not remove non-scratch files: "
                               f"{(result.stderr or result.stdout).strip()[-1600:]}")


def merge_in(branches, why, heads=None):
    """Merge each branch into the room, in order. -> (merged branches, [(branch, why it does not merge)]). `heads`, when
    given, gets each merged branch's own merge commit (its first parent is main with the branches before it)."""
    merged, refused = [], []
    for b in branches:
        r = git("merge", "--no-ff", b, "-m", (why.get(b) if isinstance(why, dict) else None) or f"land {b}", cwd=ROOM)
        if r.returncode:
            git("merge", "--abort", cwd=ROOM)
            refused.append((b, (r.stdout + r.stderr).strip()[-400:] or "it does not merge"))
        else:
            merged.append(b)
            if heads is not None:
                heads[b] = git("rev-parse", "HEAD", cwd=ROOM, check=True).stdout.strip()
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


def health(world, cwd, changed=(), only=(), fail_fast=False, excuse=()):
    """health.py in the room, on the room's code and the copied world. -> its JSON, or a failure saying why not.
    a5288: `changed` (the files the landing changes) starts the checks nearest them first; `fail_fast` stops at the
    first failure of a check not in `excuse`; `only` runs just those checks. Run without them, it is all of health."""
    args = [sys.executable, "health.py", world, "--json"]
    if changed:
        args += ["--changed", ",".join(list(changed)[:300])]     # it only orders; a command line has a length
    if only:
        args += ["--only", ",".join(only)]
    if fail_fast:
        args += ["--fail-fast"] + (["--excuse", ",".join(excuse)] if excuse else [])
    # The judge is another worktree: do not inherit a builder's AGORA_TMP
    # pointing outside it (agora_tmp correctly refuses that).
    scratch = Path(cwd).resolve().parents[2] / "research/window-lab/.tmp-agora"
    os.makedirs(scratch, exist_ok=True)
    env = {**os.environ, "DESKD": "off", **{key: str(scratch) for key in ("AGORA_TMP", "TMP", "TEMP", "TMPDIR")}}
    # Visits make nested Git repositories and run child servers. Their private
    # lifetime must not overlap a subsequent room reset/clean after a restart.
    visits = STATE / "test-visits"
    visits.mkdir(parents=True, exist_ok=True)
    env["AGORA_VISIT_TMP"] = str(visits.resolve())
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=1200, env=env)
    lines = (r.stdout or "").strip().splitlines()
    try:
        data = json.loads(lines[-1])
        if not isinstance(data, dict) or not isinstance(data.get("ok"), bool) or not isinstance(data.get("failed"), list):
            raise ValueError("invalid health receipt")
    except (IndexError, ValueError):
        data = {"ok": False, "lenses_ok": [], "failed": [f"health.py did not report: {(r.stderr or r.stdout)[-300:]}"]}
    if r.returncode and data.get("ok"):
        data = {**data, "ok": False, "failed": data["failed"] + [f"health.py exited {r.returncode} despite ok receipt"]}
    # A diagnostic selection never becomes proof of the whole checkout, even
    # when an older health script does not understand/report the new flags.
    data["partial"] = bool(only) or bool(data.get("partial")) or bool(data.get("stopped"))
    data["text"] = "\n".join(lines[:-1])
    return data


def log(what, **said):
    """a5288: one line per batch, judgement and outcome in house-state/landing-log.jsonl, so the time a landing took
    can be read afterwards: which runs, how long each, what stopped them."""
    try:
        STATE.mkdir(parents=True, exist_ok=True)
        with open(STATE / "landing-log.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "pid": os.getpid(), "what": what, **said}) + "\n")
    except OSError:
        pass


def judged(world, sha, kept, **how):
    """Health of commit `sha` (the room is at it), from what is kept or by running it. Only a whole run is kept: one
    stopped at a failure, or run for some checks only (`how`, health's options), judges this landing and no other."""
    key = f"{world}:{sha}"
    if key in kept.get("health", {}):
        return kept["health"][key]
    copy_world(world, ROOM / NOTATION)
    t0 = time.time()
    h = health(world, ROOM / NOTATION, **how)
    log("health", sha=sha[:7], how={k: v for k, v in how.items() if k != "changed"}, seconds=round(time.time() - t0, 1),
        ok=h.get("ok"), stopped=h.get("stopped"), failed=(h.get("failed") or [])[:4])
    h["partial"] = bool(how.get("only")) or bool(h.get("partial")) or bool(h.get("stopped"))
    if not h["partial"]:
        kept.setdefault("health", {})[key] = {k: h.get(k) for k in ("ok", "world_at", "lenses_ok", "failed",
                                                                "failed_checks", "text", "seconds")}
        while len(kept["health"]) > 40:
            kept["health"].pop(next(iter(kept["health"])))
    return h


def faults(before, after):
    """What the landing broke: a check failing that did not fail on main, or a lens that compiled and no longer does
    (a lens or help note broken before the landing is the world's, not the landing's; workshop's rule since a1595).
    A partial run (stopped, or some checks only) says nothing of the lenses unless it compiled them."""
    if after.get("partial") and "lenses" not in (after.get("ran") or []):
        after = {**after, "lenses_ok": before.get("lenses_ok") or []}
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


def _index_file(kind):
    """A git index of its own for one park or hand, named so that no other one shares it (another process, or
    another thread of the house, in the same second)."""
    import threading
    return STATE / f"{kind}-{os.getpid()}-{threading.get_ident()}-{time.time_ns()}.index"


def new_branch(stem, commit):
    """Branch `stem` at `commit`, or stem-2, stem-3 ... when that name is taken. 15 Oct (a5245's landing failed on
    'hand/codex-20261015-133134 already exists'): the names were the second only, so two hand landings by one actor in
    one second collided, as test_landing_queue's cases 11 and 12 do on a fast machine. git refuses a name that exists
    (it locks the ref to make it), so two makers at once can never both get one name: the second takes the next. -> name"""
    for k in range(1, 1000):
        name = stem if k == 1 else f"{stem}-{k}"
        r = git("branch", name, commit, cwd=LIVE)
        if not r.returncode:
            return name
        if "already exists" not in (r.stderr + r.stdout) and git("rev-parse", "--verify", "--quiet", f"refs/heads/{name}",
                                                                   cwd=LIVE).returncode:
            raise RuntimeError(f"git branch {name} {commit}: {(r.stderr or r.stdout).strip()[-400:]}")
    raise RuntimeError(f"no free branch name like {stem}")


def park(paths, why):
    """Keep someone's uncommitted edits to `paths` (in the live checkout) as a commit on a branch of their own, then put
    those files back as main has them. Nothing is lost; the landing goes ahead. -> the branch."""
    stamp = time.strftime("%Y%m%d-%H%M%S")
    idx = _index_file("park")
    env = {"GIT_INDEX_FILE": str(idx)}
    try:
        git("read-tree", "HEAD", cwd=LIVE, env=env, check=True)
        git("add", "-A", "--", *paths, cwd=LIVE, env=env, check=True)
        tree = git("write-tree", cwd=LIVE, env=env, check=True).stdout.strip()
        c = git("commit-tree", tree, "-p", "HEAD", "-m", f"parked: uncommitted edits in the live checkout, {stamp}\n\n{why}",
                cwd=LIVE, check=True).stdout.strip()
        branch = new_branch(f"parked/{stamp}", c)
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
    # a5245, 15 Oct (876c2b6): two hand landings by one builder in the same second asked for the same name, and the
    # second failed. It looked for a free name first; a5288: two at once could both see one free, so the name is now
    # taken by making it (new_branch), and the index is named by process and thread
    stem = f"hand/{''.join(c if c.isalnum() or c in '-_' else '-' for c in who)}-{stamp}"
    idx = _index_file("hand")
    env = {"GIT_INDEX_FILE": str(idx)}
    try:
        git("read-tree", "HEAD", cwd=LIVE, env=env, check=True)
        git("add", "-A", "--", *rel, cwd=LIVE, env=env, check=True)
        tree = git("write-tree", cwd=LIVE, env=env, check=True).stdout.strip()
        if tree == git("rev-parse", "HEAD^{tree}", cwd=LIVE, check=True).stdout.strip():
            raise ValueError("those files are as main has them: nothing to land")
        msg = f"{words or 'by hand'}\n\nlanded by hand from the live checkout by {who}: {', '.join(rel)}"
        c = git("commit-tree", tree, "-p", "HEAD", "-m", msg, cwd=LIVE, check=True).stdout.strip()
        branch = new_branch(stem, c)
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
    sys.path.insert(0, str(HERE.parents[1] / "window-lab"))
    import agora_tmp
    conflicts = []
    for p, mine in theirs.items():
        now = (LIVE / p).read_bytes() if (LIVE / p).is_file() else None
        was = git("show", f"{base}:{p}", cwd=LIVE)
        if mine is None or now is None or was.returncode:
            conflicts.append(p)        # made or removed on one side: no common ground to merge on
            continue
        d = Path(agora_tmp.directory("landing-reapply-"))
        try:
            fa, fb, fc = (d / n for n in ("now", "was", "mine"))
            fa.write_bytes(now)
            fb.write_bytes(subprocess.run(["git", "show", f"{base}:{p}"], cwd=LIVE, capture_output=True).stdout)
            fc.write_bytes(mine)
            m = subprocess.run(["git", "merge-file", "-p", str(fa), str(fb), str(fc)], capture_output=True)
        finally:
            shutil.rmtree(d, ignore_errors=True)
        if m.returncode == 0:
            (LIVE / p).write_bytes(m.stdout)
        else:
            conflicts.append(p)
    return conflicts


# --------------------------------------------------------------------------------------------------------------- queue
# 15 Oct (a5288; a5261 point 2: "ten landings would take about 25 min"): each landing took the lock and ran health
# alone, so landings asked at once waited in line for one judgement each. Now a landing that asks is written into the
# queue (house-state/landing-queue.json); whoever holds the lock takes everything waiting there for the same world and
# judges it as one batch (several branches at once, as land() always could), then writes each asker's answer. A landing
# asked while a batch is judged goes into the next one. Every commit main moves to has passed a whole health, as before.

def _queue(change):
    """Read the queue, let `change` alter it, write it back, all under the queue's own short lock. -> what change says."""
    sys.path.insert(0, str(HERE))
    import explore
    STATE.mkdir(parents=True, exist_ok=True)
    path, lock = STATE / "landing-queue.json", STATE / "landing-queue.lock"
    explore.take_lock(lock, tries=6000, pause=0.01)
    try:
        try:
            q = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            q = {}
        q.setdefault("waiting", [])
        q.setdefault("done", {})
        out = change(q)
        tmp = STATE / "landing-queue.json.tmp"
        tmp.write_text(json.dumps(q, indent=1), encoding="utf-8")
        os.replace(tmp, path)
        return out
    finally:
        explore.release_lock(lock)


def _serve():
    """Holding the landing lock: judge everything waiting for one world as one batch, and answer each asker. Entries
    leave the queue only with their answer, so a server that dies leaves them for the next."""
    def take(q):
        if not q["waiting"]:
            return []
        world = q["waiting"][0]["world"]
        batch = [e for e in q["waiting"] if e["world"] == world]
        for e in batch:
            e["taken"] = os.getpid()
        return batch
    batch = _queue(take)
    if not batch:
        return
    branches = list(dict.fromkeys(b for e in batch for b in e["branches"]))
    why = {b: w for e in batch for b, w in (e.get("why") or {}).items()}
    who = ", ".join(dict.fromkeys(e["who"] for e in batch))
    log("batch", branches=branches)
    try:
        r = _land(branches, batch[0]["world"], who, why, 0)
    except Exception as e:          # said to every asker, never lost
        r = {"landed": [], "refused": [(b, f"the landing failed: {type(e).__name__}: {e}") for b in branches],
             "head": None, "heads": {}, "parked": [], "text": "", "texts": {}}
    log("answered", landed=r["landed"], refused=[[b, w[:200]] for b, w in r["refused"]])
    answers = {}
    for e in batch:
        mine = e["branches"]
        landed = [b for b in r["landed"] if b in mine]
        answers[e["id"]] = {
            "landed": landed, "refused": [list(x) for x in r["refused"] if x[0] in mine],
            "head": next((r["heads"][b][:7] for b in reversed(mine) if b in r.get("heads", {})), None) if landed else None,
            "heads": {b: r["heads"][b][:7] for b in landed if b in r.get("heads", {})},
            "parked": r["parked"] if landed else [], "main_failing": r.get("main_failing") or [],
            "text": next((r["texts"][b] for b in mine if b in r.get("texts", {})), r["text"]),
            "batch": branches}

    def answer(q):
        q["waiting"] = [e for e in q["waiting"] if e["id"] not in answers]
        q["done"].update(answers)
        # Only the caller consumes its receipt. Dropping an unread answer to
        # cap this map would leave a slow live caller waiting forever.
    _queue(answer)


def _as_tuples(r):
    r["refused"] = [tuple(x) for x in r["refused"]]
    return r


def land(branches, world="frontier", who="?", why=None, _depth=0, wait=20 * 60):
    """Judge `branches` together on main and land them if they pass. -> {"landed": [...], "refused": [(branch, why)],
    "head": short sha or None (the commit that brought this landing's last branch), "heads": {branch: its commit},
    "parked": [...], "text": health's lines, "batch": every branch judged with these}. Through the queue: it waits for
    its answer, and serves the queue itself whenever the landing lock is free."""
    branches = [b for b in dict.fromkeys(branches) if b]
    if _depth:
        return _land(branches, world, who, why or {}, _depth)
    if not branches:
        return {"landed": [], "refused": [], "head": None, "heads": {}, "parked": [], "text": ""}
    import threading
    me = {"id": f"{os.getpid()}-{threading.get_ident()}-{time.time_ns()}", "branches": branches, "world": world,
          "who": who, "why": {b: (why or {}).get(b) for b in branches if (why or {}).get(b)}, "at": time.time()}
    _queue(lambda q: q["waiting"].append(me))
    end = time.time() + wait
    while True:
        r = _queue(lambda q: q["done"].pop(me["id"], None))
        if r is not None:
            return _as_tuples(r)
        lock = _try_lock()
        if lock:
            try:
                _serve()
            finally:
                _unlock(lock)
            continue
        if time.time() > end:
            def withdraw(q):
                e = next((e for e in q["waiting"] if e["id"] == me["id"]), None)
                if e and not e.get("taken"):
                    q["waiting"].remove(e)
                    return True
                return False
            if _queue(withdraw):
                raise SystemExit(f"the landing lock was held for over {wait // 60} minutes and this landing was never "
                                 "taken; still waiting is a choice for a person")
            end = time.time() + wait            # taken into a batch being judged: its answer is coming
        time.sleep(0.2)


def _land(branches, world, who, why, depth):
    out = {"landed": [], "refused": [], "head": None, "heads": {}, "parked": [], "text": "", "texts": {}}
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
        heads = {}
        merged, refused = merge_in(todo, why, heads)
        out["refused"] += [(b, f"does not merge into main: {w}") for b, w in refused]
        if not merged:
            _keep(kept)
            return out
        sha = git("rev-parse", "HEAD", cwd=ROOM, check=True).stdout.strip()
        changed = [p for p in git("diff", "--name-only", base, sha, cwd=ROOM).stdout.split("\n") if p]
        # a5288: the checks nearest what changed start first, and the run stops at the first failure main did not
        # already have (main's own health is kept: it is the last landing's), so a broken branch costs seconds, not
        # a whole health. A run that is not stopped is the whole of health, which is what lets main move
        known = kept.get("health", {}).get(f"{world}:{base}")
        after = judged(world, sha, kept, changed=changed, fail_fast=True,
                       excuse=(known or {}).get("failed_checks") or ())
        # 14 Oct (Codex e9993: a5062 judged again and again from 16:42 while main moved by hand under it): main alone is
        # judged only when the landing fails, to tell what it broke from what was already broken. A landing that passes
        # costs one run of health, so it is less often overtaken
        before = {"ok": True, "failed": []}
        if not after.get("ok", True) or after.get("failed"):
            if known is None:
                room_at(base)
                before = judged(world, base, kept)
            else:
                before = known
            if after.get("partial") and not faults(before, after):
                # it stopped at a failure main has too (main's health was not kept when this began): judge it whole
                room_at(sha)
                after = judged(world, sha, kept, changed=changed)
        _keep(kept)
        bad = faults(before, after)
        if after.get("partial") and not bad:
            bad = ["health is incomplete; main cannot advance"]
        if bad:
            if len(merged) == 1:
                out["refused"].append((merged[0], "judged and not landed: " + "; ".join(bad)[:1500]))
                out["text"] = out["texts"][merged[0]] = after.get("text", "")
                return out
            # a5288: together they broke something. Each branch alone runs just the checks that broke (seconds each);
            # those that break them alone are named with their own failure, and the rest are judged again as one
            new = sorted(set(after.get("failed_checks") or []) - set(before.get("failed_checks") or []))
            if after.get("failed_checks") is not None and any(b.startswith("lens ") for b in bad):
                new.append("lenses")
            culprits = {}
            for b in merged:
                room_at(base)
                one, _ = merge_in([b], why)
                if not one:
                    continue
                bsha = git("rev-parse", "HEAD", cwd=ROOM, check=True).stdout.strip()
                alone = judged(world, bsha, kept, only=new) if new else judged(world, bsha, kept)
                fb = faults(before, alone)
                if fb:
                    culprits[b] = (fb, alone.get("text", ""))
            _keep(kept)
            if culprits:
                for b, (fb, text) in culprits.items():
                    out["refused"].append((b, "judged and not landed: " + "; ".join(fb)[:1500]))
                    out["texts"][b] = text
                rest = [b for b in merged if b not in culprits]
                r = _land(rest, world, who, why, depth + 1) if rest else None
            else:
                # none breaks it alone: two of them together do, or the failure comes and goes. Halves, as before
                half = len(merged) // 2
                r = None
                for part in (merged[:half], merged[half:]):
                    rr = _land(part, world, who, why, depth + 1)
                    r = rr if r is None else {**rr, **{k: r[k] + rr[k] for k in ("landed", "refused", "parked")},
                                              "heads": {**r["heads"], **rr["heads"]}, "texts": {**r["texts"], **rr["texts"]},
                                              "head": rr["head"] or r["head"], "text": rr["text"] or r["text"],
                                              "main_failing": rr.get("main_failing") or r.get("main_failing") or []}
            if r:
                for k in ("landed", "refused", "parked"):
                    out[k] += r[k]
                out["heads"].update(r["heads"])
                out["texts"].update(r["texts"])
                out["head"] = r["head"] or out["head"]
                out["text"] = r["text"] or out["text"]
                out["main_failing"] = r.get("main_failing") or []
            return out
        moved, pk, whynot = advance(sha, base, f"parked by the landing of {', '.join(merged)} (asked by {who})")
        parked = None
        if pk:
            parked = {"branch": pk[0], "conflicts": pk[1]}
            out["parked"].append(parked)
        if moved:
            out["landed"] += merged
            out["head"] = sha[:7]
            out["heads"].update({b: heads[b][:7] for b in merged})
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
    try:
        q = json.loads((STATE / "landing-queue.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        q = {}
    for e in q.get("waiting") or []:
        lines.append(f"  {'being judged' if e.get('taken') else 'waiting'}: {', '.join(e['branches'])} (by {e['who']}, "
                     f"asked {time.strftime('%H:%M:%S', time.localtime(e['at']))})")
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
    if len(r.get("batch") or []) > 1:
        print(f"judged in one batch with {', '.join(b for b in r['batch'] if b not in branches)}")
    for b in r["landed"]:
        print(f"landed {b} as {(r.get('heads') or {}).get(b) or r['head']}")
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
