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
                state.update(phase='recovery-needed', detail='House restarted during an operation; inspect retained process, branch and receipts before resuming')
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

    def event(self, state, what, text):
        with self.lock:
            state.setdefault('activity', []).append(dict(at=stamp(), what=what, text=str(text)[:4000]))
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
        again = bool(prev) and prev['phase'] in ('landed', 'released') and target not in self.children
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
        child = T.Child(cmd, tree, T.clean_env(), events, lambda *_: None, stderr=folder/'stderr.log')
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
                    self.event(state, 'act', e.get('name', 'tool'))
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
                        pending = state.get('pending', [])
                        state['pending'] = []
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
    def owner(self, state):
        """The House agent (resident or JEFF) in charge of this worker, or None when Alex asked for it himself."""
        if state.get('manager'):
            return None                  # Rowan's managed builds are woken by manager.notify
        return getattr(self.h, 'agents', {}).get(state['requester'])

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
        agent = self.owner(state)
        if agent is None:
            self.event(state, 'told', 'posted in its chat; no resident to wake (Alex reads it there)')
            return
        left = MAX_TURNS - state.get('turns', 0)
        agent.wake(
            f"~ Your worker {state['name']} ({state['task']}) finished a turn and says:\n{words}\n\n"
            f"~ You are in charge of this worker. What you say in this chat goes to it as your next instruction "
            f"({left} turns left). When its work is done and it says what it tested: house.review {state['task']}, "
            f"then house.land {state['task']} once the checks pass. Tell JEFF in Shop talk when it lands, or when "
            f"something needs Alex. If you have nothing for the worker now, stay quiet here.",
            chat=chat)
        self.event(state, 'told', f'woke {agent.name} in its chat {chat} (busy={agent.busy}, inbox={len(agent.inbox)})')

    def owner_turn_ended(self, person):
        """A resident's turn ended: what it said to its workers during that turn starts their next turn now."""
        for state in list(self.states.values()):
            if state['requester'] != person or not state.get('pending'):
                continue
            with self.lock:
                if state['phase'] != 'received' or state['task'] in self.children:
                    continue
                if self.full(state.get('provider', 'codex')):
                    self.event(state, 'held', 'resident replied, but all workers of this kind are busy; it waits')
                    continue
                state['phase'] = 'preparing'
                self.save(state)
                threading.Thread(target=self.guarded, args=(state, self.resume), daemon=True).start()

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
        return {'text': f"started a {PROVIDERS[provider]['label']} worker on {title} ({card}). Its chat is named after "
                        f"it; you are woken there each time it finishes a turn, and what you say there is its next "
                        f"instruction.", 'external': True, 'rows': out.get('rows', [])}

    def resume(self, state):
        self.assert_owned(state)
        with self.lock:
            pending=state['pending'];state['pending']=[]
            self.save(state)
        self.run_worker(state, 'Owner follow-up on this same task. Retain its scope and all safety boundaries.\n'+'\n'.join(pending))

    def retry(self, msg):
        """Only a proven pre-thread startup failure; never replay an unknown turn."""
        state=self.states.get(msg.get('args',{}).get('target'))
        if not state or state['requester'] != msg.get('caller',{}).get('person'):
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
        if not state or state['requester'] != msg.get('caller',{}).get('person'):
            return {'refused':'only the requester may continue this builder'}
        if not words:
            return {'refused':'house.tell <task> <words>: provide a follow-up'}
        task=self.session(state['requester']).look(state['task'])
        if held(task) or task.get('build_run') != state['run'] or task.get('who','') != state.get('task_owner',''):
            return {'refused':'task is held or claim changed; message did not wake it'}
        with self.lock:
            if state['phase'] not in ('asked','preparing','working','received'):
                return {'refused':'builder needs review or recovery; message did not restart it'}
            if len(state.setdefault('pending',[])) >= 10:
                return {'refused':'ten follow-ups already pending; no more were queued'}
            if state.get('turns',0) >= MAX_TURNS:
                return {'refused':f'this worker has had {MAX_TURNS} turns; review it, or start a new card'}
            if hold:          # said during the resident's own turn: starts the worker when that turn ends
                state['pending'].append(words[:8000])
                self.event(state,'heard',words)
                return {'text':'follow-up retained until your turn ends','external':True}
            if state['phase']=='received' and state['task'] not in self.children and self.full(state.get('provider','codex')):
                return {'refused':'builder capacity is occupied; follow-up did not start or queue another builder'}
            # Explicit owner correction replaces the task basis, never its authority.
            state['basis']={k:task.get(k,'') for k in ('title','text','acceptance','who')}
            state['pending'].append(words[:8000])
            self.event(state,'heard',words)
            if state['phase']=='received' and state['task'] not in self.children:
                state['phase']='preparing';self.save(state)
                threading.Thread(target=self.guarded,args=(state,self.resume),daemon=True).start()
        return {'text':'follow-up retained for this builder; it will be read at the next turn boundary','external':True}

    def hear(self, msg):
        if msg.get('word')!='say' or not msg.get('said'):
            return
        rows=self.h.m.see('look '+msg['said']).get('rows') or []
        if not rows:return
        row=rows[0]
        for state in list(self.states.values()):
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
You work only in this worktree, on this task. Read AGENTS.md first; its `read a6529 :3` line points at the
archived old desk, so skip it (the rules it lists are current). Use the Agora tools (see, do, lines) to read the
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
        if not state or state['requester'] != msg.get('caller', {}).get('person'):
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
                proc = subprocess.run([str(T.PY), '-B', '-m', 'pytest', '-q', *tests], cwd=tree,
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
        if not state or state['requester'] != msg.get('caller', {}).get('person'):
            return {'refused': 'only the requester may land this build'}
        with self.lock:
            if state['phase'] != 'reviewed':
                return {'refused': 'independent review has not passed'}
            if any(s['phase'] == 'landing' for s in self.states.values()):
                return {'refused': 'another source publication is running'}
            if self.full(state.get('provider', 'codex')):
                return {'refused': 'worker capacity is occupied: all ' + state.get('provider', 'codex') + ' workers are busy; publication did not start'}
            state['phase'] = 'landing'
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
                    task=state['task'], chat=state.get('chat', ''), doing=phase, now=state.get('detail', ''),
                    colour='sage' if phase=='working' else 'rose' if phase in ('blocked','recovery-needed') else 'sky',
                    provider=state.get('provider', 'codex'), model=state['model'], reasoning=state['reasoning'],
                    turns=state.get('turns',0), last_turn=state.get('updated',''),
                    first_words_ms=None, error=state.get('detail','') if phase=='blocked' else '',
                    acts=[], acts_text='', waiting=0, session=state.get('session',''))

    def rows(self, msg=None):
        with self.lock:
            states=list(self.states.values())
        return [self.row(s) for s in states if msg is None or self.h.m.see('look '+s['task'],use=msg.get('use')).get('rows')]

    def log(self, task):
        state = self.states[task]
        lines = [f"{e['what']}\t{e['at'][11:16]}\t{state['name']}\t{e['text']}" for e in state['activity']]
        return {'text':'\n'.join(lines), 'rows':[dict(person=task, name=state['name'], log='\n'.join(lines), lines=len(lines))]}

    def off(self):
        self.stopping = True
        for child in list(self.children.values()):
            child.stop()
