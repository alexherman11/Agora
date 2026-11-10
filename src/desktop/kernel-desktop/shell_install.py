"""EDITING THE DESKTOP HOST (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
This file is a seam between the world and Windows: it turns world facts into screen effects and screen events into world
facts, through small words. It holds no preferences and no content. Which apps, what a button opens, sizes, names, ids and
who may do what live in settings things it reads (shell-settings, wm-settings). It does not seed the world at start
(people, chats, pins). New behaviour is a rule over the words offered here. Before writing a Windows or browser helper,
use the shared one (gaming_gate for full-screen and desktop tests, widget_browser for hidden pages) instead of a copy.

shell_install: the bars as components (SHELL.md, "The bars as components"), installed through ordinary door words.

    install(door)                       a scratch world (tests): components, the two lenses, the two widgets
    python shell_install.py --live      Alex's desktop (127.0.0.1:8810), for Claude to run: say what will change first

Idempotent: a second run says nothing. Components (their code and cards) are the builder's: a changed file is written
and reviewed again. The lenses are Alex's and the agents' once they exist: an existing shell-top or shell-dock lens is
kept as it is (its arrangement may have been changed on purpose); --reset-lenses writes the shipped arrangement back.
The widgets get the shell's grants, including window.native (stewards only). Nothing restarts and no window opens:
the shell windows pick the widgets up the next time their pages load (restart the window host, or window.shell off/on).
Off switch: `off <shell-top widget>` / `off <shell-dock widget>` puts the hand-written bars back on the next page load.
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1] / 'agora'
sys.path[:0] = [str(LAB), str(HERE)]
from painter.install import widget_source  # noqa: E402
from shell_parts import cards as C  # noqa: E402

_spec = importlib.util.spec_from_file_location('shell_taskboard_install', LAB / 'apps/taskboard/install.py')
_tb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tb)
Q = _tb.quote

LENSES = {'shell-top': 'Agora top bar', 'shell-dock': 'Agora dock'}
# What the bars say. make/set/forget reach only shell-settings, kept buttons and ask requests (only=); window.native is
# the narrow bridge to the bar's own window (window.native in kd_window.py).
GRANTS = ('window.surface window.native rows look look-view help components component-health component-action ask '
          'wm.windows wm.focus wm.minimise wm.restore wm.arrange wm.close wm.pin wm.unpin wm.leave-alone wm.manage wm.mode wm.space wm.title '
          'window.list window.desktop window.activate window.launch window.open window.start window.settings window.focus window.close '
          'system.now media.now media.play media.next media.prev notice.clear make set forget off '
          'hear:make hear:set hear:forget hear:undo hear:component hear:component-action')
ONLY = 'kind:shell-settings,button,ask-request'
LENS_FACTS = dict(painter='components', right_click='ask', reconcile_ms='5000')


def shell_code():
    """The painter for a bar: its core, the shell's vocabulary (ShellKit, with the bar's stylesheet: pages/shell/shell.css
    then shell-kit.css) and painter.js; not the task board's stylesheet."""
    css = (HERE / 'pages/shell/shell.css').read_text(encoding='utf-8') + '\n' + (HERE / 'shell_parts/shell-kit.css').read_text(encoding='utf-8')
    kit = 'const SHELL_CSS = ' + json.dumps(css) + ';\n' + (HERE / 'shell_parts/shell-kit.js').read_text(encoding='utf-8')
    return widget_source(vocabulary=[kit], board_look=False)


def upsert(door, kind, name, keep_text=False, **facts):
    old = door.rows(kind, name=name)
    if not old:
        return door.say('make kind=' + kind + ' name=' + name + ''.join(' ' + k + '=' + Q(v) for k, v in facts.items()))['made'][0]
    t = old[0]['id']
    changes = {k: v for k, v in facts.items() if str(old[0].get(k, '')) != str(v) and not (keep_text and k == 'text')}
    if changes:
        door.say('look ' + t)
        door.say('set ' + t + ''.join(' ' + k + '=' + Q(v) for k, v in changes.items()))
    return t


def install(door, reset_lenses=False, say=print):
    ids = {}
    for card in C.cards():
        name = card.pop('name')
        code = C.code(name)
        t = upsert(door, 'component', name, **card, code=code)
        current = door.rows('component', name=name)[0]
        if current.get('reviewed_code') != hashlib.sha256(code.encode()).hexdigest():
            door.say('look ' + t)
            door.say('component ' + t)
        ids[name] = t
    for name, title in LENSES.items():
        text = (HERE / 'shell_parts' / f'{name}.lens').read_text(encoding='utf-8')
        existing = door.rows('lens', name=name)
        if existing and not reset_lenses and existing[0].get('text') != text:
            say(f'kept the {title} arrangement as it is (changed since it was shipped); --reset-lenses writes it back')
        ids[name] = upsert(door, 'lens', name, keep_text=not reset_lenses, title=title, text=text, **LENS_FACTS)
        ids[name + ' widget'] = activate(door, name, title)
    return ids


def activate(door, name, title):
    mid = upsert(door, 'widget', name, title=title, style='bars', component_lens=name, receipts='quiet', code=shell_code())
    current = door.rows('widget', name=name)[0]
    matching = any(g.get('words') == GRANTS and g.get('only') == ONLY and not g.get('revoked') for g in door.rows('grant', to=mid))
    if not current.get('on') or not matching:
        door.say('look ' + mid)
        door.say('widget ' + mid + ' surface=window grants=' + Q(GRANTS) + ' only=' + ONLY)
    return mid


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--live', action='store_true')
    ap.add_argument('--reset-lenses', action='store_true')
    args = ap.parse_args()
    if not args.live:
        ap.error('use install(door) for a scratch world, or explicitly --live')
    from gaming_gate import assert_clear
    assert_clear()
    door = _tb.live_door()
    for word in ('help window.native', 'help paint-clear'):
        if not door.request('/see', {'line': word}).get('ok'):
            raise SystemExit(f'{word.split()[1]} is not here yet: restart kdesk (the kernel and the window host) with this '
                             'code first. Nothing was installed.')
    before = len(door.request('/see', {'line': 'rows component'}).get('rows', []))
    ids = install(door, reset_lenses=args.reset_lenses)
    print('Installed the shell parts:', ', '.join(f'{k} {v}' for k, v in ids.items()))
    print(f'components before: {before}; nothing restarted; the bars change when their pages next load.')


if __name__ == '__main__':
    main()
