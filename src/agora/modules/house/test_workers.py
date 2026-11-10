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
        assert 'claude workers are busy' in manager.start(dict(msg('dk5'), args=dict(target='dk5', kv={'with': 'claude'})))['text']
        assert manager.states['dk5']['phase'] == 'queued'               # 4 Nov: it waits its turn, never refused
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
    assert chat is None and 'the dock unpins now' in text and 'house.tell dk1' in text and 'house.land dk1' in text


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


def test_no_turn_limit_unless_house_settings_sets_one(manager):
    s = state(manager); s['turns'] = 500                     # Alex, 4 Nov: no limit on a worker's turns
    manager.session = lambda person: manager.fixture_door
    with patch('builders.threading', SimpleNamespace(Thread=Mock())):
        assert manager.tell(dict(args=dict(target='dk1', words='more'), caller=dict(person='dk99'))).get('external')
    s = state(manager); s['turns'] = 3
    settings(manager, max_turns='3')
    out = manager.tell(dict(args=dict(target='dk1', words='more'), caller=dict(person='dk99')))
    assert '3 turns' in out['refused']


def test_worker_models_and_limits_come_from_house_settings(manager):
    assert manager.worker_model('codex') == ('gpt-6.1-sol', 'medium')          # no setting: the fallback
    assert manager.limit('worker_timeout') is None and manager.limit('max_turns') is None
    settings(manager, codex_model='gpt-6-astra', codex_reasoning='high', worker_timeout='0')
    assert manager.worker_model('codex') == ('gpt-6-astra', 'high')
    assert manager.limit('worker_timeout') is None                            # 0 means none
    settings(manager, codex_reasoning='enormous')
    assert manager.worker_model('codex')[1] == 'medium'                        # an unknown level falls back


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


# ---- dk1491 (Alex, dk1489): ownership is for being woken, not a lock on talking to a worker
def place(manager, **members):
    """A world where dk827 (JEFF) leads the place, plus any other members; the task card is the door's."""
    door = manager.fixture_door
    manager.session = lambda person: door
    previous = manager.h.m.see
    manager.h.m.see = lambda line, *a, **k: (dict(rows=[dict(id='dk1000', kind='place')]) if line == 'rows place' else
        dict(rows=[{'kind': 'place', 'member:dk827': 'leader', **{'member:' + p: r for p, r in members.items()}}])
        if line == 'look dk1000' else previous(line, *a, **k))
    return door


def told(person, name, words='carry on'):
    return dict(args=dict(target='dk1', words=words), caller=dict(person=person, name=name))


def test_a_steward_who_is_not_the_owner_tells_and_both_hear_the_reply(manager):
    s = state(manager); s['chat'] = 'dk50'; s['requester_name'] = 'Sable'; s['session'] = 'abc'
    place(manager)
    owner, jeff = Agent(), Agent(); jeff.name = 'JEFF'
    manager.h.agents = {'dk99': owner, 'dk827': jeff}
    with patch('builders.threading', SimpleNamespace(Thread=Mock())) as threads:
        out = manager.tell(told('dk827', 'JEFF', 'Add a test for the empty case'))
    assert out.get('external') and 'so are you' in out['text'] and threads.Thread.call_count == 1
    assert s['phase'] == 'preparing' and s['pending'][0].startswith('From JEFF (steward; Sable stays in charge): Add a test')
    assert s['requester'] == 'dk99'                                   # ownership did not move
    with manager.lock:
        manager.take_pending(s)                                       # the words reach the worker...
    manager.report_turn(s, 'Added it; 4 passed.')                      # ...and its turn ends
    assert 'Added it' in owner.woken[0][0] and 'You are in charge of this worker' in owner.woken[0][0]
    assert 'Added it' in jeff.woken[0][0] and 'Sable is woken too' in jeff.woken[0][0]
    manager.report_turn(s, 'Next turn, nobody else spoke.')
    assert len(jeff.woken) == 1 and len(owner.woken) == 2              # the teller hears only the turn it asked for


def test_the_cards_lead_may_tell_and_a_member_without_authority_may_not(manager):
    s = state(manager, 'working')
    door = place(manager, dk55='member', dk56='member')
    door.task['lead'] = 'Rowan'
    assert 'refused' in manager.tell(told('dk55', 'Someone'))
    assert 'refused' in manager.tell(told('dk56', ''))                 # no name never matches a lead
    assert not s.get('pending') and not s.get('told_by')
    out = manager.tell(told('dk56', 'rowan', 'use the new name'))
    assert out.get('external') and s['pending'] == ['From rowan (lead; your owner stays in charge): use the new name']
    assert any(a['what'] == 'lead' for a in s['activity'])


def test_alex_may_tell_any_worker(manager):
    s = state(manager, 'working'); s['requester'] = 'dk77'
    place(manager)
    out = manager.tell(told('dk99', 'Alex'))                          # dk99 is the desktop:alex account's person
    assert out.get('external') and s['pending'][0].startswith('From Alex (Alex;')


