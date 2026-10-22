"""hud.py: the home base above the windows (a3874), JEFF's place on Alex's screen. 15 Oct 2026, a first prototype.

    python hud.py [--lens home-base] [--as alex] [--world frontier] [--show]     run it (one instance)
    python hud.py --stop                                                          end the running one

A bare tap of the Windows key (a5980, winkey.py), or Ctrl+Alt+J, shows it over everything, or hides it; Esc hides
it. Win chords (Win+D, Win+Shift+S ...) are Windows' as before; Start opens from Ctrl+Esc or the host verb `start`.
winkey=off on the lens note (within 15 s) or --winkey off gives the Win key back. Shown, it covers the main monitor, taskbar too (or only
its work area when the lens note says hide_taskbar=no; settings and host verbs in host_verbs.py, a5300) with the
painter (lens.html through the door) showing one lens, painted over a frosted copy of what was on the screen
the moment before. Hidden, it holds nothing on screen and takes no keys but Ctrl+Alt+J and a bare Win tap.

a5834: while it runs, so does the control screen (capture/capture.py, its child): hold Ctrl+Alt and drag over
anything, the home base too, and the capture goes on the person's own chat draft, unsent. capture=off on the lens
note turns it off (at the next Ctrl+Alt+J); on --stop the capture's parent guard ends it
within two seconds. Its output: state/capture.log.

a6113: the window manager (wm.py) is its child too, but only from the dock: the host verbs wm.start and wm.stop
(wm_switch.py). Closing the home base stops it; --stop, and the next start, put back whatever a killed one left.

What it is made of, from the research of 10 to 12 Oct (a3909):
  - a native Agora window: a frameless window of our own holding the browser engine that ships with Windows (WebView2,
    through pywebview), not Edge in app mode, so the window is ours to place, show, hide and draw into;
  - an overlay summoned by a key: an ordinary topmost window;
  - live copies of other programs' windows: Windows draws a live picture of any window into a window we own (DWM
    thumbnails). The lens says where: each part whose key names a desktop window (a repeat over witnessed:desktop,
    keyed by the window's handle) gets that window's picture drawn over it, fitted, and a click on it brings that
    window forward and hides the home base.
  - what it sees of the desktop it says as rows beside the house (witnessed.py, source `witnessed:desktop`): one row
    per program window, with name (its handle), title, program and front (yes for the window that was in front).

Tried and dropped (ran 15 Oct): a see-through page over the system's acrylic or mica backdrop. With WebView2 inside
WinForms the backdrop never showed through (three ways: DWM backdrop types 3 and 2 with the frame extended, and the
older accent blur); the window drew solid. So the frost is a still picture taken as the home base opens.
"""
import argparse
import base64
import ctypes
import io
import json
import os
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
from ctypes import wintypes as wt
from pathlib import Path
from hud_lifecycle import (Mutex, Scope, Windows, inventory, mutex_name, option,
                           other_hosts, pid_path, read_pid, remove_own_pid, script_args)

ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))      # per monitor v2: pixels are pixels

HERE = Path(__file__).resolve().parent
STATE = HERE / "state"
PIDFILE = STATE / "hud.pid"
NOTATION = HERE.parents[0] / "text-desk-lab" / "notation"
sys.path.insert(0, str(NOTATION))
import witnessed  # noqa: E402
import host_verbs  # noqa: E402  (a5300: what the home base can be asked, and its settings)
import media  # noqa: E402  (a5245: the music controller)
import winkey  # noqa: E402  (a5980: a bare tap of the Windows key)
import wm_switch  # noqa: E402  (a6113: the window manager, started and stopped from the dock)

user32, dwmapi, kernel32 = ctypes.windll.user32, ctypes.windll.dwmapi, ctypes.windll.kernel32
MOD_ALT, MOD_CONTROL, MOD_NOREPEAT = 0x1, 0x2, 0x4000
WM_HOTKEY, WM_QUIT, WM_APP = 0x0312, 0x0012, 0x8000
WM_SYSCOMMAND, SC_TASKLIST = 0x0112, 0xF130
VK_ESCAPE, VK_J = 0x1B, 0x4A
HK_TOGGLE, HK_ESC = 1, 2
GWL_EXSTYLE, WS_EX_TOOLWINDOW, WS_EX_APPWINDOW = -20, 0x80, 0x40000
DWMWA_CLOAKED = 14
GA_ROOTOWNER = 3
WNDENUMPROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)


