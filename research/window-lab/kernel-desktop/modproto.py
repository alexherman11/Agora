"""modproto: the module protocol (SHAPE 11) for a module written in Python. Newline JSON on stdin and stdout.

    m = Module(offer=[...words...], on_call=fn, on_happen=fn, on_status=fn)
    m.run_reader()             reads the kernel's messages on a thread
    m.see(line, use=None)      a reading: inside a call (use given) as the caller, else on the module's own grants
    m.do(line, saw=None)       an act on the module's own grants (SHAPE 6: a module acting on its own)
    m.happen(word, target)     announce a happening of the module's namespace (delivered, not recorded)
    m.hold(word)               ask for a hold (a lease on a surface); m.release(lease) ends it

stdout belongs to the protocol: a module prints its own notes to stderr, which the kernel keeps in <world>/logs/.
"""
import json
import sys
import threading
import uuid


def log(*a):
    print(*a, file=sys.stderr, flush=True)


class Module:
    def __init__(self, offer, on_call, on_happen=None, on_status=None, on_hello=None, on_off=None):
        self.offer, self.on_call, self.on_happen = offer, on_call, on_happen
        self.on_status, self.on_hello, self.on_off = on_status, on_hello, on_off
        self.hello = {}
        self.out_lock = threading.Lock()
        self.waiting = {}                 # id or use -> [event, answer]
        self.ready = threading.Event()
        self.closed = threading.Event()

    def send(self, msg):
        with self.out_lock:
            try:
                sys.stdout.write(json.dumps(msg) + "\n")
                sys.stdout.flush()
            except (OSError, ValueError):
                self.closed.set()

    def _ask(self, key, msg, timeout):
        slot = [threading.Event(), None]
        self.waiting[key] = slot
        self.send(msg)
        slot[0].wait(timeout)
        self.waiting.pop(key, None)
        return slot[1] or {"ok": False, "refused": "the kernel did not answer", "rows": [], "text": ""}

    def see(self, line, use=None, timeout=12):
        if use:
            return self._ask(use, {"t": "see", "use": use, "line": line}, timeout)
        i = uuid.uuid4().hex[:10]
        return self._ask(i, {"t": "see", "id": i, "line": line}, timeout)

    def do(self, line, saw=None, timeout=12):
        i = uuid.uuid4().hex[:10]
        return self._ask(i, {"t": "do", "id": i, "line": line, **({"saw": saw} if saw is not None else {})}, timeout)

    def hold(self, word, timeout=12):
        """Ask the kernel for a hold (SHAPE 5): -> {lease} or {refused}."""
        use = uuid.uuid4().hex[:10]
        return self._ask(use, {"t": "hold", "use": use, "word": word}, timeout)

    def release(self, lease):
        self.send({"t": "release", "lease": lease})

    def happen(self, word, target=None, text=""):
        self.send({"t": "happen", "word": word, "target": target, "text": text})

    def _handle(self, msg):
        t = msg.get("t")
        if t == "hello":
            self.hello = msg
            if self.on_hello:
                self.on_hello(msg)
            self.send({"t": "offer", "words": self.offer})
            self.ready.set()
        elif t == "refused":
            log(f"the kernel refused: {msg}")
        elif t in ("rows", "done", "held"):
            slot = self.waiting.get(msg.get("id")) or self.waiting.get(msg.get("use"))
            if slot:
                slot[1] = msg
                slot[0].set()
        elif t == "call":
            def answer():
                try:
                    out = self.on_call(msg)
                except Exception as exc:                  # a module's mistake is a refusal, never silence
                    log(f"call {msg.get('word')} failed: {exc!r}")
                    out = {"refused": f"{msg.get('word')} failed inside the module: {exc}"}
                self.send(dict(out, t="answer", use=msg.get("use")))
            threading.Thread(target=answer, daemon=True).start()
        elif t == "status?":
            doing = self.on_status() if self.on_status else "running"
            self.send({"t": "status", "use": msg.get("use"), "doing": doing})
        elif t == "happen":
            if self.on_happen:
                threading.Thread(target=self.on_happen, args=(msg,), daemon=True).start()
        elif t == "off":
            self.closed.set()
            if self.on_off:
                self.on_off()

    def _read(self):
        for line in sys.stdin:
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            try:
                self._handle(msg)
            except Exception as exc:
                log(f"message {msg.get('t')} failed: {exc!r}")
        self.closed.set()                                 # stdin closed: the kernel is gone, so the module goes too
        if self.on_off:
            self.on_off()

    def run_reader(self):
        threading.Thread(target=self._read, daemon=True, name="protocol").start()
