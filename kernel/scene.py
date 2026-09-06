"""The desk scene and its appearances: what the shell draws, as a declarative tree.
Never: never places anything (that is verbs.place), never reads a row, never positions an entity."""

from __future__ import annotations

from typing import Any

from kernel import project, schema
from kernel.locking import synchronized
from kernel.schema import Appearance
from kernel.store import Store

DESK = schema.DESK
_BUDGET = {"icon": project.TIERS[0], "summary": project.TIERS[1], "full": project.TIERS[2]}


def appearances(world: Store, scene: str = DESK) -> list[Appearance]:
    return world.appearances(scene)


@synchronized
def tree(world: Store, viewer: str = "alex", scene: str = DESK) -> dict[str, Any]:
    """The render description: nodes with labels the shell draws and never interprets."""
    revision = world.sync()
    nodes = []
    for entry in appearances(world, scene):
        label = project.render_tokens(
            project.select(world, entry.entity, viewer, "label", _BUDGET["icon"])
        )
        summary = label
        if entry.mode != "icon":
            summary = project.render_tokens(
                project.select(world, entry.entity, viewer, "summary", _BUDGET[entry.mode])
            )
        nodes.append(
            {
                "entity": entry.entity,
                "mode": entry.mode,
                "transform": dict(entry.transform),
                "label": label,
                "summary": summary,
                "lens": world.facet(entry.entity, "core.lens") is not None,
                "component": world.facet(entry.entity, "core.component") is not None,
            }
        )
    return {
        "scene": scene,
        "exists": world.entity(scene) is not None,
        "revision": revision,
        "nodes": nodes,
    }
