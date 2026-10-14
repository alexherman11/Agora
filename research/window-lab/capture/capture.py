"""The control screen, first prototype (a5062; Alex, e9743: 'control drag over my whole screen and whatever is there ...
you understand it ... Ideally just the world objects if its not a photo').

    python capture.py [--as alex] [--world frontier] [--draft a5082] [--door http://localhost:8794]
        hold Ctrl+Alt, drag over anything on any monitor, let go: a capture is made and its id printed.
        Escape during the drag cancels and nothing is made. Close this window (or Ctrl+C) to stop it.
    python capture.py --rect x,y,w,h      make one capture of that rectangle, with no gesture and nothing drawn
    python capture.py --show x,y,w,h      draw the selection there for two seconds and save a picture of it (a test)

What a capture holds (captures.py, beside reports.py): for each Agora window under the rectangle, the world objects the
painter drew there (world, item, subject, the words, the revision they were seen at), found by asking Windows' UI
Automation what lies on screen at that moment and matching each part to the page's scene by its role and words; and
pixels only for the parts of the rectangle that are not an Agora page, with the words Windows' own text recognition
finds in them. It is kept by the house, off the world, until Alex sends it; with --draft, its id is put on his chat
draft (do prop <draft> context=<id>), which is all of it that enters the world.

The key. Plain Ctrl+drag copies files in Explorer and extends selections in editors, so it is not taken. Holding
Ctrl+Alt shows an invisible catcher over every screen (the cursor becomes a cross), so only a Ctrl+Alt+click goes to
the capture; nothing hooks the keyboard or mouse, keys are only read (GetAsyncKeyState), and every key still reaches
the program it was meant for. The catcher never takes the keyboard focus. It does not arm while a full-screen program
(a game, a film) is in front, so it can never pull one out of full screen.
"""
import argparse
import ctypes
import json
import os
import queue
import subprocess
import sys
import threading
import time
import urllib.request
from ctypes import wintypes as wt
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

HERE = Path(__file__).resolve().parent
NOTATION = HERE.parent.parent / "text-desk-lab" / "notation"
sys.path.insert(0, str(NOTATION))
import captures  # noqa: E402

user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
dwmapi = ctypes.WinDLL("dwmapi")

LRESULT = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)
WNDENUMPROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
MONITORENUMPROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HMONITOR, wt.HDC, ctypes.POINTER(wt.RECT), wt.LPARAM)

WS_POPUP = 0x80000000
WS_EX_LAYERED, WS_EX_TRANSPARENT, WS_EX_TOOLWINDOW = 0x80000, 0x20, 0x80
WS_EX_TOPMOST, WS_EX_NOACTIVATE = 0x8, 0x08000000
LWA_ALPHA = 2
HWND_TOPMOST = -1
SWP_NOACTIVATE, SWP_SHOWWINDOW = 0x10, 0x40
SW_HIDE = 0
WM_TIMER, WM_LBUTTONDOWN, WM_LBUTTONUP, WM_MOUSEMOVE = 0x113, 0x201, 0x202, 0x200
WM_MOUSEACTIVATE, WM_CLOSE, WM_DESTROY = 0x21, 0x10, 0x2
MA_NOACTIVATE = 3
VK_CONTROL, VK_MENU, VK_ESCAPE, VK_LBUTTON = 0x11, 0x12, 0x1B, 0x01
GA_ROOT = 2
ARM_MS = 120              # Ctrl+Alt held this long before the catcher shows (a quick Ctrl+Alt+key never sees it)
TINT = (70, 140, 255)     # the selection's colour


class WNDCLASS(ctypes.Structure):
    _fields_ = [("style", wt.UINT), ("lpfnWndProc", WNDPROC), ("cbClsExtra", ctypes.c_int),
                ("cbWndExtra", ctypes.c_int), ("hInstance", wt.HINSTANCE), ("hIcon", wt.HICON),
                ("hCursor", wt.HANDLE), ("hbrBackground", wt.HBRUSH),
                ("lpszMenuName", wt.LPCWSTR), ("lpszClassName", wt.LPCWSTR)]


class MONITORINFOEXW(ctypes.Structure):
    _fields_ = [("cbSize", wt.DWORD), ("rcMonitor", wt.RECT), ("rcWork", wt.RECT), ("dwFlags", wt.DWORD),
                ("szDevice", wt.WCHAR * 32)]


def _sig(fn, res, *args):
    fn.restype, fn.argtypes = res, list(args)


_sig(user32.DefWindowProcW, LRESULT, wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)
_sig(user32.RegisterClassW, wt.ATOM, ctypes.POINTER(WNDCLASS))
_sig(user32.CreateWindowExW, wt.HWND, wt.DWORD, wt.LPCWSTR, wt.LPCWSTR, wt.DWORD, ctypes.c_int, ctypes.c_int,
     ctypes.c_int, ctypes.c_int, wt.HWND, wt.HMENU, wt.HINSTANCE, wt.LPVOID)
