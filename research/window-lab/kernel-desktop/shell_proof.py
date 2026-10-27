"""shell_proof: the desktop shell (top bar, dock, desktop layer) rendered and checked, hidden and headless.

    python shell_proof.py                 everything below, evidence into evidence/shell/
    python shell_proof.py looks           only the four full-screen composites
    python shell_proof.py popovers        only the popovers
    python shell_proof.py dock            only the dock with 3, 8 and 16 apps
    python shell_proof.py a11y            only keyboard reachability and screen-reader names
    python shell_proof.py spikes          only the two hidden-desktop spikes (window shape, WorkerW)
    python shell_proof.py interact        only the click / middle-click / right-click / fallback checks

Nothing here touches Alex's screen, the live desktop (127.0.0.1:8810) or a Windows setting. The pages are served from a
tiny loopback server of their own (the same files kdesk serves under /desk/, and the same icon route), drawn by headless
Edge with a 150% device scale on a 3840x2160 screen. The window manager and the theme are other builders' work, so
fixtures.js stands in for wm.windows rows and the stand-in looks (pages/shell/looks) for /theme.css, using the contract's
exact variable names. The spikes run on a hidden desktop (research/window-lab/sandbox_window.py).

A composite is one web page: the desktop layer, a few fake app windows in their gapped places, and the real top bar and
dock pages in iframes, each clipped to the region the page itself reports for SetWindowRgn (window.__shape). So what is
drawn is what the host would let show: the rest of each window is not there.
"""
import base64
import json
import os
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
(HERE / "state").mkdir(exist_ok=True)
sys.path.insert(0, str(HERE.parents[1] / "kernel-lab"))
import shell_icons  # noqa: E402
from hidden_evidence import Browser  # noqa: E402

PAGES = HERE / "pages"
OUT = HERE / "evidence" / "shell"
PY = Path(sys.executable)
SW, SH, DPR = 2560, 1440, 1.5            # 3840 x 2160 at 150%
TOP_ROOM = 560                           # css px: the top window's height (bar + room for a popover)
DOCK_W, DOCK_H = 1560, 460               # css px: the dock window (wider and taller than its pill)
SHOWN = []                               # what each check printed, for the summary at the end


def say(line):
    SHOWN.append(line)
    print(line, flush=True)


# ------------------------------------------------------------------------------------------------ the server
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype, extra=()):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in extra:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        u = urlsplit(self.path)
        path = u.path
        if path == "/desk/icon":
            q = parse_qs(u.query)
            code, ctype, data = shell_icons.serve((q.get("ref") or [""])[0], (q.get("size") or ["128"])[0])
            return self._send(code, data, ctype)
        if path.startswith("/proof/theme/"):
            from theme import compile as TC, model as TM, starters as TS
            slug = path.rsplit("/", 1)[-1][:-4]
            th = dict(TS.all_starters()).get(slug)
            if th is None:
                return self._send(404, b"no such starter", "text/plain")
            r = TM.resolve(th)
            return self._send(200, TC.css(r, TC.wallpaper_uri(r), TM.digest(th)).encode("utf-8"), "text/css; charset=utf-8")
        if path == "/proof/composite.html":
            return self._send(200, composite_page(parse_qs(u.query)).encode("utf-8"), "text/html; charset=utf-8")
        if path.startswith("/desk/"):
            p = (PAGES / path[6:]).resolve()
            if PAGES.resolve() in p.parents and p.is_file():
                ctype = {".html": "text/html", ".css": "text/css", ".js": "application/javascript", ".svg": "image/svg+xml",
                         ".png": "image/png"}.get(p.suffix, "application/octet-stream")
                return self._send(200, p.read_bytes(), ctype + ("; charset=utf-8" if ctype.startswith("text") or "javascript" in ctype else ""))
        self._send(404, b"not here", "text/plain")


def serve():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


