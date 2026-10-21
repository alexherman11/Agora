"""seam_browser.py (a7950): the living map's seam in real browsers, on hud_playtest's disposable copy. Never the live
world, never Alex's screen, no Conversation send. Both halves run on the sandbox desktop under the guard.

    python research/window-lab/living-map/seam_browser.py [--edge-only | --bridge-only]

A, hidden Edge (hud_playtest.Window): map-host.html holds the stand-in frame (desk-shell/map/standin.html) over pins
  and a route made in the copy. (1) a pin's lat changed by line reaches what the frame is sent; (2) the frame's 'move'
  (pressed as a hand presses: Windows messages) is one undoable event, and a move from an old revision is refused and
  overwrites nothing; (3) the route is sent in order, and still after a pin is renamed; (4) messages from the wrong
  origin or window, and the stand-in's #probe battery (channel, op, NaN, Infinity, range, unknown thing, command
  strings, a bare string, an array), are each refused, and the frame's own request to the desk is refused too.
B, a pywebview window with a js_api bridge, as the home base has (bridge_page.py): (5) the frame tries the bridge by
  every road (its own window, its parent, chrome.webview.postMessage in the bridge's own format); only the top page's
  control call reaches Python.
Reports: research/window-lab/demos/living-map/<time>-seam/ (report.json, shots).
"""
import argparse
import asyncio
import datetime
import json
import re
import sys
import time
import traceback
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
sys.path.insert(0, str(LAB))
import hud_playtest as pt  # noqa: E402

DEMOS = Path(r"C:/Projects/Agora4/research/window-lab/demos/living-map")
ME = "worker-a7950"
STATE = "JSON.stringify(window.__mapHost || null)"


def fixture(copy):
    """Synthetic pins and a route in a surface of their own, in the copy only (a7875: real pins wait for verified
    coordinates). -> {surface, p1, p2, p3, route}"""
    def made(line):
        said = copy.do(line, ME)
        m = re.search(r"created ([af]\d+)", said)
        if not m:
            raise SystemExit(f"fixture: {line[:80]} -> {said[:300]}")
        return m.group(1)
    kinds = copy.do("find kind:note,tags:kind", ME)
    have = {k: (f'"{k}"' in kinds) for k in ("pin", "route")}
    root = re.search(r"\b(f\d+)\b", copy.do("look", ME))
    if not root:
        raise SystemExit("fixture: look names no surface to make the check in")
    copy.do(f"look {root.group(1)}", ME)
    f = made(f'do create {root.group(1)} kind=surface title="Living map seam check (synthetic)"')
    copy.do(f"look {f}", ME)
    for k in ("pin", "route"):
        if not have[k]:
            made(f'do create {f} kind=note title={k} tags=kind is=note text="(copy only)"')
    out = {"surface": f, "kinds here before": have, "root": root.group(1) if root else None}
    out["p1"] = made(f'do create {f} kind=pin title="Synthetic one" lat=51.5194 lon=-0.127 label="Synthetic one"')
    out["p2"] = made(f'do create {f} kind=pin title="Synthetic two" lat=51.518 lon=-0.126 label="Synthetic two" colour=teal')
    out["p3"] = made(f'do create {f} kind=pin title="Synthetic three" lat=51.52 lon=-0.125 label="Synthetic three"')
    out["route"] = made(f'do create {f} kind=route title="Synthetic walk" label="Synthetic walk" text="{out["p2"]}\\n{out["p1"]}\\n{out["p3"]}"')
    return out


def props(copy, nid):
    said = copy.do(f"examine {nid}", ME)
    # the thing's own line (a receipt may open with '!! since your last look ...')
    first = next((l for l in said.splitlines() if l.strip().startswith(f"{nid} ")), "")
    return dict(re.findall(r"(\w+)=(\S+)", first))


