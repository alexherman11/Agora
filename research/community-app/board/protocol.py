"""Small stdio module loop. Only transient requests live in process memory."""
import json
import sys
import threading

pending = {}
output_lock = threading.Lock()
hello = {}


def quote(value):
    return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"') + '"'


def line(command, target=None, **kv):
    return command + (' ' + target if target else '') + ''.join(' ' + k + '=' + quote(v) for k, v in kv.items())


def send(message):
    with output_lock:
        print(json.dumps(message, ensure_ascii=True), flush=True)


def read(use, text):
    slot = [threading.Event(), None]
    pending[use] = slot
    send(dict(t='see', use=use, line=text))
    try:
        if not slot[0].wait(8):
            raise ValueError('kernel reading timed out')
        if slot[1].get('refused'):
            raise ValueError(slot[1]['refused'])
        return slot[1].get('rows', [])
    finally:
        pending.pop(use, None)


def run(entries, call, doing, startup=None):
    def answer(message):
        try:
            result = call(message)
        except Exception as exc:
            result = dict(refused=str(exc))
        send(dict(result, t='answer', use=message['use']))
    for raw in sys.stdin:
        message = json.loads(raw)
        t = message.get('t')
        if t == 'hello':
            hello.update(message)
            if startup:
                startup(message)
            send(dict(t='offer', words=entries))
        elif t == 'call':
            threading.Thread(target=answer, args=(message,), daemon=True).start()
        elif t == 'rows' and message.get('use') in pending:
            slot = pending[message['use']]
            slot[1] = message
            slot[0].set()
        elif t == 'status?':
            send(dict(t='status', use=message.get('use'), doing=doing))
        elif t == 'off':
            return
