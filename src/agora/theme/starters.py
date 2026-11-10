"""The starter themes. Four are written here; Catppuccin Mocha arrives through the base16 importer
(starters/catppuccin-mocha.yaml), which is the point of it: a published scheme, unchanged.

Each is a plain theme object. `all_starters()` -> [(slug, validated theme)] in the order the gallery shows them.
"""
from pathlib import Path

from . import base16
from . import model as M
from . import wallpapers as W

HERE = Path(__file__).resolve().parent
YAML = HERE / "starters" / "catppuccin-mocha.yaml"


def _pal(*hexes):
    slots = M.SLOTS16
    return {slot: h for slot, h in zip(slots, hexes)}


def seabright_day():
    """Today's light Agora: warm off-white paper, white cards, a sage green accent."""
    return {
        "format": M.FORMAT, "version": M.VERSION,
        "meta": {"name": "Seabright Day", "author": "Agora", "licence": "CC-BY-4.0", "variant": "light",
                 "tags": ["light", "warm", "green"],
                 "description": "The place's own light look: warm paper, white cards, a quiet sage green."},
        "palette": _pal("#faf9f6", "#ffffff", "#e5e8e3", "#a3aca6", "#7f8b85", "#35433d", "#26332d", "#1b2620",
                        "#cf514a", "#c58332", "#c9a227", "#638779", "#4a9aa5", "#507ebc", "#8a6fb0", "#a0714f"),
        "roles": {"accent": "base0B", "focus": "base0B", "accent-ink": "base01", "ok": "base0B", "info": "base0C"},
        "type": {"size": 15, "scale": 1.2},
        "shape": {"radius": "medium", "border": 1, "gap_inner": 8, "gap_outer": 10, "bar_height": 36,
                  "dock_size": 52},
        "surface": {"bar_opacity": 0.94, "window_opacity": 1, "shadow": "soft", "blur": "none"},
        "windows": {"focused": "accent", "unfocused": "border", "pinned": "base09", "attention": "danger"},
        "wallpaper": W.seabright_day(),
    }


def dusk():
    """After the purple komorebi rice: a deep violet gradient, lavender accent, rounded windows with gaps, a glassy bar."""
    return {
        "format": M.FORMAT, "version": M.VERSION,
        "meta": {"name": "Dusk", "author": "Agora", "licence": "CC-BY-4.0", "variant": "dark",
                 "tags": ["dark", "purple", "round"],
                 "description": "Deep violet, lavender accents, round corners and wide gaps, with a translucent bar."},
        "palette": _pal("#1c1438", "#2a1f52", "#3d2f72", "#6d5cab", "#a99bd9", "#e6defa", "#f1ecff", "#ffffff",
                        "#ff7a9c", "#ffa56e", "#ffd479", "#8fe3b0", "#7fd8f0", "#8aa9ff", "#c4a8ff", "#e0a3c8"),
        "roles": {"accent": "base0E", "focus": "base0E", "info": "base0D"},
        "type": {"size": 15, "scale": 1.2},
        "shape": {"radius": "large", "border": 1, "gap_inner": 12, "gap_outer": 14, "bar_height": 38,
                  "dock_size": 56},
        "surface": {"bar_opacity": 0.6, "window_opacity": 0.88, "shadow": "deep", "blur": "soft"},
        "windows": {"focused": "accent", "unfocused": "base02", "pinned": "base0A", "attention": "danger",
                    "corner": "round"},
        "icons": {"style": "native", "plate": "raised"},
        "wallpaper": W.dusk(),
    }


def night_metal():
    """After the dark yasb rice: near-black, cool greys, one muted blue, square corners, monospace everywhere."""
    mono = "JetBrains Mono, Cascadia Mono, Consolas, monospace"
    return {
        "format": M.FORMAT, "version": M.VERSION,
        "meta": {"name": "Night Metal", "author": "Agora", "licence": "CC-BY-4.0", "variant": "dark",
                 "tags": ["dark", "mono", "square"],
                 "description": "Near-black and cool grey, one muted blue, square corners and monospace type."},
        "palette": _pal("#0e0f11", "#16181b", "#252a30", "#3d444d", "#808a94", "#c5ccd3", "#dde2e7", "#f2f4f6",
                        "#c46a6a", "#c58a5a", "#bfa665", "#7fa58a", "#6fa9b8", "#86a8c8", "#9a88b4", "#8d7566"),
        "roles": {"accent": "base0D", "focus": "base0D", "info": "base0C"},
        "type": {"ui": mono, "mono": mono, "size": 13, "scale": 1.15},
        "shape": {"radius": "none", "border": 1, "gap_inner": 10, "gap_outer": 12, "bar_height": 30, "dock_size": 44},
        "surface": {"bar_opacity": 0.95, "window_opacity": 1, "shadow": "none", "blur": "none"},
        "motion": {"fast": 80, "medium": 140, "slow": 240, "ease": "linear"},
        "windows": {"focused": "accent", "unfocused": "base02", "pinned": "base0A", "attention": "danger",
                    "corner": "square"},
        "icons": {"style": "native", "plate": "raised"},
        "wallpaper": W.night_metal(),
    }


def ink_landscape():
    """After the sepia rice: cream paper, ink-brown text, a teal accent with rust warnings, thin square borders."""
    mono = "Cascadia Mono, Consolas, monospace"
    return {
        "format": M.FORMAT, "version": M.VERSION,
        "meta": {"name": "Ink Landscape", "author": "Agora", "licence": "CC-BY-4.0", "variant": "light",
                 "tags": ["light", "mono", "square", "paper"],
                 "description": "Cream paper and ink-brown type with a teal accent, over an ink-wash mountain drawing."},
        "palette": _pal("#f2e9c9", "#faf4dc", "#ddd0a6", "#a99b74", "#6c6044", "#2f2819", "#1f1a0e", "#130f07",
                        "#b6432a", "#c27a28", "#9a8a1c", "#5c7f3a", "#1f6b73", "#2b5f7a", "#7a4a6e", "#7a5230"),
        "roles": {"accent": "base0C", "focus": "base0C", "accent-ink": "base01", "info": "base0D"},
        "type": {"ui": mono, "mono": mono, "size": 14, "scale": 1.15},
        "shape": {"radius": "none", "border": 1, "gap_inner": 10, "gap_outer": 12, "bar_height": 30, "dock_size": 46},
        "surface": {"bar_opacity": 0.96, "window_opacity": 0.97, "shadow": "none", "blur": "none"},
        "motion": {"fast": 90, "medium": 160, "slow": 280, "ease": "gentle"},
        "windows": {"focused": "accent", "unfocused": "base03", "pinned": "base09", "attention": "danger",
                    "corner": "square"},
        "icons": {"style": "native", "plate": "raised"},
        "wallpaper": W.library()["ink-landscape"],
    }


def catppuccin_mocha():
    """Imported, not written: the published base16 scheme through the same path a neighbour's file takes."""
    theme = base16.to_theme(YAML.read_text(encoding="utf-8"))
    theme["meta"]["tags"] = ["dark", "base16", "catppuccin"]
    theme["meta"]["description"] = "The Catppuccin Mocha base16 scheme (MIT), imported as published."
    return theme


ORDER = [("seabright-day", seabright_day), ("dusk", dusk), ("night-metal", night_metal),
         ("ink-landscape", ink_landscape), ("catppuccin-mocha", catppuccin_mocha)]


def all_starters():
    return [(slug, M.check(make())) for slug, make in ORDER]
