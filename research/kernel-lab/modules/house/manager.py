"""Task-scoped native manager entry. A local startup approval is the authority.

World profile edits cannot expand this allowlist. Existing House words retain
steward admission; only this guarded endpoint admits the named resident person.
"""
import hashlib
import json
from pathlib import Path

OPS = {'build':'start', 'tell':'tell', 'retry':'retry', 'review':'request_review', 'land':'land'}
NOTE_FIELDS = {'status','blocker','next_action','result','evidence','review_note','verified_evidence'}
WRITE_FIELDS = NOTE_FIELDS | {'builder','build','build_run','build_phase','build_detail','builder_chat','result_received','reviewed_commit','landed_commit','outcome'}
TERMINAL = {'received', 'reviewed', 'landed', 'blocked', 'uncertain', 'recovery-needed'}


def permit(builders, person, task):
    try:
        data = json.loads((builders.h.world/'keep'/'house-managers.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        raise RuntimeError('no current local manager approval') from None
    grant = data.get(person) if isinstance(data, dict) else None
    if not isinstance(grant, dict) or grant.get('enabled') is not True or not grant.get('approval'):
        raise RuntimeError('manager approval is absent or revoked')
    tasks = grant.get('tasks')
    if (not isinstance(tasks, list) or len(tasks) != 3 or
            any(not isinstance(t, str) or not t.isalnum() for t in tasks) or len(set(tasks)) != 3):
        raise RuntimeError('manager approval must name exactly three distinct tasks')
    if task not in tasks:
        raise RuntimeError('this task is outside the manager approval')
    return grant


def check_state(builders, state):
    if state.get('manager'):
        if state['manager'] != state['requester']:
            raise RuntimeError('manager identity changed')
        permit(builders, state['requester'], state['task'])


def dispatch(builders, msg):
    caller = msg.get('caller') or {}
    args = msg.get('args') or {}
    person, target = caller.get('person'), args.get('target')
    if not person or caller.get('id') != person:
        return {'refused':'only the approved resident person may manage; builders cannot launch siblings'}
    try:
        permit(builders, person, target)
    except RuntimeError as e:
        return {'refused':str(e)}
    action = (args.get('kv') or {}).get('action', 'report')
    if action not in (*OPS, 'report', 'note'):
        return {'refused':'choose action=build, tell, retry, review, land, report or note'}
    # Task visibility remains the ordinary kernel fence. No global inventory is returned.
    rows = builders.h.m.see('look '+target, use=msg.get('use')).get('rows') or []
    if len(rows) != 1 or rows[0].get('kind') not in ('task','taskboard-task'):
        return {'refused':'the approved task is not visible'}
    state = builders.states.get(target)
    if state and state['requester'] != person:
        return {'refused':'the existing worker belongs to another requester'}
    if action == 'note':
        fields={k:v for k,v in (args.get('kv') or {}).items() if k!='action'}
        if not fields or not set(fields)<=NOTE_FIELDS:
            return {'refused':'notes may update status, blocker, next_action, result, evidence, review_note or verified_evidence only'}
        if rows[0].get('who') != caller.get('name'):
            return {'refused':'task owner changed; note was not written'}
        return write_task(builders, dict(manager=person,requester=person,task=target,task_owner=caller.get('name'),note_only=True), rows[0], fields)
    if action == 'report':
        if not state:
            return {'text':'No builder has been started for this task.'}
        out = {'task':target, 'phase':state['phase'], 'detail':state.get('detail',''),
               'session':state.get('session',''), 'turns':state.get('turns',0),
               'checks':state.get('checks',[]), 'candidate':state.get('candidate',''),
               'landed_commit':state.get('landed_commit','')}
        if state.get('tree'):
            path = Path(state['tree'])/'BUILD-RESULT.md'
            if path.is_file():
                raw=path.read_bytes()
                out.update(self_proof=raw[:24000].decode('utf-8','replace'),
                           self_proof_sha256=hashlib.sha256(raw).hexdigest(),
                           self_proof_truncated=len(raw)>24000)
        state['manager_seen_receipt'] = receipt_key(state)
        builders.save(state)
        return {'text':json.dumps(out,ensure_ascii=False), 'rows':[out]}
    managed = dict(msg, _managed=True)
    return getattr(builders, OPS[action])(managed)


def write_task(builders, state, task, facts):
    """Trusted House bookkeeping, constrained again by per-task kernel grants.

    The record is authored by the House for its sponsoring person; the builder
    state records which approved manager requested it. Rowan gets no raw set grant.
    """
    check_state(builders,state)
    if not facts or not set(facts)<=WRITE_FIELDS:
        raise RuntimeError('task bookkeeping fields outside manager scope')
    if task.get('id') != state['task']:
        raise RuntimeError('task bookkeeping target changed')
    if task.get('who','') != state.get('task_owner',''):
        raise RuntimeError('task owner changed; bookkeeping held')
    if not state.get('note_only'):
        from builders import held
        if held(task):
            raise RuntimeError('task is held; bookkeeping did not change it')
        if state.get('basis') and any(task.get(k,'') != v for k,v in state['basis'].items()):
            raise RuntimeError('task instructions changed; bookkeeping held for owner review')
    def q(v):return '"'+str(v).replace('\\','\\\\').replace('"','\\"')+'"'
    out=builders.h.m.do('set '+state['task']+' '+' '.join(k+'='+q(v) for k,v in facts.items()),
                        saw={state['task']:int(task['rev'])})
    if 'did not answer' in str(out.get('refused') or out.get('text') or ''):
        raise TimeoutError('task bookkeeping outcome uncertain; inspect receipt before retry')
    if out.get('ok') is False or out.get('refused'):
        raise RuntimeError(out.get('text') or out.get('refused') or 'task bookkeeping refused')
    if out.get('record') and 'records' not in out:out['records']=[out['record']]
    return out


def receipt_key(state):
    return [state['phase'],state.get('updated',''),state.get('detail','')]


def notify(builders, state):
    """One bounded owner wake per terminal receipt, recoverable at House startup.

    Replaying an informational receipt after an interrupted handoff is harmless:
    the owner must reread canonical state, and lifecycle calls fence effects.
    """
    if not state.get('manager') or state.get('phase') not in TERMINAL:
        return
    if state['task'] in builders.children:
        return
    try:
        check_state(builders,state)
    except RuntimeError:
        return
    agent = getattr(builders.h,'agents',{}).get(state['manager'])
    if agent is None or agent.cfg.get('want') == 'asleep':
        return
    receipt = receipt_key(state)
    notified = getattr(builders, '_manager_notifications', {})
    builders._manager_notifications = notified
    if state.get('manager_seen_receipt') == receipt or notified.get(state['task']) == receipt:
        return
    agent.wake('~ Your builder has a receipt for '+state.get('title',state['task'])+' ('+state['task']+'): '
               +state['phase']+'. Read house.manage '+state['task']+' action=report and its current card. '
               'Received is not reviewed; landed is not activated or verified. Continue only this approved task, '
               'respect holds and corrections, coordinate activation with JEFF in Shop talk.')
    # Delivery is only an in-process suppression. A restart re-wakes any receipt
    # the owner has not actually read through action=report.
    notified[state['task']] = receipt
