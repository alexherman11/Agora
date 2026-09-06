"""Tool definitions derived from the verb and facet registries; nothing here is hand-written.
Never: never describes a capability the verbs do not have."""

from __future__ import annotations

from typing import Any

from kernel import verbs

_JSON_TYPES = {
    "str": "string",
    "dict": "object",
    "int": "integer",
    "float": "number",
    "list": "array",
}


def derive_tools() -> list[dict[str, Any]]:
    """One tool per verb, in registry order, with the facet shapes wherever a body is expected."""
    shapes = "; ".join(f"{f['type']} {f['shape']}" for f in verbs.facet_types())
    tools = []
    for vdef in verbs.REGISTRY:
        description = vdef.doc
        if any(p.kind == "dict" and name in ("facets", "body") for name, p in vdef.params.items()):
            description += f" Facet shapes: {shapes}."
        tools.append(
            {
                "name": vdef.name,
                "description": description,
                "input_schema": {
                    "type": "object",
                    "properties": {
                        name: {"type": _JSON_TYPES[p.kind], "description": p.doc}
                        for name, p in vdef.params.items()
                    },
                    "required": [name for name, p in vdef.params.items() if p.required],
                },
            }
        )
    writable = {
        f["type"]: f["json_schema"]
        for f in verbs.facet_types()
        if f["type"]
        not in {"core.component-state", "core.component-test", "core.component-admission"}
    }
    for tool in tools:
        properties = tool["input_schema"]["properties"]
        if tool["name"] == "mint":
            properties["facets"] = {
                "type": "object",
                "properties": writable,
                "additionalProperties": False,
            }
        elif tool["name"] == "attach":
            properties["body"] = {"anyOf": list(writable.values())}
    return tools


def derive_extension_tools(actions):
    """Descriptions and argument schemas come from admitted component manifests."""
    tools, targets = [], {}
    for action in actions:
        name = "extension_" + action["name"]
        targets[name] = action
        tools.append(
            {
                "name": name,
                "description": action["description"],
                "input_schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {k: {"type": t} for k, t in action["params"].items()},
                    "required": list(action["params"]),
                },
            }
        )
    return tools, targets
