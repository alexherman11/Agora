"""Prepared-action bridge experiment over the existing experimental Desk.

No HTTP endpoint, authentication, persistence, new world or renderer. A compiler
adapter supplies an already resolved scene node; this module accepts only two
existing action templates. It never executes arbitrary command text.
"""

import math
import re
from copy import deepcopy
from dataclasses import dataclass
from threading import RLock
from uuid import uuid4


class Refused(ValueError):
    pass


@dataclass(frozen=True)
class Prepared:
    actor: str
    definition: str
    definition_revision: int
    node_key: str
    target: str
    expected_revision: int
    appearance: str | None
    parent: str | None
    parent_revision: int | None
    verb: str


class Bridge:
    """Single in-process owner; callers must not retain/mutate its internal desk."""

    def __init__(self, desk):
        if desk.rules or desk.hooks or desk.follow:
            raise Refused("Staging experiment requires no rules, external hooks or clock following")
        self._desk = deepcopy(desk)
        self._lock = RLock()
        self._prepared = {}

    def snapshot(self):
        with self._lock:
            return deepcopy(self._desk.snapshot())

    def inspect(self, handle):
        with self._lock:
            p = self._prepared.get(handle)
            if p is None:
                raise Refused("Unknown, consumed or expired action")
            fields = (
                {"value": "exact string"}
                if p.verb == "rewrite"
                else {"x": "finite number", "y": "finite number"}
            )
            return {
                "handle": handle,
                "actor": p.actor,
                "node": p.node_key,
                "definition": {"id": p.definition, "revision": p.definition_revision},
                "operation": p.verb,
                "target": p.target,
                "appearance": p.appearance,
                "expected_revision": p.expected_revision,
                "inputs": fields,
                "coordinate_frame": (
                    {
                        "parent": p.parent,
                        "expected_revision": p.parent_revision,
                        "units": "parent-local world pixels",
                        "input_requirement": "already transformed using the offered frame",
                    }
                    if p.parent
                    else None
                ),
            }

    def _prepare(self, actor, definition_id, node, gesture):
        """Compile one actual Claude scene action into a retained typed binding.

        This is a HOST compiler adapter, not an API that accepts browser-supplied
        node/action definitions. The caller must pass the scene it just compiled
        from the same authoritative snapshot. Tests exercise that exact path.
        """
        with self._lock:
            if len(self._prepared) >= 128:
                raise Refused("Outstanding action budget reached; cancel old frames")
            w = self._desk.world
            definition = w.subjects.get(definition_id)
            if not definition or "lens" not in definition.get("tags", []):
                raise Refused("Definition must be an existing lens subject")
            acts = [a for a in node["acts"] if a["on"] == gesture]
            if len(acts) != 1:
                raise Refused("Exactly one action for this gesture required")
            line = acts[0]["line"]
            rewrite = re.fullmatch(r'do rewrite ([as]\d+) text="\$value"', line)
            move = re.fullmatch(r"do move (a\d+) to=\$x,\$y", line)
            if gesture == "edit" and rewrite:
                raw = rewrite[1]
                appearance = raw if raw in w.nodes else node.get("item")
                target = w.nodes[raw]["subject"] if raw in w.nodes else raw
                if target not in w.subjects:
                    raise Refused("Missing subject")
                if appearance and w.nodes.get(appearance, {}).get("subject") != target:
                    raise Refused("Scene occurrence does not bind this subject")
                expected, parent, parent_revision, verb = (
                    w.subjects[target]["rev"],
                    None,
                    None,
                    "rewrite",
                )
            elif gesture == "drag" and move:
                target = move[1]
                n = w.nodes.get(target)
                if not n or node.get("item") != target or n.get("type") != "appearance":
                    raise Refused("Drag needs the exact scene appearance")
                appearance, expected, parent, verb = target, n["rev"], n["parent"], "move"
                if w.nodes[parent]["layout"] != "free":
                    raise Refused("This adapter only supports free-space movement")
                parent_revision = w.nodes[parent]["rev"]
            else:
                raise Refused("Unsupported action template; never fall back to command evaluation")
            handle = uuid4().hex
            self._prepared[handle] = Prepared(
                actor,
                definition_id,
                definition["rev"],
                node["key"],
                target,
                expected,
                appearance,
                parent,
                parent_revision,
                verb,
            )
            return self.inspect(handle)

    def cancel(self, handle):
        with self._lock:
            self._prepared.pop(handle, None)

    def invoke(self, actor, handle, inputs):
        with self._lock:
            p = self._prepared.get(handle)
            if p is None:
                raise Refused("Unknown, consumed or expired action")
            if actor != p.actor:
                raise Refused("Action belongs to another actor label (not authentication)")
            if not isinstance(inputs, dict):
                raise Refused("Inputs must be an object")
            if p.verb == "rewrite":
                if set(inputs) != {"value"} or not isinstance(inputs["value"], str):
                    raise Refused("Exactly one string value required")
                if len(inputs["value"]) > 32000:
                    raise Refused("Text input budget exceeded")
                args = {"text": inputs["value"]}  # Empty/quotes/newlines/backslashes stay literal.
            else:
                if set(inputs) != {"x", "y"} or any(
                    isinstance(v, bool)
                    or not isinstance(v, (int, float))
                    or not math.isfinite(v)
                    or not 0 <= v <= 100000
                    for v in inputs.values()
                ):
                    raise Refused("Exactly two bounded finite coordinates required")
                args = {"to": f"{inputs['x']},{inputs['y']}"}
            w = self._desk.world
            definition = w.subjects.get(p.definition)
            if not definition or definition["rev"] != p.definition_revision:
                raise Refused("Definition changed since this scene was offered")
            records = w.subjects if p.verb == "rewrite" else w.nodes
            if p.target not in records or records[p.target]["rev"] != p.expected_revision:
                recent = next(
                    (
                        e
                        for e in reversed(w.events)
                        if e.get("target") == p.target or p.target in e.get("changed", [])
                    ),
                    None,
                )
                why = f"; latest {recent['id']} by {recent['by']}" if recent else ""
                raise Refused("Target changed since this scene was offered" + why)
            if p.appearance:
                n = w.nodes.get(p.appearance)
                if not n or (p.verb == "rewrite" and n.get("subject") != p.target):
                    raise Refused("Scene occurrence was removed or rebound")
            if p.parent and (
                w.nodes[p.appearance]["parent"] != p.parent
                or w.nodes.get(p.parent, {}).get("rev") != p.parent_revision
            ):
                raise Refused("Drag coordinate frame changed")
            # Staging is valid only for this in-memory desk's native operations.
            # External-effect handlers are NOT admitted by these two templates.
            candidate = deepcopy(self._desk)
            candidate.world.me = actor
            # Restore the revision captured when offered, never do a fresh look.
            candidate.seen = {p.target: p.expected_revision}
            before = len(candidate.world.events)
            result = candidate.dispatch("do", {"verb": p.verb, "target": p.target, "args": args})
            if result.get("error"):
                raise Refused(result["error"])
            events = deepcopy(candidate.world.events[before:])
            self._desk = candidate
            del self._prepared[handle]
            return {
                "receipt": result["text"],
                "events": events,
                "node": p.node_key,
                "definition": p.definition,
                "operation": p.verb,
                "target": p.target,
            }

    def offer(self, actor, definition_id):
        """Compile and bind one frame under the SAME owner lock.

        Existing Claude compiler bounds are a known gap: only finite fixture
        definitions are exercised. This is not an untrusted production loader.
        """
        import scene

        with self._lock:
            desk = deepcopy(self._desk)
            desk.world.me = actor
            definition = desk.world.subjects[definition_id]
            tree = scene.build(desk, definition["text"])
            started = set(self._prepared)
            unsupported = []

            def bind(node):
                bound = []
                for action in node["acts"]:
                    try:
                        descriptor = self._prepare(actor, definition_id, node, action["on"])
                        bound.append({"on": action["on"], "supported": True, **descriptor})
                    except Refused as exc:
                        bound.append({"on": action["on"], "supported": False, "reason": str(exc)})
                        unsupported.append({"node": node["key"], "reason": str(exc)})
                node["acts"] = bound
                for child in node["kids"]:
                    bind(child)

            try:
                bind(tree)
            except Exception:
                for handle in set(self._prepared) - started:
                    del self._prepared[handle]
                raise
            return {
                "scene": tree,
                "definition": definition_id,
                "definition_revision": definition["rev"],
                "world_revision": len(desk.world.events),
                "unsupported": unsupported,
            }
