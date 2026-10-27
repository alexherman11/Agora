"""An SVG wallpaper is data, never a document: no scripts, no styles, no remote references, no entities.

`clean(text)` returns the re-serialised, allow-listed SVG, or raises ValueError saying the first reason. The result is
only ever drawn as an image (a CSS background or <img>), where browsers run no script and load no outside file; the
allow-list is a second wall, so a stranger's theme cannot even contain them.
"""
import re
import xml.etree.ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", XLINK_NS)

MAX_BYTES = 128 * 1024
MAX_ELEMENTS = 4000
MAX_DEPTH = 16
MAX_FILTERS = 8

ELEMENTS = set("""svg g defs path rect circle ellipse line polyline polygon linearGradient radialGradient stop clipPath mask
filter feGaussianBlur feColorMatrix feOffset feBlend feComposite feFlood feMerge feMergeNode feTurbulence
feDisplacementMap feComponentTransfer feFuncA feFuncR feFuncG feFuncB title desc use pattern symbol""".split())

ATTRIBUTES = set("""id x y width height cx cy r rx ry x1 y1 x2 y2 points d transform viewBox preserveAspectRatio fill
fill-opacity fill-rule stroke stroke-width stroke-opacity stroke-linecap stroke-linejoin stroke-miterlimit
stroke-dasharray stroke-dashoffset opacity offset stop-color stop-opacity gradientUnits gradientTransform spreadMethod
fx fy fr clip-path clip-rule mask filter stdDeviation in in2 result type values mode baseFrequency numOctaves seed dx dy
flood-color flood-opacity operator k1 k2 k3 k4 version patternUnits patternTransform patternContentUnits maskUnits
maskContentUnits clipPathUnits filterUnits primitiveUnits tableValues slope intercept amplitude exponent
scale xChannelSelector yChannelSelector color-interpolation-filters shape-rendering vector-effect""".split())

URL = re.compile(r"url\(\s*([^)]*?)\s*\)", re.I)
BAD_VALUE = re.compile(r"javascript:|data:|vbscript:|<|expression\(|@import|&#|\\", re.I)


def _name(tag):
    if not tag.startswith("{"):
        raise ValueError("an element outside the SVG namespace: " + tag)
    ns, _, local = tag[1:].partition("}")
    if ns != SVG_NS:
        raise ValueError(f"an element from another namespace ({ns})")
    return local


def clean(text):
    if not isinstance(text, str):
        raise ValueError("an SVG wallpaper is text")
    raw = text.strip()
    if len(raw.encode("utf-8")) > MAX_BYTES:
        raise ValueError(f"the SVG is larger than {MAX_BYTES // 1024} KiB")
    low = raw.lower()
    for bad in ("<!doctype", "<!entity", "<?xml-stylesheet", "<![cdata[", "<script", "<style", "<foreignobject",
                "<image", "<iframe", "<a ", "<animate", "<set ", "<audio", "<video", "<text"):
        if bad in low:
            raise ValueError(f"an SVG wallpaper may not contain {bad.strip('<')}")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ValueError(f"not well-formed SVG ({exc})") from None
    if _name(root.tag) != "svg":
        raise ValueError("the root element must be svg")
    count = filters = 0

    def walk(node, depth):
        nonlocal count, filters
        count += 1
        if count > MAX_ELEMENTS:
            raise ValueError(f"more than {MAX_ELEMENTS} elements")
        if depth > MAX_DEPTH:
            raise ValueError(f"nested deeper than {MAX_DEPTH}")
        name = _name(node.tag)
        if name not in ELEMENTS:
            raise ValueError(f"the element {name} is not allowed in a wallpaper")
        if name == "filter":
            filters += 1
            if filters > MAX_FILTERS:
                raise ValueError(f"more than {MAX_FILTERS} filters")
        if name in ("title", "desc"):
            if len(node) or len(node.text or "") > 200:
                raise ValueError("a title or desc is plain text of at most 200 characters")
        elif (node.text or "").strip() or any((c.tail or "").strip() for c in node):
            raise ValueError(f"stray text inside {name}")
        for key, value in list(node.attrib.items()):
            local = key
            if key.startswith("{"):
                ns, _, local = key[1:].partition("}")
                if ns == XLINK_NS and local == "href":
                    local = "href"
                elif ns == "http://www.w3.org/XML/1998/namespace":
                    raise ValueError("xml:* attributes are not allowed")
                else:
                    raise ValueError(f"the attribute {key} is not allowed")
            if local == "href":
                if name != "use" or not re.fullmatch(r"#[A-Za-z][\w.-]{0,60}", value):
                    raise ValueError("href may only point at an id in the same drawing, from a use element")
                continue
            if local not in ATTRIBUTES:
                raise ValueError(f"the attribute {local} is not allowed (no style, event or link attributes)")
            if len(value) > 120_000 or BAD_VALUE.search(value):
                raise ValueError(f"the value of {local} is not allowed")
            for ref in URL.findall(value):
                if not re.fullmatch(r"['\"]?#[A-Za-z][\w.-]{0,60}['\"]?", ref):
                    raise ValueError("url() may only point at an id in the same drawing")
            if local == "numOctaves" and not (value.isdigit() and 1 <= int(value) <= 4):
                raise ValueError("numOctaves is 1 to 4")
        for child in node:
            if not isinstance(child.tag, str):
                raise ValueError("comments and processing instructions are not allowed")
            walk(child, depth + 1)

    walk(root, 0)
    if "viewBox" not in root.attrib:
        raise ValueError("the SVG needs a viewBox (so it can fill any screen)")
    out = ET.tostring(root, encoding="unicode")
    if not out.startswith("<svg"):
        raise ValueError("unexpected serialisation")
    if 'xmlns="' not in out.split(">", 1)[0]:
        out = out.replace("<svg", f'<svg xmlns="{SVG_NS}"', 1)
    return out
