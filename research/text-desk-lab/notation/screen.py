"""screen: see and use a painted view without a browser window. OWNER: Claude (command center, 29 Sep).

Alex, 29 Sep: workers change the painter without being able to see it. This drives a real headless Chrome (or Edge)
over the DevTools protocol against a throwaway deskd, so any agent that can run Python can look at a view, press it,
and read back what it measured. The screenshot is a PNG a model can open with its Read tool.

    python screen.py <world> --as <you> [--lens command-center] [--size 1500x900] [--live] [--term] [--page shell] STEP ...

--term keeps the desk terminal beside the lens (it is hidden by default here); --page shell opens the windowed
desktop (index.html: dock, windows, apps) instead of the painter. --reduced-motion looks as someone whose system asks
for reduced motion (prefers-reduced-motion: reduce).

By default the world is a COPY (sessions/<world>-screen-<pid>.pickle, removed after), served by a deskd on a free port
from THIS directory's desk-shell/, so a worktree sees its own painter code and nothing you do reaches the shared world.
`--live` points at the keeper's deskd (port 8794) instead: every press is then a real act, as --as, in the real world.

STEPS (run in order; parts are named by their data-key, e.g. porch/main/right/add, or x,y in CSS pixels, or a CSS
       selector beginning # or . for a part with no key: #term input, .window .titlebar)
    shot [file.png]              screenshot (default screen-<n>.png here); prints the path
    facts [key-prefix] [depth]   per painted part (to depth levels below the prefix, default 2): size, whether it
                                 scrolls or is cut, folded, hidden, off screen, a leaf's words; the window; the status line
    click <part|x,y>             left click at the part's centre (a fold handle: click <part>/handle)
    right <part|x,y>             right click; then `menu` lists the menu that opened
    menu                         the entries of the open right-click menu
    choose <label>               click the entry of the open menu with that label
    type <text>                  click into nothing first; types into what has focus (click the part first)
    key <Enter|Escape|Tab|ArrowDown|...>
    drag <part> <part|x,y>       press on the first, move, release on the second
    scroll <part> <dy>           scroll a part by dy pixels
    wait <ms>
    answer <text>                the next prompt() or confirm() the page opens is answered with text, as a person
                                 typing into it would; a dialog with no answer set is dismissed (and said)
    text <part>                  the part's visible text
    css <part[,part]> <property> each part's computed value of a CSS property now (e.g. opacity), and the animations
                                 running on it, all read at one moment (a1140: a pulse is seen by measuring it twice,
                                 a wait apart; two parts in one step show whether they are in phase)
    blur                         take focus off what has it (as a click on nothing would)
    events [n]                   the world's last n events (default 5): id, verb, by, gesture, and the line's words
    resend [k]                   post again, unchanged, the k-th last gesture this page sent (default 1: the last);
                                 prints deskd's answer. A retry after a lost answer, as the painter would make it
    restart | stop | start       stop the throwaway deskd and/or start it again on the same port (not with --live);
                                 a press while it is stopped is a lost answer, as when deskd restarts mid-send
Example:
    python screen.py frontier --as pike facts porch/main/middle click porch/main/middle/shop/handle facts porch/main/middle shot
"""
import asyncio
import base64
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import websockets

