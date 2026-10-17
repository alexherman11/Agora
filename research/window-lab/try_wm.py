"""try_wm: the window manager prototype, tried end to end with the tester's own windows only (a5052).

    python try_wm.py [--door http://127.0.0.1:8795] [--as claude] [--layout wm-strip]

Starts wm.py with three Agora windows, opens one ordinary window of its own (a small tkinter window, standing in for
any program), and asks the host, through state/wm.keys, for each thing a key does, naming the window instead of using
the focus so the test never takes Alex's focus. A picture (state/<n>-<step>.png, the host's windows only) follows each
step. Then a lens edit: wm-strip is rewritten to stack the strip vertically, and back. Then the hard way out: the host
is killed, the door stopped, and `wm.py --release-all` must put the ordinary window back where it was and close the
Agora windows from the state file alone. Every timing is the host's own (key or edit -> windows in place).
"""
import argparse
import ctypes
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import wm   # noqa: E402

PY = sys.executable
KEYS = wm.KEYS_FILE
ok_all = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {detail}"), flush=True)
    ok_all.append(ok)


def ask(*lines, wait=2.5):
    KEYS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    time.sleep(wait)


def state():
    return wm.load_state() or {}


def door_do(door, who, line):
    body = json.dumps({"session": "frontier", "as": who, "line": line, "whole": True}).encode()
    r = json.loads(urllib.request.urlopen(urllib.request.Request(door + "/api/do", data=body,
                                                                 headers={"Content-Type": "application/json"}), timeout=60).read())
    return r.get("text") or ("ERR " + str(r.get("error")))


def esc(t):
    return t.replace(chr(92), chr(92) * 2).replace('"', chr(92) + '"').replace("$", chr(92) + "$").replace(chr(10), chr(92) + "n")


