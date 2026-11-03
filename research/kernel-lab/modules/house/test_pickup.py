"""Picking stopped work back up (Alex, 3 Nov: work sat for days, unattended or forgotten). One reminder per stopped
result, a wake when a review or landing ends, JEFF hears what nobody else can pick up, cut-off workers resume when
safe, and house.hand gives a worker to a resident. No live model, window or world."""
from types import SimpleNamespace
from unittest.mock import Mock, patch
import pytest
from test_builders import manager, msg, state       # noqa: F401  (fixture)
from test_workers import Agent, place
import builders as B


def test_an_owner_whose_turn_ends_without_acting_gets_one_reminder(manager):
    s = state(manager); s['chat'] = 'dk50'; s['requester_name'] = 'Sable'
    agent = Agent(); manager.h.agents = {'dk99': agent}
    manager.session = lambda person: manager.fixture_door
    manager.report_turn(s, 'Done; 3 passed.')
    assert len(agent.woken) == 1 and s.get('awaiting')
    manager.owner_turn_ended('dk99')                      # it took a turn and did nothing about the worker
    assert len(agent.woken) == 2 and 'Reminder' in agent.woken[1][0] and 'Codex fixture (dk1)' in agent.woken[1][0]
    manager.owner_turn_ended('dk99')                      # ...and only once
    assert len(agent.woken) == 2


def test_no_reminder_while_the_owner_still_has_wakes_queued_or_after_it_acted(manager):
    s = state(manager); s['chat'] = 'dk50'
    agent = Agent(); manager.h.agents = {'dk99': agent}
    manager.session = lambda person: manager.fixture_door
    manager.report_turn(s, 'Done.')
    agent.inbox = ['another wake']
    manager.owner_turn_ended('dk99')
    assert len(agent.woken) == 1                          # the first wake has not even been read yet
    agent.inbox = []
    with patch('builders.threading', SimpleNamespace(Thread=Mock())):
        assert manager.request_review(msg()).get('external')
    manager.owner_turn_ended('dk99')
    assert len(agent.woken) == 1 and 'awaiting' not in s


def test_a_finished_review_or_a_failure_wakes_the_owner(manager):
    s = state(manager, 'reviewed'); s['candidate'] = 'c0ffee123456'
    agent = Agent(); manager.h.agents = {'dk99': agent}
    manager.guarded(s, lambda st: None)
    assert 'passed its independent checks' in agent.woken[-1][0] and 'house.land dk1' in agent.woken[-1][0]
    assert 'house.snap' in agent.woken[-1][0]

    def fails(st):
        raise RuntimeError('main conflicts with this worker in house.py')
    manager.guarded(s, fails)
    assert s['phase'] == 'blocked' and 'main conflicts' in agent.woken[-1][0] and 'house.hand dk1' in agent.woken[-1][0]


def test_a_landing_asks_the_owner_to_check_it_and_tell_jeff(manager):
    s = state(manager, 'landed'); s.update(landed_commit='abc1234567', detail='source landed')
    agent = Agent(); manager.h.agents = {'dk99': agent}
    manager.guarded(s, lambda st: None)
    text = agent.woken[-1][0]
    assert 'landed on main (abc123456)' in text and 'tell JEFF in Shop talk' in text and 'looks good' in text


def test_work_nobody_can_pick_up_goes_to_jeff(manager):
    s = state(manager); s['chat'] = 'dk50'; s['requester'] = 'dk2'; s['requester_name'] = 'Alex'
    jeff = Agent(); jeff.name = 'JEFF'; jeff.person = 'dk827'
    manager.h.agents = {'dk827': jeff}
    manager.session = lambda person: manager.fixture_door
    manager.report_turn(s, 'Done.')                       # Alex asked for it: no resident to wake
    assert 'Nobody can pick this up' in jeff.woken[0][0] and 'house.hand dk1' in jeff.woken[0][0]
    down = Agent(); down.state = {'error': 'Failed to authenticate: OAuth session expired'}; down.person = 'dk99'
    manager.h.agents = {'dk99': down, 'dk827': jeff}
    s['requester'] = 'dk99'
    manager.report_turn(s, 'Done again.')                 # its owner's sign-in expired
    assert 'OAuth session expired' in jeff.woken[-1][0] and down.woken     # it still reads it when it is back


