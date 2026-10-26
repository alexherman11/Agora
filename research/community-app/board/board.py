"""Board words. All durable state is things, all writes are admitted lines.

Kinds, channels, orderings, labels, rate limits and the default are world data.
This reviewed process supplies the readings and multi-thing validations that
the thin composition language cannot yet express.
"""
from datetime import datetime, timedelta, timezone

from protocol import hello, line, read, run


def stamp(value):
    result = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    if result.tzinfo is None:
        if len(str(value)) == 10:
            return result.replace(tzinfo=timezone.utc)
        raise ValueError('use a date or a time with UTC/timezone, such as 2026-11-04T19:00Z')
    return result


def owner(row):
    return row.get('for') or row.get('made_by')


def rows(use, kind, **filters):
    return read(use, line('rows ' + kind, **filters))


def get(use, kind, target):
    result = next((r for r in rows(use, kind) if r['id'] == target), None)
    if result is None:
        raise ValueError('no visible ' + kind + ' with that name')
    return result


def scope(row):
    return (row.get('groups') or [hello['place']])[0]


def leader(use, person, group):
    seen = set()
    while group and group not in seen:
        seen.add(group)
        a = read(use, 'look ' + group)[0]
        if a.get('member:' + person) == 'leader':
            return True
        group = next((k[3:] for k in a if k.startswith('in:')), None)
    return False


def answer(lines, *things):
    return dict(lines=lines, saw={r['id']: r['rev'] for r in things})


def own_marks(use, person):
    return [r for r in rows(use, 'board-mark') if owner(r) == person]


def visible_posts(use, person, channel=None):
    posts = rows(use, 'post')
    marks = own_marks(use, person)
    hidden = {r['about'] for r in marks if r.get('action') in ('hide', 'mute')}
    return [p for p in posts if p['id'] not in hidden and p.get('thread') not in hidden and
            (channel is None or scope(p) == channel)]


def why(post, replies, names=None):
    bits = []
    if post.get('pinned'):
        bits.append('pinned by ' + (names or {}).get(post['pinned'], 'a leader'))
    bits.append(str(post.get('likes', 0)) + ' upvotes')
    count = sum(1 for r in replies if r.get('thread') == post['id'])
    if count:
        bits.append(str(count) + ' replies')
    if post.get('answered'):
        bits.append('answered')
    if post.get('outcome'):
        bits.append('leader decision')
    return ' · '.join(bits)


