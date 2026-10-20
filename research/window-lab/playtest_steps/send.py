from playtest_steps import Step
from playtest_steps._support import COMPOSER, json


def bind(play, opened):
    w, c = play.w, play.copy
    async def s_send():
        draft = getattr(play, "draft", None)
        if not draft:
            raise AssertionError("no draft from the step before")
        x, y = await play.find(COMPOSER, "the chat composer")
        await w.click(x, y)
        r = await play.timed(f"(() => {{ const t = {COMPOSER}; return t && t.value === '' && pt.parts('lens:jeff-chat').some(e => !e.querySelector('[data-key]') && e.textContent.includes({json.dumps(draft)})); }})()",
                             lambda: w.key("Enter"))
        if not r["ok"]:
            r["want"] = "Enter did not send the draft into the feed (and empty the composer)"
        else:
            r["note"] = "sent in the copy's Conversation (no one real reads it)"
        return r
    return s_send


STEP = Step(name='send', description='send it with Enter: it shows in the feed', order=1400,
            needs=(), script=bind, assertion='send it with Enter: it shows in the feed', budget=(100, 300))
