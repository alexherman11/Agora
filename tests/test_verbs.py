"""The four verbs: what they accept, what they record, and what they refuse."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from kernel import events, store, verbs
from kernel.schema import DESK
from kernel.verbs import VerbError


def test_mint_returns_a_fresh_entity_with_provenance(world: store.Store) -> None:
    a = verbs.mint(world, "alex", {"core.name": {"name": "a"}})
    b = verbs.mint(world, "jeff")
    assert a != b and a.startswith("ent_")
    assert world.entity(a).minted_by == "alex"
    assert world.entity(b).minted_by == "jeff"
    assert world.facet(a, "core.name").body == {"name": "a"}
    assert world.facets(b) == []


def test_every_event_carries_its_actor(world: store.Store) -> None:
    note = verbs.mint(world, "jeff", {"core.name": {"name": "notes"}})
    verbs.attach(world, "jeff", note, "core.text", {"text": "hi"})
    verbs.place(world, "jeff", note)
    actors = {e.actor for e in events.replay(world.world)}
    assert actors == {"jeff"}
    kinds = [e.kind for e in events.replay(world.world)]
    assert kinds == ["entity-minted", "facet-attached", "entity-minted", "appearance-placed"]


def test_attach_updates_and_bumps_revision(world: store.Store) -> None:
    note = verbs.mint(world, "alex")
    first = verbs.attach(world, "alex", note, "core.name", {"name": "draft"})
    second = verbs.attach(world, "jeff", note, "core.name", {"name": "final", "aliases": ["f"]})
    assert (first.revision, second.revision) == (1, 2)
    assert second.written_by == "jeff"
    assert world.facet(note, "core.name").body["aliases"] == ["f"]


def test_text_update_is_a_text_edited_event(world: store.Store) -> None:
    note = verbs.mint(world, "alex")
    verbs.attach(world, "alex", note, "core.text", {"text": "one"})
    verbs.attach(world, "alex", note, "core.text", {"text": "two"})
    kinds = [e.kind for e in events.replay(world.world)]
    assert kinds == ["entity-minted", "facet-attached", "text-edited"]


def test_text_import_from_file_logs_the_content(world: store.Store, notes_file: Path) -> None:
    note = verbs.mint(world, "jeff")
    record = verbs.attach(world, "jeff", note, "core.text", {"path": str(notes_file)})
    assert record.body == {"text": notes_file.read_bytes().decode("utf-8")}
    logged = list(events.replay(world.world))[-1].payload["body"]
    assert "path" not in logged and logged["text"].startswith("Buy oat milk")


def test_file_backing_records_hash_and_blob(world: store.Store, notes_file: Path) -> None:
    note = verbs.mint(world, "jeff")
    record = verbs.attach(world, "jeff", note, "core.file-backing", {"path": str(notes_file)})
    data = notes_file.read_bytes()
    assert record.body["hash"] == hashlib.sha256(data).hexdigest()
    assert record.body["size"] == len(data)
    assert events.get_blob(world.world, record.body["hash"]) == data


def test_read_returns_raw_facets(world: store.Store) -> None:
    note = verbs.mint(world, "alex", {"core.name": {"name": "n"}, "core.text": {"text": "t"}})
    everything = verbs.read(world, "jeff", note)
    assert set(everything["facets"]) == {"core.name", "core.text"}
    assert everything["facets"]["core.text"]["body"] == {"text": "t"}
    only = verbs.read(world, "jeff", note, "core.name")
    assert list(only["facets"]) == ["core.name"]
    assert only["facets"]["core.name"]["written_by"] == "alex"


def test_place_puts_an_appearance_on_the_desk(world: store.Store) -> None:
    note = verbs.mint(world, "alex")
    placed = verbs.place(world, "jeff", note, "icon", {"x": 3})
    assert placed.transform == {"x": 3, "y": 0.0, "scale": 1.0}
    [appearance] = world.appearances(DESK)
    assert appearance.entity == note and appearance.mode == "icon"
    assert world.facets(note) == []  # the entity carries no position


def test_place_again_replaces(world: store.Store) -> None:
    note = verbs.mint(world, "alex")
    other = verbs.mint(world, "alex")
    verbs.place(world, "alex", note)
    verbs.place(world, "alex", other)
    verbs.place(world, "alex", note, "full", {"x": 9, "y": 9})
    shown = world.appearances(DESK)
    assert [a.entity for a in shown] == [other, note]
    assert shown[1].mode == "full" and shown[1].transform["x"] == 9


def test_ensure_desk_is_idempotent(world: store.Store) -> None:
    assert verbs.ensure_desk(world) == DESK
    n = events.count(world.world)
    verbs.ensure_desk(world)
    verbs.ensure_desk(world, "alex")
    assert events.count(world.world) == n
    assert world.appearances(DESK) == []


def test_place_on_another_scene(world: store.Store) -> None:
    room = verbs.mint(world, "alex", {"core.scene": {"appearances": []}})
    note = verbs.mint(world, "alex")
    verbs.place(world, "alex", note, scene=room)
    assert [a.entity for a in world.appearances(room)] == [note]
    assert world.appearances(DESK) == []
    with pytest.raises(VerbError, match="not a scene"):
        verbs.place(world, "alex", note, scene=note)


def test_registry_describes_the_public_operations(world: store.Store) -> None:
    assert {v.name for v in verbs.REGISTRY} == set(verbs.VERBS)
    assert {"mint", "attach", "read", "place", "preview_lens", "activate_lens"} <= set(verbs.VERBS)
    assert {f["type"] for f in verbs.facet_types()} == {
        "core.name",
        "core.text",
        "core.file-backing",
        "core.scene",
        "core.lens",
        "core.display",
        "core.component",
        "core.component-state",
        "core.component-test",
        "core.component-admission",
    }
