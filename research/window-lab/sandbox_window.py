"""sandbox_window: real windows Alex cannot see or feel, on a desktop of their own (a5932, Alex 16 Oct: "it needs to be
able to test in a window that is not mine ... Taking over my screen for interactive tests is not an option").

    python research/window-lab/sandbox_window.py open <url|test-page> [--size 1500x900] [--name sb]   Edge, hidden
    python research/window-lab/sandbox_window.py run [--name sb] [--cdp] <command ...>        any program, hidden
    python research/window-lab/sandbox_window.py windows [--name sb] [--tree]   the windows on the sandbox desktop
    python research/window-lab/sandbox_window.py click <x> <y> [--name sb] [--right] [--client]   CSS px of the page
    python research/window-lab/sandbox_window.py type <text> [--name sb]
    python research/window-lab/sandbox_window.py key <Enter|Escape|Tab|Backspace|ArrowDown|Ctrl+b|...> [--name sb]
    python research/window-lab/sandbox_window.py js <expression> [--name sb]
    python research/window-lab/sandbox_window.py shot out.png [--name sb] [--page]
    python research/window-lab/sandbox_window.py film <seconds> out.mp4 [--name sb] [--fps 10] [--page]
    python research/window-lab/sandbox_window.py close [--name sb]         verified recorded owners only; retains receipts
    python research/window-lab/sandbox_window.py test [webview]            proves it on a harmless page (and WebView2)

screen.py --visible uses it: the painter of a world copy in a real Edge window here, driven by its steps.
`run --cdp python research/window-lab/hud.py ...` puts a pywebview (WebView2) app here with a DevTools port; click and
type then go to the child window under the point and the window with the focus. --client: x y are the window's client
pixels, for a window with no DevTools.

HOW. Windows lets one session hold several desktops (CreateDesktop); only one, the input desktop, is drawn on the
monitor and gets the keyboard and mouse. `open` makes a desktop named agora-sandbox-<name> in Alex's own window station
and starts Edge on it (CreateProcess with lpDesktop). The window is a real Win32 window with a real renderer, its own
focus and its own foreground, but on a desktop that is never switched to (this file never calls SwitchDesktop), so
nothing of it reaches his monitor, his foreground window, his focus, his cursor or his keyboard. No install, no setting:
the desktop is gone when the last process on it ends.

Input goes to the window only: click, type and key post Win32 messages (WM_LBUTTONDOWN, WM_CHAR, WM_KEYDOWN) to the
window's own queue from a thread joined to the sandbox desktop. SendInput is never used (it types into the INPUT
desktop, his). A held modifier (Ctrl+b) cannot be posted (Windows keeps the key state per input queue), so a key with
a modifier, and `js`, go through Edge's DevTools port instead. `shot` is PrintWindow of the whole window (frame and
all, as Windows composes it); --page is the page alone, as the renderer draws it (DevTools). `film` strings shots
together with ffmpeg. A bare file name goes to research/window-lab/demos/ of the main checkout, as screen_tools does.

Every verb measures Alex's side before and after: the foreground window, the focused window, the cursor and which
desktop has the input; it says `alex: untouched` or names what changed. `test` polls them every 20 ms through a whole
open-type-click-shot-film-close and fails if any changes, or if a window of ours ever becomes his foreground.

What it shares with his desktop (same window station): the clipboard and global atoms. Don't copy or paste in a test.
What it can't do: SendInput, drag and drop between windows (OLE), and DWM thumbnails (DwmRegisterThumbnail) of its
windows are not tried (a desktop no one sees is, as I understand it, not composed by DWM; unchecked). PrintWindow
with PW_RENDERFULLCONTENT does draw them, GPU pages included (ran 16 Oct: WebGL on the RTX 2080 Ti, D3D11).
Edge runs InPrivate: a fresh Edge profile signs itself into Alex's Microsoft account and syncs (seen 16 Oct).
AGORA_TMP chooses scratch space inside this worktree (relative paths start at its root); by default it is
research/window-lab/.tmp-agora. State, profiles, film frames and child TMP/TEMP use that same directory.
Cleanup cannot certify unregistered/headless browser children. It retains state/profiles and refuses automatic
retry while their ownership is unknown. Legacy PID-only manifests need explicit host-owner reconciliation.
"""
import base64
import ctypes
import json
import os
import subprocess
import sys
import threading
import time
import urllib.request
from ctypes import wintypes as wt
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import agora_tmp

agora_tmp.configure()  # before STATE, profiles, films, and any child process
import screen_tools  # noqa: E402  (DPI awareness first; ffmpeg and demos/)

u32, k32, g32 = ctypes.windll.user32, ctypes.windll.kernel32, ctypes.windll.gdi32
STATE = agora_tmp.configure() / "agora-sandbox"
EDGE = next((p for p in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                         r"C:\Program Files\Microsoft\Edge\Application\msedge.exe") if Path(p).exists()), None)

u32.CreateDesktopW.restype = wt.HANDLE
u32.CreateDesktopW.argtypes = [wt.LPCWSTR, wt.LPCWSTR, ctypes.c_void_p, wt.DWORD, wt.DWORD, ctypes.c_void_p]
u32.OpenDesktopW.restype = wt.HANDLE
u32.OpenDesktopW.argtypes = [wt.LPCWSTR, wt.DWORD, wt.BOOL, wt.DWORD]
u32.OpenInputDesktop.restype = wt.HANDLE
u32.SetThreadDesktop.argtypes = [wt.HANDLE]
u32.CloseDesktop.argtypes = [wt.HANDLE]
u32.GetUserObjectInformationW.argtypes = [wt.HANDLE, ctypes.c_int, ctypes.c_void_p, wt.DWORD, ctypes.POINTER(wt.DWORD)]
u32.GetForegroundWindow.restype = wt.HWND
u32.PostMessageW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
u32.SendMessageW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
u32.SendMessageW.restype = ctypes.c_ssize_t
u32.PrintWindow.argtypes = [wt.HWND, wt.HDC, wt.UINT]
u32.GetWindowDC.argtypes = [wt.HWND]
u32.GetWindowDC.restype = wt.HDC
u32.ReleaseDC.argtypes = [wt.HWND, wt.HDC]
u32.MapVirtualKeyW.restype = wt.UINT
u32.ChildWindowFromPointEx.argtypes = [wt.HWND, wt.POINT, wt.UINT]
u32.ChildWindowFromPointEx.restype = wt.HWND
u32.MapWindowPoints.argtypes = [wt.HWND, wt.HWND, ctypes.c_void_p, wt.UINT]
u32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.c_void_p]
u32.GetGUIThreadInfo.argtypes = [wt.DWORD, ctypes.c_void_p]
g32.CreateCompatibleDC.argtypes = [wt.HDC]
g32.CreateCompatibleDC.restype = wt.HDC
g32.CreateCompatibleBitmap.argtypes = [wt.HDC, ctypes.c_int, ctypes.c_int]
g32.CreateCompatibleBitmap.restype = wt.HBITMAP
g32.SelectObject.argtypes = [wt.HDC, wt.HGDIOBJ]
g32.SelectObject.restype = wt.HGDIOBJ
g32.GetDIBits.argtypes = [wt.HDC, wt.HBITMAP, wt.UINT, wt.UINT, ctypes.c_void_p, ctypes.c_void_p, wt.UINT]
g32.DeleteObject.argtypes = [wt.HGDIOBJ]
g32.DeleteDC.argtypes = [wt.HDC]
DESKTOP_ACCESS = 0x01FF & ~0x0100   # every desktop right except DESKTOP_SWITCHDESKTOP: this file can never show it


