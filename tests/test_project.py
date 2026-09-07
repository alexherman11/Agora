"""Projection: one selection path, budgets respected, uncertainty and attribution never dropped."""

from __future__ import annotations

from pathlib import Path

from kernel import project, scene, store, verbs
from kernel.project import TIERS, render_tokens, select, tokens
from kernel.schema import DESK


def rich_note(world: store.Store, notes_file: Path) -> str:
    return verbs.mint(
        world,
        "jeff",
        {
            "core.name": {"name": "notes"},
            "core.text": {"path": str(notes_file)},
            "core.file-backing": {"path": str(notes_file)},
        },
    )


def test_unknown_entity_projects_as_unknown(world: store.Store) -> None:
    sel = select(world, "ent_nope", "alex", "context", 60)
    assert not sel.known and sel.facts == []
    assert render_tokens(sel) == "unknown entity ent_nope"


def test_name_survives_the_smallest_tier(world: store.Store, notes_file: Path) -> None:
    note = rich_note(world, notes_file)
    text = render_tokens(select(world, note, "alex", "context", TIERS[0]))
    assert text.startswith("notes (by jeff)")
    assert "+" in text  # something was omitted, and the omission is visible


def test_budget_is_respected_at_every_tier(world: store.Store, notes_file: Path) -> None:
    note = rich_note(world, notes_file)
    for tier in TIERS:
        sel = select(world, note, "alex", "context", tier)
        spent = tokens(render_tokens(sel))
        assert spent <= tier, (tier, spent)


def test_text_is_truncated_with_a_mark_not_dropped(world: store.Store) -> None:
    note = verbs.mint(
        world, "alex", {"core.name": {"name": "n"}, "core.text": {"text": "word " * 200}}
    )
    sel = select(world, note, "alex", "context", 60)
    text_fact = next(f for f in sel.facts if f.facet == "core.text")
    assert text_fact.truncated and text_fact.text.endswith("…")
    assert "core.text" not in sel.omitted


def test_attribution_names_the_writer_unless_it_is_the_viewer(world: store.Store) -> None:
    note = verbs.mint(world, "jeff", {"core.name": {"name": "n"}})
    assert render_tokens(select(world, note, "alex", "context", 60)) == "n (by jeff)"
    assert render_tokens(select(world, note, "jeff", "context", 60)) == "n"


def test_edit_shows_up_in_projection(world: store.Store) -> None:
    note = verbs.mint(world, "alex", {"core.text": {"text": "before"}})
    assert project.project(world, note, "alex", 60) == "before"
    verbs.attach(world, "alex", note, "core.text", {"text": "after the edit"})
    assert project.project(world, note, "alex", 60) == "after the edit"


def test_scene_projects_its_items_by_name(world: store.Store) -> None:
    verbs.ensure_desk(world)
    assert project.project(world, DESK, "alex", 60) == "an empty desk (by system)"
    a = verbs.mint(world, "alex", {"core.name": {"name": "alpha"}})
    b = verbs.mint(world, "alex", {"core.name": {"name": "beta"}})
    verbs.place(world, "alex", a)
    verbs.place(world, "alex", b)
    text = project.project(world, DESK, "alex", TIERS[2])
    assert text.startswith("desk with 2 items: alpha [ent_")
    assert "beta" in text


def test_tree_is_a_render_description(world: store.Store, notes_file: Path) -> None:
    empty = scene.tree(world)
    assert empty["nodes"] == [] and empty["exists"] is False
    verbs.ensure_desk(world)
    assert scene.tree(world)["exists"] is True
    note = rich_note(world, notes_file)
    verbs.place(world, "jeff", note, "summary", {"x": 40, "y": 8})
    t = scene.tree(world, viewer="alex")
    [node] = t["nodes"]
    assert node["entity"] == note and node["mode"] == "summary"
    assert node["transform"] == {"x": 40, "y": 8, "scale": 1.0}
    assert node["label"].startswith("notes")
    assert len(node["summary"]) > len(node["label"])
    assert t["revision"] == world.last_applied
