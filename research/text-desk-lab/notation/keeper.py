"""keeper: keeps the house and deskd running on the current code, and is the way back when a landing breaks them.

    python keeper.py [world] [--port 8794]          default world: frontier

It is meant to change rarely. It:
  - runs deskd on the port and the house for the world, with DESKD pointing the house at that deskd (one host) and
    HOUSE_KEEPER=1 so the house may ask to be restarted;
  - restarts deskd whenever git HEAD moves (a landing, or anyone's commit), so the painter and the residents run the
    code that is there; the painter reloads itself when it sees the new version;
  - restarts the house at once when it exits 75 (it asked, after a landing changed Python); restarts it with a
    pause when it dies otherwise;
  - if the house dies 3 times within 5 minutes of a landing (a commit whose subject begins "land "), reverts that
    landing and says so in its log: the one part of live building that does not depend on the code it protects.
Log: house-state/keeper.log.
"""
import os
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
    deskd, house = start(["deskd.py", port], name="deskd"), None
    time.sleep(2)
    house = start(["house.py", world], env, name="house")
    log(f"keeper: world {world}, deskd on {port}, HEAD {head[:7]}")
    deaths, backoff_until, deskd_at, deskd_wait = [], 0.0, time.time(), 0.0
    try:
        while True:
            time.sleep(2)
            now_head = git("rev-parse", "HEAD")
            if now_head and now_head != head:
                log(f"HEAD moved {head[:7]} -> {now_head[:7]} ({git('log', '-1', '--format=%s')[:80]}); restarting deskd")
                head = now_head
                stop(deskd)
                deskd, deskd_at = start(["deskd.py", port], name="deskd"), time.time()
            elif deskd.poll() is not None and time.time() >= deskd_wait:
                quick = time.time() - deskd_at < 10
                log(f"deskd exited ({deskd.returncode})" + ("; it ran under 10 s (is the port taken?): waiting 60 s" if quick else "; starting it again"))
                if quick:
                    deskd_wait = time.time() + 60
                deskd, deskd_at = start(["deskd.py", port], name="deskd"), time.time()
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
            subject = git("log", "-1", "--format=%s")
            landed_at = int(git("log", "-1", "--format=%ct") or 0)
            since = [t for t in deaths if t >= landed_at]       # only deaths after the landing count against it
            if len(since) >= 3 and subject.startswith("land ") and time.time() - landed_at < 900:
                log(f"the house died {len(since)} times since '{subject[:80]}'; reverting that landing")
                r = subprocess.run(["git", "revert", "-m", "1", "--no-edit", "HEAD"], cwd=REPO, capture_output=True, text=True)
                log("revert: " + ((r.stdout + r.stderr).strip()[-300:] or "ok"))
                deaths = []
                house = start(["house.py", world], env, name="house")
            else:
                log(f"the house exited ({code}); starting it again in 30 s")
                backoff_until, house = time.time() + 30, None
    except KeyboardInterrupt:
        log("keeper: stopping")
    finally:
        stop(house)
        stop(deskd)


if __name__ == "__main__":
    main()
