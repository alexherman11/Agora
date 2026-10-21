"""journeys.py (a7466): the combined tiling + slim dock journeys a7366 lists, driven in the guarded hidden Edge window
on hud_playtest's disposable copy, staged by a7045's review_copy.stage_copy (both halves preflighted first). Never
the live world, never Alex's screen, no Conversation send, no media/account control pressed.

    python research/window-lab/combined-review/journeys.py [--small] [--only a,b] [--probe]

Input is Windows messages to the sandbox window (as a hand's), never SendInput. Each journey records ran/pass/fail/
blocked with facts and shots under research/window-lab/demos/combined-review/<time>-<size>/ (report.json, report.md).
"""
import argparse
import asyncio
import datetime
import json
import sys
import time
import traceback
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
sys.path.insert(0, str(LAB))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(LAB / "hud-dividers"))
import hud_playtest as pt  # noqa: E402
import review_copy  # noqa: E402

DEMOS = Path(r"C:/Projects/Agora4/research/window-lab/demos/combined-review")

# ---- page-side helpers, installed once per load ---------------------------------------------------------------------
HELPERS = r"""(() => { if (window.__cr) return 'kept'; const R = e => { const b = e.getBoundingClientRect(); return [Math.round(b.left*10)/10, Math.round(b.top*10)/10, Math.round(b.width*10)/10, Math.round(b.height*10)/10]; };
  const vis = e => !!e && e.getClientRects().length > 0 && getComputedStyle(e).visibility !== 'hidden' && getComputedStyle(e).display !== 'none';
  const root = () => document.querySelector('[data-partition]');
  const members = () => { const r = root(); return r ? [...r.children].filter(e => e._n && e._n.paint && e._n.paint.partition_item) : []; };
  const label = e => (e._n.paint.tip && e._n.paint.tip[0]) || ((e.querySelector('[data-carry]') || {}).textContent || '').trim().slice(0, 40) || '?';
  const grip = e => [...e.querySelectorAll('[data-carry]')].find(g => vis(g) && g._n && g._n.fence && g._n.fence.item === e._n.paint.partition_item);
  const hit = e => { if (!e) return null; const b = e.getBoundingClientRect(), x = b.left + b.width / 2, y = b.top + b.height / 2, at = document.elementFromPoint(x, y);
    return { x, y, ok: !!at && (e === at || e.contains(at)), at: at ? (at.className && typeof at.className === 'string' ? at.tagName + '.' + at.className.split(' ')[0] : at.tagName) : 'nothing' }; };
  const byLabel = w => members().find(e => label(e).toLowerCase().includes(w.toLowerCase()));
  window.__cr = { R, vis, root, members, label, grip, hit, byLabel,
    state() { const r = root(); if (!r) return null; return { tree: r._n.paint.partition.tree, focus: r._n.paint.partition.focus || '' }; },
    boxes() { return members().filter(vis).map(e => ({ id: e._n.paint.partition_item, label: label(e), r: R(e), chrome: e._n.paint.chrome || '', sizing: e._n.paint.sizing || '' })); },
    chrome() { const r = root(); if (!r) return []; return [...r.querySelectorAll(':scope > .l-divider, :scope > .partition-tool')].map(e => ({ cls: e.className, axis: e.dataset.axis || '', text: e.textContent, label: e.getAttribute('aria-label') || e.title || '', r: R(e) })); },
    previews() { return [...document.querySelectorAll('.landing-box')].filter(e => !e.hidden && vis(e)).map(e => ({ in: e.parentElement && (e.parentElement.dataset.partition ? 'partition' : (e.parentElement.dataset.key || e.parentElement.tagName)), r: R(e) })); },
    ghost() { const g = [...document.body.children].find(e => e.style && e.style.position === 'fixed' && e.style.pointerEvents === 'none' && e.style.zIndex === '40'); return g ? { r: R(g), opacity: g.style.opacity, transition: g.style.transition, animation: g.style.animation, text: g.innerText.slice(0, 60) } : null; },
    selection() { const s = getSelection(); return s ? s.toString().length : 0; },
    page() { const se = document.scrollingElement; return { vis: document.visibilityState, iw: innerWidth, ih: innerHeight, dpr: devicePixelRatio, sw: se.scrollWidth, sh: se.scrollHeight, sx: se.scrollLeft, sy: se.scrollTop }; },
    dock() { return [...document.querySelectorAll('[data-key]')].filter(e => e._n && /(^|\/)app$/.test(e.dataset.key.split('/').slice(-2, -1)[0] || '') === false && e.dataset.key.includes('/dock') && e._n.paint && (e._n.roles || []).length >= 0).length; },
  }; return 'installed'; })()"""


