"""EDITING THE DESKTOP HOST (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
This file is a seam between the world and Windows: it turns world facts into screen effects and screen events into world
facts, through small words. It holds no preferences and no content. Which apps, what a button opens, sizes, names, ids and
who may do what live in settings things it reads (shell-settings, wm-settings). It does not seed the world at start
(people, chats, pins). New behaviour is a rule over the words offered here. Before writing a Windows or browser helper,
use the shared one (gaming_gate for full-screen and desktop tests, widget_browser for hidden pages) instead of a copy.

kd_window: the window module. A painter's host for the desktop, speaking the module protocol (SHAPE 11).

Started by the kernel (the world's module thing `window`), never by hand. It publishes:

    window.list [all]                  see   the Agora windows open now (with `all`, other programs' windows too, as
                                             boxes and program names, never titles): what the taskbar and the guy read
    window.open <view> [thing] [to=<spot>|at=x,y size=w,h]
                                       do    a new window thing in the world; this host opens it on the screen
    window.move <window> to=<spot>|at=x,y [size=w,h]
                                       do    puts it there on the screen (spots: left, right, center, big, ...); no record
    window.close <window>              do    the window thing goes (undo opens it again where it was)
    window.focus <window>              do    brings it forward, or tucks it away if it is in front already
    window.opened                      hear  a window this host opened is on the screen now (a rule can act on it)
    window.picture <view|lens|thing> [size=WxH|screen] [name=]
                                       do    what that window would show, drawn hidden, as the caller's private picture
                                             file ($new in the rest of the line); needs a steward's
                                             `grant <window> words=upload only=kind:file`

The wallpaper (4 Nov). Windows shows the picture `Shell settings` names (wallpaper=<file>); emptied, Alex's own wallpaper
comes back (wallpaper.py is the seam: save, set, restore). What fills the setting is the world's business: the rule
"Wallpaper follows my theme" (on=theme.changed: window.picture shell-desktop size=screen ; set ... wallpaper=$new), or
Alex's own photo. AGORA_DESKTOP_LAYER=bottom brings back the old wallpaper window instead.

How it works. The world holds intent: one `window` thing per window (shows=<view>, lens, target, edge). This process
makes the screen match it, level-triggered: after every happening that touches a window thing, and every few seconds, it
reads `rows window` on its own grants and opens and closes real windows until they agree. So a window opened by a word,
by a rule or by Alex's own press is the same act, undo works, and the windows come back after a restart.
Where a window sits is NOT in the world (Alex, 26 Oct: "visual state should not live in the world"): it is this
screen's, kept in state/geometry.json (Geometry), and the window manager's when it holds the window. A drag or a
window.move changes the screen and that file, never a record. Old at=/size= on a window thing are read once, as a
first placement, when the file has nothing for it.

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
         "viewer": ("Viewer", (1280, 900)),
         "help": ("Help", (1200, 1300)), "tasks": ("Running windows", (1100, 1000)),
         "taskbar": ("Agora taskbar", (0, 0))}


def wallpaper_window():
    """AGORA_DESKTOP_LAYER=bottom|workerw brings back the old wallpaper window (shell_native.make_layer). By default the
    wallpaper is Windows' own, set from `Shell settings` wallpaper=<file> (follow_wallpaper)."""
    return os.environ.get("AGORA_DESKTOP_LAYER", "system") != "system"


def local_page(url):
    """Is this an http page served on this machine (another Agora door, such as the frontier desk on 8794)?"""
    from urllib.parse import urlsplit
    try:
        u = urlsplit(str(url))
        return u.scheme == "http" and u.hostname in ("127.0.0.1", "localhost") and bool(u.port)
    except ValueError:
        return False


def page_answers(url, timeout=0.5):
    """Does the door serving this local page take a connection? (A window on a door that has gone paints white.)"""
    import socket
    from urllib.parse import urlsplit
    u = urlsplit(str(url))
    try:
        with socket.create_connection((u.hostname, u.port), timeout=timeout):
            return True
    except OSError:
        return False


BAR_H = 66                 # the Agora strip along the bottom, in pixels
TOP_H = 60                 # a bar along the top (window.open <lens> edge=top)
# The desktop shell (shell builder, 26 Oct 2026; pages/shell/, shell_native.py, SHELL.md): view -> (name, page, bar kind).
SHELL_VIEWS = {"shell-top": ("Agora top bar", "top", "top"), "shell-dock": ("Agora dock", "dock", "bottom"),
               "shell-desktop": ("Agora desktop", "desktop", "layer")}

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
    # Title-free native identity, and the WM's geometry lease (agora-wm/WM.md).
    user32.SetPropW.argtypes = [wt.HWND, wt.LPCWSTR, wt.HANDLE]
    user32.GetPropW.argtypes = [wt.HWND, wt.LPCWSTR]
    user32.GetPropW.restype = wt.HANDLE

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

    def __init__(self, height, placed, edge="bottom"):
        self.height, self.placed, self.hwnd, self.rect, self.full = height, placed, None, None, False
        self.edge = edge                                      # "bottom" (ABE_BOTTOM 3) or "top" (ABE_TOP 1)
        self.ready = threading.Event()
        self.error = None
        self.stop_ev = threading.Event()
        shell32.SHAppBarMessage.restype = ctypes.c_size_t
        shell32.SHAppBarMessage.argtypes = [wt.DWORD, ctypes.POINTER(self.DATA)]
        threading.Thread(target=self._run, daemon=True, name="appbar").start()
        if not self.ready.wait(5) or self.error:
            raise RuntimeError(f'AppBar did not reserve its edge: {self.error or "timeout"}')

    def _run(self):
        try:
            self._loop()
        except Exception as exc:
            self.error = exc
            self.ready.set()

    def _data(self):
        d = self.DATA()
        d.cbSize, d.hWnd, d.uCallbackMessage = ctypes.sizeof(self.DATA), self.hwnd, self.CALLBACK
        d.uEdge = 1 if self.edge == "top" else 3
        return d

    def _setpos(self):
        (mx, my, mw, mh), _ = monitor()
        d = self._data()
        d.rc = wt.RECT(mx, my, mx + mw, my + mh)
        shell32.SHAppBarMessage(2, ctypes.byref(d))           # ABM_QUERYPOS: the shell moves it clear of other bars
        if self.edge == "top":
            d.rc.bottom = d.rc.top + self.height
        else:
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
        class_name = f'AgoraKernelAppBar{self.edge}{id(self)}'
        wc.lpfnWndProc, wc.lpszClassName = self._proc, class_name
        wc.hInstance = kernel32.GetModuleHandleW(None)
        user32.RegisterClassW(ctypes.byref(wc))
        user32.CreateWindowExW.restype = wt.HWND
        user32.CreateWindowExW.argtypes = [wt.DWORD, wt.LPCWSTR, wt.LPCWSTR, wt.DWORD, ctypes.c_int, ctypes.c_int,
                                           ctypes.c_int, ctypes.c_int, wt.HWND, wt.HMENU, wt.HINSTANCE, wt.LPVOID]
        self.hwnd = user32.CreateWindowExW(WS_EX_TOOLWINDOW, class_name, "Agora taskbar strip", 0, 0, 0, 0, 0,
                                           None, None, wc.hInstance, None)
        d = self._data()
        if not self.hwnd or not shell32.SHAppBarMessage(0, ctypes.byref(d)):  # ABM_NEW
            raise RuntimeError('Windows refused the AppBar')
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

    def resize(self, height):
        """The shell's pages say how much strip they need (their --ag-bar-height / --ag-dock-size): re-register it."""
        if height > 0 and height != self.height and self.rect:
            self.height = height
            self._setpos()

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

    def open(self, wid, view, title, url, box, on_closed, on_shown, bar=False, tucked=False):
        self.wins[wid] = {"box": box, "view": view, "title": title, "url": url, "min": bool(tucked)}
        if not tucked:
            self.front = wid
        threading.Thread(target=on_shown, daemon=True).start()

    def close(self, wid):
        self.wins.pop(wid, None)

    def reload(self, wid):
        if wid in self.wins:
            self.wins[wid]["reloads"] = self.wins[wid].get("reloads", 0) + 1

    def place(self, wid, box):
        if wid in self.wins:
            self.wins[wid]["box"] = box

    def box(self, wid):
        w = self.wins.get(wid)
        return w and w["box"]

    def shown(self, wid):
        w = self.wins.get(wid)
        return bool(w and not w["min"])

    def tuck(self, wid):
        if wid in self.wins:
            self.wins[wid]["min"] = True

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


