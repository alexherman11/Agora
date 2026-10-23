"""keeper: keeps the house and deskd running on the current code, and is the way back when a landing breaks them.

    python keeper.py [world] [--port 8794]          default world: frontier

It is meant to change rarely. It:
  - runs the door (door.py) on the port and the house for the world, with DESKD pointing the house at the door (one
    host) and HOUSE_KEEPER=1 so the house may ask to be restarted;
  - a1505: the door, not the keeper, runs deskd behind it and swaps it for one on the new code whenever git HEAD moves,
    once the new one is healthy, so no page reloads and no call is cut. The keeper starts the door again if it dies;
  - restarts the house at once when it exits 75 (it asked, after a landing changed Python); restarts it with a
    pause when it dies otherwise;
  - if the house dies 3 times within 5 minutes of a landing (a commit whose subject begins "land "), reverts that
    landing and says so in its log: the one part of live building that does not depend on the code it protects. It
    reverts the landing by its hash, never HEAD (a4919), in a commit that names it, and records it in
    house-state/reverts.jsonl with the house's last output, so the house returns the commission to its worker (a5292);
  - for frontier, runs docs_sync.py --watch, so an edit to a design document in the vault or the repo reaches the
    other copy and the Handbook within a minute; starts it again, at most once a minute, if it dies. The watch is
    told the keeper's pid and ends when the keeper does, however that happens, and it refuses to be a second one.
Log: house-state/keeper.log.
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PY = sys.executable
LOG = HERE / "house-state" / "keeper.log"


def log(msg):
    LOG.parent.mkdir(exist_ok=True)
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def git(*args):
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True).stdout.strip()


def last_landing():
    """The newest landing on main's own line: a commit whose subject begins "land ", not yet reverted. a5292 (a4919):
    HEAD is not the landing. After one, the house commits its docs export on top, and anyone may commit meanwhile, so
    `git revert HEAD` reverted Codex's commit once. -> {hash, at, subject, parents} or None."""
    out = git("log", "--first-parent", "-n", "30", "--format=%H%x09%ct%x09%P%x09%s")
    reverted = set(re.findall(r"[0-9a-f]{40}", git("log", "--first-parent", "-n", "30", "--format=%b"))) if out else set()
    for line in out.splitlines():
        h, at, parents, subject = (line.split("\t", 3) + ["", "", "", ""])[:4]
        if subject.startswith("land ") and h not in reverted:
            return {"hash": h, "at": int(at or 0), "subject": subject, "parents": parents.split()}
    return None


