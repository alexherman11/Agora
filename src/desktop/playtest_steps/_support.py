"""Shared fixtures only; individual steps live in sibling files."""
import asyncio
import json
import re
import subprocess
import time
from types import SimpleNamespace

from hud_playtest import CHIP, DOCK, HERE, PY, Missing, Skip, q, press, open_panel, panel
from hud_scroll import prove
import witnessed

WAIT_ITEMS = "window.__pt.parts('lens:waiting-on-me').filter(e => /\\/now\\/[a-z]\\d+\\/head$/.test(e.dataset.key) || /\\/designs\\/[a-z]\\d+\\/head$/.test(e.dataset.key))"

BOARD_NEED = "window.__pt.parts('lens:home-board').filter(e => /\\/need\\/reviews\\/[a-z]\\d+\\/line$/.test(e.dataset.key))"

ON_BOARD = {"Seen / Done": "Looks good", "Later": "Later", "Send back": "Send back"}

COMPOSER = "pt.part('lens:jeff-chat') && pt.part('lens:jeff-chat').querySelector('.explicit-composer textarea, textarea')"

CHAT = "pt.part('lens:jeff-chat')"

FEEDHAS = ("(words => [...pt.parts('lens:jeff-chat')].some(e => !e.querySelector('[data-key]') && /\\/(feed|everything)\\//.test(e.dataset.key)"
           " && e.textContent.includes(words)))")

COLS = "window.__pt.parts('lens:home-tiling').filter(e => /\\/tiling\\/[a-z]\\d+$/.test(e.dataset.key))"

def feed_has(words, also=None):
    tail = (f" && pt.parts('lens:jeff-chat').some(e => /\\/tagline\\//.test(e.dataset.key) && e.textContent.includes({json.dumps(also)}))"
            if also else "")
    return f"{FEEDHAS}({json.dumps(words)}){tail}"

