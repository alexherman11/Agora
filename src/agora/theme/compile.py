"""Compile a resolved theme into what each surface reads (CONTRACTS section 1):

    css(resolved)        theme.css: the `--ag-*` variables, one vocabulary for every web surface
    native(resolved)     theme-native.json: window gaps, border width, corner and state colours for the window manager
    legacy(resolved)     the component painter's older tokens (paper, card, ink, muted, accent, red ...) as roles
    scope(resolved)      the same variables as a dict, for painting a preview of a theme inside another theme

Everything here is a pure function of the theme, so equal themes give byte-equal output in any world.
"""
import re

from . import colour as C
from . import model as M

WALLPAPER_SIZE = {"cover": "cover", "contain": "contain", "fill": "100% 100%", "tile": "auto"}


def _stop(colour, pal):
    if colour == "transparent":
        return "transparent"
    ref, _, pct = colour.partition("@")
    h = ref.lower() if M.HEX.fullmatch(ref) else pal[M.slot_name(ref)]
    return C.rgba(h, int(pct) / 100) if pct else h


def gradient(layers, pal):
    """CSS background layers, topmost first, from a validated gradient wallpaper."""
    parts = []
    for layer in layers:
        stops = ", ".join(f"{_stop(c, pal)} {p:g}%" for c, p in layer["stops"])
        if layer["type"] == "linear":
            parts.append(f"linear-gradient({layer['angle']:g}deg, {stops})")
        else:
            x, y = layer["at"]
            parts.append(f"radial-gradient({layer['size']} at {x:g}% {y:g}%, {stops})")
    return ", ".join(parts)


def wallpaper_css(r, url=None):
    """-> (background value, size, repeat). `url` is where the host serves an svg or image wallpaper."""
    w = r["wallpaper"]
    kind = w.get("kind", "none")
    if kind == "gradient":
        return gradient(w["layers"], r["palette"]), WALLPAPER_SIZE[w.get("fit", "cover")], "no-repeat"
    if kind in ("svg", "image") and url:
        repeat = "repeat" if w.get("fit") == "tile" else "no-repeat"
        return f'url("{url}")', WALLPAPER_SIZE[w.get("fit", "cover")], repeat
    return "none", "cover", "no-repeat"


def wallpaper_uri(r):
    """An svg or image wallpaper as a data: address (for previews inside a sandboxed page), else None."""
    import base64
    w = r["wallpaper"]
    if w.get("kind") == "svg":
        return "data:image/svg+xml;base64," + base64.b64encode(w["svg"].encode("utf-8")).decode("ascii")
    if w.get("kind") == "image":
        return w["image"]
    return None


def soft(surface, colour, amount):
    return C.mix(surface, colour, amount)


