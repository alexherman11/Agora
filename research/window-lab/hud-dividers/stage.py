"""Divider FOUNDATION ONLY: not the completed c7080 navigation redesign.

Exact, additive home-tiling patches for JEFF. Never opens a live connection.

    python research/window-lab/hud-dividers/stage.py

Prints desk `do replace` lines. JEFF reads the live lens, checks each passage,
saves a restore note, then applies one line at a time after source landing.
No style, current layout, panel membership or existing data is replaced.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PATCHES = (
    ("  share $span\n  role tilecol",
     "  share $span\n  resize span min 240\n  role tilecol"),
    ("panel : column\n  share 1\n  role pane",
     "panel : column\n  share $(max(0.000001, $p.height_share or 1))\n  resize height_share min 140\n  role pane"),
    ("  share $big\n  role pane",
     "  share $(max(0.000001, $p.full_share or big))\n  resize full_share min 240\n  role pane"),
    ("  let span = ($col.span or 1)",
     "  let span = max(0.000001, $col.span or 1)"),
    ('tip "Panels" "Drag a title anywhere;',
     'tip "Panels" "Drag a divider to resize neighbours; drag a title anywhere;'),
)


def staged(text):
    for old, new in PATCHES:
        if new in text:
            continue
        if text.count(old) != 1:
            raise ValueError(f"STOP: expected exactly one passage: {old!r}")
        text = text.replace(old, new)
    return text


def quoted(value):
    return json.dumps(value, ensure_ascii=False).replace("$", r"\$")


if __name__ == "__main__":
    before = (HERE / "home-tiling.before").read_text(encoding="utf-8")
    staged(before)  # fail closed before printing any act
    for old, new in PATCHES:
        print(f"do replace a5692 old={quoted(old)} new={quoted(new)}")
