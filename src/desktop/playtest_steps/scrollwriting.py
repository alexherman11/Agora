from playtest_steps import Step
from playtest_steps._support import prove, wheel_helpers


def bind(play, opened):
    w, c = play.w, play.copy
    fixture = wheel_helpers(play)
    checked = fixture.checked
    create = fixture.create
    show = fixture.show
    writer = fixture.writer
    async def writing():
        doc = create("Long Writing wheel fixture", "role=doc")
        checked(f"read {writer}")
        checked(f'do prop {writer} open={doc} find=""')
        # Stand the Writing app in the actual HUD viewer, not a separate page.
        await show(doc, "writing")
        return await prove(play, "pt.part('lens:doc-page')", "Writing document")
    return writing


STEP = Step(name='scrollwriting', description='wheel a long Writing document', order=2900,
            needs=(), script=bind, assertion='wheel a long Writing document', budget=(100, 300))
