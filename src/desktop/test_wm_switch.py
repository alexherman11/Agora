"""test_wm_switch: the dock's Window Manager icon, on the sandbox's hidden desktop with stand-in windows (a6113).

    python src/desktop/test_wm_switch.py --door http://127.0.0.1:8817 --world frontier-try

Needs a door on a COPY of the world (never frontier) that has the dock lines (wm-dock/put.py door ...); it sets
capture=off on that copy's home-base note. Everything runs on a desktop of its own (sandbox_window.py): the home base
(hud.py, --winkey off, AGORA_WM_KEYS=off so neither it nor the window manager takes a global key but Ctrl+Alt+J,
which Alex's own home base holds), two stand-in programs (tkinter; one maximized), the window manager and its Edges.
The home base is never --show'n: shown, it would take a bare Esc while it is; the test shows its window itself.

  1. a click on the icon starts the window manager: its three Agora windows arranged, the icon lit 'Put back';
     both stand-ins adopted (wm.keys, as Ctrl+Alt+A would) and moved
  2. a second click puts everything back: each stand-in's placement exactly as before, the Agora windows and Edges gone,
     the icon back to its start face
  3. crash: the window manager killed (/F): the home base's watcher puts everything back
  4. crash: the home base killed (/F, not its tree): the window manager sees it gone and puts everything back
  5. crash: the home base and the window manager killed together (/T /F): the next home base puts everything back as
     it starts
All the while a guard watches Alex's foreground, focus, cursor and input desktop (sandbox_window.Guard).
"""
import argparse
import ctypes
import json
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sandbox_window as sb  # noqa: E402
import screen_tools  # noqa: E402
import wm  # noqa: E402

PY = sys.executable
BASE = getattr(sys, "_base_executable", PY)
NAME = "wm-switch"
HUD_TITLE = "Agora home base"
results = []


def check(what, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + what + ("" if ok else f"\n     {detail}"), flush=True)
    results.append(ok)
    return ok


def door_do(a, line, who="worker-a6113"):
    body = json.dumps({"session": a.world, "as": who, "line": line, "whole": True}).encode()
    return json.loads(urllib.request.urlopen(urllib.request.Request(a.door + "/api/do", data=body, method="POST"),
                                             timeout=30).read()).get("text") or ""


def wait(what, fn, secs=40, step=0.3):
    t = time.time() + secs
    while time.time() < t:
        got = fn()
        if got:
            return got
        time.sleep(step)
    return None


def find(title, shown=True):
    return next((w[0] for w in sb.top_windows(NAME) if (w[4] or not shown) and w[3] == title), None)


def placement(h):
    p = wm.placement(h)
    return {"show": p["show"], "normal": p["normal"], "rect": wm.rect(h)}


STANDIN = ("import ctypes, tkinter as t; ctypes.windll.shcore.SetProcessDpiAwareness(2); r = t.Tk(); r.title({title!r});"
           "r.geometry({geo!r}); t.Label(r, text={title!r}, font=('Segoe UI', 24)).pack(expand=1);"
           "{zoom}r.mainloop()")


class Hud:
    def __init__(self, a):
        self.a = a
        st = sb.run_hidden(NAME, ["python", str(HERE / "hud.py"), "--door", a.door, "--world", a.world, "--as", "alex",
                                  "--winkey", "off"], cdp=True, env={"AGORA_WM_KEYS": "off"})
        self.port = st["port"]
        self.hwnd = wait("the home base window", lambda: find(HUD_TITLE, shown=False), 60)
        self.cdp = sb.Cdp(self.port)
        wait("its page", lambda: self.cdp.js("document.querySelectorAll('[data-key]').length > 20"), 60)
        # shown by the test, not by the home base (which would take Esc): the page is painted and takes clicks
        ctypes.windll.user32.ShowWindow(self.hwnd, 4)            # SW_SHOWNOACTIVATE
        self.pid = int((HERE / "state" / "hud.pid").read_text())

    def face(self):
        """'start', 'on', 'epic' or None: which face of the Window Manager icon is painted."""
        # every icon carries the parts its guards leave out, unpainted: only a painted one counts
        return self.cdp.js("""(() => { for (const e of document.querySelectorAll('[data-key]')) {
              if (!e.getClientRects().length) continue;
              const k = e.dataset.key, t = e.textContent.trim();
              if (/\\/wmon$/.test(k)) return 'on';
              if (/\\/wm$/.test(k)) return 'start';
              if (/\\/view$/.test(k) && t.includes('Window Manager')) return 'epic'; } return null; })()""")

    def click(self, part):
        box = self.cdp.js(f"""(() => {{ for (const e of document.querySelectorAll('[data-key]'))
              if (/\\/{part}$/.test(e.dataset.key) && e.getClientRects().length) {{ const r = e.getBoundingClientRect();
                return [r.x + r.width / 2, r.y + r.height / 2]; }} return null; }})()""")
        if not box:
            return False
        ox, oy, dpr = sb.page_origin(self.hwnd, self.cdp)
        sb.click_at(self.hwnd, ox + box[0] * dpr, oy + box[1] * dpr)
        return True

    def shot(self, name):
        out = screen_tools.place(name)
        sb.page_shot(self.cdp).save(out)
        return out

    def close(self):
        try:
            self.cdp.close()
        except Exception:
            pass


