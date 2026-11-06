"""Reconcile interrupted builder operations and deliver durable restart receipts.

This is lifecycle machinery, not a new source of authority. Existing claims,
holds, manager approvals and provider capacity still fence every continuation.
Message prose comes from the Agent Book; receipt fields describe observed state.
"""
import json
import os
import uuid


SHUTDOWN = 'House shutting down; preserve work and reconcile before retry'


def park(builders, state, reason):
    """Persist the interruption before stopping the process or losing its phase."""
    if state.get('restart_pending'):
        return
    state.update(cut_phase=state['phase'], cut_from=state.get('updated', ''),
                 restart_pending=True, phase='recovery-needed', detail=reason)
    state.pop('cut_told', None)
    state.pop('restart_context', None)
    state.pop('queued_turn', None)
    builders.save(state)


def last_words(state):
    if state.get('interrupted_words'):
        return state['interrupted_words']
    for entry in reversed(state.get('activity') or []):
        if entry.get('what') == 'said':
            return entry.get('text', '')
    return state.get('last_words', '')


def reason_to_wait(builders, state):
    from builders import alive, held

    task = builders.session(state['requester']).look(state['task'])
    if task.get('build_run') != state['run']:
        return 'card claim changed; retained work must be reconciled'
    if 'task_owner' in state and task.get('who', '') != state['task_owner']:
        return 'card owner changed; ownership needs reconciliation'
    if held(task):
        return 'card is held; automatic continuation is not authorised'
    if state.get('handover'):
        return 'ownership transfer is unresolved'
    if state.get('manager'):
        # The existing manager approval must still admit this card.
        import manager
        manager.check_state(builders, state)
    if state.get('land_attempt') or builders.cut_phase(state) != 'working':
        return 'interrupted ' + str(builders.cut_phase(state) or 'unknown operation') + '; effects need reconciliation'
    if state['phase'] == 'uncertain' or state.get('effects_unknown'):
        return 'unknown effects: ' + str(state.get('detail', 'lost operation result'))
    if state.get('in_flight_effects'):
        return 'unknown effects: tool completion was not observed'
    if not state.get('effect_tracking') and any(e.get('what') == 'act' for e in state.get('activity', [])):
        return 'unknown effects: older worker has no tool completion receipts'
    if alive(state.get('pid')) or alive(state.get('land_child_pid')) or state['task'] in builders.children:
        return 'previous process may still be running'
    if not state.get('session') or not state.get('tree'):
        return 'no retained session or worktree for a safe continuation'
    return ''


def sync_card(builders, state):
    """Retry failed bookkeeping, but never overwrite a successor's claim."""
    phase = state['phase']
    build = {'asked': 'asked', 'preparing': 'asked', 'working': 'building',
             'reviewing': 'landing', 'landing': 'landing', 'received': 'landing',
             'reviewed': 'landing', 'landed': 'landed', 'released': 'released',
             'queued': 'asked'}.get(phase, 'blocked')
    facts = dict(build=build, build_phase=phase, build_detail=str(state.get('detail', ''))[:1500])
    try:
        out = builders.h.m.see('look ' + state['task'])
        if out.get('ok') is False:
            raise RuntimeError('card reading unavailable')
        rows = out.get('rows') or []
        if len(rows) != 1:
            raise RuntimeError('card is not visible for bookkeeping')
        if rows[0].get('build_run') != state['run']:
            state.pop('restart_sync_pending', None)
            return
        if any(rows[0].get(k) != v for k, v in facts.items()):
            builders.update(state, **facts)
        state.pop('restart_sync_pending', None)
        state.pop('restart_sync_error', None)
    except Exception as exc:
        state['restart_sync_pending'] = True
        state['restart_sync_error'] = str(exc)
    finally:
        builders.save(state)


