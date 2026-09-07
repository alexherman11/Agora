"""Regression invariants from the holistic review, exercised only in temporary worlds."""

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest

from kernel import events, project, scene, store, verbs
from kernel.text import TextDoc


def test_processes_share_the_world_lock(world):
    code = """
import sys
from kernel import verbs
world = verbs.open_world(sys.argv[1])
for i in range(12):
    verbs.mint(world, 'test-process', {'core.text': {'text': str(i)}})
world.close()
"""
    workers = [
        subprocess.Popen([sys.executable, "-c", code, str(world.world.path)]) for _ in range(4)
    ]
    try:
        assert [worker.wait(timeout=30) for worker in workers] == [0] * 4
    finally:
        for worker in workers:
            if worker.poll() is None:
                worker.kill()
                worker.wait()
    assert len(world.snapshot()["entities"]) == 48
    with_rebuild(world)


def test_historical_scenes_include_placement_revisions(world):
    desk = verbs.ensure_desk(world)
    first = verbs.mint(world, "alex")
    second = verbs.mint(world, "jeff")
    verbs.place(world, "alex", first)
    retained = world.facet(desk, "core.scene")
    verbs.place(world, "jeff", second)
    assert world.historical(desk, "core.scene", retained.revision) == retained
    current = world.facet(desk, "core.scene")
    assert world.historical(desk, "core.scene", current.revision) == current


def test_rebuild_cannot_replace_world_truth(world):
    verbs.mint(world, "alex")
    before = world.world.log.read_bytes()
    with pytest.raises(ValueError, match="cache file"):
        store.rebuild(world.world, world.world.log)
    assert world.world.log.read_bytes() == before


def test_malformed_committed_payload_is_reported_as_corruption(world):
    verbs.mint(world, "alex")
    event = json.loads(world.world.log.read_text())
    event["payload"]["facets"] = []
    world.world.log.write_text(json.dumps(event) + "\n")
    with pytest.raises(events.LogError, match="facets must map"):
        store.rebuild(world.world)


def test_multiple_handles_and_threads_apply_each_event_once(world):
    other = store.open_store(world.world)

    def work(i):
        handle = world if i % 2 else other
        entity = verbs.mint(handle, "alex", {"core.text": {"text": str(i)}})
        assert handle.facet(entity, "core.text").revision == 1
        return entity

    try:
        with ThreadPoolExecutor(max_workers=8) as pool:
            ids = list(pool.map(work, range(32)))
        assert len(set(ids)) == 32
        with_rebuild(world)
    finally:
        other.close()


def with_rebuild(world):
    rebuilt = store.rebuild(world.world)
    try:
        assert world.snapshot() == rebuilt.snapshot()
    finally:
        rebuilt.close()


def test_duplicate_apply_is_idempotent(world):
    entity = verbs.mint(world, "alex", {"core.text": {"text": "one"}})
    world.sync()
    store.apply(world._db, list(events.replay(world.world))[-1])
    assert world.facet(entity, "core.text").revision == 1
    with_rebuild(world)


def test_current_and_reopened_reads_do_not_decode_the_old_log(world):
    entity = verbs.mint(world, "alex", {"core.text": {"text": "one"}})
    world.sync()
    with patch.object(events, "_decode", side_effect=AssertionError("read the old log")):
        assert world.facet(entity, "core.text").body["text"] == "one"
        other = store.open_store(world.world)
        other.close()


def test_stale_text_flush_refuses_without_losing_either_edit(world):
    entity = verbs.mint(world, "alex", {"core.text": {"text": "hello"}})
    a, b = TextDoc(world, "alex", entity), TextDoc(world, "jeff", entity)
    a.insert(0, "A ")
    b.insert(5, " B")
    a.flush()
    before = world.world.log.read_bytes()
    with pytest.raises(verbs.VerbError, match="stale"):
        b.flush()
    assert world.world.log.read_bytes() == before
    assert b.dirty and b.plaintext() == "hello B"
    assert world.facet(entity, "core.text").body["text"] == "A hello"
    with_rebuild(world)


def test_anchor_identity_survives_reopen_without_an_edit(world):
    entity = verbs.mint(world, "alex", {"core.text": {"text": "hello world"}})
    doc = TextDoc(world, "alex", entity)
    anchor = doc.anchor(6, 11)
    doc.close()
    reopened = TextDoc(world, "alex", entity)
    assert reopened.resolve(anchor).exact
    verbs.attach(world, "alex", entity, "core.text", {"text": "replacement"})
    found = TextDoc(world, "alex", entity).resolve(anchor)
    assert not found.live and found.revision == anchor.revision
    assert (
        verbs.read(world, "alex", entity, "core.text", anchor.revision)["facets"]["core.text"][
            "body"
        ]["text"]
        == "hello world"
    )


