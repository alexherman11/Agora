from playtest_steps import Step
from playtest_steps._support import prove, wheel_helpers


def bind(play, opened):
    w, c = play.w, play.copy
    fixture = wheel_helpers(play)
    create = fixture.create
    show = fixture.show
    async def note():
        await show(create("Long note wheel fixture"))
        return await prove(play, "pt.part('lens:home-note')", "long note")
    return note


STEP = Step(name='scrollnote', description='wheel a long note inside its panel', order=2800,
            needs=(), script=bind, assertion='wheel a long note inside its panel', budget=(100, 300))
