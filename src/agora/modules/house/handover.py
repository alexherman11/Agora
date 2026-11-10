"""Recoverable House ownership transfer across the card and saved worker state.

The saved requester is the worker's authority. A durable intent fences lifecycle
actions while a card write is unresolved; only that intent can reconcile it.
No ownership is inferred from an independently edited card or a display name.
"""
from copy import deepcopy


PENDING = 'its handoff is unresolved; repeat house.hand with the same recipient to reconcile it'


def receipt(state, text, status):
    return {'text': text, 'external': True,
            'rows': [dict(task=state['task'], build_run=state['run'], status=status,
                          owner=state['requester'], owner_name=state.get('requester_name', ''))]}


def chat_for(b, state, door, person):
    """Recover the chat from an earlier timed-out/deduplicated make."""
    from builders import q
    rows = door.call('/see', 'rows chat about=' + state['task']).get('rows') or []
    matches = [r['id'] for r in rows if r.get('kind') == 'chat'
               and r.get('about') == state['task'] and r.get('name') == state['name']
               and r.get('with') == person
               and (r.get('for') == person or r.get('made_by') == person)]
    if len(matches) > 1:
        raise RuntimeError('multiple recipient chats match this worker; reconcile its chat first')
    if matches:
        return matches[0]
    out = door.call('/do', 'make kind=chat name=' + q(state['name'])
                    + ' about=' + state['task'] + ' with=' + person,
                    press=state['run'] + '-chat-' + person)
    made = out.get('made') or []
    if len(made) != 1:
        raise RuntimeError('chat creation has no confirmed chat; repeat the handoff to read it back')
    return made[0]


def finish(b, state, task):
    """Commit the canonical owner only after this intent's card write is visible."""
    from builders import stamp
    with b.lock:
        hand = state.get('handover')
        if not hand or hand.get('step') != 'writing':
            return False
        if (task.get('build_run') != state['run'] or task.get('who') != hand['name']
                or task.get('lead') != hand['name'] or task.get('builder_chat') != hand['chat']
                or int(task['rev']) <= hand['rev']):
            return False
        candidate = deepcopy(state)
        candidate.update(requester=hand['person'], requester_name=hand['name'],
                         task_owner=task.get('who', ''), chat=hand['chat'], tellers=[], told_by=[],
                         boss_note={'heading': 'Worker brief', 'facts': {
                             'text': task.get('text', ''), 'acceptance': task.get('acceptance', '')}},
                         awaiting=stamp(), hand_notice=dict(hand))
        for key in ('manager', 'reminded', 'handover'):
            candidate.pop(key, None)
        if candidate.get('basis'):
            candidate['basis'] = {k: task.get(k, '') for k in ('title', 'text', 'acceptance', 'who')}
        candidate.setdefault('handed', []).append(
            dict(at=stamp(), by=hand['by'], was=hand['was'], to=hand['name']))
        candidate.setdefault('activity', []).append(dict(
            at=stamp(), what='handed', text=f'{hand["by"]} handed it from {hand["was"]} to {hand["name"]}'))
        candidate['activity'] = candidate['activity'][-100:]
        candidate['hand_receipt'] = dict(status='handed', owner=hand['person'], owner_name=hand['name'])
        b.save(candidate)                 # a failed save must not change the in-memory authority
        state.update(candidate)
        for key in ('manager', 'reminded', 'handover'):
            state.pop(key, None)
    return True


def deliver(b, state):
    """Notification failure cannot turn a completed transfer into a refusal."""
    from builders import q
    # A different notice may still be waiting on an agent. The durable notice
    # stays queued for the next tick; a hand receipt never waits for that lock.
    if not b.notification_lock.acquire(blocking=False):
        return
    try:
        hand = state.get('hand_notice')
        if not hand:
            return
        agent = getattr(b.h, 'agents', {}).get(hand['person'])
        if agent is None:
            return
        note = b.message('A worker was handed to them', state, by=hand['by'], was=hand['was'],
                         detail=str(state.get('detail', ''))[:500],
                         words=str(state.get('last_words') or '').strip()[:2500])
        if not hand.get('recipient_notified'):
            agent.wake(note)
            hand['recipient_notified'] = True
            b.save(state)
        if hand.get('caller') and hand['caller'] != hand['person']:
            context = dict(requester=hand['caller'], requester_name=hand['by'],
                           task=state['task'], name=state['name'])
            b.wake_owner(context, f'Handoff completed: {hand["name"]} is in charge of '
                         f'{state["name"]}; the card and saved worker agree.')
        state.pop('hand_notice', None)
        b.save(state)
        try:
            b.session(hand['person']).call('/do', f'say {hand["chat"]} text={q(note[:3000])}')
        except Exception:
            pass                         # owner delivery succeeded; chat is only a copy
    finally:
        b.notification_lock.release()


