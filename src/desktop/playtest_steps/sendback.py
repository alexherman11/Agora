from playtest_steps import Step
from playtest_steps._support import Missing, helpers, open_panel


def bind(play, opened):
    w, c = play.w, play.copy
    on_board = helpers(play).on_board
    answer = helpers(play).answer
    async def s_sendback():
        r = await on_board("Send back", "sent back")
        if r is not None:
            return r
        await open_panel(play, "Waiting on you", "waiting-on-me")
        lens = c.do("read waiting-on-me", "hud-playtest")
        if "send back" not in lens.lower():
            raise Missing("no Send back on a waiting item (waiting-on-me has Seen / Done, Later, Open fully, Open here); no commission named for it")
        return await answer("Send back", True, "sent back")
    return s_sendback


STEP = Step(name='sendback', description='answer a waiting item: Send back', order=700,
            needs=(), script=bind, assertion='answer a waiting item: Send back', budget=(100, 300))
