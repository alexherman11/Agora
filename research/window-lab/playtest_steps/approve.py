from playtest_steps import Step
from playtest_steps._support import helpers


def bind(play, opened):
    w, c = play.w, play.copy
    answer = helpers(play).answer
    return lambda: answer('Seen / Done', True, 'left the list')


STEP = Step(name='approve', description='answer a waiting item: Seen / Done, and see it leave', order=600,
            needs=(), script=bind, assertion='answer a waiting item: Seen / Done, and see it leave', budget=(100, 300))
