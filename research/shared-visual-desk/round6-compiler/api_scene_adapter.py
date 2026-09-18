"""Offered handles over the current /api/scene packet, with retained capture.

This is an in-memory server integration adapter, not an HTTP proxy. The server
must own the Desk, capture and offer under one lock, then expose only handles and
typed input. No caller-supplied scene can mint authority. No live state is loaded.
"""

import json
import sys
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

BASE = Path(__file__).resolve().parents[1]
for path in (BASE / "round5-bridge", BASE.parent / "text-desk-lab" / "notation"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
from frame_contract import (  # noqa: E402
    SCENE_PATH,
    _CompilationDesk,
    _load_actual_compiler,
    _source_hashes,
    dependency_signature,
)
from prepared_actions import Bridge, Refused  # noqa: E402


def _digest(value):
    return sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()
    ).hexdigest()


class ScenePacketBridge(Bridge):
    def __init__(self, desk):
        super().__init__(desk)
        self._captures = {}
        self._guards = {}

    def capture(self, actor, lens_name):
        """Equivalent to server-side /api/scene capture; return a defensive copy."""
        with self._lock:
            if len(self._captures) >= 16:
                raise Refused("Capture budget reached; release old captures")
            desk = deepcopy(self._desk)
            desk.world.me = actor
            source = SCENE_PATH.read_bytes()
            compiler_hashes = _source_hashes()
            if sha256(source).hexdigest() != compiler_hashes["scene_sha256"]:
                raise Refused("Compiler changed while capturing")
            compiler = _load_actual_compiler(source)
            compilation_desk = _CompilationDesk(desk)
            tree, text = compiler.scene_for(compilation_desk, lens_name)
            packet = {"scene": tree, "text": text, "events_total": len(desk.world.events)}
            if compiler_hashes != _source_hashes():
                raise Refused("Compiler changed while capturing")
            # Last-good is a derived cache, retained in this research owner.
            self._desk._lens_good = deepcopy(getattr(compilation_desk, "_lens_good", {}))
            capture_id = uuid4().hex
            self._captures[capture_id] = {
                "actor": actor,
                "packet": deepcopy(packet),
                "digest": _digest(packet),
                "dependencies": dependency_signature(self._desk),
                "compiler": compiler_hashes,
            }
            return {"capture_id": capture_id, "packet": deepcopy(packet)}

    def offer_from_owner(self, desk, actor, lens_name):
        """Host seam: caller holds the actual session lock; no second world owner.

        Retain this adapter's handle store between requests, but replace its Desk
        reference with the freshly locked authoritative Desk on EVERY request.
        The returned packet is an offer, never a durable world mutation.
        """
        with self._lock:
            if desk.rules or desk.hooks or desk.follow:
                raise Refused("Native staging requires no rules, external hooks or clock following")
            self._desk = desk
            capture = self.capture(actor, lens_name)
            return self.offer_capture(actor, capture["capture_id"])

    def invoke_on_owner(self, desk, actor, handle, inputs):
        """Return (new_desk, receipt) for the host's existing atomic commit path.

        Caller holds its session lock through rebind, invocation and saving the
        returned Desk. Refusal never applies the staged candidate. Disk failure,
        crash recovery, external effects and authentication are not modeled here.
        """
        with self._lock:
            if desk.rules or desk.hooks or desk.follow:
                raise Refused("Native staging requires no rules, external hooks or clock following")
            self._desk = desk
            receipt = self.invoke(actor, handle, inputs)
            return self._desk, receipt

    def release_capture(self, capture_id):
        with self._lock:
            self._captures.pop(capture_id, None)

    def offer_capture(self, actor, capture_id, packet=None):
        with self._lock:
            capture = self._captures.get(capture_id)
            if capture is None:
                raise Refused("Unknown or consumed server capture")
            if capture["actor"] != actor:
                raise Refused("Capture belongs to another actor label")
            if packet is not None and _digest(packet) != capture["digest"]:
                raise Refused("Echoed packet differs from the retained server capture")
            if capture["dependencies"] != dependency_signature(self._desk):
                raise Refused("World changed between capture and offer; capture again")
            if capture["compiler"] != _source_hashes():
                raise Refused("Compiler changed between capture and offer")
            packet = deepcopy(capture["packet"])
            tree = packet["scene"]
            definition = tree.get("def")
            if tree.get("broken") or not definition:
                raise Refused("Fallback or missing definition provenance: no actions offered")
            current = self._desk.world.subjects.get(definition.get("id"))
            if not current or current["rev"] != definition.get("rev"):
                raise Refused("Packet definition generation is unavailable")
            chains, joins = {}, []
            typed, created = {}, []

            def definition_record(s):
                return {
                    "id": s["id"],
                    "revision": s["rev"],
                    "source_sha256": sha256(s["text"].encode()).hexdigest(),
                }

            outer = [definition_record(current)]
            # Current packets do not fully declare these native bindings. They
            # are exact server-side joins, openly listed, not client assertions.
            joins.extend(
                [
                    "subject identity/revision from owned world appearance.subject",
                    "parent identity/revision and parent-local coordinates from owned world",
                    "operation and input schema from two exact admitted native templates",
                    "nested definition identity resolved by actual compiler find_lens",
                ]
            )
            compiler = _load_actual_compiler(SCENE_PATH.read_bytes())

            def walk(node, chain):
                chains[node["key"]] = deepcopy(chain)
                descriptors = []
                for action in node.get("acts", []):
                    try:
                        d = self._prepare(actor, definition["id"], node, action["on"])
                        created.append(d["handle"])
                        self._guards[d["handle"]] = {
                            "definitions": deepcopy(chain),
                            "compiler": capture["compiler"],
                        }
                        descriptors.append(
                            {
                                **d,
                                "on": action["on"],
                                "supported": True,
                                "definitions": deepcopy(chain),
                            }
                        )
                    except Refused as exc:
                        descriptors.append(
                            {"on": action["on"], "supported": False, "reason": str(exc)}
                        )
                if descriptors:
                    typed[node["key"]] = descriptors
                inner_name = node.get("lens")
                for child in node.get("kids", []):
                    child_chain = chain
                    if inner_name and child["key"] == node["key"] + "/lens:" + inner_name:
                        inner = compiler.find_lens(self._desk, inner_name)
                        child_chain = chain + [definition_record(inner)]
                    walk(child, child_chain)

            try:
                walk(tree, outer)
                if capture["compiler"] != _source_hashes():
                    raise Refused("Compiler changed while binding the offered actions")
            except Exception:
                for handle in created:
                    self.cancel(handle)
                raise
            del self._captures[capture_id]
            return {
                "packet": packet,
                "typed_actions": typed,
                "definition_chains": chains,
                "joins": joins,
                "limitations": [
                    "No HTTP endpoint or authentication installed.",
                    "Raw command lines remain inspection data only.",
                    "Only whole-subject rewrite and free appearance move admitted.",
                ],
            }

    def invoke(self, actor, handle, inputs):
        with self._lock:
            guard = self._guards.get(handle)
            if not guard:
                raise Refused("Unknown, cancelled or consumed action")
            if guard["compiler"] != _source_hashes():
                raise Refused("Compiler or style changed since the action was offered")
            for definition in guard["definitions"]:
                current = self._desk.world.subjects.get(definition["id"])
                if (
                    not current
                    or current["rev"] != definition["revision"]
                    or sha256(current["text"].encode()).hexdigest() != definition["source_sha256"]
                ):
                    raise Refused("Composed definition changed since the action was offered")
            result = super().invoke(actor, handle, inputs)
            self._guards.pop(handle, None)
            return result

    def cancel(self, handle):
        with self._lock:
            super().cancel(handle)
            self._guards.pop(handle, None)
