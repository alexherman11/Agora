"""Kernel House builders. No Frontier queue and no credentials or grants minted here.

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

ACTIVE = {'asked', 'preparing', 'working', 'reviewing', 'landing'}
RESUMABLE = {'received', 'blocked', 'reviewed'}   # stopped, not landed or released: house.tell gives it a new turn
CUT = {'recovery-needed', 'uncertain'}             # cut off (House restart, lost answer): resumable once its process is gone
WAITING = RESUMABLE | CUT                          # stopped and waiting on the one in charge of it
FINISHED = {'done', 'verified', 'finished', 'completed', 'released', 'cancelled', 'trashed'}   # a card's lane or status


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
    ['research/kernel-lab/tests/test_chat.py', 'research/kernel-lab/tests/test_paint_health.py'],
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
            raise RuntimeError(out.get('text') or out.get('error') or 'door refused')
        return out

    def look(self, target):
        rows = self.call('/see', 'look ' + target).get('rows') or []
        if len(rows) != 1:
            raise RuntimeError('task is missing or not visible')
        return rows[0]


PROVIDERS = {  # Alex, 28 Oct: up to four Claude and four Codex workers at a time
    'claude': dict(model='claude-opus-5-5', reasoning='medium', label='Claude'),
    'codex': dict(model='gpt-6.1-sol', reasoning='medium', label='Codex'),
}
MAX_TURNS = 25          # a worker's conversation with its resident ends here; review or a new card starts afresh
CLAUDE_TOOLS = ('Bash', 'Read', 'Edit', 'MultiEdit', 'Write', 'Glob', 'Grep', 'TodoWrite',
                'mcp__agora__see', 'mcp__agora__do', 'mcp__agora__lines')
CLAUDE_DENIED = ('Bash(git push:*)', 'Bash(git checkout main:*)', 'Bash(git switch main:*)', 'Bash(git reset --hard:*)',
                 'Bash(git worktree:*)', 'Bash(git branch -D:*)', 'Bash(rm -rf /*)', 'Bash(taskkill:*)', 'Bash(shutdown:*)')


class Builders:
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
        busy = sum((s['phase'] in ACTIVE or s['task'] in self.children) and s.get('provider', 'codex') == provider
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
        self.states, self.children = {}, {}
        self.stopping = False
        for path in self.home.glob('*/state.json'):
            state = json.loads(path.read_text(encoding='utf-8'))
            if state.get('superseded_by'):        # an earlier run of a card that has had a new one
                continue
            if state['phase'] in ACTIVE:
                state.update(cut_phase=state['phase'], phase='recovery-needed', updated=stamp(),
                             detail=f"House restarted while it was {state['phase']}; inspect retained process, branch "
                                    "and receipts before resuming")
            rows=house.m.see('look '+state['task']).get('rows') or []
            if rows and rows[0].get('build_run') != state['run']:
                state.update(phase='released',detail='world claim released or reassigned; preserved work is not running')
            self.states[state['task']] = state
            self.save(state)

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

    def git(self, cwd, *args):
        """27 Oct: twice a git call finished its work but held the House past its timeout (a background repack, then
        two parallel reviews' `git add` stuck ~25 min). So: no auto gc/maintenance; one git at a time; stdin is empty,
        never the House's own kernel pipe; output goes to files, so no leftover child can hold a pipe open; and a
        timeout kills git's whole process tree."""
        cmd = ['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', '-C', str(cwd), *args]
        with self.git_lock, tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
            proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=out, stderr=err, creationflags=T.NO_WINDOW)
            try:
                code = proc.wait(timeout=120)
            except subprocess.TimeoutExpired:
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
        door = self.session(state['requester'])
        for attempt in range(4):
            task = door.look(state['task'])
            if task.get('build_run') != state['run']:
                raise RuntimeError('claim changed; the previous builder cannot update this task')
            try:
                if state.get('manager'):
                    return M.write_task(self, state, task, facts)
                return door.call('/do', 'set ' + state['task'] + ' ' + ' '.join(k+'='+q(v) for k,v in facts.items()),
                                 saw={state['task']: int(task['rev'])})
            except RuntimeError as exc:
                # 28 Oct: JEFF, as lead, set the card between this read and write; the run blocked before its
                # worktree. The claim is re-read each time, so another writer's facts are never overwritten blind.
                if 'stale' not in str(exc) or attempt == 3:
                    raise

    def phase(self, state, phase, detail, **facts):
        state.update(phase=phase, detail=detail, updated=stamp())
        self.event(state, phase, detail)
        build = {'asked':'asked', 'preparing':'asked', 'working':'building', 'reviewing':'landing',
                 'received':'landing', 'reviewed':'landing', 'landed':'landed'}.get(phase, 'blocked')
        self.update(state, build=build, build_phase=phase, build_detail=detail[:1500], **facts)

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
            if target in self.states and not again:
                return {'text': 'existing request: ' + self.states[target]['phase'], 'rows': [self.row(self.states[target])]}
            if self.full(provider):
                return {'refused': f'worker capacity is occupied: all {self.capacity_for(provider)} {provider} workers are busy; nothing was queued'}
            run = 'kernel-' + target + '-' + uuid.uuid4().hex[:10]
            state = dict(task=target, run=run, name=p['label']+' — '+short(task.get('title') or 'Builder', 60), requester=caller['person'],
                         requester_name=caller.get('name', ''), provider=provider,
                         title=task.get('title') or target, phase='asked', detail='claim pending',
                         model=p['model'], reasoning=p['reasoning'], created=stamp(), activity=[],
                         task_owner=task.get('who',''), pending=[], basis={k:task.get(k,'') for k in ('title','text','acceptance','who')})
            if msg.get('_managed'):
                state['manager'] = caller['person']
                M.check_state(self, state)
            if again:
                state['previous_run'] = prev['run']
                prev['superseded_by'] = run
                self.save(prev)
            self.states[target] = state
            self.save(state)
            threading.Thread(target=self.guarded, args=(state, self.build), daemon=True).start()
        return {'text': 'builder request recorded; claim and launch follow asynchronously', 'external': True,
                'rows': [self.row(state)]}

    def guarded(self, state, operation):
        try:
            operation(state)
        except Exception as exc:
            uncertain=isinstance(exc,(TimeoutError,ConnectionError,urllib.error.URLError,subprocess.TimeoutExpired))
            state.update(phase='uncertain' if uncertain else 'blocked', detail=str(exc)[:2000])
            self.event(state, state['phase'], state['detail'])
            try:
                if not uncertain:
                    self.update(state, build='blocked', build_phase=state['phase'], build_detail=state['detail'])
            except Exception:
                # The local receipt remains authoritative if ownership/door changed.
                pass
        finally:
            M.notify(self, state)
            try:
                self.outcome(state)
            except Exception as exc:                 # noqa: BLE001  telling is a help, never a reason to fail
                self.event(state, 'unsaid', f'outcome wake: {exc!r}')

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
                   '--model', state['model'], '--reasoning', state['reasoning'], '--timeout', '2400',
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
        self.phase(state, 'preparing', f'adapter started; awaiting authenticated {label} thread', builder_chat=state['chat'])
        if not child.send(prompt):
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
                    continue
                kind = e.get('e')
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
                elif kind == 'tool':
                    activity = T.worker_activity.tool(e)
                    self.event(state, 'act', activity['summary'] if activity else e.get('name', 'tool'),
                               activity['detail'] if activity else None)
                elif kind == 'text':
                    self.event(state, 'said', e['text'])
                    said.append(e['text'])
                elif kind == 'result':
                    state['result_received'] = stamp()
                    state['result_ok'] = bool(e.get('ok'))
                    if not e.get('ok'):
                        raise RuntimeError('worker failed: '+str(e.get('detail')))
                    state['turns']=state.get('turns',0)+1
                    self.report_turn(state, said[-1] if said else '(the worker ended its turn without words)')
                    said = []
                    self.assert_owned(state)
                    with self.lock:
                        pending = self.take_pending(state)
                    if pending:
                        self.event(state, 'heard', 'delivering queued owner follow-up')
                        if not child.send('\n'.join(pending)):
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
            if state['phase']=='received' and state.get('pending'):
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
                why = f"{state.get('requester_name') or 'Alex'} asked for it and is not a resident the House can wake"
            else:
                why = f"{agent.name}, in charge of it, can't act now ({(getattr(agent, 'state', None) or {}).get('error') or 'asleep'})"
            out.append((gm, f"~ Nobody can pick this up: {why}. Ask a resident in Shop talk to take it, and hand it "
                            f"over with house.hand {state['task']} <name>; or leave it if it should wait.\n"))
        return out

    def wake_owner(self, state, text):
        for agent, prefix in self.route(state):
            agent.wake(prefix + text)
            self.event(state, 'told', f"woke {agent.name} (busy={getattr(agent, 'busy', '?')}, "
                                      f"inbox={len(getattr(agent, 'inbox', None) or [])})"
                       + (' for its owner' if prefix else ''))

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
            if what in ('said', 'act', 'heard', 'working', 'preparing', 'asked', 'reopened', 'received'):
                return 'working'
            if what in ('reviewing', 'review-again', 'committed'):
                return 'reviewing'
            if what in ('reviewed', 'landing', 'carried'):
                return 'landing'
        return None

    def resumable(self, state):
        """Stopped and safe for a new turn on its worktree: received, blocked or reviewed; or cut off mid-turn
        with its process gone (never mid-review or mid-landing, where main or its branch may be half moved)."""
        if state['task'] in self.children:
            return False
        if state['phase'] in RESUMABLE:
            return True
        return (state['phase'] in CUT and bool(state.get('tree')) and self.cut_phase(state) == 'working'
                and not alive(state.get('pid')))

    def outcome(self, state):
        """A House operation on the worker ended (review, landing, or a failure): the one in charge hears how."""
        phase, task, name = state['phase'], state['task'], state['name']
        if self.stopping:
            return                       # the House is going down; wake_cut_off tells them when it is back
        if phase in ACTIVE or phase in ('received', 'released') or state.get('manager'):
            return                       # received: report_turn already woke them with the worker's words
        if phase == 'reviewed':
            text = (f"~ {name} ({task}) passed its independent checks (commit {str(state.get('candidate', ''))[:9]}). "
                    f"If it changes what Alex sees, look before landing: house.snap <thing> from={task} shows the "
                    f"worker's code in a hidden sandbox. Then house.land {task}.")
        elif phase == 'landed':
            text = (f"~ {name} ({task}) landed on main ({str(state.get('landed_commit', ''))[:9]}). "
                    f"{state.get('detail', '')}\n~ Check it works where Alex will see it (house.snap <thing>; if it "
                    f"needs the kernel or the House restarted first, ask JEFF in Shop talk). Then tell JEFF in Shop "
                    f"talk, in plain words, that it is done and looks good, or what is wrong, and set the card's lane "
                    f"to Done once you have checked.")
        else:
            text = (f"~ {name} ({task}) stopped ({phase}): {str(state.get('detail', ''))[:700]}\n~ You are in charge "
                    f"of it: tell it what to do (house.tell {task} <words>), review it again (house.review {task}), "
                    f"hand it on (house.hand {task} <name>), or tell JEFF in Shop talk if it needs Alex.")
        said = [phase, str(state.get('detail', ''))[:300]]
        if state.get('last_outcome') == said:
            self.event(state, 'quiet', 'same outcome as last time; nobody woken again')
            return                       # the same failure twice wakes nobody twice (the 3 Nov loop)
        state['last_outcome'] = said
        self.stopped(state)
        self.wake_owner(state, text)

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
        return f"- {state['name']} ({state['task']}): {state['phase']} since {since}. {str(state.get('detail', ''))[:200]}"

    def wake_cut_off(self):
        """House start: owners hear, once, about workers a restart cut off (each gets one wake listing them)."""
        heard = {}
        with self.lock:
            for state in self.states.values():
                if state['phase'] not in CUT or state.get('cut_told') or state.get('manager') or self.card_done(state):
                    continue
                state['cut_told'] = stamp()
                for agent, prefix in self.route(state):
                    heard.setdefault(agent.person, (agent, []))[1].append((state, prefix))
        for agent, items in heard.values():
            lines = []
            for state, prefix in items:
                self.stopped(state)
                ok = self.resumable(state)
                lines.append(self.waiting_line(state) + (
                    f" It can carry on: house.tell {state['task']} <words> starts a new turn on its worktree."
                    if ok else f" It was cut off while {self.cut_phase(state) or 'busy'}: don't resume it; hand the "
                               f"question to Claude or Alex in Shop talk, or start afresh with house.build {state['task']}.")
                    + (' (Its owner cannot act now: hand it to a resident with house.hand.)' if prefix else ''))
            agent.wake("~ The House restarted and cut these workers off mid-way. You are the one to pick them up:\n"
                       + '\n'.join(lines) + "\n~ For each: carry it on, hand it on (house.hand <card> <name>), or "
                       "say on its card why it waits.")
            for state, _ in items:
                self.event(state, 'told', f'woke {agent.name} about the cut-off')

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
        agent.wake("~ Reminder: these workers stopped and still wait on you:\n"
                   + '\n'.join(self.waiting_line(s) for s in waiting)
                   + "\n~ For each: answer it (house.tell <card> <words>), review or land it, check it (house.snap), "
                     "hand it on (house.hand <card> <name>), or say on its card why it waits. This is the only reminder.")
        for state in waiting:
            self.event(state, 'reminded', f'reminded {agent.name}')

    def hand(self, msg):
        """house.hand <card> <name>: give a worker (and its card) to another resident, who is in charge from now."""
        args = msg.get('args') or {}
        caller = msg.get('caller') or {}
        state = self.states.get(args.get('target'))
        name = str(args.get('words') or '').strip().lstrip('@').strip()
        if not state:
            return {'refused': 'this card has no worker'}
        if not name:
            return {'refused': 'house.hand <card> <name>: who takes it'}
        if not (self.may_act(state, msg) or self.alex(caller.get('person'))):
            return {'refused': "only the worker's owner, a steward or Alex may hand it on"}
        agents = getattr(self.h, 'agents', {})
        to = next((a for a in agents.values() if a.name.casefold() == name.casefold()), None)
        if to is None:
            return {'refused': f"{name} is not a House agent; they are: " + ', '.join(a.name for a in agents.values())}
        if to.person == state['requester']:
            return {'refused': f'{to.name} is already in charge of it'}
        with self.lock:
            if state['task'] in self.children or state['phase'] in ACTIVE:
                return {'refused': f"it is {state['phase']} now; hand it on once it stops"}
            if state['phase'] == 'released':
                return {'refused': 'it was released; house.build starts a new worker on the card'}
        try:
            door = self.session(to.person)
        except RuntimeError:
            return {'refused': f'{to.name} has no worker session; it cannot run workers yet'}
        card = state['task']
        task = door.look(card)
        if not task:
            return {'refused': f'{to.name} cannot see the card {card}'}
        # The card is rewritten by whoever may: the one handing it on (JEFF and Alex lead the desktop), else its old
        # owner, else the new one (3 Nov: a resident may not set a card it did not make).
        moved, why = False, ''
        for person in dict.fromkeys(p for p in (caller.get('person'), state['requester'], to.person) if p):
            try:
                self.session(person).call('/do', f'set {card} who={q(to.name)} lead={q(to.name)}',
                                          saw={card: int(task['rev'])})
                moved = True
                break
            except Exception as exc:                  # noqa: BLE001  try the next who may
                why = str(exc)
        if not moved:
            return {'refused': f'not handed: the card could not be given to {to.name}: {why[:300]}'}
        try:
            task = door.look(card)
            chat = door.call('/do', 'make kind=chat name=' + q(state['name']) + ' about=' + card + ' with=' + to.person,
                             press=state['run'] + '-chat-' + to.person)['made'][-1]
        except Exception as exc:                          # noqa: BLE001
            return {'refused': f'not handed: {str(exc)[:300]}'}
        was = state.get('requester_name') or state['requester']
        by = caller.get('name') or caller.get('person') or 'someone'
        with self.lock:
            state.update(requester=to.person, requester_name=to.name, task_owner=task.get('who', ''), chat=chat,
                         boss_note=f'{was} handed you on: {to.name} is in charge of you from now, and your messages '
                                   f'go to them.', tellers=[], told_by=[])
            state.pop('manager', None)
            if state.get('basis'):
                state['basis'] = {k: task.get(k, '') for k in ('title', 'text', 'acceptance', 'who')}
            state.setdefault('handed', []).append(dict(at=stamp(), by=by, was=was, to=to.name))
            self.save(state)
        self.event(state, 'handed', f'{by} handed it from {was} to {to.name}')
        last = str(state.get('last_words') or '').strip()
        try:
            note = f'{by} handed this worker to {to.name}. Last words: ' + (last or '(none kept)')
            door.call('/do', f'say {chat} text={q(note[:3000])}')
        except Exception as exc:                          # noqa: BLE001
            self.event(state, 'unsaid', str(exc))
        self.stopped(state)
        ok = self.resumable(state)
        to.wake(f"~ {by} handed you the worker {state['name']} ({card}); you are in charge of it now (it was {was}'s).\n"
                f"~ Where it stands: {state['phase']}. {str(state.get('detail', ''))[:500]}\n"
                + (f"~ Its last words:\n{last[:2500]}\n" if last else '')
                + f"~ Read the card (look {card}) and its log (house.log {card}). Then "
                + (f"answer it (house.tell {card} <words>), " if ok else '')
                + f"review or land it (house.review / house.land {card}), check what Alex would see (house.snap), "
                  f"and tell JEFF in Shop talk, in plain words, when it is done and looks good, or when it needs "
                  f"Alex. If it is no longer wanted, say so on the card and set its lane to Done.")
        return {'text': f'{to.name} is in charge of {state["name"]} ({card}) now and was woken with where it stands',
                'external': True}

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
        left = MAX_TURNS - state.get('turns', 0)
        agents = getattr(self.h, 'agents', {})
        for t in tellers:
            other = agents.get(t['person'])
            if other is None:
                self.event(state, 'told', f"{t['name']} told it this turn; not a House agent to wake (reads its chat)")
                continue
            other.wake(
                f"~ The worker {state['name']} ({state['task']}), which you told something, finished a turn and says:\n"
                f"{words}\n\n~ Its owner {state.get('requester_name') or state['requester']} is woken too and stays in "
                f"charge of it. You may answer it with house.tell {state['task']} <your words> ({left} turns left).")
            self.event(state, 'told', f"woke {t['name']}, who told it this turn ({t['as']})")
        others = ', '.join(sorted({t['name'] for t in tellers}))
        if not self.route(state):
            self.event(state, 'told', 'posted in its chat; no resident to wake (Alex reads it there)')
            return
        self.wake_owner(state,
            f"~ Your worker {state['name']} ({state['task']}) finished a turn and says:\n{words}\n\n"
            + (f"~ This turn it also followed words from {others}; you are still in charge.\n" if others else '')
            + f"~ You are in charge of this worker. To answer it, run house.tell {state['task']} <your words>: that is "
            f"its next instruction ({left} turns left). When its work is done and it says what it tested: "
            f"house.review {state['task']}, then house.land {state['task']} once the checks pass; house.snap shows "
            f"what Alex would see. Tell JEFF in Shop talk, in plain words, when it is done and looks good, or when "
            f"something needs Alex.")

    def owner_turn_ended(self, person):
        """A resident's turn ended: what it said to its workers during that turn starts their next turn now."""
        for state in list(self.states.values()):
            if state['requester'] != person or not state.get('pending'):
                continue
            with self.lock:
                if not self.resumable(state):
                    continue
                if self.full(state.get('provider', 'codex')):
                    self.event(state, 'held', 'resident replied, but all workers of this kind are busy; it waits')
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

    def take_pending(self, state):
        """Hand the queued words to the worker; whoever said them (besides its owner) hears how this turn ends."""
        pending, state['pending'] = state.get('pending', []), []
        if pending:
            state['tellers'], state['told_by'] = state.get('told_by') or [], []
        self.save(state)
        return pending

    def reopen(self, state):
        """A stopped worker (received, blocked, reviewed) takes a new turn in the same worktree. A review's receipts
        are about a result that is about to change, so they move to `earlier_reviews` instead of standing as current."""
        was = state['phase']
        if was != 'received':
            old = {k: state.pop(k) for k in ('review_base', 'candidate', 'checks', 'self_proof_sha256') if k in state}
            if old:
                state.setdefault('earlier_reviews', []).append(dict(old, phase=was, detail=state.get('detail', ''), at=stamp()))
            self.event(state, 'reopened', f"was {was} ({str(state.get('detail', ''))[:300]}); a new turn on the same worktree")
        if was in CUT:
            state['resume_note'] = ('You were cut off mid-turn (the House restarted or lost touch with you). Check what '
                                    'your worktree already holds before going on.')
        state['reopened_from'] = was if was != 'received' else state.get('reopened_from', '')
        state['phase'] = 'preparing'
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
            return {'refused': f'made card {card}, but the worker did not start: {out["refused"]}'}
        return {'text': f"started a {PROVIDERS[provider]['label']} worker on {title} ({card}). You are woken each time "
                        f"it finishes a turn (its words also go in its chat); answer it with house.tell {card} <words>.",
                'external': True, 'rows': out.get('rows', [])}

    def resume(self, state):
        self.assert_owned(state)
        with self.lock:
            pending=self.take_pending(state)
            notes=[state.pop(k) for k in ('boss_note','resume_note') if state.get(k)]
            self.save(state)
        prompt='Follow-up on this same task. Retain its scope and all safety boundaries.\n'+'\n'.join(notes+pending)
        if not state.get('session'):      # stopped before any model thread: the worker has not read its task yet
            prompt=self.prompt(state,self.session(state['requester']).look(state['task']))+'\n'+prompt
        self.run_worker(state, prompt)

    def retry(self, msg):
        """Only a proven pre-thread startup failure; never replay an unknown turn."""
        state=self.states.get(msg.get('args',{}).get('target'))
        if not state or not self.may_act(state, msg):
            return {'refused':'only the requester may retry this startup'}
        with self.lock:
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
        if held(task) or task.get('build_run') != state['run'] or task.get('who','') != state.get('task_owner',''):
            return {'refused':'task is held or claim changed; message did not wake it'}
        with self.lock:
            phase=state['phase']
            if phase in ('landed','released'):
                return {'refused':f'this worker is {phase}; start a new run with house.build {state["task"]}'}
            if phase not in ('asked','preparing','working') and phase not in RESUMABLE and not self.resumable(state):
                # reviewing/landing: the House is acting on its result now. Cut off (recovery-needed, uncertain):
                # resumable once its process is gone, and only if it was cut off mid-turn, not mid-review/landing.
                if phase in CUT and self.cut_phase(state) == 'working':
                    return {'refused':f'worker is {phase} and its process may still be running; wait, or ask JEFF to '
                                      f'stop it (message did not restart it)'}
                if phase in CUT:
                    return {'refused':f'worker was cut off while {self.cut_phase(state) or "busy"}; main or its branch '
                                      f'may be half moved, so it is not resumed. Ask Claude or Alex in Shop talk, or '
                                      f'start afresh with house.build {state["task"]}'}
                return {'refused':f'worker is {phase}; reconcile it before a new turn (message did not restart it)'}
            if phase in RESUMABLE and state['task'] not in self.children and not state.get('tree'):
                return {'refused':'worker stopped before its worktree was made; house.retry '+state['task']+' starts it'}
            if len(state.setdefault('pending',[])) >= 10:
                return {'refused':'ten follow-ups already pending; no more were queued'}
            if state.get('turns',0) >= MAX_TURNS:
                return {'refused':f'this worker has had {MAX_TURNS} turns; review it, or start a new card'}
            if how!='owner':  # the worker knows who said it; the owner stays in charge and is still woken
                name=caller.get('name') or caller.get('person') or 'someone'
                words=f'From {name} ({how}; {state.get("requester_name") or "your owner"} stays in charge): {words}'
                added=not any(t['person']==caller.get('person') for t in state.setdefault('told_by',[]))
                if added:
                    state['told_by'].append(dict(person=caller.get('person'),name=name,**{'as':how}))
            if hold:          # said during the resident's own turn: starts the worker when that turn ends
                state['pending'].append(words[:8000])
                self.event(state,'heard',words)
                return {'text':'follow-up retained until your turn ends','external':True}
            resume=self.resumable(state)
            if resume and self.full(state.get('provider','codex')):
                if how!='owner' and added:state['told_by'].pop()
                return {'refused':'builder capacity is occupied; follow-up did not start or queue another builder'}
            # Explicit owner correction replaces the task basis, never its authority.
            state['basis']={k:task.get(k,'') for k in ('title','text','acceptance','who')}
            state['pending'].append(words[:8000])
            self.event(state,'heard',words)
            if how!='owner':
                self.event(state,how,f"{caller.get('name') or caller.get('person')} told it as {how}, not its owner")
            if resume:
                self.reopen(state)
                threading.Thread(target=self.guarded,args=(state,self.resume),daemon=True).start()
        told='' if how=='owner' else '; its owner is woken when it ends that turn, and so are you'
        if resume and phase!='received':
            return {'text':f'worker was {phase}; it resumes with your words in a new turn on the same worktree{told}',
                    'external':True}
        return {'text':f'follow-up retained for this builder; it will be read at the next turn boundary{told}','external':True}

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

    def prompt(self, state, task):
        boss = state.get('requester_name') or 'the person who asked'
        return f'''You are {state['name']}, a coding worker in Alex's Agora desktop (the kernel world on 8810).
{boss} is in charge of you. Your last message each turn is posted in your chat with {boss}; they answer there,
and their answer is your next instruction. Ask them when something is unclear instead of guessing.
Task: {state['title']} ({state['task']}). Task text: {task.get('text', '')}
Acceptance: {task.get('acceptance', '') or 'what the task text asks for, working and tested'}
You work only in this worktree, on this task. Read AGENTS.md first, then Alex's live standing rules with the
Agora tools (see `look dk838`). Use the Agora tools (see, do, lines) to read the
world; never change credentials, security settings or providers, and never start another worker.
No visible test windows (hidden fixtures only), no pushes, no merging to main, no deleting other people's work, no
stopping Alex's programs. If something is denied, stop and say so; do not route around it.
Use the pinned {T.PY}. Do not commit: leave your changes in the worktree; at review the House commits them to your
branch (except BUILD-RESULT.md and top-level dot-folders, where scratch and temp fixtures belong).
When done, leave BUILD-RESULT.md at the worktree root: what you changed (files), what you ran and its results, what is
left. Then end your turn with a short summary for {boss}: done, or what you need from them.
'''

    def assert_owned(self, state):
        M.check_state(self, state)
        task = self.session(state['requester']).look(state['task'])
        if task.get('build_run') != state['run'] or held(task):
            raise RuntimeError('task claim changed or is held; stop this operation')
        if state.get('basis') and any(task.get(k,'') != v for k,v in state['basis'].items()):
            raise RuntimeError('task instructions or owner changed; review the correction before continuing')

    def request_review(self, msg):
        state = self.states.get(msg.get('args', {}).get('target'))
        if not state or not self.may_act(state, msg):
            return {'refused': 'only the requester may review this build'}
        with self.lock:
            # Review again: after main moved past a reviewed result, or after a review whose checks failed (the run
            # stays blocked with its review receipts). Never an active, uncertain or pre-review failure.
            again = state['phase'] == 'reviewed' or (state['phase'] == 'blocked' and state.get('review_base'))
            if state.get('pending') and state['phase'] == 'received' and state['task'] not in self.children:
                # the requester chose review over what it last said to the worker in the same turn
                self.event(state, 'dropped', 'review asked; not sent to the worker: ' + ' | '.join(state['pending'])[:500])
                state['pending'] = []
            if (state['phase'] != 'received' and not again) or state['task'] in self.children or state.get('pending'):
                return {'refused': 'review requires a received, reviewed or review-failed result, not an active or uncertain worker'}
            if self.full(state.get('provider', 'codex')):
                return {'refused': 'worker capacity is occupied: all ' + state.get('provider', 'codex') + ' workers are busy; review did not start'}
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
        if not report.is_file():
            raise RuntimeError('worker self-proof BUILD-RESULT.md is missing')
        # Never erase or stash worker edits: commit them to its branch, then check that exact commit.
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
            try:
                self.git(tree, 'merge', '--no-edit', base)
            except RuntimeError:
                # Never leave conflict markers for the next review's commit to pick up.
                conflicted = self.git(tree, 'diff', '--name-only', '--diff-filter=U').split()
                self.git(tree, 'merge', '--abort')
                raise RuntimeError('main conflicts with this worker in ' + ', '.join(conflicted or ['some files'])
                                   + '; merge main into the worker branch by hand, then review again') from None
        candidate = self.git(tree, 'rev-parse', 'HEAD')
        state.update(review_base=base, candidate=candidate, checks=[])
        self.phase(state, 'reviewing', 'independent kernel and hidden desktop checks on '+candidate[:12])
        folder = self.home/state['run']
        for i, tests in enumerate(CHECKS):
            path = folder/f'check-{i}.txt'
            with path.open('w', encoding='utf-8') as out:
                proc = subprocess.run([str(T.PY), '-B', '-m', 'pytest', '-q', *tests], cwd=tree, env=T.clean_env('off'),
                                      stdout=out, stderr=subprocess.STDOUT, timeout=600, creationflags=T.NO_WINDOW)
            receipt = dict(tests=tests, returncode=proc.returncode, evidence=str(path),
                           sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            state['checks'].append(receipt)
            self.save(state)
            if proc.returncode:
                raise RuntimeError('independent check failed; see '+str(path))
        if self.git(tree, 'rev-parse', 'HEAD') != candidate or self.git(tree, 'status', '--porcelain', '--untracked-files=no'):
            raise RuntimeError('candidate changed during review; evidence not reusable')
        self.phase(state, 'reviewed', 'independent checks passed; awaiting source publication and activation',
                   reviewed_commit=candidate)

    def land(self, msg):
        state = self.states.get(msg.get('args', {}).get('target'))
        if not state or not self.may_act(state, msg):
            return {'refused': 'only the requester may land this build'}
        with self.lock:
            if state['phase'] != 'reviewed':
                return {'refused': 'independent review has not passed'}
            if any(s['phase'] == 'landing' for s in self.states.values()):
                return {'refused': 'another source publication is running'}
            if self.full(state.get('provider', 'codex')):
                return {'refused': 'worker capacity is occupied: all ' + state.get('provider', 'codex') + ' workers are busy; publication did not start'}
            state['phase'] = 'landing'
            state.pop('awaiting', None)
            state.pop('reminded', None)
            self.save(state)
            threading.Thread(target=self.guarded, args=(state, self.publish), daemon=True).start()
        return {'text': 'source publication requested; activation and task verification remain separate', 'external': True}

    def publish(self, state):
        self.assert_owned(state)
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
                    awaiting=state.get('awaiting',''), owner_name=state.get('requester_name',''),
                    first_words_ms=None, error=state.get('detail','') if phase=='blocked' else '',
                    acts=[], acts_text='', waiting=0, session=state.get('session',''))

    def rows(self, msg=None):
        with self.lock:
            states=list(self.states.values())
        return [self.row(s) for s in states if msg is None or self.h.m.see('look '+s['task'],use=msg.get('use')).get('rows')]

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
        self.stopping = True
        for child in list(self.children.values()):
            child.stop()
