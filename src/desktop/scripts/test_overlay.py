"""test_overlay (a6313, 17 Oct 2026): the Rocket League timer's notice shows over a game and never takes it from him.

    python src/desktop/scripts/test_overlay.py [--film]

Everything happens on a sandbox desktop (sandbox_window.py): a desktop of its own that is never shown, so nothing here
reaches Alex's screen, keyboard or game. Never run the real timer, never touch RocketLeague.exe; this test does neither.

  1. A stand-in game (standin_game.py) covers a monitor there, as a borderless game does, and takes the keyboard.
  2. The timer script is started with -ShowNotice, which starts its notice exactly as the watcher does (Send-Notice: a
     hidden powershell drawing the overlay), with -Quiet (no voice on his speakers), -StateDir a temp folder (its log is
     not his) and -OnlyOnDesktop the sandbox's name (the overlay draws nothing anywhere else).
  3. While it is up, every 50 ms: is it visible, above the stand-in, at the top centre of the stand-in's monitor; its
     window styles; which window is ACTIVE and which has the FOCUS in the stand-in's thread and in the overlay's
     thread (GetGUIThreadInfo); what window a click at its centre would reach (WindowFromPoint); the stand-in's own
     focus log. It must go by itself after its seconds.
  4. A control: the old notice (WScript.Shell Popup 0x1030, a system-modal message box) on the same desktop, measured
     the same way, so the test shows its measures would catch a notice that takes activation.
Alex's side is watched all the while by sandbox_window.Guard (foreground, focus, cursor, input desktop every 20 ms, and
no window titled 'rocket league timer' on his desktop). --film writes demos/a6313/overlay-sandbox.mp4: the stand-in
with the overlay composed over it at its place (each window is printed apart; the hidden desktop is not composed).
"""
import ctypes
import json
import subprocess
import sys
import tempfile
import threading
import time
from ctypes import wintypes as wt
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import sandbox_window as sb  # noqa: E402  (DPI awareness first, through screen_tools)
import screen_tools  # noqa: E402

u32 = sb.u32
u32.WindowFromPoint.argtypes = [wt.POINT]
u32.WindowFromPoint.restype = wt.HWND
u32.GetAncestor.argtypes = [wt.HWND, wt.UINT]
u32.GetAncestor.restype = wt.HWND
u32.GetWindowLongW.argtypes = [wt.HWND, ctypes.c_int]
u32.GetWindowLongW.restype = ctypes.c_long
u32.IsWindowVisible.argtypes = [wt.HWND]
u32.MonitorFromWindow.argtypes = [wt.HWND, wt.DWORD]
u32.MonitorFromWindow.restype = wt.HANDLE

SCRIPT = HERE / "RocketLeagueTimer.ps1"
TITLE = "Rocket League timer"
EX = {"NOACTIVATE": 0x8000000, "TOOLWINDOW": 0x80, "TOPMOST": 0x8, "LAYERED": 0x80000, "TRANSPARENT": 0x20}
FILM = "--film" in sys.argv

fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok or not detail else f"\n     {str(detail)[:600]}"))
    if not ok:
        fails.append(name)


class MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", wt.DWORD), ("rcMonitor", wt.RECT), ("rcWork", wt.RECT), ("dwFlags", wt.DWORD)]


def monitors():
    found = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HANDLE, wt.HDC, ctypes.POINTER(wt.RECT), wt.LPARAM)
    def each(h, _, r, __):
        mi = MONITORINFO(cbSize=ctypes.sizeof(MONITORINFO))
        u32.GetMonitorInfoW(h, ctypes.byref(mi))
        m = mi.rcMonitor
        found.append(((m.left, m.top, m.right - m.left, m.bottom - m.top), bool(mi.dwFlags & 1)))
        return True
    u32.EnumDisplayMonitors(None, None, each, 0)
    return found


def gui(tid, name):
    """(active, focus) of a thread there, read from a thread on its desktop (from another desktop the call fails)."""
    return on_sandbox(name, lambda: _gui(tid))


def _gui(tid):
    gi = sb.GUITHREADINFO(cbSize=ctypes.sizeof(sb.GUITHREADINFO))
    if not u32.GetGUIThreadInfo(tid, ctypes.byref(gi)):
        return None
    return int(gi.hwndActive or 0), int(gi.hwndFocus or 0)


def tid_of(hwnd):
    return u32.GetWindowThreadProcessId(hwnd, None)