class STARTUPINFOW(ctypes.Structure):
    _fields_ = [("cb", wt.DWORD), ("lpReserved", wt.LPWSTR), ("lpDesktop", wt.LPWSTR), ("lpTitle", wt.LPWSTR),
                ("dwX", wt.DWORD), ("dwY", wt.DWORD), ("dwXSize", wt.DWORD), ("dwYSize", wt.DWORD),
                ("dwXCountChars", wt.DWORD), ("dwYCountChars", wt.DWORD), ("dwFillAttribute", wt.DWORD),
                ("dwFlags", wt.DWORD), ("wShowWindow", wt.WORD), ("cbReserved2", wt.WORD),
                ("lpReserved2", ctypes.c_void_p), ("hStdInput", wt.HANDLE), ("hStdOutput", wt.HANDLE),
                ("hStdError", wt.HANDLE)]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [("hProcess", wt.HANDLE), ("hThread", wt.HANDLE), ("dwProcessId", wt.DWORD), ("dwThreadId", wt.DWORD)]


class GUITHREADINFO(ctypes.Structure):
    _fields_ = [("cbSize", wt.DWORD), ("flags", wt.DWORD), ("hwndActive", wt.HWND), ("hwndFocus", wt.HWND),
                ("hwndCapture", wt.HWND), ("hwndMenuOwner", wt.HWND), ("hwndMoveSize", wt.HWND),
                ("hwndCaret", wt.HWND), ("rcCaret", wt.RECT)]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wt.DWORD), ("biWidth", wt.LONG), ("biHeight", wt.LONG), ("biPlanes", wt.WORD),
                ("biBitCount", wt.WORD), ("biCompression", wt.DWORD), ("biSizeImage", wt.DWORD),
                ("biXPelsPerMeter", wt.LONG), ("biYPelsPerMeter", wt.LONG), ("biClrUsed", wt.DWORD),
                ("biClrImportant", wt.DWORD)]


# ---- Alex's side: what must never change -------------------------------------------------------------------------

def desk_name(h):
    buf, n = ctypes.create_unicode_buffer(256), wt.DWORD()
    u32.GetUserObjectInformationW(h, 2, buf, ctypes.sizeof(buf), ctypes.byref(n))      # UOI_NAME
    return buf.value


def exe(pid):
    h = k32.OpenProcess(0x1000, False, pid)              # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return "?"
    buf, n = ctypes.create_unicode_buffer(1024), wt.DWORD(1024)
    k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n))
    k32.CloseHandle(h)
    return Path(buf.value).name


def owner(hwnd):
    pid = wt.DWORD()
    u32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wt.UINT), ("dwTime", wt.DWORD)]


def last_input():
    """When a person (or SendInput) last moved the mouse or pressed a key, in ms of GetTickCount. Messages posted to a
    window never count, so a change means real input on the PC: his, as this file sends none."""
    li = LASTINPUTINFO(cbSize=ctypes.sizeof(LASTINPUTINFO))
    u32.GetLastInputInfo(ctypes.byref(li))
    return li.dwTime


def ticks():
    return k32.GetTickCount()


def alex():
    """What Alex's screen holds now, read from a fresh thread (it starts on his desktop even when this one has joined
    the sandbox's): his foreground window, its focused child, the cursor, the input desktop."""
    box = []
    t = threading.Thread(target=lambda: box.append(_alex()))
    t.start()
    t.join()
    return box[0]


def _alex():
    gi = GUITHREADINFO(cbSize=ctypes.sizeof(GUITHREADINFO))
    u32.GetGUIThreadInfo(0, ctypes.byref(gi))
    pt = wt.POINT()
    u32.GetCursorPos(ctypes.byref(pt))
    h = u32.OpenInputDesktop(0, False, 0x0001)          # DESKTOP_READOBJECTS
    name = desk_name(h) if h else "?"
    if h:
        u32.CloseDesktop(h)
    return {"foreground": int(u32.GetForegroundWindow() or 0), "focus": int(gi.hwndFocus or 0),
            "cursor": (pt.x, pt.y), "input desktop": name}


def compare(before, after):
    changed = [f"{k} {before[k]} -> {after[k]}" for k in before if before[k] != after[k]]
    return "alex: untouched" if not changed else "alex: CHANGED " + "; ".join(changed)


# ---- the sandbox desktop -----------------------------------------------------------------------------------------

def state_file(name):
    return STATE / f"{name}.json"


def load(name):
    f = state_file(name)
    if not f.exists():
        sys.exit(f"no sandbox {name!r} is open (open <url> first)")
    return json.loads(f.read_text(encoding="utf-8"))


def desktop(name, create=False):
    full = f"agora-sandbox-{name}"
    h = u32.OpenDesktopW(full, 0, False, DESKTOP_ACCESS)
    if not h and create:
        h = u32.CreateDesktopW(full, None, None, 0, DESKTOP_ACCESS, None)
    if not h:
        sys.exit(f"desktop {full}: {'cannot make it' if create else 'not there (its processes ended?)'} "
                 f"(error {k32.GetLastError()})")
    return h, full


def join(name):
    """Put this thread on the sandbox desktop, so it can find, post to and print the windows there."""
    h, _ = desktop(name)
    if not u32.SetThreadDesktop(h):
        sys.exit(f"cannot join the sandbox desktop (error {k32.GetLastError()})")
    return h


def start(name, argv, env=None):
    """Serialize launches with cleanup; an abandoned lock needs reconciliation."""
    f = state_file(name)
    lock = f.with_suffix(".cleanup-lock")
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        return _start_locked(name, argv, env)
    finally:
        os.close(fd)
        lock.unlink(missing_ok=True)


