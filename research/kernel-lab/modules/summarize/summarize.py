"""Reviewed, stateless task summaries. Only loopback Ollama; no files or downloads.

Model selection is taskboard-settings' `model` fact (default qwen2.5:3b).
All model attempts share a seven-second call budget. Failure is labelled, never
silently presented as a model result. Undo reverses facts, not model computation.
"""
import json
import re
import sys
import threading
import time
import urllib.request

pending = {}
lock = threading.Lock()


def quote(value):
    return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"') + '"'


def send(message):
    with lock:
        print(json.dumps(message), flush=True)


def read(use, line):
    event = threading.Event()
    pending[use] = [event, None]
    send(dict(t='see', use=use, line=line))
    if not event.wait(2):
        pending.pop(use, None)
        raise ValueError('kernel reading timed out')
    result = pending.pop(use)[1]
    if result.get('refused'):
        raise ValueError(result['refused'])
    return result.get('rows', [])


def shorten(text):
    clause = re.split(r'[\r\n;]|(?<=[.!?])\s|\s[—–]\s', str(text).strip())[0]
    clause = ' '.join(clause.split())
    if len(clause) <= 60:
        return clause
    cut = clause[:61].rsplit(' ', 1)[0]
    return (cut or clause[:60]).rstrip(' ,:')


def summary(text, model, deadline):
    remaining = deadline - time.monotonic()
    if remaining > .1:
        try:
            payload = dict(model=model, stream=False, keep_alive='5m',
                prompt='Summarize this task as one short description, at most 60 characters. '
                       'Preserve intent; no commentary or extra facts. Return only the description.\n'
                       '<task>' + text[:6000] + '</task>',
                options=dict(temperature=0, num_predict=48))
            req = urllib.request.Request('http://127.0.0.1:11434/api/generate',
                json.dumps(payload).encode(), {'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=min(1.5, remaining)) as response:
                answer = json.load(response)
            value = ' '.join(answer.get('response', '').split()).strip('"')
            if value and len(value) <= 90 and answer.get('done'):
                return value, 'local model · ' + model
        except (OSError, ValueError, TimeoutError):
            pass
    return shorten(text), 'short version, no model'


def call(message):
    use, word = message['use'], message['word']
    args = message.get('args') or {}
    kv = args.get('kv') or {}
    deadline = time.monotonic() + 6.5
    if word == 'summarize.save':
        field = kv.get('field')
        if field not in ('note', 'text'):
            raise ValueError('Only note and text are editable through this adapter')
        tasks = read(use, 'rows taskboard-task')
        task = next((t for t in tasks if t['id'] == args.get('target')), None)
        if not task:
            raise ValueError('No visible task to edit')
        # lens.js TEXT.esc encodes newlines, but the kernel shlex surface
        # preserves \n. This explicit adapter is confined to painter saves.
        # A literal backslash followed by n is ambiguous here (NEEDS.md).
        text = str(kv.get('text', '')).replace('\\n', '\n')
        return dict(lines=['set '+task['id']+' '+field+'='+quote(text)],
                    saw={task['id']: task['rev']})
    if word == 'summarize.add':
        text = str(kv.get('text') or args.get('words') or '').strip()
        match = re.search(r'\s+p([1-4])$', text, re.I)
        priority = match[1] if match else '4'
        title = text[:match.start()].strip() if match else text
        if not title:
            raise ValueError('Write a task description before its optional p1–p4.')
        # Parsing is code; creation and its automatic summarization remain words.
        return dict(lines=['make kind=taskboard-task title=' + quote(title) +
            ' text="" note="" lane=Backlog priority=' + priority +
            ' colour=paper note_colour=paper note_style=normal who=' + quote(message['caller']['name']) +
            ' source=local source_status=open seats=1'], saw={})
    settings = read(use, 'rows taskboard-settings name=taskboard')
    model = str(settings[0].get('model') or 'qwen2.5:3b') if settings else 'qwen2.5:3b'
    if word == 'summarize.task':
        target = args.get('target')
        if not target:
            raise ValueError('summarize.task needs a task')
        tasks = read(use, 'rows taskboard-task')
        tasks = [t for t in tasks if t['id'] == target]
        if not tasks:
            raise ValueError('No visible task with that name')
    else:
        lane = kv.get('lane') or args.get('words', '').strip()
        target = args.get('target')
        if target:
            lanes = read(use, 'rows taskboard-lane')
            lane = next((t['name'] for t in lanes if t['id'] == target), lane)
        if lane and lane not in ('Backlog', 'Now', 'Done', 'board'):
            raise ValueError('Choose Backlog, Now, Done or board')
        tasks = read(use, 'rows taskboard-task' + (' lane=' + quote(lane) if lane and lane != 'board' else ''))
    saw = {t['id']: t['rev'] for t in tasks + settings}
    lines = []
    for task in tasks:
        text = str(task.get('title') or '')
        if task.get('text'):
            text += '\n' + str(task['text'])
        short, provenance = summary(text, model, deadline)
        defaults = dict(priority='4', colour='paper', note_colour='paper', note_style='normal')
        extra = ''.join(' '+key+'='+quote(value) for key,value in defaults.items() if key not in task)
        lines.append('set ' + task['id'] + ' short=' + quote(short) + ' short_source=' + quote(provenance) + extra)
    return dict(lines=lines, saw=saw)


def answer(message):
    try:
        result = call(message)
    except Exception as exc:
        result = dict(refused=str(exc))
    send(dict(result, t='answer', use=message['use']))


def main():
    for raw in sys.stdin:
        msg = json.loads(raw)
        t = msg.get('t')
        if t == 'hello':
            send(dict(t='offer', words=[
                dict(word='summarize.task', kind='do', takes='<id>', undo='yes',
                     help='summarize.task <task>: set short and its provenance. Local Ollama; otherwise a literal short version. Undo restores facts. Set taskboard-settings model= to choose an installed model; off summarize stops it.'),
                dict(word='summarize.all', kind='do', takes='[<id>] [lane=<name>]', undo='yes',
                     help='summarize.all [lane=Backlog|Now|Done|board]: summarize visible tasks together, one undoable act. A lane id also works. Unavailable/slow models use labelled deterministic shortening.'),
                dict(word='summarize.add', kind='do', takes='text=<text>', undo='yes',
                     help='summarize.add text="Fix the bar p1": quick-add a task, stripping an optional trailing p1–p4. Defaults to p4. A world rule supplies short in a separate act. Undo takes back the latest act; later dependent acts must be undone before creation.'),
                dict(word='summarize.save', kind='do', takes='<id> field=<note|text> text=<text>', undo='yes',
                     help='summarize.save <task> field=note|text text="…": painter multiline save adapter. Converts escaped line breaks to real lines; literal backslash-n is ambiguous on this transport (NEEDS.md). Typed task-note accepts actual newlines without this adapter. Undo restores the previous text.')]))
        elif t == 'call':
            threading.Thread(target=answer, args=(msg,), daemon=True).start()
        elif t == 'rows' and msg.get('use') in pending:
            slot = pending[msg['use']]
            slot[1] = msg
            slot[0].set()
        elif t == 'status?':
            send(dict(t='status', use=msg.get('use'), doing='Local task summaries; literal fallback; no private storage'))
        elif t == 'off':
            return


if __name__ == '__main__':
    main()
