"""EDITING THE PAINTER (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
The painter's vocabulary (formats, handles, scopes, parts) is shared by every app. Add to it only what any lens could
use, documented where lens authors read it (ARRANGEMENT.md); never a handle, format or branch for one app. If one app
needs something, the general form of it is the change.

Data-only arrangement compiler. No component JavaScript runs to describe a view."""
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
            elif line.startswith('watch '):
                node.setdefault('watches',[]).append(literal(line[6:].removeprefix('reading:')))
            # Panels and sizes (Alex, 4 Nov): a part may be a side panel the window opens and shuts from its top bar,
            # and a lens names its window's widths. Which panels are open is the window's own view, never recorded.
            elif line.startswith('panel '):
                clauses = [c.strip() for c in pieces(line[6:])]
                side = clauses.pop(0)
                if side not in ('left', 'right'):
                    raise Refused(f'lens line {number}: panel left or panel right, then icon, label, width')
                panel = dict(node.get('panel') or {}, side=side)
                for clause in clauses:
                    key, _, value = clause.partition(' ')
                    if key not in ('icon', 'label', 'width') or not value.strip():
                        raise Refused(f'lens line {number}: a panel takes icon <name>, label "<words>" and width <px>')
                    panel[key] = literal(value.strip())
                node['panel'] = panel
            elif line.startswith('shut when '):
                # size names (shut when narrow middle), or a condition in only-when's form (shut when $view.open = "")
                text = line[10:].strip()
                if not text: raise Refused(f'lens line {number}: shut when <sizes> or shut when <condition>')
                node.setdefault('panel', {})['shut'] = text
            elif line.startswith('sizes '):
                sizes = []
                for clause in pieces(line[6:]):
                    name, _, start = clause.strip().partition(' ')
                    if not re.fullmatch(r'[\w-]+', name) or not start.strip().isdigit():
                        raise Refused(f'lens line {number}: sizes <name> <from px>, ... (sizes narrow 0, wide 1200)')
                    sizes.append([name, int(start)])
                node['sizes'] = sorted(sizes, key=lambda s: s[1])
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


def resolve_line(text, env):
    """One substitution, quoted as data even inside an authored quoted value."""
    def replace(match):
        value = resolve(match[0], env)
        before = text[:match.start()]
        quoted, escaped = False, False
        for ch in before:
            if escaped: escaped = False
            elif ch == '\\': escaped = True
            elif ch == '"': quoted = not quoted
        escaped_value = value.replace('\\', '\\\\').replace('"', '\\"')
        return escaped_value if quoted else '"' + escaped_value + '"'
    return REF.sub(replace, text)


def shut_now(text, env):
    """Whether a panel's layout wants it shut now: size names (the window's $view.size is one of them) or a condition."""
    if not text: return False
    if re.search(r'[$=<>]', text): return condition(text, env)
    return str((env.get('view') or {}).get('size', '')) in text.replace(',', ' ').split()


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


