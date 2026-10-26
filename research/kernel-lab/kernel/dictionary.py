"""Steward edits and stable bindings. Translations name the same entry."""
import re

from .kernel import Refused, MAY_WORDS
from . import lines as L


def names(a):
    return {str(a.get('word', '')).casefold(), *str(a.get('aliases', '')).casefold().split(),
            *(str(v).casefold() for f, v in a.items() if f.startswith('label.'))}


def check_names(k, t, values):
    a = dict(k.state.things[t], **values)
    module = str(a.get('from', '')).startswith('module:')
    namespace = a.get('from', '')[7:] + '.'
    for n in names(a):
        if not n or re.search(r'[\s;=$]', n):
            raise Refused('a dictionary name is one word, without spaces, ;, = or $')
        if '.' in n and not (module and n.startswith(namespace)):
            # Kernel administration words are the only built-in dotted names.
            if not (a.get('from') == 'kernel' and n == a.get('bound')):
                raise Refused('dotted names belong to the implementing module')
        other = k.find_entry(n, a.get('lives'))
        if other and other != t:
            raise Refused(f'{n} already answers here')


def word_set(k, actor, st, entry, tx, group, saw=None):
    t = st.target
    if k.state.get(t, 'kind') != 'word':
        raise Refused('word-set needs a dictionary entry')
    scope = k.state.get(t, 'lives')
    if not k.is_steward(actor.person) and not (scope and k.is_leader(actor.person, scope)):
        raise Refused('stewards edit place words; group leaders edit their scoped entries')
    values = dict(st.kv)
    values.pop('in', None)
    allowed = {'help', 'aliases', 'may', 'undo', 'takes', 'once', 'sealed', 'status'}
    if not values or any(f not in allowed and not re.fullmatch(r'(label|help)\.[a-z][a-z0-9-]*', f)
                         for f in values):
        raise Refused('word-set edits help, aliases, may, undo, takes, once, sealed, status, label.<lang>, help.<lang>')
    if 'help' in values and not values['help'].strip():
        raise Refused('a word with no help is not published')
    if 'may' in values and not all(x.strip() in MAY_WORDS for x in values['may'].split(' or ')):
        raise Refused('may says anyone, members, leaders, stewards, maker or nobody, joined by or')
    if 'undo' in values and values['undo'] not in ('yes', 'no', 'external'):
        raise Refused('undo says yes, no or external')
    if 'sealed' in values and values['sealed'] not in ('yes', 'no'):
        raise Refused('sealed says yes or no')
    if 'status' in values and values['status'] not in ('live', 'old', 'hidden'):
        raise Refused('status says live, old or hidden')
    if 'aliases' in values:
        values['aliases'] = values['aliases'].casefold()
    check_names(k, t, {f: v for f, v in values.items() if v})
    k.fence(actor, t, list(values), saw)
    if 'aliases' in values or any(f.startswith('label.') for f in values):
        bind_legacy(k, tx)
    for f, v in values.items():
        if v:
            tx.set(t, f, v)
        else:
            tx.set(t, f)
    return {'text': 'ok word-set [r?]'}


def word_rename(k, actor, st, entry, tx, group, saw=None):
    t, name = st.target, st.kv.get('to', '').casefold()
    if k.state.get(t, 'kind') != 'word' or not name:
        raise Refused('word-rename <entry> to=<new name>')
    if not k.is_steward(actor.person):
        raise Refused('only stewards rename dictionary entries')
    check_names(k, t, {'word': name})
    k.fence(actor, t, ['word'], saw)
    bind_legacy(k, tx)
    tx.set(t, 'word', name)
    return {'text': 'ok word-rename [r?] · stored lines keep their entry ids'}


def bind_legacy(k, tx):
    """Capture old worlds' saved heads before any dictionary name can change."""
    for t, a in k.state.things.items():
        group = a.get('lives') or (k.groups_of(t) or [k.place])[0]
        if a.get('from') == 'verb' and not a.get('steps_bound'):
            tx.set(t, 'steps_bound', bind(k, a['steps'], group, a['word'], t))
        if a.get('kind') == 'rule':
            if not a.get('do_bound'):
                tx.set(t, 'do_bound', bind(k, a.get('do', ''), group))
            if not a.get('on_entry'):
                eid = k.find_entry(a.get('on', ''), group)
                if eid:
                    tx.set(t, 'on_entry', eid)


def language(k, actor, st, entry, tx, group, saw=None):
    code = st.words.strip().lower()
    if not re.fullmatch(r'[a-z][a-z0-9-]{0,34}', code) or k.state.get(actor.person, 'kind') != 'person':
        raise Refused('language <code>: choose your language, for example language es')
    tx.set(actor.person, 'language', code)
    return {'text': 'ok language ' + code + ' [r?]'}


def bind(k, text, group, self_word=None, self_id=None):
    """Keep authored text separately; only the executable heads become entry ids."""
    lines = []
    for line in L.split_batch(text):
        raw = re.sub(r'^do\s+', '', line.strip())
        st = L.parse(raw)
        eid = self_id if st.word == self_word else k.find_entry(st.word, st.kv.get('in') or group)
        if not eid:
            raise Refused(f'nothing answers to {st.word}; stored lines need published words')
        lines.append(re.sub(r'^\S+', eid, raw, count=1))
    return '; '.join(lines)


def localized(k, person, a):
    language = k.state.get(person, 'language') or k.state.get(person, 'lang')
    if not language:
        return a
    return dict(a, word=a.get('label.' + language, a.get('word')),
                help=a.get('help.' + language, a.get('help')))