def _page_visible(win):
    """Make a window's WebView2 page visible even though WinForms never showed the window (it was shown by Win32)."""
    def make():
        from System.Reflection import BindingFlags
        view = win.native.browser.webview
        field = view.GetType().GetField("_coreWebView2Controller", BindingFlags.NonPublic | BindingFlags.Instance)
        controller = field.GetValue(view) if field else None
        if controller is not None:
            controller.IsVisible = True
    try:
        from System import Func, Type
        win.native.Invoke(Func[Type](make))
    except Exception as exc:                            # noqa: BLE001  the window still opens; it may restore blank
        log(f"page visible: {exc!r}")


class GuiScreen(Screen):
    def __init__(self, module):
        import webview
        self.webview, self.module = webview, module
        self.wins = {}            # wid -> {"w": pywebview window, "hwnd": int, "view": str}
        self.closing = set()
        self.bars, self.bar_hidden = {}, {}     # wid -> AppBar, and whether it stepped back for a full-screen program
        self.lock = threading.Lock()
        from taskbar_guard import Lease
        self.taskbar_lease = Lease()

    def start(self, then):
        import widget_guard
        import window_profiles
        import window_transparency
        window_profiles.install()
        window_transparency.install()
        widget_guard.install()
        # pywebview needs a window before start: a hidden one that holds the loop and shows nothing
        self.anchor = self.webview.create_window("Agora window host", html="<html></html>", hidden=True,
                                                 width=200, height=100)
        self.webview.start(then, gui="edgechromium", private_mode=True)

    def open(self, wid, view, title, url, box, on_closed, on_shown, bar=False, tucked=False):
        s = scale()
        x, y, w, h = box
        api = None if view == "viewer" else PageApi(self, wid)
        glassy = view in SHELL_VIEWS and bar in ("top", "bottom")
        win = self.webview.create_window(title, url, js_api=api, x=int(x / s), y=int(y / s), width=max(200, int(w / s)),
                                         height=max(30, int(h / s)), frameless=view != "viewer", easy_drag=False, on_top=bool(bar) and bar != "layer", min_size=(120, 24),
                                         background_color="#F6F3EC", text_select=True, hidden=True, transparent=glassy)
        rec = {"w": win, "hwnd": None, "view": view, "bar": bar}
        with self.lock:
            self.wins[wid] = rec
        if glassy:
            win.agora_navigated = lambda ok: self._bar_page(wid, url, ok)   # window_transparency

        def shown_once():
            try:
                hwnd = int(win.native.Handle.ToInt64())
            except Exception:
                hwnd = user32.FindWindowW(None, title)
            rec["hwnd"] = hwnd
            user32.SetPropW(hwnd, "Agora.Window." + wid, wt.HANDLE(1))
            if bar:
                self._make_bar(wid, hwnd, bar)
            else:
                user32.SetWindowPos(hwnd, None, x, y, w, h, SWP_NOZORDER)
            on_shown()

        def loaded():
            if view == "viewer":
                return  # Viewer owns a separate native pane; the placeholder does not gate it.
            if rec["hwnd"] is None:
                if rec.get("page_failed"):
                    return                                  # an error page is never shown; _bar_page tries again
                if bar and bar != "layer":
                    # A bar is a tool window before it is ever visible. 27 Oct: shown first, it was for a moment a
                    # visible frameless Agora window, the window manager took the dock for a tile and moved it.
                    try:
                        early = int(win.native.Handle.ToInt64())
                        ex = user32.GetWindowLongPtrW(early, GWL_EXSTYLE)
                        user32.SetWindowLongPtrW(early, GWL_EXSTYLE, (ex | WS_EX_TOOLWINDOW) & ~WS_EX_APPWINDOW)
                        if glassy:
                            # dk1136: on glass before it is ever visible. Off glass, the transparent page drew the
                            # whole window white (3840x840, 2340x690) for the moment between this show and _make_bar.
                            import shell_native
                            shell_native.glass(early)
                    except Exception:
                        pass
                if tucked and not bar:
                    # A window tucked away before a restart comes back tucked, never shown first. 27 Oct: shown and
                    # then tucked, it looked newly opened to the window manager, which minimised Alex's Claude window
                    # to make room for it.
                    try:
                        early = int(win.native.Handle.ToInt64())
                        user32.SetPropW(early, "Agora.Window." + wid, wt.HANDLE(1))
                        user32.SetWindowPos(early, None, x, y, w, h, SWP_NOZORDER | SWP_NOACTIVATE)
                        user32.ShowWindow(early, 7)             # SW_SHOWMINNOACTIVE: on the taskbar, tucked, not active
                        # 28 Oct: shown past WinForms, the form still thinks it is hidden, so WebView2 keeps the page
                        # hidden and the window restores as a blank cream box (JEFF chat, Writing, map). Tell the page.
                        _page_visible(win)
                        rec["hwnd"] = early
                        on_shown()
                        return
                    except Exception:
                        pass
                win.show()
                time.sleep(0.15)
                shown_once()

        def closed():
            with self.lock:
                self.wins.pop(wid, None)
                mine = wid in self.closing
                self.closing.discard(wid)
            b = self.bars.pop(wid, None)
            if b:
                b.remove()
            if bar == 'bottom':
                self.taskbar_lease.release()
            if not mine:
                on_closed()
        win.events.loaded += loaded
        win.events.closed += closed
        if view == "viewer":
            import viewer
            viewer.attach(win, f"http://127.0.0.1:{PORT}", self.module.token)
            if tucked:
                early = int(win.native.Handle.ToInt64())
                user32.ShowWindow(early, 7)
                rec["hwnd"] = early
                user32.SetPropW(early, "Agora.Window." + wid, wt.HANDLE(1))
                on_shown()
            else:
                win.show()
                shown_once()

    def _make_bar(self, wid, hwnd, edge):
        view = (self.wins.get(wid) or {}).get("view")
        if edge == "layer":                                   # the desktop layer: no strip, bottom-most (shell_native)
            import shell_native
            self.layer_mode = shell_native.make_layer(hwnd, monitor()[0])
            return
        if edge == 'bottom':
            self.taskbar_lease.acquire()
        ex = user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
        user32.ShowWindow(hwnd, SW_HIDE)
        user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, (ex | WS_EX_TOOLWINDOW) & ~WS_EX_APPWINDOW)

        def placed(rect, top):
            x, y, w, h = rect
            user32.SetWindowPos(hwnd, HWND_TOPMOST, x, y, w, h, SWP_NOACTIVATE | SWP_FRAMECHANGED)
            if not self.bar_hidden.get(wid):
                user32.ShowWindow(hwnd, SW_SHOWNOACTIVATE)
        height = TOP_H if edge == "top" else BAR_H
        if view in SHELL_VIEWS:                               # the shell's bars: a strip reserved, a window of their own
            import shell_native
            shell_native.glass(hwnd)
            placed = shell_native.bar_placer(view, hwnd, lambda h: user32.ShowWindow(h, SW_SHOWNOACTIVATE), scale,
                                             lambda: not self._bar_may_show(wid))
            height = shell_native.initial_reserve(view, scale())
        self.bar_hidden[wid] = False
        try:
            self.bars[wid] = AppBar(height, placed, edge)
        except Exception:
            self.taskbar_lease.release()
            raise
        threading.Thread(target=self._step_back, args=(wid, hwnd), daemon=True, name="full-screen").start()

    def _step_back(self, wid, hwnd):
        """While another program is full screen (a game), the strip is hidden; it comes back when that ends. The
        shell's own notice (ABN_FULLSCREENAPP) did not reach it in a test (ran 23 Oct), so this looks for itself."""
        import gaming_gate
        mine = {hwnd}
        while wid in self.bars and user32.IsWindow(hwnd):
            fg = user32.GetForegroundWindow()
            full = False
            if fg and fg not in mine:
                if not gaming_gate.is_desktop(fg):           # Explorer's desktop or Agora's wallpaper layer
                    x, y, w, h = rect_of(fg)
                    (mx, my, mw, mh), _ = monitor()
                    full = x <= mx and y <= my and x + w >= mx + mw and y + h >= my + mh
            if full != self.bar_hidden.get(wid):
                self.bar_hidden[wid] = full
                if full:
                    user32.ShowWindow(hwnd, SW_HIDE)
                elif self._bar_may_show(wid):
                    user32.ShowWindow(hwnd, SW_SHOWNOACTIVATE)
                    user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOACTIVATE | SWP_NOMOVE | SWP_NOSIZE)
            time.sleep(0.5)

    def _bar_may_show(self, wid):
        rec = self.wins.get(wid) or {}
        return not self.bar_hidden.get(wid) and not rec.get("page_failed")

    def _bar_page(self, wid, url, ok):
        """A see-through bar's navigation ended (window_transparency; GUI thread). WebView2's error page is opaque and
        DWM does not clip it to the region, so a bar on one would be a big white block (dk1136): hidden, and its page
        tried again until it comes. A page that arrives shows the bar again (unless a game is full screen)."""
        rec = self.wins.get(wid)
        if not rec:
            return
        failed, rec["page_failed"] = rec.get("page_failed"), not ok
        hwnd = rec["hwnd"]
        if not ok:
            if hwnd:
                user32.ShowWindow(hwnd, SW_HIDE)
            if not failed:
                log(f"window {wid}: its page did not load; hidden, trying again every 5 s")

            def again():
                time.sleep(5)
                if self.wins.get(wid) is rec and rec.get("page_failed") and wid not in self.closing:
                    try:
                        # Not Window.load_url (it waits for `shown`, which a bar WinForms never showed never sets), nor
                        # the control's Source (it ignores the URL it already holds, the failed one): Navigate itself.
                        from System import Func, Type
                        form = rec["w"].native
                        rec["w"].events.loaded.clear()
                        form.Invoke(Func[Type](lambda: form.browser.webview.CoreWebView2.Navigate(url)))
                    except Exception as exc:            # noqa: BLE001  the next failure, if any, tries again
                        log(f"window {wid}: trying its page again: {exc!r}")
            threading.Thread(target=again, daemon=True, name="bar-page-again").start()
        elif failed:
            log(f"window {wid}: its page loaded")
            if hwnd and wid in self.bars and self._bar_may_show(wid):
                user32.ShowWindow(hwnd, SW_SHOWNOACTIVATE)

    def close(self, wid):
        with self.lock:
            rec = self.wins.get(wid)
            if rec:
                self.closing.add(wid)
        if rec:
            rec["w"].destroy()

    def reload(self, wid):
        """The page again from disk, in the same window: same place, same tuck, nothing closes."""
        rec = self.wins.get(wid)
        if rec:
            # run_js may wait for an answer the reloading page never gives: let it wait on its own thread
            threading.Thread(target=lambda: rec["w"].run_js("location.reload()"), daemon=True).start()

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

    def tuck(self, wid):
        rec = self.wins.get(wid)
        if rec and rec["hwnd"]:
            user32.ShowWindow(rec["hwnd"], 7)          # SW_SHOWMINNOACTIVE: tucked away as it was, never activated

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
        if user32.GetForegroundWindow() == h:
            return "brought forward"
        # Windows may refuse a background process keyboard focus. An explicit
        # open can still raise its ordinary window without stealing that focus.
        # Do not use topmost, synthetic input, or thread-input attachment.
        if user32.SetWindowPos(h, None, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE):
            return "raised without changing keyboard focus"
        return "Windows did not bring this window forward"

    def minimize(self, wid):
        rec = self.wins.get(wid)
        if rec and rec["hwnd"]:
            user32.ShowWindow(rec["hwnd"], SW_MINIMIZE)

    def shell_layout(self, wid, spec, dpr):
        """A shell page's report: {reserve: css px of strip, shape: [rounded rects in css px]}. Solid only there."""
        import shell_native
        rec = self.wins.get(wid)
        if not rec or not rec["hwnd"]:
            return False
        try:
            spec = json.loads(spec) if isinstance(spec, str) else spec
            dpr = float(dpr or scale())
        except (TypeError, ValueError):
            return False
        ok = shell_native.set_shape(rec["hwnd"], spec.get("shape") or [], dpr)
        bar = self.bars.get(wid)
        if bar and spec.get("reserve"):
            bar.resize(int(round(float(spec["reserve"]) * dpr)))
        return ok

    def shell_thumbs(self, wid, tiles, dpr):
        import shell_native
        rec = self.wins.get(wid)
        if not rec or not rec["hwnd"]:
            return 0
        th = rec.setdefault("thumbs", shell_native.Thumbs())
        try:
            tiles = json.loads(tiles) if isinstance(tiles, str) else tiles
        except ValueError:
            return 0
        return th.show(rec["hwnd"], tiles, float(dpr or scale())) if tiles else (th.clear() or 0)

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

    # -- the desktop shell's pages (pages/shell/shell.js Native.*, or a shell widget through window.native): shape,
    # reserved strip, DWM thumbnails, a live title. Only a shell window answers; any other page asking gets nothing
    # (26 Oct: before this, any page could clip its own window).
    def _shell(self):
        rec = self._screen.wins.get(self._wid) or {}
        return rec.get("view") in SHELL_VIEWS

    def layout(self, spec, dpr=1.5):
        return self._screen.shell_layout(self._wid, spec, dpr) if self._shell() else False

    def thumbs(self, tiles, dpr=1.5):
        return self._screen.shell_thumbs(self._wid, tiles, dpr) if self._shell() else 0

    def title(self, handle):
        if not self._shell():
            return ""
        import shell_native
        return shell_native.window_title(handle)

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


