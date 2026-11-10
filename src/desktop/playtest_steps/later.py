from playtest_steps import Step
from playtest_steps._support import helpers


def bind(play, opened):
    w, c = play.w, play.copy
    answer = helpers(play).answer
    return lambda: answer('Later', True, 'moved below LATER')


STEP = Step(name='later', description='answer a waiting item: Later, and see it go below', order=500,
            needs=(), script=bind, assertion='answer a waiting item: Later, and see it go below', budget=(100, 300))