_sig(user32.SetWindowPos, wt.BOOL, wt.HWND, wt.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wt.UINT)
_sig(user32.ShowWindow, wt.BOOL, wt.HWND, ctypes.c_int)
_sig(user32.SetLayeredWindowAttributes, wt.BOOL, wt.HWND, wt.COLORREF, ctypes.c_byte, wt.DWORD)
_sig(user32.GetAsyncKeyState, ctypes.c_short, ctypes.c_int)
_sig(user32.GetCursorPos, wt.BOOL, ctypes.POINTER(wt.POINT))
_sig(user32.SetCapture, wt.HWND, wt.HWND)
_sig(user32.ReleaseCapture, wt.BOOL)
_sig(user32.SetTimer, ctypes.c_size_t, wt.HWND, ctypes.c_size_t, wt.UINT, wt.LPVOID)
_sig(user32.GetMessageW, ctypes.c_int, ctypes.POINTER(wt.MSG), wt.HWND, wt.UINT, wt.UINT)
_sig(user32.TranslateMessage, wt.BOOL, ctypes.POINTER(wt.MSG))
_sig(user32.DispatchMessageW, LRESULT, ctypes.POINTER(wt.MSG))
_sig(user32.PostQuitMessage, None, ctypes.c_int)
_sig(user32.LoadCursorW, wt.HANDLE, wt.HINSTANCE, wt.LPVOID)
_sig(user32.WindowFromPoint, wt.HWND, wt.POINT)
_sig(user32.GetAncestor, wt.HWND, wt.HWND, wt.UINT)
_sig(user32.GetForegroundWindow, wt.HWND)
_sig(user32.GetWindowRect, wt.BOOL, wt.HWND, ctypes.POINTER(wt.RECT))
_sig(user32.GetClassNameW, ctypes.c_int, wt.HWND, wt.LPWSTR, ctypes.c_int)
_sig(user32.GetWindowTextW, ctypes.c_int, wt.HWND, wt.LPWSTR, ctypes.c_int)
_sig(user32.GetWindowThreadProcessId, wt.DWORD, wt.HWND, ctypes.POINTER(wt.DWORD))
_sig(user32.MonitorFromWindow, wt.HMONITOR, wt.HWND, wt.DWORD)
_sig(user32.MonitorFromPoint, wt.HMONITOR, wt.POINT, wt.DWORD)
_sig(user32.GetMonitorInfoW, wt.BOOL, wt.HMONITOR, ctypes.POINTER(MONITORINFOEXW))
_sig(user32.EnumDisplayMonitors, wt.BOOL, wt.HDC, ctypes.POINTER(wt.RECT), MONITORENUMPROC, wt.LPARAM)
_sig(user32.GetSystemMetrics, ctypes.c_int, ctypes.c_int)
_sig(gdi32.CreateSolidBrush, wt.HBRUSH, wt.COLORREF)
_sig(kernel32.GetModuleHandleW, wt.HMODULE, wt.LPCWSTR)
_sig(kernel32.CreateMutexW, wt.HANDLE, wt.LPVOID, wt.BOOL, wt.LPCWSTR)
_sig(kernel32.OpenProcess, wt.HANDLE, wt.DWORD, wt.BOOL, wt.DWORD)
_sig(kernel32.CloseHandle, wt.BOOL, wt.HANDLE)
_sig(kernel32.QueryFullProcessImageNameW, wt.BOOL, wt.HANDLE, wt.DWORD, wt.LPWSTR, ctypes.POINTER(wt.DWORD))


def ms(t):
    return round((time.perf_counter() - t) * 1000)


def held(vk):
    return bool(user32.GetAsyncKeyState(vk) & 0x8000)


# --- the screen ---------------------------------------------------------------------------------------------------
def monitors():
    out = []

    def each(h, hdc, r, lp):
        mi = MONITORINFOEXW()
        mi.cbSize = ctypes.sizeof(mi)
        user32.GetMonitorInfoW(h, ctypes.byref(mi))
        dx, dy = wt.UINT(), wt.UINT()
        ctypes.WinDLL("shcore").GetDpiForMonitor(h, 0, ctypes.byref(dx), ctypes.byref(dy))
        m = mi.rcMonitor
        out.append({"index": len(out), "device": mi.szDevice, "rect": [m.left, m.top, m.right - m.left, m.bottom - m.top],
                    "scale": round(dx.value / 96, 3), "primary": bool(mi.dwFlags & 1), "h": h})
        return True

    user32.EnumDisplayMonitors(None, None, MONITORENUMPROC(each), 0)
    return out


def monitor_of(rect):
    """The monitor holding the most of the rectangle."""
    x, y, w, h = rect
    best = None
    for m in monitors():
        mx, my, mw, mh = m["rect"]
        a = max(0, min(x + w, mx + mw) - max(x, mx)) * max(0, min(y + h, my + mh) - max(y, my))
        if best is None or a > best[0]:
            best = (a, m)
    m = dict(best[1])
    m.pop("h", None)
    m.pop("primary", None)
    return m