def call(message):
    use, word = message['use'], message['word'].split('.')[-1]
    args = message.get('args') or {}
    kv, target = dict(args.get('kv') or {}), args.get('target')
    person = message['caller']['person']
    now = read(use, 'clock')[0]['at']
    group = kv.get('in') or hello['place']

    if word == 'post':
        channel = next((r for r in rows(use, 'board-channel') if r.get('group') == group), None)
        if not channel:
            raise ValueError('choose a board channel with in=<channel group>')
        kinds = rows(use, 'kind')
        name = kv.pop('post_kind', 'discussion')
        definition = next((r for r in kinds if r.get('name') == name or r['id'] == name), None)
        if not definition:
            raise ValueError('unknown post kind; make kind=kind name=… fields=… to add one')
        if definition.get('leaders_only') == 'yes' and not leader(use, person, group):
            raise ValueError('this kind is posted by a leader')
        allowed = set(str(definition.get('fields', '')).split()) | {'text', 'title', 'in'}
        if any(k not in allowed for k in kv):
            raise ValueError('this kind accepts: ' + ' '.join(sorted(allowed)))
        for required in str(definition.get('required', '')).split():
            if not kv.get(required):
                raise ValueError('this kind needs ' + required + '=')
        text = str(kv.pop('text', '') or args.get('words') or '').strip()
        if not text:
            raise ValueError('write some text before posting')
        if kv.get('closes'):
            stamp(kv['closes'])
        if kv.get('start'):
            stamp(kv['start'])
        if 'seats' in kv and (not str(kv['seats']).isdigit() or not 1 <= int(kv['seats']) <= 10000):
            raise ValueError('seats needs a number from 1 to 10000')
        if kv.get('options'):
            options = kv['options'].split()
            if len(set(options)) != len(options) or not 2 <= len(options) <= 20:
                raise ValueError('polls need 2 to 20 distinct options')
        kv['in'] = group
        kv['post_kind'] = definition['name']
        return answer([line('post', text=text, **kv)], definition, channel)

    if word == 'reply':
        parent = get(use, 'post', target)
        depth = int(parent.get('depth', 0)) + 1
        if depth > 2:
            raise ValueError('Replies stop at two levels. Reply to the thread to keep it readable.')
        text = str(kv.get('text') or args.get('words') or '').strip()
        if not text:
            raise ValueError('write a reply')
        extra, saw = {}, [parent]
        if kv.get('quote'):
            source = kv.get('source') or target
            try:
                page = int(kv.get('page', 1))
            except ValueError:
                raise ValueError('page must be a number starting at 1')
            source_posts = [r for r in rows(use, 'post') if r['id'] == source]
            if source_posts:
                passage = source_posts[0].get('text', '')
                saw += source_posts
            else:
                passage = read(use, line('file-read', source, page=page))[0]['text']
                source_rows = [r for r in rows(use, 'any') if r['id'] == source]
                saw += source_rows
            if kv['quote'] not in passage:
                raise ValueError('the quote must be an exact visible passage from that post or page')
            extra = dict(quote=kv['quote'], quote_source=source, quote_page=str(page))
        return answer([line('reply', text=text, reply_to=target, thread=parent.get('thread') or target,
            depth=str(depth), post_kind='reply', within=target, **{'in': scope(parent)}, **extra)], *saw)

    if word in ('answer', 'decide'):
        thread = get(use, 'post', target)
        group = scope(thread)
        leads = leader(use, person, group)
        if word == 'answer':
            if thread.get('post_kind') != 'question':
                raise ValueError('mark an answer on a question')
            if owner(thread) != person and not leads:
                raise ValueError('the asker or a leader marks the answer')
            reply = get(use, 'post', kv.get('reply'))
            if reply.get('thread') != target:
                raise ValueError('choose a reply in this thread')
            return answer([line('set', target, answered=reply['id'], answered_at=now)], thread, reply)
        if not leads:
            raise ValueError('a leader records the outcome')
        text = kv.get('text') or args.get('words')
        if not text:
            raise ValueError('write the decision outcome')
        return answer([line('make', kind='decision', text=text, about=target, within=target, **{'in': group}),
                       line('set', target, outcome=text, decided_at=now)], thread)

    if word in ('personal', 'seen', 'report'):
        if word == 'seen':
            existing = [r for r in rows(use, 'board-seen') if owner(r) == person]
            if existing:
                return answer([line('set', existing[0]['id'], at=now)], existing[0])
            return answer([line('make', kind='board-seen', at=now, sees='me')])
        post = get(use, 'post', target)
        if word == 'report':
            if not kv.get('reason'):
                raise ValueError('say why you are reporting this post')
            return answer([line('make', kind='board-report', about=target, reason=kv['reason'],
                within=target, sees='leaders', **{'in': scope(post)})], post)
        action = kv.get('action')
        if action not in ('hide', 'mute', 'bookmark', 'follow'):
            raise ValueError('action says hide, mute, bookmark or follow; undo the receipt to remove it')
        return answer([line('make', kind='board-mark', about=target, action=action, sees='me')], post)

    if word == 'rsvp':
        event = next((r for r in rows(use, 'post') + rows(use, 'event') if r['id'] == target), None)
        if not event or (event.get('post_kind') != 'event' and event['kind'] != 'event'):
            raise ValueError('RSVP to an event')
        status = kv.get('status', 'going')
        if status not in ('going', 'maybe'):
            raise ValueError('RSVP says going or maybe')
        # Both choices use the existing claim word and its undo, seat and once
        # checks. Status is a linked thing, so callers never edit the event.
        return answer([line('claim', target), line('make', kind='board-rsvp', status=status,
            about=target, within=target, **{'in': scope(event)})], event)

    if word == 'queue':
        result = rows(use, 'board-report')
        if kv.get('in'):
            result = [r for r in result if scope(r) == kv['in']]
        return dict(text=str(len(result)) + ' reports visible to your leadership', rows=result)

    if word == 'calendar':
        event = next((r for r in rows(use, 'post') + rows(use, 'event') if r['id'] == target), None)
        if not event or not event.get('start'):
            raise ValueError('choose an event with a start time')
        def escape(s):
            return str(s).replace('\\', '\\\\').replace('\r', '').replace('\n', '\\n').replace(',', '\\,').replace(';', '\\;')
        def date(s):
            return stamp(s).astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ') if len(s) > 10 else s.replace('-', '')
        lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Agora//Community board//EN',
                 'BEGIN:VEVENT', 'UID:' + target + '@agora', 'DTSTAMP:' + date(now)]
        for key, field in [('DTSTART', 'start'), ('DTEND', 'end'), ('SUMMARY', 'title'), ('LOCATION', 'location')]:
            if event.get(field):
                key += ';VALUE=DATE' if key in ('DTSTART', 'DTEND') and len(event[field]) == 10 else ''
                lines.append(key + ':' + (date(event[field]) if field in ('start', 'end') else escape(event[field])))
        lines += ['END:VEVENT', 'END:VCALENDAR', '']
        # RFC 5545 folding by UTF-8 bytes, with a continuation space.
        folded = []
        for raw in lines:
            current = ''
            for c in raw:
                if len((current + c).encode()) > 75:
                    folded.append(current)
                    current = ' '
                current += c
            folded.append(current)
        text = '\r\n'.join(folded)
        return dict(text=text, rows=[dict(filename=target + '.ics', mime_type='text/calendar', text=text)])

    if word == 'badges':
        groups = rows(use, 'group') + rows(use, 'place')
        groups = [read(use, 'look ' + g['id'])[0] for g in groups]
        people = rows(use, 'person')
        agents = rows(use, 'agent')
        result = []
        for p in people:
            badges = []
            if any(g.get('member:' + p['id']) == 'leader' and g['kind'] == 'place' for g in groups):
                badges.append('steward')
            if any(g.get('member:' + p['id']) == 'leader' and g['kind'] == 'group' for g in groups):
                badges.append('leader')
            result.append(dict(id=p['id'], name=p['name'], badges=badges))
        names = {p['id']: p['name'] for p in people}
        for agent in agents:
            result.append(dict(id=agent['id'], name='agent for ' + names.get(agent.get('for'), 'a person'), badges=['agent']))
        return dict(text='\n'.join(r['name'] + ': ' + ', '.join(r['badges']) for r in result), rows=result)

    posts = visible_posts(use, person, kv.get('in'))
    threads = [p for p in posts if not p.get('reply_to')]
    replies = [p for p in posts if p.get('reply_to')]
    if word == 'why-here':
        post = next((p for p in posts if p['id'] == target), None)
        if not post:
            raise ValueError('no visible post in your feed')
        names = {r['id']: r['name'] for r in rows(use, 'person')}
        return dict(text=why(post, replies, names), rows=[dict(id=target, why=why(post, replies, names))])
    if word == 'search':
        query = str(kv.get('q') or args.get('words') or '').casefold().strip()
        if not query:
            raise ValueError('search q="some words"')
        result = []
        files = {r['id']: r for r in rows(use, 'file')}
        hidden = {r['about'] for r in own_marks(use, person) if r.get('action') in ('hide', 'mute')}
        all_posts = {r['id']: r for r in rows(use, 'post')}
        for p in posts:
            if kv.get('kind') and p.get('post_kind') != kv['kind']:
                continue
            if kv.get('person') and owner(p) != kv['person']:
                continue
            if kv.get('since') and p['made'] < kv['since']:
                continue
            if kv.get('before') and p['made'] >= kv['before']:
                continue
            if query in (p.get('title', '') + '\n' + p.get('text', '')).casefold():
                result.append(dict(p, match='post text'))
        for doc in rows(use, 'document'):
            # Permission was already checked through the file's current parent.
            parent_id = files.get(doc.get('file_source'), {}).get('attached_to')
            parent = all_posts.get(parent_id)
            if parent_id in hidden or (parent and parent.get('thread') in hidden):
                continue
            if kv.get('in') and scope(parent or doc) != kv['in']:
                continue
            if kv.get('kind') and kv['kind'] != 'document':
                continue
            if kv.get('person') and owner(doc) != kv['person']:
                continue
            if kv.get('since') and stamp(doc['made']) < stamp(kv['since']):
                continue
            if kv.get('before') and stamp(doc['made']) >= stamp(kv['before']):
                continue
            content = read(use, 'file-read ' + doc['id'])[0]
            for i, page in enumerate(content.get('pages', []), 1):
                if query in page.casefold():
                    result.append(dict(id=doc['id'], match='document page', page=i, text=page,
                                       file_source=doc['file_source']))
        return dict(text=str(len(result)) + ' matches', rows=result)
    if word == 'catch-up':
        seen = [r for r in rows(use, 'board-seen') if owner(r) == person]
        since = kv.get('since') or (seen[0]['at'] if seen else '1970-01-01T00:00:00+00:00')
        marks = own_marks(use, person)
        following = {r['about'] for r in marks if r.get('action') == 'follow'}
        result = []
        for p in threads:
            for category, when in [('decision', p.get('decided_at')), ('event', p.get('made') if p.get('post_kind') == 'event' else None),
                                   ('answer', p.get('answered_at'))]:
                if when and stamp(when) > stamp(since):
                    result.append(dict(p, category=category))
        busy = []
        for p in threads:
            fresh = [r for r in replies if r.get('thread') == p['id'] and stamp(r['made']) > stamp(since)]
            if fresh:
                busy.append(dict(p, category='busy', new_replies=len(fresh)))
        result += sorted(busy, key=lambda p: (-p['new_replies'], p['id']))[:10]
        result += [dict(e, category='event') for e in rows(use, 'event') if e.get('file_source') and
                   stamp(e['made']) > stamp(since) and (not kv.get('in') or scope(e) == kv['in'])]
        result += [dict(r, category='following') for r in replies if r.get('thread') in following and stamp(r['made']) > stamp(since)]
        return dict(text='Catch-up since ' + since + ' · plain data, no model', rows=result)
    if word == 'feed':
        names = {r['id']: r['name'] for r in rows(use, 'person')}
        orders = rows(use, 'board-order')
        settings = rows(use, 'board-settings')
        selected = kv.get('order') or (settings[0].get('default_order') if settings else 'new')
        order = next((r for r in orders if r['id'] == selected or r.get('name') == selected), None)
        rule = order.get('rule') if order else selected
        if rule == 'top-week':
            cutoff = stamp(now) - timedelta(days=7)
            threads = [p for p in threads if stamp(p['made']) >= cutoff]
            key = lambda p: (bool(p.get('pinned')), p.get('likes', 0), p['made'])
        elif rule == 'needs-answers':
            threads = [p for p in threads if p.get('post_kind') == 'question' and not p.get('answered')]
            key = lambda p: (bool(p.get('pinned')), p['made'])
        elif rule == 'soon':
            threads = [p for p in threads if p.get('start') and stamp(p['start']) >= stamp(now)]
            threads.sort(key=lambda p: p['start'])
            key = None
        elif rule == 'bookmarks':
            bookmarked = {m['about'] for m in own_marks(use, person) if m.get('action') == 'bookmark'}
            threads = [p for p in threads if p['id'] in bookmarked]
            key = lambda p: p['made']
        elif rule == 'new':
            key = lambda p: (bool(p.get('pinned')), p['made'], p['id'])
        else:
            raise ValueError('ordering needs rule=new, top-week, needs-answers, soon or bookmarks')
        if key:
            threads.sort(key=key, reverse=True)
        for p in threads:
            p['why_here'] = why(p, replies, names)
            if p.get('seats_left') == 0:
                p['full'] = True
                p['closed_to_claims'] = True
        return dict(text=str(len(threads)) + ' threads · ' + str(selected), rows=threads)
    raise ValueError('unknown board word')


