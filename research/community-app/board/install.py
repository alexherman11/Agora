"""Installer speaks words through the caller's existing door; never a live target by default."""
import json
import sys
from pathlib import Path

from protocol import line

HERE = Path(__file__).resolve().parent
# list facts a definitions.json channel entry may carry onto its board-channel thing
CHANNEL_KEYS = ('opens', 'opens_label', 'label', 'hidden', 'section', 'compose_default')


def modules():
    return [dict(name='board', run=[sys.executable, str(HERE / 'board.py')], publishes='board.*',
                 grants='clock rows look post reply make set claim file-read'),
            dict(name='files', run=[sys.executable, str(HERE / 'files.py')], publishes='files.*',
                 grants='rows file-result')]


def install(say, see):
    """say/see are authenticated callables returning ordinary door receipts."""
    data = json.loads((HERE / 'definitions.json').read_text(encoding='utf-8'))
    ids = dict(channels={}, kinds={}, orderings={})
    entries = see('rows word')['rows']
    base_post = next(e['id'] for e in entries if e.get('from') == 'kernel' and e.get('bound') == 'post')
    for definition in data['channels']:
        # opens names the entry's own view (calendar, map, chat, …); the board lens arranges a part for it.
        # A chat entry is a chat thing (the kernel's say/react/pin words); a group=no entry is a view only.
        facts = {k: definition[k] for k in CHANNEL_KEYS if k in definition}
        if definition.get('opens') == 'chat':
            cid = say(line('make', kind='chat', name=definition['name']))['made'][0]
            ids['channels'][definition['name']] = cid
            say(line('make', kind='board-channel', chat=cid, title=definition['name'], **facts))
            continue
        if definition.get('group') == 'no':
            ids['channels'][definition['name']] = say(line('make', kind='board-channel', title=definition['name'], **facts))['made'][0]
            continue
        gid = say(line('group', name=definition['name'], open='yes'))['made'][0]
        ids['channels'][definition['name']] = gid
        say(line('make', kind='board-channel', group=gid, title=definition['name'], **facts))
        for word, limit, may in [('post', definition['posts_per_day'], definition['post_may']),
                                  ('reply', definition['replies_per_day'], 'members')]:
            eid = say(line('dictionary-copy', base_post, word=word, **{'in': gid}))['made'][0]
            see('look ' + eid)
            say(line('word-set', eid, may=may, once=f'at most {limit} per day per person',
                help=f'{word}: {limit} per person per day in {definition["name"]}. Please give neighbors time to respond. Undo takes your act back.'))
    for definition in data['kinds']:
        ids['kinds'][definition['name']] = say(line('make', kind='kind', **definition))['made'][0]
    for definition in data['orderings']:
        ids['orderings'][definition['name']] = say(line('make', kind='board-order', **definition))['made'][0]
    ids['settings'] = say(line('make', kind='board-settings', title='Seabright board defaults',
        default_order=ids['orderings']['New'], steward='Alex'))['made'][0]
    ids['file_settings'] = say(line('make', kind='file-settings', max_bytes=str(25 * 1024 * 1024)))['made'][0]
    for name, order in [('new', 'new'), ('top-this-week', 'top-week'), ('needs-answers', 'needs-answers'),
                         ('happening-soon', 'soon')]:
        say(line('verb ' + name, kind_of='see', may='members', steps='board.feed order=' + order,
            help=name + ': a copyable feed reading; make your own board-order thing or verb.'))
    say(line('verb catch-up', kind_of='see', may='members', steps='board.catch-up',
             help='catch-up: new decisions, events, answers, busy threads and followed replies since your marker. Plain data.'))
    return ids