class Journeys:
    def __init__(self, win, copy, out, size):
        self.w, self.copy, self.out, self.size = win, copy, out, size
        self.play = pt.Play(win, copy, out, ["a7045", "a7223"])
        self.rows, self.shots, self.selection_left, self.reloads = [], 0, [], []

    async def js(self, src):
        await self.w.js(HELPERS)
        if await self.w.js("document.visibilityState") != "visible":
            self.hidden_seen = True
        return await self.w.js(src)

    async def shot(self, name):
        self.shots += 1
        p = self.out / f"{self.shots:02d}-{name}.png"
        await self.w.shot(p)
        return p.name

    async def settle(self, secs=1.5):
        await asyncio.sleep(secs)

    async def reload(self):
        await self.w.p.call("Page.reload")
        for _ in range(100):
            await asyncio.sleep(0.2)
            if await self.w.js("!!document.querySelector('[data-partition]')"):
                break
        await asyncio.sleep(1.2)
        await self.w.js("document.getElementById('hud-frost')?.remove()")

    # a hand's drag that can stop in the middle: messages to the window, as hud_playtest.Window.drag sends them
    async def hold(self, x0, y0, points, look=None, release=True, steps=10):
        SB, w = self.w.SB, self.w
        # Round 1 (ebe9a91) found a carry left page text selected and cleared it here before each press. Round 2
        # (c7492) rechecks the repair WITHOUT that workaround: what is left selected is only counted and reported
        left = await w.js("getSelection().toString().length")
        if left:
            self.selection_left.append(left)
        ox, oy, dpr = await w.origin()
        cx, cy = ox + x0 * dpr, oy + y0 * dpr
        t, dx, dy = w._descend(cx, cy)
        at = lambda x, y: SB.xy(ox + x * dpr + dx, oy + y * dpr + dy)  # noqa: E731
        SB.post(t, SB.WM_MOUSEMOVE, 0, at(x0, y0))
        time.sleep(0.03)
        SB.post(t, SB.WM_LBUTTONDOWN, 1, at(x0, y0))
        px, py, seen = x0, y0, []
        for (x, y) in points:
            for k in range(1, steps + 1):
                time.sleep(0.025)
                SB.post(t, SB.WM_MOUSEMOVE, 1, at(px + (x - px) * k / steps, py + (y - py) * k / steps))
            px, py = x, y
            await asyncio.sleep(0.25)
            if look:
                seen.append(await look(x, y))
        if release:
            SB.post(t, SB.WM_LBUTTONUP, 0, at(px, py))
        return seen, (t, at, px, py)

    def up(self, handle):
        t, at, px, py = handle
        self.w.SB.post(t, self.w.SB.WM_LBUTTONUP, 0, at(px, py))

    def record(self, jid, name, outcome, note, facts=None, shots=()):
        if outcome == "pass" and getattr(self, "hidden_seen", False):
            outcome, note = "invalid", "the page was hidden (not painting) during this journey; " + note
        row = {"id": jid, "journey": name, "outcome": outcome, "note": note, "facts": facts or {}, "shots": list(shots)}
        self.rows.append(row)
        self.hidden_seen = False
        print(f"  {outcome:<8} {jid:<14} {note[:220]}", flush=True)
        return row

    async def probe(self):
        facts = {"page": await self.js("__cr.page()"), "state": await self.js("__cr.state()"), "boxes": await self.js("__cr.boxes()"),
                 "chrome": await self.js("__cr.chrome()"),
                 "grips": await self.js("__cr.members().map(e => ({label: __cr.label(e), grip: !!__cr.grip(e), gripr: __cr.grip(e) ? __cr.R(__cr.grip(e)) : null, hit: __cr.hit(__cr.grip(e)), buttons: [...e.querySelectorAll('button,[data-key]')].filter(b => b.tagName === 'BUTTON' || (b._n && b._n.acts && b._n.acts.some(a => a.on === 'click'))).filter(__cr.vis).slice(0, 12).map(b => (b.innerText || b.title || b.getAttribute('aria-label') || b.dataset.key || '').trim().slice(0, 30))}))"),
                 "dock": await self.js("[...document.querySelectorAll('[data-drop]')].map(e => ({key: e.dataset.key, r: __cr.R(e), drops: (e._drops || []).map(a => a.part)}))"),
                 "dockapps": await self.js("[...document.querySelectorAll('[data-key]')].filter(e => /\\/app$|\\/app\\/\\d+$/.test(e.dataset.key) || (e.dataset.key.split('/').slice(-2,-1)[0] === 'app')).filter(__cr.vis).map(e => ({key: e.dataset.key, r: __cr.R(e), tip: e._n && e._n.paint.tip}))"),
                 "composer": await self.js("[...document.querySelectorAll('textarea,[contenteditable=true]')].filter(__cr.vis).map(e => ({tag: e.tagName, key: (e.closest('[data-key]') || {}).dataset?.key, r: __cr.R(e)}))")}
        print(json.dumps(facts, indent=1, ensure_ascii=False)[:12000])
        return self.record("probe", "what the staged copy paints", "ran", "facts printed", facts, [await self.shot("probe")])


