import json
from types import SimpleNamespace
from unittest.mock import Mock, patch
import pytest
from test_builders import manager as fixture_manager, msg, state
import manager as M

@pytest.fixture
def manager(fixture_manager):
    b=fixture_manager
    p=b.h.world/'keep'/'house-managers.json'
    p.write_text(json.dumps({'dk99':{'tasks':['dk1','dk2','dk3'],'enabled':True,'approval':'fixture'}}))
    return b

def request(target='dk1',action='build',person='dk99',actor='dk99'):
    m=msg(target,person);m['caller']['id']=actor;m['args']['kv']={'action':action}
    return m

@pytest.mark.parametrize('m',[request(person='dk98',actor='dk98'),request(actor='agent99'),request('dk4')])
def test_unapproved_caller_and_task_never_dispatch(manager,m):
    with patch.object(manager,'start') as start:
        assert 'refused' in M.dispatch(manager,m)
        start.assert_not_called()
    assert not manager.states

def test_three_tasks_dispatch_as_requester_without_escalation(manager):
    manager.fixture_door.task['who']='Alex'
    manager.capacity_for=lambda provider:2           # a pool of two, set in house-settings
    # Mock the builder's imported namespace, not process-wide Thread.start:
    # resident fixtures can still finish unrelated background callbacks.
    with patch('builders.threading', SimpleNamespace(Thread=Mock())) as threads:
        for task in ('dk1','dk2'):
            assert M.dispatch(manager,request(task)).get('external')
            assert manager.states[task]['manager']=='dk99'
        assert 'refused' in M.dispatch(manager,request('dk3'))  # pool of two
        assert threads.Thread.call_count==2
        assert threads.Thread.return_value.start.call_count==2
        assert [call.kwargs['args'][0]['task'] for call in threads.Thread.call_args_list]==['dk1','dk2']

@pytest.mark.parametrize('change',[{'enabled':False},{'tasks':['dk1','dk2','dk3','dk4']},{'approval':''}])
def test_revocation_and_malformed_grant_fail_closed(manager,change):
    path=manager.h.world/'keep'/'house-managers.json'
    data=json.loads(path.read_text());data['dk99'].update(change);path.write_text(json.dumps(data))
    assert 'refused' in M.dispatch(manager,request())
    s=state(manager);s['manager']='dk99'
    with pytest.raises(RuntimeError):manager.assert_owned(s)

def test_other_requester_is_not_adopted(manager):
    state(manager)['requester']='dk98'
    assert 'another requester' in M.dispatch(manager,request(action='report'))['refused']

def test_manager_receipt_deduplicates_and_reports_do_not_complete(manager):
    s=state(manager);s['manager']='dk99'
    a=SimpleNamespace(cfg={'want':'awake'},wake=Mock())
    manager.h.agents={'dk99':a}
    M.notify(manager,s);M.notify(manager,s)
    a.wake.assert_called_once()
    assert 'Received is not reviewed' in a.wake.call_args.args[0]
    assert M.dispatch(manager,request(action='report'))['rows'][0]['phase']=='received'
    assert manager.fixture_door.task['lane']=='Now'

def test_sleep_or_active_child_defers_notification(manager):
    s=state(manager);s['manager']='dk99'
    a=SimpleNamespace(cfg={'want':'asleep'},wake=Mock());manager.h.agents={'dk99':a}
    M.notify(manager,s);a.wake.assert_not_called()
    a.cfg['want']='awake';manager.children['dk1']=object()
    M.notify(manager,s);a.wake.assert_not_called()
    manager.children.clear();M.notify(manager,s);a.wake.assert_called_once()

def test_worker_proof_is_bounded_and_hashed(manager):
    s=state(manager);s['manager']='dk99';manager.repo.mkdir(parents=True)
    (manager.repo/'BUILD-RESULT.md').write_text('x'*25000)
    out=M.dispatch(manager,request(action='report'))['rows'][0]
    assert len(out['self_proof'])==24000 and out['self_proof_truncated']
    assert len(out['self_proof_sha256'])==64


def test_restart_reoffers_unread_receipt_but_not_acknowledged_report(manager):
    s=state(manager);s['manager']='dk99'
    a=SimpleNamespace(cfg={'want':'awake'},wake=Mock());manager.h.agents={'dk99':a}
    M.notify(manager,s)
    del manager._manager_notifications
    M.notify(manager,s)
    assert a.wake.call_count==2  # first wake could have been lost on House exit
    M.dispatch(manager,request(action='report'))
    del manager._manager_notifications
    M.notify(manager,s)
    assert a.wake.call_count==2


def test_house_bookkeeping_uses_only_approved_fields_and_revision(manager):
    s=state(manager);s['manager']='dk99';manager.session=lambda _:manager.fixture_door
    manager.h.m.do=Mock(return_value={'ok':True,'record':'r9'})
    out=manager.update(s,build_phase='received')
    assert out['records']==['r9']
    assert manager.h.m.do.call_args.kwargs['saw']=={'dk1':1}
    assert not manager.fixture_door.writes
    with pytest.raises(RuntimeError,match='fields'):
        manager.update(s,who='Somebody else')
    assert manager.h.m.do.call_count==1


def test_manager_notes_cannot_change_ownership_or_scope(manager):
    manager.fixture_door.task['who']='Alex';manager.h.m.do=Mock(return_value={'ok':True,'record':'r9'})
    m=request(action='note');m['args']['kv']['who']='Rowan'
    assert 'refused' in M.dispatch(manager,m)
    manager.h.m.do.assert_not_called()
    m['args']['kv']={'action':'note','next_action':'Check acceptance proof'}
    assert M.dispatch(manager,m)['ok']
    assert manager.h.m.do.call_count==1


def test_reassigned_to_jeff_no_longer_starts_for_manager(manager):
    manager.fixture_door.task['who']='JEFF'
    with patch('builders.threading', SimpleNamespace(Thread=Mock())) as threads:
        assert 'no longer owns' in M.dispatch(manager,request())['refused']
        threads.Thread.assert_not_called()

@pytest.mark.parametrize('change',[{'who':'JEFF'},{'text':'new instructions'},{'paused':'yes'}])
def test_progress_write_revalidates_owner_instructions_and_hold(manager,change):
    s=state(manager);s.update(manager='dk99',task_owner='Alex',basis={'text':'original','who':'Alex'})
    manager.fixture_door.task.update(who='Alex',**{})
    manager.fixture_door.task.update(change)
    manager.session=lambda _:manager.fixture_door
    manager.h.m.do=Mock(return_value={'ok':True})
    with pytest.raises(RuntimeError):manager.update(s,build_phase='received')
    manager.h.m.do.assert_not_called()


def test_lost_bookkeeping_answer_is_uncertain_and_not_retried(manager):
    s=state(manager);s['manager']='dk99';manager.session=lambda _:manager.fixture_door
    manager.h.m.do=Mock(return_value={'ok':False,'refused':'the kernel did not answer'})
    with pytest.raises(TimeoutError,match='uncertain'):manager.update(s,build_phase='received')
    assert manager.h.m.do.call_count==1
