"""Bounded data graphics for Agora's existing picture + row-source contracts.

World authors supply records, units, provenance and style roles. This module knows
no application, provider, color or endpoint. It emits the same evidence as words
and SVG. No script, foreign objects, URLs or animation are emitted.
"""
import math
import re
from html import escape

MAX_RECORDS = 160
MAX_LABEL = 240


def number(value):
    if isinstance(value, bool) or value is None or value == "":
        return None
    try:
        out = float(value)
        return out if math.isfinite(out) and abs(out) <= 1e15 else None
    except (ValueError, TypeError, OverflowError):
        return None


def word(value):
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(value if value is not None else ""))[:MAX_LABEL]


def fmt(value):
    return "unknown" if value is None else f"{value:,.6g}"


def role(value):
    return "r-" + value.replace(".", "_") if isinstance(value, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{0,63}", value) else ""


def graphic(config, records=None):
    """Return status/summary/detail/picture/count; malformed data is visible.

    mode: bars, stack, line. Records: label, value, role, optional numeric x.
    null/nonfinite values are missing (line gaps). Bars/stack are nonnegative.
    maximum is a fixed scale/capacity, never inferred as capacity. Line x is
    explicitly numeric, or uniformly spaced sample order. No smoothing.
    """
    title = word(config.get("title", "Data"))
    unit = word(config.get("unit", "units"))
    basis = word(config.get("basis", "provenance unknown"))
    mode = config.get("mode", "bars")
    rows = config.get("records", []) if records is None else records
    notes = []
    status = "ready"
    problem = ""
    if mode not in ("bars", "stack", "line"):
        problem = "mode must be bars, stack or line"
    elif not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows):
        problem = "records must be a list of objects"
    elif len(rows) > MAX_RECORDS:
        problem = f"{len(rows)} records exceeds the {MAX_RECORDS} record bound; aggregate explicitly"
    if problem:
        rows = []
        status = "error"
        notes.append(problem)
    normalized = []
    for i, r in enumerate(rows):
        value = number(r.get("value"))
        if value is not None and mode != "line" and value < 0:
            status = "error"
            notes.append("negative values cannot form bars or parts of a whole")
            value = None
        normalized.append(dict(label=word(r.get("label", f"Sample {i + 1}")), value=value,
                               x=number(r.get("x")), role=role(r.get("role") or config.get("role", ""))))
    values = [r["value"] for r in normalized if r["value"] is not None]
    maximum = number(config.get("maximum"))
    radius = number(config.get("corner_radius", 3))
    mark_height = number(config.get("mark_height", 10))
    if radius is None or not 0 <= radius <= 4:
        notes.append("corner_radius must be between 0 and 4")
        status = "error"
        radius = 0
    if mark_height is None or not 4 <= mark_height <= 64:
        notes.append("mark_height must be between 4 and 64")
        status = "error"
        mark_height = 10
    if "maximum" in config and (maximum is None or maximum <= 0):
        notes.append("maximum must be a finite positive number")
        status = "error"
    if not rows and status != "error":
        status = "empty"
        notes.append("No observations")
    elif rows and len(values) < len(rows):
        if status != "error":
            status = "partial" if values else "unknown"
        notes.append(f"{len(rows) - len(values)} unknown; never counted as zero")
    if status != "error" and config.get("state") in ("stale", "error", "unknown"):
        status = config["state"]
        notes.append(word(config.get("note", status)))
    if config.get("as_of"):
        notes.append("Observed " + word(config["as_of"]))
    total = sum(values)
    scale = maximum or (total if mode == "stack" else max(values, default=0)) or 1
    if maximum and ((mode == "stack" and total > maximum) or (mode in ("bars", "line") and any(v > maximum for v in values))):
        status = "error"
        notes.append("values exceed the stated maximum; graphic withheld")
    if mode == "line":
        explicit_x = any("x" in r for r in rows)
        if explicit_x and any(r["x"] is None for r in normalized):
            status = "error"
            notes.append("every sample needs numeric x when x is supplied")
        elif explicit_x and any(a["x"] >= b["x"] for a, b in zip(normalized, normalized[1:])):
            status = "error"
            notes.append("x must strictly increase; samples were not reordered")
        notes.append(word(config.get("x_unit", "sample order")) if not explicit_x else "x: " + word(config.get("x_unit", "units")))
    entries = [f'{r["label"]}: {fmt(r["value"])} {unit}' + (f' at {fmt(r["x"])}' if mode == "line" and r["x"] is not None else "") for r in normalized]
    scale_note = f"maximum {fmt(maximum)} {unit}" if maximum else "scale follows observed values; no capacity supplied"
    summary = f"{title} · {basis} · {status} · {len(values)}/{len(rows)} known"
    detail = "; ".join([summary, scale_note, *notes, *entries])
    # Layout coordinates are dimensionless viewBox units. Colors and fonts are
    # inherited from world style roles by the existing SVG painter.
    width = 400
    height = (58 + len(rows) * 34) if mode == "bars" else (90 + len(rows) * 25 if mode == "stack" else 190)
    height = max(75, height)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">',
           '<title>' + escape(detail) + '</title>']

    def text(x, y, value, **attrs):
        at = " ".join(f'{k.replace("_", "-")}="{escape(str(v), quote=True)}"' for k, v in attrs.items())
        out.append(f'<text x="{x:g}" y="{y:g}" fill="currentColor" {at}>{escape(word(value))}</text>')

    def rect(x, y, w, h, cls="", opacity=1):
        out.append(f'<rect x="{x:.3f}" y="{y:.3f}" width="{max(0, w):.3f}" height="{h:g}" rx="{radius:g}" ry="{radius:g}" fill="currentColor" opacity="{opacity}" class="{cls}"/>')

    text(0, 17, title[:42], font_size=16, font_weight=600)
    text(0, 37, f'{basis} · {unit}'[:62], font_size=12)
    if status in ("empty", "error", "unknown"):
        text(0, 62, " · ".join(notes) or status, font_size=12)
    elif mode == "bars":
        for i, r in enumerate(normalized):
            y = 58 + i * 34
            label = r["label"] if len(r["label"]) <= 38 else r["label"][:37] + "…"
            text(0, y, label, font_size=13)
            text(400, y, fmt(r["value"]), text_anchor="end", font_size=13)
            rect(0, y + 7, 400, 8, opacity=.09)
            if r["value"] is not None:
                rect(0, y + 7, r["value"] / scale * 400, 8, r["role"])
    elif mode == "stack":
        rect(0, 51, 400, 18, opacity=.09)
        x = 0
        for i, r in enumerate(normalized):
            if r["value"] is not None:
                w = r["value"] / scale * 400
                rect(x, 51, w, 18, r["role"])
                x += w
            rect(0, 86 + i * 25, 10, 10, r["role"], 1 if r["value"] is not None else .2)
            text(19, 95 + i * 25, f'{r["label"][:32]} · {fmt(r["value"])} {unit}', font_size=13)
        if maximum and total < maximum:
            notes.append(f"unassigned {fmt(maximum - total)} {unit}; not assumed free")
    else:
        lo, hi = min(0, min(values, default=0)), maximum or max(0, max(values, default=0))
        if hi == lo:
            hi = lo + 1
        xs = [r["x"] if explicit_x else i for i, r in enumerate(normalized)]
        xlo, xhi = min(xs, default=0), max(xs, default=1)
        if xhi == xlo:
            xhi = xlo + 1
        text(0, 63, fmt(hi), font_size=11)
        text(0, 170, fmt(lo), font_size=11)
        segments = []
        run = []
        for r, x in zip(normalized, xs):
            if r["value"] is None:
                if run:
                    segments.append(run)
                run = []
                continue
            px, py = 45 + (x-xlo)/(xhi-xlo)*350, 155 - (r["value"]-lo)/(hi-lo)*95
            run.append(f"{px:.3f},{py:.3f}")
            out.append(f'<circle cx="{px:.3f}" cy="{py:.3f}" r="3" fill="currentColor" class="{r["role"]}"/>')
        if run:
            segments.append(run)
        for run in segments:
            out.append(f'<polyline points="{" ".join(run)}" fill="none" stroke="currentColor" stroke-width="2" class="{role(config.get("role", ""))}"/>')
        text(45, 182, normalized[0]["label"][:28] if normalized else "", font_size=12)
        text(395, 182, normalized[-1]["label"][:28] if normalized else "", text_anchor="end", font_size=12)
    out.append('</svg>')
    detail = "; ".join([summary, scale_note, *notes, *entries])
    # Include final notes (e.g. unassigned capacity) in the accessible name too.
    out[1] = '<title>' + escape(detail) + '</title>'
    parts = []
    if mode == "bars" and status not in ("empty", "error"):
        for r in normalized:
            value = r["value"]
            bar = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 {mark_height:g}"><title>' + escape(f'{r["label"]}: {fmt(value)} {unit}; {basis}; {status}') + '</title>'
            bar += f'<rect width="400" height="{mark_height:g}" rx="{radius:g}" ry="{radius:g}" fill="currentColor" opacity=".09"/>'
            if value is not None:
                bar += f'<rect width="{value / scale * 400:.3f}" height="{mark_height:g}" rx="{radius:g}" ry="{radius:g}" fill="currentColor" class="{r["role"]}"/>'
            parts.append(dict(label=r["label"], value_text=f'{fmt(value)} {unit}', picture=bar + '</svg>',
                              status="unknown" if value is None else status, detail=detail))
    return dict(status=status, summary=summary, detail=detail, picture="".join(out), count=len(rows), known=len(values), parts=parts)
