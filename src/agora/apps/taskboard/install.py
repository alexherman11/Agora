"""Install a word-only Task board through the door; no kernel imports or source changes.

Default: seed from frontier, install on 8810 as Alex, then window.open.
Re-running checks definitions and stable source keys, leaving existing work untouched.
"""
import argparse
import json
import re
import shlex
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def quote(s):
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"') + '"'


class Door:
    def __init__(self, url, token):
        self.url, self.token = url.rstrip('/'), token

    def request(self, path, body=None):
        for attempt in range(25):
            req = urllib.request.Request(self.url + path,
                None if body is None else json.dumps(body).encode(),
                {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + self.token})
            try:
                with urllib.request.urlopen(req, timeout=45) as response:
                    return json.load(response)
            except (urllib.error.URLError, ConnectionError, TimeoutError):
                if attempt == 24:
                    raise
                time.sleep(2)

    def say(self, line, **extra):
        out = self.request('/do', dict(line=line, **extra))
        if not out.get('ok'):
            raise RuntimeError(out)
        return out

    def rows(self, kind, **facts):
        return self.say('rows ' + kind + ''.join(' ' + k + '=' + quote(v) for k, v in facts.items()))['rows']


def live_door():
    keep = ROOT / 'src/desktop/kernel-desktop/state/world/keep'
    # Current desktop uses sessions.json with signer, older dev-entry uses dev-sessions.json.
    for name in ('sessions.json', 'dev-sessions.json'):
        path = keep / name
        if not path.exists():
            continue
        sessions = json.loads(path.read_text(encoding='utf-8'))
        matches = [t for t, v in sessions.items() if v.get('signer') == 'alex']
        if not matches:
            matches = [t for t, v in sessions.items() if not v.get('agent') and 'alex' in v.get('account', '').lower()]
        if len(matches) == 1:
            return Door('http://127.0.0.1:8810', matches[0])
    raise RuntimeError('No unambiguous existing Alex desktop session; no session files changed')


def declarations():
    text = '\n'.join(x for x in HERE.joinpath('install.lines').read_text(encoding='utf-8').splitlines()
                     if not x.lstrip().startswith('#'))
    quote_char = None
    escaped = False
    current = ''
    for ch in text:
        if quote_char:
            current += ch
            if escaped:
                escaped = False
            elif ch == '\\':
                escaped = True
            elif ch == quote_char:
                quote_char = None
        elif ch in ('"', "'"):
            quote_char = ch
            current += ch
        elif ch == '\n':
            if current.strip():
                yield current.strip()
            current = ''
        else:
            current += ch
    if current.strip():
        yield current.strip()


def install(door):
    made = skipped = 0
    for line in declarations():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        # Every declaration is a literal, directly speakable line. Each has a stable name.
        words = shlex.split(line)
        if words[0] == 'verb':
            bound = words[1]
            existing = door.rows('word', bound=bound)
            if existing:
                skipped += 1
                continue
        else:
            facts = dict(w.split('=', 1) for w in words[1:] if '=' in w)
            if facts['kind'] == 'lens' and not door.rows('lens', name='taskboard'):
                previous = door.rows('lens', name='Task board')
                if previous and previous[0].get('style') == 'taskboard':
                    door.say('set ' + previous[0]['id'] + ' name=taskboard')
                    made += 1
                    continue
            existing = door.rows(facts['kind'], name=facts['name'])
            if existing:
                # Upgrade only authored definitions. Settings and existing tasks
                # are world data; never reset them on a later install.
                updates = {k: v for k, v in facts.items() if k not in ('kind', 'name')
                           and str(existing[0].get(k, '')) != v}
                if facts['kind'] not in ('lens', 'style', 'rule') or not updates:
                    skipped += 1
                    continue
                door.say('look ' + existing[0]['id'])
                door.say('set ' + existing[0]['id'] + ' ' + ' '.join(k+'='+quote(v) for k,v in updates.items()))
                made += 1
                continue
        # A stable press makes a lost response safe to retry, including across a restart.
        import hashlib
        door.say(line, press='taskboard-install-' + hashlib.sha256(line.encode()).hexdigest())
        made += 1
    return made, skipped