def _start_locked(name, argv, env=None):
    """CreateProcess on the sandbox desktop; -> pid. The handle of the desktop is held by the process from then on."""
    from sandbox_owned import OwnedProcesses
    from sandbox_receipts import complete, error, write
    f = state_file(name)
    st = {"pids": [], "owners": [], "at": time.time()}
    if f.exists():
        st = json.loads(f.read_text(encoding="utf-8"))
        if st.get("cleanup") or any(r.get("status") == "pending" for r in st.get("launches", [])):
            raise RuntimeError("previous cleanup receipt needs reconciliation; no launch")
        if set(st.get("pids", [])) - {p["pid"] for p in st.get("owners", []) if complete(p)}:
            raise RuntimeError("previous ownership incomplete; no launch")
    launch = {"status": "pending", "at": time.time()}
    st.setdefault("launches", []).append(launch)
    write(f, st)  # unknown crash outcome blocks another launch, even before PID capture
    h, full = desktop(name, create=True)
    si = STARTUPINFOW(cb=ctypes.sizeof(STARTUPINFOW), lpDesktop=f"WinSta0\\{full}")
    si.dwFlags, si.wShowWindow = 0x1, 4        # STARTF_USESHOWWINDOW, SW_SHOWNOACTIVATE (on its own desktop anyway)
    pi = PROCESS_INFORMATION()
    line = ctypes.create_unicode_buffer(subprocess.list2cmdline(argv))
    block = None
    if env:
        merged = {**os.environ, **env}
        block = ctypes.create_unicode_buffer("".join(f"{k}={v}\0" for k, v in merged.items()) + "\0")
    flags = 0x00000200 | 0x08000000 | (0x400 if block else 0)  # NEW_PROCESS_GROUP, NO_WINDOW, UNICODE_ENVIRONMENT
    ok = k32.CreateProcessW(None, line, None, None, False, flags, block, None, ctypes.byref(si), ctypes.byref(pi))
    if not ok:
        launch.update(status="failed", winerror=int(k32.GetLastError()))
        write(f, st)
        sys.exit(f"CreateProcess failed (error {launch['winerror']})")
    # Preserve launch identity before callers add their own state fields.
    # A missing/denied metadata read retains an UNKNOWN owner; never adopt a
    # window's PID as a replacement. This does not grant host/WMI access.
    st.setdefault("pid", pi.dwProcessId)
    launch.update(status="created", pid=pi.dwProcessId)
    st.setdefault("pids", []).append(pi.dwProcessId)
    try:
        st.setdefault("owners", []).append(OwnedProcesses().on_handle(pi.dwProcessId, pi.hProcess))
    except Exception as exc:
        st.setdefault("ownership_errors", []).append({"pid": pi.dwProcessId, "error": error(exc)})
    finally:
        # Persist even partial ownership; failure is not permission to kill.
        try:
            write(f, st)
        finally:
            k32.CloseHandle(pi.hThread)
            k32.CloseHandle(pi.hProcess)
    # the desktop handle stays open until this process ends: closed at once, the desktop can vanish before the new
    # process has joined it, and the process then exits with no window (ran 16 Oct: 3 of 5 Edge starts died so)
    return pi.dwProcessId


def free_port():
    import socket
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def top_windows(name):
    """[(hwnd, pid, class, title, visible, (x, y, w, h))] of the top-level windows on the sandbox desktop."""
    h, _ = desktop(name)
    out = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def each(w, _):
        pid = wt.DWORD()
        u32.GetWindowThreadProcessId(w, ctypes.byref(pid))
        cls, title = ctypes.create_unicode_buffer(256), ctypes.create_unicode_buffer(512)
        u32.GetClassNameW(w, cls, 256)
        u32.GetWindowTextW(w, title, 512)
        r = wt.RECT()
        u32.GetWindowRect(w, ctypes.byref(r))
        out.append((int(w), pid.value, cls.value, title.value, bool(u32.IsWindowVisible(w)),
                    (r.left, r.top, r.right - r.left, r.bottom - r.top)))
        return True
    u32.EnumDesktopWindows(h, each, 0)
    u32.CloseDesktop(h)
    return out


def main_window(name, st=None):
    """The sandbox's own window: the largest visible titled top-level window there (Edge's app window)."""
    wins = [w for w in top_windows(name) if w[4] and w[3] and w[5][2] > 50 and w[5][3] > 50]
    if not wins:
        sys.exit("no visible window on the sandbox desktop yet")
    return max(wins, key=lambda w: w[5][2] * w[5][3])[0]


# ---- DevTools ------------------------------------------------------------------------------------------------------

class Cdp:
    def __init__(self, port):
        from websockets.sync.client import connect
        tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=5).read())
        url = next(t["webSocketDebuggerUrl"] for t in tabs if t.get("type") == "page")
        self.ws, self.n = connect(url, origin=None, max_size=64 * 1024 * 1024), 0

    def call(self, method, **params):
        self.n += 1
        self.ws.send(json.dumps({"id": self.n, "method": method, "params": params}))
        while True:
            m = json.loads(self.ws.recv())
            if m.get("id") == self.n:
                if "error" in m:
                    raise RuntimeError(f"{method}: {m['error'].get('message')}")
                return m.get("result", {})

    def js(self, expr):
        r = self.call("Runtime.evaluate", expression=expr, awaitPromise=True, returnByValue=True)
        if r.get("exceptionDetails"):
            raise RuntimeError(str(r["exceptionDetails"].get("exception", {}).get("description") or r["exceptionDetails"]))
        return r.get("result", {}).get("value")

    def close(self):
        self.ws.close()


def wait_cdp(port, secs=30):
    t = time.time() + secs
    while time.time() < t:
        try:
            tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=2).read())
            if any(x.get("type") == "page" for x in tabs):
                return True
        except Exception:
            pass
        time.sleep(0.2)
    return False


# ---- seeing: PrintWindow -------------------------------------------------------------------------------------------

