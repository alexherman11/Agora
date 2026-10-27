"""Bounded builder lifecycle proofs; no live model, native window, or live world."""
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch
import pytest

HERE=Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import builders as B


class WorldDoor:
    def __init__(self):
        self.token='fixture'
        self.task=dict(id='dk1',kind='taskboard-task',title='Repair',text='original',rev=1,lane='Now')
        self.writes=[]
    def look(self, target):return dict(self.task)
    def call(self, route, line, **kw):
        import shlex
        self.writes.append((route,line,kw))
        if line.startswith('set '):
            assert kw['saw']=={'dk1':self.task['rev']}
            self.task.update(dict(x.split('=',1) for x in shlex.split(line)[2:]))
            self.task['rev']+=1
        return dict(ok=True, records=['r1'],made=['dk2'])


@pytest.fixture
def manager(tmp_path):
    home=tmp_path/'world/modules/house';home.mkdir(parents=True)
    world=home.parent.parent;(world/'keep').mkdir()
    (world/'keep/accounts.json').write_text(json.dumps({'desktop:alex':'dk99','desktop:other':'dk98'}))
    (world/'keep/sessions.json').write_text(json.dumps({'fixture-token':{'account':'desktop:alex','agent':'claude'}}))
    door=WorldDoor()
    m=SimpleNamespace(see=lambda *a,**k:dict(rows=[dict(door.task)]),happen=lambda *a:None)
    h=SimpleNamespace(home=home,world=world,m=m,builder_url='http://127.0.0.1:1')
    b=B.Builders(h,tmp_path/'repo'); b.fixture_door=door
    return b


def msg(target='dk1', person='dk99'):
    return dict(args={'target':target},caller={'person':person,'name':'Alex'},use='fixture')


def state(b, phase='received'):
    s=dict(task='dk1',run='kernel-fixture',name='Codex fixture',requester='dk99',title='Repair',phase=phase,
           model='gpt-6.1-sol',reasoning='medium',activity=[],tree=str(b.repo),base='a',result_received='now')
    b.states['dk1']=s;b.save(s);b.fixture_door.task['build_run']=s['run']
    return s


def test_session_is_existing_agent_of_authenticated_requester(manager):
    assert manager.session('dk99').token=='fixture-token'
    with pytest.raises(RuntimeError,match='no unambiguous'):
        manager.session('dk98')


@pytest.mark.parametrize('field,value',[('paused','yes'),('approval_required','true'),('permission_required','1'),
                                       ('cancelled','yes'),('status','cancelled'),('lane','Done')])
def test_held_work_never_spawns(manager,field,value):
    manager.fixture_door.task[field]=value
    with patch.object(B.threading.Thread,'start') as launch:
        assert 'refused' in manager.start(msg())
        launch.assert_not_called()


def test_capacity_and_duplicate_are_not_running_claims(manager):
    with patch.object(B.threading.Thread,'start') as launch:
        a=manager.start(msg())
        assert a['rows'][0]['doing']=='asked'
        assert manager.start(msg())['rows'][0]['doing']=='asked'
        assert launch.call_count==1
        manager.start(msg('dk2'))
        assert 'refused' in manager.start(msg('dk3'))
        assert launch.call_count==2


def test_foreign_owner_not_stolen(manager):
    manager.fixture_door.task['who']='Another builder'
    assert 'another owner' in manager.start(msg())['refused']


def test_restart_retains_session_and_marks_uncertainty(manager):
    s=state(manager,'working');s['session']='codex-session';manager.save(s)
    again=B.Builders(manager.h,manager.repo)
    assert again.states['dk1']['phase']=='recovery-needed'
    assert again.states['dk1']['session']=='codex-session'
    assert not again.children


def test_claim_change_blocks_receipt_and_landing(manager):
    s=state(manager)
    manager.session=lambda _:manager.fixture_door
    manager.fixture_door.task['build_run']='somebody-else'
    with pytest.raises(RuntimeError,match='claim changed'):
        manager.update(s,build='landed')
    assert not manager.fixture_door.writes


