from playtest_steps import Step
from playtest_steps._support import DOCK, asyncio, json, press


def bind(play, opened):
    w, c = play.w, play.copy
    async def s_dock():
        icon = DOCK.format(json.dumps("Board"))
        if not await play.has(icon):
            raise AssertionError("no Board icon on the dock")
        r = await play.timed("pt.parts('lens:home-viewer').some(e => /\\/open\\/f155$/.test(e.dataset.key))", press(play, icon, "Board on the dock"))
        if not r["ok"]:
            r["want"] = "Board on the dock did not open the Board in the middle"
            return r
        await asyncio.sleep(0.3)
        await w.shot(play.out / f"{play.n + 1:02d}-dock-board.png")
        r2 = await play.timed("!!pt.part('lens:jeff-chat') && !pt.parts('lens:home-viewer').some(e => /\\/open\\/f155$/.test(e.dataset.key))",
                              press(play, DOCK.format(json.dumps("JEFF")), "JEFF on the dock"))
        if not r2["ok"]:
            r2["want"] = "JEFF on the dock did not bring the chat back"
            return r2
        r["note"] = f"Board opened in {r['ms']} ms, JEFF's chat back in {r2['ms']} ms"
        r["ms"] = max(r["ms"], r2["ms"])
        return r
    return s_dock


STEP = Step(name='dock', description='use the dock: Board, then back to JEFF', order=2500,
            needs=(), script=bind, assertion='use the dock: Board, then back to JEFF', budget=(100, 300))
