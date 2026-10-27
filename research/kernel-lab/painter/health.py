"""Viewer-scoped component observations and narrowly bounded recovery words.

26 Oct 2026 (builder draft, after Alex: "visual state should not live in the world"). A painter's health is screen state:
what a part painted, how long it took, that it stopped, that it is quarantined. It is kept in the kernel process's memory
(`local(k)`), per viewer, lens and part, and never written to the log; a restart forgets it, as screen state should be
forgotten. What stays in the world is intent: turning a part off for yourself (a private view-preference) and restoring a
previous code or setting version (an ordinary recorded change). Old `paint-report` things, written before this, are removed
in one act by the steward word `paint-clear`.
"""
import json
import math
import threading

from kernel.kernel import Refused, GONE

_LOCK = threading.Lock()


def local(k):
    """The kernel process's own table of paint health: {(viewer, lens id, part path): {...}}. Never in k.state."""
    table = getattr(k, '_paint_health', None)
    if table is None:
        with _LOCK:
            table = getattr(k, '_paint_health', None)
            if table is None:
                table = {}
                k._paint_health = table
    return table


def reports_for(k, viewer, lens):
    """{path: health} of one viewer's one lens."""
    return {path: dict(h) for (v, l, path), h in list(local(k).items()) if v == viewer and l == lens}


def component_status(k, actor, name):
    reports = [h for (v, _l, _p), h in list(local(k).items()) if v == actor.person and h.get('component') == name]
    if not reports: return dict(health='unobserved', last_error='', quarantined=False)
    failures = [r for r in reports if r.get('health') in ('stopped', 'slow')]
    latest = max(failures or reports, key=lambda r: r.get('observed_at', ''))
    return dict(health=latest.get('health', 'unobserved'), last_error=latest.get('last_error', ''),
                quarantined=any(r.get('quarantined') for r in reports))


def plan_for(k, actor, target):
    from painter.arrangement import compile_view
    plan=compile_view(k,actor,target)['rows'][0]
    if actor.kind=='module':
        widget=k.shown(actor.person,actor.module)
        if not widget or widget.get('kind')!='widget':raise Refused('component report needs its painter instance')
        own=compile_view(k,actor,widget.get('component_lens',''))['rows'][0]
        if own['lens']!=plan['lens']:raise Refused('a painter reports or recovers only its own lens')
    return plan


def part_of(plan, path):
    """The plan part a path names. A repeated slot (api.child with a key) paints `<slot path>#<key>`: its own owner and
    health, reported against the slot it repeats."""
    path = str(path or '')
    parts = {p['part']: p for p in plan['parts']}
    return parts.get(path) or parts.get(path.split('#', 1)[0])


def _entry(k, viewer, lens, path):
    table = local(k)
    with _LOCK:
        return table.setdefault((viewer, lens, path), dict(health='unobserved', last_error='', failures=0,
                                                             quarantined=False, action_epoch=0))


def component_health(k,actor,st,entry,tx,group,saw=None):
    """Local only: nothing is recorded, nothing is written into the world, no happening is sent."""
    if actor.kind!='module':raise Refused('component-health is a running painter observation')
    plan=plan_for(k,actor,st.target or st.words.strip())
    try:reports=json.loads(st.kv.get('data',''))
    except ValueError:raise Refused('health data needs a JSON array')
    if not isinstance(reports,list) or len(reports)>150:raise Refused('health data: at most 150 part observations')
    checked = []
    for report in reports:
        if not isinstance(report,dict) or len(str(report.get('path', ''))) > 500 or part_of(plan, report.get('path')) is None:
            raise Refused('health part is not in this viewer projection')
        if report.get('health') not in ('healthy','stopped','slow','starting'):raise Refused('health: healthy, stopped, slow or starting')
        elapsed=report.get('elapsed_ms',0)
        if not isinstance(elapsed,(int,float)) or not math.isfinite(elapsed) or not 0<=elapsed<1e9:raise Refused('elapsed_ms must be finite and nonnegative')
        checked.append(report)
    now = k.now().isoformat()
    for report in checked:
        h = _entry(k, actor.person, plan['lens'], str(report['path']))
        health = report['health']
        failures = int(h.get('failures', 0)) + (health in ('stopped', 'slow'))
        # Painted text and computed styles are never kept, here or in the world (Alex, 26 Oct).
        h.update(component=part_of(plan, report['path'])['component'], health=health,
                 last_error=str(report.get('last_error', '')).split('\n')[0][:300], failures=failures,
                 quarantined=bool(h.get('quarantined') or failures >= 2), elapsed_ms=round(elapsed, 3),
                 source=str(report.get('source', ''))[:100], observed_at=now)
    return dict(text='ok component observations (kept on this screen, not in the world)',rows=[])


