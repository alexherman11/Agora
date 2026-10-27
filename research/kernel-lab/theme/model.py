"""The theme thing: a closed schema, a validator that says why, and the derived values (CONTRACTS section 1).

A theme is plain data. `validate(obj)` returns the normalised theme or every reason it was refused; nothing is ever
repaired silently into something else. Unsafe things (scripts, remote addresses, font files, oversized assets) have no
place in the schema, so there is nothing to sanitise away: they are simply not accepted.

    theme = {"format": "agora-theme", "version": 1, "meta": {...}, "palette": {"base00": "#rrggbb", ...},
             "roles": {...}, "type": {...}, "shape": {...}, "surface": {...}, "motion": {...}, "windows": {...},
             "icons": {...}, "wallpaper": {...}}

Only `meta.name` and the sixteen palette slots are required. Everything else has a default, and base10 to base17 and
accent-ink are derived when absent.
"""
import base64
import copy
import json
import re

from . import colour as C
from . import svgsafe

FORMAT = "agora-theme"
VERSION = 1
MAX_TEXT = 300_000              # a whole theme, inline assets included, as text (the kernel splits a long line slowly: see THEMES.md)
MAX_IMAGE_BYTES = 150_000       # a raster wallpaper, decoded (about 200 KB as text, which the kernel reads in about a second)
SLOTS16 = [f"base{n:02X}" for n in range(16)]
SLOTS24 = SLOTS16 + [f"base{n:02X}" for n in range(0x10, 0x18)]
ROLES = ["bg", "surface", "raised", "bar", "ink", "ink-muted", "border", "select", "accent", "accent-ink", "ok", "warn",
         "danger", "info", "focus", "scrim"]
ROLE_DEFAULTS = {"bg": "base00", "surface": "base00", "raised": "base01", "bar": "base01", "ink": "base05",
                 "ink-muted": "base04", "border": "base02", "select": "base02", "accent": "base0D",
                 "accent-ink": None, "ok": "base0B", "warn": "base09", "danger": "base08", "info": "base0C",
                 "focus": "base0D", "scrim": "base00@60"}
STATES = ["focused", "unfocused", "pinned", "attention"]
STATE_DEFAULTS = {"focused": "focus", "unfocused": "border", "pinned": "warn", "attention": "danger"}
RADII = {"none": (0, 0, 0), "small": (3, 6, 10), "medium": (8, 12, 16), "large": (12, 18, 28)}
CORNER_FOR = {"none": "square", "small": "small", "medium": "round", "large": "round"}
SHADOWS = {"none": "none", "soft": "0 6px 24px rgba(0, 0, 0, .18)", "deep": "0 14px 44px rgba(0, 0, 0, .38)"}
LICENCES = ["CC-BY-4.0", "CC0-1.0", "CC-BY-SA-4.0", "MIT", "Apache-2.0", "ISC", "Unlicense"]
GENERIC_FONTS = {"serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui", "ui-monospace", "ui-sans-serif",
                 "ui-serif", "ui-rounded", "emoji", "math"}
EASES = {"standard": "cubic-bezier(.2, .7, .2, 1)", "gentle": "cubic-bezier(.4, 0, .2, 1)", "linear": "linear",
         "snappy": "cubic-bezier(.3, 1.3, .5, 1)", "ease-out": "ease-out", "ease-in-out": "ease-in-out"}
FONT_STACKS = {      # what the editor offers; a theme may name any plain family, these are known to be on Windows
    "ui": ["Segoe UI Variable Text, Segoe UI, system-ui, sans-serif", "Segoe UI, system-ui, sans-serif",
           "Calibri, Segoe UI, sans-serif", "Verdana, Geneva, sans-serif", "Trebuchet MS, Segoe UI, sans-serif",
           "Georgia, serif", "Palatino Linotype, Georgia, serif", "Cambria, Georgia, serif",
           "Inter, Segoe UI, sans-serif",
           "Cascadia Mono, Consolas, monospace", "JetBrains Mono, Cascadia Mono, Consolas, monospace",
           "IBM Plex Mono, Cascadia Mono, Consolas, monospace"],
    "mono": ["Cascadia Mono, Consolas, monospace", "Cascadia Code, Consolas, monospace", "Consolas, monospace",
             "JetBrains Mono, Cascadia Mono, Consolas, monospace", "Fira Code, Cascadia Mono, Consolas, monospace",
             "IBM Plex Mono, Cascadia Mono, Consolas, monospace", "Iosevka, Cascadia Mono, Consolas, monospace",
             "Lucida Console, monospace", "Courier New, monospace"],
}
DEFAULT_TYPE = {"ui": FONT_STACKS["ui"][0], "mono": FONT_STACKS["mono"][0], "size": 15, "scale": 1.2}

