from playtest_steps import Step
from playtest_steps._support import COMPOSER, asyncio, json, q, time


def bind(play, opened):
    w, c = play.w, play.copy
    async def s_chat():
        x, y = await play.find(COMPOSER, "the chat composer")
        await w.click(x, y)
        draft = "playtest draft, kept across a repaint"
        await w.type(draft)
        await asyncio.sleep(0.4)
        got = await w.js(f"(() => {{ const pt = window.__pt, t = {COMPOSER}; return t ? t.value : null; }})()")
        if got != draft:
            raise AssertionError(f"typing into the composer gave {got!r}")
        stamp = f"playtest repaint {int(time.time())}"
        said = []

        # the desk holds back a line from someone who has not read the chat's newest lines: he reads it first
        await asyncio.to_thread(c.do, "read a5080", "jeff")

        async def speak():
            said.append(await asyncio.to_thread(c.do, f"do append a5080 line={q('@alex: ' + stamp)}", "jeff"))
        # someone else speaks in the chat (in the copy): the feed repaints under the draft
        r = await play.timed(f"pt.parts('lens:jeff-chat').some(e => !e.querySelector('[data-key]') && e.textContent.includes({json.dumps(stamp)}))",
                             speak, timeout=6000, scripted=True)
        if not r.get("ok"):
            r["status"] = (r.get("status") or "") + f" (the door said to jeff's line: {(said or [''])[0][:200]!r})"
        kept = await w.js(f"(() => {{ const pt = window.__pt, t = {COMPOSER}; return t ? t.value : null; }})()")
        rep, r["ms"], r["first_ms"] = r["ms"], None, None    # no input of his: the repaint's speed is not his press's
        if not r.get("ok"):
            r["want"] = "the other person's line did not paint in the feed"
            r["timeout"] = 6000
            return r
        if kept != draft:
            raise AssertionError(f"the draft was lost in the repaint: the composer holds {kept!r}")
        play.draft = draft
        return {"note": f"a line from jeff (in the copy) painted in the feed {rep} ms after it was sent; the draft stayed whole"}
    return s_chat


STEP = Step(name='chat', description='type in the chat composer; the draft survives a repaint', order=1300,
            needs=(), script=bind, assertion='type in the chat composer; the draft survives a repaint', budget=(100, 300))
