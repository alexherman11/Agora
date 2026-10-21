"""Measure and photograph the map frame on the hidden desktop, under the guard. Nothing shows on Alex's screen.

  python research/map-lab/ground/measure.py            -> shots/*.png and results/measure.json, and a summary

Each size (800x600, 1280x720) gets a fresh InPrivate Edge on its own hidden desktop (so the load is cold), served
from a local http server on 127.0.0.1 that only serves this folder. Checks, in order:
  load      cold-load time to the first drawn frame; triangles; fixture size; footprints
  shot      the 3D map with the three stand-in pins and their route, then the same with the curve on
  idle      no frame drawn and no animation frame asked for over 3 s of quiet, after load and after input
  frames    p95 draw time (CPU + GPU, gl.finish) and frame interval over a real mouse drag, and over a measured spin
  curve     one lat/lon -> world -> back, curve off and on; and through the screen (project, then pick the ground)
  static    the page with WebGL refused: the flat plan draws, with pins, attribution and no render loop
  frame     host.html holds map.html in a sandboxed iframe: the draw arrives, a real drag sends one 'move', a stale
            rev is refused, the frame cannot reach its parent or the network
"""
import functools
import http.server
import json
import os
import platform
import statistics
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "window-lab"))
import sandbox_window as sw  # noqa: E402

SHOTS, RESULTS = HERE / "shots", HERE / "results"
SIZES = [(800, 600), (1280, 720)]
PINS = json.loads((HERE / "stand_in_draw.json").read_text(encoding="utf-8"))


def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            super().end_headers()
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(HERE)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


def p95(xs):
    xs = sorted(xs)
    return round(xs[min(len(xs) - 1, int(round(0.95 * (len(xs) - 1))))], 2) if xs else None


def summary(xs):
    return {"n": len(xs), "p50": round(statistics.median(xs), 2) if xs else None, "p95": p95(xs),
            "max": round(max(xs), 2) if xs else None}


class FrameCdp(sw.Cdp):
    """DevTools on the sandboxed iframe itself: Edge runs an opaque-origin frame in a process of its own, so it is
    a target of its own (type 'iframe'), not a child in the page's frame tree (ran 21 Oct: no childFrames)."""
    def __init__(self, port):
        from websockets.sync.client import connect
        for _ in range(50):
            tabs = json.loads(sw.urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=5).read())
            hit = [t for t in tabs if t.get("type") == "iframe" and t.get("url", "").split("?")[0].endswith("/map.html")]
            if hit:
                break
            time.sleep(0.1)
        else:
            raise RuntimeError("no iframe target for map.html: " + json.dumps([(t.get('type'), t.get('url')) for t in tabs]))
        self.ws, self.n = connect(hit[0]["webSocketDebuggerUrl"], origin=None, max_size=64 * 1024 * 1024), 0


def js_in(f, _ctx, expr):
    return f.js(expr)


def mouse(c, kind, x, y, buttons=0, button="none"):
    c.call("Input.dispatchMouseEvent", type=kind, x=x, y=y, button=button, buttons=buttons, clickCount=1)


def drag(c, x0, y0, x1, y1, steps, gap=0.016):
    mouse(c, "mouseMoved", x0, y0)
    mouse(c, "mousePressed", x0, y0, 1, "left")
    for k in range(1, steps + 1):
        mouse(c, "mouseMoved", x0 + (x1 - x0) * k / steps, y0 + (y1 - y0) * k / steps, 1, "left")
        time.sleep(gap)
    mouse(c, "mouseReleased", x1, y1, 0, "left")


def nav(c, url):
    c.call("Page.navigate", url=url)
    for _ in range(100):
        time.sleep(0.1)
        try:
            if c.js("document.readyState") == "complete" and c.js("!!(window.__map || window.__host)"):
                return
        except Exception:
            pass
    raise RuntimeError("page did not come up: " + url)


def settle(c):
    c.js("new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, 50))))")


