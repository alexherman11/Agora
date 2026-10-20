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
    """Seven independent reported steps, with before/after shots, selected by --only scroll."""
    from hud_playtest import q, press, open_panel
    import witnessed
    c = play.copy
    viewer = "prop:role=home-view,prop:actor=alex"
    writer = "prop:role=writer,prop:actor=alex"
    long_text = "\n\n".join(f"## Passage {i}\n\n" + ("Long-content wheel fixture. " * 18) for i in range(1, 65))

    def checked(line, who="alex"):
        said = c.do(line, who)
        failed = said.startswith("ERR") or "refused" in said.lower()
        assert not failed or "nothing to change" in said.lower(), f"scroll fixture refused: {said[:400]}"
        return said

    def create(title, props=""):
        checked("look f5204")
        said = checked(f"do create f5204 kind=note title={q(title)} {props} text={q(long_text)}")
        hit = re.search(r"created (a\d+)", said)
        assert hit, f"scroll fixture has no create receipt: {said[:400]}"
        return hit.group(1)

    async def show(thing, lens=""):
        checked(f"read {viewer}")
        checked(f'do prop {viewer} viewing={q(thing)} with={q(lens)} find=""')
        await asyncio.sleep(2)

    async def note():
        await show(create("Long note wheel fixture"))
        return await prove(play, "pt.part('lens:home-note')", "long note")

    async def writing():
        doc = create("Long Writing wheel fixture", "role=doc")
        checked(f"read {writer}")
        checked(f'do prop {writer} open={doc} find=""')
        # Stand the Writing app in the actual HUD viewer, not a separate page.
        await show(doc, "writing")
        return await prove(play, "pt.part('lens:doc-page')", "Writing document")

    def chat_fixture():
        checked("read a5080", "jeff")
        checked(f"do append a5080 line={q(long_text)}", "jeff")

    async def chat():
        chat_fixture()
        await show("a5080")
        return await prove(play, "pt.parts('lens:jeff-chat').find(e => /\\/feed$/.test(e.dataset.key))", "HUD chat feed")

    async def conversation():
        chat_fixture()
        await show("a5080", "conversation")
        return await prove(play, "pt.part('lens:conversation')", "Conversation feed")

    async def feed():
        card = create("Stand-in worker wheel fixture", "worker=wheel-fixture")
        rows = [{"kind":"head", "who":"Stand-in worker", "state":"working", "last":150, "events":150}]
        rows += [{"kind":"action", "group":"actions", "n":i, "at":"12:00",
                  "text":f"Stand-in action {i}. " + "Content in the At-work feed. " * 12} for i in range(1,151)]
        witnessed.write(c.session, f"feed-{card}", rows, by="hud-playtest")
        checked(f"read {viewer}")
        checked(f'do prop {viewer} feed_held=0 feed_show=""')
        await show(card, "home-feed")
        return await prove(play, "pt.parts('lens:home-feed').find(e => /\\/follow$/.test(e.dataset.key))", "At-work feed")

    async def board():
        # Landed deliberately shows only the latest five. Populate the preceding
        # band so reaching Landed needs scrolling even on a quiet copied board.
        for i in range(24):
            checked("look f5204")
            checked(f'do create f5204 kind=note title="Stand-in queued work {i+1}" commission=asked')
        await show("a5080")  # avoid a second board instance in the viewer
        await open_panel(play, "The board", "home-board")
        landed = "pt.parts('lens:home-board').find(e => /\\/landed$/.test(e.dataset.key))"
        # Opening a fold is setup; the subsequent proof uses wheel input only.
        handle = f"({landed}) && ({landed}).querySelector(':scope > button[aria-expanded]')"
        if await play.has(f"({landed}) && ({landed}).dataset.folded === '1'"):
            await press(play, handle, "board's Landed fold")()
        await asyncio.sleep(.5)
        assert await play.has(f"({landed}) && !({landed}).matches('[data-folded=\"1\"]')"), "Landed fold did not open"
        return await prove(play, landed, "board Landed list")

    async def reader():
        play.needs("a6460", "proposal reader wheel check", ("reader", "markdown"))
        report = create("Long proposal wheel fixture", "tags=ready-for-review")
        await show(report, "reader")
        return await prove(play, "pt.part('lens:reader')", "proposal reader")

    return [(sid, label, fn, (100,300)) for sid, label, fn in (
        ("scrollnote", "wheel a long note inside its panel", note),
        ("scrollwriting", "wheel a long Writing document", writing),
        ("scrollchat", "wheel the HUD chat feed", chat),
        ("scrollconversation", "wheel the Conversation feed", conversation),
        ("scrollfeed", "wheel the At-work feed", feed),
        ("scrollboard", "wheel the board's Landed list", board),
        ("scrollreader", "wheel a long proposal in the reader", reader),
    )]
