"""Print the staged payload/checked hunks/docs as JSON; no Desk or world access."""
import json

import docs_stage
import navigation_stage as stage

before = (stage.HERE / "home-tiling.current").read_text(encoding="utf-8")
print(json.dumps({
    "lens": stage.staged(before),
    "hunks": [{"old": old, "new": new} for old, new in stage.patches(before)],
    "docs": docs_stage.commands(),
    "guide": (stage.HERE / "NAVIGATION.md").read_text(encoding="utf-8"),
}, ensure_ascii=True))
