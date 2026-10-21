"""The journeys journeys.py plays (a7466), in a7366's order. Each takes the Journeys object J and records rows.
Coordinates are CSS px of the page; input is posted to the hidden window. Every journey that changes the copy's
layout puts the fixture tree back at its end (the copy only)."""
import asyncio
import json

from hud_playtest import q

TOL = 1.01          # CSS px: preview and result must agree within 1 px


# ---- shared reads and checks ------------------------------------------------------------------------------------


async def fixture(J):
    if not getattr(J, "fixture", None):
        st = await J.js("__cr.state()")
        J.fixture = {"tree": st["tree"], "focus": st["focus"], "layout": await J.js("__cr.root()._n.fence.item")}
    return J.fixture


async def restore(J, to=None):
    f = await fixture(J)
    if to:
        f = {**f, "tree": to["tree"], "focus": to["focus"]}
    J.copy.do(f"look {f['layout']}", "hud-playtest")
    said = J.copy.do(f"do prop {f['layout']} tree={q(f['tree'])} full={q(f['focus'])}", "hud-playtest")
    if "ERR" in said and "already has that" not in said:
        raise AssertionError("fixture restore refused: " + said[:200])
    for _ in range(40):
        await asyncio.sleep(0.25)
        st = await J.js("__cr.state()")
        if st and json.loads(st["tree"]) == json.loads(f["tree"]) and st["focus"] == f["focus"]:
            break
    await asyncio.sleep(0.8)


async def box(J, label):
    b = [x for x in await J.js("__cr.boxes()") if label.lower() in x["label"].lower()]
    return b[0] if b else None


async def grip(J, label):
    g = await J.js(f"(() => {{ const e = __cr.byLabel({json.dumps(label)}); return e ? __cr.hit(__cr.grip(e)) : null; }})()")
    if not g:
        raise AssertionError(f"no carry grip for {label}")
    if not g["ok"]:
        raise AssertionError(f"{label}'s grip is covered: a press at its centre lands on {g['at']}")
    return g["x"], g["y"]


async def frame(J):
    return await J.js("__cr.R(__cr.root())")


async def problems(J):
    """What a person would see wrong with the layout now: overlap, page overflow, dock collision, and partition
    chrome (dividers, Fit tools) standing where the panels no longer are."""
    boxes, chrome, page, fr = await J.js("__cr.boxes()"), await J.js("__cr.chrome()"), await J.js("__cr.page()"), await frame(J)
    dock = await J.js("(() => { const d = document.querySelector('[data-key$=\"/foot/bar/f5565\"]'); return d ? __cr.R(d) : null; })()")
    out = []
    if page["sw"] > page["iw"] + 1 or page["sh"] > page["ih"] + 1:
        out.append(f"page overflows {page['sw']}x{page['sh']} > {page['iw']}x{page['ih']}")
    for i, a in enumerate(boxes):
        ax, ay, aw, ah = a["r"]
        if ax < fr[0] - 1 or ay < fr[1] - 1 or ax + aw > fr[0] + fr[2] + 1 or ay + ah > fr[1] + fr[3] + 1:
            out.append(f"{a['label']} outside the layout frame")
        for b in boxes[i + 1:]:
            bx, by, bw, bh = b["r"]
            ox = min(ax + aw, bx + bw) - max(ax, bx)
            oy = min(ay + ah, by + bh) - max(ay, by)
            if ox > 2 and oy > 2:
                out.append(f"{a['label']} overlaps {b['label']} ({ox:.0f}x{oy:.0f})")
        if aw < 2 or ah < 2:
            out.append(f"{a['label']} is {aw}x{ah}")
    if dock:
        for a in boxes:
            if a["r"][1] + a["r"][3] > dock[1] + 1 and a["r"][0] < dock[0] + dock[2] and a["r"][0] + a["r"][2] > dock[0]:
                out.append(f"{a['label']} runs into the dock")
    for c in chrome:
        x, y, w, h = c["r"]
        if c["cls"] == "partition-tool" and c["text"] in ("Fit", "↔"):
            if not any(abs(x + w - (b["r"][0] + b["r"][2])) <= 1.5 and abs(y + h - (b["r"][1] + b["r"][3])) <= 1.5 for b in boxes):
                out.append(f"a {c['text']} tool stands at {x:.0f},{y:.0f} where no panel ends (stale)")
        elif c["cls"] == "l-divider" and c["label"].startswith("Resize neighbouring"):
            mid = (x + w / 2, y + h / 2)
            inside = [b for b in boxes if b["r"][0] + 3 < mid[0] < b["r"][0] + b["r"][2] - 3 and b["r"][1] + 3 < mid[1] < b["r"][1] + b["r"][3] - 3]
            if inside:
                out.append(f"a {c['axis']} divider at {mid[0]:.0f},{mid[1]:.0f} lies inside {inside[0]['label']} (stale)")
    return out


def agree(prev, res):
    return all(abs(a - b) <= TOL for a, b in zip(prev, res))


async def carry_to(J, label, x, y, back=None):
    """Pick up a panel by its grip, carry it to x,y, look at what shows mid-carry, release (or come back first)."""
    gx, gy = await grip(J, label)

    async def look(px, py):
        return {"previews": await J.js("__cr.previews()"), "ghost": await J.js("__cr.ghost()"),
                "dim": await J.js(f"(() => {{ const e = __cr.byLabel({json.dumps(label)}); return e ? e.style.opacity : null; }})()"),
                "selection": await J.js("__cr.selection()")}
    pts = [(gx + 30, gy + 10), (x, y)] + ([back] if back else [])
    seen, _ = await J.hold(gx, gy, pts, look)
    # how long the old dividers/Fit tools stand where panels no longer are, after the release
    t0, stale_ms = asyncio.get_event_loop().time(), None
    for _ in range(40):
        if not [p for p in await problems(J) if "stale" in p]:
            stale_ms = round((asyncio.get_event_loop().time() - t0) * 1000)
            break
        await asyncio.sleep(0.05)
    J.stale_ms = getattr(J, "stale_ms", []) + [stale_ms]
    await J.settle(2.0)
    return seen


# ---- the journeys ---------------------------------------------------------------------------------------------------

async def facts(J):
    """actual CSS viewport, DPR, painted layout, dock bounds"""
    f = await fixture(J)
    page, boxes, chrome = await J.js("__cr.page()"), await J.js("__cr.boxes()"), await J.js("__cr.chrome()")
    dock = await J.js("[...document.querySelectorAll('[data-key*=\"/foot/bar/f5565\"]')].filter(e => /\\/apps\\/a\\d+$/.test(e.dataset.key) || /\\/f5565$/.test(e.dataset.key)).map(e => ({key: e.dataset.key.split('/').slice(-1)[0], r: __cr.R(e)}))")
    bad = await problems(J)
    J.record("facts", facts.__doc__, "pass" if not bad and page["iw"] == J.size[0] and page["ih"] == J.size[1] else "fail",
             f"page {page['iw']}x{page['ih']} CSS at DPR {page['dpr']}; panels " + "; ".join(f"{b['label']} {b['r'][2]:.0f}x{b['r'][3]:.0f}" for b in boxes)
             + (f"; problems: {bad}" if bad else "; no overlap/overflow/dock collision/stale chrome"),
             {"page": page, "boxes": boxes, "chrome": chrome, "dock": dock, "fixture": f}, [await J.shot("facts")])


async def clicks(J):
    """title clicks, a 4px move and a text click neither snap nor resize; a header pin toggle leaves geometry"""
    await fixture(J)
    before, boxes0 = await J.js("__cr.state()"), await J.js("__cr.boxes()")
    notes = []
    for label in ("The board", "Viewer", "Chat", "Music"):
        x, y = await grip(J, label)
        await J.w.click(x, y)
        await J.settle(0.8)
        if await J.js("__cr.state()") != before:
            notes.append(f"{label} title click changed the tree")
        await J.hold(x, y, [(x + 4, y)], steps=4)
        await J.settle(0.8)
        if await J.js("__cr.state()") != before:
            notes.append(f"{label} 4px move changed the tree")
    p = await J.js("(() => { const e = [...document.querySelectorAll('[data-key*=\"lens:home-viewer\"] p, [data-key*=\"lens:home-viewer\"] .l-text')].find(__cr.vis); return e ? __cr.hit(e) : null; })()")
    if p:
        await J.w.click(p["x"], p["y"])
        await J.settle(0.8)
        if await J.js("__cr.state()") != before:
            notes.append("a click on viewer text changed the tree")
    boxes1 = await J.js("__cr.boxes()")
    moved = [a["label"] for a, b in zip(boxes0, boxes1) if not agree(a["r"], b["r"])]
    if moved:
        notes.append(f"boxes moved: {moved}")
    sel = await J.js("__cr.selection()")
    J.record("clicks", clicks.__doc__, "pass" if not notes else "fail",
             "; ".join(notes) or f"4 title clicks, 4 four-pixel moves and a text click: tree and every box unchanged (selection {sel} chars)",
             {"before": before}, [await J.shot("clicks")])


async def ghost(J):
    """past 5px a whole-panel copy follows the hand, the source dims, a preview shows; Escape cancels with no event"""
    await fixture(J)
    before = await J.js("__cr.state()")
    gx, gy = await grip(J, "The board")
    fr = await frame(J)
    seen, handle = await J.hold(gx, gy, [(fr[0] + fr[2] / 2, fr[1] + fr[3] - 3)], lambda x, y: J.js("({ghost: __cr.ghost(), previews: __cr.previews(), dim: __cr.byLabel('The board').style.opacity, sel: __cr.selection()})"), release=False)
    shot = await J.shot("ghost-held")
    J.w.SB.press_key(J.w.SB.focused(J.w.win), "Escape")
    await J.settle(0.6)
    J.up(handle)
    await J.settle(1.5)
    s = seen[0]
    after = await J.js("__cr.state()")
    g = s["ghost"] or {}
    notes = []
    if not g:
        notes.append("no ghost while carried")
    else:
        if "need you" not in g["text"] and "board" not in g["text"].lower():
            notes.append(f"ghost is not the whole panel ({g['text']!r})")
        if not g["transition"].startswith("none") or not g["animation"].endswith("none"):
            notes.append("ghost animates")
    if s["dim"] != "0.35":
        notes.append(f"source opacity {s['dim']!r}, not dimmed")
    if not s["previews"]:
        notes.append("no landing preview")
    if s["sel"]:
        notes.append(f"the carry selected {s['sel']} characters of page text")
    if after != before:
        notes.append("Escape did not cancel: the tree changed")
    if await J.js("__cr.ghost()"):
        notes.append("ghost left on the page after Escape")
    J.record("ghost", ghost.__doc__, "pass" if not notes else "fail",
             "; ".join(notes) or f"ghost {g.get('r')} opacity {g.get('opacity')} no transition; source dimmed .35; preview {s['previews'][0]['r']}; Escape: no tree change, ghost gone",
             {"held": s}, [shot, await J.shot("ghost-after-escape")])


async def edges(J):
    """drops on the four desk edges span the full axis; preview == result within 1px; from three panels incl. bare app"""
    await fixture(J)
    for label in ("The board", "Chat", "Music"):
        for side in ("bottom", "top", "left", "right"):
            fr = await frame(J)
            x, y = {"bottom": (fr[0] + fr[2] / 2, fr[1] + fr[3] - 3), "top": (fr[0] + fr[2] / 2, fr[1] + 3),
                    "left": (fr[0] + 3, fr[1] + fr[3] / 2), "right": (fr[0] + fr[2] - 3, fr[1] + fr[3] / 2)}[side]
            seen = await carry_to(J, label, x, y)
            mid = seen[1]
            pv = [p for p in mid["previews"] if p["in"] == "partition"]
            b = await box(J, label)
            bad = await problems(J)
            notes = []
            if not pv:
                notes.append("no partition preview at the edge")
            elif not b or not agree(pv[0]["r"], b["r"]):
                notes.append(f"preview {pv[0]['r']} != result {b and b['r']}")
            if b:
                span = b["r"][2] if side in ("top", "bottom") else b["r"][3]
                full = fr[2] if side in ("top", "bottom") else fr[3]
                if abs(span - full) > TOL:
                    notes.append(f"spans {span:.1f} of the desk's {full:.1f}")
            notes += bad
            J.record(f"edge-{side}-{label.split()[-1].lower()}", f"{label} to the desk's {side} edge", "pass" if not notes else "fail",
                     "; ".join(notes) or f"preview {pv[0]['r']} = result {b['r']}, spans the desk",
                     {"preview": mid, "result": b, "frame": fr}, [await J.shot(f"edge-{side}-{label.split()[-1].lower()}")])
            await restore(J)


