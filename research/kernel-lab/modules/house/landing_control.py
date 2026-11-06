"""Bounded, cooperative landing execution; no abandoned thread may publish later.

All landing subprocesses and lock waits pass through this control. Cancellation
unwinds the owning thread, which releases its own locks only after its child
has stopped. Network doors already have bounded timeouts.
"""
from contextlib import contextmanager
import json
import math
import os
from pathlib import Path
import subprocess
import threading
import time


class Stopped(RuntimeError):
    pass


def policy(settings):
    values = json.loads(Path(__file__).with_name('landing-defaults.json').read_text())
    for key, default in values.items():
        value = float(settings.get(key, default))
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f'{key} must be positive finite seconds')
        values[key] = value
    return values


class Control:
    def __init__(self, settings):
        self.policy = policy(settings)
        self.started = time.monotonic()
        self.deadline = self.started + self.policy['landing_timeout']
        self.cancelled = threading.Event()
        self.reason = ''
        self.unstopped = None
        self.on_child = lambda proc: None

    def cancel(self, reason):
        self.reason = reason
        self.cancelled.set()

    def check(self):
        if self.cancelled.is_set():
            raise Stopped(self.reason)
        if time.monotonic() >= self.deadline:
            raise Stopped('landing_timeout exceeded')

    @contextmanager
    def acquire(self, lock, name):
        until = min(self.deadline, time.monotonic() + self.policy['landing_wait_timeout'])
        while True:
            self.check()
            remaining = until - time.monotonic()
            if remaining <= 0:
                raise Stopped(f'landing_wait_timeout exceeded waiting for {name}')
            if lock.acquire(timeout=min(self.policy['landing_poll_interval'], remaining)):
                break
        try:
            self.check()
            yield
        finally:
            if self.unstopped is not None and self.unstopped.poll() is None:
                # An OS denial is not permission to release a lock around a child
                # that may still write. Keep only that lock fenced; the House
                # thread can settle and report the PID immediately.
                proc = self.unstopped
                def release_after_exit():
                    proc.wait()
                    lock.release()
                threading.Thread(target=release_after_exit, daemon=True).start()
            else:
                lock.release()

    def wait(self, proc, timeout):
        until = min(self.deadline, time.monotonic() + timeout)
        try:
            self.on_child(proc)
            while True:
                self.check()
                remaining = until - time.monotonic()
                if remaining <= 0:
                    raise subprocess.TimeoutExpired(proc.args, timeout)
                try:
                    return proc.wait(timeout=min(self.policy['landing_poll_interval'], remaining))
                except subprocess.TimeoutExpired:
                    pass
        except BaseException as cause:
            # Only this attempt's process tree, never a worker or live application.
            self.unstopped = proc
            if os.name == 'nt':
                result = subprocess.run(
                    ['taskkill', '/T', '/F', '/PID', str(proc.pid)],
                    stdin=subprocess.DEVNULL, capture_output=True, timeout=self.policy['landing_cleanup_timeout'],
                    creationflags=subprocess.CREATE_NO_WINDOW)
                if result.returncode and proc.poll() is None:
                    detail = (result.stderr or result.stdout or b'no diagnostic').decode('utf-8', 'replace')[:500]
                    raise RuntimeError(f'{cause}; cannot stop landing child PID {proc.pid}: {detail}; '
                                       'held locks stay fenced until it exits') from cause
            else:
                proc.kill()
            proc.wait(timeout=self.policy['landing_cleanup_timeout'])
            self.unstopped = None
            raise
        finally:
            if proc.poll() is not None:
                self.on_child(None)

    def run(self, command, *, timeout, **kwargs):
        """File-backed output only: no inherited pipe can keep completion waiting."""
        self.check()
        proc = subprocess.Popen(command, stdin=subprocess.DEVNULL, **kwargs)
        code = self.wait(proc, timeout)
        self.check()
        return subprocess.CompletedProcess(command, code)
