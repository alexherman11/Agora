"""Hidden in-process kernels; no live world, model, native window or Git writes."""
import json
from pathlib import Path
import sys
import threading
from types import SimpleNamespace
from unittest.mock import patch

import pytest

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1]),
               str(HERE.parents[2] / 'window-lab/kernel-desktop')]
import builders as B
from kernel.kernel import Kernel
from test_workers import Agent


@pytest.fixture
def world(tmp_path):
    k = Kernel(tmp_path / 'kernel', dict(tag='hf', name='Hidden handoff fixture',
               steward=dict(account='owner', name='Owner')))
    old = k.accounts['owner']
    new = k.join('recipient', 'Recipient', invite={'admitted': 'steward'})['person']
    stranger = k.join('stranger', 'Stranger', invite={'admitted': 'steward'})['person']
    actors = {p: k.actor_for(p, agent='handoff-fixture') for p in (old, new, stranger)}
    writes = []

    class Door:
        token = 'fixture'

        def __init__(self, person):
            self.person = person

        def call(self, route, line, **kw):
            if route == '/do':
                writes.append((self.person, line, kw))
            out = k.run(actors[self.person], line, mode='see' if route == '/see' else 'do', **kw)
            if not out['ok']:
                raise B.DoorRefused(out['text'])
            return out

        def look(self, target):
            return self.call('/see', 'look ' + target)['rows'][0]

    task = Door(old).call('/do', 'make kind=taskboard-task title=Repair who=Owner lead=Owner '
                         'build_run=fixture-run')['made'][0]
    book = (HERE / 'fixtures/agent-book.md').read_text(encoding='utf-8')
    home = tmp_path / 'house'
    home.mkdir()
    module = SimpleNamespace(
        see=lambda line, **kw: dict(rows=[dict(text=book)]) if line == 'look "Agent Book"'
        else k.run(actors[old], line, mode='see'), happen=lambda *a: None)
    agents = {}
    for person, name in ((old, 'Owner'), (new, 'Recipient'), (stranger, 'Stranger')):
        a = Agent()
        a.person, a.name = person, name
        agents[person] = a
    house = SimpleNamespace(home=home, world=tmp_path / 'kernel', m=module, agents=agents)
    b = B.Builders(house, tmp_path / 'repo')
    b.session = Door
    s = dict(task=task, run='fixture-run', name='Worker fixture', requester=old,
             requester_name='Owner', task_owner='Owner', phase='received', tree=str(b.repo),
             model='fixture', reasoning='fixture',
             activity=[], basis=dict(title='Repair', text='', acceptance='', who='Owner'))
    b.states[task] = s
    b.save(s)

    def request(person=old, recipient='Recipient'):
        return dict(word='house.hand', use='fixture-use',
                    args=dict(target=task, words=recipient),
                    caller=dict(person=person, name=agents[person].name))

    return SimpleNamespace(k=k, b=b, s=s, old=old, new=new, stranger=stranger, Door=Door,
                           request=request, writes=writes, house=house)


def assert_owner(w, person):
    state = w.b.states[w.s['task']]
    disk = json.loads((w.b.home / state['run'] / 'state.json').read_text(encoding='utf-8'))
    row = w.b.row(state)
    assert state['requester'] == disk['requester'] == row['owner'] == person
    assert row['owner_name'] == disk['requester_name'] == w.house.agents[person].name
    assert w.b.may_act(state, w.request(person))
    assert not w.b.may_act(state, w.request(w.stranger))


def test_real_deduplicated_chat_and_round_trip_back_to_previous_owner(world):
    w = world
    for person, name in ((w.new, 'Recipient'), (w.old, 'Owner')):
        door = w.Door(person)
        line = f'make kind=chat name="Worker fixture" about={w.s["task"]} with={person}'
        key = w.s['run'] + '-chat-' + person
        chat = door.call('/do', line, press=key)['made'][0]
        assert door.call('/do', line, press=key)['made'] == []   # exact original IndexError trigger
        out = w.b.hand(w.request(recipient=name))
        assert out['rows'][0]['status'] == 'handed', out
        assert w.s['chat'] == chat
        assert_owner(w, person)
        card = door.look(w.s['task'])
        assert card['who'] == card['lead'] == name and card['builder_chat'] == chat
    assert len([line for _, line, _ in w.writes if line.startswith('make kind=chat')]) == 4