def frame_target(port, words, secs=10):
    """A DevTools connection to the out-of-process frame whose address holds `words` (sandbox_window.Cdp, aimed at an
    iframe target instead of the page)."""
    import sandbox_window as SB
    from websockets.sync.client import connect
    import urllib.request
    t0 = time.time()
    while True:
        tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=5).read())
        t = next((t for t in tabs if t.get("type") == "iframe" and words in t.get("url", "")), None)
        if t or time.time() - t0 > secs:
            break
        time.sleep(0.3)
    if not t:
        raise LookupError(f"no frame target for {words}: {[(x.get('type'), x.get('url', '')[:60]) for x in tabs]}")
    c = SB.Cdp.__new__(SB.Cdp)
    c.ws, c.n = connect(t["webSocketDebuggerUrl"], origin=None, max_size=16 * 1024 * 1024), 0
    return c


class Run:
    def __init__(self, out):
        self.out, self.rows, self.shots = out, [], 0

    def record(self, jid, outcome, note, facts=None, shots=()):
        self.rows.append({"id": jid, "outcome": outcome, "note": note, "facts": facts or {}, "shots": list(shots)})
        print(f"  {outcome:<8} {jid:<26} {note[:200]}", flush=True)


async def edge(R, copy, fx):
    win = pt.Window(False)
    guard = None
    try:
        url = f"{copy.base}/map-host.html?" + urllib.parse.urlencode({"session": copy.session, "as": "alex", "scope": fx["surface"]})
        await win.open(url)

        async def host():
            try:
                return json.loads(await win.js(STATE) or "null")
            except Exception:              # the page is between loads (the probe reloads it)
                return None

        async def until(pred, secs=8.0):
            t = time.time()
            while time.time() - t < secs:
                h = await host()
                if h and pred(h):
                    return h
                await asyncio.sleep(0.2)
            return await host()

        async def shot(name):
            R.shots += 1
            p = R.out / f"{R.shots:02d}-{name}.png"
            await win.shot(p)
            return p.name

        h = await until(lambda h: h["draws"] >= 1 and h["last"], 15)
        page = await win.js("[innerWidth, innerHeight, devicePixelRatio]")
        R.record("ready", "ran" if h and h["draws"] else "fail", f"page {page}, draws {h and h['draws']}, problems {h and h['problems']}",
                 {"page": page, "first draw": h and h["last"]}, [await shot("ready")])

        # the frame's DOM, read by DevTools (rects and data attributes only; nothing in it is called or changed). A
        # sandboxed frame is its own process in Chromium (an out-of-process frame), so it is its own DevTools target;
        # a frame kept in the page's process is reached through an isolated world instead
        tree = await win.p.call("Page.getFrameTree")
        kids = tree["frameTree"].get("childFrames") or []
        fcdp = None
        if not kids:
            import sandbox_window as SB
            port = json.loads(SB.state_file(win.name).read_text(encoding="utf-8"))["port"]
            fcdp = frame_target(port, "map/standin.html")
        R.frame_process = "its own (out-of-process frame)" if fcdp else "the page's"

        async def in_frame(expr):
            if fcdp:
                return fcdp.js(expr)
            ctx = (await win.p.call("Page.createIsolatedWorld", frameId=kids[0]["frame"]["id"], worldName="a7950"))["executionContextId"]
            r = await win.p.call("Runtime.evaluate", expression=expr, contextId=ctx, returnByValue=True)
            return r.get("result", {}).get("value")

        async def press(sel, what):
            box = await win.js("(() => { const b = document.querySelector('iframe.map-frame').getBoundingClientRect(); return [b.left, b.top]; })()")
            r = await in_frame(f"(() => {{ const e = document.querySelector({json.dumps(sel)}); if (!e) return null; e.scrollIntoView({{block: 'nearest'}}); const b = e.getBoundingClientRect(); return [b.left + b.width / 2, b.top + b.height / 2]; }})()")
            if not r:
                raise LookupError(f"nothing to press in the frame: {what}")
            await win.click(box[0] + r[0], box[1] + r[1])

        p1, p2, p3, route = fx["p1"], fx["p2"], fx["p3"], fx["route"]
        sent = lambda h, pid: next((p for p in (h["last"] or {}).get("pins", []) if p["id"] == pid), None)  # noqa: E731

        # (1) lat by line -> what the frame is sent
        try:
            before = sent(h, p1)
            copy.do(f"look {p1}", ME)
            copy.do(f"do prop {p1} lat=51.5203", ME)
            h = await until(lambda h: (sent(h, p1) or {}).get("lat") == 51.5203)
            after = sent(h, p1)
            frame_sees = await in_frame(f"(document.querySelector('[data-pin=\"{p1}\"]') || {{}}).dataset?.lat || null")
            ok = after and after["lat"] == 51.5203 and after["rev"] > before["rev"] and frame_sees == "51.5203"
            R.record("1 lat by line", "pass" if ok else "fail", f"sent {before['lat']} rev {before['rev']} -> {after and after['lat']} rev {after and after['rev']}; the frame shows lat {frame_sees}",
                     {"before": before, "after": after, "frame": frame_sees}, [await shot("1-lat")])
        except Exception as e:
            R.record("1 lat by line", "error", f"{type(e).__name__}: {e}", {"trace": traceback.format_exc()[-800:]})

        # (2) a move pressed in the frame: one undoable event; a stale one refused, nothing overwritten
        try:
            n0 = copy.at()
            at = sent(await host(), p1)
            await press(f"[data-pin=\"{p1}\"] button.move", "move north")
            h = await until(lambda h: any(a["op"] == "move" for a in h["answered"]) or h["refused"])
            n1 = copy.at()
            now = props(copy, p1)
            ev = copy.do(f"history {p1}", ME).strip().splitlines()[-1]
            ans = next((a for a in reversed(h["answered"]) if a["op"] == "move"), None)
            eid = ans["events"][0] if ans and len(ans["events"]) == 1 else None
            moved = abs(float(now.get("lat", "nan")) - (at["lat"] + 0.001)) < 1e-6
            if eid:
                copy.do(f"undo {eid}", "alex")
            back = props(copy, p1)
            ok = eid and n1 == n0 + 1 and moved and abs(float(back.get("lat", "nan")) - at["lat"]) < 1e-9
            R.record("2 move is one command", "pass" if ok else "fail",
                     f"events {n0} -> {n1}; lat {at['lat']} -> {now.get('lat')} by {ev.strip()[:90]}; after undo {back.get('lat')}",
                     {"answered": h["answered"][-1:], "sent": h["sent"][-1:], "history": ev}, [await shot("2-move")])
        except Exception as e:
            R.record("2 move is one command", "error", f"{type(e).__name__}: {e}", {"trace": traceback.format_exc()[-800:]})
        try:
            h0 = await until(lambda h: (sent(h, p1) or {}).get("lat") is not None)
            draws0, n0, lat0 = h0["draws"], copy.at(), props(copy, p1).get("lat")
            refused0 = len(h0["refused"])
            await press(f"[data-pin=\"{p1}\"] button.stale", "move from an old revision")
            h = await until(lambda h: len(h["refused"]) > refused0 and h["draws"] > draws0)
            why = h["refused"][-1]["why"] if len(h["refused"]) > refused0 else None
            ok = why and "stale" in why and copy.at() == n0 and props(copy, p1).get("lat") == lat0 and h["draws"] > draws0
            R.record("2 stale move refused", "pass" if ok else "fail", f"{why!r}; events {n0} -> {copy.at()}; lat {lat0} -> {props(copy, p1).get('lat')}; drawn again {draws0} -> {h['draws']}",
                     {"refused": h["refused"][-1:]}, [await shot("2-stale")])
        except Exception as e:
            R.record("2 stale move refused", "error", f"{type(e).__name__}: {e}", {"trace": traceback.format_exc()[-800:]})

        # press views the pin; drop makes one pin in the scope (Pike c7997), one undo
        try:
            k0 = len((await host())["answered"])
            await press(f"[data-pin=\"{p1}\"] button.press", "the pin's name")
            h = await until(lambda h: len(h["answered"]) > k0)
            pressed = h["answered"][k0] if len(h["answered"]) > k0 else None
            viewing = re.search(r"\bviewing=(\S*)", "\n".join(l for l in copy.do("find prop:role=home-view,prop:actor=alex", ME).splitlines() if " note " in l))
            n0, k1 = copy.at(), len(h["answered"])
            await press("#drop", "drop a pin")
            h = await until(lambda h: len(h["answered"]) > k1 and any(p["label"] == "New pin" for p in (h["last"] or {}).get("pins", [])))
            dropped = h["answered"][k1] if len(h["answered"]) > k1 else None
            made = [p for p in (h["last"] or {}).get("pins", []) if p["label"] == "New pin"]
            n1 = copy.at()
            eid = dropped["events"][0] if dropped and len(dropped["events"]) == 1 else None
            if eid:
                copy.do(f"undo {eid}", "alex")
            h2 = await until(lambda h: not [p for p in (h["last"] or {}).get("pins", []) if p["label"] == "New pin"])
            gone = not [p for p in (h2["last"] or {}).get("pins", []) if p["label"] == "New pin"]
            ok = pressed and pressed["line"] == f"do view {p1}" and viewing and viewing.group(1) == p1 \
                and dropped and n1 == n0 + 1 and len(made) == 1 and abs(made[0]["lat"] - 51.519) < 1e-9 and gone
            R.record("press and drop", "pass" if ok else "fail",
                     f"press -> {pressed and pressed['line']}, the viewer on {viewing and viewing.group(1)}; drop -> {dropped and dropped['line']}, events {n0} -> {n1}, "
                     f"drawn {[(p['id'], p['lat'], p['lon']) for p in made]}; after undo of {eid} gone: {gone}",
                     {"pressed": pressed, "dropped": dropped, "refused": h2["refused"][-3:]}, [await shot("press-drop")])
        except Exception as e:
            R.record("press and drop", "error", f"{type(e).__name__}: {e}", {"trace": traceback.format_exc()[-800:]})

        # (3) the route, in order, and after a rename
        try:
            h = await host()
            r0 = next((r for r in h["last"]["routes"] if r["id"] == route), None)
            copy.do(f"look {p1}", ME)
            copy.do(f'do retitle {p1} title="Renamed synthetic place"', ME)
            copy.do(f"look {p1}", ME)
            copy.do(f'do prop {p1} label="Renamed synthetic place"', ME)
            h = await until(lambda h: (sent(h, p1) or {}).get("label") == "Renamed synthetic place")
            r1 = next((r for r in h["last"]["routes"] if r["id"] == route), None)
            shown = await in_frame(f"(document.querySelector('[data-route=\"{route}\"]') || {{}}).dataset?.order || null")
            want = [p2, p1, p3]
            ok = r0 and r1 and r0["pins"] == want and r1["pins"] == want and shown == ",".join(want)
            R.record("3 route in order", "pass" if ok else "fail", f"sent {r0 and r0['pins']}, after the rename {r1 and r1['pins']}; the frame shows {shown}",
                     {"before": r0, "after": r1}, [await shot("3-route")])
        except Exception as e:
            R.record("3 route in order", "error", f"{type(e).__name__}: {e}", {"trace": traceback.format_exc()[-800:]})

        # (4) origin and window: from the top page, from a same-origin frame, from a second sandboxed frame
        try:
            n0, k0 = copy.at(), len((await host())["refused"])
            msg = json.dumps({"channel": "agora-map/1", "op": "press", "id": p1})
            await win.js(f"window.postMessage({msg}, '*')")
            await win.js(f"(() => {{ const f = document.createElement('iframe'); f.srcdoc = '<script>parent.postMessage({msg.replace(chr(39), chr(92) + chr(39))}, \"*\")<' + '/script>'; document.body.appendChild(f); }})()")
            await win.js(f"(() => {{ const f = document.createElement('iframe'); f.setAttribute('sandbox', 'allow-scripts'); f.srcdoc = '<script>parent.postMessage({msg.replace(chr(39), chr(92) + chr(39))}, \"*\")<' + '/script>'; document.body.appendChild(f); }})()")
            h = await until(lambda h: len(h["refused"]) >= k0 + 3)
            whys = [r["why"] for r in h["refused"][k0:]]
            ok = sum("wrong origin" in w for w in whys) == 2 and sum("not from the map frame" in w for w in whys) == 1 and copy.at() == n0
            R.record("4 origin and window", "pass" if ok else "fail", f"{whys}; events {n0} -> {copy.at()}", {"refused": h["refused"][k0:]})
        except Exception as e:
            R.record("4 origin and window", "error", f"{type(e).__name__}: {e}", {"trace": traceback.format_exc()[-800:]})

        # (4) the stand-in's probe battery, and the frame's own request to the desk
        try:
            n0 = copy.at()
            await win.js("location.hash = 'probe'; location.reload()")
            await asyncio.sleep(1.0)
            h = await until(lambda h: any('"op":"report"' in r["data"] for r in h["refused"]), 20)
            rep = next((json.loads(r["data"]) for r in h["refused"] if '"op":"report"' in r["data"]), None)
            others = [r for r in h["refused"] if '"op":"report"' not in r["data"]]
            res = (rep or {}).get("results", {})
            desk_closed = all(str(res.get(k)) in ("403", "threw TypeError") for k in ("POST /api/do", "GET /api/map"))
            by_window = [r for r in others if "only on the port" in r["why"]]
            ok = rep and len(others) == len(rep["hostile"]) + 1 and len(by_window) == 1 and not h["answered"] and copy.at() == n0 and desk_closed
            R.record("4 probe battery", "pass" if ok else "fail",
                     f"{len(others) - len(by_window)} of {len(rep['hostile']) if rep else '?'} hostile messages on the port refused, and its press to the window instead ({len(by_window)}); nothing answered; events {n0} -> {copy.at()}; the frame's own requests: POST /api/do {res.get('POST /api/do')}, GET /api/map {res.get('GET /api/map')}",
                     {"refused": [(r['why'], r['data'][:120]) for r in others], "frame says": res}, [await shot("4-probe")])
        except Exception as e:
            R.record("4 probe battery", "error", f"{type(e).__name__}: {e}", {"trace": traceback.format_exc()[-800:]})
        R.page_errors = await win.js("(window.__pt && window.__pt.errors) || []")
    finally:
        guard = await win.close()
    return guard


