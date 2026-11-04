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
    book=(HERE/'fixtures/agent-book.md').read_text(encoding='utf-8')
    m=SimpleNamespace(see=lambda line,**k:dict(rows=[dict(text=book) if line == 'look "Agent Book"' else dict(door.task)]),
                      happen=lambda *a:None)
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
        for target in ('dk2','dk3','dk4'):           # four Codex workers by default (Alex, 28 Oct)
            manager.start(msg(target))
        queued=manager.start(msg('dk5'))             # 4 Nov: a full pool queues, never refuses
        assert 'starts by itself' in queued['text'] and manager.states['dk5']['phase']=='queued'
        assert launch.call_count==4
        manager.states['dk1']['phase']='landed'      # a slot frees: the queued one starts
        manager.start_queued()
        assert manager.states['dk5']['phase']=='asked' and launch.call_count==5


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
    s=state(manager)
    assert 'refused' in manager.request_review(msg(person='dk98'))
    assert 'refused' in manager.land(msg(person='dk98'))
    with patch.object(B.threading.Thread,'start') as launch:     # 4 Nov: land is one step from a finished turn
        assert manager.land(msg()).get('external')
        assert s['phase']=='reviewing' and s['land_from']=='received' and launch.call_count==1


def test_followup_retained_once_and_does_not_wake_paused_work(manager):
    s=state(manager,'working');manager.session=lambda _:manager.fixture_door
    m=msg();m['args']['words']='Keep the original title; fix only minimising.'
    assert manager.tell(m).get('external')
    assert s['pending']==[m['args']['words']]
    manager.fixture_door.task['paused']='yes'
    assert 'refused' in manager.tell(m)
    assert len(s['pending'])==1
    manager.fixture_door.task.pop('paused')
    manager.fixture_door.task['build_run']='kernel-another-run'      # its card moved on to another worker
    assert 'moved on' in manager.tell(m)['refused']


def test_a_changed_card_goes_to_the_worker_instead_of_stopping_it(manager):
    s=state(manager);s['basis']={'text':'original'};manager.session=lambda _:manager.fixture_door
    manager.fixture_door.task['text']='corrected acceptance'
    manager.assert_owned(s)                       # 4 Nov: no block; the new card is its next instruction
    assert s['resume_note']['facts']['text']=='corrected acceptance' and s['basis']['text']=='corrected acceptance'
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


def test_retry_cannot_replay_a_started_or_uncertain_turn(manager):
    s=state(manager,'blocked');s['session']='a-real-thread'
    assert 'refused' in manager.retry(msg())
    s.pop('session');s['phase']='uncertain'
    assert 'refused' in manager.retry(msg())


def test_retry_retains_claim_tree_and_only_runs_unchanged_prethread_failure(manager):
    s=state(manager,'blocked');manager.session=lambda _:manager.fixture_door
    manager.git=lambda cwd,*args:'a' if args[0]=='rev-parse' else ''
    original=(s['run'],s['tree'])
    with patch.object(B.threading.Thread,'start') as launch:
        assert manager.retry(msg()).get('external')
        assert launch.call_count==1
    assert (s['run'],s['tree'])==original
    assert s['phase']=='preparing'


def test_retry_refuses_changed_source(manager):
    s=state(manager,'blocked');manager.session=lambda _:manager.fixture_door
    manager.git=lambda cwd,*args:'b'
    with patch.object(B.threading, 'Thread') as thread:
        assert manager.retry(msg()).get('external')
        target=thread.call_args.kwargs['target'];args=thread.call_args.kwargs['args']
        target(*args)
    assert s['phase']=='blocked'
    assert 'tree has changes' in s['detail']


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


def landing_repo(manager, edit):
    """main with a three-line file, a reviewed candidate that changes line three, and someone's uncommitted edit."""
    b=manager;repo=b.repo;repo.mkdir(exist_ok=True)
    b.git(repo,'init','-b','main');b.git(repo,'config','user.name','Fixture');b.git(repo,'config','user.email','fixture@invalid')
    b.git(repo,'config','core.autocrlf','false')         # as in the canonical checkout
    (repo/'shared.py').write_bytes(b'one\ntwo\nthree\n');(repo/'only.py').write_bytes(b'old\n')
    b.git(repo,'add','.');b.git(repo,'commit','-qm','base');base=b.git(repo,'rev-parse','HEAD')
    tree=repo.parent/'tree';b.git(repo,'worktree','add','-q','-b','worker/fx',str(tree))
    (tree/'shared.py').write_bytes(b'one\ntwo\nthree, landed\n');(tree/'only.py').write_bytes(b'new\n');(tree/'added.py').write_bytes(b'added\n')
    b.git(tree,'add','.');b.git(tree,'commit','-qm','candidate');cand=b.git(tree,'rev-parse','HEAD')
    (repo/'shared.py').write_bytes(edit)
    s=state(manager,'reviewed');s.update(review_base=base,candidate=cand,tree=str(tree))
    manager.session=lambda _:manager.fixture_door
    return s,base,cand


