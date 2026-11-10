"""Crash/shutdown fixtures only: no model, live world, process kill or window."""
import json
import shlex
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from test_builders import manager as manager, state
from test_workers import Agent
import builders as B
import restart_recovery as R
import transport as T


def residents(b):
    owner, gm = Agent(), Agent()
    owner.person = 'dk99'
    gm.person, gm.name, gm.cfg = 'gm', 'Coordinator', {'role': 'general-manager'}
    b.h.agents = {'dk99': owner, 'gm': gm}
    b.session = lambda _: b.fixture_door
    return owner, gm


def test_restart_reconciles_safe_unknown_and_landing_and_repairs_cards(manager):
    b = manager
    owner, gm = residents(b)
    b.wake_cut_off()
    owner.woken.clear()
    gm.woken.clear()
    book = b.h.m.see('look "Agent Book"')
    cards = {}
    states = []
    for task, phase in [('safe', 'working'), ('unknown', 'uncertain'), ('landing', 'landing')]:
        s = dict(task=task, run='run-' + task, name=task, requester='dk99', phase=phase,
                 tree=str(b.repo), session='session-' + task, pid=0, activity=[],
                 updated='2020-01-01T00:00:00Z', effect_tracking=True, detail='lost result')
        if task == 'safe':
            s['last_words'] = 'The parser fix is in the tree; verify the empty input next.'
        if task == 'unknown':
            s.update(cut_phase='working', in_flight_effects={'tool-1': 'commandExecution'})
        if task == 'landing':
            s.update(land_attempt='attempt', land_step='publish', land_in_progress=True)
        b.states[task] = s
        b.save(s)
        states.append(s)
        cards[task] = dict(id=task, rev=1, build_run=s['run'], build='building',
                           build_phase='working', build_detail='worker running', lane='Now')
    b.h.m.see = lambda line, **kw: book if line == 'look "Agent Book"' else {
        'rows': [dict(cards[line[5:]])] if line.startswith('look ') and line[5:] in cards else []}
    def write(line, **kw):
        _, task, *facts = shlex.split(line)
        assert kw['saw'] == {task: cards[task]['rev']}
        cards[task].update(dict(f.split('=', 1) for f in facts))
        cards[task]['rev'] += 1
        return dict(ok=True)
    b.h.m.do = write
    b.off()  # graceful shutdown must persist the phase before any child exits
    assert states[0]['cut_phase'] == 'working'
    assert cards['safe']['build_phase'] == 'recovery-needed'
    again = B.Builders(b.h, b.repo)
    again.session = lambda _: SimpleNamespace(look=lambda task: dict(cards[task]))
    with patch.object(B.threading.Thread, 'start') as launch:
        again.wake_cut_off()
        again.wake_cut_off()
    assert launch.call_count == 1
    assert again.states['safe']['phase'] == 'preparing'
    assert again.states['unknown']['phase'] == 'uncertain'
    assert again.states['landing']['phase'] == 'blocked'
    assert cards['safe']['build_phase'] == 'preparing'
    assert cards['unknown']['build_phase'] == 'uncertain'
    assert cards['landing']['build_phase'] == 'blocked'
    assert len(owner.woken) == 1
    assert 'unknown' in owner.woken[0][0] and 'landing' in owner.woken[0][0]
    assert 'effects' in owner.woken[0][0]
    assert len(gm.woken) == 2
    assert 'house-restarted' in gm.woken[0][0]
    summary = gm.woken[1][0]
    assert 'house-reconciled' in summary and all(task in summary for task in cards)
    sent = {}
    again.run_worker = lambda s, prompt: sent.update(prompt=prompt, session=s['session'])
    again.resume(again.states['safe'])
    assert sent['session'] == 'session-safe'
    assert states[0]['last_words'] in sent['prompt']


def test_legacy_shutdown_blocked_worker_and_stale_working_card(manager):
    b = manager
    owner, gm = residents(b)
    b.wake_cut_off()
    owner.woken.clear()
    gm.woken.clear()
    s = state(b, 'blocked')
    s.update(detail=R.SHUTDOWN, session='session', pid=0,
             activity=[dict(what='working'), dict(what='said', text='Last checkpoint')])
    b.save(s)
    b.fixture_door.task.update(build='building', build_phase='working')
    again = B.Builders(b.h, b.repo)
    again.session = b.session
    with patch.object(B.threading.Thread, 'start') as launch:
        again.wake_cut_off()
    assert launch.call_count == 1
    assert again.states['dk1']['restart_context']['last_words'] == 'Last checkpoint'
    assert b.fixture_door.task['build_phase'] == 'preparing'
    assert not owner.woken and len(gm.woken) == 2


