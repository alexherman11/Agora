"""Compose actual scene compilation, candidate activation and exact native actions.

Ephemeral research owner only. There is no HTTP endpoint, installed capability,
authentication or browser renderer here. Original scene actions remain printable;
only typed_actions are admitted by this bridge's invocation path.
"""

import sys
from copy import deepcopy
from pathlib import Path

ROUND5 = Path(__file__).resolve().parents[1] / "round5-bridge"
NOTATION = Path(__file__).resolve().parents[2] / "text-desk-lab" / "notation"
for directory in (ROUND5, NOTATION):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from activation import DefinitionLifecycle  # noqa: E402
from prepared_actions import Bridge, Refused  # noqa: E402


class CompilerBridge(Bridge):
    """One lock and one Desk owner across prepare, activate, offer and invoke."""

    def __init__(self, desk, definition_id):
        super().__init__(desk)
        self.definition_id = definition_id
        self._lifecycle = DefinitionLifecycle(self._desk, definition_id)
        self._action_generations = {}
        self._action_definitions = {}
        candidate = self.propose(self._desk.world.subjects[definition_id]["text"], 0)
        if not candidate["ok"]:
            raise Refused(str(candidate["errors"]))
        activated = self.activate(candidate["candidate_id"], 0)
        if not activated["ok"]:
            raise Refused(str(activated["errors"]))

    def propose(self, source, expected_active_revision):
        with self._lock:
            return self._lifecycle.propose(source, expected_active_revision)

    def activate(self, candidate_id, expected_active_revision):
        with self._lock:
            return self._lifecycle.activate(candidate_id, expected_active_revision)

    def restore(self, revision, expected_active_revision):
        with self._lock:
            return self._lifecycle.restore(revision, expected_active_revision)

    def lifecycle_state(self):
        with self._lock:
            return self._lifecycle.snapshot()

    def set_view_state(self, view_id, state):
        with self._lock:
            self._lifecycle.set_view_state(view_id, state)

    def offer(self, actor):
        with self._lock:
            semantic_frame = self._lifecycle.compile_active(actor=actor)
            frame = {
                "semantic_frame": semantic_frame,
                "frame_id": semantic_frame["frame_id"],
                "scene": deepcopy(semantic_frame["scene"]),
                "bindings": deepcopy(semantic_frame["bindings"]),
            }
            generation = self._lifecycle.activation_revision
            frame["activation_revision"] = generation
            frame["typed_actions"] = {}
            frame["action_transport"] = "typed-handles-only"
            frame["limitations"] = list(frame.get("limitations", [])) + [
                "Original scene command templates are inspection data, not invocation authority.",
                "This adapter has no installed browser or authenticated transport.",
                "Only native whole-subject rewrite and free appearance move are admitted.",
                "Active definition records are pinned compiler inputs; "
                "displayed definition text may differ from drafts.",
                "Definition drafts adopt new behavior only after deliberate activation.",
            ]
            created = []

            def bind(node):
                descriptors = []
                for action in node["acts"]:
                    try:
                        descriptor = self._prepare(actor, self.definition_id, node, action["on"])
                        handle = descriptor["handle"]
                        created.append(handle)
                        self._action_generations[handle] = generation
                        chain = deepcopy(frame["bindings"][node["key"]]["definition_chain"])
                        self._action_definitions[handle] = chain
                        descriptors.append(
                            {
                                **descriptor,
                                "on": action["on"],
                                "supported": True,
                                "activation_revision": generation,
                            }
                        )
                    except Refused as exc:
                        descriptors.append(
                            {
                                "on": action["on"],
                                "supported": False,
                                "reason": str(exc),
                            }
                        )
                if descriptors:
                    frame["typed_actions"][node["key"]] = descriptors
                for child in node["kids"]:
                    bind(child)

            try:
                bind(frame["scene"])
            except Exception:
                for handle in created:
                    self.cancel(handle)
                raise
            # Text includes the actual compiler's tree and the same admitted
            # action sidecar used by graphical consumers. No per-app describer.
            base_text = semantic_frame["inspection"]["text"]
            if not isinstance(base_text, str):
                base_text = str(base_text)
            lines = [base_text, "typed actions (the invocation contract):"]
            for key, actions in frame["typed_actions"].items():
                for action in actions:
                    if action["supported"]:
                        lines.append(
                            f"  {key}: {action['on']} -> {action['operation']} "
                            f"{action['target']} handle={action['handle']} "
                            f"inputs={action['inputs']} activation={generation}"
                        )
                    else:
                        lines.append(f"  {key}: {action['on']} unsupported: {action['reason']}")
            frame["text"] = "\n".join(lines)
            return frame

    def inspect(self, handle):
        with self._lock:
            result = super().inspect(handle)
            generation = self._action_generations.get(handle)
            if generation is not None:
                result["activation_revision"] = generation
                result["active"] = generation == self._lifecycle.activation_revision
            return result

    def invoke(self, actor, handle, inputs):
        with self._lock:
            generation = self._action_generations.get(handle)
            if generation is None:
                raise Refused("Unknown, cancelled or consumed action")
            if generation != self._lifecycle.activation_revision:
                raise Refused("Active definition changed since this action was offered")
            # All active definition records are pinned by the lifecycle. Draft
            # edits do not change their meaning; activation_revision is the guard.
            result = super().invoke(actor, handle, inputs)
            self._action_generations.pop(handle, None)
            self._action_definitions.pop(handle, None)
            self._lifecycle.set_desk(self._desk)
            return result

    def cancel(self, handle):
        with self._lock:
            super().cancel(handle)
            self._action_generations.pop(handle, None)
            self._action_definitions.pop(handle, None)

    def release_frame(self, frame):
        """Explicitly discard offered handles when its owning view closes."""
        with self._lock:
            for actions in frame.get("typed_actions", {}).values():
                for action in actions:
                    if action.get("supported"):
                        self.cancel(action["handle"])

    def action_state(self):
        with self._lock:
            return deepcopy(self._action_generations)
