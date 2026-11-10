"""Opt-in JSON property references for surface copies, independent of any app.

copy_json=prop1,prop2 declares version-1 JSON envelopes. Only the exact typed
object {"$ref": "<identity>"} names a reference; plain strings/keys are literal.
"""
import json
import math


def read(raw):
    def bad_constant(value):
        raise ValueError(f"non-finite JSON value {value}")

    def unique(pairs):
        result = {}
        for key, item in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key {key}")
            result[key] = item
        return result

    value = json.loads(raw, parse_constant=bad_constant, object_pairs_hook=unique)
    if not isinstance(value, dict) or type(value.get("v")) is not int or value["v"] != 1:
        raise ValueError("structured references need a version-1 JSON object")

    def validate(part, depth=0):
        if depth > 128:
            raise ValueError("structured references exceed 128 levels")
        if isinstance(part, dict):
            if "$ref" in part:
                if set(part) != {"$ref"} or not isinstance(part["$ref"], str) or not part["$ref"]:
                    raise ValueError("a typed reference must be exactly a nonempty {$ref: string}")
            else:
                for item in part.values():
                    validate(item, depth + 1)
        elif isinstance(part, list):
            for item in part:
                validate(item, depth + 1)
        elif isinstance(part, float) and not math.isfinite(part):
            raise ValueError("non-finite JSON number")

    validate(value)
    return value


def remap(value, identities):
    if isinstance(value, dict):
        if set(value) == {"$ref"}:
            return {"$ref": identities.get(value["$ref"]) or value["$ref"]}
        return {key: remap(item, identities) for key, item in value.items()}
    if isinstance(value, list):
        return [remap(item, identities) for item in value]
    return value


def write(value, identities):
    return json.dumps(remap(value, identities), ensure_ascii=False, separators=(",", ":"), allow_nan=False)