def print_window(hwnd):
    """The window as Windows composes it (PW_RENDERFULLCONTENT), frame and all; -> a PIL image."""
    from PIL import Image
    r = wt.RECT()
    u32.GetWindowRect(hwnd, ctypes.byref(r))
    w, h = r.right - r.left, r.bottom - r.top
    wdc = u32.GetWindowDC(hwnd)
    dc = g32.CreateCompatibleDC(wdc)
    bmp = g32.CreateCompatibleBitmap(wdc, w, h)
    old = g32.SelectObject(dc, bmp)
    ok = u32.PrintWindow(hwnd, dc, 2)
    bi = BITMAPINFOHEADER(biSize=ctypes.sizeof(BITMAPINFOHEADER), biWidth=w, biHeight=-h, biPlanes=1, biBitCount=32)
    buf = ctypes.create_string_buffer(w * h * 4)
    g32.GetDIBits(dc, bmp, 0, h, buf, ctypes.byref(bi), 0)
    g32.SelectObject(dc, old)
    g32.DeleteObject(bmp)
    g32.DeleteDC(dc)
    u32.ReleaseDC(hwnd, wdc)
    if not ok:
        raise RuntimeError(f"PrintWindow failed (error {k32.GetLastError()})")
    return Image.frombuffer("RGB", (w, h), buf, "raw", "BGRX", 0, 1)


# ---- input: window messages to the window's own queue ------------------------------------------------------------

WM_MOUSEMOVE, WM_LBUTTONDOWN, WM_LBUTTONUP, WM_RBUTTONDOWN, WM_RBUTTONUP = 0x200, 0x201, 0x202, 0x204, 0x205
WM_KEYDOWN, WM_KEYUP, WM_CHAR = 0x100, 0x101, 0x102
VK = {"Enter": 13, "Escape": 27, "Tab": 9, "Backspace": 8, "Delete": 46, "ArrowDown": 40, "ArrowUp": 38,
      "ArrowLeft": 37, "ArrowRight": 39, "Space": 32, "Home": 36, "End": 35, "PageUp": 33, "PageDown": 34}


def xy(x, y):
    return (int(y) & 0xFFFF) << 16 | (int(x) & 0xFFFF)


def children(hwnd):
    found = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def each(c, _):
        cls = ctypes.create_unicode_buffer(256)
        u32.GetClassNameW(c, cls, 256)
        r = wt.RECT()
        u32.GetWindowRect(c, ctypes.byref(r))
        found.append((int(c), cls.value, bool(u32.IsWindowVisible(c)), (r.left, r.top, r.right - r.left, r.bottom - r.top)))
        return True
    u32.EnumChildWindows(hwnd, each, 0)
    return found


def post(hwnd, msg, wp, lp):
    if not u32.PostMessageW(hwnd, msg, wp, lp):
        raise RuntimeError(f"PostMessage {msg:#x} refused (error {k32.GetLastError()})")


def page_origin(hwnd, cdp=None, inner=None):
    """Where the page's (0, 0) is in the window's client pixels, and the page's pixel ratio. `inner` is the page's
    [innerWidth, innerHeight, devicePixelRatio] when the caller has read it already (screen.py)."""
    r = wt.RECT()
    u32.GetClientRect(hwnd, ctypes.byref(r))
    iw, ih, dpr = inner or cdp.js("[innerWidth, innerHeight, devicePixelRatio]")
    return (r.right - iw * dpr) / 2, r.bottom - ih * dpr, dpr


def click(hwnd, cx, cy, right=False):
    """A press and release at client pixel cx, cy, as Windows would deliver it, to this window's queue only."""
    down, up, mk = (WM_RBUTTONDOWN, WM_RBUTTONUP, 2) if right else (WM_LBUTTONDOWN, WM_LBUTTONUP, 1)
    post(hwnd, WM_MOUSEMOVE, 0, xy(cx, cy))
    time.sleep(0.03)
    post(hwnd, down, mk, xy(cx, cy))
    time.sleep(0.06)
    post(hwnd, up, 0, xy(cx, cy))


def cls_of(h):
    buf = ctypes.create_unicode_buffer(256)
    u32.GetClassNameW(h, buf, 256)
    return buf.value


def click_at(hwnd, cx, cy, right=False):
    """A click at client pixel cx, cy of the top window, sent to the deepest visible child under it (a WebView2 page
    lives in child windows; Edge's own page has none), in that child's own client pixels. -> the window clicked."""
    target, pt = deepest(hwnd, cx, cy)
    click(target, pt.x, pt.y, right)
    return target


def deepest(hwnd, cx, cy):
    """The deepest visible child under client pixel cx, cy of the top window, and the point in its client pixels."""
    target, pt = hwnd, wt.POINT(int(cx), int(cy))
    while True:
        c = u32.ChildWindowFromPointEx(target, pt, 1)          # CWP_SKIPINVISIBLE
        # Chromium's own window takes the mouse; the windows inside it draw (D3D) or serve accessibility
        if not c or c == target or cls_of(c) in ("Intermediate D3D Window", "Chrome_RenderWidgetHostHWND"):
            break
        u32.MapWindowPoints(target, c, ctypes.byref(pt), 1)
        target = c
    return target, pt


WM_MOUSEWHEEL = 0x20A


def wheel_at(hwnd, cx, cy, dy):
    """A wheel turn at client pixel cx, cy of the top window, as Windows delivers it (a6549): WM_MOUSEWHEEL carries
    SCREEN coordinates and goes to the window under them; dy > 0 scrolls down (a notch is 120, as the wheel reports
    -120). One message per notch, as a real wheel sends. -> the window it went to."""
    if not dy:
        return hwnd
    target, inner = deepest(hwnd, cx, cy)
    pt = wt.POINT(int(cx), int(cy))
    u32.ClientToScreen(hwnd, ctypes.byref(pt))
    post(target, WM_MOUSEMOVE, 0, xy(inner.x, inner.y))
    notches = max(1, round(abs(dy) / 120))
    delta = -120 if dy > 0 else 120
    for _ in range(notches):
        time.sleep(0.03)
        post(target, WM_MOUSEWHEEL, (delta & 0xFFFF) << 16, xy(pt.x, pt.y))
    return target


def focused(hwnd):
    """The window that has the keyboard focus in the sandbox window's thread (where keys go), or the window."""
    gi = GUITHREADINFO(cbSize=ctypes.sizeof(GUITHREADINFO))
    tid = u32.GetWindowThreadProcessId(hwnd, None)
    if u32.GetGUIThreadInfo(tid, ctypes.byref(gi)) and gi.hwndFocus:
        return gi.hwndFocus
    return hwnd


def key_lparam(vk, up=False):
    scan = u32.MapVirtualKeyW(vk, 0)
    ext = 1 << 24 if vk in (33, 34, 35, 36, 37, 38, 39, 40, 45, 46) else 0
    return 1 | scan << 16 | ext | ((3 << 30) if up else 0)


