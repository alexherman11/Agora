"""Colour arithmetic for themes: sRGB hex, WCAG contrast, OKLab mixing. Standard library only."""
import math
import re

HEX6 = re.compile(r"#[0-9a-fA-F]{6}")


def parse(h):
    h = str(h)
    if not HEX6.fullmatch(h):
        raise ValueError(f"not a #rrggbb colour: {h!r}")
    return int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)


def hexed(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(c)))) for c in rgb)


def _lin(c):
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _gam(x):
    x = max(0.0, min(1.0, x))
    return 255.0 * (12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055)


def luminance(h):
    r, g, b = (_lin(c) for c in parse(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def to_oklab(h):
    r, g, b = (_lin(c) for c in parse(h))
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = (math.copysign(abs(x) ** (1 / 3), x) for x in (l, m, s))
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def from_oklab(lab):
    L, a, b = lab
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    bl = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    return hexed((_gam(r), _gam(g), _gam(bl)))


def mix(a, b, t):
    """a at 1-t, b at t, mixed in OKLab."""
    t = max(0.0, min(1.0, t))
    la, lb = to_oklab(a), to_oklab(b)
    return from_oklab(tuple(x + (y - x) * t for x, y in zip(la, lb)))


def lightness(h):
    return to_oklab(h)[0]


def lch(h):
    L, a, b = to_oklab(h)
    return L, math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360


def from_lch(L, C, hue):
    r = math.radians(hue)
    return from_oklab((L, C * math.cos(r), C * math.sin(r)))


def shift(h, dl=0.0, chroma=1.0):
    """Lightness shifted by dl (OKLab L units) and chroma scaled."""
    L, C, hue = lch(h)
    return from_lch(max(0.0, min(1.0, L + dl)), C * chroma, hue)


def rgba(h, alpha):
    r, g, b = parse(h)
    a = round(float(alpha), 3)
    return f"rgba({r}, {g}, {b}, {a:g})"


def is_light(h):
    return luminance(h) > 0.4