def _sig(fn, res, *args):
    fn.restype, fn.argtypes = res, list(args)


_sig(user32.EnumWindows, wt.BOOL, WNDENUMPROC, wt.LPARAM)
_sig(user32.IsWindowVisible, wt.BOOL, wt.HWND)
_sig(user32.IsIconic, wt.BOOL, wt.HWND)
_sig(user32.IsWindow, wt.BOOL, wt.HWND)
_sig(user32.GetWindowTextW, ctypes.c_int, wt.HWND, wt.LPWSTR, ctypes.c_int)
_sig(user32.GetWindowTextLengthW, ctypes.c_int, wt.HWND)
_sig(user32.GetWindowLongW, ctypes.c_long, wt.HWND, ctypes.c_int)
_sig(user32.GetAncestor, wt.HWND, wt.HWND, wt.UINT)
_sig(user32.GetLastActivePopup, wt.HWND, wt.HWND)
_sig(user32.GetForegroundWindow, wt.HWND)
_sig(user32.SetForegroundWindow, wt.BOOL, wt.HWND)
_sig(user32.ShowWindow, wt.BOOL, wt.HWND, ctypes.c_int)
_sig(user32.GetWindowThreadProcessId, wt.DWORD, wt.HWND, ctypes.POINTER(wt.DWORD))
_sig(user32.RegisterHotKey, wt.BOOL, wt.HWND, ctypes.c_int, wt.UINT, wt.UINT)
_sig(user32.UnregisterHotKey, wt.BOOL, wt.HWND, ctypes.c_int)
_sig(user32.GetMessageW, ctypes.c_int, ctypes.POINTER(wt.MSG), wt.HWND, wt.UINT, wt.UINT)
_sig(user32.PostThreadMessageW, wt.BOOL, wt.DWORD, wt.UINT, wt.WPARAM, wt.LPARAM)
_sig(user32.PostMessageW, wt.BOOL, wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)
_sig(user32.SetWindowPos, wt.BOOL, wt.HWND, wt.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wt.UINT)
_sig(user32.MonitorFromPoint, wt.HMONITOR, wt.POINT, wt.DWORD)
_sig(user32.GetMonitorInfoW, wt.BOOL, wt.HMONITOR, ctypes.c_void_p)
_sig(user32.ClientToScreen, wt.BOOL, wt.HWND, ctypes.POINTER(wt.POINT))
_sig(dwmapi.DwmGetWindowAttribute, ctypes.c_long, wt.HWND, wt.DWORD, ctypes.c_void_p, wt.DWORD)
_sig(dwmapi.DwmRegisterThumbnail, ctypes.c_long, wt.HWND, wt.HWND, ctypes.POINTER(ctypes.c_void_p))
_sig(dwmapi.DwmUnregisterThumbnail, ctypes.c_long, ctypes.c_void_p)
_sig(dwmapi.DwmQueryThumbnailSourceSize, ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(wt.SIZE))
_sig(dwmapi.DwmUpdateThumbnailProperties, ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p)
_sig(kernel32.OpenProcess, wt.HANDLE, wt.DWORD, wt.BOOL, wt.DWORD)
_sig(kernel32.CloseHandle, wt.BOOL, wt.HANDLE)
_sig(kernel32.QueryFullProcessImageNameW, wt.BOOL, wt.HANDLE, wt.DWORD, wt.LPWSTR, ctypes.POINTER(wt.DWORD))
_sig(kernel32.GetCurrentThreadId, wt.DWORD)


class MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", wt.DWORD), ("rcMonitor", wt.RECT), ("rcWork", wt.RECT), ("dwFlags", wt.DWORD)]


class THUMB(ctypes.Structure):
    _fields_ = [("dwFlags", wt.DWORD), ("rcDestination", wt.RECT), ("rcSource", wt.RECT), ("opacity", ctypes.c_ubyte),
                ("fVisible", wt.BOOL), ("fSourceClientAreaOnly", wt.BOOL)]


TNP_RECTDESTINATION, TNP_RECTSOURCE, TNP_OPACITY, TNP_VISIBLE, TNP_SOURCECLIENTAREAONLY = 0x1, 0x2, 0x4, 0x8, 0x10


def work_area():
    m = user32.MonitorFromPoint(wt.POINT(0, 0), 1)
    mi = MONITORINFO()
    mi.cbSize = ctypes.sizeof(mi)
    user32.GetMonitorInfoW(m, ctypes.byref(mi))
    r = mi.rcWork
    return r.left, r.top, r.right - r.left, r.bottom - r.top


