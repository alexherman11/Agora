"""The constitutional facet definitions, frozen: what each facet says, validates as, projects to.
Never: no I/O, no events, no Loro; a definition is never added or changed at runtime."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from kernel.schema import MODES


class FacetError(Exception):
    """A body the definition refuses. The message says what shape was expected."""


@dataclass(frozen=True)
class Field:
    kind: str  # "str" | "int" | "float" | "list" | "dict"
    required: bool = False
    doc: str = ""


@dataclass(frozen=True)
class FacetDef:
    type: str
    doc: str
    fields: MappingProxyType[str, Field]
    authority: str  # "intent" in M1; "reconciler" arrives with the reconcilers
    merge: str  # "register" | "sequence" | "reconciled"
    projection: str  # "name" | "text" | "file" | "scene" | "generic"
    limits: MappingProxyType[str, int]

    def shape(self) -> str:
        parts = []
        for name, f in self.fields.items():
            parts.append(f"{name}{'' if f.required else '?'}: {f.kind}")
        return "{" + ", ".join(parts) + "}"


_PY = {"str": str, "int": int, "float": (int, float), "list": list, "dict": dict}


def _def(type_: str, doc: str, fields: dict[str, Field], **kw: Any) -> FacetDef:
    return FacetDef(
        type=type_,
        doc=doc,
        fields=MappingProxyType(fields),
        authority=kw.get("authority", "intent"),
        merge=kw.get("merge", "register"),
        projection=kw.get("projection", "generic"),
        limits=MappingProxyType(kw.get("limits", {})),
    )


REGISTRY: MappingProxyType[str, FacetDef] = MappingProxyType(
    {
        "core.name": _def(
            "core.name",
            "What the entity is called, plus aliases.",
            {
                "name": Field("str", True, "the display name"),
                "aliases": Field("list", False, "other names it answers to"),
            },
            projection="name",
            limits={"name": 200},
        ),
        "core.text": _def(
            "core.text",
            "A text body. Give `text` to set it, or `path` to import a UTF-8 file's contents.",
            {
                "text": Field("str", False, "the whole text"),
                "path": Field("str", False, "a file to import as the text (resolved on attach)"),
                "snapshot": Field("str", False, "base64 CRDT snapshot; written by the text layer"),
            },
            merge="sequence",
            projection="text",
            limits={"text": 1_000_000},
        ),
        "core.file-backing": _def(
            "core.file-backing",
            "The entity's bytes live in a file. Give `path`; the hash and size are recorded.",
            {
                "path": Field("str", True, "path to the backing file"),
                "hash": Field("str", False, "sha256 of the bytes at import; filled on attach"),
                "size": Field("int", False, "byte count at import; filled on attach"),
            },
            projection="file",
        ),
        "core.scene": _def(
            "core.scene",
            "A surface that places entities. Appearances hold position; entities never do.",
            {
                "appearances": Field(
                    "list", True, "[{entity, mode: icon|summary|full, transform: {x, y, scale}}]"
                ),
            },
            projection="scene",
        ),
    }
)


def validate(facet_type: str, body: Any) -> dict[str, Any]:
    """Return the body if it fits the definition; otherwise refuse with the expected shape."""
    if facet_type not in REGISTRY:
        raise FacetError(f"unknown facet type {facet_type!r}; M1 knows {sorted(REGISTRY)}")
    fdef = REGISTRY[facet_type]
    if not isinstance(body, dict):
        got = type(body).__name__
        raise FacetError(f"{facet_type} expects an object {fdef.shape()}; got {got}")
    unknown = sorted(set(body) - set(fdef.fields))
    if unknown:
        raise FacetError(f"{facet_type} expects {fdef.shape()}; unknown keys {unknown}")
    for name, f in fdef.fields.items():
        if f.required and name not in body:
            raise FacetError(f"{facet_type} expects {fdef.shape()}; missing required {name!r}")
        if name in body and not isinstance(body[name], _PY[f.kind]):
            raise FacetError(
                f"{facet_type}.{name} must be {f.kind}; got {type(body[name]).__name__}"
            )
        if name in body and f.kind == "str" and name in fdef.limits:
            if len(body[name]) > fdef.limits[name]:
                raise FacetError(f"{facet_type}.{name} is limited to {fdef.limits[name]} chars")
    if facet_type == "core.text" and "text" not in body and "path" not in body:
        raise FacetError("core.text needs either `text` or `path`")
    if facet_type == "core.scene":
        for entry in body["appearances"]:
            validate_appearance(entry)
    return body


def validate_appearance(entry: Any) -> None:
    shape = "{entity: str, mode: icon|summary|full, transform: {x, y, scale}}"
    if not isinstance(entry, dict) or not isinstance(entry.get("entity"), str):
        raise FacetError(f"an appearance is {shape}; got {entry!r}")
    if entry.get("mode", "icon") not in MODES:
        raise FacetError(f"appearance mode must be one of {list(MODES)}; got {entry.get('mode')!r}")
    transform = entry.get("transform", {})
    if not isinstance(transform, dict) or not all(
        isinstance(v, int | float) for v in transform.values()
    ):
        raise FacetError(f"a transform is {{x, y, scale}} with numbers; got {transform!r}")


def describe() -> list[dict[str, Any]]:
    """The registry as plain data, for tool derivation and JEFF's context."""
    return [
        {
            "type": fdef.type,
            "doc": fdef.doc,
            "shape": fdef.shape(),
            "fields": {n: f.doc for n, f in fdef.fields.items()},
            "merge": fdef.merge,
        }
        for fdef in REGISTRY.values()
    ]
