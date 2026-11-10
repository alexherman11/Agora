from playtest_steps import Step


def bind(play, opened):
    w, c = play.w, play.copy
    async def s_open():
        r = dict(opened)
        if r.get("ok"):
            r["note"] = "a cold load of the page (from navigation); the hotkey shows an already loaded page"
        return r
    return s_open


STEP = Step(name='open', description='open the home base: tiles and dock painted', order=100,
            needs=(), script=bind, assertion='open the home base: tiles and dock painted', budget=(1000, 3000))
