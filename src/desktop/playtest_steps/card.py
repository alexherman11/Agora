from playtest_steps import Step
from playtest_steps._support import asyncio, json, press


def bind(play, opened):
    w, c = play.w, play.copy
    async def s_card():
        k = await w.js("(() => { const pt = window.__pt; const c = pt.parts('lens:home-board').find(e => e.dataset.foldInline && e.dataset.folded === '1');"
                       " return c ? c.dataset.key : null; })()")
        if not k:
            raise AssertionError("no folded card on the board to open")
        kk = json.dumps(k)
        line = f"[...pt.key({kk}).children].find(e => e.dataset && e.dataset.peek)"
        r = await play.timed(f"pt.key({kk}) && pt.key({kk}).dataset.folded !== '1'", press(play, line, "the card's line"))
        if not r["ok"]:
            r["want"] = "the card did not open"
            return r
        await asyncio.sleep(0.4)
        await w.shot(play.out / f"{play.n + 1:02d}-card-open.png")
        r2 = await play.timed(f"pt.key({kk}) && pt.key({kk}).dataset.folded === '1'", press(play, line, "the open card's line"))
        if not r2["ok"]:
            r2["want"] = "the card opened but a second press did not close it"
            return r2
        r["note"] = f"opened in {r['ms']} ms, closed in {r2['ms']} ms (card {k.rsplit('/', 1)[-1]})"
        r["ms"] = max(r["ms"], r2["ms"])
        return r
    return s_card


STEP = Step(name='card', description='click a card to expand it, and again to close it', order=400,
            needs=(), script=bind, assertion='click a card to expand it, and again to close it', budget=(100, 300))
