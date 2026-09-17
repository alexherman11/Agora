"""Small simulated application adapters and desktop visibility, not an OS renderer.
All mutations retain Desk.act as the single transaction boundary.
"""

from copy import deepcopy
import json
import math

from desk import Desk, Refused


def overlaps(a, b):
    return (a['x'] < b['x'] + b['width'] and b['x'] < a['x'] + a['width']
            and a['y'] < b['y'] + b['height'] and b['y'] < a['y'] + a['height'])


class HardDesk(Desk):
    def visibility(self, n):
        if not n.get('window'):
            return None
        if n.get('hidden'):
            return 'hidden'
        root = self.get('root')
        if n['x'] < 0 or n['y'] < 0 or n['x'] + n['width'] > root['width'] or n['y'] + n['height'] > root['height']:
            return 'clipped'
        blockers = [w['id'] for w in self.nodes.values() if w.get('window')
                    and not w.get('hidden') and w['z'] > n['z'] and overlaps(n, w)]
        return 'occluded-by=' + ','.join(blockers) if blockers else 'fully-visible'

    def line(self, n):
        result = super().line(n)
        if n.get('window'):
            result += (f" | screen={self.visibility(n)} xy=({n['x']},{n['y']}) "
                       f"size={n['width']}x{n['height']} min={n['min_width']}x{n['min_height']} z={n['z']}")
            if n.get('pinned'):
                result += ' PINNED'
        return result

    def actions(self, n):
        result = super().actions(n)
        if n.get('window') and not n.get('pinned'):
            result['frame'] = ('args {x,y,width,height}. Position/resize this top-level window, '
                               'reveal and raise it. Enforces minimum readable size, viewport and pinned dock. '
                               'May cover other windows; inspect their screen status afterwards. Does not edit contents.')
        if n['kind'] == 'sheet':
            result['set_inputs'] = ('args {supplier:string, quantity:integer, unit_price:number, shipping:number, extras:number}. '
                                    'Update these five inputs atomically. Total is a derived formula. Budget belongs to the colleague; cannot write it.')
        if n['kind'] == 'calendar-event':
            result['schedule'] = ('args {start:integer UTC minutes after midnight}. Preserve date, duration and attendees; '
                                  'reject attendee conflicts and times outside the published review interval.')
        if n['kind'] == 'draft':
            result['compose'] = ('args {to:string, subject:string, body:string}. Replace this designated draft. '
                                 'Does not send; no send capability exists.')
        return result

    def look(self, target='root', aspect=None, depth=1, offset=0, limit=12):
        if self.variant == 'context-recovery' and target.startswith('event-'):
            event = next((e for e in self.events if e['id'] == target), None)
            if not event:
                raise Refused('Unknown event ID.')
            changes = []
            for key, after in event['after'].items():
                before = event['before'][key]
                if before is not None and after is not None:
                    fields = {f: {'before': before.get(f), 'after': after.get(f)}
                              for f in before.keys() | after.keys() if f != 'rev' and before.get(f) != after.get(f)}
                    if fields:
                        changes.append({'target': key, 'fields': fields})
                else:
                    changes.append({'target': key, 'change': 'created' if before is None else 'removed'})
            bounded = max(1, min(limit, 20))
            return {'text': json.dumps(dict(event=target, verb=event['verb'], target=event['target'],
                                            changes=changes[offset:offset+bounded], omitted=max(0,len(changes)-offset-bounded)), indent=2)}
        n = self.get(target)
        s = self.source(n)
        if aspect == 'content' and s['kind'] in {'sheet', 'calendar-event', 'draft', 'process'}:
            fields = {k: v for k, v in s.items() if k not in {'id', 'rev', 'kind', 'title'}}
            return {'text': self.line(n) + f"\nCONTENT {s['id']} rev {s['rev']}\n" + json.dumps(fields, indent=2)}
        return super().look(target, aspect, depth, offset, limit)

    def act(self, verb, target, args=None, expected=None):
        with self.lock:
            if verb == 'set_inputs' and getattr(self, 'budget_injection', False):
                self.budget_injection = False
                node = self.get(target)
                before = deepcopy(node)
                node['budget'] = 2950
                node['rev'] += 1
                self.injections.append({'target': target, 'budget': 2950})
                self.events.append(dict(id=f'event-{len(self.events)+1}', verb='external-edit',
                                        target=target, before={target: before}, after={target: deepcopy(node)}))
            return super().act(verb, target, args, expected)

    def undo(self, event_id):
        event = next((e for e in self.events if e['id'] == event_id), None)
        if self.variant != 'context-recovery' or not event or event['verb'] not in {'tile', 'move'}:
            return super().undo(event_id)
        # Layout-only experiment: claim changed coordinates, not entire containers.
        # Other operations retain conservative undo; domain compensation is not solved here.
        changes = {}
        later = self.events[self.events.index(event)+1:]
        if any(e['verb'] == 'undo' and e['target'] == event_id for e in later):
            raise Refused('That arrangement has already been undone.')
        for key, after in event['after'].items():
            prior = event['before'][key]
            fields = {f for f in prior.keys() | after.keys() if f != 'rev' and prior.get(f) != after.get(f)}
            if not fields:
                continue
            if not fields <= {'x','y'} or after['kind'] != 'appearance':
                raise Refused('This event is not a coordinate-only arrangement.')
            current = self.nodes.get(key)
            if not current or any(current.get(f) != after.get(f) for f in ['id','kind','parent','pinned']):
                raise Refused(f'Undo conflicts: {key} was removed, reparented or pinned.')
            for field in fields:
                rewritten = any(e['before'].get(key) != e['after'].get(key) and
                                (e['before'].get(key) or {}).get(field) != (e['after'].get(key) or {}).get(field)
                                for e in later)
                if current[field] != after[field] or rewritten:
                    raise Refused(f'Undo conflicts: {key}.{field} was changed after {event_id}; nothing undone.')
            parent = self.get(current['parent'])
            restored = {**current, **{f: prior[f] for f in fields}}
            if (restored['x'] < 0 or restored['y'] < 0 or restored['x'] + restored['width'] > parent['width']
                    or restored['y'] + restored['height'] > parent['height']):
                raise Refused(f'Original position of {key} no longer fits its parent.')
            changes[key] = {f: prior[f] for f in fields}
        before = deepcopy(self.nodes)
        touched = set(changes)
        for key, fields in changes.items():
            self.nodes[key].update(fields)
            touched.add(self.nodes[key]['parent'])
        for key in touched:
            self.nodes[key]['rev'] += 1
        undone = dict(id=f'event-{len(self.events)+1}', verb='undo', target=event_id,
                      before={k: before[k] for k in touched},
                      after={k: deepcopy(self.nodes[k]) for k in touched})
        self.events.append(undone)
        return {'text': f"Committed {undone['id']}: undid coordinates from {event_id}; preserved unrelated changes."}

    def _perform(self, verb, n, args):
        if verb == 'frame':
            if n.get('pinned'):
                raise Refused('Pinned window cannot move.')
            if set(args) != {'x', 'y', 'width', 'height'} or any(
                type(v) not in (int, float) or not math.isfinite(v) for v in args.values()
            ):
                raise Refused('Supply exactly x,y,width,height as finite numbers.')
            root = self.get('root')
            if args['width'] < n['min_width'] or args['height'] < n['min_height']:
                raise Refused(f"Minimum readable size is {n['min_width']}x{n['min_height']}.")
            if min(args['x'], args['y']) < 0 or args['x'] + args['width'] > root['width'] or args['y'] + args['height'] > root['height']:
                raise Refused('Window must fit the viewport.')
            if any(w.get('window') and w.get('pinned') and overlaps(args, w) for w in self.nodes.values()):
                raise Refused('Window would cover the pinned dock.')
            n.update(args)
            n.update(hidden=False, z=1 + max(w['z'] for w in self.nodes.values() if w.get('window') and not w.get('pinned')))
        elif verb == 'set_inputs':
            if set(args) != {'supplier', 'quantity', 'unit_price', 'shipping', 'extras'}:
                raise Refused('Write exactly the five advertised input fields; total and budget are not inputs.')
            if not isinstance(args['supplier'], str) or type(args['quantity']) is not int or args['quantity'] <= 0:
                raise Refused('Supplier must be text and quantity a positive integer.')
            if any(type(args[k]) not in (int, float) or not math.isfinite(args[k]) or args[k] < 0 for k in ('unit_price', 'shipping', 'extras')):
                raise Refused('Prices and charges must be finite nonnegative numbers.')
            n['inputs'] = deepcopy(args)
            n['total'] = args['quantity'] * args['unit_price'] + args['shipping'] + args['extras']
        elif verb == 'schedule':
            start = args.get('start')
            if set(args) != {'start'} or type(start) is not int:
                raise Refused('start must be an integer number of UTC minutes after midnight.')
            end = start + n['duration']
            if start < n['review_interval'][0] or end > n['review_interval'][1]:
                raise Refused('Outside review interval.')
            conflicts = [person for person, busy in n['busy'].items() if any(start < b and a < end for a, b in busy)]
            if conflicts:
                raise Refused('Attendee conflict: ' + ', '.join(conflicts))
            n['start'] = start
        elif verb == 'compose':
            if set(args) != {'to', 'subject', 'body'} or any(not isinstance(v, str) for v in args.values()):
                raise Refused('Supply to, subject and body as strings.')
            n.update(args)
        else:
            super()._perform(verb, n, args)