def helpers(play):
    w, c = play.w, play.copy
    async def on_board(button, label):
        try:
            await open_panel(play, "The board", "home-board")
        except AssertionError:
            return None                          # no board in this layout: Waiting on you answers
        # a press before this one may still be on its way (its card hidden at once, `leaves`): when its answer is
        # painted the list closes up, so aim only once nothing is in flight, as a person aims at a settled screen
        await w.js("new Promise(r => { const t0 = performance.now(); const f = () => !document.querySelector('[data-sending=\"1\"]') || performance.now() - t0 > 3000 ? r(true) : setTimeout(f, 20); f(); })")
        heads = await w.js(f"{BOARD_NEED}.map(e => e.dataset.key)")
        if not heads:
            return None
        head = heads[0]
        item, hk, word = head.split("/")[-2], json.dumps(head), ON_BOARD[button]
        gone = f"!pt.parts('lens:home-board').some(e => /\\/need\\/reviews\\/{item}\\/line$/.test(e.dataset.key))"
        later = f"pt.all('lens:home-board').some(e => /\\/need\\/later\\/a\\/{item}$/.test(e.dataset.key))"
        pred = gone + (f" && {later}" if button == "Later" else "")
        r = await play.timed(pred, press(play, f"pt.pressable(pt.leaf({json.dumps(word)}, pt.key({hk})))", f"'{word}' on the board"))
        if not r["ok"]:
            r["want"] = f"'{word}' did not take {item} off NEEDS YOU" + (" and under Later" if button == "Later" else "")
            return r
        r["note"] = f"{item}: on the board's NEEDS YOU line, one press: {label} in {r['ms']} ms"
        return r

    async def answer(button, want_gone_from_now, label):
        r = await on_board(button, label)
        if r is not None:
            return r
        r0 = await open_panel(play, "Waiting on you", "waiting-on-me")
        heads = await w.js(f"{WAIT_ITEMS}.map(e => e.dataset.key)")
        heads = [h for h in heads if "/now/" in h]
        if not heads:
            raise AssertionError("nothing waits on Alex in the list (nothing to answer)")
        head = heads[0]
        item = head.split("/")[-2]
        hk = json.dumps(head)
        r1 = await play.timed(f"pt.leaf({json.dumps(button)}, pt.key({hk}).parentElement)", press(play, f"pt.key({hk})", "the item"))
        if not r1["ok"]:
            r1["want"] = f"a press on the item did not open it to show {button}"
            return r1
        gone = f"!pt.parts('lens:waiting-on-me').some(e => /\\/now\\/{item}\\/head$/.test(e.dataset.key))"
        later = f"pt.parts('lens:waiting-on-me').some(e => /\\/later\\/{item}\\/head$/.test(e.dataset.key))"
        pred = gone + (f" && {later}" if button == "Later" else "")
        r = await play.timed(pred, press(play, f"pt.pressable(pt.leaf({json.dumps(button)}, pt.key({hk}).parentElement))", f"'{button}'"))
        if not r["ok"]:
            r["want"] = f"'{button}' did not take {item} off the list" + (" and below LATER" if button == "Later" else "")
            return r
        r["note"] = f"{item}: opened in {r1['ms']} ms, {label} in {r['ms']} ms"
        return r

    async def widen_column(p):
        """a5994's tiling: ⇔ steps a column through a third, a half, two thirds of the room and back to its own."""
        before = await w.js(f"(() => {{ const pt = window.__pt; return pt.rect({p}); }})()")
        btn = f"pt.pressable(pt.leaf('⇔', {p}))"
        r = await play.timed(f"(() => {{ const r = pt.rect({p}); return r && r[2] > {before[2] * 1.2}; }})()", press(play, btn, "⇔ on Music"))
        if not r["ok"]:
            r["want"] = "⇔ did not widen Music's column"
            return r
        await asyncio.sleep(0.3)
        await w.shot(play.out / f"{play.n + 1:02d}-widen-wide.png")
        times = [r["ms"]]
        for k in range(3):                      # on round: back to the width it had
            mid = await w.js(f"(() => {{ const pt = window.__pt; return pt.rect({p}); }})()")
            r2 = await play.timed(f"(() => {{ const r = pt.rect({p}); return r && Math.abs(r[2] - {mid[2]}) > 8; }})()", press(play, btn, "⇔ on Music"))
            if not r2["ok"]:
                r2["want"] = f"the press {k + 2} on ⇔ changed nothing"
                return r2
            times.append(r2["ms"])
            if abs((await w.js(f"(() => {{ const pt = window.__pt; return pt.rect({p}); }})()"))[2] - before[2]) < before[2] * 0.08:
                break
        else:
            return {"ok": False, "want": "⇔ never came back round to Music's own width", "sawInput": True}
        r["note"] = f"⇔ pressed {len(times)} times round to its own width: " + ", ".join(f"{t} ms" for t in times) + " (a5994's tiling)"
        r["ms"] = max(times)
        return r
    return SimpleNamespace(on_board=on_board, answer=answer, widen_column=widen_column)

def wheel_helpers(play):
    """Seven independent reported steps, with before/after shots, selected by --only scroll."""
    from hud_playtest import q, press, open_panel
    import witnessed
    c = play.copy
    viewer = "prop:role=home-view,prop:actor=alex"
    writer = "prop:role=writer,prop:actor=alex"
    long_text = "\n\n".join(f"## Passage {i}\n\n" + ("Long-content wheel fixture. " * 18) for i in range(1, 65))
    def checked(line, who="alex"):
        said = c.do(line, who)
        failed = said.startswith("ERR") or "refused" in said.lower()
        assert not failed or "nothing to change" in said.lower(), f"scroll fixture refused: {said[:400]}"
        return said
    def create(title, props=""):
        checked("look f5204")
        said = checked(f"do create f5204 kind=note title={q(title)} {props} text={q(long_text)}")
        hit = re.search(r"created (a\d+)", said)
        assert hit, f"scroll fixture has no create receipt: {said[:400]}"
        return hit.group(1)
    async def show(thing, lens=""):
        checked(f"read {viewer}")
        checked(f'do prop {viewer} viewing={q(thing)} with={q(lens)} find=""')
        await asyncio.sleep(2)
    def chat_fixture():
        checked("read a5080", "jeff")
        checked(f"do append a5080 line={q(long_text)}", "jeff")
    return SimpleNamespace(checked=checked, create=create, show=show, chat_fixture=chat_fixture, viewer=viewer, writer=writer)
