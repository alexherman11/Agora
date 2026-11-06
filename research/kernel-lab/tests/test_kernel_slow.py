"""Slow-lock diagnostics, with isolated files and no live kernel or processes."""
import json
from pathlib import Path
import sys
import threading
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kernel import scratch
from kernel.kernel import Actor, Kernel, Refused
from kernel import slow


@pytest.fixture
def folder():
    with scratch.TemporaryDirectory(prefix="kernel-slow-test-") as path:
        yield Path(path)


@pytest.fixture
def clock(monkeypatch):
    now = [0.0]
    monkeypatch.setattr(slow.time, "perf_counter", lambda: now[0])
    return now


def test_fast_and_recursive_acquisitions_do_not_inspect_or_write(folder, clock, monkeypatch):
    log = slow.SlowLog(folder / "slow.jsonl")
    lock = slow.TimedRLock(log)
    monkeypatch.setattr(slow, "_context", lambda *args: pytest.fail("fast stack inspection"))
    with lock:
        with lock:
            clock[0] = .300
    assert log.snapshot() == ([], 0)
    assert not log.path.exists()
    assert lock._local.frame is None and lock._holder is None


def test_outer_hold_survives_recursion_and_exception_and_keeps_only_identity(folder, clock):
    log = slow.SlowLog(folder / "slow.jsonl")
    lock = slow.TimedRLock(log)
    actor = Actor("module-id", "person-id", "module", module="module-id",
                  caller=Actor("agent-id", "person-id", "agent"))
    st = SimpleNamespace(word="rows", text="rows secret-title", kv={"secret": "never-log-this"})
    with pytest.raises(ValueError):
        with lock:
            clock[0] = .2
            with lock:
                clock[0] = .4
            clock[0] = .6
            raise ValueError("private exception")
    rows, errors = log.snapshot()
    assert len(rows) == 1 and not errors
    row = rows[0]
    assert (row["kind"], row["word"], row["module"], row["caller"], row["duration_ms"]) == (
        "hold", st.word, actor.module, "agent-id", 600)
    assert row["file"] == __file__ and row["line"] > 0
    assert "secret" not in log.path.read_text() and "private" not in log.path.read_text()
    assert not lock._is_owned()
    with lock:
        pass
    assert len(log.snapshot()[0]) == 1


def test_announcement_without_actor_has_word_and_module(folder, clock):
    log = slow.SlowLog(folder / "slow.jsonl")
    lock = slow.TimedRLock(log)

    def announce(mid, word):
        with lock:
            clock[0] += .5

    announce("test-module", "test.changed")
    row = log.snapshot()[0][0]
    assert (row["word"], row["module"], row["caller"]) == ("test.changed", "test-module", None)


def test_lock_before_parsing_records_only_command_word(folder, clock):
    log = slow.SlowLog(folder / "slow.jsonl")
    lock = slow.TimedRLock(log)

    def _run(actor, line):
        with lock:
            clock[0] += .5

    _run(Actor("agent-id", "person-id", "agent"), 'do look "private-title"')
    row = log.snapshot()[0][0]
    assert row["word"] == "look" and row["caller"] == "agent-id"
    assert "private-title" not in log.path.read_text()


def test_verb_context_is_kept_alongside_inner_word(folder, clock):
    log = slow.SlowLog(folder / "slow.jsonl")
    lock = slow.TimedRLock(log)

    def step(st):
        with lock:
            clock[0] += .5

    def verb_note(st):
        step(SimpleNamespace(word="look"))

    verb_note(SimpleNamespace(word="test.read"))
    row = log.snapshot()[0][0]
    assert row["word"] == "look" and row["verb"] == "test.read"


def test_contended_wait_names_waiter_and_observed_holder(folder):
    log = slow.SlowLog(folder / "slow.jsonl")
    lock = slow.TimedRLock(log)
    ready = threading.Event()
    attempted = threading.Event()
    errors = []

    def hold():
        word, mid = "test.changed", "test-module"
        try:
            with lock:
                ready.set()
                assert attempted.wait(2)
                threading.Event().wait(.4)
        except BaseException as exc:
            errors.append(exc)

    thread = threading.Thread(target=hold)
    thread.start()
    try:
        assert ready.wait(2)
        st = SimpleNamespace(word="rows")
        actor = Actor("agent-id", "person-id", "agent")
        attempted.set()
        with lock:
            pass
    finally:
        thread.join(2)
    assert not thread.is_alive() and not errors
    rows, _ = log.snapshot()
    wait = next(r for r in rows if r["kind"] == "wait")
    hold = next(r for r in rows if r["kind"] == "hold")
    assert wait["duration_ms"] > 300 and wait["acquired"]
    assert wait["word"] == st.word and wait["caller"] == actor.id
    assert wait["holder_at_wait_start"]["module"] == "test-module"
    assert wait["holder_at_wait_start"]["word"] == "test.changed"
    assert wait["holder_at_wait_start"]["thread"] == hold["thread"]


