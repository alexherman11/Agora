"""tinted-theming base16 and base24 scheme files: read them into a theme, write a theme's palette back out.

The scheme format (https://github.com/tinted-theming/home) is a small YAML file:

    system: "base16"
    name: "Catppuccin Mocha"
    author: "Catppuccin Org"
    variant: "dark"
    palette:
      base00: "#1e1e2e"
      ...

Only that subset is read, by a reader of our own (no YAML library, no tags, anchors, includes or code), so a scheme
file can only ever say what the format allows.
"""
import re

from . import model as M

MAX_BYTES = 16_384
SCALAR = re.compile(r'''^\s*(?:"([^"]*)"|'([^']*)'|([^#]*?))\s*(?:\s#.*)?$''')


class SchemeError(ValueError):
    pass


def parse(text):
    """-> a dict of the scheme: top-level scalars and `palette` as a dict. Raises SchemeError."""
    if not isinstance(text, str) or len(text.encode("utf-8")) > MAX_BYTES:
        raise SchemeError(f"a scheme file is plain text of at most {MAX_BYTES // 1024} KiB")
    out, section = {}, None
    for number, raw in enumerate(text.replace("\r\n", "\n").split("\n"), 1):
        if not raw.strip() or raw.lstrip().startswith("#") or raw.strip() in ("---", "..."):
            continue
        if raw.lstrip()[0] in "-!&*|>%@`[{" or "\t" in raw[: len(raw) - len(raw.lstrip())]:
            raise SchemeError(f"line {number}: only plain 'key: value' lines are read (no lists, tags, anchors or tabs)")
        indent = len(raw) - len(raw.lstrip())
        key, colon, rest = raw.strip().partition(":")
        if not colon or not re.fullmatch(r"[A-Za-z0-9_\-]+", key):
            raise SchemeError(f"line {number}: expected 'key: value'")
        m = SCALAR.match(rest)
        value = next((g for g in m.groups() if g is not None), "").strip() if m else None
        if value is None:
            raise SchemeError(f"line {number}: cannot read the value")
        if indent == 0:
            if value == "":
                section = key
                out[section] = {}
            else:
                section = None
                out[key] = value
        else:
            if section is None:
                raise SchemeError(f"line {number}: an indented line needs a heading above it")
            out[section][key] = value
    return out


def _hex(value):
    v = str(value).strip().lstrip("#")
    return "#" + v.lower() if re.fullmatch(r"[0-9a-fA-F]{6}", v) else None


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40] or "scheme"


def to_theme(text, name=None):
    """Read a base16/base24 scheme into an Agora theme object (not yet validated by model.validate)."""
    raw = parse(text)
    system = str(raw.get("system", "base16")).lower()
    if system not in ("base16", "base24"):
        raise SchemeError(f"system is {system!r}; this reads base16 and base24 schemes")
    palette = raw.get("palette")
    if not isinstance(palette, dict):       # the older, flat layout: base00 ... at the top
        palette = {k: v for k, v in raw.items() if M.SLOT.fullmatch(k) and isinstance(v, str)}
    pal = {}
    for key, value in palette.items():
        slot = M.slot_name(key)
        if not slot:
            raise SchemeError(f"{key!r} is not a base slot")
        h = _hex(value)
        if not h:
            raise SchemeError(f"{key} is not a six digit colour: {value!r}")
        pal[slot] = h
    missing = [s for s in M.SLOTS16 if s not in pal]
    if missing:
        raise SchemeError("the palette is missing " + ", ".join(missing))
    title = (name or raw.get("name") or raw.get("scheme") or "Imported scheme")
    variant = str(raw.get("variant", "auto")).lower()
    if variant not in ("light", "dark"):
        variant = "auto"
    slug = str(raw.get("slug") or slugify(title))
    meta = {"name": str(title)[:60], "author": str(raw.get("author") or "unknown")[:60],
            "licence": str(raw.get("license") or raw.get("licence") or "MIT")[:40], "variant": variant,
            "from": f"{system}:{slug}"[:80], "tags": [system]}
    description = raw.get("description")
    if description:
        meta["description"] = str(description)[:280]
    theme = {"format": M.FORMAT, "version": M.VERSION, "meta": meta, "palette": pal,
             "shape": {"radius": "medium"},
             "wallpaper": {"kind": "gradient", "layers": [
                 {"type": "radial", "at": [18, 8], "size": "farthest-corner",
                  "stops": [["base0D@26", 0], ["transparent", 62]]},
                 {"type": "linear", "angle": 180, "stops": [["base01", 0], ["base00", 100]]}]}}
    return theme


def to_yaml(theme):
    """A theme's palette as a tinted-theming scheme file (base24 when the theme carries base10 to base17)."""
    pal = theme["palette"]
    system = "base24" if all(s in pal for s in M.SLOTS24) else "base16"
    meta = theme["meta"]
    lines = [f'system: "{system}"', f'name: "{meta["name"]}"', f'slug: "{slugify(meta["name"])}"',
             f'author: "{meta.get("author", "unknown")}"']
    variant = meta.get("variant", "auto")
    if variant in ("light", "dark"):
        lines.append(f'variant: "{variant}"')
    lines.append("palette:")
    for slot in (M.SLOTS24 if system == "base24" else M.SLOTS16):
        lines.append(f'  {slot}: "{pal[slot]}"')
    return "\n".join(lines) + "\n"
