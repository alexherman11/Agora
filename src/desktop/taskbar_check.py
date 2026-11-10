"""taskbar_check.py: is the main taskbar there, and what is on top of it? (a5394) 15 Oct 2026.

    python taskbar_check.py          one line: the taskbar's state and the window drawn where it is

The home base hides the taskbar by covering it (hud.py, hide_taskbar=yes), never by hiding the taskbar's own window,
so a home base that is killed leaves nothing to put back. This says which it is now, for a test to read:
    taskbar visible=yes top=taskbar        the taskbar shows
    taskbar visible=yes top=hud            the home base is over it
    taskbar visible=no ...                 something hid the taskbar's window itself (not us; say so)
"""
import ctypes
from ctypes import wintypes as wt

ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
user32 = ctypes.windll.user32
user32.FindWindowW.restype = wt.HWND
user32.FindWindowW.argtypes = [wt.LPCWSTR, wt.LPCWSTR]
user32.WindowFromPoint.restype = wt.HWND
user32.WindowFromPoint.argtypes = [wt.POINT]
user32.GetAncestor.restype = wt.HWND
user32.GetAncestor.argtypes = [wt.HWND, wt.UINT]
user32.IsWindowVisible.argtypes = [wt.HWND]
user32.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
user32.GetClassNameW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
user32.GetWindowTextW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]


def text(fn, h):
    b = ctypes.create_unicode_buffer(256)
    fn(h, b, 256)
    return b.value


def check():
    tray = user32.FindWindowW("Shell_TrayWnd", None)
    if not tray:
        return "taskbar none (no Shell_TrayWnd)"
    r = wt.RECT()
    user32.GetWindowRect(tray, ctypes.byref(r))
    p = wt.POINT((r.left + r.right) // 2, (r.top + r.bottom) // 2)      # the middle of the taskbar's strip
    top = user32.GetAncestor(user32.WindowFromPoint(p), 2)                  # GA_ROOT
    if top == tray:
        who = "taskbar"
    elif text(user32.GetWindowTextW, top) == "Agora home base":
        who = "hud"
    else:
        who = f"other({text(user32.GetClassNameW, top)!r} {text(user32.GetWindowTextW, top)[:40]!r})"
    vis = "yes" if user32.IsWindowVisible(tray) else "no"
    return f"taskbar visible={vis} top={who} rect={r.left},{r.top},{r.right},{r.bottom}"


if __name__ == "__main__":
    print(check())
