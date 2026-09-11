"""Bounded application-defined JSON schemas and generic projection.
Never fetch remote schema references or execute custom validation code.
"""

import json

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

from agora3.world import Refusal, encoded

ALLOWED = {
    "type",
    "properties",
    "required",
    "additionalProperties",
    "items",
    "enum",
    "const",
    "minimum",
    "maximum",
    "minLength",
    "maxLength",
    "minItems",
    "maxItems",
    "description",
}


def check_schema(schema, depth=0):
    if depth > 12 or not isinstance(schema, dict):
        raise Refusal(
            "Use bounded JSON record/list/scalar schemas, without references or "
            "executable validators."
        )
    unknown = set(schema) - ALLOWED
    if unknown:
        raise Refusal(
            f"Unsupported schema keywords: {sorted(unknown)}. Supported: {sorted(ALLOWED)}"
        )
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise Refusal(f"Invalid schema: {exc.message}") from exc
    for child in schema.get("properties", {}).values():
        check_schema(child, depth + 1)
    for key in ("items", "additionalProperties"):
        if isinstance(schema.get(key), dict):
            check_schema(schema[key], depth + 1)


def validate(schema, value):
    try:
        Draft202012Validator(schema).validate(value)
    except ValidationError as exc:
        raise Refusal(f"Schema mismatch at {list(exc.path)}: {exc.message}") from exc


def record(properties, required=None):
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties) if required is None else required,
        "additionalProperties": False,
    }


TEXT = {"type": "string", "maxLength": 100000}
BUILTINS = {
    "core.text": record({"text": TEXT}),
    "core.title": record({"text": {"type": "string", "maxLength": 500}}),
    "core.appearance": record(
        {
            k: {"type": "number", "minimum": -100000, "maximum": 100000}
            for k in ("x", "y", "width", "height")
        }
        | {"scene": {"type": "string", "maxLength": 160}},
        ["x", "y", "scene"],
    ),
    "core.message": record(
        {
            "role": {"enum": ["user", "assistant", "system"]},
            "text": TEXT,
            "created_at": {"type": "string"},
        }
    ),
    "core.draft": {"type": "object"},
    "core.collection": record({"name": TEXT, "entries": {"type": "array", "maxItems": 10000}}),
}


def validate_facets(obj_id, old, patch, db):
    if obj_id.startswith("agora.") or any(f.startswith("agora.") for f in patch):
        raise Refusal("Use package/schema operations for protected runtime records.")
    for facet, value in patch.items():
        if value is None:
            continue
        if len(encoded(value).encode()) > 256000:
            raise Refusal("Each application facet is limited to 256 KB in this runtime.")
        schema = BUILTINS.get(facet)
        if schema is None:
            row = db.execute(
                "SELECT body FROM objects WHERE id=?", ("agora.schema." + facet,)
            ).fetchone()
            if row is None:
                raise Refusal(f"Unknown facet {facet}; define it with schema.define first.")
            schema = json.loads(row[0])["facets"]["agora.schema"]["schema"]
        validate(schema, value)
