"""Trusted widget broker. Never send its instance capability into the iframe."""
import secrets
import re
import threading
import time

from kernel.inpage import Principal
from kernel.kernel import Refused

SURFACES = {'window': 'window.surface', 'top': 'window.bar', 'bottom': 'window.bar', 'overlay': 'window.overlay'}


def quote(text):
    return '"' + str(text).replace('\\', '\\\\').replace('"', '\\"') + '"'


class Widgets:
    def __init__(self, kernel):
        self.k, self.instances = kernel, {}
        self.guard_key = secrets.token_urlsafe(32)
        self.lock = threading.RLock()

    def reap(self):
        for token, i in list(self.instances.items()):
            try:
                i['p'].check()
                if time.monotonic() - i['at'] > 20:
                    raise Refused('widget host disconnected')
            except Refused:
                self.close(token)

    def close(self, token):
        i = self.instances.pop(token, None)
        if i:
            self.k.release(lease=i['lease'])
            if i.get('native'):
                self.k.release(lease=i['native'])
            i['p'].close()

    def native_lease(self, p, mid):
        """The shell's bars only: a widget that holds window.native (a steward's ordinary grant; holds lists it, off ends
        it) may ask its own window for a click region, a reserved strip, DWM thumbnails and a live title. The page's
        window must also be a shell window: PageApi refuses on any other (kd_window.py). -> lease or None."""
        grants = ' '.join(self.k.state.get(g, 'words') or '' for g in self.k._grants_to(mid))
        if 'window.native' not in grants.split():
            return None
        try:
            return p.hold('window.native')
        except Refused:
            return None

    def theme(self, mid, viewer):
        """What a widget is told about the look it wears: the roles as the painter's tokens (paper, card, ink, muted, accent,
        the colour names, the shapes), the compiled theme.css, and the palette and roles for anything that mixes its own
        colours. The theme is the viewer's own (place default, just for them, or being tried): theme/service.py.
        A widget that sets pin_style=yes keeps the older behaviour: only the four tokens its named style note gives."""
        from theme import service
        p = service.payload(self.k, viewer, '/desk/')
        name = self.k.state.get(mid, 'style') or 'bars'
        theme = dict(p['tokens'], font=p['font'], style=name, source='', css=p['css'], hash=p['hash'],
                     variant=p['variant'], roles=p['roles'], palette=p['palette'], name=p['name'])
        if self.k.state.get(mid, 'pin_style') == 'yes':
            # Style source travels as data too, allowing richer painters to interpret their own style tokens
            # without granting the widget arbitrary reads.
            style = next((s for s in self.k.things('style') if self.k.state.get(s, 'name') == name), None)
            a = self.k.shown(viewer, style) if style else None
            theme['source'] = (a or {}).get('text', '')
            for key, value in re.findall(r'^token\s+(paper|card|ink|accent)\s*=\s*(#[0-9a-fA-F]{6})\b', theme['source'], re.M):
                theme[key] = value
        return theme

    def request(self, actor, action, body):
        with self.lock:
            self.reap()
            if action == 'open':
                mid = str(body.get('widget') or '')
                token = secrets.token_urlsafe(32)
                p = Principal(self.k, mid, actor, token)
                surface = self.k.state.get(mid, 'surface') or 'window'
                lease = p.hold(SURFACES[surface])
                native = self.native_lease(p, mid)
                self.instances[token] = dict(p=p, lease=lease, native=native, at=time.monotonic(), cursor=len(self.k.happenings),
                                             words=set(), calls=[], hits=[], paint=None)
                return dict(ok=True, instance=token, widget=mid, code=self.k.state.get(mid, 'code'), native=bool(native),
                            name=self.k.state.get(mid, 'title') or self.k.name(mid), surface=surface, theme=self.theme(mid, actor.person),
                            component_lens=self.k.state.get(mid,'component_lens',''),receipts=self.k.state.get(mid,'receipts','line'))
            token = str(body.get('instance') or '')
            i = self.instances.get(token)
            if not i or i['p'].viewer.id != actor.id:
                raise Refused('no widget instance for this viewer')
            p = i['p']
            p.check()
            i['at'] = time.monotonic()
            if action == 'stall':
                # The trusted parent watchdog remains responsive when its
                # opaque renderer hangs. Persist quarantine BEFORE replacing it.
                from painter.arrangement import compile_view
                plan=compile_view(self.k,p.actor,self.k.state.get(p.mid,'component_lens',''))['rows'][0]
                path=str(body.get('path',''))[:500]
                from painter.health import part_of
                part=part_of(plan,path)
                if not part:raise Refused('stalled part is no longer in this view')
                candidates=[a for a in plan['parts'] if a['component']==part['component']] if body.get('stage')=='module' else [dict(part,part=path)]
                elapsed=body.get('elapsed_ms',2500)
                if not isinstance(elapsed,(float,int)) or not 0<=elapsed<=1e8:raise Refused('invalid watchdog elapsed time')
                reports=[dict(path=a['part'],health='stopped',last_error=f'Native parent watchdog: no response for {elapsed:g} ms',elapsed_ms=elapsed,painted=[]) for a in candidates]
                # Two observations represent a blocked operation and the failed
                # heartbeat. Each is an ordinary, viewer-scoped kernel act.
                for _ in range(2):
                    out=p.run('component-health '+plan['lens']+' data='+quote(__import__('json').dumps(reports)))
                    if not out.get('ok'):return out
                return {'ok':True}
            if action == 'close':
                self.close(token)
                return {'ok': True}
            if action == 'poll':
                with self.k.lock:
                    happenings = self.k.happenings[i['cursor']:]
                    i['cursor'] = len(self.k.happenings)
                    events = [self.k.happening_for(actor.person, h) for h in happenings
                              if h['word'] in i['words'] and p.hears(h['word']) and self.k.may_hear(actor.person, h)]
                    for e in events:
                        if e['word'] != 'guy.say':
                            e.pop('text', None)  # no unrelated field values hidden inside command text
                return dict(ok=True, events=events)
            now = time.monotonic()
            i['calls'] = [t for t in i['calls'] if now - t < 1]
            if len(i['calls']) >= 40:
                raise Refused('widget is speaking too quickly; try again in a second')
            i['calls'].append(now)
            op = body.get('op')
            if op == 'project':
                import json
                from painter.arrangement import compile_view
                target = self.k.state.get(p.mid, 'component_lens', '')
                admitted = p.run('look-view ' + quote(target) + ' plan=yes', mode='see')
                if not admitted.get('ok'): return admitted
                view = body.get('view', {})
                if not isinstance(view, dict) or len(json.dumps(view)) > 8000 or any(
                        not isinstance(v, (str, int, float, bool)) for v in view.values()):
                    raise Refused('view state needs a small object of plain values')
                # Each nested reading uses this exact viewer/instance principal.
                # No world lock is held while a process module answers.
                out = compile_view(self.k, p.actor, target,
                                   reader=lambda command: p.run(command, mode='see'), view=view)
                return dict(ok=True, **out)
            if op == 'file-check':
                target = str(body.get('target', ''))
                variant = body.get('variant', 'content')
                if not re.fullmatch(r'[a-zA-Z]+\d+', target) or variant not in ('content', 'thumbnail'):
                    raise Refused('choose a file thing and content or thumbnail')
                admitted = p.run('file-read ' + target, mode='see')
                if not admitted.get('ok'): return admitted
                # /files authenticates the parent's own cookie and rechecks
                # current permissions. The component never receives this URL.
                return dict(ok=True, path='/files/' + target + '?variant=' + variant)
            if op == 'upload':
                import base64
                from kernel.blobs import receive, cap
                encoded = body.get('data')
                if not isinstance(encoded, str) or len(encoded) > 4 * ((cap(self.k) + 2) // 3):
                    raise Refused('file exceeds the steward size setting')
                try:
                    data = base64.b64decode(encoded, validate=True)
                except ValueError:
                    raise Refused('invalid upload bytes')
                # receive runs as this viewer narrowed to this widget's grants.
                return receive(self.k, p.actor, data, body.get('name', 'Upload'), body.get('group'))
            if op in ('do', 'see'):
                line = body.get('line')
                if not isinstance(line, str) or len(line) > 64000:
                    raise Refused('a bridge line must be text, at most 64000 characters')
                return p.run(line, mode=op, saw=body.get('saw'))
            if op == 'hear':
                word = str(body.get('word') or '')
                if not p.hears(word):
                    raise Refused('no grant to hear ' + word)
                i['words'].add(word)
                return {'ok': True}
            if op == 'theme':
                return dict(ok=True, theme=self.theme(p.mid, actor.person))
            if op == 'describe':
                return p.run('describe ' + p.mid + ' text=' + quote(str(body.get('text') or '')[:2000]))
            raise Refused('unknown bridge call')