def compile_view(k, actor, target, _trail=(), reader=None, view=None):
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
        return compile_view(k, actor, target, (*_trail,lens['id']), reader=reader, view=view)
    if not lens or lens.get('kind') != 'lens' or lens.get('painter') != 'components':
        raise Refused('look-view needs a component lens, its widget or window')
    def preferences_for(l):
        return [a for a in visible.values() if a.get('kind') == 'view-preference'
                and (a.get('made_by') in (actor.person,actor.id) or a.get('for')==actor.person)
                and a.get('lens') in (l['id'], l.get('name'))]
    preferences = preferences_for(lens)
    # A viewer may own an arrangement without changing the shared lens.
    source = next((a['text'] for a in reversed(preferences) if 'text' in a), lens.get('text', ''))
    definitions = parse(source)
    # Reading-backed collections are evaluated by the trusted host, outside the
    # kernel lock. Reports reuse only that instance's last projection; every id
    # is intersected with current visibility before it can be painted again.
    projection = getattr(actor, '_component_projection', {}).get(lens['id'], {})
    defaults=json.loads(lens.get('view','{}'))
    for preference in preferences:
        defaults.update({key[5:]:value for key,value in preference.items() if key.startswith('view.')})
    view = dict(defaults, **(projection.get('view', {}) if view is None else view))
    reading_cache = {} if reader else projection.get('readings', {})
    reading_sources = [];watch_values=[]
    def read_rows(command):
        if command.startswith('look-view '): raise Refused('a collection cannot recursively read look-view')
        if reader:
            if command not in reading_cache:
                result = reader(command)
                if not result.get('ok'): raise Refused(result.get('text', 'reading refused'))
                reading_cache[command] = result.get('rows', [])
        result=[]
        for row in reading_cache.get(command, []):
            r=dict(row);tid=r.get('id')
            if tid and tid not in visible:
                if command != 'forgotten': continue
                # Notices contain no hidden text; re-read before reusing them.
                if not reader:
                    fresh=k.run(actor, 'forgotten', mode='see').get('rows', [])
                    r=next((x for x in fresh if x.get('id')==tid), None)
                    if r is None: continue
            if tid in visible: r.setdefault('rev', visible[tid]['rev'])
            result.append(r)
        return result
    components = {a['name']: a for a in visible.values() if a.get('kind') == 'component' and a.get('name')}
    # Paint health is this screen's, kept in the kernel process's memory and never in the world (painter/health.py).
    from painter.health import reports_for
    reports = reports_for(k, actor.person, lens['id'])
    counts, shown, settings_seen = Counter(), {}, []
    nested = []
    def nest(node, env, path, level, scope):
        # `part : lens, name <lens>` paints another component lens in place, by name: its own templates,
        # view defaults, personal views and styles come with it. The same lens also opens alone in a window.
        wanted = str(node['settings'].get('name') or node['settings'].get('text') or '')
        inner = next((a for a in visible.values() if a.get('kind') == 'lens' and wanted in (a['id'], a.get('name'))), None)
        if not inner or inner.get('painter') != 'components':
            raise Refused(f'lens part {node["name"]}: no visible component lens named {wanted}')
        if inner['id'] in scope['lenses']: raise Refused('cyclic view reference')
        prefs = preferences_for(inner)
        inner_defs = parse(next((a['text'] for a in reversed(prefs) if 'text' in a), inner.get('text', '')))
        inner_view = json.loads(inner.get('view', '{}') or '{}')
        for preference in prefs:
            inner_view.update({key[5:]:value for key,value in preference.items() if key.startswith('view.')})
        # The host lens's view and this window's choices win; the nested lens only fills what is missing.
        for key, value in inner_view.items(): view.setdefault(key, value)
        if inner not in nested: nested.append(inner)
        # The nested root takes the host part's name, so the host's personal views reach it as <part>.<setting>.
        root = dict(inner_defs['root'], name=node['name'])
        return expand(root, env, path, level+1, dict(defs=inner_defs, prefs=prefs+scope['prefs'], lenses=(*scope['lenses'], inner['id'])))
    def expand(node, env, path, level=0, scope=None):
        scope = scope or dict(defs=definitions, prefs=preferences, lenses=(lens['id'],))
        if level > 24:
            raise Refused('component arrangement nests too deeply')
        if node.get('when') and not condition(node['when'], env): return None
        if node['component'] == 'lens': return nest(node, env, path, level, scope)
        for watch in node.get('watches',[]):
            command=resolve_line(watch,env)
            watch_values.append(dict(path=path,line=command,rows=read_rows(command)))
            reading_sources.append(dict(path=path,line=command,watch=True,observed=command in reading_cache or bool(reader)))
        query = node.get('query')
        query_children = None
        if query:
            query, _, alias = query.partition(' as ')
            clauses = pieces(query)
            selector = clauses.pop(0)
            if selector.startswith('reading:'):
                command = resolve_line(literal(selector[8:]), env)
                reading_sources.append(dict(path=path, line=command, observed=command in reading_cache or bool(reader)))
                items = read_rows(command)
            else:
                tag = selector.removeprefix('tag:')
                # a kind with a shape (or one another extends) also draws what has that shape, read under the
                # kind's names: an event that says starts shows as start (kernel/kinds.py)
                fitted = k.kinds.is_open(tag)
                items = [a for a in visible.values() if a.get('kind') == tag] if not fitted else [
                    k.kinds.filled(a, tag) for a in visible.values() if k.kinds.fits(a, tag)]
            for clause in clauses:
                clause = clause.strip()
                key, _, value = clause.removeprefix('prop:').partition('=')
                items = [a for a in items if str(a.get(key, '')) == resolve(value, env)]
            def order(a):
                v = a.get(node.get('by', 'order'), '')
                try: return (0, float(v))
                except (TypeError, ValueError): return (1, str(v))
            if not selector.startswith('reading:') or node.get('by'): items.sort(key=order)
            # Pagination bounds component construction, not just visible pixels.
            offset = max(0, int(resolve(node['settings'].get('offset', '0'), env) or 0))
            limit = min(100, max(1, int(resolve(node['settings'].get('limit', '100'), env) or 100)))
            total = len(items)
            items = items[offset:offset+limit] if 'limit' in node['settings'] else items
            template = scope['defs'].get(node.get('each'))
            if not template: raise Refused('each needs a named template')
            kids = []
            for index, item in enumerate(items):
                next_env = dict(env, **{alias or 'item':item, 'item':item})
                child = expand(template, next_env, path+'/'+str(item.get('id') or index), level+1, scope)
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
        def setting_value(key,value):
            if schema.get(key,{}).get('type')=='json' and REF.fullmatch(str(value)):
                result=env
                for bit in str(value)[1:].split('.'):result=result.get(bit,'') if isinstance(result,dict) else ''
                if isinstance(result,(dict,list)):return result
            return resolve(value,env)
        settings = {key:setting_value(key,value) for key, value in node['settings'].items() if key not in ('limit','offset')}
        for preference in scope['prefs']:
            for key, value in preference.items():
                if key.startswith(node['name']+'.'):
                    settings[key.split('.',1)[1]] = value
        enabled=settings.pop('enabled',True)
        displays={};formats=dict(node.get('formats',{}));labels=dict(node.get('labels',{}))
        for preference in scope['prefs']:
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
            if key not in settings and key!='ui':error=f'{kind}: display handle needs an existing setting; unknown {key}'
        for key,value in settings.items():
            try:
                mapping=labels.get(key,{})
                if not isinstance(mapping,dict):raise Refused('labels needs a JSON object')
                displays[key]=str(mapping.get(str(value),present(value,formats[key],k.now()) if key in formats else value))
            except Refused as exc:error=str(exc)
        facts = env.get('item', {})
        reads = {v['id']:dict(rev=v['rev'],participant=True) for v in env.values() if isinstance(v,dict) and 'id' in v and 'rev' in v}
        for tid in reads:
            if tid in visible: shown[tid] = visible[tid]
        children = query_children if query_children is not None else [x for child in node['children'] if (x := expand(child, env, path+'/'+child['name'], level+1, scope))]
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
                    observed_at=report.get('observed_at'),failures=report.get('failures',0),disabled=False,action_epoch=report.get('action_epoch',0))
        if error:health.update(health='stopped',last_error=error)
        settings_seen.append(dict(part=path, name=node['name'],component=kind, settings=settings, display=displays,labels=labels.get('ui',{}),facts=facts,health=health,
                                 parts=declared_parts,gestures=[g['event'] for g in node['gestures']]))
        panel = node.get('panel')
        if panel:
            if 'side' not in panel: raise Refused(f'{path}: shut when needs a panel line (panel left or panel right)')
            panel = dict(panel, shut_now=shut_now(panel.get('shut', ''), env))
        return dict(component=kind, name=node['name'], path=path, role=node.get('role',''), panel=panel, settings=settings, facts=facts, saw=reads,viewer=env.get('viewer',{}),
                    collection=dict(total=total, offset=offset, limit=limit) if query else None,
                    definition=component['id'] if component else None,error=error,display=displays,formats=formats,labels=labels.get('ui',{}),health=health,
                    disabled=str(enabled).lower() in ('no','false','0') or bool(health['disabled']),motions=node.get('motions',[]),
                    gestures=[dict(event=g['event'], line=g['line'], env=env) for g in node['gestures']], children=children)
    base = dict(view=view, viewer=dict(id=actor.person, name=k.name(actor.person)), today=k.now().strftime('%Y-%m-%d'),
                now=k.now().strftime('%Y-%m-%dT%H:%M:%SZ') if '$now' in source else '')
    tree = expand(definitions['root'], base, 'root')
    # A nested lens's styles and tokens come first; the host lens's own, then personal ones, override them.
    owners = [(lens['id'], lens.get('name'))] + [(a['id'], a.get('name')) for a in nested]
    styles = [a for a in visible.values() if a.get('kind') == 'part-style' and any(a.get('lens') in names for names in owners)
              and (not a.get('personal') or a.get('made_by') in (actor.person,actor.id) or a.get('for')==actor.person)]
    styles.sort(key=lambda a:(bool(a.get('personal')), a.get('lens') in owners[0]))
    if reader:
        if not hasattr(actor, '_component_projection'): actor._component_projection = {}
        actor._component_projection[lens['id']] = dict(view=view, readings=reading_cache)
        # what this person's running window shows, so look-view and view can read it from Lines (screen state)
        if actor.kind == 'module' and actor.module: windows(k)[(actor.module, actor.person)] = dict(view)
    used = [dict(components[name],trusted=components[name].get('reviewed_code')==hashlib.sha256(components[name].get('code','').encode()).hexdigest()) for name in counts if name in components]
    for a in [lens, *nested, *used, *styles, *preferences, *shown.values()]: k.mark(actor, a['id'], a)
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
                                    components=used, styles=paint_styles,tokens=tokens,style_errors=style_errors,
                                    readings=reading_sources, watches=watch_values, view=view, sizes=definitions['root'].get('sizes', []),
                                    # Lens-wide painter handles: how often to reread as a safety net (500..60000 ms,
                                    # default 1500) and whether right-clicking any part opens the ask menu.
                                    options=dict(reconcile_ms=lens.get('reconcile_ms',''),right_click=lens.get('right_click','')))])


