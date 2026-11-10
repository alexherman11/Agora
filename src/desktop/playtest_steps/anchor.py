from playtest_steps import Step
from playtest_steps._support import Skip, asyncio, feed_has, json, re, time


def bind(play, opened):
    w, c = play.w, play.copy
    async def s_anchor():
        play.needs("a6638", "highlight and comment through the chat", ("jeff-chat", "commenting"))
        if not getattr(play, "doc", None):
            raise AssertionError("no document open from the step before (about)")
        writer = await asyncio.to_thread(c.do, "find prop:role=writer,prop:actor=alex", "alex")
        if "view=conversation" not in writer:
            raise Skip("Alex's writer note is not at view=conversation in this world: the comment box is doc-page's own")
        await asyncio.sleep(1.0)
        box = "pt.parts('lens:jeff-chat').find(e => /\\/dock\\/commenting\\/on\\/say$/.test(e.dataset.key) && pt.vis(e))"
        pick = """(() => { const pt = window.__pt, l = pt.part('lens:doc-page'), d = l && (l.querySelector('.md-doc') || l);
            const tw = document.createTreeWalker(d, NodeFilter.SHOW_TEXT); let n;
            while ((n = tw.nextNode())) { const m = /[A-Za-z]{3,} [A-Za-z]{3,} [A-Za-z]{3,}/.exec(n.data); if (!m || !pt.vis(n.parentElement)) continue;
              getSelection().setBaseAndExtent(n, m.index, n, m.index + m[0].length); document.dispatchEvent(new PointerEvent('pointerup', {bubbles: true}));
              return m[0]; } return null; })()"""
        words = {}

        async def select():
            words["w"] = await w.js(pick)
        # a scripted selection: headless drags over a contenteditable Markdown text leave none (the comment step says why)
        r1 = await play.timed(f"!!({box})", select, timeout=6000, scripted=True)
        if not r1["ok"]:
            r1["want"] = f"selecting {words.get('w')!r} in the open document did not turn the chat's box into its comment"
            return r1
        x, y = await play.find(box, "the chat's comment box")
        await w.click(x, y)
        note = f"playtest comment {int(time.time()) % 100000}"
        await w.type(note)
        r = await play.timed(feed_has(note, "sent to"), lambda: w.key("Enter"), timeout=6000)
        if not r["ok"]:
            r["want"] = "the comment did not show in the chat with a receipt (sent to ...)"
            return r
        margin = await play.has(f"pt.parts('lens:doc-page').some(e => !e.querySelector('[data-key]') && e.textContent.includes({json.dumps(note)}))")
        talk = re.search(r"talk=(a\d+)", await asyncio.to_thread(c.do, f"read {play.doc}", "hud-playtest"))
        play.talk = talk.group(1) if talk else None
        r["note"] = (f"selected {words.get('w')!r}: the chat's comment box in {r1['ms']} ms; shown quoted with its receipt in {r['ms']} ms; "
                     f"{'anchored in the margin' if margin else 'NOT in the margin'}; kept in {'its Talk ' + play.talk if play.talk else 'no Talk (FAIL)'}")
        if not margin or not play.talk:
            r["ok"] = False
            r["want"] = "the comment is not both in the margin and in the document's Talk"
        return r
    return s_anchor


STEP = Step(name='anchor', description='highlight words, comment in the chat: routed, anchored, a receipt', order=1600,
            needs=(('a6638', 'highlight and comment through the chat'),), script=bind, assertion='highlight words, comment in the chat: routed, anchored, a receipt', budget=(100, 300))
