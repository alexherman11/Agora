"""Viewer-scoped component observations and narrowly bounded recovery words."""
import json
import math

from kernel.kernel import Refused, GONE


def component_status(k,actor,name):
    reports=[k.shown(actor.person,t) for t in k.things('paint-report')]
    reports=[r for r in reports if r and r.get('viewer')==actor.person and r.get('component')==name]
    if not reports:return dict(health='unobserved',last_error='',quarantined=False)
    failures=[r for r in reports if r.get('health') in ('stopped','slow')]
    latest=max(failures or reports,key=lambda r:r.get('observed_at',''))
    return dict(health=latest.get('health','unobserved'),last_error=latest.get('last_error',''),quarantined=any(r.get('quarantined') for r in reports))


def plan_for(k, actor, target):
    from painter.arrangement import compile_view
    plan=compile_view(k,actor,target)['rows'][0]
    if actor.kind=='module':
        widget=k.shown(actor.person,actor.module)
        if not widget or widget.get('kind')!='widget':raise Refused('component report needs its painter instance')
        own=compile_view(k,actor,widget.get('component_lens',''))['rows'][0]
        if own['lens']!=plan['lens']:raise Refused('a painter reports or recovers only its own lens')
    return plan


def report_thing(k,actor,tx,lens,path):
    for (t,key),value in tx.over.items():
        if key=='kind' and value=='paint-report' and tx.get(t,'viewer')==actor.person and tx.get(t,'lens')==lens and tx.get(t,'path')==path:return t
    for t in k.things('paint-report'):
        a=k.shown(actor.person,t)
        if a and a.get('viewer')==actor.person and a.get('lens')==lens and a.get('path')==path:return t
    t=tx.mint()
    for key,value in dict(kind='paint-report',viewer=actor.person,lens=lens,path=path,made_by=actor.id,
                          sees='person:'+actor.person,**{'in:'+k.place:len(k.log.records)+1}).items():tx.set(t,key,value)
    return t


def component_health(k,actor,st,entry,tx,group,saw=None):
    if actor.kind!='module':raise Refused('component-health is a running painter observation')
    plan=plan_for(k,actor,st.target or st.words.strip())
    try:reports=json.loads(st.kv.get('data',''))
    except ValueError:raise Refused('health data needs a JSON array')
    if not isinstance(reports,list) or len(reports)>150:raise Refused('health data: at most 150 part observations')
    paths={p['part']:p for p in plan['parts']}
    for report in reports:
        if not isinstance(report,dict) or report.get('path') not in paths:raise Refused('health part is not in this viewer projection')
        if report.get('health') not in ('healthy','stopped','slow','starting'):raise Refused('health: healthy, stopped, slow or starting')
        elapsed=report.get('elapsed_ms',0)
        if not isinstance(elapsed,(int,float)) or not math.isfinite(elapsed) or not 0<=elapsed<1e9:raise Refused('elapsed_ms must be finite and nonnegative')
        painted=report.get('painted',[])
        if not isinstance(painted,list) or len(painted)>80 or len(json.dumps(painted))>12000:raise Refused('paint observation is too large')
        t=report_thing(k,actor,tx,plan['lens'],report['path'])
        tx.parts[-1]['target']=t
        tx.parts[-1]['words']='component-health · private painter observation'
        health=report['health'];failures=int(tx.get(t,'failures',0))+(health in ('stopped','slow'))
        for key,value in dict(component=paths[report['path']]['component'],health=health,last_error=str(report.get('last_error','')).split('\n')[0][:300],
                              failures=failures,quarantined=bool(tx.get(t,'quarantined',False) or failures>=2),
                              painted=painted,elapsed_ms=round(elapsed,3),source=str(report.get('source',''))[:100],
                              observed_at=k.now().isoformat()).items():tx.set(t,key,value)
    return dict(text='ok component observations',rows=[])


def component_action(k,actor,st,entry,tx,group,saw=None):
    plan=plan_for(k,actor,st.target or st.words.strip());path=st.kv.get('path','')
    node=next((p for p in plan['parts'] if p['part']==path),None)
    if node is None:raise Refused('choose a part in look-view')
    action=st.kv.get('action','retry')
    if action not in ('retry','previous','off','clear'):raise Refused('action: retry, previous, off or clear')
    t=report_thing(k,actor,tx,plan['lens'],path)
    tx.parts[-1]['target']=t
    tx.parts[-1]['words']='component-action '+action+' · private part control'
    if action=='clear':
        if not k.is_steward(actor.person):raise Refused('only a steward clears quarantine')
        tx.set(t,'quarantined',False);tx.set(t,'failures',0)
    if action=='previous':
        # Restore only the latest changed field owned by this part's definition
        # or arrangement, never an unrelated act or a whole transaction.
        definition=next((c for c in plan['components'] if c.get('name')==node['component']),{})
        choices=[(definition.get('id'),'code'),(plan['lens'],'text')]
        choices += [(p,key) for p in k.things('view-preference') if k.state.get(p,'lens') in (plan['lens'],k.state.get(plan['lens'],'name'))
                    and (k.state.get(p,'made_by')==actor.person or k.state.get(p,'for')==actor.person)
                    for key in k.state.things[p] if key.startswith(node['name']+'.') or key=='text']
        # Genesis/make is not a previous version. A read revision from the card
        # is mandatory, so an intervening edit cannot silently be rolled back.
        candidates=[(k.state.last_seq(target,field),target,field) for target,field in choices if target and len(k.state.history.get((target,field),[]))>1]
        if not candidates:raise Refused('this part has no previous code or setting version')
        seq,target,field=max(candidates)
        if (saw or {}).get(target) not in (k.state.rev.get(target),{'rev':k.state.rev.get(target)}):raise Refused('part changed since the stopped card; try again to read its current version')
        if not (k.is_steward(actor.person) or k.state.get(target,'made_by')==actor.person or k.state.get(target,'for')==actor.person):raise Refused('previous version needs its maker or a steward')
        tx.set(target,field,k.state.before(target,field,seq))
        if field=='code':
            # Restoring code never silently grants review; it runs in quarantine
            # until an explicit steward component review.
            tx.set(t,'quarantined',True)
    tx.set(t,'disabled',action=='off')
    tx.set(t,'health','off' if action=='off' else 'unobserved')
    tx.set(t,'last_error','')
    tx.set(t,'action_epoch',int(tx.get(t,'action_epoch',0))+1)
    return dict(text='ok '+node['component']+' '+action)


def personal_view(k,actor,st,entry,tx,group,saw=None):
    from kernel.words import make
    from kernel.lines import Step
    plan=plan_for(k,actor,st.target or st.words.strip())
    values=dict(st.kv,kind='view-preference',sees='me',lens=plan['lens'])
    return make(k,actor,Step(st.text,'make',None,values,''),entry,tx,group,saw)


def personal_style(k,actor,st,entry,tx,group,saw=None):
    from kernel.words import make
    from kernel.lines import Step
    plan=plan_for(k,actor,st.target or st.words.strip())
    values=dict(st.kv,kind='part-style',sees='me',personal='yes',lens=plan['lens'])
    return make(k,actor,Step(st.text,'make',None,values,''),entry,tx,group,saw)
