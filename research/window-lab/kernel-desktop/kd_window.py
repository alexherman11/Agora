"""kd_window: the window module. A painter's host for the desktop, speaking the module protocol (SHAPE 11).

Started by the kernel (the world's module thing `window`), never by hand. It publishes:

    window.list [all]                  see   the Agora windows open now (with `all`, other programs' windows too, as
                                             boxes and program names, never titles): what the taskbar and the guy read
    window.open <view> [thing] [to=<spot>|at=x,y size=w,h]
                                       do    a new window thing in the world; this host opens it on the screen
    window.move <window> to=<spot>|at=x,y [size=w,h]
                                       do    sets where it is (spots: left, right, center, big, top-left, ...)
    window.close <window>              do    the window thing goes (undo opens it again where it was)
    window.focus <window>              do    brings it forward, or tucks it away if it is in front already
    window.opened                      hear  a window this host opened is on the screen now (a rule can act on it)

How it works. The world holds intent: one `window` thing per window (shows=<view>, at, size, sees). This process makes
the screen match it, level-triggered: after every happening that touches a window thing, and every few seconds, it
reads `rows window` on its own grants and opens, moves and closes real windows until they agree. So a window opened by
a word, by a rule or by Alex's own press is the same act, undo works, and the windows come back after a restart.
When Alex drags a window, it records where he left it (`set <window> at=.. size=..`, by this module, on its own).

Its windows are WebView2 (pywebview), frameless. A window showing a lens (a world thing `kind=lens`, made by a
line) is lens.js itself, unchanged, painting from the kernel's painter routes, inside a thin frame page that gives it
a strip to drag and close by; the desktop's own views (lines, thing, help, the taskbar) are pages under /desk/. Each is
opened through the door's /dev/signin, which sets Alex's session as an HttpOnly cookie. The taskbar
window is held along the bottom edge as an AppBar (the shell's own seam), so maximized windows stop above it; when the
process ends, however it ends, the shell gives the strip back (ran 23 Oct: 625 ms after a hard kill).

Off: `off window` (a kernel word) stops this process: every Agora window closes and the strip comes back. undo turns it
on again, and the windows reopen where the world says. --headless keeps windows in memory only, for hidden tests.
"""
import ctypes
import json
import os
import sys
import threading
import time
from ctypes import wintypes as wt
from pathlib import Path
from urllib.parse import quote

VENV_SITE = Path(__file__).resolve().parents[3] / ".venv" / "Lib" / "site-packages"
if VENV_SITE.exists() and str(VENV_SITE) not in sys.path:
    sys.path.append(str(VENV_SITE))          # run by the base interpreter (a real pid), with the venv's packages

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from modproto import Module, log  # noqa: E402

HEADLESS = "--headless" in sys.argv
PORT = int(os.environ.get("AGORA_KDESK_PORT", "8810"))
LENS_SIZE = (1180, 1500)        # a lens window's first size, in real pixels
VIEWS = {"lines": ("Lines", (1500, 760)), "thing": ("Thing", (1000, 820)),
         "help": ("Help", (1200, 1300)), "taskbar": ("Agora taskbar", (0, 0))}
BAR_H = 66

if sys.platform == "win32":
    # private handles: argtypes set on the shared ctypes.windll.user32 broke pywebview's own calls (ran 23 Oct)
    user32, shell32 = ctypes.WinDLL("user32", use_last_error=True), ctypes.WinDLL("shell32")
    kernel32, dwmapi = ctypes.WinDLL("kernel32"), ctypes.WinDLL("dwmapi")
    kernel32.GetModuleHandleW.restype = wt.HMODULE
    if not HEADLESS:
        user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))        # per monitor v2: pixels are pixels
    WNDENUMPROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    user32.EnumWindows.argtypes = [WNDENUMPROC, wt.LPARAM]
    user32.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
    user32.SetWindowPos.argtypes = [wt.HWND, wt.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wt.UINT]
    user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
    user32.GetWindowLongPtrW.argtypes = [wt.HWND, ctypes.c_int]
    user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t
    user32.SetWindowLongPtrW.argtypes = [wt.HWND, ctypes.c_int, ctypes.c_ssize_t]
    user32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
    user32.IsWindowVisible.argtypes = [wt.HWND]
    user32.IsIconic.argtypes = [wt.HWND]
    user32.ShowWindow.argtypes = [wt.HWND, ctypes.c_int]
    user32.SetForegroundWindow.argtypes = [wt.HWND]
    user32.GetForegroundWindow.restype = wt.HWND
    user32.GetAncestor.restype = wt.HWND
    user32.GetAncestor.argtypes = [wt.HWND, wt.UINT]
    user32.GetWindow.restype = wt.HWND
    user32.GetWindow.argtypes = [wt.HWND, wt.UINT]
    dwmapi.DwmGetWindowAttribute.argtypes = [wt.HWND, wt.DWORD, ctypes.c_void_p, wt.DWORD]

