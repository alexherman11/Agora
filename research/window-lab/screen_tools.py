"""screen_tools: see and record Alex's real screen, as a Claude Code session does (a5378, Alex 15 Oct: the builders
can do everything Claude has been able to do; a design is done only when it is demoed to him).

    python research/window-lab/screen_tools.py look out.png                    the main monitor, as it is now
    python research/window-lab/screen_tools.py look x y w h out.png            a rectangle of the desktop
    python research/window-lab/screen_tools.py look --window <words> out.png   one window, by words of its title
    python research/window-lab/screen_tools.py windows                         the visible windows: handle, x y w h, title
    python research/window-lab/screen_tools.py record <seconds> out.mp4 [x y w h]
    python research/window-lab/screen_tools.py show <seconds> out.mp4 [--wait s] <command ...>
    python research/window-lab/screen_tools.py stop                            ends a recording now (the off switch)

Then open the PNG with Read. `look` changes nothing on the screen. `record` films the main monitor (or the rectangle)
for at most 600 seconds; it also writes <out>-last.png, the last frame, so you can Read what it caught (a video can't be
read). `show` starts a command (a demo), films it, then stops it and everything it started: say on the card what will
appear on Alex's screen before you run it.

Coordinates are real pixels on the virtual desktop: the process is made DPI aware before anything is measured
(without it Windows hands back rectangles scaled to 96 dpi). A bare file name, with no folder, goes to demos/ in
research/window-lab of the MAIN checkout, ignored by git, so a recording outlives the worktree it was made in; name the
file on the card. ffmpeg is found as $FFMPEG, on PATH, or where winget put it.
"""
import ctypes
import glob
import json
import os
import shutil
import subprocess
import sys
import time
from ctypes import wintypes as wt
from pathlib import Path

if sys.platform == "win32":
    ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))     # per monitor v2, before any measure

HERE = Path(__file__).resolve().parent
MAX_SECONDS = 600


def demos():
    """research/window-lab/demos of the main checkout (a worker's worktree is removed when it lands)."""
    def ask(*args):
        try:
            return subprocess.run(["git", "rev-parse", *args], cwd=HERE, capture_output=True, text=True,
                                  timeout=20).stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            return ""
    common, top, main = ask("--path-format=absolute", "--git-common-dir"), ask("--show-toplevel"), HERE
    if common and top:
        try:
            main = Path(common).parent / HERE.relative_to(Path(top).resolve())
        except ValueError:
            pass
    d = main / "demos"
    d.mkdir(parents=True, exist_ok=True)
    return d


def place(out):
    p = Path(out)
    return demos() / p.name if p.parent == Path(".") else p.resolve()


