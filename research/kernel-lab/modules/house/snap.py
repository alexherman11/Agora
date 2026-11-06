"""EDITING A MODULE (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
A module is a seam to something outside the kernel (a model provider, git, Twitch, the media session, a map server) and
turns it into world facts and words. What the world does with them (who is told, when, in what words, how it looks)
belongs in rules, lenses and this module's settings thing, read at each use. Names (JEFF, Alex), ids (dk...), models,
counts, timeouts and message text in this file are debt: move them to settings when you touch them, and never add more.

snap: a picture of a world thing the way it shows in a window on Alex's desktop, taken where nobody sees it.

    snap(what, token, out, *, door='http://127.0.0.1:8810', source=None, world=None, size=(1280, 800), wait=4)
        -> {'path': out, 'shown': <the page's URL, no token>, 'detail': <short text>}

A resident can only see and do through the door, so it cannot look at what it built. This takes the look for it: the
House word `house.snap <thing>` calls snap() and answers with a line `[image: <path>]`, which the MCP door adapter
(kernel-lab/mcp/agora_mcp.py) turns into an image the model sees.

`what` is a world thing id (a window, a lens, a widget, or any other thing), a lens name, or a desktop path
(`/desk/...` or `/lens.html?...`). The page is the one the window module would open for it (kd_window.py _open):
    a window thing   its own page: /desk/frame.html?lens=..., /desk/widget.html?widget=..., /desk/<view>.html, shell bars
    a lens           /desk/widget.html?widget=<w> when a component widget paints it (as window.open <lens> does),
                     else /desk/frame.html?lens=<name>&name=<title>
    a widget         /desk/widget.html?widget=<id>
    anything else    /desk/thing.html?target=<id> (what `window.open thing <id>` shows)
The page is loaded straight from the door (not through /desk/window-origin, which only the owner may use).

Who looks. `token` is the caller's own bearer token. It is set as the session cookie inside the hidden browser (over
DevTools, never in a URL), so the page shows what the caller may see, as the caller. It is never printed, logged or
returned.

Two modes, nothing on the screen in either:
    source=None       the live door, read-only: headless Chrome/Edge on a throwaway profile (shoot.browser), and every
                      request that could write is failed inside the browser before it leaves (any POST but /see and
                      the widget door's reading calls; anything not on loopback). The world is only read.
    source=<checkout> what that unlanded code would look like: a throwaway copy of the live world (`world`, default
                      the live world dir: its log, keep and blobs, as sandbox.py `fresh` copies) in a temp folder, a
                      kdesk from *that tree's* code on a free port (as sandbox.py `run`: window, system and media
                      --headless; theme, board and files as they are; every other module off, so no model, house,
                      window manager or guy), shot, then the kdesk and its whole process tree are ended (taskkill /T
                      on the pid started here) and the copy deleted, whatever happened.
Paint readiness is bounded by 90 s overall. A missed deadline returns a labelled picture;
capturing it has a separate bounded allowance. Transport failures raise RuntimeError with a plain reason.

    python snap.py <what> <out.png> --token-file <file> [--source <tree>] [--door URL] [--size 1280x800] [--wait 4]
"""
import argparse
import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]                                   # research/kernel-lab
ROOT = LAB.parents[1]                                   # the checkout this file is in
DESK_REL = Path("research") / "window-lab" / "kernel-desktop"
LIVE_WORLD = ROOT / DESK_REL / "state" / "world"
PY = ROOT / ".venv" / "Scripts" / "python.exe"
if not PY.is_file():
    # Worker trees share the interpreter running their checks, as kdesk.py does.
    PY = Path(sys.prefix) / "Scripts" / "python.exe"
NO_WINDOW = 0x08000000
LIMIT = 90.0                                            # seconds, for the whole snap

VENV_SITE = ROOT / ".venv" / "Lib" / "site-packages"
if VENV_SITE.exists() and str(VENV_SITE) not in sys.path:
    sys.path.append(str(VENV_SITE))          # the House runs on the base interpreter; websockets is the venv's (kd_window)
sys.path.insert(0, str(LAB))
import shoot  # noqa: E402  (headless browser on a throwaway profile)
from kernel import scratch  # noqa: E402  (temp folders a sandboxed worker can write to)