def test_timed_out_wait_and_nonblocking_failure_preserve_lock_ownership(folder):
    log = slow.SlowLog(folder / "slow.jsonl")
    lock = slow.TimedRLock(log)
    ready, finish = threading.Event(), threading.Event()

    def owner():
        with lock:
            ready.set()
            finish.wait(3)

    thread = threading.Thread(target=owner)
    thread.start()
    try:
        assert ready.wait(2)
        assert not lock.acquire(False)
        assert not lock.acquire(timeout=.35)
        with pytest.raises(RuntimeError):
            lock.release()
        wait = log.snapshot()[0][0]
        assert wait["kind"] == "wait" and not wait["acquired"] and wait["duration_ms"] > 300
        assert thread.is_alive()
    finally:
        finish.set()
        thread.join(2)
    assert lock.acquire(False)
    lock.release()


def test_logging_is_outside_kernel_lock(folder, clock, monkeypatch):
    log = slow.SlowLog(folder / "slow.jsonl")
    lock = slow.TimedRLock(log)
    original = log.keep
    owned = []

    def keep(row):
        owned.append(lock._is_owned())
        original(row)

    monkeypatch.setattr(log, "keep", keep)
    with lock:
        clock[0] = .5
    assert owned == [False]


def test_ring_is_bounded_and_append_log_survives_reopening(folder):
    path = folder / "slow.jsonl"
    log = slow.SlowLog(path)
    for n in range(75):
        log.keep(dict(n=n))
    rows, _ = log.snapshot()
    assert [r["n"] for r in rows] == list(range(74, 24, -1))
    assert len(path.read_text().splitlines()) == 75
    assert slow.SlowLog(path).snapshot()[0] == rows
    with path.open("a") as stream:
        stream.write('{"cut_short":')
    reopened = slow.SlowLog(path)
    assert reopened.snapshot()[0] == rows
    reopened.keep(dict(n=75))
    assert slow.SlowLog(path).snapshot()[0] == [dict(n=75)] + rows[:-1]


def test_disk_failure_retains_ring_and_reports_failure_without_breaking_act(folder, clock):
    log = slow.SlowLog(folder / "missing-directory" / "slow.jsonl")
    lock = slow.TimedRLock(log)
    with lock:
        clock[0] = .5
    rows, errors = log.snapshot()
    assert len(rows) == 1 and errors == 1 and not lock._is_owned()


def test_ring_read_does_not_need_disk_lock(folder):
    log = slow.SlowLog(folder / "slow.jsonl")
    with log._disk:
        assert log.snapshot() == ([], 0)


def test_diagnostic_sink_failure_does_not_change_success(folder, clock, monkeypatch):
    log = slow.SlowLog(folder / "slow.jsonl")
    lock = slow.TimedRLock(log)
    monkeypatch.setattr(log, "keep", lambda row: (_ for _ in ()).throw(ValueError("broken log")))
    with lock:
        clock[0] = .5
    assert not lock._is_owned()


def test_context_failure_still_records_location_without_changing_success(folder, clock, monkeypatch):
    log = slow.SlowLog(folder / "slow.jsonl")
    lock = slow.TimedRLock(log)
    monkeypatch.setattr(slow, "_context", lambda *args: (_ for _ in ()).throw(ValueError("private")))
    with lock:
        clock[0] = .5
    row = log.snapshot()[0][0]
    assert row["context_error"] == "ValueError" and row["file"] == __file__
    assert not lock._is_owned() and "private" not in log.path.read_text()


def test_reading_and_help_are_registered_and_reading_never_writes_world(folder, monkeypatch):
    k = Kernel(folder, {"tag": "ts", "name": "Test", "steward": {"account": "test", "name": "Test"}})
    person = next(p for p in k.things("person") if k.is_steward(p))
    actor = Actor(person, person, "person")
    assert "300 ms" in k.step(actor, "help kernel.slow", mode="see")["text"]
    assert k.step(actor, "kernel.slow", mode="see")["rows"] == []
    assert k.entry(k.find_entry("kernel.slow", None))["may"] == "stewards"
    seq = len(k.log.records)
    # Exercise the actual Kernel.step lock with deterministic slow timing.
    ticks = iter([0.0, 0.0, .5])
    monkeypatch.setattr(slow.time, "perf_counter", lambda: next(ticks))
    k.step(actor, "clock", mode="see")
    monkeypatch.undo()
    row = k.step(actor, "kernel.slow", mode="see")["rows"][0]
    assert row["word"] == "clock" and row["caller"] == person
    assert row["file"].endswith("kernel.py") and row["duration_ms"] == 500
    assert len(k.log.records) == seq
    assert json.loads(k.slow.path.read_text().splitlines()[-1]) == row
    with pytest.raises(Refused):
        slow.slow(k, Actor("outsider", "outsider", "person"), None, None, None, None)
