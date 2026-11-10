from playtest_steps import Step
from playtest_steps._support import open_panel


def bind(play, opened):
    w, c = play.w, play.copy
    async def s_board():
        play.needs_board = True
        r = await open_panel(play, "The board", "home-board")
        lanes = await w.js("window.__pt.parts('lens:home-board').filter(e => /\\/head\\/name$/.test(e.dataset.key)).map(e => e.textContent.trim())")
        if not lanes:
            raise AssertionError("the board shows no lanes")
        r = r or {"note": "already out"}
        r["note"] = (r.get("note", "") + "; lanes: " + ", ".join(lanes)).lstrip("; ")
        return r
    return s_board


STEP = Step(name='board', description='see the board (its chip on the shelf)', order=300,
            needs=(), script=bind, assertion='see the board (its chip on the shelf)', budget=(100, 300))