VIEWS = ("lines", "thing", "help", "tasks", "taskbar")  # kd_window.VIEWS
SHELL_VIEWS = {"shell-top": "top", "shell-dock": "dock", "shell-desktop": "desktop"}   # kd_window.SHELL_VIEWS
# the widget door's calls that only read (kdesk widgets.py): open/close/poll an instance; project/see/... as `call` ops
WIDGET_READS = {"open", "close", "poll"}
WIDGET_READ_OPS = {"project", "see", "file-check", "hear", "theme"}


def _q(v):
    return urllib.parse.quote(str(v), safe="")


def _loopback(url):
    u = urllib.parse.urlsplit(url)
    return u.scheme == "http" and u.hostname in ("127.0.0.1", "localhost", "::1") and not u.username


# ---- which page ---------------------------------------------------------------------------------------------------

def _see(door, token, line, timeout=15):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    req = urllib.request.Request(door.rstrip("/") + "/see", json.dumps({"line": line}).encode("utf-8"),
                                 {"Content-Type": "application/json", "Authorization": "Bearer " + token})
    try:
        with opener.open(req, timeout=timeout) as r:
            return json.load(r)
    except urllib.error.HTTPError as exc:
        try:
            out = json.loads(exc.read())
        except ValueError:
            out = {}
        return {"ok": False, "text": out.get("error") or out.get("refused") or f"the door said HTTP {exc.code}"}
    except (urllib.error.URLError, OSError, ValueError):
        return {"ok": False, "text": "the door is not answering"}


def page_for(row, widget_for_lens=None):
    """A thing's row -> (the path its window shows, what it is). Mirrors kd_window.py _open."""
    rid, kind = row.get("id", ""), row.get("kind")
    if kind == "window":
        shows, target = row.get("shows"), row.get("target")
        tail = f"&target={_q(target)}" if target else ""
        if shows in SHELL_VIEWS:
            return f"/desk/shell/{SHELL_VIEWS[shows]}.html?win={_q(rid)}", f"the {shows} shell window"
        if shows == "page":
            return str(row.get("url") or ""), "a page window"
        if row.get("widget"):
            return f"/desk/widget.html?win={_q(rid)}&widget={_q(row['widget'])}{tail}", "a component window"
        if row.get("lens") and row.get("edge"):
            return (f"/desk/bar.html?win={_q(rid)}&lens={_q(row['lens'])}&edge={_q(row['edge'])}",
                    f"the {row['edge']} bar")
        if row.get("lens"):
            return (f"/desk/frame.html?win={_q(rid)}&lens={_q(row['lens'])}&name={_q(row.get('name') or '')}",
                    "a lens window")
        view = shows if shows in VIEWS else "thing"
        return f"/desk/{view}.html?win={_q(rid)}{tail}", f"the {view} window"
    if kind == "lens":
        if widget_for_lens:
            return f"/desk/widget.html?widget={_q(widget_for_lens)}", "the lens, painted by its component widget"
        title = row.get("title") or row.get("name") or ""      # lens.js finds a lens by its title (scene.find_lens)
        return f"/desk/frame.html?lens={_q(title)}&name={_q(title)}", "the lens in a window frame"
    if kind == "widget":
        return f"/desk/widget.html?widget={_q(rid)}", "the widget"
    return f"/desk/thing.html?target={_q(rid)}", f"the {kind or 'thing'} in the Thing window"