class Geometry:
    """Where each window sits on this screen: local, never in the world (Alex, 26 Oct: "visual state should not live
    in the world"). The world says which windows are open and what they show; where they are belongs to this desktop
    and its window manager. Kept in state/geometry.json so windows come back where they were after a restart."""

    def __init__(self, path):
        self.path, self.lock = path, threading.Lock()
        self.boxes, self.tucked = {}, set()
        if path and path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                self.tucked = set(data.pop("__tucked__", []))
                self.boxes = {k: tuple(v) for k, v in data.items()}
            except (OSError, ValueError):
                self.boxes, self.tucked = {}, set()

    def get(self, wid):
        return self.boxes.get(wid)

    def is_tucked(self, wid):
        return wid in self.tucked

    def put(self, wid, box=None, tucked=None):
        with self.lock:
            before = (self.boxes.get(wid), wid in self.tucked)
            if box is not None:
                self.boxes[wid] = tuple(int(v) for v in box)
            if tucked is not None:
                (self.tucked.add if tucked else self.tucked.discard)(wid)
            if self.path and before != (self.boxes.get(wid), wid in self.tucked):
                tmp = self.path.with_suffix(".tmp")
                tmp.write_text(json.dumps({**self.boxes, "__tucked__": sorted(self.tucked)}), encoding="utf-8")
                os.replace(tmp, self.path)


