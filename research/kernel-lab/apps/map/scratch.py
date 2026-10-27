"""A hidden scratch desktop world with the map installed: for trying lines and for the browser checks.

    python scratch.py            installs, runs a few lines, prints what came back, and closes
    from scratch import Scratch  Scratch() -> .door (Alex), .say(line, who), .url, .token(who), .ids, .close()
Nothing appears on the screen: the kernel desktop starts headless (no windows), in a temporary folder.
"""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
sys.path[:0] = [str(HERE), str(LAB), str(LAB.parent / 'window-lab/kernel-desktop')]
from test_kdesk import Desk  # noqa: E402
from install import install, taskboard  # noqa: E402


class Scratch:
    def __init__(self):
        t0 = time.time()
        self.d = Desk()
        self.url = self.d.url
        self.door = taskboard.Door(self.url, self.d.entry.token('alex'))
        self.ids = install(self.door)
        self.started = round(time.time() - t0, 1)

    def token(self, who='alex'):
        return self.d.entry.token(who)

    def say(self, line, who='alex'):
        route = '/see' if line.split()[0] in ('rows', 'look', 'help', 'map.find', 'map.where', 'map.near', 'map.path',
                                               'map.layers', 'look-view') else '/do'
        return taskboard.Door(self.url, self.token(who)).request(route, {'line': line})

    def close(self):
        self.d.close()


def serve(door_file, stop_file):
    """Keep a scratch world up for someone working only in lines (say.py), until stop_file appears."""
    s = Scratch()
    try:
        say = s.say
        say('make kind=kind name=event fields="start end location place seats"')
        say('make kind=spot map=Seabright name="Tide pools" lat=36.9630 lon=-122.0040 text="Low tide only"')
        say('make kind=event title="Beach cleanup" start=2026-10-31T09:00 location="Seabright Beach"')
        say('make kind=event title="Council night" start=2026-10-30T18:30 location="Museum of Natural History"')
        Path(door_file).write_text(json.dumps({'url': s.url, 'token': s.token('claude'), 'alex': s.token('alex'),
                                               'widget': s.ids['widget']}), encoding='utf-8')
        print('serving', s.url, flush=True)
        while not Path(stop_file).exists():
            time.sleep(1)
    finally:
        s.close()


if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == 'serve':
    serve(sys.argv[2], sys.argv[3])
    sys.exit(0)

if __name__ == '__main__':
    s = Scratch()
    try:
        print('started and installed in', s.started, 's', json.dumps(s.ids))
        for line in ['map.find Seabright & Murray', 'map.find java junction',
                     'make kind=spot map=Seabright name="Tide pools" lat=36.9630 lon=-122.0040',
                     'map.where "Tide pools"', 'map.near "Java Junction" within=400',
                     'map.route name="Flyers: Murray to the beach" stops="Seabright Station > Java Junction > Seabright Beach"',
                     'map.layers Seabright', 'map.hide Events', 'map.layers Seabright', 'map.show "Tide pools"']:
            out = s.say(line)
            print('\n>', line, '\n', out.get('ok'), (out.get('text') or out.get('error') or '')[:600])
            if line.startswith('map.layers'):
                print(json.dumps(out.get('rows'), indent=0)[:1500])
    finally:
        s.close()
