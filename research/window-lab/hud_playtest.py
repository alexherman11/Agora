"""hud_playtest.py: the home base played as Alex plays it, every step timed, on a copy of the world (a6040, 16 Oct).
OWNER: worker-a6040. Alex, 16 Oct 15:07: 'the process needs much more playtesting.'

    python research/window-lab/hud_playtest.py                    play it; the report goes to the live world
    python research/window-lab/hud_playtest.py --report none      play it; print the report only
    python research/window-lab/hud_playtest.py --only board,chat  some steps (see --list), the rest skipped
    python research/window-lab/hud_playtest.py --assume a5994     run the steps of a commission that has not landed
                                                                  (a branch about to land: try your work before it does)
    python research/window-lab/hud_playtest.py --apply a.desk,b.lens   your world half, applied to the copy first:
                                                                  .desk lines, .lens/.verb notes in Home base (put.py's way)
    python research/window-lab/hud_playtest.py --break card       break a lens in the copy first, to see a step fail
    python research/window-lab/hud_playtest.py --list             the steps, their budgets and what they wait on

What it does. It copies the world (--world, default frontier-try where it exists, else frontier) and serves the copy
by a door of its own with THIS checkout's painter, as screen.py does; the house of the copy is staged busy (residents
and builders at work) with six stand-in windows, as hud_stage.py does. It opens the home base lens as alex in a REAL
Edge window on a desktop Alex never sees (sandbox_window.py, a5932), 2560x1440 at his 150 %, with a stand-in for the
home base's host (host verbs are recorded, not done). Then it walks through his day: each step finds its part as a
person would (by the words on it), presses it with Windows messages to that window only, and measures, in the page,
from the input event to the first frame where the asserted result is painted (and to the first change of any kind).
A step passes when its result shows; it is slow over 300 ms (the aim is 100); a step for a commission that has not
landed skips with a note; one whose feature is missing says so. Every step takes a shot of the window.

Where it writes. Shots and report.md/json: research/window-lab/demos/hud-playtest/<when>/ of the main checkout (they
outlive a worktree). With --report live (the default when the live door answers): the note "HUD playtest" in JEFF's
corner (role=hud-playtest) is rewritten, its earlier verdicts kept at its foot (and every version in its history), and
when a step that passed last time fails now, a 'HUD playtest failed' notice goes to Alex's notices. --by <name> signs
those acts (default hud-playtest). Nothing else reaches the shared world: every press is in the copy.

The guard. sandbox_window.Guard watches Alex's foreground, focus, cursor and input desktop every 20 ms through the run;
its verdict is in the report. --headless runs the same walk in headless Chrome instead (no window at all; input by
DevTools), for a machine where the sandbox can't open.

A builder before landing: run it from your worktree (it plays your painter), with --assume <your card> and --apply
<your world half>; a run with --assume, --apply, --break or --only never writes the standing report.

Scroll checks (UNVERIFIED in a6549): --only scroll selects the wheel checks.
Fixtures stay in the copy; real wheel input must move content while the HUD
stays at 0. Reader waits on a6460 or --assume a6460 with its --apply files. See hud_scroll.py.

Steps are scanned from playtest_steps/*.py and sorted by their declared (order, name).
Add one file exporting STEP = Step(...); see playtest_steps/README.md.
--list prints the current steps, budgets and feature dependencies without opening a browser.
"""
import asyncio
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import websockets

if __name__ == "__main__":
    sys.modules.setdefault("hud_playtest", sys.modules[__name__])

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1] / "research" / "text-desk-lab" / "notation"
sys.path.insert(0, str(LAB))
sys.path.insert(0, str(HERE))
import screen        # noqa: E402  (the browser list, Page, free_port, wait_http)
import screen_tools  # noqa: E402  (demos/, DPI awareness)
import witnessed     # noqa: E402
import agora_tmp     # noqa: E402

PY = sys.executable
LIVE = "http://127.0.0.1:8794"
OK_MS, SLOW_MS = 100, 300
SIZE, SCALE = (2560, 1440), 1.5          # Alex's 3840x2160 at 150 % (a5736)
WINDOWS = [("Visual Studio Code", "Code.exe"), ("Inbox - Mail", "olk.exe"), ("Music", "Spotify.exe"),
           ("Agora notation - Terminal", "WindowsTerminal.exe"), ("Docs - Edge", "msedge.exe"), ("Files", "explorer.exe")]
DUSK = ("html{background:radial-gradient(1200px 800px at 18% 22%,#2a3c4a 0%,transparent 60%),"
        "radial-gradient(900px 700px at 82% 70%,#3a2a40 0%,transparent 62%),#0b0d10 fixed!important}"
        "body,#paint{background:transparent!important}")
# --break: a lens changed in the copy before the walk, to prove the step that should notice does (a6040's done check)
BREAKS = {
    "card": ("home-board", "  fold inline handle cardopen\n", "", "a board card no longer opens on a press: `card` should fail"),
    # the Later of an item not opened fully (the one a press meets): it closes the item but no longer marks it
    "later": ("waiting-on-me", '!= "yes" do prop $item review=later; do prop $rd reviewing=""',
              '!= "yes" do prop $rd reviewing=""', "Later no longer marks the item: `later` should fail"),
}