HWND_TOPMOST, HWND_NOTOPMOST = wt.HWND(-1), wt.HWND(-2)
SWP_NOZORDER, SWP_NOACTIVATE, SWP_FRAMECHANGED, SWP_NOMOVE, SWP_NOSIZE = 0x4, 0x10, 0x20, 0x2, 0x1
GWL_EXSTYLE, WS_EX_TOOLWINDOW, WS_EX_APPWINDOW = -20, 0x80, 0x40000
SW_HIDE, SW_SHOWNOACTIVATE, SW_RESTORE, SW_MINIMIZE = 0, 4, 9, 6


def rect_of(hwnd):
    r = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return r.left, r.top, r.right - r.left, r.bottom - r.top


def monitor():
    """The primary monitor and its work area, in real pixels."""
    w, h = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    r = wt.RECT()
    user32.SystemParametersInfoW(0x30, 0, ctypes.byref(r), 0)
    return (0, 0, w, h), (r.left, r.top, r.right, r.bottom)


def scale():
    try:
        return user32.GetDpiForSystem() / 96.0
    except Exception:
        return 1.0


class AppBar:
    """A strip along the bottom edge, reserved through the shell (SHAppBarMessage). A hidden window of its own takes
    the shell's notices; the visible taskbar window is placed into the strip and kept topmost, except while another
    program is full screen (a game), when it steps back."""

    class DATA(ctypes.Structure):
        _fields_ = [("cbSize", wt.DWORD), ("hWnd", wt.HWND), ("uCallbackMessage", wt.UINT), ("uEdge", wt.UINT),
                    ("rc", wt.RECT), ("lParam", wt.LPARAM)]

    CALLBACK = 0x8000 + 0x41

    def __init__(self, height, placed):
        self.height, self.placed, self.hwnd, self.rect, self.full = height, placed, None, None, False
        self.ready = threading.Event()
        self.stop_ev = threading.Event()
        shell32.SHAppBarMessage.restype = ctypes.c_size_t
        shell32.SHAppBarMessage.argtypes = [wt.DWORD, ctypes.POINTER(self.DATA)]
        threading.Thread(target=self._loop, daemon=True, name="appbar").start()
        self.ready.wait(5)

    def _data(self):
        d = self.DATA()
        d.cbSize, d.hWnd, d.uCallbackMessage, d.uEdge = ctypes.sizeof(self.DATA), self.hwnd, self.CALLBACK, 3
        return d

    def _setpos(self):
        (mx, my, mw, mh), _ = monitor()
        d = self._data()
        d.rc = wt.RECT(mx, my, mx + mw, my + mh)
        shell32.SHAppBarMessage(2, ctypes.byref(d))           # ABM_QUERYPOS: the shell moves it above its own taskbar
        d.rc.top = d.rc.bottom - self.height
        shell32.SHAppBarMessage(3, ctypes.byref(d))           # ABM_SETPOS
        self.rect = (d.rc.left, d.rc.top, d.rc.right - d.rc.left, d.rc.bottom - d.rc.top)
        self.placed(self.rect, not self.full)

    def _loop(self):
        WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)
        user32.DefWindowProcW.restype = ctypes.c_ssize_t
        user32.DefWindowProcW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]

        def proc(h, m, w, l):
            if m == self.CALLBACK:
                if w == 2:                                    # ABN_FULLSCREENAPP
                    self.full = bool(l)
                    if self.rect:
                        self.placed(self.rect, not self.full)
                elif w == 1:                                  # ABN_POSCHANGED
                    self._setpos()
            return user32.DefWindowProcW(h, m, w, l)
        self._proc = WNDPROC(proc)

        class WNDCLASS(ctypes.Structure):
            _fields_ = [("style", wt.UINT), ("lpfnWndProc", WNDPROC), ("cbClsExtra", ctypes.c_int),
                        ("cbWndExtra", ctypes.c_int), ("hInstance", wt.HINSTANCE), ("hIcon", wt.HICON),
                        ("hCursor", wt.HANDLE), ("hbrBackground", wt.HBRUSH), ("lpszMenuName", wt.LPCWSTR),
                        ("lpszClassName", wt.LPCWSTR)]
        wc = WNDCLASS()
        wc.lpfnWndProc, wc.lpszClassName = self._proc, "AgoraKernelAppBar"
        wc.hInstance = kernel32.GetModuleHandleW(None)
        user32.RegisterClassW(ctypes.byref(wc))
        user32.CreateWindowExW.restype = wt.HWND
        user32.CreateWindowExW.argtypes = [wt.DWORD, wt.LPCWSTR, wt.LPCWSTR, wt.DWORD, ctypes.c_int, ctypes.c_int,
                                           ctypes.c_int, ctypes.c_int, wt.HWND, wt.HMENU, wt.HINSTANCE, wt.LPVOID]
        self.hwnd = user32.CreateWindowExW(WS_EX_TOOLWINDOW, "AgoraKernelAppBar", "Agora taskbar strip", 0, 0, 0, 0, 0,
                                           None, None, wc.hInstance, None)
        d = self._data()
        shell32.SHAppBarMessage(0, ctypes.byref(d))           # ABM_NEW
        self._setpos()
        self.ready.set()
        msg = wt.MSG()
        while not self.stop_ev.is_set():
            while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
            time.sleep(0.05)
        d = self._data()
        shell32.SHAppBarMessage(1, ctypes.byref(d))           # ABM_REMOVE: the strip comes back
        user32.DestroyWindow(self.hwnd)

    def remove(self):
        self.stop_ev.set()