CURVE_TEST = """(async () => {
  const M = __map, G = M.geo, F = M.frame, R = M.curveRadius, a = %s;
  const frames = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  const stored0 = JSON.stringify(M.drawn()), fx0 = JSON.stringify(window.MAP_FIXTURE);
  const out = {anchor: a, radius_m: R};
  const L = G.toLocal(F, a.lat, a.lon);
  for (const [name, r] of [['flat', 0], ['curve', R]]) {
    const w = G.world(F, r, a.lat, a.lon, 0), g = G.geographic(F, r, w), u = G.unwarp(r, w[0], w[1], w[2]);
    out[name] = {world: w.map(v => +v.toFixed(4)), back: {lat: g.lat, lon: g.lon}, height_m: g.h,
                 err_m: Math.hypot((g.lat - a.lat) * F.mlat, (g.lon - a.lon) * F.mlon),
                 ground_local_m: {e: u.e, n: u.n}};
  }
  out.same_ground_point_m = Math.hypot(out.flat.ground_local_m.e - out.curve.ground_local_m.e,
                                       out.flat.ground_local_m.n - out.curve.ground_local_m.n);
  out.on_sphere_m = Math.abs(Math.hypot(out.curve.world[0], out.curve.world[1] + R, out.curve.world[2]) - R);
  out.mesh_chord_sag_max_m = M.gridCell() ** 2 / (8 * R);
  for (const on of [false, true]) {
    M.setCurve(on); await frames();
    const s = M.project(a.lat, a.lon, 0), g = M.pick(s[0], s[1]);
    out[on ? 'screen_curve' : 'screen_flat'] = {px: s.map(v => +v.toFixed(2)), back: g,
      err_m: Math.hypot((g.lat - a.lat) * F.mlat, (g.lon - a.lon) * F.mlon)};
  }
  M.setCurve(false); await frames();
  out.stored_unchanged = JSON.stringify(M.drawn()) === stored0 && JSON.stringify(window.MAP_FIXTURE) === fx0;
  return out;
})()"""


