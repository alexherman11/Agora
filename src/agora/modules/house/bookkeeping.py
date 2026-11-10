"""Durable reporting for House card writes, independent of the saved requester.

The coordination destination is house-settings.bookkeeping_failure_chat.
Only the House module's existing grants are used; a refusal never selects a
different writer. The ordinary House tick retries each undelivered destination.
"""
import hashlib
import json
from shlex import quote


def failed(b, state, exc):
    reason = f'{type(exc).__name__}: {exc}'[:2000]
    key = hashlib.sha256(json.dumps(
        [state['run'], state.get('land_attempt') or state.get('phase'), reason]
    ).encode()).hexdigest()
    notices = state.setdefault('bookkeeping_failures', {})
    if key not in notices:
        notices[key] = dict(key=key, task=state['task'], run=state['run'],
                            attempt=state.get('land_attempt', ''), reason=reason,
                            lead=state.get('bookkeeping_lead', ''), delivered=[])
        b.save(state)


def checked(out):
    if out.get('ok') is False or out.get('refused'):
        raise RuntimeError(out.get('text') or out.get('refused') or 'House notice refused')
    return out


def deliver(b, state):
    if not state.get('bookkeeping_failures'):
        return
    if not b.notification_lock.acquire(blocking=False):
        return
    try:
        for notice in list(state['bookkeeping_failures'].values()):
            for destination in ('lead', 'chat'):
                if destination in notice['delivered']:
                    continue
                try:
                    if 'text' not in notice:
                        text = b.message('House card write failed', state, reason=notice['reason'])
                        # Preserve diagnostic evidence even when the live template is absent.
                        notice['text'] = text + '\n' + json.dumps({
                            k: notice[k] for k in ('key', 'task', 'run', 'attempt', 'reason')
                        }, ensure_ascii=False)
                        b.save(state)
                    if destination == 'lead':
                        wake_lead(b, state, notice)
                    else:
                        post_notice(b, notice)
                    notice['delivered'].append(destination)
                    notice.pop(destination + '_error', None)
                except Exception as exc:
                    notice[destination + '_error'] = f'{type(exc).__name__}: {exc}'[:1000]
                b.save(state)
    finally:
        b.notification_lock.release()


def wake_lead(b, state, notice):
    # Resolve the current lead, not a stale requester or an earlier lead.
    rows = checked(b.h.m.see('look ' + quote(state['task']))).get('rows') or []
    if len(rows) == 1 and rows[0].get('id') == state['task']:
        notice['lead'] = rows[0].get('lead', '')
    lead = str(notice.get('lead') or '')
    agents = getattr(b.h, 'agents', {})
    matches = [(person, a) for person, a in agents.items()
               if lead and (person == lead or a.name.casefold() == lead.casefold())]
    if not lead:
        raise RuntimeError('card has no lead; notice remains pending')
    if len(matches) != 1:
        # A person without a House agent still gets an addressed world receipt.
        # The kernel checks recipient visibility and deduplicates this key.
        checked(b.h.m.do('notification.send ' + quote(state['task']) + ' to=' + quote(lead)
                         + ' key=' + quote(notice['key']) + ' text=' + quote(notice['text'])))
        notice['lead_person'] = lead
        return
    person, agent = matches[0]
    agent.wake(notice['text'])
    notice['lead_person'] = person


def post_notice(b, notice):
    target = b.settings().get('bookkeeping_failure_chat')
    if not target:
        raise RuntimeError('House settings bookkeeping_failure_chat is not configured')
    rows = checked(b.h.m.see('look ' + quote(str(target)))).get('rows') or []
    if len(rows) != 1 or rows[0].get('kind') != 'chat':
        raise RuntimeError('bookkeeping_failure_chat is not one visible chat')
    chat = rows[0]['id']
    # Read back before sending, including after a lost answer or a House crash.
    rows = checked(b.h.m.see('rows said chat=' + quote(chat) + ' about=' + quote(notice['task']))).get('rows') or []
    if not any(r.get('chat') == chat and r.get('about') == notice['task']
               and r.get('text') == notice['text'] for r in rows):
        checked(b.h.m.do('say ' + quote(chat) + ' about=' + quote(notice['task'])
                         + ' text=' + quote(notice['text'])))
    notice['chat'] = chat
