"""HUD wheel regression steps (a6549): browser acceptance still UNVERIFIED.

Run hud_playtest.py --only scroll --report none in a browser-capable environment.
Fixtures are written only through that runner's copied door/witnessed sources.
The page's real lenses/layout are used unchanged. The reader waits on a6460.
"""
import asyncio
import re


# Find an overflowing panel, intersect its pointer area with every clipping
# ancestor, and hit-test it. Never scroll it in JS: only measure around input.
PREPARE = r"""(scope => {
  if (!scope) throw Error('long-content scope is missing');
  const page = document.scrollingElement;
  if (page.scrollTop || page.scrollLeft) throw Error('HUD page already scrolled');
  const candidates = [...scope.querySelectorAll('*'), scope];
  // Never accept scrolling the HUD's columns as a panel-scroll success.
  let bounded = false;
  for (let p = scope.parentElement; p && p !== page; p = p.parentElement) {
    candidates.push(p);
    if (p.classList.contains('r-pane')) { bounded = true; break; }
  }
  if (!bounded) throw Error('long content is not inside a HUD pane');
  for (const box of candidates) {
    if (box === page || box === document.body || box.id === 'paint') continue;
    if (!/^(auto|scroll)$/.test(getComputedStyle(box).overflowY) || box.scrollHeight <= box.clientHeight + 2) continue;
    const r = box.getBoundingClientRect();
    let l = Math.max(0, r.left), t = Math.max(0, r.top),
        rr = Math.min(innerWidth, r.right), b = Math.min(innerHeight, r.bottom);
    for (let p = box.parentElement; p; p = p.parentElement) {
      const s = getComputedStyle(p), a = p.getBoundingClientRect();
      if (/auto|scroll|hidden|clip/.test(s.overflowX)) { l = Math.max(l, a.left); rr = Math.min(rr, a.right); }
      if (/auto|scroll|hidden|clip/.test(s.overflowY)) { t = Math.max(t, a.top); b = Math.min(b, a.bottom); }
    }
    if (rr - l < 12 || b - t < 12) continue;
    // Prefer text belonging to the requested content, rather than a sticky
    // header or some other panel that happens to scroll beside it.
    const content = [...scope.querySelectorAll('*')].find(e => e.getClientRects().length &&
      !e.children.length && e.textContent.trim() && box.contains(e) &&
      !/^(BUTTON|INPUT|TEXTAREA)$/.test(e.tagName) &&
      !e.closest('[data-peek]') && getComputedStyle(e).position !== 'fixed' &&
      getComputedStyle(e).position !== 'sticky');
    if (!content) continue;
    for (const f of [.5, .3, .7]) {
      const x = l + (rr-l)*f, y = t + (b-t)*.5, hit = document.elementFromPoint(x,y);
      if (!hit || !box.contains(hit)) continue;
      const before = {scroll:box.scrollTop, top:content.getBoundingClientRect().top};
      window.__pt.scrollProbe = {box, content, before, wheel:0};
      addEventListener('wheel', () => window.__pt.scrollProbe.wheel++, {once:true, capture:true});
      return {x,y,dy:box.scrollTop >= (box.scrollHeight-box.clientHeight)/2 ? -720 : 720,
              before, key:box.dataset.key || box.className};
    }
  }
  throw Error('long content has no reachable bounded scroll container; inspect its ancestor heights/overflow');
})"""

RESULT = r"""(() => {
  const p = window.__pt.scrollProbe, root = document.scrollingElement;
  if (!p.box.isConnected || !p.content.isConnected) throw Error('content repainted during wheel proof; retry after settling');
  return {scroll:p.box.scrollTop, top:p.content.getBoundingClientRect().top,
    pageX:root.scrollLeft, pageY:root.scrollTop, wheel:p.wheel};
})()"""


async def prove(play, scope, name):
    await asyncio.sleep(1.2)  # let end-follow and the last scene settle
    start = await play.w.js(f"(() => {{const pt=window.__pt; return ({PREPARE})({scope});}})()")
    await play.w.shot(play.out / f"{play.n:02d}-scroll-before.png")
    await play.w.wheel(start["x"], start["y"], start["dy"])
    after = None
    for _ in range(25):
        await asyncio.sleep(.08)
        after = await play.w.js(RESULT)
        if after["pageX"] or after["pageY"]:
            raise AssertionError(f"{name}: wheel moved the HUD page: {after}")
        if abs(after["scroll"] - start["before"]["scroll"]) > 2:
            break
    moved = after["scroll"] - start["before"]["scroll"]
    content_moved = start["before"]["top"] - after["top"]
    assert after["wheel"], f"{name}: no wheel event reached the page"
    assert moved * start["dy"] > 0, f"{name}: wheel did not move panel content: {start} -> {after}"
    assert abs(moved - content_moved) < 2, f"{name}: scrollbar moved but content did not follow: {start} -> {after}"
    return {"note": f"real wheel: {name}; {start['key']}; scroll {start['before']['scroll']} -> "
                    f"{after['scroll']}, content moved {content_moved:.1f} px; HUD page stayed at 0"}


def steps(play):
    """Compatibility for callers of the former wheel-step factory."""
    from playtest_steps import discover
    return [(s.name, s.description, s.script(play, None), s.budget)
            for s in discover() if s.name.startswith("scroll")]