def component_action(k,actor,st,entry,tx,group,saw=None):
    plan=plan_for(k,actor,st.target or st.words.strip());path=st.kv.get('path','')
    node=part_of(plan, path)
    if node is None:raise Refused('choose a part in look-view')
    action=st.kv.get('action','retry')
    if action not in ('retry','previous','off','clear'):raise Refused('action: retry, previous, off or clear')
    if action=='clear' and not k.is_steward(actor.person):raise Refused('only a steward clears quarantine')
    h=_entry(k,actor.person,plan['lens'],path)
    mine=[p for p in k.things('view-preference') if k.state.get(p,'lens') in (plan['lens'],k.state.get(plan['lens'],'name'))
          and (k.state.get(p,'made_by') in (actor.person,actor.id) or k.state.get(p,'for')==actor.person)
          and not k.state.get(p,'forgotten')]
    off_key=node['name']+'.enabled'
    text='ok '+node['component']+' '+action
    if action=='off':
        # Turning a part off is the viewer's own intent: a private preference, recorded, and undo takes it back. Written
        # here (not through make) so a painter whose make grant reaches only its domain kinds can still offer it.
        tx.parts[-1]['words']='component-action off · just for me'
        p=tx.mint()
        for key,value in {'kind':'view-preference','lens':plan['lens'],off_key:'no','made_by':actor.id,
                          'sees':'person:'+actor.person,'in:'+k.place:len(k.log.records)+1}.items():tx.set(p,key,value)
        if actor.id!=actor.person:tx.set(p,'for',actor.person)
        tx.parts[-1]['target']=p
        text+=' · turned off just for you (undo turns it on again)'
    elif action=='retry':
        # Try again also turns a part back on when the viewer had turned it off.
        for p in mine:
            if str(k.state.get(p,off_key,'')).lower() in ('no','false','0'):
                tx.parts[-1]['target']=p
                tx.set(p,off_key)
    elif action=='clear':
        h.update(quarantined=False,failures=0)
    elif action=='previous':
        # Restore only the latest changed field owned by this part's definition
        # or arrangement, never an unrelated act or a whole transaction.
        definition=next((c for c in plan['components'] if c.get('name')==node['component']),{})
        choices=[(definition.get('id'),'code'),(plan['lens'],'text')]
        choices += [(p,key) for p in mine for key in k.state.things[p] if key.startswith(node['name']+'.') or key=='text']
        # Genesis/make is not a previous version. A read revision from the card
        # is mandatory, so an intervening edit cannot silently be rolled back.
        candidates=[(k.state.last_seq(target,field),target,field) for target,field in choices if target and len(k.state.history.get((target,field),[]))>1]
        if not candidates:raise Refused('this part has no previous code or setting version')
        seq,target,field=max(candidates)
        if (saw or {}).get(target) not in (k.state.rev.get(target),{'rev':k.state.rev.get(target)}):raise Refused('part changed since the stopped card; try again to read its current version')
        if not (k.is_steward(actor.person) or k.state.get(target,'made_by')==actor.person or k.state.get(target,'for')==actor.person):raise Refused('previous version needs its maker or a steward')
        tx.parts[-1]['target']=target
        tx.parts[-1]['words']='component-action previous · '+node['component']
        tx.set(target,field,k.state.before(target,field,seq))
        if field=='code':
            # Restoring code never silently grants review; it runs in quarantine
            # until an explicit steward component review.
            h['quarantined']=True
    h.update(health='unobserved',last_error='',action_epoch=int(h.get('action_epoch',0))+1)
    return dict(text=text)


def paint_clear(k,actor,st,entry,tx,group,saw=None):
    """Forget every old paint-report thing in one act: screen state that the painter used to write into the world."""
    if not k.is_steward(actor.person):raise Refused('only a steward clears old paint reports')
    old=[t for t in k.things('paint-report') if not k.state.get(t,'forgotten')]
    if not old:return dict(text='no paint reports left; paint health is kept on the screen now',rows=[])
    tx.parts[-1]['words']=f'paint-clear · {len(old)} old paint reports'
    for t in old:
        tx.set(t,'forgotten',actor.person)   # no forget_reason: that is a moderator's note, and boards list those
    return dict(text=f'ok paint-clear [r?] · {len(old)} old paint reports out of every view, in one act; undo brings them back',rows=[])


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