def variables(r, wallpaper_url=None):
    """The `--ag-*` vocabulary, in a stable order."""
    v = {}
    pal, roles = r["palette"], r["roles"]
    for slot in M.SLOTS24:
        v[f"--ag-{slot}"] = pal[slot]
    for role in M.ROLES:
        v[f"--ag-{role}"] = C.rgba(roles[role], r["scrim_pct"] / 100) if role == "scrim" else roles[role]
    surface, ink = roles["surface"], roles["ink"]
    mild = 0.16 if r["variant"] == "dark" else 0.13
    for name in ("accent", "ok", "warn", "danger", "info"):
        v[f"--ag-{name}-soft"] = soft(surface, roles[name], mild)
    v["--ag-hover"] = C.rgba(ink, 0.08)
    v["--ag-active"] = C.rgba(ink, 0.14)
    v["--ag-ink-faint"] = C.mix(roles["ink-muted"], surface, 0.45)
    t = r["type"]
    v["--ag-font-ui"] = _stack(t["ui"])
    v["--ag-font-mono"] = _stack(t["mono"])
    v["--ag-font-display"] = _stack(t["display"])
    v["--ag-text"] = f"{t['size']:g}px"
    v["--ag-scale"] = f"{t['scale']:g}"
    s = r["shape"]
    small, medium, large = M.RADII[s["radius"]]
    v["--ag-radius-s"], v["--ag-radius-m"], v["--ag-radius-l"] = f"{small}px", f"{medium}px", f"{large}px"
    v["--ag-radius-pill"] = "999px"
    v["--ag-border-w"] = f"{s['border']}px"
    v["--ag-gap-inner"], v["--ag-gap-outer"] = f"{s['gap_inner']}px", f"{s['gap_outer']}px"
    v["--ag-bar-height"], v["--ag-dock-size"] = f"{s['bar_height']}px", f"{s['dock_size']}px"
    f = r["surface"]
    v["--ag-bar-opacity"] = f"{f['bar_opacity']:g}"
    v["--ag-window-opacity"] = f"{f['window_opacity']:g}"
    v["--ag-bar-bg"] = C.rgba(roles["bar"], f["bar_opacity"])
    v["--ag-window-bg"] = C.rgba(surface, f["window_opacity"])
    v["--ag-shadow"] = M.SHADOWS[f["shadow"]]
    v["--ag-backdrop"] = "blur(14px) saturate(1.15)" if f["blur"] == "soft" else "none"
    m = r["motion"]
    off = m["reduce"]
    v["--ag-dur-fast"] = "0ms" if off else f"{m['fast']}ms"
    v["--ag-dur-med"] = "0ms" if off else f"{m['medium']}ms"
    v["--ag-dur-slow"] = "0ms" if off else f"{m['slow']}ms"
    v["--ag-ease"] = M.EASES.get(m["ease"], m["ease"])
    for state in M.STATES:
        v[f"--ag-win-{state}"] = r["windows"][state]
    v["--ag-icon-plate"] = r["icons"]["plate_hex"]
    v["--ag-icon-filter"] = "invert(1) brightness(.92)" if r["variant"] == "dark" else "none"   # for dark-on-clear line icons
    bg, size, repeat = wallpaper_css(r, wallpaper_url)
    v["--ag-wallpaper"] = bg
    v["--ag-wallpaper-size"] = size
    v["--ag-wallpaper-repeat"] = repeat
    dim = r["wallpaper"].get("dim", 0)
    v["--ag-wallpaper-dim"] = C.rgba(pal["base00"], dim)
    v["--ag-variant"] = r["variant"]
    return v


def _stack(stack):
    out = []
    for name in stack.split(", "):
        out.append(name if name in M.GENERIC_FONTS else f'"{name}"')
    return ", ".join(out)


def css(r, wallpaper_url=None, digest=""):
    name = re.sub(r"[^A-Za-z0-9 ._\-]", "", r["meta"]["name"])
    lines = [f"/* agora theme: {name} {digest} */", ":root {", f"  color-scheme: {r['variant']};"]
    lines += [f"  {k}: {val};" for k, val in variables(r, wallpaper_url).items()]
    lines.append("}")
    return "\n".join(lines) + "\n"


def scope(r):
    """The variables as a dict for painting this theme inside a page that wears another (a preview card)."""
    out = variables(r)
    out.pop("--ag-wallpaper")
    out["--ag-wallpaper"] = "none"
    return out


def native(r, digest="", name=""):
    s = r["shape"]
    return {"version": 1, "theme": name or r["meta"]["name"], "hash": digest, "variant": r["variant"],
            "gap_inner": s["gap_inner"], "gap_outer": s["gap_outer"], "border_width": s["border"],
            "corner": r["windows"]["corner"], "radius": M.RADII[s["radius"]][1],
            "colors": {state: r["windows"][state] for state in M.STATES},
            "bar_height": s["bar_height"], "dock_size": s["dock_size"], "bar_opacity": r["surface"]["bar_opacity"]}


def legacy(r):
    """The painter's tokens (paper, card, ink, muted, accent, the colour names and shapes) as roles."""
    roles, pal = r["roles"], r["palette"]
    surface = roles["surface"]
    mild = 0.18 if r["variant"] == "dark" else 0.14
    small, medium, large = M.RADII[r["shape"]["radius"]]
    tokens = {"paper": surface, "card": roles["raised"], "ink": roles["ink"], "muted": roles["ink-muted"],
            "accent": roles["accent"], "red": pal["base08"], "orange": pal["base09"], "blue": pal["base0D"],
            "grey": C.mix(roles["ink-muted"], surface, 0.3),
            "rose": soft(surface, pal["base08"], mild), "peach": soft(surface, pal["base09"], mild),
            "sage": soft(surface, pal["base0B"], mild), "sky": soft(surface, pal["base0D"], mild),
            "lilac": soft(surface, pal["base0E"], mild),
            "small": f"{small}px", "medium": f"{medium}px", "large": f"{large}px", "soft": f"{medium}px",
            "round": "50%"}
    # the older widgets were handed upper-case hex; keep that spelling so what they compare and show does not change
    return {k: (v.upper() if isinstance(v, str) and v.startswith("#") else v) for k, v in tokens.items()}