def test_a_worker_cut_off_mid_turn_resumes_once_its_process_is_gone(manager):
    s = state(manager, 'recovery-needed'); s.update(cut_phase='working', session='abc', pid=0)
    manager.session = lambda person: manager.fixture_door
    with patch('builders.threading', SimpleNamespace(Thread=Mock())) as threads:
        out = manager.tell(dict(msg(), args=dict(target='dk1', words='carry on from where you were')))
    assert out.get('external') and s['phase'] == 'preparing' and threads.Thread.call_count == 1
    sent = {}
    manager.run_worker = lambda st, prompt: sent.update(prompt=prompt)
    manager.resume(s)
    assert 'cut off mid-turn' in sent['prompt'] and 'carry on from where you were' in sent['prompt']


@pytest.mark.parametrize('cut', ['reviewing', 'landing', None])
def test_a_worker_cut_off_mid_review_or_landing_is_not_resumed(manager, cut):
    s = state(manager, 'recovery-needed'); s['pid'] = 0
    if cut:
        s['cut_phase'] = cut
    manager.session = lambda person: manager.fixture_door
    with patch('builders.threading', SimpleNamespace(Thread=Mock())) as threads:
        assert 'refused' in manager.tell(dict(msg(), args=dict(target='dk1', words='more')))
    threads.Thread.assert_not_called()


def test_a_cut_off_worker_whose_process_still_runs_is_not_run_twice(manager, monkeypatch):
    s = state(manager, 'recovery-needed'); s.update(cut_phase='working', pid=4242)
    monkeypatch.setattr(B, 'alive', lambda pid: True)
    manager.session = lambda person: manager.fixture_door
    assert 'may still be running' in manager.tell(dict(msg(), args=dict(target='dk1', words='more')))['refused']


def test_a_dead_pid_is_not_alive_and_this_process_is():
    import os
    assert B.alive(os.getpid()) and not B.alive(0) and not B.alive(None)


def test_the_house_start_tells_each_owner_once_about_cut_off_workers(manager):
    s = state(manager, 'recovery-needed'); s.update(cut_phase='working', pid=0)
    agent = Agent(); agent.person = 'dk99'; manager.h.agents = {'dk99': agent}
    manager.wake_cut_off()
    manager.wake_cut_off()
    assert len(agent.woken) == 1 and 'cut these workers off' in agent.woken[0][0]
    assert 'house.tell dk1' in agent.woken[0][0] and s.get('awaiting')


def test_workers_on_finished_cards_nag_nobody(manager):
    s = state(manager, 'recovery-needed'); s.update(cut_phase='working', pid=0)
    manager.fixture_door.task['lane'] = 'Done'
    agent = Agent(); agent.person = 'dk99'; manager.h.agents = {'dk99': agent}
    manager.wake_cut_off()
    s['awaiting'] = 'then'
    manager.owner_turn_ended('dk99')
    assert agent.woken == []


def test_words_for_a_worker_whose_card_moved_on_are_dropped_not_looped(manager):
    """3 Nov, live: a worker whose card claim had moved kept its words, so every JEFF turn end resumed it, it blocked,
    the block woke JEFF, and round again (33 times). Now the words are dropped and the same block wakes nobody twice."""
    s = state(manager, 'blocked'); s.update(pending=['carry on'], detail='task claim changed or is held')
    manager.fixture_door.task['build_run'] = 'someone-elses-run'
    agent = Agent(); agent.person = 'dk99'; manager.h.agents = {'dk99': agent}
    with patch('builders.threading', SimpleNamespace(Thread=Mock())) as threads:
        manager.owner_turn_ended('dk99')
    threads.Thread.assert_not_called()
    assert s['pending'] == [] and s['phase'] == 'blocked'
    assert any(a['what'] == 'dropped' for a in s['activity'])
    manager.outcome(s)
    manager.outcome(s)
    assert len([w for w in agent.woken if 'stopped (blocked)' in w[0]]) == 1


def test_older_runs_say_what_they_were_cut_off_doing():
    def cut(*whats):
        return B.Builders.cut_phase(SimpleNamespace(), dict(activity=[dict(what=w) for w in whats]))
    assert cut('preparing', 'act', 'said') == 'working'
    assert cut('received', 'reviewing') == 'reviewing' and cut('reviewing', 'reviewed') == 'landing'
    assert cut() is None