# ------------------------------------------------------------------------------------------------ the composite
def fake_windows_html():
    """Three app windows in their gapped places, drawn with the page's own variables (an app that follows the theme).
    The work area is what is left of the screen after the top strip and the dock strip."""
    return """
<style>
  .fw { position:absolute; display:flex; flex-direction:column; overflow:hidden; border-radius:var(--ag-radius-m);
        background:var(--ag-surface); color:var(--ag-ink); border:var(--ag-border-width) solid var(--ag-border);
        box-shadow:var(--ag-shadow); font:400 13.5px/1.5 var(--ag-font-ui); }
  .fw.front { border-color:var(--ag-accent); }
  .fw header { display:flex; align-items:center; gap:10px; height:34px; padding:0 12px; background:color-mix(in srgb,var(--ag-bar) 70%,var(--ag-surface));
               border-bottom:var(--ag-border-width) solid var(--ag-border); font-weight:600; font-size:12.5px; flex:none; }
  .fw header i { width:11px; height:11px; border-radius:50%; background:color-mix(in srgb,var(--ag-ink) 22%,transparent); }
  .fw header i:nth-child(1) { background:var(--ag-danger); } .fw header i:nth-child(2) { background:var(--ag-warn); } .fw header i:nth-child(3) { background:var(--ag-ok); }
  .fw .body { flex:1; padding:14px 16px; overflow:hidden; }
  .mono { font-family:var(--ag-font-mono); font-size:13px; line-height:1.55; white-space:pre; }
  .mono .a { color:var(--ag-accent); } .mono .o { color:var(--ag-ok); } .mono .w { color:var(--ag-warn); } .mono .d { color:var(--ag-ink-muted); } .mono .r { color:var(--ag-danger); }
  .card { background:var(--ag-raised); border:var(--ag-border-width) solid var(--ag-border); border-radius:var(--ag-radius-m); padding:14px 16px; margin-bottom:12px; }
  .card b { display:block; font-size:15px; margin-bottom:3px; }
  .card small { color:var(--ag-ink-muted); }
  .pillrow { display:flex; gap:8px; margin-bottom:14px; }
  .pillrow span { padding:5px 14px; border-radius:var(--ag-radius-pill); background:color-mix(in srgb,var(--ag-accent) 16%,transparent); font-weight:600; font-size:12.5px; }
  .pillrow span:first-child { background:var(--ag-accent); color:var(--ag-accent-ink); }
  .bars { display:grid; grid-template-columns:90px 1fr 50px; gap:6px 12px; align-items:center; font-family:var(--ag-font-mono); font-size:12.5px; }
  .bars i { height:9px; border-radius:6px; background:color-mix(in srgb,var(--ag-ink) 12%,transparent); position:relative; overflow:hidden; display:block; }
  .bars i::after { content:""; position:absolute; inset:0 auto 0 0; width:var(--w); background:var(--ag-accent); }
</style>
<div class="fw front" id="w1"><header><i></i><i></i><i></i><span>Terminal</span></header><div class="body mono"><span class="d">~</span> <span class="a">$</span> agora status
<span class="o">ok</span>  desk       <span class="d">Alex's desktop · 3 windows · theme </span><span class="a" id="tn"></span>
<span class="o">ok</span>  jeff       <span class="d">here, drafting the council summary</span>
<span class="o">ok</span>  wm         <span class="d">live · 4 pinned · gaps 8</span>
<span class="w">..</span>  feed       <span class="d">3 new posts</span>

<span class="d">~</span> <span class="a">$</span> window.list
  dk4  Task board   <span class="d">taskboard</span>   <span class="d">at 1240,96</span>
  dk7  Lines        <span class="d">lines</span>       <span class="d">at 80,620</span>
  dk9  Board        <span class="d">board</span>       <span class="d">tucked away</span>

<span class="d">~</span> <span class="a">$</span> <span class="r">_</span></div></div>
<div class="fw" id="w2"><header><i></i><i></i><i></i><span>Seabright Board</span></header><div class="body">
  <div class="pillrow"><span>Today</span><span>Harbor</span><span>Council</span><span>Market</span></div>
  <div class="card"><b>Harbor cleanup, Saturday at nine</b><small>Maya, 5 min ago · 14 going · 6 spots left</small></div>
  <div class="card"><b>Council agenda for Thursday</b><small>Posted by the clerk · three items need a vote</small></div>
  <div class="card"><b>Lost: grey cat near Pier 2</b><small>Dana, yesterday · answers to Moth</small></div></div></div>
<div class="fw" id="w3"><header><i></i><i></i><i></i><span>Task board</span></header><div class="body mono">
<span class="d">CPU</span>  <span class="a">||||||||||</span><span class="d">..........</span> 52%
<span class="d">MEM</span>  <span class="a">||||||||</span><span class="d">............</span> 41%
<span class="d">NET</span>  <span class="o">||||</span><span class="d">................</span> 1.2 MB/s

<span class="a">Now</span>      Review the community board proof
<span class="a">Next</span>     Seabright sign-in page
<span class="d">Later</span>    Shifts and the volunteer calendar</div></div>
"""


def theme_qs(desc):
    """'real:dusk' -> the theme builder's compiled starter; 'standin:dusk' -> this folder's stand-in look."""
    kind, _, slug = desc.partition(":")
    return f"theme=/proof/theme/{slug}.css" if kind == "real" else f"look={slug}"


def theme_href(desc):
    kind, _, slug = desc.partition(":")
    return f"/proof/theme/{slug}.css" if kind == "real" else f"/desk/shell/looks/{slug}.css"