class Recovery:
    def __init__(self, builders):
        self.b = builders
        self.path = builders.home / 'restart-receipts.json'
        self.lock = builders.notification_lock
        self.records = json.loads(self.path.read_text(encoding='utf-8')) if self.path.exists() else []
        # Keep undelivered receipts across another restart; completed receipts
        # are already deduplicated in the receiving agent's durable inbox.
        self.records = [r for r in self.records if not r.get('complete')]
        self.current = dict(id=uuid.uuid4().hex, notices=[], reconciled=False)
        self.records.append(self.current)
        self.save()

    def save(self):
        tmp = self.path.with_suffix('.tmp')
        tmp.write_text(json.dumps(self.records, indent=2), encoding='utf-8')
        os.replace(tmp, self.path)

    def notice(self, record, key, person, text):
        record['notices'].append(dict(key=record['id'] + ':' + key, person=person, text=text))

    def receipt(self, event, **facts):
        evidence = json.dumps(dict(event=event, **facts), ensure_ascii=False)
        text = self.b.message("Someone woke them", by="House", words=evidence)
        return text + '\n' + evidence if text.startswith('Message unavailable:') else text

    def announce(self):
        record = self.current
        if not record.get('announced'):
            self.notice(record, 'restart', None, self.receipt('house-restarted', restart=record['id']))
            record['announced'] = True
            self.save()

    def reconcile(self):
        """Once per boot, inspect every parked operation; one bad card cannot stop the others."""
        from builders import CUT, WAITING, stamp

        b, record = self.b, self.current
        if record['reconciled']:
            return
        self.announce()
        resumed, waiting, owners = [], [], {}
        with b.lock:
            for state in list(b.states.values()):
                # Also repair stale working fields on ordinary stopped workers.
                if state['phase'] in WAITING or state.get('restart_pending'):
                    sync_card(b, state)
                unknown_block = state['phase'] == 'blocked' and (state.get('effects_unknown') or state.get('in_flight_effects'))
                if (state['phase'] not in CUT and not state.get('restart_pending') and not unknown_block) or b.card_done(state):
                    continue
                if state['phase'] in ('released', 'landed') and not state.get('land_attempt'):
                    continue
                try:
                    why = reason_to_wait(b, state)
                except Exception as exc:
                    why = 'reconciliation unavailable: ' + str(exc)
                row = dict(card=state['task'], run=state['run'], name=state['name'],
                           owner=state.get('requester_name') or state['requester'])
                if not why:
                    state['restart_context'] = dict(last_words=last_words(state),
                                                    interrupted_phase=b.cut_phase(state))
                    state['resume_note'] = {'heading': 'When a restart cut it off'}
                    state['queued_turn'] = stamp()
                    state['detail'] = 'safe restart continuation queued for a worker slot'
                    state['cut_told'] = stamp()
                    b.save(state)
                    resumed.append(row)
                else:
                    row['reason'] = why
                    row['phase'] = state['phase']
                    row['owner_available'] = b.usable(getattr(b.h, 'agents', {}).get(state['requester']))
                    waiting.append(row)
                    state['detail'] = why
                    state['restart_sync_pending'] = True
                    b.stopped(state)
                    sync_card(b, state)
                    state['last_outcome'] = [state['phase'], str(state.get('detail', ''))[:300],
                                             state.get('land_attempt')]
                    state.pop('outcome_pending', None)
                    if not state.get('cut_told'):
                        # The general manager's single summary is also the
                        # fallback when an owner is absent or cannot act.
                        person = state.get('manager') or state['requester']
                        owners.setdefault(person, []).append(row)
                state.pop('restart_pending', None)
                b.save(state)
            b.start_queued()
            for row in resumed:
                state = b.states[row['card']]
                row.update(phase=state['phase'], queued=bool(state.get('queued_turn')))
                sync_card(b, state)
        gm = b.general_manager()
        for person, rows in owners.items():
            if gm is not None and person == gm.person:
                continue
            self.notice(record, 'owner:' + person, person,
                        self.receipt('workers-await-reconciliation', workers=rows))
        self.notice(record, 'summary', None,
                    self.receipt('house-reconciled', resumed=resumed, waiting=waiting))
        record.update(reconciled=True, waiting=waiting)
        for earlier in self.records:
            if earlier is record or earlier['reconciled']:
                continue
            # Another restart interrupted reconciliation itself. Its pending
            # receipt is completed by this inspection, never silently dropped.
            if not earlier.get('announced'):
                self.notice(earlier, 'restart', None, self.receipt('house-restarted', restart=earlier['id']))
                earlier['announced'] = True
            self.notice(earlier, 'summary', None,
                        self.receipt('house-reconciled', continued_by=record['id'],
                                     resumed=resumed, waiting=waiting))
            earlier.update(reconciled=True, waiting=waiting)
        self.save()

    def deliver_notices(self, record):
        b = self.b
        for notice in record['notices']:
            if notice.get('delivered'):
                continue
            agent = (getattr(b.h, 'agents', {}).get(notice['person'])
                     if notice['person'] else b.general_manager())
            if agent is None:
                continue
            try:
                if hasattr(agent, 'wake_once'):
                    agent.wake_once(notice['key'], notice['text'])
                else:
                    agent.wake(notice['text'])
            except Exception:
                continue
            notice['delivered'] = True
            self.save()

    def deliver(self):
        b = self.b
        if self.current['reconciled'] and all(r.get('complete') for r in self.records):
            return
        if b.stopping or not self.lock.acquire(blocking=False):
            return
        try:
            self.announce()
            self.deliver_notices(self.current)  # announce restart before slow card reconciliation
            self.reconcile()
            for record in self.records:
                if record.get('complete'):
                    continue
                self.deliver_notices(record)
                record['complete'] = record['reconciled'] and all(n.get('delivered') for n in record['notices'])
                if record['complete']:
                    for row in record.get('waiting', []):
                        state = b.states.get(row['card'])
                        if (state and state['run'] == row['run'] and state['phase'] == row['phase']
                                and state.get('detail') == row['reason']):
                            state['cut_told'] = record['id']
                            # The restart receipt supersedes the generic
                            # outcome for this same interruption.
                            state['last_outcome'] = [state['phase'], str(state.get('detail', ''))[:300],
                                                     state.get('land_attempt')]
                            state.pop('outcome_pending', None)
                            b.save(state)
            self.save()
        finally:
            self.lock.release()