def on_sandbox(name, fn):
    """fn() run on a thread joined to the sandbox desktop (WindowFromPoint and the foreground are per desktop)."""
    box = []

    def go():
        sb.join(name)
        box.append(fn())
    t = threading.Thread(target=go)
    t.start()
    t.join()
    return box[0]


def wait_for(fn, secs, step=0.05):
    end = time.time() + secs
    while time.time() < end:
        v = fn()
        if v:
            return v
        time.sleep(step)
    return None


def find(name, title):
    """-> (hwnd, z) of the visible window with this title on the sandbox desktop; z 0 is the top of its z-order."""
    for z, w in enumerate(x for x in sb.top_windows(name) if x[4]):
        if w[3] == title:
            return w[0], z, w[5]
    return None


def compose(standin, over, srect, orect):
    im = sb.print_window(standin)
    if over:
        try:
            oi = sb.print_window(over)
            im.paste(oi, (orect[0] - srect[0], orect[1] - srect[1]))
        except RuntimeError:
            pass
    return im.resize((im.size[0] // 3, im.size[1] // 3))


def run_case(mon, primary, tmp, frames):
    name = f"rl-overlay-{int(time.time() * 1000) % 10 ** 8}"
    desk = f"agora-sandbox-{name}"
    (x, y, w, h) = mon
    where = f"{'primary' if primary else 'other'} monitor {w}x{h} at {x},{y}"
    print(f"\n-- on the {where} --")
    out = tmp / name
    out.mkdir()
    try:
        sb.run_hidden(name, ["python", str(HERE / "standin_game.py"), str(out), str(x), str(y), str(w), str(h)])
        if not wait_for(lambda: (out / "standin.json").exists(), 30):
            check(f"{where}: the stand-in game opened on the sandbox desktop", False)
            return
        found = wait_for(lambda: find(name, "stand-in game"), 10)
        standin, _, srect = found
        stid = tid_of(standin)
        time.sleep(0.8)
        before = gui(stid, name)
        check(f"{where}: the stand-in game is the active window with the keyboard in its own thread",
              before and before[0] == standin, before)

        # the notice, started the way the watcher starts it
        argv = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(SCRIPT), "-ShowNotice",
                "-Overlay", "7 minutes of Rocket League left", "-OverlayDetail", "Don't start another match after this one.",
                # "Python", not "python": run_hidden turns an argument that is exactly "python" into the interpreter's
                # path; Get-Process matches names in any case
                "-ProcessName", "Python", "-StateDir", str(out), "-OverlaySeconds", "5", "-Quiet", "-OnlyOnDesktop", desk]
        t0 = time.time()
        sb.run_hidden(name, argv)
        seen = []                     # (t, hwnd, z, rect, exstyle, standin gui, overlay gui, hit)
        ov = None
        end = t0 + 40
        while time.time() < end:
            f = find(name, TITLE)
            if f:
                ov = f
                hwnd, z, rect = f
                cx, cy = rect[0] + rect[2] // 2, rect[1] + rect[3] // 2
                hit = on_sandbox(name, lambda: int(u32.GetAncestor(u32.WindowFromPoint(wt.POINT(cx, cy)), 2) or 0))
                sz = next(i for i, x in enumerate(w for w in sb.top_windows(name) if w[4]) if x[0] == standin)
                seen.append((time.time() - t0, hwnd, z, sz, rect, u32.GetWindowLongW(hwnd, -20) & 0xFFFFFFFF,
                             gui(stid, name), gui(tid_of(hwnd), name), hit))
                if frames is not None and len(seen) % 3 == 1:
                    frames.append(compose(standin, hwnd, srect, rect))
            elif seen:
                break
            elif frames is not None and len(frames) < 10 and time.time() - t0 > 1:
                frames.append(compose(standin, None, srect, None))
            time.sleep(0.05)
        gone_at = time.time() - t0
        logf = out / "Python-timer.log"
        log = logf.read_text(encoding="utf-8-sig") if logf.exists() else ""
        if not seen:
            check(f"{where}: the notice appeared on the sandbox desktop", False, log)
            return
        first, hwnd = seen[0][0], seen[0][1]
        shown_for = seen[-1][0] - first
        print(f"     appeared {first:.1f} s after the start (a powershell starting and compiling it), "
              f"up for {shown_for:.1f} s, polled {len(seen)} times")
        check(f"{where}: it appeared, and went by itself after about its 5 s", 3.5 <= shown_for <= 8 and gone_at < 40,
              f"up {shown_for:.1f} s")
        ex = seen[0][5]
        check(f"{where}: its window styles are " + ", ".join(EX), all(ex & v for v in EX.values()), hex(ex))
        check(f"{where}: it is above the stand-in game every time it was looked at",
              all(s[2] < s[3] for s in seen), [(round(s[0], 1), s[2], s[3]) for s in seen[:5]])
        r = seen[0][4]
        mid = r[0] + r[2] / 2
        check(f"{where}: it is at the top centre of the game's monitor and small ({r[2]}x{r[3]} at {r[0]},{r[1]})",
              abs(mid - (x + w / 2)) <= 2 and y <= r[1] <= y + h * 0.06 and r[2] < w * 0.4 and r[3] < h * 0.12, r)
        check(f"{where}: in the stand-in's thread the active window stayed the stand-in throughout",
              all(s[6] == before for s in seen), [s[6] for s in seen if s[6] != before][:3])
        check(f"{where}: the overlay's own thread never had an active or focused window",
              all(s[7] == (0, 0) for s in seen), [s[7] for s in seen if s[7] != (0, 0)][:3])
        check(f"{where}: a click at its centre reaches the stand-in game, not it",
              all(s[8] == standin for s in seen), [s[8] for s in seen if s[8] != standin][:3])
        flog = (out / "standin-focus.log").read_text(encoding="utf-8").split() if (out / "standin-focus.log").exists() else []
        outs = [float(flog[i]) for i in range(0, len(flog) - 1, 2) if flog[i + 1] == "out" and float(flog[i]) > t0]
        check(f"{where}: the stand-in game never lost the keyboard (its own focus log)", not outs, outs)
        check(f"{where}: the notice's log line says it was over the game",
              "Notice shown over the game" in log, log[-400:])
        print("     its log: " + " | ".join(l.split("  ", 1)[-1] for l in log.strip().splitlines()))

        # the control: the old notice, measured the same way
        if primary:
            ctrl = "rocket league timer (old notice control)"
            sb.run_hidden(name, ["powershell.exe", "-NoProfile", "-Command",
                                 f"(New-Object -ComObject WScript.Shell).Popup('the old notice', 4, '{ctrl}', 0x1030) | Out-Null"])
            got = wait_for(lambda: find(name, ctrl), 20)
            cg = []
            if got:
                for _ in range(10):
                    cg.append((gui(stid, name), gui(tid_of(got[0]), name)))
                    time.sleep(0.1)
                if frames is not None:
                    pass
            check("control: the old message box shows up as its thread's ACTIVE window (so the measure catches it)",
                  bool(got) and any(o and o[0] == got[0] for _, o in cg), cg[:3])
            print(f"     control: the stand-in's thread then read {cg[-1][0] if cg else None} (before: {before}); "
                  f"the box's thread {cg[-1][1] if cg else None} (the box is {got[0] if got else None})")
            wait_for(lambda: not find(name, ctrl), 10)
    finally:
        sb.close(name, quiet=True)


def main():
    tmp = Path(tempfile.mkdtemp(prefix="rl-overlay-"))
    mons = monitors()
    print("monitors: " + "; ".join(f"{m[0][2]}x{m[0][3]} at {m[0][0]},{m[0][1]}{' (primary)' if m[1] else ''}" for m in mons))
    cases = [m for m in mons if m[1]] + [m for m in mons if not m[1]][:1]
    frames = [] if FILM else None
    with sb.Guard("rl-overlay-guard-none", "rocket league timer") as g:
        for mon, primary in cases:
            run_case(mon, primary, tmp, frames if primary else None)
    code, words = g.verdict()
    print("\n" + words)
    if code:
        fails.append("Alex's side")
    if FILM and frames:
        film = screen_tools.demos() / "a6313" / "overlay-sandbox.mp4"
        film.parent.mkdir(parents=True, exist_ok=True)
        fdir = tmp / "frames"
        fdir.mkdir()
        for i, im in enumerate(frames):
            im.convert("RGB").save(fdir / f"{i:05d}.png")
        subprocess.run([screen_tools.ffmpeg(), "-y", "-loglevel", "error", "-framerate", "4", "-i",
                        str(fdir / "%05d.png"), "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-c:v", "libx264",
                        "-pix_fmt", "yuv420p", str(film)], check=True)
        mid = frames[min(len(frames) - 1, 12)]
        mid.save(film.with_suffix(".png"))
        print(f"film: {film.as_posix()} ({len(frames)} frames); a frame with the notice: {film.with_suffix('.png').as_posix()}")
    print(f"\n{len(fails)} failed" if fails else "\nall passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