async def local(J):
    """a panel dropped on another panel's four edges splits that panel; centre makes tabs; each tab selects"""
    await fixture(J)
    for side in ("left", "right", "top", "bottom", "centre"):
        t = await box(J, "Viewer")
        x0, y0, w, h = t["r"]
        x, y = {"left": (x0 + w * .1, y0 + h / 2), "right": (x0 + w * .9, y0 + h / 2), "top": (x0 + w / 2, y0 + h * .1),
                "bottom": (x0 + w / 2, y0 + h * .9), "centre": (x0 + w / 2, y0 + h / 2)}[side]
        seen = await carry_to(J, "The board", x, y)
        pv = [p for p in seen[1]["previews"] if p["in"] == "partition"]
        b = await box(J, "The board")
        notes = []
        if side != "centre":
            if not pv or not b or not agree(pv[0]["r"], b["r"]):
                notes.append(f"preview {pv and pv[0]['r']} != result {b and b['r']}")
        else:
            tabs = [c for c in await J.js("__cr.chrome()") if c["label"].startswith("Show ")]
            if len(tabs) < 2:
                notes.append(f"centre drop made {len(tabs)} tab buttons")
            for tb in tabs:
                await J.w.click(tb["r"][0] + tb["r"][2] / 2, tb["r"][1] + tb["r"][3] / 2)
                await J.settle(1.5)
                shown = [x["label"] for x in await J.js("__cr.boxes()")]
                want = tb["label"][5:]
                if not any(want.lower() in s.lower() for s in shown):
                    notes.append(f"tab {want!r} did not show its panel (shown {shown})")
        notes += await problems(J)
        J.record(f"local-{side}", f"the board onto the viewer's {side}", "pass" if not notes else "fail",
                 "; ".join(notes) or (f"preview = result {b['r']}" if side != "centre" else "two tabs; each selected its panel"),
                 {"preview": seen[1], "result": b}, [await J.shot(f"local-{side}")])
        await restore(J)


async def fit(J):
    """Fit content / fill toggles a leaf; a bare app's content handles persist an extent"""
    await fixture(J)
    tools = [c for c in await J.js("__cr.chrome()") if c["text"] == "Fit"]
    b0 = await box(J, "The board")
    t = [c for c in tools if abs(c["r"][0] + c["r"][2] - (b0["r"][0] + b0["r"][2])) < 2]
    notes, shots = [], []
    if not t:
        notes.append("no Fit tool on the board")
    else:
        await J.w.click(t[0]["r"][0] + 18, t[0]["r"][1] + 11)
        await J.settle(2)
        tree = json.loads((await J.js("__cr.state()"))["tree"])
        b1 = await box(J, "The board")
        shots.append(await J.shot("fit-content"))
        if '"content"' not in json.dumps(tree) or b1["r"] == b0["r"]:
            notes.append(f"Fit did not make the board content-sized ({b0['r']} -> {b1['r']})")
        back = [c for c in await J.js("__cr.chrome()") if c["text"] == "↔"]
        if back:
            await J.w.click(back[0]["r"][0] + 18, back[0]["r"][1] + 11)
            await J.settle(2)
            if not agree((await box(J, "The board"))["r"], b0["r"]):
                notes.append("↔ did not give the board its space back")
        else:
            notes.append("no ↔ tool after Fit")
        notes += await problems(J)
    m0 = await box(J, "Music")
    hx = [c for c in await J.js("__cr.chrome()") if c["label"] == "Resize content width"]
    if hx:
        x, y = hx[0]["r"][0] + 6, hx[0]["r"][1] + hx[0]["r"][3] / 2
        await J.hold(x, y, [(x + 80, y)])
        await J.settle(2)
        m1 = await box(J, "Music")
        if abs(m1["r"][2] - m0["r"][2] - 80) > 2:
            notes.append(f"music content width {m0['r'][2]} -> {m1['r'][2]}, not +80")
        await J.reload()
        m2 = await box(J, "Music")
        if not agree(m2["r"], m1["r"]):
            notes.append(f"music extent did not persist a reload ({m1['r']} -> {m2['r']})")
        shots.append(await J.shot("fit-music-extent"))
    else:
        notes.append("no content width handle on music")
    J.record("fit", fit.__doc__, "pass" if not notes else "fail", "; ".join(notes) or "Fit made the board content-sized and ↔ restored it; music +80 wide by its handle, kept over a reload", {}, shots)
    await restore(J)


async def dividers(J):
    """every shared divider both ways and to its minimum; then a horizontal split both ways"""
    await fixture(J)
    notes, shots, statuses = [], [], []
    async def sweep(tag, base=None):
        ds = [c for c in await J.js("__cr.chrome()") if c["label"].startswith("Resize neighbouring")]
        for k, d in enumerate(ds):
            x, y = d["r"][0] + d["r"][2] / 2, d["r"][1] + d["r"][3] / 2
            ax = d["axis"]
            for delta in (80, -80, -4000, 4000):
                d2 = [c for c in await J.js("__cr.chrome()") if c["label"].startswith("Resize neighbouring")]
                if len(d2) <= k:
                    notes.append(f"{tag} divider {k} vanished")
                    break
                dd = d2[k]
                x, y = dd["r"][0] + dd["r"][2] / 2, dd["r"][1] + dd["r"][3] / 2
                st0, b0 = await J.js("__cr.state()"), await J.js("__cr.boxes()")
                tx, ty = (x + delta, y) if ax == "x" else (x, y + delta)
                pg = await J.js("__cr.page()")
                tx, ty = max(2, min(pg["iw"] - 2, tx)), max(2, min(pg["ih"] - 2, ty))
                await J.hold(x, y, [(tx, ty)])
                await J.settle(1.6)
                st1, b1 = await J.js("__cr.state()"), await J.js("__cr.boxes()")
                status = await J.js("((document.getElementById('status') || {}).textContent || '').slice(0, 120)")
                if status:
                    statuses.append(f"{tag} {ax} divider {k} {delta:+}: {status}")
                if abs(delta) == 80 and st1 == st0:
                    notes.append(f"{tag} {ax} divider {k} {delta:+}: no weight change saved")
                small = [b for b in b1 if (b["r"][2] < 240 - 1 if ax == "x" else b["r"][3] < 140 - 1) and b["sizing"] != "content"]
                if small:
                    notes.append(f"{tag} {ax} divider {k} {delta:+}: {small[0]['label']} below its minimum ({small[0]['r'][2]:.0f}x{small[0]['r'][3]:.0f})")
                notes.extend(f"{tag} {ax} divider {k} {delta:+}: {p}" for p in await problems(J))
            shots.append(await J.shot(f"divider-{tag}-{k}"))
            await restore(J, base)
    await sweep("columns")
    fr = await frame(J)
    await carry_to(J, "Chat", fr[0] + fr[2] / 2, fr[1] + fr[3] - 3)
    rows = await J.js("__cr.state()")
    await sweep("rows", rows)
    J.record("dividers", dividers.__doc__, "pass" if not notes else "fail",
             "; ".join(dict.fromkeys(notes)) or "every column divider and, with chat across the bottom, every divider of that layout: +80/-80 saved, pushed to both ends the minima held, no overlap/overflow/stale chrome",
             {"status lines": statuses}, shots)
    if statuses:
        J.record("divider-status", "what the status line says after divider releases", "fail" if any("refused" in s for s in statuses) else "pass",
                 "; ".join(dict.fromkeys(statuses))[:600], {}, [])
    await restore(J)


async def focus(J):
    """double-click fills (focus) with the pinned chat beside, a rail for the rest; a focused divider persists a reload; again restores"""
    await fixture(J)
    notes, shots = [], []
    x, y = await grip(J, "The board")
    await J.w.dblclick(x, y)
    await J.settle(2)
    st = await J.js("__cr.state()")
    boxes = await J.js("__cr.boxes()")
    rail = [c for c in await J.js("__cr.chrome()") if c["label"].startswith("Fill with ")]
    shots.append(await J.shot("focus"))
    if not st["focus"]:
        notes.append("double-click set no focus")
    labels = [b["label"] for b in boxes]
    if "Chat" not in labels:
        notes.append(f"pinned chat not beside the focused board ({labels})")
    if not rail:
        notes.append("no rail of the others")
    ds = [c for c in await J.js("__cr.chrome()") if c["label"].startswith("Resize neighbouring")]
    if ds:
        d = ds[0]
        dx, dy = d["r"][0] + 6, d["r"][1] + d["r"][3] / 2
        await J.hold(dx, dy, [(dx - 120, dy)])
        await J.settle(2)
        fw = json.loads((await J.js("__cr.state()"))["tree"]).get("focus_weights")
        if not fw:
            notes.append("focused divider saved no focus_weights")
        b1 = await J.js("__cr.boxes()")
        await J.reload()
        b2 = await J.js("__cr.boxes()")
        if [b["r"] for b in b1] != [b["r"] for b in b2]:
            if not all(agree(a["r"], b["r"]) for a, b in zip(b1, b2)):
                notes.append("focused layout changed over a reload")
        shots.append(await J.shot("focus-resized-reloaded"))
    else:
        notes.append("no divider in focus")
    x, y = await grip(J, "The board")
    await J.w.dblclick(x, y)
    await J.settle(2)
    if (await J.js("__cr.state()"))["focus"]:
        notes.append("second double-click did not restore")
    notes += await problems(J)
    shots.append(await J.shot("focus-restored"))
    J.record("focus", focus.__doc__, "pass" if not notes else "fail", "; ".join(notes) or f"focus on the board with Chat beside and a rail of {len(rail)}; focused divider saved and kept over reload; double-click restored", {}, shots)
    await restore(J)


DOCK_PINS = ("[...document.querySelectorAll('[data-key*=\"/foot/bar/f5565/\"]')].filter(e => /\\/apps\\/a\\d+$/.test(e.dataset.key) && __cr.vis(e))"
             ".map(e => ({id: e.dataset.key.split('/').pop(), tip: (e._n.paint.tip || [])[0], h: __cr.hit(e), open: (e.className || '').includes('open')}))")


async def shelf(J):
    """pin the board panel to the dock, shelve it from its header, open it from its pin twice: one board, back in place"""
    await fixture(J)
    b0 = await box(J, "The board")
    pins0 = await J.js(DOCK_PINS)
    dock = await J.js("(() => { const d = document.querySelector('[data-key$=\"/foot/bar/f5565\"]'); return d ? __cr.R(d) : null; })()")
    await carry_to(J, "The board", dock[0] + dock[2] - 4, dock[1] + dock[3] / 2)
    pins1 = await J.js(DOCK_PINS)
    new = [p for p in pins1 if p["id"] not in {q_["id"] for q_ in pins0}]
    if not new:
        J.record("shelf", shelf.__doc__, "fail", f"dropping the board panel on the dock made no pin ({[p['tip'] for p in pins1]})", {}, [await J.shot("shelf-nopin")])
        await restore(J)
        return
    pin = new[0]
    open_before = pin["open"]
    h = await J.js("(() => { const e = __cr.byLabel('The board'); const b = [...e.querySelectorAll('[data-key]')].find(x => x.innerText.trim() === '–' && __cr.vis(x)); return b ? __cr.hit(b) : null; })()")
    notes, shots = [], []
    if not h:
        J.record("shelf", shelf.__doc__, "blocked", "no shelf control found on the board header", {}, [await J.shot("shelf-none")])
        return
    await J.w.click(h["x"], h["y"])
    await J.settle(2)
    if await box(J, "The board"):
        notes.append("the board still shows after its shelf control")
    shots.append(await J.shot("shelf-shelved"))
    shelved = [p for p in await J.js(DOCK_PINS) if p["id"] == pin["id"]]
    if not open_before:
        notes.append("the new pin did not show the board as open before shelving")
    if shelved and shelved[0]["open"]:
        notes.append("the pin still shows open while the board is shelved")
    for _ in range(2):
        p = [p for p in await J.js(DOCK_PINS) if p["id"] == pin["id"]][0]
        await J.w.click(p["h"]["x"], p["h"]["y"])
        await J.settle(2)
    boards = [b for b in await J.js("__cr.boxes()") if "board" in b["label"].lower()]
    if len(boards) != 1:
        notes.append(f"{len(boards)} board panels after opening its pin twice")
    elif not agree(boards[0]["r"], b0["r"]):
        notes.append(f"reopened at {boards[0]['r']}, was {b0['r']}")
    reopened = [p for p in await J.js(DOCK_PINS) if p["id"] == pin["id"]]
    if reopened and not reopened[0]["open"]:
        notes.append("the pin does not show open after reopening")
    notes += await problems(J)
    shots.append(await J.shot("shelf-reopened"))
    J.record("shelf", shelf.__doc__, "pass" if not notes else "fail",
             "; ".join(notes) or f"board pinned ({pin['tip']}), shelved from its header (pin open marker off), opened twice from its pin: one board, back at {b0['r']}, marker on",
             {"pin": pin}, shots)
    J.copy.do("read a5674", "hud-playtest")
    J.copy.do("do prop a5674 shelf=no", "hud-playtest")
    await restore(J)


