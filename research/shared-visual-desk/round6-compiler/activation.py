"""In-memory candidate/active lifecycle around the actual scene frame compiler.

The caller owns the Desk and holds its lock across each operation. No world mutation,
durable authority, renderer, parser or package installer is introduced here.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
from typing import Callable


@dataclass(frozen=True)
class _Candidate:
    candidate_id: str
    source: str
    source_hash: str
    base_revision: int
    frame: dict
    definitions: dict


class DefinitionLifecycle:
    def __init__(self, desk, definition_id: str, *, compiler: Callable | None = None,
                 checker: Callable | None = None):
        from frame_contract import compile_frame, check_frame
        self._desk = desk
        self.definition_id = definition_id
        self._compiler = compiler or compile_frame
        self._checker = checker or check_frame
        self._revision = 0
        self._active = None
        self._history = {}
        self._candidates = {}
        self._next_candidate = 1
        self._views = {}

    def set_desk(self, desk):
        """Rebind the caller's owner after an atomic Desk swap; never copy authority."""
        self._desk = desk

    @property
    def activation_revision(self):
        return self._revision

    @property
    def active_source(self):
        return self._active.source if self._active else None

    @property
    def active_frame(self):
        return deepcopy(self._active.frame) if self._active else None

    @property
    def active_definition_records(self):
        return deepcopy(self._active.definitions) if self._active else {}

    def compile_active(self, actor=None):
        """Compile current material through the retained active definition closure.

        Only a disposable snapshot receives the pinned records. The authoritative
        Desk is untouched. Definition records displayed as material consequently
        show the pinned edition here; candidate source needs its own editor view.
        Frame dependencies describe this explicit compilation snapshot, not a
        claim that the authoritative current definition records are identical.
        """
        if self._active is None:
            raise ValueError("no active definition")
        snapshot = deepcopy(self._desk)
        for definition_id, record in self._active.definitions.items():
            snapshot.world.subjects[definition_id] = deepcopy(record)
        frame = self._compiler(snapshot, self.definition_id, source=self._active.source, actor=actor)
        reached = {definition["id"] for definition in frame["definitions"]}
        if reached - self._active.definitions.keys():
            raise ValueError("active projection reached an unpinned definition; preview and activate again")
        return frame

    @property
    def view_states(self):
        return deepcopy(self._views)

    def set_view_state(self, view_id: str, state):
        if not isinstance(view_id, str) or not view_id:
            raise ValueError("view_id must be a nonempty string")
        self._views[view_id] = deepcopy(state)

    def snapshot(self):
        return {"activation_revision": self._revision, "definition_id": self.definition_id,
                "active_source": self.active_source, "active_frame": self.active_frame,
                "active_definition_records": self.active_definition_records,
                "view_states": self.view_states, "historical_revisions": sorted(self._history)}

    def _failure(self, *errors, diagnostics=None):
        messages = [str(e) for e in errors]
        return {"ok": False, "errors": messages,
                "diagnostics": deepcopy(diagnostics) if diagnostics else [{"code": "activation-refused", "message": message} for message in messages],
                "activation_revision": self._revision}

    def _base_error(self, expected):
        if type(expected) is not int or expected < 0:
            return "expected_active_revision must be a nonnegative integer"
        if expected != self._revision:
            return f"stale activation revision: expected {expected}; active is {self._revision}"
        return None

    def propose(self, source: str, expected_active_revision: int):
        """Compile a retained candidate. Returned previews are defensive copies.

        compiler(desk, definition_id, source=...) returns a frame or raises.
        Injected compilers must be read-only. This is an in-process contract,
        not a sandbox for arbitrary Python or a rollback of external effects.
        """
        if error := self._base_error(expected_active_revision):
            return self._failure(error)
        if not isinstance(source, str):
            return self._failure("source must be text")
        try:
            frame = self._compiler(self._desk, self.definition_id, source=source)
            # check both sides of compilation, including wrapper dependencies.
            validity = self._checker(self._desk, frame)
            if not validity.get("ok"):
                return self._failure(*validity.get("reasons", ["candidate frame is stale"]), diagnostics=validity.get("diagnostics"))
            definitions = {}
            for identity in frame.get("definitions", []):
                definition_id = identity["id"]
                record = deepcopy(self._desk.world.subjects.get(definition_id))
                if not record or record["rev"] != identity["revision"]:
                    return self._failure("definition closure changed during candidate capture")
                if definition_id == self.definition_id:
                    record["text"] = source
                if sha256(record["text"].encode()).hexdigest() != identity["source_sha256"]:
                    return self._failure("definition closure source does not match compiled candidate")
                definitions[definition_id] = record
            if self.definition_id not in definitions:
                return self._failure("candidate frame omitted the root definition closure")
            frame = deepcopy(frame)
        except Exception as exc:
            return self._failure(f"candidate refused: {type(exc).__name__}: {exc}", diagnostics=getattr(exc, "diagnostics", None))
        if error := self._base_error(expected_active_revision):
            return self._failure(error)
        candidate_id = f"candidate-{self._next_candidate}"
        self._next_candidate += 1
        candidate = _Candidate(candidate_id, source, sha256(source.encode()).hexdigest(),
                               self._revision, frame, definitions)
        self._candidates[candidate_id] = candidate
        return {"ok": True, "errors": [], "candidate_id": candidate_id,
                "base_revision": candidate.base_revision, "source_sha256": candidate.source_hash,
                "frame": deepcopy(frame)}

    def activate(self, candidate_id: str, expected_active_revision: int):
        if error := self._base_error(expected_active_revision):
            return self._failure(error)
        if not isinstance(candidate_id, str):
            return self._failure("candidate_id must be text")
        candidate = self._candidates.get(candidate_id)
        if candidate is None:
            return self._failure("unknown or consumed candidate")
        if candidate.base_revision != self._revision:
            return self._failure("candidate was compiled against an older active revision")
        try:
            # The checker receives a copy so even a wrapper cannot mutate the retained frame.
            validity = self._checker(self._desk, deepcopy(candidate.frame))
        except Exception as exc:
            return self._failure(f"activation check refused: {type(exc).__name__}: {exc}", diagnostics=getattr(exc, "diagnostics", None))
        if not validity.get("ok"):
            return self._failure(*validity.get("reasons", ["candidate frame is stale"]), diagnostics=validity.get("diagnostics"))
        if error := self._base_error(expected_active_revision):
            return self._failure(error)
        before = self._revision
        self._revision += 1
        self._active = candidate
        self._history[self._revision] = candidate.source
        del self._candidates[candidate_id]
        return {"ok": True, "errors": [], "activation_revision": self._revision,
                "receipt": {"operation": "activate", "from_revision": before,
                            "to_revision": self._revision, "source_sha256": candidate.source_hash,
                            "definition_id": self.definition_id,
                            "world_effects": [], "view_state_effects": []}}

    def restore(self, historical_revision: int, expected_active_revision: int):
        """Recompile historical source now and activate as a NEW monotonic generation.

        No previous world state, action, draft or selection is replayed/restored.
        """
        if error := self._base_error(expected_active_revision):
            return self._failure(error)
        if type(historical_revision) is not int or historical_revision not in self._history:
            return self._failure("unknown historical active revision")
        candidate = self.propose(self._history[historical_revision], expected_active_revision)
        if not candidate["ok"]:
            return candidate
        result = self.activate(candidate["candidate_id"], expected_active_revision)
        if result["ok"]:
            result["receipt"]["operation"] = "restore-definition"
            result["receipt"]["restored_source_from_revision"] = historical_revision
        return result
