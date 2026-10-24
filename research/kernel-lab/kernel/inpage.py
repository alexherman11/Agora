"""In-page modules. Transport and rendering belong to a host; powers stay here.

A fresh principal per viewer/instance keeps fence observations out of other pages.
No bearer credential is minted for the untrusted page.
"""
from .kernel import Actor, Refused


class Principal:
    def __init__(self, kernel, mid, viewer, instance):
        self.k, self.mid, self.viewer = kernel, mid, viewer
        self.actor = Actor(mid, viewer.person, 'module', module=mid, caller=viewer)
        self.actor.seen_key = f'{mid}@{viewer.id}@{instance}'
        with kernel.lock:
            self.generation = self.version()
            self.check()

    def version(self):
        s = self.k.state
        return (s.last_seq(self.mid, 'on'), s.last_seq(self.mid, 'code'))

    def check(self):
        k, m = self.k, self.mid
        if (k.state.get(m, 'kind') != 'widget' or not k.state.get(m, 'code') or
                not k.state.get(m, 'on') or k.state.get(m, 'forgotten') or
                self.version() != self.generation or k.shown(self.viewer.person, m) is None):
            raise Refused('this widget is off or changed; reopen it')

    def run(self, line, mode='do', saw=None):
        with self.k.lock:
            self.check()
        return self.k.run(self.actor, line, mode=mode, saw=saw)

    def hears(self, word):
        with self.k.lock:
            self.check()
            return any(self.k._matches(' '.join(w[5:] for w in
                       (self.k.state.get(g, 'words') or '').split() if w.startswith('hear:')), word)
                       for g in self.k._grants_to(self.mid))

    def hold(self, word):
        with self.k.lock:
            self.check()
            eid = self.k.find_entry(word)
            if not eid or self.k.state.get(eid, 'word_kind') != 'hold' or not self.k.may(
                    self.actor, self.k.entry(eid), self.mid, self.k.place):
                raise Refused(f'no grant to hold {word}')
            return self.k.hold(self.mid, word)[0]

    def close(self):
        self.k.seen.pop(self.actor.seen_key, None)


def widget(k, actor, st, entry, tx, group, saw=None):
    """Explicit local activation, separate from portable code definitions."""
    m = st.target
    if k.state.get(m, 'kind') != 'widget' or not k.state.get(m, 'code'):
        raise Refused('widget needs a widget thing with code')
    k.fence(actor, m, ['on'], saw)
    surface = st.kv.get('surface', 'window')
    if surface not in ('window', 'top', 'bottom', 'overlay'):
        raise Refused('surface is window, top, bottom or overlay')
    words = st.kv.get('grants', '')
    for g in k._grants_to(m):
        tx.set(g, 'revoked', True)
    for key, value in dict(on=True, surface=surface, **{'for':actor.person}).items():
        tx.set(m, key, value)
    g = tx.mint()
    for key, value in dict(kind='grant', to=m, words=words, where=group, by=actor.person).items():
        tx.set(g, key, value)
    if st.kv.get('only'):
        tx.set(g, 'only', st.kv['only'])
    return {'text': f'ok widget {k.name(m)} [r?] · explicit grants; off stops it'}
