"""The theme format, its checks and its compiler (src/agora/theme/): pure, no kernel needed."""
import copy
import json
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LAB))
from theme import base16, colour, compile as K, model as M, service, starters, svgsafe, wallpapers  # noqa: E402


def dusk():
    return copy.deepcopy(starters.dusk())


class Colour(unittest.TestCase):
    def test_contrast_and_mixing(self):
        self.assertAlmostEqual(colour.contrast("#000000", "#ffffff"), 21.0, places=1)
        self.assertAlmostEqual(colour.contrast("#777777", "#777777"), 1.0, places=2)
        self.assertEqual(colour.mix("#000000", "#ffffff", 0).lower(), "#000000")
        self.assertEqual(colour.mix("#000000", "#ffffff", 1).lower(), "#ffffff")
        self.assertTrue(colour.is_light("#faf9f6"))
        self.assertFalse(colour.is_light("#1c1438"))


class Starters(unittest.TestCase):
    def test_every_starter_passes_the_check_and_reads_in_its_own_colours(self):
        for slug, theme in starters.all_starters():
            clean, _ = M.validate(theme)
            r = M.resolve(clean)
            self.assertGreaterEqual(colour.contrast(r["roles"]["ink"], r["roles"]["surface"]), 7.0, slug)
            # Seabright Day keeps today's white-on-sage buttons (3.98:1) so the place looks exactly as it did
            floor = 3.9 if slug == "seabright-day" else 4.5
            self.assertGreaterEqual(colour.contrast(r["roles"]["accent-ink"], r["roles"]["accent"]), floor, slug)
            self.assertEqual(M.digest(clean), M.digest(M.check_text(M.canonical(clean))), slug)

    def test_five_starters_one_of_them_imported_from_base16(self):
        names = [s for s, _ in starters.ORDER]
        self.assertEqual(len(names), 5)
        mocha = dict(starters.all_starters())["catppuccin-mocha"]
        self.assertTrue(mocha["meta"]["from"].startswith("base16:"))

    def test_the_resolved_theme_has_derived_slots_and_variant(self):
        r = M.resolve(dusk())
        self.assertEqual(r["variant"], "dark")
        for i in range(0x10, 0x18):
            self.assertIn(f"base{i:02X}", r["palette"])
        self.assertEqual(M.resolve(starters.seabright_day())["variant"], "light")


class Refusals(unittest.TestCase):
    def refuse(self, mutate, where):
        t = dusk()
        mutate(t)
        with self.assertRaises(M.ThemeError) as caught:
            M.check(t)
        self.assertIn(where, str(caught.exception))

    def test_unsafe_things_are_refused_and_named(self):
        self.refuse(lambda t: t.__setitem__("type", {"ui": "Arial</style><script>alert(1)</script>"}), "type.ui")
        self.refuse(lambda t: t.__setitem__("type", {"mono": "Consolas, url(https://evil.example/x)"}), "type.mono")
        self.refuse(lambda t: t.__setitem__("roles", {"accent": "url(javascript:1)"}), "roles.accent")
        self.refuse(lambda t: t.__setitem__("css", "body{display:none}"), "css")
        self.refuse(lambda t: t["palette"].__setitem__("base00", "red"), "palette.base00")
        self.refuse(lambda t: t["shape"].__setitem__("gap_inner", 500), "shape.gap_inner")
        self.refuse(lambda t: t.__setitem__("wallpaper", {"kind": "image", "image": "https://evil.example/w.png"}),
                    "wallpaper.image")

    def test_every_reason_is_reported_together(self):
        t = dusk()
        t["type"] = {"ui": "x;y"}
        t["shape"]["gap_inner"] = 999
        with self.assertRaises(M.ThemeError) as caught:
            M.check(t)
        self.assertGreaterEqual(len(caught.exception.errors), 2)

    def test_theme_text_limits(self):
        with self.assertRaises(M.ThemeError):
            M.check_text("x" * (M.MAX_TEXT + 1))
        with self.assertRaises(M.ThemeError):
            M.check_text("not json")

    def test_oversized_raster_is_refused(self):
        import base64
        data = b"\x89PNG\r\n\x1a\n" + b"\x00" * (M.MAX_IMAGE_BYTES + 10)
        self.refuse(lambda t: t.__setitem__("wallpaper", {"kind": "image",
                    "image": "data:image/png;base64," + base64.b64encode(data).decode()}), "larger than")

    def test_a_picture_must_be_the_kind_it_says(self):
        import base64
        self.refuse(lambda t: t.__setitem__("wallpaper", {"kind": "image",
                    "image": "data:image/png;base64," + base64.b64encode(b"<html>").decode()}), "not a png")


