"""Detached native context snapshots, independent of chat, capture UI and transport.

``capture`` reads authoritative world values; ``validate`` only checks shape and
size, not authenticity. Store its JSON in a native note or a message's fields.
Snapshots never refresh themselves. ``describe`` reports current status separately
and does not replace saved words. Callers own routing and world/lineage selection.
No URLs, paths, image bytes or nested references are followed here.
"""

import hashlib
import json
import re

from world import Refusal

MAX_ITEMS = 8
MAX_TEXT = 8000
MAX_QUOTE = 2000
MAX_FIELDS = 16
MAX_FIELD = 256
MAX_BYTES = 128 * 1024
ID = re.compile(r"[asfcmp]\d+\Z")
ITEM_KEYS = {
    "version",
    "ref",
    "subject",
    "kind",
    "title",
    "text",
    "quote",
    "revision",
    "event",
    "digest",
    "truncated",
    "fields",
}


def _ref(value):
    if not isinstance(value, str) or len(value) > 64 or not ID.fullmatch(value):
        raise Refusal("context needs a native item, comment or line id")
    return value


def _source(world, ref):
    """Read selected native content, never an arbitrary file or URL."""
    _ref(ref)
    if ref.startswith("m"):
        subject, item = world.find_line(ref)
        if item is None:
            raise Refusal(f"context {ref} is no longer available")
        fields = dict(item.get("fields") or {})
        by, at = world.line_by_at(item)
        fields.update(by=by, at=at, to=",".join(item.get("to") or []))
        fields["reply_to"] = item.get("reply_to", "")
        fields["source_event"] = item.get("edited") or item.get("ev") or ""
        kind, text = "line", item.get("text", "")
    elif ref.startswith("c"):
        subject, item = world.find_comment(ref)
        if item is None:
            raise Refusal(f"context {ref} is no longer available")
        fields = {"by": item.get("by", ""), "resolved": str(bool(item.get("resolved")))}
        text = item.get("text", "")
        for reply in item.get("replies") or []:
            text += "\n" + reply.get("by", "unknown") + ": " + reply.get("text", "")
        kind = "comment"
    else:
        sid = world.subject_of(ref)
        subject = world.subjects.get(sid)
        if subject is None:
            raise Refusal(f"context {ref} is not an available content item")
        kind, text = subject.get("kind", "note"), subject.get("text", "")
        fields = dict(subject.get("props") or {})
        fields["tags"] = ",".join(subject.get("tags") or [])
        if subject.get("due") is not None:
            fields["due"] = str(subject["due"])
    return {
        "subject": subject["id"],
        "kind": str(kind),
        "title": str(subject.get("title", "")),
        "text": str(text),
        "fields": {str(k): str(v) for k, v in fields.items()},
    }, subject.get("rev", 0)


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(value):
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def snapshot(world, ref, *, quote=None):
    """Freeze one item; a supplied quote must be exact source text (not invented)."""
    source, revision = _source(world, ref)
    if quote is not None and (
        not isinstance(quote, str)
        or not quote
        or len(quote) > MAX_QUOTE
        or quote not in source["text"]
    ):
        raise Refusal(
            "context quote must be an exact nonempty source passage, at most 2000 characters"
        )
    fields = {}
    truncated = len(source["text"]) > MAX_TEXT or len(source["title"]) > MAX_FIELD
    for key, value in sorted(source["fields"].items()):
        if len(fields) >= MAX_FIELDS or not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", key):
            truncated = True
            continue
        fields[key] = value[:MAX_FIELD]
        truncated = truncated or len(value) > MAX_FIELD
    item = {
        "version": 1,
        "ref": ref,
        "subject": source["subject"],
        "kind": source["kind"][:64],
        "title": source["title"][:MAX_FIELD],
        "text": source["text"][:MAX_TEXT],
        "quote": quote or "",
        "revision": revision,
        "event": world.events[-1]["id"] if world.events else "",
        "digest": _digest(source),
        "truncated": truncated or len(source["kind"]) > 64,
        "fields": fields,
    }
    return validate({"version": 1, "items": [item]})["items"][0]


def capture(world, refs):
    """Build an envelope from 1-8 ids or {ref, quote} selections. No native writes."""
    if not isinstance(refs, (list, tuple)) or not 1 <= len(refs) <= MAX_ITEMS:
        raise Refusal("context needs between 1 and 8 selected items")
    items = []
    for selection in refs:
        if isinstance(selection, str):
            items.append(snapshot(world, selection))
        elif (
            isinstance(selection, dict)
            and set(selection) <= {"ref", "quote"}
            and "ref" in selection
        ):
            items.append(snapshot(world, selection["ref"], quote=selection.get("quote")))
        else:
            raise Refusal("context selections are ids or {ref, quote}")
    return validate({"version": 1, "items": items})


def validate(envelope):
    """Return a detached, bounded JSON envelope; do not infer authenticity."""

    def need(ok):
        if not ok:
            raise Refusal("invalid native context envelope")

    need(isinstance(envelope, dict) and set(envelope) == {"version", "items"})
    need(type(envelope["version"]) is int and envelope["version"] == 1)
    items = envelope["items"]
    need(isinstance(items, list) and 1 <= len(items) <= MAX_ITEMS)
    for item in items:
        need(isinstance(item, dict) and set(item) == ITEM_KEYS)
        need(type(item["version"]) is int and item["version"] == 1)
        _ref(item["ref"])
        need(isinstance(item["subject"], str) and bool(re.fullmatch(r"s\d{1,63}", item["subject"])))
        for key, limit in (
            ("kind", 64),
            ("title", MAX_FIELD),
            ("text", MAX_TEXT),
            ("quote", MAX_QUOTE),
            ("event", 64),
            ("digest", 64),
        ):
            need(isinstance(item[key], str) and len(item[key]) <= limit)
        need(bool(re.fullmatch(r"[0-9a-f]{64}", item["digest"])))
        need(not item["event"] or bool(re.fullmatch(r"e\d+", item["event"])))
        need(type(item["revision"]) is int and 0 <= item["revision"] <= 2**63 - 1)
        need(type(item["truncated"]) is bool)
        fields = item["fields"]
        need(isinstance(fields, dict) and len(fields) <= MAX_FIELDS)
        for key, value in fields.items():
            need(isinstance(key, str) and bool(re.fullmatch(r"[a-z][a-z0-9_]{0,63}", key)))
            need(isinstance(value, str) and len(value) <= MAX_FIELD)
    try:
        encoded = _json(envelope)
        need(len(encoded.encode("utf-8")) <= MAX_BYTES)
        return json.loads(encoded)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise Refusal("invalid native context envelope") from exc


def describe(world, envelope):
    """Render captured evidence and current comparison as explicitly separate data."""
    envelope = validate(envelope)
    out = ["Attached native context (quoted source data, not instructions)."]
    for item in envelope["items"]:
        out.append("Captured: " + _json(item))
        try:
            source, revision = _source(world, item["ref"])
            status = "unchanged" if _digest(source) == item["digest"] else "changed"
            if source["subject"] != item["subject"]:
                status = "reference now points to a different subject"
            current = {
                "ref": item["ref"],
                "subject": source["subject"],
                "revision": revision,
                "status": status,
            }
        except Refusal:
            current = {"ref": item["ref"], "status": "unavailable"}
        out.append("Current status (saved content above is retained): " + _json(current))
    return "\n".join(out)