HERE = Path(__file__).resolve().parent
PY = sys.executable
BROWSERS = [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe", "/usr/bin/google-chrome", "/usr/bin/chromium"]

FACTS_JS = r"""
((prefix, depth) => {
  const base = prefix ? prefix.split('/').length : 0, out = [], vis = e => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length);
  for (const e of document.querySelectorAll('#paint [data-key]')) {
    const k = e.dataset.key; if (prefix && !k.startsWith(prefix)) continue;
    if (k.split('/').length - base > depth) continue;
    if (!vis(e)) { if (e.hidden) out.push(`${k}: hidden`); continue; }
    const r = e.getBoundingClientRect(), st = getComputedStyle(e);
    const scrolls = /(auto|scroll)/.test(st.overflowY) && e.scrollHeight > e.clientHeight + 1;
    const cut = !scrolls && st.overflowY !== 'visible' && e.scrollHeight > e.clientHeight + 1;
    const bits = [`${Math.round(r.width)}x${Math.round(r.height)} at ${Math.round(r.left)},${Math.round(r.top)}`];
    if (scrolls) bits.push(`scrolls (${e.scrollHeight}px of content, at ${Math.round(e.scrollTop)})`);
    if (cut) bits.push(`cut (${e.scrollHeight}px of content)`);
    if (e.dataset.folded === '1') bits.push('folded');
    if (r.bottom < 0 || r.top > innerHeight || r.right < 0 || r.left > innerWidth) bits.push('off screen');
    const h = e.querySelector(':scope > button'); if (h) bits.push(`handle "${h.textContent}"`);
    if (e.childElementCount === 0 || e.children.length === (h ? 1 : 0)) { const t = e.textContent.trim(); if (t) bits.push(JSON.stringify(t.length > 60 ? t.slice(0, 60) + '…' : t)); }
    out.push(`${k}: ${bits.join(', ')}`);
  }
  const s = document.getElementById('status');
  return [`window ${innerWidth}x${innerHeight}, page ${document.documentElement.scrollWidth}x${document.documentElement.scrollHeight}`
          + (s && s.textContent ? `; status: ${s.textContent.slice(0, 300)}` : '; status: (none)'), ...out].join('\n');
})
"""


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def wait_http(url, secs=20):
    t = time.time() + secs
    while time.time() < t:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                return r.read()
        except Exception:
            time.sleep(0.2)
    raise SystemExit(f"screen: nothing answered at {url} within {secs}s")


class Page:
    def __init__(self, ws):
        self.ws, self.n, self.reply = ws, 0, None

    async def call(self, method, **params):
        self.n += 1
        me = self.n
        await self.ws.send(json.dumps({"id": me, "method": method, "params": params}))
        while True:
            m = json.loads(await self.ws.recv())
            if m.get("method") == "Page.javascriptDialogOpening":
                # a1047: a prompt() or confirm() blocks the press that opened it; it is answered as `answer` said, or
                # dismissed. Sent without waiting: the press's own reply comes once the dialog is closed.
                d, text, self.reply = m["params"], self.reply, None
                print(f"dialog ({d.get('type')}) {d.get('message', '')!r}: " + (f"answered {text!r}" if text is not None else "dismissed"))
                self.n += 1
                await self.ws.send(json.dumps({"id": self.n, "method": "Page.handleJavaScriptDialog",
                                               "params": {"accept": text is not None, "promptText": text or ""}}))
                continue
            if m.get("id") == me:
                if "error" in m:
                    raise RuntimeError(f"{method}: {m['error'].get('message')}")
                return m.get("result", {})

    async def js(self, expr):
        r = await self.call("Runtime.evaluate", expression=expr, awaitPromise=True, returnByValue=True)
        if r.get("exceptionDetails"):
            raise RuntimeError(r["exceptionDetails"].get("exception", {}).get("description") or str(r["exceptionDetails"]))
        return r.get("result", {}).get("value")

    async def where(self, target):
        if "," in target and all(p.strip().lstrip("-").replace(".", "").isdigit() for p in target.split(",")):
            x, y = (float(p) for p in target.split(","))
            return x, y
        if target[:1] in "#.":                  # a1047: a part with no key (the terminal's line, a shell window) by CSS
            r = await self.js(f"""(() => {{ const e = document.querySelector({json.dumps(target)}); if (!e) return null;
                e.scrollIntoView({{block: 'nearest', inline: 'nearest'}}); const r = e.getBoundingClientRect();
                return [r.left + r.width / 2, r.top + r.height / 2, r.width, r.height]; }})()""")
            if not r or (r[2] == 0 and r[3] == 0):
                raise RuntimeError(f"nothing visible matches {target!r}")
            return r[0], r[1]
        handle = target.endswith("/handle")
        key = target[:-len("/handle")] if handle else target
        r = await self.js(f"""(() => {{ let e = document.querySelector('[data-key="{key}"]'); if (!e) return null;
            {"e = e.querySelector(':scope > button') || e;" if handle else ""}
            e.scrollIntoView({{block: 'nearest', inline: 'nearest'}}); const r = e.getBoundingClientRect();
            return [r.left + r.width / 2, r.top + r.height / 2, r.width, r.height]; }})()""")
        if not r:
            raise RuntimeError(f"no painted part {key!r} (try `facts` to list the keys)")
        if r[2] == 0 and r[3] == 0:
            raise RuntimeError(f"{key!r} is painted but not visible (folded or hidden?)")
        return r[0], r[1]

    async def mouse(self, kind, x, y, button="left", buttons=1, count=1):
        await self.call("Input.dispatchMouseEvent", type=kind, x=x, y=y, button=button, buttons=buttons, clickCount=count)

    async def press(self, x, y, button="left"):
        b = 1 if button == "left" else 2
        await self.mouse("mouseMoved", x, y, "none", 0)
        await self.mouse("mousePressed", x, y, button, b)
        await self.mouse("mouseReleased", x, y, button, 0)


STEPS = ("shot", "facts", "click", "right", "menu", "choose", "type", "key", "drag", "scroll", "wait", "answer", "text",
         "css", "blur", "events", "resend", "restart", "stop", "start")
# a1008: every body the page posts to /api/do is kept (page-side, in order), so `resend` can replay one unchanged
SENDS_JS = """(() => { const f = window.fetch; window.__sends = [];
  window.fetch = (u, o) => { if (String(u).startsWith('/api/do') && o && o.body) window.__sends.push(o.body); return f(u, o); }; })();"""
EVENTS_JS = r"""
(async (n) => {
  const s = new URLSearchParams(location.search).get('session');
  const t = (await (await fetch(`/api/events?session=${s}&since=999999999`)).json()).total;
  const evs = (await (await fetch(`/api/events?session=${s}&since=${Math.max(0, t - n)}`)).json()).events;
  return [`events: ${t} in all`, ...evs.map(e => `  ${e.id} ${e.verb} ${e.target} by ${e.by}${e.gesture ? ' gesture ' + e.gesture : ''} `
    + JSON.stringify(e.args || {}).slice(0, 90))].join('\n');
})
"""
KEYS = {"Enter": (13, "\r"), "Escape": (27, ""), "Tab": (9, "\t"), "Backspace": (8, ""), "Delete": (46, ""),
        "ArrowDown": (40, ""), "ArrowUp": (38, ""), "ArrowLeft": (37, ""), "ArrowRight": (39, ""), "Space": (32, " ")}


async def run(url, steps, size, shots, restart=None, still=False):
    w, h = size
    exe = next((b for b in BROWSERS if Path(b).exists()), None)
    if not exe:
        raise SystemExit("screen: no Chrome or Edge found; looked in " + ", ".join(BROWSERS))
    prof = tempfile.mkdtemp(prefix="screen-profile-")
    port = free_port()
    br = subprocess.Popen([exe, "--headless=new", f"--remote-debugging-port={port}", f"--user-data-dir={prof}",
                           "--no-first-run", "--no-default-browser-check", "--disable-extensions", "--hide-scrollbars",
                           f"--window-size={w},{h}", "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wait_http(f"http://127.0.0.1:{port}/json/version")
        tabs = json.loads(wait_http(f"http://127.0.0.1:{port}/json"))
        ws_url = next(t["webSocketDebuggerUrl"] for t in tabs if t.get("type") == "page")
        async with websockets.connect(ws_url, max_size=64 * 1024 * 1024) as ws:
            p = Page(ws)
            await p.call("Page.enable")
            await p.call("Emulation.setDeviceMetricsOverride", width=w, height=h, deviceScaleFactor=1, mobile=False)
            if still:
                await p.call("Emulation.setEmulatedMedia", features=[{"name": "prefers-reduced-motion", "value": "reduce"}])
            await p.call("Page.addScriptToEvaluateOnNewDocument", source=SENDS_JS)
            await p.call("Page.navigate", url=url)
            for _ in range(100):                          # the painter has drawn when a keyed part exists, or it refused
                await asyncio.sleep(0.2)
                ok = await p.js("!!document.querySelector('#paint [data-key], #dock button') || !!(document.getElementById('status')||{}).textContent")
                if ok:
                    break
            await asyncio.sleep(0.6)
            i = 0
            while i < len(steps):
                s = steps[i]
                i += 1
                arg = lambda: steps.__getitem__(i)          # noqa: E731
                if s == "shot":
                    f = steps[i] if i < len(steps) and steps[i].endswith(".png") else None
                    if f:
                        i += 1
                    shots[0] += 1
                    f = Path(f or f"screen-{shots[0]}.png").resolve()
                    data = (await p.call("Page.captureScreenshot", format="png"))["data"]
                    f.write_bytes(base64.b64decode(data))
                    print(f"shot: {f}")
                elif s == "facts":
                    pre, depth = "", 2
                    if i < len(steps) and steps[i] not in STEPS and not steps[i].isdigit():
                        pre, i = steps[i], i + 1
                    if i < len(steps) and steps[i].isdigit():
                        depth, i = int(steps[i]), i + 1
                    print(await p.js(f"{FACTS_JS}({json.dumps(pre)}, {depth})"))
                elif s in ("click", "right"):
                    x, y = await p.where(arg())
                    i += 1
                    await p.press(x, y, "left" if s == "click" else "right")
                    await asyncio.sleep(0.8)
                    print(f"{s} at {round(x)},{round(y)}")
                elif s == "menu":
                    print("menu: " + (await p.js("(() => { const m = document.getElementById('menu-pop'); return m ? [...m.querySelectorAll('button')].map(b => b.textContent).join(' | ') : '(no menu open)'; })()")))
                elif s == "choose":
                    label = arg()
                    i += 1
                    r = await p.js(f"(() => {{ const b = [...document.querySelectorAll('#menu-pop button')].find(b => b.textContent === {json.dumps(label)}); if (!b) return null; const r = b.getBoundingClientRect(); return [r.left + r.width/2, r.top + r.height/2]; }})()")
                    if not r:
                        raise RuntimeError(f"no open menu entry {label!r}")
                    await p.press(*r)
                    await asyncio.sleep(1.5)
                    print(f"chose {label!r}")
                elif s == "type":
                    await p.call("Input.insertText", text=arg())
                    i += 1
                    print("typed")
                elif s == "key":
                    k = arg()
                    i += 1
                    code, text = KEYS.get(k, (0, k if len(k) == 1 else ""))
                    base = dict(key=" " if k == "Space" else k, windowsVirtualKeyCode=code, code=k)
                    await p.call("Input.dispatchKeyEvent", type="keyDown", text=text, **base)
                    await p.call("Input.dispatchKeyEvent", type="keyUp", **base)
                    await asyncio.sleep(1.2 if k == "Enter" else 0.3)
                    print(f"key {k}")
                elif s == "drag":
                    x0, y0 = await p.where(arg())
                    x1, y1 = await p.where(steps[i + 1])
                    i += 2
                    await p.mouse("mouseMoved", x0, y0, "none", 0)
                    await p.mouse("mousePressed", x0, y0, "left", 1)
                    for t in range(1, 11):
                        await p.mouse("mouseMoved", x0 + (x1 - x0) * t / 10, y0 + (y1 - y0) * t / 10, "left", 1)
                        await asyncio.sleep(0.03)
                    await p.mouse("mouseReleased", x1, y1, "left", 0)
                    await asyncio.sleep(1.5)
                    print(f"dragged {round(x0)},{round(y0)} -> {round(x1)},{round(y1)}")
                elif s == "scroll":
                    key, dy = arg(), steps[i + 1]
                    i += 2
                    print(await p.js(f"(() => {{ const e = document.querySelector('[data-key=\"{key}\"]'); if (!e) return 'no part {key}'; e.scrollTop += {float(dy)}; return 'scrolled {key} to ' + Math.round(e.scrollTop); }})()"))
                elif s == "wait":
                    await asyncio.sleep(float(arg()) / 1000)
                    i += 1
                elif s == "answer":
                    p.reply = arg()
                    i += 1
                    print(f"the next dialog will be answered {p.reply!r}")
                elif s == "text":
                    key = arg()
                    i += 1
                    print(await p.js(f"(() => {{ const e = document.querySelector('[data-key=\"{key}\"]'); return e ? e.innerText : 'no part {key}'; }})()"))
                elif s == "css":
                    key, prop = arg(), steps[i + 1]
                    i += 2
                    print(await p.js(f"""(() => {json.dumps(key.split(","))}.map(k => {{ const e = document.querySelector(`[data-key="${{k}}"]`);
                        if (!e) return 'no part ' + k; const a = e.getAnimations().map(a => a.animationName || a.constructor.name);
                        return k + ' {prop} ' + getComputedStyle(e).getPropertyValue({json.dumps(prop)}) + '; animations: ' + (a.join(', ') || 'none'); }}).join('\\n'))()"""))
                elif s == "blur":
                    print("blurred " + str(await p.js("(() => { const a = document.activeElement; const k = a && a.dataset && a.dataset.key; if (a && a.blur) a.blur(); return k || (a ? a.tagName : 'nothing'); })()")))
                    await asyncio.sleep(1.2)
                elif s == "events":
                    n = 5
                    if i < len(steps) and steps[i].isdigit():
                        n, i = int(steps[i]), i + 1
                    print(await p.js(f"{EVENTS_JS}({n})"))
                elif s == "resend":
                    k = 1
                    if i < len(steps) and steps[i].isdigit():
                        k, i = int(steps[i]), i + 1
                    r = await p.js(f"""(async () => {{ const b = window.__sends[window.__sends.length - {k}]; if (!b) return 'resend: this page sent nothing yet';
                        const r = await (await fetch('/api/do', {{method: 'POST', body: b}})).json();
                        return 'resent ' + JSON.stringify(JSON.parse(b).gesture || null) + ': ' + JSON.stringify({{text: r.text, error: r.error, events: r.events}}); }})()""")
                    print(r)
                elif s in ("restart", "stop", "start"):
                    if not restart:
                        raise RuntimeError(f"{s}: only the throwaway deskd can be stopped or started (not with --live)")
                    restart(s)
                    print({"restart": "deskd restarted", "stop": "deskd stopped", "start": "deskd started"}[s])
                else:
                    raise RuntimeError(f"unknown step {s!r}; see python screen.py --help")
    finally:
        br.terminate()
        try:
            br.wait(timeout=10)
        except Exception:
            br.kill()
        shutil.rmtree(prof, ignore_errors=True)


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return
    world, who, lens, size, live, steps = a[0], None, "command-center", (1500, 900), False, []
    page, term, still = "lens", False, False
    k = 1
    while k < len(a):
        if a[k] == "--reduced-motion":
            still, k = True, k + 1
        elif a[k] == "--page":
            page, k = a[k + 1], k + 2
            if page not in ("lens", "shell"):
                raise SystemExit("screen: --page is lens (the painter, lens.html) or shell (the windowed desktop, index.html)")
        elif a[k] == "--term":
            term, k = True, k + 1
        elif a[k] == "--as":
            who, k = a[k + 1], k + 2
        elif a[k] == "--lens":
            lens, k = a[k + 1], k + 2
        elif a[k] == "--size":
            size, k = tuple(int(x) for x in a[k + 1].lower().split("x")), k + 2
        elif a[k] == "--live":
            live, k = True, k + 1
        else:
            steps.append(a[k])
            k += 1
    if not who:
        raise SystemExit("screen: say who is looking with --as <you> (a press acts as that name)")
    steps = steps or ["facts", "shot"]
    srv, copy, restart = None, None, None
    try:
        if live:
            port, session = 8794, world
        else:
            src = HERE / "sessions" / f"{world}.pickle"
            if not src.exists():
                raise SystemExit(f"screen: no world {world!r} in {HERE / 'sessions'}")
            session = f"{world}-screen-{os.getpid()}"
            copy = HERE / "sessions" / f"{session}.pickle"
            shutil.copy(src, copy)
            port = free_port()
            srv = subprocess.Popen([PY, "deskd.py", str(port)], cwd=HERE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            wait_http(f"http://127.0.0.1:{port}/lens.html")

            def restart(how):
                nonlocal srv
                if how in ("restart", "stop") and srv.poll() is None:
                    srv.terminate()
                    srv.wait()
                if how in ("restart", "start") and srv.poll() is not None:
                    srv = subprocess.Popen([PY, "deskd.py", str(port)], cwd=HERE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    wait_http(f"http://127.0.0.1:{port}/lens.html")
        if page == "shell":
            q, what, file = urllib.parse.urlencode({"session": session, "as": who}), "the windowed shell", "index.html"
        else:
            q = {"session": session, "as": who, "lens": lens, "view": "painter"} | ({} if term else {"inspect": "0"})
            q, what, file = urllib.parse.urlencode(q), f"lens {lens}" + (" with the terminal" if term else ""), "lens.html"
        print(f"screen: {'LIVE ' if live else 'a copy of '}{world} as {who}, {what}, {size[0]}x{size[1]}")
        asyncio.run(run(f"http://127.0.0.1:{port}/{file}?{q}", steps, size, [0], restart, still))
    finally:
        if srv:
            srv.terminate()
            srv.wait()
        if copy:
            for p in copy.parent.glob(copy.stem + "*"):
                p.unlink(missing_ok=True)


if __name__ == "__main__":
    import urllib.parse  # noqa: E402,F401
    main()
