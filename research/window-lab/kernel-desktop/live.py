"""live: readings that change too often to be facts, painted onto widget things without a record.

Claude (PROOF a13428), 24 Oct 2026. A widget is an ordinary world thing, made, moved and forgotten by lines:

    make kind=widget bar=top side=right shows=cpu label=CPU order=30

What it shows now (CPU 12%, the song playing, the time) is not a fact: writing it into the log every two seconds would
bury the world in noise. So a module that reads the machine writes `<world>/modules/<name>/live.json`
({"cpu": {"text": "12%", ...}, ...}), and when the painter builds a scene, every widget gets the props of the key it
`shows` (value, detail, ...), read at that moment. Nothing is recorded; lens.js repaints on its usual 1.5 s check
when the scene changes. Two keys are worked out here, from the world and the clock: `time` and `feed` (posts made
after the widget's `read` fact: its count of new ones).

This is a desk-side layer over the kernel's painter (painter.Facade.desk_for), not a kernel change. The word the kernel
lacks: a live (unrecorded) aspect a module may supply for things that ask for it.
"""
import json
import re
import time
import icons
from pathlib import Path

STALE_S = 15                      # a reading older than this is shown as gone, not as the last number


def _num(t):
    m = re.search(r"\d+$", t or "")
    return int(m.group()) if m else 0


def readings(k):
    """key -> props, from every module's live.json that is fresh."""
    out = {}
    root = Path(k.dir) / "modules"
    now = time.time()
    for f in root.glob("*/live.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if now - float(d.get("at", 0)) > STALE_S:
            continue
        for key, v in d.items():
            if isinstance(v, dict):
                out[key] = v
    t = time.localtime(now)
    out["time"] = {"value": time.strftime("%H:%M", t), "detail": time.strftime("%a %d %b", t)}
    return out


def _flat(v):
    return {a: (x if isinstance(x, str) else json.dumps(x) if isinstance(x, (list, dict)) else str(x))
            for a, x in v.items() if x is not None}


def install(facade_cls):
    """Wrap the painter's desk_for so widgets carry their live props. Idempotent."""
    if getattr(facade_cls.desk_for, "live", False):
        return
    orig = facade_cls.desk_for

    def desk_for(self, reader):
        d = orig(self, reader)
        k = self.k
        live = None
        for s in d.world.subjects.values():
            if "widget" not in (s.get("tags") or []):
                continue
            if live is None:
                live = readings(k)
            props = s["props"]
            for blank in ("label", "value", "detail", "does"):
                props.setdefault(blank, "")
            key = props.get("shows", "")
            if key == "feed":
                read = _num(props.get("read", ""))
                with k.lock:
                    new = sum(1 for t in k.things("post") if _num(t) > read and not k.state.get(t, "forgotten")
                              and k.shown(reader, t) is not None)
                props.update(value=str(new) if new else "", detail="new" if new else "all read",
                             upto=f"s{max((_num(t) for t in k.things('post')), default=0)}")
            elif key in live:
                props.update(_flat(live[key]))
            props['symbol'] = props.get('symbol') or icons.svg(props.get('icon') or key)
            props['tooltip'] = (props.get('label') or key.capitalize()) + ': ' + props.get('value', '') + ' ' + props.get('detail', '')
            if key == 'media':
                value = props.get('value', '')
                props['value'] = value[:32] + ('…' if len(value) > 32 else '')
        return d
    desk_for.live = True
    facade_cls.desk_for = desk_for