def test_ordinary_blocked_worker_repairs_stale_card_without_resuming(manager):
    owner, gm = residents(manager)
    s = state(manager, 'blocked')
    s['detail'] = 'review conflict'
    manager.fixture_door.task.update(build='building', build_phase='working')
    with patch.object(B.threading.Thread, 'start') as launch:
        manager.wake_cut_off()
    launch.assert_not_called()
    assert manager.fixture_door.task['build'] == 'blocked'
    assert manager.fixture_door.task['build_phase'] == 'blocked'


@pytest.mark.parametrize('extra,reason', [
    ({'in_flight_effects': {'x': 'commandExecution'}}, 'completion'),
    ({'effects_unknown': True}, 'unknown effects'),
    ({'cut_phase': 'reviewing'}, 'reviewing'),
    ({'session': ''}, 'session'),
    ({'handover': {'id': 'handoff'}}, 'ownership'),
    ({'effect_tracking': False, 'activity': [{'what': 'act'}]}, 'older worker'),
])
def test_unsafe_workers_wait_with_reason(manager, extra, reason):
    owner, gm = residents(manager)
    s = state(manager, 'recovery-needed')
    s.update(cut_phase='working', session='s', pid=0, effect_tracking=True)
    s.update(extra)
    with patch.object(B.threading.Thread, 'start') as launch:
        manager.wake_cut_off()
    launch.assert_not_called()
    assert reason in owner.woken[0][0]
    assert len(gm.woken) == 2


def test_live_process_and_held_card_do_not_resume(manager):
    owner, gm = residents(manager)
    s = state(manager, 'recovery-needed')
    s.update(cut_phase='working', session='s', pid=42)
    with patch.object(B, 'alive', return_value=True):
        assert 'process' in R.reason_to_wait(manager, s)
    manager.fixture_door.task['paused'] = 'yes'
    assert 'held' in R.reason_to_wait(manager, s)


def test_one_wake_failure_does_not_suppress_other_receipts_and_retries(manager):
    owner, gm = residents(manager)
    s = state(manager, 'recovery-needed')
    s.update(cut_phase='landing')
    deliver = owner.wake
    owner.wake = Mock(side_effect=RuntimeError('temporarily unavailable'))
    manager.wake_cut_off()
    assert len(gm.woken) == 2
    owner.wake = deliver
    manager.wake_cut_off()
    manager.wake_cut_off()
    assert len(owner.woken) == 1 and len(gm.woken) == 2


def test_pool_full_queues_and_shutdown_never_starts_queued_work(manager):
    residents(manager)
    s = state(manager, 'recovery-needed')
    s.update(cut_phase='working', session='s', pid=0)
    manager.full = lambda _: True
    with patch.object(B.threading.Thread, 'start') as launch:
        manager.wake_cut_off()
        assert s['queued_turn'] and s['phase'] == 'recovery-needed'
        manager.stopping = True
        manager.full = lambda _: False
        manager.start_queued()
        launch.assert_not_called()
        manager.stopping = False
        manager.start_queued()
        assert launch.call_count == 1


def test_guarded_shutdown_exit_preserves_interrupted_phase(manager):
    residents(manager)
    s = state(manager, 'working')
    manager.off()
    def exited(st):
        raise RuntimeError('worker exited without successful result: 1')
    manager.guarded(s, exited)
    assert s['phase'] == 'recovery-needed' and s['cut_phase'] == 'working'
    assert manager.fixture_door.task['build_phase'] == 'recovery-needed'


@pytest.mark.parametrize('provider', ['codex', 'claude'])
def test_effect_stream_correlates_without_persisting_arguments(provider):
    if provider == 'codex':
        start = dict(type='codex_event', method='item/started', data={'item': {
            'id': 'x', 'type': 'mcpToolCall', 'arguments': 'private'}})
        end = dict(type='codex_event', method='item/completed', data={'item': {
            'id': 'x', 'type': 'mcpToolCall', 'result': 'private'}})
    else:
        start = dict(type='assistant', message={'content': [
            dict(type='tool_use', id='x', name='Bash', input='private')]})
        end = dict(type='user', message={'content': [
            dict(type='tool_result', tool_use_id='x', content='private')]})
    events = T.effect_events(start) + T.effect_events(end)
    assert [e['e'] for e in events] == ['effect-started', 'effect-finished']
    assert events[0]['id'] == events[1]['id'] == 'x'
    assert 'private' not in json.dumps(events)


def test_durable_agent_wake_is_accepted_once_and_survives_busy_crash(manager):
    import house
    a = house.Agent.__new__(house.Agent)
    a.state, a.inbox, a.busy = {}, [], True
    a.lock = B.threading.RLock()
    a.state_path = manager.home / 'agent-state.json'
    a.wake_once('restart-1', 'House restarted')
    a.wake_once('restart-1', 'House restarted')
    disk = json.loads(a.state_path.read_text())
    assert len(a.inbox) == 1 and len(disk['durable_wakes']) == 1
    a.state, a.inbox = disk, []
    a.wake_once('restart-1', 'House restarted')
    assert not a.inbox  # replay suppressed; catch_up consumes the durable inbox
    a.house = SimpleNamespace()
    a._begin = Mock()
    h = house.House.__new__(house.House)
    h._catch_up = lambda agent: None
    h.catch_up(a)
    assert len(a.inbox) == 1 and a.inbox[0]['text'] == 'House restarted'


