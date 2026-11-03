"""Switch on the Seabright board's channel views in the live desktop: Documents and the map inside the board.

Claude, 3 Nov 2026, from Alex's "unstick the board" (cards dk1498, dk1561/dk1614, dk1563). Safe to run again:
every step checks what is already there first. Opens no window.

    C:/Projects/Agora4/.venv/Scripts/python.exe research/community-app/board/board_activate.py --live

What it does, all as Alex through his door:
  1. one document library, Research & documents, seen by that channel's group;
  2. the document components (and the file preview's new `target` setting), each reviewed as it is installed;
  3. the seabright-documents lens (nested in the board, no window of its own);
  4. grants: files provider make/set limited to that library; board widget the five files.* words limited to that
     library, their event subscriptions, and the five map reads its map panel needs (apps/map/EMBEDDING.md);
  5. the board lens from board.lens (asks, documents and map lines), and Research & documents opens=documents.
The map's own components (map-panel) come from apps/map/install.py --live, run before this.
"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1] / 'kernel-lab'
sys.path[:0] = [str(HERE), str(LAB)]
from painter.install import taskboard, upsert, Q          # noqa: E402
from painter.catalogue import cards, T                   # noqa: E402
from documents_install import PARTS                      # noqa: E402

LIBRARY = 'seabright-documents'
FILES_WORDS = 'files.browse files.folder files.store files.rename files.move'
HEAR_WORDS = 'hear:attach hear:files.* hear:file-result'
MAP_WORDS = 'map.layers map.tile map.find map.where map.place'


def component(door, name, code, **card):
    tid = upsert(door, 'component', name, code=code, **card)
    if door.rows('component', name=name)[0].get('reviewed_code') != hashlib.sha256(code.encode()).hexdigest():
        door.say('look ' + tid)
        door.say('component ' + tid)
    return tid


def grant(door, to, words, only=''):
    """Say a grant only when no live grant to `to` already carries exactly these words and narrowing."""
    for g in door.rows('grant', to=to):
        if not g.get('revoked') and g.get('words') == words and str(g.get('only') or '') == only:
            return g['id']
    door.say('look ' + to)
    return door.say('grant ' + to + ' words=' + Q(words) + (' only=' + Q(only) if only else ''))['made'][0]


def activate(door):
    ids = {}
    channel = next(r for r in door.rows('board-channel') if r.get('title') == 'Research & documents')
    group = channel['group']
    have = door.rows('document-library', name=LIBRARY)
    ids['library'] = have[0]['id'] if have else door.say(
        f'make kind=document-library name={LIBRARY} title="Research & documents" sees=group in={group}')['made'][0]

    source = (HERE / 'document-components.js').read_text(encoding='utf-8')
    source = source.replace('export default {mount', 'export default {css:' +
                            json.dumps((HERE / 'documents.css').read_text(encoding='utf-8')) + ',mount')
    for card in cards():
        if card['name'] in ('file', 'table'):
            name = card.pop('name')
            path = LAB / 'components' / (name + '.js')
            ids[name] = component(door, name, (path if path.exists() else LAB / 'components/catalogue.js')
                                  .read_text(encoding='utf-8'), **card)
    lens_text = (HERE / 'documents.lens').read_text(encoding='utf-8')
    for name, (purpose, parts, slots, gestures) in PARTS.items():
        schema = dict(labels=T(default='{}'), library=T('fact'))
        if name == 'document-library':
            schema['title'] = T(default='Research & documents')
        ids[name] = component(door, name, source, purpose=purpose, category='files', settings=json.dumps(schema),
                              parts=json.dumps({p: dict(facts='bound visible row') for p in parts.split()}),
                              slots=json.dumps(slots.split()), gestures=gestures,
                              example=lens_text if name == 'document-library' else 'root : ' + name,
                              uses='Document libraries; community research; file galleries',
                              limitations='Needs the files module and authored slots/gestures. Phone slot is empty.')
    ids['lens'] = upsert(door, 'lens', LIBRARY, title='Research & documents', painter='components', text=lens_text,
                         view=json.dumps(dict(documentsFolder='', documentsOpen='')))

    files = door.rows('module', name='files')[0]['id']
    board = door.rows('widget', name='seabright-board')[0]['id']
    ids['grant_files'] = grant(door, files, 'make set', f'kind:document-folder,document-entry;library:{ids["library"]}')
    ids['grant_board_files'] = grant(door, board, FILES_WORDS, f'library:{ids["library"]}')
    ids['grant_board_hear'] = grant(door, board, HEAR_WORDS)
    ids['grant_board_map'] = grant(door, board, MAP_WORDS)

    ids['board_lens'] = upsert(door, 'lens', 'seabright-board', text=(HERE / 'board.lens').read_text(encoding='utf-8'))
    if channel.get('opens') != 'documents':
        door.say('look ' + channel['id'])
        door.say(f'set {channel["id"]} opens=documents opens_label=Documents')
    return ids


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--live', action='store_true')
    if not ap.parse_args().live:
        ap.error('import activate(door) for a scratch world; --live switches the views on in the desktop world')
    sys.path.insert(0, str(HERE.parents[2] / 'research/window-lab/kernel-desktop'))
    from gaming_gate import assert_clear
    assert_clear()
    print(json.dumps(activate(taskboard.live_door()), indent=1))


if __name__ == '__main__':
    main()