def test_landing_keeps_someone_elses_uncommitted_edits_on_top(manager):
    s,base,cand=landing_repo(manager,b'one, being reworked\ntwo\nthree\n')
    manager.publish(s)
    repo=manager.repo
    assert s['phase']=='landed' and manager.git(repo,'rev-parse','HEAD')==cand
    assert (repo/'shared.py').read_bytes()==b'one, being reworked\ntwo\nthree, landed\n'
    assert (repo/'only.py').read_bytes()==b'new\n' and (repo/'added.py').read_bytes()==b'added\n'
    assert manager.git(repo,'diff','--name-only','HEAD')=='shared.py'          # still theirs, still uncommitted
    assert '+one, being reworked' in manager.git(repo,'diff','HEAD')
    assert manager.git(repo,'diff','--cached','--name-only')==''
    assert (manager.home/s['run']/'carried/shared.py').read_bytes()==b'one, being reworked\ntwo\nthree\n'


def test_landing_retries_a_busy_file_and_names_one_it_could_not_write(manager, monkeypatch):
    s,base,cand=landing_repo(manager,b'one, being reworked\ntwo\nthree\n')
    monkeypatch.setattr(B.time,'sleep',lambda _:None)
    real=Path.write_bytes;fails={'n':2}
    def busy(self,data):
        if self.name=='shared.py' and self.parent==manager.repo and fails['n']:
            fails['n']-=1;raise OSError(22,'Invalid argument')
        return real(self,data)
    monkeypatch.setattr(Path,'write_bytes',busy)
    manager.publish(s)
    assert s['phase']=='landed' and 'NOT carried' not in s['detail']
    assert (manager.repo/'shared.py').read_bytes()==b'one, being reworked\ntwo\nthree, landed\n'
    s2,_,_=landing_repo_again(manager)
    fails['n']=99
    manager.publish(s2)
    assert s2['phase']=='landed' and 'NOT carried' in s2['detail'] and 'shared.py' in s2['detail']


def landing_repo_again(manager):
    """A second reviewed candidate on top of the first; line one's uncommitted edit is still there."""
    repo=manager.repo;tree=repo.parent/'tree';base=manager.git(repo,'rev-parse','HEAD')
    manager.git(tree,'reset','-q','--hard',base)
    (tree/'only.py').write_bytes(b'newer\n');(tree/'shared.py').write_bytes(b'one\ntwo\nthree, landed again\n')
    manager.git(tree,'commit','-qam','second');cand=manager.git(tree,'rev-parse','HEAD')
    s=state(manager,'reviewed');s.update(review_base=base,candidate=cand,tree=str(tree))
    return s,base,cand


def test_a_review_that_conflicts_with_main_leaves_a_clean_tree_and_may_run_again(manager):
    s,base,cand=landing_repo(manager,b'one\ntwo\nthree\n')
    repo=manager.repo;tree=Path(s['tree'])
    (repo/'shared.py').write_bytes(b'one\ntwo\nthree, main moved\n')
    manager.git(repo,'commit','-qam','main moved')
    (tree/'BUILD-RESULT.md').write_text('fixture')
    s.update(phase='reviewing',base=base)
    with pytest.raises(RuntimeError,match='conflicts with this worker in shared.py'):
        manager.review(s)
    assert manager.git(tree,'status','--porcelain','--untracked-files=no')==''
    assert s['review_base']==manager.git(repo,'rev-parse','HEAD')
    s.update(phase='blocked')
    assert manager.request_review(msg('dk1')).get('external')


def test_landing_refuses_a_conflict_and_moves_nothing(manager):
    s,base,cand=landing_repo(manager,b'one\ntwo\nthree, theirs\n')
    with pytest.raises(RuntimeError,match='conflict'):
        manager.publish(s)
    repo=manager.repo
    assert manager.git(repo,'rev-parse','HEAD')==base
    assert (repo/'shared.py').read_bytes()==b'one\ntwo\nthree, theirs\n' and (repo/'only.py').read_bytes()==b'old\n'


def test_a_stale_card_write_is_reread_and_written_again(manager):
    s=state(manager)
    class Busy(WorldDoor):
        def call(self,route,line,**kw):
            if line.startswith('set ') and not getattr(self,'raced',False):
                self.raced=True;self.task['rev']+=1;self.task['next_action']='the lead wrote this'
                raise RuntimeError('refused: stale: dk1 changed since it was read; nothing was done')
            return super().call(route,line,**kw)
    busy=Busy();busy.task['build_run']=s['run'];manager.session=lambda _:busy
    manager.update(s,build_phase='preparing')
    assert busy.task['build_phase']=='preparing' and busy.task['next_action']=='the lead wrote this'


def test_retry_after_the_claim_and_before_a_worktree_prepares_it(manager):
    s=state(manager,'blocked');s.update(claim_records=['r1']);s.pop('tree',None);manager.save(s)
    manager.session=lambda _:manager.fixture_door
    prepared=[]
    manager.prepare=lambda st,door:prepared.append(st['run'])
    out=manager.retry(msg('dk1'))
    assert out.get('external'),out
    import time
    deadline=time.monotonic()+5
    while not prepared and time.monotonic()<deadline:time.sleep(.02)
    assert prepared==[s['run']]


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
    monkeypatch.setattr(B.T, 'PY', Path(sys.executable))
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
            self.events.put(dict(e='turn_started',turn='scripted-turn'))
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