def run_size(base, w, h, out):
    name = f"map-{os.getpid()}-{w}"
    r = {"size": [w, h]}
    st = sw.open_edge(name, base + "/map.html", size=f"{w}x{h}")
    r["viewport"] = st.get("viewport")
    c = sw.Cdp(st["port"])
    try:
        settle(c)
        r["load"] = c.js("""(() => { const n = performance.getEntriesByType('navigation')[0];
          return {first_frame_ms: +__map.stats.firstFrameMs.toFixed(1), dom_content_loaded_ms: +n.domContentLoadedEventEnd.toFixed(1),
                  load_event_ms: +n.loadEventEnd.toFixed(1), transfer_bytes: performance.getEntriesByType('resource')
                  .reduce((s, e) => s + (e.transferSize || 0), n.transferSize || 0),
                  resources: performance.getEntriesByType('resource').map(e => [e.name.split('/').pop(), e.transferSize])}; })()""")
        r["scene"] = c.js("""({mode: __map.stats.mode, renderer: __map.stats.renderer, triangles: __map.stats.triangles,
          triangles_buildings: __map.stats.trianglesBuildings, triangles_ground: __map.stats.trianglesGround,
          outline_segments: __map.stats.lines, footprints: __map.footprints, heights: __map.heights,
          dpr: devicePixelRatio, gl_error: __map.stats.glError || null})""")
        r["draw_reply"] = c.js(f"__map.receive({json.dumps(PINS)})")
        settle(c)
        # idle: nothing drawn or asked for over 3 s of quiet
        f0 = c.js("[__map.stats.frames, __map.stats.rafRequests]")
        time.sleep(3)
        f1 = c.js("[__map.stats.frames, __map.stats.rafRequests]")
        r["idle_after_load"] = {"frames": f1[0] - f0[0], "raf_requests": f1[1] - f0[1]}
        sw.page_shot(c).save(SHOTS / f"map-{w}x{h}.png")
        r["attribution"] = c.js("""(() => { const a = document.getElementById('attrib').getBoundingClientRect();
          const top = document.elementFromPoint(a.x + a.width / 2, a.y + a.height / 2);
          return {text: document.getElementById('attrib').textContent, box: [a.x, a.y, a.width, a.height].map(Math.round),
                  inside_view: a.x >= 0 && a.y >= 0 && a.right <= innerWidth && a.bottom <= innerHeight,
                  on_top: !!top && top.closest('#attrib') !== null}; })()""")
        r["legend"] = c.js("document.getElementById('legend').innerText")
        # frames under a real drag (CDP mouse input on the canvas), GPU included
        c.js("__map.stats.sync = true, __map.stats.lastDrawAt = null, window.__d0 = __map.stats.drawMs.length, "
             "window.__i0 = __map.stats.intervals.length")
        x0, y0 = w * 0.3, h * 0.45
        under = c.js(f"(() => {{ const e = document.elementFromPoint({x0}, {y0}); return e && (e.id || e.className); }})()")
        yaw0 = c.js("__map.view.yaw")
        drag(c, x0, y0, x0 + 300, y0 + 60, 90)
        settle(c)
        d = c.js("({draw: __map.stats.drawMs.slice(__d0), intervals: __map.stats.intervals.slice(__i0)})")
        c.js("__map.stats.sync = false")
        r["frames_drag"] = {"pressed_on": under, "yaw_turned": round(c.js("__map.view.yaw") - yaw0, 3),
                            "draw_ms": summary(d["draw"]), "interval_ms": summary(d["intervals"][1:])}
        f0 = c.js("[__map.stats.frames, __map.stats.rafRequests]")
        time.sleep(3)
        f1 = c.js("[__map.stats.frames, __map.stats.rafRequests]")
        r["idle_after_input"] = {"frames": f1[0] - f0[0], "raf_requests": f1[1] - f0[1]}
        b = c.js("__map.bench(240, true)")
        r["frames_spin"] = {"draw_ms": summary(b["draw"]), "interval_ms": summary(b["intervals"][1:])}
        c.js("document.getElementById('reset').click()")
        settle(c)
        r["curve"] = c.js(CURVE_TEST % json.dumps({"lat": PINS["pins"][0]["lat"], "lon": PINS["pins"][0]["lon"]}))
        c.js("__map.setCurve(true)")
        settle(c)
        sw.page_shot(c).save(SHOTS / f"map-{w}x{h}-curve.png")
        c.js("__map.setCurve(false); document.getElementById('mark').click()")
        settle(c)
        sw.page_shot(c).save(SHOTS / f"map-{w}x{h}-estimates.png")
        # a building pressed: its height and where that height came from
        r["building_info"] = c.js("""(() => { const s = __map.project(%f, %f, 8); return __map.pickBuilding(s[0], s[1]); })()"""
                                  % (PINS["pins"][0]["lat"], PINS["pins"][0]["lon"]))
        # static fallback: WebGL refused
        nav(c, base + "/map.html?nogl=1")
        c.js(f"__map.receive({json.dumps(PINS)})")
        settle(c)
        f0 = c.js("[__map.stats.frames, __map.stats.rafRequests]")
        time.sleep(2)
        f1 = c.js("[__map.stats.frames, __map.stats.rafRequests]")
        r["static"] = c.js("""(() => { const a = document.getElementById('attrib').getBoundingClientRect();
          const s = __map.project(%f, %f, 0), g = __map.pick(s[0], s[1]);
          return {mode: __map.stats.mode, plan_visible: getComputedStyle(document.getElementById('plan')).display,
                  pins_shown: [...document.querySelectorAll('.pin')].filter(p => p.style.display !== 'none').length,
                  pin_list: [...document.querySelectorAll('#pinlist button')].map(b => b.textContent),
                  attribution_visible: a.width > 0 && a.right <= innerWidth && a.bottom <= innerHeight,
                  pick_err_m: Math.hypot((g.lat - %f) * __map.frame.mlat, (g.lon - %f) * __map.frame.mlon),
                  button: document.getElementById('flat2d').textContent}; })()"""
                           % ((PINS["pins"][0]["lat"], PINS["pins"][0]["lon"]) * 2))
        r["static"]["idle"] = {"frames": f1[0] - f0[0], "raf_requests": f1[1] - f0[1]}
        sw.page_shot(c).save(SHOTS / f"map-{w}x{h}-static.png")
        # the isolated frame inside the stand-in host
        nav(c, base + "/host.html")
        time.sleep(1.0)
        ctx, fcd = None, FrameCdp(st["port"])
        fr0 = {"frame_is_own_target": True}
        js_in(fcd, ctx,"new Promise(r => { const t = () => __map.drawn().pins.length ? r() : setTimeout(t, 50); t(); })")
        fr = {"received": js_in(fcd, ctx,"(() => { const d = __map.drawn(); return {pins: d.pins.map(p => p.label), "
                                      "route: d.routes.map(r => r.pins)}; })()")}
        fr["isolation"] = js_in(fcd, ctx,"""(async () => {
          const o = {origin: self.origin, url_origin: location.origin};
          try { o.parent_document = !!parent.document; } catch (e) { o.parent_document = 'blocked: ' + e.name; }
          try { o.parent_host = typeof parent.__host; } catch (e) { o.parent_host = 'blocked: ' + e.name; }
          try { await fetch('/fixture.js'); o.fetch = 'allowed'; } catch (e) { o.fetch = 'blocked: ' + e.name; }
          try { localStorage.length; o.storage = 'allowed'; } catch (e) { o.storage = 'blocked: ' + e.name; }
          return o; })()""")
        tip = js_in(fcd, ctx,"(() => { const p = __map.drawn().pins[1]; return __map.project(p.lat, p.lon, 0); })()")
        drag(c, tip[0], tip[1] - 14, tip[0] - 70, tip[1] + 20 - 14, 20)    # west, away from the other two pins
        time.sleep(0.6)
        fr["after_drag"] = {"host_log": c.js("__host.log.slice(-2)"),
                            "host_rev": c.js("__host.state.pins[1].rev"),
                            "frame_rev": js_in(fcd, ctx,"__map.drawn().pins[1].rev"),
                            "moves_sent": js_in(fcd, ctx,"__map.outbox.filter(m => m.op === 'move').length")}
        # a newer edit the frame has not seen (as if made by line elsewhere), then a real drag from the old picture
        c.js("__host.state.pins[1].rev += 1")
        before = c.js("JSON.stringify(__host.state.pins[1])")
        tip = js_in(fcd, ctx, "(() => { const p = __map.drawn().pins[1]; return __map.project(p.lat, p.lon, 0); })()")
        drag(c, tip[0], tip[1] - 14, tip[0] - 40, tip[1] + 40 - 14, 20)
        time.sleep(0.6)
        fr["stale_move"] = {"grabbed": js_in(fcd, ctx, "__map.outbox.filter(m => m.op === 'move').slice(-1)[0].id"),
                            "host_log": c.js("__host.log.slice(-1)"),
                            "host_pin_unchanged": c.js("JSON.stringify(__host.state.pins[1])") == before,
                            "frame_redrawn_rev": js_in(fcd, ctx, "__map.drawn().pins[1].rev"),
                            "host_rev": c.js("__host.state.pins[1].rev")}
        # well-formed, but on the window instead of the port: refused both ways
        js_in(fcd, ctx, "parent.postMessage({channel: 'agora-map/1', op: 'press', id: 'p1'}, '*')")
        c.js("__host.frame.contentWindow.postMessage({channel: 'agora-map/1', op: 'draw', pins: [], routes: []}, '*')")
        time.sleep(0.4)
        fr["window_not_port"] = {"host_log": c.js("__host.log.slice(-1)"),
                                 "frame_refusals": js_in(fcd, ctx, "__map.refusals.slice(-1)"),
                                 "frame_still_draws": js_in(fcd, ctx, "__map.drawn().pins.length")}
        tip = js_in(fcd, ctx,"(() => { const p = __map.drawn().pins[0]; return __map.project(p.lat, p.lon, 0); })()")
        mouse(c, "mouseMoved", tip[0], tip[1] - 14)
        mouse(c, "mousePressed", tip[0], tip[1] - 14, 1, "left")
        mouse(c, "mouseReleased", tip[0], tip[1] - 14, 0, "left")
        time.sleep(0.4)
        fr["press"] = c.js("__host.log.slice(-1)")
        sw.page_shot(c).save(SHOTS / f"host-{w}x{h}.png")
        r["frame"] = {**fr0, **fr}
        fcd.close()
    finally:
        c.close()
        sw.close(name, quiet=True)
    out.append(r)