def panels_of(plan):
    """The side panels in a plan and whether this window has each open: its view says, open unless shut."""
    found, view = [], plan.get('view', {})
    def walk(node):
        if node.get('panel'):
            found.append(dict(name=node['name'], path=node['path'], side=node['panel']['side'], shut_when=node['panel'].get('shut', ''),
                              layout_shuts=node['panel'].get('shut_now', False), state=view.get(node['name']) or 'open'))
        for child in node.get('children', []): walk(child)
    if plan.get('tree'): walk(plan['tree'])
    return found


def windows(k):
    """{(widget id, person): the view that person's running window last painted}. Kept in the kernel process's memory,
    like paint health: screen state, never in k.state or the log; a restart forgets it until the window paints again."""
    table = getattr(k, '_window_views', None)
    if table is None:
        table = k._window_views = {}
    return table


def window_of(k, actor, target):
    """The widget a line names (by id, name or lens), when this person can see it."""
    shown = lambda t: k.state.get(t, 'kind') == 'widget' and not k.state.get(t, 'forgotten') and k.shown(actor.person, t) is not None
    if target in k.state.things and shown(target): return target
    return next((t for t in k.state.things if shown(t) and target in (k.state.get(t, 'name'), k.state.get(t, 'component_lens'))), None)


def look_view(k, actor, st, entry, tx, group, saw=None):
    target = st.target or st.words.strip()
    w = window_of(k, actor, target) if actor.kind != 'module' else None
    seen = windows(k).get((w, actor.person)) if w else None
    out=compile_view(k, actor, w or target, view=seen)
    if st.kv.get('plan') not in ('yes','true','1'):
        full=out['rows'][0]
        parts=[{key:value for key,value in p.items() if key!='facts'} for p in full['parts']]
        out['rows']=[dict(kind=full['kind'],lens=full['lens'],counts=full['counts'],parts=parts,style_errors=full['style_errors'],
                          readings=full.get('readings',[]),view=full.get('view',{}),panels=panels_of(full),
                          observation='Paint health of this screen, private to this viewer and never recorded; unobserved is not proof of paint. plan=yes returns the full plan.')]
        panels = out['rows'][0]['panels']
        if panels or seen:
            out['text'] += '\n' + ('window: ' + ', '.join(f'{key}={value}' for key, value in sorted(seen.items()) if key != 'target')
                                   if seen else 'window: not open (the lens defaults below)')
        if panels:
            out['text'] += '\npanels: ' + ' · '.join(f"{p['name']} {p['state']} ({p['side']}" + (', shuts when ' + p['shut_when'] if p['shut_when'] else '') + ')' for p in panels)
        out['text']+='\n'+ '\n'.join(p['name']+' ('+p['component']+'): '+p['health']['health']+(' · '+p['health']['last_error'] if p['health']['last_error'] else '') for p in parts if p['health']['health']!='unobserved')
    return out


