"""Read-only resource/idle gate for synthetic broker smoke calls. No inference."""
import ctypes as C
from ctypes import wintypes as W
import http.client
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/window-lab/kernel-desktop"))
from gaming_gate import reasons


class LASTINPUTINFO(C.Structure):
    _fields_ = [("size", W.UINT), ("tick", W.DWORD)]


class MEMORYSTATUSEX(C.Structure):
    _fields_ = [("length", W.DWORD), ("load", W.DWORD)] + [
        (n, C.c_ulonglong) for n in ("physical", "available", "pagefile", "pagefree",
                                    "virtual", "virtualfree", "extended")]


def readiness():
    k, u = C.WinDLL("kernel32", use_last_error=True), C.WinDLL("user32", use_last_error=True)
    last = LASTINPUTINFO(C.sizeof(LASTINPUTINFO), 0)
    memory = MEMORYSTATUSEX()
    memory.length = C.sizeof(memory)
    if not u.GetLastInputInfo(C.byref(last)) or not k.GlobalMemoryStatusEx(C.byref(memory)):
        return dict(safe=False, reason="Idle or memory inspection unavailable")
    idle = ((k.GetTickCount() & 0xffffffff) - last.tick) & 0xffffffff
    gate = reasons()
    conn = http.client.HTTPConnection("127.0.0.1", 11434, timeout=1)
    try:
        conn.request("GET", "/api/ps")
        response = conn.getresponse()
        if response.status != 200:
            return dict(safe=False, reason="Local model metadata unavailable")
        models = json.loads(response.read(65536)).get("models", [])
    finally:
        conn.close()
    # Cold loading another model alongside a resident model is not this probe's scope.
    loaded = [m.get("name") for m in models]
    safe = not gate and idle >= 30000 and memory.available >= 8 * 1024**3 and not loaded
    return dict(safe=safe, gaming_reasons=gate, idle_seconds=idle // 1000,
                available_GiB=round(memory.available / 1024**3, 1), loaded=loaded,
                checked_at=time.time(),
                boundary="One cold synthetic call only; no prewarm, model switch, unload or queue.")


if __name__ == "__main__":
    print(json.dumps(readiness()))