def bridge(R, copy, fx):
    """(5) in a real pywebview window with a js_api bridge, on the sandbox desktop, under the guard."""
    import sandbox_window as SB
    name = f"map-{__import__('os').getpid()}"
    log = Path(copy.state) / "bridge-calls.jsonl"
    log.write_text("", encoding="utf-8")
    url = f"{copy.base}/map-host.html?" + urllib.parse.urlencode({"session": copy.session, "as": "alex", "scope": fx["surface"]}) + "#probe"
    guard = SB.Guard(name, "Agora map bridge check")
    guard.__enter__()
    try:
        st = SB.run_hidden(name, ["python", str(HERE / "bridge_page.py"), url, str(log)], cdp=True)
        SB.join(name)
        c = None
        for _ in range(60):
            try:
                c = SB.Cdp(st["port"])
                if c.js("!!(window.__mapHost && window.__mapHost.draws)"):
                    break
            except Exception:
                pass
            time.sleep(0.5)
        for _ in range(60):          # the probe reports after 1.5 s in the frame, then its requests
            if c and c.js("!!(window.__mapHost && window.__mapHost.refused.some(r => r.data.includes('\"op\":\"report\"')))"):
                break
            time.sleep(0.5)
        # the control: the top page reaches the bridge (so a silence from the frame means something)
        top = c.js("(async () => { try { return await window.pywebview.api.touched('from the top page'); } catch (e) { return 'threw ' + e.name; } })()")
        time.sleep(1.0)
        rep = json.loads(c.js("JSON.stringify(window.__mapHost.refused.map(r => r.data).filter(d => d.includes('\"op\":\"report\"')))") or "[]")
        res = json.loads(rep[0])["results"] if rep else {}
        calls = [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines() if l.strip()]
        engine = c.js("navigator.userAgent")
        from_frame = [x for x in calls if any("frame" in str(w) for w in x)]
        ok = top == "recorded" and calls and not from_frame and res and res.get("pywebview here") == "undefined" \
            and str(res.get("parent.pywebview", "")).startswith("threw") and str(res.get("top.document", "")).startswith("threw")
        R.record("5 frame cannot reach bridge", "pass" if ok else "fail",
                 f"top page's control call: {top!r}; calls that reached Python: {calls}; the frame saw: {res}",
                 {"engine": engine[-80:] if engine else None, "frame says": res, "calls": calls})
        c.close()
    except Exception as e:
        R.record("5 frame cannot reach bridge", "error", f"{type(e).__name__}: {e}", {"trace": traceback.format_exc()[-800:]})
    finally:
        SB.close(name, quiet=True)
        guard.__exit__(None, None, None)
    return guard.verdict()


