"""shell_native: the window side of the desktop shell (shell builder, 26 Oct 2026).

The shell pages (pages/shell/) are web pages in frameless WebView2 windows. What a page cannot do for itself lives here,
and kd_window.py calls it (PageApi.layout / thumbs / title, the bar placers, the desktop layer):

  * SHAPE. A WebView2 window is rectangular and, in windowed hosting, cannot be see-through (spike 1, shell_proof.py:
    transparent=True shows the host's grey, a colour key makes the whole window click-through on a composed desktop,
    SetWindowRgn clips both pixels and hit-testing). So a window is solid only where its page says: the page reports
    rounded rectangles in CSS pixels, and set_shape() turns them into one region (SetWindowRgn). What is round and
    smooth is drawn inside the region over a copy of the wallpaper (the page's own business).
  * RESERVE. The strip a bar needs is reserved by an AppBar of its own (kd_window.AppBar, an invisible window); the
    visible window is separate, so the dock can be a centred pill with room above it for menus. The page says how much
    to reserve (its own --ag-bar-height / --ag-dock-size), and AppBar.resize() re-registers the strip.
  * THUMBNAILS. DwmRegisterThumbnail draws a live picture of another window inside this one, over a placeholder the
    page leaves; window handles that are not numbers (a window manager's own keys) are not drawn, the placeholder stays.
  * THE DESKTOP LAYER. Since 27 Oct the default is no window at all: wallpaper.py renders the theme's wallpaper to a
    picture and sets it as the Windows wallpaper. The window below is the opt-in fallback (AGORA_DESKTOP_LAYER=bottom):
    a bottom-most tool window that draws the theme's wallpaper (kept at the bottom, never activated). AGORA_DESKTOP_LAYER=
    workerw tries the Progman/WorkerW attach; unverified on build 26200 (the structure there is DefView as a child of
    Progman, see SHELL.md).

Only documented user32/dwmapi/gdi32 calls, no hooks, no injection. (The system wallpaper is wallpaper.py's, not this file's.)
"""
import ctypes
import json
import os
import threading
import time
from ctypes import wintypes as wt

user32, gdi32, dwmapi = (ctypes.WinDLL(n, use_last_error=True) for n in ("user32", "gdi32", "dwmapi"))
user32.SetWindowPos.argtypes = [wt.HWND, wt.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wt.UINT]
user32.SetWindowRgn.argtypes = [wt.HWND, wt.HRGN, wt.BOOL]
user32.GetWindowRgn.argtypes = [wt.HWND, wt.HRGN]
user32.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
user32.GetClientRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
user32.IsWindow.argtypes = [wt.HWND]
user32.GetWindowTextW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
user32.GetWindowLongPtrW.argtypes = [wt.HWND, ctypes.c_int]
user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t
user32.SetWindowLongPtrW.argtypes = [wt.HWND, ctypes.c_int, ctypes.c_ssize_t]
user32.FindWindowW.restype = wt.HWND
user32.FindWindowW.argtypes = [wt.LPCWSTR, wt.LPCWSTR]
gdi32.CreateRoundRectRgn.restype = wt.HRGN
gdi32.CreateRoundRectRgn.argtypes = [ctypes.c_int] * 6
gdi32.CreateRectRgn.restype = wt.HRGN
gdi32.CreateRectRgn.argtypes = [ctypes.c_int] * 4
gdi32.CombineRgn.argtypes = [wt.HRGN, wt.HRGN, wt.HRGN, ctypes.c_int]
gdi32.DeleteObject.argtypes = [wt.HGDIOBJ]
dwmapi.DwmRegisterThumbnail.argtypes = [wt.HWND, wt.HWND, ctypes.POINTER(wt.HANDLE)]
dwmapi.DwmUnregisterThumbnail.argtypes = [wt.HANDLE]
dwmapi.DwmUpdateThumbnailProperties.argtypes = [wt.HANDLE, ctypes.c_void_p]

SWP_NOSIZE, SWP_NOMOVE, SWP_NOZORDER, SWP_NOACTIVATE, SWP_SHOWWINDOW = 0x1, 0x2, 0x4, 0x10, 0x40
HWND_BOTTOM, HWND_TOPMOST = wt.HWND(1), wt.HWND(-1)
GWL_EXSTYLE, WS_EX_TOOLWINDOW, WS_EX_NOACTIVATE, WS_EX_APPWINDOW = -20, 0x80, 0x08000000, 0x40000

# the window sizes pages are laid out for (CSS px): a bar is the strip plus room for a popover, the dock is a wider,
# taller window than its pill so menus and previews have somewhere to open. The rest is clipped away by the region.
TOP_ROOM_CSS = 560
DOCK_CSS = (1560, 460)
RESERVE_DEFAULT = {"top": 40, "bottom": 80}      # CSS px, until the page says what it needs