def revert(landing, why, world):
    """Revert that landing by its hash, in a commit that names it, and record it in house-state/reverts.jsonl, where
    the house reads it and returns the commission to its worker (workshop.keeper_reverts)."""
    h, subject = landing["hash"], landing["subject"]
    log(f"{why}: reverting {h[:7]} '{subject[:80]}' (HEAD is {git('rev-parse', '--short', 'HEAD')})")
    merge = len(landing["parents"]) > 1
    # git's own message names it ('Revert "land ..."', 'This reverts commit <hash>'); --no-commit would let a commit
    # of ours sweep in whatever someone has staged in the main checkout
    r = subprocess.run(["git", "revert", "--no-edit", *(["-m", "1"] if merge else []), h],
                       cwd=REPO, capture_output=True, text=True)
    if r.returncode:
        subprocess.run(["git", "revert", "--abort"], cwd=REPO, capture_output=True, text=True)
    log("revert: " + ((r.stdout + r.stderr).strip()[-300:] or "ok"))
    if r.returncode:
        return None
    try:
        tail = (HERE / "house-state" / "house.out").read_text(encoding="utf-8", errors="replace")[-1500:]
    except OSError:
        tail = ""
    cid = subject[5:].split(":", 1)[0].strip()
    entry = {"at": time.strftime("%Y-%m-%d %H:%M:%S"), "world": world, "hash": h, "subject": subject,
             "cid": cid, "tip": landing["parents"][1] if merge else "", "revert": git("rev-parse", "HEAD"),
             "why": why, "tail": tail}
    with (HERE / "house-state" / "reverts.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def start(args, env=None, name=""):
    (HERE / "house-state").mkdir(exist_ok=True)      # a fresh checkout has none (it is not in git)
    out = open(HERE / "house-state" / f"{name}.out", "a", encoding="utf-8")
    return subprocess.Popen([PY, *args], cwd=HERE, env=env, stdout=out, stderr=subprocess.STDOUT)


def stop(p):
    if p and p.poll() is None:
        p.terminate()
        try:
            p.wait(timeout=20)
        except subprocess.TimeoutExpired:
            p.kill()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    world = args[0] if args else "frontier"
    port = sys.argv[sys.argv.index("--port") + 1] if "--port" in sys.argv[:-1] else "8794"
    env = {**os.environ, "DESKD": f"http://127.0.0.1:{port}", "HOUSE_KEEPER": "1"}
    head = git("rev-parse", "HEAD")
    door_args = ["door.py", port, "--world", world]
    deskd, house = start(door_args, name="door"), None
    time.sleep(8)                               # the door answers once its first deskd does
    house = start(["house.py", world], env, name="house")
    # handbook_docs.py writes to frontier, so only frontier's keeper runs the watch
    docs_args = ["docs_sync.py", "--watch", "--with", str(os.getpid())] if world == "frontier" else None
    docs, docs_at = (start(docs_args, env, name="docs_sync"), time.time()) if docs_args else (None, 0.0)
    # Twitch chat into frontier's chat role=twitch-chat (read-only; feed=off there is its off switch)
    tw_args = ([str(HERE.parent.parent / "window-lab" / "twitch_chat.py"), "--with", str(os.getpid())]
               if world == "frontier" else None)
    tw, tw_at = (start(tw_args, env, name="twitch_chat"), time.time()) if tw_args else (None, 0.0)
    log(f"keeper: world {world}, the door on {port} (deskd behind it), HEAD {head[:7]}")
    deaths, backoff_until, deskd_at, deskd_wait = [], 0.0, time.time(), 0.0
    try:
        while True:
            time.sleep(2)
            if deskd.poll() is not None and time.time() >= deskd_wait:
                quick = time.time() - deskd_at < 10
                log(f"the door exited ({deskd.returncode})" + ("; it ran under 10 s (is the port taken?): waiting 60 s" if quick else "; starting it again"))
                if quick:
                    deskd_wait = time.time() + 60
                deskd, deskd_at = start(door_args, name="door"), time.time()
            if docs and docs.poll() is not None and time.time() - docs_at >= 60:
                log("another docs_sync watch holds the lock; trying again" if docs.returncode == 76
                    else f"docs_sync exited ({docs.returncode}); starting it again")
                docs, docs_at = start(docs_args, env, name="docs_sync"), time.time()
            if tw and tw.poll() is not None and time.time() - tw_at >= 60:
                if tw.returncode != 76:            # 76: another bridge holds the lock
                    log(f"twitch_chat exited ({tw.returncode}); starting it again")
                tw, tw_at = start(tw_args, env, name="twitch_chat"), time.time()
            if house is None:                          # waiting out a pause after a crash
                if time.time() >= backoff_until:
                    house = start(["house.py", world], env, name="house")
                continue
            if house.poll() is None:
                continue
            code = house.returncode
            if code == 75:
                log("the house asked to restart on new code")
                house = start(["house.py", world], env, name="house")
                continue
            if code == 76:
                log("another house already runs this world (one house per world); keeper will not start a second. "
                    "Stop the other one, or this keeper")
                backoff_until, house = time.time() + 60, None
                continue
            deaths = [t for t in deaths if time.time() - t < 300] + [time.time()]
            landing = last_landing()
            since = [t for t in deaths if landing and t >= landing["at"]]   # only deaths after the landing count against it
            if landing and len(since) >= 3 and time.time() - landing["at"] < 900:
                revert(landing, f"the house died {len(since)} times in the {int(time.time() - landing['at'])} s after it landed",
                       world)
                deaths = []
                house = start(["house.py", world], env, name="house")
            else:
                log(f"the house exited ({code}); starting it again in 30 s")
                backoff_until, house = time.time() + 30, None
    except KeyboardInterrupt:
        log("keeper: stopping")
    finally:
        stop(house)
        stop(docs)
        stop(tw)
        stop(deskd)


if __name__ == "__main__":
    main()
