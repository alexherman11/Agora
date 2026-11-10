"""Open the Writing window in a hidden browser over a door (a sandbox), and take pictures. Nothing shows on the screen.

    python look.py [--door http://127.0.0.1:8831] [--out evidence] [--who alex]
The browser is headless (painter.browser.Page over widget_browser), signed in with an existing desktop session.
"""
import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
ROOT = LAB.parents[1]
sys.path[:0] = [str(HERE), str(LAB)]
import painter.browser as pb  # noqa: E402
from install import claude_door  # noqa: E402


def token(who):
    sessions = json.loads((ROOT / 'src/desktop/kernel-desktop/state/world/keep/sessions.json').read_text(encoding='utf-8'))
    return [t for t, v in sessions.items() if v.get('signer') == who][0]


def open_writing(url, who='alex', width=1440, height=900):
    door = claude_door(url)
    widget = door.rows('widget', name='writing')[0]['id']
    page = pb.Page(url, token(who), widget, width, height)
    page.until('!!document.querySelector(".wr-shell")', 40)
    page.js('new Promise(r=>setTimeout(r,500))')
    return page


def errors(page):
    """Script errors in the window. The headless harness blocks the page's live stream (ERR_BLOCKED_BY_CLIENT, so the
    window polls instead); those network lines are the harness, not the page."""
    def harness(e):
        entry = e.get('params', {}).get('entry', {})
        return entry.get('source') == 'network' and 'ERR_BLOCKED_BY_CLIENT' in entry.get('text', '')
    return [e for e in page.errors if (e.get('method') == 'Runtime.exceptionThrown'
            or e.get('params', {}).get('entry', {}).get('level') == 'error') and not harness(e)]


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--door', default='http://127.0.0.1:8831')
    ap.add_argument('--out', default=str(HERE / 'evidence'))
    ap.add_argument('--who', default='alex')
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    page = open_writing(a.door, a.who)
    print('window ready in', round(time.time() - t0, 1), 's')
    page.shot(str(out / 'look-home.png'))
    print(json.dumps(errors(page))[:3000])
    page.close()
