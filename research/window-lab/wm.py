"""wm: a window manager prototype. A lens arranges real windows on the screen (a5052, story a3871).

    python wm.py [--open design-review,command-center,doc-editor] [--layout wm-strip] [--as alex] [--world frontier]
                 [--door http://127.0.0.1:8794] [--monitor N]
    python wm.py --release-all      put back every window the host moved, close the windows it opened, stop its page;
                                    reads only state/wm.json, so it works with the desk stopped (and with the host gone)

Alex never runs these: the home base does (a6113). Its dock icon asks `host wm.start` and `host wm.stop` (wm_switch.py),
which runs this as its child with --parent <the home base's pid>: when that process is gone the host puts everything
back and ends. --keys off (or AGORA_WM_KEYS=off in its environment) takes no global key: tests on the sandbox use it.

What it does. The host opens Agora windows the way lens_window.py does (Edge in app mode on lens.html, its own profile)
and keeps each one's window handle. It does not decide where they go. It paints a LAYOUT LENS, a note in the world
(wm-strip by default), in an unseen page: Edge with no window (headless), sized to the monitor's work area at the
monitor's scale, painting as the viewer `wm`. The painter reports the box of every part it painted (a1473, with
positions since a5047), and the host moves each window to the box of the part keyed by that window's name. The layout
is read once, by the painter, and edited like any lens: change wm-strip and the windows move, with no code changed.

The rows the layout repeats over are the windows the host keeps, written beside the house as the `windows` source
(witnessed.py: witnessed, with age, never in the world). A window with no box in the paint (a clamp left it out) is
minimized until it has one again.

Keys (global, while the host runs):
    Ctrl+Alt+.  Ctrl+Alt+,    slide the strip: the first unpinned window goes last, or back
    Ctrl+Alt+P                pin the focused window, or unpin it (the layout keeps pinned ones in view)
    Ctrl+Alt+-  Ctrl+Alt+=    collapse the focused window to its lesser lens (its lens note says lesser=<lens>; one
                              that names none keeps its lens), and expand it back
    Ctrl+Alt+A                adopt the focused ordinary window into the strip (only on this key, one at a time)
    Ctrl+Alt+X                release the focused adopted window: it goes back where it was
    Ctrl+Alt+Backspace        release everything and stop: adopted windows back where they were, Agora windows closed

What it keeps: intent (order, pinned, collapsed, adopted, and every adopted window's place before) in state/wm.json,
not in the world. With it, every process it started, by identity (pid, creation time, executable): release-all ends
only those that still match, never a pid alone, and a state file from before this boot is put aside untouched
(a6113, after c6176: a stale file's pids belonged to a Claude resident and to Alex's Writing window by then). Nothing else of an ordinary program is read or moved unless it was adopted: the windows the host
looks at are its own Edge's (found by process, never by title) and the one in front when Ctrl+Alt+A is pressed.
"""
import argparse
import ctypes
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from ctypes import wintypes as wt
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTATION = HERE.parent / "text-desk-lab" / "notation"
STATE_DIR = HERE / "state"
STATE = STATE_DIR / "wm.json"
LOG = STATE_DIR / "wm.log"
KEYS_FILE = STATE_DIR / "wm.keys"             # a test's asks, read and removed each tick (see Host.asked)
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
EDGE_ROOT = STATE_DIR / "wm-edge"             # a6113: each run's own Edge profiles, <run>/windows and <run>/unseen
                                              # (run_profiles); never state/edge-profile, lens_window.py's
VIEWER = "wm"

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
dwmapi = ctypes.WinDLL("dwmapi")
shcore = ctypes.WinDLL("shcore")

WNDENUMPROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
SWP_NOZORDER, SWP_NOACTIVATE, SWP_NOOWNERZORDER = 0x4, 0x10, 0x200
SW_HIDE, SW_SHOWNORMAL, SW_SHOWMINNOACTIVE, SW_SHOWNOACTIVATE, SW_RESTORE = 0, 1, 7, 4, 9
WM_CLOSE, WM_HOTKEY, WM_TIMER = 0x0010, 0x0312, 0x0113
MOD_ALT, MOD_CONTROL, MOD_NOREPEAT = 0x1, 0x2, 0x4000
DWMWA_EXTENDED_FRAME_BOUNDS = 9
MONITOR_DEFAULTTOPRIMARY = 1
GA_ROOT = 2
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


class MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", wt.DWORD), ("rcMonitor", wt.RECT), ("rcWork", wt.RECT), ("dwFlags", wt.DWORD)]


class WINDOWPLACEMENT(ctypes.Structure):
    _fields_ = [("length", wt.UINT), ("flags", wt.UINT), ("showCmd", wt.UINT), ("ptMinPosition", wt.POINT),
                ("ptMaxPosition", wt.POINT), ("rcNormalPosition", wt.RECT)]


def _sig(fn, res, *args):
    fn.restype, fn.argtypes = res, list(args)


