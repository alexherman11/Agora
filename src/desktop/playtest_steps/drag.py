from playtest_steps import Step
from playtest_steps._support import COLS, json, open_panel, panel


def bind(play, opened):
    w, c = play.w, play.copy
    async def s_drag():
        await open_panel(play, "The board", "home-board")
        cols = await w.js(f"{COLS}.map(e => e.dataset.key)")
        k = await w.js(f"(() => {{ const pt = window.__pt, p = {panel('The board')}; return p ? p.dataset.key : null; }})()")
        if not k or len(cols) < 2:
            raise AssertionError(f"no board panel to drag ({k}) or fewer than two columns ({len(cols)})")
        home = next(c_ for c_ in cols if k.startswith(c_ + "/"))
        there = next(c_ for c_ in cols if c_ != home)
        pid = k.rsplit("/", 1)[-1]
        x0, y0 = await play.find(f"{panel('The board')}.querySelector('[data-carry]') || {panel('The board')}", "the board's title bar")
        # onto the other column's empty foot, or (a full column's foot has no height) onto its first panel's title
        x1, y1 = await play.find(f"pt.key({json.dumps(there + '/foot')}) || pt.parts({json.dumps(there + '/')}).find(e => /\\/grip$/.test(e.dataset.key))",
                                 "the other column's foot or a panel in it")
        r = await play.timed(f"!!pt.key({json.dumps(there + '/' + pid)})", lambda: w.drag(x0, y0, x1, y1))
        play.moved = (pid, home, there)
        if not r["ok"]:
            r["want"] = f"the board did not move from {home.rsplit('/', 1)[-1]} to {there.rsplit('/', 1)[-1]}"
        else:
            r["note"] = f"moved from column {home.rsplit('/', 1)[-1]} to {there.rsplit('/', 1)[-1]}"
        return r
    return s_drag


STEP = Step(name='drag', description='drag the board to another column', order=1800,
            needs=(), script=bind, assertion='drag the board to another column', budget=(100, 300))
