"""Axiom 1: truth derives the present. rebuild(world) == world.store, always."""

from __future__ import annotations

from pathlib import Path

from kernel import events, store, verbs


def populate(world: store.Store, notes_file: Path) -> str:
    note = verbs.mint(world, "alex", {"core.name": {"name": "notes"}})
    verbs.attach(world, "alex", note, "core.text", {"path": str(notes_file)})
    verbs.attach(world, "alex", note, "core.file-backing", {"path": str(notes_file)})
    verbs.attach(world, "jeff", note, "core.text", {"text": "Buy oat milk.\n"})
    verbs.place(world, "jeff", note, "icon", {"x": 10, "y": 20})
    verbs.place(world, "alex", note, "summary")
    return note


def test_rebuild_equals_store(world: store.Store, notes_file: Path) -> None:
    populate(world, notes_file)
    assert store.rebuild(world.world).snapshot() == world.snapshot()


def test_rebuild_is_empty_for_an_empty_world(world: store.Store) -> None:
    assert store.rebuild(world.world).snapshot() == world.snapshot()
    assert world.snapshot()["entities"] == []


def test_store_survives_restart(world_path: Path, notes_file: Path) -> None:
    first = verbs.open_world(world_path)
    populate(first, notes_file)
    before = first.snapshot()
    first.close()
    again = verbs.open_world(world_path)
    assert again.snapshot() == before


def test_world_returns_from_the_log_alone(world_path: Path, notes_file: Path) -> None:
    first = verbs.open_world(world_path)
    note = populate(first, notes_file)
    before = first.snapshot()
    first.close()
    (world_path / "store.db").unlink()
    again = verbs.open_world(world_path)
    assert again.snapshot() == before
    assert again.facet(note, "core.text").revision == 2
    assert [a.mode for a in again.appearances("ent_desk")] == ["summary"]


def test_boot_replays_only_the_tail(world_path: Path, notes_file: Path) -> None:
    first = verbs.open_world(world_path)
    populate(first, notes_file)
    assert first.sync() == events.count(first.world)
    verbs.mint(first, "alex")
    assert first.last_applied == events.count(first.world) - 1  # not yet read, not yet applied
    second = store.open_store(first.world)  # a second store over the same db and log
    assert second.last_applied == events.count(first.world)
    assert first.sync() == second.sync() == events.count(first.world)


def test_revisions_and_writers_are_derived_from_order(world: store.Store, notes_file: Path) -> None:
    note = populate(world, notes_file)
    text = world.facet(note, "core.text")
    assert text.revision == 2 and text.written_by == "jeff"
    scene = world.facet("ent_desk", "core.scene")
    assert scene.revision == 3 and scene.written_by == "alex"  # minted, placed, placed


def test_torn_tail_is_skipped_and_sealed(world: store.Store) -> None:
    verbs.mint(world, "alex")
    with open(world.world.log, "ab") as handle:
        handle.write(b'{"id":"evt_torn","ts":1.0,"actor":"alex","kind":"entity-min')
    assert events.count(world.world) == 1
    verbs.mint(world, "alex")
    assert events.count(world.world) == 2
    assert [e.seq for e in events.replay(world.world)] == [1, 3]  # the torn line keeps its seq
    assert store.rebuild(world.world).snapshot() == world.snapshot()
    assert len(world.world.log.read_bytes().split(b"\n")) == 4  # three lines, sealed