_sig(user32.EnumWindows, wt.BOOL, WNDENUMPROC, wt.LPARAM)
_sig(user32.GetWindowThreadProcessId, wt.DWORD, wt.HWND, ctypes.POINTER(wt.DWORD))
_sig(user32.IsWindow, wt.BOOL, wt.HWND)
_sig(user32.IsWindowVisible, wt.BOOL, wt.HWND)
_sig(user32.IsIconic, wt.BOOL, wt.HWND)
_sig(user32.IsZoomed, wt.BOOL, wt.HWND)
_sig(user32.GetWindowTextW, ctypes.c_int, wt.HWND, wt.LPWSTR, ctypes.c_int)
_sig(user32.GetClassNameW, ctypes.c_int, wt.HWND, wt.LPWSTR, ctypes.c_int)
_sig(user32.GetForegroundWindow, wt.HWND)
_sig(user32.GetAncestor, wt.HWND, wt.HWND, wt.UINT)
_sig(user32.GetWindowRect, wt.BOOL, wt.HWND, ctypes.POINTER(wt.RECT))
_sig(user32.SetWindowPos, wt.BOOL, wt.HWND, wt.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wt.UINT)
_sig(user32.ShowWindow, wt.BOOL, wt.HWND, ctypes.c_int)
_sig(user32.GetWindowPlacement, wt.BOOL, wt.HWND, ctypes.POINTER(WINDOWPLACEMENT))
_sig(user32.SetWindowPlacement, wt.BOOL, wt.HWND, ctypes.POINTER(WINDOWPLACEMENT))
_sig(user32.PostMessageW, wt.BOOL, wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)
_sig(user32.RegisterHotKey, wt.BOOL, wt.HWND, ctypes.c_int, wt.UINT, wt.UINT)
_sig(user32.UnregisterHotKey, wt.BOOL, wt.HWND, ctypes.c_int)
_sig(user32.SetTimer, ctypes.c_size_t, wt.HWND, ctypes.c_size_t, wt.UINT, wt.LPVOID)
_sig(user32.GetMessageW, ctypes.c_int, ctypes.POINTER(wt.MSG), wt.HWND, wt.UINT, wt.UINT)
_sig(user32.MonitorFromWindow, wt.HMONITOR, wt.HWND, wt.DWORD)
_sig(user32.GetMonitorInfoW, wt.BOOL, wt.HMONITOR, ctypes.POINTER(MONITORINFO))
_sig(dwmapi.DwmGetWindowAttribute, ctypes.c_long, wt.HWND, wt.DWORD, ctypes.c_void_p, wt.DWORD)
_sig(shcore.GetDpiForMonitor, ctypes.c_long, wt.HMONITOR, ctypes.c_int, ctypes.POINTER(wt.UINT), ctypes.POINTER(wt.UINT))
_sig(kernel32.OpenProcess, wt.HANDLE, wt.DWORD, wt.BOOL, wt.DWORD)
_sig(kernel32.CloseHandle, wt.BOOL, wt.HANDLE)
_sig(kernel32.GetExitCodeProcess, wt.BOOL, wt.HANDLE, ctypes.POINTER(wt.DWORD))
_sig(kernel32.TerminateProcess, wt.BOOL, wt.HANDLE, wt.UINT)

_MONITORS = ctypes.WINFUNCTYPE(wt.BOOL, wt.HMONITOR, wt.HDC, ctypes.POINTER(wt.RECT), wt.LPARAM)
_sig(user32.EnumDisplayMonitors, wt.BOOL, wt.HDC, ctypes.POINTER(wt.RECT), _MONITORS, wt.LPARAM)


def log(*a):
    line = time.strftime("%H:%M:%S") + f".{int(time.time() * 1000) % 1000:03d} " + " ".join(str(x) for x in a)
    print(line, flush=True)
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


# ---- windows, through official calls only --------------------------------------------------------------------------
def pid_of(hwnd):
    pid = wt.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value


def alive(pid):
    h = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
    if not h:
        return False
    code = wt.DWORD()
    kernel32.GetExitCodeProcess(h, ctypes.byref(code))
    kernel32.CloseHandle(h)
    return code.value == 259


# ---- which process is which: a pid alone is never trusted (a6113, after Codex's c6176) ------------------------------
# Windows gives a pid to a new process soon after its owner ends: on 16 Oct a stale wm.json named an Edge pid that a
# Claude resident then had. So every process the host starts is kept as {pid, created, exe, parent, line}: its creation
# time (100 ns ticks since 1601, which no later process with the same pid can share) and its executable. Anything is
# killed only when both still match, checked on the very handle that kills it; a record missing either is never killed.
class FILETIME(ctypes.Structure):
    _fields_ = [("lo", wt.DWORD), ("hi", wt.DWORD)]


_sig(kernel32.GetProcessTimes, wt.BOOL, wt.HANDLE, ctypes.POINTER(FILETIME), ctypes.POINTER(FILETIME),
     ctypes.POINTER(FILETIME), ctypes.POINTER(FILETIME))
_sig(kernel32.QueryFullProcessImageNameW, wt.BOOL, wt.HANDLE, wt.DWORD, wt.LPWSTR, ctypes.POINTER(wt.DWORD))
_sig(kernel32.GetTickCount64, ctypes.c_ulonglong)


def _of_handle(h):
    """(created, exe) of an open process handle, or None when it has ended."""
    code = wt.DWORD()
    kernel32.GetExitCodeProcess(h, ctypes.byref(code))
    if code.value != 259:
        return None
    c, e, k, u = FILETIME(), FILETIME(), FILETIME(), FILETIME()
    if not kernel32.GetProcessTimes(h, ctypes.byref(c), ctypes.byref(e), ctypes.byref(k), ctypes.byref(u)):
        return None
    buf, n = ctypes.create_unicode_buffer(1024), wt.DWORD(1024)
    if not kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n)):
        return None
    return (c.hi << 32) | c.lo, buf.value


def identity(pid, **more):
    """-> {pid, created, exe, ...more} of a process running now, or None."""
    h = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
    if not h:
        return None
    try:
        got = _of_handle(h)
    finally:
        kernel32.CloseHandle(h)
    return {"pid": int(pid), "created": got[0], "exe": got[1], **more} if got else None


def created_unix(rec):
    return rec["created"] / 1e7 - 11644473600


def same(rec):
    """'' when the process this record names runs now and is the very one recorded; else why not (in words)."""
    if not isinstance(rec, dict) or not rec.get("pid") or not rec.get("created") or not rec.get("exe"):
        return "its creation time or executable was not recorded"
    now = identity(rec["pid"])
    if now is None:
        return "it is not running"
    if now["created"] != rec["created"]:
        return f"pid {rec['pid']} now belongs to another process (created at another time: {now['exe']})"
    if now["exe"].lower() != str(rec["exe"]).lower():
        return f"pid {rec['pid']} now runs another program ({now['exe']})"
    return ""


