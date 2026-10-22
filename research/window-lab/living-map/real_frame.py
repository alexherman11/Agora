"""real_frame.py (a7950, Pike c8178/c8227): the seam with ground's REAL frame (research/map-lab/ground/map.html, a7946)
over Pike's real fixture (scope f8161, 'Living map: Bloomsbury sample': three OSM-verified pins and a three-pin route),
on hud_playtest's disposable copy, in hidden Edge on the sandbox desktop under the guard. Never the live world, never
Alex's screen.

    python research/window-lab/living-map/real_frame.py [--presses 12]

  ready   the host's draw reaches the frame: three pins and the route, nothing refused
  1       a pin's lat changed by line: what the frame is sent, what it holds, and where its pin stands on screen
  2       a real mouse drag of a pin in the frame: one event, the note's lat and lon changed, undone by its event
  3       the route in order, and still after the pin is renamed (title and label)
  press   a real click on a pin: the host answers 'do view <pin>' and the viewer is on it
  drop    a real double-click on the ground: one pin made in the scope, at 6 decimals; undone
  time    press to answer drawn back (Rowan c8181): from the frame's pointerup to the frame's repaint with the world's
          answer, through the host, /api/map, /api/do and the redraw; and the local selection (pointerup to the pin
          marked); n presses, p50/p95/max, against the contract's 100 ms; with the hardware
The stale move, origins, the probe battery and the dead old port stay with the stand-in (seam_browser.py), which can
send what a well-behaved frame never does.
Report: research/window-lab/demos/living-map/<time>-real/ (report.json, shots).
"""
import argparse
import asyncio
import datetime
import json
import re
import statistics
import sys
import time
import traceback
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
sys.path.insert(0, str(LAB))
sys.path.insert(0, str(HERE))
import hud_playtest as pt  # noqa: E402
from seam_browser import Run, frame_target, props  # noqa: E402

DEMOS = Path(r"C:/Projects/Agora4/research/window-lab/demos/living-map")
ME = "worker-a7950"
SCOPE = "f8161"
STATE = "JSON.stringify(window.__mapHost || null)"
# in the frame, read-only listeners: when a pointer is let go, when the pin layer is rebuilt (every draw rebuilds it),
# painted (the next animation frame), and when a pin is first marked selected
PROBE = """(() => { if (window.__t) return 'kept'; const t = window.__t = {ups: [], draws: [], sel: []};
  document.addEventListener('pointerup', () => t.ups.push(Date.now()), true);
  const pins = document.getElementById('pins');
  new MutationObserver(() => { const at = Date.now(); requestAnimationFrame(() => t.draws.push([at, Date.now()])); })
    .observe(pins, {childList: true});
  new MutationObserver(ms => { for (const m of ms) if (m.target.classList && m.target.classList.contains('sel'))
      { requestAnimationFrame(() => t.sel.push(Date.now())); break; } })
    .observe(pins, {attributes: true, subtree: true, attributeFilter: ['class']});
  return 'set'; })()"""


def hardware():
    """As ground reported its draw cost (research/map-lab/ground/measure.py)."""
    import ctypes
    import os
    import platform

    class MS(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong), ("a", ctypes.c_ulonglong), ("b", ctypes.c_ulonglong),
                    ("c", ctypes.c_ulonglong), ("d", ctypes.c_ulonglong), ("e", ctypes.c_ulonglong)]
    m = MS()
    m.dwLength = ctypes.sizeof(MS)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return {"os": platform.platform(), "cpu": platform.processor(), "logical_cpus": os.cpu_count(),
            "ram_gib": round(m.ullTotalPhys / 2 ** 30, 1), "browser": "Microsoft Edge (sandbox, InPrivate)"}


