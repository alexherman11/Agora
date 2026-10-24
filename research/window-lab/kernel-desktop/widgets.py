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
            i['p'].close()

    def theme(self, mid, viewer):
        # Style source travels as data too, allowing richer painters to interpret
        # their own style tokens without granting the widget arbitrary reads.
        name = self.k.state.get(mid, 'style') or 'bars'
        style = next((s for s in self.k.things('style') if self.k.state.get(s, 'name') == name), None)
        a = self.k.shown(viewer, style) if style else None
        theme = dict(paper='#FAF9F6', card='#FFFFFF', ink='#293542', muted='#85909B', accent='#638779',
                    font='Segoe UI, system-ui, sans-serif', style=name, source=(a or {}).get('text', ''))
        for key, value in re.findall(r'^token\s+(paper|card|ink|accent)\s*=\s*(#[0-9a-fA-F]{6})\b',theme['source'],re.M):
            theme[key]=value
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
                self.instances[token] = dict(p=p, lease=lease, at=time.monotonic(), cursor=len(self.k.happenings),
                                             words=set(), calls=[], hits=[], paint=None)
                return dict(ok=True, instance=token, widget=mid, code=self.k.state.get(mid, 'code'),
                            name=self.k.state.get(mid, 'title') or self.k.name(mid), surface=surface, theme=self.theme(mid, actor.person))
            token = str(body.get('instance') or '')
            i = self.instances.get(token)
            if not i or i['p'].viewer.id != actor.id:
                raise Refused('no widget instance for this viewer')
            p = i['p']
            p.check()
            i['at'] = time.monotonic()
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
