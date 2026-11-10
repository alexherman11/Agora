"""press.py: press a key or click a point on Alex's real screen, as a person would (a5592: trying the home base's music
buttons on his PC). 15 Oct 2026.

    python press.py home                 Ctrl+Alt+J: show or hide the home base
    python press.py esc                  Esc: put the home base away
    python press.py click x y [x y ...]  a left click at real pixel x, y (DPI aware), each point 0.4 s after the last;
                                         the cursor goes back where it was (two prevs in a row skip back, where one
                                         late in a song only restarts it)

Plain SendInput, nothing injected into any program. Say on the card what will appear before using it.
"""
import ctypes
import sys
import time
from ctypes import wintypes as wt

user32 = ctypes.windll.user32
user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))


class _KI(ctypes.Structure):
    _fields_ = [("wVk", wt.WORD), ("wScan", wt.WORD), ("dwFlags", wt.DWORD), ("time", wt.DWORD),
                ("dwExtraInfo", ctypes.c_size_t)]


class _MI(ctypes.Structure):
    _fields_ = [("dx", wt.LONG), ("dy", wt.LONG), ("mouseData", wt.DWORD), ("dwFlags", wt.DWORD), ("time", wt.DWORD),
                ("dwExtraInfo", ctypes.c_size_t)]


class _IN(ctypes.Structure):
    class _U(ctypes.Union):
        _fields_ = [("ki", _KI), ("mi", _MI), ("pad", ctypes.c_byte * 32)]
    _anonymous_ = ("u",)
    _fields_ = [("type", wt.DWORD), ("u", _U)]


def send(*events):
    arr = (_IN * len(events))(*events)
    return user32.SendInput(len(events), arr, ctypes.sizeof(_IN)) == len(events)


def key(vk, up=False):
    e = _IN(type=1)
    e.ki = _KI(vk, 0, 0x2 if up else 0, 0, 0)
    return e


def chord(*vks):
    return send(*[key(v) for v in vks], *[key(v, True) for v in reversed(vks)])


def click(x, y):
    was = wt.POINT()
    user32.GetCursorPos(ctypes.byref(was))
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.05)
    down, up = _IN(type=0), _IN(type=0)
    down.mi = _MI(0, 0, 0, 0x2, 0, 0)                                  # LEFTDOWN
    up.mi = _MI(0, 0, 0, 0x4, 0, 0)                                    # LEFTUP
    ok = send(down, up)
    time.sleep(0.05)
    user32.SetCursorPos(was.x, was.y)
    return ok


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else ""
    if what == "home":
        print(chord(0x11, 0x12, ord("J")))                             # Ctrl, Alt, J
    elif what == "esc":
        print(chord(0x1B))
    elif what == "click" and len(sys.argv) >= 4 and len(sys.argv) % 2 == 0:
        pts = sys.argv[2:]                                             # several points: clicked 0.4 s apart
        for i in range(0, len(pts), 2):
            print(click(pts[i], pts[i + 1]))
            time.sleep(0.4)
    else:
        sys.exit(__doc__)
