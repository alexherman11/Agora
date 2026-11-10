from playtest_steps import Step
from playtest_steps._support import prove, wheel_helpers


def bind(play, opened):
    w, c = play.w, play.copy
    fixture = wheel_helpers(play)
    show = fixture.show
    chat_fixture = fixture.chat_fixture
    async def chat():
        chat_fixture()
        await show("a5080")
        return await prove(play, "pt.parts('lens:jeff-chat').find(e => /\\/feed$/.test(e.dataset.key))", "HUD chat feed")
    return chat


STEP = Step(name='scrollchat', description='wheel the HUD chat feed', order=3000,
            needs=(), script=bind, assertion='wheel the HUD chat feed', budget=(100, 300))
