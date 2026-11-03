"""Fail-closed read-only memory gate; no unload, prewarm or system changes."""
import ctypes as C
from ctypes import wintypes as W


def idle_milliseconds():
    """Read-only last-input telemetry; unavailable/ambiguous values abstain."""
    class LASTINPUTINFO(C.Structure):
        _fields_ = [("size", W.UINT), ("tick", W.DWORD)]
    k = C.WinDLL("kernel32", use_last_error=True)
    u = C.WinDLL("user32", use_last_error=True)
    u.GetLastInputInfo.argtypes = [C.POINTER(LASTINPUTINFO)]
    u.GetLastInputInfo.restype = W.BOOL
    k.GetTickCount64.restype = C.c_ulonglong
    info = LASTINPUTINFO(C.sizeof(LASTINPUTINFO), 0)
    if not u.GetLastInputInfo(C.byref(info)):
        raise OSError("last-input telemetry unavailable")
    tick = k.GetTickCount64()
    if not tick:
        raise OSError("uptime telemetry unavailable")
    elapsed = ((tick & 0xffffffff) - info.tick) & 0xffffffff
    if elapsed > 24 * 60 * 60 * 1000:
        raise OSError("last-input telemetry ambiguous")
    return elapsed


def require_idle():
    try:
        elapsed = idle_milliseconds()
        if not isinstance(elapsed, int) or isinstance(elapsed, bool) or elapsed < 0:
            raise ValueError("invalid idle telemetry")
        if elapsed < 30000:
            raise ValueError("desktop has not been idle for 30 seconds")
    except Exception as exc:
        raise ValueError("semantic admission held: " + str(exc)) from exc


def reason(selected, loaded):
    class MEMORYSTATUSEX(C.Structure):
        _fields_ = [("length", W.DWORD), ("load", W.DWORD)] + [
            (n, C.c_ulonglong) for n in ("physical", "available", "pagefile", "pagefree",
                                        "virtual", "virtualfree", "extended")]

    memory = MEMORYSTATUSEX()
    memory.length = C.sizeof(memory)
    if not C.WinDLL("kernel32", use_last_error=True).GlobalMemoryStatusEx(C.byref(memory)):
        return "memory inspection unavailable"
    names = {m.get("name") for m in loaded.get("models", [])}
    if names and selected not in names:
        return "another local model is resident"
    required = (2 if selected in names else 8) * 1024**3
    if memory.available < required:
        return "not enough free memory for a safe local search"
    return None
