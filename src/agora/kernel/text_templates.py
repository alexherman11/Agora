"""Read a prose template by Markdown heading through a caller's reading door.

No stored copies or cached sections. The document remains the authority.
"""
import json
import re
from datetime import datetime, UTC

from .kernel import Kernel


def section(text, heading):
    """A heading's direct body, ending at the next heading of any level.

    Child sections have their own address; proposed additions below a message
    are not silently promoted into instructions. Fenced headings are text.
    """
    found, body, fence = False, [], None
    for line in text.splitlines():
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker:
            token = marker[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
        title = None if fence or marker else re.match(r"^ {0,3}#{1,6}[ \t]+(.+?)[ \t]*$", line)
        if title:
            if found:
                break
            found = re.sub(r"[ \t]+#+[ \t]*$", "", title[1]) == heading
        elif found:
            body.append(line)
    body = "\n".join(body).strip()
    # A whole-body text fence quotes literal Markdown headings in a template.
    # Other fences, or fences embedded in prose, remain part of the message.
    literal = re.fullmatch(r"(`{3,}|~{3,})text[ \t]*\n([\s\S]*?)\n\1", body)
    if literal:
        body = literal[2].strip()
    if not found or not body:
        raise ValueError("missing or empty heading")
    return body


def render(see, document, heading, facts=None, names=None):
    """Read and fill once. A gap supplies no substitute operational instruction."""
    def read(target):
        result = see("look " + json.dumps(str(target), ensure_ascii=False))
        rows = result.get("rows") or []
        if result.get("ok") is False or not rows:
            raise ValueError("unreadable reference " + str(target))
        return rows[0]

    try:
        body = section(str(read(document).get("text") or ""), heading)
        now = datetime.now(UTC)
        supplied = {"now": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "today": now.date().isoformat()}
        return Kernel.fill_text(body, {**supplied, **(names or {})}, facts or {}, read)
    except Exception as exc:
        # Never leak transport bodies, credentials or private referenced facts.
        # Only our own validation errors may contain authored template names.
        reason = str(exc) if type(exc) is ValueError and str(exc).startswith(
            ("unfilled $", "unreadable reference ", "missing or empty heading")) else type(exc).__name__
        return f"Message unavailable: {document} / {heading} ({reason}). No instruction supplied."
