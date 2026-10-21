from playtest_steps import Step
from playtest_steps._support import asyncio, json, DOCK, open_panel, panel, press


def bind(play, opened):
    w, c = play.w, play.copy
    async def s_equal():
        """a5994's final pass (Alex, 17 Oct: equal footing): the viewer and JEFF's chat are panels like the rest, with the
        same header; filling Music keeps the pinned chat beside it; the viewer's × puts its panel away (the chat stays),
        and Board on the dock brings it back."""
        play.needs("a5994", "the viewer and the chat as panels", ("home-tiling", "EQUAL FOOTING"))
        for t in ("Viewer", "Chat"):
            if not await play.has(panel(t)):
                raise AssertionError(f"no '{t}' panel with a header (equal footing not in this world?)")
        music = panel("Music")
        await open_panel(play, "Music", "home-music")
        x, y = await play.find(f"{music}.querySelector('[data-key$=\"/grip/title\"]')", "Music's title")
        r = await play.timed(f"!!pt.parts('lens:home-tiling').find(e => /\\/room\\/a\\d+$/.test(e.dataset.key) && pt.vis(e) && e.textContent.includes('Music')) && !!{panel('Chat')}", lambda: w.dblclick(x, y))
        if not r["ok"]:
            r["want"] = "Music did not fill the room with JEFF's pinned chat beside it"
            return r
        await asyncio.sleep(0.3)
        await w.shot(play.out / f"{play.n + 1:02d}-equal-filled.png")
        x, y = await play.find(f"{music}.querySelector('[data-key$=\"/grip/title\"]')", "Music's title, filled")
        await w.dblclick(x, y)
        await asyncio.sleep(1.0)
        close = "[...document.querySelectorAll('#paint [data-key]')].find(e => pt.vis(e) && /lens:home-viewer.*\\/head\\/close$/.test(e.dataset.key))"
        note = f"Music filled with the pinned chat beside it in {r['ms']} ms"
        if await play.has(close):
            r2 = await play.timed(f"!{panel('Viewer')} && !!{panel('Chat')}", press(play, close, "the viewer's ×"))
            if not r2["ok"]:
                r2["want"] = "the viewer's × did not put the Viewer panel away (with the chat kept)"
                return r2
            icon = DOCK.format(json.dumps("Board"))
            r3 = await play.timed(f"!!{panel('Viewer')} && pt.parts('lens:home-viewer').some(e => /\\/open\\/f155$/.test(e.dataset.key))", press(play, icon, "Board on the dock"))
            if not r3["ok"]:
                r3["want"] = "Board on the dock did not bring the Viewer panel back with the Board"
                return r3
            note += f"; the viewer's × put its panel away in {r2['ms']} ms, Board on the dock brought it back in {r3['ms']} ms"
            r["ms"] = max(r["ms"], r2["ms"], r3["ms"])
            # by its key: the words 'JEFF' also name him in The house and in the chat's head, where a press opens his corner
            jeff = "pt.parts('lens:home-dock').find(e => /\\/chat$/.test(e.dataset.key) && pt.vis(e))"
            r4 = await play.timed(f"!{panel('Viewer')}", press(play, jeff, "JEFF on the dock"))
            if not r4["ok"]:                     # and leave the viewer closed, as the dock step expects to find it
                r4["want"] = "JEFF on the dock did not put the Viewer panel away again"
                return r4
        r["note"] = note
        return r
    return s_equal


STEP = Step(name='equal', description='the viewer and the chat are panels: fill keeps the pinned chat, × and the dock', order=2050,
            needs=(('a5994', 'the viewer and the chat as panels'),), script=bind, assertion='the viewer and the chat are panels: fill keeps the pinned chat, × and the dock', budget=(100, 300))
