"""Data-only arrangement compiler. No component JavaScript runs to describe a view."""
import hashlib
import json
import re
import math
from collections import Counter

from kernel.kernel import Refused


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
                   and a.get('made_by') == actor.person and a.get('lens') in (lens['id'], lens.get('name'))]
    # A viewer may own an arrangement without changing the shared lens.
    source = next((a['text'] for a in reversed(preferences) if 'text' in a), lens.get('text', ''))
    definitions = parse(source)
    components = {a['name']: a for a in visible.values() if a.get('kind') == 'component' and a.get('name')}
    styles = [a for a in visible.values() if a.get('kind') == 'part-style' and a.get('lens') in (lens['id'], lens.get('name'))
              and (not a.get('personal') or a.get('made_by') == actor.person)]
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
        if kind not in ('column', 'row', 'text', 'grid', 'wrap', 'split', 'layers', 'absolute', 'scroll'):
            if not component or component.get('reviewed_code') != hashlib.sha256(component.get('code', '').encode()).hexdigest():
                raise Refused(f'component {kind} has no steward review for these bytes')
            try: schema = json.loads(component.get('settings', '{}'))
            except ValueError: raise Refused(f'component {kind} settings must be JSON')
        else: schema = {}
        settings = {key:resolve(value, env) for key, value in node['settings'].items()}
        for preference in preferences:
            for key, value in preference.items():
                if key.startswith(node['name']+'.'):
                    settings[key.split('.',1)[1]] = value
        for key, spec in schema.items():
            if key not in settings and 'default' in spec: settings[key] = spec['default']
            if key not in settings: continue
            typ = spec.get('type', 'text')
            if typ == 'number':
                try: settings[key] = float(settings[key])
                except (TypeError, ValueError): raise Refused(f'{kind}.{key} needs a number')
                if not math.isfinite(settings[key]): raise Refused(f'{kind}.{key} needs a finite number')
            elif typ == 'boolean':
                if str(settings[key]).lower() not in ('yes','true','1','no','false','0',''):
                    raise Refused(f'{kind}.{key} needs a boolean')
                settings[key] = str(settings[key]).lower() in ('yes','true','1')
            elif typ == 'json':
                if isinstance(settings[key], str):
                    try: settings[key] = json.loads(settings[key])
                    except ValueError: raise Refused(f'{kind}.{key} needs JSON')
            elif typ not in ('text', 'fact'): raise Refused(f'unknown setting type {typ}')
        for key in settings:
            if schema and key not in schema: raise Refused(f'{kind} has no setting {key}; help {kind}')
        facts = env.get('item', {})
        reads = {v['id']:dict(rev=v['rev'],participant=True) for v in env.values() if isinstance(v,dict) and 'id' in v and 'rev' in v}
        for tid in reads: shown[tid] = visible[tid]
        children = query_children if query_children is not None else [x for child in node['children'] if (x := expand(child, env, path+'/'+child['name'], level+1))]
        if not query or kind != 'column': counts[kind] += 1
        settings_seen.append(dict(part=path, component=kind, settings=settings, facts=facts))
        return dict(component=kind, name=node['name'], path=path, role=node.get('role',''), settings=settings, facts=facts, saw=reads,
                    gestures=[dict(event=g['event'], line=g['line'], env=env) for g in node['gestures']], children=children)
    base = dict(viewer=dict(id=actor.person, name=k.name(actor.person)), today=k.now().strftime('%Y-%m-%d'),
                now=k.now().strftime('%Y-%m-%dT%H:%M:%SZ') if '$now' in source else '')
    tree = expand(definitions['root'], base, 'root')
    used = [components[name] for name in counts if name in components]
    for a in [lens, *used, *styles, *preferences, *shown.values()]: k.mark(actor, a['id'], a)
    text = f"{lens.get('title') or lens.get('name')}: " + ', '.join(f'{n} {kind}' for kind,n in counts.items())
    if styles: text += '. Style: ' + '; '.join(a.get('target','')+' '+json.dumps({key:v for key,v in a.items() if key in ('glow','padding','gap','radius','lines','color','background','emphasis')}) for a in styles)
    return dict(text=text, rows=[dict(kind='view-description', lens=lens['id'], tree=tree, counts=dict(counts), parts=settings_seen,
                                    components=used, styles=styles)])


def look_view(k, actor, st, entry, tx, group, saw=None):
    return compile_view(k, actor, st.target or st.words.strip())


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
    for t in k.things('component'):
        a = k.shown(actor.person, t)
        if a and name in (t, a.get('name')):
            k.mark(actor, t, a)
            card = dict(a, id=t, rev=k.state.rev.get(t,0))
            card.pop('code', None)
            return dict(text='\n'.join(str(card.get(key,'')) for key in
                ('name','purpose','limitations','settings','parts','slots','gestures','example','uses')), rows=[card])


def components(k, actor, st, entry, tx, group, saw=None):
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
                              limitations=a.get('limitations',''),score=score))
    cards.sort(key=lambda c:(-c['score'], c['category'], c['name']))
    return dict(text='\n'.join(f"{c['category']} · {c['name']}: {c['purpose']} "
                              f"{('Limits: '+c['limitations']) if c['limitations'] else ''}" for c in cards)
                or 'No catalogue component matches. See the reach map for missing layers.', rows=cards)
