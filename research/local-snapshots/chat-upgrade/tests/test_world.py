"""Journal and gateway invariants, against throwaway native worlds."""

import json

import pytest

from agora3.gateway import Gateway
from agora3.world import Refusal, World


@pytest.fixture
def gateway(tmp_path):
    return Gateway(tmp_path)


def change(id="note", revision=0, text="hello"):
    return {"id": id, "expected_revision": revision, "facets": {"core.text": {"text": text}}}


def test_replay_and_rebuild_from_journal(gateway):
    human = gateway.principal("human")
    gateway.commit(human, [change()])
    gateway.commit(human, [change(revision=1, text="revised")])
    expected = gateway.world.get("note")
    assert expected["written_by"] == "human"
    with gateway.world.connection() as db:
        db.execute("DELETE FROM objects")
        db.commit()
    assert not gateway.world.verify()["ok"]
    gateway.world.rebuild()
    assert gateway.world.get("note") == expected
    assert gateway.world.verify()["ok"]


def test_failed_batch_changes_neither_journal_nor_projection(gateway):
    actor = gateway.principal("jeff")
    gateway.commit(actor, [change()])
    before = gateway.world.query()
    with pytest.raises(Refusal, match="Stale"):
        gateway.commit(actor, [change("other"), change(revision=0)])
    assert gateway.world.query() == before
    assert gateway.world.verify()["ok"]


@pytest.mark.parametrize("bad", [True, -1, "1", 1.0, None])
def test_revision_must_be_explicit_integer(gateway, bad):
    with pytest.raises(Refusal):
        gateway.commit(gateway.principal("jeff"), [change(revision=bad)])
    assert gateway.world.query()["watermark"] == 0


def test_duplicate_change_is_not_two_writes(gateway):
    with pytest.raises(Refusal, match="at most once"):
        gateway.commit(gateway.principal("jeff"), [change(), change()])
    assert gateway.world.query()["watermark"] == 0


def test_application_schema_has_real_validation_and_generic_reads(gateway):
    actor = gateway.principal("jeff")
    schema = {
        "type": "object",
        "properties": {"score": {"type": "integer"}},
        "required": ["score"],
        "additionalProperties": False,
    }
    gateway.dispatch(actor, "schema.define", {"type": "alex.review", "schema": schema})
    gateway.commit(
        actor, [{"id": "review", "expected_revision": 0, "facets": {"alex.review": {"score": 4}}}]
    )
    with pytest.raises(Refusal, match="Schema mismatch"):
        gateway.commit(
            actor,
            [{"id": "review", "expected_revision": 1, "facets": {"alex.review": {"score": "bad"}}}],
        )
    assert gateway.world.query(["alex.review"])["items"][0]["facets"]["alex.review"] == {"score": 4}


def test_schema_never_fetches_reference(gateway):
    with pytest.raises(Refusal):
        gateway.dispatch(
            gateway.principal("jeff"),
            "schema.define",
            {"type": "alex.remote", "schema": {"$ref": "http://localhost/private"}},
        )
    assert gateway.world.query()["watermark"] == 0


def test_native_content_cannot_mint_runtime_authority(gateway):
    actor = gateway.principal("jeff")
    for object_id, facet in [("agora.package.fake", "core.text"), ("fake", "agora.installation")]:
        with pytest.raises(Refusal):
            gateway.commit(
                actor,
                [
                    {
                        "id": object_id,
                        "expected_revision": 0,
                        "facets": {facet: {"text": "approved"}},
                    }
                ],
            )
    with pytest.raises(Refusal):
        gateway.dispatch(actor, "schema.define", {"type": "core.text", "schema": {}})
    assert gateway.world.query()["watermark"] == 0


def test_pagination_is_explicit(gateway):
    gateway.commit(gateway.principal("human"), [change(f"note{i}") for i in range(4)])
    first = gateway.world.query(limit=2)
    assert not first["complete"]
    second = gateway.world.query(limit=2, after=first["next_after"])
    assert second["complete"]
    assert len({o["id"] for o in first["items"] + second["items"]}) == 4


def test_unsupported_journal_version_never_rebuilds(gateway):
    gateway.commit(gateway.principal("human"), [change()])
    with gateway.world.connection() as db:
        db.execute(
            "INSERT INTO events(version,actor,at,body) VALUES(999,'test','now',?)",
            (json.dumps({"objects": []}),),
        )
        db.commit()
    with pytest.raises(Refusal, match="Unsupported"):
        gateway.world.rebuild()
    assert gateway.world.get("note")["revision"] == 1


def test_reopening_reads_retained_native_records(gateway):
    gateway.commit(gateway.principal("human"), [change()])
    assert World(gateway.world.directory).get("note") == gateway.world.get("note")
