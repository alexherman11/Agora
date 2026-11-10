"""Wallpapers we drew: gradients and one ink-wash landscape, all generated here, nothing downloaded.

`library()` -> {preset name: wallpaper object (the `wallpaper` section of a theme)}. An editor offers these; choosing one
copies the drawing into the theme, so a theme stays one self-contained thing.
"""
import random

_CACHE = {}


def _gradient(*layers, dim=0):
    return {"kind": "gradient", "layers": list(layers), "fit": "cover", "dim": dim}


def seabright_day():
    return _gradient(
        {"type": "radial", "at": [14, 6], "size": "farthest-corner", "stops": [["base0B@24", 0], ["transparent", 58]]},
        {"type": "radial", "at": [92, 96], "size": "farthest-corner", "stops": [["base09@16", 0], ["transparent", 52]]},
        {"type": "linear", "angle": 170, "stops": [["#f3f6ef", 0], ["#f8f4ea", 55], ["#eef1e8", 100]]})


def dusk():
    return _gradient(
        {"type": "radial", "at": [22, 0], "size": "farthest-corner", "stops": [["base0E@46", 0], ["transparent", 56]]},
        {"type": "radial", "at": [96, 96], "size": "farthest-corner", "stops": [["#ff6fb5@30", 0], ["transparent", 52]]},
        {"type": "linear", "angle": 160, "stops": [["#5a3bb0", 0], ["#2f1c66", 52], ["#120a2c", 100]]})


def night_metal():
    return _gradient(
        {"type": "radial", "at": [50, -10], "size": "farthest-corner", "stops": [["#2a3138", 0], ["transparent", 62]]},
        {"type": "linear", "angle": 180, "stops": [["#0b0c0e", 0], ["#101216", 100]]})


def aurora():
    return _gradient(
        {"type": "radial", "at": [20, 10], "size": "farthest-corner", "stops": [["#35d6a4@42", 0], ["transparent", 54]]},
        {"type": "radial", "at": [85, 20], "size": "farthest-corner", "stops": [["#6a7bff@40", 0], ["transparent", 55]]},
        {"type": "linear", "angle": 180, "stops": [["#0b1a2b", 0], ["#0a1020", 100]]})


def sunrise():
    return _gradient(
        {"type": "radial", "at": [50, 105], "size": "farthest-corner", "stops": [["#ffb86b@85", 0], ["transparent", 60]]},
        {"type": "linear", "angle": 180, "stops": [["#ffe9d2", 0], ["#ffd2c0", 55], ["#e6b8d6", 100]]})


def paper():
    return _gradient({"type": "linear", "angle": 180, "stops": [["#f2e8c6", 0], ["#ebdfb8", 100]]})


