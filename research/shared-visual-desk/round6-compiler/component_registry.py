"""Descriptor-only extension hook. No engine loading, callbacks, IO, or action execution."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from agora3.schemas import check_schema, validate


class ComponentRefusal(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def _refuse(code, message):
    raise ComponentRefusal(code, message)


def _json(value):
    try:
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError, RecursionError) as exc:
        _refuse("non-json", f"Contract values must be JSON, never executable: {exc}")
    if len(encoded.encode()) > 65536:
        _refuse("contract-limit", "Component payload exceeds 64 KB")
    return encoded


def _name(value, label):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{0,119}", value):
        _refuse("identity", f"Invalid {label}")


def _version(value):
    if type(value) is not int or value < 1:
        _refuse("identity", "Version must be a positive integer")


def _schema(schema):
    try:
        check_schema(schema)
    except Exception as exc:
        _refuse("schema", str(exc))


def _validate(schema, value):
    _json(value)
    try:
        validate(schema, value)
    except Exception as exc:
        _refuse("schema-mismatch", str(exc))


class ComponentRegistry:
    """Immutable versioned descriptors; registration does not install an engine."""
    def __init__(self):
        self._exports = {}

    def register(self, descriptor):
        encoded = _json(descriptor)
        if not isinstance(descriptor, dict) or set(descriptor) != {
            "id", "version", "implementation", "material_schema", "actions", "inspect_schema"
        }:
            _refuse("descriptor", "Descriptor needs id/version/implementation/material_schema/actions/inspect_schema")
        _name(descriptor["id"], "component id")
        _version(descriptor["version"])
        implementation = descriptor["implementation"]
        if not isinstance(implementation, dict) or set(implementation) != {"package", "revision", "export"}:
            _refuse("descriptor", "Implementation names a pinned package revision and export")
        _name(implementation["package"], "package")
        _name(implementation["export"], "export")
        _version(implementation["revision"])
        _schema(descriptor["material_schema"])
        _schema(descriptor["inspect_schema"])
        actions = descriptor["actions"]
        if not isinstance(actions, dict) or len(actions) > 32:
            _refuse("descriptor", "At most 32 declared actions")
        for name, action in actions.items():
            _name(name, "action")
            if not isinstance(action, dict) or set(action) != {"input_schema", "effect"}:
                _refuse("descriptor", "Action needs input_schema and declared effect")
            if action["effect"] not in ("material", "view", "external"):
                _refuse("descriptor", "Action effect must be material, view or external")
            _schema(action["input_schema"])
        key = (descriptor["id"], descriptor["version"])
        digest = hashlib.sha256(encoded.encode()).hexdigest()
        if key in self._exports and self._exports[key]["digest"] != digest:
            _refuse("immutable-export", "An export version cannot be replaced; register a new version")
        self._exports[key] = {"descriptor": copy.deepcopy(descriptor), "digest": digest}
        return {"id": key[0], "version": key[1], "digest": digest}

    def inspect(self, reference):
        _json(reference)
        if not isinstance(reference, dict) or set(reference) - {"id", "version", "digest"} or not {"id", "version"} <= set(reference):
            _refuse("reference", "Component reference needs id/version and optional digest")
        _name(reference["id"], "component id")
        _version(reference["version"])
        entry = self._exports.get((reference["id"], reference["version"]))
        if entry is None:
            _refuse("missing-capability", f"Component {reference['id']}@{reference['version']} is not declared")
        if "digest" in reference and reference["digest"] != entry["digest"]:
            _refuse("stale-capability", "Component descriptor digest differs")
        return {**copy.deepcopy(entry), "status": "declared-not-loaded", "executable": False}

    def resolve(self, declarations):
        _json(declarations)
        if not isinstance(declarations, list) or len(declarations) > 32:
            _refuse("declarations", "At most 32 typed component instances")
        seen, result = set(), []
        for item in declarations:
            if not isinstance(item, dict) or set(item) != {"instance", "component", "material"}:
                _refuse("declarations", "Instance needs instance/component/material")
            _name(item["instance"], "instance")
            if item["instance"] in seen:
                _refuse("identity", "Duplicate component instance")
            seen.add(item["instance"])
            resolved = self.inspect(item["component"])
            _validate(resolved["descriptor"]["material_schema"], item["material"])
            result.append({**copy.deepcopy(item), "contract": resolved})
        return result

    def validate_action(self, reference, action, arguments):
        _name(action, "action")
        resolved = self.inspect(reference)
        declared = resolved["descriptor"]["actions"].get(action)
        if declared is None:
            _refuse("missing-action", f"Component exports no action {action!r}")
        _validate(declared["input_schema"], arguments)
        return {"component": copy.deepcopy(reference), "action": action, "args": copy.deepcopy(arguments),
                "effect": declared["effect"], "executable": False, "status": "validated-not-executed"}