async def cancel(J):
    """Escape, a viewport resize and a window blur mid-carry cancel with no event (resize/blur are dispatched events)"""
    await fixture(J)
    notes = []
    before = await J.js("__cr.state()")
    fr = await frame(J)
    for how in ("resize", "blur"):
        gx, gy = await grip(J, "The board")
        _, handle = await J.hold(gx, gy, [(fr[0] + fr[2] / 2, fr[1] + fr[3] - 3)], release=False)
        await J.js(f"window.dispatchEvent(new Event({json.dumps(how)}))")
        await J.settle(0.4)
        left = {"ghost": await J.js("__cr.ghost()"), "previews": await J.js("__cr.previews()")}
        J.up(handle)
        await J.settle(1.5)
        if await J.js("__cr.state()") != before:
            notes.append(f"{how} mid-carry: the release still committed")
        if left["ghost"] or left["previews"]:
            notes.append(f"{how}: ghost/preview left after cancel")
    J.record("cancel", cancel.__doc__, "pass" if not notes else "fail",
             "; ".join(notes) or "Escape (journey ghost), resize and blur each cancelled: nothing committed, ghost and preview gone. pointercancel not driven (no real touch input here)", {}, [await J.shot("cancel")])
    await restore(J)


async def stale(J):
    """a competing world change while a panel is held refuses the stale drop and repaints the real layout"""
    f = await fixture(J)
    fr = await frame(J)
    gx, gy = await grip(J, "The board")
    _, handle = await J.hold(gx, gy, [(fr[0] + fr[2] / 2, fr[1] + fr[3] - 3)], release=False)
    other = json.loads(f["tree"])
    other["root"]["weights"] = [w * (2 if i == len(other["root"]["weights"]) - 1 else 1) for i, w in enumerate(other["root"]["weights"])]
    J.copy.do(f"look {f['layout']}", "hud-playtest")
    said = J.copy.do(f"do prop {f['layout']} tree={q(json.dumps(other))}", "hud-playtest")
    await J.settle(0.8)
    J.up(handle)
    await J.settle(3)
    st = json.loads((await J.js("__cr.state()"))["tree"])
    status = await J.js("((document.getElementById('status') || {}).textContent || '').slice(0, 200)")
    notes = []
    if st != other:
        notes.append(f"after the competing change the tree is not the competitor's (stale drop committed?): {json.dumps(st)[:160]}")
    notes += await problems(J)
    J.record("stale", stale.__doc__, "pass" if not notes else "fail",
             "; ".join(notes) or f"competing weight change kept; the held drop did not commit over it; status: {status!r}",
             {"competing": said[:200], "status": status}, [await J.shot("stale")])
    await restore(J)


async def draft(J):
    """an unsent chat draft and its caret survive rearrange, resize, focus and reload (nothing is sent)"""
    await fixture(J)
    c = await J.js("(() => { const t = [...document.querySelectorAll('textarea')].find(e => __cr.vis(e) && e.closest('[data-key*=\"lens:jeff-chat\"]')); return t ? __cr.hit(t) : null; })()")
    if not c:
        J.record("draft", draft.__doc__, "blocked", "no chat composer painted", {}, [await J.shot("draft-none")])
        return
    await J.w.click(c["x"], c["y"])
    await J.settle(0.4)
    await J.w.type("unsent review draft")
    for _ in range(3):
        await J.w.key("ArrowLeft")
    await J.settle(0.5)
    read = "(() => { const t = [...document.querySelectorAll('textarea')].find(e => __cr.vis(e) && e.closest('[data-key*=\"lens:jeff-chat\"]')); return t ? [t.value, t.selectionStart, document.activeElement === t] : null; })()"
    v0 = await J.js(read)
    notes, seen = [], {"typed": v0}
    if not v0 or v0[0] != "unsent review draft":
        notes.append(f"typing did not arrive: {v0}")
    fr = await frame(J)
    await carry_to(J, "The board", fr[0] + fr[2] / 2, fr[1] + fr[3] - 3)
    seen["after drop"] = await J.js(read)
    ds = [d for d in await J.js("__cr.chrome()") if d["label"].startswith("Resize neighbouring")]
    if ds:
        d = ds[0]
        x, y = d["r"][0] + d["r"][2] / 2, d["r"][1] + d["r"][3] / 2
        await J.hold(x, y, [(x + 60, y)] if d["axis"] == "x" else [(x, y + 60)])
        await J.settle(1.6)
        seen["after divider"] = await J.js(read)
    x, y = await grip(J, "Viewer")
    await J.w.dblclick(x, y)
    await J.settle(1.6)
    seen["after focus"] = await J.js(read)
    await J.w.dblclick(*(await grip(J, "Viewer")))
    await J.settle(1.6)
    await J.reload()
    seen["after reload"] = await J.js(read)
    for k, v in seen.items():
        if k == "typed":
            continue
        if not v or v[0] != v0[0]:
            notes.append(f"{k}: words {v and v[0]!r}")
        elif v[1] != v0[1] and k != "after reload":
            notes.append(f"{k}: caret {v[1]} (was {v0[1]})")
    sent = await J.js("[...document.querySelectorAll('[data-key*=\"lens:jeff-chat\"]')].some(e => e.innerText.includes('unsent review draft') && e.tagName !== 'TEXTAREA' && !e.querySelector('textarea'))")
    if sent:
        notes.append("the draft text appears outside the composer (sent?)")
    J.record("draft", draft.__doc__, "pass" if not notes else "fail", "; ".join(notes) or f"words and caret {v0[1]} kept through drop, divider, focus; words kept over reload ({seen['after reload']})", seen, [await J.shot("draft")])
    await restore(J)


async def bare(J):
    """the bare Spotify app: compact, no generic header or Fit tools; its grip carries the whole surface; no media pressed"""
    await fixture(J)
    m = await box(J, "Music")
    info = await J.js("(() => { const e = __cr.byLabel('Music'); return { header: [...e.querySelectorAll('[data-key]')].filter(x => ['◆','–','⇔'].includes(x.innerText.trim()) && __cr.vis(x)).length, grip: __cr.R(__cr.grip(e)), text: e.innerText.slice(0, 80) }; })()")
    tools = [c for c in await J.js("__cr.chrome()") if c["text"] in ("Fit", "↔") and abs(c["r"][0] + c["r"][2] - (m["r"][0] + m["r"][2])) < 2]
    notes = []
    if info["header"]:
        notes.append(f"{info['header']} generic header controls on the bare app")
    if tools:
        notes.append("a Fit tool on the bare app")
    gx, gy = await grip(J, "Music")
    seen, handle = await J.hold(gx, gy, [(gx + 200, gy + 300)], lambda x, y: J.js("__cr.ghost()"), release=False)
    J.w.SB.press_key(J.w.SB.focused(J.w.win), "Escape")
    await J.settle(0.5)
    J.up(handle)
    await J.settle(1)
    g = seen[0]
    if not g or "Nothing playing" not in g["text"] and "Spotify" not in g["text"]:
        notes.append(f"appgrip ghost is not the whole app ({g and g['text']!r})")
    J.record("bare", bare.__doc__, "pass" if not notes else "fail",
             "; ".join(notes) or f"music {m['r'][2]:.0f}x{m['r'][3]:.0f} (content), no header controls or Fit; appgrip {info['grip'][2]:.0f}x{info['grip'][3]:.0f} carries the whole app. Playback/heart not pressed: no track is playing in the copy and media/account operations are out of scope (Connect Spotify untouched)",
             {"music": m, "info": info, "ghost": g}, [await J.shot("bare")])


async def dock_pins(J):
    """carrying a panel over the dock shows only the dock's target, back over the desk only the split's; two drops make one pin"""
    await fixture(J)
    dock = await J.js("(() => { const d = document.querySelector('[data-key$=\"/foot/bar/f5565\"]'); return d ? __cr.R(d) : null; })()")
    count = "[...document.querySelectorAll('[data-key*=\"/foot/bar/f5565/\"]')].filter(e => /\\/apps\\/a\\d+$/.test(e.dataset.key) && __cr.vis(e)).length"
    n0 = await J.js(count)
    notes, shots = [], []
    dx, dy = dock[0] + dock[2] / 2, dock[1] + dock[3] / 2
    bb = (await box(J, "The board"))["r"]
    seen = await carry_to(J, "Viewer", dx, dy, back=(bb[0] + bb[2] / 2, bb[1] + bb[3] / 2))
    over, back = seen[1]["previews"], seen[2]["previews"]
    if len(over) != 1 or over[0]["in"] == "partition":
        notes.append(f"over the dock the previews were {over}")
    if len(back) != 1 or back[0]["in"] != "partition":
        notes.append(f"back over the desk the previews were {back}")
    await restore(J)
    for k in range(2):
        seen = await carry_to(J, "Viewer", dx, dy)
        shots.append(await J.shot(f"dock-drop-{k + 1}"))
        if (await J.js("__cr.state()"))["tree"] != (await fixture(J))["tree"]:
            notes.append(f"dock drop {k + 1} also rearranged the tree")
            await restore(J)
    n2 = await J.js(count)
    if n2 != n0 + 1:
        notes.append(f"pins {n0} -> {n2} after two drops of the viewer (want +1)")
    notes += await problems(J)
    J.record("dock-pin", dock_pins.__doc__, "pass" if not notes else "fail", "; ".join(notes) or f"one target at a time (dock box over the dock, split box over the desk); two drops: pins {n0} -> {n2}; tree untouched", {"over": over, "back": back}, shots)


async def dock_order(J):
    """reorder pins by drag both ways and to the end; remove by menu; restore removed pins; dropping outside changes nothing"""
    pins = "[...document.querySelectorAll('[data-key*=\"/foot/bar/f5565/\"]')].filter(e => /\\/apps\\/a\\d+$/.test(e.dataset.key) && __cr.vis(e)).map(e => ({id: e.dataset.key.split('/').pop(), tip: (e._n.paint.tip || [])[0], r: __cr.R(e)}))"
    p0 = await J.js(pins)
    notes, shots = [], []
    if len(p0) < 3:
        J.record("dock-order", dock_order.__doc__, "blocked", f"only {len(p0)} pins", {}, [])
        return
    a, c = p0[0], p0[2]
    await J.hold(a["r"][0] + a["r"][2] / 2, a["r"][1] + a["r"][3] / 2, [(c["r"][0] + c["r"][2] * .3, c["r"][1] + c["r"][3] / 2)])
    await J.settle(2)
    p1 = await J.js(pins)
    ids0, ids1 = [p["id"] for p in p0], [p["id"] for p in p1]
    if ids1 == ids0:
        notes.append("drag first onto third's left changed no order")
    last = p1[-1]
    b = p1[0]
    await J.hold(b["r"][0] + b["r"][2] / 2, b["r"][1] + b["r"][3] / 2, [(last["r"][0] + last["r"][2] * .92, last["r"][1] + last["r"][3] / 2)])
    await J.settle(2)
    p2 = await J.js(pins)
    if [p["id"] for p in p2][-1] != b["id"]:
        notes.append(f"drop on the last pin's right edge did not move it last ({[p['id'] for p in p2]})")
    shots.append(await J.shot("dock-reordered"))
    fr = await frame(J)
    x = p2[1]
    await J.hold(x["r"][0] + x["r"][2] / 2, x["r"][1] + x["r"][3] / 2, [(fr[0] + 300, fr[1] + 300)])
    await J.settle(2)
    if [p["id"] for p in await J.js(pins)] != [p["id"] for p in p2]:
        notes.append("dropping a pin outside the dock changed the pins")
    await J.w.click(x["r"][0] + x["r"][2] / 2, x["r"][1] + x["r"][3] / 2, right=True)
    await J.settle(0.8)
    menu = await J.js("(() => { const m = document.getElementById('menu-pop'); return m ? [...m.querySelectorAll('button')].map(b => b.textContent) : null; })()")
    if not menu or "Remove pin" not in menu:
        notes.append(f"pin menu {menu}")
    else:
        r = await J.js("(() => { const b = [...document.querySelectorAll('#menu-pop button')].find(b => b.textContent === 'Remove pin'); const r = b.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; })()")
        await J.w.click(*r)
        await J.settle(2)
        p3 = await J.js(pins)
        if x["id"] in [p["id"] for p in p3]:
            notes.append("Remove pin left the pin")
        shots.append(await J.shot("dock-removed"))
        bar = await J.js("(() => { const d = document.querySelector('[data-key$=\"/foot/bar/f5565\"]'); return d ? __cr.R(d) : null; })()")
        await J.w.click(bar[0] + 3, bar[1] + bar[3] / 2, right=True)
        await J.settle(0.8)
        menu2 = await J.js("(() => { const m = document.getElementById('menu-pop'); return m ? [...m.querySelectorAll('button')].map(b => b.textContent) : null; })()")
        if menu2 and "Restore removed pins" in menu2:
            r = await J.js("(() => { const b = [...document.querySelectorAll('#menu-pop button')].find(b => b.textContent === 'Restore removed pins'); const r = b.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; })()")
            await J.w.click(*r)
            await J.settle(2)
            p4 = await J.js(pins)
            if [p["id"] for p in p4] != [p["id"] for p in p2]:
                notes.append(f"restore gave {[p['id'] for p in p4]}, want {[p['id'] for p in p2]}")
        else:
            notes.append(f"no 'Restore removed pins' on the dock's menu ({menu2})")
            await J.w.key("Escape")
    shots.append(await J.shot("dock-restored"))
    J.record("dock-order", dock_order.__doc__, "pass" if not notes else "fail", "; ".join(notes) or "reordered both ways and to the end; outside drop changed nothing; Remove pin by menu; Restore removed pins put it back in order", {"before": ids0}, shots)


