"""No browser: file imports in an isolated world, compiled Documents bindings and real words."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1] / 'kernel-lab'
sys.path[:0] = [str(HERE), str(LAB)]
from proof import Proof, install, line
from painter.arrangement import compile_view, resolve_line
from painter.catalogue import cards, T
from painter.install import upsert, widget_source
from documents_install import PARTS


def main():
    f = Proof()
    location = Path(f.tmp.name)
    try:
        ids = install(lambda s: f.say('Alex', s), lambda s: f.see('Alex', s))
        class Door:
            say = staticmethod(lambda s: f.say('Alex', s))
            rows = staticmethod(lambda kind, **kv: f.see('Alex', line('rows', kind, **kv))['rows'])
        d = Door()
        for card in cards():
            name = card.pop('name')
            p = LAB / 'components' / (name + '.js')
            upsert(d, 'component', name, **card, code=(p if p.exists() else LAB / 'components/catalogue.js').read_text(encoding='utf-8'))
        for name, (purpose, parts, slots, gestures) in PARTS.items():
            upsert(d, 'component', name, purpose=purpose, settings=json.dumps(dict(labels=T(default='{}'), library=T('fact'))),
                   parts=json.dumps({p: {} for p in parts.split()}), slots=json.dumps(slots.split()), gestures=gestures,
                   code=(HERE / 'document-components.js').read_text(encoding='utf-8'))
        group = ids['channels']['Research & documents']
        library = d.say(line('make', kind='document-library', name='seabright-documents', title='Research & documents', **{'in': group}))['made'][0]
        _, uploaded = f.upload('Alex', 'minutes.txt', b'Exact passage in a document.', group)
        assert uploaded['ok'] and uploaded['conversion']['ok'], uploaded
        file = uploaded['made'][0]
        entry = d.say(line('make', kind='document-entry', file=file, library=library, parent=library, within=library, name='Minutes', **{'in': group}))['made'][0]
        f.see('Alex', 'look ' + file); f.see('Alex', 'look ' + entry)
        d.say(line('attach', file, to=entry))
        lens = upsert(d, 'lens', 'seabright-documents', painter='components',
                      text=(HERE / 'documents.lens').read_text(encoding='utf-8'),
                      view=json.dumps(dict(documentsFolder='', documentsOpen=entry)))
        upsert(d, 'widget', 'seabright-documents', component_lens='seabright-documents', code=widget_source(board_look=False))
        before = {kind: d.rows(kind) for kind in ('widget', 'grant', 'window')}
        imports = {
            'input': LAB / 'components/catalogue.js',
            'calendar': LAB / 'components/calendar.js',
            'file': LAB / 'components/file.js',
            'work-overview': LAB / 'components/work-overview.js',
            **{name: HERE / 'board-components.bundle.js' for name in ('board-feed', 'board-composer')},
            **{name: LAB / 'apps/map/map-components.bundle.js' for name in ('map-shell', 'map-layers', 'map-panel')},
        }
        for name, path in imports.items():
            target = upsert(d, 'component', name, code=path.read_text(encoding='utf-8'))
            f.see('Alex', 'look ' + target)
            d.say('component ' + target)
        f.check('nine components import exact bytes from one file each',
                all(d.rows('component', name=name)[0]['code'] == path.read_text(encoding='utf-8')
                    for name, path in imports.items()))
        f.check('component imports leave widgets grants and windows unchanged',
                all(d.rows(kind) == before[kind] for kind in before))
        f.check('existing widget has no pagination helper dependency',
                'pageBounds' not in d.rows('widget', name='seabright-documents')[0]['code'])
        actor = f.k.actor_for(f.k.accounts['alex'])
        plan = compile_view(f.k, actor, lens, reader=lambda text: f.raw('Alex', text, 'see'))['rows'][0]
        def walk(n):
            yield n
            for c in n['children']:
                yield from walk(c)
        reader = next(n for n in walk(plan['tree']) if n['component'] == 'file')
        f.check('Documents binds a visible inline destination', reader['settings']['quoteMode'] == 'inline' and reader['settings']['startLabel'] == 'Research & documents')
        f.check('library-only file retains its group for explicit discussion', reader['facts']['groups'] == [group])
        start = next(g for g in reader['gestures'] if g['event'] == 'start')
        command = resolve_line(start['line'].replace('$fields', 'text="Response\\n\\n> Exact passage" title="Minutes"'),
                               dict(start['env'], group=group))
        thread = d.say(command)['made'][0]
        f.check('authored start creates one discussion in its channel', group in next(p for p in d.rows('post') if p['id'] == thread)['groups'])
        reply = next(g for g in reader['gestures'] if g['event'] == 'reply')
        command = resolve_line(reply['line'].replace('$fields', 'text="Reply" quote="Exact passage" source=' + file + ' page=1'),
                               dict(reply['env'], target=thread))
        made = d.say(command)['made'][0]
        saved = next(p for p in d.rows('post') if p['id'] == made)
        f.check('authored reply stores exact document quotation', saved['quote'] == 'Exact passage' and saved['quote_source'] == file)
        refused = f.raw('Alex', line('board.reply', thread, text='Wrong quote', quote='NOT IN DOCUMENT', source=file, page=1))
        f.check('underlying word still refuses an invented passage', not refused['ok'])
        print('ROUND1 WORLD CHECKS ' + str(f.checks), flush=True)
    finally:
        f.close()
    assert not location.exists(), 'fixture world remains: ' + str(location)
    print('ROUND1 FIXTURE REMOVED', flush=True)


if __name__ == '__main__':
    main()