HEX = re.compile(r"#[0-9a-fA-F]{6}")
SLOT = re.compile(r"base(?:0[0-9A-Fa-f]|1[0-7])")
FAMILY = re.compile(r"[A-Za-z0-9][A-Za-z0-9 _.\-]{0,58}")
TOP = {"format", "version", "meta", "palette", "roles", "type", "shape", "surface", "motion", "windows", "icons",
       "wallpaper"}
SECTION_KEYS = {
    "meta": {"name", "author", "licence", "variant", "tags", "from", "description"},
    "type": {"ui", "mono", "display", "size", "scale"},
    "shape": {"radius", "border", "gap_inner", "gap_outer", "bar_height", "dock_size"},
    "surface": {"bar_opacity", "window_opacity", "shadow", "blur"},
    "motion": {"fast", "medium", "slow", "ease", "reduce"},
    "windows": {"focused", "unfocused", "pinned", "attention", "corner"},
    "icons": {"style", "plate"},
}
NUMBERS = {   # path -> (low, high, integer?)
    "type.size": (11, 22, False), "type.scale": (1.0, 1.6, False),
    "shape.border": (0, 4, True), "shape.gap_inner": (0, 32, True), "shape.gap_outer": (0, 48, True),
    "shape.bar_height": (24, 64, True), "shape.dock_size": (32, 96, True),
    "surface.bar_opacity": (0.2, 1.0, False), "surface.window_opacity": (0.5, 1.0, False),
    "motion.fast": (0, 400, True), "motion.medium": (0, 800, True), "motion.slow": (0, 1500, True),
}
ENUMS = {
    "meta.variant": {"light", "dark", "auto"}, "shape.radius": set(RADII), "surface.shadow": set(SHADOWS),
    "surface.blur": {"none", "soft"}, "windows.corner": {"square", "round", "small"},
    "icons.style": {"native", "plate", "mono"}, "wallpaper.fit": {"cover", "contain", "fill", "tile"},
}


class ThemeError(ValueError):
    """Every reason a theme was refused, each naming where."""

    def __init__(self, errors):
        self.errors = list(errors)
        super().__init__("; ".join(f"{p}: {m}" for p, m in self.errors) or "invalid theme")


def slot_name(s):
    s = str(s)
    if not SLOT.fullmatch(s):
        return None
    return "base" + s[4:].upper()


def font_stack(value, where, errors):
    """A font stack is names only. Returns the normalised 'A, B, generic' string or None."""
    if not isinstance(value, str) or not value.strip() or len(value) > 200:
        errors.append((where, "a font stack is a short list of font family names, like 'Segoe UI, sans-serif'"))
        return None
    names = []
    for raw in value.split(","):
        name = raw.strip().strip("'\"").strip()
        if name.lower() in GENERIC_FONTS:
            names.append(name.lower())
        elif FAMILY.fullmatch(name) and not re.search(r"url|expression|import|script|data|http|javascript", name, re.I):
            names.append(name)
        else:
            errors.append((where, f"{raw.strip()[:40]!r} is not a plain font family name (names only: no files, "
                                  "addresses, brackets, quotes or code)"))
            return None
    if not names or len(names) > 8:
        errors.append((where, "one to eight font family names"))
        return None
    return ", ".join(names)