def deployed_identity(copy):
    """a7925: what the copy holds as deployed, before anything is pressed: the home-tiling lens text, Alex's layout's
    tree, its members and shelves, and the event the copy starts at (SHA-256 of exact bodies/values; reads only)."""
    import hashlib
    import re as _re
    h = lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest().upper()  # noqa: E731
    said = copy.do("read a5692 :3", "hud-playtest").splitlines()
    i = said.index("---")
    lens = "\n".join(said[i + 1:said.index("---", i + 1)])
    snap = json.load(urllib.request.urlopen(copy.base + "/api/snapshot?" + urllib.parse.urlencode({"session": copy.session, "as": "hud-playtest"}), timeout=60))
    f = next((n for n in snap["nodes"].values() if n.get("id") == "f5664" or n.get("appears") == "f5664"), None) or snap["nodes"].get("f5664") or {}
    props = f.get("props") or {}
    panels = copy.do("find prop:role=home-panel,prop:actor=alex", "hud-playtest")
    rows = [l.strip() for l in panels.splitlines() if _re.match(r"\s+a\d+ note ", l)]
    return {"events": copy.at(), "home-tiling a5692": {"sha256": h(lens), "lines": len(lens.splitlines()),
                                                       "has partition": "partition" in lens},
            "f5664 props": sorted(props), "f5664 tree sha256": h(str(props.get("tree", ""))), "f5664 tree": str(props.get("tree", ""))[:600],
            "panels": [_re.sub(r"\s+·\s+\d+w.*$", "", r) for r in rows]}


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", default="frontier-try")
    ap.add_argument("--small", action="store_true")
    ap.add_argument("--only", type=lambda s: s.split(","), default=None)
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--glance-fix", action="store_true", help="c7532: JEFF's staged a7531 style line, in the disposable copy only")
    ap.add_argument("--deployed", action="store_true",
                    help="a7925: the world is already migrated (JEFF e16654/e16658): stage nothing, keep Alex's shelves, record what is deployed")
    ap.add_argument("--live-tree", action="store_true", help="with --deployed: Alex's current live f5664 tree (read only) onto the copy")
    a = ap.parse_args()
    size = (1280, 800) if a.small else (2560, 1440)
    pt.SIZE = size
    out = DEMOS / f"{datetime.datetime.now():%Y-%m-%d-%H%M%S}-{size[0]}x{size[1]}{'-deployed' if a.deployed else ''}"
    out.mkdir(parents=True, exist_ok=True)
    copy = pt.Copy(a.world)
    win, guard = None, None
    j = None
    deployed = None
    try:
        if a.deployed:
            if a.live_tree:
                # the live arrangement as Alex left it (read-only GET from the live door), put on the COPY only
                snap = json.load(urllib.request.urlopen(pt.LIVE + "/api/snapshot?" + urllib.parse.urlencode({"session": "frontier", "as": "worker-a7925"}), timeout=60))
                live = (snap["nodes"].get("f5664") or {}).get("props") or {}
                copy.do("look f5664", "alex")
                said = copy.do(f"do prop f5664 tree={pt.q(live['tree'])}", "alex")
                print("live tree on the copy:", (said.strip().splitlines() or [""])[0][:160])
                if "ERR" in said and "already has that" not in said:
                    raise SystemExit("the live tree did not go onto the copy: " + said[:300])
            deployed = deployed_identity(copy)
            print(json.dumps(deployed, indent=1, ensure_ascii=False))
        else:
            review_copy.stage_copy(copy)
        if a.glance_fix:
            # a7531, exactly: a transparent token and `edge glanceclear` on role lgstat; lgstat.on unchanged. The copy only.
            old = "role lgstat : between gap, align center, corner gap, pad gap /2, pad left gap, pad right gap"
            copy.do("look a5206", "hud-playtest")
            said = copy.do(f"do replace a5206 old={pt.q(old + chr(10))} new={pt.q('token glanceclear = #00000000' + chr(10) + old + ', edge glanceclear' + chr(10))}", "hud-playtest")
            print("glance fix (copy only):", said.splitlines()[0][:200] if said else said)
            if "ERR" in said:
                raise SystemExit("the staged glance fix did not apply to the copy: " + said[:300])
        # a7784: Alex's layout now has the Viewer shelved; earlier rounds' journeys stand on four panels, so the copy (only)
        # opens The lowdown in it, as a press on a name does (the view verb brings the Viewer panel out)
        import re as _re
        vline = copy.do("find prop:role=home-panel,prop:actor=alex,prop:lens=home-viewer", "hud-playtest")
        if "shelf=yes" in vline and not a.deployed:
            vid = _re.search(r"^\s+(a\d+) note", copy.do("find prop:role=home-view,prop:actor=alex", "hud-playtest"), _re.M).group(1)
            copy.do(f"read {vid}", "alex")
            said = copy.do("do view a5202", "alex")
            print("viewer brought out in the copy:", (said.strip().splitlines() or [""])[-1][:160])
        win = pt.Window(False)
        await win.open(copy.url())
        for _ in range(100):
            await asyncio.sleep(0.2)
            if await win.js("!!document.querySelector('[data-partition]')"):
                break
        await asyncio.sleep(1.5)
        await win.js("document.getElementById('hud-frost')?.remove()")
        j = Journeys(win, copy, out, size)
        if a.probe:
            await j.probe()
        else:
            import journey_steps
            for jid, fn in journey_steps.ALL:
                if (a.only and jid not in a.only) or (not a.only and (jid, fn) in journey_steps.DIAGNOSES):
                    continue
                try:
                    left = await win.js("getSelection().toString().length")
                    if left:          # never cleared in place: a fresh page, and it is reported
                        j.reloads.append((jid, left))
                        await j.reload()
                    await fn(j)
                except Exception as e:
                    j.record(jid, fn.__doc__ or jid, "error", f"{type(e).__name__}: {e}", {"trace": traceback.format_exc()[-1500:]},
                             [await j.shot(jid + "-error")])
                    try:
                        await j.reload()
                    except Exception:
                        pass
        errors = await win.js("(window.__pt && window.__pt.errors) || []")
    finally:
        if win:
            guard = await win.close()
        copy.close()
    rows = j.rows if j else []
    rep = {"size": size, "world_at": None, "deployed": deployed, "guard": guard, "page_errors": errors if win else None, "rows": rows,
           "selection_left_before_presses": j.selection_left if j else [],
           "stale_chrome_ms_after_release": getattr(j, "stale_ms", []) if j else []}
    (out / "report.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    md = [f"# Combined tiling + dock journeys, {size[0]}x{size[1]}", "", f"guard: {guard[1] if guard else 'none'}", "",
          "| journey | outcome | note | shots |", "|---|---|---|---|"]
    md += [f"| {r['id']} | {r['outcome']} | {r['note'].replace('|', '/')[:400]} | {', '.join(r['shots'])} |" for r in rows]
    md += ["", f"Text left selected before presses (counted only, never cleared): {j.selection_left if j else []}",
           f"Journeys started on a reloaded page because the previous one left text selected (journey, chars): {j.reloads if j else []}",
           f"Old dividers/Fit tools left standing after each carry's release, ms until gone (first read included; None = still stale at 2 s): {getattr(j, 'stale_ms', []) if j else []}",
           f"Page errors: {errors if win else None}"]
    (out / "report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"guard: {guard[1] if guard else 'none'}")
    print(f"report: {out / 'report.md'}")
    return 1 if (guard and guard[0]) else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
