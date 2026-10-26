"""Data-only arrangement compiler. No component JavaScript runs to describe a view."""
import hashlib
import json
import re
import math
from collections import Counter

from kernel.kernel import Refused
from painter.handles import style_values, present


def pieces(text):
    parts, current, quote, escaped = [], '', False, False
    for ch in text:
        if escaped: current += ch; escaped = False; continue
        if ch == '\\': current += ch; escaped = True; continue
        if ch == '"': quote = not quote
        if ch == ',' and not quote:
            if current.strip(): parts.append(current.strip())
            current = ''
        else: current += ch
    if current.strip(): parts.append(current.strip())
    return parts


def literal(value):
    if value.startswith('"') and value.endswith('"'):
        try: return json.loads(value)
        except ValueError: return value[1:-1]
    return value


def parse(text):
    roots, stack = {}, []
    for number, raw in enumerate(text.splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith('#'):
            continue
        depth, line = len(raw)-len(raw.lstrip()), raw.strip()
        while stack and stack[-1][0] >= depth:
            stack.pop()
        match = re.match(r'([\w-]+)\s*:\s*([\w-]+)(.*)', line)
        if match:
            name, kind, tail = match.groups()
            node = dict(name=name, component=kind, settings={}, children=[], gestures=[], query=None)
            if tail.lstrip().startswith('"'):
                first, *rest = pieces(tail.lstrip())
                node['settings']['text'] = literal(first)
                tail = ','.join(rest)
            for clause in pieces(tail.lstrip(', ')):
                if clause.startswith('role '):
                    node['role'] = clause[5:]
                elif clause.startswith('of '):
                    node['query'] = clause[3:]
                elif clause.startswith('prop:'):
                    node['query'] += ',' + clause
                elif clause.startswith('by '):
                    node['by'] = clause[3:]
                elif clause.startswith('each '):
                    node['each'] = clause[5:]
                elif clause.startswith('only when '):
                    node['when'] = clause[10:]
                else:
                    key, _, value = clause.partition(' ')
                    node['settings'][key] = literal(value)
            if stack:
                stack[-1][1]['children'].append(node)
            else:
                if name in roots:
                    raise Refused(f'lens line {number}: duplicate part {name}')
                roots[name] = node
            stack.append((depth, node))
        elif stack:
            node = stack[-1][1]
            if line.startswith('on ') and ' do ' in line:
                event, command = line[3:].split(' do ', 1)
                node['gestures'].append(dict(event=event, line=command))
            elif line.startswith('only when '):
                node['when'] = line[10:]
            elif line.startswith('setting '):
                key, value = line[8:].split('=', 1)
                node['settings'][key.strip()] = literal(value.strip())
            elif line.startswith('format '):
                key, _, formatter=line[7:].partition(' ')
                node.setdefault('formats',{})[key]=formatter.removeprefix('as ')
            elif line.startswith('labels '):
                key, _, mapping=line[7:].partition(' ')
                try:node.setdefault('labels',{})[key]=json.loads(literal(mapping))
                except ValueError:raise Refused('labels <setting> <JSON object>')
                if not isinstance(node['labels'][key],dict):raise Refused('labels needs a JSON object')
            elif line.startswith('when ') and ' play ' in line:
                trigger, token=line[5:].split(' play ',1)
                if not re.fullmatch(r'(?:fact [\w.-]+ changes|happening [\w.*-]+)',trigger):raise Refused('when fact <field> changes play <token>, or when happening <word> play <token>')
                node.setdefault('motions',[]).append(dict(trigger=trigger,token=token))
            else:
                raise Refused(f'lens line {number}: unknown arrangement word {line}')
        else:
            raise Refused(f'lens line {number}: expected a part')
    if 'root' not in roots:
        raise Refused('component lens needs root : <component>')
    return roots


REF = re.compile(r'\$([\w.-]+)')


def resolve(text, env):
    def value(match):
        path = match[1].split('.')
        v = env
        for bit in path:
            v = v.get(bit, '') if isinstance(v, dict) else ''
        if isinstance(v, dict): return str(v.get('id', ''))
        return str(v)
    return REF.sub(value, str(text))


def condition(text, env):
    # Deliberately small, no eval. Empty fields and literal equality suffice for
    # arrangements; add a composed see word when richer domain meaning is needed.
    if ' or ' in text: return any(condition(x, env) for x in text.split(' or '))
    if ' and ' in text: return all(condition(x, env) for x in text.split(' and '))
    match = re.fullmatch(r'(.+?)\s*(!=|>=|<=|=|>|<)\s*(.*)', text)
    if not match:
        raise Refused('only when expects <value> =|!=|>|<|>=|<= <value>')
    a, op, b = match.groups()
    a, b = resolve(a.strip().strip('"'), env), resolve(b.strip().strip('"'), env)
    if op == '=': return a == b
    if op == '!=': return a != b
    try: a, b = float(a), float(b)
    except ValueError: pass
    return {'>': lambda: a > b, '<': lambda: a < b, '>=': lambda: a >= b, '<=': lambda: a <= b}[op]()


def compile_view(k, actor, target, _trail=()):
    if target in _trail or len(_trail)>16: raise Refused('cyclic view reference')
    visible = {}
    for tid in k.state.things:
        a = k.shown(actor.person, tid)
        if a is not None and not a.get('forgotten'):
            visible[tid] = dict(a, id=tid, rev=k.state.rev.get(tid, 0))
    lens = visible.get(target) or next((a for a in visible.values() if a.get('name') == target and a.get('kind') == 'lens'), None)
    if lens and lens.get('kind') in ('window', 'widget'):
        target = lens.get('component_lens') or lens.get('lens') or lens.get('shows', '')
        if target == lens.get('id'): raise Refused('cyclic view reference')
        return compile_view(k, actor, target, (*_trail,lens['id']))
    if not lens or lens.get('kind') != 'lens' or lens.get('painter') != 'components':
        raise Refused('look-view needs a component lens, its widget or window')
    preferences = [a for a in visible.values() if a.get('kind') == 'view-preference'
                   and (a.get('made_by') in (actor.person,actor.id) or a.get('for')==actor.person)
                   and a.get('lens') in (lens['id'], lens.get('name'))]
    # A viewer may own an arrangement without changing the shared lens.
    source = next((a['text'] for a in reversed(preferences) if 'text' in a), lens.get('text', ''))
    definitions = parse(source)
    components = {a['name']: a for a in visible.values() if a.get('kind') == 'component' and a.get('name')}
    styles = [a for a in visible.values() if a.get('kind') == 'part-style' and a.get('lens') in (lens['id'], lens.get('name'))
              and (not a.get('personal') or a.get('made_by') in (actor.person,actor.id) or a.get('for')==actor.person)]
    styles.sort(key=lambda a:bool(a.get('personal')))
    reports = {a.get('path'):a for a in visible.values() if a.get('kind')=='paint-report'
               and a.get('viewer')==actor.person and a.get('lens')==lens['id']}
    counts, shown, settings_seen = Counter(), {}, []
    def expand(node, env, path, level=0):
        if level > 24:
            raise Refused('component arrangement nests too deeply')
        if node.get('when') and not condition(node['when'], env): return None
        query = node.get('query')
        query_children = None
        if query:
            query, _, alias = query.partition(' as ')
            clauses = pieces(query)
            tag = clauses.pop(0).removeprefix('tag:')
            items = [a for a in visible.values() if a.get('kind') == tag]
            for clause in clauses:
                clause = clause.strip()
                key, _, value = clause.removeprefix('prop:').partition('=')
                items = [a for a in items if str(a.get(key, '')) == resolve(value, env)]
            def order(a):
                v = a.get(node.get('by', 'order'), '')
                try: return (0, float(v))
                except (TypeError, ValueError): return (1, str(v))
            items.sort(key=order)
            template = definitions.get(node.get('each'))
            if not template: raise Refused('each needs a named template')
            kids = []
            for item in items:
                next_env = dict(env, **{alias or 'item':item, 'item':item})
                child = expand(template, next_env, path+'/'+item['id'], level+1)
                if child: kids.append(child)
            query_children = kids
        kind = node['component']
        component = components.get(kind)
        error='';schema={};quarantined=False
        if kind not in ('column', 'row', 'text', 'grid', 'wrap', 'split', 'layers', 'absolute', 'scroll'):
            if not component:error=f'component {kind} is missing'
            else:
                quarantined=component.get('isolation')=='worker' or component.get('reviewed_code') != hashlib.sha256(component.get('code', '').encode()).hexdigest()
                try:
                    schema=json.loads(component.get('settings','{}'))
                    if not isinstance(schema,dict) or any(not isinstance(s,dict) for s in schema.values()):raise ValueError()
                except ValueError:error=f'component {kind} settings must be a JSON type declaration';schema={}
        settings = {key:resolve(value, env) for key, value in node['settings'].items()}
        for preference in preferences:
            for key, value in preference.items():
                if key.startswith(node['name']+'.'):
                    settings[key.split('.',1)[1]] = value
        enabled=settings.pop('enabled',True)
        displays={};formats=dict(node.get('formats',{}));labels=dict(node.get('labels',{}))
        for preference in preferences:
            for key,value in preference.items():
                if key.startswith(node['name']+'.format.'):
                    formats[key.split('.format.',1)[1]]=value
                if key.startswith(node['name']+'.labels.'):
                    try:labels[key.split('.labels.',1)[1]]=json.loads(value)
                    except ValueError:error='personal labels need a JSON object'
        settings={key:value for key,value in settings.items() if not key.startswith(('format.','labels.'))}
        for key, spec in schema.items():
            if key not in settings and 'default' in spec: settings[key] = spec['default']
            if key not in settings: continue
            typ = spec.get('type', 'text')
            if typ == 'number':
                try: settings[key] = float(settings[key])
                except (TypeError, ValueError): error=f'{kind}.{key} needs a number';continue
                if not math.isfinite(settings[key]): error=f'{kind}.{key} needs a finite number';settings[key]=None
            elif typ == 'boolean':
                if str(settings[key]).lower() not in ('yes','true','1','no','false','0',''):
                    error=f'{kind}.{key} needs a boolean'
                settings[key] = str(settings[key]).lower() in ('yes','true','1')
            elif typ == 'json':
                if isinstance(settings[key], str):
                    try: settings[key] = json.loads(settings[key])
                    except ValueError: error=f'{kind}.{key} needs JSON'
            elif typ not in ('text', 'fact'): error=f'unknown setting type {typ}'
        for key in settings:
            if schema and key not in schema:error=f'{kind} has no setting {key}; help {kind}'
        for key in formats.keys()|labels.keys():
            if key not in settings:error=f'{kind}: display handle needs an existing setting; unknown {key}'
        for key,value in settings.items():
            try:
                mapping=labels.get(key,{})
                if not isinstance(mapping,dict):raise Refused('labels needs a JSON object')
                displays[key]=str(mapping.get(str(value),present(value,formats[key],k.now()) if key in formats else value))
            except Refused as exc:error=str(exc)
        facts = env.get('item', {})
        reads = {v['id']:dict(rev=v['rev'],participant=True) for v in env.values() if isinstance(v,dict) and 'id' in v and 'rev' in v}
        for tid in reads: shown[tid] = visible[tid]
        children = query_children if query_children is not None else [x for child in node['children'] if (x := expand(child, env, path+'/'+child['name'], level+1))]
        if not query or kind != 'column': counts[kind] += 1
        report=reports.get(path,{})
        declared_parts=[]
        if component:
            try:
                declared=json.loads(component.get('parts','{}'))
                if not isinstance(declared,dict):raise ValueError()
                declared_parts=list(declared)
            except (ValueError,TypeError):error=f'{kind} parts must be a JSON object'
        health=dict(health=report.get('health','unobserved'),last_error=report.get('last_error',''),quarantined=bool(report.get('quarantined') or quarantined),
                    painted=report.get('painted',[]),observed_at=report.get('observed_at'),failures=report.get('failures',0),disabled=report.get('disabled',False),action_epoch=report.get('action_epoch',0))
        if error:health.update(health='stopped',last_error=error)
        settings_seen.append(dict(part=path, name=node['name'],component=kind, settings=settings, display=displays,facts=facts,health=health,
                                 parts=declared_parts,gestures=[g['event'] for g in node['gestures']]))
        return dict(component=kind, name=node['name'], path=path, role=node.get('role',''), settings=settings, facts=facts, saw=reads,
                    definition=component['id'] if component else None,error=error,display=displays,health=health,
                    disabled=str(enabled).lower() in ('no','false','0') or bool(health['disabled']),motions=node.get('motions',[]),
                    gestures=[dict(event=g['event'], line=g['line'], env=env) for g in node['gestures']], children=children)
    base = dict(viewer=dict(id=actor.person, name=k.name(actor.person)), today=k.now().strftime('%Y-%m-%d'),
                now=k.now().strftime('%Y-%m-%dT%H:%M:%SZ') if '$now' in source else '')
    tree = expand(definitions['root'], base, 'root')
    used = [dict(components[name],trusted=components[name].get('reviewed_code')==hashlib.sha256(components[name].get('code','').encode()).hexdigest()) for name in counts if name in components]
    for a in [lens, *used, *styles, *preferences, *shown.values()]: k.mark(actor, a['id'], a)
    text = f"{lens.get('title') or lens.get('name')}: " + ', '.join(f'{n} {kind}' for kind,n in counts.items())
    tokens={};style_errors=[];paint_styles=[]
    for a in styles:
        if a.get('target')=='tokens':
            try:tokens.update(style_values(a))
            except Refused as exc:style_errors.append(dict(style=a['id'],error=str(exc)))
    for a in styles:
        if a.get('target')=='tokens':continue
        try:paint_styles.append(dict(a,paint=style_values(a,tokens)))
        except Refused as exc:style_errors.append(dict(style=a['id'],error=str(exc)))
    if styles:text+='. Style: '+ '; '.join(a.get('target','')+' '+json.dumps(a.get('paint',{})) for a in paint_styles)
    if style_errors:text+='; paint refusals: '+ '; '.join(e['error'] for e in style_errors)
    return dict(text=text, rows=[dict(kind='view-description', lens=lens['id'], tree=tree, counts=dict(counts), parts=settings_seen,
                                    components=used, styles=paint_styles,tokens=tokens,style_errors=style_errors)])


def look_view(k, actor, st, entry, tx, group, saw=None):
    out=compile_view(k, actor, st.target or st.words.strip())
    if st.kv.get('plan') not in ('yes','true','1'):
        full=out['rows'][0]
        parts=[{key:value for key,value in p.items() if key!='facts'} for p in full['parts']]
        out['rows']=[dict(kind=full['kind'],lens=full['lens'],counts=full['counts'],parts=parts,style_errors=full['style_errors'],
                          observation='Last painter report, private to this viewer; unobserved is not proof of paint. plan=yes returns the full plan.')]
        out['text']+='\n'+ '\n'.join(p['name']+' ('+p['component']+'): '+p['health']['health']+(' · '+p['health']['last_error'] if p['health']['last_error'] else '') for p in parts if p['health']['health']!='unobserved')
    return out


def component(k, actor, st, entry, tx, group, saw=None):
    t = st.target or next((t for t in k.things('component') if k.state.get(t,'name') == st.words.strip()), None)
    a = k.shown(actor.person, t)
    if not a or a.get('kind') != 'component' or not a.get('code'):
        raise Refused('component <thing>: review a component with inline module code')
    k.fence(actor, t, ['code'], saw)
    for field in ('settings','parts','slots'):
        try: json.loads(a.get(field, '{}'))
        except ValueError: raise Refused(f'component {field} must be JSON')
    tx.set(t, 'reviewed_code', hashlib.sha256(a['code'].encode()).hexdigest())
    return {'text':'ok reviewed component bytes [r?]'}


def component_card(k, actor, name):
    from painter.health import component_status
    for t in k.things('component'):
        a = k.shown(actor.person, t)
        if a and name in (t, a.get('name')):
            k.mark(actor, t, a)
            card = dict(a, id=t, rev=k.state.rev.get(t,0))
            card.update(component_status(k,actor,a.get('name')))
            card.pop('code', None)
            return dict(text='\n'.join(str(card.get(key,'')) for key in
                ('name','purpose','limitations','settings','parts','slots','gestures','example','uses')), rows=[card])


def components(k, actor, st, entry, tx, group, saw=None):
    from painter.health import component_status
    terms = set(re.findall(r'[a-z]{3,}', str(st.kv.get('for','')).lower())) - {'the','for','with','and','make','here'}
    cards = []
    for t in k.things('component'):
        a = k.shown(actor.person,t)
        if a:
            haystack = ' '.join(str(a.get(key,'')) for key in ('name','purpose','uses','limitations')).lower()
            score = sum(term in haystack for term in terms)
            if terms and not score: continue
            k.mark(actor,t,a)
            cards.append(dict(id=t,name=a.get('name'),category=a.get('category','other'),purpose=a.get('purpose',''),
                              limitations=a.get('limitations',''),score=score,**component_status(k,actor,a.get('name'))))
    cards.sort(key=lambda c:(-c['score'], c['category'], c['name']))
    return dict(text='\n'.join(f"{c['category']} · {c['name']}: {c['purpose']} [{c['health']}{'; quarantined' if c['quarantined'] else ''}] "
                              f"{('Limits: '+c['limitations']) if c['limitations'] else ''}" for c in cards)
                or 'No catalogue component matches. See the reach map for missing layers.', rows=cards)
