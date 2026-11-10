"""search <words> and find <words> (card dk1322, Alex dk1514, 28 Oct): 'search Seabright' resolved Seabright as the
map and refused; 'find Seabright' said nothing here is a seabright. A world shaped like the live one (8810), hidden."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kernel.kernel import Kernel, Tx


@pytest.fixture
def world(tmp_path):
    k = Kernel(tmp_path / 'world', {'tag': 'sw', 'name': 'Search',
        'steward': {'account': 'alex', 'name': 'Alex'}, 'invites_counted_by': 'kernel',
        'invites': [{'code': 'x', 'uses': 5}], 'groups': [{'name': 'Private'}]})
    a = k.actor_for(k.accounts['alex'])
    b = k.actor_for(k.join('bea', 'Bea', invite='x')['person'])
    private = next(g for g in k.things('group') if k.state.get(g, 'name') == 'Private')
    ids = {}

    def put(key, **facts):
        tx = Tx(k)
        tx.part('make', None, 'fixture')
        t = tx.mint()
        for f, v in dict(facts, made_by=k.accounts['alex']).items():
            tx.set(t, f, v)
        k._commit(tx, by='kernel', words='fixture')
        ids[key] = t

    # the live world's board.search: a module's family word, the only "search" before this card
    put('board.search', kind='word', word='board.search', word_kind='see', takes='q=<text>', may='members',
        undo='no', **{'from': 'module:board'}, bound='board.search', lives=k.place,
        help='Search visible posts, replies and extracted document pages.')
    put('map', kind='map', name='Seabright', lens='seabright-map', centre='36.9672,-122.0088')
    put('lens', kind='lens', name='seabright-board', title='Seabright board',
        text='root : board-shell, title "Seabright"\n  watch reading:"rows kind"\n'
             '  watch reading:"rows board-channel"\n  watch reading:"rows board-order"')
    put('widget', kind='widget', name='seabright-board', title='Seabright board')
    put('button', kind='button', name='seabright-board-button', label='Seabright board', bar='taskbar',
        does='window.open seabright-board')
    put('mapbutton', kind='button', name='seabright-map-button', label='Seabright map', bar='taskbar')
    for c in ('Announcements', 'Meetings & events', 'Research & documents', 'Asks & offers'):
        put(c, kind='board-channel', title=c)
    put('order', kind='board-order', sort='new')                                     # no name: not listed
    put('done', kind='taskboard-task', title='Seabright board: first sketch', lane='Done', text='Shipped.')
    put('build', kind='taskboard-task', title='Seabright board: build out the app', lane='Now',
        text='Alex: flesh out the Seabright board into a real app. Research & documents: folders, uploads.')
    put('cal', kind='taskboard-task', title='Calendar for meetings', lane='Next',
        text='The Meetings & events channel of the Seabright board opens to a calendar.')
    put('other', kind='taskboard-task', title='Dentist', lane='Now', text='Tuesday.')
    put('secret', kind='note', title='Seabright surprise party', sees='group:' + private)
    return k, a, b, ids


def run(k, actor, line, ok=True):
    out = k.run(actor, line)
    assert out['ok'] == ok, out
    return out


def found(out):
    return [r['id'] for r in out['rows']]


def test_search_seabright_finds_the_board_its_button_channels_map_and_open_cards(world):
    """The exact case: Alex asks why Claude can't find the active Seabright work."""
    k, a, b, ids = world
    out = run(k, a, 'search Seabright')
    got = found(out)
    for key in ('lens', 'widget', 'button', 'mapbutton', 'map', 'build', 'cal',
                'Announcements', 'Meetings & events', 'Research & documents', 'Asks & offers'):
        assert ids[key] in got, (key, out['text'])
    assert ids['other'] not in got and ids['order'] not in got and ids['board.search'] not in got
    # title matches first; the open Now card above the done one; channels (shown in the board) after titles
    assert got.index(ids['build']) < got.index(ids['done']) if ids['done'] in got else True
    assert got.index(ids['build']) < got.index(ids['Announcements']) < got.index(ids['cal'])
    row = out['rows'][got.index(ids['build'])]
    assert row['kind'] == 'taskboard-task' and row['name'] == 'Seabright board: build out the app'
    assert row['lane'] == 'Now' and 'Seabright' in row['snippet']
    assert 'Seabright board: build out the app' in out['text'] and 'taskboard-task' in out['text']
    chan = out['rows'][got.index(ids['Announcements'])]
    assert chan['match'] == 'part' and 'Seabright board' in chan['snippet']


def test_the_exact_card_title_comes_first_and_done_work_comes_last(world):
    k, a, b, ids = world
    out = run(k, a, "search 'Seabright board: build out the app'")
    assert found(out)[0] == ids['build']
    out = run(k, a, 'search Seabright board limit=50')
    got = found(out)
    assert got[-1] == ids['done']                                   # done work below everything open
    assert got.index(ids['build']) < got.index(ids['cal'])         # a title match above a text-only match


def test_find_words_searches_when_the_word_is_no_kind_and_lists_a_kind_when_it_is(world):
    k, a, b, ids = world
    out = run(k, a, 'find Seabright')
    assert 'nothing here is a' not in out['text']
    assert ids['build'] in found(out) and ids['map'] in found(out)
    assert found(run(k, a, 'find Seabright limit=2')) == found(out)[:2]
    assert {r['kind'] for r in run(k, a, 'find board-channel')['rows']} == {'board-channel'}
    assert 'search gizmo finds things' in run(k, a, 'rows gizmo')['text']   # rows itself still says so


def test_a_things_name_never_hijacks_the_word(world):
    """Seabright names the map (and the board); search must not become map.search or board.search."""
    k, a, b, ids = world
    out = run(k, a, 'search Seabright map')
    assert found(out)[0] in (ids['mapbutton'], ids['map'])
    assert ids['map'] in found(out)
    out = run(k, a, f"search {ids['map']}")                         # an id is words too: nothing has it as text
    assert out['rows'] == [] and 'nothing you can see has' in out['text']


def test_limit_kind_case_and_every_word_must_match(world):
    k, a, b, ids = world
    out = run(k, a, 'search SEABRIGHT limit=3')
    assert len(out['rows']) == 3 and 'limit=' in out['text']
    assert {r['kind'] for r in run(k, a, 'search seabright kind=button')['rows']} == {'button'}
    assert found(run(k, a, 'search seabright kind=task')) and all(
        r['kind'] == 'taskboard-task' for r in run(k, a, 'search seabright kind=task')['rows'])
    got = found(run(k, a, 'search seabright calendar'))
    assert got == [ids['cal']]
    run(k, a, 'search', ok=False)
    run(k, a, 'search seabright limit=lots', ok=False)


def test_search_shows_only_what_the_asker_may_see(world):
    k, a, b, ids = world
    assert ids['secret'] in found(run(k, a, 'search Seabright limit=50'))
    assert ids['secret'] not in found(run(k, b, 'search Seabright limit=50'))
    assert run(k, b, 'search surprise')['rows'] == []
    run(k, a, f"forget {ids['build']}")
    assert ids['build'] not in found(run(k, a, 'search Seabright limit=50'))


def test_help_names_search(world):
    k, a, b, ids = world
    assert 'search <words>' in run(k, a, 'help search')['text']
    assert 'search Seabright' in run(k, a, 'help')['text']
    assert 'searches as search does' in run(k, a, 'help rows')['text']
    assert run(k, a, 'board.search q=x', ok=False)        # still its own word (no module runs in this fixture)
