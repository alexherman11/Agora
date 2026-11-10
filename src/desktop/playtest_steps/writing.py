from playtest_steps import Step
from playtest_steps._support import DOCK, json, press


def bind(play, opened):
    w, c = play.w, play.copy
    async def s_writing():
        await w.js("window.__pt.host.length = 0")
        icon = DOCK.format(json.dumps("Writing room"))
        if not await play.has(icon):
            raise AssertionError("no Writing room on the dock")
        r = await play.timed("pt.host.some(h => h.startsWith('window writing')) || !!pt.part('lens:writing')", press(play, icon, "Writing room on the dock"))
        if not r["ok"]:
            r["want"] = "Writing room asked the home base for nothing and showed no Writing"
            return r
        inside = await play.has("pt.part('lens:writing')")
        r["note"] = "Writing opened inside the home base" if inside else "asked the host `window writing` (a window of its own; the stand-in host records it)"
        return r
    return s_writing


STEP = Step(name='writing', description='open Writing from the dock', order=1000,
            needs=(), script=bind, assertion='open Writing from the dock', budget=(100, 300))
