"""EDITING A MODULE (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
A module is a seam to something outside the kernel (a model provider, git, Twitch, the media session, a map server) and
turns it into world facts and words. What the world does with them (who is told, when, in what words, how it looks)
belongs in rules, lenses and this module's settings thing, read at each use. Names (JEFF, Alex), ids (dk...), models,
counts, timeouts and message text in this file are debt: move them to settings when you touch them, and never add more.

Kernel House builders. No Frontier queue and no credentials or grants minted here.

Calls return a durable request promptly. A builder uses the requester's existing
agent session, just as residents use their own door sessions (MOVING-IN D3).
Received work is reviewed independently; neither a model result nor landing
closes the user's task. Restart uncertainty is held for explicit reconciliation.
"""
import hashlib
import json
import os
from pathlib import Path
import queue
import subprocess
import tempfile
import threading
import time
import urllib.request
import urllib.error
import uuid

import transport as T
import manager as M
from messages import message
import review_suites
import handover
import landing_control
import bookkeeping
import restart_recovery

ACTIVE = {'asked', 'preparing', 'working', 'reviewing', 'landing'}
RESUMABLE = {'received', 'blocked', 'reviewed'}   # stopped, not landed or released: house.tell gives it a new turn
CUT = {'recovery-needed', 'uncertain'}             # cut off (House restart, lost answer): resumable once its process is gone
WAITING = RESUMABLE | CUT                          # stopped and waiting on the one in charge of it
FINISHED = {'done', 'verified', 'finished', 'completed', 'released', 'cancelled', 'trashed'}   # a card's lane or status
QUEUED = 'queued'                                  # asked for while every slot of its kind was busy: starts when one frees


class Released(Exception):
    """Its card no longer holds this worker (moved on to another run, or finished): it ends quietly as released."""


def alive(pid):
    """Is this process still running? Unsure counts as alive, so a cut-off worker is never run twice."""
    if not pid:
        return False
    try:
        import ctypes
        k = ctypes.windll.kernel32
        h = k.OpenProcess(0x1000, False, int(pid))          # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return k.GetLastError() == 5                     # access denied: something is there
        code = ctypes.c_ulong()
        ok = k.GetExitCodeProcess(h, ctypes.byref(code))
        k.CloseHandle(h)
        return not ok or code.value == 259                   # STILL_ACTIVE
    except Exception:                                        # noqa: BLE001
        return True
HELD = {'yes', 'true', '1', 'paused', 'held', 'blocked', 'cancelled', 'canceled'}
CHECKS = [
    ['research/kernel-lab/tests/test_chat.py', 'research/kernel-lab/tests/test_paint_health.py',
     'research/kernel-lab/modules/house/test_imports.py'],
    ['research/window-lab/kernel-desktop/test_kdesk.py'],
]


def q(value):
    return json.dumps(str(value), ensure_ascii=False)


def stamp():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def short(text, n):
    """Cut at a whole word (Sable, 28 Oct: a card title ended mid-word)."""
    text = ' '.join(str(text).split())
    if len(text) <= n:
        return text
    cut = text[:n - 1].rsplit(' ', 1)[0].rstrip(' ,.;:')
    return (cut or text[:n - 1]) + '…'


def held(task):
    return task.get('lane', '').lower() == 'done' or any(
        str(task.get(k, '')).lower() in HELD for k in
        ('paused', 'cancelled', 'permission_required', 'approval_required', 'status'))


class DoorRefused(RuntimeError):
    """A negative kernel receipt, distinct from losing a mutation's answer."""


class Door:
    def __init__(self, url, token):
        self.url, self.token = url, token
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def call(self, route, line, **extra):
        req = urllib.request.Request(self.url + route, json.dumps(dict(line=line, **extra)).encode(),
            {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + self.token})
        # No mutation retries: a lost answer is uncertain, not permission to replay.
        with self.opener.open(req, timeout=20) as reply:
            out = json.load(reply)
        if not out.get('ok'):
            raise DoorRefused(out.get('text') or out.get('error') or 'door refused')
        return out

    def look(self, target):
        rows = self.call('/see', 'look ' + target).get('rows') or []
        if len(rows) != 1:
            raise RuntimeError('task is missing or not visible')
        return rows[0]


PROVIDERS = {  # Alex, 28 Oct: up to four Claude and four Codex workers at a time
    # the model and reasoning here are only the fallback: House settings `claude_model`, `claude_reasoning`,
    # `codex_model`, `codex_reasoning` choose them (Alex, 4 Nov: numbers and names live in the world)
    'claude': dict(model='claude-opus-5-5', reasoning='medium', label='Claude'),
    'codex': dict(model='gpt-6.1-sol', reasoning='medium', label='Codex'),
}
REASONING = {'low', 'medium', 'high', 'xhigh'}
# Alex, 4 Nov: no limit on a worker's turns or on how long a turn runs, unless House settings set `max_turns` or
# `worker_timeout` (seconds); left out, there is none.
CLAUDE_TOOLS = ('Bash', 'Read', 'Edit', 'MultiEdit', 'Write', 'Glob', 'Grep', 'TodoWrite',
                'mcp__agora__see', 'mcp__agora__do', 'mcp__agora__lines')
CLAUDE_DENIED = ('Bash(git push:*)', 'Bash(git checkout main:*)', 'Bash(git switch main:*)', 'Bash(git reset --hard:*)',
                 'Bash(git worktree:*)', 'Bash(git branch -D:*)', 'Bash(rm -rf /*)', 'Bash(taskkill:*)', 'Bash(shutdown:*)')


