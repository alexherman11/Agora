"""Exact documentation hunks for JEFF after the source lands. No world access."""
from navigation_stage import quoted

HELP_OLD = "share <weight>, hint"
HELP_NEW = ("share <weight>, resize <prop> min <pixels>, "
            "partition <prop> min <width> <height> gap <pixels> [focus <prop>], "
            "companion <expression>, sizing <expression>, chrome <expression>, hint")
HELP_DETAIL = """  resize <prop> min <pixels> (a7045), on repeated shared frames: drag a shared divider to redistribute neighbouring
  weights; both fenced prop writes persist together. Arrows preview, Enter saves, Escape cancels; a 12px transparent
  handle covers each shared axis. Minimum outer sizes scale together when physically impossible in the viewport.
  partition <prop> min <width> <height> gap <pixels> [focus <prop>] (a7045), on a frame standing on a world thing:
  direct bound children are leaves of a version-1 JSON split/tab tree in that prop. Use guarded children for shelves
  (not a filtered membership), so their places persist; actual removed members are pruned, new ones appended. The tree
  has root={id:{"$ref":<appearance>}, size:"content" optional} or {axis:"x"|"y", kids:[...], weights:[positive numbers]} or
  {axis:"tabs", kids:[...], active:{"$ref":<appearance>}}. Unset/invalid trees recover from current children. A carried child's
  title moves the whole child after 5px; stationary/interactive clicks do not resize. The four outer edge targets
  wrap the remaining root; local edges split the target, its centre makes tabs. One plan supplies preview and drop,
  including removal/collapse, minima and gaps. Fit content / Fill allocated space persists a leaf's sizing policy.
  A focus prop names the enlarged child; companion <expression> on a child keeps it beside that child. Other titles
  form a rail. Focus leaves the normal tree intact; focused divider weights persist separately as focus_weights.
  One generated arrange act writes the tree and focus props in one ordinary fenced prop event; no host action.
  The fence includes the member selection and direct panel revisions (guarded shelves too); concurrent panel
  policy/membership changes refuse a stale gesture. Reused scenes refresh these reads, without fencing app content.
  Declare copy_json=tree on the containing layout to preserve typed panel references through workspace copies.
  Only exact {"$ref":"<identity>"} objects in declared version-1 JSON props are remapped by copy; literal strings/keys
  and outside references stay unchanged. Unsupported versions/malformed data refuse before creating any copy.
  Focus weights persist as arrays of typed panel/member references and numeric weights, never identity-bearing keys.
  sizing <expression> on a child supplies a content/stretch preference until an explicit tree sizing choice exists.
  chrome <expression> returning "none" omits generated Fit/fill tools. Header/app carry regions and their styling
  remain lens-defined: a bare app can carry from a quiet grip without stealing input from its embedded controls.
  Content leaves expose right/bottom resize handles; extent:[width,height] persists that manual size, bounded to
  their allocation. Fit clears it. An edge drop or shared-divider resize intentionally fills its previewed region.
  Escape, cancellation, focus loss and viewport resize cancel a drag. Space on a title, arrow to a global edge,
  Enter moves it; dividers accept arrows/Enter/Escape. Only previews are local. The painter draws no raw identities.
"""
HANDBOOK_OLD = '| `role <name>` or `role <name> when <selection | expr>` | Look,'
HANDBOOK_NEW = (
    '| `resize <prop> min <pixels>` | Repeated shared frames expose both axes of shared dividers; '
    'preview by pointer or arrows, persist paired fenced world weights on release/Enter, cancel with Escape. '
    'Minimum outer sizes scale proportionately only when the viewport cannot contain them. |\n'
    '| `partition <prop> min <width> <height> gap <pixels> [focus <prop>]`, `companion <expression>` | '
    'a7045: a generic bounded split/tab layout held in a world JSON prop, whose direct bound children are leaves. '
    'Guard shelves rather than filtering membership. Whole-child carry starts at 5px; outer-edge targets wrap the '
    'remaining root, local edges split a leaf, centres make tabs. Preview and drop share the same geometric plan '
    '(minima/gaps/removal included). Fit content or stretch persists per leaf; focus/pinned companions preserve the '
    'normal tree, with separate focused weights. One fenced ordinary prop act commits the entire change. '
    'The direct-child paint contract adds partition_item even for a guarded/passive child; it is never drawn. '
    'Set copy_json=tree on the layout: copy remaps only explicit {"$ref":"identity"} objects in declared version-1 '
    'JSON props; literal strings/keys and external references remain unchanged, malformed/version errors refuse before '
    'creating any part. Focus weights use arrays of typed panel/member references. '
    '`sizing <expression>` supplies content/stretch preference; explicit tree policy wins. `chrome <expression>` '
    'of "none" hides generated sizing tools; the lens supplies its bare carry region separately from app controls. '
    'partition.js holds the pure model/geometry and partition-ui.js the pointer/keyboard adapter. See '
    'src/desktop/hud-dividers/NAVIGATION.md for schema, staged world migration and acceptance limits. |\n'
    + HANDBOOK_OLD
)


def commands():
    return [
        f"do replace a1853 old={quoted(HELP_OLD)} new={quoted(HELP_NEW)}",
        f"do append a1853 line={quoted(HELP_DETAIL)}",
        f"do replace a243 old={quoted(HANDBOOK_OLD)} new={quoted(HANDBOOK_NEW)}",
    ]


if __name__ == "__main__":
    print("\n".join(commands()))
