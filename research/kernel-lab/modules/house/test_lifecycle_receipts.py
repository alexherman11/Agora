"""Lifecycle receipts, hidden fixtures only: no worker, model, window or live world."""
import json
import threading
import time
import sys
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch

import pytest
from test_builders import manager, msg, state  # noqa: F401
from test_builders import landing_repo
from test_workers import Agent
import builders as B


def owner(manager):
    agent = Agent()
    manager.h.agents = {'dk99': agent}
    manager.session = lambda _: manager.fixture_door
    return agent


@pytest.mark.parametrize('case', ['checks', 'merge', 'lock', 'success'])
def test_real_hidden_git_landing_ends_once(manager, monkeypatch, case):
    agent = owner(manager)
    s, base, candidate = landing_repo(manager, b'one\ntwo\nthree\n')
    tree = Path(s['tree'])
    (tree / 'BUILD-RESULT.md').write_text('hidden fixture')
    manager.activate = lambda st: st.update(activation='nothing needed restarting; it is live')
    expected = dict(checks='independent check failed', merge='shared.py',
                    lock='index.lock', success='it is live')[case]
    if case == 'checks':
        monkeypatch.setattr(B.T, 'PY', Path(sys.executable))
        s.update(phase='received', base=base)
        check = tree / '.hidden-check.py'
        check.write_text('def test_failure():\n    assert False, "hidden check failed"\n')
        monkeypatch.setattr(B, 'CHECKS', [[str(check)]])
    elif case == 'merge':
        s.update(phase='received', base=base)
        (manager.repo / 'shared.py').write_bytes(b'one\ntwo\nthree, main moved\n')
        manager.git(manager.repo, 'commit', '-qam', 'isolated main change')
    elif case == 'lock':
        # This is our fixture repository's lock, never the real repository's.
        (manager.repo / '.git/index.lock').write_text('fixture lock; keep intact')
    with patch.object(B.threading.Thread, 'start'):
        assert manager.land(msg()).get('external')
    began = time.monotonic()
    manager.guarded(s, manager.land_all)
    assert time.monotonic() - began < 60
    manager.deliver_outcomes()
    assert len(agent.woken) == 1 and expected in agent.woken[0][0]
    assert 'next' in s['land_receipt']
    assert s['phase'] == ('landed' if case == 'success' else 'blocked')
    if case == 'lock':
        assert (manager.repo / '.git/index.lock').read_text() == 'fixture lock; keep intact'
    if case != 'success':
        assert manager.git(manager.repo, 'rev-parse', 'HEAD') != candidate


@pytest.mark.parametrize('step,reason', [
    ('checks', 'independent check failed; see check-0.txt'),
    ('merge', 'main conflicts with this worker in painter.js'),
    ('publication', "Unable to create index.lock: File exists"),
])
def test_every_failed_land_wakes_once_with_step_reason_and_next_move(manager, step, reason):
    agent = owner(manager)
    s = state(manager)
    manager.git = lambda *a: 'main-sha'
    def review(st):
        st['land_step'] = step
        if step != 'publication':
            raise RuntimeError(reason)
    def publish(st):
        raise RuntimeError(reason)
    manager.review, manager.publish = review, publish
    with patch.object(B.threading.Thread, 'start'):
        assert manager.land(msg()).get('external')
    began = time.monotonic()
    manager.guarded(s, manager.land_all)
    assert time.monotonic() - began < 60
    manager.deliver_outcomes()
    manager.outcome(s)
    assert len(agent.woken) == 1
    text = agent.woken[0][0]
    assert step in text and reason in text and 'house.tell dk1' in text
    assert s['land_receipt']['step'] == step
    assert manager.fixture_door.task['build_phase'] == s['phase'] == 'blocked'
    # A second accepted landing that hits the same problem is a new end.
    with patch.object(B.threading.Thread, 'start'):
        manager.land(msg())
    manager.guarded(s, manager.land_all)
    assert len(agent.woken) == 2


def test_successful_land_wakes_once_after_activation(manager):
    agent = owner(manager)
    s = state(manager)
    manager.git = lambda *a: 'main-sha'
    manager.review = lambda st: st.update(candidate='candidate', phase='reviewed')
    manager.publish = lambda st: manager.phase(st, 'landed', 'source landed', landed_commit='candidate')
    manager.activate = lambda st: st.update(activation='nothing needed restarting; it is live')
    with patch.object(B.threading.Thread, 'start'):
        manager.land(msg())
    manager.guarded(s, manager.land_all)
    manager.outcome(s)
    manager.deliver_outcomes()
    assert len(agent.woken) == 1
    assert 'it is live' in agent.woken[0][0] and 'house.snap' in agent.woken[0][0]
    assert s['land_receipt']['step'] == 'activation'
    assert manager.fixture_door.task['build_phase'] == 'landed'


