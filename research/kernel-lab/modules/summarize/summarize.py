"""Task-board adapter; inference delegates to the single model process.

Before registration, deterministic literal fallback keeps old boards usable.
Shared inference is model.preview, admitted here as one act.
"""
import json
import re
import sys
import threading
import time

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
    if not event.wait(9):
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
    model_words = read(use, 'rows word bound=model.preview')
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
        if model_words:
            if time.monotonic() >= deadline:
                raise ValueError('Summary batch exceeded its budget; summarize a smaller lane')
            prepared = read(use, 'model.preview ' + task['id'] + ' operation=summarize words=10')
            if not prepared or not prepared[0].get('lines'):
                raise ValueError('model did not prepare a summary')
            lines.extend(prepared[0]['lines'])
            saw.update(prepared[0]['saw'])
            short = provenance = None
        else:
            # Compatibility before model registration: no second inference path.
            short, provenance = shorten(text), 'short version, no model'
        defaults = dict(priority='4', colour='paper', note_colour='paper', note_style='normal')
        extra = ''.join(' '+key+'='+quote(value) for key,value in defaults.items() if key not in task)
        if short is not None:
            lines.append('set ' + task['id'] + ' short=' + quote(short) + ' short_source=' + quote(provenance) + extra)
        elif extra:
            lines.append('set ' + task['id'] + extra)
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
                     help='summarize.task <task>: thin adapter to model.summarize via model.preview. Set model-settings model= to choose a model. Undo restores facts. Before model registration: literal fallback. Off model stops inference; off summarize stops board adapters.'),
                dict(word='summarize.all', kind='do', takes='[<id>] [lane=<name>]', undo='yes',
                     help='summarize.all [lane=Backlog|Now|Done|board]: delegate visible tasks to model.preview, one undoable act. Per-card model quota applies. Large/slow batches refuse atomically; use a smaller lane. A lane id also works.'),
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