def kill_same(rec):
    """End the process this record names only if it is still that one: '' when ended, else why it was left alone.
    The check and the kill use one handle, so the pid cannot change hands between them."""
    if not isinstance(rec, dict) or not rec.get("pid") or not rec.get("created") or not rec.get("exe"):
        return "its creation time or executable was not recorded"
    h = kernel32.OpenProcess(0x0001 | PROCESS_QUERY_LIMITED_INFORMATION, False, int(rec["pid"]))   # TERMINATE too
    if not h:      # ERROR_INVALID_PARAMETER: no process has that pid now
        return "it is not running" if ctypes.get_last_error() == 87 else \
            f"it may not be opened (error {ctypes.get_last_error()}); left alone"
    try:
        got = _of_handle(h)
        if got is None:
            return "it is not running"
        if got[0] != rec["created"] or got[1].lower() != str(rec["exe"]).lower():
            return f"pid {rec['pid']} now belongs to another process ({got[1]}); left alone"
        kernel32.TerminateProcess(h, 0)
        return ""
    finally:
        kernel32.CloseHandle(h)


def boot_time():
    """When Windows last started, as a unix time (to a second or so)."""
    return time.time() - kernel32.GetTickCount64() / 1000


def top_windows_of(pids):
    """The visible top-level windows of these processes (never anyone else's: the pid is asked before anything)."""
    out = []

    def each(hwnd, _):
        if pid_of(hwnd) in pids and user32.IsWindowVisible(hwnd):
            cls = ctypes.create_unicode_buffer(64)
            user32.GetClassNameW(hwnd, cls, 64)
            if cls.value == "Chrome_WidgetWin_1":
                out.append(hwnd)
        return True
    user32.EnumWindows(WNDENUMPROC(each), 0)
    return out


def title(hwnd):
    buf = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(hwnd, buf, 256)
    return buf.value


def rect(hwnd):
    r = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return [r.left, r.top, r.right - r.left, r.bottom - r.top]


def frame_margins(hwnd):
    """The invisible resize borders Windows puts round a window: (left, top, right, bottom) between its rect and the
    edge that is drawn, so the drawn edge lands on the box."""
    outer, ext = wt.RECT(), wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(outer))
    if dwmapi.DwmGetWindowAttribute(hwnd, DWMWA_EXTENDED_FRAME_BOUNDS, ctypes.byref(ext), ctypes.sizeof(ext)) != 0:
        return 0, 0, 0, 0
    return ext.left - outer.left, ext.top - outer.top, outer.right - ext.right, outer.bottom - ext.bottom


def place(hwnd, x, y, w, h):
    if user32.IsIconic(hwnd) or user32.IsZoomed(hwnd):
        user32.ShowWindow(hwnd, SW_SHOWNOACTIVATE if user32.IsIconic(hwnd) else SW_RESTORE)
    l, t, r, b = frame_margins(hwnd)
    user32.SetWindowPos(hwnd, None, x - l, y - t, w + l + r, h + t + b, SWP_NOZORDER | SWP_NOACTIVATE | SWP_NOOWNERZORDER)


def placement(hwnd):
    p = WINDOWPLACEMENT()
    p.length = ctypes.sizeof(WINDOWPLACEMENT)
    user32.GetWindowPlacement(hwnd, ctypes.byref(p))
    r = p.rcNormalPosition
    return {"show": p.showCmd, "normal": [r.left, r.top, r.right, r.bottom], "min": [p.ptMinPosition.x, p.ptMinPosition.y],
            "max": [p.ptMaxPosition.x, p.ptMaxPosition.y], "flags": p.flags}


def put_back(hwnd, was):
    p = WINDOWPLACEMENT()
    p.length = ctypes.sizeof(WINDOWPLACEMENT)
    p.flags, p.showCmd = was["flags"], was["show"]
    p.ptMinPosition, p.ptMaxPosition = wt.POINT(*was["min"]), wt.POINT(*was["max"])
    p.rcNormalPosition = wt.RECT(*was["normal"])
    return bool(user32.SetWindowPlacement(hwnd, ctypes.byref(p)))


def monitors():
    out = []

    def each(hmon, _hdc, _r, _):
        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)
        user32.GetMonitorInfoW(hmon, ctypes.byref(mi))
        dx, dy = wt.UINT(), wt.UINT()
        shcore.GetDpiForMonitor(hmon, 0, ctypes.byref(dx), ctypes.byref(dy))
        w = mi.rcWork
        out.append({"work": [w.left, w.top, w.right - w.left, w.bottom - w.top], "scale": dx.value / 96, "primary": bool(mi.dwFlags & 1)})
        return True
    user32.EnumDisplayMonitors(None, None, _MONITORS(each), 0)
    return out


def profile_procs(profile, since):
    """The browser processes on one of THIS run's own profile folders that began after `since` (unix time), as identity
    records. The folder is made new for the run (run_profiles), so only an Edge this host started can be on it."""
    out = []
    for pid in profile_pids(profile):
        rec = identity(pid, why=f"the browser on {Path(profile).name}")
        if rec and created_unix(rec) >= since - 2:
            out.append(rec)
    return out


def run_profiles():
    """Two new Edge profile folders for one run of the host: (windows, unseen). Never lens_window.py's state/edge-profile,
    which Writing and other app windows use: on 16 Oct release-all would have ended them (c6176). Folders of runs that
    ended are removed (one an Edge still holds stays, and is tried again next time)."""
    import shutil
    EDGE_ROOT.mkdir(parents=True, exist_ok=True)
    for old in EDGE_ROOT.iterdir():
        shutil.rmtree(old, ignore_errors=True)
    run = EDGE_ROOT / time.strftime("%Y%m%d-%H%M%S")
    return run / "windows", run / "unseen"


