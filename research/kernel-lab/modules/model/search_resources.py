"""Fail-closed read-only memory gate; no unload, prewarm or system changes."""
import ctypes as C
from ctypes import wintypes as W


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