def type_text(hwnd, text):
    """A character typed with one unshifted key goes as that key's WM_KEYDOWN and WM_KEYUP: the window's own message
    loop (TranslateMessage) makes the WM_CHAR, as it does for a person's key. Posting the WM_CHAR as well typed every
    letter twice (ran 16 Oct). Anything else (capitals, !, é, emoji) goes as WM_CHAR alone: a posted key cannot hold
    Shift down, so the page gets its input but no keydown for it."""
    for ch in text:
        scan = u32.VkKeyScanW(ord(ch)) if ord(ch) < 0x10000 else -1
        if scan != -1 and scan & 0xFF00 == 0 and ch != "\n":
            vk = scan & 0xFF
            post(hwnd, WM_KEYDOWN, vk, key_lparam(vk))
            post(hwnd, WM_KEYUP, vk, key_lparam(vk, True))
        elif ch == "\n":
            post(hwnd, WM_KEYDOWN, 13, key_lparam(13))
            post(hwnd, WM_KEYUP, 13, key_lparam(13, True))
        else:
            units = ch.encode("utf-16-le")
            for k in range(0, len(units), 2):
                post(hwnd, WM_CHAR, int.from_bytes(units[k:k + 2], "little"), 1)
        time.sleep(0.015)


def press_key(hwnd, name):
    """One key, down and up (Enter's, Tab's and Backspace's WM_CHAR are made by the window's TranslateMessage)."""
    vk = VK.get(name) or (u32.VkKeyScanW(ord(name)) & 0xFF if len(name) == 1 else 0)
    if not vk:
        raise SystemExit(f"no key {name!r}: {', '.join(VK)} or one character")
    post(hwnd, WM_KEYDOWN, vk, key_lparam(vk))
    post(hwnd, WM_KEYUP, vk, key_lparam(vk, True))


def cdp_key(cdp, k):
    """A key with held modifiers (Ctrl+b), through DevTools: posted messages cannot hold a modifier down."""
    mods = 0
    while "+" in k[1:]:
        m, k = k.split("+", 1)
        mods |= {"alt": 1, "ctrl": 2, "meta": 4, "shift": 8}[m.lower()]
    code = VK.get(k) or (ord(k.upper()) if len(k) == 1 else 0)
    text = "" if mods & 7 else ({"Enter": "\r", "Tab": "\t", "Space": " "}.get(k) or (k if len(k) == 1 else ""))
    base = dict(key=" " if k == "Space" else k, windowsVirtualKeyCode=code, code=k, modifiers=mods)
    cdp.call("Input.dispatchKeyEvent", type="keyDown", text=text, **base)
    cdp.call("Input.dispatchKeyEvent", type="keyUp", **base)


def page_shot(cdp):
    from io import BytesIO
    from PIL import Image
    return Image.open(BytesIO(base64.b64decode(cdp.call("Page.captureScreenshot", format="png")["data"])))


# ---- opening and closing -----------------------------------------------------------------------------------------

TEST_HTML = """<!doctype html><title>sandbox test</title>
<style>body{font:22px Segoe UI,sans-serif;background:#f3ede2;margin:30px} input,button{font:inherit;padding:6px 12px}
#log{font:14px Consolas,monospace;color:#555}</style>
<h1>A harmless sandbox page</h1><p><input id=i placeholder="type here"> <button id=b>pressed 0</button></p><pre id=log></pre>
<script>let n = 0; b.onclick = () => b.textContent = 'pressed ' + (++n);
for (const t of ['keydown', 'input', 'mousedown', 'click', 'contextmenu'])
  addEventListener(t, e => { log.textContent = (t + (e.key ? ' ' + e.key : '') + (e.isTrusted ? '' : ' UNTRUSTED') + '\\n'
    + log.textContent).slice(0, 600); }, true);</script>"""
TEST_URL = "data:text/html;base64," + base64.b64encode(TEST_HTML.encode()).decode()

def open_edge(name, url, size="1500x900", tries=2, viewport=True):
    """Edge as an app window on the sandbox desktop, InPrivate (a fresh Edge profile signs itself into Alex's Microsoft
    account and starts syncing his data into it: seen 16 Oct, a5932), on a DevTools port of its own. size is the page's
    CSS viewport (viewport=False: the outer window, as before a7413). -> the state; st["viewport"] is the page's
    [innerWidth, innerHeight, devicePixelRatio] as measured. A failed start closes its own sandbox and exits."""
    from sandbox_receipts import update_manifest
    if state_file(name).exists():
        sys.exit(f"sandbox {name!r} is open already (close it, or use --name)")
    STATE.mkdir(parents=True, exist_ok=True)
    w, h = size.lower().split("x")
    prof = STATE / f"{name}-profile"
    for attempt in range(tries):
        port = free_port()
        pid = start(name, [EDGE, f"--user-data-dir={prof}", f"--remote-debugging-port={port}",
                           "--inprivate",
                           "--no-first-run", "--no-default-browser-check", "--disable-sync", "--disable-extensions",
                           # a7466: with Alex's display asleep (39 min idle, 20 Oct) Edge judged every window occluded:
                           # the page went visibilityState hidden, stopped painting (blank PrintWindow) and its carries
                           # never started. A window on a desktop no one sees must not depend on his monitor
                           "--disable-features=CalculateNativeWinOcclusion", "--disable-backgrounding-occluded-windows",
                           "--disable-renderer-backgrounding",
                           f"--window-size={w},{h}", "--window-position=0,0", f"--app={url}"])
        st = update_manifest(state_file(name), {
            "pid": pid, "port": port, "url": url, "profile": str(prof), "at": time.time()})
        if wait_cdp(port, 30):
            break
        # ran 16 Oct: with a profile folder Edge has not seen, the first start exits without a window; the second runs
        print(f"edge (pid {pid}) gave no DevTools port; {'again' if attempt + 1 < tries else 'giving up'}")
        receipt = close(name, quiet=True)
        if not receipt or not receipt.get("ok"):
            sys.exit("edge start failed; cleanup not confirmed; ownership state retained, no retry")
    else:
        sys.exit("edge did not start on the sandbox desktop")
    # a7413: from here a failure (the page's websocket reset at readyState, WinError 10054, as seen only in Codex
    # workers' sandboxes) left this desktop and its Edge running, and screen.py's guard with no verdict; now the start
    # closes what it opened and says how far it got. Nothing is retried.
    stage = "the window"
    try:
        for _ in range(50):                        # the window, and the page drawn
            if [x for x in top_windows(name) if x[4] and x[3] and x[5][2] > 50]:
                break
            time.sleep(0.2)
        stage = "the page's DevTools websocket"
        c = Cdp(port)
        try:
            stage = "document.readyState"
            for _ in range(50):
                if c.js("document.readyState") == "complete":
                    break
                time.sleep(0.2)
            if viewport:
                stage = "fitting the page to " + size
                st = update_manifest(state_file(name), {"viewport": fit_viewport(c, int(w), int(h))})
        finally:
            c.close()
    except BaseException as e:
        why = start_failure(st, stage, e)
        close(name, quiet=True)
        raise SystemExit(why) from e
    return st