# In the page from its first line: the timer, the finders, and a stand-in for the home base's host (hud.py's js_api).
PT_JS = r"""(() => {
  const pt = window.__pt = { last: 0, lastType: '', first: 0, done: 0, pred: null, host: [], errors: [], opened: 0 };
  const quiet = n => { for (let e = n && (n.nodeType === 1 ? n : n.parentElement); e; e = e.parentElement)
    if (e.dataset && e.dataset.key && /lens:home-widgets|\/live\b/.test(e.dataset.key)) return true; return false; };
  // a6153: a press is timed from the release that ends it: the click (or a drag's eaten click) that follows a release
  // within 500 ms is the same press, and no longer starts the clock again (a drag's landing box, shown at the release,
  // was never counted as its first change)
  for (const t of ['mouseup', 'pointerup', 'click', 'dblclick', 'keydown', 'contextmenu'])
    addEventListener(t, e => { const now = e.timeStamp || performance.now();
      if ((t === 'click' || t === 'dblclick' || t === 'mouseup') && /^(pointerup|mouseup)$/.test(pt.lastType) && pt.last && now - pt.last < 500) return;
      pt.last = now; pt.lastType = t; pt.first = 0; }, true);
  new MutationObserver(ms => { if (pt.last && !pt.first && ms.some(m => !quiet(m.target))) pt.first = performance.now(); })
    .observe(document, { subtree: true, childList: true, attributes: true, characterData: true });
  addEventListener('error', e => pt.errors.push(String(e.message).slice(0, 200)));
  // where a press's time goes: each request to the desk (the act, the scene after it), when it began and how long
  pt.reqs = []; const f0 = window.fetch;
  window.fetch = (u, o) => { const s = String(u), kind = s.startsWith('/api/do') ? 'do' : s.startsWith('/api/scene') ? 'scene' : null;
    if (!kind) return f0(u, o); const t = performance.now();
    return f0(u, o).then(r => { pt.reqs.push([kind, t, performance.now() - t]); return r; }, e => { pt.reqs.push([kind + ' lost', t, performance.now() - t]); throw e; }); };
  const openTick = () => { if (!pt.opened && document.querySelector('#paint [data-key^="home/tiles"] [data-key]')
      && document.querySelector('#paint [data-key^="home/dock"] [data-key]')) pt.opened = performance.now();
    if (!pt.opened) requestAnimationFrame(openTick); };
  requestAnimationFrame(openTick);
  pt.vis = e => { if (!e || !e.isConnected) return false; const r = e.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && r.bottom > 0 && r.right > 0 && r.top < innerHeight && r.left < innerWidth
      && !e.closest('[hidden]') && getComputedStyle(e).visibility !== 'hidden'; };
  // 'lens:x' is a whole segment of a key (lens:home-board is not lens:home-board-small); anything else, a substring
  pt.all = sub => { const seg = sub.startsWith('lens:') ? new RegExp('(^|/)' + sub.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '(/|$)') : null;
    return [...document.querySelectorAll('#paint [data-key]')].filter(e => seg ? seg.test(e.dataset.key) : e.dataset.key.includes(sub)); };
  pt.parts = sub => pt.all(sub).filter(pt.vis);
  pt.part = sub => pt.parts(sub)[0] || null;
  pt.key = k => { const e = document.querySelector(`#paint [data-key="${CSS.escape(k)}"]`); return e && pt.vis(e) ? e : null; };
  // a leaf with exactly these words (or starting with them, words ending in …), under scope (default the page)
  pt.leaf = (words, scope) => [...(scope || document).querySelectorAll('#paint [data-key], [data-key]')].find(e =>
    pt.vis(e) && !e.querySelector('[data-key]') && (words.endsWith('…') ? e.textContent.trim().startsWith(words.slice(0, -1)) : e.textContent.trim() === words)) || null;
  // a6271: an icon with no words is found by the name its tip says (what a person reads with the pointer on it)
  pt.tipped = (name, scope, sub) => scope ? [...scope.querySelectorAll('[data-tip]')].find(e => pt.vis(e) && e.dataset.tip === name
    && (!sub || e.dataset.key.includes(sub))) || null : null;
  pt.acts = e => (e && e._n && e._n.acts || []).map(a => a.on);
  pt.pressable = e => { for (let x = e; x && x.id !== 'paint'; x = x.parentElement)
    if (x.dataset && (x.dataset.host || x.dataset.carry || x.dataset.foldInline || x.dataset.clamped) || pt.acts(x).some(a => a === 'click' || a === 'edit' || a === 'menu') || x.tagName === 'BUTTON') return x;
    return null; };
  pt.center = e => { if (!e) return null; e.scrollIntoView({ block: 'nearest', inline: 'nearest' }); const r = e.getBoundingClientRect();
    return [r.left + r.width / 2, r.top + r.height / 2]; };
  pt.rect = e => { if (!e) return null; const r = e.getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; };
  pt.arm = src => { pt.pred = new Function('pt', 'return (' + src + ')'); pt.last = 0; pt.first = 0; pt.done = 0; pt.err = '';
    let already = false; try { already = !!pt.pred(pt); } catch (e) { pt.err = String(e); }
    const tick = () => { if (!pt.pred) return;
      if (pt.last && !pt.done) { let ok = false; try { ok = !!pt.pred(pt); } catch (e) { pt.err = String(e); }
        if (ok) { pt.done = performance.now(); pt.dIn = pt.last; pt.dType = pt.lastType; pt.dFirst = pt.first; } }
      if (!pt.done) requestAnimationFrame(tick); };
    requestAnimationFrame(tick); return already; };
  pt.wait = ms => new Promise(r => { const t0 = performance.now(); const f = () => {
    if (pt.done || performance.now() - t0 > ms) { const ok = !!pt.done;
      const t0in = ok ? pt.dIn : pt.last, until = ok ? pt.done : performance.now();
      const reqs = pt.reqs.filter(q => t0in && q[1] >= t0in - 5 && q[1] <= until).map(q => [q[0], Math.round(q[1] - t0in), Math.round(q[2])]);
      const out = { ok, input: t0in, type: ok ? pt.dType : pt.lastType, first: ok ? pt.dFirst : pt.first, reqs,
                    done: pt.done, err: pt.err, sawInput: !!pt.last,
                    status: ((document.getElementById('status') || {}).textContent || '').slice(0, 300) };
      pt.pred = null; r(out); } else setTimeout(f, 8); }; f(); });
  window.pywebview = { api: { host: async (verb, rest) => { pt.host.push(verb + (rest ? ' ' + rest : '')); return 'ok ' + verb + ' (playtest stand-in host)'; } } };
})();"""


# ---- the copy: a world, a door and a staged house of its own ------------------------------------------------------

