"""EDITING THE KERNEL (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
The kernel changes only to give every world a general capability: a word, a check, a kind of fact any app, module or
person can use. It never names its tenants: no app, module, person, kind or field name appears in this code except the
kernel's own (word, rule, kind, grant, person, ...).

Text with a history (Builder draft by Claude, 4 Nov 2026, from Alex: "make it a crdt ... make documents work more like a
regular document editor"). `edit <thing> field=<name> changes=<json> base=<len:hash>` changes a text fact by its
changed spans instead of resending the whole text, and keeps every change, with who made it and when, in a Loro CRDT
document beside the world (`<world>/bodies/<thing>.<field>.loro`). The fact itself is still the truth everyone reads:
the edit ends as an ordinary `set` of the new text (every check `set` makes, its record, undo, hear:set). The body is
history kept beside it, and never served: deleted words live there, so only the kernel reads it.

- changes: a JSON list of [from, to, inserted], positions in UTF-16 code units (what a browser counts) into the base
  text, in ascending order and not overlapping. [[3, 3, "x"]] inserts x at 3; [[3, 5, ""]] deletes two.
- base: the length and FNV-1a hash of the text the changes were made against (`fingerprint` below; the page computes
  the same). If the fact still says that text, the changes apply to it.
- version: (optional) what an earlier edit returned. If the text changed meanwhile and the body still holds the base,
  the changes merge into the newer text, as a CRDT merges. Otherwise the edit is refused as stale and nothing changes:
  the writer applies what changed to its own copy and sends again.

Anyone who writes the fact another way (`set`, `undo`, an agent writing the whole text) is fine: before the next edit
the body takes the fact's text as one change, so the body never disagrees with the world.
"""
import json
import threading
from pathlib import Path

from .kernel import Refused

FOLD_AFTER = 400          # appended updates before the file is folded into one snapshot
_lock = threading.Lock()


def fingerprint(text):
    """Length and FNV-1a (32 bit) over UTF-16 code units: what a page can compute without crypto."""
    data = str(text).encode('utf-16-le')
    h = 0x811c9dc5
    for i in range(0, len(data), 2):
        h ^= data[i] | (data[i + 1] << 8)
        h = (h * 0x01000193) & 0xffffffff
    return f'{len(data) // 2}:{h:08x}'


def apply_spans(text, changes):
    """The text with the changes applied (UTF-16 positions), or Refused."""
    data = str(text).encode('utf-16-le')
    n = len(data) // 2
    last = -1
    spans = []
    for c in changes:
        if not (isinstance(c, list) and len(c) == 3 and all(isinstance(x, int) for x in c[:2]) and isinstance(c[2], str)):
            raise Refused('edit changes= is a list of [from, to, inserted]')
        a, b, ins = c
        if a < max(last, 0) or b < a or b > n or (a < last):
            raise Refused('edit changes must be in order, not overlapping, and inside the text')
        last = b
        spans.append((a, b, ins))
    for a, b, ins in reversed(spans):
        data = data[:a * 2] + ins.encode('utf-16-le') + data[b * 2:]
    return data.decode('utf-16-le'), spans


class Body:
    """One text fact's history: a Loro document whose text container `text` follows the fact."""

    def __init__(self, path):
        import loro
        self.loro = loro
        self.path = path
        self.doc = loro.LoroDoc()
        self.doc.set_record_timestamp(True)
        self.doc.set_change_merge_interval(30)
        self.appended = 0
        if path.exists():
            raw = path.read_bytes()
            blobs, i = [], 0
            while i + 4 <= len(raw):
                size = int.from_bytes(raw[i:i + 4], 'big')
                if i + 4 + size > len(raw):
                    break                       # a torn last write: the fact catches the body up below
                blobs.append(raw[i + 4:i + 4 + size])
                i += 4 + size
            if blobs:
                self.doc.import_batch(blobs)
            self.appended = len(blobs)
        self.text = self.doc.get_text('text')

    def string(self):
        return self.text.to_string()

    def version(self):
        return self.doc.oplog_frontiers.encode().hex()

    def commit(self, by):
        self.doc.set_next_commit_message(json.dumps(by, sort_keys=True))
        self.doc.commit()

    def follow(self, current, by):
        """Take the fact's current text as one change, if someone wrote it another way."""
        if self.string() != current:
            if len(current) > 50000 or len(self.string()) > 50000:
                self.text.update_by_line(current)
            else:
                self.text.update(current)
            self.commit(by)

    def apply(self, spans, by):
        for a, b, ins in reversed(spans):
            if b > a:
                self.text.delete_utf16(a, b - a)
            if ins:
                self.text.insert_utf16(a, ins)
        self.commit(by)

    def merge(self, version, base, spans, by):
        """Apply spans made against an older version, merged into the newest text. None if the body lacks it."""
        loro = self.loro
        try:
            at = loro.Frontiers.decode(bytes.fromhex(version))
            fork = self.doc.fork_at(at)
        except Exception:
            return None
        ft = fork.get_text('text')
        if fingerprint(ft.to_string()) != base:
            return None
        for a, b, ins in reversed(spans):
            if b > a:
                ft.delete_utf16(a, b - a)
            if ins:
                ft.insert_utf16(a, ins)
        fork.set_next_commit_message(json.dumps(by, sort_keys=True))
        fork.commit()
        self.doc.import_(fork.export(loro.ExportMode.Updates(fork.frontiers_to_vv(at))))
        return self.string()

    def save(self, since):
        """Append what changed since the version vector `since`; fold into one snapshot now and then."""
        loro = self.loro
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.appended >= FOLD_AFTER or not self.path.exists():
            snap = self.doc.export(loro.ExportMode.Snapshot())
            tmp = self.path.with_suffix('.tmp')
            tmp.write_bytes(len(snap).to_bytes(4, 'big') + snap)
            tmp.replace(self.path)
            self.appended = 1
            return
        update = self.doc.export(loro.ExportMode.Updates(since))
        with open(self.path, 'ab') as f:
            f.write(len(update).to_bytes(4, 'big') + update)
        self.appended += 1