def migrate(door):
    """Add missing v2 facts, never recreate a card or rewrite a previous fact."""
    changed = 0
    for task in door.rows('taskboard-task'):
        defaults = dict(priority='4', colour='paper', note_colour='paper', note_style='normal', note='')
        missing = {k: v for k, v in defaults.items() if k not in task}
        # Empty values remove facts, so absent empty notes stay absent.
        missing = {k:v for k,v in missing.items() if v}
        if missing:
            door.say('look ' + task['id'])
            door.say('set ' + task['id'] + ' ' + ' '.join(k+'='+quote(v) for k,v in missing.items()))
            changed += 1
        if not task.get('short'):
            door.say('summarize.task ' + task['id'])
    return changed


def frontier(line):
    req = urllib.request.Request('http://127.0.0.1:8794/api/do',
        json.dumps({'session': 'frontier', 'as': 'codex', 'line': line}).encode(),
        {'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=40) as r:
        out = json.load(r)
    if out.get('error'):
        raise RuntimeError(out['error'])
    return out['text']


def seed(door):
    listing = frontier('find tag:communities')
    epic = frontier('read a13308 :3')
    ideas = frontier('read a13437 :3')
    sources = []
    for m in re.finditer(r'(a\d+) task "([^"]+)" · status=(\S+) level=story[^\n]*', listing):
        source, title, status = m.groups()
        if status in ('done', 'closed') or source not in epic:
            continue
        full = frontier('read ' + source + ' :3')
        owner = re.search(r'owner=(\S+)', m[0])
        sources.append(dict(source=source, title=title.removeprefix('STORY · '),
            lane='Now' if status in ('doing', 'active') else 'Backlog',
            who=owner[1] if owner else 'Alex', status=status, text=full.split('---')[1].strip()))
    for m in re.finditer(r'^  (c\d+) ([^:]+): (.*) \(open\)$', ideas, re.M):
        source, author, text = m.groups()
        title = text.split(':', 1)[0].split('. ', 1)[0][:94]
        sources.append(dict(source=source, title=title, lane='Backlog', who=author,
                            status='idea', text=text))
    snapshot = {'read_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'epic': 'a13308', 'tasks': sources}
    # Evidence is source prose only; never contains session tokens.
    (HERE / 'evidence').mkdir(exist_ok=True)
    prior = HERE / 'evidence/frontier-seed.json'
    if not prior.exists():
        prior.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding='utf-8')
    added = 0
    for task in sources:
        if door.rows('taskboard-task', source=task['source']):
            continue
        add_word = door.rows('word', bound='task-add')[0]['word']
        line = add_word + ' ' + ' '.join(k + '=' + quote(v) for k, v in dict(
            title=task['title'], to=task['lane'], who=task['who'], when=snapshot['read_at'],
            source=task['source'], status=task['status'], text=task['text']).items())
        door.say(line, press='taskboard-seed-' + task['source'])
        added += 1
    return added, len(sources)


def open_board(door):
    windows = door.rows('window', lens='taskboard')
    if windows:
        receipt = 'window intent already exists'
    else:
        receipt = door.say('window.open taskboard at=140,110 size=1380,920')['text']
        for window in door.rows('window', lens='taskboard'):
            if window.get('name') != 'Task board':
                door.say('set ' + window['id'] + ' name="Task board"')
    for _ in range(20):
        if any(w.get('shows') == 'taskboard' and w.get('shown') for w in door.say('window.list')['rows']):
            return receipt + '\n~ desktop host: Task board is shown'
        time.sleep(.5)
    return receipt + '\n~ desktop host: shown=false; native visibility is not confirmed'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--no-open', action='store_true')
    ap.add_argument('--no-seed', action='store_true')
    args = ap.parse_args()
    d = live_door()
    made, skipped = install(d)
    print(f'Install: {made} lines applied, {skipped} unchanged', flush=True)
    print('Word names: ' + ', '.join(r['word'] for name in ('add', 'move', 'assign', 'done', 'note')
                                   for r in d.rows('word', bound='task-'+name)), flush=True)
    if not args.no_seed:
        added, total = seed(d)
        print(f'Seed: {added} added, {total} current source tasks', flush=True)
    print(f'V2: {migrate(d)} existing cards gained missing defaults; identities/history retained', flush=True)
    if not args.no_open:
        print(open_board(d), flush=True)


if __name__ == '__main__':
    main()
