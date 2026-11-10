"""reload_check.py (a7925): does an open home base pick up new painter files by itself? On hud_playtest's disposable
copy, in the guarded hidden Edge window, the painter files the COPY's door serves (its own temp desk-shell, made by this
run) are changed under an open page, as a landing changes the live checkout's; lens.js asks /api/version every 5 s.

    python src/desktop/combined-review/reload_check.py [--small]

1. hands free: the page should reload on its own, keeping the view, and come back with the partition painter;
2. an unsent words in the chat composer: it should wait (the quiet line says so) and keep the words;
3. the words cleared by keys: it should then load.
Nothing is sent (no Enter), nothing on Alex's screen, never the live world.
"""
import argparse
import asyncio
import datetime
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
sys.path.insert(0, str(LAB))
import hud_playtest as pt  # noqa: E402

DEMOS = Path(r"C:/Projects/Agora4/src/desktop/demos/combined-review")
TA = "[...document.querySelectorAll('textarea')].find(e => e.getClientRects().length && e.closest('[data-key*=\"lens:jeff-chat\"]'))"
LOOK = ("(() => ({ origin: performance.timeOrigin, mark: window.__a7925 || null, partition: !!document.querySelector('[data-partition]'), "
        "Partition: typeof window.Partition, line: [...document.querySelectorAll('body *')].filter(e => !e.children.length && /screen code/.test(e.textContent)).map(e => e.textContent.trim()).slice(0, 2), "
        f"words: ({TA} || {{}}).value ?? null, page: [innerWidth, innerHeight, devicePixelRatio] }}))()")


async def wait_reload(win, origin, secs):
    t = time.time()
    while time.time() - t < secs:
        await asyncio.sleep(0.5)
        try:
            s = await win.js(LOOK)
        except Exception:
            continue
        if s and s["origin"] != origin and s["partition"]:
            return round(time.time() - t, 1), s
    return None, await win.js(LOOK)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--small", action="store_true")
    a = ap.parse_args()
    pt.SIZE = (1280, 800) if a.small else (2560, 1440)
    out = DEMOS / f"{datetime.datetime.now():%Y-%m-%d-%H%M%S}-{pt.SIZE[0]}x{pt.SIZE[1]}-reload"
    out.mkdir(parents=True, exist_ok=True)
    copy = pt.Copy("frontier-try")
    shell = Path(copy.state) / "desk-shell"
    marker = shell / "a7925-marker.txt"          # a new painter file in the copy's own static dir (made by this run)
    win, guard, rep = None, None, {"steps": []}
    try:
        win = pt.Window(False)
        await win.open(copy.url())
        for _ in range(100):
            await asyncio.sleep(0.2)
            if await win.js("!!document.querySelector('[data-partition]')"):
                break
        await asyncio.sleep(6)                    # lens.js has asked /api/version once and keeps the painter it has
        await win.js("document.getElementById('hud-frost')?.remove()")
        rep["start"] = await win.js(LOOK)

        # 1. hands free
        await win.js("window.__a7925 = 1")
        o = (await win.js(LOOK))["origin"]
        marker.write_text("1", encoding="utf-8")
        took, s = await wait_reload(win, o, 25)
        rep["steps"].append({"step": "hands free, new painter files", "reloaded after s": took, "after": s})
        await win.shot(out / "1-free.png")

        # 2. unsent words in the composer: press it, type, then new painter files
        h = await win.js(f"(() => {{ const t = {TA}; if (!t) return null; const b = t.getBoundingClientRect(); return [b.left + b.width / 2, b.top + b.height / 2]; }})()")
        if not h:
            rep["steps"].append({"step": "composer", "blocked": "no visible chat composer at this size"})
        else:
            await win.click(*h)
            await asyncio.sleep(0.4)
            await win.type("unsent a7925 words")
            await asyncio.sleep(0.6)
            await win.js("window.__a7925 = 2")
            o = (await win.js(LOOK))["origin"]
            marker.write_text("22", encoding="utf-8")
            took, s = await wait_reload(win, o, 20)
            rep["steps"].append({"step": "unsent words in the composer, new painter files", "reloaded after s": took, "after": s})
            await win.shot(out / "2-busy.png")

            # 3. the words cleared by keys (a hand's Ctrl+A, Backspace): it should load now
            await win.key("ctrl+a")
            await win.key("Backspace")
            await asyncio.sleep(0.3)
            took, s = await wait_reload(win, o, 25)
            rep["steps"].append({"step": "words cleared", "reloaded after s": took, "after": s})
            await win.shot(out / "3-cleared.png")
        rep["errors"] = await win.js("(window.__pt && window.__pt.errors) || []")
    finally:
        if win:
            guard = await win.close()
        copy.close()
    rep["guard"] = guard
    (out / "report.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print(json.dumps(rep, indent=1, ensure_ascii=False, default=str)[:6000])
    print(f"guard: {guard[1] if guard else 'none'}")
    print(f"report: {out / 'report.json'}")


if __name__ == "__main__":
    asyncio.run(main())