def fit_viewport(c, w, h):
    """--size names the PAGE (CSS px, innerWidth x innerHeight), as headless does: Edge's --window-size is the outer
    window, so at 2560x1440 the page was 2546x1403 (ran 20 Oct, a7413). Grow the window by its own frame; -> the page's
    [innerWidth, innerHeight, devicePixelRatio] as they are after (Windows caps a window near the screen: then less).
    A page the size of the whole screen (Alex's 2560x1440 at 150%) cannot fit inside a framed window (ran: capped at
    2560x1420), so that one is the window made fullscreen, on the hidden desktop like everything else here."""
    iw, ih, ow, oh, sw, sh = c.js("[innerWidth, innerHeight, outerWidth, outerHeight, screen.width, screen.height]")
    if (iw, ih) != (w, h):
        win = c.call("Browser.getWindowForTarget")["windowId"]
        if (w, h) == (sw, sh):
            c.call("Browser.setWindowBounds", windowId=win, bounds={"windowState": "fullscreen"})
        else:
            c.call("Browser.setWindowBounds", windowId=win, bounds={"left": 0, "top": 0, "width": w + ow - iw,
                                                                    "height": h + oh - ih})
        for _ in range(25):
            time.sleep(0.1)
            if c.js("[innerWidth, innerHeight]") != [iw, ih]:
                break
        time.sleep(0.2)
    return c.js("[innerWidth, innerHeight, devicePixelRatio]")


def start_failure(st, stage, e):
    """Name the failed stage; a failed executable query cannot establish exit."""
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{st['port']}/json/version", timeout=2).read()
        port = "still answered"
    except Exception as pe:
        port = f"no longer answered ({type(pe).__name__})"
    pid = "presence unknown (see ownership receipt)"
    from sandbox_receipts import error
    safe = error(e)
    return (f"edge started on the sandbox desktop but failed at {stage}: {safe['type']}: {safe['message']}; edge pid {st['pid']} "
            f"{pid}, its DevTools port {port}; cleanup requested, see its receipt (not a tested page)")


def run_hidden(name, argv, cdp=False, env=None):
    """Any program on the sandbox desktop. --cdp gives a WebView2 in it a DevTools port (its environment variable);
    env adds to its environment (a6113: AGORA_WM_KEYS=off, so a window manager there takes no global key)."""
    from sandbox_receipts import update_manifest
    STATE.mkdir(parents=True, exist_ok=True)
    port = free_port() if cdp else None
    env = {**(env or {}), **({"WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS":
                            f"--remote-debugging-port={port}"} if cdp else {})} or None
    argv = [sys.executable if a == "python" else a for a in argv]
    pid = start(name, argv, env)
    st = update_manifest(state_file(name), {"port": port} if port else {})
    if port:
        print(f"devtools {'up' if wait_cdp(port, 60) else 'NOT up (no WebView2 page yet?)'} on {port}")
    return st


def close(name, quiet=False):
    """Cleanup only recorded identities; preserve failed/unknown ownership.

    No taskkill /T, PID adoption from a desktop, profile sweep or ignored error.
    Children need their own parent/creation/exe/profile records before cleanup.
    """
    import os
    from sandbox_owned import OwnedProcesses
    from sandbox_receipts import cleanup, error, write
    f = state_file(name)
    if not f.exists():
        if not quiet:
            print(f"sandbox {name}: ownership state missing; cleanup not admitted")
        return {"ok": False, "reason": "ownership state missing"}
    lock = f.with_suffix(".cleanup-lock")
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return {"ok": False, "reason": "cleanup already pending; reconcile receipt"}
    try:
        try:
            st = json.loads(f.read_text(encoding="utf-8"))
        except Exception as exc:
            result = {"ok": False, "reason": "ownership unreadable; no effects", "error": error(exc)}
            write(f.with_suffix(".cleanup-failed.json"), result)
            return result

        def remaining():
            # None historically meant either absent desktop or OpenDesktop
            # denial. It is UNKNOWN until a host-capable verifier establishes
            # absence; never turn it into [] here.
            windows = top_windows_quiet(name)
            st["remaining_window_pids"] = None if windows is None else sorted({w[1] for w in windows})
            # Window enumeration cannot establish that headless/unregistered
            # engine children exited. Until the engine owner supplies a
            # reviewed runtime boundary, preserve UNKNOWN even with no windows.
            # Never archive state or admit an automatic retry from this signal.
            st["runtime_closure"] = "unknown: no reconciled child ownership boundary"
            return None

        try:
            result = cleanup(st, OwnedProcesses(), lambda data: write(f, data), remaining)
        except Exception as exc:
            result = {"ok": False, "reason": "cleanup failed; ownership retained", "error": error(exc)}
            # If writing the primary receipt failed, do not overwrite its
            # last durable intent. Preserve a separate failure if possible.
            try:
                write(f.with_suffix(".cleanup-failed.json"), result)
            except OSError:
                pass
        if result["ok"]:
            # Retain receipts even on success; never delete a profile here.
            f.replace(f.with_name(f.stem + f".closed-{time.time_ns()}.json"))
        if not quiet:
            print(f"sandbox {name}: {result['reason']}; receipts retained")
        return result
    finally:
        os.close(fd)
        lock.unlink(missing_ok=True)


def top_windows_quiet(name):
    h = u32.OpenDesktopW(f"agora-sandbox-{name}", 0, False, DESKTOP_ACCESS)
    if not h:
        return None
    u32.CloseDesktop(h)
    return top_windows(name)


# ---- the verbs -----------------------------------------------------------------------------------------------------

def take(args, flag, default=None, value=True):
    if flag not in args:
        return default, args
    k = args.index(flag)
    if not value:
        return True, args[:k] + args[k + 1:]
    return args[k + 1], args[:k] + args[k + 2:]


