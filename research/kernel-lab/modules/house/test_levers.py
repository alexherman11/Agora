"""The levers that keep work from sitting blocked (Alex, 4 Nov: "ideally nothing should ever be blocked; someone in
the tree needs the scope to fix it"). Stop and release a worker, a worker whose card moved on ends quietly, landing is
one step, and a House change waits for quiet before it restarts the House. No live model, window or world."""
from types import SimpleNamespace
from unittest.mock import Mock, patch
import pytest
from test_builders import manager, msg, state       # noqa: F401  (fixture)
from test_workers import Agent
import builders as B


class Child:
    def __init__(self):
        self.stopped = False

    def stop(self):
        self.stopped = True


def test_release_ends_a_stopped_worker_for_good_and_frees_its_card(manager):
    s = state(manager, 'blocked'); s['pending'] = ['old words']; s['awaiting'] = 'x'
    manager.session = lambda person: manager.fixture_door
    out = manager.release(dict(msg(), args=dict(target='dk1', words='superseded by dk9')))
    assert out.get('external') and s['phase'] == 'released' and s['pending'] == [] and 'awaiting' not in s
    assert 'superseded by dk9' in s['detail'] and manager.fixture_door.task['build'] == 'released'
    assert 'refused' in manager.release(msg(person='dk98'))          # not its owner, a steward or Alex


def test_release_of_a_running_worker_stops_it_and_ends_released(manager):
    s = state(manager, 'working'); child = Child(); manager.children['dk1'] = child
    manager.session = lambda person: manager.fixture_door
    assert manager.release(msg()).get('external') and child.stopped and s['releasing']
    manager.children.pop('dk1')

    def run(st):                                                     # its run loop notices and ends
        raise RuntimeError('stopped')
    agent = Agent(); manager.h.agents = {'dk99': agent}
    manager.guarded(s, run)
    assert s['phase'] == 'released' and agent.woken == []


def test_stop_ends_the_turn_keeps_the_worker_and_a_new_word_starts_it(manager):
    s = state(manager, 'working'); child = Child(); manager.children['dk1'] = child; s['pending'] = ['stale']
    manager.session = lambda person: manager.fixture_door
    assert 'house.tell dk1' in manager.halt(msg())['text'] and child.stopped and s['pending'] == []
    manager.children.pop('dk1')
    agent = Agent(); manager.h.agents = {'dk99': agent}

    def run(st):
        raise RuntimeError('stopped')
    manager.guarded(s, run)
    assert s['phase'] == 'blocked' and 'stopped by Alex' in s['detail']
    assert agent.woken == []                                         # its owner stopped it: no wake about it
    with patch('builders.threading', SimpleNamespace(Thread=Mock())) as threads:
        assert manager.tell(dict(msg(), args=dict(target='dk1', words='do it the other way'))).get('external')
    assert threads.Thread.call_count == 1 and s['phase'] == 'preparing'


def test_stop_refuses_what_is_not_running(manager):
    state(manager, 'received')
    assert 'house.release dk1' in manager.halt(msg())['refused']


def test_a_worker_whose_card_moved_on_ends_released_and_wakes_nobody(manager):
    s = state(manager, 'blocked'); manager.session = lambda person: manager.fixture_door
    manager.fixture_door.task['build_run'] = 'kernel-a-newer-run'
    agent = Agent(); manager.h.agents = {'dk99': agent}
    manager.guarded(s, manager.assert_owned)
    assert s['phase'] == 'released' and 'moved on' in s['detail'] and agent.woken == []
    assert 'build' not in manager.fixture_door.task                  # the newer run's card facts are not touched


def test_a_worker_on_a_finished_card_ends_released(manager):
    s = state(manager, 'blocked'); manager.session = lambda person: manager.fixture_door
    manager.fixture_door.task['lane'] = 'Done'
    manager.guarded(s, manager.assert_owned)
    assert s['phase'] == 'released' and 'finished' in s['detail']


def test_land_is_one_step_checks_then_landing_then_switching_on(manager):
    s = state(manager, 'received'); calls = []
    manager.git = lambda cwd, *a: 'main-sha'
    manager.review = lambda st: calls.append('review') or st.update(phase='reviewed', candidate='c1', review_base='main-sha')
    manager.publish = lambda st: calls.append('publish') or st.update(phase='landed')
    manager.activate = lambda st: calls.append('activate')
    s['land_from'] = 'received'
    manager.land_all(s)
    assert calls == ['review', 'publish', 'activate']


def test_land_checks_again_when_main_moved_between_checks_and_landing(manager):
    s = state(manager, 'reviewed'); s.update(candidate='c1', review_base='old', land_from='reviewed'); calls = []
    manager.git = lambda cwd, *a: 'main-sha'
    tries = iter([RuntimeError('main advanced after review; preserve result'), None])

    def publish(st):
        calls.append('publish')
        err = next(tries)
        if err:
            raise err
    manager.review = lambda st: calls.append('review') or st.update(review_base='main-sha')
    manager.publish = publish
    manager.activate = lambda st: calls.append('activate')
    manager.land_all(s)
    assert calls == ['review', 'publish', 'review', 'publish', 'activate']


def test_a_reviewed_worker_on_current_main_lands_without_checking_twice(manager):
    s = state(manager, 'reviewed'); s.update(candidate='c1', review_base='main-sha', land_from='reviewed'); calls = []
    manager.session = lambda _: manager.fixture_door   # landing rereads card suite requirements
    manager.git = lambda cwd, *a: 'main-sha'
    manager.review = lambda st: calls.append('review')
    manager.publish = lambda st: calls.append('publish')
    manager.activate = lambda st: calls.append('activate')
    manager.land_all(s)
    assert calls == ['publish', 'activate']


def test_a_house_change_restarts_at_once_but_never_during_a_git_step(manager):
    """Alex, 5 Nov: a restart pauses each agent and worker and continues them after, instead of waiting for quiet.
    Only claiming, review and landing touch git, so only those hold it back."""
    spawned = []
    manager.spawn_reload = lambda args, log: spawned.append(args)
    manager.house_restart_due = True
    landing = state(manager, 'landing')
    manager.idle_check()
    assert spawned == [] and manager.house_restart_due              # mid-landing: wait for git
    landing['phase'] = 'landed'
    busy = Agent(); busy.busy = True; manager.h.agents = {'dk99': busy}
    manager.children['dk7'] = Child()                                 # an agent and a worker mid-turn: no wait
    manager.idle_check()
    assert spawned == [['house']] and not manager.house_restart_due


def test_activation_skips_the_house_while_switching_the_rest_on(manager, monkeypatch):
    s = state(manager, 'landed'); spawned = []
    manager.spawn_reload = lambda args, log: spawned.append(args)
    dry = 'kernel changed (research/kernel-lab/kernel/x.py): only the kernel restarts\nhouse: house.py\nwindow: w.py\n'
    monkeypatch.setattr(B.subprocess, 'run', lambda *a, **k: SimpleNamespace(stdout=dry))
    manager.h.agents = {'dk99': Agent(busy=True)}
    manager.activate(s)
    assert spawned == [['--skip', 'house']] and manager.house_restart_due
    assert 'kernel changed' in s['activation'] and 'House restarts by itself' in s['activation']