def source_guard(R, copy, fx):
    """5b (Pike c8089): pywebview puts its bridge into whatever top document loads, so the Python side should refuse a
    bridge message whose source is not the desk's own origin. bridge_page.py's wrap of pywebview's handler (in the
    caller, not the package) is tried: the desk's page reaches the bridge; the same top page, moved to another origin
    (localhost, not 127.0.0.1: the same server, a different origin), does not, and the refusal is written down."""
    import sandbox_window as SB
    name = f"mapg-{__import__('os').getpid()}"
    log = Path(copy.state) / "bridge-guard-calls.jsonl"
    log.write_text("", encoding="utf-8")
    q = urllib.parse.urlencode({"session": copy.session, "as": "alex", "scope": fx["surface"]})
    url = f"{copy.base}/map-host.html?{q}"
    other = url.replace("127.0.0.1", "localhost")
    guard = SB.Guard(name, "Agora map bridge check")
    guard.__enter__()
    call = ("(async () => { for (let i = 0; i < 40 && !(window.pywebview && window.pywebview.api && window.pywebview.api.touched); i++) await new Promise(r => setTimeout(r, 250));"
            " if (!(window.pywebview && window.pywebview.api && window.pywebview.api.touched)) return 'no bridge here';"
            " return await Promise.race([window.pywebview.api.touched(WORDS), new Promise(r => setTimeout(() => r('no answer in 4 s'), 4000))]); })()")
    try:
        st = SB.run_hidden(name, ["python", str(HERE / "bridge_page.py"), url, str(log), copy.base], cdp=True)
        SB.join(name)
        c = None
        for _ in range(60):
            try:
                c = SB.Cdp(st["port"])
                if c.js("!!(window.__mapHost && window.__mapHost.draws)"):
                    break
            except Exception:
                pass
            time.sleep(0.5)
        own = c.js(call.replace("WORDS", json.dumps("the desk's own page")))
        c.js(f"location.href = {json.dumps(other)}")
        time.sleep(3.0)
        at = c.js("location.origin")
        moved = c.js(call.replace("WORDS", json.dumps("another origin")))
        time.sleep(1.0)
        calls = [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines() if l.strip()]
        refused = [x for x in calls if x and x[0] == "refused"]
        ok = own == "recorded" and ["the desk's own page"] in calls and ["another origin"] not in calls and refused \
            and at.startswith("http://localhost")
        R.record("5b bridge refuses others", "pass" if ok else "fail",
                 f"desk page {own!r}; top moved to {at}: {moved!r}; written: {calls}",
                 {"calls": calls, "allowed": copy.base, "moved to": at})
        c.close()
    except Exception as e:
        R.record("5b bridge refuses others", "error", f"{type(e).__name__}: {e}", {"trace": traceback.format_exc()[-800:]})
    finally:
        SB.close(name, quiet=True)
        guard.__exit__(None, None, None)
    return guard.verdict()


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edge-only", action="store_true")
    ap.add_argument("--bridge-only", action="store_true")
    a = ap.parse_args()
    out = DEMOS / f"{datetime.datetime.now():%Y-%m-%d-%H%M%S}-seam"
    out.mkdir(parents=True, exist_ok=True)
    R = Run(out)
    pt.SIZE = (1280, 800)
    copy = pt.Copy("frontier-try")
    guards = {}
    try:
        fx = fixture(copy)
        print("fixture (copy only):", fx, flush=True)
        R.fixture = fx
        if not a.bridge_only:
            guards["edge"] = await edge(R, copy, fx)
        if not a.edge_only:
            guards["pywebview"] = bridge(R, copy, fx)
            guards["pywebview, source guard"] = source_guard(R, copy, fx)
    finally:
        copy.close()
    rep = {"fixture": getattr(R, "fixture", None), "guards": guards, "page_errors": getattr(R, "page_errors", None), "rows": R.rows}
    (out / "report.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    for k, g in guards.items():
        print(f"guard ({k}): {g[1] if isinstance(g, (list, tuple)) else g}")
    print(f"report: {out / 'report.json'}")


if __name__ == "__main__":
    asyncio.run(main())