def test_codex_progress_only_publishes_safe_activity():
    assert B.T.reduce({'type':'codex_event','method':'item/completed',
                       'data':{'item':{'type':'reasoning','text':'private'}}})==[]
    tool=B.T.reduce({'type':'codex_event','method':'item/started',
                     'data':{'item':{'type':'commandExecution','command':'TOKEN=private git diff --check'}}})
    assert tool==[{'e':'tool','name':'commandExecution','input':{},
                  'activity':{'summary':'ran: TOKEN=[hidden] git diff --check',
                              'detail':'ran: TOKEN=[hidden] git diff --check'}}]
    assert B.T.reduce({'type':'system','subtype':'init','session_id':'session'})[0]['e']=='init'
    assert B.T.reduce({'type':'system','subtype':'turn_started','turn_id':'turn'})[0]['e']=='turn_started'


def test_codex_public_text_is_not_duplicated_by_final_aggregate():
    import io, queue
    events=[{'type':'codex_event','method':'item/completed',
             'data':{'item':{'type':'agentMessage','text':'Progress'}}},
            {'type':'assistant','message':{'content':[{'type':'text','text':'Progress'}]}},
            {'type':'result','is_error':False}]
    child=B.T.Child.__new__(B.T.Child)
    child.codex_streamed=False;child.log=lambda *a:None;child.events=queue.Queue()
    child.proc=SimpleNamespace(stdout=io.StringIO('\n'.join(json.dumps(e) for e in events)),wait=lambda:0)
    child._read()
    got=[]
    while not child.events.empty():got.append(child.events.get())
    assert [e['text'] for e in got if e['e']=='text']==['Progress']


def test_house_commits_what_a_sandboxed_worker_left(tmp_path):
    """The worker sandbox cannot write .git (index.lock denied), so review commits its tree to the worker's own
    branch: new and changed source go in; BUILD-RESULT.md and top-level dot-folders (temp fixtures) stay out."""
    h=SimpleNamespace(home=tmp_path/'home',m=SimpleNamespace(happen=lambda *a:None))
    repo=tmp_path/'repo';repo.mkdir();b=B.Builders(h,repo)
    b.git(repo,'init','-b','main');b.git(repo,'config','user.name','Fixture');b.git(repo,'config','user.email','fixture@invalid')
    (repo/'value.txt').write_text('before');b.git(repo,'add','.');b.git(repo,'commit','-m','base')
    tree=tmp_path/'tree';b.git(repo,'worktree','add','-b','worker/x',str(tree),'main')
    (tree/'value.txt').write_text('after');(tree/'pkg').mkdir();(tree/'pkg'/'new.py').write_text('x=1\n')
    (tree/'BUILD-RESULT.md').write_text('proof');(tree/'.regression-tmp').mkdir();(tree/'.regression-tmp'/'log').write_text('t')
    s=dict(task='t1',run='kernel-t1-x',name='Codex — fixture',activity=[])
    b.commit_worker(s,tree)
    assert sorted(s['house_commit']['files'])==['pkg/new.py','value.txt']
    assert b.git(tree,'status','--porcelain','--untracked-files=no')==''
    assert b.git(repo,'rev-parse','main')!=s['house_commit']['commit']          # its own branch, never main
    left=b.git(tree,'status','--porcelain')
    assert 'BUILD-RESULT.md' in left and '.regression-tmp' in left
    b.commit_worker(s,tree)                                                      # nothing new: no empty commit
    assert b.git(tree,'rev-parse','HEAD')==s['house_commit']['commit']


@pytest.mark.parametrize('phase,base,ok',[('reviewed','a',True),('blocked','a',True),('blocked',None,False),
                                          ('uncertain','a',False),('working',None,False)])
def test_review_again_only_after_a_review(manager,phase,base,ok):
    """A reviewed result whose main moved, or one whose review checks failed, may be reviewed again by its
    requester; a worker failure before review, an uncertain or an active run may not."""
    s=state(manager,phase)
    if base:s['review_base']=base
    manager.review=lambda st:None
    out=manager.request_review(msg())
    assert ('refused' not in out)==ok,out


def test_a_landed_or_released_card_may_have_a_new_run(manager,monkeypatch):
    """Landed then reverted (dk1025, 27 Oct): the requester can start a second run; the first is kept, marked
    superseded, and never reloaded over the new one. An active run still refuses."""
    started=[]
    monkeypatch.setattr(B.threading,'Thread',lambda target,args,daemon:SimpleNamespace(start=lambda:started.append(args[0])))
    s=state(manager,'working')
    assert 'refused' in manager.start(msg()) or 'existing request' in manager.start(msg()).get('text','')
    s['phase']='landed'
    out=manager.start(msg())
    assert out.get('external'),out
    new=manager.states['dk1']
    assert new['run']!=s['run'] and new['previous_run']==s['run'] and s['superseded_by']==new['run']
    assert started==[new]
