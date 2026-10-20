from playtest_steps import Step
from playtest_steps._support import asyncio, panel


def bind(play, opened):
    w, c = play.w, play.copy
    async def s_search():
        """a6642 (Alex, 20 Oct: 'I want search to be outside of the tiling'): the find is the bar's own, at the top
        middle. Typing with nothing in hand starts a search there, Enter drops the results under it (titles first), Down
        and Enter open the first, beside the chat when the viewer already shows something; a filled panel leaves it
        where it was."""
        play.needs("a6642", "the search in the top bar", ("home-tiling", "lens home-search"))
        box = "[...(pt.part('lens:home-search') || document).querySelectorAll('[data-caret]')].find(e => pt.vis(e))"
        if not await play.has(box):
            raise AssertionError("no search box in the top bar (lens home-search)")
        where = f"(() => {{ const pt = window.__pt, r = {box}.closest('[data-arrows]').getBoundingClientRect(); return [Math.round(r.left + r.width / 2 - innerWidth / 2), Math.round(r.top), Math.round(r.width)]; }})()"
        at = await w.js(where)
        if abs(at[0]) > 40 or at[1] > 80:
            raise AssertionError(f"the search is not at the top middle: its centre is {at[0]} px from the page's, its top at {at[1]} px")
        await w.js("(() => { if (document.activeElement) document.activeElement.blur(); })()")
        r0 = await play.timed(f"(({box}) || {{}}).innerText === 'h' && document.activeElement === {box}", lambda: w.key("h"))
        if not r0["ok"]:
            r0["want"] = "typing with no text in hand did not start a search in the bar"
            return r0
        await w.type("ome")
        hits = "pt.parts('lens:home-search').filter(e => /\\/titles\\/[af]\\d+$/.test(e.dataset.key) && pt.vis(e))"
        r = await play.timed(f"{hits}.length > 0", lambda: w.key("Enter"))
        if not r["ok"]:
            r["want"] = "Enter did not drop results under the search (words 'home')"
            return r
        await asyncio.sleep(0.3)
        await w.shot(play.out / f"{play.n + 1:02d}-search-results.png")
        first = (await w.js(f"(() => {{ const pt = window.__pt; return {hits}[0].dataset.key; }})()")).rsplit("/", 1)[-1]
        things = "pt.parts('lens:home-thing').filter(e => pt.vis(e)).length"
        before = await w.js(f"(() => {{ const pt = window.__pt; return {things}; }})()")
        await w.key("ArrowDown")
        opened = (f"{things} > {before} || pt.parts('lens:home-viewer').some(e => e.dataset.key.endsWith('/open/{first}') && pt.vis(e))")
        r2 = await play.timed(opened, lambda: w.key("Enter"))
        if not r2["ok"]:
            r2["want"] = f"Down and Enter did not open the first result ({first})"
            return r2
        await asyncio.sleep(0.3)
        await w.shot(play.out / f"{play.n + 1:02d}-search-opened.png")
        grip = panel("The board")
        if await play.has(grip):
            x, y = await play.find(f"{grip}.querySelector('[data-key$=\"/grip/title\"]')", "The board's title")
            await w.dblclick(x, y)
            await asyncio.sleep(1.2)
            filled = await w.js(where)
            await w.shot(play.out / f"{play.n + 1:02d}-search-filled.png")
            x, y = await play.find(f"{grip}.querySelector('[data-key$=\"/grip/title\"]')", "The board's title, filled")
            await w.dblclick(x, y)
            if filled != at:
                raise AssertionError(f"filling a panel moved the search: {at} -> {filled}")
        r["note"] = (f"bar centred ({at[0]:+d} px), {at[2]} px wide; typing started it in {r0['ms']} ms, results in {r['ms']} ms, "
                     f"the first opened in {r2['ms']} ms" + ("; a filled panel left it in place" if await play.has(grip) else ""))
        r["ms"] = max(r["ms"], r2["ms"])
        return r
    return s_search


STEP = Step(name='search', description='search from the top bar: type, results drop down, open one', order=2400,
            needs=(('a6642', 'the search in the top bar'),), script=bind, assertion='search from the top bar: type, results drop down, open one', budget=(100, 300))