async def dock_look(J):
    """compact coloured icons, hover names readable, open markers truthful, nothing overflowing"""
    pins = await J.js("[...document.querySelectorAll('[data-key*=\"/foot/bar/f5565/\"]')].filter(e => /\\/apps\\/a\\d+$/.test(e.dataset.key) && __cr.vis(e)).map(e => ({tip: (e._n.paint.tip || [])[0], r: __cr.R(e), open: (e.className || '').includes('open'), cls: e.className, bg: getComputedStyle(e.querySelector('[data-key$=\"/icon\"]') || e).backgroundColor, fg: getComputedStyle(e.querySelector('[data-key*=\"/glyph\"], [data-key*=\"/pics\"]') || e).color}))")
    notes, shots, tips = [], [], []
    SB, w = J.w.SB, J.w
    for p in pins:
        ox, oy, dpr = await w.origin()
        cx, cy = ox + (p["r"][0] + p["r"][2] / 2) * dpr, oy + (p["r"][1] + p["r"][3] / 2) * dpr
        t, dx, dy = w._descend(cx, cy)
        SB.post(t, SB.WM_MOUSEMOVE, 0, SB.xy(cx + dx, cy + dy))
        await J.settle(1.0)
        tip = await J.js("(() => { const e = [...document.querySelectorAll('.l-tip, [role=tooltip], .tip, [popover]')].find(e => __cr.vis(e) && e.innerText.trim()); if (!e) return null; const r = __cr.R(e); return {text: e.innerText.trim().slice(0, 80), r, font: getComputedStyle(e).fontSize, inside: r[0] >= 0 && r[1] >= 0 && r[0] + r[2] <= innerWidth && r[1] + r[3] <= innerHeight}; })()")
        tips.append(tip)
        if not tip:
            notes.append(f"no hover name over {p['tip']}")
        elif not tip["inside"]:
            notes.append(f"{p['tip']}'s hover name runs off the page {tip['r']}")
        if p is pins[0]:
            shots.append(await J.shot("dock-hover"))
    SB.post(t, SB.WM_MOUSEMOVE, 0, SB.xy(5, 5))
    colours = {p["bg"] for p in pins} | {p["fg"] for p in pins}
    tinted = await J.js("[...document.querySelectorAll('[data-key*=\"/foot/bar/f5565/\"][class*=\"sd_icon_\"]')].length")
    blocked = None
    if not tinted:
        blocked = (f"colour not testable: no pin carries tint= in this world (live dock checked too); handoff step 4 has JEFF set "
                   f"tints at apply. All pins draw {sorted(colours)}")
    elif len(colours) < 3:
        notes.append(f"tinted pins are not coloured apart ({colours})")
    opened = [p["tip"] for p in pins if p["open"]]
    if blocked and not notes:
        J.record("dock-colour", "pins coloured apart by tint", "blocked", blocked, {}, [])
    J.record("dock-look", "compact icons, hover names readable, open markers truthful, nothing overflowing", "pass" if not notes else "fail",
             "; ".join(notes) or f"{len(pins)} pins {pins[0]['r'][2]:.0f}x{pins[0]['r'][3]:.0f}, colours {sorted(colours)}; hover names {[t and t['text'] for t in tips]}; open markers on {opened}",
             {"pins": pins, "tips": tips}, shots + [await J.shot("dock-look")])


async def reload_keeps(J):
    """a changed layout survives a reload exactly"""
    await fixture(J)
    fr = await frame(J)
    await carry_to(J, "Chat", fr[0] + 3, fr[1] + fr[3] / 2)
    b0, s0 = await J.js("__cr.boxes()"), await J.js("__cr.state()")
    await J.reload()
    b1, s1 = await J.js("__cr.boxes()"), await J.js("__cr.state()")
    notes = []
    if s0 != s1:
        notes.append("tree/focus changed over reload")
    if len(b0) != len(b1) or not all(agree(a["r"], b["r"]) for a, b in zip(b0, b1)):
        notes.append(f"boxes changed over reload {[b['r'] for b in b0]} -> {[b['r'] for b in b1]}")
    J.record("reload", reload_keeps.__doc__, "pass" if not notes else "fail", "; ".join(notes) or "chat moved to the left edge; tree and every box identical after reload", {}, [await J.shot("reload")])
    await restore(J)


async def syncdiag(J):
    """does the partition re-sync between a press and its threshold when a carry is lost (diagnosis)"""
    await fixture(J)
    out = []
    fr = await frame(J)
    for k in range(4):
        await J.js("(() => { window.__ev = []; if (!window.__evl) { window.__evl = 1; for (const t of ['pointerdown','pointerup','pointercancel','mousedown','lostpointercapture','gotpointercapture']) document.addEventListener(t, e => window.__ev.push([t, e.pointerId, e.buttons, e.button, (e.target.className || e.target.tagName || '').toString().slice(0, 30), e.defaultPrevented, e.isPrimary]), true); let n = 0; document.addEventListener('pointermove', e => { if (n++ % 4 === 0) window.__ev.push(['move', e.pointerId, e.buttons]); }, true); } })()")
        await J.js("(() => { window.__marks = [...__cr.root().querySelectorAll(':scope > .l-divider')]; window.__root0 = __cr.root(); window.__fetches = 0; if (!window.__fw) { window.__fw = 1; const f = window.fetch; window.fetch = (u, o) => { window.__fetches++; window.__lastFetch = String(u).slice(0, 60); return f(u, o); }; } })()")
        gx, gy = await grip(J, "The board")
        if k >= 2:
            await J.js("getSelection().removeAllRanges()")
        out.append({"before press": {"selected chars": await J.js("__cr.selection()"), "cleared first": k >= 2}})
        seen, _ = await J.hold(gx, gy, [(gx + 30, gy + 10), (fr[0] + fr[2] / 2, fr[1] + fr[3] - 3)],
                               lambda x, y: J.js("({ghost: !!__cr.ghost()})"))
        out.append({"carried": seen[0]["ghost"], "events": [e[0] for e in await J.js("window.__ev.slice(0, 4)")]})
        await J.settle(2)
        await restore(J)
    print(json.dumps(out, indent=1))
    J.record("syncdiag", syncdiag.__doc__, "ran", json.dumps(out), {"runs": out}, [])


async def debug(J):
    """raw state mid-carry (diagnosis only)"""
    await fixture(J)
    fr = await frame(J)
    gx, gy = await grip(J, "The board")
    raw = "({boxes: [...document.querySelectorAll('.landing-box')].map(e => ({hidden: e.hidden, parent: e.parentElement && (e.parentElement.dataset.partition ? 'partition' : e.parentElement.dataset.key), style: e.getAttribute('style'), r: __cr.R(e)})), ghost: __cr.ghost(), gt: (() => { const g = [...document.body.children].find(e => e.style && e.style.zIndex === '40'); return g ? g.style.transform : null; })(), sel: __cr.selection(), resizing: document.documentElement.dataset.resizing || '', active: document.activeElement && document.activeElement.tagName})"
    seen, handle = await J.hold(gx, gy, [(gx + 30, gy + 10), (fr[0] + fr[2] / 2, fr[1] + fr[3] - 3)], lambda x, y: J.js(raw), release=False)
    print(json.dumps(seen, indent=1)[:4000])
    await J.shot("debug-held")
    J.up(handle)
    await J.settle(2)
    print(json.dumps(await J.js("__cr.boxes()"))[:600])
    await J.shot("debug-after")
    J.record("debug", "debug", "ran", "printed", {"seen": seen}, [])
    await restore(J)


async def escdiag(J):
    """which input leaves later carries dead (diagnosis)"""
    await fixture(J)

    async def can_carry():
        gx, gy = await grip(J, "The board")
        seen, handle = await J.hold(gx, gy, [(gx + 40, gy + 120)], lambda x, y: J.js("[!!__cr.ghost(), __cr.selection(), document.elementFromPoint(" + str(gx) + "," + str(gy) + ")?.className]"), release=False)
        await J.shot("escdiag-held")
        J.up(handle)
        await J.settle(1.5)
        await restore(J)
        return seen[0]
    out = {"fresh": await can_carry()}
    J.w.SB.press_key(J.w.SB.focused(J.w.win), "Escape")
    await J.settle(1)
    out["host calls after a bare Escape"] = await J.js("(window.__pt && window.__pt.host || []).slice()")
    out["after a bare Escape"] = await can_carry()
    out["again 1"] = await can_carry()
    await J.w.p.call("Input.dispatchKeyEvent", type="keyDown", key="Escape", code="Escape", windowsVirtualKeyCode=27)
    await J.w.p.call("Input.dispatchKeyEvent", type="keyUp", key="Escape", code="Escape", windowsVirtualKeyCode=27)
    await J.settle(1)
    out["after a DevTools Escape"] = await can_carry()
    J.w.SB.press_key(J.w.SB.focused(J.w.win), "a")
    await J.settle(1)
    out["after a posted 'a' key"] = await can_carry()
    await J.reload()
    gx, gy = await grip(J, "The board")
    _, handle = await J.hold(gx, gy, [(gx + 40, gy + 120)], release=False)
    J.w.SB.press_key(J.w.SB.focused(J.w.win), "Escape")
    await J.settle(0.6)
    J.up(handle)
    await J.settle(1.5)
    out["host calls after Escape mid-carry"] = await J.js("(window.__pt && window.__pt.host || []).slice()")
    out["after Escape mid-carry"] = await can_carry()
    out["again"] = await can_carry()
    out["divider after"] = None
    ds = [c for c in await J.js("__cr.chrome()") if c["label"].startswith("Resize neighbouring")]
    if ds:
        d = ds[0]
        st0 = await J.js("__cr.state()")
        x, y = d["r"][0] + 6, d["r"][1] + d["r"][3] / 2
        await J.hold(x, y, [(x + 80, y)])
        await J.settle(1.6)
        out["divider after"] = (await J.js("__cr.state()")) != st0
        await restore(J)
    out["userSelect"] = await J.js("document.body.style.userSelect")
    await J.reload()
    out["after reload"] = await can_carry()
    print(out)
    J.record("escdiag", escdiag.__doc__, "ran", json.dumps(out), out, [])


# ---- round 2 (c7492): the repaired bytes, with no selection clearing and no masking waits -------------------------

CHAT_TA = "[...document.querySelectorAll('textarea')].find(e => __cr.vis(e) && e.closest('[data-key*=\"lens:jeff-chat\"]'))"
STATUS = "((document.getElementById('status') || {}).textContent || '').slice(0, 160)"


async def wrap_fetch(J):
    """One page-side wrapper for /api/do: window.__delay holds every answer back (ms); window.__refuse answers it refused."""
    await J.js("""(() => { if (window.__dwrap) return; window.__dwrap = 1; window.__delay = 0; window.__refuse = false; const f = window.fetch;
      window.fetch = (u, o) => { if (!String(u).startsWith('/api/do')) return f(u, o);
        if (window.__refuse) return Promise.resolve(new Response(JSON.stringify({ text: 'ERR refused: review test refusal (a7466)' }), { headers: { 'Content-Type': 'application/json' } }));
        return window.__delay ? new Promise(r => setTimeout(r, window.__delay)).then(() => f(u, o)) : f(u, o); }; })()""")


async def answered(J, timeout=5.0):
    """Wait until the world's answer to the last drop is painted (tools rebuilt, none stale); -> ms waited."""
    t0 = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - t0 < timeout:
        ch = await J.js("__cr.chrome()")
        if [c for c in ch if c["cls"] == "l-divider"] and not [p for p in await problems(J) if "stale" in p]:
            return round((asyncio.get_event_loop().time() - t0) * 1000)
        await asyncio.sleep(0.05)
    return None