def colour_ref(value, where, errors, allow_roles=False, alpha=False):
    """A base slot, a #rrggbb colour, or (where allowed) a role name; scrim-style 'slot@pct' when alpha."""
    if not isinstance(value, str):
        errors.append((where, "a colour is a base slot name (base0D), a #rrggbb colour"
                       + (", or a role name" if allow_roles else "")))
        return None
    v = value.strip()
    pct = ""
    if alpha and "@" in v:
        v, _, pct = v.partition("@")
        if not (pct.isdigit() and 0 <= int(pct) <= 100):
            errors.append((where, "the part after @ is a percentage, 0 to 100"))
            return None
        pct = "@" + str(int(pct))
    if HEX.fullmatch(v):
        return v.lower() + pct
    s = slot_name(v)
    if s:
        return s + pct
    if allow_roles and v in ROLES and not pct:
        return v
    errors.append((where, f"{value[:40]!r} is not a base slot, a #rrggbb colour"
                   + (" or a role name" if allow_roles else "")))
    return None


def _num(value, path, errors):
    low, high, integer = NUMBERS[path]
    if isinstance(value, bool):
        errors.append((path, "a number"))
        return None
    if isinstance(value, str):
        try:
            value = float(value)
        except ValueError:
            errors.append((path, "a number"))
            return None
    if not isinstance(value, (int, float)):
        errors.append((path, "a number"))
        return None
    if not (low <= value <= high):
        errors.append((path, f"between {low:g} and {high:g}"))
        return None
    return int(round(value)) if integer else round(float(value), 3)


def _text(value, path, errors, limit):
    if not isinstance(value, str) or not value.strip() or len(value) > limit or not re.fullmatch(
            r"[^\x00-\x1f\x7f<>`\\]+", value):
        errors.append((path, f"plain text, 1 to {limit} characters, with no markup or control characters"))
        return None
    return value.strip()


def _stops(stops, where, errors):
    out = []
    if not isinstance(stops, list) or not 2 <= len(stops) <= 8:
        errors.append((where, "two to eight colour stops, each [colour, position 0-100]"))
        return None
    for i, stop in enumerate(stops):
        if not isinstance(stop, (list, tuple)) or len(stop) != 2:
            errors.append((f"{where}[{i}]", "a stop is [colour, position]"))
            return None
        col, pos = stop
        if col == "transparent":
            c = "transparent"
        else:
            c = colour_ref(col, f"{where}[{i}]", errors, alpha=True)
            if c is None:
                return None
        if isinstance(pos, bool) or not isinstance(pos, (int, float)) or not 0 <= pos <= 100:
            errors.append((f"{where}[{i}]", "a position from 0 to 100"))
            return None
        out.append([c, int(pos) if float(pos) == int(pos) else round(float(pos), 2)])
    return out


