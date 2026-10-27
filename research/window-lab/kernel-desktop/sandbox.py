"""sandbox: a private, hidden copy of Alex's desktop world, for trials that must not touch his screen.

    python sandbox.py fresh [--name claude-terminal]      copy state/world to state/world-<name> (replacing an old copy)
    python sandbox.py run   [--name claude-terminal] [--port 8830]
    python sandbox.py stop  [--name claude-terminal]      the sandbox and its module processes (taskkill /T)

The copy keeps every thing, word and lens of the live world, but before any module starts it rewrites each module's
`run` so the module runs --headless (windows in memory, no media session, fixed readings, no window manager on the real
desktop), and turns off the modules that would reach outside (model, summarize: live model calls). No widget overlays.
Nothing appears on screen. The live world (state/world, door 8810) is only read, once, when copying.
"""
import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "kernel-lab"))
sys.path.insert(0, str(HERE))

HEADLESS = {"window", "guy", "system", "media", "wm"}
OFF = {"model", "summarize"}


def world_dir(name):
    return HERE / "state" / f"world-{name}"


def fresh(name):
    src, dst = HERE / "state" / "world", world_dir(name)
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src / "log", dst / "log")
    (dst / "keep").mkdir(parents=True)
    for f in ("accounts.json", "seal.key", "sessions.json"):
        if (src / "keep" / f).exists():
            shutil.copy2(src / "keep" / f, dst / "keep" / f)
    print(f"sandbox: copied the live world to {dst.name}")


def run(name, port):
    import kdesk
    from kernel.kernel import Tx
    world = world_dir(name)
    k, srv, host, entry = kdesk.start(world, port, modules=False, headless=True)
    with k.lock:
        tx = Tx(k)
        tx.part("install", None, "install")
        n = 0
        for m in k.things("module"):
            nm, argv = k.state.get(m, "name"), list(k.state.get(m, "run") or [])
            if nm in OFF and k.state.get(m, "on"):
                tx.set(m, "on", False); n += 1
            elif nm in HEADLESS and "--headless" not in argv:
                tx.set(m, "run", argv + ["--headless"]); n += 1
            elif nm not in HEADLESS | OFF | {"theme", "board", "files"} and k.state.get(m, "on"):
                tx.set(m, "on", False); n += 1           # a module this sandbox does not know: off, to be safe
        if n:
            k._commit(tx, by="kernel", words="sandbox: modules headless, outside-reaching modules off")
    host.reconcile()
    (world / "keep" / "sandbox.pid").write_text(str(os.getpid()))
    print(f"sandbox: {k.name(k.place)} (copy) on http://127.0.0.1:{port}, hidden; {len(k.log.records)} records", flush=True)
    try:
        while True:
            time.sleep(2)
            host.reconcile()
    except KeyboardInterrupt:
        pass
    finally:
        host.stop_all()
        srv.shutdown()
        srv.server_close()


def stop(name):
    pid = world_dir(name) / "keep" / "sandbox.pid"
    if not pid.exists():
        return print("sandbox: not running (no pid file)")
    out = subprocess.run(["taskkill", "/PID", pid.read_text().strip(), "/T", "/F"], capture_output=True, text=True)
    pid.unlink()
    print("sandbox: stopped" if out.returncode == 0 else "sandbox: " + (out.stderr or out.stdout).strip())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["fresh", "run", "stop"])
    ap.add_argument("--name", default="claude-terminal")
    ap.add_argument("--port", type=int, default=8830)
    a = ap.parse_args()
    {"fresh": lambda: fresh(a.name), "run": lambda: run(a.name, a.port), "stop": lambda: stop(a.name)}[a.what]()
