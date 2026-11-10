from playtest_steps import Step
from playtest_steps._support import asyncio, open_panel, press


def bind(play, opened):
    w, c = play.w, play.copy
    async def s_timer():
        """a6057: the focus timer as one line, in The house's You row (or the top bar while The house is away): Start
        runs it (a Pause appears), × puts it back (Start again)."""
        play.needs("a6057", "the timer as one line", ("home-timer", "ltgo"))
        t = "pt.part('lens:home-timer')"
        if not await play.has(t):
            await open_panel(play, "The house", "home-house")
        if not await play.has(t):
            raise AssertionError("no timer (home-timer) in The house or in the top bar")
        if not await play.has(f"pt.leaf('Start', {t})"):
            raise AssertionError("the timer shows no Start (it was running when the walk began?)")
        r = await play.timed(f"!!pt.leaf('Pause', {t})", press(play, f"pt.pressable(pt.leaf('Start', {t}))", "the timer's Start"))
        if not r["ok"]:
            r["want"] = "Start did not run the timer (no Pause showed)"
            return r
        await asyncio.sleep(1.2)
        await w.shot(play.out / f"{play.n + 1:02d}-timer-running.png")
        r2 = await play.timed(f"!!pt.leaf('Start', {t})", press(play, f"pt.pressable(pt.leaf('×', {t}))", "the timer's ×"))
        if not r2["ok"]:
            r2["want"] = "the timer ran, but × did not put it back"
            return r2
        r["note"] = f"started in {r['ms']} ms, put back in {r2['ms']} ms"
        r["ms"] = max(r["ms"], r2["ms"])
        return r
    return s_timer


STEP = Step(name='timer', description='start the focus timer, then put it back', order=900,
            needs=(('a6057', 'the timer as one line'),), script=bind, assertion='start the focus timer, then put it back', budget=(100, 300))