def _device(rect_css, dpr):
    x, y, w, h, r = (rect_css.get(k, 0) for k in ("x", "y", "w", "h", "r"))
    return int(round(x * dpr)), int(round(y * dpr)), int(round((x + w) * dpr)), int(round((y + h) * dpr)), int(round(r * dpr))


def build_region(shape, dpr, width, height):
    """A GDI region from the page's rounded rectangles (CSS px), clipped to the window. The caller owns nothing: the
    system owns the region once SetWindowRgn succeeds."""
    union = None
    for rc in shape:
        l, t, r_, b, rad = _device(rc, dpr)
        l, t, r_, b = max(0, l), max(0, t), min(width, r_), min(height, b)
        if r_ <= l or b <= t:
            continue
        one = (gdi32.CreateRoundRectRgn(l, t, r_ + 1, b + 1, 2 * rad, 2 * rad) if rad > 0
               else gdi32.CreateRectRgn(l, t, r_, b))
        if union is None:
            union = one
        else:
            gdi32.CombineRgn(union, union, one, 2)               # RGN_OR
            gdi32.DeleteObject(one)
    return union


class MARGINS(ctypes.Structure):
    _fields_ = [("l", ctypes.c_int), ("r", ctypes.c_int), ("t", ctypes.c_int), ("b", ctypes.c_int)]


def glass(hwnd):
    """See-through where the page is (Claude, 26 Oct, live). On Alex's real screen DWM does NOT clip a WebView2's
    drawing to the window region: the whole window rect showed white (ran: pixel (255,255,255) at 1900,400 under the
    top bar; spike 1 D's 'see-through' corner was that same white, read as a pass because hit-testing passed). So the
    window is a transparent WebView2 (pywebview transparent=True, black host) on a sheet of DWM glass: black and
    transparent pixels show what is behind. The region stays, for clicks only."""
    m = MARGINS(-1, -1, -1, -1)
    return dwmapi.DwmExtendFrameIntoClientArea(wt.HWND(hwnd), ctypes.byref(m)) == 0


def set_shape(hwnd, shape, dpr):
    r = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    rgn = build_region(shape, dpr, r.right - r.left, r.bottom - r.top)
    if rgn is None:
        return False
    if not user32.SetWindowRgn(hwnd, rgn, True):
        gdi32.DeleteObject(rgn)
        return False
    return True


# ---------------------------------------------------------------- where a bar's visible window goes
def bar_placer(view, hwnd, show, scale_fn, hidden_fn):
    """-> placed(rect, top): called by the AppBar with the strip it reserved (device px). The top bar's window is the
    strip's width and the strip's height plus room; the dock's window is centred on the strip, its bottom on the
    strip's bottom."""
    def placed(rect, _top):
        x, y, w, h = rect
        s = scale_fn()
        if view == "shell-top":
            ww, hh = w, int(TOP_ROOM_CSS * s)
            wx, wy = x, y
        else:
            ww, hh = min(w, int(DOCK_CSS[0] * s)), int(DOCK_CSS[1] * s)
            wx, wy = x + (w - ww) // 2, y + h - hh
        user32.SetWindowPos(hwnd, HWND_TOPMOST, wx, wy, ww, hh, SWP_NOACTIVATE)
        # Until the page says where it is solid (set_shape), only the reserved strip takes clicks. 27 Oct: the top bar's
        # page loaded a sign-in error, never sent its shape, and its whole 560 px window sat over Alex's screen.
        probe = gdi32.CreateRectRgn(0, 0, 0, 0)
        unshaped = user32.GetWindowRgn(hwnd, probe) == 0                          # ERROR: no region yet
        gdi32.DeleteObject(probe)
        if unshaped:
            top = 0 if view == "shell-top" else max(0, hh - h)
            strip = gdi32.CreateRectRgn(0, top, ww, top + min(h, hh))
            if not user32.SetWindowRgn(hwnd, strip, True):
                gdi32.DeleteObject(strip)
        if not hidden_fn():
            show(hwnd)
        if view == "shell-top":
            import performance_overlay
            performance_overlay.accommodate(hwnd)
    return placed


def initial_reserve(view, scale):
    return int((RESERVE_DEFAULT["top"] if view == "shell-top" else RESERVE_DEFAULT["bottom"]) * scale)