# ---------------------------------------------------------------- the screen: real windows, or windows in memory
class Screen:
    """What a host must do; GuiScreen does it with WebView2 windows, MemScreen in memory (hidden tests)."""


class MemScreen(Screen):
    def __init__(self):
        self.wins, self.front = {}, None

    def start(self, then):
        then()
        threading.Event().wait()

    def open(self, wid, view, title, url, box, on_closed, on_shown, bar=False):
        self.wins[wid] = {"box": box, "view": view, "title": title, "url": url, "min": False}
        self.front = wid
        threading.Thread(target=on_shown, daemon=True).start()

    def close(self, wid):
        self.wins.pop(wid, None)

    def place(self, wid, box):
        if wid in self.wins:
            self.wins[wid]["box"] = box

    def box(self, wid):
        w = self.wins.get(wid)
        return w and w["box"]

    def shown(self, wid):
        w = self.wins.get(wid)
        return bool(w and not w["min"])

    def focus(self, wid):
        if self.front == wid and not self.wins[wid]["min"]:
            self.wins[wid]["min"] = True
            return "tucked away"
        self.wins[wid]["min"] = False
        self.front = wid
        return "brought forward"

    def is_front(self, wid):
        return self.front == wid

    def others(self):
        return []

    def work(self):
        return (0, 0, 3840, 2088 - BAR_H)