def whole_monitor(area):
    """The whole monitor that holds a work area, the taskbar's strip included (a5394)."""
    x, y, w, h = area
    mi = MONITORINFO()
    mi.cbSize = ctypes.sizeof(mi)
    user32.GetMonitorInfoW(user32.MonitorFromPoint(wt.POINT(x + w // 2, y + h // 2), 2), ctypes.byref(mi))
    r = mi.rcMonitor
    return r.left, r.top, r.right - r.left, r.bottom - r.top


def title_of(h):
    n = user32.GetWindowTextLengthW(h)
    buf = ctypes.create_unicode_buffer(n + 1)
    user32.GetWindowTextW(h, buf, n + 1)
    return buf.value


def program_of(h):
    pid = wt.DWORD()
    user32.GetWindowThreadProcessId(h, ctypes.byref(pid))
    hp = kernel32.OpenProcess(0x1000, False, pid.value)
    if not hp:
        return "", pid.value
    try:
        buf, size = ctypes.create_unicode_buffer(520), wt.DWORD(520)
        ok = kernel32.QueryFullProcessImageNameW(hp, 0, buf, ctypes.byref(size))
        return (Path(buf.value).stem if ok else ""), pid.value
    finally:
        kernel32.CloseHandle(hp)


def cloaked(h):
    v = wt.DWORD()
    dwmapi.DwmGetWindowAttribute(h, DWMWA_CLOAKED, ctypes.byref(v), ctypes.sizeof(v))
    return v.value != 0


def alt_tab_windows(skip_pid):
    """The windows Alt+Tab would offer, front first: visible, uncloaked, titled, not tool windows, their own root."""
    out = []

    def each(h, _):
        if not user32.IsWindowVisible(h) or cloaked(h):
            return True
        ex = user32.GetWindowLongW(h, GWL_EXSTYLE)
        if ex & WS_EX_TOOLWINDOW and not ex & WS_EX_APPWINDOW:
            return True
        if user32.GetAncestor(h, GA_ROOTOWNER) != h and not ex & WS_EX_APPWINDOW:
            return True
        t = title_of(h)
        if not t or t in ("Program Manager", "Windows Input Experience"):
            return True
        prog, pid = program_of(h)
        if pid == skip_pid:
            return True
        out.append({"name": str(h), "title": t, "program": prog, "minimized": "yes" if user32.IsIconic(h) else "no"})
        return True

    user32.EnumWindows(WNDENUMPROC(each), 0)
    return out


# a click on a part that shows a window's picture (a role named thumb, keyed by the window's handle) brings it forward
CLICKS = """(() => { if (window.__hudClicks) return; window.__hudClicks = 1;
  document.addEventListener('click', e => {
    const el = e.target.closest('[data-key]'); if (!el) return;
    const t = el.closest('[class*="thumb"]') || (el.className.indexOf('thumb') >= 0 ? el : null); if (!t) return;
    const m = /(?:^|[^0-9])(\\d{5,})(?:$|[^0-9])/.exec(t.dataset.key); if (!m) return;
    e.preventDefault(); e.stopPropagation(); window.pywebview.api.bring(m[1]);
  }, true); })()"""

# where the parts keyed by a window's handle are, in real pixels, and the box that shows of each
SLOTS = ("(() => { const out = []; const r0 = window.devicePixelRatio || 1;"
         " for (const el of document.querySelectorAll('[data-key]')) {"
         "  const m = /(?:^|[^0-9])(\\d{5,})(?:$|[^0-9])/.exec(el.dataset.key); if (!m) continue;"
         "  if (el.closest('[data-folded=\"1\"]') || el.hidden) continue;"
         "  const b = el.getBoundingClientRect(); if (b.width < 24 || b.height < 24) continue;"
         # a5736: what of it shows, inside every box that clips it and the window (a DWM picture paints over
         # everything, so a tile cut at a panel's foot drew its whole window over the dock below)
         "  let l = 0, t = 0, r = innerWidth, d = innerHeight;"
         "  for (let p = el.parentElement; p; p = p.parentElement) { const s = getComputedStyle(p);"
         "   if (s.overflowX === 'visible' && s.overflowY === 'visible') continue; const c = p.getBoundingClientRect();"
         "   l = Math.max(l, c.left); t = Math.max(t, c.top); r = Math.min(r, c.right); d = Math.min(d, c.bottom); }"
         "  out.push({key: el.dataset.key, h: m[1], x: b.left * r0, y: b.top * r0, w: b.width * r0, hh: b.height * r0,"
         "   clip: [l * r0, t * r0, r * r0, d * r0], slot: el.className.indexOf('thumb') >= 0});"
         " } return out; })()")


def fit(s, sw, sh):
    """-> (where on the page, which part of the window) for a slot from SLOTS and a window of sw x sh, or None.
    The window's picture is fitted into the slot; a5736: only what the slot's clipping boxes show of it is drawn,
    cropped from the source to match, and nothing when less than 40% of it shows (a sliver of a window reads as a
    glitch)."""
    sw, sh = max(1, sw), max(1, sh)
    k = min(s["w"] / sw, s["hh"] / sh)
    w, hh = int(sw * k), int(sh * k)
    x, y = int(s["x"] + (s["w"] - w) / 2), int(s["y"] + (s["hh"] - hh) / 2)
    cl, ct, cr, cb = s.get("clip") or (x, y, x + w, y + hh)
    vx, vy, vr, vb = max(x, int(cl)), max(y, int(ct)), min(x + w, int(cr)), min(y + hh, int(cb))
    if vr <= vx or vb <= vy or (vr - vx) * (vb - vy) < 0.4 * w * hh:
        return None
    return (vx, vy, vr, vb), (int((vx - x) / k), int((vy - y) / k), int((vr - x) / k), int((vb - y) / k))


class Hud:
    def __init__(self, a):
        self.a = a
        self.door = a.door.rstrip("/")
        self.capture = None           # a5834: the control screen, our child while capture=on
        self.window = None
        self.hwnd = None
        self.shown = False
        self.front = None             # the window that was in front when the home base opened
        self.thumbs = {}              # source hwnd -> (thumbnail id, last rect)
        self.keys_tid = None
        self.winkey = None            # a5980: the Win-key hook, while it is in
        self.lock = threading.Lock()
        self.settings = dict(host_verbs.DEFAULTS)

    def area(self):
        """Where it shows: the work area, or the whole monitor when hide_taskbar=yes (a5394). It covers the taskbar and
        never hides the taskbar's own window, so a home base that is put away, stopped or killed has nothing to restore."""
        a = host_verbs.work_area(self.settings["monitor"])
        return whole_monitor(a) if self.settings.get("hide_taskbar") == "yes" else a

    # -- the page
    def url(self):
        q = {"session": self.a.world, "as": self.a.who, "lens": self.a.lens, "inspect": "0"}
        return f"{self.door}/lens.html?{urllib.parse.urlencode(q)}"

    def frost(self):
        """A still, blurred and darkened copy of the work area as it is now, as a data address for the page."""
        from PIL import ImageGrab, ImageFilter, ImageEnhance
        x, y, w, h = self.area()
        im = ImageGrab.grab(bbox=(x, y, x + w, y + h)).convert("RGB")
        im = im.resize((max(1, w // 6), max(1, h // 6)))
        im = im.filter(ImageFilter.GaussianBlur(6))
        im = ImageEnhance.Brightness(ImageEnhance.Color(im).enhance(0.8)).enhance(0.42)
        b = io.BytesIO()
        im.save(b, "JPEG", quality=80)
        return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()

    def dress(self, frost):
        css = ("html{background:#0d100f url(%s) center/cover no-repeat fixed!important}"
               "body,#paint{background:transparent!important}") % frost
        self.window.evaluate_js(CLICKS)
        # a8901: any press in the home base stops the voice at once (voice.hush is nothing while it is quiet)
        self.window.evaluate_js("window.__voiceHush || (window.__voiceHush = 1, document.addEventListener('pointerdown',"
                                " () => { const a = window.pywebview && window.pywebview.api;"
                                " if (a && a.host) a.host('voice.hush', ''); }, true))")
        self.window.evaluate_js("(() => { let s = document.getElementById('hud-frost');"
                                " if (!s) { s = document.createElement('style'); s.id = 'hud-frost'; document.head.append(s); }"
                                " s.textContent = %s; })()" % json.dumps(css))

    # -- the desktop as rows
    def say_desktop(self):
        rows = alt_tab_windows(os.getpid())
        for r in rows:
            r["front"] = "yes" if self.front and r["name"] == str(self.front) else "no"
        # a6153: only what changed is written (the clock once a minute), and the pages are told only then: each rewrite
        # had every open lens built again, every 2 s, and a press landed behind that build
        wrote = [witnessed.write(self.a.world, "desktop", rows, by="hud", changed_only=True),
                 witnessed.write(self.a.world, "host", host_verbs.rows(), by="hud", changed_only=True),
                 witnessed.write(self.a.world, "media", media.rows(), by="hud", changed_only=True)]
        # a5496: the time, for the clock at the home base's top left (the taskbar's clock is hidden while it is open)
        now = time.localtime()
        wrote.append(witnessed.write(self.a.world, "clock", [{"time": time.strftime("%H:%M", now),
                                                              "day": time.strftime("%A %d %B", now).replace(" 0", " ")}],
                                     by="hud", changed_only=True))
        if not any(wrote):
            return rows
        self.tell_pages()
        return rows

    def tell_pages(self):
        """The door tells each open page that a witnessed source changed, so it is painted again (voice.py too)."""
        try:
            urllib.request.urlopen(urllib.request.Request(self.door + "/door/witnessed", data=b"{}", method="POST"),
                                   timeout=2).read()
        except OSError:
            pass

    # -- live pictures of windows, where the lens put their parts
    def slots(self):
        try:
            return self.window.evaluate_js(SLOTS) or []
        except Exception:
            return []

    def place_thumbs(self):
        if not self.shown:
            return
        want = {}
        for s in self.slots():
            if s["slot"]:
                want[int(s["h"])] = s
        with self.lock:
            for h in list(self.thumbs):
                if h not in want or not user32.IsWindow(h):
                    dwmapi.DwmUnregisterThumbnail(self.thumbs.pop(h)[0])
            for h, s in want.items():
                if not user32.IsWindow(h):
                    continue
                if h not in self.thumbs:
                    t = ctypes.c_void_p()
                    if dwmapi.DwmRegisterThumbnail(self.hwnd, h, ctypes.byref(t)) != 0:
                        continue
                    self.thumbs[h] = (t, "new")
                t, last = self.thumbs[h]
                size = wt.SIZE()
                dwmapi.DwmQueryThumbnailSourceSize(t, ctypes.byref(size))
                got = fit(s, size.cx, size.cy)
                if got == last:
                    continue
                if got:
                    p = THUMB(TNP_RECTDESTINATION | TNP_RECTSOURCE | TNP_OPACITY | TNP_VISIBLE | TNP_SOURCECLIENTAREAONLY,
                              wt.RECT(*got[0]), wt.RECT(*got[1]), 255, True, False)
                else:
                    p = THUMB(TNP_VISIBLE, wt.RECT(), wt.RECT(), 255, False, False)
                dwmapi.DwmUpdateThumbnailProperties(t, ctypes.byref(p))
                self.thumbs[h] = (t, got)

    def drop_thumbs(self):
        with self.lock:
            for t, _ in self.thumbs.values():
                dwmapi.DwmUnregisterThumbnail(t)
            self.thumbs.clear()

    # -- show and hide
    def show(self):
        if self.shown:
            return
        self.settings = host_verbs.settings(self.door, self.a.world, self.a.lens)     # a prop changed takes effect now
        self.tend_capture()
        fg = user32.GetForegroundWindow()
        self.front = fg if fg and fg != self.hwnd else None
        self.dress(self.frost())
        self.say_desktop()
        x, y, w, h = self.area()
        user32.SetWindowPos(self.hwnd, wt.HWND(-1), x, y, w, h, 0x40)         # topmost, shown
        self.window.show()
        user32.SetForegroundWindow(self.hwnd)
        self.shown = True
        if self.keys_tid:
            user32.PostThreadMessageW(self.keys_tid, WM_APP + 1, 1, 0)        # take Esc while shown
        self.window.evaluate_js("window.__hud && window.__hud.shown && window.__hud.shown()")

    def hide(self, to=None):
        if not self.shown:
            return
        self.shown = False
        if getattr(self, "voice", None) is not None:
            self.voice.stop("the home base was hidden")      # a8901: it never listens or speaks while put away
        self.drop_thumbs()
        self.window.hide()
        if self.keys_tid:
            user32.PostThreadMessageW(self.keys_tid, WM_APP + 1, 0, 0)
        target = to or self.front
        if target and user32.IsWindow(target):
            if user32.IsIconic(target):
                user32.ShowWindow(target, 9)
            user32.SetForegroundWindow(target)

    def toggle(self):
        self.hide() if self.shown else self.show()

    # -- the control screen (a5834): hold Ctrl+Alt and drag anywhere, the HUD too; the capture goes on the person's own
    # chat draft (jeff-chat shows it as a chip with its picture, unsent). Our child, so it lives and ends with us:
    # --stop ends the tree, and it ends itself when this process is gone (--parent). capture=off on the lens note
    # stops it at the next show.
    def tend_capture(self):
        want = self.settings.get("capture", "on") == "on"
        running = self.capture is not None and self.capture.poll() is None
        if want and not running:
            log = open(STATE / "capture.log", "a", encoding="utf-8")
            log.write(f"--- {time.strftime('%Y-%m-%d %H:%M:%S')} started by the home base {os.getpid()}\n")
            log.flush()
            self.capture = subprocess.Popen(
                [sys.executable, "-u", str(HERE / "capture" / "capture.py"), "--as", self.a.who, "--world", self.a.world,
                 "--door", self.door, "--draft", "auto", "--parent", str(os.getpid())],
                stdout=log, stderr=subprocess.STDOUT, creationflags=0x08000000)      # CREATE_NO_WINDOW
            log.close()
        elif not want and running:
            self.stop_capture()

    def stop_capture(self):
        if self.capture is not None and self.capture.poll() is None:
            native = Windows()
            processes = inventory(native)
            if processes is None:
                print("hud: capture stop deferred: process inventory unknown", flush=True)
                return
            for proc in processes:
                args = script_args(proc, str(HERE / "capture" / "capture.py"))
                if (proc.pid == self.capture.pid or proc.parent == self.capture.pid) and args is not None \
                        and option(args, "--parent", "") == str(os.getpid()):
                    print(f"hud: capture {proc.pid} created={proc.created}: {native.end(proc)}", flush=True)
        self.capture = None

    # -- what the page asks of the host (pywebview's js_api)
    def media(self, action):
        """A music button was pressed: press it, then say the new song soon after (a5245)."""
        did = media.press(action)
        threading.Timer(0.8, self.say_desktop).start()
        return did

    def bring(self, name):
        """A tile was clicked: that window comes forward and the home base gets out of the way."""
        try:
            h = int(name)
        except (TypeError, ValueError):
            return False
        self.hide(to=h)
        return True

    # -- keys
    def keys(self):
        self.keys_tid = kernel32.GetCurrentThreadId()
        mods, vk = host_verbs.hotkey(self.settings["hotkey"]) or (MOD_CONTROL | MOD_ALT, VK_J)      # read once
        registered = bool(user32.RegisterHotKey(None, HK_TOGGLE, mods | MOD_NOREPEAT, vk))
        if not registered:
            print(f"hud: {self.settings['hotkey']} is taken; retrying while the home base runs", flush=True)
        msg = wt.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            if msg.message == WM_HOTKEY and msg.wParam == HK_TOGGLE:
                self.toggle()
            elif msg.message == WM_HOTKEY and msg.wParam == HK_ESC:
                self.hide()
            elif msg.message == WM_APP + 2:                                       # a5980: a bare Win tap
                self.toggle()
            elif msg.message == WM_APP + 3 and not registered:
                registered = bool(user32.RegisterHotKey(None, HK_TOGGLE, mods | MOD_NOREPEAT, vk))
                if registered:
                    print(f"hud: {self.settings['hotkey']} is available again; registered", flush=True)
            elif msg.message == WM_APP + 1:
                if msg.wParam:
                    if not user32.RegisterHotKey(None, HK_ESC, MOD_NOREPEAT, VK_ESCAPE):
                        print("hud: Esc is taken by another program; the page's put-away still works", flush=True)
                else:
                    user32.UnregisterHotKey(None, HK_ESC)
        user32.UnregisterHotKey(None, HK_TOGGLE)

    # a5980: a bare tap of the Windows key. The hook lives on its own thread (winkey.Hook) and posts the toggle to the
    # keys thread, so a slow show never holds up a key on the machine. This guard puts the hook in and takes it out:
    # out while winkey=off (the lens note, read every 15 s; --winkey off) and while a full-screen program is in front,
    # so no Python of ours sits in a game's input path. --stop, a crash or a kill take it out with the process.
    def winkey_tap(self):
        if self.keys_tid:
            user32.PostThreadMessageW(self.keys_tid, WM_APP + 2, 0, 0)

    def guard_winkey(self):
        me, n, said, slow = os.getpid(), 0, None, (0, 0)
        while True:
            if self.keys_tid:
                user32.PostThreadMessageW(self.keys_tid, WM_APP + 3, 0, 0)  # an old duplicate may have held the key
            if self.winkey and self.winkey.on:
                if n % 60 == 59:
                    self.winkey.reseat()                  # Windows drops a slow hook without a word: put it back
                got = (self.winkey.slow, self.winkey.dropped)
                if got != slow:
                    print(f"hud: the Win-key hook was slow {got[0]} time(s) (slowest "
                          f"{self.winkey.slowest * 1000:.0f} ms); {got[1]} time(s) Windows had dropped it", flush=True)
                    slow = got
            if n % 15 == 14:
                s = host_verbs.settings(self.door, self.a.world, self.a.lens)
                if s.get("read"):                         # a door that did not answer keeps what we had
                    self.settings = s
            n += 1
            off = "--winkey off" if self.a.winkey == "off" else \
                "winkey=off on the lens note" if self.settings.get("winkey") == "off" else \
                "a full-screen program is in front" if winkey.fullscreen_in_front(me) else ""
            try:
                if not off and not (self.winkey and self.winkey.on):
                    self.winkey = winkey.Hook(self.winkey_tap, may=lambda: winkey.why_not(me),
                                              log=lambda t: print("hud:", t, flush=True))
                    off = "" if self.winkey.start() else "the hook did not go in"
                elif off and self.winkey:
                    self.winkey.stop()
                    self.winkey = None
            except Exception as e:
                off = f"{type(e).__name__}: {e}"
            now = off or "on"
            if now != said:
                what = "shows and hides the home base" if now == "on" else "is Windows' own: " + now
                print("hud: the Win key " + what, flush=True)
                said = now
            time.sleep(1)

    def open_start(self):
        """The host verb `start` (a5980): Windows' Start menu, asked for as a window menu does; no key is pressed."""
        if self.hwnd:
            user32.PostMessageW(self.hwnd, WM_SYSCOMMAND, SC_TASKLIST, 0)

    def tend(self):
        """While shown: the desktop's rows every two seconds, the pictures placed every quarter second."""
        n = 0
        while True:
            time.sleep(0.25)
            if not self.shown:
                continue
            n += 1
            try:
                if n % 4 == 0 and getattr(self, "voice", None) is not None:
                    self.voice.tick()                 # a8901: silence, a game or the switch end a listening
                if n % 8 == 0:
                    self.say_desktop()
                self.place_thumbs()
            except Exception as e:
                print("hud: tend:", e, flush=True)

    def started(self):
        for _ in range(200):                     # a window made hidden has its form a moment after the loop starts
            if self.window.native is not None:
                break
            time.sleep(0.05)
        self.hwnd = wt.HWND(self.window.native.Handle.ToInt64())
        # out of Alt+Tab and the taskbar: the home base is reached by its key
        ex = user32.GetWindowLongW(self.hwnd, GWL_EXSTYLE)
        ctypes.windll.user32.SetWindowLongW(self.hwnd, GWL_EXSTYLE, (ex | WS_EX_TOOLWINDOW) & ~WS_EX_APPWINDOW)
        # a6113: what it can be asked is so from its start, not only once it has been shown (the dock reads it)
        witnessed.write(self.a.world, "host", host_verbs.rows(), by="hud")
        threading.Thread(target=self.keys, daemon=True).start()
        threading.Thread(target=self.tend, daemon=True).start()
        threading.Thread(target=self.guard_winkey, daemon=True).start()
        self.tend_capture()
        if self.a.show:
            time.sleep(1.5)
            self.show()

    def closed(self):
        if self.winkey:
            self.winkey.stop()
        self.stop_capture()
        try:
            wm_switch.SWITCH.stop(self)               # a6113: the window manager it started puts everything back
        except Exception as e:
            print("hud: window manager stop:", e, flush=True)
        witnessed.clear(self.a.world, "wm")
        witnessed.clear(self.a.world, "desktop")
        media.stop()                                  # a6443: the media session's reader (smtc.ps1) ends with it
        witnessed.clear(self.a.world, "media")
        witnessed.clear(self.a.world, "clock")
        witnessed.clear(self.a.world, "host")
        if getattr(self, "voice", None) is not None:          # a8901: the speech child ends with the home base
            self.voice.stop("the home base closed")
            self.voice.engine.close()
        witnessed.clear(self.a.world, "voice")
        if self.keys_tid:
            user32.PostThreadMessageW(self.keys_tid, WM_QUIT, 0, 0)
        remove_own_pid(PIDFILE, os.getpid())

    def run(self):
        import webview
        self.settings = host_verbs.settings(self.door, self.a.world, self.a.lens)
        x, y, w, h = host_verbs.work_area(self.settings["monitor"])
        self.window = webview.create_window("Agora home base", self.url(), js_api=Api(self), x=x, y=y, width=w,
                                            height=h, frameless=True, on_top=True, hidden=True, easy_drag=False,
                                            background_color="#0D100F", text_select=True)
        self.window.events.closed += self.closed
        webview.start(self.started, gui="edgechromium", private_mode=False,
                      storage_path=str(STATE / "hud-webview"))


class Api:
    def __init__(self, hud):
        self._hud = hud

    def bring(self, name):
        return self._hud.bring(name)

    def media(self, action):
        return self._hud.media(action)

    def hide(self):
        self._hud.hide()
        return True

    def host(self, verb, words=""):
        """A lens's `on click host <verb> [words]` (a5300): 'ok ...' or 'ERR ...', never raises."""
        return host_verbs.call(self._hud, verb, words)


def main():
    global PIDFILE
    ap = argparse.ArgumentParser()
    ap.add_argument("--lens", default="home-base")
    ap.add_argument("--as", dest="who", default="alex")
    ap.add_argument("--world", default="frontier")
    ap.add_argument("--show", action="store_true", help="open shown, not waiting for the key")
    ap.add_argument("--stop", action="store_true", help="end the running home base (and its control screen)")
    ap.add_argument("--door", default="http://127.0.0.1:8794", help="the desk's door (a copy's, for a test)")
    ap.add_argument("--winkey", choices=("on", "off"), default="on",
                    help="off: the Win key stays Windows' whatever the lens note says (a5980)")
    a = ap.parse_args()
    STATE.mkdir(parents=True, exist_ok=True)
    PIDFILE = pid_path(STATE, a.world, a.door)
    native = Windows()
    scope = Scope(str(HERE / "hud.py"), str(NOTATION / "keeper.py"), a.world, a.door)
    if a.stop:
        processes = inventory(native)
        if processes is None:
            print("hud: stop refused: process inventory unknown; pid file preserved", flush=True)
            return 75
        hosts = scope.hosts(processes)
        # Interpreter first, launcher afterwards. Every end checks the original
        # creation time and executable on the exact handle it terminates.
        for proc in sorted(hosts, key=lambda p: p.created, reverse=True):
            result = native.end(proc)
            print(f"hud: stop {proc.pid} created={proc.created}: {result}", flush=True)
        remaining = inventory(native)
        if remaining is None or scope.hosts(remaining):
            print("hud: stop not confirmed; pid file preserved", flush=True)
            return 75
        for proc in hosts:
            remove_own_pid(PIDFILE, proc.pid)
        wm_switch.release_left()                      # a6113: put back a killed window manager's windows
        witnessed.clear(a.world, "desktop")
        witnessed.clear(a.world, "media")
        witnessed.clear(a.world, "clock")
        witnessed.clear(a.world, "host")
        witnessed.clear(a.world, "wm")
        return 0
    guard = Mutex(native, mutex_name(a.world, a.door))
    if not guard.acquire():
        print("hud: already running (home-base OS mutex exists); exiting", flush=True)
        return 76
    claimed = False
    try:
        # Existing hosts from before the mutex change must also block a start.
        processes = inventory(native)
        if processes is None or read_pid(PIDFILE) is None:
            print("hud: start deferred: process inventory or pid record unknown", flush=True)
            return 75
        others = other_hosts(processes, scope, os.getpid(), os.getppid())
        if others:
            print("hud: already running as", ", ".join(str(p.pid) for p in others), flush=True)
            return 76
        PIDFILE.write_text(str(os.getpid()))
        claimed = True
        wm_switch.release_left()                      # a6113: put back a killed window manager's windows
        witnessed.clear(a.world, "wm")
        print("hud: running; a bare Win tap or Ctrl+Alt+J shows or hides it, Esc hides it, `python hud.py --stop` ends it",
              flush=True)
        Hud(a).run()
        return 0
    finally:
        try:
            if claimed:
                remove_own_pid(PIDFILE, os.getpid())
        finally:
            guard.close()


if __name__ == "__main__":
    sys.exit(main())
