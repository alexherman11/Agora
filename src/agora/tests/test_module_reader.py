"""A module's reader thread ends cleanly when `stop` closes its pipe under it (seen in the desktop's log at every
restart, 28 Oct): it used to die with "I/O operation on closed file" before waking the calls still waiting, so they
waited out the whole call timeout. No process is started."""
import sys
import threading
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kernel.modules import ModuleProcess  # noqa: E402


class ClosedUnderUs:
    def __iter__(self):
        raise ValueError("I/O operation on closed file.")


def test_a_closed_pipe_wakes_every_waiting_call():
    p = ModuleProcess.__new__(ModuleProcess)
    p.proc = SimpleNamespace(stdout=ClosedUnderUs(), stderr=ClosedUnderUs(), pid=0)
    p.stdout_closed = threading.Event()
    waiting = threading.Event()
    p.pending = {"u1": {"event": waiting, "answer": None, "caller": None}}
    p.err = []
    p._read()
    assert p.stdout_closed.is_set() and waiting.is_set()


def test_accepted_call_keeps_the_callers_reading_context_until_late_answer():
    p = ModuleProcess.__new__(ModuleProcess)
    caller = object()
    seen = []
    p.mid = "fixture"
    p.host = SimpleNamespace(kernel=SimpleNamespace(
        module_see=lambda mid, who, line: seen.append((mid, who, line)) or {"rows": []}))
    p.pending = {}
    messages = []
    def send(msg):
        messages.append(msg)
        if msg["t"] == "call":
            p.handle({"t": "accepted", "use": msg["use"]})
    p.send = send
    answer = p.ask({"t": "call", "word": "fixture.start"}, .01, caller=caller)
    assert answer["external"] and "starting" in answer["text"]
    use = answer["use"]
    p._see(p.pending[use]["caller"], {"use": use, "line": "look fixture"})
    assert seen == [("fixture", caller, "look fixture")]
    # A late answer closes the context. Its lines cannot become a second act.
    p.handle({"t": "answer", "use": use, "lines": ["make kind=fixture"]})
    assert not p.pending


def test_an_accepted_fast_call_returns_the_final_receipt_and_releases_context():
    p = ModuleProcess.__new__(ModuleProcess)
    p.host = SimpleNamespace(kernel=SimpleNamespace())
    p.pending = {}
    def send(msg):
        p.handle({"t": "accepted", "use": msg["use"]})
        p.handle({"t": "answer", "use": msg["use"], "text": "recorded", "external": True})
    p.send = send
    assert p.ask({"t": "call"}, .01)["text"] == "recorded"
    assert not p.pending