def test_attribution_reads_current_heading_and_names_a_missing_one(manager):
    s = state(manager, 'working')
    s['requester_name'] = 'Sable'
    place(manager)
    previous = manager.h.m.see
    book = ''
    manager.h.m.see = lambda line, **kw: (
        dict(rows=[dict(text=book)]) if line == 'look "Agent Book"' else previous(line, **kw))
    for version in ('Before', 'After'):
        book = f'### Follow-up from another person\n{version} $.name / $.role / $.owner / $.words'
        assert manager.tell(told('dk827', 'JEFF', 'Correction')).get('external')
        assert s['pending'][-1] == f'{version} JEFF / steward / Sable / Correction'
    book = '### Renamed\nOther'
    assert manager.tell(told('dk827', 'JEFF')).get('external')
    assert 'Agent Book / Follow-up from another person (missing or empty heading)' in s['pending'][-1]


def test_wordless_worker_renders_current_book_at_turn_end(manager, tmp_path):
    s = state(manager, 'preparing')
    s.update(chat='dk50', tree=str(tmp_path))
    manager.session = lambda person: manager.fixture_door
    manager.report_turn = Mock()
    previous = manager.h.m.see
    book = ''
    manager.h.m.see = lambda line, **kw: (
        dict(rows=[dict(text=book)]) if line == 'look "Agent Book"' else previous(line, **kw))

    class Child:
        def __init__(self, cmd, cwd, env, events, log, stderr=None):
            self.events, self.proc = events, SimpleNamespace(pid=1)
        def send(self, text):
            self.events.put(dict(e='result', ok=True))
            return True
        def stop(self):
            pass

    with patch.object(B.T, 'Child', Child):
        for version in ('Before', 'After'):
            book = f'### Worker ended without words\n{version} silent $.name'
            manager.run_worker(s, 'fixture')
            assert manager.report_turn.call_args.args[1] == f'{version} silent Codex fixture'
        book = '### Renamed\nOther'
        manager.run_worker(s, 'fixture')
        assert 'Agent Book / Worker ended without words (missing or empty heading)' in manager.report_turn.call_args.args[1]


def test_tell_resumes_a_blocked_builder_in_its_worktree(manager):
    s = state(manager, 'blocked'); s['detail'] = 'worker self-proof BUILD-RESULT.md is missing'; s['session'] = 'abc'
    place(manager)
    with patch('builders.threading', SimpleNamespace(Thread=Mock())) as threads:
        out = manager.tell(told('dk827', 'JEFF', 'Write BUILD-RESULT.md'))
    assert out.get('external') and 'was blocked' in out['text'], out
    assert s['phase'] == 'preparing' and threads.Thread.call_count == 1
    assert threads.Thread.call_args.kwargs['args'] == (s, manager.resume)
    assert any(a['what'] == 'reopened' and 'BUILD-RESULT.md is missing' in a['text'] for a in s['activity'])
    sent = {}
    manager.run_worker = lambda st, prompt: sent.update(prompt=prompt, tree=st['tree'], session=st['session'])
    manager.resume(s)
    assert 'Write BUILD-RESULT.md' in sent['prompt'] and sent['session'] == 'abc' and sent['tree'] == str(manager.repo)
    assert s['pending'] == [] and s['tellers'][0]['person'] == 'dk827'


def test_a_reviewed_builder_resumes_and_its_old_review_no_longer_stands(manager):
    s = state(manager, 'reviewed'); s.update(review_base='m1', candidate='c1', checks=[dict(returncode=0)], session='abc')
    manager.session = lambda person: manager.fixture_door
    with patch('builders.threading', SimpleNamespace(Thread=Mock())):
        assert manager.tell(dict(msg(), args=dict(target='dk1', words='one more fix'))).get('external')
    assert 'candidate' not in s and 'review_base' not in s and 'checks' not in s
    assert s['earlier_reviews'][0]['candidate'] == 'c1' and s['earlier_reviews'][0]['phase'] == 'reviewed'
    assert 'refused' in manager.land(msg())                            # nothing reviewed stands until review runs again


def test_a_builder_that_never_started_resumes_with_its_whole_task(manager):
    s = state(manager, 'blocked'); s['pending'] = ['go']               # no model thread yet, but a worktree
    manager.session = lambda person: manager.fixture_door
    sent = {}
    manager.run_worker = lambda st, prompt: sent.update(prompt=prompt)
    manager.resume(s)
    assert 'You are Codex fixture' in sent['prompt'] and sent['prompt'].rstrip().endswith('go')


@pytest.mark.parametrize('phase', ['landed', 'released', 'uncertain', 'recovery-needed', 'reviewing', 'landing'])
def test_tell_does_not_restart_finished_unsure_or_busy_work(manager, phase):
    s = state(manager, phase)
    manager.session = lambda person: manager.fixture_door
    with patch('builders.threading', SimpleNamespace(Thread=Mock())) as threads:
        assert 'refused' in manager.tell(dict(msg(), args=dict(target='dk1', words='more')))
    threads.Thread.assert_not_called()
    assert s['phase'] == phase and not s.get('pending')


def test_a_builder_blocked_before_its_worktree_points_to_retry(manager):
    s = state(manager, 'blocked'); s.pop('tree')
    manager.session = lambda person: manager.fixture_door
    assert 'house.retry' in manager.tell(dict(msg(), args=dict(target='dk1', words='more')))['refused']


def test_a_held_card_still_refuses_even_a_steward(manager):
    s = state(manager, 'blocked')
    door = place(manager)
    door.task['paused'] = 'yes'
    assert 'refused' in manager.tell(told('dk827', 'JEFF'))
    assert s['phase'] == 'blocked' and not s.get('told_by')
