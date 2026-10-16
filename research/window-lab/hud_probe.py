"""hud_probe.py: what the running home base is, from outside (a5736). Read only; it changes nothing.

    python hud_probe.py          the home base window: its process, when that started, its rect, shown or not,
                                 the monitor and work area it sits on, and the scale

Answers 'is he running old code?': compare the start time with the landing (git log) of the change in question.
"""
import ctypes
import datetime
from ctypes import wintypes as wt

ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
user32, kernel32, shcore = ctypes.windll.user32, ctypes.windll.kernel32, ctypes.windll.shcore
WNDENUMPROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)


class MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", wt.DWORD), ("rcMonitor", wt.RECT), ("rcWork", wt.RECT), ("dwFlags", wt.DWORD)]


def started(pid):
    h = kernel32.OpenProcess(0x1000, False, pid)
    if not h:
        return None, ""
    c, e, k, u = (wt.FILETIME() for _ in range(4))
    kernel32.GetProcessTimes(h, ctypes.byref(c), ctypes.byref(e), ctypes.byref(k), ctypes.byref(u))
    buf, size = ctypes.create_unicode_buffer(520), wt.DWORD(520)
    kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size))
    kernel32.CloseHandle(h)
    t = (c.dwHighDateTime << 32 | c.dwLowDateTime) / 1e7 - 11644473600
    return datetime.datetime.fromtimestamp(t).astimezone(), buf.value


def main():
    found = []

    def each(h, _):
        n = user32.GetWindowTextLengthW(h)
        b = ctypes.create_unicode_buffer(n + 1)
        user32.GetWindowTextW(h, b, n + 1)
        if b.value == "Agora home base":
            found.append(h)
        return True

    user32.EnumWindows(WNDENUMPROC(each), 0)
    print("now", datetime.datetime.now().astimezone().isoformat(timespec="seconds"))
    if not found:
        print("no home base window")
    for h in found:
        pid = wt.DWORD()
        user32.GetWindowThreadProcessId(h, ctypes.byref(pid))
        t, exe = started(pid.value)
        r = wt.RECT()
        user32.GetWindowRect(h, ctypes.byref(r))
        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(mi)
        m = user32.MonitorFromWindow(h, 2)
        user32.GetMonitorInfoW(m, ctypes.byref(mi))
        sc = ctypes.c_uint()
        shcore.GetScaleFactorForMonitor(m, ctypes.byref(sc))
        print(f"hwnd {h} pid {pid.value} started {t.isoformat(timespec='seconds') if t else '?'} exe {exe}")
        print(f"  rect {r.left},{r.top} {r.right - r.left}x{r.bottom - r.top} visible={bool(user32.IsWindowVisible(h))}")
        print(f"  monitor {mi.rcMonitor.right - mi.rcMonitor.left}x{mi.rcMonitor.bottom - mi.rcMonitor.top}"
              f" work {mi.rcWork.right - mi.rcWork.left}x{mi.rcWork.bottom - mi.rcWork.top} scale {sc.value}%")


if __name__ == "__main__":
    main()
