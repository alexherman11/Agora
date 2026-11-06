"""Ghost landing regression: fixture doors, local children, no models or desktop."""
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
from unittest.mock import Mock, patch

import pytest
import builders as B
import landing_control as L
from test_builders import manager, msg, state  # noqa: F401
from test_workers import Agent
from test_handover import world  # noqa: F401


def setup(manager):
    s = state(manager)
    manager.session = lambda _: manager.fixture_door
    manager.h.agents = {'dk99': Agent()}
    manager.start_queued = lambda: None
    manager.idle_check = lambda: None
    manager.settings = lambda: dict(landing_timeout=3, landing_wait_timeout=0.1)
    return s


def admit(manager):
    with patch.object(B.threading.Thread, 'start'):
        return manager.land(msg())


def test_started_receipt_precedes_thread_and_duplicate_keeps_attempt(manager):
    s = setup(manager)
    out = admit(manager)
    saved = json.loads((manager.home / s['run'] / 'state.json').read_text())
    assert out['rows'][0]['attempt'] == saved['land_attempt']
    assert saved['land_step'] == 'started'
    assert saved['activity'][-1]['what'] == 'started'
    assert manager.land(msg())['rows'][0]['attempt'] == saved['land_attempt']


def test_repeated_attempts_retain_each_terminal_receipt(manager):
    s = setup(manager)
    manager.land_all = Mock(side_effect=RuntimeError('same failure'))
    attempts = []
    for _ in range(2):
        attempts.append(admit(manager)['rows'][0]['attempt'])
        manager.run_landing(s)
    saved = json.loads((manager.home / s['run'] / 'state.json').read_text())
    assert len(set(attempts)) == 2
    assert all(saved['land_attempts'][attempt]['phase'] == 'blocked' for attempt in attempts)
    assert len(manager.h.agents['dk99'].woken) == 2


def test_pending_notice_cannot_wake_a_mid_landing_reviewed_result(manager):
    s = setup(manager)
    admit(manager)
    s.update(phase='reviewed', outcome_pending=True)
    manager.deliver_outcomes()
    assert not manager.h.agents['dk99'].woken
    manager.land_all = Mock(side_effect=RuntimeError('publication failed'))
    manager.run_landing(s)
    assert len(manager.h.agents['dk99'].woken) == 1
    assert 'publication failed' in manager.h.agents['dk99'].woken[0][0]


def test_dk1156_shape_refused_owner_write_is_not_a_ghost(manager):
    """A steward can request land, but saved owner lacks card-write rights.

    Duplicate chats, a stale card and desktop suite never reach review: the
    first ownership/card update is the failing boundary.
    """
    s = setup(manager)
    manager.fixture_door.task.update(build='landing', build_phase='received', builder_chat='dk2530',
        test_suites=json.dumps([dict(name='Hidden real drag', runner='python',
                                    paths=['hidden_real_drag.py'], timeout=180, desktop=True)]))
    manager.fixture_door.call = Mock(side_effect=B.DoorRefused('set is for its maker or lead'))
    manager.review = Mock()
    manager.activate = Mock()
    attempt = admit(manager)['rows'][0]['attempt']
    manager.run_landing(s)
    assert s['phase'] == 'blocked'
    assert 'set is for its maker or lead' in s['detail']
    assert s['land_receipt']['attempt'] == attempt
    assert manager.row(s)['land_sync_error']
    assert s['land_sync_pending']
    assert len(manager.h.agents['dk99'].woken) == 1
    assert attempt in manager.h.agents['dk99'].woken[0][0]
    manager.review.assert_not_called()
    manager.activate.assert_not_called()
    assert manager.landing_lock.acquire(blocking=False)
    manager.landing_lock.release()


def test_real_kernel_owner_mismatch_wakes_owner_and_requesting_steward(world):
    b, s, old, new = world.b, world.s, world.old, world.new
    # Card remains owned by the steward; saved worker requester is another person.
    s.update(requester=new, requester_name='Recipient')
    b.start_queued = lambda: None
    b.idle_check = lambda: None
    b.review = Mock()
    with patch.object(B.threading.Thread, 'start'):
        out = b.land(dict(args=dict(target=s['task']), caller=dict(person=old, name='Owner')))
    assert out.get('external'), out
    b.run_landing(s)
    assert s['phase'] == 'blocked'
    assert 'refused' in s['land_sync_error']
    assert b.session(old).look(s['task']).get('land_attempt') is None
    assert len(b.h.agents[new].woken) == len(b.h.agents[old].woken) == 1
    assert s['land_attempt'] in b.h.agents[old].woken[0][0]
    b.review.assert_not_called()


@pytest.mark.parametrize('error', [RuntimeError('broken'), TimeoutError('door timed out'),
                                  SystemExit('thread exited')])
