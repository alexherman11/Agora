from playtest_steps import Step
from playtest_steps._support import CHAT, asyncio, feed_has, json, re, time


def bind(play, opened):
    w, c = play.w, play.copy
    async def s_about():
        play.needs("a6638", "the chat is about what is open", ("jeff-chat", "abouting"))
        found = await asyncio.to_thread(c.do, "find prop:role=doc,prop:author", "alex")
        doc = re.search(r"(a\d+) note \"([^\"]+)\"", found)
        view = re.search(r"(a\d+) note \"[^\"]*\" · role=home-view actor=alex",
                         await asyncio.to_thread(c.do, "find prop:role=home-view,prop:actor=alex", "alex"))
        if not doc or not view:
            raise AssertionError("no authored document (role=doc, a note) or no viewer note of Alex's in this world")
        play.doc, play.doc_title = doc.group(1), doc.group(2)

        async def open_it():
            await asyncio.to_thread(c.do, f"read {view.group(1)}", "alex")
            await asyncio.to_thread(c.do, f"do prop {view.group(1)} viewing={play.doc}", "alex")
        r = await play.timed(f"pt.parts('lens:jeff-chat').some(e => /\\/about\\//.test(e.dataset.key) && pt.vis(e) && e.textContent.includes({json.dumps(play.doc_title)}))",
                             open_it, timeout=6000, scripted=True)
        if not r["ok"]:
            r["want"] = f"the chat did not say About {play.doc_title!r} once it was open in the middle"
            return r
        side = await w.js("(() => { const pt = window.__pt, a = pt.rect(pt.part('lens:doc-page')), b = pt.rect(pt.part('lens:jeff-chat')); return a && b ? a[0] + a[2] <= b[0] + 2 : null; })()")
        x, y = await play.find(f"{CHAT}.querySelector('[data-key$=\"/dock/say\"] textarea')", "the chat composer")
        await w.click(x, y)
        ask = f"playtest question {int(time.time()) % 100000}"
        await w.type(ask)
        r2 = await play.timed(feed_has(ask, play.doc_title), lambda: w.key("Enter"), timeout=6000)
        if not r2["ok"]:
            r2["want"] = "the question did not show in the feed tagged with what was open"
            return r2
        r2["note"] = (f"About {play.doc_title!r} in {r['ms']} ms after it opened; the page {'stands left of' if side else 'is NOT left of'} the chat; "
                      f"the question shown tagged in {r2['ms']} ms" + ("" if side else " (FAIL: not beside)"))
        if not side:
            r2["ok"] = False
            r2["want"] = "the document and the chat are not side by side"
        return r2
    return s_about


STEP = Step(name='about', description='open a document: the chat is about it; a question carries it', order=1500,
            needs=(('a6638', 'the chat is about what is open'),), script=bind, assertion='open a document: the chat is about it; a question carries it', budget=(100, 300))
