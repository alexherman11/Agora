"""Install versioned widget code through ordinary lines; no source paths in world definitions.

Live use is gated by gaming_gate.py. Import install(door) for a scratch kernel.
"""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location('taskboard_install', HERE.parent / 'apps/taskboard/install.py')
taskboard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(taskboard)
quote = taskboard.quote

SPECS = [
    ('taskboard-js', 'Task board · JavaScript', 'taskboard', 'window',
     'window.surface describe rows look history task-add task-move task-assign task-done task-note task-priority '
     'task-colour task-note-colour task-note-style task-filter task-rename task-remove summarize.* make set forget undo '
     'hear:make hear:set hear:forget hear:undo', 'kind:taskboard-task,taskboard-settings'),
    ('desktop-guy', 'Desktop companion', 'guy', 'overlay',
     'window.overlay describe rows window.list hear:guy.say hear:guy.hop hear:window.opened hear:set hear:undo', ''),
    ('guy-editor', 'Guy studio', 'guy-editor', 'window',
     'window.surface describe rows look set guy.say guy.hop hear:set hear:undo', 'kind:guy-profile'),
    ('now-playing', 'Now playing', 'now-playing', 'top',
     'window.bar describe media.now media.play media.next', ''),
]


def code(view):
    files = ['common.js'] + (['guy-art.js'] if view in ('guy', 'guy-editor') else []) + [view+'.js']
    return '\n\n'.join((HERE / f).read_text(encoding='utf-8') for f in files)


def install(door):
    if not door.rows('guy-profile'):
        door.say('make kind=guy-profile name=Moss body="#9EBDA7" face="#F3DEC0" accent="#D9A689" '
                 'speed=75 mood=curious phrases="A little room to think.\nOne good thing at a time.\nShall we take a small step?"')
    result = {}
    for name, title, view, surface, grants, only in SPECS:
        existing = door.rows('widget', name=name)
        source = code(view)
        if not existing:
            out = door.say('make kind=widget name='+name+' title='+quote(title)+' style=bars code='+quote(source))
            mid = out['made'][0]
        else:
            mid = existing[0]['id']
            if existing[0].get('code') != source:
                door.say('look '+mid)
                door.say('set '+mid+' code='+quote(source))
        live_grants = door.rows('grant', to=mid)
        matching = any(g.get('words') == grants and not g.get('revoked') and g.get('only', '') == only for g in live_grants)
        current = door.rows('widget', name=name)[0]
        if not matching or not current.get('on') or current.get('surface') != surface:
            door.say('look '+mid)
            door.say(f'widget {mid} surface={surface} grants='+quote(grants)+((' only='+only) if only else ''))
        result[name] = mid
    return result


def open_windows(door):
    door.say('window.open taskboard-js to=right')
    door.say('window.open guy-editor at=40,160 size=680,1120')


def main():
    import sys
    sys.path.insert(0,str(ROOT/'research/window-lab/kernel-desktop'))
    from gaming_gate import assert_clear
    assert_clear()
    d = taskboard.live_door()
    print('Installed widget definitions:', ', '.join(install(d)))
    open_windows(d)


if __name__ == '__main__':
    main()
