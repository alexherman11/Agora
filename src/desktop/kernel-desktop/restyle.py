"""Install v2 lens/style definitions through the ordinary door, undoably.

No boot-time rewriting: the world's copies remain authoritative afterwards.
"""
import argparse
import json
from pathlib import Path
from kd_say import say

HERE = Path(__file__).resolve().parent


def install(token, port=8810):
    results = []
    def line(text):
        out = say(text, token, port)
        if not out.get('ok'):
            raise RuntimeError(out.get('text'))
        results.append(out['text'])
        return out
    for kind, name, filename, extra in (
        ('style', 'bars', 'bars.style', ''), ('style', 'tiles', 'tiles.style', ''),
        ('lens', 'topbar', 'topbar.lens', ' style=bars'), ('lens', 'feed', 'feed.lens', ' style=tiles')):
        rows = line(f'rows {kind} name={name}').get('rows') or []
        text = (HERE / 'lenses' / filename).read_text(encoding='utf-8')
        source = '"' + text.replace('\\', '\\\\').replace('"', '\\"') + '"'
        if rows:
            line(f"look {rows[0]['id']}")
            line(f"set {rows[0]['id']} text={source}{extra}")
        else:
            line(f'make kind={kind} name={name} text={source}{extra}')
    # The feed on the dock and in the launcher (shell-kit.js reads `rows app`, 4 Nov): made once, never overwritten.
    if not (line('rows app name=feed').get('rows') or []):
        line('make kind=app name=feed label=Feed does="window.open feed"')
    # Shell controls are ordinary world things too. Install only absent slots;
    # changes/removals afterwards are the world's, never enforced at boot.
    defaults = [
        ('start', 'kind=button label="Windows Start" icon=panels-top-left does="window.start"'),
        ('agora', 'kind=button label="Agora · Lines" icon=terminal does="window.open lines"'),
        ('network', 'kind=widget side=right shows=network icon=wifi does="window.settings which=network" order=10'),
        ('volume', 'kind=widget side=right shows=volume icon=volume-2 does="window.settings which=volume" order=20'),
        ('battery', 'kind=widget side=right shows=battery icon=battery does="window.settings which=battery" order=30'),
        ('clock', 'kind=widget shows=time does="window.settings which=time"'),
        ('off', 'kind=button label="Turn Agora windows off" icon=power confirm=yes does="off window"'),
        ('holds', 'kind=widget shows=holds icon=hand'),
    ]
    for slot, words in defaults:
        if not line(f'rows any bar=taskbar slot={slot}').get('rows'):
            line(f'make {words} bar=taskbar slot={slot}')
    return results


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--world', type=Path, default=HERE / 'state' / 'world')
    ap.add_argument('--port', type=int, default=8810)
    a = ap.parse_args()
    sessions = json.loads((a.world / 'keep' / 'sessions.json').read_text(encoding='utf-8'))
    token = next(t for t, v in sessions.items() if v.get('signer') == 'claude')
    for result in install(token, a.port):
        print(result)
