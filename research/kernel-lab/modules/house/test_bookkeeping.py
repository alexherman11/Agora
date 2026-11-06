"""Hidden card bookkeeping and delivery; no live world, workers or activation."""
import json
import threading
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

import pytest
import builders as B
import bookkeeping as N
from test_ghost_landing import bookkeeping
from test_handover import world  # noqa: F401
from test_workers import Agent


@pytest.fixture
def receipt_world(request, monkeypatch):
    if request.param == 'disk':
        return request.getfixturevalue('world')
    # Real kernel permissions and transactions, with storage explicitly doubled.
    # This proves authority, not on-disk durability, and never accesses temp dirs.
    from kernel import kernel as K, store

    class MemoryLog:
        def __init__(self, _):
            self.records, self.head = [], ''
        def replay(self):
            return store.State()
        def append(self, rec):
            rec = dict(rec, v=store.SHAPE, seq=len(self.records) + 1, prev=self.head)
            rec['digest'] = store.digest(rec)
            self.records.append(rec)
            self.head = rec['digest']
            return rec

    path = MagicMock()
    path.__truediv__.return_value = path
    path.exists.return_value = False
    path.read_bytes.return_value = b'fixture-only-memory-key'
    path.read_text.side_effect = FileNotFoundError
    monkeypatch.setattr(K, 'Path', lambda _: path)
    monkeypatch.setattr(K, 'Log', MemoryLog)
    monkeypatch.setattr(K.Kernel, '_keep_write', lambda *a: None)
    k = K.Kernel('memory-only', dict(tag='mf', name='Memory receipt fixture',
        steward=dict(account='caller', name='Owner'),
        modules=[dict(name='house', run=['never-started'], publishes='house.*',
                      grants='house.* rows look', **{'for': 'steward'})]))
    old = k.accounts['caller']
    new = k.join('owner', 'Recipient', invite={'admitted': 'steward'})['person']
    stranger = k.join('lead', 'Stranger', invite={'admitted': 'steward'})['person']

    class Door:
        def __init__(self, person):
            self.actor = k.actor_for(person, agent='fixture')
        def call(self, route, line, **kw):
            out = k.run(self.actor, line, mode='see' if route == '/see' else 'do', **kw)
            if not out['ok']:
                raise B.DoorRefused(out['text'])
            return out
        def look(self, target):
            return self.call('/see', 'look ' + target)['rows'][0]

    mid = k.module_named('house')
    book = (Path(__file__).parent / 'fixtures/agent-book.md').read_text(encoding='utf-8')
    module = SimpleNamespace(
        see=lambda line, **kw: dict(rows=[dict(text=book)]) if line == 'look "Agent Book"'
        else k.module_own(mid, line, mode='see'),
        do=lambda line, **kw: k.module_own(mid, line, **kw), happen=lambda *a: None)
    agents = {}
    for person, name in ((old, 'Owner'), (new, 'Recipient'), (stranger, 'Stranger')):
        agent = Agent()
        agent.person, agent.name = person, name
        agents[person] = agent
    b = B.Builders.__new__(B.Builders)
    b.h = SimpleNamespace(m=module, agents=agents)
    b.lock, b.notification_lock = threading.RLock(), threading.RLock()
    b.land_context, b.land_controls = threading.local(), {}
    b.states, b.children, b.stopping = {}, {}, False
    b.session, b.steward, b.alex = Door, k.is_steward, lambda _: False
    b.settings = lambda: dict(landing_timeout=3, landing_wait_timeout=0.1)
    b.save = Mock()
    s = dict(run='fixture-run', name='Worker fixture', phase='received', tree='fixture-only',
             activity=[])
    return SimpleNamespace(k=k, b=b, s=s, old=old, new=new, stranger=stranger, mid=mid, Door=Door)


def notification_fixture():
    b, state, card = bookkeeping()
    card.update(kind='taskboard-task', lead='Lead')
    lead, owner = Agent(), Agent()
    lead.name, owner.name = 'Lead', 'Owner'
    b.h.agents = {'lead-person': lead, 'former-owner': owner}
    b.notification_lock = threading.RLock()
    b.settings = lambda: dict(bookkeeping_failure_chat='coordination-chat')
    b.message = lambda *args, **kw: 'House card write failed'
    posts = []

    def see(line):
        if line == 'look coordination-chat':
            return dict(rows=[dict(id='coordination-chat', kind='chat')])
        if line.startswith('rows said '):
            return dict(rows=list(posts))
        return dict(rows=[dict(card)])

    def do(line, **kw):
        import shlex
        if line.startswith('say '):
            args = dict(x.split('=', 1) for x in shlex.split(line)[2:])
            posts.append(dict(chat='coordination-chat', **args))
            return dict(ok=True)
        return dict(ok=False, text='House lacks card-write grant')

    b.h.m.see, b.h.m.do = Mock(side_effect=see), Mock(side_effect=do)
    return b, state, card, lead, owner, posts


