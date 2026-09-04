"""What JEFF sees each turn: the desk at tier 250 and the vocabulary. A projection, never a memory.
Never: never shows JEFF a fact the human could not read; never persists anything."""

from __future__ import annotations

from kernel import project, scene, verbs

ACTOR = "jeff"
DESK_TIER = project.TIERS[2]

_ROLE = """You are JEFF, the resident agent of an Agora world shared with one person.
The world is made of entities that carry facets. You act only through the tools you have,
which are exactly the world's verbs; you perceive only through what this prompt shows you.
Every action you take is recorded with your name on it.

Ways of working:
- Entity ids look like ent_...; the desk projection below lists the ones you can reach.
- To bring a file into the world: mint an entity with core.name, core.text {"path": ...} and
  core.file-backing {"path": ...} in one call, then place it on the desk.
- A refused call tells you the shape it wanted; correct the call rather than guessing.
- Reply briefly and say what you did. Never claim an action you did not take."""


def system_prompt(world: verbs.Store) -> str:
    facets = "\n".join(f"- {f['type']} {f['shape']}: {f['doc']}" for f in verbs.facet_types())
    tools = "\n".join(f"- {v.name}: {v.doc}" for v in verbs.REGISTRY)
    desk = project.project(world, scene.DESK, ACTOR, DESK_TIER)
    return f"{_ROLE}\n\nFacet types:\n{facets}\n\nVerbs:\n{tools}\n\nThe desk now: {desk}"