class Builders:
    def settings(self):
        """The House settings thing's facts, read each time (never cached): {} when there is none."""
        reading = self.h.m.see('rows house-settings')
        rows = [r for r in reading.get('rows', []) if r.get('kind') == 'house-settings']
        return rows[0] if len(rows) == 1 else {}

    def worker_model(self, provider):
        """(model, reasoning) for a new worker of this provider: House settings, else the PROVIDERS fallback."""
        s, p = self.settings(), PROVIDERS[provider]
        model = str(s.get(provider + '_model') or '').strip() or p['model']
        reasoning = str(s.get(provider + '_reasoning') or '').strip().lower()
        return model, (reasoning if reasoning in REASONING else p['reasoning'])

    def limit(self, name):
        """A positive whole number from House settings (max_turns, worker_timeout), or None: no limit."""
        value = str(self.settings().get(name) or '').strip()
        return int(value) if value.isdigit() and int(value) > 0 else None

    def capacity_for(self, provider):
        """Each provider has its own pool: house-settings `claude_workers` / `codex_workers` (1 to 4), default 4.
        The older shared `builder_capacity` still sizes the Codex pool when `codex_workers` is not set."""
        reading = self.h.m.see('rows house-settings')
        if reading.get('ok') is False:
            raise RuntimeError('worker capacity unavailable; no new worker admitted')
        settings = [r for r in reading.get('rows', []) if r.get('kind') == 'house-settings']
        if len(settings) > 1:
            raise RuntimeError('ambiguous house settings; no new worker admitted')
        row = settings[0] if settings else {}
        raw = row.get(provider + '_workers', row.get('builder_capacity', 4) if provider == 'codex' else 4)
        value = str(raw).strip()
        if value not in ('1', '2', '3', '4'):
            raise RuntimeError(f'{provider}_workers must be 1 to 4; no new worker admitted')
        return int(value)

    def full(self, provider):
        busy = sum((s['phase'] in ACTIVE or s['task'] in self.children
                    or (s['phase'] in WAITING and (alive(s.get('pid')) or alive(s.get('land_child_pid')))))
                   and s.get('provider', 'codex') == provider
                   for s in self.states.values())
        return busy >= self.capacity_for(provider)

    @property
    def capacity(self):
        """World-configured shared pool, bounded by the existing four-worker cap.

        Lowering the value never interrupts work already admitted. Invalid or
        ambiguous configuration closes admission until the owner corrects it.
        """
        reading = self.h.m.see('rows house-settings')
        if reading.get('ok') is False:
            raise RuntimeError('builder capacity unavailable; no new worker admitted')
        settings = [r for r in reading.get('rows', []) if r.get('kind') == 'house-settings']
        if len(settings) > 1:
            raise RuntimeError('ambiguous house settings; no new worker admitted')
        raw = settings[0].get('builder_capacity', 2) if settings else 2
        value = str(raw).strip()
        if value not in ('1', '2', '3', '4'):
            raise RuntimeError('builder_capacity must be 1 to 4; no new worker admitted')
        return int(value)

    def __init__(self, house, repo=T.REPO):
        self.h = house
        self.repo = Path(repo)
        self.home = house.home / 'builders'
        self.home.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.notification_lock = threading.RLock()
        self.states, self.children = {}, {}
        self.handing = set()
        self.request_receipts = {}
        self.stopping = False
        self.landing_lock = threading.Lock()          # only publication shares exclusion with imports
        self.landing_queue_lock = threading.Lock()    # reviews queue here; imports only share publication
        self.land_controls = {}
        self.land_context = threading.local()
        self.house_restart_due = False                # a landed change to the House itself: restart once all is idle
        for path in self.home.glob('*/state.json'):
            state = json.loads(path.read_text(encoding='utf-8'))
            if state.get('superseded_by'):        # an earlier run of a card that has had a new one
                continue
            if state.get('land_child_pid') and not alive(state['land_child_pid']):
                state.pop('land_child_pid')
            if state['phase'] in ACTIVE or state.get('land_in_progress') or state.get('land_child_pid'):
                restart_recovery.park(self, state, f"House restarted while it was {state['phase']}")
                if state.get('land_attempt'):
                    state.update(phase='blocked', outcome_pending=True, land_sync_pending=True,
                                 land_in_progress=False,
                                 detail='House restarted during landing at ' + state.get('land_step', 'unknown'))
                    self.landing_receipt(state)
            elif state['phase'] == 'blocked' and state.get('detail') == restart_recovery.SHUTDOWN:
                # Migrate the old shutdown failure that startup used to ignore.
                cut = self.cut_phase(state)
                restart_recovery.park(self, state, state['detail'])
                state['cut_phase'] = cut
            rows=house.m.see('look '+state['task']).get('rows') or []
            if rows and rows[0].get('build_run') != state['run'] and state['phase'] not in ('released', 'landed'):
                state.update(phase='released',detail='its card moved on to another worker; its worktree is kept')
            elif rows and state['phase'] not in ('landed', 'released') and any(
                    str(rows[0].get(f, '')).strip().casefold() in FINISHED for f in ('lane', 'status')):
                state.update(phase='released', detail='its card is finished; its worktree is kept')
            if rows and state.get('handover') and state['phase'] != 'released':
                handover.finish(self, state, rows[0])
            self.states[state['task']] = state
            self.save(state)
        self.recovery = restart_recovery.Recovery(self)

    def save(self, state):
        with self.lock:
            folder = self.home / state['run']
            folder.mkdir(exist_ok=True)
            tmp = folder / 'state.tmp'
            tmp.write_text(json.dumps(state, indent=2), encoding='utf-8')
            os.replace(tmp, folder / 'state.json')

    def event(self, state, what, text, detail=None):
        with self.lock:
            entry = dict(at=stamp(), what=what, text=str(text)[:4000])
            if detail is not None:
                entry['detail'] = detail
            state.setdefault('activity', []).append(entry)
            state['activity'] = state['activity'][-100:]
            self.save(state)
        self.h.m.happen('house.doing', state['task'], str(text)[:200])

    def session(self, person):
        # Existing account/person mapping, never a name-based authority guess.
        keep = self.h.world / 'keep'
        accounts = json.loads((keep / 'accounts.json').read_text(encoding='utf-8'))
        sessions = json.loads((keep / 'sessions.json').read_text(encoding='utf-8'))
        tokens = [token for token, entry in sessions.items()
                  if entry.get('agent') and accounts.get(entry.get('account')) == person]
        if len(tokens) != 1:
            raise RuntimeError('requester has no unambiguous existing builder agent session; no credential was created')
        return Door(self.h.builder_url, tokens[0])

    git_lock = threading.Lock()

    def land_check(self):
        control = getattr(self.land_context, 'control', None)
        if control:
            control.check()

    def git_guard(self):
        blocker = self.landing_blocker()
        if blocker:
            raise RuntimeError(blocker)
        control = getattr(self.land_context, 'control', None)
        return control.acquire(self.git_lock, 'git') if control else self.git_lock

    def landing_blocker(self):
        """A crash/OS denial may leave a child alive. Never guess that its writes stopped."""
        for state in self.states.values():
            pid = state.get('land_child_pid')
            control = self.land_controls.get(state['task'])
            if pid and (control is None or control.unstopped is not None) and alive(pid):
                return f"landing child PID {pid} may still be running for {state['task']}; inspect it before retrying"
        return ''

    def landing_busy(self, state):
        return (state['task'] in self.land_controls or
                bool(state.get('land_child_pid') and alive(state['land_child_pid'])))

    def git(self, cwd, *args):
        """27 Oct: twice a git call finished its work but held the House past its timeout (a background repack, then
        two parallel reviews' `git add` stuck ~25 min). So: no auto gc/maintenance; one git at a time; stdin is empty,
        never the House's own kernel pipe; output goes to files, so no leftover child can hold a pipe open; and a
        timeout kills git's whole process tree."""
        cmd = ['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', '-C', str(cwd), *args]
        self.land_check()
        with self.git_guard(), tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
            proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=out, stderr=err, creationflags=T.NO_WINDOW)
            try:
                control = getattr(self.land_context, 'control', None)
                code = control.wait(proc, 120) if control else proc.wait(timeout=120)
            except subprocess.TimeoutExpired:
                if not control:
                    subprocess.run(['taskkill', '/T', '/F', '/PID', str(proc.pid)], capture_output=True,
                                   stdin=subprocess.DEVNULL, timeout=30, creationflags=T.NO_WINDOW)
                raise
            out.seek(0), err.seek(0)
            stdout = out.read().decode('utf-8', 'replace')
            stderr = err.read().decode('utf-8', 'replace')
        if code:
            raise RuntimeError((stderr or stdout)[-2000:])
        return stdout.strip()

    def update(self, state, **facts):
        M.check_state(self, state)
        if not facts or not set(facts) <= M.BUILD_FIELDS:
            raise RuntimeError('task bookkeeping fields outside House build scope')
        try:
            return self._update_build_fields(state, facts)
        except Exception as exc:
            bookkeeping.failed(self, state, exc)
            raise

    def _update_build_fields(self, state, facts):
        for attempt in range(4):
            out = self.h.m.see('look ' + state['task'])
            if out.get('ok') is False or out.get('refused'):
                raise RuntimeError(out.get('text') or out.get('refused') or 'task reading refused')
            rows = out.get('rows') or []
            if len(rows) != 1 or rows[0].get('id') != state['task']:
                raise RuntimeError('task bookkeeping target is not visible to the House')
            task = rows[0]
            state['bookkeeping_lead'] = task.get('lead', '')
            if task.get('build_run') != state['run']:
                raise RuntimeError('claim changed; the previous builder cannot update this task')
            try:
                if state.get('manager'):
                    return M.write_task(self, state, task, facts)
                return M.write_facts(self, task, facts)
            except RuntimeError as exc:
                # 28 Oct: JEFF, as lead, set the card between this read and write; the run blocked before its
                # worktree. The claim is re-read each time, so another writer's facts are never overwritten blind.
                if 'stale' not in str(exc) or attempt == 3:
                    raise

    def phase(self, state, phase, detail, **facts):
        self.land_check()
        if self.stopping and phase in ACTIVE:
            restart_recovery.park(self, state, restart_recovery.SHUTDOWN)
            raise RuntimeError(restart_recovery.SHUTDOWN)
        state.update(phase=phase, detail=detail, updated=stamp())
        self.event(state, phase, detail)
        build = {'asked':'asked', 'preparing':'asked', 'working':'building', 'reviewing':'landing',
                 'received':'landing', 'reviewed':'landing', 'landed':'landed', 'released':'released'}.get(phase, 'blocked')
        self.update(state, build=build, build_phase=phase, build_detail=detail[:1500], **facts)
        self.try_start_outcome(state)

    def start_request(self, msg):
        """The protocol acknowledged this call; reconcile its eventual result."""
        caller = msg.get('caller') or {}
        context = dict(requester=caller.get('person'), requester_name=caller.get('name'),
                       task=(msg.get('args') or {}).get('target') or '', name=msg['word'])
        try:
            operation = self.work if msg['word'] == 'house.work' else self.start
            out = operation(dict(msg, _start_notice=True))
        except Exception as exc:
            # A door timeout can follow a successful write. Never call that a refusal.
            out = {'text': f'start unresolved: {exc}; reconcile the card before trying again',
                   'external': True}
        if out.get('rows'):
            state = self.states.get(out['rows'][0].get('task'))
            if state and state['phase'] == QUEUED:
                self.try_start_outcome(state)
        else:
            result = out.get('refused') or out.get('text', '')
            self.request_receipts[msg['use']] = (context, result)
            self.deliver_start_requests()
        return out

    def deliver_start_requests(self):
        with self.notification_lock:
            for request, (context, result) in list(self.request_receipts.items()):
                try:
                    self.wake_owner(context, self.message("Start request settled", context, result=result)
                                    + '\n' + result)
                except Exception:
                    continue
                self.request_receipts.pop(request, None)

    def try_start_outcome(self, state):
        # Lifecycle callers may hold self.lock. A notifier saves under self.lock:
        # never wait for it here (notification_lock -> lock versus lock -> notification_lock).
        if not self.notification_lock.acquire(blocking=False):
            return
        try:
            self._start_outcome(state)
        finally:
            self.notification_lock.release()

    def _start_outcome(self, state):
        if not state.get('start_notice'):
            return
        if state['phase'] == 'asked':
            return                          # claim has not reached the card yet
        try:
            card = self.session(state['requester']).look(state['task'])
            result = dict(request=state['start_notice'], card=state['task'], build_run=card.get('build_run', ''),
                          build=card.get('build', ''), build_phase=card.get('build_phase', ''),
                          request_phase=state['phase'], detail=state.get('detail', ''))
            self.wake_owner(state, self.message("Start request settled", state, result=json.dumps(result))
                            + '\n' + json.dumps(result), receipt=('start', state['start_notice']))
            state.pop('start_notice', None)
            state['start_receipt'] = result
            self.save(state)
        except Exception as exc:
            self.event(state, 'unsaid', f'start wake: {exc!r}')

    def start(self, msg):
        target = (msg.get('args') or {}).get('target')
        if not target or not target.isalnum():
            return {'refused': 'house.build needs a task'}
        caller = msg.get('caller') or {}
        # Read as this caller narrowed by the House's existing read grant.
        rows = self.h.m.see('look ' + target, use=msg.get('use')).get('rows') or []
        # which things a build reaches is the word's shape (needs=kind=taskboard-task|task, kernel kinds.py), checked
        # before the house is asked, so a steward can widen it in the world without editing this file
        if not rows:
            return {'refused': 'choose a visible task card'}
        task = rows[0]
        # A card may have a new run once its last one landed or was released (e.g. landed then reverted).
        prev = self.states.get(target)
        # ... or when its last run was cut off (House restart) or failed: nothing runs, and its worktree stays for reading
        again = bool(prev) and prev['phase'] in ('landed', 'released', 'recovery-needed', 'blocked', 'uncertain')             and target not in self.children
        claimed = task.get('builder') or task.get('build_run')
        if held(task) or (claimed and not (again and task.get('build_run') in (prev['run'], None, ''))):
            return {'refused': 'task is held, finished, or already has a builder; reconcile it before a new build'}
        if msg.get('_managed') and task.get('who') != caller.get('name'):
            return {'refused': 'approved manager no longer owns this task'}
        if task.get('who') and task.get('who') not in (caller.get('name'), 'JEFF'):
            return {'refused': 'task has another owner; ask that owner to release it first'}
        self.session(caller['person'])  # validate before recording or spawning anything
        kv = (msg.get('args') or {}).get('kv') or {}
        provider = str(kv.get('with') or kv.get('provider') or 'codex').lower()
        if provider not in PROVIDERS:
            return {'refused': 'with=claude or with=codex'}
        if msg.get('_managed') and provider != 'codex':
            return {'refused': 'managed builds use Codex workers'}
        p = PROVIDERS[provider]
        with self.lock:
            if prev and self.landing_busy(prev):
                return {'refused': 'the House is settling its landing; wait before replacing this worker'}
            if target in self.states and not again:
                return {'text': 'existing request: ' + self.states[target]['phase'], 'rows': [self.row(self.states[target])]}
            queued = self.full(provider)       # every slot busy: it waits its turn (start_queued), never refused
            model, reasoning = self.worker_model(provider)
            run = 'kernel-' + target + '-' + uuid.uuid4().hex[:10]
            state = dict(task=target, run=run, name=p['label']+' — '+short(task.get('title') or 'Builder', 60), requester=caller['person'],
                         requester_name=caller.get('name', ''), provider=provider,
                         title=task.get('title') or target, phase='asked', detail='claim pending',
                         model=model, reasoning=reasoning, created=stamp(), activity=[],
                         task_owner=task.get('who',''), pending=[], basis={k:task.get(k,'') for k in ('title','text','acceptance','who')})
            if msg.get('_start_notice'):
                state['start_notice'] = msg.get('use')
            if msg.get('_managed'):
                state['manager'] = caller['person']
                M.check_state(self, state)
            if again:
                state['previous_run'] = prev['run']
                prev['superseded_by'] = run
                self.save(prev)
            if queued:
                state.update(phase=QUEUED, detail=f'waiting for a free {provider} slot')
            self.states[target] = state
            self.save(state)
            if queued:
                self.event(state, QUEUED, state['detail'])
                return {'text': f'all {self.capacity_for(provider)} {provider} workers are busy; this one starts by itself '
                                f'as soon as one is free', 'external': True, 'rows': [self.row(state)]}
            threading.Thread(target=self.guarded, args=(state, self.build), daemon=True).start()
        return {'text': 'builder request recorded; claim and launch follow asynchronously', 'external': True,
                'rows': [self.row(state)]}

    def guarded(self, state, operation):
        try:
            operation(state)
        except Released as exc:
            self.released(state, str(exc))
        except Exception as exc:
            halted, releasing = state.pop('halted_by', None), state.pop('releasing', None)
            uncertain=isinstance(exc,(TimeoutError,ConnectionError,urllib.error.URLError,subprocess.TimeoutExpired))
            if uncertain:
                state['effects_unknown'] = True
            if releasing:
                self.released(state, releasing)
                return
            if halted:
                state.update(phase='blocked', detail=f"stopped by {halted}; house.tell {state['task']} <words> starts it "
                                                     f"again with new words, house.release {state['task']} drops it")
            elif self.stopping and (state['phase'] in ACTIVE or state.get('restart_pending')):
                restart_recovery.park(self, state, restart_recovery.SHUTDOWN)
            else:
                state.update(phase='uncertain' if uncertain else 'blocked', detail=str(exc)[:2000])
            self.event(state, state['phase'], state['detail'])
            try:
                if not uncertain:
                    self.update(state, build='blocked', build_phase=state['phase'], build_detail=state['detail'])
            except Exception:
                # The local receipt remains authoritative if ownership/door changed.
                pass
        finally:
            try:
                M.notify(self, state)
            except Exception as exc:
                self.event(state, 'unsaid', f'manager wake: {exc!r}')
            try:
                self.try_start_outcome(state)
                self.outcome(state)
            except Exception as exc:                 # noqa: BLE001  telling is a help, never a reason to fail
                self.event(state, 'unsaid', f'outcome wake: {exc!r}')
            try:                                     # a slot may be free now; a House change may be waiting for quiet
                self.start_queued()
                self.idle_check()
            except Exception as exc:                 # noqa: BLE001
                self.event(state, 'unsaid', f'queue or restart check: {exc!r}')

    def released(self, state, detail):
        """It ends for good: nothing runs, nobody is reminded, its worktree and branch are kept for reading."""
        for k in ('awaiting', 'reminded', 'halted_by', 'releasing', 'queued_turn', 'quiet'):
            state.pop(k, None)
        state['pending'] = []
        state.update(phase='released', detail=detail, updated=stamp())
        self.event(state, 'released', detail)
        try:
            self.update(state, build='released', build_phase='released', build_detail=detail[:1500])
        except Exception:                            # noqa: BLE001  its card moved on: the new run's facts aren't ours
            pass
        self.save(state)

    def start_queued(self):
        """A slot came free: queued workers start, then queued follow-ups, oldest first. Nothing waiting is refused."""
        with self.lock:
            if self.stopping:
                return
            waiting = sorted((s for s in self.states.values() if s['phase'] == QUEUED or s.get('queued_turn')),
                             key=lambda s: s.get('queued_turn') or s.get('created') or '')
            for state in waiting:
                if state.get('handover'):
                    continue
                try:
                    if self.full(state.get('provider', 'codex')):
                        continue
                except RuntimeError:
                    return
                if state['phase'] == QUEUED:
                    state.update(phase='asked', detail='claim pending')
                    self.save(state)
                    self.event(state, 'asked', 'a slot came free; it starts now')
                    threading.Thread(target=self.guarded, args=(state, self.build), daemon=True).start()
                elif self.resumable(state) and (state.get('pending') or state.get('resume_note')):
                    state.pop('queued_turn', None)
                    self.reopen(state)
                    threading.Thread(target=self.guarded, args=(state, self.resume), daemon=True).start()
                else:
                    state.pop('queued_turn', None)
                    self.save(state)

    def idle_check(self):
        """A landed change to the House itself switches on as soon as no git step is under way (Alex, 5 Nov: a
        restart pauses each agent and worker and continues them when it is back, instead of waiting for quiet).
        Agents mid-turn are said their turn again (house.py, in_flight); workers mid-turn carry on by themselves
        (wake_cut_off). Only claiming, review and landing touch git, so only those are waited for."""
        if not self.house_restart_due or self.stopping:
            return
        if self.land_controls or self.landing_blocker():
            return
        if any(s['phase'] in ('reviewing', 'landing', 'asked', 'preparing') for s in self.states.values()):
            return
        self.house_restart_due = False
        self.spawn_reload(['house'], self.home / 'activation-house.log')

    def spawn_reload(self, args, log):
        """kd_reload, detached from the House (it may restart the House itself), with no window."""
        helper = Path(__file__).resolve().parent / 'activate_now.py'
        pyw = Path(str(T.PY)).with_name('pythonw.exe')
        exe = pyw if pyw.exists() else Path(str(T.PY))
        line = f'"{exe}" "{helper}" --log "{log}" ' + ' '.join(args)
        ps = ("$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = '"
              + line.replace("'", "''") + "' }; $r.ReturnValue")
        proc = subprocess.run(['powershell', '-NoProfile', '-Command', ps], capture_output=True, text=True, timeout=60,
                              creationflags=T.NO_WINDOW)
        if proc.returncode or proc.stdout.strip() != '0':
            raise RuntimeError('activation helper did not start: ' + (proc.stderr or proc.stdout).strip()[:500])

    def build(self, state):
        M.check_state(self, state)
        door = self.session(state['requester'])
        task = door.look(state['task'])
        if (held(task) or task.get('build_run') not in (state.get('previous_run'), None, '')
                or (task.get('builder') and not state.get('previous_run')) or task.get('who','') != state['task_owner']):
            raise RuntimeError('task changed before claim; nothing launched')
        if state.get('manager'):
            claim = M.write_task(self, state, task, dict(builder=state['name'],build='asked',build_run=state['run']))
        else:
            claim = door.call('/do', 'set '+state['task']+' builder='+q(state['name'])+' build=asked build_run='+q(state['run']),
                              saw={state['task']: int(task['rev'])})
        state['claim_records'] = claim.get('records', [])
        self.prepare(state, door)

    def prepare(self, state, door):
        """After the claim: the worktree, the builder's chat, the first turn."""
        task = door.look(state['task'])
        self.phase(state, 'preparing', 'claim recorded; preparing isolated worktree')
        base = self.git(self.repo, 'rev-parse', 'main')
        tree = self.repo / '.worktrees' / state['run']
        branch = 'worker/' + state['run']
        state.update(base=base, tree=str(tree), branch=branch)
        self.save(state)
        self.git(self.repo, 'worktree', 'add', '-b', branch, str(tree), base)
        chat = door.call('/do', 'make kind=chat name='+q(state['name'])+' about='+state['task']+' with='+state['requester'],
                         press=state['run']+'-chat')
        state['chat'] = chat['made'][-1]
        self.run_worker(state, self.prompt(state, task))

    def run_worker(self, state, prompt):
        door = self.session(state['requester'])
        tree = Path(state['tree'])
        folder = self.home / state['run']
        (folder/'prompt.md').write_text(prompt, encoding='utf-8')
        (folder/'token').write_text(door.token, encoding='utf-8')
        mcp = T.mcp_config(self.h.builder_url, folder/'token', folder/'mcp.json')
        events = queue.Queue()
        claude = state.get('provider') == 'claude'
        label = PROVIDERS[state.get('provider', 'codex')]['label']
        if claude:
            cmd = [T.find_claude(), '-p', '--input-format', 'stream-json', '--output-format', 'stream-json', '--verbose',
                   '--model', state['model'], '--effort', state['reasoning'],
                   '--mcp-config', mcp, '--strict-mcp-config', '--setting-sources', '',
                   '--permission-mode', 'acceptEdits', '--allowedTools', ','.join(CLAUDE_TOOLS),
                   '--disallowedTools', ','.join(CLAUDE_DENIED)]
        else:
            cmd = [str(T.PY), str(T.REPO/'research/codex-residents/codex_worker.py'),
                   '--model', state['model'], '--reasoning', state['reasoning'],
                   '--timeout', str(self.limit('worker_timeout') or 0),
                   '--prompt-file', str(folder/'prompt.md'), '--mcp-config', mcp, '--lease', str(folder/'process.lock')]
        if state.get('session'):
            cmd += ['--resume', state['session']]
        self.assert_owned(state)
        env = T.clean_env()
        # 3 Nov: the Codex sandbox may write only inside the worktree, so its temp folder is there too (a top-level
        # dot-folder, which the House never commits). Python 3.12's mkdtemp still makes owner-only folders; tests
        # should make scratch folders with plain mkdir (test_kdesk scratch_dir).
        scratch = tree / '.tmp'
        scratch.mkdir(exist_ok=True)
        env.update(TMP=str(scratch), TEMP=str(scratch), TMPDIR=str(scratch))     # gettempdir reads TMPDIR first
        child = T.Child(cmd, tree, env, events, lambda *_: None, stderr=folder/'stderr.log')
        self.children[state['task']] = child
        state['pid'] = child.proc.pid
        state['effect_tracking'] = True
        self.phase(state, 'preparing', f'adapter started; awaiting authenticated {label} thread', builder_chat=state['chat'])
        if not child.send(prompt):
            state['effects_unknown'] = True
            self.save(state)
            raise RuntimeError('initial send uncertain; no replay')
        ended = False
        said = []                    # this turn's words, the last of which go to the resident in the worker's chat
        try:
            while not ended:
                try:
                    e = events.get(timeout=1)
                except queue.Empty:
                    if self.stopping:
                        raise RuntimeError('House shutting down; preserve work and reconcile before retry')
                    if state.get('halted_by') or state.get('releasing'):
                        raise RuntimeError('stopped')       # house.stop / house.release: guarded says how it ended
                    continue
                kind = e.get('e')
                if kind in ('effect-started', 'effect-finished', 'effect-unknown'):
                    with self.lock:
                        effects = state.setdefault('in_flight_effects', {})
                        if kind in ('effect-started', 'effect-unknown'):
                            effects[e['id']] = e['name']
                            if kind == 'effect-unknown':
                                state['effects_unknown'] = True
                        else:
                            effects.pop(e['id'], None)
                        self.save(state)
                    continue
                if self.stopping and kind != 'text':
                    raise RuntimeError(restart_recovery.SHUTDOWN)
                if kind == 'init':
                    state['session'] = e['session']
                    state['thread_started'] = stamp()
                    self.event(state, 'init', f'authenticated {label} thread started')
                    if claude and state['phase'] != 'working':     # Claude has no separate turn-started event
                        state['turn_started'] = stamp()
                        self.phase(state, 'working', f'authenticated {label} turn running')
                elif kind == 'turn_started':
                    state['turn_started'] = stamp()
                    state['turn_id'] = e.get('turn')
                    self.phase(state, 'working', f'authenticated {label} turn running')
                if kind == 'turn_started' or (claude and kind in ('init', 'tool', 'text')):
                    self.followup_started(state)
                    if state.pop('restart_context', None) is not None:
                        self.save(state)
                if kind == 'tool':
                    activity = T.worker_activity.tool(e)
                    self.event(state, 'act', activity['summary'] if activity else e.get('name', 'tool'),
                               activity['detail'] if activity else None)
                elif kind == 'text':
                    state['last_words'] = e['text']
                    state['interrupted_words'] = e['text']
                    self.event(state, 'said', e['text'])
                    said.append(e['text'])
                elif kind == 'result':
                    state['result_received'] = stamp()
                    state['result_ok'] = bool(e.get('ok'))
                    if not e.get('ok'):
                        raise RuntimeError('worker failed: '+str(e.get('detail')))
                    state['turns']=state.get('turns',0)+1
                    self.report_turn(state, said[-1] if said else self.message("Worker ended without words", state))
                    said = []
                    self.assert_owned(state)
                    with self.lock:
                        pending = self.take_pending(state)
                    if pending:
                        self.event(state, 'heard', 'delivering queued owner follow-up')
                        if not child.send(self.message("Follow-up", state, owner_words='\n'.join(pending))):
                            state['effects_unknown'] = True
                            self.save(state)
                            raise RuntimeError('follow-up send uncertain; no replay')
                        continue
                    self.phase(state, 'received', 'worker ended; result received, not yet independently reviewed',
                               result_received=state['result_received'])
                    ended = True
                elif kind == 'exit':
                    raise RuntimeError('worker exited without successful result: '+str(e.get('code')))
        finally:
            child.stop()
            self.children.pop(state['task'], None)
            if not self.stopping and state['phase']=='received' and state.get('pending'):
                with self.lock:
                    state['phase']='preparing'
                    self.save(state)
                threading.Thread(target=self.guarded,args=(state,self.resume),daemon=True).start()

    # ---- a worker and the resident in charge of it talk in the worker's chat
    def steward(self, person):
        """A leader of the place: Alex and JEFF (Alex, 28 Oct: JEFF must be able to unstick anything)."""
        if not person:
            return False
        for place in self.h.m.see('rows place').get('rows') or []:
            rows = self.h.m.see('look ' + str(place.get('id'))).get('rows') or [{}]
            if rows[0].get('member:' + person) == 'leader':
                return True
        return False

    def may_act(self, state, msg):
        """The one in charge of a worker acts on it; so may any steward, to unstick it."""
        person = (msg.get('caller') or {}).get('person')
        if person == state['requester']:
            return True
        if self.steward(person):
            self.event(state, 'steward', f"{(msg.get('caller') or {}).get('name') or person} acted on it as a steward")
            return True
        return False

    def alex(self, person):
        """Alex's own person, from the existing account mapping (never a name guess)."""
        try:
            accounts = json.loads((self.h.world / 'keep' / 'accounts.json').read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return False
        return bool(person) and accounts.get('desktop:alex') == person

    def may_tell(self, state, task, msg):
        """Alex, 28 Oct (dk1489): ownership is for being woken and for checking in, not a lock on talking. Anyone
        with equal or higher authority over the card may tell its worker: its owner, the card's lead, a steward, Alex.
        Returns how the caller holds that authority, or None."""
        caller = msg.get('caller') or {}
        person, name = caller.get('person'), str(caller.get('name') or '').strip()
        if person and person == state['requester']:
            return 'owner'
        lead = str(task.get('lead') or '').strip()
        if lead and (lead == person or (name and lead.casefold() == name.casefold())):
            return 'lead'
        if self.alex(person):
            return 'Alex'
        if self.steward(person):
            return 'steward'
        return None

    def owner(self, state):
        """The House agent (resident or JEFF) in charge of this worker, or None when Alex asked for it himself."""
        if state.get('manager'):
            return None                  # Rowan's managed builds are woken by manager.notify
        return getattr(self.h, 'agents', {}).get(state['requester'])

    # ---- who picks a stopped worker back up (Alex, 3 Nov: work sat for days, unattended or forgotten)

    def general_manager(self):
        """JEFF: the one who hears about work nobody else can pick up. A house-agent with role=general-manager."""
        agents = getattr(self.h, 'agents', {})
        return next((a for a in agents.values() if (getattr(a, 'cfg', None) or {}).get('role') == 'general-manager'), None) or \
            next((a for a in agents.values() if a.name == 'JEFF'), None)

    @staticmethod
    def usable(agent):
        """Can this agent take a turn now? Asleep, or failing (e.g. its sign-in expired), it cannot."""
        if agent is None:
            return False
        cfg, st = getattr(agent, 'cfg', None) or {}, getattr(agent, 'state', None) or {}
        return cfg.get('want', 'awake') != 'asleep' and not (st.get('error') and not getattr(agent, 'busy', False))

    def route(self, state):
        """Who hears that this worker stopped: its owner; and JEFF, with a note, when nobody can act on it (Alex asked
        for it himself, or its owner is down). Rowan's managed builds go through manager.notify instead."""
        if state.get('manager'):
            return []
        agent = self.owner(state)
        if self.usable(agent):
            return [(agent, '')]
        out = [(agent, '')] if agent is not None else []          # it reads this when it is back
        gm = self.general_manager()
        if gm is not None and gm is not agent:
            if agent is None:
                why = self.message("Requester is not a resident", state, requester=state.get("requester_name") or "Alex")
            else:
                why = self.message("Owner cannot act", state, agent=agent.name,
                                   error=(getattr(agent, "state", None) or {}).get("error") or "asleep")
            out.append((gm, self.message("Nobody can pick this up (JEFF)", state, why=why) + "\n"))
        return out

    def wake_owner(self, state, text, receipt=None):
        routes = self.route(state)
        if receipt and receipt[0] == 'outcome' and state.get('land_caller'):
            caller = getattr(self.h, 'agents', {}).get(state['land_caller'])
            if caller is not None and all(agent is not caller for agent, _ in routes):
                routes.append((caller, ''))
        if not routes:
            raise RuntimeError('no owner is available for this receipt')
        delivery = None
        if receipt:
            kind, key = receipt
            deliveries = state.setdefault('wake_deliveries', {})
            delivery = deliveries.get(kind)
            if not delivery or delivery['key'] != key:
                delivery = deliveries[kind] = dict(key=key, people=[])
        for agent, prefix in routes:
            person = getattr(agent, 'person', None) or agent.name
            if delivery and person in delivery['people']:
                continue
            agent.wake(prefix + text)
            if delivery is not None:
                delivery['people'].append(person)
                self.save(state)
            try:
                self.event(state, 'told', f"woke {agent.name} (busy={getattr(agent, 'busy', '?')}, "
                                          f"inbox={len(getattr(agent, 'inbox', None) or [])})"
                           + (' for its owner' if prefix else ''))
            except Exception:
                pass                        # delivery succeeded even if its diagnostic failed

    def stopped(self, state):
        """It waits on the one in charge from now; they get one reminder if a turn of theirs ends without acting."""
        with self.lock:
            state['awaiting'] = stamp()
            state.pop('reminded', None)
            self.save(state)

    def answered(self, state):
        with self.lock:
            state.pop('awaiting', None)
            state.pop('reminded', None)
            self.save(state)

    def cut_phase(self, state):
        """What a cut-off worker was doing (older runs did not record it: read it off the activity)."""
        if state.get('cut_phase'):
            return state['cut_phase']
        for e in reversed(state.get('activity') or []):
            what = e.get('what')
            if what in ('said', 'act', 'heard', 'working'):
                return 'working'
            if what in ('preparing', 'asked', 'reopened', 'received'):
                return what
            if what in ('reviewing', 'review-again', 'committed'):
                return 'reviewing'
            if what in ('reviewed', 'landing', 'carried'):
                return 'landing'
        return None

    def resumable(self, state):
        """Stopped and safe for a new turn on its worktree: received, blocked or reviewed; or cut off mid-turn
        with its process gone (never mid-review or mid-landing, where main or its branch may be half moved)."""
        if state['task'] in self.children or state.get('handover') or self.landing_busy(state):
            return False
        if state['phase'] in RESUMABLE:
            return True
        return (state['phase'] in CUT and bool(state.get('tree')) and self.cut_phase(state) == 'working'
                and not alive(state.get('pid')))

    def outcome(self, state):
        """A House operation on the worker ended (review, landing, or a failure): the one in charge hears how."""
        if not self.notification_lock.acquire(blocking=False):
            state['outcome_pending'] = True
            self.save(state)
            return
        try:
            bookkeeping.deliver(self, state)
            self._outcome(state)
        finally:
            self.notification_lock.release()

    def _outcome(self, state):
        phase, task, name = state['phase'], state['task'], state['name']
        if self.stopping:
            return                       # the House is going down; wake_cut_off tells them when it is back
        if state.get('land_in_progress'):
            return                       # reviewed/landed are intermediate phases until activation settles
        if phase in ACTIVE or phase in ('received', 'released', QUEUED) or state.get('manager'):
            return                       # received: report_turn already woke them with the worker's words
        if state.pop('quiet', None):
            self.save(state)
            return                       # its owner stopped it themselves: they know
        state['outcome_pending'] = True
        self.save(state)
        if phase == "reviewed":
            text = self.message("It passed its checks", state, commit=str(state.get("candidate", ""))[:9])
        elif phase == "landed":
            text = self.message("It landed", state, commit=str(state.get("landed_commit", ""))[:9],
                                activation=state.get("activation", ""))
        else:
            detail = str(state.get("detail", ""))[:700]
            if state.get('land_attempt'):
                detail = state.get('land_step', 'landing') + ': ' + detail
            text = self.message("It stopped", state, detail=detail)
        checks_text = review_suites.summary(state.get('checks', []))
        if checks_text:
            text += '\n' + checks_text
        if state.get('land_attempt'):
            self.landing_receipt(state)
            text += '\n' + json.dumps(state['land_receipt'])
        said = [phase, str(state.get('detail', ''))[:300], state.get('land_attempt')]
        if state.get('last_outcome') == said:
            state.pop('outcome_pending', None)
            self.event(state, 'quiet', 'same outcome as last time; nobody woken again')
            return                       # the same failure twice wakes nobody twice (the 3 Nov loop)
        self.stopped(state)
        self.wake_owner(state, text, receipt=('outcome', said))
        state['last_outcome'] = said
        state.pop('outcome_pending', None)
        self.save(state)

    def deliver_outcomes(self):
        """Retry undelivered receipts on the House's ordinary tick."""
        self.recovery.deliver()
        self.start_queued()
        self.deliver_start_requests()
        for state in list(self.states.values()):
            if state.get('restart_sync_pending'):
                restart_recovery.sync_card(self, state)
            bookkeeping.deliver(self, state)
            if state.get('land_sync_pending') and not state.get('land_in_progress'):
                self.sync_landing(state)
            try:
                handover.reconcile(self, state)
                handover.deliver(self, state)
            except Exception:
                pass
            self.try_start_outcome(state)
            if state.get('followup_notice'):
                self.followup_started(state)
            if state.get('outcome_pending'):
                try:
                    self.outcome(state)
                except Exception:
                    pass

    def card_done(self, state):
        """Its card is finished (lane Done and the like): nobody needs reminding about the worker any more."""
        try:
            rows = self.h.m.see('look ' + state['task']).get('rows') or []
        except Exception:                                 # noqa: BLE001
            return False
        card = rows[0] if rows else {}
        return any(str(card.get(f, '')).strip().casefold() in FINISHED for f in ('lane', 'status'))

    def waiting_line(self, state):
        since = str(state.get('awaiting') or state.get('updated') or '')[:16].replace('T', ' ')
        return self.message("Waiting worker row", state, since=since, detail=str(state.get("detail", ""))[:200])

    def wake_cut_off(self):
        """Startup and retry use the same durable reconciliation receipts."""
        self.recovery.deliver()

    def remind(self, person):
        """A turn of theirs ended and workers still wait on them: one reminder per stopped result, never more."""
        agent = getattr(self.h, 'agents', {}).get(person)
        if agent is None or agent.busy or agent.inbox:
            return
        waiting = []
        with self.lock:
            for state in self.states.values():
                if (state['requester'] == person and state.get('awaiting') and not state.get('reminded')
                        and state['phase'] in WAITING and state['task'] not in self.children
                        and not state.get('pending') and not state.get('manager') and not self.card_done(state)):
                    state['reminded'] = stamp()
                    self.save(state)
                    waiting.append(state)
        if not waiting:
            return
        agent.wake(self.message("One reminder", list="\n".join(self.waiting_line(s) for s in waiting)))
        for state in waiting:
            self.event(state, 'reminded', f'reminded {agent.name}')

    def hand(self, msg):
        return handover.hand(self, msg)

    def hand_request(self, msg):
        """An accepted slow call always delivers its eventual receipt to its caller."""
        caller = msg.get('caller') or {}
        context = dict(requester=caller.get('person'), requester_name=caller.get('name'),
                       task=(msg.get('args') or {}).get('target') or '', name=msg['word'])
        try:
            out = self.hand(msg)
        except Exception as exc:
            out = {'text': f'handoff unresolved: {exc}; inspect house.who and repeat the same handoff',
                   'external': True}
        if not out.get('caller_receipt'):
            self.request_receipts[msg['use']] = (context, out.get('refused') or out.get('text', ''))
            # The refusal/unresolved answer is ready even if another receipt's
            # recipient is slow. The normal tick retries this queued delivery.
            if self.notification_lock.acquire(blocking=False):
                try:
                    self.deliver_start_requests()
                finally:
                    self.notification_lock.release()
        return out

    def halt(self, msg):
        """house.stop <card>: end a running worker's turn now (Alex, 4 Nov: JEFF could not stop a looping worker).
        It keeps its worktree; house.tell starts it again with new words, house.release drops it."""
        state = self.states.get((msg.get('args') or {}).get('target'))
        caller = msg.get('caller') or {}
        if not state:
            return {'refused': 'this card has no worker'}
        if not (self.may_act(state, msg) or self.alex(caller.get('person'))):
            return {'refused': "only the worker's owner, a steward or Alex may stop it"}
        by = caller.get('name') or caller.get('person') or 'someone'
        with self.lock:
            if state.get('handover'):
                return {'refused': handover.PENDING}
            if not (self.may_act(state, msg) or self.alex(caller.get('person'))):
                return {'refused': 'worker ownership changed; read house.who before acting'}
            child = self.children.get(state['task'])
            if state['phase'] in ('reviewing', 'landing') or self.landing_busy(state):
                return {'refused': 'the House is landing it; a steward can use house.land-cancel'}
            if child is None:
                if state['phase'] in ('asked', 'preparing'):
                    return {'refused': 'it is starting up; stop it in a moment, or house.release drops it now'}
                return {'refused': f'it is not running ({state["phase"]}); house.release {state["task"]} drops it for good'}
            dropped, state['pending'] = state.get('pending') or [], []
            state['halted_by'] = by
            if caller.get('person') == state['requester']:
                state['quiet'] = True
            self.event(state, 'stopping', f'stopped by {by}' + (('; not sent: ' + ' | '.join(dropped))[:500] if dropped else ''))
            self.save(state)
        child.stop()
        return {'text': f'{state["name"]} is stopping; it keeps its worktree. house.tell {state["task"]} <words> starts it '
                        f'again with new words', 'external': True}

    def release(self, msg):
        """house.release <card> [why]: this worker ends for good (stopped first if it is running). Its worktree and
        branch are kept; the card is free for a new worker. Nobody is reminded about it again."""
        args = msg.get('args') or {}
        state = self.states.get(args.get('target'))
        caller = msg.get('caller') or {}
        if not state:
            return {'refused': 'this card has no worker'}
        if not (self.may_act(state, msg) or self.alex(caller.get('person'))):
            return {'refused': "only the worker's owner, a steward or Alex may release it"}
        by = caller.get('name') or caller.get('person') or 'someone'
        why = f'released by {by}' + (f': {str(args.get("words")).strip()[:300]}' if args.get('words') else '')
        with self.lock:
            if state.get('handover'):
                return {'refused': handover.PENDING}
            if not (self.may_act(state, msg) or self.alex(caller.get('person'))):
                return {'refused': 'worker ownership changed; read house.who before acting'}
            if state['phase'] == 'landed':
                return {'refused': 'it already landed; nothing to release'}
            if state['phase'] == 'released':
                return {'text': 'it was already released', 'external': True}
            if state['phase'] in ('reviewing', 'landing') or self.landing_busy(state):
                return {'refused': 'the House is landing it now; release it after, if you still want to'}
            child = self.children.get(state['task'])
            if child is not None:
                state['releasing'] = why
                state['pending'] = []
                self.save(state)
            else:
                self.released(state, why)
        if child is not None:
            child.stop()
        return {'text': f'{state["name"]} is released; its worktree and branch are kept, and the card is free for a new '
                        f'worker (house.build {state["task"]})', 'external': True}

    def report_turn(self, state, words):
        """End of a worker turn: its last words go into its chat (as the worker, so they never count as the owner's
        instruction), and the resident in charge is woken there. Whatever the resident says back in that chat is the
        worker's next instruction (hear)."""
        words = str(words).strip()[:3500]
        chat = state.get('chat')
        if not chat:
            return
        try:
            self.session(state['requester']).call('/do', f'say {chat} text={q(words)}')
        except Exception as exc:                          # noqa: BLE001  the activity record still has it
            self.event(state, 'unsaid', str(exc))
        with self.lock:
            tellers, state['tellers'] = state.get('tellers') or [], []     # others whose words this turn followed
            state['last_words'] = words
            self.save(state)
        self.stopped(state)
        agents = getattr(self.h, 'agents', {})
        for t in tellers:
            other = agents.get(t['person'])
            if other is None:
                self.event(state, 'told', f"{t['name']} told it this turn; not a House agent to wake (reads its chat)")
                continue
            other.wake(self.message("A worker they told something finished", state, words=words))
            self.event(state, 'told', f"woke {t['name']}, who told it this turn ({t['as']})")
        if not self.route(state):
            self.event(state, 'told', 'posted in its chat; no resident to wake (Alex reads it there)')
            return
        self.wake_owner(state, self.message("Their worker finished a turn", state, words=words))

    def owner_turn_ended(self, person):
        """A resident's turn ended: what it said to its workers during that turn starts their next turn now."""
        for state in list(self.states.values()):
            if state['requester'] != person or not state.get('pending'):
                continue
            with self.lock:
                if not self.resumable(state):
                    continue
                if self.full(state.get('provider', 'codex')):
                    if not state.get('queued_turn'):
                        state['queued_turn'] = stamp()      # start_queued gives it the next free slot
                        self.event(state, QUEUED, 'its owner replied while every slot was busy; it starts when one frees')
                        self.save(state)
                    continue
                # 3 Nov, live: an old worker whose card had moved on kept its words; every turn end resumed it, it
                # blocked at once (claim changed), the block woke JEFF, his turn ended... 33 times in an hour.
                # Words for a worker whose card no longer holds it are dropped, never retried.
                try:
                    rows = self.h.m.see('look ' + state['task']).get('rows') or []
                except Exception:                         # noqa: BLE001
                    rows = []
                card = rows[0] if rows else {}
                if not card or card.get('build_run') != state['run'] or held(card) or self.card_done(state):
                    dropped, state['pending'] = state.get('pending') or [], []
                    self.event(state, 'dropped', 'its card no longer holds this worker (claim moved, held or done); '
                               'not sent: ' + ' | '.join(dropped)[:500])
                    continue
                self.reopen(state)
                threading.Thread(target=self.guarded, args=(state, self.resume), daemon=True).start()
        self.remind(person)
        self.idle_check()

    def take_pending(self, state):
        """Hand the queued words to the worker; whoever said them (besides its owner) hears how this turn ends."""
        pending, state['pending'] = state.get('pending', []), []
        if pending:
            state['tellers'], state['told_by'] = state.get('told_by') or [], []
            state['followup_inflight'] = dict(count=len(pending), queued_at=state.pop('followup_queued_at', ''))
        self.save(state)
        return pending

    def followup_started(self, state):
        """An authenticated turn (or Claude's activity) confirms retained words ran."""
        with self.notification_lock:
            receipt = state.pop('followup_inflight', None)
            if receipt:
                state['followup_receipt'] = dict(receipt, started=stamp(), card=state['task'])
                state['followup_notice'] = True
                self.save(state)
            if not state.get('followup_notice'):
                return
            try:
                self.wake_owner(state, self.message("Retained words started", state)
                                + '\n' + json.dumps(state['followup_receipt']),
                                receipt=('followup', state['followup_receipt']))
            except Exception:
                return
            state.pop('followup_notice', None)
            self.save(state)

    def reopen(self, state):
        """A stopped worker (received, blocked, reviewed) takes a new turn in the same worktree. A review's receipts
        are about a result that is about to change, so they move to `earlier_reviews` instead of standing as current."""
        was = state['phase']
        for key in ('land_attempt', 'land_step', 'land_receipt', 'land_caller', 'land_sync_pending',
                    'land_sync_error', 'land_in_progress', 'outcome_pending'):
            state.pop(key, None)
        if was != 'received':
            old = {k: state.pop(k) for k in ('review_base', 'candidate', 'checks', 'self_proof_sha256') if k in state}
            if old:
                state.setdefault('earlier_reviews', []).append(dict(old, phase=was, detail=state.get('detail', ''), at=stamp()))
            self.event(state, 'reopened', f"was {was} ({str(state.get('detail', ''))[:300]}); a new turn on the same worktree")
        if was in CUT:
            state["resume_note"] = {"heading": "When a restart cut it off"}
        state['reopened_from'] = was if was != 'received' else state.get('reopened_from', '')
        state['phase'] = 'preparing'
        state['detail'] = 'retained worker continuation preparing'
        state.pop('restart_pending', None)
        state.pop('cut_phase', None)
        state.pop('cut_from', None)
        state.pop('cut_told', None)
        state.pop('effects_unknown', None)
        state.pop('in_flight_effects', None)
        state.pop('awaiting', None)
        state.pop('reminded', None)
        self.save(state)

    def work(self, msg):
        """house.work <what to do, in plain words> [with=claude|codex]: a card for the caller and a worker on it."""
        caller = msg.get('caller') or {}
        args = msg.get('args') or {}
        kv = dict(args.get('kv') or {})
        words = ' '.join(str(args.get(k) or '') for k in ('target', 'words')).strip()
        if not words:
            return {'refused': 'house.work <what to do, in plain words> [with=claude|codex]'}
        provider = str(kv.get('with') or 'codex').lower()
        if provider not in PROVIDERS:
            return {'refused': 'with=claude or with=codex'}
        try:
            door = self.session(caller.get('person'))
        except RuntimeError:
            return {'refused': 'only Alex, JEFF and the residents have workers'}
        if self.full(provider):
            return {'refused': f'worker capacity is occupied: all {self.capacity_for(provider)} {provider} workers are busy; nothing was started'}
        name = caller.get('name') or ''
        title = short(words.splitlines()[0], 80)
        made = door.call('/do', f'make kind=taskboard-task title={q(title)} text={q(words)} lane=Now '
                                f'who={q(name)} lead={q(name)}')
        card = (made.get('made') or [None])[-1]
        if not card:
            return {'refused': 'the card was not made: ' + str(made.get('text', ''))[:200]}
        out = self.start(dict(msg, args=dict(target=card, kv=dict(kv, **{'with': provider}))))
        if out.get('refused'):
            return {'text': f'made card {card}, but the worker did not start: {out["refused"]}',
                    'external': True}
        return {'text': f"recorded a {PROVIDERS[provider]['label']} worker request on {title} ({card}). You are woken each time "
                        f"it finishes a turn (its words also go in its chat); answer it with house.tell {card} <words>.",
                'external': True, 'rows': out.get('rows', [])}

    def resume(self, state):
        self.assert_owned(state)
        with self.lock:
            pending=self.take_pending(state)
            notes=[state.pop(k) for k in ('boss_note','resume_note') if state.get(k)]
            self.save(state)
        notes = [self.message(note["heading"], state, **note.get("facts", {}))
                 if isinstance(note, dict) else note for note in notes]
        if state.get('restart_context'):
            notes.append(json.dumps(state['restart_context'], ensure_ascii=False))
        prompt=self.message("Follow-up", state, owner_words="\n".join(notes+pending))
        if not state.get('session'):      # stopped before any model thread: the worker has not read its task yet
            prompt=self.prompt(state,self.session(state['requester']).look(state['task']))+'\n'+prompt
        self.run_worker(state, prompt)

    def retry(self, msg):
        """Only a proven pre-thread startup failure; never replay an unknown turn."""
        state=self.states.get(msg.get('args',{}).get('target'))
        if not state or not self.may_act(state, msg):
            return {'refused':'only the requester may retry this startup'}
        with self.lock:
            if self.landing_busy(state):
                return {'refused': 'the House is settling its landing; wait before retrying this worker'}
            if state.get('handover'):
                return {'refused': handover.PENDING}
            if not (self.may_act(state, msg)):
                return {'refused': 'worker ownership changed; read house.who before acting'}
            if state['phase']!='blocked' or state.get('session') or state['task'] in self.children:
                return {'refused':'retry only applies to a terminal startup failure before any Codex thread'}
            if self.full(state.get('provider','codex')):
                return {'refused':'worker capacity is occupied: all '+state.get('provider','codex')+' workers are busy'}
            state['phase']='preparing';self.save(state)
            def launch(s):
                self.assert_owned(s)
                if s.get('claim_records') and not s.get('tree'):     # blocked after the claim, before any worktree
                    return self.prepare(s, self.session(s['requester']))
                if (not s.get('tree') or self.git(s['tree'],'rev-parse','HEAD')!=s['base']
                        or self.git(s['tree'],'status','--porcelain','--untracked-files=no')):
                    raise RuntimeError('startup tree has changes; reconcile before retry')
                task=self.session(s['requester']).look(s['task'])
                self.run_worker(s,self.prompt(s,task))
            threading.Thread(target=self.guarded,args=(state,launch),daemon=True).start()
        return {'text':'pre-thread startup retry recorded; same claim and worktree, no task replay','external':True}

    def tell(self, msg, hold=False):
        state=self.states.get(msg.get('args',{}).get('target'))
        words=str(msg.get('args',{}).get('words') or '').strip()
        if not state:
            return {'refused':'this card has no worker; house.build or house.work starts one'}
        task=self.session(state['requester']).look(state['task'])
        caller=msg.get('caller') or {}
        how=self.may_tell(state, task, msg)
        if not how:
            return {'refused':"only the worker's owner, the card's lead, a steward or Alex may tell this worker"}
        if not words:
            return {'refused':'house.tell <task> <words>: provide a follow-up'}
        if held(task):
            return {'refused':'its card is paused (held); unpause the card, then tell it'}
        if task.get('build_run') != state['run']:
            return {'refused':f'its card has moved on to another worker; house.release {state["task"]} drops this one'}
        with self.lock:
            if self.landing_busy(state):
                return {'refused': 'the House is settling its landing; wait for the result before another turn'}
            if state.get('handover'):
                return {'refused': handover.PENDING}
            if not (self.may_tell(state, task, msg)):
                return {'refused': 'worker ownership changed; read house.who before acting'}
            phase=state['phase']
            if phase in ('landed','released'):
                return {'refused':f'this worker is {phase}; start a new run with house.build {state["task"]}'}
            if phase == QUEUED:
                return {'refused':'it has not started yet (every slot is busy); it starts by itself when one frees'}
            if phase not in ('asked','preparing','working') and phase not in RESUMABLE and not self.resumable(state):
                # reviewing/landing: the House is acting on its result now. Cut off (recovery-needed, uncertain):
                # resumable once its process is gone, and only if it was cut off mid-turn, not mid-review/landing.
                if phase in CUT and self.cut_phase(state) == 'working':
                    return {'refused':f'worker is {phase} and its process may still be running; house.stop '
                                      f'{state["task"]} ends it, then tell it again'}
                if phase in CUT:
                    return {'refused':f'worker was cut off while {self.cut_phase(state) or "busy"}; land it again '
                                      f'(house.land {state["task"]}), or drop it (house.release {state["task"]}) and '
                                      f'start afresh (house.build {state["task"]})'}
                return {'refused':f'worker is {phase}; the House is landing it now, you hear when it ends'}
            if phase in RESUMABLE and state['task'] not in self.children and not state.get('tree'):
                return {'refused':'worker stopped before its worktree was made; house.retry '+state['task']+' starts it'}
            if len(state.setdefault('pending',[])) >= 10:
                return {'refused':'ten follow-ups already pending; no more were queued'}
            cap=self.limit('max_turns')
            if cap and state.get('turns',0) >= cap:
                return {'refused':f'this worker has had {cap} turns (House settings max_turns); land it, or start a new card'}
            if how!='owner':  # the worker knows who said it; the owner stays in charge and is still woken
                name=caller.get('name') or caller.get('person') or 'someone'
                words=self.message("Follow-up from another person",state,name=name,role=how,
                                   owner=state.get("requester_name") or "your owner",words=words)
                added=not any(t['person']==caller.get('person') for t in state.setdefault('told_by',[]))
                if added:
                    state['told_by'].append(dict(person=caller.get('person'),name=name,**{'as':how}))
            if hold:          # said during the resident's own turn: starts the worker when that turn ends
                state.setdefault('followup_queued_at', stamp())
                state['pending'].append(words[:8000])
                self.event(state,'heard',words)
                return {'text':'follow-up retained until your turn ends and a worker slot is free; '
                               'you hear when its turn starts','external':True}
            resume=self.resumable(state)
            # Explicit owner correction replaces the task basis, never its authority.
            state['basis']={k:task.get(k,'') for k in ('title','text','acceptance','who')}
            state['pending'].append(words[:8000])
            state.setdefault('followup_queued_at', stamp())
            self.event(state,'heard',words)
            if resume and self.full(state.get('provider','codex')):
                state['queued_turn']=stamp()        # every slot busy: it starts with these words when one frees
                self.event(state,QUEUED,'told while every slot was busy; it starts when one frees')
                self.save(state)
                return {'text':f'every {state.get("provider","codex")} slot is busy; it starts with your words by itself '
                               f'as soon as one frees; you hear when its turn starts','external':True}
            if how!='owner':
                self.event(state,how,f"{caller.get('name') or caller.get('person')} told it as {how}, not its owner")
            if resume:
                self.reopen(state)
                threading.Thread(target=self.guarded,args=(state,self.resume),daemon=True).start()
        told='' if how=='owner' else '; its owner is woken when it ends that turn, and so are you'
        if resume and phase!='received':
            return {'text':f'worker was {phase}; it resumes with your words in a new turn on the same worktree{told}',
                    'external':True}
        return {'text':f'follow-up retained for this builder; it will be read at the next turn boundary; '
                       f'you hear when that turn starts{told}','external':True}

    def hear(self, msg):
        if msg.get('word')!='say' or not msg.get('said'):
            return
        by=msg.get('by_id')
        rows_by_person={}
        for state in list(self.states.values()):
            if not state.get('chat') or (by and by!=state['requester']):
                continue
            # 28 Oct: a worker's chat is closed to the House itself, so Sable's answers there were never read. Read the
            # line as the person in charge (its worker session sees its own chats).
            person=state['requester']
            if person not in rows_by_person:
                try:
                    rows_by_person[person]=self.session(person).call('/see','look '+msg['said']).get('rows') or []
                except Exception:                          # noqa: BLE001  not theirs to see: not theirs to answer
                    rows_by_person[person]=[]
            rows=rows_by_person[person]
            if not rows:continue
            row=rows[0]
            # Only the actual requesting person in their private worker chat.
            # Agent-authored output cannot recursively wake itself.
            if row.get('chat')==state.get('chat') and row.get('made_by')==state['requester']:
                seen=state.setdefault('heard',[])
                if msg['said'] in seen:return
                seen.append(msg['said']);self.save(state)
                agent=self.owner(state)
                out=self.tell(dict(args=dict(target=state['task'],words=row.get('text','')),
                                   caller=dict(person=state['requester'])),
                              hold=bool(agent is not None and agent.busy))
                if out.get('refused'):self.event(state,'held',out['refused'])

    def message(self, heading, state=None, **facts):
        state = state or {}
        context = dict(state, card=state.get("task", ""), owner=state.get("requester_name") or state.get("requester", ""))
        context.update(facts)
        return message(self.h.m.see, heading, **context)

    def prompt(self, state, task):
        return self.message("Worker brief", state, text=task.get("text", ""),
                            acceptance=task.get("acceptance", ""))

    def assert_owned(self, state):
        self.land_check()
        M.check_state(self, state)
        task = self.session(state['requester']).look(state['task'])
        # Alex, 4 Nov: nothing sits blocked. A worker whose card moved on or finished is released, quietly; a card
        # that changed goes to the worker as its new instructions. Only a card someone paused (held) stops it.
        if task.get('build_run') != state['run']:
            raise Released('its card moved on to another worker; its worktree is kept')
        if state['phase'] != 'landing' and any(str(task.get(f, '')).strip().casefold() in FINISHED
                                               for f in ('lane', 'status')):
            raise Released('its card is finished; its worktree is kept')
        if held(task):
            raise RuntimeError('its card is paused (held); it carries on when the card is unpaused')
        if state.get('basis') and any(task.get(k,'') != v for k,v in state['basis'].items()):
            state['basis'] = {k: task.get(k, '') for k in ('title', 'text', 'acceptance', 'who')}
            state["resume_note"] = {"heading": "When its card changed", "facts": {
                "text": str(task.get("text", ""))[:3000], "acceptance": task.get("acceptance", "")}}
            self.event(state, 'card-changed', 'its card changed; the new version goes to the worker at its next turn')
            self.save(state)

    def request_review(self, msg):
        state = self.states.get(msg.get('args', {}).get('target'))
        if not state or not self.may_act(state, msg):
            return {'refused': 'only the requester may review this build'}
        with self.lock:
            if self.landing_busy(state):
                return {'refused': 'the House is settling its landing; wait for the result before another review'}
            if state.get('handover'):
                return {'refused': handover.PENDING}
            if not (self.may_act(state, msg)):
                return {'refused': 'worker ownership changed; read house.who before acting'}
            # Review again: after main moved past a reviewed result, or after a review whose checks failed (the run
            # stays blocked with its review receipts). Never an active, uncertain or pre-review failure.
            again = state['phase'] == 'reviewed' or (state['phase'] == 'blocked' and state.get('review_base'))
            if state.get('pending') and state['phase'] == 'received' and state['task'] not in self.children:
                # the requester chose review over what it last said to the worker in the same turn
                self.event(state, 'dropped', 'review asked; not sent to the worker: ' + ' | '.join(state['pending'])[:500])
                state['pending'] = []
            if (state['phase'] != 'received' and not again) or state['task'] in self.children or state.get('pending'):
                return {'refused': 'review requires a received, reviewed or review-failed result, not an active or uncertain worker'}
            if again:
                self.event(state, 'review-again', 'independent checks requested again on the current main')
            state['phase'] = 'reviewing'
            state.pop('awaiting', None)
            state.pop('reminded', None)
            self.save(state)
            threading.Thread(target=self.guarded, args=(state, self.review), daemon=True).start()
        return {'text': 'independent checks requested; source is not landed', 'external': True}

    def commit_worker(self, state, tree):
        """The worker's sandbox cannot write .git (index.lock is denied), as on the old desk (workshop CODEX_LIMITS,
        1 Oct). So the House commits what it left, to the worker's own branch only, before the independent checks.
        Left out: BUILD-RESULT.md (its self-proof, kept untracked) and dot-folders at the top (scratch, temp fixtures)."""
        self.git(tree, 'add', '-A', '--', '.', ':(exclude)BUILD-RESULT.md', ':(exclude,glob).*', ':(exclude,glob).*/**')
        files = self.git(tree, 'diff', '--cached', '--name-only').splitlines()
        if not files:
            return
        self.git(tree, 'commit', '-q', '-m', state['name'] + '\n\nCommitted by the House for builder run ' + state['run']
                 + ' (the worker sandbox cannot write .git).')
        state['house_commit'] = dict(commit=self.git(tree, 'rev-parse', 'HEAD'), files=files)
        self.event(state, 'committed', f"House committed {len(files)} file(s) the worker left: " + ', '.join(files[:12]))

    def review(self, state):
        self.assert_owned(state)
        tree = Path(state['tree'])
        report = tree/'BUILD-RESULT.md'
        if not report.is_file():     # 4 Nov: a missing note never stops a landing; its last words stand in for it
            report.write_text('# Build result\n\n(The worker left no BUILD-RESULT.md. Its last words:)\n\n'
                              + str(state.get('last_words') or '(none kept)') + '\n', encoding='utf-8')
            self.event(state, 'self-proof', 'no BUILD-RESULT.md; the House wrote one from its last words')
        # Never erase or stash worker edits: commit them to its branch, then check that exact commit.
        if getattr(self.land_context, 'control', None):
            self.landing_step(state, 'commit')
        self.commit_worker(state, tree)
        if self.git(tree, 'status', '--porcelain', '--untracked-files=no'):
            raise RuntimeError('worker has uncommitted tracked changes; source review held')
        state['self_proof_sha256'] = hashlib.sha256(report.read_bytes()).hexdigest()
        base = self.git(self.repo, 'rev-parse', 'main')
        # Recorded before the merge, so a review that stops here may be asked for again (28 Oct: Pike's review hit a
        # kdesk.py conflict with the Rowan work and could not be reviewed again).
        state['review_base'] = base
        self.save(state)
        if base != state['base']:
            if state.get('land_attempt'):
                if getattr(self.land_context, 'control', None):
                    self.landing_step(state, 'merge')
                else:
                    state['land_step'] = 'merge'
            try:
                self.git(tree, 'merge', '--no-edit', base)
            except RuntimeError:
                # Never leave conflict markers for the next review's commit to pick up.
                conflicted = self.git(tree, 'diff', '--name-only', '--diff-filter=U').split()
                if not conflicted:
                    raise                       # e.g. index.lock: preserve the actual refusal
                self.git(tree, 'merge', '--abort')
                raise RuntimeError('main conflicts with this worker in ' + ', '.join(conflicted or ['some files'])
                                   + '; merge main into the worker branch by hand, then review again') from None
        candidate = self.git(tree, 'rev-parse', 'HEAD')
        if state.get('land_attempt'):
            if getattr(self.land_context, 'control', None):
                self.landing_step(state, 'checks')
            else:
                state['land_step'] = 'checks'
        state.update(review_base=base, candidate=candidate, checks=[])
        self.phase(state, 'reviewing', 'independent kernel and hidden desktop checks on '+candidate[:12])
        folder = self.home/state['run']/('review-' + uuid.uuid4().hex)
        folder.mkdir()
        suites = self.review_plan(state)
        state['review_suites'] = review_suites.fingerprint(suites)
        self.save(state)
        failures = []
        for i, suite in enumerate(suites):
            path = folder/f'check-{i}.txt'
            command = review_suites.command(suite, T.PY)
            receipt = dict(name=suite['name'], runner=suite['runner'], tests=suite['paths'],
                           command=command, candidate=candidate, status='running', returncode=None,
                           evidence=str(path), artifacts=str(folder / f'check-{i}-artifacts'))
            state['checks'].append(receipt)
            self.save(state)
            with path.open('w', encoding='utf-8') as out:
                try:
                    if suite['desktop']:
                        import gaming_gate
                        gaming_gate.assert_clear()
                    env = T.clean_env('off')
                    env['AGORA_TMP'] = str(tree / '.tmp' / 'house-review' / state['run'] / str(i))
                    env['AGORA_REVIEW_EVIDENCE'] = receipt['artifacts']
                    control = getattr(self.land_context, 'control', None)
                    run = control.run if control else subprocess.run
                    proc = run(command, cwd=tree, env=env, stdout=out, stderr=subprocess.STDOUT,
                               timeout=suite['timeout'], creationflags=T.NO_WINDOW)
                    receipt.update(returncode=proc.returncode, status='passed' if proc.returncode == 0 else 'failed')
                except Exception as exc:
                    receipt.update(status='blocked' if isinstance(exc, RuntimeError) else 'failed',
                                   error=f'{type(exc).__name__}: {exc}')
                    out.write('\n' + receipt['error'] + '\n')
            receipt['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            self.save(state)
            self.land_check()
            if receipt['status'] != 'passed':
                failures.append(f"{suite['name']}; see {path}")
        if failures:
            raise RuntimeError('independent check failed: ' + ' | '.join(failures))
        if review_suites.fingerprint(self.review_plan(state)) != state['review_suites']:
            raise RuntimeError('card suites changed during review; check again')
        if self.git(tree, 'rev-parse', 'HEAD') != candidate or self.git(tree, 'status', '--porcelain', '--untracked-files=no'):
            raise RuntimeError('candidate changed during review; evidence not reusable')
        self.phase(state, 'reviewed', 'independent checks passed; awaiting source publication and activation',
                   reviewed_commit=candidate)

    def review_plan(self, state):
        card = self.session(state['requester']).look(state['task'])
        return review_suites.plan(card, state['tree'], CHECKS)

    def suites_current(self, state):
        current = self.review_plan(state)
        # Old reviews of cards without suites retain the existing baseline contract.
        if not state.get('review_suites'):
            return len(current) == len(CHECKS)
        return state['review_suites'] == review_suites.fingerprint(current)

    def landing_receipt(self, state):
        state.setdefault('land_step', 'started')
        state['land_receipt'] = dict(attempt=state['land_attempt'], step=state['land_step'],
                                    phase=state['phase'], reason=state.get('detail', ''),
                                    checks=state.get('checks', []), activation=state.get('activation', ''),
                                    landed_commit=state.get('landed_commit', ''),
                                    next=(f'house.snap <thing>; verify {state["task"]}' if state['phase'] == 'landed'
                                          else f'house.tell {state["task"]} <repair the reported step>; '
                                               f'house.land {state["task"]}'))
        state.setdefault('land_attempts', {})[state['land_attempt']] = state['land_receipt']
        return state['land_receipt']

    def sync_landing(self, state, strict=False):
        """Publish House-owned facts; retain any refused module write locally."""
        try:
            self.update(state, land_attempt=state['land_attempt'], land_step=state['land_step'],
                        land_receipt=json.dumps(self.landing_receipt(state)),
                        build='blocked' if state['phase'] == 'blocked' else
                              'landed' if state['phase'] == 'landed' else 'landing',
                        outcome='failed' if state['phase'] == 'blocked' else 'unverified',
                        build_phase=state['phase'], build_detail=state.get('detail', '')[:1500])
            state.pop('land_sync_pending', None)
            state.pop('land_sync_error', None)
        except Exception as exc:
            state['land_sync_pending'] = True
            state['land_sync_error'] = f'{type(exc).__name__}: {exc}'
            if strict:
                raise
        finally:
            self.save(state)

    def landing_step(self, state, step):
        self.land_check()
        state['land_step'] = step
        self.landing_receipt(state)
        self.event(state, step, f"landing {state['land_attempt']}: {step}")
        self.sync_landing(state, strict=True)

    def settle_landing(self, state, exc):
        state.update(phase='blocked', detail=f'{type(exc).__name__}: {exc}'[:2000], updated=stamp(),
                     outcome_pending=True, land_sync_pending=True)
        self.landing_receipt(state)
        self.event(state, 'blocked', state['detail'])

    def run_landing(self, state):
        """The whole asynchronous boundary, including setup and BaseException, has a durable result."""
        control = self.land_controls[state['task']]
        try:
            control.policy = landing_control.policy(self.settings())
            control.deadline = control.started + control.policy['landing_timeout']
            def track_child(proc):
                if proc is None:
                    state.pop('land_child_pid', None)
                else:
                    state['land_child_pid'] = proc.pid
                self.save(state)
            control.on_child = track_child
            self.land_context.control = control
            blocker = self.landing_blocker()
            if blocker:
                raise RuntimeError(blocker)
            self.sync_landing(state, strict=True)
            self.land_all(state)
            self.land_check()
        except BaseException as exc:
            self.settle_landing(state, exc)
        finally:
            self.land_context.control = None
            self.landing_receipt(state)
            state['outcome_pending'] = True
            state['land_in_progress'] = False
            self.save(state)                   # notification/card failures cannot erase the result
            self.sync_landing(state)
            try:
                M.notify(self, state)
            except Exception as exc:
                self.event(state, 'unsaid', f'manager wake: {exc!r}')
            try:
                self.outcome(state)
            except Exception as exc:
                self.event(state, 'unsaid', f'landing outcome wake: {exc!r}')
            if control.unstopped is not None and control.unstopped.poll() is None:
                state['land_child_pid'] = control.unstopped.pid
                self.save(state)
                def clear_after_exit():
                    control.unstopped.wait()
                    with self.lock:
                        state.pop('land_child_pid', None)
                        self.land_controls.pop(state['task'], None)
                        self.save(state)
                threading.Thread(target=clear_after_exit, daemon=True).start()
            else:
                self.land_controls.pop(state['task'], None)
            try:
                self.start_queued()
                self.idle_check()
            except Exception as exc:
                self.event(state, 'unsaid', f'queue or restart check: {exc!r}')

    def cancel_landing(self, msg):
        caller = (msg.get('caller') or {}).get('person')
        if not caller or not (self.steward(caller) or self.alex(caller)):
            return {'refused': 'house.land-cancel is for stewards'}
        task = (msg.get('args') or {}).get('target')
        state, control = self.states.get(task), self.land_controls.get(task)
        if not state or not control:
            return {'refused': 'no active landing for this card'}
        control.cancel('landing cancelled by ' + str((msg.get('caller') or {}).get('name') or caller))
        # The owning thread stops its child before releasing any publication lock.
        # Do not label cancellation complete until that unwind has finished.
        return {'text': 'landing cancellation requested; its stopped result will wake the owner',
                'external': True, 'rows': [dict(self.landing_receipt(state), cancellation='requested')]}

    def land(self, msg):
        """house.land <card>: one step (Alex, 4 Nov). The House runs the checks, lands the worker's work on main and
        switches it on; the owner hears once, when it is live or what stopped it. One landing at a time: the next
        waits its turn instead of being refused."""
        state = self.states.get(msg.get('args', {}).get('target'))
        if not state:
            return {'refused': 'this card has no worker; house.build or house.work starts one'}
        if not self.may_act(state, msg):
            return {'refused': "only the worker's owner, a steward or Alex may land it"}
        with self.lock:
            if state.get('handover'):
                return {'refused': handover.PENDING}
            if not (self.may_act(state, msg)):
                return {'refused': 'worker ownership changed; read house.who before acting'}
            phase = state['phase']
            if state['task'] in self.children or phase in ('asked', 'preparing', 'working'):
                return {'refused': f'it is still working; house.land {state["task"]} once its turn ends '
                                   f'(or house.stop {state["task"]} first)'}
            if state['task'] in self.land_controls:
                return {'text': 'it is already landing; you hear when it is live', 'external': True,
                        'rows': [self.landing_receipt(state)]}
            if phase in ('reviewing', 'landing'):
                return {'refused': 'an earlier review or landing is unresolved; reconcile it before retrying'}
            if phase in ('landed', 'released', QUEUED):
                return {'refused': f'it is {phase}; nothing to land'}
            if state.get('pending'):
                return {'refused': "you told it something it hasn't read yet; let that turn run, then land it"}
            if not state.get('tree'):
                return {'refused': 'it stopped before it had a worktree; nothing to land'}
            if self.landing_blocker():
                return {'refused': self.landing_blocker()}
            if phase in CUT and (self.cut_phase(state) not in ('working', 'reviewing') or alive(state.get('pid'))):
                return {'refused': f'it was cut off while {self.cut_phase(state) or "busy"}; house.release it and '
                                   f'start afresh with house.build {state["task"]}'}
            state['land_from'] = phase
            state['land_attempt'] = uuid.uuid4().hex
            state['land_step'] = 'started'
            state['land_started'] = stamp()
            state['land_in_progress'] = True
            state['land_caller'] = (msg.get('caller') or {}).get('person')
            state.pop('outcome_pending', None)
            state['checks'] = [] if phase != 'reviewed' else state.get('checks', [])
            state['detail'] = 'landing started'
            state.pop('quiet', None)
            state.pop('activation', None)
            state['phase'] = 'reviewing'
            state.pop('awaiting', None)
            state.pop('reminded', None)
            self.landing_receipt(state)
            self.event(state, 'started', 'landing ' + state['land_attempt'] + ' started')
            try:
                self.sync_landing(state, strict=True)
                self.land_controls[state['task']] = landing_control.Control({})
                threading.Thread(target=self.run_landing, args=(state,), daemon=True).start()
            except BaseException as exc:
                self.land_controls.pop(state['task'], None)
                state['land_in_progress'] = False
                self.settle_landing(state, exc)
                self.sync_landing(state)
        return {'text': 'landing: the House runs the checks, lands it on main and switches it on; you hear once, '
                        'when it is live or what stopped it', 'external': True,
                'rows': [dict(state['land_receipt'])]}

    def land_all(self, state):
        reviewed = state.pop('land_from', '') == 'reviewed'
        control = getattr(self.land_context, 'control', None)
        queue_guard = control.acquire(self.landing_queue_lock, 'landing queue') if control else self.landing_queue_lock
        if control:
            self.landing_step(state, 'waiting')
        with queue_guard:
            for attempt in range(2):            # main may move between checks and landing (someone else landed)
                main = self.git(self.repo, 'rev-parse', 'main')
                if not (reviewed and state.get('candidate') and state.get('review_base') == main
                        and self.suites_current(state)):
                    if control:
                        self.landing_step(state, 'checks')
                    else:
                        state['land_step'] = 'checks'
                    self.review(state)
                if control:
                    self.landing_step(state, 'publication')
                else:
                    state['land_step'] = 'publication'
                state['phase'] = 'landing'
                self.save(state)
                try:
                    guard = control.acquire(self.landing_lock, 'publication') if control else self.landing_lock
                    with guard:
                        self.land_check()
                        self.publish(state)
                    break
                except RuntimeError as exc:
                    if 'main advanced' not in str(exc) or attempt:
                        raise
                    reviewed = False
        if control:
            self.landing_step(state, 'activation')
        else:
            state['land_step'] = 'activation'
        self.activate(state)

    def activate(self, state):
        """Switch the landed change on: restart what it made stale (kd_reload, detached). A change to the House itself
        restarts the House as soon as no git step is under way; who it cuts off resumes (idle_check)."""
        reload = T.REPO / 'research' / 'window-lab' / 'kernel-desktop' / 'kd_reload.py'
        self.land_check()
        try:
            control = getattr(self.land_context, 'control', None)
            if control:
                with tempfile.TemporaryFile() as out:
                    result = control.run([str(T.PY), str(reload), '--dry'], stdout=out, stderr=subprocess.STDOUT,
                                         timeout=120, creationflags=T.NO_WINDOW)
                    out.seek(0)
                    result.stdout = out.read().decode('utf-8', 'replace')
                    result.stderr = ''
            else:
                result = subprocess.run([str(T.PY), str(reload), '--dry'], capture_output=True, text=True, timeout=120,
                                        creationflags=T.NO_WINDOW)
            if getattr(result, 'returncode', 0):
                raise RuntimeError('activation inspection failed: ' + (result.stderr or result.stdout)[:500])
            dry = result.stdout
        except Exception as exc:                       # noqa: BLE001  landed is landed; say what didn't switch on
            state['activation'] = f'not switched on ({exc}); ask JEFF to house.restart what it needs'
            self.event(state, 'activation', state['activation'])
            self.save(state)
            if control:
                raise
            return
        lines = [x.strip() for x in dry.splitlines() if x.strip()]
        if not lines:
            state['activation'] = 'activation inspection returned no result; ask JEFF to check before restarting'
            if control:
                raise RuntimeError(state['activation'])
        elif any('nothing is stale' in x for x in lines):
            state['activation'] = 'nothing needed restarting; it is live'
        else:
            house = any(x.startswith('house:') for x in lines)
            others = [x for x in lines if not x.startswith('house:')]
            if others:
                try:
                    self.land_check()
                    self.spawn_reload(['--skip', 'house'] if house else [], self.home / state['run'] / 'activation.log')
                except Exception as exc:
                    state['activation'] = f'not switched on ({exc}); ask JEFF to house.restart what it needs'
                    self.event(state, 'activation', state['activation'])
                    if control:
                        raise
                    return
            if house:
                self.house_restart_due = True
            state['activation'] = ('switching on: ' + '; '.join(x.split(' (')[0].split(':')[0] for x in lines)
                                   + ('. The House restarts by itself once no git step is under way; anyone mid-turn carries on after' if house else ''))
        self.event(state, 'activation', state['activation'])
        self.save(state)

    def publish(self, state):
        self.assert_owned(state)
        if not self.suites_current(state):
            raise RuntimeError('card suites changed after review; review again before publication')
        if self.git(self.repo, 'branch', '--show-current') != 'main':
            raise RuntimeError('canonical checkout is not on main')
        if self.git(self.repo, 'rev-parse', 'HEAD') != state['review_base']:
            raise RuntimeError('main advanced after review; preserve result and reconcile before publication')
        if self.git(state['tree'], 'rev-parse', 'HEAD') != state['candidate']:
            raise RuntimeError('candidate changed after review')
        changed = self.git(state['tree'], 'diff', '--name-only', state['review_base'], state['candidate']).splitlines()
        dirty = self.git(self.repo, 'diff', 'HEAD', '--name-only').splitlines()
        overlap = sorted(set(changed) & set(dirty))
        late = []
        if not overlap:
            self.git(self.repo, 'merge', '--ff-only', state['candidate'])
        else:
            late = self.carry_over(state, changed, overlap)
        state['landed_commit'] = self.git(self.repo, 'rev-parse', 'HEAD')
        # Main has moved either way, so the run is landed; edits that could not be carried are named, not hidden.
        self.phase(state, 'landed', 'source landed; activation and owner outcome verification remain'
                   + ('; uncommitted edits NOT carried: ' + '; '.join(late) if late else ''),
                   landed_commit=state['landed_commit'], outcome='unverified')

    def carry_over(self, state, changed, overlap):
        """Land while someone else's uncommitted edits sit in files the candidate also changes (Alex, 28 Oct: land
        just the builder's code while another session reworks its own). Each such file gets a three-way merge
        (main, the edited file, the candidate); any conflict refuses before anything moves. Then main moves to the
        candidate and the edited files keep their edits on top, still uncommitted. Copies go to the run folder."""
        base, cand = state['review_base'], state['candidate']
        folder = self.home/state['run']/'carried'
        merged = {}
        for f in overlap:
            path = self.repo/f
            if not path.is_file() or not self.git(self.repo, 'ls-tree', '--name-only', cand, '--', f):
                raise RuntimeError(f'canonical uncommitted edits overlap candidate on {f} (added or deleted); reconcile by hand')
            mine = path.read_bytes()
            text = self.merge_file(mine, self.show(base, f), self.show(cand, f))
            if text is None:
                raise RuntimeError(f'canonical uncommitted edits conflict with candidate in {f}; preserve both and reconcile')
            (folder/f).parent.mkdir(parents=True, exist_ok=True)
            (folder/f).write_bytes(mine)
            merged[f] = (mine, text)
        self.git(self.repo, 'update-ref', '-m', 'House landing '+state['run'], 'refs/heads/main', cand, base)
        self.git(self.repo, 'reset', '-q', cand, '--', *changed)
        clean = [f for f in changed if f not in merged]
        for f in clean:
            if self.git(self.repo, 'ls-tree', '--name-only', cand, '--', f):
                self.git(self.repo, 'checkout', '-q', '--', f)
            elif (self.repo/f).exists():
                (self.repo/f).unlink()
        late = []
        for f, (mine, text) in merged.items():
            path = self.repo/f
            for attempt in range(6):
                # 28 Oct: one write failed with [Errno 22] (the file was busy for a moment); main had already moved,
                # so the run blocked with the edits sitting on the old code. Read, merge and write again, briefly.
                try:
                    now = path.read_bytes()
                    if now != mine:          # edited again while landing: merge the newest edits instead
                        text = self.merge_file(now, self.show(base, f), self.show(cand, f))
                        if text is None:
                            late.append(f'{f} (edited during landing; conflicts)')
                            break
                    path.write_bytes(text)
                    break
                except OSError as exc:
                    if attempt == 5:
                        late.append(f'{f} ({exc})')
                    else:
                        time.sleep(0.5)
        self.event(state, 'carried', 'kept uncommitted edits on top of the landed code in ' + ', '.join(overlap)
                   + (f'; NOT carried, reconcile from the copy: {"; ".join(late)}' if late else '')
                   + f'; copies in {folder}')
        return late

    def show(self, rev, f):
        control = getattr(self.land_context, 'control', None)
        if control:
            with self.git_guard(), tempfile.TemporaryFile() as out:
                result = control.run(['git', '-C', str(self.repo), 'cat-file', '--filters', f'{rev}:{f}'],
                                     stdout=out, stderr=subprocess.STDOUT, timeout=60, creationflags=T.NO_WINDOW)
                if result.returncode:
                    raise RuntimeError('git cat-file failed during landing')
                out.seek(0)
                return out.read()
        with self.git_lock:
            return subprocess.run(['git', '-C', str(self.repo), 'cat-file', '--filters', f'{rev}:{f}'], capture_output=True, check=True,
                                  stdin=subprocess.DEVNULL, timeout=60, creationflags=T.NO_WINDOW).stdout

    def merge_file(self, mine, base, theirs):
        """git merge-file on three byte strings; the merged bytes, or None on any conflict."""
        with tempfile.TemporaryDirectory() as d:
            paths = []
            for name, data in (('mine', mine), ('base', base), ('theirs', theirs)):
                p = Path(d)/name
                p.write_bytes(data)
                paths.append(str(p))
            control = getattr(self.land_context, 'control', None)
            if control:
                proc = control.run(['git', 'merge-file', *paths], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   timeout=60, creationflags=T.NO_WINDOW)
            else:
                proc = subprocess.run(['git', 'merge-file', *paths], capture_output=True, stdin=subprocess.DEVNULL,
                                      timeout=60, creationflags=T.NO_WINDOW)
            return Path(paths[0]).read_bytes() if proc.returncode == 0 else None

    def row(self, state):
        phase = state['phase']
        return dict(id=state['task'], person=state['task'], name=state['name'], role='builder',
                    task=state['task'], build_run=state['run'], chat=state.get('chat', ''), doing=phase, now=state.get('detail', ''),
                    colour='sage' if phase=='working' else 'rose' if phase in ('blocked','recovery-needed') else 'sky',
                    provider=state.get('provider', 'codex'), model=state['model'], reasoning=state['reasoning'],
                    turns=state.get('turns',0), last_turn=state.get('updated',''),
                    awaiting=state.get('awaiting',''), owner=state.get('requester',''),
                    owner_name=state.get('requester_name',''),
                    handoff_status='unresolved' if state.get('handover') else '',
                    handoff_to=(state.get('handover') or {}).get('name', ''),
                    land_attempt=state.get('land_attempt', ''), land_step=state.get('land_step', ''),
                    land_receipt=state.get('land_receipt', {}), land_sync_error=state.get('land_sync_error', ''),
                    bookkeeping_notices=[{k: n[k] for k in
                        ('key', 'reason', 'lead', 'delivered', 'lead_error', 'chat_error') if k in n}
                        for n in state.get('bookkeeping_failures', {}).values()],
                    land_child_pid=state.get('land_child_pid'),
                    first_words_ms=None, error=state.get('detail','') if phase=='blocked' else '',
                    acts=[], acts_text='', waiting=0, session=state.get('session',''))

    def rows(self, msg=None):
        with self.lock:
            states=[dict(s) for s in self.states.values()]
        if msg is not None and states:
            # Keep the caller's card visibility without a kernel round trip per worker.
            visible = {r['id'] for kind in ('taskboard-task', 'task')
                       for r in self.h.m.see('rows '+kind, use=msg.get('use')).get('rows') or []}
            states = [s for s in states if s['task'] in visible]
        return [self.row(s) for s in states]

    def log(self, task):
        state = self.states[task]
        lines = [f"{e['what']}\t{e['at'][11:16]}\t{state['name']}\t{e['text']}" for e in state['activity']]
        rendered = [
            f"act-detail\t{e['at'][11:16]}\t{state['name']}\t" +
            json.dumps(dict(summary=e['text'], detail=e['detail']), ensure_ascii=False)
            if e.get('detail') else line
            for e, line in zip(state['activity'], lines)]
        if any(e['what'] == 'act' and not e.get('detail') for e in state['activity']):
            note = 'info\t\t\tOlder or unsupported activity has no saved command or paths; shown as recorded.'
            lines.append(note)
            rendered.append(note)
        return {'text':'\n'.join(lines), 'rows':[dict(person=task, name=state['name'], log='\n'.join(rendered), lines=len(lines))]}

    def off(self):
        with self.lock:
            self.stopping = True
            for state in self.states.values():
                if state['phase'] in ACTIVE:
                    restart_recovery.park(self, state, restart_recovery.SHUTDOWN)
                    state['restart_sync_pending'] = True
                    self.save(state)
        # Persist all interruptions before any potentially slow stop or write.
        for state in list(self.states.values()):
            if state.get('restart_sync_pending'):
                restart_recovery.sync_card(self, state)
        for child in list(self.children.values()):
            child.stop()
