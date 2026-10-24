"""Gated native acceptance capture. Only the three requested demo windows focus.
No clicks, typing, reload, scroll changes or task edits.
"""
import ctypes
import json
from pathlib import Path
import sys
import time

from install import taskboard
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'window-lab/kernel-desktop'))
from gaming_gate import assert_clear
from PIL import ImageGrab

assert_clear()
ctypes.WinDLL('user32').SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
d=taskboard.live_door()
for view in (() if '--read-only' in sys.argv else ('taskboard','taskboard-js','guy-editor')):
    assert_clear()
    rows=d.say('window.list')['rows']
    window=next(w for w in rows if w.get('shows')==view and w.get('shown'))
    if not window.get('front'):d.say('window.focus '+window['id'])
if '--read-only' not in sys.argv:
    assert_clear();d.say('guy.hop');d.say('guy.say "A little room to think."')
    time.sleep(1.4)
    assert_clear()
    ImageGrab.grab(bbox=(0,0,3840,2160)).save(HERE/'evidence/live-desktop.png')
    ImageGrab.grab(bbox=(0,0,3840,80)).save(HERE/'evidence/live-bar.png')
widgets=d.rows('widget')
holds=d.say('holds')['rows']
report=dict(tasks=len(d.rows('taskboard-task')),windows=[w for w in d.say('window.list')['rows']
    if w.get('shows') in ('taskboard','taskboard-js','guy-editor')],holds=holds,
    descriptions={w['name']:d.say('look '+w['id'])['rows'][0].get('description') for w in widgets if w.get('code')})
(HERE/'evidence/live.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(('LIVE READ: ' if '--read-only' in sys.argv else 'LIVE NATIVE: ')+str(report['tasks'])+' shared tasks; demo windows and holds recorded')
print('LIVE HOLDS: '+', '.join(h['by']+' → '+h['word'] for h in holds))