def wm_state():
    return wm.load_state() or {}


def agora_hwnds(st):
    return [w["hwnd"] for w in st.get("windows", []) if w["kind"] == "agora" and w.get("hwnd")]


def arranged(n=3):
    st = wm_state()
    hs = agora_hwnds(st)
    if len(hs) < n or "windows in place" not in (wm.LOG.read_text(encoding="utf-8") if wm.LOG.exists() else ""):
        return None
    return st


def edges_left():
    return wm.profile_pids(wm.EDGE_ROOT)            # every run's own folders (a6113): no other program's Edge


def adopt(hwnds):
    wm.KEYS_FILE.write_text("".join(f"adopt {h}\n" for h in hwnds), encoding="utf-8")
    return wait("adopted", lambda: len([w for w in wm_state().get("windows", []) if w["kind"] == "adopted"]) == len(hwnds), 15)


def back(standins, before):
    return all(placement(h) == before[h] for h in standins)


def all_back(standins, before, label, agora):
    ok = wait("back", lambda: back(standins, before), 30)
    check(f"{label}: each stand-in's placement is exactly as before", ok,
          {h: (placement(h), before[h]) for h in standins})
    check(f"{label}: the Agora windows are closed", wait("closed", lambda: not any(wm.user32.IsWindow(h) for h in agora), 15),
          [h for h in agora if wm.user32.IsWindow(h)])
    left = wait("edges", lambda: not edges_left() or None, 20)
    check(f"{label}: none of the window manager's Edges runs", left, edges_left())


def start_by_click(hud, label):
    check(f"{label}: the icon shows its start face", wait("face", lambda: hud.face() == "start", 20), hud.face())
    t0 = time.time()
    if wm.LOG.exists():           # what the last release said: what it ended and what it left alone (c6178)
        for ln in wm.LOG.read_text(encoding="utf-8").splitlines():
            if "release-all" in ln:
                print("     log:", ln[13:])
    wm.LOG.unlink(missing_ok=True)
    check(f"{label}: the icon was clicked", hud.click("wm"))
    st = wait("arranged", arranged, 60)
    if not check(f"{label}: the window manager runs with its three Agora windows arranged "
                 f"({round(time.time() - t0, 1)} s from the click)", st, wm_state()):
        raise SystemExit("it did not start; the rest would prove nothing")
    return st


def main():
    ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    ap = argparse.ArgumentParser()
    ap.add_argument("--door", default="http://127.0.0.1:8817")
    ap.add_argument("--world", default="frontier-try")
    a = ap.parse_args()
    if a.world == "frontier" or a.door.endswith(":8794"):
        sys.exit("a copy of the world only, on a door of its own")
    put = [PY, str(HERE / "wm-dock" / "put.py")]
    print(subprocess.run(put + ["door", a.door, a.world], capture_output=True, text=True).stdout.strip()[-300:])
    if "capture=off" not in door_do(a, "read a5208").splitlines()[0]:
        print(door_do(a, "do prop a5208 capture=off").strip()[-200:])
    sb.close(NAME, quiet=True)
    (HERE / "state" / "hud.pid").unlink(missing_ok=True)
    wm.KEYS_FILE.unlink(missing_ok=True)

    # the guard's word must be one only the sandbox's windows have: 'agora' matched Alex's own home base and the house's
    # consoles (ran 16 Oct). Its other check, any window of a process the sandbox started, needs no word
    with sb.Guard(NAME, "stand-in") as guard:
        try:
            run(a)
        finally:
            sb.close(NAME)
            wm.release_all(say=print)
    code, words = guard.verdict()
    print(words)
    if subprocess.run(put + ["check", a.door, a.world], capture_output=True).returncode:
        print("NOTE: the copy lost the dock lines during the run (a landing recopies frontier-try): a failure of a "
              "face may be that, not the code")
    print(f"{results.count(True)} passed, {results.count(False)} failed")
    return 1 if (False in results or code) else 0


