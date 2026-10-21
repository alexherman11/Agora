from playtest_steps import Step
from playtest_steps._support import open_panel, panel


def bind(play, opened):
    w, c = play.w, play.copy
    async def s_fill():
        play.needs("a5994", "double-click to fill the space", ("home-tiling", "on double"))
        await open_panel(play, "Music", "home-music")
        p = panel("Music")
        before = await w.js(f"(() => {{ const pt = window.__pt; return pt.rect({p}); }})()")
        title = f"{p}.querySelector('[data-key$=\"/grip/title\"]') || {p}"
        x, y = await play.find(title, "Music's title")
        r = await play.timed(f"(() => {{ const r = pt.rect({p}); return r && r[2] * r[3] > {before[2] * before[3] * 2}; }})()", lambda: w.dblclick(x, y))
        if not r["ok"]:
            r["want"] = "a double-click on Music did not fill the space"
            return r
        x, y = await play.find(title, "Music's title")
        r2 = await play.timed(f"(() => {{ const r = pt.rect({p}); return r && Math.abs(r[2] * r[3] - {before[2] * before[3]}) < {before[2] * before[3] * 0.15}; }})()", lambda: w.dblclick(x, y))
        if not r2["ok"]:
            r2["want"] = "Music filled the space but a second double-click did not restore it"
            return r2
        r["note"] = f"filled in {r['ms']} ms, restored in {r2['ms']} ms"
        r["ms"] = max(r["ms"], r2["ms"])
        return r
    return s_fill


STEP = Step(name='fill', description='double-click Music to fill the space, then restore', order=2000,
            needs=(('a5994', 'double-click to fill the space'),), script=bind, assertion='double-click Music to fill the space, then restore', budget=(100, 300))