class GuiScreen(Screen):
    def __init__(self, module):
        import webview
        self.webview, self.module = webview, module
        self.wins = {}            # wid -> {"w": pywebview window, "hwnd": int, "view": str}
        self.closing = set()
        self.bar = None
        self.lock = threading.Lock()

    def start(self, then):
        # pywebview needs a window before start: a hidden one that holds the loop and shows nothing
        self.anchor = self.webview.create_window("Agora window host", html="<html></html>", hidden=True,
                                                 width=200, height=100)
        self.webview.start(then, gui="edgechromium", private_mode=True)

    def open(self, wid, view, title, url, box, on_closed, on_shown, bar=False):
        s = scale()
        x, y, w, h = box
        api = PageApi(self, wid)
        win = self.webview.create_window(title, url, js_api=api, x=int(x / s), y=int(y / s), width=max(200, int(w / s)),
                                         height=max(30, int(h / s)), frameless=True, easy_drag=False, on_top=bar, min_size=(120, 24),
                                         background_color="#F6F3EC", text_select=True, hidden=True)
        rec = {"w": win, "hwnd": None, "view": view, "bar": bar}
        with self.lock:
            self.wins[wid] = rec

        def shown_once():
            try:
                hwnd = int(win.native.Handle.ToInt64())
            except Exception:
                hwnd = user32.FindWindowW(None, title)
            rec["hwnd"] = hwnd
            if bar:
                self._make_bar(wid, hwnd)
            else:
                user32.SetWindowPos(hwnd, None, x, y, w, h, SWP_NOZORDER)
            on_shown()

        def loaded():
            if rec["hwnd"] is None:
                win.show()
                time.sleep(0.15)
                shown_once()

        def closed():
            with self.lock:
                self.wins.pop(wid, None)
                mine = wid in self.closing
                self.closing.discard(wid)
            if rec.get("bar") and self.bar:
                self.bar.remove()
                self.bar = None
            if not mine:
                on_closed()
        win.events.loaded += loaded
        win.events.closed += closed

    def _make_bar(self, wid, hwnd):
        ex = user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
        user32.ShowWindow(hwnd, SW_HIDE)
        user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, (ex | WS_EX_TOOLWINDOW) & ~WS_EX_APPWINDOW)

        def placed(rect, top):
            x, y, w, h = rect
            user32.SetWindowPos(hwnd, HWND_TOPMOST, x, y, w, h, SWP_NOACTIVATE | SWP_FRAMECHANGED)
            if not self.bar_hidden:
                user32.ShowWindow(hwnd, SW_SHOWNOACTIVATE)
        self.bar_hidden = False
        self.bar = AppBar(BAR_H, placed)
        threading.Thread(target=self._step_back, args=(hwnd,), daemon=True, name="full-screen").start()

    def _step_back(self, hwnd):
        """While another program is full screen (a game), the strip is hidden; it comes back when that ends. The
        shell's own notice (ABN_FULLSCREENAPP) did not reach it in a test (ran 23 Oct), so this looks for itself."""
        mine = {hwnd}
        while self.bar and user32.IsWindow(hwnd):
            fg = user32.GetForegroundWindow()
            full = False
            if fg and fg not in mine:
                cls = ctypes.create_unicode_buffer(64)
                user32.GetClassNameW(fg, cls, 64)
                if cls.value not in ("Progman", "WorkerW", "Shell_TrayWnd", "Shell_SecondaryTrayWnd"):
                    x, y, w, h = rect_of(fg)
                    (mx, my, mw, mh), _ = monitor()
                    full = x <= mx and y <= my and x + w >= mx + mw and y + h >= my + mh
            if full != self.bar_hidden:
                self.bar_hidden = full
                if full:
                    user32.ShowWindow(hwnd, SW_HIDE)
                else:
                    user32.ShowWindow(hwnd, SW_SHOWNOACTIVATE)
                    user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOACTIVATE | SWP_NOMOVE | SWP_NOSIZE)
            time.sleep(0.5)

    def close(self, wid):
        with self.lock:
            rec = self.wins.get(wid)
            if rec:
                self.closing.add(wid)
        if rec:
            rec["w"].destroy()

    def place(self, wid, box):
        rec = self.wins.get(wid)
        if rec and rec["hwnd"] and not rec["bar"]:
            if user32.IsIconic(rec["hwnd"]):
                user32.ShowWindow(rec["hwnd"], SW_RESTORE)
            user32.SetWindowPos(rec["hwnd"], None, *box, SWP_NOZORDER | SWP_NOACTIVATE)

    def box(self, wid):
        rec = self.wins.get(wid)
        if not rec or not rec["hwnd"] or user32.IsIconic(rec["hwnd"]):
            return None
        return rect_of(rec["hwnd"])

    def shown(self, wid):
        rec = self.wins.get(wid)
        return bool(rec and rec["hwnd"] and user32.IsWindowVisible(rec["hwnd"]) and not user32.IsIconic(rec["hwnd"]))

    def is_front(self, wid):
        rec = self.wins.get(wid)
        return bool(rec and rec["hwnd"] and user32.GetForegroundWindow() == rec["hwnd"])

    def focus(self, wid):
        rec = self.wins.get(wid)
        if not rec or not rec["hwnd"]:
            return "not on the screen yet"
        h = rec["hwnd"]
        if user32.GetForegroundWindow() == h and not user32.IsIconic(h):
            user32.ShowWindow(h, SW_MINIMIZE)
            return "tucked away"
        if user32.IsIconic(h):
            user32.ShowWindow(h, SW_RESTORE)
        user32.SetForegroundWindow(h)
        return "brought forward"

    def minimize(self, wid):
        rec = self.wins.get(wid)
        if rec and rec["hwnd"]:
            user32.ShowWindow(rec["hwnd"], SW_MINIMIZE)

    def others(self):
        """Other programs' windows as boxes, front to back: what the guy hops on. Titles are never read."""
        mine = {r["hwnd"] for r in self.wins.values() if r["hwnd"]}
        pid_self = os.getpid()
        out = []

        def each(h, _):
            if h in mine or not user32.IsWindowVisible(h) or user32.IsIconic(h):
                return True
            if user32.GetAncestor(h, 3) != h:                 # GA_ROOTOWNER: only top-level owners
                return True
            ex = user32.GetWindowLongPtrW(h, GWL_EXSTYLE)
            if ex & WS_EX_TOOLWINDOW:
                return True
            cloaked = ctypes.c_int(0)
            dwmapi.DwmGetWindowAttribute(h, 14, ctypes.byref(cloaked), 4)
            if cloaked.value:
                return True
            pid = wt.DWORD()
            user32.GetWindowThreadProcessId(h, ctypes.byref(pid))
            if pid.value == pid_self:
                return True
            x, y, w, hh = rect_of(h)
            if w < 120 or hh < 80:
                return True
            out.append({"x": x, "y": y, "w": w, "h": hh, "pid": pid.value, "hwnd": h})
            return True
        user32.EnumWindows(WNDENUMPROC(each), 0)
        return out

    def z_order(self):
        """Every visible top-level window handle, front to back, so mine and others' can be merged in order."""
        out = []

        def each(h, _):
            if user32.IsWindowVisible(h) and not user32.IsIconic(h):
                out.append(h)
            return True
        user32.EnumWindows(WNDENUMPROC(each), 0)
        return out

    def work(self):
        _, (l, t, r, b) = monitor()
        return (l, t, r - l, b - t)