class Svg(unittest.TestCase):
    HEAD = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'

    def test_the_ink_wallpaper_passes_and_is_reserialised(self):
        text = wallpapers.ink_landscape()
        out = svgsafe.clean(text)
        self.assertIn("<svg", out)
        self.assertLess(len(out.encode()), svgsafe.MAX_BYTES)

    def test_active_content_is_refused(self):
        for bad in (self.HEAD + "<script>alert(1)</script></svg>",
                    self.HEAD + '<rect width="1" height="1" onload="x()"/></svg>',
                    self.HEAD + '<image href="https://evil.example/a.png"/></svg>',
                    self.HEAD + '<style>*{background:url(http://x)}</style></svg>',
                    self.HEAD + '<foreignObject><div/></foreignObject></svg>',
                    '<!DOCTYPE svg [<!ENTITY a "b">]>' + self.HEAD + "</svg>",
                    self.HEAD + '<use href="https://evil.example/a.svg#x"/></svg>',
                    self.HEAD + '<rect fill="url(https://evil.example/p)"/></svg>',
                    self.HEAD + "<a><rect/></a></svg>"):
            with self.assertRaises(ValueError, msg=bad[:70]):
                svgsafe.clean(bad)

    def test_local_references_and_limits(self):
        ok = self.HEAD + '<defs><linearGradient id="g"><stop offset="0" stop-color="#fff"/></linearGradient></defs><rect width="9" height="9" fill="url(#g)"/></svg>'
        self.assertIn("url(#g)", svgsafe.clean(ok))
        with self.assertRaises(ValueError):
            svgsafe.clean(self.HEAD + "<g>" * (svgsafe.MAX_DEPTH + 2) + "</g>" * (svgsafe.MAX_DEPTH + 2) + "</svg>")
        with self.assertRaises(ValueError):
            svgsafe.clean(self.HEAD + "<rect/>" * (svgsafe.MAX_ELEMENTS + 1) + "</svg>")
        with self.assertRaises(ValueError):
            svgsafe.clean('<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>')      # no viewBox


class Base16(unittest.TestCase):
    SCHEME = "\n".join(['system: "base16"', 'name: "Test Scheme"', 'author: "Someone"', 'variant: "dark"', "palette:"] +
                       [f'  base{i:02X}: "#{(i * 15) % 256:02x}{(i * 7) % 256:02x}{(i * 3 + 40) % 256:02x}"' for i in range(16)])

    def test_import_makes_a_checked_theme_and_exports_it_back(self):
        theme = base16.to_theme(self.SCHEME)
        clean = M.check(theme)
        self.assertEqual(clean["meta"]["name"], "Test Scheme")
        self.assertTrue(clean["meta"]["from"].startswith("base16:"))
        back = base16.parse(base16.to_yaml(clean))
        for i in range(16):
            self.assertEqual(str(back["palette"][f"base{i:02X}"]).lower(), clean["palette"][f"base{i:02X}"].lower())

    def test_a_scheme_missing_a_slot_or_with_a_bad_colour_is_refused(self):
        with self.assertRaises(base16.SchemeError):
            base16.to_theme(self.SCHEME.replace('  base0F:', '  base1F:'))
        with self.assertRaises((base16.SchemeError, M.ThemeError)):
            M.check(base16.to_theme(self.SCHEME.replace('"#', '"url(#', 1)))

    def test_base24_extra_slots_are_accepted(self):
        text = self.SCHEME + "".join(f'\n  base{i:02X}: "#{i * 9:02x}{i * 5:02x}{i * 3:02x}"' for i in range(0x10, 0x18))
        self.assertIn("base10", M.check(base16.to_theme(text))["palette"])


