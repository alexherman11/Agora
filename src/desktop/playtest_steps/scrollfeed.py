from playtest_steps import Step
from playtest_steps._support import prove, wheel_helpers, witnessed


def bind(play, opened):
    w, c = play.w, play.copy
    fixture = wheel_helpers(play)
    checked = fixture.checked
    create = fixture.create
    show = fixture.show
    viewer = fixture.viewer
    async def feed():
        card = create("Stand-in worker wheel fixture", "worker=wheel-fixture")
        rows = [{"kind":"head", "who":"Stand-in worker", "state":"working", "last":150, "events":150}]
        rows += [{"kind":"action", "group":"actions", "n":i, "at":"12:00",
                  "text":f"Stand-in action {i}. " + "Content in the At-work feed. " * 12} for i in range(1,151)]
        witnessed.write(c.session, f"feed-{card}", rows, by="hud-playtest")
        checked(f"read {viewer}")
        checked(f'do prop {viewer} feed_held=0 feed_show=""')
        await show(card, "home-feed")
        return await prove(play, "pt.parts('lens:home-feed').find(e => /\\/follow$/.test(e.dataset.key))", "At-work feed")
    return feed


STEP = Step(name='scrollfeed', description='wheel the At-work feed', order=3200,
            needs=(), script=bind, assertion='wheel the At-work feed', budget=(100, 300))