async def consecutive_paced(J):
    """three carries of the same panel, each started once the previous drop's answer is painted (no selection clearing)"""
    await J.reload()
    await fixture(J)
    fr = await frame(J)
    notes, rows = [], []
    for side, (x, y) in (("bottom", (fr[0] + fr[2] / 2, fr[1] + fr[3] - 3)), ("top", (fr[0] + fr[2] / 2, fr[1] + 3)),
                         ("left", (fr[0] + 3, fr[1] + fr[3] / 2))):
        sel0 = await J.js("__cr.selection()")
        gx, gy = await grip(J, "The board")
        at = await J.js(f"(() => {{ const g = __cr.grip(__cr.byLabel('The board')), e = document.elementFromPoint({gx}, {gy}); return {{grip: g && [g.dataset.key.split('/').slice(-2).join('/'), __cr.R(g)], "
                        f"at: e && [(e.dataset.key || e.className || e.tagName).toString().split('/').slice(-2).join('/'), e.tagName, (e.innerText || '').slice(0, 30), getComputedStyle(e).userSelect], sending: document.querySelectorAll('[data-sending=\"1\"]').length}}; }})()")
        seen, _ = await J.hold(gx, gy, [(gx + 30, gy + 10), (x, y)], lambda a, b: J.js("({ghost: !!__cr.ghost(), sel: __cr.selection(), text: String(getSelection()).slice(0, 60)})"))
        waited = await answered(J)
        rows.append({"side": side, "selected before": sel0, "press": [gx, gy], "pressed on": at, "mid": seen[1], "answer painted after ms": waited})
        if not seen[1]["ghost"] or seen[1]["sel"]:
            notes.append(f"{side}: carry {'started' if seen[1]['ghost'] else 'did not start'}, {seen[1]['sel']} selected")
    b = await box(J, "The board")
    if not b or abs(b["r"][3] - fr[3]) > TOL:
        notes.append(f"final board {b and b['r']}")
    J.record("consecutive-paced", consecutive_paced.__doc__, "pass" if not notes else "fail",
             "; ".join(notes) or f"each carry started with nothing selected and landed; answers painted after {[r['answer painted after ms'] for r in rows]} ms",
             {"rows": rows}, [await J.shot("consecutive-paced")])
    await restore(J)


async def consecutive(J):
    """three carries of the same panel back to back, no wait and no selection clearing: each picks up and lands"""
    await J.reload()
    await fixture(J)
    fr = await frame(J)
    notes, rows, declined = [], [], []
    for side, (x, y) in (("bottom", (fr[0] + fr[2] / 2, fr[1] + fr[3] - 3)), ("top", (fr[0] + fr[2] / 2, fr[1] + 3)),
                         ("left", (fr[0] + 3, fr[1] + fr[3] / 2))):
        before = {"sel": await J.js("__cr.selection()"), "us": await J.js("document.body.style.userSelect")}
        gx, gy = await grip(J, "The board")
        seen, _ = await J.hold(gx, gy, [(gx + 30, gy + 10), (x, y)],
                               lambda a, b: J.js("({ghost: !!__cr.ghost(), sel: __cr.selection(), us: document.body.style.userSelect, pv: __cr.previews().length})"))
        after = {"sel": await J.js("__cr.selection()"), "us": await J.js("document.body.style.userSelect")}
        rows.append({"side": side, "before": before, "mid": seen[1], "after": after})
        # round 3 (c7502): a grab during the previous drop's pending answer is DECLINED by design; it must be clean
        if not seen[1]["ghost"]:
            declined.append(side)
            if seen[1]["sel"]:
                notes.append(f"{side}: declined grab selected {seen[1]['sel']} characters")
        else:
            if seen[1]["sel"]:
                notes.append(f"{side}: {seen[1]['sel']} characters selected mid-carry")
            if seen[1]["us"] != "none":
                notes.append(f"{side}: selection not suppressed mid-carry (userSelect {seen[1]['us']!r})")
        if after["us"] != before["us"]:
            notes.append(f"{side}: userSelect {before['us']!r} -> {after['us']!r} after release")
    await J.settle(2.5)
    notes += await problems(J)
    left = await J.js("__cr.selection()")
    if left:
        notes.append(f"{left} characters still selected at the end (the next carry starting on them would be cancelled)")
    gx, gy = await grip(J, "The board")
    seen, _ = await J.hold(gx, gy, [(gx + 30, gy + 10), (fr[0] + fr[2] / 2, fr[1] + fr[3] - 3)], lambda a, b: J.js("!!__cr.ghost()"))
    if not seen[1]:
        notes.append("the carry after the answers arrived did not start")
    await answered(J)
    J.record("consecutive", consecutive.__doc__, "pass" if not notes else "fail",
             "; ".join(notes) or f"three grabs with no pause: {3 - len(declined)} carried, {len(declined)} declined while an answer was pending ({declined}) with nothing selected and the policy unchanged; the next grab after the answers carried and landed",
             {"rows": rows, "declined": declined}, [await J.shot("consecutive")])
    await restore(J)


async def immediate(J):
    """with the world's answer held back 1.5 s: straight after a drop no obsolete divider/Fit tool stands where panels were, the optimistic layout holds, a second carry is tried, and the answer brings tools back"""
    await J.reload()
    await fixture(J)
    await wrap_fetch(J)
    old = [c for c in await J.js("__cr.chrome()") if c["label"].startswith("Resize neighbouring")]
    await J.js("window.__delay = 1500")
    fr = await frame(J)
    gx, gy = await grip(J, "The board")
    await J.hold(gx, gy, [(gx + 30, gy + 10), (fr[0] + fr[2] / 2, fr[1] + fr[3] - 3)])
    now = {"stale": [p for p in await problems(J) if "stale" in p], "board": await box(J, "The board"),
           "tools": len(await J.js("__cr.chrome()")),
           "at old dividers": [await J.js(f"(() => {{ const e = document.elementFromPoint({c['r'][0] + 6}, {c['r'][1] + c['r'][3] * .25}); return e ? (typeof e.className === 'string' ? e.className.split(' ')[0] : e.tagName) : null; }})()") for c in old]}
    shot = await J.shot("immediate-pending")
    cx, cy = await grip(J, "Chat")
    seen, handle = await J.hold(cx, cy, [(cx - 40, cy + 30)], lambda a, b: J.js("!!__cr.ghost()"), release=False)
    J.w.SB.press_key(J.w.SB.focused(J.w.win), "Escape")
    await asyncio.sleep(0.2)
    J.up(handle)
    second = seen[0]
    await J.settle(3)
    await J.js("window.__delay = 0")
    later = {"stale": [p for p in await problems(J) if "stale" in p], "dividers": len([c for c in await J.js("__cr.chrome()") if c["cls"] == "l-divider"]),
             "board": await box(J, "The board")}
    notes = []
    if now["stale"]:
        notes.append(f"obsolete tools stood right after the drop: {now['stale'][:2]}")
    if "l-divider" in now["at old dividers"]:
        notes.append(f"a press where an old divider was still lands on a divider ({now['at old dividers']})")
    if not now["board"] or abs(now["board"]["r"][2] - fr[2]) > TOL:
        notes.append(f"optimistic layout not held while pending ({now['board'] and now['board']['r']})")
    if later["stale"] or not later["dividers"]:
        notes.append(f"after the answer: stale {later['stale'][:2]}, dividers {later['dividers']}")
    J.record("immediate", immediate.__doc__, "pass" if not notes else "fail",
             "; ".join(notes) or f"pending 1.5 s: no obsolete tool, old divider spots now hit {now['at old dividers']}, board held at {now['board']['r']}; "
             f"a second carry during the pending answer {'started' if second else 'was declined (no ghost) and left nothing behind'}; answer: {later['dividers']} dividers, none stale",
             {"now": now, "later": later, "second carry started": second}, [shot, await J.shot("immediate-answered")])
    await restore(J)


async def refusal(J):
    """a refused drop rolls back to the world's layout, tools come back, the selection policy is restored"""
    f = await fixture(J)
    await wrap_fetch(J)
    b0, us0 = await J.js("__cr.boxes()"), await J.js("document.body.style.userSelect")
    await J.js("window.__refuse = true")
    fr = await frame(J)
    gx, gy = await grip(J, "The board")
    await J.hold(gx, gy, [(gx + 30, gy + 10), (fr[0] + fr[2] / 2, fr[1] + fr[3] - 3)])
    await J.settle(2.5)
    await J.js("window.__refuse = false")
    b1, st, status = await J.js("__cr.boxes()"), await J.js("__cr.state()"), await J.js(STATUS)
    notes = []
    if json.loads(st["tree"]) != json.loads(f["tree"]):
        notes.append("the world tree changed despite the refusal")
    if len(b0) != len(b1) or not all(agree(a["r"], b["r"]) for a, b in zip(b0, b1)):
        notes.append(f"the page did not roll back ({[b['r'] for b in b1]})")
    if "review test refusal" not in status:
        notes.append(f"the refusal was not said ({status!r})")
    if await J.js("document.body.style.userSelect") != us0 or await J.js("__cr.selection()"):
        notes.append("selection policy/state not restored after the refusal")
    notes += await problems(J)
    if not [c for c in await J.js("__cr.chrome()") if c["cls"] == "l-divider"]:
        notes.append("no dividers after the rollback")
    J.record("refusal", refusal.__doc__, "pass" if not notes else "fail",
             "; ".join(notes) or f"refused drop rolled back to the world's boxes, dividers back, status {status!r}",
             {"status": status}, [await J.shot("refusal")])
    await restore(J)


async def cancel_policy(J):
    """Escape, resize and blur mid-carry each restore the page's own selection policy, including a prior inline one"""
    await fixture(J)
    fr = await frame(J)
    notes, seen_rows = [], []
    for prior in ("", "text"):
        await J.js(f"document.body.style.userSelect = {json.dumps(prior)}")
        for how in ("escape", "resize", "blur"):
            gx, gy = await grip(J, "The board")
            seen, handle = await J.hold(gx, gy, [(gx + 30, gy + 10), (fr[0] + fr[2] / 2, fr[1] + fr[3] - 3)],
                                        lambda a, b: J.js("document.body.style.userSelect"), release=False)
            if how == "escape":
                J.w.SB.press_key(J.w.SB.focused(J.w.win), "Escape")
            else:
                await J.js(f"window.dispatchEvent(new Event({json.dumps(how)}))")
            await asyncio.sleep(0.3)
            J.up(handle)
            await J.settle(1.2)
            us, sel, st, gh = await J.js("document.body.style.userSelect"), await J.js("__cr.selection()"), await J.js("__cr.state()"), await J.js("__cr.ghost()")
            seen_rows.append([prior, how, seen[1], us, sel])
            if seen[1] != "none":
                notes.append(f"prior {prior!r} {how}: not suppressed mid-carry ({seen[1]!r})")
            if us != prior:
                notes.append(f"prior {prior!r} {how}: userSelect {us!r} after cancel")
            if sel or gh:
                notes.append(f"prior {prior!r} {how}: selection {sel} / ghost left")
            if json.loads(st["tree"]) != json.loads((await fixture(J))["tree"]):
                notes.append(f"prior {prior!r} {how}: the cancel committed")
                await restore(J)
    await J.js("document.body.style.userSelect = ''")
    J.record("cancel-policy", cancel_policy.__doc__, "pass" if not notes else "fail",
             "; ".join(notes) or "6 cancels (prior '' and 'text' × Escape, resize, blur): suppressed mid-carry, prior policy back, nothing selected or committed (resize/blur are dispatched events)",
             {"rows": seen_rows}, [await J.shot("cancel-policy")])


async def composer(J):
    """an unsent draft, its selected range and the chat's context survive carries and a divider drag"""
    await fixture(J)
    c = await J.js(f"(() => {{ const t = {CHAT_TA}; return t ? __cr.hit(t) : null; }})()")
    if not c or not c["ok"]:
        J.record("composer", composer.__doc__, "blocked", f"the chat composer cannot be pressed at this size ({c})", {}, [await J.shot("composer-cut")])
        return
    await J.w.click(c["x"], c["y"])
    await asyncio.sleep(0.3)
    await J.w.type("unsent review draft")
    await J.js(f"{CHAT_TA}.setSelectionRange(3, 9)")
    read = f"(() => {{ const t = {CHAT_TA}; const chat = t.closest('[data-key*=\"lens:jeff-chat\"]'); return {{ v: t.value, s: t.selectionStart, e: t.selectionEnd, ctx: (() => {{ const s = (__cr.byLabel('Chat') || chat).innerText.replace(/\\s+/g, ' '); const i = s.lastIndexOf('Attach open item'); return i < 0 ? 'no context row' : s.slice(i, i + 120); }})() }}; }})()"
    v0 = await J.js(read)
    out, notes = {"start": v0}, []
    fr = await frame(J)
    await carry_to(J, "The board", fr[0] + fr[2] / 2, fr[1] + fr[3] - 3)
    out["after drop"] = await J.js(read)
    await carry_to(J, "The board", fr[0] + 3, fr[1] + fr[3] / 2)
    out["after second drop"] = await J.js(read)
    ds = [d for d in await J.js("__cr.chrome()") if d["label"].startswith("Resize neighbouring")]
    if ds:
        d = ds[0]
        x, y = d["r"][0] + d["r"][2] / 2, d["r"][1] + d["r"][3] / 2
        await J.hold(x, y, [(x + 60, y)] if d["axis"] == "x" else [(x, y + 60)])
        await J.settle(1.6)
        out["after divider"] = await J.js(read)
    for k, v in out.items():
        if k != "start" and v != v0:
            notes.append(f"{k}: {v} (was {v0})")
    sent = await J.js("[...document.querySelectorAll('[data-key*=\"lens:jeff-chat\"]')].some(e => e.innerText.includes('unsent review draft') && !e.querySelector('textarea') && e.tagName !== 'TEXTAREA')")
    if sent:
        notes.append("the draft appears outside the composer (sent?)")
    J.record("composer", composer.__doc__, "pass" if not notes else "fail",
             "; ".join(notes) or f"words, range {v0['s']}-{v0['e']} and context {v0['ctx']} unchanged through two drops and a divider; nothing sent",
             out, [await J.shot("composer")])
    await restore(J)