def sweep():
    """Copies an earlier run left behind when it was stopped mid-way (the house restarting kills it): only this
    script's own (<world>-playtest-<pid>), and only when that process is gone."""
    import re
    for p in (LAB / "sessions").glob("*-playtest-*.pickle*"):
        m = re.search(r"-playtest-(\d+)", p.name)
        if not m or int(m.group(1)) == os.getpid():
            continue
        alive = subprocess.run(["tasklist", "/FI", f"PID eq {m.group(1)}", "/NH"], capture_output=True, text=True).stdout
        if m.group(1) not in alive:
            p.unlink(missing_ok=True)
            shutil.rmtree(LAB / "house-state" / p.name.split(".pickle")[0], ignore_errors=True)
            print(f"hud_playtest: removed {p.name}, left by a run that was stopped", flush=True)


class Copy:
    def __init__(self, world):
        sweep()
        src = LAB / "sessions" / f"{world}.pickle"
        if not src.exists():
            sys.exit(f"hud_playtest: no world {world!r} in {LAB / 'sessions'}")
        self.world, self.session = world, f"{world}-playtest-{os.getpid()}"
        self.pickle = LAB / "sessions" / f"{self.session}.pickle"
        shutil.copy(src, self.pickle)
        if not os.environ.get("PLAYTEST_NOLOG"):
            # a6153: as the live world is kept, a snapshot plus the log since (Snappy Desk): a copy without a log pickles
            # the whole world twice at every write, and each press's act timed ~200-250 ms slower than it is live
            # (screen.py --logged, a6010). PLAYTEST_NOLOG=1 plays the old way, to compare
            import pickle
            import store
            store.genesis(pickle.loads(self.pickle.read_bytes()), self.pickle, why="hud_playtest")
        self.state = agora_tmp.directory("playtest-door-")
        shell = Path(self.state) / "desk-shell"
        shutil.copytree(LAB / "desk-shell", shell)
        # the house as the real one stands: windows open, residents and builders at work (hud_stage.py, a5534)
        self.house = LAB / "house-state" / self.session
        witnessed.write(self.session, "desktop", [{"name": str(1000000 + i), "title": t, "program": p, "front": "yes" if i == 0 else "no"}
                                                  for i, (t, p) in enumerate(WINDOWS)], by="hud_playtest")
        doing = {"f5189": ("jeff", "working"), "f571": ("sable", "working"), "f576": ("pike", "resting"),
                 "a5496": ("worker-a5496", "working"), "a5530": ("worker-a5530", "working")}
        st = {"pid": os.getpid(), "beat": time.time() + 3600, "world": self.session, "workers": {},
              "residents": {c: {"actor": n, "alive": True, "doing": d, "turns": 3, "last_turn": time.time()} for c, (n, d) in doing.items()}}
        (self.house / "house.json").write_text(json.dumps(st), encoding="utf-8")
        self.port = screen.free_port()
        self.srv = subprocess.Popen([PY, "door.py", str(self.port), "--no-git", "--state", self.state, "--static", str(shell)],
                                    cwd=LAB, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        screen.wait_http(f"http://127.0.0.1:{self.port}/lens.html", 60)
        self.base = f"http://127.0.0.1:{self.port}"

    def url(self, lens="home-base", who="alex"):
        return f"{self.base}/lens.html?" + urllib.parse.urlencode({"session": self.session, "as": who, "lens": lens, "view": "painter", "inspect": "0"})

    def do(self, line, who="alex"):
        return door(self.base, self.session, who, line)

    def at(self):
        try:
            with urllib.request.urlopen(f"{self.base}/api/events?session={self.session}&since=999999999", timeout=10) as r:
                return json.loads(r.read()).get("total")
        except Exception:
            return None

    def close(self):
        self.srv.terminate()
        try:
            self.srv.wait(timeout=10)
        except Exception:
            self.srv.kill()
        time.sleep(3.5)                     # the door's deskd goes within 3 s of the door (screen.py)
        shutil.rmtree(self.state, ignore_errors=True)
        shutil.rmtree(self.house, ignore_errors=True)
        for p in self.pickle.parent.glob(self.pickle.stem + "*"):
            p.unlink(missing_ok=True)
        shutil.rmtree(LAB / "house-state" / "reports" / self.pickle.stem, ignore_errors=True)


def door(base, session, who, line):
    """One desk command through a door (whole: the line is one command, so a value may hold ; and newlines). -> text."""
    body = json.dumps({"session": session, "as": who, "line": line, "whole": True}).encode()
    req = urllib.request.Request(f"{base}/api/do", body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.loads(r.read())
    return (("ERR " + out["error"] + "\n") if out.get("error") else "") + (out.get("text") or "")


def q(s):
    """A desk value in double quotes: backslash, quote and dollar escaped; a newline written \\n (the desk makes it one)."""
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


# ---- the window and its input ---------------------------------------------------------------------------------------

class Window:
    """The home base page, in the sandbox (a real Edge window on a hidden desktop) or headless Chrome. Input goes to it
    alone: Windows messages to the sandbox window, or DevTools events headless."""

    def __init__(self, headless):
        self.headless, self.SB, self.guard, self.br, self.name, self.ws = headless, None, None, None, None, None
        self.prof = None

    async def open(self, url):
        w, h = SIZE
        self.prof = agora_tmp.directory("playtest-profile-")
        if self.headless:
            exe = next((b for b in screen.BROWSERS if Path(b).exists()), None)
            port = screen.free_port()
            self.br = subprocess.Popen([exe, f"--remote-debugging-port={port}", f"--user-data-dir={self.prof}", "--no-first-run",
                                        "--no-default-browser-check", "--disable-extensions", f"--window-size={w},{h}",
                                        "--headless=new", "--hide-scrollbars", "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            import sandbox_window as SB
            self.SB, self.name = SB, f"playtest-{os.getpid()}"
            self.guard = SB.Guard(self.name, f"agora-sandbox-{self.name}")
            self.guard.__enter__()
            # opened on the page itself, as an app window (opened on about:blank and sent on, it grew a tab strip and
            # an address bar); the page is loaded again below, once the timer is in it from its first line
            port = SB.open_edge(self.name, url, f"{w}x{h}")["port"]
        screen.wait_http(f"http://127.0.0.1:{port}/json/version")
        tabs = json.loads(screen.wait_http(f"http://127.0.0.1:{port}/json"))
        self.ws = await websockets.connect(next(t["webSocketDebuggerUrl"] for t in tabs if t.get("type") == "page"), origin=None, max_size=64 * 1024 * 1024)
        self.p = screen.Page(self.ws)
        if self.SB:
            self.SB.join(self.name)
            self.win = self.SB.main_window(self.name)
        await self.p.call("Page.enable")
        if self.headless:
            await self.p.call("Emulation.setDeviceMetricsOverride", width=w, height=h, deviceScaleFactor=SCALE, mobile=False)
        await self.p.call("Page.addScriptToEvaluateOnNewDocument", source=PT_JS)
        await self.p.call("Page.addScriptToEvaluateOnNewDocument",
                          source="addEventListener('DOMContentLoaded', () => { const s = document.createElement('style'); s.id = 'hud-frost'; "
                                 f"s.textContent = {json.dumps(DUSK)}; document.head.append(s); }});")
        await self.p.call("Page.navigate", url=url)

    async def js(self, expr):
        return await self.p.js(expr)

    async def origin(self):
        return self.SB.page_origin(self.win, inner=await self.js("[innerWidth, innerHeight, devicePixelRatio]"))

    def _descend(self, cx, cy):
        """The window under client pixel cx, cy (as sandbox_window.click_at finds it) and the point in its own pixels."""
        SB, u32, wt = self.SB, self.SB.u32, self.SB.wt
        target, pt = self.win, wt.POINT(int(cx), int(cy))
        while True:
            c = u32.ChildWindowFromPointEx(target, pt, 1)
            if not c or c == target or SB.cls_of(c) in ("Intermediate D3D Window", "Chrome_RenderWidgetHostHWND"):
                break
            u32.MapWindowPoints(target, c, ctypes_byref(pt), 1)
            target = c
        return target, pt.x - int(cx), pt.y - int(cy)

    async def click(self, x, y, right=False):
        if self.SB:
            ox, oy, dpr = await self.origin()
            self.SB.click_at(self.win, ox + x * dpr, oy + y * dpr, right)
        else:
            await self.p.press(x, y, "right" if right else "left")

    async def dblclick(self, x, y):
        if self.SB:
            SB = self.SB
            ox, oy, dpr = await self.origin()
            cx, cy = ox + x * dpr, oy + y * dpr
            t, dx, dy = self._descend(cx, cy)
            at = SB.xy(cx + dx, cy + dy)
            SB.post(t, SB.WM_MOUSEMOVE, 0, at)
            for msg, wp in ((SB.WM_LBUTTONDOWN, 1), (SB.WM_LBUTTONUP, 0), (0x203, 1), (SB.WM_LBUTTONUP, 0)):   # 0x203 WM_LBUTTONDBLCLK
                SB.post(t, msg, wp, at)
                time.sleep(0.04)
        else:
            for n in (1, 2):
                await self.p.mouse("mousePressed", x, y, "left", 1, n)
                await self.p.mouse("mouseReleased", x, y, "left", 0, n)

    async def drag(self, x0, y0, x1, y1, steps=12, devtools=False):
        """devtools: the drag as DevTools mouse events (Chromium's own input path) even in the sandbox: posted window
        messages move pointers (a carry works) but select no text (ran 16 Oct, a control drag over the chat's words)."""
        if self.SB and not devtools:
            SB = self.SB
            ox, oy, dpr = await self.origin()
            a, b = (ox + x0 * dpr, oy + y0 * dpr), (ox + x1 * dpr, oy + y1 * dpr)
            t, dx, dy = self._descend(*a)
            SB.post(t, SB.WM_MOUSEMOVE, 0, SB.xy(a[0] + dx, a[1] + dy))
            time.sleep(0.03)
            SB.post(t, SB.WM_LBUTTONDOWN, 1, SB.xy(a[0] + dx, a[1] + dy))
            for k in range(1, steps + 1):
                time.sleep(0.03)
                SB.post(t, SB.WM_MOUSEMOVE, 1, SB.xy(a[0] + (b[0] - a[0]) * k / steps + dx, a[1] + (b[1] - a[1]) * k / steps + dy))
            time.sleep(0.05)
            SB.post(t, SB.WM_LBUTTONUP, 0, SB.xy(b[0] + dx, b[1] + dy))
        else:
            await self.p.mouse("mouseMoved", x0, y0, "none", 0)
            await self.p.mouse("mousePressed", x0, y0, "left", 1)
            for k in range(1, steps + 1):
                await self.p.mouse("mouseMoved", x0 + (x1 - x0) * k / steps, y0 + (y1 - y0) * k / steps, "left", 1)
                await asyncio.sleep(0.03)
            await self.p.mouse("mouseReleased", x1, y1, "left", 0)

    async def type(self, text):
        if self.SB:
            self.SB.type_text(self.SB.focused(self.win), text)
        else:
            await self.p.call("Input.insertText", text=text)

    async def wheel(self, x, y, dy):
        """Real wheel input, never a scrollTop assignment or scrollIntoView."""
        if self.SB:
            ox, oy, dpr = await self.origin()
            self.SB.wheel_at(self.win, ox + x * dpr, oy + y * dpr, dy)
        else:
            await self.p.call("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y)
            await self.p.call("Input.dispatchMouseEvent", type="mouseWheel", x=x, y=y, deltaX=0, deltaY=dy)

    async def key(self, k):
        if self.SB and "+" not in k[1:] and (k in self.SB.VK or len(k) == 1):
            self.SB.press_key(self.SB.focused(self.win), k)
            return
        mods = 0
        while "+" in k[1:]:
            m, k = k.split("+", 1)
            mods |= {"alt": 1, "ctrl": 2, "meta": 4, "shift": 8}[m.lower()]
        code, text = screen.KEYS.get(k, (ord(k.upper()) if len(k) == 1 else 0, k if len(k) == 1 else ""))
        base = dict(key=k, windowsVirtualKeyCode=code, code=k, modifiers=mods)
        await self.p.call("Input.dispatchKeyEvent", type="keyDown", text="" if mods & 7 else text, **base)
        await self.p.call("Input.dispatchKeyEvent", type="keyUp", **base)

    async def shot(self, path):
        from io import BytesIO
        import base64
        from PIL import Image
        if self.SB:
            im = self.SB.print_window(self.win)
        else:
            im = Image.open(BytesIO(base64.b64decode((await self.p.call("Page.captureScreenshot", format="png"))["data"])))
        im = im.convert("RGB")
        im.thumbnail((1920, 1920))
        im.save(path)
        return path

    async def close(self):
        if getattr(self, "said", None):          # closed already: the same verdict again
            return self.said
        self.said = await self._close()
        return self.said

    async def _close(self):
        if self.ws:
            try:
                await self.ws.close()
            except Exception:
                pass
        if self.br:
            self.br.terminate()
            try:
                self.br.wait(timeout=10)
            except Exception:
                self.br.kill()
        verdict = (0, "headless: no window was made, nothing could reach Alex's screen")
        if self.SB:
            self.SB.close(self.name, quiet=True)
            self.guard.__exit__(None, None, None)
            verdict = self.guard.verdict()
        if self.prof:
            shutil.rmtree(self.prof, ignore_errors=True)
        return verdict


def ctypes_byref(x):
    import ctypes
    return ctypes.byref(x)


# ---- a step --------------------------------------------------------------------------------------------------------

class Skip(Exception):
    pass


class Missing(Exception):
    pass


class Play:
    def __init__(self, win, copy, out, assume):
        self.w, self.copy, self.out, self.assume, self.results, self.n = win, copy, out, set(assume), [], 0
        self.landed = {}

    def needs(self, card, what, probe=None):
        """A step for a commission: skipped until the card says landed in the world played (or --assume names it), and,
        with probe=(lens, words), until that lens holds those words: the code can land before its world half is applied."""
        if card in self.assume:
            return
        self._landed(card, what)
        if probe:
            lens, words = probe
            if words not in self.copy.do(f"read {lens}", "hud-playtest"):
                raise Skip(f"{card} ({what}) has landed, but its world half is not in this world: {lens} has no '{words}'")

    def _landed(self, card, what):
        if card not in self.landed:
            import re
            t = self.copy.do(f"look {card}", "hud-playtest").split("\n")
            t = next((x for x in t if x.lstrip().startswith(card + " ")), "")
            # landed, or re-asked after it landed (the house writes landed=<commit> on the card)
            self.landed[card] = "commission=landed" in t or bool(re.search(r"\blanded=[0-9a-f]{6,}", t))
        if not self.landed[card]:
            raise Skip(f"waits on {card} ({what}), not landed yet")

    async def find(self, expr, what, reachable=True):
        """The centre of the part a JS expression names (pt.* helpers); one that is not there is a failure, and so is
        one a person cannot press: painted, but cut off by a panel that never scrolls or covered by something (the
        element at its centre is not it). Ran 16 Oct: an item's demo pushed its Seen / Done below its panel's cut."""
        c = await self.w.js(f"""(() => {{ const pt = window.__pt, e = {expr}; const c = pt.center(e); if (!c) return null;
            const at = document.elementFromPoint(c[0], c[1]);
            return {{ c, hit: !!at && (e.contains(at) || at.contains(e)), at: at ? ((at.dataset && at.dataset.key) || at.tagName).split('/').slice(-2).join('/') : 'nothing' }}; }})()""")
        if not c:
            raise AssertionError(f"could not find {what}")
        if reachable and not c["hit"]:
            raise AssertionError(f"{what} is painted but cut off or covered: a press at its centre lands on {c['at']} (a person cannot press it)")
        return c["c"]

    async def has(self, expr):
        return await self.w.js(f"(() => {{ const pt = window.__pt; return !!({expr}); }})()")

    async def timed(self, pred, act, timeout=4000, scripted=False):
        """Arm the result, do the input, wait for the result's frame. -> the timings (ms from the input event).
        scripted: the cause is not an input of his (a line someone else says): timed from just before it."""
        already = await self.w.js(f"window.__pt.arm({json.dumps(pred)})")
        if already:
            raise AssertionError("the result was showing before the input (the step cannot tell)")
        if scripted:
            await self.w.js("(() => { window.__pt.last = performance.now(); window.__pt.lastType = 'script'; })()")
        await act()
        r = await self.w.js(f"window.__pt.wait({timeout})")
        r["ms"] = round(r["done"] - r["input"]) if r["ok"] and r["input"] else None
        r["first_ms"] = round(r["first"] - r["input"]) if r["first"] and r["input"] and r["first"] >= r["input"] else None
        return r

    async def step(self, sid, name, fn, budget=(OK_MS, SLOW_MS)):
        self.n += 1
        res = {"id": sid, "name": name, "outcome": "pass", "ms": None, "first_ms": None, "note": "", "shot": "", "via": "", "budget": list(budget)}
        t0 = time.time()
        try:
            r = await fn()
            r = r or {}
            res["ms"], res["first_ms"] = r.get("ms"), r.get("first_ms")
            res["note"] = r.get("note", "")
            res["via"] = ", ".join(f"{k} {d} ms at +{s}" for k, s, d in (r.get("reqs") or []))
            if r.get("ok") is False:
                res["outcome"] = "fail"
                res["note"] = (r.get("want", "the result did not show") + f" within {r.get('timeout', 4000) // 1000} s"
                               + (f"; first change at {r['first_ms']} ms" if r.get("first_ms") is not None else "; nothing on the page changed")
                               + ("" if r.get("sawInput") else "; the page saw no input event")
                               + (f"; status: {r['status']}" if r.get("status") else "")).strip()
            elif res["ms"] is not None and res["ms"] > budget[1]:
                res["outcome"] = "slow"
            elif res["ms"] is not None and res["ms"] > budget[0]:
                res["note"] = (res["note"] + f"; over the {budget[0]} ms aim").lstrip("; ")
        except Skip as e:
            res["outcome"], res["note"] = "skip", str(e)
        except Missing as e:
            res["outcome"], res["note"] = "missing", str(e)
        except AssertionError as e:
            res["outcome"], res["note"] = "fail", str(e)
        except Exception as e:                       # the script's own trouble is a failure too, named
            res["outcome"], res["note"] = "fail", f"{type(e).__name__}: {e}"
        if res["outcome"] != "skip" and res["note"] != "not in --only":
            try:
                res["shot"] = str(await self.w.shot(self.out / f"{self.n:02d}-{sid}.png"))
            except Exception as e:
                res["note"] += f" (no shot: {e})"
        res["secs"] = round(time.time() - t0, 1)
        self.results.append(res)
        ms = f"{res['ms']} ms" if res["ms"] is not None else "-"
        print(f"  {res['outcome']:<7} {sid:<9} {ms:>8}  {name}" + (f"  ({res['note']})" if res["note"] else "")
              + (f"  [{res['via']}]" if res["via"] else ""), flush=True)
        return res


def press(play, expr, what, right=False):
    async def act():
        x, y = await play.find(expr, what)
        await play.w.click(x, y, right)
    return act


# ---- Alex's day ----------------------------------------------------------------------------------------------------
# Finders use the words a person sees, inside the lens that paints them (keys hold `lens:<name>` segments), so a
# restyle or a moved panel does not break a step; a step names what it looked for when it can't find it.

# a6271: the shelf's chips and the dock's icons are one bar of icons now (home-dock: /apps/ and /panels/ groups), each
# found by its tip; a chip or icon with words (the a5500 dock, home-panels) is still found by them
CHIP = ("(() => {{ const s = pt.part('lens:home-panels'); return (s && pt.pressable(pt.leaf({0}, s))) "
        "|| pt.tipped({0}, pt.part('lens:home-dock'), '/panels/'); }})()")
PANEL = "(() => {{ const t = [...document.querySelectorAll('#paint [data-key$=\"/grip/title\"]')].find(e => pt.vis(e) && e.textContent.trim() === {0}); return t ? t.parentElement.parentElement : null; }})()"
DOCK = ("(() => {{ const d = pt.part('lens:home-dock'); return (d && pt.pressable(pt.leaf({0}, d))) "
        "|| pt.tipped({0}, d, '/apps/'); }})()")


def panel(title):
    return PANEL.format(json.dumps(title))


async def open_panel(play, title, lens):
    """Bring a panel out of the shelf (its chip in the dock), as Alex would; already out, nothing to do."""
    if await play.has(f"pt.part('lens:{lens}')"):
        return None
    if not await play.has(CHIP.format(json.dumps(title))):
        raise AssertionError(f"no '{title}' panel out and no chip for it on the shelf")
    return await play.timed(f"pt.part('lens:{lens}')", press(play, CHIP.format(json.dumps(title)), f"the '{title}' chip"))


async def walk(play, only):
    w, c = play.w, play.copy
    S = play.step

    def want(sid):
        return not only or sid in only or ("scroll" in only and sid.startswith("scroll"))

    async def skip_unwanted(sid, name):
        async def no():
            raise Skip("not in --only")
        res = await S(sid, name, no)
        res["outcome"] = "not played"

    # every walk waits for the first paint, whichever steps it plays (`open` reports it)
    opened = await w.js("""new Promise(res => { const t0 = performance.now(); const f = () => { const pt = window.__pt;
        if (pt && pt.opened) return res({ ok: true, ms: Math.round(pt.opened), first_ms: null });
        if (performance.now() - t0 > 15000) return res({ ok: false, want: 'the home base tiles and dock' , timeout: 15000});
        setTimeout(f, 20); }; f(); })""")
    await asyncio.sleep(1.2)                     # its first scenes settle (reports, fonts)

    from playtest_steps import discover
    for step in discover():
        if want(step.name):
            await S(step.name, step.description, step.script(play, opened), step.budget)
        else:
            await skip_unwanted(step.name, step.description)


# ---- the report ----------------------------------------------------------------------------------------------------

def summarize(results):
    n = {k: sum(r["outcome"] == k for r in results) for k in ("pass", "slow", "fail", "skip", "missing")}
    clicks = sorted(r["ms"] for r in results if r["ms"] is not None and r["id"] not in ("open",))
    med = clicks[len(clicks) // 2] if clicks else None
    played = n["pass"] + n["slow"] + n["fail"]
    bad = [r["id"] for r in results if r["outcome"] == "fail"]
    slow = [r["id"] for r in results if r["outcome"] == "slow"]
    verdict = (f"{n['pass']} of {played} played steps pass" + (f", {n['slow']} slow ({', '.join(slow)})" if slow else "")
               + (f", {n['fail']} fail ({', '.join(bad)})" if bad else "") + f"; {n['skip']} wait on landings"
               + (f", {n['missing']} missing" if n["missing"] else "") + (f"; median press {med} ms" if med is not None else ""))
    return n, med, verdict


def report_md(results, meta, previous):
    n, med, verdict = summarize(results)
    L = [f"# HUD playtest, {meta['when']}", "",
         f"**Verdict: {verdict}.**", "",
         f"Played on a copy of {meta['world']} at e{meta['at']}, as alex, in {meta['window']}; painter of {meta['code']}. "
         f"Times are from the input event to the first frame that paints the result (first change in brackets); "
         f"aim {OK_MS} ms, slow over {SLOW_MS} ms. The guard: {meta['guard']}", "",
         "| # | step | result | painted | first change | the desk's requests in it | note |", "|---|---|---|---|---|---|---|"]
    for i, r in enumerate(results, 1):
        ms = f"{r['ms']} ms" if r["ms"] is not None else ""
        fm = f"{r['first_ms']} ms" if r["first_ms"] is not None else ""
        L.append(f"| {i} | {r['name']} (`{r['id']}`) | {r['outcome'].upper() if r['outcome'] in ('fail', 'slow') else r['outcome']} | {ms} | {fm} | {r.get('via', '')} | {r['note'].replace('|', '/')} |")
    fails = [r for r in results if r["outcome"] in ("fail", "slow")]
    if fails:
        L += ["", "## What failed or was slow"]
        for r in fails:
            L.append(f"- `{r['id']}` {r['name']}: {r['note'] or (str(r['ms']) + ' ms')}. Shot: {r['shot']}")
    L += ["", f"Every step's shot: {meta['out']}. Run it again: `python research/window-lab/hud_playtest.py` "
          "(or re-ask the playtest card a6040). `--assume <card>` plays the steps of a commission before it lands."]
    if previous:
        L += ["", "## Earlier runs"] + [f"- {p}" for p in previous[:12]]
    return "\n".join(L), verdict


def write_live(md, verdict, results, meta, by, base=LIVE, session="frontier"):
    """The report note in JEFF's corner, rewritten; a notice to Alex when a step that passed last time fails now.
    base/session: the live door by default; --report copy writes into the copy instead (a test of this path)."""
    def door(b, s, who, line):                      # noqa: F811  (this report's world, whichever it is)
        return globals()["door"](base, session, who, line)
    found = door(LIVE, "frontier", by, "find role=hud-playtest")
    import re
    m = re.search(r"\b(a\d+) note \"HUD playtest\"", found)
    passed_now = [r["id"] for r in results if r["outcome"] in ("pass", "slow")]
    failed_now = [r["id"] for r in results if r["outcome"] == "fail"]
    props = f"verdict={q(verdict)} passed={q(','.join(passed_now))} failed={q(','.join(failed_now))} world_at={q('e' + str(meta['at']))} ran={q(meta['iso'])}"
    if not m:
        door(LIVE, "frontier", by, "look \"JEFF's corner\"")          # the desk refuses a create in what you have not seen
        out = door(LIVE, "frontier", by, f"do create \"JEFF's corner\" kind=note title=\"HUD playtest\" role=hud-playtest text={q(md)}")
        nid = re.search(r"created (a\d+)", out) or re.search(r"\bok create\b.*?\b(a\d+)\b", out)
        nid = nid.group(1) if nid else None
        if not nid:
            return f"could not make the report note: {out[:300]}"
        door(LIVE, "frontier", by, f"look {nid}")
        door(LIVE, "frontier", by, f"do prop {nid} {props}")
        return f"made the report note {nid} in JEFF's corner"
    nid = m.group(1)
    old = door(LIVE, "frontier", by, f"read {nid}")
    was = re.search(r"\bpassed=(\"[^\"]*\"|\S*)", old)
    was = (was.group(1).strip('"').split(",") if was else [])
    newly = [s for s in failed_now if s in was]
    out1 = door(LIVE, "frontier", by, f"do rewrite {nid} text={q(md)}")
    door(LIVE, "frontier", by, f"look {nid}")
    out2 = door(LIVE, "frontier", by, f"do prop {nid} {props}")
    said = f"rewrote the report note {nid}" + ("" if "ERR" not in out1 + out2 else f" (refused: {(out1 + out2)[:300]})")
    if newly:
        names = ", ".join(r["name"] for r in results if r["id"] in newly)
        door(LIVE, "frontier", by, "look \"Alex's notices\"")
        out = door(LIVE, "frontier", by, "do create \"Alex's notices\" kind=note title=\"HUD playtest failed\" role=notice to=alex "
                                         f"topic=playtest about={nid} came={q(meta['iso'])} text={q('Passed last time, failed now: ' + names + '. ' + verdict)}")
        said += f"; a 'HUD playtest failed' notice for Alex ({', '.join(newly)})" + ("" if "ERR" not in out else f" REFUSED: {out[:200]}")
    return said


def previous_runs(by):
    """The verdict lines kept at the foot of the live note, and its last verdict, newest first."""
    try:
        found = door(LIVE, "frontier", by, "find role=hud-playtest")
    except Exception:
        return []
    import re
    m = re.search(r"\b(a\d+) note \"HUD playtest\"", found)
    if not m:
        return []
    t = door(LIVE, "frontier", by, f"read {m.group(1)}")
    head = re.search(r"# HUD playtest, (.+)", t)
    v = re.search(r"\*\*Verdict: (.+?)\.\*\*", t)
    at = re.search(r"copy of \S+ at (e\d+)", t)
    earlier = re.findall(r"^- (\d{1,2} \w+ \d\d:\d\d.*)$", t.split("## Earlier runs", 1)[1], re.M) if "## Earlier runs" in t else []
    first = [f"{head.group(1)} ({at.group(1) if at else '?'}): {v.group(1)}"] if head and v else []
    return first + earlier


def apply_file(copy, path, who):
    """One file of a world half, into the copy: .desk is one command a line (# skipped); .lens and .verb are notes in
    Home base (f5204) named for the file, rewritten when there, else made, as home-layout/put.py writes them."""
    import re

    def ok(said):
        return not ((said.startswith("ERR") or "refused" in said[:200]) and "nothing to change" not in said[:300])
    if path.suffix in (".lens", ".verb"):
        name, text = path.stem, path.read_text(encoding="utf-8").rstrip("\n")
        kind = path.suffix[1:]
        found = copy.do(f"find title:{name},tag:{kind},in:f5204", who)
        hit = re.findall(rf"^\s*(a\d+) note \"{re.escape(name)}\"", found, re.M)
        if hit:
            copy.do(f"read {hit[0]}", who)
            said = copy.do(f"do rewrite {hit[0]} text={q(text)}", who)
        else:
            copy.do("look f5204", who)
            more = "style=home-style" if kind == "lens" else "on=f5189"
            said = copy.do(f"do create f5204 kind=note title={name} tags={kind} {more} text={q(text)}", who)
        if not ok(said):
            sys.exit(f"--apply {path.name}: refused in the copy\n{said[:400]}")
    else:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.lstrip().startswith("#"):
                said = copy.do(line, who)
                if not ok(said):
                    sys.exit(f"--apply {path.name}: refused in the copy, stopping at: {line[:120]}\n{said[:400]}")
    print(f"applied {path.name} to the copy", flush=True)


def git_code():
    try:
        return subprocess.run(["git", "log", "-1", "--format=%h %s"], cwd=HERE, capture_output=True, text=True, timeout=20).stdout.strip()[:80]
    except Exception:
        return "?"


async def amain(a):
    world = a.world or ("frontier-try" if (LAB / "sessions" / "frontier-try.pickle").exists() else "frontier")
    stamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
    out = screen_tools.demos() / "hud-playtest" / stamp
    out.mkdir(parents=True, exist_ok=True)
    print(f"hud_playtest: a copy of {world}, {'headless' if a.headless else 'a real window on a hidden desktop'}; shots in {out}", flush=True)
    copy = Copy(world)
    win = Window(a.headless)
    guard = (1, "the run stopped before the guard said")
    play = None
    try:
        at = copy.at()
        for f in a.apply:               # a world half not applied live yet, tried on the copy first
            apply_file(copy, Path(f), a.apply_as)
        for b in a.breaks:
            lens, old, new, why = BREAKS[b]
            c1 = copy.do(f"read {lens}", "hud-playtest")
            c2 = copy.do(f"do replace {lens} old={q(old)} new={q(new)}", "hud-playtest")
            if "ok replace" not in c2:      # a break that did not take proves nothing: stop
                sys.exit(f"--break {b}: the copy's {lens} did not take the change (its words have moved on?): {c2[:300]}")
            print(f"broke {lens} in the copy: {why}", flush=True)
        await win.open(copy.url())
        play = Play(win, copy, out, a.assume)
        await walk(play, set(a.only) if a.only else None)
        errors = await win.js("window.__pt.errors")
        guard = await win.close()
        if a.report == "copy":
            # the report path, tried in the copy: an earlier report that says every played step passed, then this
            # run's over it, so each step failing now makes the notice; then what the copy's notices hold
            played = [r["id"] for r in play.results if r["outcome"] in ("pass", "slow", "fail")]
            seed = write_live("# HUD playtest, (seeded by --report copy)\n\n**Verdict: seeded.**", "seeded",
                              [{"id": s, "outcome": "pass", "name": s} for s in played], {"at": at, "iso": "seed"}, a.by, copy.base, copy.session)
            print(f"report copy: seeded an earlier report claiming {len(played)} steps passed ({seed})")
            when = datetime.datetime.now()
            meta0 = {"when": when.strftime("%d %b %H:%M").lstrip("0"), "iso": when.isoformat(timespec="seconds"), "world": world,
                     "at": at, "window": "", "code": git_code(), "guard": guard[1], "out": str(out)}
            md0, verdict0 = report_md(play.results, meta0, [])
            print("report copy: " + write_live(md0, verdict0, play.results, meta0, a.by, copy.base, copy.session))
            print("report copy, the copy's notices now:\n" + copy.do("find prop:role=notice,prop:topic=playtest", a.by)[:800])
            print("report copy, the copy's report note:\n" + copy.do("find role=hud-playtest", a.by)[:600])
    finally:
        guard = await win.close()
        copy.close()
    when = datetime.datetime.now()
    meta = {"when": when.strftime("%d %b %H:%M").lstrip("0"), "iso": when.isoformat(timespec="seconds"), "world": world, "at": at,
            "window": ("headless Chrome" if a.headless else "a real Edge window on a hidden desktop") + f" {SIZE[0]}x{SIZE[1]} at {int(SCALE * 100)} %",
            "code": git_code(), "guard": guard[1], "out": str(out), "breaks": a.breaks}
    if errors:
        meta["guard"] += f" Page errors: {'; '.join(errors[:3])}"
    prev = previous_runs(a.by) if a.report == "live" else []
    md, verdict = report_md(play.results, meta, prev)
    if a.breaks:
        md = md.replace("# HUD playtest,", f"# HUD playtest (lens broken on purpose: {', '.join(a.breaks)}),", 1)
    (out / "report.md").write_text(md, encoding="utf-8")
    (out / "report.json").write_text(json.dumps({"meta": meta, "results": play.results}, indent=1), encoding="utf-8")
    print("\n" + md + "\n")
    print(f"guard: {guard[1]}")
    if a.report == "live" and not (a.breaks or a.only or a.apply or a.assume):
        print(write_live(md, verdict, play.results, meta, a.by))
    elif a.report == "live":
        print("not written to the live world: a run with --break, --only, --apply or --assume is a check, not the standing report")
    return 1 if guard[0] or any(r["outcome"] == "fail" for r in play.results) else 0


def main():
    import argparse
    ap = argparse.ArgumentParser(description="the home base played as Alex plays it, timed (see the top of this file)")
    ap.add_argument("--world")
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--report", choices=["live", "none", "copy"], default=None)
    ap.add_argument("--by", default="hud-playtest")
    ap.add_argument("--only", type=lambda s: s.split(","), default=None)
    ap.add_argument("--assume", type=lambda s: s.split(","), default=[])
    ap.add_argument("--break", dest="breaks", type=lambda s: s.split(","), default=[])
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--apply", type=lambda s: s.split(","), default=[],
                    help="files applied to the copy first: .desk lines, .lens / .verb notes in Home base (as put.py does)")
    ap.add_argument("--apply-as", default="alex")
    ap.add_argument("--profile-scenes", default=None,
                    help="a6153: a folder; the copy's deskd profiles each scene build into it (press-speed/read_profiles.py)")
    a = ap.parse_args()
    if a.profile_scenes:
        os.environ["DESKD_PROFILE_SCENES"] = str(Path(a.profile_scenes).resolve())     # the door's deskd inherits it
    if a.list:
        from playtest_steps import discover
        for step in discover():
            needs = ", ".join(n[0] + ": " + n[1] for n in step.needs) or "none"
            print(f"{step.name}: {step.description} [{step.budget[0]}/{step.budget[1]} ms; needs {needs}]")
        return 0
    for b in a.breaks:
        if b not in BREAKS:
            sys.exit(f"--break: one of {', '.join(BREAKS)}")
    if a.report is None:
        try:
            urllib.request.urlopen(f"{LIVE}/lens.html", timeout=3)
            a.report = "live"
        except Exception:
            a.report = "none"
    return asyncio.run(amain(a))


if __name__ == "__main__":
    sys.exit(main())