@pytest.mark.parametrize('failure', ['inspection', 'empty', 'launch'])
def test_activation_failure_never_says_the_landed_source_is_live(manager, monkeypatch, failure):
    s = state(manager, 'landed')
    s.update(land_attempt='attempt', land_step='activation', detail='source landed')
    agent = owner(manager)
    result = SimpleNamespace(returncode=1 if failure == 'inspection' else 0,
                             stdout='window: changed.py' if failure == 'launch' else '',
                             stderr='inspection unavailable')
    monkeypatch.setattr(B.subprocess, 'run', lambda *a, **kw: result)
    manager.spawn_reload = lambda *a: (_ for _ in ()).throw(RuntimeError('helper refused'))
    manager.guarded(s, manager.activate)
    assert s['phase'] == 'landed' and 'it is live' not in agent.woken[0][0]
    assert len(agent.woken) == 1 and s['land_receipt']['step'] == 'activation'


def test_failed_delivery_is_retried_and_diagnostic_failure_does_not_repeat_wake(manager):
    agent = owner(manager)
    s = state(manager, 'blocked')
    s.update(land_attempt='attempt', land_step='merge', detail='painter.js conflict')
    wake = agent.wake
    agent.wake = lambda *a: (_ for _ in ()).throw(RuntimeError('inbox unavailable'))
    manager.guarded(s, lambda _: None)
    assert s['outcome_pending'] and not s.get('last_outcome')
    agent.wake = wake
    event = manager.event
    def broken_diagnostic(st, what, text, *args):
        if what == 'told':
            raise RuntimeError('diagnostic unavailable')
        return event(st, what, text, *args)
    manager.event = broken_diagnostic
    manager.deliver_outcomes()
    manager.deliver_outcomes()
    assert len(agent.woken) == 1 and not s.get('outcome_pending')


def test_fallback_delivery_failure_does_not_wake_the_owner_twice(manager):
    agent = owner(manager)
    agent.state = {'error': 'temporarily unavailable'}
    gm = Agent()
    gm.name, gm.person = 'JEFF', 'dk827'
    manager.h.agents['dk827'] = gm
    s = state(manager, 'blocked')
    s.update(land_attempt='attempt', land_step='merge', detail='painter.js conflict')
    wake = gm.wake
    gm.wake = lambda *_: (_ for _ in ()).throw(RuntimeError('fallback inbox unavailable'))
    manager.guarded(s, lambda _: None)
    assert len(agent.woken) == 1 and s['outcome_pending']
    gm.wake = wake
    manager.deliver_outcomes()
    assert len(agent.woken) == len(gm.woken) == 1 and not s.get('outcome_pending')


def test_git_lock_during_merge_keeps_the_lock_reason_and_does_not_abort(manager):
    s = state(manager)
    s.update(land_attempt='attempt', land_step='checks')
    manager.repo.mkdir()
    (manager.repo / 'BUILD-RESULT.md').write_text('fixture')
    manager.assert_owned = lambda _: None
    manager.commit_worker = lambda *a: None
    calls = []
    def git(cwd, *args):
        calls.append(args)
        if args == ('rev-parse', 'main'):
            return 'new-main'
        if args[:2] == ('merge', '--no-edit'):
            raise RuntimeError('index.lock: File exists')
        return ''
    manager.git = git
    with pytest.raises(RuntimeError, match='index.lock'):
        manager.review(s)
    assert ('merge', '--abort') not in calls


def test_retained_tell_names_its_wait_and_wakes_once_when_the_turn_starts(manager):
    agent = owner(manager)
    s = state(manager, 'blocked')
    request = dict(msg(), args=dict(target='dk1', words='repair the conflict'))
    receipt = manager.tell(request, hold=True)
    assert 'until your turn ends' in receipt['text'] and 'slot is free' in receipt['text']
    assert agent.woken == []
    assert manager.take_pending(s) == ['repair the conflict']
    assert agent.woken == []                   # dequeuing alone is not proof it ran
    manager.followup_started(s)                # authenticated turn event
    manager.followup_started(s)
    assert len(agent.woken) == 1
    assert 'started the turn' in agent.woken[0][0]
    assert s['followup_receipt']['count'] == 1


