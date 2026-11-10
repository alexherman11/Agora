from playtest_steps import Step
from playtest_steps._support import json, press


WSICON = "pt.tipped({0}, pt.part('lens:home-workspaces'))"

TITLES = "[...document.querySelectorAll('#paint [data-key$=\"/grip/title\"]')].filter(e => pt.vis(e)).map(e => e.textContent.trim()).sort().join('|')"


def bind(play, opened):
    w, c = play.w, play.copy
    async def s_workspace():
        play.needs("a6427", "workspaces from the dock", ("home-workspaces", "workspace"))
        if not await play.has(WSICON.format(json.dumps("writing"))):
            raise AssertionError("no 'writing' workspace icon in the dock")
        before = await w.js(f"(() => {{ const pt = window.__pt; return {TITLES}; }})()")
        # since a5994's equal footing the viewer (Writing open in it) and the chat are panels: those two, nothing else
        r = await play.timed("pt.part('lens:writing') && " + TITLES + " === 'Chat|Viewer'",
                             press(play, WSICON.format(json.dumps("writing")), "the dock's writing icon"), timeout=6000)
        if not r["ok"]:
            r["want"] = "pressing writing did not lay the home base out as the Viewer (Writing) and the Chat, nothing else out"
            return r
        side = await w.js("(() => { const pt = window.__pt, a = pt.rect(pt.part('lens:writing')), b = pt.rect(pt.part('lens:jeff-chat')); return a && b ? a[0] + a[2] <= b[0] + 2 : null; })()")
        r2 = await play.timed(f"!pt.part('lens:writing') || {TITLES} === {json.dumps(before)}",
                              press(play, WSICON.format(json.dumps("back")), "the dock's back icon"), timeout=6000)
        after = await w.js(f"(() => {{ const pt = window.__pt; return {TITLES}; }})()")
        if not r2["ok"] or after != before:
            r2["ok"] = False
            r2["want"] = f"back did not return the panels as they were ({before!r} before, {after!r} after)"
            return r2
        r2["note"] = (f"writing in {r['ms']} ms (Writing {'left of' if side else 'NOT left of'} the chat, only Viewer and Chat out); "
                      f"back in {r2['ms']} ms, the same panels out as before")
        if not side:
            r2["ok"] = False
            r2["want"] = "Writing is not beside the chat"
        return r2
    return s_workspace


STEP = Step(name='workspace', description='press a workspace in the dock (writing), then back', order=1750,
            needs=(('a6427', 'workspaces from the dock'),), script=bind, assertion='press a workspace in the dock (writing), then back', budget=(100, 300))
