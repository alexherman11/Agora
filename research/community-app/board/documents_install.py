"""Recovered legacy installer for historical hidden fixtures; NOT a live plan.

The caller installs/reloads the files module using board.install.modules().
No module, grant or live world is modified merely by importing this file.
Its broad standalone-widget grants are held, not proposed for issuance.
Production closeout uses DOCUMENTS-ISSUANCE.md and must not replay this installer.
"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1] / 'kernel-lab'
sys.path.insert(0, str(LAB))
from painter.install import upsert, widget_source, Q
from painter.catalogue import cards, T

GRANTS = ('window.surface rows look look-view components help component-health component-action '
          'files.* file-read upload attach make set board.rsvp board.calendar '
          'hear:make hear:set hear:attach hear:files.* hear:file-result hear:forget hear:undo '
          'hear:component hear:component-action')
PARTS = {
    'document-library': ('A nestable document library with authored toolbar, upload, phone and listing slots.',
                         'body heading', 'tools upload phone listing', ''),
    'document-toolbar': ('Folder path and folder creation for any document library.',
                         'body breadcrumbs name status', '', 'folder'),
    'document-upload': ('Drop files or use one Choose files button through the guarded files door.',
                        'body picker drop choose status', '', 'store attach'),
    'document-list': ('A reading-backed collection of folders and document entries.',
                      'body empty', 'entries', ''),
    'document-entry': ('Named folder or file, rename, move, post source and preview slot.',
                       'body name destination source status', 'preview', 'rename move store'),
}


def templates():
    """Append unchanged to any host lens; the first line supplies its routing part."""
    return (HERE / 'documents.lens').read_text(encoding='utf-8').split('\n', 1)[1]


def install_documents(door):
    channels = door.rows('board-channel')
    channel = next((r['group'] for r in channels if r.get('title') == 'Research & documents'), None)
    if not channel:
        raise ValueError('Install the board channels before its document library.')
    library = upsert(door, 'document-library', 'seabright-documents',
                     title='Research & documents', **{'in': channel})
    source = (HERE / 'document-components.bundle.js').read_text(encoding='utf-8')

    def component(name, code, **card):
        tid = upsert(door, 'component', name, code=code, **card)
        if door.rows('component', name=name)[0].get('reviewed_code') != hashlib.sha256(code.encode()).hexdigest():
            door.say('look ' + tid)
            door.say('component ' + tid)
        return tid

    for card in cards():
        if card['name'] in ('file', 'table'):
            name = card.pop('name')
            path = LAB / 'components' / (name + '.js')
            code = (path if path.exists() else LAB / 'components/catalogue.js').read_text(encoding='utf-8')
            component(name, code, **card)
    for name, (purpose, parts, slots, gestures) in PARTS.items():
        schema = dict(labels=T(default='{}'), library=T('fact'))
        if name == 'document-library':
            schema['title'] = T(default='Research & documents')
            schema['showHeading'] = T('boolean', True)
        component(name, source, purpose=purpose, category='files', settings=json.dumps(schema),
                  parts=json.dumps({p: dict(facts='bound visible row') for p in parts.split()}),
                  slots=json.dumps(slots.split()), gestures=gestures,
                  example=(HERE / 'documents.lens').read_text(encoding='utf-8') if name == 'document-library' else 'root : ' + name,
                  uses='Document libraries; community research; file galleries',
                  limitations='Requires the files module and authored slots/gestures. Phone slot is empty; no network listener.')
    lens = upsert(door, 'lens', 'seabright-documents', title='Research & documents', painter='components',
                  text=(HERE / 'documents.lens').read_text(encoding='utf-8'),
                  view=json.dumps(dict(documentsFolder='', documentsOpen='')))
    widget = upsert(door, 'widget', 'seabright-documents', title='Research & documents',
                    style='bars', receipts='quiet', component_lens='seabright-documents',
                    code=widget_source(board_look=False))
    current = door.rows('widget', name='seabright-documents')[0]
    if not current.get('on') or not any(g.get('words') == GRANTS and not g.get('revoked') for g in door.rows('grant', to=widget)):
        door.say('look ' + widget)
        door.say('widget ' + widget + ' surface=window grants=' + Q(GRANTS))
    upsert(door, 'button', 'seabright-documents-button', label='Research & documents',
           icon='folder', bar='taskbar', does='window.open seabright-documents')
    return dict(library=library, lens=lens, widget=widget, opened=False)
