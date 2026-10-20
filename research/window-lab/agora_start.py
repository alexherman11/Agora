"""agora_start.py: Agora at logon (Alex, 20 Oct 2026: the home base on the Windows key, and it stays between restarts).

    pythonw agora_start.py            keep Agora up: the desk (keeper.py: house, door on 8794) if it is not answering,
                                      then the home base (hud.py, hidden, on the Windows key and Ctrl+Alt+J); checks
                                      once a minute and starts again whichever has stopped
    python agora_start.py --stop      end this supervisor (the desk and the home base keep running; hud.py --stop ends
                                      the home base, and the keeper is stopped as keeper-runs-detached says)
    python agora_start.py --install   run it at every logon: a shortcut "Agora.lnk" in Alex's Startup folder (no admin;
                                      a scheduled logon task needs administrator rights, refused 20 Oct)
    python agora_start.py --uninstall stop running it at logon (removes the shortcut)

One instance (state/agora_start.pid). It never opens a window: the home base starts hidden and waits for its key.
What it did is in state/agora_start.log.
"""
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

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
    import ctypes
    from ctypes import wintypes as wt
    k = ctypes.windll.kernel32
    h = k.OpenProcess(0x1000, False, int(pid))
    if not h:
        return False
    code = wt.DWORD()
    k.GetExitCodeProcess(h, ctypes.byref(code))
    k.CloseHandle(h)
    return code.value == 259


def door_up():
    try:
        with urllib.request.urlopen(DOOR, timeout=3) as r:
            return r.status == 200
    except OSError:
        return False


def running(script):
    """Is a python process running this script? (WMI, as wm.py finds its browser)"""
    q = f"Get-CimInstance Win32_Process -Filter \"Name like 'python%'\" | Where-Object {{ $_.CommandLine -like '*{script}*' -and $_.ProcessId -ne {os.getpid()} -and $_.ParentProcessId -ne {os.getpid()} }} | Measure-Object | % Count"
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", q], capture_output=True, text=True, timeout=30,
                             creationflags=NO_WINDOW).stdout.strip()
        return int(out or 0) > 0
    except (OSError, ValueError, subprocess.SubprocessError):
        return False


def start(args, cwd):
    subprocess.Popen(args, cwd=str(cwd), creationflags=NO_WINDOW | NEW_GROUP | DETACHED, close_fds=True,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def hud_alive():
    p = STATE / "hud.pid"
    try:
        return alive(int(p.read_text().strip()))
    except (OSError, ValueError):
        return False


def tend():
    if not door_up() and not running("keeper.py"):
        log("the desk is not answering and no keeper runs: starting keeper.py frontier --port 8794")
        start([str(PY), str(NOTATION / "keeper.py"), "frontier", "--port", "8794"], NOTATION)
    if not hud_alive():
        for _ in range(60):                       # the home base paints from the door: wait for it, up to 3 minutes
            if door_up():
                break
            time.sleep(3)
        if not hud_alive():
            log("the home base is not running: starting hud.py (hidden; Windows key or Ctrl+Alt+J)")
            start([str(PYW), str(LAB / "hud.py")], LAB)


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
    try:
        while not OFF.exists():
            try:
                tend()
            except Exception as e:                # one bad check never ends the supervisor
                log(f"check failed: {e!r}")
            for _ in range(60):
                if OFF.exists():
                    break
                time.sleep(1)
    finally:
        log("supervisor ended")
        PIDFILE.unlink(missing_ok=True)
        OFF.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
