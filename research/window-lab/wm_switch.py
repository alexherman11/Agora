"""wm_switch: the window manager (wm.py) started and stopped by the home base, so Alex never types a command (a6113).
16 Oct 2026. Alex: "why does it say to start it, I'm not going to do that. I want you to facilitate."

The dock icon asks `host wm.start` and `host wm.stop` (host_verbs.py); this is what they do.

    start   wm.py runs as the home base's child (--parent <its pid>, --as/--world/--door the home base's own), its output
            in state/wm.out. While it runs the home base says one row, witnessed:wm {name, state=on, pid}, which the
            dock reads to light its icon and to turn a second click into a stop.
    stop    asks wm.py to stop as its own key does (a `stop` line in state/wm.keys): it puts back what it moved and closes
            what it opened. If it has not ended in 10 s it is ended, and the way below puts things back.

Never leaving a window displaced, whichever part dies:
  - wm.py dies (a crash, a kill): the watcher here sees it end and, if state/wm.json still holds windows, runs
    `wm.py --release-all` (a process of its own, reading only that file), then takes the row away.
  - the home base dies: wm.py sees its parent gone within a second or two and puts everything back itself.
  - both die at once (hud.py --stop ends the whole tree): hud.py --stop, and the next home base as it starts, call
    release_left(), which runs --release-all when the state file holds windows and no host is alive.
A window manager started some other way (by hand, before this) is left alone: start says so, and its own
Ctrl+Alt+Backspace stops it.
"""
import json
import os
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
WM = HERE / "wm.py"
STATE_DIR = HERE / "state"
STATE = STATE_DIR / "wm.json"
KEYS_FILE = STATE_DIR / "wm.keys"
OUT = STATE_DIR / "wm.out"
LENS = "design-review,command-center,doc-editor"      # wm.py's own default windows
NO_WINDOW = 0x08000000


def _alive(pid):
    import ctypes
    from ctypes import wintypes as wt
    k32 = ctypes.windll.kernel32
    h = k32.OpenProcess(0x1000, False, int(pid))
    if not h:
        return False
    code = wt.DWORD()
    k32.GetExitCodeProcess(h, ctypes.byref(code))
    k32.CloseHandle(h)
    return code.value == 259


def _state():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def other_host():
    """The pid of a wm.py host alive now, by its state file, or 0 (as wm.py's own run() asks it)."""
    st = _state() or {}
    pid = st.get("host_pid")
    return pid if pid and st.get("windows") and _alive(pid) else 0


def release_left(say=print):
    """Put back what a window manager left when no host is alive to do it (wm.py --release-all). -> what it said."""
    st = _state()
    if not st or not st.get("windows"):
        return ""
    if st.get("host_pid") and _alive(st["host_pid"]):
        return ""                                     # alive: it puts back its own
    try:
        r = subprocess.run([sys.executable, str(WM), "--release-all"], capture_output=True, text=True, timeout=120,
                           creationflags=NO_WINDOW)
        out = (r.stdout.strip().splitlines() or ["(nothing said)"])[-1]
    except (OSError, subprocess.SubprocessError) as e:
        out = f"release-all failed: {e}"
    say("wm_switch:", out)
    return out


class Switch:
    def __init__(self):
        self.proc, self.watcher, self.world, self.lock = None, None, None, threading.Lock()
        self.last = ""                                # what the last end of a run said

    def on(self):
        return self.proc is not None and self.proc.poll() is None

    def _say(self, hud, rows):
        """witnessed:wm, and a nudge to the door so the dock repaints now."""
        try:
            import witnessed
            (witnessed.write(self.world, "wm", rows, by="hud") if rows else witnessed.clear(self.world, "wm"))
        except Exception as e:
            print("wm_switch: witnessed:", e, flush=True)
        try:
            urllib.request.urlopen(urllib.request.Request(hud.door.rstrip("/") + "/door/witnessed", data=b"{}",
                                                          method="POST"), timeout=2).read()
        except (OSError, AttributeError):
            pass

    def start(self, hud, lenses=""):
        with self.lock:
            if self.on():
                return "the window manager is on already (the icon again, or Ctrl+Alt+Backspace, puts everything back)"
            other = other_host()
            if other:
                raise RuntimeError(f"a window manager started another way is running (process {other}); "
                                   "Ctrl+Alt+Backspace stops it")
            release_left()                            # a crash before this one: back first
            self.world = hud.a.world
            STATE_DIR.mkdir(parents=True, exist_ok=True)
            KEYS_FILE.unlink(missing_ok=True)         # an old ask must not stop the new host
            out = open(OUT, "a", encoding="utf-8")
            out.write(f"--- {time.strftime('%Y-%m-%d %H:%M:%S')} started by the home base {os.getpid()}\n")
            out.flush()
            self.proc = subprocess.Popen(
                [sys.executable, "-u", str(WM), "--open", lenses or LENS, "--as", hud.a.who, "--world", hud.a.world,
                 "--door", hud.door, "--parent", str(os.getpid())],
                stdout=out, stderr=subprocess.STDOUT, creationflags=NO_WINDOW)
            out.close()
            self._say(hud, [{"name": "wm", "state": "on", "pid": self.proc.pid}])
            self.watcher = threading.Thread(target=self._watch, args=(hud, self.proc), daemon=True)
            self.watcher.start()
            return f"started the window manager (process {self.proc.pid})"

    def _watch(self, hud, proc):
        proc.wait()
        said = release_left()
        self.last = f"the window manager ended (code {proc.returncode})" + (f"; {said}" if said else "")
        print("wm_switch:", self.last, flush=True)
        with self.lock:
            if self.proc is proc:
                self.proc = None
        self._say(hud, [])

    def stop(self, hud, wait=10.0):
        with self.lock:
            proc, watcher = self.proc, self.watcher
        if proc is None or proc.poll() is not None:
            said = release_left()
            self.world = self.world or hud.a.world
            self._say(hud, [])
            return "the window manager was off" + (f"; put back what one left: {said}" if said else "")
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        KEYS_FILE.write_text("stop\n", encoding="utf-8")
        try:
            proc.wait(wait)
        except subprocess.TimeoutExpired:
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
        if watcher:
            watcher.join(150)                         # it runs release-all when anything was left
        return "stopped the window manager: everything is back where it was"


SWITCH = Switch()