async def tabs_focus(J):
    """drops started from a tab group and from focused mode: preview == result"""
    await fixture(J)
    notes, shots = [], []
    v = await box(J, "Viewer")
    await carry_to(J, "The board", v["r"][0] + v["r"][2] / 2, v["r"][1] + v["r"][3] / 2)
    shown = [b["label"] for b in await J.js("__cr.boxes()")]
    member = "The board" if "The board" in shown else "Viewer"
    other = "Viewer" if member == "The board" else "The board"
    fr = await frame(J)
    seen = await carry_to(J, member, fr[0] + fr[2] / 2, fr[1] + fr[3] - 3)
    pv = [p for p in seen[1]["previews"] if p["in"] == "partition"]
    b = await box(J, member)
    if not pv or not b or not agree(pv[0]["r"], b["r"]) or abs(b["r"][2] - fr[2]) > TOL:
        notes.append(f"from a tab: preview {pv and pv[0]['r']} result {b and b['r']}")
    if not await box(J, other):
        notes.append(f"{other} vanished when its tab partner left")
    shots.append(await J.shot("tab-drop"))
    await restore(J)
    x, y = await grip(J, "The board")
    await J.w.dblclick(x, y)
    await J.settle(2)
    if not (await J.js("__cr.state()"))["focus"]:
        notes.append("could not enter focus")
    else:
        fr = await frame(J)
        seen = await carry_to(J, "Chat", fr[0] + fr[2] / 2, fr[1] + fr[3] - 3)
        pv = [p for p in seen[1]["previews"] if p["in"] == "partition"]
        b, st = await box(J, "Chat"), await J.js("__cr.state()")
        if st["focus"]:
            notes.append("a drop in focus did not exit focus")
        if not pv or not b or not agree(pv[0]["r"], b["r"]):
            notes.append(f"from focus: preview {pv and pv[0]['r']} result {b and b['r']}")
        notes += await problems(J)
        shots.append(await J.shot("focus-drop"))
    J.record("tabs-focus", tabs_focus.__doc__, "pass" if not notes else "fail",
             "; ".join(notes) or f"{member} carried out of its tab group to the bottom (preview = result, {other} stays); Chat dropped at the bottom from focus: focus exits, preview = result",
             {}, shots)
    await restore(J)


async def receivers(J):
    """the dock or the carried panel changing while held: the drop is refused and nothing falls back to a split"""
    f = await fixture(J)
    dock = await J.js("(() => { const d = document.querySelector('[data-key$=\"/foot/bar/f5565\"]'); return d ? __cr.R(d) : null; })()")
    count = "[...document.querySelectorAll('[data-key*=\"/foot/bar/f5565/\"]')].filter(e => /\\/apps\\/a\\d+$/.test(e.dataset.key) && __cr.vis(e)).map(e => (e._n.paint.tip || [])[0])"
    notes, shots = [], []
    p0 = await J.js(count)
    gx, gy = await grip(J, "Viewer")
    seen, handle = await J.hold(gx, gy, [(gx + 30, gy + 10), (dock[0] + dock[2] / 2, dock[1] + dock[3] / 2)], lambda a, b: J.js("__cr.previews()"), release=False)
    J.copy.do("look f5565", "hud-playtest")
    said = J.copy.do('do create f5565 kind=note title="review probe" role=dock-pin glyph=• opens=f155', "hud-playtest")
    await asyncio.sleep(1.0)
    J.up(handle)
    await J.settle(2.5)
    p1, st, status1 = await J.js(count), await J.js("__cr.state()"), await J.js(STATUS)
    viewer_pins = [t for t in p1 if t and t.lower().startswith("viewer")]
    if len(viewer_pins) > len([t for t in p0 if t and t.lower().startswith("viewer")]):
        notes.append(f"the drop on the changed dock still pinned the viewer ({p1})")
    if json.loads(st["tree"]) != json.loads(f["tree"]):
        notes.append("the refused dock drop fell back to rearranging the tree")
        await restore(J)
    shots.append(await J.shot("receiver-changed"))
    fr = await frame(J)
    gx, gy = await grip(J, "The board")
    _, handle = await J.hold(gx, gy, [(gx + 30, gy + 10), (fr[0] + fr[2] / 2, fr[1] + fr[3] - 3)], release=False)
    J.copy.do("read a5674", "hud-playtest")
    J.copy.do("do prop a5674 about=\"review probe\"", "hud-playtest")
    await asyncio.sleep(1.0)
    J.up(handle)
    await J.settle(2.5)
    st2, status2 = await J.js("__cr.state()"), await J.js(STATUS)
    if json.loads(st2["tree"]) != json.loads(f["tree"]):
        notes.append(f"a drop of a panel changed while held still committed ({status2!r})")
    shots.append(await J.shot("carried-changed"))
    J.copy.do("read a5674", "hud-playtest")
    J.copy.do("do prop a5674 about=\"\"", "hud-playtest")
    J.record("receivers", receivers.__doc__, "pass" if not notes else "fail",
             "; ".join(notes) or f"dock changed while held: no viewer pin, tree untouched (status {status1!r}); board changed while held: no commit (status {status2!r})",
             {"probe": said[:160], "pins before": p0, "pins after": p1}, shots)
    await restore(J)


async def doc_pins(J):
    """pin the viewer's surface and a document by the viewer title; each pin opens it; the window-definition pin offers Open as a window and asks the host"""
    await fixture(J)
    pins = "[...document.querySelectorAll('[data-key*=\"/foot/bar/f5565/\"]')].filter(e => /\\/apps\\/a\\d+$/.test(e.dataset.key) && __cr.vis(e)).map(e => ({id: e.dataset.key.split('/').pop(), tip: (e._n.paint.tip || [])[0], h: __cr.hit(e)}))"
    vtitle = ("(() => { const p = __cr.byLabel('Viewer'); const g = [...p.querySelectorAll('[data-carry]')].filter(g => __cr.vis(g) && g._n && g._n.fence && "
              "g._n.fence.item !== p._n.paint.partition_item); const t = g[0]; return t ? {hit: __cr.hit(t), text: t.innerText.trim().slice(0, 60)} : null; })()")
    dock = await J.js("(() => { const d = document.querySelector('[data-key$=\"/foot/bar/f5565\"]'); return d ? __cr.R(d) : null; })()")
    notes, shots, made = [], [], []
    for what in ("surface", "document"):
        if what == "document":
            b = await J.js("(() => { const b = [...__cr.byLabel('Viewer').querySelectorAll('[data-key]')].find(x => x.innerText.trim() === 'The lowdown' && __cr.vis(x)); return b ? __cr.hit(b) : null; })()")
            if not b:
                notes.append("no 'The lowdown' chip in the viewer to open a document")
                break
            await J.w.click(b["x"], b["y"])
            await J.settle(2)
        t = await J.js(vtitle)
        if not t or not t["hit"]["ok"]:
            notes.append(f"no pressable viewer title for the {what} ({t})")
            continue
        p0 = await J.js(pins)
        await J.hold(t["hit"]["x"], t["hit"]["y"], [(t["hit"]["x"] + 30, t["hit"]["y"] + 10), (dock[0] + dock[2] - 4, dock[1] + dock[3] / 2)])
        await J.settle(2.5)
        p1 = await J.js(pins)
        new = [p for p in p1 if p["id"] not in {x["id"] for x in p0}]
        if len(new) != 1:
            notes.append(f"pinning the {what} {t['text']!r} made {len(new)} pins")
        else:
            made.append((what, t["text"], new[0]))
        shots.append(await J.shot(f"pin-{what}"))
    for what, title, pin in made[:1]:
        p = [x for x in await J.js(pins) if x["id"] == pin["id"]][0]
        await J.w.click(p["h"]["x"], p["h"]["y"])
        await J.settle(2.5)
        t = await J.js(vtitle)
        if not t or title.split()[0] not in t["text"]:
            notes.append(f"its pin did not reopen the {what} {title!r} (viewer shows {t and t['text']!r})")
        shots.append(await J.shot("pin-reopened"))
    w = [x for x in await J.js(pins) if x["tip"] == "Writing room"]
    host = None
    if w:
        await J.w.click(w[0]["h"]["x"], w[0]["h"]["y"], right=True)
        await J.settle(0.8)
        menu = await J.js("(() => { const m = document.getElementById('menu-pop'); return m ? [...m.querySelectorAll('button')].map(b => b.textContent) : null; })()")
        if not menu or "Open as a window" not in menu:
            notes.append(f"the window-definition pin's menu is {menu}")
            await J.w.key("Escape")
        else:
            r = await J.js("(() => { const b = [...document.querySelectorAll('#menu-pop button')].find(b => b.textContent === 'Open as a window'); const r = b.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; })()")
            await J.w.click(*r)
            await J.settle(1.5)
            host = await J.js("(window.__pt && window.__pt.host || []).slice(-3)")
            if not any("window" in h and "writing" in h for h in host):
                notes.append(f"Open as a window asked the host {host}")
    else:
        notes.append("no Writing room pin")
    J.record("doc-pins", doc_pins.__doc__, "pass" if not notes else "fail",
             "; ".join(notes) or f"pinned {[(w_, t_) for w_, t_, _ in made]} by the viewer title, one pin each; the surface pin reopened it; Writing room: 'Open as a window' asked the (stand-in) host {host}",
             {"made": made, "host": host}, shots)
    await restore(J)


async def tints(J):
    """the staged optional tints applied to the copy (a5567 purple, a5569 amber, a5571 blue, a5573 green): pins coloured apart"""
    for pid, tint in (("a5567", "purple"), ("a5569", "amber"), ("a5571", "blue"), ("a5573", "green")):
        J.copy.do(f"read {pid}", "hud-playtest")
        J.copy.do(f"do prop {pid} tint={tint}", "hud-playtest")
    await J.settle(2.5)
    pins = await J.js("[...document.querySelectorAll('[data-key*=\"/foot/bar/f5565/\"]')].filter(e => /\\/apps\\/a\\d+$/.test(e.dataset.key) && __cr.vis(e)).map(e => { const i = e.querySelector('[data-key$=\"/icon\"]') || e; const g = e.querySelector('[data-key*=\"/glyph\"]') || i; return {tip: (e._n.paint.tip || [])[0], cls: i.className, bg: getComputedStyle(i).backgroundColor, fg: getComputedStyle(g).color}; })")
    staged = {"JEFF": "purple", "Board": "amber", "Conversation": "blue", "Writing room": "green"}
    looks = {p["tip"]: (p["bg"], p["fg"]) for p in pins if p["tip"] in staged}
    notes = []
    if len(set(looks.values())) < 3:
        notes.append(f"tinted pins are not coloured apart: {looks}")
    if "sd_icon_blue" not in " ".join(p["cls"] for p in pins):
        blue = looks.get("Conversation")
        notes_blue = f"tint=blue has no role in home-dock (green/amber/purple/rose only): Conversation draws {blue}, the untinted default"
    else:
        notes_blue = ""
    J.record("tints", tints.__doc__, "pass" if not notes else "fail",
             "; ".join(notes) or f"coloured apart: {looks}" + (f"; note: {notes_blue}" if notes_blue else ""),
             {"pins": pins}, [await J.shot("tints")])