def main():
    ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    ap = argparse.ArgumentParser()
    ap.add_argument("--door", default="http://127.0.0.1:8795")
    ap.add_argument("--as", dest="who", default="claude")
    ap.add_argument("--layout", default="wm-strip")
    ap.add_argument("--notation", default=str(HERE.parent / "text-desk-lab" / "notation"))
    ap.add_argument("--stop-door", action="store_true", help="stop the door before release-all (a private door only)")
    a = ap.parse_args()
    wm.LOG.unlink(missing_ok=True)
    for p in wm.STATE_DIR.glob("*-*.png"):
        p.unlink()

    # an ordinary window of the tester's own, standing in for any program
    plain = subprocess.Popen([getattr(sys, "_base_executable", PY), "-c", "import ctypes, tkinter as t; ctypes.windll.shcore.SetProcessDpiAwareness(2); r = t.Tk(); r.title('An ordinary program (the tester own)');"
                              "r.geometry('900x600+300+300'); t.Label(r, text='an ordinary window', font=('Segoe UI', 28)).pack(expand=1); r.mainloop()"])
    time.sleep(1.5)
    found = []
    wm.user32.EnumWindows(wm.WNDENUMPROC(lambda h, _: (found.append(h) if wm.pid_of(h) == plain.pid and wm.user32.IsWindowVisible(h) else None) or True), 0)
    plain_hwnd = found[0]
    plain_was = wm.rect(plain_hwnd)

    host = subprocess.Popen([PY, str(HERE / "wm.py"), "--door", a.door, "--as", a.who, "--layout", a.layout, "--notation", a.notation, "--pictures"])
    time.sleep(16)                   # three windows, the unseen page, its first paint
    st = state()
    names = [w["name"] for w in st.get("windows", [])]
    check("start: three Agora windows kept", names[:3] == ["w1", "w2", "w3"], names)
    ask("snap 1-start")
    ask("slide 1")
    ask("snap 2-slid")
    ask("pin w3")
    ask("snap 3-pinned")
    ask("collapse w2", wait=4)
    ask("snap 4-collapsed")
    st = state()
    w2 = next(w for w in st["windows"] if w["name"] == "w2")
    check("collapse: w2 is collapsed, on its lesser lens when its lens names one", w2["collapsed"], w2)
    ask("expand w2")
    ask("snap 5-expanded")
    ask(f"adopt {plain_hwnd}", wait=3)
    ask("snap 6-adopted")
    st = state()
    x = next((w for w in st["windows"] if w["kind"] == "adopted"), None)
    check("adopt: the ordinary window joins the strip, its place before kept", x is not None and x["hwnd"] == plain_hwnd and x["was"], x)
    check("adopt: it was moved", wm.rect(plain_hwnd) != plain_was, wm.rect(plain_hwnd))

    # a lens edit: the strip stood up on end (rows instead of columns), and back
    have = door_do(a.door, a.who, f"find tags=lens title={a.layout}")
    lid = have.split(f'note "{a.layout}"')[0].split()[-1]
    door_do(a.door, a.who, f"read {lid}")
    ask("mark lens edit: vertical", wait=0.1)
    print(door_do(a.door, a.who, f'do replace {lid} old="  strip : row" new="  strip : column"')[:120])
    time.sleep(3)
    ask("snap 7-vertical")
    door_do(a.door, a.who, f"read {lid}")
    ask("mark lens edit: back", wait=0.1)
    door_do(a.door, a.who, f'do replace {lid} old="  strip : column" new="  strip : row"')
    time.sleep(3)
    ask("release " + x["name"], wait=3)
    check("release: the ordinary window goes back where it was", wm.rect(plain_hwnd) == plain_was, (wm.rect(plain_hwnd), plain_was))
    ask("snap 8-released")

    # the hard way out: adopt it again, then the host dies and the desk stops; release-all has only the state file
    ask(f"adopt {plain_hwnd}", wait=3)
    moved = wm.rect(plain_hwnd)
    ask("timings", wait=0.5)
    host.kill()
    host.wait()
    if a.stop_door:
        port = a.door.rsplit(":", 1)[-1]
        subprocess.run(["powershell", "-NoProfile", "-Command",
                        f"Get-CimInstance Win32_Process -Filter \"name='python.exe' and (CommandLine like '%door.py {port}%' or CommandLine like '%deskd.py%')\" | "
                        f"Where-Object {{ $_.CommandLine -like '*claude-wm*' -or $_.CommandLine -like '*door.py {port}*' }} | ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force }}"],
                       capture_output=True)
        time.sleep(1)
        try:
            urllib.request.urlopen(a.door + "/door/status", timeout=2)
            check("the door is stopped", False, "it still answers")
        except OSError:
            check("the door is stopped", True)
    kept = state()
    t0 = time.perf_counter()
    r = subprocess.run([PY, str(HERE / "wm.py"), "--release-all"], capture_output=True, text=True, timeout=120)
    print(r.stdout.strip())
    agora = [w[k] for w in kept["windows"] if w["kind"] == "agora" for k in ("hwnd", "lesser_hwnd") if w.get(k)]
    time.sleep(1)
    check(f"release-all with the host dead{' and the desk stopped' if a.stop_door else ''}: the ordinary window is back "
          f"({round((time.perf_counter() - t0) * 1000)} ms)", moved != plain_was and wm.rect(plain_hwnd) == plain_was, (wm.rect(plain_hwnd), plain_was))
    check("release-all: every Agora window closed", not any(wm.user32.IsWindow(h) for h in agora), agora)
    left = wm.profile_pids(wm.EDGE_ROOT)
    check("release-all: none of the host's Edges still runs", not left, left)
    plain.kill()
    print("timings:", [l for l in wm.LOG.read_text(encoding="utf-8").splitlines() if "in place in" in l])
    print("all passed" if all(ok_all) else f"{ok_all.count(False)} FAILED")
    return 0 if all(ok_all) else 1


if __name__ == "__main__":
    sys.exit(main())
