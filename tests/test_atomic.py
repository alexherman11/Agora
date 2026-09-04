"""Failure leaves no trace: a refused verb leaves the log byte-identical and the store unchanged."""

from __future__ import annotations

from pathlib import Path

import pytest

from kernel import events, store, verbs
from kernel.verbs import VerbError


def log_bytes(world: store.Store) -> bytes:
    return world.world.log.read_bytes()


@pytest.mark.parametrize(
    "call",
    [
        lambda w, e: verbs.attach(w, "alex", e, "core.name", {"nom": "x"}),
        lambda w, e: verbs.attach(w, "alex", e, "core.name", {"name": 42}),
        lambda w, e: verbs.attach(w, "alex", e, "core.nope", {"name": "x"}),
        lambda w, e: verbs.attach(w, "alex", e, "core.text", {}),
        lambda w, e: verbs.attach(w, "alex", e, "core.text", {"path": "/no/such/file"}),
        lambda w, e: verbs.attach(w, "alex", "ent_missing", "core.name", {"name": "x"}),
        lambda w, e: verbs.attach(w, "", e, "core.name", {"name": "x"}),
        lambda w, e: verbs.mint(w, "alex", {"core.name": {"name": "x"}, "core.text": "not a dict"}),
        lambda w, e: verbs.place(w, "alex", e, "huge"),
        lambda w, e: verbs.place(w, "alex", e, "icon", {"x": "left"}),
        lambda w, e: verbs.place(w, "alex", "ent_missing"),
        lambda w, e: verbs.place(w, "alex", e, "icon", scene="ent_not_a_scene"),
        lambda w, e: verbs.read(w, "alex", e, "core.text"),
    ],
)
def test_refusal_appends_nothing(world: store.Store, call) -> None:
    entity = verbs.mint(world, "alex", {"core.name": {"name": "thing"}})
    verbs.ensure_desk(world)
    before_log, before_snap = log_bytes(world), world.snapshot()
    with pytest.raises(VerbError) as excinfo:
        call(world, entity)
    assert log_bytes(world) == before_log
    assert world.snapshot() == before_snap
    assert str(excinfo.value)  # refusals say something


def test_refusals_are_instructive(world: store.Store) -> None:
    entity = verbs.mint(world, "alex")
    with pytest.raises(VerbError, match=r"core\.name expects \{name: str, aliases\?: list\}"):
        verbs.attach(world, "alex", entity, "core.name", {"nom": "x"})
    with pytest.raises(VerbError, match="mode must be one of"):
        verbs.place(world, "alex", entity, "giant")
    with pytest.raises(VerbError, match="no entity 'ent_missing'"):
        verbs.read(world, "alex", "ent_missing")


def test_partial_mint_is_all_or_nothing(world: store.Store, tmp_path: Path) -> None:
    before = log_bytes(world)
    with pytest.raises(VerbError):
        verbs.mint(
            world, "alex", {"core.name": {"name": "ok"}, "core.file-backing": {"path": "nope"}}
        )
    assert log_bytes(world) == before
    assert world.snapshot()["entities"] == []


def test_log_refuses_bad_intents_without_writing(world: store.Store) -> None:
    before = log_bytes(world)
    with pytest.raises(events.LogError):
        events.append(world.world, "alex", "not-a-kind", {})
    with pytest.raises(events.LogError):
        events.append(world.world, "", "entity-minted", {})
    with pytest.raises(events.LogError):
        events.append(world.world, "alex", "entity-minted", {"bytes": b"\x00"})
    assert log_bytes(world) == before