class PageApi:
    """What a page may ask its own window, and nothing else: tuck itself away, or be resized by its corner. Closing is
    a line (window.close), not a power here."""

    def __init__(self, screen, wid):
        self._screen, self._wid = screen, wid

    def minimize(self):
        self._screen.minimize(self._wid)
        return True

    def resize(self):
        """Follow the mouse from the window's corner until the button is let go (the page calls this on mousedown)."""
        rec = self._screen.wins.get(self._wid)
        if not rec or not rec["hwnd"]:
            return False
        h = rec["hwnd"]
        x, y, _, _ = rect_of(h)
        pt = wt.POINT()
        while user32.GetAsyncKeyState(0x01) & 0x8000:
            user32.GetCursorPos(ctypes.byref(pt))
            user32.SetWindowPos(h, None, x, y, max(360, pt.x - x + 6), max(240, pt.y - y + 6), SWP_NOZORDER | SWP_NOACTIVATE)
            time.sleep(0.016)
        return True


# ---------------------------------------------------------------- the module
def parse_box(row):
    try:
        x, y = [int(float(v)) for v in str(row.get("at", "")).split(",")]
        w, h = [int(float(v)) for v in str(row.get("size", "")).split(",")]
        return (x, y, w, h)
    except ValueError:
        return None


