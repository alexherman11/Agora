"""hud_playtest.py: the home base played as Alex plays it, every step timed, on a copy of the world (a6040, 16 Oct).
OWNER: worker-a6040. Alex, 16 Oct 15:07: 'the process needs much more playtesting.'

    python research/window-lab/hud_playtest.py                    play it; the report goes to the live world
    python research/window-lab/hud_playtest.py --report none      play it; print the report only
    python research/window-lab/hud_playtest.py --only board,chat  some steps (ids below), the rest skipped
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

Steps (ids for --only): open lowdown board card later approve sendback atwork writing writedoc comment chat send
drag fill widen restore glance dock esc winkey.
"""
import asyncio
import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

import websockets

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1] / "research" / "text-desk-lab" / "notation"
sys.path.insert(0, str(LAB))
sys.path.insert(0, str(HERE))
import screen        # noqa: E402  (the browser list, Page, free_port, wait_http)
import screen_tools  # noqa: E402  (demos/, DPI awareness)
import witnessed     # noqa: E402

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
  for (const t of ['mouseup', 'pointerup', 'click', 'dblclick', 'keydown', 'contextmenu'])
    addEventListener(t, e => { pt.last = e.timeStamp || performance.now(); pt.lastType = t; pt.first = 0; }, true);
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
        self.state = tempfile.mkdtemp(prefix="playtest-door-")
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
        self.prof = tempfile.mkdtemp(prefix="playtest-profile-")
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
        self.ws = await websockets.connect(next(t["webSocketDebuggerUrl"] for t in tabs if t.get("type") == "page"), max_size=64 * 1024 * 1024)
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

