"""Reviewable installer taking an already authenticated Door, never credentials.

No CLI/live default. Does not activate a widget, grant authority, open a window,
change shell settings or restart the broker. House handles reviewed activation.
"""
import hashlib
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
spec = importlib.util.spec_from_file_location("search_painter_install", LAB / "painter/install.py")
painter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(painter)

# Requested activation manifest, not executed by install(). No writes or launch
# of native executables; ordinary window host still checks the viewer's rights.
REQUIRED_GRANTS = ("window.surface rows look look-view history components help component-health component-action "
                   "search window.open hear:make hear:set hear:forget hear:undo hear:component hear:component-action")


def install(door):
    source = (HERE / "lexical.js").read_text(encoding="utf-8")
    cid = painter.upsert(door, "component", "smart-search", category="collections",
        purpose="Apps and World text search: word matches and source evidence only.",
        settings="{}", parts='{"body":{"facts":"caller-visible search results"}}', slots="[]",
        gestures="evidence", example="root : smart-search", uses="Kernel search and caller-visible source evidence",
        limitations="Word matches only; up to 50 results before supported-kind/source filters. Capabilities unverified. Files, Email and Web disconnected. No inference.",
        code=source)
    # House must review exact code hash, then activate separately.
    lens = painter.upsert(door, "lens", "smart-search", title="Search",
        painter="components", text=(HERE / "search.lens").read_text(encoding="utf-8"))
    widget = painter.upsert(door, "widget", "smart-search", title="Search", style="bars",
        component_lens="smart-search", code=painter.widget_source(board_look=False))
    return dict(component=cid, lens=lens, widget=widget,
                review_sha256=hashlib.sha256(source.encode()).hexdigest(),
                requested_grants=REQUIRED_GRANTS)


def entry(door):
    """Explicit post-review one-click entry; creates no fixture apps or windows."""
    return painter.upsert(door, "button", "smart-search-button", label="Search",
                          bar="taskbar", icon="search", does="window.open smart-search")