def startup(w, spec=None):
    """Real startup grant reconciliation, with only a never-started fixture module."""
    import kdesk
    if spec is None:
        spec = next(s for s in kdesk.module_specs(headless=True) if s['name'] == 'house')
    spec = dict(spec, run=['never-started'])
    with patch.object(kdesk, 'module_specs', return_value=[spec]):
        kdesk.after_genesis(w.k, headless=True)
    return spec


@pytest.mark.parametrize('receipt_world', ['memory', 'disk'], indirect=True)
def test_startup_installs_build_fields_despite_other_object_set_grants(receipt_world):
    w = receipt_world
    card = w.Door(w.old).call('/do', 'make kind=taskboard-task title=Repair')['made'][0]
    other = w.Door(w.old).call('/do', 'make kind=note name=Unrelated')['made'][0]
    w.Door(w.old).call('/do', f'grant house words=set only=thing:{other}')
    assert not w.k.module_own(w.mid, f'set {card} build_phase=started')['ok']
    spec = startup(w)
    assert len(spec['scoped_grants']) == 1
    assert spec['scoped_grants'][0]['words'] == 'set'
    assert spec['scoped_grants'][0]['only'].startswith('kind:taskboard-task;fields:')
    fields = set(spec['scoped_grants'][0]['only'].split('fields:')[1].split(','))
    assert fields == B.M.BUILD_FIELDS
    w.k.module_own(w.mid, f'look {card}', mode='see')
    out = w.k.module_own(w.mid, f'set {card} build_phase=started')
    assert out['ok'], out
    w.k.module_own(w.mid, f'look {card}', mode='see')
    out = w.k.module_own(w.mid, f'set {card} build_phase=blocked text=overwritten')
    assert not out['ok'] and 'outside that scope' in out['text'], out
    assert w.Door(w.old).look(card)['build_phase'] == 'started'
    outside = w.Door(w.old).call('/do', 'make kind=note name=Outside')['made'][0]
    w.k.module_own(w.mid, f'look {outside}', mode='see')
    out = w.k.module_own(w.mid, f'set {outside} build_phase=started')
    assert not out['ok'] and 'outside that scope' in out['text'], out
    n = len(w.k.log.records)
    startup(w)
    assert len(w.k.log.records) == n


@pytest.mark.parametrize('receipt_world', ['memory', 'disk'], indirect=True)
def test_startup_never_restores_revoked_scoped_grant_even_after_source_removal(receipt_world):
    w = receipt_world
    spec = startup(w)
    scope = spec['scoped_grants'][0]['only']
    grant = next(g for g in w.k._grants_to(w.mid) if w.k.state.get(g, 'only') == scope)
    seq = w.k.log.records[-1]['seq']
    w.Door(w.old).call('/do', f'undo r{seq}')
    assert grant not in w.k._grants_to(w.mid)
    startup(w, dict(spec, scoped_grants=[]))
    startup(w, spec)
    assert not any(w.k.state.get(g, 'only') == scope for g in w.k._grants_to(w.mid))


@pytest.mark.parametrize('receipt_world', ['memory', 'disk'], indirect=True)
def test_startup_leaves_off_module_without_grants(receipt_world):
    w = receipt_world
    w.Door(w.old).call('/do', 'off house')
    startup(w)
    assert not list(w.k._grants_to(w.mid))
    assert not w.k.state.get(w.mid, 'asks_scoped')


@pytest.mark.parametrize('receipt_world', ['memory', 'disk'], indirect=True)
def test_startup_new_module_gets_scoped_grant_once(receipt_world):
    w = receipt_world
    import kdesk
    house = next(s for s in kdesk.module_specs(headless=True) if s['name'] == 'house')
    spec = dict(house, name='fixture-module', publishes='fixture.*', grants='rows look')
    startup(w, spec)
    mid = w.k.module_named('fixture-module')
    scope = spec['scoped_grants'][0]['only']
    assert any(w.k.state.get(g, 'only') == scope for g in w.k._grants_to(mid))
    # A second start may initialize the old base `asks`, but may not duplicate the grant.
    startup(w, spec)
    assert sum(w.k.state.get(g, 'only') == scope for g in w.k._grants_to(mid)) == 1
    n = len(w.k.log.records)
    startup(w, spec)
    assert len(w.k.log.records) == n