class WindowHost:
    def __init__(self):
        self.geo = Geometry(None if HEADLESS else HERE / "state" / "geometry.json")
        self.intent = {}               # name -> box a window.open asked for, until its window opens
        self.screen = MemScreen() if HEADLESS else GuiScreen(self)
        self.rows = {}                 # wid -> the window thing as last read
        self.applied = {}              # wid -> the box last put on the screen (or recorded from a drag)
        self.dead_pages = set()        # page windows whose door does not answer: said once, opened when it answers
        self.settle = {}               # wid -> (box, polls seen) while a drag settles
        self.widget_codes = {}
        self.opened = 0
        self.lock = threading.RLock()
        self.dirty = threading.Event()
        self.token = None
        self.world = None              # this world's folder (its blob store takes window.picture's bytes)
        self.wall_want, self.wall_said = None, ""   # the file `Shell settings` names as the wallpaper, and what came of it
        self.games_key = None          # the game lists last mirrored (follow_games)
        self.m = Module(offer=self.offer(), on_call=self.call, on_happen=self.happen, on_status=self.status,
                        on_hello=self.hello, on_off=self.off)

    # -- protocol
    def offer(self):
        spots = "left, right, center, big, top-left, top-right, bottom-left, bottom-right"
        return [
            {"word": "window.desktop", "kind": "see", "takes": "", "may": "anyone",
             "help": "window.desktop: running Windows task buttons, including minimized windows, with executable icons. Live only; no titles enter the log."},
            {"word": "window.activate", "kind": "do", "takes": "handle=<handle>", "may": "anyone",
             "help": "window.activate handle=<handle> [do=close]: bring a current Windows task button forward, or minimize it; do=close asks the window to close (WM_CLOSE, never a kill). External screen effect."},
            {"word": "window.start", "kind": "do", "takes": "", "may": "anyone",
             "help": "window.start: open Windows Start (Ctrl+Esc)."},
            {"word": "window.settings", "kind": "do", "takes": "which=network|volume|battery|time", "may": "anyone",
             "help": "window.settings which=network|volume|battery|time: open the corresponding Windows settings."},
            {"word": "window.launch", "kind": "do", "takes": "path=<exe>", "may": "anyone",
             "help": "window.launch path=<absolute executable or Start menu shortcut>: launch a pinned Windows program. A pin is a button with bar=taskbar, path=<exe> (its icon) and does=window.launch path=<exe or .lnk/.url> (a game starts through its Steam shortcut)."},
            {"word": "window.shell", "kind": "do", "takes": "on|off", "may": "anyone",
             "help": "window.shell on|off: the desktop shell (SHELL.md): a slim top bar, a centred dock and the theme's wallpaper "
                     "as the Windows wallpaper (wallpaper.py), in place of the old top bar and taskbar. on forgets the old bars' window "
                     "things and makes the three shell things; off forgets those, brings the taskbar back and puts the old Windows "
                     "wallpaper back. One act, so undo takes it back."},
            {"word": "window.list", "kind": "see", "takes": "[all]", "may": "anyone",
             "help": "window.list [all]: the Agora windows open on this desktop now, front first. With all, other "
                     "programs' windows too, as boxes and program ids, never their titles."},
            {"word": "window.open", "kind": "do", "takes": "<view> [<id>] [to=<spot>] [at=<x,y>] [size=<w,h>]", "may": "anyone",
             "help": f"window.open <lens or view> [thing] [to=<spot>|at=x,y size=w,h]: open a window on the desktop. Any "
                     f"lens in the world (rows lens lists them; window.open feed), or the views "
                     f"{', '.join(v for v in VIEWS if v != 'taskbar')}. Spots: {spots}. Only the desktop's owner "
                     f"(and their agents) open windows here. A view open already is brought forward instead; new=yes opens another. undo closes it. "
                     f"window.open url=<http://127.0.0.1:port/...> [name=<title>] opens a page from another Agora door on this machine "
                     f"(the top bar's JEFF button opens JEFF's conversation this way)."},
            {"word": "window.picture", "kind": "do", "takes": "<view|lens|thing> [size=<w>x<h>|screen] [name=<text>]",
             "may": "anyone",
             "help": "window.picture <what window.open takes> [size=WxH|screen] [name=<text>]: what that window would "
                     "show, drawn hidden (nothing appears on the screen), as your own private picture file. size=screen "
                     "is the screen's own size. In a line, $new is the picture: window.picture shell-desktop size=screen ; "
                     "set <Shell settings> wallpaper=$new makes it the Windows wallpaper."},
            {"word": "window.move", "kind": "do", "takes": "<id> [to=<spot>] [at=<x,y>] [size=<w,h>]", "may": "anyone",
             "help": f"window.move <window> to=<spot> | at=x,y [size=w,h]: put a window somewhere ({spots}). Changes "
                     f"the screen only (where a window sits is not in the world), so nothing is recorded."},
            {"word": "window.close", "kind": "do", "takes": "<id>", "may": "anyone", "acts_on": "window",
             "help": "window.close <window>: close it. Its window thing goes from the world; undo opens it again where "
                     "it was."},
            {"word": "window.reload", "kind": "do", "takes": "[<id>] [all]", "may": "anyone",
             "help": "window.reload <window> | all: load its page again from disk, in place (nothing closes or moves). "
                     "After editing pages/ (html, js, css) this is all it takes. Changes the screen only, so nothing "
                     "is recorded."},
            {"word": "window.focus", "kind": "do", "takes": "<id>", "may": "anyone", "acts_on": "window",
             "help": "window.focus <window>: bring it forward, or tuck it away if it is in front already (what a "
                     "taskbar button does). Changes the screen only, so nothing is recorded."},
            {"word": "window.opened", "kind": "hear", "takes": "<id>", "may": "anyone",
             "help": "window.opened: heard when a window this host opened is on the screen. "
                     "make kind=rule on=window.opened do=\"window.move $target to=right\" moves every new window."},
            {"word": "window.overlay", "kind": "hold", "takes": "", "may": "stewards",
             "help": "window.overlay: a see-through surface over this desktop, held while something runs (the little "
                     "guy holds it). Held by grant; holds lists who holds it, and off <module> ends the hold."},
            {"word": "window.surface", "kind": "hold", "takes": "", "may": "anyone",
             "help": "window.surface: a widget's page in a normal window, listed by holds and ended by off."},
            {"word": "window.bar", "kind": "hold", "takes": "", "may": "anyone",
             "help": "window.bar: a widget's slot inside an existing desktop bar, listed by holds and ended by off."},
            {"word": "window.native", "kind": "hold", "takes": "", "may": "stewards",
             "help": "window.native: the shell's bars only (SHELL.md). A widget painted in a shell window may tell that window "
                     "where it is solid (its click region) and what strip to reserve, lay DWM thumbnails over its own tiles, "
                     "and read one live window title. Given by a steward's grant; holds lists it, off ends it. Refused in "
                     "any window that is not a shell window."},
        ]

    def hello(self, msg):
        self.mid, self.owner = msg.get("id"), msg.get("owner")
        try:
            world = Path(msg["world"]) if msg.get("world") else Path(msg["home"]).parents[1]   # home: <world>/modules/<me>
            sessions = json.loads((world / "keep" / "sessions.json").read_text(encoding="utf-8"))
            self.token = next(t for t, v in sessions.items() if v.get("signer") == "alex")
        except (OSError, KeyError, StopIteration, ValueError) as exc:
            log(f"no desktop session for the pages: {exc!r}")
        try:
            self.world = Path(msg["world"]) if msg.get("world") else Path(msg["home"]).parents[1]
        except (KeyError, TypeError, IndexError):
            self.world = None
        self.dirty.set()

    # -- the wallpaper: Windows shows the file `Shell settings` names (wallpaper=<file>); none, Alex's own comes back
    def follow_wallpaper(self, want):
        if want == self.wall_want:
            return
        self.wall_want = want
        if HEADLESS or wallpaper_window():
            return
        threading.Thread(target=self._apply_wallpaper, args=(want,), daemon=True, name="wallpaper").start()

    def _apply_wallpaper(self, want):
        import hashlib
        import wallpaper
        try:
            if wallpaper.OFF.exists():
                self.wall_want = None                 # look again next time, so `wallpaper.py on` needs no restart
                said = "off (wallpaper.py restore); wallpaper.py on lets the setting through again"
                if said != self.wall_said:
                    self.wall_said = said
                    log("wallpaper: " + said)
                return
            if not want:
                self.wall_said = wallpaper.restore()
            else:
                # The original picture, from this world's own store (the door serves browsers only a cleaned copy of
                # an image; this host is on the same machine and checks the hash itself).
                row = next((r for r in (self.m.see("rows file").get("rows") or []) if r.get("id") == want), {})
                mime, digest = str(row.get("mime_type") or ""), str(row.get("blob_hash") or "")
                data = (self.world / "blobs" / digest).read_bytes() if digest and self.world else b""
                if not row or hashlib.sha256(data).hexdigest() != digest:
                    raise ValueError(f"{want} is not a file this host can read")
                ext = {"image/png": "png", "image/jpeg": "jpg", "image/bmp": "bmp"}.get(mime)
                if not ext:
                    self.wall_said = f"{want} is {mime}, not a picture Windows can show; the wallpaper is unchanged"
                else:
                    wallpaper.STATE.mkdir(parents=True, exist_ok=True)
                    pic = wallpaper.STATE / f"agora-{hashlib.sha256(data).hexdigest()[:16]}.{ext}"
                    if not pic.exists():
                        pic.write_bytes(data)
                    self.wall_said = f"{want} is the Windows wallpaper ({wallpaper.apply(pic)})"
        except Exception as exc:                      # noqa: BLE001  the wallpaper never stops the window host
            said = f"could not set {want or 'the old wallpaper'}: {exc!r}"
            self.wall_want = None                     # try again on the next reconcile
            if said == self.wall_said:
                return                                # the same failure again: said once
            self.wall_said = said
        log("wallpaper: " + self.wall_said)

    # -- the games: the world's game-settings, mirrored for every process that asks gaming_gate (door or not)
    def follow_games(self, rows):
        """games=<exe,...> are Alex's games (the window manager stands still and installers wait while one runs);
        not_games=<exe,...> never count, even filling the screen. Only a game-settings thing the desktop's owner made
        counts. Written to this machine's games.json when the lists change; a hidden test writes into its own world."""
        import re
        import gaming_gate
        mine = [r for r in rows if self.owner and self.owner in (r.get("made_by"), r.get("for"))]

        def names(field):
            out = set()
            for r in mine:
                for x in str(r.get(field) or "").split(","):
                    x = x.strip().lower()
                    if re.fullmatch(r"[a-z0-9 ._()+-]{1,80}\.exe", x):
                        out.add(x)
            return out
        key = (frozenset(names("games")), frozenset(names("not_games")))
        if key == self.games_key:
            return
        path = None
        if HEADLESS and not os.environ.get("AGORA_GAMES_FILE"):
            if not self.world:
                return
            path = self.world / "games.json"             # never the machine's own file from a hidden test
        gaming_gate.write_mirror(key[0], key[1], ",".join(r["id"] for r in mine), path)
        self.games_key = key
        log(f"games: {len(key[0])} games, {len(key[1])} never games, from {', '.join(r['id'] for r in mine) or 'nothing'}")

    # -- window.picture: what window.open would show, drawn hidden, handed back as the caller's picture file
    def picture_page(self, what, use):
        """-> (page path, default size, name) for what window.open takes: a view, a shell view, a lens, a thing."""
        w = (what or "").lower()
        if w in SHELL_VIEWS:
            return f"/desk/shell/{SHELL_VIEWS[w][1]}.html?hide=1", None, SHELL_VIEWS[w][0]
        if w in VIEWS and w != "taskbar":
            return f"/desk/{w}.html", VIEWS[w][1], VIEWS[w][0]
        wr = self.m.see("rows widget name=" + w, use=use)
        widget = next((r for r in wr.get("rows", []) if r.get("code") and r.get("on") and r.get("surface") == "window"), None)
        if widget:
            return f"/desk/widget.html?widget={quote(str(widget['id']))}", None, widget.get("title") or w
        lens = self.lens_named(w, use)
        if lens:
            return (f"/desk/frame.html?lens={quote(w)}&name={quote(str(lens.get('title') or w))}", LENS_SIZE,
                    lens.get("title") or w)
        r = self.m.see(f"look {what}", use=use)
        if r.get("refused") or not r.get("ok", True):
            return None, None, None
        return f"/desk/thing.html?target={quote(what)}", VIEWS["thing"][1], what

    def picture_word(self, what, kv, use):
        import re
        if not what:
            return {"refused": "window.picture needs what to draw: a view, a lens or a thing, as window.open takes"}
        path, default, name = self.picture_page(what, use)
        if path is None:
            return {"refused": f"no view, lens or thing called {what}; rows lens lists the lenses"}
        size, ratio = tuple(default or (1280, 800)), 1.0
        if kv.get("size") == "screen":
            size, ratio = tuple(monitor()[0][2:]), scale()
        elif kv.get("size"):
            m = re.fullmatch(r"(\d{2,5})x(\d{2,5})", str(kv["size"]))
            if not m:
                return {"refused": "size is WxH in pixels (size=1280x800), or size=screen"}
            size = (int(m.group(1)), int(m.group(2)))
        if size[0] * size[1] > 64_000_000:
            return {"refused": "that picture would be over 64 megapixels; ask for a smaller size"}
        if not self.world:
            return {"refused": "this window host does not know its world's folder, so it cannot hand over a picture"}
        sys.path.append(str(HERE.parents[1] / "kernel-lab"))
        from kernel.blobs import put                       # the world's own content-addressed store
        digest = put(self.world, self.picture(path, size, ratio))
        label = kv.get("name") or f"Picture of {name}"
        return {"lines": [f"upload name={json.dumps(label, ensure_ascii=False)} digest={digest}"], "saw": {}}

    def picture(self, path, size, pixel_ratio):
        """Draw a desktop page in the host's hidden browser (widget_browser: no window, ends with this process) as Alex,
        at size real pixels; -> PNG bytes. Waits until the page says it is ready and its pictures stop arriving."""
        import base64
        import widget_browser
        w, h = size
        cw, ch = max(1, round(w / pixel_ratio)), max(1, round(h / pixel_ratio))
        with widget_browser.Browser() as cdp:
            cdp.call("Emulation.setDeviceMetricsOverride", width=cw, height=ch, deviceScaleFactor=pixel_ratio,
                     mobile=False, screenWidth=cw, screenHeight=ch)
            cdp.call("Page.navigate", url=f"http://127.0.0.1:{PORT}/dev/signin?token={quote(self.token or '')}"
                                          f"&next={quote(path)}")
            end, seen, still = time.monotonic() + 7, -1, 0
            while time.monotonic() < end and still < 3:
                n = cdp.js("document.readyState === 'complete' && window.__ready !== false && "
                           "[...document.images].every(i => i.complete) ? performance.getEntriesByType('resource').length : -1")
                still = still + 1 if n is not None and n >= 0 and n == seen else 0
                seen = n
                time.sleep(0.15)
            shot = cdp.call("Page.captureScreenshot", format="png", fromSurface=True)
        return base64.b64decode(shot["data"])

    def off(self):
        try:
            log("off: closing every Agora window")
            for wid in list(self.screen.wins):
                self.screen.close(wid)
            for b in list(getattr(self.screen, "bars", {}).values()):
                b.remove()
            lease = getattr(self.screen, 'taskbar_lease', None)
            if lease:
                lease.release()
            time.sleep(0.3)
        finally:
            os._exit(0)             # whatever failed above, off always ends the process

    def status(self):
        n = len(self.screen.wins)
        views = ", ".join(sorted(r.get("shows", "?") for r in self.rows.values()))
        wall = f"; wallpaper: {self.wall_said}" if self.wall_said else ""
        return f"{n} window{'' if n == 1 else 's'} on the screen ({views or 'none'}); {self.opened} opened since start{wall}"

    def happen(self, h):
        # the kernel sends what this module's grants hear (hear:make, hear:set, ...); any of them may touch a window
        if h.get("word") in ("make", "set", "forget", "undo", "off"):
            self.dirty.set()

    def _owner_only(self, caller):
        if caller.get("person") != self.owner and caller.get("id") != self.owner                 and caller.get("person") not in self._stewards():
            return {"refused": "window opens and moves windows only for this desktop's owner, its stewards and their "
                               "agents"}
        return None

    def _stewards(self):
        """The people who lead this place (Alex, 27 Oct: JEFF a steward too), read with `who` (grant window
        words="who"), at most every two seconds."""
        now = time.monotonic()
        if now - getattr(self, "_stewards_at", -9) > 2:
            try:
                rows = self.m.see("who").get("rows") or []
                self._steward_ids = {r["id"] for r in rows if r.get("kind") == "person" and r.get("role") == "steward"}
            except Exception:
                self._steward_ids = getattr(self, "_steward_ids", set())
            self._stewards_at = now
        return self._steward_ids

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
            # read the window things inside the call, as the caller: they list only what they may see, and the read
            # counts as their look, so a `set` on a listed window needs no other look first
            r = self.m.see("rows window", use=use)
            return self.list_rows(all_="all" in words, only={x.get("id") for x in r.get("rows") or []})
        refused = self._owner_only(caller)
        if refused:
            return refused
        if word == 'window.desktop':
            if HEADLESS:
                return {'rows': [], 'text': 'no Windows tasks (headless)'}
            import native_shell
            mine = [r['hwnd'] for r in self.screen.wins.values() if r.get('hwnd')]
            rows = native_shell.windows(mine)
            if caller.get("person") != self.owner and caller.get("id") != self.owner:
                # a steward who isn't the owner (JEFF, a resident) sees which programs are open, never their titles:
                # a title is what's in the window (a chat, a mail subject). Interim until dk1095 (security review M5,
                # 28 Oct; JEFF: only Alex sees a native window unless he shares it)
                rows = [dict(r, name=r.get('program') or 'a window') for r in rows]
            pins = self.m.see('rows any bar=taskbar', use=use)
            for pin in pins.get('rows') or []:
                if pin.get('path'):
                    rows.append(dict(kind='pin-icon', id=pin['id'], icon=native_shell.executable_icon(pin['path'])))
            return {'rows': rows, 'text': f'{len(rows)} Windows task buttons'}
        if word in ('window.activate', 'window.start', 'window.settings', 'window.launch'):
            if HEADLESS:
                return {'external': True, 'text': f'{word} (headless: nothing pressed)'}
            import native_shell
            if word == 'window.activate':
                mine = [r['hwnd'] for r in self.screen.wins.values() if r.get('hwnd')]
                ok = native_shell.activate(kv.get('handle'), mine, kv.get('do') or '')
            elif word == 'window.start':
                ok = native_shell.start_menu()
            elif word == 'window.settings':
                ok = native_shell.settings(kv.get('which'))
            else:
                path = Path(kv.get('path', ''))
                # A program, or a Start menu shortcut (a Steam or Epic game starts through its launcher: Rocket League,
                # 27 Oct). Shortcuts only from the Start menu folders, so a pin cannot open an arbitrary file.
                starts = [Path(os.environ.get(v, '')) / 'Microsoft/Windows/Start Menu/Programs' for v in ('APPDATA', 'PROGRAMDATA')]
                shortcut = path.suffix.lower() in ('.lnk', '.url') and any(s in path.parents for s in starts if str(s) != '.')
                ok = path.is_absolute() and path.is_file() and (path.suffix.lower() == '.exe' or shortcut)
                if ok:
                    os.startfile(str(path))
            return {'external': True, 'text': f'{word}: done'} if ok else {'refused': 'that Windows target is not available now'}
        if word == "window.shell":
            mode = (words[0] if words else "").lower()
            if mode not in ("on", "off"):
                return {"refused": "window.shell on|off"}
            rows = self.m.see("rows window", use=use).get("rows") or []
            shell = [r for r in rows if r.get("shows") in SHELL_VIEWS]
            old = [r for r in rows if r.get("shows") not in SHELL_VIEWS and (r.get("shows") == "taskbar" or r.get("edge"))]
            if mode == "on":
                if shell:
                    return {"text": "the desktop shell is on already"}
                lines = [f"forget {r['id']}" for r in old]
                for view, (name, _page, bar) in SHELL_VIEWS.items():
                    lines.append(f"make kind=window shows={view} name={json.dumps(name)}"
                                 + (f" edge={bar}" if bar in ("top", "bottom") else " layer=bottom"))
                return {"lines": lines, "saw": {r["id"]: r["rev"] for r in old}}
            if not shell:
                return {"text": "the desktop shell is not on"}
            lines = [f"forget {r['id']}" for r in shell]
            lines.append(f'make kind=window shows=taskbar name="Agora taskbar" edge=bottom')
            self.made_bar = True
            return {"lines": lines, "saw": {r["id"]: r["rev"] for r in shell}}
        if word == "window.open":
            # Native reconciliation lags the admitted world. A just-closed window
            # can still be in self.rows; a just-opened one may not be there yet.
            # Decide reuse from the caller's current world, leaving disposal to reconcile.
            current = self.m.see("rows window", use=use)
            if current.get("ok") is False or "rows" not in current:
                return {"refused": "could not read current windows; try opening again"}
            open_rows = current["rows"] or []
        if word == "window.picture":
            return self.picture_word(target or (words[0] if words else ""), kv, use)
        if word == "window.open" and kv.get("url"):
            # A page from another Agora door on this machine in a window of its own (27 Oct: the top bar's JEFF
            # button opens JEFF's conversation, which lives in the frontier desk on 8794). Loopback http only.
            url = kv["url"]
            if not local_page(url):
                return {"refused": "url= takes a page on this machine only: http://127.0.0.1:<port>/... or http://localhost:<port>/..."}
            same = [r for r in open_rows if r.get("shows") == "page" and r.get("url") == url]
            if same and kv.get("new") != "yes":
                if same[0]["id"] not in self.screen.wins:
                    return {"text": f"{same[0].get('name')} is opening already (new=yes opens another)"}
                said = self.screen.focus(same[0]["id"]) if not self.screen.is_front(same[0]["id"]) else "in front already"
                return {"text": f"{same[0].get('name')} is open already: {said} (new=yes opens another)"}
            name = kv.get("name") or (words[0] if words else "Page")
            self.intent[name] = self.box_for("page", kv, 0)
            return {"lines": [f"make kind=window shows=page name={json.dumps(name, ensure_ascii=False)} url={json.dumps(url)}"],
                    "saw": {}}
        if word == "window.open":
            if not words:
                return {"refused": "window.open needs a view: " + ", ".join(v for v in VIEWS if v != "taskbar")}
            view = words[0].lower()
            lens = None
            widget = None
            if view not in VIEWS:
                lens = self.lens_named(view, use)
                wr = self.m.see('rows widget name=' + view, use=use)
                widget = next((r for r in wr.get('rows', []) if r.get('code') and r.get('on') and r.get('surface') == 'window'), None)
                if lens is None and widget is None:
                    return {"refused": f"no lens or view called {view}; rows lens lists the lenses, and the views are "
                                       f"{', '.join(v for v in VIEWS if v != 'taskbar')}"}
            thing = target or (words[1] if len(words) > 1 else "")
            same = [r for r in open_rows if r.get("shows") == view and (r.get("target") or "") == thing]
            if same and kv.get("new") != "yes" and view != "taskbar" and not (kv.get("to") or kv.get("at")):
                if same[0]["id"] not in self.screen.wins:
                    return {"text": f"{same[0].get('name')} is opening already (new=yes opens another)"}
                said = self.screen.focus(same[0]["id"]) if not self.screen.is_front(same[0]["id"]) else "in front already"
                return {"text": f"{same[0].get('name')} is open already: {said} (new=yes opens another)"}
            n = sum(1 for r in open_rows if r.get("shows") == view)
            edge = kv.get("edge") or ("bottom" if view == "taskbar" else "")
            if edge and edge not in ("top", "bottom"):
                return {"refused": "edge is top or bottom: a bar along that edge of the screen"}
            if edge and not lens and view != "taskbar":
                return {"refused": "only a lens (or the taskbar) can be a bar: window.open <lens> edge=top"}
            taken = [r for r in open_rows if r.get("edge") == edge] if edge else []
            if taken:
                return {"refused": f"the {edge} edge holds {taken[0].get('name')} already; window.close it first"}
            box = self.box_for(view, dict(kv, edge=edge), n)
            base = (lens.get("title") or view.capitalize()) if lens else (widget.get('title', view) if widget else VIEWS[view][0])
            name = base + (f" {n + 1}" if n and view != "taskbar" else "")
            self.intent[name] = box                       # where it opens is this screen's business, not the world's
            line = (f'make kind=window shows={view} name={json.dumps(name,ensure_ascii=False)}'
                    + (f" lens={view}" if lens else "") + (f" target={thing}" if thing else "")
                    + (f" widget={widget['id']}" if widget else "")
                    + (f" edge={edge}" if edge else ""))
            return {"lines": [line], "saw": {}}
        if word == "window.reload" and (target or (words[0] if words else "")).lower() == "all":
            ids = [w for w in list(self.screen.wins)]
            for wid in ids:
                self.screen.reload(wid)
            return {"text": f"{len(ids)} windows reloaded"}
        if word in ("window.move", "window.close", "window.focus", "window.reload"):
            row = self.row_for(target, use)
            if row is None:
                return {"refused": f"{target or 'that'} is not one of the windows open here; window.list shows them"}
            if word == "window.focus":
                return {"text": f"{row.get('name')}: {self.screen.focus(row['id'])}"}
            if word == "window.reload":
                self.screen.reload(row["id"])
                return {"text": f"{row.get('name')} reloaded"}
            if word == "window.close":
                return {"lines": [f"forget {row['id']}"], "saw": {row["id"]: row["rev"]}}
            if row.get("edge"):
                return {"refused": f"{row.get('name')} keeps its edge ({row.get('edge')}); close it instead"}
            box = self.box_for(row.get("shows"), kv, 0, current=self.screen.box(row["id"]) or self.geo.get(row["id"]))
            self.screen.place(row["id"], box)              # the screen moves; nothing is recorded in the world
            self.applied[row["id"]] = box
            self.geo.put(row["id"], box)
            return {"text": f"{row.get('name')} moved"}
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
        edge = kv.get("edge") or ("bottom" if view == "taskbar" else "")
        if edge == "bottom":
            return (wx, wy + wh - BAR_H, ww, BAR_H)
        if edge == "top":
            return (wx, wy, ww, TOP_H)
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

    def list_rows(self, all_=False, only=None):
        """only: the window ids the caller may see (None: all of them)."""
        rows = []
        z = self.screen.z_order() if hasattr(self.screen, "z_order") else []
        zi = {h: i for i, h in enumerate(z)}
        for wid, row in sorted(self.rows.items(), key=lambda x: x[0]):
            rec = self.screen.wins.get(wid)
            if rec is None or (only is not None and wid not in only):
                continue
            box = self.screen.box(wid)
            hwnd = rec.get("hwnd") if isinstance(rec, dict) else None
            rows.append({"id": wid, "kind": "window", "name": row.get("name"), "shows": row.get("shows"),
                         "target": row.get("target"), "edge": row.get("edge") or "", "box": list(box) if box else None,
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
        settings = (self.m.see("rows shell-settings").get("rows") or [{}])[0]
        self.follow_wallpaper(str(settings.get("wallpaper") or "").strip())
        games = self.m.see("rows game-settings")
        if not games.get("refused") and games.get("ok", True):
            self.follow_games(games.get("rows") or [])
        widgets = self.m.see('rows widget')
        active = {w['id']:w['code'] for w in widgets.get('rows',[]) if w.get('on') and w.get('code') and not w.get('forgotten')}
        want = {wid:row for wid,row in want.items() if not row.get('widget') or row['widget'] in active}
        with self.lock:
            if (not any(row.get("shows") == "taskbar" or row.get("shows") in SHELL_VIEWS for row in want.values())
                    and not getattr(self, "made_bar", False)):
                self.made_bar = True
                out = self.m.do('make kind=window shows=taskbar name="Agora taskbar" edge=bottom')
                log(f"taskbar: {out.get('text')}")
                return                                  # its happening brings us back here
            self.made_bar = True
            rows = want
            if not wallpaper_window():  # the wallpaper is Windows' own (follow_wallpaper), so the layer row opens no window
                want = {wid: row for wid, row in want.items() if not row.get("layer")}
            for wid in [w for w in list(self.screen.wins) if w not in want]:
                self.screen.close(wid)
                self.applied.pop(wid, None)
            for wid, row in want.items():
                box = (self.geo.get(wid) or self.intent.pop(row.get("name"), None) or parse_box(row)
                       or self.box_for(row.get("shows"), {"edge": row.get("edge") or ""}, 0))
                if row.get('widget') and wid in self.screen.wins and self.widget_codes.get(wid)!=active[row['widget']]:
                    self.screen.close(wid)
                    continue
                if wid not in self.screen.wins:
                    if row.get('widget'):self.widget_codes[wid]=active[row['widget']]
                    self._open(wid, row, box)
                elif self.applied.get(wid) != box and not row.get("edge") and not row.get("layer"):
                    self.screen.place(wid, box)
                    self.applied[wid] = box
            self.rows = rows

    def _open(self, wid, row, box):
        if row.get("shows") in SHELL_VIEWS:                   # the desktop shell: pages/shell/<page>.html
            view = row["shows"]
            path = f"/desk/shell/{SHELL_VIEWS[view][1]}.html?win={wid}"
        elif row.get('widget'):
            view = 'widget'
            path = f"/desk/widget.html?win={wid}&widget={quote(str(row['widget']))}"
            if row.get("target"):                         # a window opened on a thing: its lens sees $view.target
                path += f"&target={quote(str(row['target']))}"
        elif row.get("lens") and row.get("edge"):
            view = "bar"                                  # a bar is the lens alone: no strip to drag or close by
            path = f"/desk/bar.html?win={wid}&lens={quote(str(row['lens']))}&edge={row['edge']}"
        elif row.get("lens"):
            view = "frame"
            path = f"/desk/frame.html?win={wid}&lens={quote(str(row['lens']))}&name={quote(str(row.get('name') or ''))}"
        else:
            view = row.get("shows") if row.get("shows") in VIEWS else "thing"
            path = f"/desk/{view}.html?win={wid}" + (f"&target={quote(str(row['target']))}" if row.get("target") else "")
        title = f"{row.get('name') or VIEWS.get(view, SHELL_VIEWS.get(view, ('Agora',)))[0]} · Agora"
        # Sign in on the control door, then redirect to this window's listener.
        # Host cookies also cover the loopback ports; pages keep native EventSource.
        path = f"/desk/window-origin?win={quote(wid)}&next={quote(path, safe='')}"
        url = (f"http://127.0.0.1:{PORT}/dev/signin?token={quote(self.token)}&next={quote(path)}" if self.token
               else f"http://127.0.0.1:{PORT}{path}")
        if row.get("shows") == "page":                    # another door's page on this machine: no sign-in of ours
            if not local_page(row.get("url") or ""):
                log(f"window {wid}: url is not a page on this machine; not opened")
                return
            url = row["url"]
            if not page_answers(url):
                # 28 Oct: the old desk on 8794 was archived, and a JEFF window still showing it opened blank white.
                # Not opened; said once (in refusals); it opens by itself once its door answers again.
                if wid not in self.dead_pages:
                    self.dead_pages.add(wid)
                    from urllib.parse import urlsplit
                    why = (f"{row.get('name') or wid} shows a page at {urlsplit(url).netloc}, which is not answering, "
                           f"so it was not opened; window.close {wid} forgets it")
                    log(f"window {wid}: {why}")
                    try:
                        self.m.do(f"failed why={json.dumps(why)} where=window")
                    except Exception as exc:        # noqa: BLE001  refusals is a courtesy; the window stays shut
                        log(f"window {wid}: could not say failed: {exc!r}")
                return
            self.dead_pages.discard(wid)
        self.applied[wid] = box
        self.geo.put(wid, box)

        def on_shown():
            if self.geo.is_tucked(wid) and not row.get("edge") and not row.get("layer"):
                self.screen.tuck(wid)
            self.opened += 1
            self.m.happen("window.opened", wid, f"{row.get('name')} is on the screen")

        def on_closed():                                  # closed by Alex (Alt+F4) or by Windows: the world follows
            row2 = self.rows.get(wid) or row
            out = self.m.do(f"forget {wid}", saw={wid: row2.get("rev", 0)})
            log(f"{wid} closed on the screen: {out.get('text')}")
        bar = row.get("edge") or ("layer" if row.get("layer") else None) or ("bottom" if view == "taskbar" else None)
        self.screen.open(wid, view, title, url, box, on_closed, on_shown, bar=bar,
                         tucked=bool(self.geo.is_tucked(wid) and not bar))

    def watch_drags(self):
        """Every half second: a window Alex moved or resized and then left alone is recorded where he left it."""
        while True:
            time.sleep(0.5)
            for wid, row in list(self.rows.items()):
                if row.get("edge") or row.get("layer") or row.get("shows") == "taskbar":
                    continue
                # Local only, so it is kept even while the window manager places the window: a restart reopens
                # each window where it really was, tucked away if it was (live, 26 Oct: stale boxes overlapped).
                hwnd = (self.screen.wins.get(wid) or {}).get("hwnd")
                if hwnd:
                    self.geo.put(wid, tucked=bool(user32.IsIconic(hwnd)))
                box = self.screen.box(wid)
                if not box or box == self.applied.get(wid):
                    self.settle.pop(wid, None)
                    continue
                seen = self.settle.get(wid)
                if seen and seen[0] == box:
                    if seen[1] >= 2:
                        self.settle.pop(wid, None)
                        self.applied[wid] = box
                        self.geo.put(wid, box)                 # local only: a drag is not a world fact
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
