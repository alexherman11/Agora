"""Read-only foreground metadata; no title, content, input or admission override."""
import ctypes
import json
from pathlib import Path
import sys
from ctypes import wintypes as w

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sandbox_window as s

k, u = s.k32, s.u32
k.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
k.OpenProcess.restype = w.HANDLE
k.QueryFullProcessImageNameW.argtypes = [
    w.HANDLE, w.DWORD, w.LPWSTR, ctypes.POINTER(w.DWORD)]
u.GetWindowRect.argtypes = [w.HWND, ctypes.POINTER(w.RECT)]
u.GetClassNameW.argtypes = [w.HWND, w.LPWSTR, ctypes.c_int]
a = s.alex()
h = a["foreground"]
r = w.RECT()
ok = u.GetWindowRect(h, ctypes.byref(r))
c = ctypes.create_unicode_buffer(256)
u.GetClassNameW(h, c, 256)
print(json.dumps({
    "scope": "read-only foreground metadata after refused preflight; no titles/content",
    "hwnd": h, "pid": s.owner(h), "exe_basename": s.exe(s.owner(h)),
    "class": c.value,
    "bounds": [r.left, r.top, r.right, r.bottom] if ok else None,
    "input_desktop": a["input desktop"],
    "causal_limit": "SHQueryUserNotificationState does not identify which window caused full-screen state",
}))
