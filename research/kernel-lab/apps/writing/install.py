"""Install the Writing center: the comment kind, seven component cards, the lens and its window, a dock button, and the
first documents (the two plans for Alex to review, and a short guide). Every step is an ordinary line through the door;
nothing here imports the kernel.

Importing install(door) is scratch-safe. `--live` installs into Alex's desktop world (door 8810) and opens nothing.
`--door URL` installs into another door (a hidden sandbox), signed as Claude.
Undo: `off` the writing widget; `forget` the Writing button, the widget, the lens and the component cards (or `undo` each
act). The documents and comments are ordinary things that belong to people; forget them one by one if wanted.
Re-running changes only what differs: a document's text is never overwritten once it exists (people may have edited it).
"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
ROOT = LAB.parents[1]
sys.path[:0] = [str(LAB)]
from painter.install import upsert, widget_source, taskboard, Q  # noqa: E402

LENS = 'writing'
GRANTS = ('window.surface rows look look-view history components help component-health component-action file-read '
          'make set forget undo say ask hear:make hear:set hear:forget hear:undo hear:say hear:component hear:component-action')
VIEW = {'open': '', 'back': '', 'fresh': ''}

KINDS = {
    'comment': dict(help='A comment on a document: about= the document, quote= the words it is about (with before=, after= '
                         'and heading= to find them again), text= what was said; reply_to= another comment; resolved=yes.',
                    fields='about quote text before after heading reply_to resolved',
                    compose_label='Comment on a document',
                    compose_description='Say something about some words in a document. It stays beside them.'),
}

T = lambda type_='text', default=None: dict(type=type_, **({} if default is None else {'default': default}))
COMPONENTS = {
    'writing-shell': ('A writing window: a slim top bar (back, home, new document), a rail of documents on the left and '
                      'the open document or the home page on the right.', 'body', 'rail home open', 'new',
                      dict(title=T(default='Writing'))),
    'doc-rail': ('The rail of a writing window: Find a document (title and text, as you type), then its collections.',
                 'body find', 'shelves', '', dict(hint=T(default='Find a document'))),
    'doc-shelf': ('A folding collection of documents: label, count, + for a new one; its rows newest first, or inner shelves.',
                  'body', 'documents shelves', 'new',
                  dict(label=T(default='Documents'), open=T('boolean', False), nested=T('boolean', False),
                       hot=T('boolean', False), empty=T(default='Nothing here yet'))),
    'doc-row': ('One document as a rail row, a home card or a list line; pressing it opens the document.',
                'row', '', '', dict(look=T(default='row'))),
    'doc-home': ('A writing window with nothing open: plans waiting for you, recently changed, and a way to start.',
                 'body', 'waiting recent', 'new', dict(recent=T('number', 8))),
    'doc-page': ('One Markdown document, drawn as you write: press a part to edit it in place, Ctrl+E for the whole '
                 'source, [[ to link another document, a plan\'s calls, comments in the margin on selected words, and '
                 'sending a passage or the whole document into JEFF\'s Conversation.', 'body title plan editor source',
                 'comments', 'edit retitle move verdict waiting comment ask-jeff new forget', {}),
    'doc-comment': ('A comment beside a document: the words it is about and where they are now (under a heading, moved, '
                    'changed or gone), its replies, reply, resolve and send to JEFF.', 'body quote text reply', '',
                    'reply resolve reopen ask-jeff', dict(doctext=T(), doctitle=T())),
}
LIMITS = ('Markdown only: headings, lists and tasks, quotes, code, tables, links, [[links]], ![[embeds]] as a card. '
          'One person edits a block at a time; a change made meanwhile refuses the save and keeps your words. '
          'Web addresses cannot be opened from the window (no word for it yet): they are shown and copied.')

GUIDE = '''# Writing in Agora

> Draft by Claude, 27 Oct 2026, after the old desk's note of the same name. Every document here is a thing that belongs to the person who made it.

A document is one **Markdown** text. It is drawn as you read it. Press a part to write in it: that part shows its marks, the rest stays drawn. Press *Ctrl+E* to see the whole source, and again to come back.

## What it knows that a file can't

- A link is a thing, not a path: [[Moving into the desktop]] stays linked when it is renamed. Type `[[` and choose.
- **Linked from**, under each document, is live: every document that links to it.
- Select some words and right-click: **Comment** puts a note beside them in the margin, and **Send to JEFF** quotes them into his Conversation with a link back here.
- A plan has your call on it: *Build it*, *Build it, with my comments*, *Not yet, I have questions*, or *Wrong shape*.

## Keys

| Key | What it does |
| --- | --- |
| `Ctrl+E` | the source, and back |
| `Ctrl+B` / `Ctrl+I` | **bold** / *italic* while writing |
| `[[` | link to a document by its title |
| `Tab` | indent a list item |
| `Ctrl+S`, `Esc` | keep what you wrote (leaving the part keeps it too) |
| `Ctrl+K` | find a document |
| `Alt+←` | back to the document before |

## Next

- [x] Headings, lists, quotes, code and tables
- [x] Links that open the other document
- [x] Comments that say when their words have changed
- [ ] Two people writing in the same part at once
'''

PLANS = [
    dict(source='research/kernel-lab/agents/MOVING-IN.md', title='Moving into the desktop', collection='plans',
         plan='answered', still_open='T1, the welcome text: not answered yet',
         page='https://claude.ai/artifact/AYPo5fhJYpK8AN7yNbK2HS', drafted_by='Claude'),
    dict(source='research/clutter-lab/README.md', title='Shedding clutter', collection='plans', plan='waiting',
         still_open='C6 (the hot log rolls over) and C10 (embeddings; kinds that nest): Alex wants to talk them through',
         page='https://claude.ai/artifact/XjG2dNmege6Kh5neznTtbS', drafted_by='Claude'),
]


def code():
    return (HERE / 'writing-components.js').read_text(encoding='utf-8')


def documents(door):
    made = {}
    for plan in PLANS:
        if door.rows('document', source=plan['source']):
            made[plan['title']] = door.rows('document', source=plan['source'])[0]['id']
            continue
        text = (ROOT / plan['source']).read_text(encoding='utf-8')
        made[plan['title']] = door.say('make kind=document' + ''.join(f' {k}={Q(v)}' for k, v in plan.items())
                                       + ' text=' + Q(text))['made'][0]
    if not door.rows('document', source='research/kernel-lab/apps/writing/install.py#guide'):
        made['Writing in Agora'] = door.say('make kind=document title="Writing in Agora" collection=documentation '
                                            'drafted_by=Claude source="research/kernel-lab/apps/writing/install.py#guide" text='
                                            + Q(GUIDE))['made'][0]
    return made


def install(door, docs=True):
    ids = {}
    for kind, facts in KINDS.items():
        ids['kind:' + kind] = upsert(door, 'kind', kind, **facts)
    source = code()
    digest = hashlib.sha256(source.encode()).hexdigest()
    for name, (purpose, parts, slots, gestures, schema) in COMPONENTS.items():
        tid = upsert(door, 'component', name, category='writing', purpose=purpose, settings=json.dumps(schema),
                     parts=json.dumps({p: dict(facts='bound visible row') for p in parts.split()}),
                     slots=json.dumps(slots.split()), gestures=gestures, example=f'root : {name}',
                     uses='Documents, plans for review, notes, comments on a passage', code=source, limitations=LIMITS)
        if door.rows('component', name=name)[0].get('reviewed_code') != digest:
            door.say('look ' + tid)
            door.say('component ' + tid)
        ids[name] = tid
    ids['lens'] = upsert(door, 'lens', LENS, title='Writing', painter='components', right_click='ask',
                         text=(HERE / 'writing.lens').read_text(encoding='utf-8'), view=json.dumps(VIEW),
                         reconcile_ms='15000')
    ids['widget'] = upsert(door, 'widget', LENS, title='Writing', style='bars', receipts='quiet', component_lens=LENS,
                           code=widget_source(board_look=False))
    current = door.rows('widget', name=LENS)[0]
    if not current.get('on') or not any(g.get('words') == GRANTS and not g.get('revoked')
                                        for g in door.rows('grant', to=ids['widget'])):
        door.say('look ' + ids['widget'])
        door.say('widget ' + ids['widget'] + ' surface=window grants=' + Q(GRANTS))
    ids['button'] = upsert(door, 'button', LENS + '-button', label='Writing', bar='taskbar', icon='pen-line',
                           does='window.open ' + LENS)
    if docs:
        ids.update(documents(door))
    return ids


def claude_door(url):
    keep = ROOT / 'research/window-lab/kernel-desktop/state/world/keep/sessions.json'
    sessions = json.loads(keep.read_text(encoding='utf-8'))
    token = [t for t, v in sessions.items() if v.get('signer') == 'claude']
    if len(token) != 1:
        raise RuntimeError('No single Claude desktop session; no session files changed')
    return taskboard.Door(url, token[0])


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--live', action='store_true')
    ap.add_argument('--door', help='another door, e.g. a hidden sandbox: http://127.0.0.1:8831')
    args = ap.parse_args()
    if args.door:
        print(json.dumps(install(claude_door(args.door)), indent=1))
        return
    if not args.live:
        ap.error('--door <sandbox url>, or --live to install into the desktop world without opening it')
    sys.path.insert(0, str(ROOT / 'research/window-lab/kernel-desktop'))
    from gaming_gate import assert_clear
    assert_clear()
    print(json.dumps(install(claude_door('http://127.0.0.1:8810')), indent=1))


if __name__ == '__main__':
    main()
