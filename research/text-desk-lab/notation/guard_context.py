"""House observations for sandbox admission, never a general host capability.

The fixed main-checkout path is outside managed builders' writable roots.
This is NOT authentication against arbitrary same-user host processes. A copied
file, worker-generated observation or configurable path cannot admit a run.
"""
import json
import ntpath
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

SCHEMA = "house-guard-context-v2"
MAX_AGE = 5.0
HERE = Path(__file__).resolve().parent


class Publisher:
    """House-owned sampler; no world reads, resident wakes or OS wake timers.

    Sample every second, or immediately after a slower observation. A slow
    main loop cannot hold this up. Sampling failures leave the reader fail-closed.
    The house supplies its current policy without sharing a mutable world.
    """
    def __init__(self):
        self.nongame = ""
        self.stopped = threading.Event()
        self.thread = threading.Thread(target=self.run, name="guard-context", daemon=True)

    def start(self):
        self.thread.start()

    def update(self, nongame):
        self.nongame = nongame

    def run(self):
        while not self.stopped.is_set():
            started = time.monotonic()
            try:
                publish(self.nongame)
            except Exception as exc:
                # Never retain exception text that could contain host details.
                print(f"house: guard context unavailable: {type(exc).__name__}", flush=True)
            if self.stopped.wait(max(0.0, 1.0 - (time.monotonic() - started))):
                break

    def close(self):
        self.stopped.set()
        # HUD identity's existing CIM probe has a three-second timeout. Do not
        # hold house shutdown indefinitely if a native probe stalls.
        self.thread.join(timeout=4.0)


def main_root():
    root = HERE.parents[2]
    if root.parent.name == ".worktrees":
        root = root.parent.parent
    return root


def location():
    return main_root() / "research/text-desk-lab/notation/house-state/frontier/guard-context.json"


def executable_name(pid):
    """Read only the image name of this foreground PID; no title/argv/content.

    The world may use a basename for its non-game rule; HUD identity needs more.
    """
    import ctypes as c
    from ctypes import wintypes as w
    if not pid:
        return "unknown"
    k = c.WinDLL("kernel32", use_last_error=True)
    k.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
    k.OpenProcess.restype = w.HANDLE
    k.QueryFullProcessImageNameW.argtypes = [
        w.HANDLE, w.DWORD, w.LPWSTR, c.POINTER(w.DWORD)]
    k.QueryFullProcessImageNameW.restype = w.BOOL
    k.CloseHandle.argtypes = [w.HANDLE]
    handle = k.OpenProcess(0x1000, False, pid)
    if not handle:
        return "unknown"
    try:
        size, image = w.DWORD(32768), c.create_unicode_buffer(32768)
        if not k.QueryFullProcessImageNameW(handle, 0, image, c.byref(size)):
            return "unknown"
        return ntpath.basename(image.value).lower() or "unknown"
    finally:
        k.CloseHandle(handle)


def nongame_names(value):
    """Only exact basenames; malformed policy grants nothing."""
    if not isinstance(value, str) or len(value) > 1024:
        return []
    names = [part.strip().lower() for part in value.split(",") if part.strip()]
    if any(not name.endswith(".exe") or any(c in name for c in "/\\:*?\"<>|")
           or name == "unknown" for name in names):
        return []
    return sorted(set(names))


def foreground_is_hud(pid):
    """Scoped read-only identity/argv query; never enumerate or trust hud.pid."""
    sys.path.insert(0, str(HERE.parents[1] / "window-lab"))
    from hud_lifecycle import Windows, Scope, Process, path_key
    try:
        if type(pid) is not int or pid <= 0:
            return False
        native = Windows()
        before = native.identity(pid)
        if before is None:
            return False
        # Numeric PID only; no world text is interpolated into shell code.
        command = (
            "$ErrorActionPreference='Stop'; "
            f"$p=Get-CimInstance Win32_Process -Filter 'ProcessId={pid}'; "
            "[PSCustomObject]@{pid=$p.ProcessId; exe=$p.ExecutablePath; "
            "created=$p.CreationDate.ToUniversalTime().ToFileTimeUtc(); "
            "command=$p.CommandLine} | ConvertTo-Json -Compress")
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True, text=True, timeout=3, creationflags=0x08000000)
        if result.returncode:
            return False
        row = json.loads(result.stdout)
        if (row["pid"] != pid or path_key(row["exe"]) != before[1]
                or abs(int(row["created"]) - before[0]) >= 10):
            return False
        # Same native birth around the scoped command read; CIM creation is
        # microsecond precision, as in the existing lifecycle inventory.
        if native.identity(pid) != before:
            return False
        proc = Process(pid, 0, before[0], before[1], native.argv(row["command"]))
        scope = Scope(str(main_root() / "research/window-lab/hud.py"), "")
        return bool(scope.hosts([proc]))
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError):
        return False


def policy_clear(data):
    """JEFF's world rule: known non-game full-screen foreground may admit."""
    exe = data.get("foreground_exe", "unknown")
    known = (isinstance(exe, str) and bool(exe) and exe != "unknown"
             and ntpath.basename(exe) == exe)
    if not (data.get("notification_result") == 0 and known
            and data.get("foreground_known") is True
            and data.get("input_desktop") == "Default"):
        return False
    state = data.get("notification_state")
    if state == 5:
        return data.get("full_screen") is False and data.get("game") is False
    if state != 2 or data.get("full_screen") is not True or data.get("game") is not None:
        return False
    names = data.get("guard_nongame")
    if (not isinstance(names, list) or not all(isinstance(n, str) for n in names)
            or names != nongame_names(",".join(names))):
        return False
    if exe.lower() not in names:
        return False
    # The world grants the HUD's pythonw, not arbitrary Python programs.
    return exe.lower() != "pythonw.exe" or data.get("foreground_hud") is True


