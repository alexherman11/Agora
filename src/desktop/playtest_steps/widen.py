from playtest_steps import Step
from playtest_steps._support import Missing, asyncio, helpers, open_panel, panel, press


def bind(play, opened):
    w, c = play.w, play.copy
    widen_column = helpers(play).widen_column
    async def s_widen():
        await open_panel(play, "Music", "home-music")
        p = panel("Music")
        if await play.has(f"{p} && pt.leaf('⇔', {p})"):
            return await widen_column(p)
        if not await play.has(f"{p} && pt.leaf('⤢', {p})"):
            raise Missing("neither ⤢ nor ⇔ on Music's title (the tiling changed: update this step)")
        before = await w.js(f"(() => {{ const pt = window.__pt; return pt.rect({p}); }})()")
        r = await play.timed(f"(() => {{ const r = pt.rect({p}); return r && r[2] > {before[2] * 1.3}; }})()", press(play, f"pt.pressable(pt.leaf('⤢', {p}))", "⤢ on Music"))
        if not r["ok"]:
            r["want"] = "⤢ did not widen Music"
            return r
        await asyncio.sleep(0.3)
        await w.shot(play.out / f"{play.n + 1:02d}-widen-wide.png")
        r2 = await play.timed(f"(() => {{ const r = pt.rect({p}); return r && Math.abs(r[2] - {before[2]}) < {before[2] * 0.1}; }})()", press(play, f"pt.pressable(pt.leaf('⤡', {p}))", "⤡ on Music"))
        if not r2["ok"]:
            r2["want"] = "Music widened but ⤡ did not give the room back"
            return r2
        r["note"] = f"widened in {r['ms']} ms, back in {r2['ms']} ms (the tiling of today, a5496)"
        r["ms"] = max(r["ms"], r2["ms"])
        return r
    return s_widen


STEP = Step(name='widen', description="widen Music (⤢, or ⇔ in a5994's tiling), then give the room back", order=2100,
            needs=(), script=bind, assertion="widen Music (⤢, or ⇔ in a5994's tiling), then give the room back", budget=(100, 300))
