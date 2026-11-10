"""Which theme applies to a person, and what each surface is told about it.

Things in the world (all plain facts, all undoable):
    kind=theme            name, title, text = the theme as canonical JSON (model.py). Made by anyone, seen by the place or
                          a group; kits carry it.
    kind=theme-settings   active = <theme>. The place's default. Only the one a steward made counts.
    kind=theme-choice     theme = <theme> | place, trial = <theme>, trial_until = <UTC time>. One per person, private
                          (sees=person:<them>): "just for me", and a theme being tried for 30 seconds.

A person sees, in this order: the theme they are trying (until its time), their own choice, the place's default, and
finally the built-in Seabright Day, so there is always a look even in a world nobody has themed.

`pick` is pure (data in, answer out) so the `theme` module, which only reads rows, and the door, which reads the kernel,
answer identically. `payload` compiles what a page, a widget and the window manager each need.
"""
import hashlib
import json
import threading
from datetime import datetime, timezone

from . import compile as K
from . import model as M

_BUILTIN = {}
_COMPILED = {}
_LOCK = threading.Lock()


def builtin():
    """Seabright Day, the look nothing can take away."""
    with _LOCK:
        if "theme" not in _BUILTIN:
            from . import starters
            _BUILTIN["theme"] = M.check(starters.seabright_day())
        return _BUILTIN["theme"]


def parse_time(text):
    try:
        t = datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def pick(settings, choices, person, now):
    """-> (theme id or None, source, trial_until or None).

    settings: [{id, active, steward: bool}], newest last.   choices: [{id, person, theme, trial, trial_until}]."""
    mine = next((c for c in choices if c.get("person") == person), None)
    if mine:
        until = parse_time(mine.get("trial_until")) if mine.get("trial") else None
        if mine.get("trial") and until and now < until:
            return mine["trial"], "trial", until
        if mine.get("theme") and mine["theme"] != "place":
            return mine["theme"], "me", None
    placed = [s for s in settings if s.get("steward") and s.get("active")]
    if placed:
        return placed[-1]["active"], "place", None
    return None, "builtin", None


# --------------------------------------------------------------------------------------------- reading the kernel
def _theme_of(k, t):
    """-> the validated theme in thing t, or None (a refused or missing theme falls back, never breaks a page)."""
    a = k.state.things.get(t) or {}
    if a.get("kind") != "theme" or a.get("forgotten"):
        return None
    try:
        return M.check_text(a.get("text"))
    except M.ThemeError:
        return None


def settings_rows(k):
    out = []
    for t in k.things("theme-settings"):
        a = k.state.things.get(t, {})
        if a.get("forgotten"):
            continue
        owner = a.get("for") or a.get("made_by")
        owner = owner if k.state.get(owner, "kind") == "person" else (k.state.get(owner, "for") or owner)
        out.append({"id": t, "active": a.get("active"), "steward": bool(owner) and k.is_steward(owner)})
    return out


def choice_rows(k):
    out = []
    for t in k.things("theme-choice"):
        a = k.state.things.get(t, {})
        if a.get("forgotten"):
            continue
        out.append({"id": t, "person": a.get("for") or a.get("made_by"), "theme": a.get("theme"),
                    "trial": a.get("trial"), "trial_until": a.get("trial_until")})
    return out


def applied(k, person):
    """-> (thing id | None, clean theme, source, trial_until) as this person sees the desktop now."""
    with k.lock:
        tid, source, until = pick(settings_rows(k), choice_rows(k), person, k.now())
        theme = _theme_of(k, tid) if tid else None
        if theme is None:
            tid, source, until, theme = None, "builtin", None, builtin()
        elif source in ("me", "trial") and k.shown(person, tid) is None:
            # a choice names a theme its person may not see: never serve it (a private theme stays private)
            tid, source, until, theme = None, "builtin", None, builtin()
        return tid, theme, source, until


def _compiled(theme, base):
    key = (M.digest(theme), base)
    got = _COMPILED.get(key)
    if got is None:
        r = M.resolve(theme)
        digest = key[0]
        w = r["wallpaper"]
        url = None
        if w.get("kind") in ("svg", "image"):
            url = f"{base}theme-wallpaper?h={digest}"
        got = {"digest": digest, "resolved": r, "css": K.css(r, url, digest), "native": K.native(r, digest),
               "legacy": K.legacy(r), "wallpaper_url": url}
        if len(_COMPILED) > 64:
            _COMPILED.clear()
        _COMPILED[key] = got
    return got


def payload(k, person, base="/desk/"):
    """Everything a surface is told, for `person` (None: nobody signed in, so the place's look)."""
    tid, theme, source, until = applied(k, person)
    c = _compiled(theme, base)
    r = c["resolved"]
    return {"hash": hashlib.sha1((c["digest"] + source + (until.isoformat() if until else "")).encode()).hexdigest()[:12],
            "theme": tid, "name": r["meta"]["name"], "source": source,
            "until": until.isoformat() if until else None, "variant": r["variant"], "css": c["css"],
            "tokens": c["legacy"], "font": r["type"]["ui"], "palette": r["palette"], "roles": r["roles"],
            "native": c["native"], "wallpaper_url": c["wallpaper_url"], "digest": c["digest"]}


def wallpaper_of(k, person, digest):
    """-> (bytes, content type) of the svg/image wallpaper of the theme this person now wears, if it is `digest`."""
    tid, theme, source, until = applied(k, person)
    if M.digest(theme) != digest:
        return None
    w = theme.get("wallpaper") or {}
    if w.get("kind") == "svg":
        return w["svg"].encode("utf-8"), "image/svg+xml"
    if w.get("kind") == "image":
        head, _, b64 = w["image"].partition(",")
        import base64
        return base64.b64decode(b64), head[5:].split(";")[0]
    return None


# --------------------------------------------------------------------------------------------- serving
def route(k, person, name, query, base="/desk/", if_none_match=None):
    """The door's theme routes. -> (status, body bytes, content type, extra headers)."""
    if name == "theme-wallpaper":
        got = wallpaper_of(k, person, query.get("h", ""))
        if not got:
            return 404, b'{"error": "no such wallpaper"}', "application/json", []
        return 200, got[0], got[1], [("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; sandbox"),
                                      ("X-Content-Type-Options", "nosniff")]
    p = payload(k, person, base)
    etag = f'"{p["hash"]}"'
    headers = [("ETag", etag)]
    if if_none_match == etag:
        return 304, b"", "text/plain", headers
    if name == "theme.css":
        return 200, p["css"].encode("utf-8"), "text/css; charset=utf-8", headers
    if name == "theme-native.json":
        body = dict(p["native"], source=p["source"], until=p["until"])
        return 200, json.dumps(body, indent=1).encode("utf-8"), "application/json", headers
    if name == "theme.json":
        body = {k_: p[k_] for k_ in ("hash", "theme", "name", "source", "until", "variant", "css", "tokens", "font",
                                     "palette", "roles", "wallpaper_url")}
        return 200, json.dumps(body).encode("utf-8"), "application/json", headers
    return 404, b'{"error": "no such route"}', "application/json", []


ROUTES = ("theme.css", "theme.json", "theme-native.json", "theme-wallpaper")