class WindowHost:
    def __init__(self):
        self.screen = MemScreen() if HEADLESS else GuiScreen(self)
        self.rows = {}                 # wid -> the window thing as last read
        self.applied = {}              # wid -> the box last put on the screen (or recorded from a drag)
        self.settle = {}               # wid -> (box, polls seen) while a drag settles
        self.opened = 0
        self.lock = threading.RLock()
        self.dirty = threading.Event()
        self.token = None
        self.m = Module(offer=self.offer(), on_call=self.call, on_happen=self.happen, on_status=self.status,
                        on_hello=self.hello, on_off=self.off)

    # -- protocol
    def offer(self):
        spots = "left, right, center, big, top-left, top-right, bottom-left, bottom-right"
        return [
            {"word": "window.list", "kind": "see", "takes": "[all]", "may": "anyone",
             "help": "window.list [all]: the Agora windows open on this desktop now, front first. With all, other "
                     "programs' windows too, as boxes and program ids, never their titles."},
            {"word": "window.open", "kind": "do", "takes": "<view> [<id>] [to=<spot>] [at=<x,y>] [size=<w,h>]", "may": "anyone",
             "help": f"window.open <lens or view> [thing] [to=<spot>|at=x,y size=w,h]: open a window on the desktop. Any "
                     f"lens in the world (rows lens lists them; window.open feed), or the views "
                     f"{', '.join(v for v in VIEWS if v != 'taskbar')}. Spots: {spots}. Only the desktop's owner "
                     f"(and their agents) open windows here. A view open already is brought forward instead; new=yes opens another. undo closes it."},
            {"word": "window.move", "kind": "do", "takes": "<id> [to=<spot>] [at=<x,y>] [size=<w,h>]", "may": "anyone",
             "help": f"window.move <window> to=<spot> | at=x,y [size=w,h]: put a window somewhere ({spots}). undo puts "
                     f"it back."},
            {"word": "window.close", "kind": "do", "takes": "<id>", "may": "anyone",
             "help": "window.close <window>: close it. Its window thing goes from the world; undo opens it again where "
                     "it was."},
            {"word": "window.focus", "kind": "do", "takes": "<id>", "may": "anyone",
             "help": "window.focus <window>: bring it forward, or tuck it away if it is in front already (what a "
                     "taskbar button does). Changes the screen only, so nothing is recorded."},
            {"word": "window.opened", "kind": "hear", "takes": "<id>", "may": "anyone",
             "help": "window.opened: heard when a window this host opened is on the screen. "
                     "make kind=rule on=window.opened do=\"window.move $target to=right\" moves every new window."},
            {"word": "window.overlay", "kind": "hold", "takes": "", "may": "stewards",
             "help": "window.overlay: a see-through surface over this desktop, held while something runs (the little "
                     "guy holds it). Held by grant; holds lists who holds it, and off <module> ends the hold."},
        ]

    def hello(self, msg):
        self.mid, self.owner = msg.get("id"), msg.get("owner")
        try:
            sessions = json.loads((Path(msg["world"]) / "keep" / "sessions.json").read_text(encoding="utf-8"))
            self.token = next(t for t, v in sessions.items() if v.get("signer") == "alex")
        except (OSError, KeyError, StopIteration, ValueError) as exc:
            log(f"no desktop session for the pages: {exc!r}")
        self.dirty.set()

    def off(self):
        log("off: closing every Agora window")
        for wid in list(self.screen.wins):
            self.screen.close(wid)
        if getattr(self.screen, "bar", None):
            self.screen.bar.remove()
        time.sleep(0.3)
        os._exit(0)

    def status(self):
        n = len(self.screen.wins)
        views = ", ".join(sorted(r.get("shows", "?") for r in self.rows.values()))
        return f"{n} window{'' if n == 1 else 's'} on the screen ({views or 'none'}); {self.opened} opened since start"

    def happen(self, h):
        # the kernel sends what this module's grants hear (hear:make, hear:set, ...); any of them may touch a window
        if h.get("word") in ("make", "set", "forget", "undo", "off"):
            self.dirty.set()

    def _owner_only(self, caller):
        if caller.get("person") != self.owner and caller.get("id") != self.owner:
            return {"refused": "window opens and moves windows only for this desktop's owner and their agents"}
        return None

    def call(self, msg):
        out = self._call(msg)
        if out.get("lines"):
            # a module does not hear its own acts, so it looks again a moment after its answer is admitted
            threading.Timer(0.3, self.dirty.set).start()
            threading.Timer(1.5, self.dirty.set).start()
        return out

    def lens_named(self, name, use):
        r = self.m.see(f"rows lens name={name}", use=use)
        return (r.get("rows") or [None])[0]

    def _call(self, msg):
        word, args, caller, use = msg["word"], msg.get("args") or {}, msg.get("caller") or {}, msg.get("use")
        kv, words, target = args.get("kv") or {}, (args.get("words") or "").split(), args.get("target")
        if word == "window.list":
            return self.list_rows(all_="all" in words)
        refused = self._owner_only(caller)
        if refused:
            return refused
        if word == "window.open":
            if not words:
                return {"refused": "window.open needs a view: " + ", ".join(v for v in VIEWS if v != "taskbar")}
            view = words[0].lower()
            lens = None
            if view not in VIEWS:
                lens = self.lens_named(view, use)
                if lens is None:
                    return {"refused": f"no lens or view called {view}; rows lens lists the lenses, and the views are "
                                       f"{', '.join(v for v in VIEWS if v != 'taskbar')}"}
            thing = target or (words[1] if len(words) > 1 else "")
            same = [r for r in self.rows.values() if r.get("shows") == view and (r.get("target") or "") == thing]
            if same and kv.get("new") != "yes" and view != "taskbar" and not (kv.get("to") or kv.get("at")):
                said = self.screen.focus(same[0]["id"]) if not self.screen.is_front(same[0]["id"]) else "in front already"
                return {"text": f"{same[0].get('name')} is open already: {said} (new=yes opens another)"}
            n = sum(1 for r in self.rows.values() if r.get("shows") == view)
            box = self.box_for(view, kv, n)
            if view == "taskbar" and n:
                return {"refused": "the taskbar is open already"}
            base = (lens.get("title") or view.capitalize()) if lens else VIEWS[view][0]
            name = base + (f" {n + 1}" if n and view != "taskbar" else "")
            line = (f'make kind=window shows={view} name="{name}" at={box[0]},{box[1]} size={box[2]},{box[3]}'
                    + (f" lens={view}" if lens else "") + (f" target={thing}" if thing else "")
                    + (" edge=bottom" if view == "taskbar" else ""))
            return {"lines": [line], "saw": {}}
        if word in ("window.move", "window.close", "window.focus"):
            row = self.row_for(target, use)
            if row is None:
                return {"refused": f"{target or 'that'} is not one of the windows open here; window.list shows them"}
            if word == "window.focus":
                return {"text": f"{row.get('name')}: {self.screen.focus(row['id'])}"}
            if word == "window.close":
                return {"lines": [f"forget {row['id']}"], "saw": {row["id"]: row["rev"]}}
            if row.get("shows") == "taskbar":
                return {"refused": "the taskbar keeps its edge; set its height or close it instead"}
            box = self.box_for(row.get("shows"), kv, 0, current=parse_box(row))
            return {"lines": [f"set {row['id']} at={box[0]},{box[1]} size={box[2]},{box[3]}"],
                    "saw": {row["id"]: row["rev"]}}
        return {"refused": f"window has no word {word}"}

    def row_for(self, target, use):
        if not target:
            return None
        r = self.m.see("rows window", use=use)
        for row in r.get("rows") or []:
            if row.get("id") == target:
                return row
        return None

    def box_for(self, view, kv, n, current=None):
        wx, wy, ww, wh = self.screen.work()
        if view == "taskbar":
            return (wx, wy + wh - BAR_H, ww, BAR_H)
        dw, dh = VIEWS.get(view, ("", LENS_SIZE))[1]
        w, h = (current[2], current[3]) if current else (dw, dh)
        if kv.get("size"):
            try:
                w, h = [int(float(v)) for v in kv["size"].split(",")]
            except ValueError:
                pass
        spot = kv.get("to")
        gap = 24
        if spot:
            half_w, half_h = (ww - 3 * gap) // 2, (wh - 3 * gap) // 2
            spots = {"left": (wx + gap, wy + gap, half_w, wh - 2 * gap),
                     "right": (wx + 2 * gap + half_w, wy + gap, half_w, wh - 2 * gap),
                     "center": (wx + (ww - w) // 2, wy + (wh - h) // 2, w, h),
                     "big": (wx + ww // 10, wy + wh // 12, ww * 8 // 10, wh * 10 // 12),
                     "top-left": (wx + gap, wy + gap, half_w, half_h),
                     "top-right": (wx + 2 * gap + half_w, wy + gap, half_w, half_h),
                     "bottom-left": (wx + gap, wy + 2 * gap + half_h, half_w, half_h),
                     "bottom-right": (wx + 2 * gap + half_w, wy + 2 * gap + half_h, half_w, half_h)}
            if spot in spots:
                return spots[spot]
        if kv.get("at"):
            try:
                x, y = [int(float(v)) for v in kv["at"].split(",")]
                return (x, y, w, h)
            except ValueError:
                pass
        if current:
            return (current[0], current[1], w, h)
        return (wx + ww - w - 120 - 64 * n, wy + 250 + 64 * n, w, min(h, wh - 300))   # low enough for the guy's bubble

    def list_rows(self, all_=False):
        rows = []
        z = self.screen.z_order() if hasattr(self.screen, "z_order") else []
        zi = {h: i for i, h in enumerate(z)}
        for wid, row in sorted(self.rows.items(), key=lambda x: x[0]):
            rec = self.screen.wins.get(wid)
            if rec is None:
                continue
            box = self.screen.box(wid)
            hwnd = rec.get("hwnd") if isinstance(rec, dict) else None
            rows.append({"id": wid, "kind": "window", "name": row.get("name"), "shows": row.get("shows"),
                         "target": row.get("target"), "box": list(box) if box else None,
                         "shown": self.screen.shown(wid), "front": self.screen.is_front(wid),
                         "z": zi.get(hwnd, 9999)})
        if all_:
            for o in self.screen.others():
                rows.append({"kind": "other", "box": [o["x"], o["y"], o["w"], o["h"]], "program": o["pid"],
                             "shown": True, "front": False, "z": zi.get(o.get("hwnd"), 9000)})
        rows.sort(key=lambda r: r.get("z", 9999))
        wx, wy, ww, wh = self.screen.work()
        lines = [f"{sum(1 for r in rows if r['kind'] == 'window')} Agora window(s) open:"]
        for r in rows:
            if r["kind"] == "window":
                lines.append(f"  {r['id']} · {r['name']} · {r['shows']}" + (f" at {r['box'][0]},{r['box'][1]}" if r["box"] else " · tucked away"))
        if all_:
            lines.append(f"  and {sum(1 for r in rows if r['kind'] == 'other')} other program window(s)")
        return {"text": "\n".join(lines), "rows": rows + [{"kind": "work", "box": [wx, wy, ww, wh]}]}

    # -- keeping the screen like the world
    def reconcile(self):
        r = self.m.see("rows window")
        if not r.get("ok", True) or r.get("refused"):
            log(f"reconcile: {r.get('text') or r.get('refused')}")
            return
        want = {row["id"]: row for row in r.get("rows") or []}
        with self.lock:
            if not any(row.get("shows") == "taskbar" for row in want.values()) and not getattr(self, "made_bar", False):
                self.made_bar = True
                box = self.box_for("taskbar", {}, 0)
                out = self.m.do(f'make kind=window shows=taskbar name="Agora taskbar" edge=bottom '
                                f'at={box[0]},{box[1]} size={box[2]},{box[3]}')
                log(f"taskbar: {out.get('text')}")
                return                                  # its happening brings us back here
            self.made_bar = True
            for wid in [w for w in list(self.screen.wins) if w not in want]:
                self.screen.close(wid)
                self.applied.pop(wid, None)
            for wid, row in want.items():
                box = parse_box(row) or self.box_for(row.get("shows"), {}, 0)
                if wid not in self.screen.wins:
                    self._open(wid, row, box)
                elif self.applied.get(wid) != box and row.get("shows") != "taskbar":
                    self.screen.place(wid, box)
                    self.applied[wid] = box
            self.rows = want

    def _open(self, wid, row, box):
        if row.get("lens"):
            view = "frame"
            path = f"/desk/frame.html?win={wid}&lens={quote(str(row['lens']))}&name={quote(str(row.get('name') or ''))}"
        else:
            view = row.get("shows") if row.get("shows") in VIEWS else "thing"
            path = f"/desk/{view}.html?win={wid}" + (f"&target={quote(str(row['target']))}" if row.get("target") else "")
        title = f"{row.get('name') or VIEWS.get(view, ('Agora',))[0]} · Agora"
        url = (f"http://127.0.0.1:{PORT}/dev/signin?token={quote(self.token)}&next={quote(path)}" if self.token
               else f"http://127.0.0.1:{PORT}{path}")
        self.applied[wid] = box

        def on_shown():
            self.opened += 1
            self.m.happen("window.opened", wid, f"{row.get('name')} is on the screen")

        def on_closed():                                  # closed by Alex (Alt+F4) or by Windows: the world follows
            row2 = self.rows.get(wid) or row
            out = self.m.do(f"forget {wid}", saw={wid: row2.get("rev", 0)})
            log(f"{wid} closed on the screen: {out.get('text')}")
        self.screen.open(wid, view, title, url, box, on_closed, on_shown, bar=(view == "taskbar"))

    def watch_drags(self):
        """Every half second: a window Alex moved or resized and then left alone is recorded where he left it."""
        while True:
            time.sleep(0.5)
            for wid, row in list(self.rows.items()):
                if row.get("shows") == "taskbar":
                    continue
                box = self.screen.box(wid)
                if not box or box == self.applied.get(wid):
                    self.settle.pop(wid, None)
                    continue
                seen = self.settle.get(wid)
                if seen and seen[0] == box:
                    if seen[1] >= 2:
                        self.settle.pop(wid, None)
                        self.applied[wid] = box
                        out = self.m.do(f"set {wid} at={box[0]},{box[1]} size={box[2]},{box[3]}",
                                        saw={wid: row.get("rev", 0)})
                        log(f"{wid} moved by hand: {out.get('text')}")
                    else:
                        self.settle[wid] = (box, seen[1] + 1)
                else:
                    self.settle[wid] = (box, 1)

    def loop(self):
        self.m.ready.wait(30)
        while not self.m.closed.is_set():
            self.dirty.wait(4)
            self.dirty.clear()
            try:
                self.reconcile()
            except Exception as exc:
                log(f"reconcile failed: {exc!r}")

    def run(self):
        self.m.run_reader()

        def started():
            threading.Thread(target=self.loop, daemon=True, name="reconcile").start()
            threading.Thread(target=self.watch_drags, daemon=True, name="drags").start()
            threading.Thread(target=self._guard, daemon=True, name="guard").start()
        self.screen.start(started)

    def _guard(self):
        self.m.closed.wait()
        self.off()


if __name__ == "__main__":
    WindowHost().run()
