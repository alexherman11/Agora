"""Machine-readable facet input schemas, including the executable component contract.
Never: never validates authority, interprets source code, or defines independent tool behavior."""


def json_schema(fdef):
    types = {
        "str": "string",
        "int": "integer",
        "float": "number",
        "dict": "object",
        "list": "array",
    }
    properties = {
        name: {"type": types[field.kind], "description": field.doc}
        for name, field in fdef.fields.items()
    }
    for name, limit in fdef.limits.items():
        if name in properties and properties[name]["type"] == "string":
            properties[name]["maxLength"] = limit
    if fdef.type == "core.component":
        strings = {"type": "array", "items": {"type": "string"}}
        params = {
            "type": "object",
            "additionalProperties": {
                "enum": ["string", "number", "integer", "boolean", "object", "array"]
            },
        }
        properties["version"]["enum"] = [1]
        properties["bindings"] = {
            "type": "object",
            "description": "Actual entity IDs map to readable facet arrays; no aliases.",
            "additionalProperties": {
                "type": "array",
                "minItems": 1,
                "items": {"enum": ["core.name", "core.text", "core.scene"]},
            },
        }
        properties["permissions"] = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "state": {"type": "boolean"},
                "place": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {"scene": {"type": "string"}, "entities": strings},
                    "required": ["scene", "entities"],
                },
                "attach": {"type": "object", "additionalProperties": strings},
            },
        }
        properties["state_schema"] = params
        properties["actions"] = {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "additionalProperties": False,
                "properties": {"description": {"type": "string"}, "params": params},
                "required": ["description", "params"],
            },
        }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": [n for n, f in fdef.fields.items() if f.required],
    }