def observe(nongame=""):
    """Read-only metadata; a scoped hidden CIM helper only for listed HUD."""
    import ctypes as c
    from ctypes import wintypes as w
    u = c.WinDLL("user32", use_last_error=True)
    k = c.WinDLL("kernel32", use_last_error=True)
    shell = c.WinDLL("shell32")
    u.GetForegroundWindow.restype = w.HWND
    u.OpenInputDesktop.argtypes = [w.DWORD, w.BOOL, w.DWORD]
    u.OpenInputDesktop.restype = w.HANDLE
    u.CloseDesktop.argtypes = [w.HANDLE]
    u.GetUserObjectInformationW.argtypes = [
        w.HANDLE, c.c_int, c.c_void_p, w.DWORD, c.POINTER(w.DWORD)]
    u.GetWindowThreadProcessId.argtypes = [w.HWND, c.POINTER(w.DWORD)]
    k.GetTickCount64.restype = c.c_ulonglong
    observed_at, uptime_ms = time.time(), int(k.GetTickCount64())
    state, pid, needed = w.DWORD(), w.DWORD(), w.DWORD()
    result = shell.SHQueryUserNotificationState(c.byref(state))
    hwnd = u.GetForegroundWindow()
    if hwnd:
        u.GetWindowThreadProcessId(hwnd, c.byref(pid))
    desktop = u.OpenInputDesktop(0, False, 1)
    name = c.create_unicode_buffer(256)
    try:
        got = desktop and u.GetUserObjectInformationW(
            desktop, 2, name, c.sizeof(name), c.byref(needed))
    finally:
        if desktop:
            u.CloseDesktop(desktop)
    clear = result == 0 and state.value == 5 and bool(hwnd) and pid.value > 0
    clear = clear and bool(got) and name.value.lower() == "default"
    exe = executable_name(pid.value)
    names = nongame_names(nongame)
    hud = (state.value == 2 and exe == "pythonw.exe" and exe in names
           and foreground_is_hud(pid.value))
    current_pid = w.DWORD()
    current_hwnd = u.GetForegroundWindow()
    if current_hwnd:
        u.GetWindowThreadProcessId(current_hwnd, c.byref(current_pid))
    # A HUD metadata query can wait up to three seconds. Do not timestamp an
    # old observation as fresh or admit across a game/lock/desktop transition.
    final_state = w.DWORD()
    final_result = shell.SHQueryUserNotificationState(c.byref(final_state))
    final_desktop = u.OpenInputDesktop(0, False, 1)
    final_name = c.create_unicode_buffer(256)
    try:
        final_got = final_desktop and u.GetUserObjectInformationW(
            final_desktop, 2, final_name, c.sizeof(final_name), c.byref(needed))
    finally:
        if final_desktop:
            u.CloseDesktop(final_desktop)
    if (current_hwnd != hwnd or current_pid.value != pid.value
            or final_result != result or final_state.value != state.value
            or not final_got or final_name.value != name.value):
        exe = "unknown"
        clear = False
        hud = False
    data = {
        "schema": SCHEMA, "issuer": "house", "issuer_pid": os.getpid(),
        "observed_at": observed_at, "uptime_ms": uptime_ms,
        "notification_result": int(result), "notification_state": state.value,
        "foreground_known": bool(hwnd) and pid.value > 0,
        "foreground_exe": exe,
        "foreground_hud": bool(hud), "guard_nongame": names,
        "input_desktop": name.value if got else "unknown",
        "full_screen": state.value in (2, 3, 7) if result == 0 else None,
        "game": True if result == 0 and state.value == 3 else
                False if clear else None,
    }
    data["admitted"] = policy_clear(data)
    return data


def publish(nongame=""):
    """Called only by the ordinary live main house, never a worker CLI."""
    if HERE.parents[2].resolve() != main_root().resolve():
        return False
    target = location()
    try:
        data = observe(nongame)
    except Exception as exc:
        data = {"schema": SCHEMA, "issuer": "house", "issuer_pid": os.getpid(),
                "observed_at": time.time(), "admitted": False,
                "error": type(exc).__name__}
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(target.name + ".pending")
    temp.write_text(json.dumps(data), encoding="utf-8")
    os.replace(temp, target)
    return True


def validate(data, now, uptime_ms):
    """Fail closed on unknown, stale, future, rebooted or inconsistent context."""
    try:
        age = now - float(data["observed_at"])
        tick_age = (uptime_ms - int(data["uptime_ms"])) / 1000
        valid = (
            data["schema"] == SCHEMA and data["issuer"] == "house"
            and type(data["issuer_pid"]) is int and data["issuer_pid"] > 0
            and 0 <= age <= MAX_AGE and 0 <= tick_age <= MAX_AGE
            and abs(age - tick_age) <= 1
            and policy_clear(data)
            and data["admitted"] is True)
    except (KeyError, TypeError, ValueError, OverflowError):
        valid = False
    return bool(valid)


def read():
    """No caller-selected path or worker fallback. Never writes the attestation."""
    import ctypes as c
    k = c.WinDLL("kernel32")
    k.GetTickCount64.restype = c.c_ulonglong
    try:
        with location().open("rb") as stream:
            payload = stream.read(8193)
        if len(payload) > 8192:
            raise ValueError("oversized observation")
        data = json.loads(payload)
    except (OSError, ValueError):
        return {"admitted": False, "reason": "house observation missing/unreadable"}
    if not validate(data, time.time(), int(k.GetTickCount64())):
        return {"admitted": False, "reason": "house observation stale/unknown/unsafe",
                "observation": data}
    return {"admitted": True, "observation": data,
            "limit": "managed-sandbox read-only house snapshot; not continuous screen monitoring"}
