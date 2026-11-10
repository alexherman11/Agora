"""Read-only live adapter for the compact crew lens; no writer or service.

Only existing house/plan publications, witnessed usage and world names are read.
The legacy source ABI receives Desk; no module callable receives it. Runtime
observations are not permission, delivery proof, billing or token consumption.
"""

import json
import math
import re
import time
from datetime import UTC, datetime
from pathlib import Path

from data_graphics import graphic
from world import Refusal

USAGE = "crew:summary|residents|workers|inactive|quota"
ARG = "needed"
FIELDS = (
    "item",
    "rid",
    "key",
    "title",
    "worker_name",
    "doing",
    "state",
    "model",
    "picture",
    "percent",
    "detail",
    "status",
    "clock",
    "counts",
    "freshness",
    "inactive_count",
)
ROOT = Path(__file__).resolve().parents[1] / "house-state"


def number(value):
    return (
        value
        if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
        else None
    )


def iso(value):
    try:
        return (
            datetime.fromtimestamp(value, UTC).strftime("%d %b %H:%M UTC")
            if number(value) is not None
            else "unknown"
        )
    except (OverflowError, OSError, ValueError):
        return "unknown"


def load(path):
    try:
        if path.stat().st_size > 2_000_000:
            return {}
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def mark(label, value, state, basis):
    result = graphic(
        dict(
            title=label,
            mode="bars",
            unit="%",
            maximum=100,
            corner_radius=0,
            mark_height=28,
            basis=basis,
            state=state,
            records=[
                dict(
                    label=label,
                    value=value,
                    role="chart.full"
                    if value is not None and value >= 100
                    else "chart.warn"
                    if value is not None and value >= 80
                    else "chart.ok",
                )
            ],
        )
    )
    part = result["parts"][0] if result["parts"] else {}
    return dict(
        picture=part.get("picture", ""),
        status=result["status"],
        percent="unknown"
        if value is None
        else "error"
        if result["status"] == "error"
        else f"{value:g}%",
    )