class Compile(unittest.TestCase):
    def test_variables_cover_the_contract_and_carry_no_address(self):
        r = M.resolve(dusk())
        v = K.variables(r)
        for name in ("--ag-bg", "--ag-surface", "--ag-ink", "--ag-accent", "--ag-accent-ink", "--ag-border", "--ag-font-ui",
                     "--ag-radius-m", "--ag-gap-inner", "--ag-bar-bg", "--ag-win-focused", "--ag-base0D", "--ag-dur-fast"):
            self.assertIn(name, v)
        css = K.css(r, None, "abc")
        self.assertNotIn("</style", css.lower())
        self.assertNotIn("http", css.lower().replace("http://www.w3.org", ""))
        self.assertNotIn("@import", css)

    def test_legacy_tokens_are_the_roles(self):
        r = M.resolve(dusk())
        legacy = K.legacy(r)
        self.assertEqual(legacy["paper"].lower(), r["roles"]["surface"].lower())
        self.assertEqual(legacy["accent"].lower(), r["roles"]["accent"].lower())
        for key in ("paper", "card", "ink", "muted", "accent", "red", "orange", "blue", "grey", "rose", "peach", "sage", "sky", "lilac"):
            self.assertIn(key, legacy)

    def test_native_sheet_is_small_and_plain(self):
        sheet = K.native(M.resolve(dusk()), "abc")
        self.assertLess(len(json.dumps(sheet)), 2000)
        for key in ("version", "hash", "variant", "gap_inner", "gap_outer", "border_width", "colors", "bar_height", "corner"):
            self.assertIn(key, sheet)

    def test_a_patch_edits_by_path_and_is_checked_again(self):
        t = M.apply_patch(dusk(), {"palette.base0d": "#ff8800", "shape.radius": "small", "wallpaper": "none"})
        self.assertEqual(M.check(t)["palette"]["base0D"].lower(), "#ff8800")
        with self.assertRaises(M.ThemeError):
            M.check(M.apply_patch(dusk(), {"shape.gap_inner": "999"}))
        with self.assertRaises(M.ThemeError):
            M.apply_patch(dusk(), {"format": "evil"})


class Scope(unittest.TestCase):
    NOW = datetime(2026, 10, 26, 12, tzinfo=timezone.utc)

    def test_a_trial_beats_a_choice_beats_the_place_beats_the_default(self):
        place = [{"id": "s1", "active": "T-place", "steward": True}]
        mine = [{"id": "c1", "person": "p1", "theme": "T-mine", "trial": "T-try",
                 "trial_until": (self.NOW + timedelta(seconds=30)).isoformat()}]
        self.assertEqual(service.pick(place, mine, "p1", self.NOW)[:2], ("T-try", "trial"))
        later = self.NOW + timedelta(seconds=31)
        self.assertEqual(service.pick(place, mine, "p1", later)[:2], ("T-mine", "me"))
        self.assertEqual(service.pick(place, mine, "p2", self.NOW)[:2], ("T-place", "place"))
        self.assertEqual(service.pick([], [], "p2", self.NOW)[:2], (None, "builtin"))

    def test_only_the_stewards_setting_counts_for_the_place(self):
        forged = [{"id": "s1", "active": "T-evil", "steward": False}]
        self.assertEqual(service.pick(forged, [], "p1", self.NOW)[:2], (None, "builtin"))

    def test_following_the_place_is_a_choice_of_place(self):
        place = [{"id": "s1", "active": "T-place", "steward": True}]
        choice = [{"id": "c1", "person": "p1", "theme": "place"}]
        self.assertEqual(service.pick(place, choice, "p1", self.NOW)[:2], ("T-place", "place"))


if __name__ == "__main__":
    unittest.main()
