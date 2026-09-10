"""Native presentation actions. Runs in the Linux guest; returns proposed writes."""
import json
import subprocess

RULE='lab.presentation.rule'
HISTORY='lab.presentation.history'

def rows(context):
    result=[]
    for obj in context['objects']:
        facets=obj['facets']; geometry=facets.get('core.appearance')
        if not geometry or geometry.get('scene')!='desk':
            continue
        if 'core.text' not in facets and 'lab.card' not in facets:
            continue
        meta=facets.get('lab.item',{})
        result.append({'id':obj['id'],'type':'card' if 'lab.card' in facets else 'note',
                       'title':facets.get('core.title',{}).get('text','Untitled'),
                       'tags':meta.get('tags',[]),'date':meta.get('date',''),
                       'geometry':{'x':geometry.get('x',16),'y':geometry.get('y',16),
                                   'width':geometry.get('width',245),'height':geometry.get('height',205)}})
    return result

def evaluate(context,rules,viewport=None):
    # One evaluator is embedded in the shell and executed here by the guest Node runtime.
    request={'rows':rows(context),'rules':rules,'viewport':viewport or {'width':900}}
    program="let b='';process.stdin.on('data',d=>b+=d);process.stdin.on('end',()=>process.stdout.write(JSON.stringify(require('./evaluator.js').evaluate(JSON.parse(b)))));"
    process=subprocess.run(['node','-e',program],input=json.dumps(request),text=True,capture_output=True,timeout=3)
    if process.returncode:
        raise ValueError('Presentation evaluator failed: '+process.stderr[:500])
    return json.loads(process.stdout)

def rules(context):
    return [dict(o['facets'][RULE],id=o['id']) for o in context['objects'] if RULE in o['facets']]

def find(context,id):
    return next((o for o in context['objects'] if o['id']==id),None)

def validate(rule):
    allowed={'name','select','style','layout','shell','priority','enabled'}
    if set(rule)-allowed:
        raise ValueError('Unknown rule fields: '+str(sorted(set(rule)-allowed)))
    if not any(k in rule for k in ('style','layout','shell')):
        raise ValueError('A rule needs style, layout or shell properties.')
    selection=rule.get('select',{})
    if set(selection)-{'ids','tag','type'} or selection.get('type','all') not in ('all','note','card'):
        raise ValueError('Selection supports ids, tag, and type all/note/card.')
    style=rule.get('style',{})
    if set(style)-{'surface','text_size','padding','radius','title_size','color'}:
        raise ValueError('Supported style properties: surface, text_size, padding, radius, title_size, color.')
    if style.get('surface','paper') not in ('paper','sage','blue','rose','white'):
        raise ValueError('Surface tokens: paper, sage, blue, rose, white.')
    if 'color' in style:
        import re
        if not re.fullmatch(r'#[0-9A-Fa-f]{6}',style['color']):
            raise ValueError('Text color must be a six-digit hex color.')
    for key,lo,hi in [('text_size',11,28),('title_size',11,32),('padding',0,40),('radius',0,32)]:
        if key in style and (type(style[key]) not in (int,float) or not lo<=style[key]<=hi):
            raise ValueError(f'{key} must be from {lo} to {hi}.')
    layout=rule.get('layout',{})
    if layout:
        if set(layout)-{'kind','columns','gap','width','height','x','y','order','responsive','axis','position','pitch','center_x','center_y','radius'}:
            raise ValueError('Unknown layout parameter; inspect the installed catalog.')
        if layout.get('kind') not in ('grid','align','snap','circle'):
            raise ValueError('Supported layouts: grid, align, snap, circle. Circle uses center_x, center_y and radius; titles run clockwise from the top.')
        for key,lo,hi in [('columns',1,6),('gap',0,80),('width',160,600),('height',140,600),('pitch',4,128),('x',0,4000),('y',0,4000),('position',0,4000),('center_x',0,4000),('center_y',0,4000),('radius',1,2000)]:
            if key in layout and (type(layout[key]) is not int or not lo<=layout[key]<=hi):
                raise ValueError(f'{key} must be an integer from {lo} to {hi}.')
        if layout.get('axis','x') not in ('x','y') or layout.get('order','id') not in ('id','title','date'):
            raise ValueError('axis is x/y; order is id/title/date.')
    shell=rule.get('shell',{})
    if set(shell)-{'chat','height','composer'} or shell.get('chat','right') not in ('right','bottom'):
        raise ValueError('Shell supports chat right/bottom, height and composer.')
    for key,lo,hi in [('height',220,500),('composer',48,160)]:
        if key in shell and (type(shell[key]) is not int or not lo<=shell[key]<=hi):
            raise ValueError(f'{key} must be from {lo} to {hi}.')