def resolve(what, door, token):
    """-> (path, what it is) for `what`, read as the caller."""
    what = str(what).strip()
    if not what:
        raise RuntimeError("snap needs a thing: an id, a lens name, or a /desk/ path")
    if what.startswith("/"):
        if not (what.startswith("/desk/") or what.startswith("/lens.html")):
            raise RuntimeError("a path must be a desktop page: /desk/... or /lens.html?...")
        return what, "a desktop page"
    row = None
    if " " not in what and "=" not in what:
        got = _see(door, token, f"look {what}")
        rows = [r for r in got.get("rows") or [] if isinstance(r, dict) and r.get("id") == what]
        row = rows[0] if rows else None
    if row is None:
        got = _see(door, token, f"rows lens name={json.dumps(what)}")
        rows = [r for r in got.get("rows") or [] if isinstance(r, dict)]
        row = rows[0] if rows else None
    if row is None:
        raise RuntimeError(f"there is no thing {what} that you can see (look {what} found nothing)")
    widget = None
    if row.get("kind") == "lens":
        # window.open <lens> paints it with the component widget that shows it, when one is on (kd_window.py)
        name = json.dumps(str(row.get("name") or ""))
        for line in (f"rows widget component_lens={name}", f"rows widget name={name}"):
            got = _see(door, token, line)
            widget = next((w["id"] for w in got.get("rows") or [] if isinstance(w, dict) and w.get("code")
                           and w.get("on") and (w.get("surface") or "window") == "window"), None)
            if widget:
                break
    path, label = page_for(row, widget)
    if not path:
        raise RuntimeError(f"{what} has no page to show")
    if row.get("kind") == "lens" and not widget and row.get("painter") == "components":
        label += " (a components lens with no widget showing it: lens.js may refuse to paint it)"
    return path, label


# ---- the hidden browser -------------------------------------------------------------------------------------------

TEXT = ("[document.body ? document.body.innerText : ''].concat([...document.querySelectorAll('iframe')].map(f => "
        "{ try { return f.contentDocument.body.innerText } catch (e) { return '' } })).join(' ')")

UNMARKED_PAINT = "painted (no first-paint marker)"
FRAME_CONTENT = """(() => {
    const parts = [];
    for (const el of document.body ? [document.body, ...document.body.querySelectorAll('*')] : []) {
        if (el.matches('script, style, template, noscript')) continue;
        const rect = el.getBoundingClientRect();
        if (rect.width <= 0 || rect.height <= 0 || rect.bottom <= 0 || rect.right <= 0 ||
            rect.top >= innerHeight || rect.left >= innerWidth) continue;
        let hidden = false;
        for (let node = el; node; node = node.parentElement) {
            const style = getComputedStyle(node);
            if (style.display === 'none' || style.visibility !== 'visible' || Number(style.opacity) === 0) {
                hidden = true; break;
            }
        }
        if (hidden) continue;
        const text = [...el.childNodes].filter(n => n.nodeType === Node.TEXT_NODE)
            .map(n => n.textContent.trim()).join('');
        const media = (el.matches('img') && el.complete && el.naturalWidth > 0) ||
            (el.matches('svg') && el.children.length > 0) || el.matches('canvas, video, input, select, textarea');
        if (text || media) parts.push([el.tagName, text, el.currentSrc || '', el.value || '',
            rect.x, rect.y, rect.width, rect.height]);
    }
    return parts.length ? JSON.stringify(parts) : '';
})()"""


async def _frame_painted(call):
    """None for ordinary pages; otherwise a marker bool or visible-content signature in the frame."""
    result = await call("Runtime.evaluate", expression=(
        "document.querySelector('#widget-surface') ? "
        "(document.querySelector('#widget-surface').dataset.components || 'pending') : 'false'"),
        returnByValue=True)
    if result.get("result", {}).get("value") == "false":
        return None
    if result.get("result", {}).get("value") != "true":
        return False
    tree = await call("Page.getFrameTree")

    def widget_frame(node):
        if node.get("frame", {}).get("name") == "agora-widget":
            return node["frame"]["id"]
        return next((found for child in node.get("childFrames", [])
                     if (found := widget_frame(child))), None)

    frame = widget_frame(tree.get("frameTree", {}))
    if not frame:
        return False
    try:
        context = await call("Page.createIsolatedWorld", frameId=frame, worldName="agora-snap")
        result = await call("Runtime.evaluate", contextId=context["executionContextId"],
                            expression="document.documentElement.dataset.painter === 'components'",
                            returnByValue=True)
        if result.get("result", {}).get("value") is True:
            return True
        result = await call("Runtime.evaluate", contextId=context["executionContextId"],
                            expression=FRAME_CONTENT, returnByValue=True)
        content = result.get("result", {}).get("value")
        # Include the context so replacing a frame restarts the stability interval.
        return f"{context['executionContextId']}:{content}" if isinstance(content, str) and content else False
    except RuntimeError:
        # The host may replace a frame while starting/recovering. Try the current frame on the next poll.
        return False