def _wallpaper(w, errors):
    if w is None:
        return None
    if not isinstance(w, dict):
        errors.append(("wallpaper", "an object with a kind"))
        return None
    kind = w.get("kind", "none")
    allowed = {"kind", "fit", "dim"}
    if kind == "gradient":
        allowed |= {"layers"}
    elif kind == "svg":
        allowed |= {"svg"}
    elif kind == "image":
        allowed |= {"image"}
    elif kind != "none":
        errors.append(("wallpaper.kind", "none, gradient, svg or image"))
        return None
    for extra in sorted(set(w) - allowed):
        errors.append((f"wallpaper.{extra}", f"not part of a {kind} wallpaper"))
    out = {"kind": kind}
    fit = w.get("fit", "cover")
    if fit not in ENUMS["wallpaper.fit"]:
        errors.append(("wallpaper.fit", "cover, contain, fill or tile"))
    else:
        out["fit"] = fit
    dim = w.get("dim", 0)
    if isinstance(dim, bool) or not isinstance(dim, (int, float)) or not 0 <= dim <= 0.8:
        errors.append(("wallpaper.dim", "a number from 0 to 0.8"))
    else:
        out["dim"] = round(float(dim), 3)
    if kind == "gradient":
        layers = w.get("layers")
        if not isinstance(layers, list) or not 1 <= len(layers) <= 4:
            errors.append(("wallpaper.layers", "one to four gradient layers"))
            return out
        clean_layers = []
        for i, layer in enumerate(layers):
            where = f"wallpaper.layers[{i}]"
            if not isinstance(layer, dict) or layer.get("type") not in ("linear", "radial") or \
                    set(layer) - {"type", "angle", "at", "size", "stops"}:
                errors.append((where, "{type: linear|radial, stops, angle | at, size}"))
                continue
            stops = _stops(layer.get("stops"), where + ".stops", errors)
            if stops is None:
                continue
            item = {"type": layer["type"], "stops": stops}
            if layer["type"] == "linear":
                angle = layer.get("angle", 180)
                if isinstance(angle, bool) or not isinstance(angle, (int, float)) or not -360 <= angle <= 360:
                    errors.append((where + ".angle", "degrees, -360 to 360"))
                    continue
                item["angle"] = int(angle) if float(angle) == int(angle) else round(float(angle), 2)
            else:
                at = layer.get("at", [50, 50])
                if not (isinstance(at, list) and len(at) == 2 and all(
                        isinstance(x, (int, float)) and not isinstance(x, bool) and -50 <= x <= 150 for x in at)):
                    errors.append((where + ".at", "[x%, y%], each -50 to 150"))
                    continue
                item["at"] = [int(x) if float(x) == int(x) else round(float(x), 2) for x in at]
                size = layer.get("size", "farthest-corner")
                if size not in ("closest-side", "farthest-side", "closest-corner", "farthest-corner"):
                    errors.append((where + ".size", "closest-side, farthest-side, closest-corner or farthest-corner"))
                    continue
                item["size"] = size
            clean_layers.append(item)
        out["layers"] = clean_layers
    elif kind == "svg":
        try:
            out["svg"] = svgsafe.clean(w.get("svg"))
        except ValueError as exc:
            errors.append(("wallpaper.svg", str(exc)))
    elif kind == "image":
        image = w.get("image")
        m = re.fullmatch(r"data:image/(png|jpeg|webp);base64,([A-Za-z0-9+/=]+)", image or "")
        if not m:
            errors.append(("wallpaper.image", "an inline data:image/png, jpeg or webp;base64 image (no addresses)"))
        else:
            try:
                data = base64.b64decode(m[2], validate=True)
            except ValueError:
                errors.append(("wallpaper.image", "the image data is not valid base64"))
                return out
            magic = {"png": data[:8] == b"\x89PNG\r\n\x1a\n", "jpeg": data[:3] == b"\xff\xd8\xff",
                     "webp": data[:4] == b"RIFF" and data[8:12] == b"WEBP"}[m[1]]
            if len(data) > MAX_IMAGE_BYTES:
                errors.append(("wallpaper.image",
                               f"larger than {MAX_IMAGE_BYTES // 1000} KB; make the picture smaller"))
            elif not magic:
                errors.append(("wallpaper.image", f"the bytes are not a {m[1]} picture"))
            else:
                out["image"] = image
    return out


