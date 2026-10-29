"""Residents run workers (Alex, 28 Oct): four Claude and four Codex at once, started by `work`, steered by talking in
the worker's chat. No live model, window or world."""
from types import SimpleNamespace
from unittest.mock import Mock, patch
import queue
import pytest
from test_builders import manager, msg, state
import builders as B


class Agent:
    def __init__(self, busy=False):
        self.busy, self.woken, self.name, self.inbox = busy, [], 'Sable', []
    def wake(self, text, chat=None, record=None):
        self.woken.append((text, chat))


def settings(b, **row):
    old = b.h.m.see
    b.h.m.see = lambda line, *a, **k: dict(rows=[dict(kind='house-settings', **row)]) if line == 'rows house-settings' else old(line, *a, **k)


def test_each_kind_has_its_own_pool_of_four(manager):
    assert manager.capacity_for('claude') == 4 and manager.capacity_for('codex') == 4
    settings(manager, claude_workers=2, builder_capacity=3)
    assert manager.capacity_for('claude') == 2 and manager.capacity_for('codex') == 3
    settings(manager, codex_workers=1, builder_capacity=3)
    assert manager.capacity_for('codex') == 1


def test_claude_and_codex_pools_fill_separately(manager):
    with patch('builders.threading', SimpleNamespace(Thread=Mock())):
        for i, t in enumerate(('dk1', 'dk2', 'dk3', 'dk4')):
            assert manager.start(dict(msg(t), args=dict(target=t, kv={'with': 'claude'}))).get('external')
        assert 'claude workers are busy' in manager.start(dict(msg('dk5'), args=dict(target='dk5', kv={'with': 'claude'})))['refused']
        assert manager.start(msg('dk6')).get('external')            # a Codex worker still starts
    s = manager.states['dk1']
    assert s['provider'] == 'claude' and s['model'] == 'claude-opus-5-5' and s['name'].startswith('Claude — ')
    assert manager.states['dk6']['provider'] == 'codex'


def test_work_makes_a_card_in_the_callers_charge_and_starts_a_worker(manager):
    made = []
    door = manager.fixture_door
    real = door.call
    def call(route, line, **kw):
        if line.startswith('make '):
            made.append(line)
            return dict(ok=True, made=['dk1'])
        return real(route, line, **kw)
    door.call = call
    manager.session = lambda person: door
    with patch('builders.threading', SimpleNamespace(Thread=Mock())):
        out = manager.work(dict(args=dict(target=None, words='Fix the dock unpin bug', kv={'with': 'claude'}),
                                caller=dict(person='dk99', name='Sable'), use='fixture'))
    assert out.get('external'), out
    assert 'title="Fix the dock unpin bug"' in made[0] and 'who="Sable"' in made[0] and 'lead="Sable"' in made[0]
    assert manager.states['dk1']['provider'] == 'claude' and manager.states['dk1']['requester_name'] == 'Sable'


def test_work_is_only_for_people_with_a_worker_session(manager):
    out = manager.work(dict(args=dict(words='anything'), caller=dict(person='dk98', name='Someone'), use='fixture'))
    assert 'only Alex, JEFF and the residents' in out['refused']


def test_a_finished_turn_goes_to_the_chat_and_wakes_the_resident_there(manager):
    s = state(manager); s['chat'] = 'dk50'; s['turns'] = 1
    agent = Agent(); manager.h.agents = {'dk99': agent}
    manager.session = lambda person: manager.fixture_door
    manager.report_turn(s, 'Done: the dock unpins now. Tests: 3 passed.')
    said = [w for w in manager.fixture_door.writes if w[1].startswith('say dk50 ')]
    assert said and 'the dock unpins now' in said[0][1]
    text, chat = agent.woken[0]
    assert chat is None and 'the dock unpins now' in text and 'house.tell dk1' in text and 'house.review dk1' in text


def test_what_the_resident_says_during_its_turn_starts_the_worker_after_it(manager):
    s = state(manager); s['chat'] = 'dk50'
    agent = Agent(busy=True); manager.h.agents = {'dk99': agent}
    door = manager.fixture_door
    real = door.call
    # the worker's chat is closed to the House: only the resident's own session reads the line
    door.call = lambda route, line, **kw: dict(ok=True, rows=[dict(chat='dk50', made_by='dk99', text='Now add a test')]) \
        if line == 'look dk60' else real(route, line, **kw)
    manager.session = lambda person: door
    manager.h.m.see = lambda line, *a, **k: dict(rows=[]) if line.startswith('look dk60') else dict(rows=[dict(door.task)])
    with patch('builders.threading', SimpleNamespace(Thread=Mock())) as threads:
        manager.hear(dict(word='say', said='dk61', by_id='dk77'))      # someone else's line is never read
        assert not any(w[1] == 'look dk61' for w in door.writes)
        manager.hear(dict(word='say', said='dk60', by_id='dk99'))
        assert s['pending'] == ['Now add a test'] and s['phase'] == 'received'
        threads.Thread.assert_not_called()
        manager.owner_turn_ended('dk99')
        assert s['phase'] == 'preparing' and threads.Thread.call_count == 1