async def _wait_for_paint(probe, deadline, *, clock=time.monotonic, sleep=asyncio.sleep):
    """Prefer the marker; older painters may instead show stable content for three seconds."""
    last, still = False, clock()
    while (remaining := deadline - clock()) > 0:
        try:
            painted = await asyncio.wait_for(probe(), remaining)
        except asyncio.TimeoutError:
            return False
        if painted is True or painted is None:
            return painted
        now = clock()
        if painted != last:
            last, still = painted, now
        if painted and now - still >= 3:
            return UNMARKED_PAINT
        await sleep(min(0.25, max(0, deadline - clock())))
    return False


def _label_picture(out, label):
    """Keep a deadline picture useful even when it is detached from its accompanying text."""
    from PIL import Image, ImageDraw
    with Image.open(out) as source:
        picture = source.convert("RGB")
    draw = ImageDraw.Draw(picture)
    bounds = draw.textbbox((12, 10), label)
    draw.rectangle((0, 0, picture.width, bounds[3] + 12), fill="#fff4ce")
    draw.text((12, 10), label, fill="#302600")
    picture.save(out)


def _read_only_allows(method, url, body):
    """In live mode: may this request leave the browser? Reads only, loopback only."""
    u = urllib.parse.urlsplit(url)
    if u.scheme in ("data", "blob", "about"):
        return True
    if not _loopback(url):
        return False
    if method in ("GET", "HEAD", "OPTIONS"):
        return True
    if method != "POST":
        return False
    if u.path in ("/see", "/api/style", "/api/observe"):     # a reading; the painter's style; a report the kernel drops
        return True
    if u.path.startswith("/desk/widget/"):
        action = u.path.rsplit("/", 1)[-1]
        if action in WIDGET_READS:
            return True
        try:
            op = json.loads(body or "").get("op")
        except (ValueError, AttributeError):
            return False
        return op in WIDGET_READ_OPS
    return False


