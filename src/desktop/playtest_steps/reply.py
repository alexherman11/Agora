from playtest_steps import Step
from playtest_steps._support import asyncio, feed_has, helpers, q, time


def bind(play, opened):
    w, c = play.w, play.copy
    answer = helpers(play).answer
    async def s_reply():
        play.needs("a6638", "an agent's answer arrives in the chat", ("jeff-chat", "tagline"))
        talk = getattr(play, "talk", None)
        if not talk:
            raise AssertionError("no Talk from the step before (anchor)")
        words = f"playtest answer {int(time.time()) % 100000}"
        said = []

        async def answer():
            await asyncio.to_thread(c.do, f"read {talk} :3", "pike")
            said.append(await asyncio.to_thread(c.do, f"do append {talk} line={q('@alex: ' + words)}", "pike"))
        r = await play.timed(feed_has(words, play.doc_title), answer, timeout=6000, scripted=True)
        rep, r["ms"], r["first_ms"] = r.get("ms"), None, None
        if not r["ok"]:
            r["want"] = f"Pike's answer in the Talk did not arrive in the chat tagged about {play.doc_title!r} (the door: {(said or [''])[0][:160]!r})"
            return r
        r["note"] = f"Pike's answer (in the copy) painted in the chat, tagged with the document, {rep} ms after it was said"
        return r
    return s_reply


STEP = Step(name='reply', description='the author answers in the Talk: it arrives in the chat, tagged', order=1700,
            needs=(('a6638', "an agent's answer arrives in the chat"),), script=bind, assertion='the author answers in the Talk: it arrives in the chat, tagged', budget=(100, 300))