def window_info(hwnd):
    t, c = ctypes.create_unicode_buffer(512), ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(hwnd, t, 512)
    user32.GetClassNameW(hwnd, c, 256)
    pid = wt.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    exe = ""
    hp = kernel32.OpenProcess(0x1000, False, pid.value)          # PROCESS_QUERY_LIMITED_INFORMATION
    if hp:
        buf, n = ctypes.create_unicode_buffer(1024), wt.DWORD(1024)
        if kernel32.QueryFullProcessImageNameW(hp, 0, buf, ctypes.byref(n)):
            exe = os.path.basename(buf.value)
        kernel32.CloseHandle(hp)
    r = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return {"hwnd": int(hwnd), "title": t.value, "class": c.value, "process": exe, "pid": pid.value,
            "wrect": [r.left, r.top, r.right - r.left, r.bottom - r.top]}


def windows_under(rect, ours=()):
    """{root hwnd: [points of the rectangle where it is the window on top]}, on a grid of at most 32 x 32 points.
    WindowFromPoint passes through click-through windows (window-lab's lights), as the mouse would."""
    x, y, w, h = rect
    nx, ny = max(2, min(32, w // 12)), max(2, min(32, h // 12))
    hits = {}
    for j in range(ny):
        for i in range(nx):
            p = wt.POINT(int(x + (i + 0.5) * w / nx), int(y + (j + 0.5) * h / ny))
            hw = user32.WindowFromPoint(p)
            root = user32.GetAncestor(hw, GA_ROOT) if hw else None
            if root and int(root) not in ours:
                hits.setdefault(int(root), []).append((p.x, p.y))
    return hits, nx * ny


def fullscreen_in_front():
    fg = user32.GetForegroundWindow()
    if not fg:
        return False
    info = window_info(fg)
    if info["class"] in ("Progman", "WorkerW", "Shell_TrayWnd"):
        return False
    mi = MONITORINFOEXW()
    mi.cbSize = ctypes.sizeof(mi)
    user32.GetMonitorInfoW(user32.MonitorFromWindow(fg, 2), ctypes.byref(mi))
    m = mi.rcMonitor
    x, y, w, h = info["wrect"]
    return x <= m.left and y <= m.top and x + w >= m.right and y + h >= m.bottom


# --- the helper (helper.ps1): UI Automation, the screen's pixels, Windows' text recognition --------------------------
class Helper:
    def __init__(self):
        self.p = subprocess.Popen(["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
                                   str(HERE / "helper.ps1")], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, encoding="utf-8", errors="replace",
                                  creationflags=0x08000000)      # CREATE_NO_WINDOW
        self.lock = threading.Lock()

    def ask(self, **q):
        with self.lock:
            self.p.stdin.write(json.dumps(q) + "\n")
            self.p.stdin.flush()
            line = self.p.stdout.readline()
        if not line:
            raise RuntimeError("the helper stopped")
        r = json.loads(line)
        if not r.get("ok"):
            raise RuntimeError(f"helper: {r.get('error')}")
        return r

    def close(self):
        try:
            self.p.stdin.close()
            self.p.wait(3)
        except Exception:
            self.p.kill()


# --- an Agora page: its scene, and the world objects drawn where the rectangle is ----------------------------------
def agora_page(url, door):
    """(session, as, lens) when url is a lens page of this door, else None."""
    if not url:
        return None
    u, d = urlparse(url), urlparse(door)
    if u.path.rstrip("/").split("/")[-1] != "lens.html" or u.port != d.port or u.hostname not in ("localhost", "127.0.0.1", d.hostname):
        return None
    q = {k: v[0] for k, v in parse_qs(u.query).items()}
    return (q.get("session", "desktop"), q.get("as", ""), q.get("lens", "")) if q.get("lens") else None


_scenes, _scene_lock = {}, threading.Lock()
PAGE_KEYS = "Enter,Tab,Shift+Tab,Backspace,Delete"          # what lens.js refresh() asks with (its build is then shared)


def scene(door, page, since=None):
    """The lens's scene as that viewer's own page asks for it (a read): the painter's view, with the page's own keys,
    so deskd answers from the build it just made for the page. The full scene costs 2.1 to 2.3 s on a busy world (ran
    14 Oct: deskd keys its builds on the world file's time, which residents change every few seconds). It is begun when
    the mouse goes down (prefetch) and a read begun since then is used. Returns (root, events_total)."""
    with _scene_lock:
        got = _scenes.get(page)
        if got and since is not None and got[2] >= since:
            return got[0], got[1]
        t = time.perf_counter()
        s, who, lens = page
        body = urllib.request.urlopen(f"{door}/api/scene?" + urlencode({"session": s, "as": who, "lens": lens, "view": "painter", "keys": PAGE_KEYS}), timeout=15).read()
        out = json.loads(body)
        if "scene" not in out:
            raise RuntimeError(out.get("refused") or "no scene")
        _scenes[page] = (out["scene"], out.get("events_total"), t)
        return out["scene"], out.get("events_total")


def prefetch(point, helper, door, ours=(), since=None, events=None):
    """When Ctrl+Alt arms and when the mouse goes down: if an Agora page is under the cursor, begin reading its scene
    (unless a read begun since `since` is kept), so the release need not wait. Reading is what the page itself does
    every 1.5 s; nothing is captured or kept by it."""
    hw = user32.WindowFromPoint(wt.POINT(*point))
    root = user32.GetAncestor(hw, GA_ROOT) if hw else None
    if not root or int(root) in ours or not window_info(root)["class"].startswith("Chrome_WidgetWin"):
        return
    try:
        page = agora_page(helper.ask(op="tree", hwnd=int(root)).get("url"), door)
        if page:
            _, count = scene(door, page, since=since if since is not None else time.perf_counter())
            if events:
                events.update(page[0], need=count)       # the log up to that scene, before the release asks
    except Exception:
        pass


def _norm(s):
    return " ".join(str(s or "").split()).casefold()


def _item_of_key(key):
    """The last id in a part's key ('review/.../docs/a4865/qt' -> a4865): a repeat keys each of its things by id."""
    for seg in reversed(str(key).split("/")):
        if len(seg) > 1 and seg[0] in "afs" and seg[1:].isdigit():
            return seg
    return None


def scene_nodes(root):
    """Every part that shows a world object, in the order painted, with its role and words. In the painter's view a
    part that can be acted on carries its fence (item, rev, and the subject it is bound to); a part that cannot (a
    card's body) is known by the id in its key, and takes its subject and rev from a fenced part of the same item."""
    out, fenced = [], {}

    def walk(n, up):
        p = n.get("paint") or {}
        if p.get("absent"):
            return
        f = n.get("fence") or {}
        item = f.get("item") or _item_of_key(n.get("key"))
        here = up
        if item:
            text = p.get("text") if p.get("text") is not None else ("".join(r.get("text", "") for r in p["runs"]) if p.get("runs") else None)
            bind = f.get("bind") if isinstance(f.get("bind"), dict) else {}
            here = {"key": n["key"], "item": item, "subject": bind.get("subject"), "role": p.get("role"), "rev": f.get("rev"),
                    "text": text, "up": up}
            if f.get("item") == item:
                fenced.setdefault(item, here)
            out.append(here)
        for k in n.get("kids") or []:
            walk(k, here)

    walk(root, None)
    for n in out:
        f = fenced.get(n["item"])
        if f:
            n["subject"] = n["subject"] or f["subject"]
            n["rev"] = n["rev"] if n["rev"] is not None else f["rev"]
        if not n["subject"] and n["item"][0] in "fs":
            n["subject"] = n["item"]                 # a surface is its own subject; an s-id is one
    return out


def covered(part, rect):
    """Is a part under the selection, as a person means it: at least a quarter of the part inside it, or the part
    filling half of it (a drag over one card brushes its neighbours by a few pixels; ran 14 Oct, a 6-pixel margin
    named the next card too)."""
    px, py, pw, ph = part
    x, y, w, h = rect
    iw, ih = min(px + pw, x + w) - max(px, x), min(py + ph, y + h) - max(py, y)
    if iw <= 0 or ih <= 0:
        return False
    i = iw * ih
    return i >= 0.25 * max(1, pw * ph) or i >= 0.5 * max(1, w * h)


def refs_from(parts, root, events_total, page, rect=None):
    """Name the world objects UI Automation found under the rectangle, exactly or not at all. The page gives each
    painted part its scene key as its id (id="part:<key>", Codex m5110), which UIA reads as the AutomationId (ran
    14 Oct, a page of my own); the key names one scene node, and so its item, subject and rev. A part with no such
    id (a page painted before that change) is never named from its words or role, which repeat (Codex m5105, Sable
    c5099): its ref says resolved=no and holds only what it showed. Returns refs, in screen order."""
    world, who, lens = page
    by_key = {n["key"]: n for n in scene_nodes(root)}
    found, loose = {}, {}
    framing = {p.get("up") for p in parts if p.get("words")}     # parts that hold a worded part: told by what they hold
    ids_here = any(p.get("aid") for p in parts)
    for i, p in enumerate(parts):
        if rect and not covered(p["rect"], rect):
            continue
        if p.get("aid"):
            n = by_key.get(p["aid"][len("part:"):])
            if n is None:
                continue                     # a part that shows no world object of its own (a lane, a column)
            ref = found.setdefault(n["item"], {"world": world, "item": n["item"], "subject": n["subject"], "kind": None,
                                               "resolved": "yes", "role": None, "lens": lens, "key": None, "words": [],
                                               "rev": n["rev"], "scene_count": events_total, "seen_event": None,
                                               "viewer": who, "_at": p["rect"][1::-1]})
            ref["words"].append(p.get("words") or n["text"] or "")
            outer = n
            while outer["up"] and outer["up"]["item"] == n["item"]:       # the card, not its title: the item's own part
                outer = outer["up"]
            ref["role"], ref["key"] = outer["role"], outer["key"]
        elif p.get("words") and p.get("roles") and i not in framing:
            sig = (p["roles"][0], _norm(p["words"]))
            loose.setdefault(sig, {"world": world, "resolved": "no", "role": p["roles"][0], "lens": lens,
                                   "words": p["words"], "viewer": who, "scene_count": events_total, "_at": p["rect"][1::-1],
                                   "why": "this part has no id on the page (not a recorded object, or painted before ids)"
                                   if ids_here else "the page gives its parts no ids (a painter from before them)"})
    out = sorted([*found.values(), *loose.values()], key=lambda r: r.pop("_at"))
    for r in out:
        if isinstance(r["words"], list):
            r["words"] = "\n".join(w for w in dict.fromkeys(r["words"]) if w)
    return out


# --- one capture --------------------------------------------------------------------------------------------------
def capture(rect, helper, args, ours=(), t0=None, since=None):
    t0 = t0 or time.perf_counter()
    timing = {}
    x, y, w, h = rect
    hits, total = windows_under(rect, ours)
    timing["windows"] = ms(t0)
    wins, refs, pixel_pts, native_pts = [], [], 0, 0
    for hwnd, pts in sorted(hits.items(), key=lambda kv: -len(kv[1])):
        info = window_info(hwnd)
        page, doc = None, None
        if info["class"].startswith("Chrome_WidgetWin"):
            try:
                t = helper.ask(op="tree", hwnd=hwnd, rect=list(rect))
                page, doc = agora_page(t.get("url"), args.door), t.get("doc")
            except RuntimeError as e:
                print("  (could not ask that window what it shows:", e, ")", flush=True)
        if page and doc:
            dx, dy, dw, dh = doc
            inside = [p for p in pts if dx <= p[0] < dx + dw and dy <= p[1] < dy + dh]
            native_pts += len(inside)
            timing["uia"] = ms(t0)
            try:
                root, total_ev = scene(args.door, page, since)
                timing["scene"] = ms(t0)
                named = refs_from(t["parts"], root, total_ev, page, rect)
                timing["named"] = ms(t0)
                if any(r["resolved"] == "yes" for r in named) and getattr(args, "events", None):
                    try:
                        args.events.update(page[0], need=total_ev)
                        for r in named:
                            if r["resolved"] == "yes":
                                r["seen_event"] = args.events.latest(page[0], [r["item"], r["subject"]], total_ev)
                    except Exception as e:      # the moment is then unknown, and says so (None), never guessed
                        print("  (the log was not read:", e, ")", flush=True)
                    timing["events"] = ms(t0)
                refs += named
            except Exception as e:
                print("  (the scene of", page, "was not read:", e, ")", flush=True)
            wins.append({"title": info["title"], "process": info["process"], "agora": True, "share": round(len(pts) / total, 3),
                         "world": page[0], "viewer": page[1], "lens": page[2]})
        else:
            pixel_pts += len(pts)
            wins.append({"title": info["title"], "process": info["process"], "agora": False, "share": round(len(pts) / total, 3)})
    pixel_pts += total - sum(len(p) for p in hits.values())       # points on no window at all are still pixels
    png, size, text, ocr = None, None, None, None
    if pixel_pts:                                                  # pixels only where they are needed
        tmp = captures.ROOT / f".grab-{os.getpid()}.png"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        g = helper.ask(op="grab", rect=list(rect), path=str(tmp), max=2048, maxbytes=2 * 1024 * 1024, ocr=True)   # Codex c5124
        png, size, ocr = tmp.read_bytes(), [g["w"], g["h"]], g.get("ocr")
        tmp.unlink(missing_ok=True)
        text = "\n".join(g.get("text") or []) or None
        timing["pixels"] = ms(t0)
    native = "none" if not refs else ("mixed" if png else "full")
    env = {"at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "monitor": monitor_of(rect), "rect": list(rect), "native": native,
           "refs": refs, "windows": wins, "image_size": size, "image_text": text,
           "text_recognition": None if png is None else ("windows" if ocr else "not available")}
    timing["made"] = ms(t0)
    env["timing_ms"] = timing
    cid = captures.make(args.world, args.who, env, png)
    timing["kept"] = ms(t0)
    return cid, env, timing


class Events:
    """Which event last changed each thing, from the log as pages read it (/api/events, no lock): read whole once
    (ran 14 Oct: 9,900 events in 2.35 s), then only what is new. Sable c5127: a ref's moment is an event's id (e<n>,
    the world's own name for it), never the scene's count of events, which differs once anything is undone."""

    def __init__(self, door, who):
        self.door, self.who, self.lock, self.seen = door, who, threading.Lock(), {}   # session -> [count read, {id: [(pos, eid)]}]

    def update(self, session, need=None):
        """Read what is new, unless what is held already reaches `need` events (a read is ~2 s whenever the world's
        file moved, ran 14 Oct, so it is skipped when the index already covers the scene)."""
        with self.lock:
            total, by = self.seen.setdefault(session, [0, {}])
            if need is not None and total >= need:
                return
            q = urlencode({"session": session, "as": self.who, "since": total})
            d = json.loads(urllib.request.urlopen(f"{self.door}/api/events?{q}", timeout=30).read())
            for i, e in enumerate(d.get("events") or [], start=total):
                for x in e.get("changed") or ([e["target"]] if e.get("target") else []):
                    by.setdefault(x, []).append((i, e.get("id")))
            self.seen[session][0] = d.get("total", total)

    def latest(self, session, ids, count):
        """The newest event among the first `count` (the scene's) that changed any of ids, or None."""
        best = None
        for x in ids:
            for pos, eid in reversed(self.seen.get(session, [0, {}])[1].get(x, [])):
                if pos < (count or 0):
                    best = max(best or (pos, eid), (pos, eid))
                    break
        return best and best[1]


def _do(args, line):
    if getattr(args, "do", None):          # a test's own desk (test_deliver.py: a copy of the world, through explore.py)
        return args.do(line)
    body =json.dumps({"session": args.world, "as": args.who, "line": line}).encode("utf-8")
    r = json.loads(urllib.request.urlopen(urllib.request.Request(f"{args.door}/api/do", data=body), timeout=15).read())
    t = r.get("error") or r.get("text") or ""
    return not (r.get("error") or "\nERR" in "\n" + t), t


DRAFT_MAX = 8            # Codex m5109, c5124: at most eight captures on a draft


def deliver(cid, args):
    """Put the capture's id on the person's draft: 'do prop <draft> context=<ids>' (Codex, Talk a4708 e9820, m5109).
    The draft is read just before, and the id joins those already there, in order, at most eight; if the draft
    changed between, the desk refuses and it is read again. Only the ids enter the world; the draft shows each as a
    chip, unsent until Send. Returns (ok, what was said)."""
    import re
    t = ""
    for _ in range(3):
        ok, t = _do(args, f"examine {args.draft}")
        if not ok:
            return False, t
        m = re.search(r"\bcontext=(.*)", t)            # up to the next prop (k=) or the next ' · '
        held = re.findall(r"cap-\d+", re.split(r"\s[\w-]+=|\s·", m.group(1))[0]) if m else []
        ids = list(dict.fromkeys([*held, cid]))
        if len(ids) > DRAFT_MAX:
            return False, f"the draft holds {DRAFT_MAX} captures already; {cid} is kept, not attached"
        ok, t = _do(args, f'do prop {args.draft} context="{" ".join(ids)}"')
        if ok:
            return True, t
        if "changed since" not in t and "since your last look" not in t:
            return False, t
    return False, t


def report(cid, env, timing, args):
    print(f"{cid}: {env['rect'][2]}x{env['rect'][3]} at {env['rect'][0]},{env['rect'][1]}, native={env['native']}, "
          f"{len(env['refs'])} world object(s), {'pixels ' + 'x'.join(map(str, env['image_size'])) if env['image_size'] else 'no pixels'}; "
          f"release to kept {timing['kept']} ms ({', '.join(f'{k} {v}' for k, v in timing.items())})", flush=True)
    for r in env["refs"]:
        words = " ".join(str(r["words"]).split())[:100]
        if r["resolved"] == "yes":
            print(f"   {r['world']} {r['item']} ({r['subject']}, {r['role']}, rev {r['rev']}, latest event {r['seen_event']}): {words}", flush=True)
        else:
            print(f"   not named exactly ({r['why']}): a {r['role']} in {r['lens']}: {words}", flush=True)
    if env.get("image_text"):
        print("   words in the pixels:", " ".join(env["image_text"].split())[:200], flush=True)
    if args.draft:
        try:
            ok, t = deliver(cid, args)
            print(f"   on the draft {args.draft}: " + ("yes" if ok else "no: " + t.strip().splitlines()[-1][:200]), flush=True)
        except Exception as e:
            print(f"   not put on the draft {args.draft}: {e}", flush=True)


# --- the overlay: an invisible catcher while Ctrl+Alt is held, and the selection as it is dragged -------------------
class Overlay:
    def __init__(self, on_done, on_down=None, on_arm=None):
        self.on_done, self.on_down, self.on_arm = on_done, on_down, on_arm
        self.proc = WNDPROC(self.wndproc)
        inst = kernel32.GetModuleHandleW(None)
        for name, cursor, colour in (("AgoraCaptureCatcher", 32515, 0), ("AgoraCaptureSelection", 32512,
                                                                         TINT[0] | TINT[1] << 8 | TINT[2] << 16)):
            c = WNDCLASS()
            c.lpfnWndProc, c.hInstance, c.lpszClassName = self.proc, inst, name
            c.hCursor = user32.LoadCursorW(None, ctypes.c_void_p(cursor))       # IDC_CROSS for the catcher
            c.hbrBackground = gdi32.CreateSolidBrush(colour)
            if not user32.RegisterClassW(ctypes.byref(c)):
                raise ctypes.WinError(ctypes.get_last_error())
            setattr(self, "cls_" + name[-8:].lower(), c)
        ex = WS_EX_LAYERED | WS_EX_TOOLWINDOW | WS_EX_TOPMOST | WS_EX_NOACTIVATE
        self.catcher = user32.CreateWindowExW(ex, "AgoraCaptureCatcher", "agora:capture", WS_POPUP, 0, 0, 1, 1, None, None, inst, None)
        user32.SetLayeredWindowAttributes(self.catcher, 0, 1, LWA_ALPHA)       # 1/255: invisible, and it takes the mouse
        # the selection: a tint and four edges, each a plain window of one colour, so a drag moves windows and paints nothing
        self.parts = []
        for alpha in (48, 230, 230, 230, 230):
            hw = user32.CreateWindowExW(ex | WS_EX_TRANSPARENT, "AgoraCaptureSelection", "agora:selection", WS_POPUP,
                                        0, 0, 1, 1, None, None, inst, None)
            user32.SetLayeredWindowAttributes(hw, 0, alpha, LWA_ALPHA)
            self.parts.append(hw)
        self.ours = {int(self.catcher), *(int(p) for p in self.parts)}
        self.armed_at, self.shown, self.start, self.last = None, False, None, None

    def show_catcher(self):
        vx, vy, vw, vh = (user32.GetSystemMetrics(i) for i in (76, 77, 78, 79))
        user32.SetWindowPos(self.catcher, HWND_TOPMOST, vx, vy, vw, vh, SWP_NOACTIVATE | SWP_SHOWWINDOW)
        self.shown = True
        if self.on_arm:
            p = wt.POINT()
            user32.GetCursorPos(ctypes.byref(p))
            self.on_arm((p.x, p.y))

    def hide(self):
        for hw in [self.catcher, *self.parts]:
            user32.ShowWindow(hw, SW_HIDE)
        self.shown = False

    def draw(self, rect):
        x, y, w, h = rect
        b = 2
        boxes = [(x, y, w, h), (x, y, w, b), (x, y + h - b, w, b), (x, y, b, h), (x + w - b, y, b, h)]
        for hw, (bx, by, bw, bh) in zip(self.parts, boxes):
            user32.SetWindowPos(hw, HWND_TOPMOST, bx, by, max(1, bw), max(1, bh), SWP_NOACTIVATE | SWP_SHOWWINDOW)

    def rect(self):
        p = wt.POINT()
        user32.GetCursorPos(ctypes.byref(p))
        (ax, ay), (bx, by) = self.start, (p.x, p.y)
        return [min(ax, bx), min(ay, by), abs(bx - ax) + 1, abs(by - ay) + 1]

    def cancel(self, why):
        user32.ReleaseCapture()
        self.start = None
        self.hide()
        print(f"cancelled ({why}): nothing captured", flush=True)

    def tick(self):
        """Every 15 ms: arm while Ctrl+Alt is held, disarm when let go, Escape cancels a drag."""
        if self.start is not None:
            if held(VK_ESCAPE):
                self.cancel("Escape")
            elif not held(VK_LBUTTON):          # the button came up somewhere the catcher did not hear it
                self.finish()
            return
        both = held(VK_CONTROL) and held(VK_MENU)
        if both and not self.shown:
            if self.armed_at is None:
                self.armed_at = time.perf_counter()
            elif (time.perf_counter() - self.armed_at) * 1000 >= ARM_MS and not held(VK_LBUTTON) and not fullscreen_in_front():
                self.show_catcher()
        elif not both:
            self.armed_at = None
            if self.shown:
                self.hide()

    def finish(self):
        r = self.rect()
        t0 = time.perf_counter()
        user32.ReleaseCapture()
        self.start = None
        self.hide()
        dwmapi.DwmFlush()                       # the selection is off the screen before its pixels are read
        if r[2] < 6 or r[3] < 6:
            print("cancelled (a click, not a drag): nothing captured", flush=True)
            return
        self.on_done(r, t0)

    def wndproc(self, hwnd, msg, wp, lp):
        if msg == WM_MOUSEACTIVATE:
            return MA_NOACTIVATE                # the program in front keeps the keyboard
        if hwnd == getattr(self, "catcher", None):       # (messages come while the windows are being made)
            if msg == WM_LBUTTONDOWN:
                p = wt.POINT()
                user32.GetCursorPos(ctypes.byref(p))
                self.start = (p.x, p.y)
                user32.SetCapture(hwnd)
                if self.on_down:
                    self.on_down(self.start)
                return 0
            if msg == WM_MOUSEMOVE and self.start is not None:
                self.draw(self.rect())
                return 0
            if msg == WM_LBUTTONUP and self.start is not None:
                self.finish()
                return 0
        if msg == WM_CLOSE:
            user32.PostQuitMessage(0)
            return 0
        return user32.DefWindowProcW(hwnd, msg, wp, lp)

    def run(self, seconds=None):
        user32.SetTimer(None, 0, 15, None)
        end = time.perf_counter() + seconds if seconds else None
        msg = wt.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            if msg.message == WM_TIMER and not msg.hWnd:
                self.tick()
                if end and time.perf_counter() > end and self.start is None:
                    break
            else:
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))