def reconcile(b, state):
    """Read back an uncertain write on the normal tick, including after restart."""
    with b.lock:
        hand = state.get('handover')
        if state['task'] in b.handing or not hand or hand.get('step') != 'writing':
            return
        b.handing.add(state['task'])
    try:
        finish(b, state, b.session(hand['person']).look(state['task']))
    finally:
        with b.lock:
            b.handing.discard(state['task'])


def hand(b, msg):
    from builders import ACTIVE, DoorRefused, q
    args, caller = msg.get('args') or {}, msg.get('caller') or {}
    state = b.states.get(args.get('target'))
    name = str(args.get('words') or '').strip().lstrip('@').strip()
    if not state:
        return {'refused': 'this card has no worker'}
    if not name:
        return {'refused': 'house.hand <card> <name>: who takes it'}
    with b.lock:
        if not (b.may_act(state, msg) or b.alex(caller.get('person'))):
            return {'refused': "only the worker's owner, a steward or Alex may hand it on"}
        agents = getattr(b.h, 'agents', {})
        to = next((a for a in agents.values() if a.name.casefold() == name.casefold()), None)
        if to is None:
            return {'refused': f'{name} is not a House agent; they are: '
                               + ', '.join(a.name for a in agents.values())}
        pending = state.get('handover')
        if state['task'] in b.handing or (pending and pending['person'] != to.person):
            return receipt(state, PENDING, 'unresolved')
        if not pending and to.person == state['requester']:
            return receipt(state, f'{to.name} is already in charge of {state["name"]}', 'handed')
        if state['task'] in b.children or state['phase'] in ACTIVE or b.landing_busy(state):
            return {'refused': f"it is {state['phase']} now; hand it on once it stops"}
        if state['phase'] == 'released':
            return {'refused': 'it was released; house.build starts a new worker on the card'}
        if not pending:
            pending = dict(person=to.person, name=to.name, step='preparing',
                           by=caller.get('name') or caller.get('person'),
                           caller=caller.get('person'),
                           was=state.get('requester_name') or state['requester'])
            state['handover'] = pending
            b.save(state)
        b.handing.add(state['task'])
    try:
        door = b.session(to.person)
        task = door.look(state['task'])
        if pending['step'] == 'preparing':
            if task.get('build_run') != state['run']:
                raise RuntimeError('the card moved on to another worker')
            chat = chat_for(b, state, door, to.person)
            # Use only the authenticated caller's session. A denial is final,
            # never a reason to try somebody else's authority.
            writer = b.session(caller.get('person'))
            task = writer.look(state['task'])
            if task.get('build_run') != state['run']:
                raise RuntimeError('the card moved on to another worker')
            pending.update(step='writing', chat=chat, rev=int(task['rev']))
            b.save(state)                # intent is durable before the remote mutation
            try:
                writer.call('/do', f'set {state["task"]} who={q(to.name)} lead={q(to.name)} '
                            f'builder_chat={q(chat)}', saw={state['task']: pending['rev']})
            except DoorRefused:
                # Door.call raises DoorRefused only for an explicit negative
                # receipt. Transport loss has an unknown outcome and stays pending.
                pending['step'] = 'refused'
                raise
            task = door.look(state['task'])
        if not finish(b, state, task):
            return receipt(state, PENDING, 'unresolved')
        return settled(b, state, to.name)
    except Exception as exc:
        if pending['step'] in ('preparing', 'refused'):
            with b.lock:
                state.pop('handover', None)
                b.save(state)
            return {'refused': f'not handed: {exc}'}
        # Even a failed read can follow a successful write. Read-only recovery
        # may confirm it; never replay an uncertain card mutation.
        try:
            reconcile_task = b.session(to.person).look(state['task'])
            if not finish(b, state, reconcile_task):
                return receipt(state, f'{PENDING}: {exc}', 'unresolved')
            return settled(b, state, to.name)
        except Exception:
            return receipt(state, f'{PENDING}: {exc}', 'unresolved')
    finally:
        with b.lock:
            b.handing.discard(state['task'])


def settled(b, state, name):
    try:
        deliver(b, state)
    except Exception:
        pass
    notice = '; owner notification is pending' if state.get('hand_notice') else '; its owner was notified'
    return dict(receipt(state, f'{name} is in charge of {state["name"]} now{notice}', 'handed'),
                caller_receipt=True)