def window_view(k, actor, st, entry, tx, group, saw=None):
    """view <window> key=value ...: change what your running window shows, its open panels or its open thing. The
    window's own view is screen state: it is told, not recorded, and only your own window listens."""
    w = window_of(k, actor, st.target or st.words.strip())
    if not w: raise Refused('view <window> key=value: name a window you can see, by its name or lens')
    values = {key: str(value) for key, value in st.kv.items()}
    if not values: raise Refused('view <window> key=value: say what to change, for example rail=open')
    for key, value in values.items():
        if not re.fullmatch(r'[a-z_][\w.-]{0,40}', key) or key in ('size', 'width'):
            raise Refused(f'view: {key} is not a view key (size and width are the window\'s own)')
        if len(value) > 200: raise Refused('view: a value is at most 200 characters')
    k._happen({'word': 'view', 'entry': entry.get('id') if isinstance(entry, dict) else None, 'target': w,
               'by': actor.person, 'for': actor.person, 'only': actor.person, 'text': json.dumps(values)})
    seen = windows(k).get((w, actor.person))
    if seen is not None: seen.update(values)
    told = ', '.join(f'{key}={value}' for key, value in values.items())
    return dict(text=f'ok view {k.name(w)} · {told}' + ('' if seen is not None else ' (no window of yours shows it now; it applies when one listens)'))


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
            card['general_handles']='labels ui {"Reply":"Responder"}; personal-view <lens> <part>.labels.ui=<JSON>; personal-style <lens> target=<component.part>; limit/offset on collections'
            return dict(text='\n'.join(str(card.get(key,'')) for key in
                ('name','purpose','limitations','settings','parts','slots','gestures','example','uses','general_handles')), rows=[card])


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
