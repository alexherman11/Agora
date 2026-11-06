"""Completed slow kernel-lock waits and holds; diagnostics beside, never in, the world.

The fast path only clocks and tracks the outer acquisition. Stack inspection and
file writes happen only for slow events, and writes happen after releasing the
kernel lock. No command arguments, titles, sessions or exception text are kept.
"""
from collections import deque
from datetime import datetime, timezone
import json
import sys
import threading
import time

THRESHOLD = 0.300
KEEP = 50


class SlowLog:
    def __init__(self, path):
        self.path = path
        self._lock = threading.Lock()
        self._disk = threading.Lock()
        self._rows = deque(maxlen=KEEP)
        self.write_errors = 0
        self._needs_separator = False
        try:
            with path.open(encoding="utf-8") as stream:
                for line in stream:
                    self._needs_separator = not line.endswith("\n")
                    try:
                        row = json.loads(line)
                        if isinstance(row, dict):
                            self._rows.append(row)
                    except ValueError:
                        continue  # tolerate a partial last line after a crash
        except OSError:
            pass

    def keep(self, row):
        with self._disk:
            with self._lock:
                self._rows.append(row)
            # Separate locks: a reading of the ring never waits for disk IO.
            try:
                with self.path.open("a", encoding="utf-8") as stream:
                    stream.write(("\n" if self._needs_separator else "") +
                                 json.dumps(row, ensure_ascii=True) + "\n")
                self._needs_separator = False
            except OSError:
                self._needs_separator = True  # a failed write may have left a partial line
                with self._lock:
                    self.write_errors += 1

    def snapshot(self):
        with self._lock:
            return list(reversed(self._rows)), self.write_errors


def _context(frame, lineno):
    """Inspect only slow acquisitions. Whitelist identity/word fields, not lines."""
    result = dict(word=frame.f_code.co_name, module=None, caller=None,
                  file=frame.f_code.co_filename, line=lineno)
    found_word = False
    while frame:
        local = frame.f_locals
        st = local.get("st")
        word = getattr(st, "word", None) or local.get("word")
        entry = local.get("entry")
        if not word and isinstance(entry, dict):
            word = entry.get("word")
        if not word and frame.f_code.co_name in ("run", "_run", "module_see", "outside_line"):
            # These entry points can take the lock before parsing a Step. Keep
            # only the command word, never the rest of their incoming line.
            line = local.get("line")
            parts = line.split(None, 2) if isinstance(line, str) else []
            if parts:
                word = parts[1] if parts[0] == "do" and len(parts) > 1 else parts[0]
        if not found_word and isinstance(word, str):
            result["word"], found_word = word, True
        actor = local.get("actor") or local.get("author")
        module = getattr(actor, "module", None) or local.get("mid")
        caller = getattr(actor, "caller", None) or local.get("caller") or actor
        if result["module"] is None and isinstance(module, str):
            result["module"] = module
        identity = getattr(caller, "id", None)
        if result["caller"] is None and isinstance(identity, str):
            result["caller"] = identity
        if frame.f_code.co_name == "verb_note" and st is not None:
            result["verb"] = st.word
        frame = frame.f_back
    return result


class TimedRLock:
    """RLock semantics; time one outer hold, not every nested reentry.

    Waits name the holder observed when acquisition began (other threads may win
    the lock in between). Events are emitted on release, not a live stack sampler.
    """
    def __init__(self, log):
        self._lock = threading.RLock()
        self._local = threading.local()
        self._holder = None
        self.log = log

    def acquire(self, blocking=True, timeout=-1):
        return self._acquire(blocking, timeout, sys._getframe(1))

    def __enter__(self):
        self._acquire(True, -1, sys._getframe(1))
        return self

    def _acquire(self, blocking, timeout, frame):
        start = time.perf_counter()
        holder = self._holder
        acquired = self._lock.acquire(blocking, timeout)
        end = time.perf_counter()
        wait = end - start
        if not acquired:
            if wait > THRESHOLD:
                self._emit(self._event("wait", wait, frame, frame.f_lineno, holder, acquired=False))
            return False
        depth = getattr(self._local, "depth", 0)
        self._local.depth = depth + 1
        if depth == 0:
            self._local.start = end
            self._local.frame = frame
            self._local.line = frame.f_lineno
            self._holder = (frame, frame.f_lineno, threading.get_ident())
            self._local.wait = (
                self._event("wait", wait, frame, frame.f_lineno, holder, acquired=True)
                if wait > THRESHOLD else None)
        return True

    def release(self):
        depth = getattr(self._local, "depth", 0)
        if depth != 1:
            self._lock.release()  # preserve RLock's error for a non-owner
            self._local.depth = depth - 1
            return
        duration = time.perf_counter() - self._local.start
        frame, lineno, wait = self._local.frame, self._local.line, self._local.wait
        self._local.depth = 0
        self._local.frame = self._local.wait = None
        self._holder = None
        self._lock.release()
        if wait:
            self._emit(wait)
        if duration > THRESHOLD:
            self._emit(self._event("hold", duration, frame, lineno))

    def __exit__(self, *exc):
        self.release()

    def _is_owned(self):
        return self._lock._is_owned()

    def _event(self, kind, duration, frame, lineno, holder=None, **extra):
        row = dict(kind=kind, duration_ms=round(duration * 1000, 3),
                   at=datetime.now(timezone.utc).isoformat(),
                   thread=threading.get_ident(), word=frame.f_code.co_name,
                   module=None, caller=None, file=frame.f_code.co_filename, line=lineno, **extra)
        try:
            row.update(_context(frame, lineno))
            if holder is not None:
                frame, lineno, thread = holder
                row["holder_at_wait_start"] = dict(thread=thread, **_context(frame, lineno))
        except Exception as exc:
            row["context_error"] = type(exc).__name__
        return row

    def _emit(self, row):
        try:
            self.log.keep(row)
        except Exception:
            pass  # diagnostics must never turn a successful act into an error


def slow(k, actor, st, entry, tx, group, saw=None):
    from .kernel import Refused
    if not (k.is_steward(actor.person) or k.is_steward(actor.id)):
        raise Refused("kernel.slow is for stewards")
    rows, errors = k.slow.snapshot()
    lines = []
    for r in rows:
        text = (f"{r['at']} {r['kind']} {r['duration_ms']:.3f} ms: {r['word']} "
                f"module={r.get('module') or '-'} caller={r.get('caller') or '-'} "
                f"({r['file']}:{r['line']})")
        if r.get("verb"):
            text += f" verb={r['verb']}"
        holder = r.get("holder_at_wait_start")
        if holder:
            text += (f"; holder at wait start: {holder['word']} "
                     f"module={holder.get('module') or '-'} caller={holder.get('caller') or '-'}")
        lines.append(text)
    text = "\n".join(lines)
    if errors:
        text += f"\n{errors} log writes failed; events remain in memory."
    return dict(text=text or "no completed kernel lock waits or holds over 300 ms", rows=rows,
                write_errors=errors)