def ffmpeg():
    found = os.environ.get("FFMPEG") or shutil.which("ffmpeg")
    if not found:
        hits = sorted(glob.glob(os.path.expandvars(
            r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\*\bin\ffmpeg.exe")))
        found = hits[-1] if hits else None
    if not found:
        sys.exit("no ffmpeg: set FFMPEG to its path (the builders' notebook names where it is on Alex's PC)")
    return found


class MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", wt.DWORD), ("rcMonitor", wt.RECT), ("rcWork", wt.RECT), ("dwFlags", wt.DWORD)]


def main_monitor():
    """x, y, w, h of the primary monitor, w and h even (x264 needs them so)."""
    u = ctypes.windll.user32
    u.MonitorFromPoint.restype = wt.HMONITOR
    m = u.MonitorFromPoint(wt.POINT(0, 0), 1)
    mi = MONITORINFO()
    mi.cbSize = ctypes.sizeof(mi)
    u.GetMonitorInfoW(m, ctypes.byref(mi))
    r = mi.rcMonitor
    return r.left, r.top, (r.right - r.left) // 2 * 2, (r.bottom - r.top) // 2 * 2


def windows():
    """[(hwnd, x, y, w, h, title)] of visible, uncloaked top-level windows with a title, front to back."""
    u, dwm = ctypes.windll.user32, ctypes.windll.dwmapi
    out = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def each(h, _):
        if not u.IsWindowVisible(h) or u.IsIconic(h):     # hidden or minimized: nothing of it is on the screen
            return True
        n = u.GetWindowTextLengthW(h)
        if not n:
            return True
        buf = ctypes.create_unicode_buffer(n + 1)
        u.GetWindowTextW(h, buf, n + 1)
        cloaked = wt.DWORD()
        dwm.DwmGetWindowAttribute(h, 14, ctypes.byref(cloaked), ctypes.sizeof(cloaked))      # DWMWA_CLOAKED
        if cloaked.value:
            return True
        r = wt.RECT()
        if dwm.DwmGetWindowAttribute(h, 9, ctypes.byref(r), ctypes.sizeof(r)):               # DWMWA_EXTENDED_FRAME_BOUNDS
            u.GetWindowRect(h, ctypes.byref(r))
        if r.right - r.left > 0 and r.bottom - r.top > 0:
            out.append((int(h or 0), r.left, r.top, r.right - r.left, r.bottom - r.top, buf.value))
        return True
    u.EnumWindows(each, 0)
    return out


def look(args):
    from PIL import ImageGrab
    if not args or not args[-1].lower().endswith(".png"):
        sys.exit("look [x y w h | --window <words>] out.png")
    out, rest = place(args[-1]), args[:-1]
    if rest[:1] == ["--window"]:
        words = " ".join(rest[1:]).lower()
        hits = [x for x in windows() if words in x[5].lower()]
        if not hits:
            sys.exit(f"no visible window has '{words}' in its title (windows lists them)")
        _, x, y, w, h, title = hits[0]
        print(f"window: {title}")
        im = ImageGrab.grab(bbox=(x, y, x + w, y + h), all_screens=True)
    elif len(rest) == 4:
        x, y, w, h = (int(v) for v in rest)
        im = ImageGrab.grab(bbox=(x, y, x + w, y + h), all_screens=True)
    elif not rest:
        x, y, w, h = main_monitor()
        im = ImageGrab.grab(bbox=(x, y, x + w, y + h), all_screens=True)
    else:
        sys.exit("look [x y w h | --window <words>] out.png")
    im.save(out)
    print(f"wrote {out.as_posix()} ({im.size[0]}x{im.size[1]}); open it with Read")


STOP = lambda: demos() / ".stop-recording"      # noqa: E731  the off switch: `stop` makes it, the recorder obeys it


def record(seconds, out, rect=None, during=None):
    """Film the main monitor (or rect) for `seconds` (at most MAX_SECONDS), ending early when `stop` is asked or the
    `during` process ends. -> the mp4's path. ffmpeg is told q on its stdin, so the file is always finished."""
    seconds = min(float(seconds), MAX_SECONDS)
    x, y, w, h = rect or main_monitor()
    w, h = w // 2 * 2, h // 2 * 2
    STOP().unlink(missing_ok=True)
    p = subprocess.Popen([ffmpeg(), "-y", "-loglevel", "error", "-f", "gdigrab", "-framerate", "24",
                          "-offset_x", str(x), "-offset_y", str(y), "-video_size", f"{w}x{h}", "-draw_mouse", "1",
                          "-i", "desktop", "-t", str(seconds), "-vf", "scale=trunc(iw/4)*2:-2", "-c:v", "libx264",
                          "-preset", "veryfast", "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)
    (demos() / ".recording").write_text(json.dumps({"pid": p.pid, "out": str(out), "at": time.time()}), encoding="utf-8")
    why = "its time ran out"
    try:
        while p.poll() is None:
            if STOP().exists():
                why = "stop was asked"
            elif during is not None and during.poll() is not None:
                why = "the command it filmed ended"
            else:
                time.sleep(0.2)
                continue
            p.stdin.write(b"q")
            p.stdin.flush()
            p.wait(timeout=30)
    finally:
        if p.poll() is None:
            p.kill()
        STOP().unlink(missing_ok=True)
        (demos() / ".recording").unlink(missing_ok=True)
    frame = out.with_name(out.stem + "-last.png")
    subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-sseof", "-0.5", "-i", str(out), "-frames:v", "1",
                    "-update", "1", str(frame)], capture_output=True)
    size = out.stat().st_size if out.exists() else 0
    print(f"wrote {out.as_posix()} ({size // 1024} KB, {w}x{h} filmed at half size; ended because {why})")
    if frame.exists():
        print(f"its last frame: {frame.as_posix()}; open it with Read to see what it caught")
    return out


def show(args):
    """show <seconds> out.mp4 [--wait s] <command ...>: start the command, wait, film it, then stop it and its children."""
    if len(args) < 3:
        sys.exit("show <seconds> out.mp4 [--wait s] <command ...>")
    seconds, out, rest = args[0], place(args[1]), args[2:]
    wait = 0.0
    if rest[:1] == ["--wait"]:
        wait, rest = float(rest[1]), rest[2:]
    cmd = [sys.executable if c == "python" else c for c in rest]
    proc = subprocess.Popen(cmd, creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
    print(f"started {' '.join(rest)} (pid {proc.pid})")
    try:
        time.sleep(wait)
        record(seconds, out, during=proc)
    finally:
        if proc.poll() is None:      # only what it started: its own process tree
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
            print(f"stopped {proc.pid} and what it started")


def main(argv):
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return
    verb, args = argv[0], argv[1:]
    if verb == "look":
        look(args)
    elif verb == "windows":
        for h, x, y, w, hh, title in windows():
            print(f"{h:>10}  {x:>6} {y:>6} {w:>5} {hh:>5}  {title}")
    elif verb == "record":
        if len(args) not in (2, 6) or not args[1].lower().endswith(".mp4"):
            sys.exit("record <seconds> out.mp4 [x y w h]")
        record(args[0], place(args[1]), tuple(int(v) for v in args[2:]) if len(args) == 6 else None)
    elif verb == "show":
        show(args)
    elif verb == "stop":
        STOP().touch()
        print("asked the recording to stop" if (demos() / ".recording").exists() else "no recording is running")
    else:
        sys.exit(f"no verb {verb}: look, windows, record, show, stop (--help)")


if __name__ == "__main__":
    main(sys.argv[1:])
