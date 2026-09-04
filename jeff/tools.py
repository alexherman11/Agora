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
    return tools