def _body(k, t, field):
    cache = k.__dict__.setdefault('_bodies', {})
    key = (t, field)
    if key not in cache:
        cache[key] = Body(Path(k.dir) / 'bodies' / f'{t}.{field}.loro')
    return cache[key]


def edit(k, actor, st, entry, tx, group, saw=None):
    from .words import set_
    t = st.target
    kv = dict(st.kv)
    field = kv.pop('field', '') or 'text'
    if not field.replace('_', '').replace('-', '').isalnum() or field in ('kind', 'id', 'in', 'as'):
        raise Refused('edit field= names one text fact, such as field=text')
    try:
        changes = json.loads(kv.pop('changes', '[]') or '[]')
    except ValueError:
        raise Refused('edit changes= must be JSON: [[from, to, "inserted"], ...]')
    if not isinstance(changes, list):
        raise Refused('edit changes= is a list of [from, to, inserted]')
    base = str(kv.pop('base', ''))
    version = str(kv.pop('version', ''))
    if kv:
        raise Refused('edit takes field=, changes=, base= and version= only; set changes other facts')
    if k.shown(actor.person, t) is None:
        raise k.no_such(t)
    current = k.state.get(t, field)
    current = '' if current is None else str(current)
    if not isinstance(k.state.get(t, field, ''), str) and current:
        raise Refused(f'{k.name(t)} {field}= is not text')
    by = {'by': actor.id, 'for': actor.person}
    with _lock:
        body = _body(k, t, field)
        since = body.doc.oplog_vv
        body.follow(current, {'by': 'outside'})
        new, spans, merged = None, None, False
        if fingerprint(current) == base:
            new, spans = apply_spans(current, changes)
            merged = False
        elif version:
            # the text changed since the writer's base: merge, if the body still knows that base
            _, spans = apply_spans('\x00' * int(base.split(':')[0] or 0), changes) if base.split(':')[0].isdigit() \
                else (None, None)
            if spans is not None:
                new = body.merge(version, base, spans, by)
            merged = new is not None
        if new is None:
            if body.doc.oplog_vv != since:
                body.save(since)
            raise Refused(f'stale: {k.name(t)} {field}= changed since this edit began; nothing was done. '
                          f'Apply what changed and send again (now {fingerprint(current)}).')
        if not merged:
            body.apply(spans, by)
        if body.string() != new:          # never let the body disagree with the fact
            body.follow(new, by)
        if new == current:
            body.save(since)
            return {'text': f'{k.name(t)} already says that; nothing changed',
                    'rows': [{'id': t, 'field': field, 'base': fingerprint(new), 'version': body.version()}]}
        st.kv = {field: new}
        try:
            # every check set makes (who may, scopes, validation); the base fingerprint above was the fence
            out = set_(k, actor, st, entry, tx, group, saw={t: k.state.rev.get(t, 0)})
        except Exception:
            k._bodies.pop((t, field), None)     # forget the unsaved change; the file still holds what was kept
            raise
        body.save(since)
    text = out.get('text', '') if isinstance(out, dict) else str(out)
    text = text.split(' · ', 1)[0] + f' · {field}= edited in {len(spans)} place{"s" if len(spans) != 1 else ""}' \
        + (', merged with a change made meanwhile' if merged else '')
    row = {'id': t, 'field': field, 'base': fingerprint(new), 'version': body.version(), 'merged': merged}
    if merged:
        row['text'] = new                 # the writer had only its own changes; it needs the merged text to go on
    return {'text': text, 'rows': [row]}


def edits(k, actor, st, entry, tx, group, saw=None):
    """see: a text fact's history from its body, grouped as Loro groups changes (who, when, how many)."""
    t = st.target
    field = st.kv.get('field') or 'text'
    if k.shown(actor.person, t) is None:
        raise k.no_such(t)
    path = Path(k.dir) / 'bodies' / f'{t}.{field}.loro'
    if not path.exists():
        return {'text': f'{k.name(t)} {field}= has no edit history yet', 'rows': []}
    with _lock:
        body = _body(k, t, field)
        rows = []
        try:
            changes = body.doc.export_json_updates(body.loro.VersionVector(), body.doc.oplog_vv)
            data = json.loads(changes) if isinstance(changes, str) else changes
            for c in (data.get('changes') or []):
                try:
                    who = json.loads(c.get('msg') or '{}')
                except ValueError:
                    who = {}
                rows.append({'by': who.get('by', ''), 'for': who.get('for', ''), 'at': c.get('timestamp'),
                             'ops': len(c.get('ops') or [])})
        except Exception as exc:              # an older wheel without JSON export: say what is there
            return {'text': f'{k.name(t)} {field}= history: {body.doc.len_changes} changes ({exc})', 'rows': []}
    rows.sort(key=lambda r: r['at'] or 0)
    named = lambda w: w if w in ('outside', '') else k.name(w)
    lines = [f"{named(r['for'] or r['by'])} · {r['ops']} op{'s' if r['ops'] != 1 else ''}" for r in rows[-12:]]
    return {'text': f'{k.name(t)} {field}= · {len(rows)} changes kept\n' + '\n'.join(lines), 'rows': rows}