async def workspace_identity(J):
    """EMULATED workspace switch (no workspace exists in the world): the layout is replaced by its own copy; the tree's typed refs remap to the copy's panels with the same geometry; a panel pin opens a panel of the CURRENT layout"""
    f = await fixture(J)
    pins = "[...document.querySelectorAll('[data-key*=\"/foot/bar/f5565/\"]')].filter(e => /\\/apps\\/a\\d+$/.test(e.dataset.key) && __cr.vis(e)).map(e => ({id: e.dataset.key.split('/').pop(), tip: (e._n.paint.tip || [])[0], h: __cr.hit(e)}))"
    notes, shots = [], []
    if not [p for p in await J.js(pins) if p["tip"] == "The board"]:
        dock = await J.js("(() => { const d = document.querySelector('[data-key$=\"/foot/bar/f5565\"]'); return __cr.R(d); })()")
        await carry_to(J, "The board", dock[0] + dock[2] - 4, dock[1] + dock[3] / 2)
    b0 = await J.js("__cr.boxes()")
    old_ids = {b["id"] for b in b0}
    J.copy.do("look f5204", "hud-playtest")
    said = J.copy.do(f"do copy {f['layout']} into=f5204", "hud-playtest")
    import re
    found = J.copy.do("find kind:surface,prop:role=home-layout,prop:actor=alex", "hud-playtest")
    ids = [i for i in re.findall(r"^\s+(f\d+) ", found, re.M) if i != f["layout"]]
    new = ids[0] if len(ids) == 1 else None
    if not new or new == f["layout"]:
        J.record("workspace", workspace_identity.__doc__, "blocked", f"could not read the copied layout's id: {said[:200]}", {}, [])
        return
    J.copy.do(f"look {f['layout']}", "hud-playtest")
    J.copy.do(f"do prop {f['layout']} role=workspace-review-old", "hud-playtest")
    J.copy.do(f"look {new}", "hud-playtest")
    J.copy.do(f"do prop {new} role=home-layout", "hud-playtest")
    await J.settle(3)
    root = await J.js("__cr.root() && __cr.root()._n.fence.item")
    b1 = await J.js("__cr.boxes()")
    tree_ids = set(re.findall(r'"\$ref": ?"(a\d+)"', (await J.js("__cr.state()"))["tree"]))
    member_ids = set(await J.js("__cr.members().map(e => e._n.paint.partition_item)"))
    if root != new:
        notes.append(f"the page still paints {root}, not the copy {new}")
    if tree_ids & old_ids:
        notes.append(f"the copy's tree still names old panels {sorted(tree_ids & old_ids)}")
    if not tree_ids <= member_ids:
        notes.append(f"tree refs {sorted(tree_ids - member_ids)} are not the copy's panels")
    if len(b0) != len(b1) or not all(agree(a["r"], b["r"]) for a, b in zip(b0, b1)):
        notes.append(f"geometry changed with the copy: {[b['r'] for b in b1]}")
    shots.append(await J.shot("workspace-copy"))
    h = await J.js("(() => { const e = __cr.byLabel('The board'); const b = e && [...e.querySelectorAll('[data-key]')].find(x => x.innerText.trim() === '–' && __cr.vis(x)); return b ? __cr.hit(b) : null; })()")
    if h:
        await J.w.click(h["x"], h["y"])
        await J.settle(2)
        p = [x for x in await J.js(pins) if x["tip"] == "The board"]
        if p:
            await J.w.click(p[0]["h"]["x"], p[0]["h"]["y"])
            await J.settle(2.5)
            boards = [b for b in await J.js("__cr.boxes()") if "board" in b["label"].lower()]
            if len(boards) != 1:
                notes.append(f"{len(boards)} boards after opening the pin in the copied layout")
            elif boards[0]["id"] in old_ids:
                notes.append(f"the pin opened the OLD layout's panel {boards[0]['id']}")
        else:
            notes.append("no board pin to open")
    else:
        notes.append("no shelf control on the board in the copied layout")
    shots.append(await J.shot("workspace-pin"))
    J.record("workspace", workspace_identity.__doc__, "pass" if not notes else "fail",
             "; ".join(notes) or f"layout {f['layout']} replaced by its copy {new}: typed refs remapped to the copy's panels, geometry identical; the board pin reopened the copy's own panel",
             {"new": new, "tree ids": sorted(tree_ids)}, shots)


# ---- round 3 (c7505): the busy-declined press, and the focus-drop mismatch measured ----------------------------

async def busy(J):
    """answer held back 1.5 s: a grab during the pending answer is declined cleanly (no ghost, nothing selected, no tree change, policy unchanged); after the answer the next carry works and lands"""
    await J.reload()
    f = await fixture(J)
    await wrap_fetch(J)
    await J.js("window.__ev = []; if (!window.__evb) { window.__evb = 1; for (const t of ['pointerdown','pointercancel','selectstart','dragstart']) document.addEventListener(t, e => window.__ev.push([t, e.defaultPrevented]), false); }")
    await J.js("window.__delay = 1500")
    fr = await frame(J)
    gx, gy = await grip(J, "The board")
    await J.hold(gx, gy, [(gx + 30, gy + 10), (fr[0] + fr[2] / 2, fr[1] + fr[3] - 3)])
    planned = await box(J, "The board")
    await J.js("window.__ev = []")
    us0 = await J.js("document.body.style.userSelect")
    bx, by = await grip(J, "The board")
    seen, handle = await J.hold(bx, by, [(bx + 30, by - 10), (fr[0] + fr[2] / 2, fr[1] + 3)],
                                lambda a, b: J.js("({ghost: !!__cr.ghost(), sel: __cr.selection(), us: document.body.style.userSelect, pv: __cr.previews().length})"), release=False)
    J.up(handle)
    await asyncio.sleep(0.2)
    declined = {"mid": seen[1], "after": {"sel": await J.js("__cr.selection()"), "us": await J.js("document.body.style.userSelect"), "board": await box(J, "The board")},
                "events": await J.js("window.__ev.slice(0, 8)")}
    shot1 = await J.shot("busy-declined")
    waited = await answered(J, 6)
    await J.js("window.__delay = 0")
    st = json.loads((await J.js("__cr.state()"))["tree"])
    gx, gy = await grip(J, "The board")
    seen2, _ = await J.hold(gx, gy, [(gx + 30, gy + 10), (fr[0] + 3, fr[1] + fr[3] / 2)], lambda a, b: J.js("({ghost: !!__cr.ghost(), sel: __cr.selection(), pv: __cr.previews()})"))
    await answered(J)
    after = await box(J, "The board")
    notes = []
    if declined["mid"]["ghost"]:
        notes.append("the grab during the pending answer started a carry")
    if declined["mid"]["sel"] or declined["after"]["sel"]:
        notes.append(f"the declined grab selected {max(declined['mid']['sel'], declined['after']['sel'])} characters")
    if declined["after"]["us"] != us0 or declined["mid"]["us"] != us0:
        notes.append(f"the declined grab changed userSelect ({us0!r} -> {declined['mid']['us']!r}/{declined['after']['us']!r})")
    if [e for e in declined["events"] if e[0] in ("pointercancel", "dragstart")]:
        notes.append(f"native drag events fired: {declined['events']}")
    if not declined["after"]["board"] or not agree(declined["after"]["board"]["r"], planned["r"]):
        notes.append(f"the optimistic layout moved under the declined grab ({declined['after']['board'] and declined['after']['board']['r']} vs {planned['r']})")
    if waited is None:
        notes.append("the held-back answer never repainted the tools")
    if json.loads(f["tree"]) == st:
        notes.append("the first drop did not commit")
    if not seen2[1]["ghost"] or seen2[1]["sel"]:
        notes.append(f"the carry after the answer: ghost {seen2[1]['ghost']}, selected {seen2[1]['sel']}")
    pv = [p for p in seen2[1]["pv"] if p["in"] == "partition"]
    if not pv or not after or not agree(pv[0]["r"], after["r"]):
        notes.append(f"after-answer drop: preview {pv and pv[0]['r']} result {after and after['r']}")
    J.record("busy", busy.__doc__, "pass" if not notes else "fail",
             "; ".join(notes) or f"declined cleanly (no ghost, 0 selected, userSelect {us0!r} kept, events {[e[0] for e in declined['events']]}, layout held); answer painted after {waited} ms; the next carry started with nothing selected and landed at its preview {after['r']}",
             {"declined": declined, "answer ms": waited, "next": seen2[1], "result": after}, [shot1, await J.shot("busy-after")])
    await restore(J)


PLOG = r"""(() => { if (window.__plogged) return; window.__plogged = 1; const P = window.Partition; window.__plog = { plan: null, geometry: [] };
  const opts = o => o && { minimum: o.minimum, gap: o.gap, tab: o.tab, visible: o.visible ? [...o.visible] : null, intrinsic: o.intrinsic || null };
  const plan = P.plan, geometry = P.geometry;
  P.plan = function (tree, dragged, target, bounds, options) { const r = plan.apply(this, arguments);
    window.__plog.plan = { tree: JSON.stringify(tree), dragged, target, bounds, options: opts(options), result: r && { box: r.box, tree: JSON.stringify(r.tree) } }; return r; };
  P.geometry = function (root, bounds, options) { const r = geometry.apply(this, arguments);
    window.__plog.geometry.push({ root: JSON.stringify(root), bounds, options: opts(options), boxes: r.boxes, splits: r.splits.map(s => ({ path: s.path, mins: s.mins, gap: s.gap, box: s.box, children: s.children })) });
    if (window.__plog.geometry.length > 6) window.__plog.geometry.shift(); return r; }; })()"""