def test_received_result_does_not_complete_task(manager):
    s=state(manager)
    manager.session=lambda _:manager.fixture_door
    manager.phase(s,'received','model ended')
    assert manager.fixture_door.task['lane']=='Now'
    assert manager.fixture_door.task['build']=='landing'
    assert manager.fixture_door.task['build_phase']=='received'
    assert not manager.fixture_door.task.get('verified')


def test_only_requester_reviews_and_lands(manager):
    state(manager)
    assert 'refused' in manager.request_review(msg(person='dk98'))
    assert 'refused' in manager.land(msg())


def test_followup_retained_once_and_does_not_wake_paused_work(manager):
    s=state(manager,'working');manager.session=lambda _:manager.fixture_door
    m=msg();m['args']['words']='Keep the original title; fix only minimising.'
    assert manager.tell(m).get('external')
    assert s['pending']==[m['args']['words']]
    manager.fixture_door.task['paused']='yes'
    assert 'refused' in manager.tell(m)
    assert len(s['pending'])==1
    manager.fixture_door.task.pop('paused')
    manager.fixture_door.task['who']='Another owner'
    assert 'refused' in manager.tell(m)


def test_correction_requires_acknowledgement_before_review(manager):
    s=state(manager);s['basis']={'text':'original'};manager.session=lambda _:manager.fixture_door
    manager.fixture_door.task['text']='corrected acceptance'
    with pytest.raises(RuntimeError,match='instructions'):
        manager.assert_owned(s)
    m=msg();m['args']['words']='Use the corrected acceptance.'
    with patch.object(B.threading.Thread,'start') as launch:
        assert manager.tell(m).get('external')
        assert s['phase']=='preparing'
        assert launch.call_count==1


def test_uncertain_mutation_does_not_write_again(manager):
    s=state(manager);manager.session=lambda _:manager.fixture_door
    def lost(_):raise TimeoutError('claim response lost')
    manager.guarded(s,lost)
    assert s['phase']=='uncertain'
    assert manager.fixture_door.writes==[]


def test_main_advancement_blocks_publish_without_git_mutation(manager):
    s=state(manager,'reviewed');s.update(review_base='a',candidate='b')
    manager.session=lambda _:manager.fixture_door
    called=[]
    def git(cwd,*args):
        called.append(args)
        return 'main' if args[0]=='branch' else 'c'
    manager.git=git
    with pytest.raises(RuntimeError,match='main advanced'):
        manager.publish(s)
    assert not any(a[0]=='merge' for a in called)


def test_publish_preserves_overlapping_uncommitted_source(manager):
    s=state(manager,'reviewed');s.update(review_base='a',candidate='b')
    manager.session=lambda _:manager.fixture_door
    called=[]
    def git(cwd,*args):
        called.append(args)
        if args[0]=='branch':return 'main'
        if args[0]=='rev-parse':return 'a' if Path(cwd)==manager.repo else 'b'
        return 'source.py'
    s['tree']=str(manager.repo/'tree');manager.git=git
    with pytest.raises(RuntimeError,match='overlap'):
        manager.publish(s)
    assert not any(a[0]=='merge' for a in called)


def test_unknown_door_outcome_is_not_retried(manager):
    s=state(manager)
    class Lost(WorldDoor):
        calls=0
        def call(self,*a,**k):self.calls+=1;raise TimeoutError('lost reply')
    lost=Lost();lost.task['build_run']=s['run'];manager.session=lambda _:lost
    with pytest.raises(TimeoutError):manager.update(s,build='building')
    assert lost.calls==1


