from playtest_steps import Step
from playtest_steps._support import Skip, asyncio, press


def bind(play, opened):
    w, c = play.w, play.copy
    async def s_number():
        """a6057: a number in the glance (top left) is the way in: a press fills the room with the panel that answers it
        (the panel's tag glance-you), a press again gives the room back."""
        play.needs("a6057", "the glance's numbers open their panel", ("home-glance", "glance-you"))
        stat = "window.__pt.parts('lens:home-glance').find(e => /\\/you\\/[a-z]\\d+$/.test(e.dataset.key))"
        if not await play.has(stat):
            if await play.has("pt.leaf('nothing waits on you', pt.part('lens:home-glance'))"):
                raise Skip("nothing waits on Alex in this world, so the glance has no number to press")
            raise AssertionError("no 'wait on you' number in the glance answered by a panel (no panel tagged glance-you?)")
        pid = (await w.js(f"(() => {{ const pt = window.__pt; return {stat}.dataset.key; }})()")).rsplit("/", 1)[-1]
        filled = f"pt.parts('lens:home-tiling').some(e => /\\/room\\/{pid}$/.test(e.dataset.key))"
        words = await w.js(f"(() => {{ const pt = window.__pt; return {stat}.innerText.replace(/\\s+/g, ' ').trim(); }})()")
        r = await play.timed(filled, press(play, stat, f"'{words}' in the glance"))
        if not r["ok"]:
            r["want"] = f"a press on '{words}' did not fill the room with its panel ({pid})"
            return r
        await asyncio.sleep(0.3)
        await w.shot(play.out / f"{play.n + 1:02d}-number-filled.png")
        r2 = await play.timed(f"!({filled})", press(play, stat, f"'{words}' again"))
        if not r2["ok"]:
            r2["want"] = f"'{words}' filled the room, but a second press did not give it back"
            return r2
        r["note"] = f"'{words}': its panel filled the room in {r['ms']} ms, gave it back in {r2['ms']} ms"
        r["ms"] = max(r["ms"], r2["ms"])
        return r
    return s_number


STEP = Step(name='number', description='press a number in the glance: its panel fills the room, and back', order=2300,
            needs=(('a6057', "the glance's numbers open their panel"),), script=bind, assertion='press a number in the glance: its panel fills the room, and back', budget=(100, 300))