def validate(obj):
    """-> (clean theme, warnings). Raises ThemeError listing every refusal."""
    errors, warnings = [], []
    if not isinstance(obj, dict):
        raise ThemeError([("theme", "a theme is an object")])
    for key in sorted(set(obj) - TOP):
        errors.append((key, "not part of the theme schema"))
    if obj.get("format", FORMAT) != FORMAT:
        errors.append(("format", f"must be {FORMAT!r}"))
    if obj.get("version", VERSION) != VERSION:
        errors.append(("version", f"this reader understands version {VERSION}"))
    out = {"format": FORMAT, "version": VERSION}

    meta = obj.get("meta")
    m = {}
    if not isinstance(meta, dict):
        errors.append(("meta", "needs at least a name"))
        meta = {}
    for extra in sorted(set(meta) - SECTION_KEYS["meta"]):
        errors.append((f"meta.{extra}", "not part of the schema"))
    for key, limit in (("name", 60), ("author", 60), ("from", 80), ("description", 280)):
        if key in meta and meta[key] not in ("", None):
            v = _text(meta[key], f"meta.{key}", errors, limit)
            if v is not None:
                m[key] = v
        elif key == "name":
            errors.append(("meta.name", "a theme needs a name"))
    if "licence" in meta and meta["licence"] not in ("", None):
        lic = meta["licence"]
        if isinstance(lic, str) and (lic in LICENCES or re.fullmatch(r"[A-Za-z0-9 .\-+]{2,40}", lic)):
            m["licence"] = lic
        else:
            errors.append(("meta.licence", "a short licence name like CC-BY-4.0"))
    m.setdefault("licence", "CC-BY-4.0")
    variant = meta.get("variant", "auto")
    if variant not in ENUMS["meta.variant"]:
        errors.append(("meta.variant", "light, dark or auto"))
    else:
        m["variant"] = variant
    tags = meta.get("tags", [])
    if not isinstance(tags, list) or len(tags) > 8 or any(
            not isinstance(t, str) or not re.fullmatch(r"[a-z0-9][a-z0-9 \-]{0,23}", t) for t in tags):
        errors.append(("meta.tags", "up to eight short lowercase tags"))
    elif tags:
        m["tags"] = list(dict.fromkeys(tags))
    out["meta"] = m

    palette = obj.get("palette")
    p = {}
    if not isinstance(palette, dict):
        errors.append(("palette", "needs base00 to base0F"))
        palette = {}
    bad_slots = set()
    for key, value in palette.items():
        slot = slot_name(key)
        if not slot:
            errors.append((f"palette.{key}", "not a base slot (base00 to base0F, optionally base10 to base17)"))
        elif not isinstance(value, str) or not HEX.fullmatch(value):
            errors.append((f"palette.{slot}", "a #rrggbb colour"))
            bad_slots.add(slot)
        else:
            p[slot] = value.lower()
    for slot in SLOTS16:
        if slot not in p and slot not in bad_slots:
            errors.append((f"palette.{slot}", "required"))
    out["palette"] = {s: p[s] for s in SLOTS24 if s in p}

    roles = obj.get("roles", {})
    r = {}
    if not isinstance(roles, dict):
        errors.append(("roles", "an object of overrides"))
        roles = {}
    for key, value in roles.items():
        if key not in ROLES:
            errors.append((f"roles.{key}", "not a role (" + " ".join(ROLES) + ")"))
            continue
        v = colour_ref(value, f"roles.{key}", errors, alpha=(key == "scrim"))
        if v is not None:
            r[key] = v
    if r:
        out["roles"] = {k: r[k] for k in ROLES if k in r}

    for section in ("type", "shape", "surface", "motion", "windows", "icons"):
        value = obj.get(section)
        if value is None:
            continue
        if not isinstance(value, dict):
            errors.append((section, "an object"))
            continue
        for extra in sorted(set(value) - SECTION_KEYS[section]):
            errors.append((f"{section}.{extra}", "not part of the schema"))
        s = {}
        for key, v in value.items():
            if key not in SECTION_KEYS[section]:
                continue
            path = f"{section}.{key}"
            if path in NUMBERS:
                n = _num(v, path, errors)
                if n is not None:
                    s[key] = n
            elif path in ENUMS:
                if v in ENUMS[path]:
                    s[key] = v
                else:
                    errors.append((path, "one of " + ", ".join(sorted(ENUMS[path]))))
            elif path in ("type.ui", "type.mono", "type.display"):
                f = font_stack(v, path, errors)
                if f:
                    s[key] = f
            elif path == "motion.ease":
                if v in EASES:
                    s[key] = v
                elif isinstance(v, str) and re.fullmatch(
                        r"cubic-bezier\(\s*-?[\d.]+\s*,\s*-?[\d.]+\s*,\s*-?[\d.]+\s*,\s*-?[\d.]+\s*\)", v):
                    nums = [float(x) for x in re.findall(r"-?[\d.]+", v)]
                    if all(-2 <= x <= 3 for x in nums) and 0 <= nums[0] <= 1 and 0 <= nums[2] <= 1:
                        s[key] = "cubic-bezier(" + ", ".join(f"{x:g}" for x in nums) + ")"
                    else:
                        errors.append((path, "cubic-bezier x values from 0 to 1, y values from -2 to 3"))
                else:
                    errors.append((path, "standard, gentle, linear, snappy, ease-out, ease-in-out or "
                                         "cubic-bezier(a, b, c, d)"))
            elif path == "motion.reduce":
                if isinstance(v, bool):
                    s[key] = v
                else:
                    errors.append((path, "true or false"))
            elif path in ("windows.focused", "windows.unfocused", "windows.pinned", "windows.attention",
                          "icons.plate"):
                c = colour_ref(v, path, errors, allow_roles=True)
                if c:
                    s[key] = c
        if s:
            out[section] = s

    if "wallpaper" in obj:
        w = _wallpaper(obj["wallpaper"], errors)
        if w and w.get("kind") != "none":
            out["wallpaper"] = w

    if errors:
        raise ThemeError(errors)
    pal = out["palette"]
    resolved = resolve(out)
    if out["meta"].get("variant") in ("light", "dark"):
        is_light = C.is_light(pal["base00"])
        if (out["meta"]["variant"] == "light") != is_light:
            warnings.append(f"meta.variant says {out['meta']['variant']} but base00 looks "
                            f"{'light' if is_light else 'dark'}")
    ratio = C.contrast(resolved["roles"]["ink"], resolved["roles"]["surface"])
    if ratio < 4.5:
        warnings.append(f"ink on surface has contrast {ratio:.1f}:1 (4.5:1 reads comfortably)")
    return out, warnings


