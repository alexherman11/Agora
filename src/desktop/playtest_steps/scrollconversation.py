from playtest_steps import Step
from playtest_steps._support import prove, wheel_helpers


def bind(play, opened):
    w, c = play.w, play.copy
    fixture = wheel_helpers(play)
    show = fixture.show
    chat_fixture = fixture.chat_fixture
    async def conversation():
        chat_fixture()
        await show("a5080", "conversation")
        return await prove(play, "pt.part('lens:conversation')", "Conversation feed")
    return conversation


STEP = Step(name='scrollconversation', description='wheel the Conversation feed', order=3100,
            needs=(), script=bind, assertion='wheel the Conversation feed', budget=(100, 300))