CHIP = "pt.pressable(pt.leaf({0}, pt.part('lens:home-panels')))"
PANEL = "(() => {{ const t = [...document.querySelectorAll('#paint [data-key$=\"/grip/title\"]')].find(e => pt.vis(e) && e.textContent.trim() === {0}); return t ? t.parentElement.parentElement : null; }})()"
DOCK = "pt.pressable(pt.leaf({0}, pt.part('lens:home-dock')))"


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
        return not only or sid in only

    async def skip_unwanted(sid, name):
        async def no():
            raise Skip("not in --only")
        res = await S(sid, name, no)
        res["outcome"] = "not played"

    steps = []
    # every walk waits for the first paint, whichever steps it plays (`open` reports it)
    opened = await w.js("""new Promise(res => { const t0 = performance.now(); const f = () => { const pt = window.__pt;
        if (pt && pt.opened) return res({ ok: true, ms: Math.round(pt.opened), first_ms: null });
        if (performance.now() - t0 > 15000) return res({ ok: false, want: 'the home base tiles and dock' , timeout: 15000});
        setTimeout(f, 20); }; f(); })""")
    await asyncio.sleep(1.2)                     # its first scenes settle (reports, fonts)

    async def s_open():
        r = dict(opened)
        if r.get("ok"):
            r["note"] = "a cold load of the page (from navigation); the hotkey shows an already loaded page"
        return r
    steps.append(("open", "open the home base: tiles and dock painted", s_open, (1000, 3000)))

    async def s_lowdown():
        r = await open_panel(play, "The lowdown", "home-lowdown")
        prose = await w.js("(() => { const pt = window.__pt, l = pt.part('lens:home-lowdown'); if (!l) return null;"
                           " const t = [...l.querySelectorAll('[data-key]')].filter(e => pt.vis(e) && !e.querySelector('[data-key]')).map(e => e.textContent.trim()).join(' ');"
                           " const cut = !!l.closest('[data-cut]') || [...l.querySelectorAll('*')].some(e => e.dataset && e.dataset.cut);"
                           " const r = l.getBoundingClientRect(); return { words: t.split(/\\s+/).length, cut, h: Math.round(r.height) }; })()")
        if not prose or prose["words"] < 12:
            raise AssertionError(f"the lowdown shows almost nothing ({prose})")
        r = r or {"note": "already out"}
        r["note"] = (r.get("note", "") + f"; {prose['words']} words shown in {prose['h']} px" + ("; CUT: some of it is hidden" if prose["cut"] else "")).lstrip("; ")
        return r
    steps.append(("lowdown", "read the lowdown (its chip on the shelf)", s_lowdown, (OK_MS, SLOW_MS)))

    async def s_board():
        play.needs_board = True
        r = await open_panel(play, "The board", "home-board")
        lanes = await w.js("window.__pt.parts('lens:home-board').filter(e => /\\/head\\/name$/.test(e.dataset.key)).map(e => e.textContent.trim())")
        if not lanes:
            raise AssertionError("the board shows no lanes")
        r = r or {"note": "already out"}
        r["note"] = (r.get("note", "") + "; lanes: " + ", ".join(lanes)).lstrip("; ")
        return r
    steps.append(("board", "see the board (its chip on the shelf)", s_board, (OK_MS, SLOW_MS)))

    async def s_card():
        k = await w.js("(() => { const pt = window.__pt; const c = pt.parts('lens:home-board').find(e => e.dataset.foldInline && e.dataset.folded === '1');"
                       " return c ? c.dataset.key : null; })()")
        if not k:
            raise AssertionError("no folded card on the board to open")
        kk = json.dumps(k)
        line = f"[...pt.key({kk}).children].find(e => e.dataset && e.dataset.peek)"
        r = await play.timed(f"pt.key({kk}) && pt.key({kk}).dataset.folded !== '1'", press(play, line, "the card's line"))
        if not r["ok"]:
            r["want"] = "the card did not open"
            return r
        await asyncio.sleep(0.4)
        await w.shot(play.out / f"{play.n + 1:02d}-card-open.png")
        r2 = await play.timed(f"pt.key({kk}) && pt.key({kk}).dataset.folded === '1'", press(play, line, "the open card's line"))
        if not r2["ok"]:
            r2["want"] = "the card opened but a second press did not close it"
            return r2
        r["note"] = f"opened in {r['ms']} ms, closed in {r2['ms']} ms (card {k.rsplit('/', 1)[-1]})"
        r["ms"] = max(r["ms"], r2["ms"])
        return r
    steps.append(("card", "click a card to expand it, and again to close it", s_card, (OK_MS, SLOW_MS)))

    WAIT_ITEMS = "window.__pt.parts('lens:waiting-on-me').filter(e => /\\/now\\/[a-z]\\d+\\/head$/.test(e.dataset.key) || /\\/designs\\/[a-z]\\d+\\/head$/.test(e.dataset.key))"

    async def answer(button, want_gone_from_now, label):
        r0 = await open_panel(play, "Waiting on you", "waiting-on-me")
        heads = await w.js(f"{WAIT_ITEMS}.map(e => e.dataset.key)")
        heads = [h for h in heads if "/now/" in h]
        if not heads:
            raise AssertionError("nothing waits on Alex in the list (nothing to answer)")
        head = heads[0]
        item = head.split("/")[-2]
        hk = json.dumps(head)
        r1 = await play.timed(f"pt.leaf({json.dumps(button)}, pt.key({hk}).parentElement)", press(play, f"pt.key({hk})", "the item"))
        if not r1["ok"]:
            r1["want"] = f"a press on the item did not open it to show {button}"
            return r1
        gone = f"!pt.parts('lens:waiting-on-me').some(e => /\\/now\\/{item}\\/head$/.test(e.dataset.key))"
        later = f"pt.parts('lens:waiting-on-me').some(e => /\\/later\\/{item}\\/head$/.test(e.dataset.key))"
        pred = gone + (f" && {later}" if button == "Later" else "")
        r = await play.timed(pred, press(play, f"pt.pressable(pt.leaf({json.dumps(button)}, pt.key({hk}).parentElement))", f"'{button}'"))
        if not r["ok"]:
            r["want"] = f"'{button}' did not take {item} off the list" + (" and below LATER" if button == "Later" else "")
            return r
        r["note"] = f"{item}: opened in {r1['ms']} ms, {label} in {r['ms']} ms"
        return r

    steps.append(("later", "answer a waiting item: Later, and see it go below", lambda: answer("Later", True, "moved below LATER"), (OK_MS, SLOW_MS)))
    steps.append(("approve", "answer a waiting item: Seen / Done, and see it leave", lambda: answer("Seen / Done", True, "left the list"), (OK_MS, SLOW_MS)))

    async def s_sendback():
        await open_panel(play, "Waiting on you", "waiting-on-me")
        lens = c.do("read waiting-on-me", "hud-playtest")
        if "send back" not in lens.lower():
            raise Missing("no Send back on a waiting item (waiting-on-me has Seen / Done, Later, Open fully, Open here); no commission named for it")
        return await answer("Send back", True, "sent back")
    steps.append(("sendback", "answer a waiting item: Send back", s_sendback, (OK_MS, SLOW_MS)))

    async def s_atwork():
        await open_panel(play, "At work", "home-work")
        row = "window.__pt.parts('lens:home-work').find(e => /\\/busy\\/[^/]+$/.test(e.dataset.key))"
        if not await play.has(row):
            raise AssertionError("no At-work rows (the copy's house is staged busy)")
        live = await play.has(f"pt.pressable({row})")
        try:
            play.needs("a5988", "the At-work feed", ("home-work", "home-feed"))
        except Skip as e:
            raise Skip(str(e) + ("" if live else "; a press on a row does nothing today (the row has no click)"))
        who = await w.js(f"(() => {{ const pt = window.__pt, r = {row}; return r ? r.innerText.split('\\n')[0].trim() : ''; }})()")
        r = await play.timed("!!pt.part('lens:home-feed')", press(play, row, "an At-work row"))
        if not r["ok"]:
            r["want"] = f"a press on {who!r} in At work opened no feed"
            return r
        lines = await w.js("window.__pt.parts('lens:home-feed').filter(e => /\\/(follow|followone|held|heldone)\\/[^/]+$/.test(e.dataset.key)).length")
        empty = await play.has("pt.leaf('No feed yet…', pt.part('lens:home-feed'))")
        r["note"] = (f"{who}'s feed opened in the viewer; " + (f"{lines} lines" if lines else
                     "it says 'No feed yet' (a copy has no house to write feeds: the lines themselves are not played here)" if empty else "no lines"))
        # give the middle back to the chat, as Alex would before the next step
        if await play.has(DOCK.format(json.dumps("JEFF"))):
            await press(play, DOCK.format(json.dumps("JEFF")), "JEFF on the dock")()
            await asyncio.sleep(1.5)
        return r
    steps.append(("atwork", "click an At-work row and watch its feed", s_atwork, (OK_MS, SLOW_MS)))

    async def s_writing():
        await w.js("window.__pt.host.length = 0")
        icon = DOCK.format(json.dumps("Writing room"))
        if not await play.has(icon):
            raise AssertionError("no Writing room on the dock")
        r = await play.timed("pt.host.some(h => h.startsWith('window writing')) || !!pt.part('lens:writing')", press(play, icon, "Writing room on the dock"))
        if not r["ok"]:
            r["want"] = "Writing room asked the home base for nothing and showed no Writing"
            return r
        inside = await play.has("pt.part('lens:writing')")
        r["note"] = "Writing opened inside the home base" if inside else "asked the host `window writing` (a window of its own; the stand-in host records it)"
        return r
    steps.append(("writing", "open Writing from the dock", s_writing, (OK_MS, SLOW_MS)))

    async def s_writeleft():
        play.needs("a5949", "Writing on the left of the chat", ("home-viewer", "split"))
        if not await play.has("pt.part('lens:writing')"):
            raise AssertionError("Writing is not painted in the home base")
        side = await w.js("(() => { const pt = window.__pt, a = pt.rect(pt.part('lens:writing')), b = pt.rect(pt.part('lens:jeff-chat')); return a && b ? a[0] + a[2] <= b[0] + 2 : null; })()")
        if not side:
            raise AssertionError("Writing is not on the left of the chat")
        # how wide the page itself is: a page squeezed to a few words a line is there but not writable
        width = await w.js("(() => { const pt = window.__pt, l = pt.part('lens:writing'), d = l && (l.querySelector('.md-doc') || l.querySelector('[contenteditable]'));"
                           " return d ? Math.round(d.getBoundingClientRect().width) : null; })()")
        note = f"Writing stands left of the chat; its page is {width} px wide"
        if width is not None and width < 360:
            raise AssertionError(note + ": squeezed to a few words a line")
        return {"note": note}
    steps.append(("writedoc", "Writing on the left of the chat", s_writeleft, (OK_MS, SLOW_MS)))

    async def s_comment():
        play.needs("a5949", "highlight-to-comment in Writing", ("home-viewer", "split"))
        doc = "pt.part('lens:writing') && (pt.part('lens:writing').querySelector('.md-doc') || pt.part('lens:writing').querySelector('[contenteditable]'))"
        if not await play.has(doc):
            raise AssertionError("no Writing document painted in the home base")
        await asyncio.sleep(1.5)        # settled: a drag in the page's late repaints would test the repaint, not the drag
        # some words of the page's own, mid-paragraph: their place on the screen, to drag over them as a person would
        span = await w.js(f"""(() => {{ const pt = window.__pt, d = {doc}; const tw = document.createTreeWalker(d, NodeFilter.SHOW_TEXT); let n;
            while ((n = tw.nextNode())) {{ const m = /[A-Za-z]{{3,}} [A-Za-z]{{3,}}/.exec(n.data); if (!m) continue;
              const r = document.createRange(); r.setStart(n, m.index); r.setEnd(n, m.index + m[0].length); const b = r.getBoundingClientRect();
              if (b.width < 30 || b.height > 40 || !pt.vis(n.parentElement)) continue;
              return {{ words: m[0], x0: b.left + 1, x1: b.right - 1, y: b.top + b.height / 2 }}; }} return null; }})()""")
        if not span:
            raise AssertionError("no line of words in the Writing page to select")
        box = "pt.parts('lens:writing').find(e => /\\/pending\\/box$/.test(e.dataset.key))"
        # posted window messages select no text in Chromium (ran 16 Oct, with a control over the chat's words), so the
        # drag goes as DevTools mouse events: a mouse drag down Chromium's own input path, selection and all
        r1 = await play.timed(f"!!({box})", lambda: w.drag(span["x0"], span["y"], span["x1"], span["y"], steps=8, devtools=True))
        how = "a mouse drag over the words (DevTools mouse events)"
        if not r1["ok"]:                      # a person's second try: click into the page first, then drag
            first_sel = await w.js("String(getSelection())")
            await w.click((span["x0"] + span["x1"]) / 2, span["y"])
            await asyncio.sleep(0.8)
            span2 = await w.js(f"""(() => {{ const pt = window.__pt, d = {doc}; const tw = document.createTreeWalker(d, NodeFilter.SHOW_TEXT); let n;
                while ((n = tw.nextNode())) {{ const i = n.data.indexOf({json.dumps(span['words'])}); if (i < 0) continue;
                  const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + {len(span['words'])}); const b = r.getBoundingClientRect();
                  return {{ x0: b.left + 1, x1: b.right - 1, y: b.top + b.height / 2 }}; }} return null; }})()""") or span
            r1 = await play.timed(f"!!({box})", lambda: w.drag(span2["x0"], span2["y"], span2["x1"], span2["y"], steps=8, devtools=True))
            if r1["ok"]:
                how = (f"a mouse drag only after a click into the page (the first drag, on the page untouched, selected "
                       f"{first_sel[:30]!r} and opened no Comment box)")
        if not r1["ok"]:                      # the drag selected nothing the page took up: say so, and select by script
            sel = await w.js("String(getSelection())")
            # a control: the same posted drag over plain words in the chat's feed. If it selects there, the Writing
            # page is what refuses a drag (a person would meet that); if not, it is this script's input
            ctl = await w.js("""(() => { const pt = window.__pt, c = pt.part('lens:jeff-chat'); if (!c) return null;
                const tw = document.createTreeWalker(c, NodeFilter.SHOW_TEXT); let n;
                while ((n = tw.nextNode())) { const m = /[A-Za-z]{3,} [A-Za-z]{3,} [A-Za-z]{3,}/.exec(n.data); if (!m || !pt.vis(n.parentElement)) continue;
                  const r = document.createRange(); r.setStart(n, m.index); r.setEnd(n, m.index + m[0].length); const b = r.getBoundingClientRect();
                  if (b.height > 40 || b.width < 30) continue; return { x0: b.left + 1, x1: b.right - 1, y: b.top + b.height / 2 }; } return null; })()""")
            got = None
            if ctl:
                await w.js("getSelection().removeAllRanges()")
                await w.drag(ctl["x0"], ctl["y"], ctl["x1"], ctl["y"], steps=8, devtools=True)
                await asyncio.sleep(0.4)
                got = await w.js("String(getSelection())")
                await w.js("getSelection().removeAllRanges()")
            how = ("a scripted selection (a drag over the words opened no Comment box; the page's selection after it: "
                   f"{sel[:40]!r}; the same drag over the chat's words selected {got[:40] if got is not None else 'nothing found to try'!r}"
                   + (": so the Writing page refuses a drag-select" if got and not sel else
                      ": so the drag is this script's limit, not the page's" if not got else "") + ")")
            r1 = await play.timed(f"!!({box})", lambda: w.js(
                f"""(() => {{ const d = {doc.replace('pt.', 'window.__pt.')}; const tw = document.createTreeWalker(d, NodeFilter.SHOW_TEXT); let n;
                while ((n = tw.nextNode())) {{ const i = n.data.indexOf({json.dumps(span['words'])}); if (i >= 0) {{
                  getSelection().setBaseAndExtent(n, i, n, i + {len(span['words'])}); document.dispatchEvent(new PointerEvent('pointerup')); return 1; }} }} return 0; }})()"""), scripted=True)
            if not r1["ok"]:
                r1["want"] = "selecting words in Writing opened no Comment box"
                return r1
        x, y = await play.find(box, "the Comment box")
        await w.click(x, y)
        await asyncio.sleep(0.3)
        note = f"playtest note {int(time.time()) % 100000}"
        await w.type(note)
        await asyncio.sleep(0.3)
        r = await play.timed(f"pt.parts('lens:writing').filter(e => !e.querySelector('[data-key]') && e.textContent.includes({json.dumps(note)})).length >= 2",
                             lambda: w.key("Enter"), timeout=6000)
        if not r["ok"]:
            n = await w.js(f"window.__pt.parts('lens:writing').filter(e => !e.querySelector('[data-key]') && e.textContent.includes({json.dumps(note)})).map(e => e.dataset.key.split('/').slice(-3).join('/'))")
            r["want"] = f"the comment did not show both as a margin note and a line in the page's Talk (it shows in: {n or 'nowhere'})"
            r["timeout"] = 6000
            return r
        r["note"] = f"selected {span['words']!r} by {how}; the Comment box in {r1['ms']} ms; margin note and Talk line in {r['ms']} ms"
        return r
    steps.append(("comment", "type in Writing, select words, comment: margin note", s_comment, (OK_MS, SLOW_MS)))

    COMPOSER = "pt.part('lens:jeff-chat') && pt.part('lens:jeff-chat').querySelector('.explicit-composer textarea, textarea')"

    async def s_chat():
        x, y = await play.find(COMPOSER, "the chat composer")
        await w.click(x, y)
        draft = "playtest draft, kept across a repaint"
        await w.type(draft)
        await asyncio.sleep(0.4)
        got = await w.js(f"(() => {{ const pt = window.__pt, t = {COMPOSER}; return t ? t.value : null; }})()")
        if got != draft:
            raise AssertionError(f"typing into the composer gave {got!r}")
        stamp = f"playtest repaint {int(time.time())}"
        said = []

        # the desk holds back a line from someone who has not read the chat's newest lines: he reads it first
        await asyncio.to_thread(c.do, "read a5080", "jeff")

        async def speak():
            said.append(await asyncio.to_thread(c.do, f"do append a5080 line={q('@alex: ' + stamp)}", "jeff"))
        # someone else speaks in the chat (in the copy): the feed repaints under the draft
        r = await play.timed(f"pt.parts('lens:jeff-chat').some(e => !e.querySelector('[data-key]') && e.textContent.includes({json.dumps(stamp)}))",
                             speak, timeout=6000, scripted=True)
        if not r.get("ok"):
            r["status"] = (r.get("status") or "") + f" (the door said to jeff's line: {(said or [''])[0][:200]!r})"
        kept = await w.js(f"(() => {{ const pt = window.__pt, t = {COMPOSER}; return t ? t.value : null; }})()")
        rep, r["ms"], r["first_ms"] = r["ms"], None, None    # no input of his: the repaint's speed is not his press's
        if not r.get("ok"):
            r["want"] = "the other person's line did not paint in the feed"
            r["timeout"] = 6000
            return r
        if kept != draft:
            raise AssertionError(f"the draft was lost in the repaint: the composer holds {kept!r}")
        play.draft = draft
        return {"note": f"a line from jeff (in the copy) painted in the feed {rep} ms after it was sent; the draft stayed whole"}
    steps.append(("chat", "type in the chat composer; the draft survives a repaint", s_chat, (OK_MS, SLOW_MS)))

    async def s_send():
        draft = getattr(play, "draft", None)
        if not draft:
            raise AssertionError("no draft from the step before")
        x, y = await play.find(COMPOSER, "the chat composer")
        await w.click(x, y)
        r = await play.timed(f"(() => {{ const t = {COMPOSER}; return t && t.value === '' && pt.parts('lens:jeff-chat').some(e => !e.querySelector('[data-key]') && e.textContent.includes({json.dumps(draft)})); }})()",
                             lambda: w.key("Enter"))
        if not r["ok"]:
            r["want"] = "Enter did not send the draft into the feed (and empty the composer)"
        else:
            r["note"] = "sent in the copy's Conversation (no one real reads it)"
        return r
    steps.append(("send", "send it with Enter: it shows in the feed", s_send, (OK_MS, SLOW_MS)))

    COLS = "window.__pt.parts('lens:home-tiling').filter(e => /\\/tiling\\/[a-z]\\d+$/.test(e.dataset.key))"

    async def s_drag():
        await open_panel(play, "The board", "home-board")
        cols = await w.js(f"{COLS}.map(e => e.dataset.key)")
        k = await w.js(f"(() => {{ const pt = window.__pt, p = {panel('The board')}; return p ? p.dataset.key : null; }})()")
        if not k or len(cols) < 2:
            raise AssertionError(f"no board panel to drag ({k}) or fewer than two columns ({len(cols)})")
        home = next(c_ for c_ in cols if k.startswith(c_ + "/"))
        there = next(c_ for c_ in cols if c_ != home)
        pid = k.rsplit("/", 1)[-1]
        x0, y0 = await play.find(f"{panel('The board')}.querySelector('[data-carry]') || {panel('The board')}", "the board's title bar")
        # onto the other column's empty foot, or (a full column's foot has no height) onto its first panel's title
        x1, y1 = await play.find(f"pt.key({json.dumps(there + '/foot')}) || pt.parts({json.dumps(there + '/')}).find(e => /\\/grip$/.test(e.dataset.key))",
                                 "the other column's foot or a panel in it")
        r = await play.timed(f"!!pt.key({json.dumps(there + '/' + pid)})", lambda: w.drag(x0, y0, x1, y1))
        play.moved = (pid, home, there)
        if not r["ok"]:
            r["want"] = f"the board did not move from {home.rsplit('/', 1)[-1]} to {there.rsplit('/', 1)[-1]}"
        else:
            r["note"] = f"moved from column {home.rsplit('/', 1)[-1]} to {there.rsplit('/', 1)[-1]}"
        return r
    steps.append(("drag", "drag the board to another column", s_drag, (OK_MS, SLOW_MS)))

    async def s_fill():
        play.needs("a5994", "double-click to fill the space", ("home-tiling", "on double"))
        await open_panel(play, "Music", "home-music")
        p = panel("Music")
        before = await w.js(f"(() => {{ const pt = window.__pt; return pt.rect({p}); }})()")
        title = f"{p}.querySelector('[data-key$=\"/grip/title\"]') || {p}"
        x, y = await play.find(title, "Music's title")
        r = await play.timed(f"(() => {{ const r = pt.rect({p}); return r && r[2] * r[3] > {before[2] * before[3] * 2}; }})()", lambda: w.dblclick(x, y))
        if not r["ok"]:
            r["want"] = "a double-click on Music did not fill the space"
            return r
        x, y = await play.find(title, "Music's title")
        r2 = await play.timed(f"(() => {{ const r = pt.rect({p}); return r && Math.abs(r[2] * r[3] - {before[2] * before[3]}) < {before[2] * before[3] * 0.15}; }})()", lambda: w.dblclick(x, y))
        if not r2["ok"]:
            r2["want"] = "Music filled the space but a second double-click did not restore it"
            return r2
        r["note"] = f"filled in {r['ms']} ms, restored in {r2['ms']} ms"
        r["ms"] = max(r["ms"], r2["ms"])
        return r
    steps.append(("fill", "double-click Music to fill the space, then restore", s_fill, (OK_MS, SLOW_MS)))

    async def s_widen():
        await open_panel(play, "Music", "home-music")
        p = panel("Music")
        if await play.has(f"{p} && pt.leaf('⇔', {p})"):
            return await widen_column(p)
        if not await play.has(f"{p} && pt.leaf('⤢', {p})"):
            raise Missing("neither ⤢ nor ⇔ on Music's title (the tiling changed: update this step)")
        before = await w.js(f"(() => {{ const pt = window.__pt; return pt.rect({p}); }})()")
        r = await play.timed(f"(() => {{ const r = pt.rect({p}); return r && r[2] > {before[2] * 1.3}; }})()", press(play, f"pt.pressable(pt.leaf('⤢', {p}))", "⤢ on Music"))
        if not r["ok"]:
            r["want"] = "⤢ did not widen Music"
            return r
        await asyncio.sleep(0.3)
        await w.shot(play.out / f"{play.n + 1:02d}-widen-wide.png")
        r2 = await play.timed(f"(() => {{ const r = pt.rect({p}); return r && Math.abs(r[2] - {before[2]}) < {before[2] * 0.1}; }})()", press(play, f"pt.pressable(pt.leaf('⤡', {p}))", "⤡ on Music"))
        if not r2["ok"]:
            r2["want"] = "Music widened but ⤡ did not give the room back"
            return r2
        r["note"] = f"widened in {r['ms']} ms, back in {r2['ms']} ms (the tiling of today, a5496)"
        r["ms"] = max(r["ms"], r2["ms"])
        return r
    async def widen_column(p):
        """a5994's tiling: ⇔ steps a column through a third, a half, two thirds of the room and back to its own."""
        before = await w.js(f"(() => {{ const pt = window.__pt; return pt.rect({p}); }})()")
        btn = f"pt.pressable(pt.leaf('⇔', {p}))"
        r = await play.timed(f"(() => {{ const r = pt.rect({p}); return r && r[2] > {before[2] * 1.2}; }})()", press(play, btn, "⇔ on Music"))
        if not r["ok"]:
            r["want"] = "⇔ did not widen Music's column"
            return r
        await asyncio.sleep(0.3)
        await w.shot(play.out / f"{play.n + 1:02d}-widen-wide.png")
        times = [r["ms"]]
        for k in range(3):                      # on round: back to the width it had
            mid = await w.js(f"(() => {{ const pt = window.__pt; return pt.rect({p}); }})()")
            r2 = await play.timed(f"(() => {{ const r = pt.rect({p}); return r && Math.abs(r[2] - {mid[2]}) > 8; }})()", press(play, btn, "⇔ on Music"))
            if not r2["ok"]:
                r2["want"] = f"the press {k + 2} on ⇔ changed nothing"
                return r2
            times.append(r2["ms"])
            if abs((await w.js(f"(() => {{ const pt = window.__pt; return pt.rect({p}); }})()"))[2] - before[2]) < before[2] * 0.08:
                break
        else:
            return {"ok": False, "want": "⇔ never came back round to Music's own width", "sawInput": True}
        r["note"] = f"⇔ pressed {len(times)} times round to its own width: " + ", ".join(f"{t} ms" for t in times) + " (a5994's tiling)"
        r["ms"] = max(times)
        return r
    steps.append(("widen", "widen Music (⤢, or ⇔ in a5994's tiling), then give the room back", s_widen, (OK_MS, SLOW_MS)))

    async def s_restore():
        moved = getattr(play, "moved", None)
        if not moved:
            raise Skip("the board was not moved")
        pid, home, there = moved
        x0, y0 = await play.find(f"{panel('The board')}.querySelector('[data-carry]') || {panel('The board')}", "the board's title bar")
        if await play.has(f"pt.key({json.dumps(home)})"):          # its column is still there: onto it
            x1, y1 = await play.find(f"pt.key({json.dumps(home + '/foot')}) || pt.parts({json.dumps(home + '/')}).find(e => /\\/grip$/.test(e.dataset.key))",
                                     "the board's first column")
            r = await play.timed(f"!!pt.key({json.dumps(home + '/' + pid)})", lambda: w.drag(x0, y0, x1, y1))
            how = "onto its column"
        else:
            # a5994's tiling: a column left empty goes. A drop near a panel's right edge makes a new column there
            other = (f"pt.parts({json.dumps(there + '/')}).find(e => new RegExp('/tiling/[a-z]\\\\d+/[a-z]\\\\d+$').test(e.dataset.key)"
                     f" && !e.dataset.key.endsWith('/{pid}'))")
            rect = await w.js(f"(() => {{ const pt = window.__pt, e = {other}; return e ? pt.rect(e) : null; }})()")
            if not rect:
                raise AssertionError("no other panel in that column to drop beside")
            x1, y1 = rect[0] + rect[2] - 6, rect[1] + rect[3] / 2
            alone = (f"(() => {{ const b = {panel('The board')}, c = b && b.parentElement; return !!c && !c.dataset.key.endsWith({json.dumps(there)})"
                     " && [...c.children].filter(x => x.querySelector(':scope > [data-key$=\"/grip\"]')).length === 1; })()")
            r = await play.timed(alone, lambda: w.drag(x0, y0, x1, y1))
            how = "into a new column of its own (dropped at a panel's right edge: its old column had gone, as a5994's tiling does)"
        if not r["ok"]:
            r["want"] = "the board did not go back to a column of its own"
        else:
            r["note"] = f"back {how}"
        return r
    steps.append(("restore", "drag the board back where it was", s_restore, (OK_MS, SLOW_MS)))

    async def s_glance():
        """What a glance at the whole home base meets, with the panels out: what is cut, squeezed or spills (a count,
        not a judgement: it fails only when a panel shows nothing but its title)."""
        g = await w.js(r"""(() => { const pt = window.__pt, out = { panels: [], cut: [], spill: [], tiny: [] };
          for (const t of document.querySelectorAll('#paint [data-key$="/grip/title"]')) { if (!pt.vis(t)) continue;
            const p = t.parentElement.parentElement, body = [...p.children].find(c => /\/body$/.test(c.dataset.key || ''));
            const name = t.textContent.trim(), r = p.getBoundingClientRect(); out.panels.push(name);
            if (p.dataset.cut || (body && body.dataset.cut) || [...p.querySelectorAll('[data-cut]')].length) out.cut.push(name);
            if (!body || !pt.vis(body) || body.getBoundingClientRect().height < 24) out.tiny.push(name); }
          for (const e of document.querySelectorAll('#paint [data-key]')) { if (!pt.vis(e) || e.querySelector('[data-key]')) continue;
            if (e.scrollWidth > e.clientWidth + 2 && getComputedStyle(e).overflowX !== 'visible' && !e.classList.contains('clamp')) out.spill.push(e.dataset.key.split('/').slice(-2).join('/')); }
          out.parts = document.querySelectorAll('#paint [data-key]').length; return out; })()""")
        note = (f"{len(g['panels'])} panels out ({', '.join(g['panels'])}); {g['parts']} painted parts; "
                f"cut at the foot: {', '.join(g['cut']) or 'none'}; words cut at the side: {len(g['spill'])}"
                + (f" ({', '.join(g['spill'][:4])})" if g["spill"] else "")
                + (f"; only a title showing: {', '.join(g['tiny'])}" if g["tiny"] else ""))
        bare = [t for t in g["tiny"] if t]
        if bare:
            raise AssertionError(note)
        return {"note": note}
    steps.append(("glance", "a glance with every panel out: what is cut or squeezed", s_glance, (OK_MS, SLOW_MS)))

    async def s_dock():
        icon = DOCK.format(json.dumps("Board"))
        if not await play.has(icon):
            raise AssertionError("no Board icon on the dock")
        r = await play.timed("pt.parts('lens:home-viewer').some(e => /\\/open\\/f155$/.test(e.dataset.key))", press(play, icon, "Board on the dock"))
        if not r["ok"]:
            r["want"] = "Board on the dock did not open the Board in the middle"
            return r
        await asyncio.sleep(0.3)
        await w.shot(play.out / f"{play.n + 1:02d}-dock-board.png")
        r2 = await play.timed("!!pt.part('lens:jeff-chat') && !pt.parts('lens:home-viewer').some(e => /\\/open\\/f155$/.test(e.dataset.key))",
                              press(play, DOCK.format(json.dumps("JEFF")), "JEFF on the dock"))
        if not r2["ok"]:
            r2["want"] = "JEFF on the dock did not bring the chat back"
            return r2
        r["note"] = f"Board opened in {r['ms']} ms, JEFF's chat back in {r2['ms']} ms"
        r["ms"] = max(r["ms"], r2["ms"])
        return r
    steps.append(("dock", "use the dock: Board, then back to JEFF", s_dock, (OK_MS, SLOW_MS)))

    async def s_esc():
        icon = DOCK.format(json.dumps("Board"))
        r1 = await play.timed("!!document.getElementById('menu-pop')", press(play, icon, "Board on the dock", right=True))
        if not r1["ok"]:
            r1["want"] = "a right-click on a dock icon opened no menu"
            return r1
        r = await play.timed("!document.getElementById('menu-pop')", lambda: w.key("Escape"))
        if not r["ok"]:
            r["want"] = "Esc did not close the open menu"
            return r
        r["note"] = (f"the dock's menu opened in {r1['ms']} ms and Esc closed it in {r['ms']} ms; Esc hiding the whole home "
                     "base is hud.py's own key (a global hotkey), not a page's, so not played here")
        return r
    steps.append(("esc", "press Esc: what is open closes", s_esc, (OK_MS, SLOW_MS)))

    async def s_winkey():
        play.needs("a5980", "the Windows key")
        p = await asyncio.to_thread(subprocess.run, [PY, str(HERE / "test_winkey.py")], capture_output=True, text=True, timeout=180)
        lines = (p.stdout or "").strip().splitlines()
        fails = [x for x in lines if x.startswith("FAIL")]
        if p.returncode or fails:
            raise AssertionError(f"test_winkey.py: {len(fails)} failed: " + "; ".join(fails[:3]) + (f" (exit {p.returncode})" if p.returncode else ""))
        return {"note": f"no key is sent: test_winkey.py drives the tap logic and the hook with made-up keys ({sum(x.startswith('ok') for x in lines)} ok)"}
    steps.append(("winkey", "the Windows key shows and hides it (test_winkey.py)", s_winkey, (OK_MS, SLOW_MS)))

    # the board goes back before fill and widen: dragged out, a5994's tiling leaves one column, and ⇔ has nothing to
    # take room from (ran 16 Oct: widen failed so, the tiling was right)
    order = ["open", "lowdown", "board", "card", "later", "approve", "sendback", "atwork", "writing", "writedoc", "comment",
             "chat", "send", "drag", "restore", "fill", "widen", "glance", "dock", "esc", "winkey"]
    steps.sort(key=lambda s: order.index(s[0]) if s[0] in order else len(order))
    for sid, name, fn, budget in steps:
        if want(sid):
            await S(sid, name, fn, budget)
        else:
            await skip_unwanted(sid, name)


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
    return 1 if guard[0] else 0


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
    a = ap.parse_args()
    if a.list:
        print(__doc__.split("Steps (ids")[1])
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
