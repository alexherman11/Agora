"""General reading/Blob transport admission. No processes, browser or live world."""
import json
import sys
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'src/agora'),str(ROOT/'src/desktop/kernel-desktop')]
from kernel.kernel import Kernel,Refused
from kernel.blobs import receive
from widgets import Widgets


def Q(value):return '"'+str(value).replace('\\','\\\\').replace('"','\\"')+'"'


@pytest.fixture
def host(tmp_path):
    k=Kernel(tmp_path/'world',dict(tag='ut',name='Transport test',steward=dict(account='alex',name='Alex'),
                                 invites_counted_by='kernel',invites=[dict(code='x',uses=3)]))
    a=k.actor_for(k.accounts['alex'])
    b=k.actor_for(k.join('bea','Bea',invite='x')['person'])
    def say(actor,command):
        out=k.run(actor,command);assert out['ok'],out;return out
    mid=say(a,'module window run='+Q('["unused"]')+' publishes="window.*" grants="rows look"')['made'][0]
    k.on_offer(mid,[dict(word='window.surface',kind='hold',may='anyone',help='Hold a scratch surface')])
    source='root : column, of reading:"rows post title=$view.query" as p, limit 2, offset $view.offset, each item\nitem : text "$p.text"'
    say(a,'make kind=lens name=transport painter=components view='+Q(json.dumps(dict(query='',offset=0)))+' text='+Q(source))
    widget=say(a,'make kind=widget name=transport component_lens=transport code="test"')['made'][0]
    say(a,'look '+widget);say(a,'widget '+widget+' grants="window.surface rows look look-view file-read component-health component-action"')
    broker=Widgets(k)
    instances={actor.id:broker.request(actor,'open',dict(widget=widget))['instance'] for actor in (a,b)}
    def call(actor,op,**args):return broker.request(actor,'call',dict(instance=instances[actor.id],op=op,**args))
    return k,a,b,say,call,broker,instances,widget


def test_reading_collection_keeps_viewer_permissions_and_bounds_construction(host):
    k,a,b,say,call,*_=host
    private=say(a,'post text="PRIVATE-PROJECTION-SENTINEL" sees=me')['made'][0]
    for i in range(4):say(a,'post text='+Q('Public '+str(i)))
    own=call(a,'project',view={})['rows'][0];other=call(b,'project',view={})['rows'][0]
    assert len(own['tree']['children'])==2 and own['tree']['collection']['total']==5
    assert len(other['tree']['children'])==2 and other['tree']['collection']['total']==4
    assert private not in json.dumps(other) and 'PRIVATE-PROJECTION' not in json.dumps(other)
    assert all(child['saw'] for child in other['tree']['children'])


def test_dynamic_reading_values_are_data_and_see_cannot_act(host):
    k,a,b,say,call,*_=host
    before=len(k.log.records)
    out=call(b,'project',view=dict(query='x"; post text="INJECTED',offset=0))
    assert out['ok'],out
    assert len(k.log.records)==before
    lens=next(t for t in k.things('lens'))
    say(a,'look '+lens);say(a,'set '+lens+' text='+Q('root : column, of reading:"post text=UNAUTHORISED" as p, each item\nitem : text "$p.text"'))
    with pytest.raises(Refused):call(b,'project',view={})
    assert not any(k.state.get(t,'text')=='UNAUTHORISED' for t in k.things('post'))


def test_file_check_requires_viewer_visibility_grant_and_live_instance(host):
    k,a,b,say,call,broker,instances,widget=host
    result=receive(k,a,b'Private file bytes','private.txt',None)
    file=result['made'][0]
    assert call(a,'file-check',target=file)['path'].startswith('/files/'+file)
    assert not call(b,'file-check',target=file)['ok']
    for target in ['../keep/sessions.json','https://elsewhere.invalid/x','a'*64]:
        with pytest.raises(Refused):call(a,'file-check',target=target)
    with pytest.raises(Refused):call(a,'file-check',target=file,variant='original')
    say(a,'look '+widget);say(a,'off '+widget)
    with pytest.raises(Refused):call(a,'file-check',target=file)