def profile_pids(profile):
    """The browser process of one of our own Edge profiles (state/edge-*), as Windows lists it: asked by command line
    and filtered there, so no other program's process is listed here. Edge's launcher hands the work to the browser and
    exits, so the process started is not the one that runs."""
    path = str(profile).replace("'", "''")
    q = f"name='msedge.exe' and CommandLine like '%{path}%' and not CommandLine like '%--type=%'".replace(chr(92), chr(92) * 2)
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", f'(Get-CimInstance Win32_Process -Filter "{q}").ProcessId'],
                           capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return set()
    return {int(x) for x in r.stdout.split() if x.isdigit()}


# ---- a picture of the host's own windows, and nothing else on the screen ---------------------------------------------
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
_sig(gdi32.CreateCompatibleDC, wt.HDC, wt.HDC)
_sig(gdi32.CreateCompatibleBitmap, wt.HBITMAP, wt.HDC, ctypes.c_int, ctypes.c_int)
_sig(gdi32.SelectObject, wt.HGDIOBJ, wt.HDC, wt.HGDIOBJ)
_sig(gdi32.DeleteObject, wt.BOOL, wt.HGDIOBJ)
_sig(gdi32.DeleteDC, wt.BOOL, wt.HDC)
_sig(gdi32.StretchBlt, wt.BOOL, wt.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wt.HDC, ctypes.c_int,
     ctypes.c_int, ctypes.c_int, ctypes.c_int, wt.DWORD)
_sig(gdi32.SetStretchBltMode, ctypes.c_int, wt.HDC, ctypes.c_int)
_sig(gdi32.GetDIBits, ctypes.c_int, wt.HDC, wt.HBITMAP, wt.UINT, wt.UINT, ctypes.c_void_p, ctypes.c_void_p, wt.UINT)
_sig(gdi32.PatBlt, wt.BOOL, wt.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wt.DWORD)
_sig(user32.PrintWindow, wt.BOOL, wt.HWND, wt.HDC, wt.UINT)
_sig(user32.GetDC, wt.HDC, wt.HWND)
_sig(user32.ReleaseDC, ctypes.c_int, wt.HWND, wt.HDC)


def snap(hwnds, work, path, shrink=3, how="print"):
    """A PNG of the work area at 1/shrink size, black but for these windows, each drawn by itself (PrintWindow) where it
    stands: what is under or between them on the screen is never read."""
    import struct
    import zlib
    ox, oy, ow, oh = work
    cw, ch = ow // shrink, oh // shrink
    screen = user32.GetDC(None)
    canvas, cbmp = gdi32.CreateCompatibleDC(screen), gdi32.CreateCompatibleBitmap(screen, cw, ch)
    old = gdi32.SelectObject(canvas, cbmp)
    gdi32.PatBlt(canvas, 0, 0, cw, ch, 0x00000042)            # BLACKNESS
    gdi32.SetStretchBltMode(canvas, 4)                        # HALFTONE
    # Edge draws on the GPU, and PrintWindow gets a blank page from it (ran 14 Oct: three white windows). So the host's
    # windows are brought to the front, without taking the focus, and the screen is copied inside each one's own drawn
    # rectangle only: what is between or beside them is never copied
    shown = [h for h in hwnds if h and user32.IsWindow(h) and user32.IsWindowVisible(h) and not user32.IsIconic(h)]
    if how == "screen":
        for h in shown:
            user32.SetWindowPos(h, None, 0, 0, 0, 0, 0x1 | 0x2 | SWP_NOACTIVATE)   # HWND_TOP (0), keep size and place
        time.sleep(0.4)
    for h in shown:
        x, y, w, hh = rect(h)
        l, t, r, b = frame_margins(h)
        vw, vh = w - l - r, hh - t - b                        # the drawn window, without its invisible borders
        if how == "screen":
            gdi32.StretchBlt(canvas, (x + l - ox) // shrink, (y + t - oy) // shrink, vw // shrink, vh // shrink,
                             screen, x + l, y + t, vw, vh, 0x00CC0020)      # SRCCOPY
            continue
        mem, bmp = gdi32.CreateCompatibleDC(screen), gdi32.CreateCompatibleBitmap(screen, w, hh)
        o2 = gdi32.SelectObject(mem, bmp)
        user32.PrintWindow(h, mem, 2)                         # PW_RENDERFULLCONTENT: the window alone, whatever covers it
        gdi32.StretchBlt(canvas, (x + l - ox) // shrink, (y + t - oy) // shrink, vw // shrink, vh // shrink,
                         mem, l, t, vw, vh, 0x00CC0020)
        gdi32.SelectObject(mem, o2)
        gdi32.DeleteObject(bmp)
        gdi32.DeleteDC(mem)
    bmi = (ctypes.c_byte * 40)()
    struct.pack_into("<IiiHHIIiiII", bmi, 0, 40, cw, -ch, 1, 32, 0, 0, 0, 0, 0, 0)
    buf = (ctypes.c_ubyte * (cw * ch * 4))()
    gdi32.SelectObject(canvas, old)
    gdi32.GetDIBits(canvas, cbmp, 0, ch, buf, bmi, 0)
    gdi32.DeleteObject(cbmp)
    gdi32.DeleteDC(canvas)
    user32.ReleaseDC(None, screen)
    raw, data = bytearray(), bytes(buf)
    for y in range(ch):                                       # BGRA rows -> RGB rows, each led by filter 0
        row = data[y * cw * 4:(y + 1) * cw * 4]
        rgb = bytearray(cw * 3)
        rgb[0::3], rgb[1::3], rgb[2::3] = row[2::4], row[1::4], row[0::4]
        raw += b"\x00" + rgb

    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)
    Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", cw, ch, 8, 2, 0, 0, 0))
                           + chunk(b"IDAT", zlib.compress(bytes(raw), 6)) + chunk(b"IEND", b""))
    return path


# ---- the state file: what release-all needs, and nothing it does not ------------------------------------------------
def load_state():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def save_state(st):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps({**st, "saved_at": time.time()}, indent=1), encoding="utf-8")
    os.replace(tmp, STATE)


