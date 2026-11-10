"""A hidden phone (390x844, headless Edge) walking the public Seabright site: the website, /meeting -> guest name ->
the board, and the signed-out board. Screenshots and a short report go to deploy/evidence/. Nothing shows on screen.

    C:/Projects/Agora4/.venv/Scripts/python.exe research/community-app/deploy/phone_check.py [--name "Test (Claude)"]

It makes one real guest account in the live world, with the name given. Claude, 5 Nov 2026.
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

FRAME_STATE = """(() => {
  const f = document.querySelector('#widget-surface iframe');
  const receipt = document.querySelector('#receipt');
  return {url: location.pathname + location.search, frame: !!f, stopped: document.querySelector('#widget-surface')?.dataset.stopped || '',
          receipt: receipt ? receipt.textContent : '', body: document.body.innerText.slice(0, 400),
          sw: document.documentElement.scrollWidth, iw: innerWidth};
})()"""


async def wait_frame(tab, seconds=25):
    st = None
    for _ in range(seconds * 2):
        st = await tab.js(FRAME_STATE)
        if st and (st["frame"] or st["stopped"]):
            break
        await asyncio.sleep(.5)
    await asyncio.sleep(6)                      # let the painter paint inside the frame
    return await tab.js(FRAME_STATE)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="Test (Claude)")
    ap.add_argument("--skip-guest", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    report = {}
    b = await Browser().start()
    try:
        visitor = await b.person("visitor", "198.51.100.10")
        await visitor.goto(BASE + "/")
        await visitor.shot(OUT / "phone-01-website.png")
        report["website"] = await visitor.js("({title: document.title, sw: document.documentElement.scrollWidth, iw: innerWidth})")
        await visitor.goto(BASE + "/board")
        report["board_signed_out"] = await wait_frame(visitor)
        await visitor.shot(OUT / "phone-02-board-signed-out.png")

        if not a.skip_guest:
            guest = await b.person("guest", "198.51.100.11")
            await guest.goto(BASE + "/meeting")
            report["meeting"] = await guest.url()
            await guest.shot(OUT / "phone-03-guest-name.png")
            await guest.type("#name", a.name)
            await guest.click("button.primary")
            await asyncio.sleep(2)
            report["after_join"] = await guest.url()
            if "/desk/widget.html" not in report["after_join"]:
                await guest.goto(BASE + "/board")
            report["board_guest"] = await wait_frame(guest)
            await guest.shot(OUT / "phone-04-board-guest.png")
    finally:
        await b.close()
    (OUT / "phone-report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps(report, indent=1))


asyncio.run(main())
