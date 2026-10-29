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
