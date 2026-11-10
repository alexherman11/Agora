"""desktop host: Agora-owned windows on the Windows desktop.

A first probe, not a design. One process owns a set of borderless, per-pixel
alpha windows described in state/windows.json and keeps them where they are:
above everything ("top") or on the desktop under every app ("bottom"), and
click-through, so they never take the mouse or the keyboard.

The file is the pass-through: anything that rewrites it (a person, a desk
verb, a resident) changes the windows within half a second, and the host
writes back when a window is moved by hand.

  python host.py            run (one instance; a second exits 76)
  python host.py --check    draw once, print each window's rect, exit

Ctrl+Alt+L toggles arrange mode: the windows get an outline, take the mouse,
drag from the middle to move and from an edge to resize. Ctrl+Alt+L again
locks them and saves.
"""
import ctypes
import json
import math
import os
import sys
from ctypes import wintypes as wt

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(HERE, "state")
STATE = os.path.join(STATE_DIR, "windows.json")
PIDFILE = os.path.join(STATE_DIR, "host.pid")

DEFAULT = {
    "windows": [
        {
            "id": "postit-light",
            "kind": "light",
            "on": True,
            "x": 2040, "y": 140, "w": 440, "h": 440,
            "color": [255, 236, 190],
            "brightness": 1.0,
            "glow": 60,
            "layer": "top",
        }
    ]
}

user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

LRESULT = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)

WS_POPUP = 0x80000000
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_TOPMOST = 0x00000008
WS_EX_NOACTIVATE = 0x08000000
GWL_EXSTYLE = -20
HWND_TOPMOST, HWND_NOTOPMOST, HWND_BOTTOM = -1, -2, 1
SWP_NOSIZE, SWP_NOMOVE, SWP_NOACTIVATE, SWP_SHOWWINDOW = 0x1, 0x2, 0x10, 0x40
SW_HIDE, SW_SHOWNOACTIVATE = 0, 4
WM_DESTROY, WM_TIMER, WM_HOTKEY = 0x0002, 0x0113, 0x0312
WM_NCHITTEST, WM_EXITSIZEMOVE, WM_MOUSEACTIVATE = 0x0084, 0x0232, 0x0021
MA_NOACTIVATE = 3
HTCAPTION, HTLEFT, HTRIGHT, HTTOP, HTTOPLEFT, HTTOPRIGHT = 2, 10, 11, 12, 13, 14
HTBOTTOM, HTBOTTOMLEFT, HTBOTTOMRIGHT = 15, 16, 17
MOD_ALT, MOD_CONTROL, MOD_NOREPEAT = 0x1, 0x2, 0x4000
ULW_ALPHA = 2
EDGE = 18


class WNDCLASS(ctypes.Structure):
    _fields_ = [("style", wt.UINT), ("lpfnWndProc", WNDPROC), ("cbClsExtra", ctypes.c_int),
                ("cbWndExtra", ctypes.c_int), ("hInstance", wt.HINSTANCE), ("hIcon", wt.HICON),
                ("hCursor", wt.HANDLE), ("hbrBackground", wt.HBRUSH),
                ("lpszMenuName", wt.LPCWSTR), ("lpszClassName", wt.LPCWSTR)]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wt.DWORD), ("biWidth", wt.LONG), ("biHeight", wt.LONG),
                ("biPlanes", wt.WORD), ("biBitCount", wt.WORD), ("biCompression", wt.DWORD),
                ("biSizeImage", wt.DWORD), ("biXPelsPerMeter", wt.LONG),
                ("biYPelsPerMeter", wt.LONG), ("biClrUsed", wt.DWORD), ("biClrImportant", wt.DWORD)]


class BLENDFUNCTION(ctypes.Structure):
    _fields_ = [("BlendOp", ctypes.c_byte), ("BlendFlags", ctypes.c_byte),
                ("SourceConstantAlpha", ctypes.c_ubyte), ("AlphaFormat", ctypes.c_byte)]


def _sig(fn, res, *args):
    fn.restype, fn.argtypes = res, list(args)


