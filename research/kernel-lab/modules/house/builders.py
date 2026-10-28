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


class Builders:
    capacity = 2

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
        door = self.session(state['requester'])
        task = door.look(state['task'])
        if task.get('build_run') != state['run']:
            raise RuntimeError('claim changed; the previous builder cannot update this task')
        return door.call('/do', 'set ' + state['task'] + ' ' + ' '.join(k+'='+q(v) for k,v in facts.items()),
                         saw={state['task']: int(task['rev'])})

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
        if not rows or rows[0].get('kind') not in ('taskboard-task', 'task'):
            return {'refused': 'choose a visible task card'}
        task = rows[0]
        if held(task) or task.get('builder') or task.get('build_run'):
            return {'refused': 'task is held, finished, or already has a builder; reconcile it before a new build'}
        if task.get('who') and task.get('who') not in (caller.get('name'), 'JEFF'):
            return {'refused': 'task has another owner; ask that owner to release it first'}
        self.session(caller['person'])  # validate before recording or spawning anything
        with self.lock:
            if target in self.states:
                return {'text': 'existing request: ' + self.states[target]['phase'], 'rows': [self.row(self.states[target])]}
            if sum(s['phase'] in ACTIVE or s['task'] in self.children for s in self.states.values()) >= self.capacity:
                return {'refused': 'both builder slots are occupied; no request was queued'}
            run = 'kernel-' + target + '-' + uuid.uuid4().hex[:10]
            state = dict(task=target, run=run, name='Codex — '+str(task.get('title') or 'Builder')[:60], requester=caller['person'],
                         title=task.get('title') or target, phase='asked', detail='claim pending',
                         model='gpt-6.1-sol', reasoning='medium', created=stamp(), activity=[],
                         task_owner=task.get('who',''), pending=[], basis={k:task.get(k,'') for k in ('title','text','acceptance','who')})
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

    def build(self, state):
        door = self.session(state['requester'])
        task = door.look(state['task'])
        if held(task) or task.get('builder') or task.get('build_run') or task.get('who','') != state['task_owner']:
            raise RuntimeError('task changed before claim; nothing launched')
        claim = door.call('/do', 'set '+state['task']+' builder='+q(state['name'])+' build=asked build_run='+q(state['run']),
                          saw={state['task']: int(task['rev'])})
        state['claim_records'] = claim.get('records', [])
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
        cmd = [str(T.PY), str(T.REPO/'research/codex-residents/codex_worker.py'),
               '--model', state['model'], '--reasoning', state['reasoning'], '--timeout', '2400',
               '--prompt-file', str(folder/'prompt.md'), '--mcp-config', mcp, '--lease', str(folder/'process.lock')]
        if state.get('session'):
            cmd += ['--resume', state['session']]
        self.assert_owned(state)
        child = T.Child(cmd, tree, T.clean_env(), events, lambda *_: None, stderr=folder/'stderr.log')
        self.children[state['task']] = child
        state['pid'] = child.proc.pid
        self.phase(state, 'preparing', 'adapter started; awaiting authenticated Codex thread', builder_chat=state['chat'])
        if not child.send(prompt):
            raise RuntimeError('initial send uncertain; no replay')
        ended = False
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
                    self.event(state, 'init', 'authenticated Codex thread started')
                elif kind == 'turn_started':
                    state['turn_started'] = stamp()
                    state['turn_id'] = e.get('turn')
                    self.phase(state, 'working', 'authenticated Codex turn running')
                elif kind == 'tool':
                    self.event(state, 'act', e.get('name', 'tool'))
                elif kind == 'text':
                    self.event(state, 'said', e['text'])
                elif kind == 'result':
                    state['result_received'] = stamp()
                    state['result_ok'] = bool(e.get('ok'))
                    if not e.get('ok'):
                        raise RuntimeError('worker failed: '+str(e.get('detail')))
                    state['turns']=state.get('turns',0)+1
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
            if sum(s['phase'] in ACTIVE or s['task'] in self.children for s in self.states.values())>=self.capacity:
                return {'refused':'both slots occupied'}
            state['phase']='preparing';self.save(state)
            def launch(s):
                self.assert_owned(s)
                if (not s.get('tree') or self.git(s['tree'],'rev-parse','HEAD')!=s['base']
                        or self.git(s['tree'],'status','--porcelain','--untracked-files=no')):
                    raise RuntimeError('startup tree has changes; reconcile before retry')
                task=self.session(s['requester']).look(s['task'])
                self.run_worker(s,self.prompt(s,task))
            threading.Thread(target=self.guarded,args=(state,launch),daemon=True).start()
        return {'text':'pre-thread startup retry recorded; same claim and worktree, no task replay','external':True}

    def tell(self, msg):
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
            if state['phase']=='received' and state['task'] not in self.children and sum(
                    s['phase'] in ACTIVE or s['task'] in self.children for s in self.states.values()) >= self.capacity:
                return {'refused':'both slots occupied; follow-up did not start or queue another builder'}
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
                out=self.tell(dict(args=dict(target=state['task'],words=row.get('text','')),
                                   caller=dict(person=state['requester'])))
                if out.get('refused'):self.event(state,'held',out['refused'])

    def prompt(self, state, task):
        return f'''You are {state['name']}, a Codex builder for Alex inside the kernel desktop.
Current task: {state['title']} ({state['task']}). Read its current card and charter via Agora see.
Task text: {task.get('text', '')}
Acceptance: {task.get('acceptance', '')}
You own only this task in this House-created worktree. Read AGENTS.md and the approved direction at
C:/Projects/Agora4/research/kernel-lab/agents/MOVING-IN.md (canonical source, not yet tracked in older worker bases).
The current world is kernel8810, not Frontier. Use Agora see/do/lines with the existing agent-for-Alex session;
never change credentials, security settings or provider, use paid fallback, or start another worker.
Preserve existing user work and apps. No visible test windows, OBS operations, global window-manager changes,
forced process stops, deletions, publishing or pushes. Use hidden fixtures. Stop an exact denied action and report it;
do not route around a denial. No task.done or merging to main: owner review remains required.
Use the pinned {T.PY}. Implement the existing requested task and test affected behavior.
Your sandbox cannot write .git (index.lock is denied): never stage or commit, and don't work around it. Leave your source
changes in this worktree; at review the House commits everything you left to your branch, except BUILD-RESULT.md and
top-level dot-folders. So keep scratch, temp fixtures and logs out of the tree or under a top-level dot-folder.
For writing import: first inspect sources/permissions, preserve originals/authorship/current writing, use idempotent
provenance and prepare a reviewable importer/manifest; do not import private or ambiguous content without review.
Do not read sessions/*.pickle directly or grep exported transcripts. Never expose secrets.
Before each irreversible effect check the current task for correction, pause, cancellation and owner changes.
Leave BUILD-RESULT.md at worktree root (untracked): exact changes and the files you changed, commands/results, limitations,
activation requirements and blockers. A model ending is received, not reviewed or verified. End with a useful result.
<transcript_evidence>
User, October 27, message Sentinel_cd8f7f9ae8c4819196c8b9c06fd41908: "awesome, can i get you to get  some codex workers get codex workers working in the world and have them start pickup up tasks and completing them?"
Assistant, October 27: "Found the blocker: the new world is running, but its House can only run JEFF; the Codex worker launcher hasn’t been built yet. I’ll have the coordinator implement that missing piece, then start with the window-minimising bug and the old-world writing import, which JEFF identified as unclaimed."
</transcript_evidence>
'''

    def assert_owned(self, state):
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
            if (state['phase'] != 'received' and not again) or state['task'] in self.children or state.get('pending'):
                return {'refused': 'review requires a received, reviewed or review-failed result, not an active or uncertain worker'}
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
        if base != state['base']:
            self.git(tree, 'merge', '--no-edit', base)
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
        if set(changed) & set(dirty):
            raise RuntimeError('canonical uncommitted edits overlap candidate; preserve both and reconcile')
        self.git(self.repo, 'merge', '--ff-only', state['candidate'])
        state['landed_commit'] = self.git(self.repo, 'rev-parse', 'HEAD')
        self.phase(state, 'landed', 'source landed; activation and owner outcome verification remain',
                   landed_commit=state['landed_commit'], outcome='unverified')

    def row(self, state):
        phase = state['phase']
        return dict(id=state['task'], person=state['task'], name=state['name'], role='builder',
                    task=state['task'], chat=state.get('chat', ''), doing=phase, now=state.get('detail', ''),
                    colour='sage' if phase=='working' else 'rose' if phase in ('blocked','recovery-needed') else 'sky',
                    provider='codex', model=state['model'], reasoning=state['reasoning'],
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
