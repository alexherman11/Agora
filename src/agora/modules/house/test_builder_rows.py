"""Worker listings against a hidden kernel; no models, workers or native windows."""
import sys
import shutil
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
import builders
import house
from kernel.kernel import Kernel
from kernel import scratch


@pytest.fixture
def world_path():
    root = HERE.parents[3] / ".tmp"
    root.mkdir(exist_ok=True)
    path = Path(scratch.mkdtemp(prefix="builder-rows-", dir=root))
    try:
        yield path
    finally:
        assert path.resolve().parent == root.resolve()
        shutil.rmtree(path)


@pytest.fixture
def listing(world_path):
    k = Kernel(world_path / "world", {
        "tag": "dk", "name": "Worker visibility",
        "steward": {"account": "owner", "name": "Owner"},
        "invites_counted_by": "kernel", "invites": [{"code": "fixture", "uses": 2}],
    })
    owner = k.actor_for(k.accounts["owner"])
    reader = k.actor_for(k.join("reader", "Reader", invite="fixture")["person"])
    actors = {"owner": owner, "reader": reader}
    h = house.House.__new__(house.House)
    h.ready = threading.Event()
    h.ready.set()
    h.agents = {}
    h.m = SimpleNamespace(see=Mock(side_effect=lambda line, use:
                                  k.run(actors[use], line, mode="see")))
    b = builders.Builders.__new__(builders.Builders)
    b.h, b.lock, b.states, b.children = h, threading.RLock(), {}, {}
    h.builders = b
    for i in range(60):
        kind = "taskboard-task" if i % 2 == 0 else "task"
        author = reader if i % 3 == 0 else owner
        private = "sees=me" if i % 3 != 1 else ""
        out = k.run(author, f'make kind={kind} title="Repair {i}" lane=Now '
                    f'build_run=run-{i} {private}')
        assert out["ok"], out
        task = out["made"][0]
        b.states[task] = dict(task=task, name=f"Worker {i}", run=f"run-{i}",
                              phase="working", model="fixture", reasoning="medium")
    forgotten = next(iter(b.states))
    out = k.run(reader, f"look {forgotten}", mode="see")
    assert out["ok"], out
    out = k.run(reader, f"forget {forgotten}")
    assert out["ok"], out
    b.states["missing-card"] = dict(b.states[forgotten], task="missing-card")
    return k, actors, h


@pytest.mark.parametrize("use", ["reader", "owner"])
def test_bulk_visibility_matches_each_card_and_refreshes(listing, use):
    k, actors, h = listing
    expected = [h.builders.row(s) for s in h.builders.states.values()
                if k.run(actors[use], "look " + s["task"], mode="see").get("rows")]
    assert expected and len(expected) < len(h.builders.states)
    assert h.builders.rows({"use": use}) == expected
    assert [(c.args[0], c.kwargs) for c in h.m.see.call_args_list] == [
        ("rows taskboard-task", {"use": use}), ("rows task", {"use": use})]
    # A fresh call must honor a visibility change, not cache the first caller's set.
    public = next(r["id"] for r in k.run(actors["owner"], "rows taskboard-task", mode="see")["rows"]
                  if not r.get("sees") and r["made_by"] == actors["owner"].person)
    assert k.run(actors["owner"], f"look {public}", mode="see")["ok"]
    out = k.run(actors["owner"], f"forget {public}")
    assert out["ok"], out
    assert public not in {r["task"] for r in h.builders.rows({"use": "reader"})}
    assert k.run(actors["owner"], "undo")["ok"]
    assert public in {r["task"] for r in h.builders.rows({"use": "owner"})}
    assert h.builders.rows({"use": use}) == expected


@pytest.mark.parametrize("word,reads", [("house.who", 2), ("house.active", 5), ("house.board", 5)])
def test_house_listings_with_sixty_workers_are_bounded(listing, word, reads):
    _, _, h = listing
    began = time.perf_counter()
    out = h.call({"word": word, "use": "reader"})
    elapsed = time.perf_counter() - began
    assert out["rows"]
    assert elapsed < 2
    assert h.m.see.call_count == reads
    assert all(c.kwargs == {"use": "reader"} and c.args[0].startswith("rows ")
               for c in h.m.see.call_args_list)
    visible = {r["task"] for r in h.builders.rows({"use": "reader"})}
    assert {r["id"] for r in out["rows"]} <= visible
    print(f"{word}: {len(h.builders.states)} workers, {len(out['rows'])} rows, "
          f"{reads} kernel reads, {elapsed:.3f} s")


def test_internal_listing_and_empty_pool_need_no_visibility_reads(listing):
    _, _, h = listing
    assert h.builders.rows() == [h.builders.row(s) for s in h.builders.states.values()]
    h.builders.states.clear()
    assert h.builders.rows({"use": "reader"}) == []
    h.m.see.assert_not_called()


def test_refused_or_empty_queries_never_expose_workers(listing):
    _, _, h = listing
    h.m.see.side_effect = [{"ok": False, "rows": []}, {"rows": None}]
    assert h.builders.rows({"use": "reader"}) == []
    assert h.m.see.call_count == 2
