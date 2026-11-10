"""press: a real mouse press or drag on the desktop, the way Alex's hand would make it (for demos and evidence).

    python press.py click <x> <y>                  a left click at real pixels, then the cursor goes back where it was
    python press.py drag <x1> <y1> <x2> <y2>       press at one point, move in steps, let go at the other
    python press.py title <words>                  the box of the window whose title is exactly <words>

It moves the real cursor for a moment, so say what it will do before it runs. It never types.
"""
import ctypes
import sys
import time
from ctypes import wintypes as wt

user32 = ctypes.windll.user32
user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
DOWN, UP = 0x0002, 0x0004


def at(x, y):
    user32.SetCursorPos(int(x), int(y))


def click(x, y):
    old = wt.POINT()
    user32.GetCursorPos(ctypes.byref(old))
    at(x, y)
    time.sleep(0.08)
    user32.mouse_event(DOWN, 0, 0, 0, 0)
    time.sleep(0.06)
    user32.mouse_event(UP, 0, 0, 0, 0)
    time.sleep(0.15)
    at(old.x, old.y)


def drag(x1, y1, x2, y2, steps=30):
    old = wt.POINT()
    user32.GetCursorPos(ctypes.byref(old))
    at(x1, y1)
    time.sleep(0.1)
    user32.mouse_event(DOWN, 0, 0, 0, 0)
    time.sleep(0.15)
    for i in range(1, steps + 1):
        at(x1 + (x2 - x1) * i / steps, y1 + (y2 - y1) * i / steps)
        time.sleep(0.02)
    time.sleep(0.15)
    user32.mouse_event(UP, 0, 0, 0, 0)
    time.sleep(0.15)
    at(old.x, old.y)


def title(words):
    h = user32.FindWindowW(None, words)
    if not h:
        return None
    r = wt.RECT()
    user32.GetWindowRect(h, ctypes.byref(r))
    return r.left, r.top, r.right - r.left, r.bottom - r.top


if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "click":
        click(*map(float, args))
    elif cmd == "drag":
        drag(*map(float, args))
    elif cmd == "title":
        print(title(" ".join(args)))