def test_asking_for_review_drops_what_was_said_in_the_same_turn(manager):
    s = state(manager); s['pending'] = ['thanks!']
    manager.session = lambda person: manager.fixture_door
    with patch('builders.threading', SimpleNamespace(Thread=Mock())):
        assert manager.request_review(msg()).get('external')
    assert s['pending'] == [] and s['phase'] == 'reviewing'


def test_a_worker_has_at_most_its_turns(manager):
    s = state(manager); s['turns'] = B.MAX_TURNS
    manager.session = lambda person: manager.fixture_door
    out = manager.tell(dict(args=dict(target='dk1', words='more'), caller=dict(person='dk99')))
    assert f'{B.MAX_TURNS} turns' in out['refused']


def test_a_claude_worker_runs_the_claude_cli_in_its_worktree(manager, tmp_path):
    s = state(manager, 'preparing'); s.update(provider='claude', model='claude-opus-5-5', chat='dk50', tree=str(tmp_path))
    manager.session = lambda person: manager.fixture_door
    seen = {}
    class Child:
        def __init__(self, cmd, cwd, env, events, log, stderr=None):
            seen['cmd'], seen['cwd'] = cmd, cwd
            self.events, self.proc = events, SimpleNamespace(pid=1)
        def send(self, text):
            seen['prompt'] = text
            self.events.put(dict(e='init', session='abc'))
            self.events.put(dict(e='text', text='All done, 2 tests pass.'))
            self.events.put(dict(e='result', ok=True))
            return True
        def stop(self): pass
    with patch.object(B.T, 'Child', Child), patch.object(B.T, 'find_claude', lambda: 'claude.exe'):
        manager.run_worker(s, 'do it')
    cmd = seen['cmd']
    assert cmd[0] == 'claude.exe' and '--permission-mode' in cmd and 'acceptEdits' in cmd
    assert 'Bash(git push:*)' in cmd[cmd.index('--disallowedTools') + 1]
    assert str(seen['cwd']) == str(tmp_path) and s['session'] == 'abc' and s['phase'] == 'received'
    assert any('All done' in w[1] for w in manager.fixture_door.writes if w[1].startswith('say dk50'))


def test_titles_end_on_a_whole_word():
    title = B.short('Write WORKERS.md, a one page guide for residents on running workers', 50)
    assert title.endswith('…') and not title[:-1].endswith(('on r', ' r')) and len(title) <= 50
    assert B.short('a b c d e f g h i j k l m n o p', 10) == 'a b c d…'
    assert B.short('short', 10) == 'short'


def test_a_steward_may_unstick_anyones_worker_and_others_may_not(manager):
    s = state(manager)                                   # requested by dk99
    manager.session = lambda person: manager.fixture_door
    task_row = dict(manager.fixture_door.task)
    manager.h.m.see = lambda line, *a, **k: (dict(rows=[dict(id='dk1000', kind='place')]) if line == 'rows place' else
        dict(rows=[{'kind': 'place', 'member:dk827': 'leader', 'member:dk55': 'member'}]) if line == 'look dk1000' else
        dict(rows=[task_row]))
    jeff = dict(args=dict(target='dk1', words='carry on'), caller=dict(person='dk827', name='JEFF'))
    other = dict(args=dict(target='dk1', words='carry on'), caller=dict(person='dk55', name='Someone'))
    assert 'refused' in manager.tell(other)
    with patch('builders.threading', SimpleNamespace(Thread=Mock())):
        assert manager.tell(jeff).get('external')
    assert any(a['what'] == 'steward' for a in s['activity'])


def test_nothing_the_house_starts_can_reach_the_live_keeper(monkeypatch):
    monkeypatch.setenv('AGORA_KEEPER', '1234 secret')
    assert 'AGORA_KEEPER' not in B.T.clean_env()
    assert 'AGORA_KEEPER' not in B.T.clean_env('off')
