"""Bounded file import preparation under an explicit caller-selected source policy.
Never: never writes blobs or events, never grants access based on an actor string."""

from __future__ import annotations

import hashlib
from pathlib import Path

from kernel import facets

MAX_IMPORT_BYTES = 8 * 1024 * 1024


def prepare(facet_type: str, body: dict, roots: tuple[Path, ...]) -> tuple[dict, bytes | None]:
    body = dict(facets.validate(facet_type, body))
    blob = None
    if facet_type in ("core.text", "core.file-backing") and "path" in body:
        target = Path(body["path"]).expanduser().resolve()
        if not any(target == r or target.is_relative_to(r) for r in roots):
            raise facets.FacetError(
                "file is outside the authorized import sources; select it first"
            )
        try:
            with target.open("rb") as handle:
                data = handle.read(MAX_IMPORT_BYTES + 1)
        except OSError as exc:
            raise facets.FacetError(f"cannot import {target.name}: {exc.strerror}") from exc
        if len(data) > MAX_IMPORT_BYTES:
            raise facets.FacetError(f"import exceeds {MAX_IMPORT_BYTES} bytes")
        if facet_type == "core.text":
            try:
                body = {"text": data.decode("utf-8")}
            except UnicodeError as exc:
                raise facets.FacetError(
                    "text import must be UTF-8; use core.file-backing for bytes"
                ) from exc
        else:
            body |= {"hash": hashlib.sha256(data).hexdigest(), "size": len(data)}
            blob = data
    return dict(facets.validate(facet_type, body)), blob