async def _shoot(ws_url, url, origin, token, out, size, wait, read_only, host_key, budget):
    import websockets
    w, h = size
    loop = asyncio.get_running_loop()
    pending, state = {}, {"n": 0, "blocked": 0}
    deadline = time.monotonic() + max(0, budget)

    async with websockets.connect(ws_url, max_size=64 * 1024 * 1024) as ws:
        async def call(method, **params):
            state["n"] += 1
            n = state["n"]
            fut = loop.create_future()
            pending[n] = fut
            await ws.send(json.dumps({"id": n, "method": method, "params": params}))
            msg = await asyncio.wait_for(fut, 20)
            if "error" in msg:
                raise RuntimeError(f"the hidden browser refused {method}")     # never echo params (the cookie)
            return msg.get("result", {})

        async def paused(p):
            req = p.get("request") or {}
            try:
                if read_only and not _read_only_allows(req.get("method", "GET"), req.get("url", ""), req.get("postData")):
                    state["blocked"] += 1
                    await call("Fetch.failRequest", requestId=p["requestId"], errorReason="BlockedByClient")
                else:
                    await call("Fetch.continueRequest", requestId=p["requestId"])
            except (RuntimeError, asyncio.TimeoutError, websockets.ConnectionClosed):
                pass

        async def reader():
            async for raw in ws:
                msg = json.loads(raw)
                if "id" in msg:
                    fut = pending.pop(msg["id"], None)
                    if fut and not fut.done():
                        fut.set_result(msg)
                elif msg.get("method") == "Fetch.requestPaused":
                    asyncio.ensure_future(paused(msg["params"]))

        async def js(expr):
            r = await call("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=True)
            return (r.get("result") or {}).get("value")

        async def run():
            await call("Fetch.enable", patterns=[{"urlPattern": "*", "requestStage": "Request"}])
            await call("Network.enable")
            await call("Network.setCookie", name="agora_session", value=token, url=origin + "/", httpOnly=True,
                       sameSite="Lax")
            if host_key:
                await call("Network.setExtraHTTPHeaders", headers={"X-Agora-Widget-Host": host_key})
            await call("Emulation.setDeviceMetricsOverride", width=w, height=h, deviceScaleFactor=1, mobile=False)
            await call("Page.enable")
            nav = await call("Page.navigate", url=url)
            if nav.get("errorText"):
                raise RuntimeError(f"the page did not load ({nav['errorText']})")
            end = time.monotonic() + 15
            while time.monotonic() < end:
                if await js("document.readyState === 'complete' && [...document.querySelectorAll('iframe')]"
                            ".every(f => { try { return !f.contentDocument || f.contentDocument.readyState === "
                            "'complete' } catch (e) { return true } })"):
                    break
                await asyncio.sleep(0.2)
            painted = await _wait_for_paint(lambda: _frame_painted(call), deadline)
            if painted is not None:
                return painted
            # then at least `wait` seconds, and until what the page says has stopped changing for a second (a lens
            # paints after its scene arrives, which a busy kernel can take a while to send). A page that still says
            # next to nothing (a lens not painted yet; a component widget, whose sandboxed frame cannot be read)
            # gets up to 4 s more, a page still changing up to 10 s more.
            began, last, still = time.monotonic(), None, time.monotonic()
            while True:
                said = await js(TEXT)
                now = time.monotonic()
                if said != last:
                    last, still = said, now
                settled = now - still >= 1.0 and (len(" ".join(str(said).split())) > 40 or now - began >= wait + 4)
                if now - began >= wait and (settled or now - began >= wait + 10):
                    break
                await asyncio.sleep(0.25)
            return True

        async def capture():
            nonlocal painted
            if painted is False:
                # The outer readiness timeout can interrupt the last poll. Check the actual frame
                # again at capture time, within the capture allowance, even if it has not settled.
                try:
                    observed = await asyncio.wait_for(_frame_painted(call), 2)
                    if observed:
                        painted = True if observed is True else UNMARKED_PAINT
                except asyncio.TimeoutError:
                    pass
            # Edge/Chrome's software compositor can hand back a stale tile right after a load: take one, let two
            # frames pass, keep the next (hidden_evidence.py does the same)
            await call("Page.captureScreenshot", format="png", fromSurface=True)
            await js("new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")
            shot = await call("Page.captureScreenshot", format="png", fromSurface=True)
            import base64
            Path(out).write_bytes(base64.b64decode(shot["data"]))
            text = await js(TEXT)
            return " ".join(str(text or "").split()), state["blocked"]

        task = asyncio.ensure_future(reader())
        try:
            try:
                painted = await asyncio.wait_for(run(), max(0, budget))
            except asyncio.TimeoutError:
                painted = False
            # Readiness may use the entire deadline; still allow a bounded capture of what actually appeared.
            try:
                text, blocked = await asyncio.wait_for(capture(), 20)
            except asyncio.TimeoutError:
                raise RuntimeError("the hidden browser took too long to capture the picture")
            return text, blocked, painted
        finally:
            task.cancel()


def _shot(url, origin, token, out, size, wait, read_only, host_key, deadline):
    with shoot.browser() as ws_url:
        return asyncio.run(_shoot(ws_url, url, origin, token, out, size, wait, read_only, host_key,
                                  deadline - time.monotonic()))


# ---- the hidden copy, from a source tree --------------------------------------------------------------------------

RUNNER = r'''
import json, os, sys, time
from pathlib import Path
desk, world, ready, live_root = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4])
src_root = desk.parents[2]
sys.path.insert(0, str(desk))
os.chdir(desk)
import kdesk
from kernel.kernel import Tx
HEADLESS, KEEP = {"window", "system", "media"}, {"theme", "board", "files"}

def moved(arg):
    """A module's path inside the live checkout -> the same file in the source tree (the interpreter stays)."""
    p = Path(str(arg))
    if not p.is_absolute():
        return arg
    try:
        rel = p.resolve().relative_to(live_root)
    except ValueError:
        return arg
    if rel.parts[:1] == (".venv",):
        return arg
    q = src_root / rel
    return str(q) if q.exists() else arg

k, srv, host, entry = kdesk.start(world, 0, modules=False, headless=True)
ran = []
with k.lock:
    tx = Tx(k)
    tx.part("install", None, "install")
    n = 0
    for m in k.things("module"):
        name, argv, on = k.state.get(m, "name"), list(k.state.get(m, "run") or []), bool(k.state.get(m, "on"))
        if on and name in HEADLESS | KEEP:
            want = [moved(a) for a in argv if a != "--allow-live"]
            if name in HEADLESS and "--headless" not in want:
                want.append("--headless")
            if want != argv:
                tx.set(m, "run", want); n += 1
            ran.append(name)
        elif on:
            tx.set(m, "on", False); n += 1
    if n:
        k._commit(tx, by="kernel", words="snap: a hidden copy; modules headless from the source tree, the rest off")
host.reconcile()
for mid in list(host.procs):
    host.wait_offered(mid, 15)
tmp = ready.with_suffix(".tmp")
runs = {k.state.get(m, "name"): k.state.get(m, "run") for m in k.things("module") if k.state.get(m, "on")}
tmp.write_text(json.dumps({"port": srv.server_address[1], "key": srv.RequestHandlerClass.widget_broker.guard_key,
                           "modules": ran, "runs": runs, "kdesk": kdesk.__file__, "records": len(k.log.records)}),
               encoding="utf-8")
os.replace(tmp, ready)
while True:
    time.sleep(2)
    host.reconcile()
'''

# what the hidden kdesk must not inherit from a live kdesk/house parent: the keeper's link (it would adopt the live
# ports and modules), the live door's port, its widget key, any agent credential
SCRUB = ("AGORA_KEEPER", "AGORA_KDESK_PORT", "AGORA_WIDGET_HOST_KEY", "AGORA_BEARER_TOKEN", "AGORA_SESSION",
         "AGORA_URL", "HOUSE_FAKE_MODEL")


def _copy_world(world, dst):
    """sandbox.py `fresh`, into a temp folder: the log, the keep (accounts, seal, sessions, managers) and blobs."""
    world = Path(world)
    if not (world / "log" / "0001.jsonl").is_file():
        raise RuntimeError(f"{world} is not a kernel world (no log)")
    shutil.copytree(world / "log", dst / "log")
    (dst / "keep").mkdir(parents=True)
    for f in ("accounts.json", "seal.key", "sessions.json", "house-managers.json"):
        if (world / "keep" / f).exists():
            shutil.copy2(world / "keep" / f, dst / "keep" / f)
    if (world / "blobs").is_dir():
        shutil.copytree(world / "blobs", dst / "blobs")


def _kill_tree(proc):
    if proc.poll() is None:
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True, creationflags=NO_WINDOW)
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        pass