def test_new_owner_can_land_after_restart_and_old_nonsteward_cannot(world):
    w = world
    assert w.b.hand(w.request()).get('external')
    again = B.Builders(w.house, w.b.repo)
    again.session = w.Door
    w.b = again
    assert_owner(w, w.new)
    # The fixture's old owner is a steward; remove only the test double's
    # steward admission to prove the ownership check independently.
    with patch.object(again, 'steward', return_value=False), patch.object(B.threading.Thread, 'start') as start:
        assert 'refused' in again.land(w.request(w.old))
        assert again.land(w.request(w.new)).get('external')
        assert start.call_count == 1


@pytest.mark.parametrize('after_write', [False, True])
def test_lost_card_answer_is_reconciled_without_replaying(world, monkeypatch, after_write):
    w = world
    original = w.Door.call
    card_writes = []

    def lose(door, route, line, **kw):
        if line.startswith('set '):
            card_writes.append(line)
            if after_write:
                original(door, route, line, **kw)
            raise TimeoutError('lost card answer')
        return original(door, route, line, **kw)

    monkeypatch.setattr(w.Door, 'call', lose)
    out = w.b.hand(w.request())
    assert 'refused' not in out
    assert out['rows'][0]['status'] == ('handed' if after_write else 'unresolved')
    if after_write:
        assert_owner(w, w.new)
    else:
        assert_owner(w, w.old)
        assert 'unresolved' in w.b.land(w.request())['refused']
        assert w.b.hand(w.request())['rows'][0]['status'] == 'unresolved'
        assert len(card_writes) == 1


def test_restart_recovers_write_that_finished_after_timeout(world, monkeypatch):
    w = world
    original = w.Door.call
    delayed = []

    def lose(door, route, line, **kw):
        if line.startswith('set '):
            delayed.append((door, route, line, kw))
            raise TimeoutError('reply lost before card write finished')
        return original(door, route, line, **kw)

    monkeypatch.setattr(w.Door, 'call', lose)
    assert w.b.hand(w.request())['rows'][0]['status'] == 'unresolved'
    door, route, line, kw = delayed[0]
    original(door, route, line, **kw)
    monkeypatch.setattr(w.Door, 'call', original)
    again = B.Builders(w.house, w.b.repo)
    again.session = w.Door
    w.b = again
    assert_owner(w, w.new)
    again.deliver_outcomes()
    assert_owner(w, w.new)
    assert 'handover' not in again.states[w.s['task']]
    assert len(w.house.agents[w.new].woken) == 1
    again.deliver_outcomes()
    assert len(w.house.agents[w.new].woken) == 1


def test_lost_chat_answer_can_retry_without_duplicate_chat_or_card_split(world, monkeypatch):
    w = world
    original = w.Door.call

    def lose(door, route, line, **kw):
        out = original(door, route, line, **kw)
        if line.startswith('make kind=chat'):
            raise TimeoutError('chat was made but answer lost')
        return out

    monkeypatch.setattr(w.Door, 'call', lose)
    out = w.b.hand(w.request())
    assert 'not handed' in out['refused']
    assert_owner(w, w.old)
    assert w.Door(w.old).look(w.s['task'])['who'] == 'Owner'
    monkeypatch.setattr(w.Door, 'call', original)
    assert w.b.hand(w.request())['rows'][0]['status'] == 'handed'
    assert_owner(w, w.new)
    assert len([line for _, line, _ in w.writes if line.startswith('make kind=chat')]) == 1


def test_empty_chat_receipt_is_explained_and_does_not_change_card(world, monkeypatch):
    w = world
    original = w.Door.call
    monkeypatch.setattr(w.Door, 'call', lambda d, route, line, **kw:
                        dict(ok=True, made=[]) if line.startswith('make kind=chat')
                        else original(d, route, line, **kw))
    out = w.b.hand(w.request())
    assert 'no confirmed chat' in out['refused']
    assert_owner(w, w.old)
    assert w.Door(w.old).look(w.s['task'])['who'] == 'Owner'


def test_explicit_denial_is_final_and_never_tries_another_person(world, monkeypatch):
    w = world
    original = w.Door.call
    attempted = []

    def deny(door, route, line, **kw):
        if line.startswith('set '):
            attempted.append(door.person)
            raise B.DoorRefused('set denied')
        return original(door, route, line, **kw)

    monkeypatch.setattr(w.Door, 'call', deny)
    out = w.b.hand(w.request())
    assert 'set denied' in out['refused'] and attempted == [w.old]
    assert_owner(w, w.old)
    assert 'handover' not in w.s


def test_notification_failure_keeps_success_and_retries_once(world, monkeypatch):
    w = world
    agent = w.house.agents[w.new]
    with patch.object(agent, 'wake', side_effect=RuntimeError('inbox unavailable')):
        out = w.b.hand(w.request())
    assert 'notification is pending' in out['text'] and 'refused' not in out
    assert_owner(w, w.new)
    w.b.deliver_outcomes()
    w.b.deliver_outcomes()
    assert len(agent.woken) == 1
    assert 'hand_notice' not in w.s