@pytest.mark.parametrize('receipt_world', ['memory', 'disk'], indirect=True)
def test_startup_remembers_equivalent_manual_grant_without_duplicate(receipt_world):
    w = receipt_world
    scope = json.loads((Path(__file__).parent / 'grants.json').read_text())[0]['only']
    w.Door(w.old).call('/do', f'grant house words=set only="{scope}"')
    seq = w.k.log.records[-1]['seq']
    startup(w)
    assert sum(w.k.state.get(g, 'only') == scope for g in w.k._grants_to(w.mid)) == 1
    w.Door(w.old).call('/do', f'undo r{seq}')
    startup(w)
    assert not any(w.k.state.get(g, 'only') == scope for g in w.k._grants_to(w.mid))


@pytest.mark.parametrize('receipt_world', ['memory', 'disk'], indirect=True)
def test_startup_still_respects_base_word_revocation(receipt_world):
    w = receipt_world
    spec = startup(w)
    spec = dict(spec, grants=spec['grants'] + ' fixture.word')
    startup(w, spec)
    seq = w.k.log.records[-1]['seq']
    assert any('fixture.word' in w.k.state.get(g, 'words').split() for g in w.k._grants_to(w.mid))
    w.Door(w.old).call('/do', f'undo r{seq}')
    startup(w, spec)
    assert not any('fixture.word' in w.k.state.get(g, 'words').split() for g in w.k._grants_to(w.mid))


def test_failed_write_reaches_lead_and_coordination_once_without_owner_authority():
    b, s, card, lead, owner, posts = notification_fixture()
    for _ in range(2):
        with pytest.raises(RuntimeError, match='grant'):
            b.update(s, build_phase='blocked')
        N.deliver(b, s)
    assert len(lead.woken) == len(posts) == 1
    assert not owner.woken
    assert 'House lacks card-write grant' in lead.woken[0][0]
    assert posts[0]['text'] == lead.woken[0][0]
    assert next(iter(s['bookkeeping_failures'].values()))['delivered'] == ['lead', 'chat']
    b.session.assert_not_called()


def test_lead_delivery_failure_does_not_prevent_chat_and_retries_only_lead():
    b, s, card, lead, owner, posts = notification_fixture()
    with pytest.raises(RuntimeError):
        b.update(s, build_phase='blocked')
    wake = lead.wake
    lead.wake = Mock(side_effect=RuntimeError('inbox unavailable'))
    N.deliver(b, s)
    notice = next(iter(s['bookkeeping_failures'].values()))
    assert notice['delivered'] == ['chat'] and 'inbox unavailable' in notice['lead_error']
    assert len(posts) == 1
    lead.wake = wake
    N.deliver(b, s)
    assert len(lead.woken) == len(posts) == 1


def test_uncertain_chat_answer_is_reconciled_after_reload_without_duplicate():
    b, s, card, lead, owner, posts = notification_fixture()
    with pytest.raises(RuntimeError):
        b.update(s, build_phase='blocked')
    send = b.h.m.do.side_effect
    def lost(line, **kw):
        send(line, **kw)
        raise TimeoutError('answer lost')
    b.h.m.do.side_effect = lost
    N.deliver(b, s)
    assert len(posts) == len(lead.woken) == 1
    notice = next(iter(s['bookkeeping_failures'].values()))
    assert notice['delivered'] == ['lead']
    saved = json.loads(json.dumps(s))
    b.h.m.do.side_effect = send
    N.deliver(b, saved)
    assert len(posts) == len(lead.woken) == 1
    assert next(iter(saved['bookkeeping_failures'].values()))['delivered'] == ['lead', 'chat']


def test_missing_chat_route_or_grant_remains_pending_and_never_uses_person_session():
    b, s, card, lead, owner, posts = notification_fixture()
    with pytest.raises(RuntimeError):
        b.update(s, build_phase='blocked')
    b.settings = lambda: {}
    N.deliver(b, s)
    notice = next(iter(s['bookkeeping_failures'].values()))
    assert 'not configured' in notice['chat_error'] and notice['delivered'] == ['lead']
    b.settings = lambda: dict(bookkeeping_failure_chat='coordination-chat')
    b.h.m.do.side_effect = lambda *a, **kw: dict(ok=False, text='say grant refused')
    N.deliver(b, s)
    assert 'say grant refused' in notice['chat_error']
    assert len(lead.woken) == 1 and not posts
    b.session.assert_not_called()


def test_notice_uses_current_lead_and_pending_notice_survives_successful_card_retry():
    b, s, card, lead, owner, posts = notification_fixture()
    card['lead'] = 'Owner'
    with pytest.raises(RuntimeError):
        b.update(s, build_phase='blocked')
    card['lead'] = 'Lead'
    b.h.m.do.side_effect = lambda *a, **kw: dict(ok=True)
    b.update(s, build_phase='received')
    N.deliver(b, s)
    assert len(lead.woken) == 1 and not owner.woken


