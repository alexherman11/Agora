from playtest_steps import Step
from playtest_steps._support import CHIP, DOCK, Skip, asyncio, json, open_panel, press


def bind(play, opened):
    w, c = play.w, play.copy
    async def s_atwork():
        # a6057: where lane 3's The house (home-house) has taken At work's place, its rows are played instead; the feed
        # they open is a5988's lens home-feed, which must be in the world
        house = await play.has("pt.part('lens:home-house')") or await play.has(CHIP.format(json.dumps("The house")))
        if house:
            await open_panel(play, "The house", "home-house")
            row = "window.__pt.parts('lens:home-house').find(e => /\\/lit\\/\\d+$/.test(e.dataset.key))"
            if not await play.has(row):
                raise AssertionError("no one at work in The house (the copy's house is staged busy)")
        else:
            await open_panel(play, "At work", "home-work")
            row = "window.__pt.parts('lens:home-work').find(e => /\\/busy\\/[^/]+$/.test(e.dataset.key))"
        if not await play.has(row):
            raise AssertionError("no At-work rows (the copy's house is staged busy)")
        live = await play.has(f"pt.pressable({row})")
        try:
            play.needs("a5988", "the At-work feed", ("home-feed", "witnessed:feed") if house else ("home-work", "home-feed"))
        except Skip as e:
            raise Skip(str(e) + ("" if live else "; a press on a row does nothing today (the row has no click)"))
        who = await w.js(f"(() => {{ const pt = window.__pt, r = {row}; return r ? r.innerText.split('\\n')[0].trim() : ''; }})()")
        r = await play.timed("!!pt.part('lens:home-feed')", press(play, row, "an At-work row"))
        if not r["ok"]:
            r["want"] = f"a press on {who!r} in At work opened no feed"
            return r
        lines = await w.js("window.__pt.parts('lens:home-feed').filter(e => /\\/(follow|followone|held|heldone)\\/[^/]+$/.test(e.dataset.key)).length")
        empty = await play.has("pt.leaf('No feed yet…', pt.part('lens:home-feed'))")
        r["note"] = (f"{who}'s feed opened in the viewer; " + (f"{lines} lines" if lines else
                     "it says 'No feed yet' (a copy has no house to write feeds: the lines themselves are not played here)" if empty else "no lines"))
        # give the middle back to the chat, as Alex would before the next step
        if await play.has(DOCK.format(json.dumps("JEFF"))):
            await press(play, DOCK.format(json.dumps("JEFF")), "JEFF on the dock")()
            await asyncio.sleep(1.5)
        return r
    return s_atwork


STEP = Step(name='atwork', description='click an At-work row and watch its feed', order=800,
            needs=(('a5988', 'the At-work feed'),), script=bind, assertion='click an At-work row and watch its feed', budget=(100, 300))