_sig(user32.DefWindowProcW, LRESULT, wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)
_sig(user32.RegisterClassW, wt.ATOM, ctypes.POINTER(WNDCLASS))
_sig(user32.CreateWindowExW, wt.HWND, wt.DWORD, wt.LPCWSTR, wt.LPCWSTR, wt.DWORD,
     ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
     wt.HWND, wt.HMENU, wt.HINSTANCE, wt.LPVOID)
_sig(user32.DestroyWindow, wt.BOOL, wt.HWND)
_sig(user32.ShowWindow, wt.BOOL, wt.HWND, ctypes.c_int)
_sig(user32.SetWindowPos, wt.BOOL, wt.HWND, wt.HWND, ctypes.c_int, ctypes.c_int,
     ctypes.c_int, ctypes.c_int, wt.UINT)
_sig(user32.GetWindowRect, wt.BOOL, wt.HWND, ctypes.POINTER(wt.RECT))
_sig(user32.GetWindowLongPtrW, ctypes.c_ssize_t, wt.HWND, ctypes.c_int)
_sig(user32.SetWindowLongPtrW, ctypes.c_ssize_t, wt.HWND, ctypes.c_int, ctypes.c_ssize_t)
_sig(user32.GetDC, wt.HDC, wt.HWND)
_sig(user32.ReleaseDC, ctypes.c_int, wt.HWND, wt.HDC)
_sig(user32.UpdateLayeredWindow, wt.BOOL, wt.HWND, wt.HDC, ctypes.POINTER(wt.POINT),
     ctypes.POINTER(wt.SIZE), wt.HDC, ctypes.POINTER(wt.POINT), wt.COLORREF,
     ctypes.POINTER(BLENDFUNCTION), wt.DWORD)
_sig(user32.SetTimer, ctypes.c_size_t, wt.HWND, ctypes.c_size_t, wt.UINT, wt.LPVOID)
_sig(user32.RegisterHotKey, wt.BOOL, wt.HWND, ctypes.c_int, wt.UINT, wt.UINT)
_sig(user32.GetMessageW, ctypes.c_int, ctypes.POINTER(wt.MSG), wt.HWND, wt.UINT, wt.UINT)
_sig(user32.TranslateMessage, wt.BOOL, ctypes.POINTER(wt.MSG))
_sig(user32.DispatchMessageW, LRESULT, ctypes.POINTER(wt.MSG))
_sig(user32.PostQuitMessage, None, ctypes.c_int)
_sig(user32.LoadCursorW, wt.HANDLE, wt.HINSTANCE, wt.LPVOID)
_sig(gdi32.CreateCompatibleDC, wt.HDC, wt.HDC)
_sig(gdi32.CreateDIBSection, wt.HBITMAP, wt.HDC, ctypes.POINTER(BITMAPINFOHEADER), wt.UINT,
     ctypes.POINTER(ctypes.c_void_p), wt.HANDLE, wt.DWORD)
_sig(gdi32.SelectObject, wt.HGDIOBJ, wt.HDC, wt.HGDIOBJ)
_sig(gdi32.DeleteObject, wt.BOOL, wt.HGDIOBJ)
_sig(gdi32.DeleteDC, wt.BOOL, wt.HDC)
_sig(kernel32.GetModuleHandleW, wt.HMODULE, wt.LPCWSTR)
_sig(kernel32.CreateMutexW, wt.HANDLE, wt.LPVOID, wt.BOOL, wt.LPCWSTR)