def main(argv):
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return
    verb, args = argv[0], argv[1:]
    name, args = take(args, "--name", "sb")
    if verb == "test":
        sys.exit(test("webview" in args))
    before, quiet_since = alex(), last_input()
    if verb == "open":
        size, args = take(args, "--size", "1500x900")
        if not args:
            sys.exit("open <url> [--size WxH] [--name n]")
        st = open_edge(name, TEST_URL if args[0] == "test-page" else args[0], size)
        print(f"opened {args[0][:100]} on desktop agora-sandbox-{name}: edge pid {st['pid']}, devtools {st['port']}")
    elif verb == "run":
        cdp, args = take(args, "--cdp", False, value=False)
        st = run_hidden(name, args, cdp)
        print(f"started {' '.join(args)} on desktop agora-sandbox-{name} (pid {st['pids'][-1]})")
    elif verb == "windows":
        join(name)
        for hw, pid, cls, title, vis, (x, y, w, h) in top_windows(name):
            if vis:
                print(f"{hw:>10}  {exe(pid):<14} {x:>5} {y:>5} {w:>5}x{h:<5} {cls:<24} {title[:70]}")
                if "--tree" in args:
                    for c, ccls, cvis, (cx, cy, cw, ch) in children(hw):
                        print(f"    {c:>10}  {exe(owner(c)):<14} {cx:>5} {cy:>5} {cw:>5}x{ch:<5} {ccls}"
                              f"{'' if cvis else ' (hidden)'}")
    elif verb == "close":
        close(name)
    elif verb in ("click", "type", "key", "js", "shot", "film"):
        st = load(name)
        join(name)
        hw = main_window(name)
        c = Cdp(st["port"]) if st.get("port") else None
        try:
            if verb == "click":
                right, args = take(args, "--right", False, value=False)
                raw, args = take(args, "--client", False, value=False)
                x, y = float(args[0]), float(args[1])
                if raw or not c:
                    cx, cy = x, y
                else:
                    ox, oy, dpr = page_origin(hw, c)
                    cx, cy = ox + x * dpr, oy + y * dpr
                click_at(hw, cx, cy, right)
                time.sleep(0.4)
                print(f"{'right ' if right else ''}clicked page {x:g},{y:g} (window client {cx:.0f},{cy:.0f})")
            elif verb == "type":
                type_text(focused(hw), " ".join(args))
                time.sleep(0.3)
                print(f"typed {len(' '.join(args))} characters")
            elif verb == "key":
                k = args[0]
                if "+" in k[1:]:
                    if not c:
                        sys.exit("a key with a modifier needs DevTools (open, or run --cdp)")
                    cdp_key(c, k)
                else:
                    press_key(focused(hw), k)
                time.sleep(0.4)
                print(f"key {k}")
            elif verb == "js":
                print(json.dumps(c.js(" ".join(args)), ensure_ascii=False, default=str)[:4000])
            elif verb == "shot":
                page, args = take(args, "--page", False, value=False)
                out = screen_tools.place(args[0] if args else "sandbox.png")
                im = page_shot(c) if page else print_window(hw)
                im.save(out)
                print(f"wrote {out.as_posix()} ({im.size[0]}x{im.size[1]}, {'the page' if page else 'the window'}); "
                      f"open it with Read")
            elif verb == "film":
                page, args = take(args, "--page", False, value=False)
                fps, args = take(args, "--fps", "10")
                film(hw, c if page else None, float(args[0]), screen_tools.place(args[1]), float(fps))
        finally:
            if c:
                c.close()
    else:
        sys.exit(f"no verb {verb!r} (--help)")
    after = alex()
    print(compare(before, after) + ("" if last_input() == quiet_since or before == after else
                                     " (real input happened meanwhile: someone at the PC moved or typed)"))