class Sandbox:
    """A hidden kdesk from `source`'s code over a throwaway copy of `world`. A context manager; always cleans up."""

    def __init__(self, source, world, deadline):
        self.source = Path(source).resolve()
        self.desk = self.source / DESK_REL
        if not (self.desk / "kdesk.py").is_file():
            raise RuntimeError(f"{source} is not an Agora checkout (no {DESK_REL.as_posix()}/kdesk.py)")
        self.world, self.deadline = Path(world), deadline
        self.tmp = self.proc = self.logf = None

    def __enter__(self):
        try:
            self.tmp = Path(scratch.mkdtemp(prefix="agora-snap-"))
            _copy_world(self.world, self.tmp / "world")
            (self.tmp / "runner.py").write_text(RUNNER, encoding="utf-8")
            ready = self.tmp / "ready.json"
            env = {k: v for k, v in os.environ.items() if k not in SCRUB}
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            self.logf = open(self.tmp / "kdesk.log", "w", encoding="utf-8")
            self.proc = subprocess.Popen([str(PY), str(self.tmp / "runner.py"), str(self.desk), str(self.tmp / "world"),
                                          str(ready), str(ROOT.resolve())], cwd=str(self.desk), env=env,
                                         stdin=subprocess.DEVNULL, stdout=self.logf, stderr=subprocess.STDOUT,
                                         creationflags=NO_WINDOW)
            while not ready.exists():
                if self.proc.poll() is not None:
                    raise RuntimeError("the hidden desk from that source stopped while starting: " + self._tail())
                if time.monotonic() > self.deadline - 15:
                    raise RuntimeError("the hidden desk from that source did not start in time")
                time.sleep(0.2)
            info = json.loads(ready.read_text(encoding="utf-8"))
            self.url, self.key, self.info = f"http://127.0.0.1:{info['port']}", info.get("key"), info
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def _tail(self):
        try:
            self.logf.flush()
            lines = (self.tmp / "kdesk.log").read_text(encoding="utf-8", errors="replace").strip().splitlines()
            return " | ".join(lines[-3:])[-400:] or "(it said nothing)"
        except OSError:
            return "(no log)"

    def __exit__(self, *exc):
        if self.proc is not None:
            _kill_tree(self.proc)
        if self.logf is not None:
            self.logf.close()
        if self.tmp is not None:
            for _ in range(20):
                shutil.rmtree(self.tmp, ignore_errors=True)
                if not self.tmp.exists():
                    break
                time.sleep(0.3)
        return False


