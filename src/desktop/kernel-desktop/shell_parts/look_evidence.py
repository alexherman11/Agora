"""look_evidence: the component bars beside the hand-written ones, same world, same data, hidden and headless.

    C:/Projects/Agora4/.venv/Scripts/python.exe shell_parts/look_evidence.py      (from kernel-desktop)

Writes evidence/shell/components-{top,dock}-{components,hand}.png and a few popovers, and prints how many pixels differ
between the two renders of each bar. Nothing appears on the screen; nothing touches the live desktop.
"""
import base64
import io
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(HERE), str(HERE.parents[1] / 'agora')]
import test_shell_components as T  # noqa: E402

OUT = HERE / 'evidence' / 'shell'


def shot(page, name):
    data = base64.b64decode(page.c.call('Page.captureScreenshot', format='png')['data'])
    (OUT / name).write_bytes(data)
    return data


def diff(a, b):
    from PIL import Image, ImageChops
    x, y = Image.open(io.BytesIO(a)).convert('RGB'), Image.open(io.BytesIO(b)).convert('RGB')
    d = ImageChops.difference(x, y)
    px = sum(1 for p in d.getdata() if max(p) > 8)
    return px, d.getbbox(), x.size[0] * x.size[1]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    T.ShellComponents.setUpClass()
    c = T.ShellComponents
    pages = []
    try:
        for which, page, (w, h) in (('top', c.top, (1600, 560)), ('dock', c.dock, (1560, 460))):
            time.sleep(2.5)
            comp = shot(page, f'components-{which}-components.png')
            hand = T.ShellPage(c.d.url, c.d.entry.token('alex'), which, c.key, w, h)
            pages.append(hand)
            hand.c.call('Page.navigate', url=c.d.url + f'/desk/shell/{which}.html?hand=1')
            hand.c.until('!!document.querySelector(".rail .btn.clock .t, .pill .item")', 20)
            time.sleep(2.5)
            hb = shot(hand, f'components-{which}-hand.png')
            px, box, total = diff(comp, hb)
            print(f'{which}: {px} of {total} pixels differ by more than 8 levels, inside {box}', flush=True)
        # popovers, components only
        top = c.top
        for sel, name in (('.btn.clock', 'calendar'), ('.btn.qs', 'quick'), ('.btn.mark', 'launcher')):
            top.mouse(sel)
            top.until('!!document.querySelector(".pop.in")', 10)
            time.sleep(.5)
            shot(top, f'components-top-pop-{name}.png')
            top.c.call('Input.dispatchKeyEvent', type='keyDown', key='Escape', code='Escape', windowsVirtualKeyCode=27)
            top.until('!document.querySelector(".pop.in")', 10)
        top.mouse('.btn.clock .t', 'right')
        top.until('!!document.querySelector(".ask-menu")', 10)
        time.sleep(.3)
        shot(top, 'components-top-ask.png')
        c.dock.mouse('.pill .item[data-fact-app="notepad"]', 'right')
        c.dock.until('!!document.querySelector(".pop.in .menu")', 10)
        time.sleep(.5)
        shot(c.dock, 'components-dock-menu.png')
    finally:
        for p in pages:
            p.close()
        T.ShellComponents.tearDownClass()


if __name__ == '__main__':
    main()
