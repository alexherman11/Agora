"""Two surface adapters share a proposal protocol, not a universal geometry schema."""

import math

from model import Refusal, key, operation


@operation
def partition(builder, surface, project, pinned):
    """Exact-scene policy: membership and all classification inputs are guarded.

    This is an explicit tag resolver, NOT a model of semantic search accuracy.
    Pin wins over project membership, so operation target sets are disjoint.
    """
    members = builder.surface(surface)
    if pinned not in members:
        raise Refusal("Pinned conversation has no occurrence in the selected surface")
    related, remainder = [], []
    for item in members:
        binding = builder.occurrence(surface, item)
        tags = builder.read(key("subject", binding["subject"], "tags"))
        if item == pinned:
            continue
        (related if project in tags else remainder).append(item)
    builder.describe(
        "selection.partition",
        surface,
        members,
        project=project,
        pinned=pinned,
        related=related,
        remainder=remainder,
        policy="exact-scene",
    )
    return related, [pinned], remainder


def free(builder, surface, item):
    builder.occurrence(surface, item)
    placement = builder.read(key("occurrence", item, "placement"))
    if placement["mode"] != "free":
        raise Refusal("Placement is maintained; choose reorder, detach, or edit the rule")
    return placement


@operation
def place(builder, surface, item, rect):
    free(builder, surface, item)
    minimum = builder.read(key("occurrence", item, "minimum"))
    if len(rect) != 4 or any(type(n) not in (int, float) or not math.isfinite(n) for n in rect):
        raise Refusal("Placement requires finite geometry")
    if rect[2] < minimum[0] or rect[3] < minimum[1]:
        raise Refusal("Placement is smaller than the declared minimum")
    builder.effect(key("occurrence", item, "placement"), {"mode": "free", "rect": rect})
    builder.describe("place", surface, [item], rect=rect)


@operation
def tile(builder, surface, targets, region, columns, measurement):
    if len(set(targets)) != len(targets):
        raise Refusal("Repeated occurrence in tile request")
    frame = builder.read(key("measurement", measurement, "frame"))
    if not frame["active"] or frame["surface"] != surface:
        raise Refusal("No current measurement for the target surface and view")
    # This first adapter uses untransformed local CSS pixels only.
    if frame["transform"] != [1, 0, 0, 1, 0, 0]:
        raise Refusal("This adapter cannot interpret the measured coordinate transform")
    x, y, width, height = region
    if (
        min(x, y) < 0
        or width <= 0
        or height <= 0
        or x + width > frame["width"]
        or y + height > frame["height"]
    ):
        raise Refusal("Requested region is outside the measured viewport")
    if type(columns) is not int or columns < 1:
        raise Refusal("Columns must be a positive integer")
    if not targets:
        builder.diagnostics.append("Empty tile selection; no placement changes")
        return
    targets = sorted(targets)  # Selection serialization order is not reading order.
    rows, gap = math.ceil(len(targets) / columns), 12
    w, h = (width - (columns - 1) * gap) / columns, (height - (rows - 1) * gap) / rows
    for index, item in enumerate(targets):
        free(builder, surface, item)
        minimum = builder.read(key("occurrence", item, "minimum"))
        if w < minimum[0] or h < minimum[1]:
            raise Refusal(
                "Tile cannot fit declared minimum sizes; choose scrolling, grouping, or another region"
            )
        rect = [
            x + (index % columns) * (w + gap),
            y + (index // columns) * (h + gap),
            w,
            h,
        ]
        builder.effect(key("occurrence", item, "placement"), {"mode": "free", "rect": rect})
    builder.describe(
        "tile",
        surface,
        targets,
        region=region,
        columns=columns,
        measurement=measurement,
    )


@operation
def layer(builder, surface, targets, direction):
    if direction not in ("sink", "raise"):
        raise Refusal("Unknown stacking operation")
    groups = {}
    for item in targets:
        builder.occurrence(surface, item)
        stratum = builder.read(key("occurrence", item, "stratum"))
        groups.setdefault(stratum, set()).add(item)
    for stratum, selected in groups.items():
        address = key("surface", surface, "stack:" + stratum)
        stack = builder.read(address)
        other = set(stack) - selected
        edges = {(a, b) if direction == "sink" else (b, a) for a in selected for b in other}
        builder.ordering(address, edges)
    builder.describe(direction, surface, targets, scope="within-each-existing-stratum")


@operation
def reorder(builder, surface, targets, before):
    members = builder.surface(surface)
    builder.read(key("surface", surface, "reading_order"))
    if not set(targets) <= set(members) or before not in members or before in targets:
        raise Refusal("Invalid list reorder")
    for item in targets + [before]:
        builder.occurrence(surface, item)
    for target in targets:
        builder.ordering(key("surface", surface, "reading_order"), {(target, before)})
    builder.describe("order.before", surface, targets, before=before)


@operation
def detach(builder, surface, item, rect):
    builder.occurrence(surface, item)
    builder.effect(key("occurrence", item, "placement"), {"mode": "free", "rect": rect})
    builder.describe("placement.detach", surface, [item], rect=rect)


def representative(builder):
    oas, mail, other = partition(builder, "desk", "oas", "mail")
    tile(builder, "desk", oas, [20, 20, 700, 1100], 2, "human")
    place(builder, "desk", mail[0], [900, 50, 600, 900])
    layer(builder, "desk", other, "sink")
    # Placement alone doesn't guarantee visibility: mail must also be raised.
    layer(builder, "desk", mail, "raise")
    return oas, mail, other
