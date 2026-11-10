"""Hidden phone pass (390x844, headless Edge) over the live board as a guest: press nav items inside the painter's
sandboxed frame (through an isolated world in that frame) and take screenshots into deploy/evidence/.

    C:/Projects/Agora4/.venv/Scripts/python.exe research/community-app/deploy/mobile_check.py --cookies <file> [--steps ...]

--cookies keeps the guest's session between runs (a scratch file, never committed). Without one, it joins through
/meeting as a new guest named --name. Claude, 5 Nov 2026.
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "site" / "scenario"))
from cdp import Browser  # noqa: E402

BASE = "https://seabright.example.org"
OUT = HERE / "evidence"


class FrameTab:
    """The painter's sandboxed frame runs in its own process (an out-of-process iframe): attach to it as a target."""
    def __init__(self, b, session):
        self.b, self.session = b, session

    async def call(self, method, **params):
        return await self.b.call(method, self.session, **params)


async def frame_ctx(tab):
    await tab.call("Target.setAutoAttach", autoAttach=True, waitForDebuggerOnStart=False, flatten=True)
    for t in (await tab.b.call("Target.getTargets"))["targetInfos"]:
        if t["type"] == "iframe":
            session = (await tab.b.call("Target.attachToTarget", targetId=t["targetId"], flatten=True))["sessionId"]
            return FrameTab(tab.b, session)
    return None


async def fjs(tab, ctx, expr):
    r = await ctx.call("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=True)
    if r.get("exceptionDetails"):
        return {"error": r["exceptionDetails"].get("text"), "detail": str(r["exceptionDetails"].get("exception", {}).get("description", ""))[:300]}
    return r.get("result", {}).get("value")


STATE = """(() => ({sw: document.documentElement.scrollWidth, iw: innerWidth,
  text: document.body.innerText.slice(0, 600),
  buttons: [...document.querySelectorAll('button,a,[role=button],summary')].map(b => (b.innerText||b.getAttribute('aria-label')||'').trim()).filter(Boolean).slice(0, 60),
  wide: [...document.querySelectorAll('body *')].filter(e => e.getBoundingClientRect().right > innerWidth + 1).slice(0, 8).map(e => e.tagName + '.' + String(e.className).slice(0, 40))}))()"""


def press(label):
    return f"""(() => {{ const want = {json.dumps(label)};
  const all = [...document.querySelectorAll('button,a,[role=button],summary,li,[tabindex]')];
  const hit = all.find(b => (b.innerText||'').trim() === want) || all.find(b => (b.innerText||'').trim().startsWith(want));
  if (!hit) return 'missing ' + want; hit.scrollIntoView({{block: 'center'}}); hit.click(); return 'pressed ' + want; }})()"""


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cookies", required=True)
    ap.add_argument("--name", default="Test (Claude)")
    ap.add_argument("--steps", default="Announcements,Calendar,Map")
    ap.add_argument("--prefix", default="", help="screenshot name prefix, e.g. visitor-")
    ap.add_argument("--js", default="", help="extra JS to run in the frame after the steps")
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    b = await Browser().start()
    report = {}
    try:
        tab = await b.person("guest", "198.51.100.12")
        ck = Path(a.cookies)
        if a.cookies == "none":
            pass                                    # a signed-out visitor
        elif ck.exists():
            for c in json.loads(ck.read_text(encoding="utf-8")):
                await tab.call("Network.setCookie", **{k: c[k] for k in ("name", "value", "domain", "path", "secure", "httpOnly") if k in c})
        else:
            await tab.goto(BASE + "/meeting")
            await tab.type("#name", a.name)
            await tab.click("button.primary")
            await asyncio.sleep(2)
            cookies = (await tab.call("Network.getCookies", urls=[BASE]))["cookies"]
            ck.write_text(json.dumps(cookies), encoding="utf-8")
        await tab.goto(BASE + "/board")
        for _ in range(30):
            await asyncio.sleep(1)
            ctx = await frame_ctx(tab)
            if ctx:
                break
        report["page"] = await tab.js("({url: location.href, body: document.body.innerText.slice(0, 300)})")
        if not ctx:
            print(json.dumps(report, indent=1))
            await tab.shot(OUT / f"mobile-{a.prefix}00-board.png")
            return
        await asyncio.sleep(5)
        report["start"] = await fjs(tab, ctx, STATE) if ctx else "no frame"
        await tab.shot(OUT / f"mobile-{a.prefix}00-board.png")
        for i, step in enumerate(s for s in a.steps.split(",") if s):
            report[step] = {"press": await fjs(tab, ctx, press(step))}
            await asyncio.sleep(10 if step == "Map" else 4)
            ctx = await frame_ctx(tab) or ctx
            report[step]["state"] = await fjs(tab, ctx, STATE)
            await tab.shot(OUT / f"mobile-{a.prefix}{i + 1:02d}-{step.lower().replace(' ', '-')}.png")
        if a.js:
            report["js"] = await fjs(tab, ctx, a.js)
            await asyncio.sleep(4)
            await tab.shot(OUT / "mobile-js.png")
    finally:
        await b.close()
    print(json.dumps(report, indent=1)[:6000])


asyncio.run(main())