def film(hwnd, cdp, seconds, out, fps=10):
    """Shots strung together: `seconds` of the window (or the page), `fps` a second, into an mp4 by ffmpeg."""
    frames = Path(agora_tmp.directory("sandbox-film-"))
    n, t0 = 0, time.time()
    try:
        while time.time() - t0 < seconds:
            t = time.time()
            im = page_shot(cdp) if cdp else print_window(hwnd)
            im.convert("RGB").save(frames / f"{n:05d}.png")
            n += 1
            time.sleep(max(0.0, 1 / fps - (time.time() - t)))
        real = n / max(time.time() - t0, 0.001)
        subprocess.run([screen_tools.ffmpeg(), "-y", "-loglevel", "error", "-framerate", f"{real:.2f}",
                        "-i", str(frames / "%05d.png"), "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                        "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", str(out)], check=True)
        last = out.with_name(out.stem + "-last.png")
        (frames / f"{n - 1:05d}.png").replace(last)
        print(f"wrote {out.as_posix()} ({n} frames, {real:.1f} a second, {out.stat().st_size // 1024} KB); "
              f"its last frame {last.as_posix()}")
    finally:
        import shutil
        shutil.rmtree(frames, ignore_errors=True)


class Guard:
    """Watches Alex's side every 20 ms from a thread of its own (on his desktop): the foreground window, focus, cursor
    and input desktop; whether a window of the sandbox ever becomes his foreground; whether a window titled like ours
    ever shows on his desktop; and whether real input (his) happened, which is what can tell his change from ours."""

    def __init__(self, sandbox, title_words):
        self.sandbox, self.words, self.stop, self.notes = sandbox, title_words.lower(), False, []
        self.ours = set()
        self.t = threading.Thread(target=self.watch, daemon=True)

    def __enter__(self):
        # a7950: from a fresh thread, as the watcher reads (alex()): a caller that has joined an earlier sandbox's desktop
        # read foreground 0 and cursor (0, 0) here, and the watcher's first true reading was then judged a FAIL
        self.first, self.input0 = alex(), last_input()
        self.his = 0                                   # changes that came with real input: his, not ours
        self.t.start()
        return self

    def __exit__(self, *exc):
        self.stop = True
        self.t.join()

    def watch(self):
        try:
            self._watch()
        except Exception as e:                         # a guard that stopped proves nothing: the verdict says so
            self.notes.append((time.time(), f"the guard itself stopped ({type(e).__name__}: {e})", True))

    def _watch(self):
        seen, k, then = self.first, 0, self.input0
        while not self.stop:
            if k % 10 == 0:
                self.ours = self.sandbox_windows()
                for w in self.his_windows():
                    if self.words in w[5].lower():
                        self.notes.append((time.time(), f"a window titled {w[5][:60]!r} is ON HIS DESKTOP", True))
            now = _alex()
            li = last_input()                          # read after the state: a move seen has already counted
            # input time is kept in ticks of ~16 ms, so two of his moves inside one tick read as no input: count
            # input in the last 150 ms as his (ran 16 Oct: two 1-pixel moves during his mouse use read as ours)
            if li == then and (ticks() - li) & 0xFFFFFFFF < 150:
                then = li - 1
            if now != seen:
                fg = now["foreground"]
                what = compare(seen, now).replace("alex: CHANGED ", "") + f" (foreground: {exe(owner(fg))})"
                if fg in self.ours:
                    self.notes.append((time.time(), "a sandbox window became his foreground: " + what, True))
                elif now["input desktop"] != self.first["input desktop"]:
                    self.notes.append((time.time(), "the input desktop changed: " + what, True))
                elif now["cursor"] != seen["cursor"] and li == then:
                    self.notes.append((time.time(), "the cursor moved with no real input: " + what, True))
                elif li != then:
                    self.his += 1                      # he moved, typed or clicked: his own change
                else:                                  # a window of his took the foreground by itself (no input)
                    self.notes.append((time.time(), "changed with no input, not to a sandbox window: " + what, False))
                seen = now
            then = li
            k += 1
            time.sleep(0.02)

    def sandbox_windows(self):
        return {x[0] for x in (top_windows_quiet(self.sandbox) or [])}

    def his_windows(self):
        """His visible windows; one owned by a process this sandbox started counts as ours, whatever its title."""
        f = state_file(self.sandbox)
        pids = set(json.loads(f.read_text(encoding="utf-8")).get("pids", [])) if f.exists() else set()
        return [w if owner(w[0]) not in pids else (*w[:5], self.words + " (by pid) " + w[5])
                for w in screen_tools.windows()]

    def verdict(self):
        """-> (code, words): 0 untouched by us, 1 touched by us (or by something we cannot tell from us)."""
        bad = [n for _, n, b in self.notes if b]
        other = [n for _, n, b in self.notes if not b]
        mine = (f"; {self.his} changes came with real input (someone at the PC), so are theirs" if self.his else "")
        if bad:
            return 1, "FAIL: " + "; ".join(bad[:6]) + mine
        return 0, ("alex: untouched by the sandbox (foreground, focus, cursor and input desktop polled every 20 ms: "
                   "no sandbox window became his foreground, none showed on his desktop, the input desktop stayed "
                   f"{self.first['input desktop']}, the cursor never moved without real input){mine}"
                   + (f"; also, with no input: {'; '.join(other[:3])}" if other else ""))


def test(webview=False):
    """Prove the sandbox on a harmless page: rendered, typed into, clicked, captured (PNG and film), Alex untouched.
    `test webview` also proves a pywebview (WebView2) window, as hud.py makes, run there with `run --cdp`."""
    name = f"selftest-{os.getpid()}"
    out = screen_tools.place("sandbox-selftest.png")
    checks = []
    with Guard(name, "sandbox test") as g:
        st = open_edge(name, TEST_URL, "1000x600")
        try:
            join(name)
            hw = main_window(name)
            c = Cdp(st["port"])
            box = c.js("(() => { const r = i.getBoundingClientRect(), s = b.getBoundingClientRect();"
                       " return [r.x + r.width / 2, r.y + r.height / 2, s.x + s.width / 2, s.y + s.height / 2]; })()")
            ox, oy, dpr = page_origin(hw, c)
            click(hw, ox + box[0] * dpr, oy + box[1] * dpr)
            time.sleep(0.4)
            checks.append(("a click put the focus in the field", c.js("document.activeElement.id") == "i"))
            type_text(hw, "Hello, sandbox! café 🙂x")
            press_key(hw, "Backspace")
            time.sleep(0.5)
            got = c.js("i.value")
            checks.append((f"typed text arrived exactly ({got!r})", got == "Hello, sandbox! café 🙂"))
            checks.append(("its keys were trusted keydowns", c.js("log.textContent.includes('keydown Backspace') && !log.textContent.includes('UNTRUSTED')")))
            cdp_key(c, "Ctrl+a")
            type_text(hw, "replaced")
            time.sleep(0.4)
            got = c.js("i.value")
            checks.append((f"Ctrl+a (DevTools) then typing replaced it ({got!r})", got == "replaced"))
            for _ in range(2):
                click(hw, ox + box[2] * dpr, oy + box[3] * dpr)
                time.sleep(0.3)
            checks.append(("two clicks pressed the button twice", c.js("b.textContent") == "pressed 2"))
            im = print_window(hw)
            im.save(out)
            px = im.convert("RGB").resize((1, 1)).getpixel((0, 0))
            checks.append((f"the window's picture is drawn ({im.size[0]}x{im.size[1]}, mean colour {px})", sum(px) > 150))
            page_shot(c).save(out.with_name(out.stem + "-page.png"))
            film(hw, None, 2, out.with_suffix(".mp4"), 10)
            checks.append(("the film was written", out.with_suffix(".mp4").stat().st_size > 1000))
            c.close()
        finally:
            close(name)
        if webview:
            wname = name + "-wv"
            script = STATE / "webview-test.py"
            script.write_text("import webview\nwebview.create_window('sandbox webview', html=" + repr(TEST_HTML)
                              + ", width=900, height=600)\nwebview.start()\n", encoding="utf-8")
            try:
                st = run_hidden(wname, ["python", str(script)], cdp=True)
                for _ in range(100):
                    if [x for x in top_windows(wname) if x[4] and x[3] == "sandbox webview"]:
                        break
                    time.sleep(0.2)
                join(wname)
                hw = main_window(wname)
                c = Cdp(st["port"])
                for _ in range(50):
                    if c.js("!!window.i"):
                        break
                    time.sleep(0.2)
                box = c.js("(() => { const r = i.getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; })()")
                ox, oy, dpr = page_origin(hw, c)
                deep = click_at(hw, ox + box[0] * dpr, oy + box[1] * dpr)
                time.sleep(0.4)
                type_text(focused(hw), "webview typed")
                time.sleep(0.5)
                checks.append((f"WebView2: a click and keys reached its page (clicked {cls_of(deep)}, "
                               f"typed to {cls_of(focused(hw))})", c.js("i.value") == "webview typed"))
                im = print_window(hw)
                im.save(out.with_name(out.stem + "-webview.png"))
                px = im.convert("RGB").resize((1, 1)).getpixel((0, 0))
                checks.append((f"WebView2: the window's picture is drawn (mean colour {px})", sum(px) > 150))
                c.close()
            finally:
                close(wname)
    code, words = g.verdict()
    for what, ok in checks:
        print(f"  {'ok  ' if ok else 'FAIL'} {what}")
    print(words)
    print(f"pictures: {out.as_posix()}, {out.with_name(out.stem + '-page.png').as_posix()}, {out.with_suffix('.mp4').as_posix()}")
    return 1 if not all(ok for _, ok in checks) else code


if __name__ == "__main__":
    main(sys.argv[1:])
