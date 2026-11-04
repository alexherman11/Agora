"""EDITING THE DESKTOP HOST (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
This file is a seam between the world and Windows: it turns world facts into screen effects and screen events into world
facts, through small words. It holds no preferences and no content. Which apps, what a button opens, sizes, names, ids and
who may do what live in settings things it reads (shell-settings, wm-settings). It does not seed the world at start
(people, chats, pins). New behaviour is a rule over the words offered here. Before writing a Windows or browser helper,
use the shared one (gaming_gate for full-screen and desktop tests, widget_browser for hidden pages) instead of a copy.

Locally vendored Lucide 0.468.0 (ISC), shared by lenses and host chrome."""
from functools import lru_cache
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent / 'pages' / 'icons'
NAMES = {'cpu': 'cpu', 'memory': 'memory-stick', 'network': 'wifi', 'volume': 'volume-2',
         'battery': 'battery', 'media': 'music-2', 'next': 'skip-forward', 'feed': 'rss',
         'apps': 'layout-grid', 'focused': 'app-window', 'time': 'calendar-days',
         'help': 'circle-help', 'wave': 'hand', 'lines': 'terminal', 'thing': 'pin'}


@lru_cache(maxsize=128)
def svg(name):
    name = NAMES.get(name, name)
    if not re.fullmatch(r'[a-z0-9-]+', name) or not (ROOT / f'{name}.svg').is_file():
        name = 'app-window'
    source = (ROOT / f'{name}.svg').read_text(encoding='utf-8').replace('\n', ' ')
    # The generic picture role sets fill on its SVG root. An explicit inner
    # group preserves Lucide's outlined shapes without touching the painter.
    head, body = source.split('>', 1)
    return head + '><g fill="none">' + body.replace('</svg>', '</g></svg>')