def check(obj):
    return validate(obj)[0]


def check_text(text):
    """A stored theme is JSON text. -> clean theme dict, or ThemeError."""
    if not isinstance(text, str) or len(text) > MAX_TEXT:
        raise ThemeError([("theme", f"theme text up to {MAX_TEXT // 1000} KB")])
    try:
        obj = json.loads(text)
    except ValueError as exc:
        raise ThemeError([("theme", f"not JSON ({exc})")]) from None
    return check(obj)


def canonical(theme):
    """The stored form: sorted keys, no spaces. Equal themes are equal text."""
    return json.dumps(theme, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def pretty(theme):
    return json.dumps(theme, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def digest(theme):
    import hashlib
    return hashlib.sha1(canonical(theme).encode("utf-8")).hexdigest()[:12]


# ------------------------------------------------------------------------------------------------------ derivations
def derive_palette(pal):
    """base00-base17 as hex; base10-base17 derived (darker backgrounds, brighter accents) when the scheme is base16."""
    out = dict(pal)
    light = C.is_light(out["base00"])
    out.setdefault("base10", C.shift(out["base00"], -0.035))
    out.setdefault("base11", C.shift(out["base00"], -0.07))
    up = 0.05 if light else 0.08
    for new, old in (("base12", "base08"), ("base13", "base0A"), ("base14", "base0B"), ("base15", "base0C"),
                     ("base16", "base0D"), ("base17", "base0E")):
        out.setdefault(new, C.shift(out[old], up, 1.08))
    return {s: out[s] for s in SLOTS24}


def accent_ink(pal, accent):
    best = max((pal["base00"], pal["base07"]), key=lambda c: C.contrast(c, accent))
    if C.contrast(best, accent) < 4.5:
        best = max(("#000000", "#ffffff"), key=lambda c: C.contrast(c, accent))
    return best


def _hex_of(ref, pal, roles=None):
    """A slot, hex or role name as hex; `slot@pct` loses its alpha here (scrim keeps it separately)."""
    ref = ref.split("@")[0]
    if HEX.fullmatch(ref):
        return ref.lower()
    if SLOT.fullmatch(ref):
        return pal[slot_name(ref)]
    return roles[ref]


def resolve(theme):
    """A validated theme with every default and derived value filled in. Pure; the compilers read only this."""
    t = theme
    pal = derive_palette(t["palette"])
    overrides = t.get("roles", {})
    roles = {}
    for role in ROLES:
        if role in ("accent-ink", "scrim"):
            continue
        roles[role] = _hex_of(overrides.get(role) or ROLE_DEFAULTS[role], pal)
    roles["accent-ink"] = _hex_of(overrides["accent-ink"], pal) if "accent-ink" in overrides \
        else accent_ink(pal, roles["accent"])
    scrim = overrides.get("scrim") or ROLE_DEFAULTS["scrim"]
    scrim_pct = int(scrim.split("@")[1]) if "@" in scrim else 60
    roles["scrim"] = _hex_of(scrim, pal)
    variant = t["meta"].get("variant", "auto")
    if variant == "auto":
        variant = "light" if C.is_light(roles["surface"]) else "dark"
    typ = dict(DEFAULT_TYPE)
    typ.update(t.get("type", {}))
    typ.setdefault("display", typ["ui"])
    shape = {"radius": "medium", "border": 1, "gap_inner": 8, "gap_outer": 10, "bar_height": 36, "dock_size": 52}
    shape.update(t.get("shape", {}))
    surface = {"bar_opacity": 1.0, "window_opacity": 1.0, "shadow": "soft", "blur": "none"}
    surface.update(t.get("surface", {}))
    motion = {"fast": 120, "medium": 200, "slow": 360, "ease": "standard", "reduce": False}
    motion.update(t.get("motion", {}))
    win = dict(STATE_DEFAULTS)
    win.update({k: v for k, v in t.get("windows", {}).items() if k != "corner"})
    windows = {state: _hex_of(win[state], pal, roles) for state in STATES}
    windows["corner"] = t.get("windows", {}).get("corner") or CORNER_FOR[shape["radius"]]
    icons = {"style": "native", "plate": "raised"}
    icons.update(t.get("icons", {}))
    icons["plate_hex"] = _hex_of(icons["plate"], pal, roles)
    return {"meta": t["meta"], "palette": pal, "roles": roles, "scrim_pct": scrim_pct, "variant": variant,
            "type": typ, "shape": shape, "surface": surface, "motion": motion, "windows": windows, "icons": icons,
            "wallpaper": t.get("wallpaper") or {"kind": "none"}}


# ------------------------------------------------------------------------------------------------------ editing
def _coerce(path, value):
    """A path=value from a line (always text) as the JSON value the schema wants."""
    if not isinstance(value, str):
        return value
    v = value.strip()
    if path in NUMBERS or path == "wallpaper.dim":
        try:
            n = float(v)
        except ValueError:
            return v
        return int(n) if NUMBERS.get(path, (0, 0, False))[2] else n
    if path == "motion.reduce":
        return v.lower() in ("true", "yes", "1", "on")
    if path == "meta.tags":
        return [t.strip().lower() for t in v.replace(",", " ").split() if t.strip()]
    return v


def apply_patch(theme, patch):
    """A copy of `theme` with dotted paths set (`palette.base0D`, `shape.radius`, `wallpaper` = none|preset:<name>).
    Empty text removes an override. The caller validates the result."""
    t = copy.deepcopy(theme)
    for path, value in patch.items():
        parts = path.split(".")
        if path == "wallpaper":
            v = str(value).strip()
            if v in ("", "none"):
                t.pop("wallpaper", None)
            elif v.startswith("preset:"):
                from . import wallpapers as W
                lib = W.library()
                if v[7:] not in lib:
                    raise ThemeError([(path, "no such wallpaper preset; try " + ", ".join(sorted(lib)))])
                keep = {k: t.get("wallpaper", {}).get(k) for k in ("fit", "dim")
                        if t.get("wallpaper", {}).get(k) is not None}
                t["wallpaper"] = dict(lib[v[7:]], **keep)
            else:
                raise ThemeError([(path, "none or preset:<name>")])
            continue
        if parts[0] not in TOP or parts[0] in ("format", "version"):
            raise ThemeError([(path, "not an editable part of a theme")])
        if parts[0] == "palette" and len(parts) == 2:
            slot = slot_name(parts[1])
            if not slot:
                raise ThemeError([(path, "not a palette slot")])
            parts = ["palette", slot]
        node = t
        for step in parts[:-1]:
            node = node.setdefault(step, {})
            if not isinstance(node, dict):
                raise ThemeError([(path, "cannot be set inside a value")])
        if value in ("", None):
            node.pop(parts[-1], None)
        else:
            node[parts[-1]] = _coerce(path, value)
    return t