def test_a_proven_start_refusal_has_no_run_and_tells_the_owner(manager):
    agent = owner(manager)
    manager.fixture_door.task['paused'] = 'yes'
    receipt = manager.start_request(dict(msg(), word='house.build'))
    assert 'refused' in receipt and not manager.states
    assert len(agent.woken) == 1 and receipt['refused'] in agent.woken[0][0]


def test_work_that_made_a_card_cannot_claim_nothing_was_done(manager):
    agent = owner(manager)
    call = manager.fixture_door.call
    manager.fixture_door.call = lambda route, line, **kw: (
        dict(ok=True, made=['dk1']) if line.startswith('make ') else call(route, line, **kw))
    manager.start = lambda _: {'refused': 'card changed before launch'}
    receipt = manager.start_request(dict(msg(), word='house.work'))
    assert receipt['external'] and 'refused' not in receipt
    assert 'made card dk1' in receipt['text'] and len(agent.woken) == 1


def test_start_delivery_failure_does_not_turn_a_settled_request_into_a_refusal(manager):
    agent = owner(manager)
    manager.work = lambda _: {'text': 'made card dk1; start unresolved', 'external': True}
    wake = agent.wake
    agent.wake = lambda *_: (_ for _ in ()).throw(RuntimeError('inbox unavailable'))
    out = manager.start_request(dict(msg(), word='house.work'))
    assert out['external'] and 'refused' not in out and manager.request_receipts
    agent.wake = wake
    manager.deliver_outcomes()
    manager.deliver_outcomes()
    assert len(agent.woken) == 1 and not manager.request_receipts


@pytest.mark.parametrize('word', ['house.build', 'house.work'])
def test_start_over_ten_seconds_returns_starting_then_reconciles_card(manager, word):
    """Real ten-second protocol deadline; blocked fake admission, no real worker."""
    from kernel.modules import Host, ModuleProcess, CALL_TIMEOUT
    from house import House
    agent = owner(manager)
    release, finished = threading.Event(), threading.Event()
    p = ModuleProcess.__new__(ModuleProcess)
    p.pending = {}
    host = Host.__new__(Host)
    host.kernel = SimpleNamespace(state=SimpleNamespace(get=lambda *a: 'House fixture'), name=lambda _: 'Alex')
    host.procs = {'house': p}
    p.host = host
    p.stdout_closed = threading.Event()
    house = House.__new__(House)
    house.ready = threading.Event()
    house.ready.set()
    house.builders = manager
    house.m = SimpleNamespace(accept=lambda m: p.handle(dict(t='accepted', use=m['use'])))
    request = dict(msg(), word=word)
    old_see = manager.h.m.see
    def see(line, **kw):
        if kw.get('use'):
            assert kw['use'] in p.pending   # original caller context survived the deadline
        return old_see(line, **kw)
    manager.h.m.see = see
    original = manager.start
    def slow_start(m):
        assert release.wait(CALL_TIMEOUT + 5)
        return original(m)
    manager.start = slow_start
    def fake_build(st):
        manager.fixture_door.task['build_run'] = st['run']
        manager.phase(st, 'working', 'fixture thread authenticated')
    manager.build = fake_build
    if word == 'house.work':
        request['args'] = dict(words='repair fixture')
        call = manager.fixture_door.call
        manager.fixture_door.call = lambda route, line, **kw: (
            dict(ok=True, made=['dk1']) if line.startswith('make ') else call(route, line, **kw))
    def send(message):
        if message['t'] != 'call':
            return
        def run():
            try:
                out = house.call(dict(request, use=message['use']))
                p.handle(dict(out, t='answer', use=message['use']))
            finally:
                finished.set()
        threading.Thread(target=run, daemon=True).start()
    p.send = send
    began = time.monotonic()
    receipt = host.call('house', word, request['args'], SimpleNamespace(id='agent', person='dk99'))
    assert time.monotonic() - began >= 10
    assert 'starting' in receipt['text'] and 'refused' not in receipt
    assert p.pending and not finished.is_set()
    release.set()
    assert finished.wait(5)
    deadline = time.monotonic() + 5
    while not manager.states['dk1'].get('start_receipt') and time.monotonic() < deadline:
        time.sleep(.01)
    late = manager.states['dk1']['start_receipt']
    card = manager.fixture_door.task
    assert late['build_run'] == card['build_run']
    assert late['build'] == card['build'] == 'building'
    assert late['build_phase'] == card['build_phase'] == 'working'
    assert len(agent.woken) == 1 and not p.pending