def pct(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, max(0, round(p / 100 * (len(xs) - 1))))] if xs else None


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--presses", type=int, default=12)
    a = ap.parse_args()
    out = DEMOS / f"{datetime.datetime.now():%Y-%m-%d-%H%M%S}-real"
    out.mkdir(parents=True, exist_ok=True)
    R = Run(out)
    pt.SIZE = (1280, 800)
    copy = pt.Copy("frontier-try")
    guard, rep = None, {}
    win = None
    try:
        tbl = copy.do(f"table in:{SCOPE}", ME)
        pins = re.findall(r"\b(a\d+)\s+.*?\bpin\b", tbl)
        route = (re.findall(r"\b(a\d+)\s+.*?\broute\b", tbl) or [None])[0]
        rtext = copy.do(f"read {route}", ME) if route else ""
        order = re.findall(r"\[\[(a\d+)\]\]|^(a\d+)$", rtext, re.M)
        order = [x or y for x, y in order]
        rep["fixture"] = {"scope": SCOPE, "pins": pins, "route": route, "route order (as written)": order}
        print("fixture (the copy's f8161):", rep["fixture"], flush=True)

        win = pt.Window(False)
        url = f"{copy.base}/map-host.html?" + urllib.parse.urlencode({"session": copy.session, "as": "alex", "scope": SCOPE, "frame": "ground"})
        await win.open(url)

        async def host():
            try:
                return json.loads(await win.js(STATE) or "null")
            except Exception:
                return None

        async def until(pred, secs=8.0):
            t = time.time()
            while time.time() - t < secs:
                h = await host()
                if h and pred(h):
                    return h
                await asyncio.sleep(0.15)
            return await host()

        async def shot(name):
            R.shots += 1
            p = R.out / f"{R.shots:02d}-{name}.png"
            await asyncio.sleep(0.5)
            await win.shot(p)
            return p.name

        h = await until(lambda h: h["draws"] >= 1 and h["last"], 20)
        import sandbox_window as SB
        port = json.loads(SB.state_file(win.name).read_text(encoding="utf-8"))["port"]
        fc = frame_target(port, "map/ground/map.html", 15)
        R.frame_process = "its own (out-of-process frame)"
        fj = fc.js
        for _ in range(40):
            if fj("!!(window.__map && __map.drawn().pins.length)"):
                break
            await asyncio.sleep(0.25)
        fj(PROBE)
        box = await win.js("(() => { const b = document.querySelector('iframe.map-frame').getBoundingClientRect(); return [b.left, b.top]; })()")
        drawn = fj("JSON.stringify(__map.drawn())")
        drawn = json.loads(drawn) if drawn else {"pins": [], "routes": []}
        refusals = fj("JSON.stringify(__map.refusals)")
        stats = json.loads(fj("JSON.stringify({mode: __map.stats.mode, renderer: __map.stats.renderer})") or "{}")
        ok = len(drawn["pins"]) == 3 and len(drawn["routes"]) == 1 and not (h or {}).get("problems")
        R.record("ready", "pass" if ok else "fail",
                 f"frame holds {len(drawn['pins'])} pins, {len(drawn['routes'])} route; host problems {(h or {}).get('problems')}; frame notes {refusals}; {stats}",
                 {"drawn": drawn, "frame notes": refusals, "frame": stats}, [await shot("ready")])

        def pin_xy(pid):
            r = fj(f"""(() => {{ const p = __map.drawn().pins.find(p => p.id === {json.dumps(pid)}); if (!p) return null;
                const el = [...document.querySelectorAll('#pins .pin')].find(e => e.getAttribute('aria-label') === 'Pin: ' + p.label);
                if (!el || el.style.display === 'none') return null; const b = el.getBoundingClientRect();
                return [b.left + b.width / 2, b.bottom - 8, el.style.left, el.style.top]; }})()""")
            return r

        def framed(pid):
            return next((p for p in json.loads(fj("JSON.stringify(__map.drawn())"))["pins"] if p["id"] == pid), None)

        sent = lambda h, pid: next((p for p in (h["last"] or {}).get("pins", []) if p["id"] == pid), None)  # noqa: E731
        p1 = pins[0] if pins else None

        # (1) lat by line
        try:
            before, at0 = sent(h, p1), pin_xy(p1)
            new_lat = round(before["lat"] + 0.0004, 6)
            copy.do(f"look {p1}", ME)
            copy.do(f"do prop {p1} lat={new_lat}", ME)
            h = await until(lambda h: (sent(h, p1) or {}).get("lat") == new_lat)
            await asyncio.sleep(0.3)
            after, at1, fr = sent(h, p1), pin_xy(p1), framed(p1)
            ok = after and after["lat"] == new_lat and after["rev"] > before["rev"] and fr and fr["lat"] == new_lat and at0 and at1 and at0[:2] != at1[:2]
            R.record("1 lat by line", "pass" if ok else "fail",
                     f"sent lat {before['lat']} rev {before['rev']} -> {after and after['lat']} rev {after and after['rev']}; the frame holds {fr and fr['lat']}; its pin on screen {at0 and at0[2:]} -> {at1 and at1[2:]}",
                     {"before": before, "after": after, "screen": [at0, at1]}, [await shot("1-lat")])
        except Exception as e:
            R.record("1 lat by line", "error", f"{type(e).__name__}: {e}", {"trace": traceback.format_exc()[-800:]})

        # (2) a real drag of the pin
        try:
            n0 = copy.at()
            was = props(copy, p1)
            xy = pin_xy(p1)
            k0 = len((await host())["answered"])
            await win.drag(box[0] + xy[0], box[1] + xy[1] - 14, box[0] + xy[0] + 60, box[1] + xy[1] + 30)
            h = await until(lambda h: len(h["answered"]) > k0 or h["refused"])
            n1 = copy.at()
            now = props(copy, p1)
            ans = next((x for x in h["answered"][k0:] if x["op"] == "move"), None)
            eid = ans["events"][0] if ans and len(ans["events"]) == 1 else None
            hist = copy.do(f"history {p1}", ME).strip().splitlines()[-1]
            shot_moved = await shot("2-dragged")
            if eid:
                copy.do(f"undo {eid}", "alex")
            back = props(copy, p1)
            moved = now.get("lat") != was.get("lat") and now.get("lon") != was.get("lon")
            ok = eid and n1 == n0 + 1 and moved and back.get("lat") == was.get("lat") and back.get("lon") == was.get("lon")
            R.record("2 drag is one command", "pass" if ok else "fail",
                     f"events {n0} -> {n1}; lat,lon {was.get('lat')},{was.get('lon')} -> {now.get('lat')},{now.get('lon')} by {hist[:90]}; after undo {back.get('lat')},{back.get('lon')}",
                     {"answered": ans, "refused": h["refused"][-2:]}, [shot_moved])
        except Exception as e:
            R.record("2 drag is one command", "error", f"{type(e).__name__}: {e}", {"trace": traceback.format_exc()[-800:]})

        # (3) the route, in order, after a rename
        try:
            h = await host()
            r0 = next((r for r in h["last"]["routes"] if r["id"] == route), None)
            f0 = json.loads(fj("JSON.stringify(__map.drawn().routes)"))
            copy.do(f"look {p1}", ME)
            old_title = props(copy, p1)
            copy.do(f'do retitle {p1} title="British Museum (renamed for the check)"', ME)
            copy.do(f"look {p1}", ME)
            copy.do(f'do prop {p1} label="British Museum (renamed for the check)"', ME)
            h = await until(lambda h: (sent(h, p1) or {}).get("label", "").endswith("check)"))
            await asyncio.sleep(0.3)
            r1 = next((r for r in h["last"]["routes"] if r["id"] == route), None)
            f1 = json.loads(fj("JSON.stringify(__map.drawn().routes)"))
            ok = r0 and r1 and r0["pins"] == order and r1["pins"] == order and f1 and f1[0]["pins"] == order and len(order) == 3
            R.record("3 route in order", "pass" if ok else "fail",
                     f"as written {order}; sent {r0 and r0['pins']}, after the rename {r1 and r1['pins']}; the frame holds {f1 and f1[0]['pins']}",
                     {"before": r0, "after": r1, "frame before": f0, "frame after": f1}, [await shot("3-route")])
        except Exception as e:
            R.record("3 route in order", "error", f"{type(e).__name__}: {e}", {"trace": traceback.format_exc()[-800:]})

        # press: a real click on a pin
        try:
            k0 = len((await host())["answered"])
            xy = pin_xy(pins[1])
            await win.click(box[0] + xy[0], box[1] + xy[1] - 14)
            h = await until(lambda h: len(h["answered"]) > k0)
            pressed = h["answered"][k0] if len(h["answered"]) > k0 else None
            viewing = re.search(r"\bviewing=(\S*)", "\n".join(l for l in copy.do("find prop:role=home-view,prop:actor=alex", ME).splitlines() if " note " in l))
            ok = pressed and pressed["line"] == f"do view {pins[1]}" and viewing and viewing.group(1) == pins[1]
            R.record("press", "pass" if ok else "fail", f"press -> {pressed and pressed['line']}; the viewer on {viewing and viewing.group(1)}",
                     {"pressed": pressed}, [await shot("press")])
        except Exception as e:
            R.record("press", "error", f"{type(e).__name__}: {e}", {"trace": traceback.format_exc()[-800:]})

        # drop: a real double-click on open ground (a point the frame itself picks as ground, between two pins)
        try:
            n0, k0 = copy.at(), len((await host())["answered"])
            # open ground: the first point, near the pins, where the frame's own hit test finds the 3D canvas (not a pin,
            # its label, or a panel) and the ground under it (the first run's point hit a pin's label: a press, not a drop)
            a_ = pin_xy(pins[1])
            spot = json.loads(fj(f"""JSON.stringify((() => {{ for (const [dx, dy] of [[0, 90], [-90, 60], [90, 60], [-120, 0], [120, 0], [0, 140]]) {{
                const x = {a_[0]} + dx, y = {a_[1]} + dy, e = document.elementFromPoint(x, y);
                if (e && e.id === 'gl' && __map.pick(x, y)) return [x, y]; }} return null; }})())""") or "null")
            gx, gy = spot
            want = json.loads(fj(f"JSON.stringify(__map.pick({gx}, {gy}))") or "null")
            await win.dblclick(box[0] + gx, box[1] + gy)
            h = await until(lambda h: len(h["answered"]) > k0 and any(p["label"] == "New pin" for p in (h["last"] or {}).get("pins", [])))
            dropped = next((x for x in h["answered"][k0:] if x["op"] == "drop"), None)
            made = [p for p in (h["last"] or {}).get("pins", []) if p["label"] == "New pin"]
            n1 = copy.at()
            sh = await shot("drop")
            eid = dropped["events"][0] if dropped and len(dropped["events"]) == 1 else None
            if eid:
                copy.do(f"undo {eid}", "alex")
            h2 = await until(lambda h: not [p for p in (h["last"] or {}).get("pins", []) if p["label"] == "New pin"])
            gone = not [p for p in (h2["last"] or {}).get("pins", []) if p["label"] == "New pin"]
            near = made and want and abs(made[0]["lat"] - want["lat"]) < 2e-5 and abs(made[0]["lon"] - want["lon"]) < 2e-5
            six = made and all(len(str(made[0][k]).split(".")[-1]) <= 6 for k in ("lat", "lon"))
            ok = dropped and n1 == n0 + 1 and len(made) == 1 and near and six and gone
            R.record("drop", "pass" if ok else "fail",
                     f"double-click on ground at {want}: {dropped and dropped['line']}; events {n0} -> {n1}; drawn {[(p['lat'], p['lon']) for p in made]}; undone, gone: {gone}",
                     {"dropped": dropped, "made": made}, [sh])
        except Exception as e:
            R.record("drop", "error", f"{type(e).__name__}: {e}", {"trace": traceback.format_exc()[-800:]})

        # time: press to answer drawn back, n real presses, alternating pins
        try:
            fj("(() => { __t.ups.length = 0; __t.draws.length = 0; __t.sel.length = 0; })()")
            (await host())
            await win.js("(() => { window.__mapHost.timings = []; })()")
            ends, sels, legs = [], [], []
            for i in range(a.presses):
                pid = pins[(i + 2) % len(pins)]
                xy = pin_xy(pid)
                u0 = len(json.loads(fj("JSON.stringify(__t.ups)")))
                k0 = len((await host())["answered"])
                await win.click(box[0] + xy[0], box[1] + xy[1] - 14)
                await until(lambda h: len(h["answered"]) > k0 and all("drawn" in t for t in h.get("timings") or []), 5)
                await asyncio.sleep(0.25)
                t = json.loads(fj("JSON.stringify(__t)"))
                if len(t["ups"]) <= u0:
                    continue
                up = t["ups"][-1]
                after = [d[1] for d in t["draws"] if d[0] >= up]
                sel = [s for s in t["sel"] if s >= up]
                if after:
                    ends.append(after[0] - up)
                if sel:
                    sels.append(sel[0] - up)
                await asyncio.sleep(0.15)
            hs = (await host()).get("timings") or []
            for x in hs:
                if all(k in x for k in ("heard", "checked", "done", "drawn")):
                    legs.append({"check": x["checked"] - x["heard"], "do": x["done"] - x["checked"], "redraw": x["drawn"] - x["done"]})
            hw = hardware()
            summ = lambda xs: {"n": len(xs), "p50": pct(xs, 50), "p95": pct(xs, 95), "max": max(xs) if xs else None}  # noqa: E731
            leg = {k: summ([l[k] for l in legs]) for k in ("check", "do", "redraw")}
            rep["timing"] = {"end to end ms": summ(ends), "selection ms": summ(sels), "host legs ms": leg, "raw": ends,
                             "hardware": hw, "frame": stats, "page": pt.SIZE}
            e2e = summ(ends)
            ok = e2e["n"] >= a.presses // 2 and e2e["p95"] is not None
            R.record("time", ("pass" if e2e["p95"] <= 100 else "slow") if ok else "fail",
                     f"press to answer drawn: p50 {e2e['p50']} ms, p95 {e2e['p95']} ms, max {e2e['max']} ms (n {e2e['n']}); "
                     f"selection marked: p95 {summ(sels)['p95']} ms; host legs p50: check {leg['check']['p50']}, do {leg['do']['p50']}, redraw {leg['redraw']['p50']} ms",
                     rep["timing"])
        except Exception as e:
            R.record("time", "error", f"{type(e).__name__}: {e}", {"trace": traceback.format_exc()[-800:]})
        R.page_errors = await win.js("(window.__pt && window.__pt.errors) || []")
        try:
            fc.close()
        except Exception:
            pass
    finally:
        if win:
            guard = await win.close()
        copy.close()
    rep.update({"guard": guard, "page_errors": getattr(R, "page_errors", None), "rows": R.rows})
    (out / "report.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"guard: {guard[1] if isinstance(guard, (list, tuple)) else guard}")
    print(f"report: {out / 'report.json'}")


if __name__ == "__main__":
    asyncio.run(main())