def catalog(arguments,context):
    return {'result':{'contract':'presentation-1','selection':'live by type note/card/all, ids or lab.item.tags tag',
        'styles':{'surface':['paper','sage','blue','rose','white'],'text_size':[11,28],'title_size':[11,32],'padding':[0,40],'radius':[0,32],'color':'#RRGGBB'},
        'layout':{'kind':['grid','align','snap','circle'],'center_x':[0,4000],'center_y':[0,4000],'radius':[1,2000],'circle':'Equal angles clockwise from top; centers use center_x/center_y (defaults 500/350), radius default 260; upright fixed-size cards; live membership and title order','columns':[1,6],'gap':[0,80],'width':[160,600],'height':[140,600],'x':[0,4000],'y':[0,4000],'order':['id','title','date'],'responsive':'default true','axis':['x','y'],'position':[0,4000],'pitch':[4,128]},
        'shell':{'chat':['right','bottom'],'height':[220,500],'composer':[48,160]},
        'precedence':'Ascending priority then rule id; last matching contributor wins per style property and layout. Higher priority overrides. Mobile retains the original tab interface.',
        'manual':'Maintained layout owns effective geometry. Use the per-surface Free placement button to create a local exception before dragging; Resume layout removes it.',
        'limits':['Circle is fixed geometry, not a collision/force solver. It may overlap other surfaces or crowd as membership grows. Mobile retains its stacked layout. No semantic content transforms, remote-app internals or overflow-free impossible fitting.','Viewport should come from experiment.observe. Default preview width is 900.'],
        'example':{'id':'reading-style','expected_revision':0,'rule':{'name':'Reading comfort','select':{'tag':'reading'},'style':{'surface':'paper','text_size':18,'padding':20},'priority':10}}}}

def preview(arguments,context):
    proposal=arguments.get('rule')
    current=rules(context)
    if proposal is not None:
        validate(proposal)
        id=arguments.get('id','preview-rule')
        current=[r for r in current if r['id']!=id]+[dict(proposal,id=id)]
    return {'result':evaluate(context,current,arguments.get('viewport'))}

def put(arguments,context):
    validate(arguments['rule'])
    id=arguments['id']; old=find(context,id)
    revision=old['revision'] if old else 0
    if arguments['expected_revision']!=revision:
        raise ValueError('Rule changed; read the current rule revision before editing.')
    history=find(context,'presentation-history')
    stack=(history or {}).get('facets',{}).get(HISTORY,{}).get('entries',[])
    entry={'id':id,'before':old['facets'].get(RULE) if old else None,'after':arguments['rule']}
    return {'result':{'rule':id,'revision':revision+1,'saved':True},'changes':[
        {'id':id,'expected_revision':revision,'facets':{RULE:arguments['rule']}},
        {'id':'presentation-history','expected_revision':history['revision'] if history else 0,'facets':{HISTORY:{'entries':(stack+[entry])[-30:]}}}]}

def remove(arguments,context):
    old=find(context,arguments['id'])
    if not old or RULE not in old['facets']:
        raise ValueError('Rule not found.')
    return put(dict(arguments,rule=dict(old['facets'][RULE],enabled=False)),context)

def undo(arguments,context):
    history=find(context,'presentation-history')
    entries=(history or {}).get('facets',{}).get(HISTORY,{}).get('entries',[])
    if not entries:
        raise ValueError('No presentation edits to undo.')
    change=entries[-1]; current=find(context,change['id'])
    if current['facets'].get(RULE)!=change['after']:
        raise ValueError('Undo would overwrite a later rule edit; inspect and resolve it.')
    return {'result':{'undone':change['id']},'changes':[
        {'id':change['id'],'expected_revision':current['revision'],'facets':{RULE:change['before']}},
        {'id':history['id'],'expected_revision':history['revision'],'facets':{HISTORY:{'entries':entries[:-1]}}}]}

def inspect(arguments,context):
    return {'result':{'rules':[{'id':o['id'],'revision':o['revision'],'rule':o['facets'][RULE]} for o in context['objects'] if RULE in o['facets']],
                      'effective':evaluate(context,rules(context),arguments.get('viewport'))}}

def apply(arguments,context):
    validate(arguments['rule'])
    if not arguments['rule'].get('layout') or arguments['rule'].get('style') or arguments['rule'].get('shell'):
        raise ValueError('Apply-once supports layout only; use put for retained style/shell rules.')
    result=evaluate(context,[dict(arguments['rule'],id='one-shot')],arguments.get('viewport'))
    changes=[]
    for row in result['rows']:
        if row['sources'].get('layout')!='one-shot':
            continue
        obj=find(context,row['id']); geometry=obj['facets']['core.appearance']|row['geometry']
        if geometry!=obj['facets']['core.appearance']:
            changes.append({'id':row['id'],'expected_revision':obj['revision'],'facets':{'core.appearance':geometry}})
    return {'result':result,'changes':changes}