async def focusdiag(J):
    """MEASUREMENT for the owner (c7505): focused Board, Chat carried to the desk's bottom edge; root client size and rect, preview / post-release / post-answer rectangles, tree and focus, and the actual P.plan and P.geometry inputs. No tolerance widened"""
    await J.reload()
    await fixture(J)
    await J.js(PLOG)
    root = ("(() => { const r = __cr.root(); const chain = []; for (let e = r; e && e !== document.body; e = e.parentElement) { "
            "const sibs = [...(e.parentElement ? e.parentElement.children : [])].filter(s => s !== e && __cr.vis(s)).map(s => [(s.dataset.key || s.className || s.tagName).toString().split('/').slice(-2).join('/'), __cr.R(s)]); "
            "chain.push([(e.dataset.key || e.className || e.tagName).toString().split('/').slice(-2).join('/'), __cr.R(e), sibs.slice(0, 6)]); if (chain.length > 7) break; } "
            "return { client: [r.clientWidth, r.clientHeight], rect: __cr.R(r), offset: [r.offsetLeft, r.offsetTop, r.offsetWidth, r.offsetHeight], ancestors: chain }; })()")
    out = {"root before focus": await J.js(root)}
    x, y = await grip(J, "The board")
    await J.w.dblclick(x, y)
    await answered(J)
    await J.settle(1)
    toprow = ("(() => { const t = document.querySelector('[data-key$=\"f5664/top\"]'); if (!t) return null; const walk = (e, d) => [...e.children].filter(__cr.vis).flatMap(k => "
              "[[(k.dataset.key || k.className || k.tagName).toString().split('/').slice(-2).join('/'), __cr.R(k), getComputedStyle(k).lineHeight, (k.innerText || '').split('\\n')[0].slice(0, 24)], ...(d < 3 ? walk(k, d + 1) : [])]); "
              "return { rect: __cr.R(t), parts: walk(t, 0).slice(0, 40) }; })()")
    lgstat = ("[...document.querySelectorAll('[class*=\"lgstat\"]')].filter(__cr.vis).map(e => { const s = getComputedStyle(e); "
              "return [e.className, __cr.R(e), s.borderTopWidth + ' ' + s.borderBottomWidth + ' ' + s.borderLeftWidth, s.borderTopStyle, s.borderTopColor, (e.innerText || '').replace(/\\s+/g, ' ').slice(0, 20)]; })")
    out["count chips in focus"] = await J.js(lgstat)
    out["top row in focus"] = await J.js(toprow)
    out["state in focus"] = await J.js("__cr.state()")
    out["root in focus"] = await J.js(root)
    out["boxes in focus"] = await J.js("__cr.boxes()")
    await J.js("window.__plog.geometry = []; window.__plog.plan = null")
    fr = await frame(J)
    cx, cy = await grip(J, "Chat")
    seen, handle = await J.hold(cx, cy, [(cx + 30, cy + 10), (fr[0] + fr[2] / 2, fr[1] + fr[3] - 3)],
                                lambda a, b: J.js(f"({{previews: __cr.previews(), plan: window.__plog.plan, root: {root}}})"), release=False)
    out["root at pickup"] = seen[0]["root"]
    out["root at the preview"] = seen[1]["root"]
    out["preview"] = seen[1]["previews"]
    out["P.plan at the preview"] = seen[1]["plan"]
    await J.js("window.__plog.geometry = []")
    J.up(handle)
    await asyncio.sleep(0.05)
    out["chat right after release"] = await box(J, "Chat")
    out["root right after release"] = await J.js(root)
    out["P.geometry calls by release"] = await J.js("window.__plog.geometry.slice()")
    await J.js("window.__plog.geometry = []")
    out["answer painted after ms"] = await answered(J)
    await J.settle(0.5)
    out["chat after the answer"] = await box(J, "Chat")
    out["root after the answer"] = await J.js(root)
    out["state after the answer"] = await J.js("__cr.state()")
    out["top row after the answer"] = await J.js(toprow)
    out["count chips after the answer"] = await J.js(lgstat)
    tf, ta = out["top row in focus"] or {}, out["top row after the answer"] or {}
    after = {p[0]: p for p in ta.get("parts", [])}
    out["top row parts that changed"] = [[p[0], p[1], (after.get(p[0]) or [None, None])[1], p[3]] for p in tf.get("parts", [])
                                         if not after.get(p[0]) or any(abs(a - b) > 0.5 for a, b in zip(p[1], after[p[0]][1]))]
    out["P.geometry calls after the answer"] = await J.js("window.__plog.geometry.slice(-3)")
    pv = [p for p in out["preview"] if p["in"] == "partition"]
    a, b = (pv[0]["r"] if pv else None), (out["chat after the answer"] or {}).get("r")
    diff = [round(q - p, 2) for p, q in zip(a, b)] if a and b else None
    out["preview minus result"] = diff
    # c7522: the root and the layout's top row at each stage; a frame that changes size under the preview is the drift
    def top_row(r):
        for _, _, sibs in (r or {}).get("ancestors", []):
            for name, rr in sibs:
                if name.endswith("/top") or name == "top":
                    return rr
        return None
    stages = {s: out.get(f"root {s}") for s in ("in focus", "at pickup", "at the preview", "right after release", "after the answer")}
    out["frames by stage"] = {s: {"root": (r or {}).get("rect"), "client": (r or {}).get("client"), "top row": top_row(r)} for s, r in stages.items()}
    heights = [v["root"][3] for v in out["frames by stage"].values() if v["root"]]
    out["root height spread"] = round(max(heights) - min(heights), 2) if heights else None
    (J.out / "focusdiag.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    ok = bool(diff) and all(abs(d) <= TOL for d in diff) and (out["root height spread"] or 0) <= TOL
    J.record("focusdiag", focusdiag.__doc__, "pass" if ok else "fail",
             f"preview {a}, right after release {(out['chat right after release'] or {}).get('r')}, after the answer {b}; difference {diff}; "
             f"root height spread across focus/pickup/preview/release/answer {out['root height spread']} px; "
             f"count chips in focus {[(c[0], c[1][3], c[2]) for c in out['count chips in focus'] or []]}, after {[(c[0], c[1][3], c[2]) for c in out['count chips after the answer'] or []]}; "
             + "; ".join(f"{s}: root {v['root']} top row {v['top row']}" for s, v in out["frames by stage"].items()) + "; full capture in focusdiag.json",
             {"file": "focusdiag.json"}, [await J.shot("focusdiag")])
    await restore(J)


CONTAIN = r"""(() => { const root = __cr.root(), cs = getComputedStyle(root), fr = __cr.R(root), out = { contain: cs.contain, root: fr, client: [root.clientWidth, root.clientHeight], panels: [], fixed: [] };
  for (const p of [...root.children].filter(e => e._n && e._n.paint.partition_item && __cr.vis(e))) {
    const r = __cr.R(p), sc = [...p.querySelectorAll('*')].filter(e => { const s = getComputedStyle(e); return /auto|scroll/.test(s.overflowY) && e.scrollHeight > e.clientHeight + 1 && e.clientHeight > 0; });
    const kids = [...p.children].filter(__cr.vis).map(k => __cr.R(k));
    out.panels.push({ label: (p.querySelector('[data-carry]') || p).innerText.split('\n')[0].slice(0, 30), r, inside: r[0] >= fr[0] - 1 && r[1] >= fr[1] - 1 && r[0] + r[2] <= fr[0] + fr[2] + 1 && r[1] + r[3] <= fr[1] + fr[3] + 1,
      cut: p.scrollWidth > p.clientWidth + 1, scrollers: sc.length, kids: kids.length, widest: Math.max(0, ...kids.map(k => k[2])) });
  }
  for (const e of root.querySelectorAll('*')) { const s = getComputedStyle(e); if (s.position === 'fixed' && __cr.vis(e)) out.fixed.push({ key: (e.dataset.key || e.className).toString().split('/').slice(-2).join('/'), r: __cr.R(e), top: s.top, left: s.left, popover: !!(e.popover && e.matches(':popover-open')) }); }
  return out; })()"""


async def containment(J):
    """c7522: the bounded partition with contain: no clipped or empty panels, a root that is not empty or shrunk, fixed descendants placed against the page, a part menu at the pointer, wheel scroll inside a panel, focus/pin geometry"""
    await J.reload()
    await fixture(J)
    fr0 = await frame(J)
    c = await J.js(CONTAIN)
    bad = []
    if not c["root"] or c["root"][2] < 100 or c["root"][3] < 100:
        bad.append(f"root is {c['root']}")
    for p in c["panels"]:
        if not p["inside"]: bad.append(f"{p['label']} outside the root")
        if p["cut"]: bad.append(f"{p['label']} cut sideways")
        if p["r"][2] < 40 or p["r"][3] < 40 or not p["kids"]: bad.append(f"{p['label']} empty or shrunk {p['r']}")
    # fixed descendants inside a layout-contained root are placed against the root, not the page: their rect top must equal their style top
    for f in c["fixed"]:
        try:
            if not f["popover"] and abs(float(f["top"].rstrip("px")) - f["r"][1]) > 1: bad.append(f"fixed {f['key']} at {f['r'][1]} but asks top {f['top']} (placed against the root)")
        except ValueError:
            pass
    # a part menu at the pointer (menus are body-level, so this checks the press reaches the part through the root)
    menu = None
    card = await J.js("(() => { const e = [...__cr.root().querySelectorAll('[data-menu]')].find(e => __cr.vis(e) && e.getBoundingClientRect().height > 8); if (!e) return null; const r = e.getBoundingClientRect(); return [r.left + Math.min(20, r.width / 2), r.top + r.height / 2]; })()")
    if card:
        await J.w.click(card[0], card[1], right=True)
        await asyncio.sleep(0.4)
        menu = await J.js("(() => { const m = document.getElementById('menu-pop'); return m ? __cr.R(m) : null; })()")
        iw, ih = await J.js("[innerWidth, innerHeight]")
        if menu and (abs(menu[0] - card[0]) > 300 or abs(menu[1] - card[1]) > 300 or menu[0] < 0 or menu[1] < 0
                     or menu[0] + menu[2] > iw + 1 or menu[1] + menu[3] > ih + 1):
            bad.append(f"menu at {menu}, pressed at {card}")
        await J.w.key("Escape")
        await asyncio.sleep(0.3)
    # wheel inside the first panel that scrolls
    wheel = await J.js("(() => { const root = __cr.root(); const e = [...root.querySelectorAll('*')].find(e => { const s = getComputedStyle(e); return /auto|scroll/.test(s.overflowY) && e.scrollHeight > e.clientHeight + 20 && e.clientHeight > 40 && __cr.vis(e); }); if (!e) return null; e.dataset.crWheel = '1'; const r = e.getBoundingClientRect(); return [r.left + r.width / 2, r.top + Math.min(40, r.height / 2), e.scrollTop]; })()")
    scrolled = None
    if wheel:
        await J.w.wheel(wheel[0], wheel[1], 240)
        await asyncio.sleep(0.5)
        top = await J.js("(() => { const e = document.querySelector('[data-cr-wheel]'); return e ? e.scrollTop : null; })()")
        scrolled = [wheel[2], top]
        if top is None or top <= wheel[2]: bad.append(f"wheel inside a panel did not scroll ({wheel[2]} -> {top})")
        await J.js("(() => { const e = document.querySelector('[data-cr-wheel]'); if (e) { e.scrollTop = 0; delete e.dataset.crWheel; } })()")
    # focus and back: the root keeps its size; pins in the header are still pressable
    x, y = await grip(J, "The board")
    await J.w.dblclick(x, y)
    await answered(J)
    await J.settle(1)
    cf = await J.js(CONTAIN)
    await restore(J)
    cb = await J.js(CONTAIN)
    for tag, cc in (("in focus", cf), ("after focus", cb)):
        if not cc["root"] or cc["root"][3] < 100: bad.append(f"root {tag} is {cc['root']}")
        for p in cc["panels"]:
            if p["r"][2] < 40 or p["r"][3] < 40 or not p["inside"]: bad.append(f"{tag}: {p['label']} {p['r']} inside={p['inside']}")
    J.record("containment", containment.__doc__, "pass" if not bad else "fail",
             f"contain {c['contain']!r}; root {c['root']} client {c['client']} (frame before {fr0}); {len(c['panels'])} panels, {sum(p['scrollers'] for p in c['panels'])} scrollers; "
             f"fixed descendants {len(c['fixed'])}; menu {menu} for a press at {card}; wheel {scrolled}; root in focus {cf['root']}, after {cb['root']}"
             + (f"; problems: {bad}" if bad else "; no clipped/empty panel, root whole, menu at the pointer, wheel scrolls"),
             {"before": c, "in focus": cf, "after": cb}, [await J.shot("containment")])


HEADPARTS = r"""(() => { const p = __cr.byLabel('The board'), g = p && __cr.grip(p); if (!g) return null;
  const isCtl = e => !!e.closest('button, a, input, textarea, select, [role=button], [contenteditable=true]') || !!(e._n && e._n.acts && e._n.acts.some(a => a.on === 'click'));
  const chain = e => { const c = []; for (let k = e; k && k !== g.parentElement; k = k.parentElement) c.push((k.dataset.key ? k.dataset.key.split('/').slice(-1)[0] : '') + '<' + k.tagName.toLowerCase() + (k.className ? '.' + String(k.className).split(' ')[0] : '') + (k.dataset.carry !== undefined ? ' data-carry' : '') + (isCtl(k) && !k.contains(g) ? ' CONTROL' : '') + '>'); return c.join(' / '); };
  const leaves = [...g.querySelectorAll('*')].filter(e => __cr.vis(e) && [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()));
  return { grip: [g.dataset.key.split('/').slice(-2).join('/'), __cr.R(g), getComputedStyle(g).userSelect],
    parts: leaves.slice(0, 16).map(e => { const r = e.getBoundingClientRect(), x = r.left + Math.min(r.width / 2, 12), y = r.top + r.height / 2, at = document.elementFromPoint(x, y);
      return { text: e.textContent.trim().slice(0, 24), x, y, chain: chain(e), control: isCtl(e), userSelect: getComputedStyle(e).userSelect, hitSelf: at === e || e.contains(at), at: at && chain(at) }; }) }; })()"""


async def countpress(J):
    """c7532: every text piece inside the Board's title grip after it is carried to the bottom: its element and ancestry up to the grip, control or not, and whether a press there carries or selects (no selection clearing; a page left with text selected is reloaded and recorded)"""
    await J.reload()
    await fixture(J)
    fr = await frame(J)
    await carry_to(J, "The board", fr[0] + fr[2] / 2, fr[1] + fr[3] - 3)
    await answered(J)
    await J.settle(1)
    hp = await J.js(HEADPARTS)
    if not hp:
        J.record("countpress", countpress.__doc__, "blocked", "no Board grip", {}, [await J.shot("countpress")])
        return
    rows, bad = [], []
    for part in hp["parts"]:
        if not part["hitSelf"]:
            rows.append({**part, "result": "covered"})
            continue
        # out and back to the press point before release (Escape is not used: with nothing carried it would close the home base)
        seen, _ = await J.hold(part["x"], part["y"], [(part["x"] + 30, part["y"] + 12), (part["x"] + 60, part["y"] + 40), (part["x"], part["y"])],
                               lambda a, b: J.js("({ghost: !!__cr.ghost(), sel: __cr.selection(), text: String(getSelection()).slice(0, 40)})"))
        await answered(J)
        await asyncio.sleep(0.4)
        mid = seen[1]
        result = "carried" if mid["ghost"] and not mid["sel"] else ("selected " + repr(mid["text"]) if mid["sel"] else "nothing")
        rows.append({**part, "result": result, "mid": mid})
        if not part["control"] and result != "carried":
            bad.append(f"{part['text']!r} ({part['chain'].split(' / ')[0]}): {result}")
        if mid["sel"] or await J.js("__cr.selection()"):
            J.reloads.append(("countpress", mid["sel"]))
            await J.reload()
            await answered(J)
            await J.settle(0.5)
    st = await J.js("__cr.state()")
    (J.out / "countpress.json").write_text(json.dumps({"grip": hp["grip"], "rows": rows, "state": st}, indent=1, default=str), encoding="utf-8")
    J.record("countpress", countpress.__doc__, "pass" if not bad else "fail",
             f"grip {hp['grip']}; " + "; ".join(f"{r['text']!r}{' [control]' if r['control'] else ''} -> {r['result']}" for r in rows)
             + (f"; non-control pieces that did not carry: {bad}" if bad else "") + "; ancestry in countpress.json",
             {"file": "countpress.json"}, [await J.shot("countpress")])
    await restore(J)


ROUND3 = [("busy", busy), ("focusdiag", focusdiag), ("containment", containment), ("countpress", countpress)]

ROUND2 = [("consecutive-paced", consecutive_paced), ("consecutive", consecutive),("immediate", immediate), ("refusal", refusal), ("cancel-policy", cancel_policy),
          ("composer", composer), ("tabs-focus", tabs_focus), ("receivers", receivers), ("doc-pins", doc_pins), ("tints", tints),
          ("workspace", workspace_identity)]

ALL = [("facts", facts), ("clicks", clicks), ("ghost", ghost), ("edges", edges), ("local", local), ("fit", fit),
       ("dividers", dividers), ("focus", focus), ("shelf", shelf), ("cancel", cancel), ("stale", stale), ("draft", draft),
       ("bare", bare), ("dock-pin", dock_pins), ("dock-order", dock_order), ("dock-look", dock_look), ("reload", reload_keeps)]
ALL = ALL[:3] + ROUND3 + ROUND2[:4] + ALL[3:] + ROUND2[4:]     # the workspace emulation replaces the layout: always last
DIAGNOSES = [("escdiag", escdiag), ("debug", debug), ("syncdiag", syncdiag)]      # --only escdiag / debug runs these
ALL += DIAGNOSES
