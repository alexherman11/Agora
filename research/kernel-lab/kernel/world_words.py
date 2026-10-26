"""Small general world operations used by community tools."""
from datetime import datetime, timezone

from .kernel import Refused


def utc(value):
    try:
        dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        if dt.tzinfo is None:
            raise ValueError()
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError):
        raise Refused('use a UTC date and time, such as 2026-11-04T19:00Z')


def clock(k, actor, st, entry, tx, group, saw=None):
    at = k.now().isoformat()
    return dict(text=at, rows=[dict(at=at)])


def group_word(k, actor, st, entry, tx, group, saw=None):
    if st.target:
        t = st.target
        if k.state.get(t, 'kind') != 'group' or not k.is_leader(actor.person, t):
            raise Refused('only a group leader changes this group')
        k.fence(actor, t, ['name', 'open'], saw)
    else:
        t = tx.mint()
        tx.set(t, 'kind', 'group')
        tx.set(t, 'made_by', actor.id)
        tx.set(t, 'in:' + group, len(k.log.records) + 1)
        tx.set(t, 'member:' + actor.person, 'leader')
    if any(a not in ('in', 'name', 'open') for a in st.kv):
        raise Refused('group takes name=, open=yes|no and in= only')
    if 'name' in st.kv:
        tx.set(t, 'name', st.kv['name'])
    if 'open' in st.kv:
        if st.kv['open'] not in ('yes', 'no'):
            raise Refused('open says yes or no')
        tx.set(t, 'open', st.kv['open'] == 'yes')
    return dict(text='ok group ' + t + ' [r?]')


def dictionary_copy(k, actor, st, entry, tx, group, saw=None):
    source = k.entry(st.target)
    word = st.kv.get('word') or source.get('word')
    from .words import VERB_NAME
    if source.get('from') != 'kernel' or not VERB_NAME.fullmatch(word or ''):
        raise Refused('copy a kernel word with a plain local name')
    if source.get('bound') in ('word-set', 'word-rename', 'module', 'grant', 'widget', 'component'):
        raise Refused('administrative words are not copied into groups')
    if any(k.state.get(e, 'word') == word and k.state.get(e, 'lives') == group for e in k.entries()):
        raise Refused('that group already has this word')
    t = tx.mint()
    for a, v in source.items():
        if a not in ('id', 'rev', 'made', 'changed', 'made_by', 'lives', 'aliases') and not a.startswith(('in:', 'sees')):
            tx.set(t, a, v)
    tx.set(t, 'kind', 'word')
    tx.set(t, 'word', word)
    tx.set(t, 'lives', group)
    tx.set(t, 'made_by', actor.id)
    tx.set(t, 'in:' + group, len(k.log.records) + 1)
    return dict(text='ok dictionary-copy ' + t + ' [r?]')


def forgotten(k, actor, st, entry, tx, group, saw=None):
    rows = []
    for t, a in k.state.things.items():
        if not a.get('forgotten') or not a.get('forget_reason'):
            continue
        if not k._sees(actor.person, a.get('sees', 'place'), t):
            continue
        parent = a.get('visibility_of')
        if parent and k.shown(actor.person, parent) is None:
            continue
        if a.get('sees_when') and not k.predicate(actor.person, a['sees_when'], t):
            continue
        rows.append(dict(id=t, by=k.name(a['forgotten']), reason=a['forget_reason'],
                         record='r' + str(k.state.last_seq(t, 'forgotten'))))
    return dict(text='\n'.join('hidden by ' + r['by'] + ': ' + r['reason'] for r in rows), rows=rows)
