from playtest_steps import Step


def bind(play, opened):
    w, c = play.w, play.copy
    async def s_writeleft():
        play.needs("a5949", "Writing on the left of the chat", ("home-viewer", "split"))
        if not await play.has("pt.part('lens:writing')"):
            raise AssertionError("Writing is not painted in the home base")
        side = await w.js("(() => { const pt = window.__pt, a = pt.rect(pt.part('lens:writing')), b = pt.rect(pt.part('lens:jeff-chat')); return a && b ? a[0] + a[2] <= b[0] + 2 : null; })()")
        if not side:
            raise AssertionError("Writing is not on the left of the chat")
        # how wide the page itself is: a page squeezed to a few words a line is there but not writable
        width = await w.js("(() => { const pt = window.__pt, l = pt.part('lens:writing'), d = l && (l.querySelector('.md-doc') || l.querySelector('[contenteditable]'));"
                           " return d ? Math.round(d.getBoundingClientRect().width) : null; })()")
        note = f"Writing stands left of the chat; its page is {width} px wide"
        if width is not None and width < 360:
            raise AssertionError(note + ": squeezed to a few words a line")
        return {"note": note}
    return s_writeleft


STEP = Step(name='writedoc', description='Writing on the left of the chat', order=1100,
            needs=(('a5949', 'Writing on the left of the chat'),), script=bind, assertion='Writing on the left of the chat', budget=(100, 300))
