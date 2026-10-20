from playtest_steps import Step
from playtest_steps._support import prove, wheel_helpers


def bind(play, opened):
    w, c = play.w, play.copy
    fixture = wheel_helpers(play)
    create = fixture.create
    show = fixture.show
    async def reader():
        play.needs("a6460", "proposal reader wheel check", ("reader", "markdown"))
        report = create("Long proposal wheel fixture", "tags=ready-for-review")
        await show(report, "reader")
        return await prove(play, "pt.part('lens:reader')", "proposal reader")
    return reader


STEP = Step(name='scrollreader', description='wheel a long proposal in the reader', order=3400,
            needs=(('a6460', 'proposal reader wheel check'),), script=bind, assertion='wheel a long proposal in the reader', budget=(100, 300))