def run(a):
    # the stand-ins: ordinary programs, one normal and one maximized
    sb.run_hidden(NAME, [BASE, "-c", STANDIN.format(title="stand-in one", geo="760x520+180+140", zoom="")])
    sb.run_hidden(NAME, [BASE, "-c", STANDIN.format(title="stand-in two", geo="640x420+1200+380",
                                                    zoom="r.state('zoomed');")])
    sb.join(NAME)
    one = wait("stand-in one", lambda: find("stand-in one"), 20)
    two = wait("stand-in two", lambda: find("stand-in two"), 20)
    time.sleep(1)
    standins = [one, two]
    before = {h: placement(h) for h in standins}
    print("stand-ins:", before)

    hud = Hud(a)
    try:
        # 1. one click starts it
        st = start_by_click(hud, "1 start")
        agora = agora_hwnds(st)
        check("1 start: the icon is lit 'Put back'", wait("on", lambda: hud.face() == "on", 15), hud.face())
        hud.shot("wm-switch-1-on.png")
        check("1 start: the window manager took no global key (--keys off)",
              "--keys off: no global key taken" in wm.LOG.read_text(encoding="utf-8"))
        rects = {h: wm.rect(h) for h in agora}
        xs = sorted(r[0] for r in rects.values())
        check("1 start: the Agora windows stand side by side (a strip)", len(set(xs)) == len(xs), rects)
        check("1 start: both stand-ins adopted into the strip", adopt(standins), wm_state().get("windows"))
        time.sleep(2)
        check("1 start: both stand-ins were moved", all(placement(h) != before[h] for h in standins),
              {h: placement(h) for h in standins})
        wm.KEYS_FILE.write_text("snap wm-switch-arranged\n", encoding="utf-8")
        time.sleep(2)

        # 2. a second click puts everything back
        check("2 stop: the lit icon was clicked", hud.click("wmon"))
        all_back(standins, before, "2 stop", agora)
        check("2 stop: the icon is back to its start face", wait("face", lambda: hud.face() == "start", 15), hud.face())
        hud.shot("wm-switch-2-off.png")

        # 3. the window manager crashes
        st = start_by_click(hud, "3 crash wm")
        agora = agora_hwnds(st)
        adopt(standins)
        time.sleep(2)
        moved = all(placement(h) != before[h] for h in standins)
        subprocess.run(["taskkill", "/PID", str(st["host_pid"]), "/F"], capture_output=True)
        all_back(standins, before, "3 crash wm (killed /F while both stand-ins were adopted)", agora)
        check("3 crash wm: they had been moved before the kill", moved)
        check("3 crash wm: the icon is back to its start face", wait("face", lambda: hud.face() == "start", 15), hud.face())

        # 4. the home base crashes, the window manager lives on
        st = start_by_click(hud, "4 crash hud")
        agora = agora_hwnds(st)
        adopt(standins)
        time.sleep(2)
        hud.close()
        subprocess.run(["taskkill", "/PID", str(hud.pid), "/F"], capture_output=True)
        all_back(standins, before, "4 crash hud (the home base killed /F, its window manager left running)", agora)
        check("4 crash hud: the window manager ended by itself", wait("ended", lambda: not wm.alive(st["host_pid"]), 15))
    finally:
        hud.close()

    # 5. both die at once; the next home base puts things back
    hud = Hud(a)
    try:
        st = start_by_click(hud, "5 crash both")
        agora = agora_hwnds(st)
        adopt(standins)
        time.sleep(2)
        hud.close()
        subprocess.run(["taskkill", "/PID", str(hud.pid), "/T", "/F"], capture_output=True)
        time.sleep(2)
        check("5 crash both: with both killed, the stand-ins are still where the strip put them",
              all(placement(h) != before[h] for h in standins))
        hud = Hud(a)                                  # the next start
        all_back(standins, before, "5 crash both, then the home base started again", agora)
        check("5 crash both: the new home base shows the start face", wait("face", lambda: hud.face() == "start", 30),
              hud.face())
    finally:
        hud.close()


if __name__ == "__main__":
    sys.exit(main())
