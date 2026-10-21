"""Stage the expanded navigation world half; never connects to the live world.

JEFF must reread home-tiling and the person's current column arrangement, save
both old lens text and old tree prop, and check the exact hunks before applying.
`patches(text)` returns scoped replacements, including only the normal/filled
tiling and panel parts. The top bar, other lenses/styles, memberships, dock,
music lenses, scrolling and tilefoot style are not rewritten.

`migration(columns)` takes a fresh manifest in current order:
[{"span":1, "panels":[{"id":"...", "height_share":1}, ...]}, ...].
Include shelved panels so restoring them restores their place. It only prepares
the new tree prop; it never moves, deletes or resets any panel/column.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def migration(columns):
    seen = set()
    kids, weights = [], []
    for col in columns:
        leaves, heights = [], []
        for panel in col["panels"]:
            pid = panel["id"]
            if pid in seen:
                raise ValueError(f"duplicate panel {pid}")
            seen.add(pid)
            leaves.append({"id": {"$ref": pid}, **({"size": "content"} if panel.get("sizing") == "content" else {})})
            heights.append(max(0.000001, float(panel.get("height_share") or 1)))
        if leaves:
            kids.append(leaves[0] if len(leaves) == 1 else dict(axis="y", kids=leaves, weights=heights))
            weights.append(max(0.000001, float(col.get("span") or 1)))
    return dict(v=1, root=kids[0] if len(kids) == 1 else dict(axis="x", kids=kids, weights=weights)) if kids else dict(v=1, root=None)


def patches(text):
    start = text.index("    tiling : row\n")
    end = text.index("column : column\n", start)
    old_tiling = text[start:end]
    new_tiling = '''    tiling : column
      share 1
      role tiling
      scroll none
      partition tree min 240 140 gap 16 focus full
      of kind:note,in:$lay.item,prop:role=home-panel as p
      each panel
'''
    start = text.index("panel : column\n")
    end = text.index("railitem : column\n", start)
    old_panel = text[start:end]
    new_panel = old_panel.replace("  share 1\n  role pane", '''  share 1
  only when ($p.shelf or "no") != "yes"
  companion ($p.pin or "") = "yes" or (($p.lens or "") = "home-viewer" and showing > 0)
  sizing ($p.sizing or "")
  chrome ($p.chrome or "")
  tip "$p.title" "Drag the title to move this panel."
  role pane''', 1)
    new_panel = "\n".join(line for line in new_panel.split("\n") if "on drop grip " not in line)
    new_panel = new_panel.replace('    on double when ($lay.full or "") = "" do prop $lay full=$p',
                                '''    on double when ($lay.full or "") != $p.item do prop $lay full=$p
    on double when ($lay.full or "") = $p.item do prop $lay full=""''')
    wider_start = new_panel.index("    wider : text")
    wider_end = new_panel.index("    away : text", wider_start)
    new_panel = new_panel[:wider_start] + '''    back : text "⤡"
      role tool
      tip "Restore" "Return to the saved arrangement."
      only when ($lay.full or "") = $p.item
      on click do prop $lay full=""
''' + new_panel[wider_end:]
    new_panel = new_panel.replace("on click do prop $p shelf=yes", '''on click when ($lay.full or "") = $p.item do prop $p shelf=yes; do prop $lay full=""
      on click when ($lay.full or "") != $p.item do prop $p shelf=yes''')
    new_panel = new_panel.replace("do close-panel $p $col", "do close-panel $p $p.in")
    new_panel = new_panel.replace("  appgrip : row\n    role appgrip\n    carry\n",
                                  '''  appgrip : row
    role appgrip
    carry
    on double when ($lay.full or "") != $p.item do prop $lay full=$p
    on double when ($lay.full or "") = $p.item do prop $lay full=""
''')
    # Keep the live filled-body passages, including the music helper choice.
    full = text[text.index("fullpanel : column\n"):]
    body = full[full.index("  body : column\n"):]
    new_panel = new_panel[:new_panel.index("  body : column\n")] + body
    tip_old = next(line.strip() for line in text.splitlines() if 'tip "Panels" ' in line)
    tip_new = ('tip "Panels" "Drag dividers to resize. Drag a title to a desk edge, a panel edge, or its centre for tabs; '
               'double-click to fill or restore. Fit toggles content size; ◆ pins a companion; – shelves a panel."')
    # Replace the retired column/rail/fullpanel definitions as one checked hunk:
    # leaving dead definitions would invite later edits to the wrong header.
    old_parts = text[text.index("column : column\n"):]
    history_old = "# Drag a panel by its title."
    history_new = ("# a7045: world tree partition replaces the column-only navigation described below. "
                   "Shared dividers resize;\n# global edges wrap the desk, local edges split, centres make tabs; "
                   "Fit toggles content sizing. The following\n# column behavior is retained as historical context, "
                   "superseded by research/window-lab/hud-dividers/NAVIGATION.md.\n"
                   + history_old)
    result = [(old_tiling, new_tiling), (old_parts, new_panel), (tip_old, tip_new), (history_old, history_new)]
    for old, _ in result:
        if text.count(old) != 1:
            raise ValueError("STOP: a navigation passage changed; reread before staging")
    return result


def staged(text):
    for old, new in patches(text):
        text = text.replace(old, new, 1)
    return text


def quoted(value):
    return json.dumps(value, ensure_ascii=False).replace("$", r"\$")


if __name__ == "__main__":
    before = (HERE / "home-tiling.current").read_text(encoding="utf-8")
    for old, new in patches(before):
        print(f"do replace a5692 old={quoted(old)} new={quoted(new)}")