def test_scene_cycles_are_finite_and_names_and_wire_budgets_survive(world):
    desk = verbs.ensure_desk(world)
    verbs.place(world, "alex", desk, "full")
    assert scene.tree(world)["nodes"]
    assert project.project(world, desk)
    entity = verbs.mint(
        world, "jeff", {"core.name": {"name": "n" * 100}, "core.text": {"text": "word " * 100}}
    )
    assert project.render_tokens(project.select(world, entity, "alex", "label", 12))
    for budget in (1, 2, 12, 60, 250):
        assert project.tokens(project.project(world, entity, "alex", budget)) <= budget


def test_invalid_place_never_initializes_a_desk(world):
    entity = verbs.mint(world, "alex")
    before = world.world.log.read_bytes()
    with pytest.raises(verbs.VerbError):
        verbs.place(world, "alex", entity, mode="bad")
    assert world.world.log.read_bytes() == before
    assert world.entity("ent_desk") is None


@pytest.mark.parametrize("value", [float("nan"), float("inf"), True])
def test_invalid_coordinates_do_not_initialize_the_desk(world, value):
    entity = verbs.mint(world, "alex")
    before = world.world.log.read_bytes()
    with pytest.raises(verbs.VerbError, match="finite numbers"):
        verbs.place(world, "alex", entity, transform={"x": value})
    assert world.world.log.read_bytes() == before
    assert world.entity("ent_desk") is None


def test_placement_respects_the_same_scene_limit_as_attachment(world):
    desk = verbs.ensure_desk(world)
    refs = [{"entity": f"reference-{i}"} for i in range(1000)]
    verbs.attach(world, "alex", desk, "core.scene", {"appearances": refs})
    entity = verbs.mint(world, "alex")
    before = world.world.log.read_bytes()
    with pytest.raises(verbs.VerbError, match="1000"):
        verbs.place(world, "alex", entity)
    assert world.world.log.read_bytes() == before


def test_import_limits_authority_and_failed_mint_leave_no_blobs(world, notes_file):
    world.import_roots = ()
    with pytest.raises(verbs.VerbError, match="authorized"):
        verbs.mint(world, "jeff", {"core.text": {"path": str(notes_file)}})
    world.import_roots = (notes_file,)
    before = world.world.log.read_bytes()
    with pytest.raises(verbs.VerbError):
        verbs.mint(
            world,
            "jeff",
            {"core.file-backing": {"path": str(notes_file)}, "core.name": {"name": 123}},
        )
    assert not list(world.world.blobs.iterdir())
    notes_file.write_text("x" * 1_000_001)
    with pytest.raises(verbs.VerbError, match="limited"):
        verbs.mint(world, "jeff", {"core.text": {"path": str(notes_file)}})
    assert world.world.log.read_bytes() == before


def test_corruption_is_not_a_torn_tail_and_failed_rebuild_preserves_destination(world, tmp_path):
    for name in ("one", "two", "three"):
        verbs.mint(world, "alex", {"core.name": {"name": name}})
    target = tmp_path / "previous.db"
    target.write_bytes(b"previous cache must survive")
    lines = world.world.log.read_bytes().splitlines(keepends=True)
    lines[1] = b"damaged committed record\n"
    world.world.log.write_bytes(b"".join(lines))
    with pytest.raises(events.LogError, match="line 2"):
        store.rebuild(world.world, target)
    assert target.read_bytes() == b"previous cache must survive"


def test_torn_multibyte_tail_recovers_without_rewriting_history(world):
    verbs.mint(world, "alex")
    with world.world.log.open("ab") as handle:
        handle.write(b'{"text":"\xe2')
    prefix = world.world.log.read_bytes()
    assert events.count(world.world) == 1
    verbs.mint(world, "alex")
    assert events.count(world.world) == 2
    assert world.world.log.read_bytes().startswith(prefix)
    with_rebuild(world)


def test_incomplete_sealing_append_does_not_acknowledge_a_record(world):
    verbs.mint(world, "alex")
    with world.world.log.open("ab") as handle:
        handle.write(b'{"torn":')
    verbs.mint(world, "alex")
    world.world.log.write_bytes(world.world.log.read_bytes()[:-1])
    with pytest.raises(events.LogError, match="preserve the log"):
        list(events.replay(world.world))