def test_jeff_hands_a_worker_to_a_resident_who_is_in_charge_from_then_on(manager):
    s = state(manager, 'received')
    s.update(chat='dk50', requester='dk827', requester_name='JEFF', task_owner='JEFF', last_words='Done; 3 passed.',
             session='abc', basis=dict(title='Repair', text='original', acceptance='', who='JEFF'))
    door = place(manager)
    door.task['who'] = 'JEFF'
    jeff, sable = Agent(), Agent()
    jeff.name, jeff.person, sable.person = 'JEFF', 'dk827', 'dk99'
    manager.h.agents = {'dk827': jeff, 'dk99': sable}
    out = manager.hand(dict(args=dict(target='dk1', words='@Sable'), caller=dict(person='dk827', name='JEFF')))
    assert out.get('external'), out
    assert s['requester'] == 'dk99' and s['requester_name'] == 'Sable' and s['task_owner'] == 'Sable'
    assert door.task['who'] == 'Sable' and door.task['lead'] == 'Sable' and s['basis']['who'] == 'Sable'
    assert any(w[1].startswith('make kind=chat') and 'with=dk99' in w[1] for w in door.writes)
    assert 'handed you the worker' in sable.woken[0][0] and 'Done; 3 passed.' in sable.woken[0][0]
    # Sable now answers it, and the worker hears who is in charge of it
    with patch('builders.threading', SimpleNamespace(Thread=Mock())):
        assert manager.tell(dict(args=dict(target='dk1', words='Add the empty case'),
                                 caller=dict(person='dk99', name='Sable'))).get('external')
    sent = {}
    manager.run_worker = lambda st, prompt: sent.update(prompt=prompt)
    manager.resume(s)
    assert 'Sable is in charge of you' in sent['prompt'] and 'Add the empty case' in sent['prompt']


def test_the_card_is_moved_by_whoever_may_set_it(manager):
    """Live, 3 Nov: a resident may not set a card it did not make, so JEFF (who leads the desktop) moves it."""
    s = state(manager, 'received'); s.update(chat='dk50', requester='dk60', requester_name='Rowan', task_owner='Rowan')
    door = place(manager)
    tried = []

    class Session:
        def __init__(self, person):
            self.person, self.token = person, 'fixture'
        def look(self, target):
            return door.look(target)
        def call(self, route, line, **kw):
            if line.startswith('set '):
                tried.append(self.person)
                if self.person != 'dk827':
                    raise RuntimeError('refused: set is for whoever made it or leaders')
            return door.call(route, line, **kw)
    manager.session = Session
    sable = Agent(); sable.person = 'dk99'
    manager.h.agents = {'dk99': sable}
    out = manager.hand(dict(args=dict(target='dk1', words='Sable'), caller=dict(person='dk827', name='JEFF')))
    assert out.get('external'), out
    assert tried == ['dk827'] and door.task['who'] == 'Sable' and s['requester'] == 'dk99'
    manager.h.agents['dk827'] = Agent()
    s.update(requester='dk99', requester_name='Sable')
    out = manager.hand(dict(args=dict(target='dk1', words='JEFF'), caller=dict(person='dk55', name='Rowan')))
    assert 'only' in out['refused']                       # a stranger still may not


def test_hand_refuses_strangers_unknown_names_and_running_workers(manager):
    s = state(manager, 'working'); s.update(requester='dk827', requester_name='JEFF')
    place(manager, dk55='member')
    sable = Agent(); sable.person = 'dk99'
    manager.h.agents = {'dk99': sable}

    def hand(person, name, who):
        return manager.hand(dict(args=dict(target='dk1', words=who), caller=dict(person=person, name=name)))
    assert 'only' in hand('dk55', 'Someone', 'Sable')['refused']
    assert 'not a House agent' in hand('dk827', 'JEFF', 'Nobody')['refused']
    assert 'once it stops' in hand('dk827', 'JEFF', 'Sable')['refused']


def test_a_worker_keeps_its_temp_folder_inside_its_worktree(manager):
    s = state(manager); s['chat'] = 'dk50'
    manager.repo.mkdir(parents=True, exist_ok=True)
    manager.session = lambda person: manager.fixture_door
    seen = {}

    class Child:
        def __init__(self, cmd, cwd, env, *a, **k):
            seen.update(env=env)
            raise RuntimeError('stop here')
    with patch.object(B.T, 'Child', Child), pytest.raises(RuntimeError, match='stop here'):
        manager.run_worker(s, 'go')
    assert seen['env']['TMP'] == str(manager.repo / '.tmp') == seen['env']['TEMP'] == seen['env']['TMPDIR']