def test_every_thread_failure_settles_and_wakes(manager, error):
    s = setup(manager)
    admit(manager)
    manager.land_all = Mock(side_effect=error)
    manager.run_landing(s)
    assert s['phase'] == 'blocked' and str(error) in s['detail']
    assert manager.fixture_door.task['build_phase'] == 'blocked'
    assert len(manager.h.agents['dk99'].woken) == 1
    assert not manager.land_controls


def test_thread_launch_failure_is_saved_and_tick_delivers(manager):
    s = setup(manager)
    with patch.object(B.threading.Thread, 'start', side_effect=RuntimeError('no threads')):
        out = manager.land(msg())
    assert out['rows'][0]['phase'] == 'blocked'
    manager.deliver_outcomes()
    assert 'no threads' in manager.h.agents['dk99'].woken[0][0]
    assert manager.fixture_door.task['build_phase'] == 'blocked'


def test_control_setup_failure_still_has_a_started_attempt_and_wake(manager):
    s = setup(manager)
    with patch.object(L, 'Control', side_effect=OSError('control defaults unavailable')):
        out = manager.land(msg())
    assert out['rows'][0]['phase'] == 'blocked'
    assert any(e['what'] == 'started' for e in s['activity'])
    manager.deliver_outcomes()
    assert 'control defaults unavailable' in manager.h.agents['dk99'].woken[0][0]


@pytest.mark.parametrize('phase', ['reviewing', 'landing', 'landed'])
def test_restart_recovers_attempt_even_during_activation(manager, phase):
    s = setup(manager)
    admit(manager)
    s.update(phase=phase, land_step='activation' if phase == 'landed' else 'checks')
    manager.save(s)
    recovered = B.Builders(manager.h, manager.repo)
    s = recovered.states[s['task']]
    assert s['phase'] == 'blocked' and s['outcome_pending']
    assert 'House restarted' in s['land_receipt']['reason']
    recovered.session = lambda _: manager.fixture_door
    recovered.deliver_outcomes()
    assert len(manager.h.agents['dk99'].woken) == 1
    assert manager.fixture_door.task['build_phase'] == 'blocked'


@pytest.mark.parametrize('lock_name', ['landing_queue_lock', 'git_lock'])
def test_stuck_lock_wait_is_bounded_and_never_releases_someone_elses_lock(manager, lock_name):
    s = setup(manager)
    admit(manager)
    lock = getattr(manager, lock_name)
    lock.acquire()
    try:
        before = time.monotonic()
        manager.run_landing(s)
        assert time.monotonic() - before < 2
        assert s['phase'] == 'blocked' and 'landing_wait_timeout' in s['detail']
        assert lock.locked()
    finally:
        lock.release()
    assert manager.landing_lock.acquire(blocking=False)
    manager.landing_lock.release()


def test_review_does_not_hold_import_publication_lock(manager):
    s = setup(manager)
    admit(manager)
    manager.git = lambda *_: 'main'
    def review(st):
        assert manager.landing_lock.acquire(blocking=False)
        manager.landing_lock.release()
        st.update(phase='reviewed', candidate='candidate', review_base='main')
    manager.review = review
    def publish(st):
        assert manager.landing_lock.locked()
        st.update(phase='landed', landed_commit='candidate')
    manager.publish = publish
    manager.activate = Mock()
    manager.run_landing(s)
    assert s['phase'] == 'landed'
    manager.activate.assert_called_once()


def test_only_steward_can_cancel_and_cancel_before_publication_cannot_publish(manager):
    s = setup(manager)
    admit(manager)
    manager.steward = lambda person: person == 'dk99'
    manager.alex = lambda _: False
    assert 'refused' in manager.cancel_landing(msg(person='dk98'))
    assert manager.cancel_landing(msg())['rows'][0]['cancellation'] == 'requested'
    manager.publish = Mock()
    manager.run_landing(s)
    assert s['phase'] == 'blocked' and 'cancelled by Alex' in s['detail']
    manager.publish.assert_not_called()
    assert len(manager.h.agents['dk99'].woken) == 1


def test_cancel_after_publication_keeps_commit_and_does_not_activate(manager):
    s = setup(manager)
    admit(manager)
    manager.git = lambda *_: 'main'
    manager.review = lambda st: st.update(phase='reviewed')
    def publish(st):
        st.update(phase='landed', landed_commit='published')
        manager.land_controls[st['task']].cancel('fixture cancellation')
    manager.publish = publish
    manager.activate = Mock()
    manager.run_landing(s)
    assert s['phase'] == 'blocked' and s['landed_commit'] == 'published'
    assert s['land_receipt']['landed_commit'] == 'published'
    manager.activate.assert_not_called()