def hardware():
    import ctypes

    class MS(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong), ("a", ctypes.c_ulonglong), ("b", ctypes.c_ulonglong),
                    ("c", ctypes.c_ulonglong), ("d", ctypes.c_ulonglong), ("e", ctypes.c_ulonglong)]
    m = MS()
    m.dwLength = ctypes.sizeof(MS)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return {"os": platform.platform(), "cpu": platform.processor(), "logical_cpus": os.cpu_count(),
            "ram_gib": round(m.ullTotalPhys / 2 ** 30, 1), "browser": "Microsoft Edge (sandbox, InPrivate)"}


def main():
    SHOTS.mkdir(exist_ok=True)
    RESULTS.mkdir(exist_ok=True)
    srv, base = serve()
    out, verdict = [], None
    guard = sw.Guard(f"map-{os.getpid()}-{SIZES[0][0]}", "Map: Bloomsbury")
    try:
        with guard:
            for w, h in SIZES:
                guard.sandbox = f"map-{os.getpid()}-{w}"
                run_size(base, w, h, out)
        verdict = guard.verdict()
    finally:
        srv.shutdown()
    fixture = (HERE / "fixture.js").stat().st_size
    res = {"hardware": hardware(), "fixture_bytes": fixture, "fixture_mib": round(fixture / 2 ** 20, 3),
           "extract": json.loads((HERE / "extract" / "acquisition.json").read_text(encoding="utf-8")),
           "sizes": out, "guard": verdict[1] if verdict else None, "at": time.strftime("%Y-%m-%d %H:%M:%S")}
    (RESULTS / "measure.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1)[:12000])


if __name__ == "__main__":
    main()