class _Noise:
    """Smooth 1D value noise from a seeded lattice, in -1..1."""

    def __init__(self, seed):
        rng = random.Random(seed)
        self.t = [rng.uniform(-1, 1) for _ in range(512)]

    def __call__(self, x):
        i = int(x // 1)
        f = x - i
        a, b = self.t[i % 512], self.t[(i + 1) % 512]
        u = f * f * (3 - 2 * f)
        return a + (b - a) * u


def _skyline(seed, base, amp, x0=-40, x1=1640, step=7, spread=1.0, octaves=5, sharp=1.0, bias=0.0, taper=(0, 0)):
    """A craggy ridgeline: ridged noise at several scales. -> [(x, y)] with y = base - height."""
    n = _Noise(seed)
    pts = []
    x = x0
    while x <= x1:
        h, total, f, a = 0.0, 0.0, 0.0035 * spread, 1.0
        for _ in range(octaves):
            r = 1 - abs(n(x * f + seed * 0.37))
            h += (r ** (1.6 * sharp)) * a
            total += a
            f *= 2.1
            a *= 0.5
        h = h / total - 0.45
        rise = 1.0
        for length, edge in ((taper[0], x - x0), (taper[1], x1 - x)):
            if length:
                u = max(0.0, min(1.0, edge / length))
                rise *= u * u * (3 - 2 * u)
        pts.append((x, base - (amp * (h + bias)) * rise))
        x += step
    return pts


def _ridge_path(pts, bottom):
    d = "M%d %d " % (pts[0][0], bottom) + " ".join("L%.0f %.0f" % p for p in pts)
    return d + " L%d %d Z" % (pts[-1][0], bottom)


def _crest_path(pts):
    return "M" + " L".join("%.0f %.0f" % p for p in pts)


def ink_landscape():
    """Cream paper, mist, ranges of ink-wash crags with pen hatching, a pale sun, birds and a pine branch."""
    W, H = 1600, 900
    far = _skyline(11, 440, 330, spread=0.8, sharp=1.1, bias=0.1)
    far2 = _skyline(23, 540, 300, spread=1.0, sharp=1.2)
    mid = _skyline(37, 660, 330, spread=1.1, sharp=1.2, bias=0.05)
    near_r = _skyline(53, 915, 640, x0=720, x1=1640, spread=0.9, sharp=1.15, bias=0.3, taper=(380, 0))
    near_l = _skyline(71, 915, 400, x0=-40, x1=640, spread=1.2, sharp=1.25, bias=0.2, taper=(0, 300))
    d = {}
    for key, pts in (("far", far), ("far2", far2), ("mid", mid), ("nr", near_r), ("nl", near_l)):
        d[key] = _ridge_path(pts, 920)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice">',
        "<title>Ink landscape</title>",
        "<defs>",
        '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f5ecd2"/>'
        '<stop offset="0.62" stop-color="#efe3bf"/><stop offset="1" stop-color="#e4d6aa"/></linearGradient>',
        '<radialGradient id="glow" cx="0.74" cy="0.21" r="0.45"><stop offset="0" stop-color="#fcf5dc" stop-opacity="1"/>'
        '<stop offset="1" stop-color="#fcf5dc" stop-opacity="0"/></radialGradient>',
        '<linearGradient id="mist" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f1e6c3" stop-opacity="0"/>'
        '<stop offset="0.55" stop-color="#f1e6c3" stop-opacity="0.92"/><stop offset="1" stop-color="#f1e6c3" '
        'stop-opacity="0"/></linearGradient>',
        '<pattern id="hatch" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(62)">'
        '<line x1="0" y1="0" x2="0" y2="5" stroke="#241d11" stroke-width="1" stroke-opacity="0.7"/></pattern>',
        '<pattern id="hatch2" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(-28)">'
        '<line x1="0" y1="0" x2="0" y2="4" stroke="#241d11" stroke-width="0.8" stroke-opacity="0.55"/></pattern>',
        '<filter id="soft" x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur stdDeviation="1.6"/></filter>',
        '<filter id="wash" x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur stdDeviation="6"/></filter>',
        f'<path id="far" d="{d["far"]}"/>', f'<path id="far2" d="{d["far2"]}"/>', f'<path id="mid" d="{d["mid"]}"/>',
        f'<path id="nr" d="{d["nr"]}"/>', f'<path id="nl" d="{d["nl"]}"/>',
        "</defs>",
        f'<rect width="{W}" height="{H}" fill="url(#sky)"/>',
        f'<rect width="{W}" height="{H}" fill="url(#glow)"/>',
        '<circle cx="1180" cy="190" r="84" fill="#f8f0d4" opacity="0.95"/>',
        '<use href="#far" fill="#cfc39c" opacity="0.72" filter="url(#wash)"/>',
        '<use href="#far" fill="url(#hatch2)" opacity="0.14"/>',
        f'<rect x="0" y="300" width="{W}" height="360" fill="url(#mist)" opacity="0.55"/>',
        '<use href="#far2" fill="#b3a57d" opacity="0.66" filter="url(#soft)"/>',
        '<use href="#far2" fill="url(#hatch2)" opacity="0.3"/>',
        f'<rect x="0" y="420" width="{W}" height="380" fill="url(#mist)" opacity="0.6"/>',
        '<use href="#mid" fill="#8a7c58" opacity="0.8"/>',
        '<use href="#mid" fill="url(#hatch)" opacity="0.42"/>',
        '<use href="#mid" fill="url(#hatch2)" opacity="0.25"/>',
        f'<path d="{_crest_path(mid)}" fill="none" stroke="#2c2416" stroke-width="1.3" opacity="0.55"/>',
        f'<rect x="0" y="560" width="{W}" height="360" fill="url(#mist)" opacity="0.5"/>',
        '<use href="#nl" fill="#40371f" opacity="0.92"/>',
        '<use href="#nl" fill="url(#hatch)" opacity="0.5"/>',
        f'<path d="{_crest_path(near_l)}" fill="none" stroke="#1e180d" stroke-width="1.6" opacity="0.8"/>',
        '<use href="#nr" fill="#352d1b" opacity="0.94"/>',
        '<use href="#nr" fill="url(#hatch)" opacity="0.55"/>',
        '<use href="#nr" fill="url(#hatch2)" opacity="0.35"/>',
        f'<path d="{_crest_path(near_r)}" fill="none" stroke="#1a150a" stroke-width="1.8" opacity="0.85"/>',
        
    ]
    birds = ['<g stroke="#2b2418" stroke-width="1.6" stroke-linecap="round" fill="none" opacity="0.7">']
    for x, y, s in ((930, 250, 1.0), (975, 232, 0.8), (1010, 262, 0.7), (880, 280, 0.6)):
        birds.append(f'<path d="M{x} {y} q{9 * s:.0f} {-8 * s:.0f} {18 * s:.0f} 0 q{9 * s:.0f} {-8 * s:.0f} {18 * s:.0f} 0"/>')
    birds.append("</g>")
    parts += birds
    branch = ['<g stroke="#2b2418" stroke-linecap="round" fill="none" opacity="0.82">',
              '<path d="M-20 70 C 120 98 240 86 340 156" stroke-width="3.2"/>']
    for i in range(18):
        t = i / 17
        x = -10 + 340 * t
        y = 72 + 88 * t * t + 14 * t
        for k, (dx, dy) in enumerate(((26, -20), (30, 15), (22, 38))):
            branch.append(f'<path d="M{x:.0f} {y:.0f} l{dx} {dy}" stroke-width="{1.2 if k else 1.4}"/>')
    branch.append("</g>")
    parts += branch
    parts.append("</svg>")
    return "".join(parts)


def library():
    if not _CACHE:
        from . import svgsafe
        _CACHE.update({
            "seabright-day": dict(seabright_day()), "dusk": dict(dusk()), "night-metal": dict(night_metal()),
            "aurora": dict(aurora()), "sunrise": dict(sunrise()), "paper": dict(paper()),
            "ink-landscape": {"kind": "svg", "svg": svgsafe.clean(ink_landscape()), "fit": "cover", "dim": 0},
        })
    return {k: dict(v) for k, v in _CACHE.items()}