def composite_page(q):
    g = lambda k, d="": (q.get(k) or [d])[0]
    desc, apps = g("look", "real:dusk"), g("apps", "wm8")
    extra = g("extra")            # more query to pass to the pages (e.g. wm=off, hide=1)
    only_desk = g("only") == "desk"
    tq = theme_qs(desc)
    ex = ("&" + extra) if extra else ""
    scr = f"sx=0&sy=0&sw={SW}&sh={SH}"
    hide = "display:none;" if only_desk else ""
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>composite</title>
<link rel="stylesheet" href="/desk/shell/shell.css"><link id="theme" rel="stylesheet" href="{theme_href(desc)}">
<style>html,body{{margin:0;width:{SW}px;height:{SH}px;overflow:hidden;background:#000}} iframe{{position:absolute;border:0;background:transparent}}
.wallpaper{{left:0;top:0;width:{SW}px;height:{SH}px}}</style></head><body>
<iframe class="wallpaper" id="desk" src="/desk/shell/desktop.html?{tq}&{scr}" title="desktop layer"></iframe>
<div id="windows" style="position:absolute;inset:0">{fake_windows_html()}</div>
<iframe id="top" src="/desk/shell/top.html?{tq}&fixture={apps}&{scr}{ex}" style="{hide}left:0;top:0;width:{SW}px;height:{TOP_ROOM}px" title="top bar"></iframe>
<iframe id="dock" src="/desk/shell/dock.html?{tq}&fixture={apps}&sx={(SW - DOCK_W) // 2}&sy={SH - DOCK_H}&sw={SW}&sh={SH}{ex}"
        style="{hide}left:{(SW - DOCK_W) // 2}px;top:{SH - DOCK_H}px;width:{DOCK_W}px;height:{DOCK_H}px" title="dock"></iframe>
<script>
// place the fake windows in the work area the pages reserve: the top bar's height and the dock's strip, with the
// theme's own gaps (the window manager's job in life; drawn here only so the composite reads as a whole screen)
function css(n){{return getComputedStyle(document.documentElement).getPropertyValue(n).trim();}}
function px(n,d){{const v=parseFloat(css(n));return Number.isNaN(v)?d:v;}}
function lay(){{
  const bh=px('--ag-bar-height',36), ds=px('--ag-dock-size',60), go=px('--ag-gap-outer',10), gi=px('--ag-gap-inner',8);
  const x0=go, y0=bh+go, x1={SW}-go, y1={SH}-(ds+2*go)-go;
  const w=x1-x0, h=y1-y0, lw=Math.round(w*0.33), mw=Math.round(w*0.40), th=Math.round(h*0.60);
  const set=(id,x,y,ww,hh)=>{{const e=document.getElementById(id);e.style.cssText=`left:${{x}}px;top:${{y}}px;width:${{ww}}px;height:${{hh}}px`;}};
  set('w1',x0,y0,lw,th); set('w2',x0+lw+gi,y0,mw,Math.round(h*0.72)); set('w3',x0,y0+th+gi,lw,h-th-gi);
  document.getElementById('tn').textContent='{desc.partition(":")[2]}';
}}
function clipFor(frame){{
  const s=frame.contentWindow.__shape; if(!s) return false;
  const parts=s.shape.map(r=>{{const x=r.x,y=r.y,w=r.w,h=r.h,k=Math.max(0,Math.min(r.r,w/2,h/2));
    return `M${{x+k}} ${{y}}H${{x+w-k}}A${{k}} ${{k}} 0 0 1 ${{x+w}} ${{y+k}}V${{y+h-k}}A${{k}} ${{k}} 0 0 1 ${{x+w-k}} ${{y+h}}H${{x+k}}A${{k}} ${{k}} 0 0 1 ${{x}} ${{y+h-k}}V${{y+k}}A${{k}} ${{k}} 0 0 1 ${{x+k}} ${{y}}Z`;}}).join('');
  frame.style.clipPath=`path('${{parts}}')`; return true;
}}
window.composite=()=>{{lay();return [document.getElementById('top'),document.getElementById('dock')].map(clipFor);}};
lay();
</script></body></html>"""


# ------------------------------------------------------------------------------------------------ browser helpers
ENTER = chr(13)
VK = {"Tab": 9, "Enter": 13, "Escape": 27, "ArrowLeft": 37, "ArrowUp": 38, "ArrowRight": 39, "ArrowDown": 40, "ContextMenu": 93,
      "Home": 36, "End": 35, " ": 32}
DOCK_X, DOCK_Y = (SW - DOCK_W) // 2, SH - DOCK_H


class Shot:
    def __init__(self, base):
        self.base = base
        self.b = Browser()
        self.c = self.b.__enter__()
        self.c.call("Emulation.setDeviceMetricsOverride", width=SW, height=SH, deviceScaleFactor=DPR, mobile=False)
        self.c.call("Emulation.setFocusEmulationEnabled", enabled=True)

    def close(self):
        self.b.__exit__(None, None, None)

    def js(self, expr):
        return self.c.js(expr)

    def composite(self, desc, apps="wm8", extra="", only=""):
        c = self.c
        c.call("Page.navigate", url=f"{self.base}/proof/composite.html?look={desc}&apps={apps}&extra={extra}&only={only}")
        c.until("document.readyState==='complete'")
        c.until("['top','dock','desk'].every(id=>{const w=document.getElementById(id).contentWindow;return w&&w.__ready===true})", timeout=40)
        time.sleep(1.0)
        c.js("window.composite()")
        return c

    def page(self, name, desc, apps="wm8", extra="", w=SW, h=700):
        """One shell page on its own (not in a composite), for keyboard and click checks."""
        c = self.c
        c.call("Emulation.setDeviceMetricsOverride", width=w, height=h, deviceScaleFactor=DPR, mobile=False)
        ex = ("&" + extra) if extra else ""
        c.call("Page.navigate", url=f"{self.base}/desk/shell/{name}.html?{theme_qs(desc)}&fixture={apps}&sx=0&sy=0&sw={SW}&sh={SH}{ex}")
        c.until("document.readyState==='complete' && window.__ready===true", timeout=40)
        time.sleep(0.8)
        c.call("Page.bringToFront")                       # a Tab out of the previous page leaves keyboard focus in the browser's own chrome
        c.call("Emulation.setFocusEmulationEnabled", enabled=True)
        c.js("window.focus()")
        return c

    def restore(self):
        self.c.call("Emulation.setDeviceMetricsOverride", width=SW, height=SH, deviceScaleFactor=DPR, mobile=False)

    def frame(self, id_, expr):
        return self.c.js(f"(()=>{{const w=document.getElementById({json.dumps(id_)}).contentWindow;return ({expr});}})()")

    def settle(self):
        self.c.call("Runtime.evaluate", expression="new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))", awaitPromise=True)
        time.sleep(0.45)

    def png(self, path, clip=None, composite=True):
        """A screenshot that is only kept once two captures in a row agree (Edge's software compositor can hand back a
        stale or tiled frame right after a layout change)."""
        c = self.c
        if composite:
            c.js("window.composite()")
        self.settle()
        args = dict(format="png", captureBeyondViewport=False, fromSurface=True)
        if clip:
            x, y, w, h = clip
            args["clip"] = dict(x=x, y=y, width=w, height=h, scale=DPR)
        prev = None
        for _ in range(6):
            data = c.call("Page.captureScreenshot", **args)["data"]
            if data == prev:
                break
            prev = data
            time.sleep(0.25)
        Path(path).write_bytes(base64.b64decode(data))
        return Path(path)

    # keyboard and mouse, as real input events
    def key(self, name, mods=0):
        vk = VK.get(name)
        base = dict(key=name if len(name) > 1 or name != " " else " ", code=name, windowsVirtualKeyCode=vk or 0, nativeVirtualKeyCode=vk or 0, modifiers=mods)
        if name in ("Enter", " "):                       # a button is pressed by the character event
            base.update(text=ENTER if name == "Enter" else " ", unmodifiedText=ENTER if name == "Enter" else " ")
            self.c.call("Input.dispatchKeyEvent", type="keyDown", **base)
        else:
            self.c.call("Input.dispatchKeyEvent", type="rawKeyDown", **base)
        self.c.call("Input.dispatchKeyEvent", type="keyUp", **base)
        time.sleep(0.12)

    def type(self, text):
        self.c.call("Input.insertText", text=text)
        time.sleep(0.15)

    def mouse(self, x, y, button="left", kind="click"):
        c = self.c
        c.call("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y)
        time.sleep(0.05)
        if kind == "move":
            return
        c.call("Input.dispatchMouseEvent", type="mousePressed", x=x, y=y, button=button, clickCount=1)
        c.call("Input.dispatchMouseEvent", type="mouseReleased", x=x, y=y, button=button, clickCount=1)
        time.sleep(0.2)

    def center(self, selector, root="document"):
        return self.c.js(f"(()=>{{const e={root}.querySelector({json.dumps(selector)});if(!e)return null;const r=e.getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2];}})()")

    def active(self):
        return self.c.js("(()=>{const a=document.activeElement;if(!a||a===document.body)return null;return {tag:a.tagName.toLowerCase(),label:a.getAttribute('aria-label')||a.textContent.trim().slice(0,40),role:a.getAttribute('role')||''}})()")

    def acts(self):
        return self.c.js("window.__acts||[]")


def crop_of(shape_rects, off=(0, 0), margin=50, minw=0, top_anchor=False, extra_below=0):
    xs = [(r["x"], r["y"], r["x"] + r["w"], r["y"] + r["h"]) for r in shape_rects]
    x0 = min(a for a, _, _, _ in xs) + off[0] - margin
    y0 = min(b for _, b, _, _ in xs) + off[1] - margin
    x1 = max(c for _, _, c, _ in xs) + off[0] + margin
    y1 = max(d for _, _, _, d in xs) + off[1] + margin + extra_below
    if top_anchor:
        y0 = 0
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(SW, max(x1, x0 + minw)), min(SH, y1)
    return (int(x0), int(y0), int(x1 - x0), int(y1 - y0))


# ------------------------------------------------------------------------------------------------ the checks
ALL_LOOKS = ["real:seabright-day", "real:dusk", "real:night-metal", "real:ink-landscape", "standin:seabright-day", "standin:dusk"]


def name_of(desc):
    k, _, s = desc.partition(":")
    return f"{k}-{s}"


def looks(shot):
    for desc in ALL_LOOKS:
        shot.composite(desc)
        p = shot.png(OUT / f"full-{name_of(desc)}.png")
        from PIL import Image
        with Image.open(p) as im:
            say(f"full screen: {p.name} {im.size[0]}x{im.size[1]} (top bar, dock and desktop layer in {desc}; 3 fake app windows in their gapped places)")


TOP_POPS = [("launcher", ".btn.mark"), ("app", ".btn.focus"), ("clock", ".btn.clock"), ("bell", ".btn.bell"), ("media", ".btn.media"),
            ("quick", ".btn.qs"), ("jeff", ".btn.jeff")]


def popovers(shot):
    n = 0
    for desc in ("real:dusk", "real:seabright-day", "real:ink-landscape", "real:night-metal"):
        shot.composite(desc)
        which = TOP_POPS if desc in ("real:dusk", "real:seabright-day") else TOP_POPS[2:3]
        for pop, sel in which:
            shot.frame("top", f"w.document.querySelector({json.dumps(sel)}).click()")
            shot.c.until("document.getElementById('top').contentWindow.document.querySelector('.pop.in')!==null", timeout=10)
            time.sleep(0.3)
            rects = shot.frame("top", "w.__shape.shape.slice(1)")
            clip = crop_of(rects, margin=24, minw=520, top_anchor=True)
            p = shot.png(OUT / f"pop-{name_of(desc)}-{pop}.png", clip=clip)
            n += 1
            shot.frame("top", "w.Shell.Pop.close(true)")
            shot.settle()
        if desc in ("real:dusk", "real:seabright-day"):
            # the off button, pressed once: armed, with its toast
            shot.frame("top", "w.document.querySelector('.btn.off').click()")
            time.sleep(0.5)
            rects = [{"x": 1900, "y": 0, "w": 660, "h": 140}]
            shot.png(OUT / f"pop-{name_of(desc)}-off-armed.png", clip=(1700, 0, 860, 170))
            n += 1
            shot.frame("top", "(()=>{w.Shell.Top.state.armed=false;w.Shell.Top.parts.off.classList.remove('armed')})()")
            # the dock's menu, preview and launcher
            for pop, js in (("dock-menu", "(()=>{const b=w.document.querySelector('.item[data-id*=\"msedge\"]');b.dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,cancelable:true}))})()"),
                            ("dock-preview", "(()=>{const b=w.document.querySelector('.item[data-id*=\"msedge\"]');b.dispatchEvent(new PointerEvent('pointerenter'))})()"),
                            ("dock-launcher", "w.document.querySelector('.item.brand').click()")):
                shot.frame("dock", js)
                shot.c.until("document.getElementById('dock').contentWindow.document.querySelector('.pop.in, .pop.preview')!==null", timeout=10)
                time.sleep(0.5)
                sh = shot.frame("dock", "w.__shape")
                rects = [r for r in sh["shape"][1:]] + [sh["shape"][0]]
                clip = crop_of(rects, off=(DOCK_X, DOCK_Y), margin=28, minw=640)
                shot.png(OUT / f"pop-{name_of(desc)}-{pop}.png", clip=clip)
                n += 1
                shot.frame("dock", "(()=>{w.Shell.Pop.close(true);w.Shell.Dock.closePreview(true)})()")
                shot.settle()
    say(f"popovers: {n} images (launcher, app menu, calendar, notifications, media, quick settings, JEFF, off armed, dock menu, dock preview, dock launcher)")


def dock_sets(shot):
    n = 0
    for desc in ("real:seabright-day", "real:dusk", "real:night-metal", "real:ink-landscape"):
        for apps in ("wm3", "wm8", "wm16"):
            shot.composite(desc, apps=apps)
            sh = shot.frame("dock", "w.__shape")
            pill = sh["pill"]
            rows = shot.frame("dock", "w.Shell.Dock.items.length")
            clip = (max(0, int(DOCK_X + pill["x"] - 80)), int(DOCK_Y + pill["y"] - 40), int(pill["w"] + 160), int(pill["h"] + 80))
            shot.png(OUT / f"dock-{name_of(desc)}-{apps[2:]}.png", clip=clip)
            n += 1
            say(f"dock {desc} with {apps[2:]} running apps: {rows} items, pill {pill['w']:.0f}x{pill['h']:.0f} css px, reserve {sh['reserve']} css px")
    say(f"dock sets: {n} images")


def seam(shot):
    """The wallpaper slice behind a window must be the desktop layer's own pixels. Render the screen with only the
    desktop layer, then with the bar and dock windows present but their parts hidden (window.hide), and compare."""
    from PIL import Image, ImageChops
    for desc in ("real:seabright-day", "real:dusk", "real:ink-landscape", "standin:dusk"):
        shot.composite(desc, only="desk")
        a = shot.png(OUT.parent.parent / "state" / "seam-a.png", composite=False)
        shot.composite(desc, extra="hide=1")
        b = shot.png(OUT.parent.parent / "state" / "seam-b.png")
        ia, ib = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
        diff = ImageChops.difference(ia, ib)
        box = diff.getbbox()
        n = sum(1 for p in diff.getdata() if max(p) > 0)
        big = sum(1 for p in diff.getdata() if max(p) > 2)
        say(f"seam {desc}: desktop layer alone vs bar+dock windows over it with their parts hidden: {n} of {ia.size[0] * ia.size[1]} pixels differ, "
            f"{big} by more than 2 levels, largest difference {max(diff.getextrema()[i][1] for i in range(3))}"
            + (f", inside {box}" if box else ""))
    for f in ("seam-a.png", "seam-b.png"):
        (OUT.parent.parent / "state" / f).unlink(missing_ok=True)


def a11y(shot, only=None):
    lines = []
    for name, desc in (("top", "real:dusk"), ("dock", "real:dusk")):
        if only and name != only:
            continue
        shot.page(name, desc, h=700)
        c = shot.c
        ax = c.call("Accessibility.getFullAXTree")["nodes"]
        interesting = [n for n in ax if n.get("role", {}).get("value") in ("button", "switch", "textbox", "menuitem", "toolbar", "dialog", "group", "meter", "progressbar", "status", "separator", "grid", "gridcell")]
        unnamed = [n for n in interesting if n["role"]["value"] in ("button", "switch", "textbox", "menuitem") and not (n.get("name", {}).get("value") or "").strip()]
        lines.append(f"[{name}] accessibility tree: {len(interesting)} landmarks and controls, {len(unnamed)} controls without a name")
        for n in interesting:
            lines.append(f"    {n['role']['value']:<9} {(n.get('name', {}).get('value') or '(no name)')[:90]}")
        # keyboard: Tab enters the toolbar, arrows walk it
        c.js("document.activeElement&&document.activeElement.blur&&document.activeElement.blur()")
        shot.key("Tab")
        first = shot.active()
        lines.append(f"[{name}] Tab -> {first}")
        seen = [first["label"]] if first else []
        for _ in range(30):
            time.sleep(0.25)
            shot.key("ArrowRight")
            a = shot.active()
            if a is None or (len(seen) == 1 and a["label"] in seen):
                time.sleep(0.4)
                shot.key("ArrowRight") if a is not None else None
                a = shot.active()
            if not a or a["label"] in seen:
                lines.append(f"    (walk stopped at {a}; seen so far {len(seen)})")
                break
            seen.append(a["label"])
        lines.append(f"[{name}] ArrowRight walks {len(seen)} controls: " + " | ".join(seen))
        shot.key("Tab")
        after = shot.active()
        lines.append(f"[{name}] one more Tab leaves the toolbar (one tab stop): {after}")
        if name == "top":
            shot.js("document.querySelector('.btn.mark').focus()")
            shot.key("Enter")
            c.until("!!document.querySelector('.pop.in')", timeout=8)
            lines.append(f"[top] Enter on the launcher opens it; focus is in: {shot.active()}")
            shot.type("li")
            n = c.js("document.querySelectorAll('.pop .app').length")
            lines.append(f"[top] typing 'li' filters the launcher to {n} app(s)")
            shot.key("Escape")
            time.sleep(0.3)
            lines.append(f"[top] Escape closes it and focus returns to: {shot.active()}")
            shot.js("document.querySelector('.btn.clock').focus()")
            shot.key(" ")
            time.sleep(0.3)
            lines.append(f"[top] Space opens the calendar: popover role={c.js('document.querySelector(\".pop.in\")&&document.querySelector(\".pop.in\").getAttribute(\"role\")')}, label={c.js('document.querySelector(\".pop.in\")&&document.querySelector(\".pop.in\").getAttribute(\"aria-label\")')}")
            shot.key("Escape")
        else:
            for attempt in range(3):
                shot.js("document.querySelectorAll('.item')[3].focus()")
                time.sleep(0.3)
                shot.key("ContextMenu")
                try:
                    c.until("!!document.querySelector('.pop.in .menu')", timeout=3)
                    break
                except AssertionError:
                    lines.append(f"    (Menu key attempt {attempt + 1} opened nothing; active {shot.active()})")
            c.until("!!document.querySelector('.pop.in .menu')", timeout=8)
            rows = c.js("[...document.querySelectorAll('.pop.in .mrow')].map(r=>r.textContent.trim())")
            lines.append(f"[dock] the Menu key opens an item's menu: {rows}; focus in: {shot.active()}")
            shot.key("ArrowDown")
            lines.append(f"[dock] ArrowDown inside the menu moves focus to: {shot.active()}")
            shot.key("Escape")
            time.sleep(0.3)
            lines.append(f"[dock] Escape closes the menu, focus returns to: {shot.active()}")
    shot.restore()
    (OUT / "a11y-report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    bad = [l for l in lines if "controls without a name" in l and " 0 controls" not in l]
    say("keyboard and screen reader: " + "; ".join(l for l in lines if l.startswith("[") and ("without a name" in l or "walks" in l or "Escape" in l or "Enter on" in l))[:900])
    say("  full report: evidence/shell/a11y-report.txt" + ("   UNNAMED CONTROLS FOUND" if bad else ""))
    assert not bad, bad


def interact(shot):
    """Clicks, middle click, right click, hover and the keyboard, with the window manager answering, and with it off."""
    ok = []

    def check(label, cond, detail=""):
        ok.append(bool(cond))
        say(f"  {'ok  ' if cond else 'FAIL'} {label}" + (f": {detail}" if detail else ""))
        assert cond, label

    shot.page("dock", "real:dusk", apps="wm8", h=500)
    c = shot.c
    say("interaction, window manager answering (fixture wm.windows rows):")
    items = c.js("[...document.querySelectorAll('.item')].map(b=>b.dataset.id)")
    # a not-in-front app: click focuses
    x, y = shot.center('.item[data-id*="notepad"]')
    shot.mouse(x, y)
    check("click on an app that is not in front -> wm.focus", any(a.startswith("wm.focus ") for a in shot.acts()), shot.acts()[-1:] )
    time.sleep(0.4)
    shot.js("window.Shell.Dock.refresh()")
    time.sleep(0.4)
    x, y = shot.center('.item[data-id*="notepad"]')
    shot.mouse(x, y)
    check("click again on the app now in front -> wm.minimise", any(a.startswith("wm.minimise ") for a in shot.acts()), shot.acts()[-1:])
    shot.js("window.Shell.Dock.refresh()")
    time.sleep(0.4)
    x, y = shot.center('.item[data-id*="mspaint"]')      # the fixture's minimised app
    cls = c.js("document.querySelector('.item[data-id*=\"mspaint\"]').className")
    shot.mouse(x, y)
    check("click on a minimised app -> wm.restore", any(a.startswith("wm.restore ") for a in shot.acts()), f"item class '{cls}'; {shot.acts()[-1:]}")
    # a pinned app that is not running: launch; middle click: a new window
    x, y = shot.center('.item[data-id*="wordpad"]')
    shot.mouse(x, y)
    check("click on a pinned app that is not running -> window.launch", any(a.startswith("window.launch path=") and "wordpad" in a for a in shot.acts()), shot.acts()[-1:])
    x, y = shot.center('.item[data-id*="notepad"]')
    before = len(shot.acts())
    shot.mouse(x, y, button="middle")
    check("middle click -> a new window (window.launch)", any(a.startswith("window.launch path=") and "notepad" in a for a in shot.acts()[before:]), shot.acts()[-1:])
    # right click: the menu
    shot.mouse(*shot.center('.item[data-id*="msedge"]'), button="right")
    c.until("!!document.querySelector('.pop.in .menu')", timeout=8)
    rows = c.js("[...document.querySelectorAll('.pop.in .mrow')].map(r=>r.textContent.trim())")
    check("right click -> menu with the app's windows, new window, pin/unpin, close", len(rows) >= 6 and any("Pin in place" in r for r in rows) and any("Close" in r for r in rows), rows)
    shot.mouse(*c.js("(()=>{const e=[...document.querySelectorAll('.pop.in .mrow')].find(r=>/Pin in place/.test(r.textContent));const r=e.getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2]})()"))
    check("menu: Pin in place -> wm.pin", any(a.startswith("wm.pin ") for a in shot.acts()), shot.acts()[-1:])
    shot.js("window.Shell.Dock.refresh()")
    time.sleep(0.4)
    shot.mouse(*shot.center('.item[data-id*="msedge"]'), button="right")
    c.until("!!document.querySelector('.pop.in .menu')", timeout=8)
    shot.mouse(*c.js("(()=>{const e=[...document.querySelectorAll('.pop.in .mrow')].find(r=>/Close all/.test(r.textContent));const r=e.getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2]})()"))
    time.sleep(0.4)
    check("menu: Close all windows -> wm.close for each", sum(1 for a in shot.acts() if a.startswith("wm.close ")) >= 3, [a for a in shot.acts() if a.startswith("wm.close")])
    # hover preview
    shot.mouse(*shot.center('.item[data-id*="explorer"]'), kind="move")
    c.until("!!document.querySelector('.pop.preview')", timeout=8)
    tiles = c.js("document.querySelectorAll('.pop.preview .tile').length")
    time.sleep(0.4)
    native = c.js("(window.__native||[]).filter(n=>n[0]==='thumbs').length")
    check("hover -> preview card with a tile per window, and a thumbs request to the host", tiles >= 2 and native >= 1, f"{tiles} tiles, {native} thumbs call(s)")
    shot.mouse(5, 5, kind="move")
    time.sleep(0.6)
    check("moving away closes the preview", c.js("!document.querySelector('.pop.preview')"))
    # the window manager is off: everything falls back to native_shell words
    shot.page("dock", "real:dusk", apps="wm8", extra="wm=off", h=500)
    say("interaction, window manager off (fallback to window.desktop / window.activate):")
    x, y = shot.center('.item[data-id*="notepad"]')
    shot.mouse(x, y)
    check("click -> window.activate handle=...", any(a.startswith("window.activate handle=") for a in shot.acts()), shot.acts()[-1:])
    shot.mouse(*shot.center('.item[data-id*="notepad"]'), button="right")
    c.until("!!document.querySelector('.pop.in .menu')", timeout=8)
    rows = c.js("[...document.querySelectorAll('.pop.in .mrow')].map(r=>r.textContent.trim())")
    check("menu in fallback: no pin-in-place (it needs the window manager); windows, new window, keep in dock and close still work", not any("Pin in place" in r for r in rows) and any("Close" in r for r in rows) and any("Keep in dock" in r for r in rows), rows)
    # the top bar
    shot.page("top", "real:dusk", apps="wm8", h=640)
    say("top bar:")
    shot.mouse(*shot.center(".btn.off"))
    check("off: first press only arms it", not any(a in ("off window", "wm.mode off") for a in shot.acts()) and c.js("document.querySelector('.btn.off').classList.contains('armed')"))
    shot.mouse(*shot.center(".btn.off"))
    time.sleep(0.3)
    check("off: second press -> wm.mode off, then off window", shot.acts()[-2:] == ["wm.mode off", "off window"], shot.acts()[-2:])
    shot.mouse(*shot.center(".btn.media"))
    c.until("!!document.querySelector('.pop.in .mediapop')", timeout=8)
    shot.mouse(*shot.center('.pop.in .btn.big'))
    check("media popover: play/pause -> media.play", "media.play" in shot.acts(), shot.acts()[-1:])
    shot.key("Escape")
    shot.mouse(*shot.center(".btn.qs"))
    c.until("!!document.querySelector('.pop.in .quick')", timeout=8)
    shot.mouse(*shot.center('.pop.in .sw'))
    time.sleep(0.3)
    check("quick settings: show CPU in the bar is a switch that writes a setting", any("show_cpu=yes" in a for a in shot.acts()), shot.acts()[-1:])
    shot.js("window.Shell.Top.refreshSlow()")
    time.sleep(0.5)
    check("an optional reading appears only after the setting says so", c.js("!document.querySelector('.read').hidden"), c.js("document.querySelector('.read').textContent"))
    shot.restore()
    say(f"interaction: {sum(ok)} of {len(ok)} checks passed")


def run_spikes():
    out = []
    for script, name in (("shell_spike_window.py", "spike-window.json"), ("shell_spike_desktop.py", "spike-desktop.json")):
        f = OUT / name
        f.unlink(missing_ok=True)
        r = subprocess.run([str(PY), str(HERE.parent / "sandbox_window.py"), "run", "--name", "shellspike-" + name[6:-5], "python",
                            str(HERE / script), str(f)], capture_output=True, text=True, timeout=60)
        end = time.time() + 90
        while not f.is_file() and time.time() < end:
            time.sleep(1)
        time.sleep(1)
        out.append((name, f.read_text(encoding="utf-8") if f.is_file() else None, r.stdout.strip().splitlines()[-1:]))
    say("spike 1, window shape (hidden desktop, WebView2 in pywebview; evidence/shell/spike-window.json and four PNGs):")
    try:
        d = json.loads(out[0][1])
        for k, v in d.items():
            if not isinstance(v, dict):
                continue
            p = v.get("paint", {})
            say(f"  {k}: corner pixel in the window's own paint {tuple(p.get('corner', ()))}; hit test at the corner passes to the window behind: "
                f"{v.get('hit_test_corner_is_backing')}, at the centre reaches this window: {v.get('hit_test_centre_is_this_window')}; "
                f"layered={v.get('layered', {}).get('ex_layered')} key={v.get('layered', {}).get('colorkey_bgr')}; blended edge pixels per corner {p.get('blended_pixels_in_one_corner')}")
    except Exception as exc:                  # noqa: BLE001
        say(f"  spike 1 did not produce a result: {exc!r}")
    say("spike 2, WorkerW desktop layer (hidden desktop, evidence/shell/spike-desktop.json):")
    try:
        d = json.loads(out[1][1])
        for k, v in d.items():
            say(f"  {k}: {v}")
    except Exception as exc:                  # noqa: BLE001
        say(f"  spike 2 did not produce a result: {exc!r}")
    say("live desktop structure, read-only (no message sent): " + live_survey())


def live_survey():
    import ctypes
    from ctypes import wintypes as wt
    u = ctypes.WinDLL("user32")
    u.GetClassNameW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
    P = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    u.EnumWindows.argtypes = [P, wt.LPARAM]
    u.EnumChildWindows.argtypes = [wt.HWND, P, wt.LPARAM]
    u.GetParent.argtypes = [wt.HWND]
    u.GetParent.restype = wt.HWND
    cls = lambda h: (lambda b: (u.GetClassNameW(h, b, 80), b.value)[1])(ctypes.create_unicode_buffer(80))
    prog, workers = [], []

    @P
    def each(h, _):
        c = cls(h)
        if c == "Progman":
            prog.append(h)
        elif c == "WorkerW":
            workers.append(h)
        return True
    u.EnumWindows(each, 0)
    kids = []
    for p in prog:
        @P
        def kid(c, _):
            if u.GetParent(c) == p:
                kids.append(cls(c))
            return True
        u.EnumChildWindows(p, kid, 0)
    visible = sum(1 for w in workers if u.IsWindowVisible(w))
    return (f"Progman present: {bool(prog)}; its direct children: {kids}; WorkerW top-level windows: {len(workers)} of which visible: {visible}. "
            f"So SHELLDLL_DefView is Progman's own child (the 24H2 structure), not inside a WorkerW")


def main(argv):
    which = argv[1] if len(argv) > 1 else "all"
    OUT.mkdir(parents=True, exist_ok=True)
    srv, base = serve()
    shot = None
    t0 = time.time()
    try:
        if which in ("all", "spikes"):
            run_spikes()
        if which in ("all", "looks", "popovers", "dock", "a11y", "interact", "seam"):
            shot = Shot(base)
            for name, fn in (("looks", looks), ("popovers", popovers), ("dock", dock_sets), ("seam", seam), ("a11y", a11y), ("interact", interact)):
                if which in ("all", name):
                    fn(shot)
    finally:
        if shot:
            shot.close()
        srv.shutdown()
    (OUT / "proof-output.txt").write_text("\n".join(SHOWN) + f"\n(ran in {time.time() - t0:.0f} s)\n", encoding="utf-8")
    print(f"done in {time.time() - t0:.0f} s; output in evidence/shell/proof-output.txt")


if __name__ == "__main__":
    main(sys.argv)