def stale(st):
    """'' when this state file can be acted on, else why not. A file saved before Windows last started names windows
    and processes that are all gone, their handles and pids since given to others: it is never acted on."""
    at = st.get("saved_at")
    if not isinstance(at, (int, float)):
        return "it has no save time (written by a host from before 16 Oct's fix)"
    if at < boot_time() - 5:
        return f"it was saved at {time.strftime('%d %b %H:%M', time.localtime(at))}, before Windows last started"
    return ""


def retire(why, say=log):
    """Put a state file that must not be acted on aside (state/wm.stale-<when>.json), touching nothing it names."""
    to = STATE.with_name(f"wm.stale-{time.strftime('%Y%m%d-%H%M%S')}.json")
    try:
        os.replace(STATE, to)
    except OSError as e:
        say(f"release-all: could not put the old state file aside ({e}); nothing acted on")
        return
    say(f"release-all: the state file was not acted on, because {why}; it is now {to.name}, and nothing it names was touched")


def host_alive(st):
    """The host that wrote this state, if it runs now and is that very process (identity, not a bare pid)."""
    return bool(st) and not same(st.get("host"))


def release_all(st=None, say=log):
    """Every adopted window back where it was, every Agora window the host opened closed, its Edges stopped, and the
    windows source removed. Reads only the state file: no desk, no door.

    What it ends and what it never does (a6113, c6178): it ends only processes recorded in edge_procs and unseen_procs
    whose creation time and executable still match (kill_same), never a pid alone and never a process found by its
    profile folder. It closes a window only when its process is one of those, and puts an adopted window back only when
    the window's process is still the one recorded at adoption. A file from before this boot, or with no save time, is
    retired untouched (stale, retire). Each thing it leaves alone is named in what it says."""
    st = st or load_state()
    if not st:
        say("release-all: no state file; nothing was kept")
        return 0
    why = stale(st)
    if why:
        retire(why, say)
        return 0
    procs = [r for r in (st.get("edge_procs") or []) + (st.get("unseen_procs") or []) if isinstance(r, dict)]
    ours = {r["pid"] for r in procs if not same(r)}             # the recorded Edges that are still those very processes
    back = closed = 0
    left = []
    for w in st.get("windows", []):
        for key in ("hwnd", "lesser_hwnd"):
            h = w.get(key)
            if not h or not user32.IsWindow(h):
                continue
            if w["kind"] == "adopted" and key == "hwnd":
                rec = w.get("proc")
                whynot = same(rec) or ("" if pid_of(h) == rec.get("pid") else "the window now belongs to another process")
                if whynot or not w.get("was"):
                    left.append(f"adopted window {w.get('title', h)!r} not moved: {whynot or 'no place before was kept'}")
                    continue
                put_back(h, w["was"])
                back += 1
            elif pid_of(h) in ours:
                user32.PostMessageW(h, WM_CLOSE, 0, 0)
                closed += 1
            else:
                left.append(f"window {h} not closed: its process is not one this host started")
    time.sleep(0.5)
    # the Edges the host started go too: an Edge keeps running after its last window closes, and the unseen one has none
    ended = 0
    for r in procs:
        whynot = kill_same(r)
        if not whynot:
            ended += 1
        elif whynot != "it is not running":
            left.append(f"process {r.get('pid')} not ended: {whynot}")
    for line in left:
        say("release-all: LEFT ALONE:", line)
    try:
        sys.path.insert(0, str(Path(st.get("notation") or NOTATION)))
        import witnessed
        witnessed.ROOT = Path(st.get("notation") or NOTATION) / "house-state"
        witnessed.clear(st.get("world") or "frontier", "windows")
    except Exception as e:                       # the desk's code may be what is broken: release-all does not need it
        say("release-all: windows source not removed:", e)
    say(f"release-all: {back} adopted window(s) put back, {closed} Agora window(s) closed, {ended} of the host's own "
        f"Edge process(es) ended, {len(left)} thing(s) left alone")
    save_state({**st, "windows": [], "edge_procs": [], "unseen_procs": [], "released": time.time()})
    return 0


# ---- the host ---------------------------------------------------------------------------------------------------------
BOX = re.compile(r"^(\d+)x(\d+)@(-?\d+),(-?\d+)")