def test_real_kernel_claim_fence_and_git_lifecycle(tmp_path, monkeypatch):
    """Real kernel transactions, House-created git worktree, independent subprocess
    proof and publication; only the model boundary is scripted. No live world."""
    import time
    sys.path.insert(0,str(B.T.REPO/'research/kernel-lab'))
    from kernel.kernel import Kernel
    home=tmp_path/'world/modules/house';home.mkdir(parents=True)
    world=home.parent.parent
    k=Kernel(world,dict(tag='fx',name='Builder fixture',steward={'account':'fixture:alex','name':'Alex'},modules=[]))
    person=k.accounts['fixture:alex']; actor=k.actor_for(person,'fixture-builder')
    task=k.run(actor,'make kind=taskboard-task title="Fixture repair" lane=Now')['made'][0]
    (world/'keep/sessions.json').write_text(json.dumps({'fixture-token':{'account':'fixture:alex','agent':'fixture-builder'}}))
    class KernelDoor:
        token='fixture-token'
        def look(self,target):return self.call('/see','look '+target)['rows'][0]
        def call(self,route,line,**kw):
            out=k.run(actor,line,mode='see' if route=='/see' else 'do',**kw)
            if not out['ok']:raise RuntimeError(out['text'])
            return out
    door=KernelDoor()
    h=SimpleNamespace(home=home,world=world,builder_url='http://127.0.0.1:1',
                      m=SimpleNamespace(see=lambda line,**kw:door.call('/see',line),happen=lambda *a:None))
    repo=tmp_path/'repo';repo.mkdir();b=B.Builders(h,repo);b.session=lambda _:door
    b.git(repo,'init','-b','main');b.git(repo,'config','user.name','Fixture');b.git(repo,'config','user.email','fixture@invalid')
    (repo/'value.txt').write_text('before');(repo/'other.txt').write_text('preserved')
    (repo/'test_value.py').write_text('from pathlib import Path\ndef test_value():\n    assert Path("value.txt").read_text() == "after"\n')
    b.git(repo,'add','.');b.git(repo,'commit','-m','fixture base')
    class ScriptedChild:
        def __init__(self,cmd,cwd,env,events,log,**kw):
            self.events=events;self.tree=Path(cwd);self.proc=SimpleNamespace(pid=1234)
        def send(self,text):
            (self.tree/'value.txt').write_text('after')
            b.git(self.tree,'add','value.txt');b.git(self.tree,'commit','-m','fixture repair')
            (self.tree/'BUILD-RESULT.md').write_text('Scripted fixture changed value; independent check must verify it.')
            self.events.put(dict(e='init',session='scripted-session'))
            self.events.put(dict(e='text',text='repair ready'))
            self.events.put(dict(e='result',ok=True))
            return True
        def stop(self):pass
    monkeypatch.setattr(B.T,'Child',ScriptedChild)
    out=b.start(dict(args={'target':task},caller={'person':person,'name':'Alex'},use='fixture'))
    assert out.get('external'),out
    deadline=time.monotonic()+15
    while b.states[task]['phase'] not in ('received','blocked') and time.monotonic()<deadline:time.sleep(.02)
    s=b.states[task]
    assert s['phase']=='received',s
    assert s['session']=='scripted-session'
    assert s['claim_records']
    assert door.look(task)['lane']=='Now'
    # A stale claim cannot replace the current claim even with the same agent identity.
    old=door.look(task)
    door.call('/do','set '+task+' note="new fact"',saw={task:old['rev']})
    with pytest.raises(RuntimeError):
        door.call('/do','set '+task+' note="stale overwrite"',saw={task:old['rev']})
    monkeypatch.setattr(B,'CHECKS',[['test_value.py']])
    b.review(s)
    assert s['phase']=='reviewed'
    assert s['checks'][0]['returncode']==0
    (repo/'other.txt').write_text('unrelated user edit')
    b.publish(s)
    assert s['phase']=='landed'
    assert (repo/'value.txt').read_text()=='after'
    assert (repo/'other.txt').read_text()=='unrelated user edit'
    assert door.look(task)['outcome']=='unverified'
    assert door.look(task)['lane']=='Now'


def test_mcp_compatibility_does_not_broaden_other_tools(tmp_path):
    repo=B.T.REPO
    sys.path.insert(0,str(repo/'research/codex-residents'))
    import codex_worker as W
    for server,tools in [('agora',['see','do','lines']),('desk',['desk'])]:
        path=tmp_path/'mcp.json';path.write_text(json.dumps({'mcpServers':{server:{'command':'fixture'}}}))
        params=W.thread_parameters(tmp_path,'gpt-6.1-sol','fixture',path)
        assert params['config']['mcp_servers'][server]['enabled_tools']==tools
        assert params['approvalPolicy']=='never'
        assert params['sandbox']=='workspace-write'
    path.write_text(json.dumps({'mcpServers':{'agora':{},'desk':{}}}))
    with pytest.raises(ValueError):W.thread_parameters(tmp_path,'gpt-6.1-sol','fixture',path)
