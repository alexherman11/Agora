"""References survive change: anchors follow edits above and inside them, and never lie."""

from __future__ import annotations

from kernel import events, store, verbs
from kernel.text import Locator, TextDoc


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def note_with(world: store.Store, text: str) -> str:
    return verbs.mint(world, "alex", {"core.text": {"text": text}})


def test_anchor_survives_an_edit_above(world: store.Store) -> None:
    doc = TextDoc(world, "alex", note_with(world, "hello world"))
    anchor = doc.anchor(6, 11)
    doc.insert(0, "well, ")
    found = doc.resolve(anchor)
    assert (found.start, found.end, found.exact) == (12, 17, True)
    assert doc.plaintext()[found.start : found.end] == "world"


def test_anchor_survives_an_edit_inside(world: store.Store) -> None:
    doc = TextDoc(world, "alex", note_with(world, "hello world"))
    anchor = doc.anchor(6, 11)
    doc.insert(8, "XX")
    found = doc.resolve(anchor)
    assert found.live and not found.exact
    assert doc.plaintext()[found.start : found.end] == "woXXrld"


def test_anchor_survives_a_deletion_above(world: store.Store) -> None:
    doc = TextDoc(world, "alex", note_with(world, "hello world"))
    anchor = doc.anchor(6, 11)
    doc.delete(0, 6)
    found = doc.resolve(anchor)
    assert (found.start, found.end, found.exact) == (0, 5, True)


def test_deleted_range_resolves_to_its_recorded_revision(world: store.Store) -> None:
    entity = note_with(world, "hello world")
    doc = TextDoc(world, "alex", entity)
    anchor = doc.anchor(6, 11)
    assert anchor.revision == 1
    doc.delete(5, 6)
    found = doc.resolve(anchor)
    assert not found.live and found.revision == 1  # never a wrong place


def test_anchor_round_trips_through_the_log(world: store.Store) -> None:
    entity = note_with(world, "hello world")
    doc = TextDoc(world, "alex", entity)
    anchor = doc.anchor(6, 11)
    doc.insert(0, "oh, ")
    doc.close()
    again = TextDoc(world, "alex", entity)  # reopened from the logged snapshot
    found = again.resolve(Locator.from_dict(anchor.to_dict()))
    assert (found.start, found.end, found.exact) == (10, 15, True)
    assert again.plaintext() == "oh, hello world"


def test_a_burst_is_one_event(world: store.Store) -> None:
    clock = Clock()
    entity = note_with(world, "")
    doc = TextDoc(world, "alex", entity, clock=clock)
    before = events.count(world.world)
    for word in "the log records decisions not motion".split():
        doc.insert(len(doc.plaintext()), word + " ")
        clock.now += 0.5
        assert doc.tick() is None
    assert events.count(world.world) == before  # keystrokes are not events
    clock.now += 3.0
    record = doc.tick()
    assert record is not None and record.revision == 2
    assert events.count(world.world) == before + 1
    assert list(events.replay(world.world))[-1].kind == "text-edited"
    assert world.facet(entity, "core.text").body["text"] == "the log records decisions not motion "


def test_a_large_delta_flushes_early(world: store.Store) -> None:
    clock = Clock()
    doc = TextDoc(world, "alex", note_with(world, ""), clock=clock, burst=100)
    before = events.count(world.world)
    doc.insert(0, "x" * 60)
    assert events.count(world.world) == before
    doc.insert(0, "y" * 60)
    assert events.count(world.world) == before + 1
    assert not doc.dirty


def test_plain_attach_after_a_snapshot_wins(world: store.Store) -> None:
    entity = note_with(world, "first")
    doc = TextDoc(world, "alex", entity)
    doc.insert(5, " draft")
    doc.close()
    verbs.attach(world, "jeff", entity, "core.text", {"text": "rewritten"})
    assert TextDoc(world, "alex", entity).plaintext() == "rewritten"


def test_rebuild_still_matches_after_text_edits(world: store.Store) -> None:
    doc = TextDoc(world, "alex", note_with(world, "abc"))
    doc.insert(3, "def")
    doc.close()
    assert store.rebuild(world.world).snapshot() == world.snapshot()
