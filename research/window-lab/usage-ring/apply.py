"""Apply Alex's quota-ring presentation through the Desk gateway, preserving unrelated prose.

Use a forked world for painter checks first; live edits re-read each shared note.
Backups retain exact prior text in ignored local storage. No source service restart.
"""
import argparse
import json
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def apply(world):
    def act(line):
        body = json.dumps({'session': world, 'as': 'codex', 'line': line, 'whole': True}).encode()
        request = urllib.request.Request('http://127.0.0.1:8794/api/do', body,
                                         {'Content-Type': 'application/json'})
        with urllib.request.urlopen(request, timeout=120) as response:
            result = json.load(response)
        text = result.get('text') or ''
        detail = text or str(result.get('error') or '')
        if line.startswith('do prop ') and detail.startswith(line.split()[2] + ' already has '):
            return detail
        if result.get('error') or any(x.startswith(('ERR ', 'MISS ', 'stopped')) for x in text.splitlines()):
            raise RuntimeError(result.get('error') or text)
        return text

    backup = ROOT / 'local' / 'usage-ring' / f'{world}-{time.time_ns()}.json'
    backup.parent.mkdir(parents=True, exist_ok=True)
    saved = {}

    def read(target):
        text = act(f'read {target} :3').split('\n---\n', 1)[1].rsplit('\n---', 1)[0]
        saved[target] = text
        backup.write_text(json.dumps(saved, ensure_ascii=False, indent=2), encoding='utf-8')
        return text

    q = lambda text: json.dumps(text, ensure_ascii=False)
    roles = (HERE / 'roles.style').read_text(encoding='utf-8').strip()
    style = read('a5206')
    if 'role uring :' not in style:
        print(act('do append a5206 line=' + q(roles)))
    plan_style = read('a6769')
    if 'role uring :' not in plan_style:
        print(act('do append a6769 line=' + q('token warm = #B85C00\ntoken accent = #0B8F6E\ntoken wash = ink at 5%\n' + roles)))
    print(act('do prop a6771 style=plan-usage-style slot=footer'))
    ring = (HERE / 'home-usage.lens').read_text(encoding='utf-8').rstrip()
    if read('a6771').rstrip() != ring:
        print(act('do rewrite a6771 text=' + q(ring)))
    print(act('do tag a6771 remove=widget'))
    # Remove only the usage insertion, leaving the current status/clock layout intact.
    glance = read('a6348')
    old = '  usage : column\n   lens plan-usage-glance\n'
    if old in glance:
        print(act('do replace a6348 old=' + q(old) + ' new=""'))
    elif 'lens plan-usage-glance' in glance:
        raise RuntimeError('Glance insertion moved; read it before editing')
    chat = read('a5210')
    old = ('    help : text "Enter sends · Shift+Enter for a new line · @name to send to someone else · '
           'Ctrl+Alt drag to show JEFF something"\n      role hint\n      only when held = ""\n')
    new = ('    footer : row\n      role urfooter\n      only when held = ""\n'
           '      help : text "Enter sends · Shift+Enter for a new line · @name to send to someone else · '
           'Ctrl+Alt drag to show JEFF something"\n        role hint\n        share 1\n'
           '      quota : row\n        lens home-usage\n')
    if new not in chat:
        if chat.count(old) != 1:
            raise RuntimeError('Composer help moved; read it before editing')
        print(act('do replace a5210 old=' + q(old) + ' new=' + q(new)))
    for lens in ('home-usage', 'jeff-chat', 'home-base'):
        result = act(f'scene {lens} ok')
        if 'does not compile' in result:
            raise RuntimeError(result)
        print(result)
    print('Exact prior text: ' + str(backup))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('world')
    apply(parser.parse_args().world)
