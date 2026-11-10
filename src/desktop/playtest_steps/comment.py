from playtest_steps import Step
from playtest_steps._support import asyncio, json, time


def bind(play, opened):
    w, c = play.w, play.copy
    async def s_comment():
        play.needs("a5949", "highlight-to-comment in Writing", ("home-viewer", "split"))
        doc = "pt.part('lens:writing') && (pt.part('lens:writing').querySelector('.md-doc') || pt.part('lens:writing').querySelector('[contenteditable]'))"
        if not await play.has(doc):
            raise AssertionError("no Writing document painted in the home base")
        await asyncio.sleep(1.5)        # settled: a drag in the page's late repaints would test the repaint, not the drag
        # some words of the page's own, mid-paragraph: their place on the screen, to drag over them as a person would
        span = await w.js(f"""(() => {{ const pt = window.__pt, d = {doc}; const tw = document.createTreeWalker(d, NodeFilter.SHOW_TEXT); let n;
            while ((n = tw.nextNode())) {{ const m = /[A-Za-z]{{3,}} [A-Za-z]{{3,}}/.exec(n.data); if (!m) continue;
              const r = document.createRange(); r.setStart(n, m.index); r.setEnd(n, m.index + m[0].length); const b = r.getBoundingClientRect();
              if (b.width < 30 || b.height > 40 || !pt.vis(n.parentElement)) continue;
              return {{ words: m[0], x0: b.left + 1, x1: b.right - 1, y: b.top + b.height / 2 }}; }} return null; }})()""")
        if not span:
            raise AssertionError("no line of words in the Writing page to select")
        # a6638: with Alex's writer note at view=conversation the comment box is the chat's own (dock/commenting)
        box = ("(pt.parts('lens:writing').find(e => /\\/pending\\/box$/.test(e.dataset.key))"
               " || pt.parts('lens:jeff-chat').find(e => /\\/dock\\/commenting\\/on\\/say$/.test(e.dataset.key) && pt.vis(e)))")
        # posted window messages select no text in Chromium (ran 16 Oct, with a control over the chat's words), so the
        # drag goes as DevTools mouse events: a mouse drag down Chromium's own input path, selection and all
        r1 = await play.timed(f"!!({box})", lambda: w.drag(span["x0"], span["y"], span["x1"], span["y"], steps=8, devtools=True))
        how = "a mouse drag over the words (DevTools mouse events)"
        if not r1["ok"]:                      # a person's second try: click into the page first, then drag
            first_sel = await w.js("String(getSelection())")
            await w.click((span["x0"] + span["x1"]) / 2, span["y"])
            await asyncio.sleep(0.8)
            span2 = await w.js(f"""(() => {{ const pt = window.__pt, d = {doc}; const tw = document.createTreeWalker(d, NodeFilter.SHOW_TEXT); let n;
                while ((n = tw.nextNode())) {{ const i = n.data.indexOf({json.dumps(span['words'])}); if (i < 0) continue;
                  const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + {len(span['words'])}); const b = r.getBoundingClientRect();
                  return {{ x0: b.left + 1, x1: b.right - 1, y: b.top + b.height / 2 }}; }} return null; }})()""") or span
            r1 = await play.timed(f"!!({box})", lambda: w.drag(span2["x0"], span2["y"], span2["x1"], span2["y"], steps=8, devtools=True))
            if r1["ok"]:
                how = (f"a mouse drag only after a click into the page (the first drag, on the page untouched, selected "
                       f"{first_sel[:30]!r} and opened no Comment box)")
        if not r1["ok"]:                      # the drag selected nothing the page took up: say so, and select by script
            sel = await w.js("String(getSelection())")
            # a control: the same posted drag over plain words in the chat's feed. If it selects there, the Writing
            # page is what refuses a drag (a person would meet that); if not, it is this script's input
            ctl = await w.js("""(() => { const pt = window.__pt, c = pt.part('lens:jeff-chat'); if (!c) return null;
                const tw = document.createTreeWalker(c, NodeFilter.SHOW_TEXT); let n;
                while ((n = tw.nextNode())) { const m = /[A-Za-z]{3,} [A-Za-z]{3,} [A-Za-z]{3,}/.exec(n.data); if (!m || !pt.vis(n.parentElement)) continue;
                  const r = document.createRange(); r.setStart(n, m.index); r.setEnd(n, m.index + m[0].length); const b = r.getBoundingClientRect();
                  if (b.height > 40 || b.width < 30) continue; return { x0: b.left + 1, x1: b.right - 1, y: b.top + b.height / 2 }; } return null; })()""")
            got = None
            if ctl:
                await w.js("getSelection().removeAllRanges()")
                await w.drag(ctl["x0"], ctl["y"], ctl["x1"], ctl["y"], steps=8, devtools=True)
                await asyncio.sleep(0.4)
                got = await w.js("String(getSelection())")
                await w.js("getSelection().removeAllRanges()")
            how = ("a scripted selection (a drag over the words opened no Comment box; the page's selection after it: "
                   f"{sel[:40]!r}; the same drag over the chat's words selected {got[:40] if got is not None else 'nothing found to try'!r}"
                   + (": so the Writing page refuses a drag-select" if got and not sel else
                      ": so the drag is this script's limit, not the page's" if not got else "") + ")")
            r1 = await play.timed(f"!!({box})", lambda: w.js(
                f"""(() => {{ const d = {doc.replace('pt.', 'window.__pt.')}; const tw = document.createTreeWalker(d, NodeFilter.SHOW_TEXT); let n;
                while ((n = tw.nextNode())) {{ const i = n.data.indexOf({json.dumps(span['words'])}); if (i >= 0) {{
                  getSelection().setBaseAndExtent(n, i, n, i + {len(span['words'])}); document.dispatchEvent(new PointerEvent('pointerup')); return 1; }} }} return 0; }})()"""), scripted=True)
            if not r1["ok"]:
                r1["want"] = "selecting words in Writing opened no Comment box"
                return r1
        x, y = await play.find(box, "the Comment box")
        await w.click(x, y)
        await asyncio.sleep(0.3)
        note = f"playtest note {int(time.time()) % 100000}"
        await w.type(note)
        await asyncio.sleep(0.3)
        # shown twice: the margin note, and its line in the page's Talk or (a6638) in the Conversation
        shown = f"[...pt.parts('lens:writing'), ...pt.parts('lens:jeff-chat')].filter(e => !e.querySelector('[data-key]') && e.textContent.includes({json.dumps(note)}))"
        r = await play.timed(f"{shown}.length >= 2", lambda: w.key("Enter"), timeout=6000)
        if not r["ok"]:
            n = await w.js(f"(() => {{ const pt = window.__pt; return {shown}.map(e => e.dataset.key.split('/').slice(-3).join('/')); }})()")
            r["want"] = f"the comment did not show both as a margin note and a line in the page's Talk (it shows in: {n or 'nowhere'})"
            r["timeout"] = 6000
            return r
        r["note"] = f"selected {span['words']!r} by {how}; the Comment box in {r1['ms']} ms; margin note and Talk line in {r['ms']} ms"
        return r
    return s_comment


STEP = Step(name='comment', description='type in Writing, select words, comment: margin note', order=1200,
            needs=(('a5949', 'highlight-to-comment in Writing'),), script=bind, assertion='type in Writing, select words, comment: margin note', budget=(100, 300))