def light_pixels(w, h, spec, outline):
    """Premultiplied BGRA for a soft-edged light, top row first."""
    r, g, b = (int(c) for c in spec.get("color", [255, 236, 190]))
    a0 = max(0.0, min(1.0, float(spec.get("brightness", 1.0))))
    glow = max(0, min(int(spec.get("glow", 60)), (min(w, h) - 1) // 2))

    def px(d):
        t = 1.0 if glow == 0 else max(0.0, 1.0 - d / glow)
        a = a0 * t * t * (3 - 2 * t)
        return bytes((int(b * a), int(g * a), int(r * a), int(255 * a)))

    rows = {}

    def row(dy):
        if dy not in rows:
            left = [px(math.hypot(glow - x, dy)) for x in range(glow)]
            rows[dy] = b"".join(left) + px(dy) * (w - 2 * glow) + b"".join(reversed(left))
        return rows[dy]

    buf = bytearray(b"".join(row(max(glow - y, y - (h - 1 - glow), 0)) for y in range(h)))
    if outline:
        line = bytes((255, 220, 80, 255))
        for y in range(h):
            for x in (range(w) if y < 2 or y >= h - 2 else (0, 1, w - 2, w - 1)):
                buf[(y * w + x) * 4:(y * w + x) * 4 + 4] = line
    return bytes(buf)


PAINTERS = {"light": light_pixels}


class Host:
    def __init__(self):
        self.specs = {}      # id -> spec, as in the file
        self.hwnds = {}      # id -> hwnd
        self.arrange = False
        self.mtime = None
        self.proc = WNDPROC(self.wndproc)
        cls = WNDCLASS()
        cls.lpfnWndProc = self.proc
        cls.hInstance = kernel32.GetModuleHandleW(None)
        cls.hCursor = user32.LoadCursorW(None, ctypes.c_void_p(32646))  # IDC_SIZEALL
        cls.lpszClassName = "AgoraHostWindow"
        self.cls = cls
        if not user32.RegisterClassW(ctypes.byref(cls)):
            raise ctypes.WinError(ctypes.get_last_error())

    # --- the file -------------------------------------------------------
    def load(self):
        if not os.path.exists(STATE):
            os.makedirs(STATE_DIR, exist_ok=True)
            self.save(DEFAULT)
        try:
            with open(STATE, encoding="utf-8") as f:
                doc = json.load(f)
            specs = {s["id"]: s for s in doc.get("windows", [])}
        except (OSError, ValueError, KeyError, TypeError) as e:
            print("windows.json not read, keeping what is shown:", e, flush=True)
            return
        self.mtime = os.path.getmtime(STATE)
        for wid in set(self.hwnds) - set(specs):
            user32.DestroyWindow(self.hwnds.pop(wid))
        self.specs = specs
        for wid in specs:
            self.show(wid)

    def save(self, doc=None):
        doc = doc or {"windows": list(self.specs.values())}
        tmp = STATE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=2)
        os.replace(tmp, STATE)
        self.mtime = os.path.getmtime(STATE)

    # --- one window -----------------------------------------------------
    def show(self, wid):
        spec = self.specs[wid]
        painter = PAINTERS.get(spec.get("kind"))
        hwnd = self.hwnds.get(wid)
        if painter is None or not spec.get("on", True):
            if hwnd:
                user32.ShowWindow(hwnd, SW_HIDE)
            return
        x, y = int(spec["x"]), int(spec["y"])
        w, h = max(8, int(spec["w"])), max(8, int(spec["h"]))
        top = spec.get("layer", "top") != "bottom"
        ex = WS_EX_LAYERED | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
        ex |= WS_EX_TOPMOST if top else 0
        ex |= 0 if self.arrange else WS_EX_TRANSPARENT
        if not hwnd:
            hwnd = user32.CreateWindowExW(ex, self.cls.lpszClassName, "agora:" + wid, WS_POPUP,
                                          x, y, w, h, None, None, self.cls.hInstance, None)
            if not hwnd:
                raise ctypes.WinError(ctypes.get_last_error())
            self.hwnds[wid] = hwnd
        else:
            user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, ex)
        self.blit(hwnd, x, y, w, h, painter(w, h, spec, self.arrange))
        user32.ShowWindow(hwnd, SW_SHOWNOACTIVATE)
        self.place(wid)

    def place(self, wid):
        hwnd = self.hwnds.get(wid)
        if hwnd and self.specs[wid].get("on", True):
            top = self.specs[wid].get("layer", "top") != "bottom"
            after = HWND_TOPMOST if top or self.arrange else HWND_BOTTOM
            user32.SetWindowPos(hwnd, after, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
            if not top and not self.arrange:
                user32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0,
                                    SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
                user32.SetWindowPos(hwnd, HWND_BOTTOM, 0, 0, 0, 0,
                                    SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)

    def blit(self, hwnd, x, y, w, h, pixels):
        screen = user32.GetDC(None)
        mem = gdi32.CreateCompatibleDC(screen)
        bmi = BITMAPINFOHEADER()
        bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.biWidth, bmi.biHeight, bmi.biPlanes, bmi.biBitCount = w, -h, 1, 32
        bits = ctypes.c_void_p()
        bmp = gdi32.CreateDIBSection(screen, ctypes.byref(bmi), 0, ctypes.byref(bits), None, 0)
        ctypes.memmove(bits, pixels, len(pixels))
        old = gdi32.SelectObject(mem, bmp)
        blend = BLENDFUNCTION(0, 0, 255, 1)
        ok = user32.UpdateLayeredWindow(hwnd, screen, ctypes.byref(wt.POINT(x, y)),
                                        ctypes.byref(wt.SIZE(w, h)), mem,
                                        ctypes.byref(wt.POINT(0, 0)), 0,
                                        ctypes.byref(blend), ULW_ALPHA)
        if not ok:
            print("UpdateLayeredWindow failed:", ctypes.get_last_error(), flush=True)
        gdi32.SelectObject(mem, old)
        gdi32.DeleteObject(bmp)
        gdi32.DeleteDC(mem)
        user32.ReleaseDC(None, screen)

    def rect(self, hwnd):
        r = wt.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(r))
        return r.left, r.top, r.right - r.left, r.bottom - r.top

    def wid_of(self, hwnd):
        for wid, h in self.hwnds.items():
            if h == hwnd:
                return wid

    # --- messages -------------------------------------------------------
    def wndproc(self, hwnd, msg, wp, lp):
        if msg == WM_MOUSEACTIVATE:
            return MA_NOACTIVATE
        if msg == WM_NCHITTEST and self.arrange:
            x, y, w, h = self.rect(hwnd)
            px = ctypes.c_short(lp & 0xFFFF).value - x
            py = ctypes.c_short((lp >> 16) & 0xFFFF).value - y
            l, r, t, b = px < EDGE, px >= w - EDGE, py < EDGE, py >= h - EDGE
            return (HTTOPLEFT if t and l else HTTOPRIGHT if t and r else
                    HTBOTTOMLEFT if b and l else HTBOTTOMRIGHT if b and r else
                    HTLEFT if l else HTRIGHT if r else HTTOP if t else
                    HTBOTTOM if b else HTCAPTION)
        if msg == WM_EXITSIZEMOVE:
            wid = self.wid_of(hwnd)
            if wid:
                s = self.specs[wid]
                s["x"], s["y"], s["w"], s["h"] = self.rect(hwnd)
                self.show(wid)
                self.save()
            return 0
        return user32.DefWindowProcW(hwnd, msg, wp, lp)

    def tick(self):
        try:
            changed = os.path.getmtime(STATE) != self.mtime
        except OSError:
            changed = False
        if changed:
            self.load()
        else:
            for wid in self.specs:
                self.place(wid)

    def toggle_arrange(self):
        self.arrange = not self.arrange
        for wid in self.specs:
            self.show(wid)
        if not self.arrange:
            self.save()

    def run(self):
        self.load()
        if not user32.RegisterHotKey(None, 1, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, ord("L")):
            print("Ctrl+Alt+L is taken; arrange mode has no key", flush=True)
        user32.SetTimer(None, 0, 500, None)
        msg = wt.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            if msg.message == WM_HOTKEY:
                self.toggle_arrange()
            elif msg.message == WM_TIMER and not msg.hWnd:
                self.tick()
            else:
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))


def main():
    try:
        user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))  # per-monitor v2: real pixels
    except (AttributeError, OSError):
        pass
    check = "--check" in sys.argv
    if not check:
        kernel32.CreateMutexW(None, False, "AgoraWindowLabHost")
        if ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS
            print("a host is already running", flush=True)
            return 76
    host = Host()
    if check:
        host.load()
        for wid, hwnd in host.hwnds.items():
            print(wid, host.rect(hwnd), flush=True)
        return 0
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(PIDFILE, "w") as f:
        f.write(str(os.getpid()))
    host.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