def test_parallel_hand_and_land_cannot_cross_an_unresolved_write(world, monkeypatch):
    w = world
    reached, release = threading.Event(), threading.Event()
    original = w.Door.call
    outcomes = []

    def slow(door, route, line, **kw):
        if line.startswith('set '):
            reached.set()
            assert release.wait(5)
        return original(door, route, line, **kw)

    monkeypatch.setattr(w.Door, 'call', slow)
    thread = threading.Thread(target=lambda: outcomes.append(w.b.hand(w.request())))
    thread.start()
    try:
        assert reached.wait(5)
        assert w.b.hand(w.request())['rows'][0]['status'] == 'unresolved'
        assert 'unresolved' in w.b.land(w.request())['refused']
        assert 'unresolved' in w.b.release(w.request())['refused']
        assert 'unresolved' in w.b.tell(w.request())['refused']
    finally:
        release.set()
        thread.join(5)
    assert outcomes[0]['rows'][0]['status'] == 'handed'
    assert_owner(w, w.new)


def test_card_name_edit_alone_does_not_grant_worker_authority(world):
    w = world
    task = w.Door(w.old).look(w.s['task'])
    w.Door(w.old).call('/do', f'set {w.s["task"]} who=Recipient lead=Recipient',
                       saw={w.s['task']: task['rev']})
    assert 'refused' in w.b.land(w.request(w.new))
    assert_owner(w, w.old)


def test_legacy_partial_handoff_repairs_card_chat_and_worker_together(world):
    w = world
    door = w.Door(w.new)
    chat = door.call('/do', f'make kind=chat name="Worker fixture" about={w.s["task"]} with={w.new}',
                     press=w.s['run'] + '-chat-' + w.new)['made'][0]
    task = w.Door(w.old).look(w.s['task'])
    w.Door(w.old).call('/do', f'set {w.s["task"]} who=Recipient lead=Recipient',
                       saw={w.s['task']: task['rev']})
    assert w.b.hand(w.request())['rows'][0]['status'] == 'handed'
    assert_owner(w, w.new)
    assert door.look(w.s['task'])['builder_chat'] == chat == w.s['chat']


def test_failed_owner_save_keeps_old_authority_until_durable_recovery(world, monkeypatch):
    w = world
    original = w.b.save
    def fail_new_owner(state):
        if state['requester'] == w.new:
            raise OSError('disk unavailable')
        return original(state)
    monkeypatch.setattr(w.b, 'save', fail_new_owner)
    assert w.b.hand(w.request())['rows'][0]['status'] == 'unresolved'
    assert_owner(w, w.old)
    assert w.Door(w.new).look(w.s['task'])['who'] == 'Recipient'
    again = B.Builders(w.house, w.b.repo)
    again.session = w.Door
    w.b = again
    again.deliver_outcomes()
    assert_owner(w, w.new)
    assert any('Recipient is in charge' in text for text, _ in w.house.agents[w.old].woken)


def test_slow_hand_returns_starting_then_delivers_actual_owner_receipt(world, monkeypatch):
    from house import House
    from kernel.modules import ModuleProcess, CALL_TIMEOUT
    w = world
    p = ModuleProcess.__new__(ModuleProcess)
    p.pending = {}
    p.host = SimpleNamespace(kernel=SimpleNamespace())
    h = House.__new__(House)
    h.ready = threading.Event()
    h.ready.set()
    h.builders = w.b
    h.m = SimpleNamespace(accept=lambda m: p.handle(dict(t='accepted', use=m['use'])))
    release, finished = threading.Event(), threading.Event()
    original = w.b.hand
    def slow(msg):
        assert release.wait(CALL_TIMEOUT + 5)
        return original(msg)
    monkeypatch.setattr(w.b, 'hand', slow)

    def send(msg):
        def run():
            try:
                out = h.call(dict(w.request(), use=msg['use']))
                p.handle(dict(out, t='answer', use=msg['use']))
            finally:
                finished.set()
        threading.Thread(target=run).start()
    p.send = send
    answer = p.ask(dict(t='call', word='house.hand'), CALL_TIMEOUT, caller=object())
    assert 'starting' in answer['text'] and 'refused' not in answer and p.pending
    release.set()
    assert finished.wait(5) and not p.pending
    assert_owner(w, w.new)
    assert any('Recipient is in charge' in text for text, _ in w.house.agents[w.old].woken)
