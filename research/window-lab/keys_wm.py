"""keys_wm: the window manager's keys pressed for real (a5052): the host's hot keys, not its test asks.

    python keys_wm.py [--door http://127.0.0.1:8795] [--as claude]

try_wm.py names each window in an ask, so it never takes the focus. This one presses the keys as a person does
(SendInput: Ctrl+Alt+<key>), with the focus put on one of the host's own windows first, so it does take the focus for
about half a minute: say so before running it while someone is at the screen. It ends with Ctrl+Alt+Backspace, the key
that releases everything, while the desk runs, and checks that nothing of the host is left.
"""
import argparse
import ctypes
import subprocess
import sys
import time
from ctypes import wintypes as wt
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import wm   # noqa: E402

user32 = ctypes.WinDLL("user32", use_last_error=True)
VK_CONTROL, VK_MENU = 0x11, 0x12
KEYEVENTF_KEYUP = 0x2
results = []


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wt.WORD), ("wScan", wt.WORD), ("dwFlags", wt.DWORD), ("time", wt.DWORD), ("dwExtraInfo", ctypes.c_size_t)]


class INPUT(ctypes.Structure):
    class _U(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT), ("pad", ctypes.c_byte * 32)]
    _anonymous_ = ("u",)
    _fields_ = [("type", wt.DWORD), ("u", _U)]


def press(*vks):
    """Each key down in order, then up in reverse, as one SendInput."""
    seq = [(vk, 0) for vk in vks] + [(vk, KEYEVENTF_KEYUP) for vk in reversed(vks)]
    arr = (INPUT * len(seq))(*[INPUT(type=1, ki=KEYBDINPUT(vk, 0, f, 0, 0)) for vk, f in seq])
    user32.SendInput(len(seq), arr, ctypes.sizeof(INPUT))


def focus(hwnd):
    """The focus onto one of the host's windows. Windows lets a background program take the focus only just after a
    key, so an Alt press and release goes first (the documented way round the foreground lock)."""
    press(VK_MENU)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.4)
    return user32.GetForegroundWindow() == hwnd


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {detail}"), flush=True)
    results.append(ok)


def windows():
    return {w["name"]: w for w in (wm.load_state() or {}).get("windows", [])}


def main():
    ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    ap = argparse.ArgumentParser()
    ap.add_argument("--door", default="http://127.0.0.1:8795")
    ap.add_argument("--as", dest="who", default="claude")
    ap.add_argument("--notation", default=str(HERE.parent / "text-desk-lab" / "notation"))
    a = ap.parse_args()
    host = subprocess.Popen([sys.executable, str(HERE / "wm.py"), "--door", a.door, "--as", a.who, "--notation", a.notation, "--pictures"])
    time.sleep(16)
    ws = windows()
    order = list(ws)
    check("started: three windows", len(ws) == 3, order)

    press(VK_CONTROL, VK_MENU, 0xBE)                          # Ctrl+Alt+.  slide
    time.sleep(1.5)
    check("Ctrl+Alt+. slides the strip", list(windows()) == order[1:] + order[:1], list(windows()))

    target = windows()[order[2]]
    check("the focus is on one of the host's windows", focus(target["hwnd"]))
    press(VK_CONTROL, VK_MENU, ord("P"))                      # pin the focused one
    time.sleep(1.5)
    check(f"Ctrl+Alt+P pins the focused window ({order[2]})", windows()[order[2]]["pinned"])
    wm.KEYS_FILE.write_text("snap k1-pinned\n", encoding="utf-8")
    time.sleep(1.5)
    press(VK_CONTROL, VK_MENU, 0xBD)                          # Ctrl+Alt+-  collapse the focused one
    time.sleep(2.5)
    check("Ctrl+Alt+- collapses it", windows()[order[2]]["collapsed"])
    wm.KEYS_FILE.write_text("snap k2-collapsed\n", encoding="utf-8")
    time.sleep(1.5)
    w = windows()[order[2]]
    focus(w.get("lesser_hwnd") or w["hwnd"])                  # collapsed onto its lesser lens, that window has it now
    press(VK_CONTROL, VK_MENU, 0xBB)                          # Ctrl+Alt+=  expand
    time.sleep(2)
    check("Ctrl+Alt+= expands it", not windows()[order[2]]["collapsed"])
    # an ordinary window of the tester's own: adopted on Ctrl+Alt+A while it has the focus, released on Ctrl+Alt+X
    plain = subprocess.Popen([getattr(sys, "_base_executable", sys.executable), "-c",
                              "import ctypes, tkinter as t; ctypes.windll.shcore.SetProcessDpiAwareness(2); r = t.Tk(); "
                              "r.title('An ordinary program (the tester own)'); r.geometry('1200x800+400+400'); r.mainloop()"])
    time.sleep(2)
    found = []
    wm.user32.EnumWindows(wm.WNDENUMPROC(lambda h, _: (found.append(h) if wm.pid_of(h) == plain.pid and user32.IsWindowVisible(h) else None) or True), 0)
    was = wm.rect(found[0])
    focus(found[0])
    press(VK_CONTROL, VK_MENU, ord("A"))
    time.sleep(2)
    x = next((w for w in windows().values() if w["kind"] == "adopted"), None)
    check("Ctrl+Alt+A adopts the focused ordinary window, and moves it", x is not None and x["hwnd"] == found[0]
          and wm.rect(found[0]) != was, (x, wm.rect(found[0]), was))
    focus(found[0])
    press(VK_CONTROL, VK_MENU, ord("X"))
    time.sleep(2)
    check("Ctrl+Alt+X releases it, back where it was", not any(w["kind"] == "adopted" for w in windows().values())
          and wm.rect(found[0]) == was, (wm.rect(found[0]), was))
    plain.kill()
    kept = wm.load_state()
    press(VK_CONTROL, VK_MENU, 0x08)                         # Ctrl+Alt+Backspace  release everything, stop
    try:
        host.wait(30)
        check("Ctrl+Alt+Backspace stops the host", True)
    except subprocess.TimeoutExpired:
        check("Ctrl+Alt+Backspace stops the host", False, "still running after 30 s")
        host.kill()
    time.sleep(1)
    agora = [w[k] for w in kept["windows"] for k in ("hwnd", "lesser_hwnd") if w.get(k)]
    check("every Agora window closed", not any(user32.IsWindow(h) for h in agora), agora)
    left = wm.profile_pids(wm.EDGE_ROOT)
    check("none of the host's Edges still runs", not left, left)
    print("key timings:", [l.split(" ", 1)[1][:60] for l in wm.LOG.read_text(encoding="utf-8").splitlines() if "in place in" in l][-6:])
    print("all passed" if all(results) else f"{results.count(False)} FAILED")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
