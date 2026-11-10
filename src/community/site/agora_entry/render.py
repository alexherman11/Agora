"""HTML from templates, escaped by default.

Templates are plain files with `{name}` slots. Every value is HTML-escaped
unless it is wrapped in `Safe`, which only code in this package does, for
fragments it has itself built from escaped parts.
"""

from __future__ import annotations

import html
import string
from functools import cache
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"


class Safe(str):
    """A string that is already HTML."""


def esc(value: object) -> str:
    if isinstance(value, Safe):
        return value
    return html.escape("" if value is None else str(value), quote=True)


def join(parts) -> Safe:
    return Safe("".join(esc(p) for p in parts))


def tag(name: str, text: object = "", **attrs) -> Safe:
    """A small element: tag("a", "Sign in", href="/signin", class_="btn")."""
    rendered = "".join(
        f' {k.rstrip("_").replace("_", "-")}="{esc(v)}"'
        for k, v in attrs.items() if v is not None and v is not False
    )
    return Safe(f"<{name}{rendered}>{esc(text)}</{name}>")


class _Escaping(string.Formatter):
    def format_field(self, value, format_spec):
        if isinstance(value, Safe):
            return value
        return esc(format(value, format_spec))


_FMT = _Escaping()


@cache
def _template(name: str) -> str:
    return (TEMPLATES / name).read_text(encoding="utf-8")


def fill(name: str, **ctx) -> Safe:
    return Safe(_FMT.format(_template(name), **ctx))