class Host:
    def __init__(self, a):
        self.a = a
        self.world, self.who, self.layout, self.door = a.world, a.who, a.layout, a.door.rstrip("/")
        self.notation = Path(a.notation).resolve()
        sys.path.insert(0, str(self.notation))
        import witnessed
        witnessed.ROOT = self.notation / "house-state"
        self.witnessed = witnessed
        mons = monitors()
        self.mon = mons[a.monitor] if a.monitor is not None else next(m for m in mons if m["primary"])
        self.windows = []            # [{name, kind, lens, hwnd, lesser, lesser_hwnd, pinned, collapsed, pid, was, title}]
        # a6113: every process this host starts, as identity records by pid (kill_same reads them), and this run's own
        # profile folders, so no Edge it did not start can be taken for one of its own
        self.edge_procs, self.unseen_procs, self.unseen_at, self.n = {}, {}, 0, 0
        self.started_at = time.time()
        self.profile = self.unseen_profile = None             # run() makes them (run_profiles)
        self.parent =identity(a.parent) if a.parent else None     # the home base, as the process it is now
        self.report_seen, self.applied, self.focus = None, None, None
        self.pending = None          # (what was asked, when): a key, a lens edit, a start; cleared when windows move
        self.timings = []
        self.parent_checked = 0

    # -- the state file
    def save(self):
        save_state({"world": self.world, "notation": str(self.notation), "host_pid": os.getpid(),
                    "host": identity(os.getpid(), why="the window manager host"),
                    "edge_procs": list(self.edge_procs.values()), "unseen_procs": list(self.unseen_procs.values()),
                    "windows": [{k: v for k, v in w.items()} for w in self.windows]})

    @property
    def edge_pids(self):
        return set(self.edge_procs)

    def keep(self, procs, pid, why):
        """Record a process this host has just started (or found on this run's own profile), once."""
        if pid not in procs:
            rec = identity(pid, why=why, parent=os.getpid())
            if rec:
                procs[pid] = rec

    # -- the windows source: what the layout repeats over
    def say_rows(self, why):
        rows = [{"name": w["name"], "title": w["title"], "lens": (w.get("lesser") or w["lens"]) if w["collapsed"] else w["lens"],
                 "kind": w["kind"], "pinned": "yes" if w["pinned"] else "no", "collapsed": "yes" if w["collapsed"] else "no",
                 "focused": "yes" if w["name"] == self.focus else "no"} for w in self.windows]
        self.witnessed.write(self.world, "windows", rows, by=VIEWER)
        if self.pending is None or not why.startswith("focus"):     # a focus change never takes the clock from a key
            self.pending = (why, time.perf_counter())
        try:
            urllib.request.urlopen(urllib.request.Request(self.door + "/door/witnessed", data=b"{}", method="POST"), timeout=2).read()
        except OSError:
            pass                     # an older door: its stream looks at its next half-second check
        self.save()

    # -- Agora windows
    def url(self, lens, who=None, size=None):
        q = {"session": self.world, "as": who or self.who, "lens": lens, "inspect": "0"}
        return f"{self.door}/lens.html?{urllib.parse.urlencode(q)}"

    def edge(self, profile, *args):
        profile.mkdir(parents=True, exist_ok=True)
        # no crash bubble, no restored session: a window the host did not ask for is not one it would track
        return subprocess.Popen([EDGE, f"--user-data-dir={profile}", "--no-first-run", "--no-default-browser-check",
                                 "--hide-crash-restore-bubble", "--disable-session-crashed-bubble", *args],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def open_window(self, lens):
        """One Agora window on `lens`, found as the window our Edge did not have before. -> hwnd or None."""
        x, y, w, h = self.mon["work"]
        before = set(top_windows_of(self.edge_pids)) if self.edge_pids else set()
        # --pictures: Edge composites without the GPU, so PrintWindow can draw each window alone (it draws a GPU-composited
        # Edge blank; ran 14 Oct). Only tests ask for it: a picture then holds the host's windows and nothing else
        extra = ["--disable-gpu-compositing"] if self.a.pictures else []
        # a6113: InPrivate, no sync: a fresh Edge profile signs itself into Alex's Microsoft account and syncs (a5932)
        p = self.edge(self.profile, *extra, "--inprivate", "--disable-sync", f"--app={self.url(lens)}", f"--window-size={w // 3},{h // 2}", f"--window-position={x + 40},{y + 40}")
        self.keep(self.edge_procs, p.pid, f"Edge for {lens}")      # the first launch on the profile is its browser
        deadline = time.time() + 15
        while time.time() < deadline:
            time.sleep(0.15)
            new = [hw for hw in top_windows_of(self.edge_pids) if hw not in before and hw not in self.hwnds()]
            if new:
                return new[0]
            if not alive(p.pid) and not any(not same(r) for r in self.edge_procs.values()):
                # the launch handed its work to another process and ended: on this run's own new profile folder that
                # process can only be one this host's launch began (and it began after this run started)
                for r in profile_procs(self.profile, self.started_at):
                    self.edge_procs.setdefault(r["pid"], {**r, "parent": None})
        log("no window appeared for", lens)
        return None

    def hwnds(self):
        return {w.get(k) for w in self.windows for k in ("hwnd", "lesser_hwnd") if w.get(k)}

    def lesser_of(self, lens):
        """The lens note's lesser=, read as anyone reads it: `find` through the door, as the viewer wm."""
        try:
            body = json.dumps({"session": self.world, "as": VIEWER, "line": f"find tags=lens title={lens}", "whole": True}).encode()
            r = json.loads(urllib.request.urlopen(urllib.request.Request(self.door + "/api/do", data=body,
                                                                         headers={"Content-Type": "application/json"}), timeout=20).read())
            m = re.search(r'(?:note|lens) "' + re.escape(lens) + r'"[^\n]*?\blesser=([^\s·]+)', r.get("text") or "", re.I)
            return m.group(1) if m else None
        except (OSError, ValueError):
            return None

    def add_agora(self, lens):
        self.n += 1
        hwnd = self.open_window(lens)
        if hwnd:
            self.windows.append({"name": f"w{self.n}", "kind": "agora", "lens": lens, "title": lens, "hwnd": hwnd,
                                 "lesser": None, "lesser_hwnd": None, "pinned": False, "collapsed": False})
            log("opened", lens, "as", f"w{self.n}", hex(hwnd))

    # -- the unseen page
    def start_unseen(self):
        x, y, w, h = self.mon["work"]
        s = self.mon["scale"]
        self.unseen_at = time.time()
        p = self.edge(self.unseen_profile, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--force-device-scale-factor={s}",
                      f"--window-size={round(w / s)},{round(h / s)}", self.url(self.layout, who=VIEWER))
        self.keep(self.unseen_procs, p.pid, "Edge launcher for the unseen page")
        for _ in range(40):
            found = profile_procs(self.unseen_profile, self.started_at)
            for r in found:
                self.unseen_procs.setdefault(r["pid"], {**r, "parent": None})
            if found:
                break
            time.sleep(0.2)
        self.save()
        log(f"unseen page: {self.layout} at {round(w / s)}x{round(h / s)} css px, scale {s}, launcher {p.pid}, browser {sorted(self.unseen_procs)}")

    def report_path(self):
        return self.notation / "house-state" / "reports" / self.world / f"{urllib.parse.quote(VIEWER, safe='')}.json"

    def read_report(self):
        p = self.report_path()
        try:
            st = p.stat()
        except OSError:
            return None
        if self.report_seen == (st.st_mtime_ns, st.st_size):
            return None
        try:
            r = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None                   # mid-write: the next tick reads it
        self.report_seen = (st.st_mtime_ns, st.st_size)
        return r if str(r.get("lens") or "").lower() == self.layout.lower() else None

    def apply(self, rep):
        """Each window to the box of the part keyed by its name; a window with no box is minimized."""
        # The layout's root part is the screen's work area: its box is mapped onto it, so neither the page's own lines
        # (lens.html keeps one at the foot) nor the headless window's chrome (its inner size is less than it was asked)
        # leaves a strip of screen unused. The stretch this makes is about 1% (ran 14 Oct: root 2530x1237 css px).
        boxes = rep.get("boxes") or {}
        ox, oy, ow, oh = self.mon["work"]
        by_name, root = {}, None
        for key, b in boxes.items():
            m = BOX.match(str(b))
            if m:
                box = tuple(int(v) for v in m.groups())
                if "/" not in key:
                    root = box
                by_name.setdefault(key.rsplit("/", 1)[-1], box)
        if not root or root[0] < 8 or root[1] < 8:
            log("the layout's root has no box; nothing moved")
            return
        sx, sy = ow / root[0], oh / root[1]
        moved = []
        for w in self.windows:
            box = by_name.get(w["name"])
            show, hide = (w["lesser_hwnd"], w["hwnd"]) if w["collapsed"] and w.get("lesser_hwnd") else (w["hwnd"], w.get("lesser_hwnd"))
            if hide and user32.IsWindow(hide) and user32.IsWindowVisible(hide):
                user32.ShowWindow(hide, SW_HIDE)
            if not show or not user32.IsWindow(show):
                continue
            if box is None or box[0] < 8 or box[1] < 8:
                if not user32.IsIconic(show):
                    user32.ShowWindow(show, SW_SHOWMINNOACTIVE)
                moved.append((w["name"], "minimized"))
                continue
            bw, bh, bx, by = box
            x0, y0 = round((bx - root[2]) * sx), round((by - root[3]) * sy)
            target = (ox + x0, oy + y0, round((bx - root[2] + bw) * sx) - x0, round((by - root[3] + bh) * sy) - y0)
            if not user32.IsWindowVisible(show):
                user32.ShowWindow(show, SW_SHOWNOACTIVATE)
            place(show, *target)
            moved.append((w["name"], target))
        if self.pending:
            why, t0 = self.pending
            ms = round((time.perf_counter() - t0) * 1000)
            self.timings.append((why, ms))
            log(f"{why}: windows in place in {ms} ms", moved)
            self.pending = None
        else:
            log("repainted (a lens edit, or the page's own poll): windows placed", moved)
        self.applied = moved

    # -- keys
    def focused(self):
        fg = user32.GetAncestor(user32.GetForegroundWindow(), GA_ROOT)
        for w in self.windows:
            if fg and fg in (w.get("hwnd"), w.get("lesser_hwnd")):
                return w
        return None

    def slide(self, step):
        free = [k for k, w in enumerate(self.windows) if not w["pinned"]]
        if len(free) < 2:
            return
        moving = [self.windows[k] for k in free]
        moving = moving[1:] + moving[:1] if step > 0 else moving[-1:] + moving[:-1]
        for k, w in zip(free, moving):
            self.windows[k] = w
        self.say_rows("slide " + ("right" if step > 0 else "left"))

    def named(self, name):
        return next((w for w in self.windows if w["name"] == name), None) if name else self.focused()

    def pin(self, name=None):
        w = self.named(name)
        if w:
            w["pinned"] = not w["pinned"]
            self.say_rows(("pin " if w["pinned"] else "unpin ") + w["name"])

    def collapse(self, on, name=None):
        w = self.named(name)
        if not w or w["collapsed"] == on:
            return
        if on and w["kind"] == "agora" and w.get("lesser") is None:
            w["lesser"] = self.lesser_of(w["lens"]) or ""
            if w["lesser"] and not w.get("lesser_hwnd"):
                w["lesser_hwnd"] = self.open_window(w["lesser"])
        w["collapsed"] = on
        self.say_rows(("collapse " if on else "expand ") + w["name"])

    def adopt(self, hwnd=None):
        fg = int(hwnd) if hwnd else user32.GetAncestor(user32.GetForegroundWindow(), GA_ROOT)
        if not fg or fg in self.hwnds() or pid_of(fg) in self.edge_pids or pid_of(fg) == os.getpid():
            return
        cls = ctypes.create_unicode_buffer(64)
        user32.GetClassNameW(fg, cls, 64)
        if cls.value in ("Shell_TrayWnd", "Progman", "WorkerW", "Shell_SecondaryTrayWnd"):
            return                   # the taskbar and the desktop are not windows to arrange
        self.n += 1
        # only now, adopted on Alex's key, is the window's title read
        at = next((k for k, w in enumerate(self.windows) if not w["pinned"]), len(self.windows))
        self.windows.insert(at, {"name": f"x{self.n}", "kind": "adopted", "lens": "", "title": title(fg) or cls.value, "hwnd": fg,
                             "pid": pid_of(fg), "was": placement(fg), "lesser": None, "lesser_hwnd": None,
                             # a6113: release puts it back only while its process is still this one (never kills it)
                             "proc": identity(pid_of(fg), why="an adopted window's program"),
                             "pinned": False, "collapsed": False})
        self.save()                  # its place before is kept before anything moves it
        self.say_rows(f"adopt x{self.n}")

    def release(self, name=None):
        w = self.named(name)
        if w and w["kind"] == "adopted":
            self.windows.remove(w)
            put_back(w["hwnd"], w["was"])
            self.say_rows("release " + w["name"])

    KEYS = {1: (ord("P"),), 2: (0xBE,), 3: (0xBC,), 4: (0xBD,), 5: (0xBB,), 6: (ord("A"),), 7: (ord("X"),), 8: (0x08,)}

    def on_key(self, k):
        {1: self.pin, 2: lambda: self.slide(1), 3: lambda: self.slide(-1), 4: lambda: self.collapse(True),
         5: lambda: self.collapse(False), 6: self.adopt, 7: self.release}.get(k, lambda: None)()

    # -- what a test asks, in place of keys: one line a key, naming the window instead of the focus (state/wm.keys)
    def asked(self):
        try:
            lines = KEYS_FILE.read_text(encoding="utf-8").splitlines()
            KEYS_FILE.unlink()
        except OSError:
            return False
        for line in lines:
            verb, _, arg = line.strip().partition(" ")
            log("asked:", line.strip())
            if verb == "stop":
                return True
            {"slide": lambda: self.slide(int(arg or 1)), "pin": lambda: self.pin(arg), "collapse": lambda: self.collapse(True, arg),
             "expand": lambda: self.collapse(False, arg), "adopt": lambda: self.adopt(arg), "release": lambda: self.release(arg),
             "timings": lambda: log("timings so far:", self.timings),
             # a test about to change something outside the host (a lens edit) starts the clock here
             "mark": lambda: setattr(self, "pending", (arg or "mark", time.perf_counter())),
             "snap": lambda: log("snap:", snap(self.hwnds(), self.mon["work"], STATE_DIR / f"{arg or 'snap'}.png"))}.get(verb, lambda: log("unknown ask:", line))()
        return False

    # -- the loop
    def tick(self):
        """One look round; -> True when the host should put everything back and stop (its home base is gone)."""
        gone =[w for w in self.windows if not user32.IsWindow(w["hwnd"])]
        for w in gone:
            self.windows.remove(w)
            if w.get("lesser_hwnd") and user32.IsWindow(w["lesser_hwnd"]):
                user32.PostMessageW(w["lesser_hwnd"], WM_CLOSE, 0, 0)       # its lesser goes with it
            log("window gone:", w["name"])
        for w in self.windows:
            if w.get("lesser_hwnd") and not user32.IsWindow(w["lesser_hwnd"]):
                w["lesser_hwnd"], w["lesser"] = None, None                  # its lesser was closed: it shows its own lens
                if w["collapsed"]:
                    w["collapsed"] = False
                    gone.append(w)
        f = self.focused()
        name = f["name"] if f else self.focus
        if gone or name != self.focus:
            self.focus = name
            self.say_rows("closed " + ",".join(w["name"] for w in gone) if gone else "focus " + str(name))
        rep = self.read_report()
        if rep is not None:
            self.apply(rep)
        if self.a.parent and time.time() - self.parent_checked > 1:
            self.parent_checked = time.time()
            # its identity, not its pid: a pid given to a new process must not keep this host running alone
            if self.parent is None or same(self.parent):
                log("the home base that started us is gone (pid", self.a.parent, "); putting everything back")
                return True
        if time.time() - self.unseen_at > 30 and not any(not same(r) for r in self.unseen_procs.values()):
            log("the unseen page stopped; starting it again")         # at most once in 30 s
            self.start_unseen()
        return False

    def run(self):
        st = load_state()
        if st and st.get("windows") and not stale(st) and host_alive(st) and st["host"]["pid"] != os.getpid():
            log("a host is already running (pid", st["host"]["pid"], ")")
            return 76
        if st and not st.get("released"):
            log("a host before this one left its state; putting back what it names first")
            release_all(st)
        self.profile, self.unseen_profile = run_profiles()     # after that release: an old run's folder may be freed
        for lens in [x for x in self.a.open.split(",") if x]:
            self.add_agora(lens)
        time.sleep(0.5)
        for h in top_windows_of(self.edge_pids):
            if h not in self.hwnds():              # our own Edge's, and not asked for (a restored page): closed
                log("closing a window our Edge opened unasked:", hex(h))
                user32.PostMessageW(h, WM_CLOSE, 0, 0)
        self.say_rows("start")
        self.start_unseen()
        ok = [k for k in self.KEYS if self.a.keys == "on"
              and user32.RegisterHotKey(None, k, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, self.KEYS[k][0])]
        if self.a.keys != "on":
            log("--keys off: no global key taken")
        elif len(ok) < len(self.KEYS):
            log("keys taken by another program:", [k for k in self.KEYS if k not in ok])
        user32.SetTimer(None, 0, 30, None)
        msg = wt.MSG()
        try:
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == WM_HOTKEY:
                    if msg.wParam == 8:
                        break
                    self.on_key(msg.wParam)
                elif msg.message == WM_TIMER:
                    if self.asked() or self.tick():
                        break
                if self.a.seconds and time.time() - self.started > self.a.seconds:
                    break
        finally:
            for k in ok:
                user32.UnregisterHotKey(None, k)
            self.save()
            release_all()
            log("timings:", self.timings)
        return 0


def main():
    try:
        user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))   # per-monitor v2: real pixels
    except (AttributeError, OSError):
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--open", default="design-review,command-center,doc-editor")
    ap.add_argument("--layout", default="wm-strip")
    ap.add_argument("--as", dest="who", default="alex")
    ap.add_argument("--world", default="frontier")
    ap.add_argument("--door", default="http://127.0.0.1:8794")
    ap.add_argument("--notation", default=str(NOTATION), help="the lab the door runs from (where reports and rows live)")
    ap.add_argument("--monitor", type=int, default=None, help="which monitor, counting from 0 (default: the primary)")
    ap.add_argument("--pictures", action="store_true", help="draw windows so `snap` can picture each alone (tests)")
    ap.add_argument("--seconds", type=float, default=0, help="stop after this long, putting everything back (tests)")
    ap.add_argument("--parent", type=int, default=None, help="the home base's pid (wm_switch.py): put back and stop when it is gone")
    ap.add_argument("--keys", choices=("on", "off"), default=os.environ.get("AGORA_WM_KEYS", "on"),
                    help="off: take no global key (a test on the sandbox desktop)")
    ap.add_argument("--release-all", action="store_true")
    a = ap.parse_args()
    if a.release_all:
        return release_all()
    h = Host(a)
    h.started = time.time()
    return h.run()


if __name__ == "__main__":
    sys.exit(main())