def main():
    ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))     # per-monitor v2: real pixels
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--as", dest="who", default="alex")
    ap.add_argument("--world", default="frontier")
    ap.add_argument("--draft", default=None, help="the draft note a capture's id is put on (Alex's: a5082)")
    ap.add_argument("--door", default="http://localhost:8794")
    ap.add_argument("--rect", help="x,y,w,h: capture this rectangle now, with no gesture")
    ap.add_argument("--windows", action="store_true", help="list the Agora pages on screen and where they are")
    ap.add_argument("--drag-ms", type=int, default=0, help="with --rect: begin as a mouse-down would, release this much later")
    ap.add_argument("--show",help="x,y,w,h: draw the selection there for two seconds and save a picture of it")
    ap.add_argument("--for", dest="seconds", type=float, default=None, help="stop by itself after this many seconds")
    ap.add_argument("--shot",default=str(HERE / "state" / "screen-selection.png"))
    args = ap.parse_args()
    args.door = args.door.rstrip("/")

    helper = Helper()
    args.events = Events(args.door, args.who)
    threading.Thread(target=lambda: args.events.update(args.world), daemon=True).start()   # the log, read once ahead
    try:
        t = time.perf_counter()
        ping = helper.ask(op="ping")
        print(f"helper ready in {ms(t)} ms; text recognition: {ping.get('lang') or 'not available'}", flush=True)
        if args.windows:
            found = []

            def each(hw, lp):
                if user32.IsWindowVisible(hw):
                    i = window_info(hw)
                    if i["class"].startswith("Chrome_WidgetWin") and i["wrect"][2] > 200:
                        found.append(i)
                return True

            user32.EnumWindows(WNDENUMPROC(each), 0)
            for i in found:
                t = helper.ask(op="tree", hwnd=i["hwnd"])
                page = agora_page(t.get("url"), args.door)
                if page:
                    print(f"{page[2]} as {page[1]} in {page[0]}: page at {t.get('doc')}", flush=True)
            print(f"({len(found)} browser windows looked at, {sum(1 for i in found if i['title'] == 'Lens')} titled Lens)", flush=True)
            return 0
        if args.rect:
            r = [int(v) for v in args.rect.split(",")]
            since = None
            if args.drag_ms:            # as a drag would: the mouse goes down at the corner, the release comes later
                since = time.perf_counter()
                threading.Thread(target=prefetch, args=((r[0], r[1]), helper, args.door, (), since, args.events), daemon=True).start()
                time.sleep(args.drag_ms / 1000)
            cid, env, timing = capture(r, helper, args, since=since)
            report(cid, env, timing, args)
            return 0
        if args.show:
            r = [int(v) for v in args.show.split(",")]
            ov = Overlay(lambda *a: None)
            ov.draw(r)
            time.sleep(0.4)
            pad = 40
            Path(args.shot).parent.mkdir(parents=True, exist_ok=True)
            g = helper.ask(op="grab", rect=[r[0] - pad, r[1] - pad, r[2] + 2 * pad, r[3] + 2 * pad], path=args.shot,
                           max=4096, ocr=False, blt=True)
            time.sleep(1.6)
            ov.hide()
            print(f"the selection was drawn at {r} and taken as {g['w']}x{g['h']}: {args.shot}", flush=True)
            return 0
        kernel32.CreateMutexW(None, False, "AgoraControlScreen")
        if ctypes.get_last_error() == 183:
            print("the control screen is already running", flush=True)
            return 76
        jobs, down = queue.Queue(), [None]

        def on_arm(point):
            down[0] = time.perf_counter()
            threading.Thread(target=prefetch, args=(point, helper, args.door, ov.ours, down[0], args.events), daemon=True).start()

        def on_down(point):
            threading.Thread(target=prefetch, args=(point, helper, args.door, ov.ours, down[0], args.events), daemon=True).start()

        ov = Overlay(lambda r, t0: jobs.put((r, t0)), on_down, on_arm)

        def worker():
            while True:
                r, t0 = jobs.get()
                if r is None:
                    return
                try:
                    cid, env, timing = capture(r, helper, args, ov.ours, t0, down[0])
                    report(cid, env, timing, args)
                except Exception as e:
                    print("capture failed:", type(e).__name__, e, flush=True)

        threading.Thread(target=worker, daemon=True).start()
        print(f"control screen on, as {args.who} in {args.world}" + (f", captures go on the draft {args.draft}" if args.draft else "")
              + ": hold Ctrl+Alt and drag; Escape cancels; Ctrl+C or closing this window stops it", flush=True)
        try:
            ov.run(args.seconds)
        except KeyboardInterrupt:
            pass
        ov.hide()
        jobs.put((None, None))
        print("control screen off", flush=True)
        return 0
    finally:
        helper.close()


if __name__ == "__main__":
    sys.exit(main())