# ---------------------------------------------------------------- live thumbnails
class Thumbs:
    """DWM thumbnails of other windows drawn inside one of ours. One set at a time per window."""

    class PROPS(ctypes.Structure):
        _fields_ = [("flags", wt.DWORD), ("dest", wt.RECT), ("source", wt.RECT), ("opacity", ctypes.c_ubyte),
                    ("visible", wt.BOOL), ("client_only", wt.BOOL)]

    def __init__(self):
        self.ids = []

    def clear(self):
        for t in self.ids:
            try:
                dwmapi.DwmUnregisterThumbnail(t)
            except OSError:
                pass
        self.ids = []

    def show(self, dest_hwnd, tiles, dpr):
        """tiles: [{hwnd, x, y, w, h}] in CSS px of the destination window. Returns how many were drawn."""
        self.clear()
        n = 0
        for t in tiles:
            try:
                src = int(t.get("hwnd") or 0)
            except (TypeError, ValueError):
                continue
            if not src or not user32.IsWindow(src):
                continue
            tid = wt.HANDLE()
            if dwmapi.DwmRegisterThumbnail(dest_hwnd, src, ctypes.byref(tid)) != 0:
                continue
            rc = wt.RECT()
            user32.GetClientRect(src, ctypes.byref(rc))
            sw, sh = max(1, rc.right - rc.left), max(1, rc.bottom - rc.top)
            bw, bh = t["w"] * dpr, t["h"] * dpr
            k = min(bw / sw, bh / sh)
            w, h = int(sw * k), int(sh * k)
            x, y = int(t["x"] * dpr + (bw - w) / 2), int(t["y"] * dpr + (bh - h) / 2)
            p = self.PROPS(flags=0x1 | 0x4 | 0x8 | 0x10, dest=wt.RECT(x, y, x + w, y + h), opacity=255, visible=True, client_only=True)
            if dwmapi.DwmUpdateThumbnailProperties(tid, ctypes.byref(p)) == 0:
                self.ids.append(tid)
                n += 1
        return n


def window_title(handle):
    try:
        h = int(handle)
    except (TypeError, ValueError):
        return ""
    buf = ctypes.create_unicode_buffer(300)
    user32.GetWindowTextW(h, buf, 300)
    return buf.value


# ---------------------------------------------------------------- the desktop layer
def make_layer(hwnd, monitor_rect):
    """A bottom-most tool window over the whole monitor, never activated. Covers the desktop icons (what is lost, see
    SHELL.md); kept at the bottom of the normal windows by a small loop."""
    ex = user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
    user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, (ex | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE) & ~WS_EX_APPWINDOW)
    # Say "this is the desktop" so full-screen checks (bars stepping back, the guy hiding, the WM's game gate) do not
    # take the wallpaper for a game when a click puts it in front (gaming_gate.is_desktop reads it, any process).
    import gaming_gate
    user32.SetPropW.argtypes = [wt.HWND, wt.LPCWSTR, wt.HANDLE]
    user32.SetPropW(hwnd, gaming_gate.DESKTOP_PROP, wt.HANDLE(1))
    x, y, w, h = monitor_rect
    mode = os.environ.get("AGORA_DESKTOP_LAYER", "bottom")
    if mode == "workerw":
        if attach_workerw(hwnd, monitor_rect):
            return "workerw"
    user32.SetWindowPos(hwnd, HWND_BOTTOM, x, y, w, h, SWP_NOACTIVATE | SWP_SHOWWINDOW)

    def keep():
        while user32.IsWindow(hwnd):
            user32.SetWindowPos(hwnd, HWND_BOTTOM, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
            time.sleep(1.0)
    threading.Thread(target=keep, daemon=True, name="desktop-layer").start()
    return "bottom"


def attach_workerw(hwnd, monitor_rect):
    """The Progman/WorkerW method. Opt-in only. Sends the documented-by-use 0x052C message to Progman, then parents the
    window to the WorkerW that appears behind the icons (older builds) or to Progman itself (24H2 and later, where
    SHELLDLL_DefView is Progman's own child). Returns False, changing nothing, if neither structure is found."""
    progman = user32.FindWindowW("Progman", None)
    if not progman:
        return False
    out = ctypes.c_size_t()
    user32.SendMessageTimeoutW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM, wt.UINT, wt.UINT, ctypes.POINTER(ctypes.c_size_t)]
    user32.SendMessageTimeoutW(progman, 0x052C, 0xD, 0x1, 0x2, 1000, ctypes.byref(out))
    user32.FindWindowExW.restype = wt.HWND
    user32.FindWindowExW.argtypes = [wt.HWND, wt.HWND, wt.LPCWSTR, wt.LPCWSTR]
    user32.SetParent.argtypes = [wt.HWND, wt.HWND]
    target = None
    defview_in_progman = bool(user32.FindWindowExW(progman, None, "SHELLDLL_DefView", None))
    if defview_in_progman:
        target = progman                                     # 24H2+: the picture goes in as a child, behind DefView
    else:
        w = None
        while True:
            w = user32.FindWindowExW(None, w, "WorkerW", None)
            if not w:
                break
            if user32.FindWindowExW(w, None, "SHELLDLL_DefView", None):
                target = user32.FindWindowExW(None, w, "WorkerW", None)
                break
    if not target:
        return False
    user32.SetParent(hwnd, target)
    x, y, w, h = monitor_rect
    user32.SetWindowPos(hwnd, HWND_BOTTOM, 0, 0, w, h, SWP_NOACTIVATE | SWP_SHOWWINDOW)
    return True