def compose(house, usage, plans, names, queued, now):
    """Pure explicit-input projection, also exercised with adversarial fixtures."""
    beat = number(house.get("beat"))
    stale = beat is None or not -5 <= now - beat < 30
    residents = house.get("residents")
    workers = house.get("workers")
    residents = (
        residents
        if isinstance(residents, dict) and all(isinstance(r, dict) for r in residents.values())
        else None
    )
    workers = (
        workers
        if isinstance(workers, dict) and all(isinstance(r, dict) for r in workers.values())
        else None
    )
    usage_at = number(usage.get("at")) if isinstance(usage, dict) else None
    usage_rows = usage.get("rows", []) if isinstance(usage, dict) else []
    if not isinstance(usage_rows, list) or usage_at is None or usage_at > now + 5:
        usage_rows = []
    context = {
        r.get("corner"): r for r in usage_rows if isinstance(r, dict) and r.get("kind") == "agent"
    }
    active = {
        k: r
        for k, r in (workers or {}).items()
        if isinstance(r, dict) and r.get("doing") in ("working", "waiting")
    }
    inactive = len(workers) - len(active) if workers is not None else 0
    counts = (
        f"residents {len(residents) if residents is not None else '?'} | "
        f"workers {len(active) if workers is not None else '?'}/"
        f"{len(workers) if workers is not None else '?'} active | queue {queued}"
    )
    out = {k: [] for k in ("summary", "residents", "workers", "inactive", "quota")}
    out["summary"] = [
        dict(
            item="",
            key="summary",
            title="Crew observatory",
            clock=iso(now),
            counts=counts,
            status="stale" if stale else "ready",
            inactive_count=inactive,
            freshness=f"{'STALE / ' if stale else 'reported / '}house {iso(beat)}"
            " / context measurement age unknown",
            detail="Context is last provider-reported tokens / capacity, "
            "not cumulative consumption. "
            "Usage publication time is not measurement time. Account quotas are separate. "
            "Active includes working and waiting workers. No hidden thinking is inspected.",
        )
    ]
    for group, members in (("residents", residents), ("workers", workers)):
        if members is None:
            out[group].append(
                dict(
                    item="",
                    key=group + ".unknown",
                    title="Telemetry unavailable",
                    worker_name="Unknown",
                    doing="unknown",
                    state="unknown",
                    model="?",
                    picture="",
                    percent="unknown",
                    status="unknown",
                    detail="No valid house publication for this group.",
                )
            )
        for key, runtime in sorted((members or {}).items()):
            if not isinstance(runtime, dict):
                continue
            observed = context.get(key, {})
            title = names.get(key) or (
                runtime.get("actor", "").title()
                if group == "residents"
                else "Task name unavailable"
            )
            title = str(title)[:240]
            tokens, capacity = number(observed.get("tokens")), number(observed.get("window"))
            value = (
                round(tokens / capacity * 100, 1)
                if tokens is not None and tokens >= 0 and capacity is not None and capacity > 0
                else None
            )
            if value is not None and not math.isfinite(value):
                value = None
            state = "unknown" if value is None else "stale" if stale else "ready"
            display = mark(title, value, state, "reported context; measurement age unknown")
            configured, last = runtime.get("model"), observed.get("model")
            model = str(configured) if configured else ("~" + str(last) if last else "?")
            for full, short in (
                ("gpt-6-astra", "astra"),
                ("gpt-6.1-sol", "sol6.1"),
                ("gpt-6-sol", "sol6"),
                ("claude-opus-5-5", "opus5.5"),
            ):
                model = model.replace(full, short)
            if runtime.get("reasoning"):
                model += "/" + str(runtime["reasoning"])
            doing = runtime.get("doing") or "unknown"
            label = "stale" if stale else "paused" if runtime.get("status") == "paused" else doing
            detail = (
                f"{title}. Reported activity: {doing}; status: {runtime.get('status', 'unknown')}; "
                f"alive flag: {runtime.get('alive', 'unknown')}; "
                f"turns: {runtime.get('turns', 'unknown')}. "
                f"Context: {tokens if tokens is not None else 'unknown'} / "
                f"{capacity if capacity is not None else 'unknown'}; "
                f"capacity source: {observed.get('window_from', 'unknown')}; "
                f"last context model: {last or 'unknown'}. "
                f"Configured model: {configured or 'unknown'}; usage published: {iso(usage_at)}; "
                "measurement age unknown. "
                f"House observed: {iso(beat)}. Retry: {iso(runtime.get('retry_at'))}. "
                f"Recovery needed: {runtime.get('recovery_needed', 'unknown')}."
            )
            worker = (
                re.sub(r"-?builder-?", " ", str(runtime.get("builder") or "Worker")).strip().title()
            )
            if worker.isdecimal():
                worker = "Worker " + worker
            elif not worker:
                worker = "Worker"
            target = "inactive" if group == "workers" and key not in active else group
            out[target].append(
                dict(
                    item=key if key in names else "",
                    key=key,
                    title=title,
                    worker_name=worker,
                    doing=doing,
                    state=label,
                    model=model,
                    detail=detail,
                    **display,
                )
            )
    windows = plans.get("windows") if isinstance(plans.get("windows"), dict) else {}
    for key, row in sorted(windows.items()):
        if not isinstance(row, dict):
            continue
        value, reset, at = (
            number(row.get("percent")),
            number(row.get("resets")),
            number(row.get("asof")),
        )
        if reset is None or reset <= now or at is None or at > now + 5:
            value = None
        label = (
            str(row.get("provider") or "Unknown").title()
            + " "
            + str(row.get("label") or "window").replace(" hours", "h").replace(" days", "d")
        )
        display = mark(
            label,
            value,
            "unknown" if value is None else "stale" if stale else "ready",
            "account quota; reported used percent",
        )
        out["quota"].append(
            dict(
                item="",
                key=key,
                title=label,
                detail=f"Observed: {iso(at)}; resets: {iso(reset)}; "
                f"source: {row.get('source', 'unknown')}. Account-wide, not agent context.",
                **display,
            )
        )
    if not out["quota"]:
        out["quota"] = [
            dict(
                item="",
                key="quota.unknown",
                title="Account quota",
                picture="",
                percent="unknown",
                status="unknown",
                detail="No provider quota observations available.",
            )
        ]
    for group in out.values():
        for row in group:
            row["rid"] = row["key"]
    return out


def rows(desk, arg, session):
    if arg not in ("summary", "residents", "workers", "inactive", "quota"):
        raise Refusal(USAGE)
    world = str(session or getattr(desk, "_session", "")).split("@")[0]
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_-]{0,63}", world):
        return compose({}, None, {}, {}, "unknown", time.time())[arg]
    house = load(ROOT / world / "house.json")
    if house.get("world") != world:
        house = {}
    import witnessed

    try:
        usage = witnessed.read(world, "usage")
    except (OSError, ValueError, TypeError, OverflowError):
        usage = None
    names = {}
    for group in ("residents", "workers"):
        members = house.get(group)
        for key in members if isinstance(members, dict) else {}:
            node = desk.world.nodes.get(key, {})
            subject = desk.world.subjects.get(node.get("subject"), {})
            title = subject.get("title") or node.get("title")
            if title:
                names[key] = title
    queued = sum(
        (s.get("props") or {}).get("commission") == "asked" for s in desk.world.subjects.values()
    )
    return compose(
        house, usage, load(ROOT / world / "plan-usage.json"), names, queued, time.time()
    )[arg]
