"""charts:<note>: reusable bars, segmented composition and line graphics.

The note's text is a JSON object described in data-dashboard/README.md. The row
exposes words and SVG together, composed with ordinary text/picture/role/fold.
"""
import json

from data_graphics import graphic
from world import Refusal

USAGE = "charts:<note>[/marks]"
FIELDS = ("item", "title", "summary", "detail", "picture", "status", "count", "known", "label", "value_text")
ARG = "needed"


def rows(desk, arg, session):
    import scene
    marks = arg.endswith("/marks")
    if marks:
        arg = arg[:-6]
    try:
        nid = desk._resolve(arg)
        subject = desk.world.subjects.get(desk.world.subject_of(nid))
        if subject is None:
            raise ValueError("chart definition must be a note")
        raw = subject.get("text", "")
        if len(raw) > 100_000:
            raise ValueError("chart definition exceeds 100,000 characters")
        config = json.loads(raw)
        if not isinstance(config, dict):
            raise ValueError("chart definition must be an object")
        config = dict(config)
        config.setdefault("title", subject["title"])
        records = None
        if "source" in config:
            source = config["source"]
            if not isinstance(source, str) or scene.source_head(source) == "charts":
                raise ValueError("source must name a non-chart row source")
            source_rows = scene.rows(desk, source, session)
            if source_rows is None:
                raise ValueError("unknown row source")
            if not source_rows:
                config.update(state="unknown", note="Source supplied no observations; empty and unavailable cannot be distinguished by this row contract")
            fields = config.get("fields", {})
            if not isinstance(fields, dict):
                raise ValueError("fields must map label/value/x/role to row field names")
            records = [{k: row.get(fields.get(k, k)) for k in ("label", "value", "role")}
                       | ({"x": row.get(fields["x"])} if "x" in fields else {}) for row in source_rows]
        result = graphic(config, records)
        parts = result.pop("parts")
        if marks:
            return [dict(item=nid, title=config["title"], summary=result["summary"], count=result["count"], known=result["known"], **part) for part in parts]
        return [dict(item=nid, title=config["title"], **result)]
    except (ValueError, TypeError, KeyError, Refusal) as exc:
        result = graphic(dict(title="Chart unavailable", state="error", note=str(exc)))
        result.pop("parts")
        return [dict(item=arg, title="Chart unavailable", **result)]