SPECS = [
    ('post', 'do', 'text=<text> [post_kind=<kind>] in=<group>', 'Post with a world-defined kind and its fields. Channel post may/once govern admission; upload separately, then attach.'),
    ('reply', 'do', '<id> text=<text> [quote=<passage> source=<id> page=N]', 'Reply to a thread or first reply, at most two levels. Exact quotes must be visible post text or document page text.'),
    ('answer', 'do', '<id> reply=<id>', 'The asker or a leader marks one reply as the answer. Undo restores needs-answer state.'),
    ('decide', 'do', '<id> text=<outcome>', 'A leader records an outcome on a thread and in catch-up, in one undoable act.'),
    ('personal', 'do', '<id> action=hide|mute|bookmark|follow', 'Private preference for this person and their agents. Hide/mute only changes your readings. Undo removes the mark.'),
    ('seen', 'do', '', 'Mark the kernel time last seen for you and your agents. Undo restores the previous marker. Read catch-up before marking.'),
    ('report', 'do', '<id> reason=<text>', 'Report a visible post with a reason. Only its group leaders see the report; undo removes it.'),
    ('rsvp', 'do', '<id> [status=going|maybe]', 'RSVP through claim, with a going/maybe marker. Both reserve one event seat. Undo releases the seat and status together.'),
    ('queue', 'see', '[in=<group>]', 'Read reports visible to your leadership, optionally in one channel.'),
    ('feed', 'see', '[order=<world ordering>] [in=<group>]', 'Your visible threads in a copyable world ordering. New, top-week, needs-answers, soon, bookmarks. Private hide/mute applies.'),
    ('catch-up', 'see', '[since=<UTC>] [in=<group>]', 'Plain data since your last-seen marker: decisions, events, answers, busiest threads and followed replies. No inference.'),
    ('why-here', 'see', '<id>', 'Read why this visible post is here: pin, upvotes, replies, answer and leader decision.'),
    ('search', 'see', 'q=<text> [in=<group> kind=<kind> person=<person> since=<UTC> before=<UTC>]', 'Search visible posts, replies and extracted document pages. No hidden files or private group text.'),
    ('calendar', 'see', '<id>', 'Export a visible event as RFC 5545 calendar text, with filename and MIME type for a download button.'),
    ('badges', 'see', '', 'Read real names and current leader/steward badges; agents say agent for <person>.'),
]

if __name__ == '__main__':
    run([dict(word='board.' + name, kind=kind, takes=takes, may='members', undo='yes' if kind == 'do' else 'no', help=help)
         for name, kind, takes, help in SPECS], call, 'Community board words; world definitions and caller-visible readings; no private store')
