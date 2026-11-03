"""Offline document scenarios. No windows, sockets, live world or native driver."""
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / 'kernel-lab')]
from kernel.kernel import Kernel
from kernel.blobs import receive
from documents import call


@pytest.fixture
def desk(tmp_path):
    k = Kernel(tmp_path / 'world', dict(tag='docs', name='Documents test',
        steward=dict(account='alex', name='Alex'), invites_counted_by='kernel',
        invites=[dict(code='x', uses=5)]))
    a = k.actor_for(k.accounts['alex'])
    b = k.actor_for(k.join('bea', 'Bea', invite='x')['person'])
    def act(text, actor=a):
        out = k.run(actor, text)
        assert out['ok'], out
        return out
    group = act('group name=Research open=yes')['made'][0]
    library = act('make kind=document-library name=documents in=' + group)['made'][0]
    return k, a, b, act, group, library


def invoke(desk, word, actor=None, **args):
    k, a, _, _, _, _ = desk
    actor = actor or a
    def read(use, text):
        out = k.run(actor, text, mode='see')
        assert out['ok'], out
        return out['rows']
    target = args.pop('target', None)
    result = call(dict(use='test', word='files.' + word, args=dict(target=target, kv=args),
                       caller=dict(id=actor.id, person=actor.person)), read)
    if 'lines' not in result:
        return result
    for text in result['lines']:
        out = k.run(actor, text, saw=result['saw'])
        assert out['ok'], out
    return out


def test_upload_folder_rename_move_preview_and_find_again(desk):
    k, a, b, act, group, library = desk
    folder = invoke(desk, 'folder', name='Meeting notes', library=library)['made'][0]
    nested = invoke(desk, 'folder', name='November', library=library, parent=folder)['made'][0]
    file = receive(k, a, b'Neighbour meeting notes', 'notes.txt', group)['made'][0]
    entry = invoke(desk, 'store', target=file, library=library, parent=folder)['made'][0]
    assert not k.shown(b.person, file)  # indexing cannot publish bytes
    act('look ' + file)
    act('look ' + entry)
    act('attach ' + file + ' to=' + entry)
    assert k.shown(b.person, file)
    invoke(desk, 'rename', target=entry, name='Minutes')
    invoke(desk, 'move', target=entry, to=nested)
    assert [r['name'] for r in invoke(desk, 'browse', library=library, parent=nested)['rows']] == ['Minutes']
    assert not any(r.get('file_id') == file for r in invoke(desk, 'browse', library=library, parent=folder)['rows'])
    assert k.run(b, 'file-read ' + file, mode='see')['ok']
    invoke(desk, 'move', target=entry, to=library)
    assert invoke(desk, 'browse', library=library)['rows'][1]['name'] == 'Minutes'


def test_cycles_cross_library_and_empty_names_refuse(desk):
    _, _, _, act, group, library = desk
    parent = invoke(desk, 'folder', name='Parent', library=library)['made'][0]
    child = invoke(desk, 'folder', name='Child', library=library, parent=parent)['made'][0]
    for destination in (parent, child):
        with pytest.raises(ValueError, match='inside itself'):
            invoke(desk, 'move', target=parent, to=destination)
    other = act('make kind=document-library name=other in=' + group)['made'][0]
    with pytest.raises(ValueError, match='this library'):
        invoke(desk, 'move', target=child, to=other)
    with pytest.raises(ValueError, match='name'):
        invoke(desk, 'folder', library=library, name=' ')


def test_post_attachment_stays_linked_and_follows_original_visibility(desk):
    k, a, b, act, group, library = desk
    post = act('post "Original post" in=' + group)['made'][0]
    file = receive(k, a, b'Original evidence', 'evidence.txt', group)['made'][0]
    act('look ' + file); act('look ' + post)
    act('attach ' + file + ' to=' + post)
    rows = invoke(desk, 'browse', library=library)['rows']
    assert rows[0]['source_post'] == post and rows[0]['file_id'] == file
    entry = invoke(desk, 'store', target=file, library=library)['made'][0]
    assert k.state.get(file, 'attached_to') == post
    assert len(invoke(desk, 'browse', library=library)['rows']) == 1
    # Hiding the source also hides bytes and the document entry from browse.
    act('look ' + post); act('forget ' + post + ' reason="Outdated"')
    assert not invoke(desk, 'browse', actor=b, library=library)['rows']
    assert not k.run(b, 'file-read ' + file, mode='see')['ok']
    assert k.state.get(entry, 'file') == file


def test_other_member_cannot_rename_or_move_someone_elses_folder(desk):
    k, _, b, _, _, library = desk
    folder = invoke(desk, 'folder', name='Shared folder', library=library)['made'][0]
    def read(use, text):
        return k.run(b, text, mode='see')['rows']
    result = call(dict(use='b', word='files.rename', args=dict(target=folder, kv=dict(name='Changed'))), read)
    out = k.run(b, result['lines'][0], saw=result['saw'])
    assert not out['ok']
    assert k.state.get(folder, 'name') == 'Shared folder'
