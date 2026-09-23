"""Durable revocation and schema admission stay correct across gateway instances."""

import multiprocessing

import pytest

from agora3.gateway import Gateway
from agora3.locking import ProcessLock
from agora3.world import Refusal


def change(name="note"):
    return [{"id": name, "expected_revision": 0, "facets": {"core.text": {"text": "hello"}}}]


def _writer_waiting_for_revoke(directory, connection):
    gateway = Gateway(directory)
    actor = gateway.principal("guest")
    connection.send("ready")
    connection.recv()
    try:
        gateway.commit(actor, change("child-note"))
    except Refusal:
        connection.send("refused")
    else:
        connection.send("committed")
    connection.close()


def _lock_waiter(path, connection):
    connection.send("ready")
    with ProcessLock(path, timeout=5):
        connection.send("acquired")
    connection.close()


def test_second_gateway_reads_revocation_and_rotation(tmp_path):
    one, two = Gateway(tmp_path), Gateway(tmp_path)
    before = two.keep
    actor = two.principal("guest")
    one.revoke()
    assert two.keep["generation"] == before["generation"] + 1
    assert two.keep["guest"] != before["guest"]
    with pytest.raises(Refusal, match="stopped or replaced"):
        two.commit(actor, change())
    assert two.world.query()["items"] == []
    one.resume()
    with pytest.raises(Refusal, match="stopped or replaced"):
        two.commit(actor, change())
    two.commit(two.principal("guest"), change())
    assert one.world.get("note")["revision"] == 1


def test_keep_snapshot_is_not_an_authority_mutation(tmp_path):
    gateway = Gateway(tmp_path)
    snapshot = gateway.keep
    snapshot["enabled"] = False
    assert gateway.keep["enabled"] is True


def test_authentication_uses_rotated_token_and_preserves_operator_recovery(tmp_path):
    one, two = Gateway(tmp_path), Gateway(tmp_path)
    old_keep = one.keep
    actor = two.authenticate(old_keep["guest"])
    assert actor.name == "guest"
    one.revoke()
    with pytest.raises(Refusal, match="authenticated"):
        two.authenticate(old_keep["guest"])
    operator = two.authenticate(old_keep["operator"], operator=True, name="human")
    assert operator.name == "human"
    assert operator.generation == one.keep["generation"]
    with pytest.raises(Refusal, match="stopped or replaced"):
        two.commit(operator, change())
    with pytest.raises(Refusal, match="authenticated"):
        two.authenticate(None)


def test_authentication_never_rebinds_old_token_to_later_generation(tmp_path, monkeypatch):
    one, two = Gateway(tmp_path), Gateway(tmp_path)
    token, generation = one.keep["guest"], one.keep["generation"]

    def interrupted_comparison(value, expected):
        # A same-thread reentrant hook stands in for the old split-auth race.
        one.revoke()
        return value == expected

    monkeypatch.setattr("agora3.gateway.secrets.compare_digest", interrupted_comparison)
    actor = two.authenticate(token)
    assert actor.generation == generation
    with pytest.raises(Refusal, match="stopped or replaced"):
        two.commit(actor, change())


def test_running_other_process_observes_revoke(tmp_path):
    gateway = Gateway(tmp_path)
    context = multiprocessing.get_context("spawn")
    parent, child = context.Pipe()
    process = context.Process(target=_writer_waiting_for_revoke, args=(str(tmp_path), child))
    process.start()
    child.close()
    try:
        assert parent.poll(10), "child did not initialize"
        assert parent.recv() == "ready"
        gateway.revoke()
        parent.send("try-write")
        assert parent.poll(10), "child did not return"
        assert parent.recv() == "refused"
        process.join(10)
        assert process.exitcode == 0
        assert gateway.world.query()["items"] == []
    finally:
        if process.is_alive():
            process.terminate()
            process.join(5)
        parent.close()


def test_file_lock_serializes_another_process_and_is_reentrant(tmp_path):
    path = str(tmp_path / ".authority.lock")
    context = multiprocessing.get_context("spawn")
    parent, child = context.Pipe()
    process = context.Process(target=_lock_waiter, args=(path, child))
    try:
        with ProcessLock(path):
            with ProcessLock(path):
                process.start()
                child.close()
                assert parent.poll(10), "child did not start"
                assert parent.recv() == "ready"
                assert not parent.poll(0.2), "child acquired a held lock"
        assert parent.poll(10), "child did not acquire the released lock"
        assert parent.recv() == "acquired"
        process.join(10)
        assert process.exitcode == 0
    finally:
        if process.is_alive():
            process.terminate()
            process.join(5)
        parent.close()


def test_nested_failure_releases_shared_lock(tmp_path):
    first, second = ProcessLock(tmp_path / "lock"), ProcessLock(tmp_path / "lock")
    with pytest.raises(ValueError):
        with first, second:
            raise ValueError("test failure")
    with second, first:
        pass


def test_schema_evolution_rejects_changed_snapshot(tmp_path, monkeypatch):
    first, second = Gateway(tmp_path), Gateway(tmp_path)
    one, two = first.principal("human"), second.principal("human")
    first.define_schema(one, type="alex.question", schema={"type": "string"})
    first.commit(
        one, [{"id": "a", "expected_revision": 0, "facets": {"alex.question": "long enough value"}}]
    )
    original = first.world.query

    def changed_query(*args, **kwargs):
        snapshot = original(*args, **kwargs)
        # Reentrant simulation of a writer between snapshot and schema admission.
        second.commit(two, [{"id": "b", "expected_revision": 0, "facets": {"alex.question": "x"}}])
        return snapshot

    monkeypatch.setattr(first.world, "query", changed_query)
    with pytest.raises(Refusal, match="snapshot is stale"):
        first.define_schema(
            one,
            type="alex.question",
            expected_revision=1,
            schema={"type": "string", "minLength": 10},
        )
    assert second.world.get("agora.schema.alex.question")["revision"] == 1
    assert second.world.get("b")["facets"]["alex.question"] == "x"
    assert second.world.verify()["ok"] is True