def test_shutdown_tool_without_completion_is_never_automatically_replayed(manager, tmp_path):
    residents(manager)
    s = state(manager, 'working')
    s.update(tree=str(tmp_path), chat='chat', session='s')
    class Child:
        def __init__(self, cmd, cwd, env, events, log, stderr=None):
            self.events, self.proc = events, SimpleNamespace(pid=0)
        def send(self, prompt):
            self.events.put(dict(e='turn_started', turn='turn'))
            self.events.put(dict(e='effect-started', id='tool', name='commandExecution'))
            self.events.put(dict(e='text', text='Checking the saved files.'))
            self.events.put(dict(e='exit', code=1))
            return True
        def stop(self):
            pass
    with patch.object(T, 'Child', Child):
        manager.guarded(s, lambda st: manager.run_worker(st, 'Continue'))
    assert s['in_flight_effects'] == {'tool': 'commandExecution'}
    assert s['last_words'] == 'Checking the saved files.'
    assert 'completion' in R.reason_to_wait(manager, s)
    with patch.object(B.threading.Thread, 'start') as launch:
        manager.wake_cut_off()
    launch.assert_not_called()


def test_bookkeeping_failure_retries_without_duplicate_wakes(manager):
    owner, gm = residents(manager)
    s = state(manager, 'recovery-needed')
    s['cut_phase'] = 'landing'
    update = manager.update
    manager.update = Mock(side_effect=RuntimeError('bookkeeping unavailable'))
    manager.wake_cut_off()
    assert s['restart_sync_pending']
    manager.update = update
    manager.deliver_outcomes()
    assert not s.get('restart_sync_pending')
    assert manager.fixture_door.task['build_phase'] == 'recovery-needed'
    assert len(owner.woken) == 1 and len(gm.woken) == 2


def test_completed_effects_and_a_second_restart_can_resume_again(manager):
    residents(manager)
    s = state(manager, 'working')
    s.update(session='s', pid=0, effect_tracking=True, in_flight_effects={})
    manager.off()
    for _ in range(2):
        again = B.Builders(manager.h, manager.repo)
        again.session = manager.session
        with patch.object(B.threading.Thread, 'start') as launch:
            again.wake_cut_off()
        assert launch.call_count == 1
        s = again.states['dk1']
        assert not s.get('cut_phase') and not s.get('restart_pending')
        again.phase(s, 'working', 'authenticated turn running')
        again.off()
        assert s['cut_phase'] == 'working'


def test_restart_during_reconciliation_completes_both_summaries(manager):
    owner, gm = residents(manager)
    s = state(manager, 'working')
    s.update(session='s', pid=0)
    manager.save(s)
    manager.recovery.announce()  # crash before classification/delivery
    again = B.Builders(manager.h, manager.repo)
    again.session = manager.session
    with patch.object(B.threading.Thread, 'start'):
        again.wake_cut_off()
        again.wake_cut_off()
    assert len(gm.woken) == 4  # one restart and one summary for each boot
    assert all(r['complete'] for r in again.recovery.records)


def test_missing_book_still_delivers_cards_and_reasons(manager):
    owner, gm = residents(manager)
    s = state(manager, 'recovery-needed')
    s['cut_phase'] = 'landing'
    see = manager.h.m.see
    manager.h.m.see = lambda line, **kw: {'rows': []} if line == 'look "Agent Book"' else see(line, **kw)
    manager.wake_cut_off()
    assert 'Message unavailable:' in owner.woken[0][0]
    assert '"card": "dk1"' in owner.woken[0][0] and 'effects need reconciliation' in owner.woken[0][0]
    assert len(gm.woken) == 2 and 'house-reconciled' in gm.woken[1][0]


def test_failed_tool_result_or_missing_correlation_is_not_proof_of_settled_effects():
    result = dict(type='codex_event', method='item/completed',
                  data={'item': dict(type='mcpToolCall', id='tool', status='failed', error='private')})
    event = T.effect_events(result)[0]
    assert event['e'] == 'effect-unknown' and 'private' not in json.dumps(event)
    result['data']['item'].pop('id')
    assert T.effect_events(result) == []
    assert T.effect_events(dict(type='user', message={'content': [
        dict(type='tool_result', tool_use_id='tool', is_error=True, content='private')]}))[0]['e'] == 'effect-unknown'


def test_possibly_live_parked_process_still_occupies_its_provider_slot(manager):
    s = state(manager, 'uncertain')
    s.update(pid=42, provider='codex')
    manager.capacity_for = lambda provider: 1
    with patch.object(B, 'alive', side_effect=lambda pid: pid == 42):
        assert manager.full('codex')
        assert not manager.full('claude')
