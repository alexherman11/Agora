from playtest_steps import Step
from playtest_steps._support import Skip, json, panel


def bind(play, opened):
    w, c = play.w, play.copy
    async def s_restore():
        moved = getattr(play, "moved", None)
        if not moved:
            raise Skip("the board was not moved")
        pid, home, there = moved
        x0, y0 = await play.find(f"{panel('The board')}.querySelector('[data-carry]') || {panel('The board')}", "the board's title bar")
        if await play.has(f"pt.key({json.dumps(home)})"):          # its column is still there: onto it
            x1, y1 = await play.find(f"pt.key({json.dumps(home + '/foot')}) || pt.parts({json.dumps(home + '/')}).find(e => /\\/grip$/.test(e.dataset.key))",
                                     "the board's first column")
            r = await play.timed(f"!!pt.key({json.dumps(home + '/' + pid)})", lambda: w.drag(x0, y0, x1, y1))
            how = "onto its column"
        else:
            # a5994's tiling: a column left empty goes. A drop near a panel's right edge makes a new column there
            other = (f"pt.parts({json.dumps(there + '/')}).find(e => new RegExp('/tiling/[a-z]\\\\d+/[a-z]\\\\d+$').test(e.dataset.key)"
                     f" && !e.dataset.key.endsWith('/{pid}'))")
            rect = await w.js(f"(() => {{ const pt = window.__pt, e = {other}; return e ? pt.rect(e) : null; }})()")
            if not rect:
                raise AssertionError("no other panel in that column to drop beside")
            x1, y1 = rect[0] + rect[2] - 6, rect[1] + rect[3] / 2
            alone = (f"(() => {{ const b = {panel('The board')}, c = b && b.parentElement; return !!c && !c.dataset.key.endsWith({json.dumps(there)})"
                     " && [...c.children].filter(x => x.querySelector(':scope > [data-key$=\"/grip\"]')).length === 1; })()")
            r = await play.timed(alone, lambda: w.drag(x0, y0, x1, y1))
            how = "into a new column of its own (dropped at a panel's right edge: its old column had gone, as a5994's tiling does)"
        if not r["ok"]:
            r["want"] = "the board did not go back to a column of its own"
        else:
            r["note"] = f"back {how}"
        return r
    return s_restore


STEP = Step(name='restore', description='drag the board back where it was', order=1900,
            needs=(), script=bind, assertion='drag the board back where it was', budget=(100, 300))