def test_cached_reading_does_not_keep_a_newly_hidden_post_visible(host):
    k,a,b,say,call,broker,instances,widget=host
    target=say(a,'post text="Initially shared"')['made'][0]
    result=call(b,'project',view={});assert result['ok'],result
    plan=result['rows'][0]
    assert target in json.dumps(plan)
    say(a,'look '+target);say(a,'forget '+target)
    # Health/action validation reuses the instance projection, rechecking IDs.
    principal=broker.instances[instances[b.id]]['p']
    out=principal.run('look-view transport plan=yes',mode='see')
    assert target not in json.dumps(out) and 'Initially shared' not in json.dumps(out)


def test_agent_origin_is_kernel_owned_through_a_module_wrapper(host):
    from kernel.kernel import Actor
    k,a,b,say,call,broker,instances,widget=host
    agent=k.actor_for(a.person,'Neighbour helper')
    say(a,'grant '+widget+' words="post make"')
    wrapper=Actor(widget,a.person,'module',module=widget,caller=agent)
    target=say(wrapper,'post text="Shared by an agent through a reviewed wrapper"')['made'][0]
    assert k.state.get(target,'via_actor')==agent.id
    assert k.state.get(target,'for')==a.person and k.state.get(target,'made_by')==widget
    assert not k.run(a,'post text=Forged via_actor='+agent.id)['ok']
    say(a,'look '+target)
    assert not k.run(a,'set '+target+' via_actor=other')['ok']


def test_ui_labels_keep_domain_values_and_personal_scope(host):
    k,a,b,say,call,*_=host
    lens=next(t for t in k.things('lens'))
    text='root : text "Reply"\n  labels ui {"Reply":"Responder"}'
    say(a,'look '+lens);say(a,'set '+lens+' text='+Q(text))
    plan=call(b,'project',view={})['rows'][0]
    assert plan['tree']['settings']['text']=='Reply' and plan['tree']['labels']=={'Reply':'Responder'}
    say(a,'personal-view transport root.labels.ui='+Q('{"Reply":"Contestar"}'))
    assert call(a,'project',view={})['rows'][0]['tree']['labels']=={'Reply':'Contestar'}
    assert call(b,'project',view={})['rows'][0]['tree']['labels']=={'Reply':'Responder'}


def test_poll_options_preserve_declared_case_and_sealed_counts(host):
    k,a,b,say,*_=host
    poll=say(a,'make kind=poll title="Which day?" options="Saturday Sunday"')['made'][0]
    say(b,'vote '+poll+' Saturday')
    assert k.shown(a.person,poll)['votes_Saturday']==1
    say(a,'vote '+poll+' sunday')
    shown=k.shown(b.person,poll)
    assert shown['options']=='Saturday Sunday' and shown['votes_Sunday']==1
    assert not any(key.startswith('vote:') for key in shown)


def test_json_bindings_watch_readings_and_private_opening_defaults(host):
    k,a,b,say,call,*_=host
    lens=next(t for t in k.things('lens'))
    component=say(a,'make kind=component name=structured settings='+Q('{"content":{"type":"json"}}')+' parts="{}" slots="[]" code="example"')['made'][0]
    private=say(a,'post text="Private watched text" sees=me')['made'][0]
    source='root : column\n  watch reading:"rows post"\n  state : text "$view.query"\n  items : column, of reading:"rows post" as p, each item\nitem : structured, content $p'
    say(a,'look '+lens);say(a,'set '+lens+' text='+Q(source))
    own=call(a,'project',view={})['rows'][0];other=call(b,'project',view={})['rows'][0]
    content=own['tree']['children'][1]['children'][0]['settings']['content']
    assert isinstance(content,dict) and content['id']==private and content['text']=='Private watched text'
    assert private not in json.dumps(other) and 'Private watched text' not in json.dumps(other)
    say(a,'personal-view transport view.query="My opening preference"')
    assert call(a,'project',view={})['rows'][0]['view']['query']=='My opening preference'
    assert call(b,'project',view={})['rows'][0]['view']['query']==''
    assert call(a,'project',view=dict(query='This window'))['rows'][0]['view']['query']=='This window'
