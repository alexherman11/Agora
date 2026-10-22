"""Separately supplied reviewed capabilities, not part of the composition host.

Interval arithmetic and graphics deliberately use different ports. The presenter
owns the conversion between them. The frame is recursive through a typed slot.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import data_graphics
from capability_modules import Definition, Output, Port, Registry, Slot, plain


def obj(properties, required=()):
    return dict(
        type="object", properties=properties, required=list(required), additionalProperties=False
    )


NUMBER = dict(type="number", minimum=-1e12, maximum=1e12)
TEXT = dict(type="string", maxLength=1000)
INTERVALS = Port.of(
    "intervals.v1",
    obj(
        {
            "intervals": dict(
                type="array",
                maxItems=160,
                items=obj({"start": NUMBER, "end": NUMBER}, ("start", "end")),
            ),
            "title": TEXT,
            "unit": TEXT,
        },
        ("intervals",),
    ),
)
COVERAGE = Port.of(
    "coverage.v1",
    obj(
        {
            "duration": dict(type="number", minimum=0),
            "merged": dict(
                type="array",
                maxItems=160,
                items=dict(type="array", items=NUMBER, minItems=2, maxItems=2),
            ),
            "count": dict(type="integer", minimum=0),
        },
        ("duration", "merged", "count"),
    ),
)
GRAPHICS_INPUT = Port.of(
    "graphic-request.v1",
    obj(
        {
            "config": dict(type="object"),
            "records": dict(type="array", maxItems=160, items=dict(type="object")),
        },
        ("config", "records"),
    ),
)
GRAPHICS_OUTPUT = Port.of(
    "graphic-result.v1",
    obj(
        {
            "status": dict(enum=["ready", "partial", "unknown", "empty", "error", "stale"]),
            "summary": TEXT,
            "detail": dict(type="string", maxLength=100000),
            "picture": dict(type="string", maxLength=200000),
            "count": dict(type="integer", minimum=0),
            "known": dict(type="integer", minimum=0),
            "parts": dict(type="array", maxItems=160, items=dict(type="object")),
        },
        ("status", "summary", "detail", "picture", "count", "known", "parts"),
    ),
)
ROWS = Port.of(
    "rows.v1",
    dict(
        type="array",
        maxItems=160,
        items=obj(
            {
                "key": TEXT,
                "title": TEXT,
                "summary": TEXT,
                "detail": dict(type="string", maxLength=100000),
                "picture": dict(type="string", maxLength=200000),
                "status": dict(enum=["ready", "partial", "unknown", "empty", "error", "stale"]),
            },
            ("key", "title", "summary", "detail", "picture", "status"),
        ),
    ),
)
COMPUTE = frozenset({"compute.intervals"})
DRAW = frozenset({"render.graphics"})
BOTH = COMPUTE | DRAW


def union_intervals(context, value):
    merged = []
    for interval in sorted(value["intervals"], key=lambda row: (row["start"], row["end"])):
        start, end = interval["start"], interval["end"]
        if start > end:
            return Output(None, "error", "interval end precedes start")
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return Output(
        dict(duration=sum(b - a for a, b in merged), merged=merged, count=len(value["intervals"])),
        "ready" if merged else "empty",
    )


def graphics(context, value):
    # The independently supplied function accepts mutable dict/list. It gets a
    # fresh local copy, never a Desk, caller's object or mutable shared context.
    request = plain(value)
    if context.input_status == "stale" and request["config"].get("state", "ready") == "ready":
        request["config"]["state"] = "stale"
        request["config"].setdefault(
            "note", "Retained upstream observation; freshness is not confirmed"
        )
    result = data_graphics.graphic(request["config"], request["records"])
    return Output(result, result["status"], result["detail"])


def coverage_view(context, value):
    measure = context.child("measure", value)
    if measure.value is None:
        return measure
    data = measure.value
    unit = value.get("unit", "units")
    title = value.get("title", "Covered time")
    chart = context.child(
        "draw",
        dict(
            config=dict(mode="bars", title=title, unit=unit, basis="union of explicit intervals"),
            records=[dict(label="Covered", value=data["duration"], role="good")],
        ),
    )
    if chart.value is None:
        return chart
    rendered = chart.value
    # Empty is evidence of an explicit empty input, not inferred producer health.
    status = "empty" if measure.status == "empty" else chart.status
    return Output(
        [
            dict(
                key="coverage",
                title=title,
                summary=f"Covered: {data['duration']:g} {unit}",
                detail=f"{data['count']} intervals; merged: {plain(data['merged'])}. "
                + rendered["detail"],
                picture=rendered["picture"],
                status=status,
            )
        ],
        status,
    )


def frame(context, value):
    child = context.child("body", value)
    if child.value is None:
        return child
    rows = plain(child.value)
    for row in rows:
        row["detail"] = "Framed composition. " + row["detail"]
    return Output(rows, child.status, child.detail)


def definitions():
    # Pin the actual supplied implementation AND its independently owned graphics
    # dependency. Source edits change pins, even if someone forgets a version bump.
    own = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    graphics_artifact = hashlib.sha256(
        Path(__file__).read_bytes() + Path(data_graphics.__file__).read_bytes()
    ).hexdigest()
    return (
        Definition("intervals.union", "1", own, INTERVALS, COVERAGE, union_intervals, COMPUTE),
        Definition(
            "graphics.draw", "1", graphics_artifact, GRAPHICS_INPUT, GRAPHICS_OUTPUT, graphics, DRAW
        ),
        Definition(
            "coverage.view",
            "1",
            own,
            INTERVALS,
            ROWS,
            coverage_view,
            slots={
                "measure": Slot(INTERVALS, COVERAGE, COMPUTE),
                "draw": Slot(GRAPHICS_INPUT, GRAPHICS_OUTPUT, DRAW),
            },
        ),
        Definition(
            "rows.frame",
            "1",
            own,
            INTERVALS,
            ROWS,
            frame,
            slots={"body": Slot(INTERVALS, ROWS, BOTH)},
        ),
    )


def registry():
    return Registry(definitions(), grants=BOTH)


def coverage_document(registry, frames=2):
    """Example authoring helper; serialized output contains exact pins, not code."""
    nodes = {
        "view": registry.binding(
            "coverage.view@1", grants=BOTH, children=dict(measure="measure", draw="graphic")
        ),
        "measure": registry.binding("intervals.union@1", grants=COMPUTE),
        "graphic": registry.binding("graphics.draw@1", grants=DRAW),
    }
    root = "view"
    for n in range(frames):
        name = f"frame{n}"
        nodes[name] = registry.binding("rows.frame@1", grants=BOTH, children=dict(body=root))
        root = name
    return dict(root=root, nodes=nodes)