@pytest.mark.parametrize('receipt_world', ['memory', 'disk'], indirect=True)
@pytest.mark.parametrize('resident', [True, False])
def test_kernel_failed_write_reaches_lead_and_shop_talk(receipt_world, resident):
    w = receipt_world
    card = w.Door(w.old).call('/do',
        'make kind=taskboard-task title=Repair lead=Stranger build_run=fixture-run')['made'][0]
    chat = w.Door(w.old).call('/do', 'make kind=chat name="Shop talk"')['made'][0]
    w.Door(w.old).call('/do', f'grant house words=say only=thing:{chat}')
    w.Door(w.old).call('/do', f'grant house words=notification.send only=thing:{card}')
    w.Door(w.old).call('/do',
        f'make kind=house-settings name="House settings" bookkeeping_failure_chat={chat}')
    w.b.settings = B.Builders.settings.__get__(w.b)
    w.s.update(task=card, requester=w.new, requester_name='Recipient')
    w.b.states.clear()
    w.b.states[card] = w.s
    lead_agent = w.b.h.agents[w.stranger]
    if not resident:
        w.b.h.agents.pop(w.stranger)
    with patch.object(B.threading.Thread, 'start') as launch:
        out = w.b.land(dict(args=dict(target=card), caller=dict(person=w.old, name='Owner')))
    assert out['rows'][0]['phase'] == 'blocked'
    launch.assert_not_called()
    w.b.outcome(w.s)
    w.b.outcome(w.s)
    said = w.Door(w.old).call('/see', f'rows said chat={chat} about={card}')['rows']
    assert len(said) == 1
    assert 'could not write its build receipt' in said[0]['text']
    assert json.loads(said[0]['text'].splitlines()[-1])['task'] == card
    if resident:
        assert len(lead_agent.woken) == 1 and lead_agent.woken[0][0] == said[0]['text']
    else:
        notices = w.Door(w.stranger).call('/see',
            f'rows notification recipient={w.stranger} about={card}')['rows']
        assert len(notices) == 1 and notices[0]['text'] == said[0]['text']
    notice = next(iter(w.s['bookkeeping_failures'].values()))
    assert notice['delivered'] == ['lead', 'chat'], notice
    assert len(w.b.h.agents[w.new].woken) == len(w.b.h.agents[w.old].woken) == 1


@pytest.mark.parametrize('receipt_world', ['memory', 'disk'], indirect=True)
def test_four_distinct_people_card_receipt_uses_house_narrow_grant(receipt_world):
    w = receipt_world
    # A makes the card, B leads it, C is the landing steward, D owns the worker.
    maker = w.k.join('maker', 'Maker', invite={'admitted': 'steward'})['person']
    actor = w.k.actor_for(maker)
    out = w.k.run(actor, 'make kind=taskboard-task title=Repair lead=Stranger '
                        'who=Recipient build_run=fixture-run')
    assert out['ok'], out
    task = out['made'][0]
    lead, caller, owner = w.stranger, w.old, w.new
    assert len({maker, lead, caller, owner}) == 4
    startup(w)  # The shipped declaration, with no per-card grant by hand.
    # Prove both the old mismatch and the module's kernel-enforced field limit.
    with pytest.raises(B.DoorRefused, match='set is for'):
        w.Door(owner).call('/do', f'set {task} build_phase=reviewing')
    assert not w.k.module_own(w.mid, f'set {task} text=overwritten')['ok']
    w.b.states.clear()
    w.s.update(task=task, requester=owner, requester_name='Recipient',
               task_owner='Recipient', basis=dict(title='Repair', who='Recipient'))
    w.b.states[task] = w.s
    w.b.save(w.s)
    w.b.start_queued = lambda: None
    w.b.idle_check = lambda: None
    w.b.land_all = lambda state: w.b.phase(state, 'landed', 'fixture publication',
                                          landed_commit='fixture-commit', outcome='unverified')
    with patch.object(B.threading.Thread, 'start'):
        out = w.b.land(dict(args=dict(target=task), caller=dict(person=caller, name='Owner')))
    card = w.Door(caller).look(task)
    assert card['land_attempt'] == out['rows'][0]['attempt']
    assert card['land_step'] == 'started'
    assert card['made_by'] == maker and card['lead'] == 'Stranger'
    assert card['who'] == 'Recipient'
    w.b.run_landing(w.s)
    card = w.Door(caller).look(task)
    assert card['build_phase'] == 'landed' and card['landed_commit'] == 'fixture-commit'
    assert json.loads(card['land_receipt'])['phase'] == 'landed'