def test_total_deadline_stops_child_tree_and_wakes(manager):
    s = setup(manager)
    manager.settings = lambda: dict(landing_timeout=0.2, landing_wait_timeout=0.1)
    admit(manager)
    proc = Mock(pid=43210, args=['fixture child'])
    proc.wait.side_effect = [subprocess.TimeoutExpired('fixture', 30)] * 3 + [0]
    proc.poll.return_value = None
    def slow(st):
        manager.land_context.control.run([sys.executable, '-B', '-c', 'import time; time.sleep(30)'],
            timeout=30, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=B.T.NO_WINDOW)
    manager.land_all = slow
    def tick(*args, **kwargs):
        manager.land_context.control.deadline = 0
        return proc
    with patch.object(L.subprocess, 'Popen', side_effect=tick), \
            patch.object(L.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)) as kill:
        def stopped(**kwargs):
            proc.poll.return_value = 0
            return 0
        proc.wait.side_effect = stopped
        manager.run_landing(s)
    assert s['phase'] == 'blocked' and 'landing_timeout' in s['detail']
    if sys.platform == 'win32':
        assert kill.call_args.args[0] == ['taskkill', '/T', '/F', '/PID', '43210']
    else:
        proc.kill.assert_called_once()
    assert 'land_child_pid' not in s
    assert len(manager.h.agents['dk99'].woken) == 1


@pytest.mark.skipif(sys.platform != 'win32', reason='Windows process-tree boundary')
def test_denied_child_stop_reports_promptly_and_keeps_mutation_fenced(manager):
    s = setup(manager)
    admit(manager)
    exited = threading.Event()
    proc = Mock(pid=43210, args=['fixture child'])
    proc.poll.side_effect = lambda: 0 if exited.is_set() else None
    proc.wait.side_effect = lambda **kw: exited.wait(2)
    def spawn(*args, **kwargs):
        manager.land_context.control.deadline = 0
        return proc
    def slow(st):
        control = manager.land_context.control
        with control.acquire(manager.landing_lock, 'publication'):
            control.run(['fixture'], timeout=30, stdout=subprocess.DEVNULL)
    manager.land_all = slow
    try:
        with patch.object(L.subprocess, 'Popen', side_effect=spawn), \
                patch.object(L.subprocess, 'run', return_value=subprocess.CompletedProcess(
                    [], 1, stdout=b'', stderr=b'access denied')), \
                patch.object(B, 'alive', side_effect=lambda pid: not exited.is_set()):
            before = time.monotonic()
            manager.run_landing(s)
            assert time.monotonic() - before < 1
            assert s['phase'] == 'blocked' and 'access denied' in s['detail']
            assert s['land_child_pid'] == 43210
            assert manager.landing_lock.locked()
            assert manager.landing_blocker()
            assert 'refused' in manager.request_review(msg())
            assert 'refused' in manager.release(msg())
            assert len(manager.h.agents['dk99'].woken) == 1
    finally:
        exited.set()
    until = time.monotonic() + 2
    while (manager.landing_lock.locked() or manager.land_controls) and time.monotonic() < until:
        threading.Event().wait(0.01)
    assert not manager.landing_lock.locked() and not manager.land_controls
    assert 'land_child_pid' not in s


def test_crash_child_is_not_assumed_dead_on_restart(manager):
    s = setup(manager)
    admit(manager)
    s['land_child_pid'] = 43210
    manager.save(s)
    with patch.object(B, 'alive', return_value=True):
        recovered = B.Builders(manager.h, manager.repo)
        assert '43210' in recovered.landing_blocker()
        assert recovered.states[s['task']]['phase'] == 'blocked'
        assert 'refused' in recovered.land(msg())
    with patch.object(B, 'alive', return_value=False):
        assert not recovered.landing_blocker()


def test_cancellation_word_is_steward_only_and_dispatches():
    import house as H
    h = H.House.__new__(H.House)
    h.ready = threading.Event()
    h.ready.set()
    h.builders = Mock()
    offer = next(w for w in H.OFFER if w['word'] == 'house.land-cancel')
    assert offer['may'] == 'stewards'
    call = dict(msg(), word='house.land-cancel')
    h.call(call)
    h.builders.cancel_landing.assert_called_once_with(call)


def test_notification_contention_never_deadlocks_lifecycle_lock(manager):
    s = setup(manager)
    held, release, finished = threading.Event(), threading.Event(), threading.Event()
    def notifier():
        with manager.notification_lock:
            held.set()
            release.wait(2)
            manager.save(s)
    thread = threading.Thread(target=notifier, daemon=True)
    thread.start()
    assert held.wait(1)
    def lifecycle():
        with manager.lock:
            release.set()
            manager.try_start_outcome(s)
            manager.outcome(s)
        finished.set()
    other = threading.Thread(target=lifecycle, daemon=True)
    other.start()
    assert finished.wait(1), 'notification lock and lifecycle lock inverted'
    thread.join(1)
    other.join(1)


@pytest.mark.parametrize('value', [0, -1, 'nan', 'inf', 'bad'])
def test_bad_world_timeout_records_a_blocked_attempt(manager, value):
    s = setup(manager)
    manager.settings = lambda: dict(landing_timeout=value)
    admit(manager)
    manager.run_landing(s)
    assert s['phase'] == 'blocked' and s['land_attempt']
    assert len(manager.h.agents['dk99'].woken) == 1