# ---- the word -----------------------------------------------------------------------------------------------------

def snap(what, token, out, *, door="http://127.0.0.1:8810", source=None, world=None, size=(1280, 800), wait=4):
    """A hidden picture of `what` as its window shows it -> {'path', 'shown', 'detail'}. See the module's words."""
    started = time.monotonic()
    deadline = started + LIMIT
    if not token or any(c in token for c in "\r\n;"):
        raise RuntimeError("snap needs the caller's session token")
    if not _loopback(door):
        raise RuntimeError("the door must be a loopback http address")
    w, h = (int(x) for x in size)
    if not (200 <= w <= 4000 and 150 <= h <= 4000):
        raise RuntimeError("size must be between 200x150 and 4000x4000")
    wait = max(0.0, min(float(wait), 20.0))
    out = str(Path(out).resolve())
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    box = Sandbox(source, world or LIVE_WORLD, deadline) if source else None
    try:
        if box:
            box.__enter__()
        base = box.url if box else door.rstrip("/")
        host_key = box.key if box else os.environ.get("AGORA_WIDGET_HOST_KEY")
        path, label = resolve(what, base, token)
        url = path if path.startswith("http") else base + path
        if not _loopback(url):
            raise RuntimeError("that window shows a page that is not on this machine")
        origin = "{0.scheme}://{0.netloc}".format(urllib.parse.urlsplit(url))
        text, blocked, painted = _shot(url, origin, token, out, (w, h), wait, read_only=box is None,
                                       host_key=host_key, deadline=deadline)
    finally:
        if box:
            box.__exit__(None, None, None)
    if not Path(out).is_file() or Path(out).stat().st_size == 0:
        raise RuntimeError("no picture was taken")
    paint_status = painted if painted == UNMARKED_PAINT else ("" if painted else f"not painted after {LIMIT:g} s")
    if paint_status:
        _label_picture(out, paint_status)
    where = f"from {Path(source).name} (a hidden copy of the world)" if box else "live, read-only"
    said = text[:240] + ("…" if len(text) > 240 else "")
    detail = (f"{label}, {w}x{h}, {where}, {time.monotonic() - started:.1f} s"
              + (f"; {paint_status}" if paint_status else "")
              + (f"; {blocked} writes held back" if blocked else "")
              + (f"; widgets cannot paint here (no desktop host key)" if not host_key and "widget" in path else "")
              + (f"; the page says: {said}" if said else "; the page shows no text"))
    return {"path": out, "shown": url, "detail": detail, "paint_status": paint_status}


def main():
    ap = argparse.ArgumentParser(description="a hidden picture of a world thing as its window shows it")
    ap.add_argument("what")
    ap.add_argument("out")
    ap.add_argument("--token-file", required=True, help="a file holding the caller's session token (never printed)")
    ap.add_argument("--source", help="a checkout (e.g. a worker's worktree): shoot its code over a copy of the world")
    ap.add_argument("--world", help="the world the copy is made from (default: the live desktop world)")
    ap.add_argument("--door", default="http://127.0.0.1:8810")
    ap.add_argument("--size", default="1280x800")
    ap.add_argument("--wait", type=float, default=4)
    a = ap.parse_args()
    token = Path(a.token_file).read_text(encoding="utf-8").strip()
    try:
        got = snap(a.what, token, a.out, door=a.door, source=a.source, world=a.world,
                   size=tuple(int(x) for x in a.size.lower().split("x")), wait=a.wait)
    except RuntimeError as exc:
        sys.exit(f"snap: {exc}")
    print(json.dumps(got, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
