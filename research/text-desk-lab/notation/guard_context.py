"""House observations for sandbox admission, never a general host capability.

The fixed main-checkout path is outside managed builders' writable roots.
This is NOT authentication against arbitrary same-user host processes. A copied
file, worker-generated observation or configurable path cannot admit a run.
"""
import json
import os
from pathlib import Path
import time

SCHEMA = "house-guard-context-v1"
MAX_AGE = 5.0
HERE = Path(__file__).resolve().parent


def main_root():
    root = HERE.parents[2]
    if root.parent.name == ".worktrees":
        root = root.parent.parent
    return root


def location():
    return main_root() / "research/text-desk-lab/notation/house-state/frontier/guard-context.json"


def observe():
    """Metadata only: no titles, screen readback, input, wake or process launch."""
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
    return {
        "schema": SCHEMA, "issuer": "house", "issuer_pid": os.getpid(),
        "observed_at": time.time(), "uptime_ms": int(k.GetTickCount64()),
        "notification_result": int(result), "notification_state": state.value,
        "foreground_known": bool(hwnd) and pid.value > 0,
        "input_desktop": name.value if got else "unknown",
        "full_screen": state.value in (2, 3, 7) if result == 0 else None,
        "game": True if result == 0 and state.value == 3 else
                False if clear else None,
        "admitted": bool(clear),
    }


def publish():
    """Called only by the ordinary live main house, never a worker CLI."""
    if HERE.parents[2].resolve() != main_root().resolve():
        return False
    target = location()
    try:
        data = observe()
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
            and data["notification_result"] == 0
            and data["notification_state"] == 5
            and data["foreground_known"] is True
            and data["input_desktop"] == "Default"
            and data["full_screen"] is False and data["game"] is False
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
