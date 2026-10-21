"""agora_start.py: Agora at logon (Alex, 20 Oct 2026: the home base on the Windows key, and it stays between restarts).

    pythonw agora_start.py            keep Agora up: the desk (keeper.py: house, door on 8794) if it is not answering,
                                      then the home base (hud.py, hidden, on the Windows key and Ctrl+Alt+J); checks
                                      once a minute; absence/unknown checks retry in five seconds
    python agora_start.py --stop      end this supervisor (the desk and the home base keep running; hud.py --stop ends
                                      the home base, and the keeper is stopped as keeper-runs-detached says)
    python agora_start.py --install   run it at every logon: a shortcut "Agora.lnk" in Alex's Startup folder (no admin;
                                      a scheduled logon task needs administrator rights, refused 20 Oct)
    python agora_start.py --uninstall stop running it at logon (removes the shortcut)

One instance (state/agora_start.pid). It never opens a window: the home base starts hidden and waits for its key.
What it did is in state/agora_start.log.
hud.pid is never deleted here. HUD starts require two confirmed misses, a live
keeper and an answering backend. Inventory failures and keeper restarts defer.
Duplicate hosts are reconciled by hud_lifecycle.py, by verified process identity.
"""
import os
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from hud_lifecycle import Monitor, Scope, Windows, inventory, read_pid, with_health

LAB = Path(__file__).resolve().parent
ROOT = LAB.parents[1]
PY = ROOT / ".venv" / "Scripts" / "python.exe"
PYW = ROOT / ".venv" / "Scripts" / "pythonw.exe"
NOTATION = ROOT / "research" / "text-desk-lab" / "notation"
STATE = LAB / "state"
PIDFILE, LOG, OFF = STATE / "agora_start.pid", STATE / "agora_start.log", STATE / "agora_start.off"
DOOR = "http://127.0.0.1:8794/door/status"
NO_WINDOW, NEW_GROUP, DETACHED = 0x08000000, 0x00000200, 0x00000008


def log(msg):
    STATE.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")


def alive(pid):
    return Windows().identity(int(pid)) is not None


def door_up():
    try:
        with urllib.request.urlopen(DOOR, timeout=3) as r:
            return r.status == 200 and json.load(r).get("up") is True
    except (OSError, ValueError):
        return False


def start(args, cwd):
    subprocess.Popen(args, cwd=str(cwd), creationflags=NO_WINDOW | NEW_GROUP | DETACHED, close_fds=True,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


SCOPE = Scope(str(LAB / "hud.py"), str(NOTATION / "keeper.py"))


def tend(monitor, native):
    processes = with_health(inventory(native), SCOPE, native)
    def launch(which):
        if which == "keeper":
            start([str(PY), str(NOTATION / "keeper.py"), "frontier", "--port", "8794"], NOTATION)
        else:
            start([str(PYW), str(LAB / "hud.py")], LAB)
    return monitor.tick(processes, read_pid(STATE / "hud.pid"), door_up(), time.monotonic(),
                        start=launch, end=native.end, healthy=native.healthy, log=log)


STARTUP = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup" / "Agora.lnk"


def install():
    ps = ("$s = (New-Object -ComObject WScript.Shell).CreateShortcut('%s'); $s.TargetPath = '%s'; "
          "$s.Arguments = '\"%s\"'; $s.WorkingDirectory = '%s'; $s.Description = 'Agora: the desk and the home base'; $s.Save()"
          % (STARTUP, PYW, LAB / "agora_start.py", LAB))
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True)
    print(f"installed: {STARTUP}" if STARTUP.exists() else (r.stderr or r.stdout).strip())


def main():
    a = sys.argv[1:]
    STATE.mkdir(parents=True, exist_ok=True)
    if "--install" in a:
        return install()
    if "--uninstall" in a:
        STARTUP.unlink(missing_ok=True)
        return print("removed", STARTUP)
    old = PIDFILE.read_text().strip() if PIDFILE.exists() else ""
    if "--stop" in a:
        OFF.write_text("stop")
        return print("asked the supervisor to end (within a minute)" if old.isdigit() and alive(old) else "not running")
    if old.isdigit() and alive(old):
        return print("already running as", old)
    OFF.unlink(missing_ok=True)
    PIDFILE.write_text(str(os.getpid()))
    log(f"supervisor started (pid {os.getpid()})")
    monitor, native = Monitor(SCOPE), Windows()
    try:
        while not OFF.exists():
            delay = 60
            try:
                delay = tend(monitor, native)
            except Exception as e:                # one bad check never ends the supervisor
                monitor.hud_misses.first = monitor.keeper_misses.first = None
                delay = 5
                log(f"check failed: {e!r}")
            for _ in range(delay):
                if OFF.exists():
                    break
                time.sleep(1)
    finally:
        log("supervisor ended")
        PIDFILE.unlink(missing_ok=True)
        OFF.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
