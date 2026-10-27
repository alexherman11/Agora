"""Record readings. Never return raw testimony, seals, hashes or other things' facts."""
def trail(k, reader, thing):
    current = k.shown(reader, thing)
    if current is None:
        raise k.no_such(thing)
    past, rows = {}, []
    for rec in k.log.records:
        parts = [p for p in rec['parts'] if any(f[0] == thing for f in p['facts']) or p.get('target') == thing]
        if not parts:
            continue
        before = dict(past)
        touched = [f for p in parts for f in p['facts'] if f[0] == thing]
        for f in touched:
            if len(f) == 3:
                past.pop(f[1], None)
            else:
                past[f[1]] = f[3]
        # Both the current fence and the visibility at the time apply. A later
        # publication must not publish old private text retroactively.
        historical = past or before
        if not k._sees(reader, historical.get('sees', 'place'), thing):
            continue
        if historical.get('sees_when') and historical.get('sees_when') != k.state.get(thing, 'sees_when'):
            continue                         # changed policies cannot disclose an older protected reading
        sealed = rec.get('by') == 'sealed'
        facts = []
        for f in touched:
            aspect = f[1]
            if aspect.startswith(('like:', 'vote:', 'sees', 'allows.', 'in:', 'member:')):
                continue
            if sealed:
                continue
            if not k._sees(reader, k.state.get(thing, 'sees.' + aspect, 'place'), thing):
                continue
            if not k._sees(reader, historical.get('sees.' + aspect, 'place'), thing):
                continue
            if len(f) > 3 and isinstance(f[3], dict) and 'redacted' in f[3]:
                continue
            facts.append({'aspect': aspect, 'value': f[3]} if len(f) > 3 else {'aspect': aspect, 'removed': True})
        if not facts and not sealed and touched:
            continue
        eid = rec.get('entry')
        word = k.state.get(eid, 'word') or parts[0]['word']
        by = 'sealed' if sealed else (k.name(rec.get('by')) or 'someone')
        if not sealed and rec.get('via') == 'module' and rec.get('for'):
            by += ' for ' + k.name(rec['for'])
        def display(value):
            if isinstance(value, str) and value in k.state.things:
                visible = k.shown(reader, value)
                return (visible.get('title') or visible.get('name') or visible.get('label') or k.name(value)
                        or 'a thing') if visible is not None else 'a hidden thing'
            return str(value)
        changes = '; '.join(f"{f['aspect']}=" + (display(f['value']) if 'value' in f else '(removed)') for f in facts)
        rows.append({'record': 'r' + str(rec['seq']), 'at': rec['at'], 'by': by,
                     'word': word, 'facts': facts, 'changes': changes, 'sealed': sealed})
    return rows


def times(k, thing):
    history = k.state.history.get((thing, 'kind'), [])
    made = history[0][0] if history else None
    changed = k.state.rev.get(thing)
    return {key: k.log.records[seq - 1]['at'] for key, seq in [('made', made), ('changed', changed)] if seq}
