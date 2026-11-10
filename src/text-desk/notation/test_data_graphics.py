"""Real data failures and the new source through the unchanged scene compiler."""
import json
import re
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch

import explore
import scene
from data_graphics import graphic


def q(value):
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


class GraphicsTests(unittest.TestCase):
    def test_zero_is_known_and_missing_is_not_zero(self):
        g = graphic(dict(records=[dict(label="Started", value=0), dict(label="Awaiting sensor", value=None)]))
        self.assertEqual((g["status"], g["count"], g["known"]), ("partial", 2, 1))
        self.assertEqual(g["parts"][0]["value_text"], "0 units")
        self.assertEqual(g["parts"][1]["value_text"], "unknown units")

    def test_numeric_strings_are_measured_and_booleans_are_not(self):
        g = graphic(dict(records=[dict(value="1200"), dict(value=True), dict(value="NaN"), dict(value=float("inf"))]))
        self.assertEqual(g["known"], 1)

    def test_negative_parts_are_visible_error(self):
        g = graphic(dict(mode="stack", records=[dict(value=-1)]))
        self.assertEqual(g["status"], "error")
        self.assertIn("negative", g["detail"])

    def test_above_capacity_does_not_silently_clip(self):
        for mode in ("stack", "bars"):
            g = graphic(dict(mode=mode, maximum=10, records=[dict(value=11)]))
            self.assertEqual(g["status"], "error")
            self.assertNotIn("<rect", g["picture"])

    def test_absent_capacity_is_not_claimed(self):
        g = graphic(dict(records=[dict(value=4)]))
        self.assertIn("no capacity supplied", g["detail"])

    def test_invalid_maximum_is_error(self):
        for value in (0, -1, "bad", False):
            self.assertEqual(graphic(dict(maximum=value))["status"], "error")

    def test_unassigned_is_not_free(self):
        g = graphic(dict(mode="stack", maximum=100, records=[dict(value=20), dict(value=None)]))
        self.assertIn("unassigned 80 units; not assumed free", g["detail"])
        self.assertIn("1 unknown", g["detail"])

    def test_line_preserves_gaps(self):
        g = graphic(dict(mode="line", records=[dict(value=1), dict(value=2), dict(value=None), dict(value=3), dict(value=4)]))
        self.assertEqual(g["picture"].count("<polyline"), 2)
        self.assertEqual(g["picture"].count("<circle"), 4)

    def test_time_series_uses_numeric_spacing(self):
        g = graphic(dict(mode="line", records=[dict(x=0, value=0), dict(x=1, value=1), dict(x=10, value=2)]))
        self.assertIn('cx="80.000"', g["picture"])
        self.assertIn('cx="395.000"', g["picture"])

    def test_invalid_time_axis_does_not_reorder_or_guess(self):
        for xs in ((1, 1), (2, 1), (1, None)):
            g = graphic(dict(mode="line", records=[dict(x=x, value=5) for x in xs]))
            self.assertEqual(g["status"], "error")

    def test_zero_and_one_sample_line_are_finite(self):
        for values in ([0, 0, 0], [7]):
            g = graphic(dict(mode="line", records=[dict(value=v) for v in values]))
            root = ET.fromstring(g["picture"])
            self.assertTrue(all(float(n.attrib["cx"]) == float(n.attrib["cx"]) for n in root.iter() if "cx" in n.attrib))

    def test_untrusted_labels_and_roles_cannot_inject_svg(self):
        g = graphic(dict(title="<script>&\x00", records=[dict(label='<img onerror="x">', value=2, role='x" onclick="x')]))
        root = ET.fromstring(g["picture"])
        self.assertNotIn("<script>", g["picture"])
        self.assertFalse(any("onclick" in node.attrib for node in root.iter()))
        self.assertIn('&lt;img', g["detail"].replace('<', '&lt;'))

    def test_large_values_are_finite_and_record_bound_is_visible(self):
        g = graphic(dict(mode="stack", records=[dict(value=1e15), dict(value=1e15)]))
        self.assertNotIn("inf", g["picture"])
        g = graphic(dict(records=[dict(value=1)] * 161))
        self.assertEqual(g["status"], "error")
        self.assertIn("aggregate explicitly", g["detail"])

    def test_empty_stale_and_errors_remain_text(self):
        self.assertEqual(graphic(dict(records=[]))["status"], "empty")
        self.assertEqual(graphic(dict(mode="pie"))["status"], "error")
        self.assertIn("Old sample", graphic(dict(state="stale", note="Old sample"))["detail"])

    def test_long_label_is_whole_in_words_and_bar_marks(self):
        label = "A long real-world task name " * 7
        g = graphic(dict(records=[dict(label=label, value=50)]))
        self.assertIn(label, g["detail"])
        self.assertEqual(g["parts"][0]["label"], label)

    def test_square_geometry_is_explicit_for_full_and_compact_bars(self):
        for mode in ("bars", "stack"):
            g = graphic(dict(mode=mode, maximum=100, corner_radius=0,
                             records=[dict(value=0), dict(value=100), dict(value=None)]))
            for svg in [g["picture"]] + [p["picture"] for p in g["parts"]]:
                rects = [e for e in ET.fromstring(svg).iter() if e.tag.endswith("rect")]
                self.assertTrue(rects)
                self.assertTrue(all(e.get("rx") == "0" and e.get("ry") == "0" for e in rects))

    def test_default_geometry_is_compatible_and_small_bars_have_configurable_thickness(self):
        g = graphic(dict(records=[dict(value=1)]))
        self.assertIn('rx="3"', g["picture"])
        self.assertIn('viewBox="0 0 400 10"', g["parts"][0]["picture"])
        g = graphic(dict(mark_height=28, records=[dict(value=1)]))
        self.assertIn('viewBox="0 0 400 28"', g["parts"][0]["picture"])
        self.assertIn('height="28"', g["parts"][0]["picture"])

    def test_bad_geometry_remains_error_even_with_stale_state(self):
        for key, value in (("corner_radius", -1), ("corner_radius", 5), ("mark_height", 0), ("mark_height", 65)):
            g = graphic(dict(state="stale", records=[dict(value=1)], **{key:value}))
            self.assertEqual(g["status"], "error")
            self.assertEqual(g["parts"], [])

    def test_compact_accessible_name_preserves_staleness(self):
        g = graphic(dict(state="stale", note="Old observation", records=[dict(value=42)]))
        self.assertIn("stale</title>", g["parts"][0]["picture"])


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.d = explore.fresh()
        self.d._session = "graphics-in-memory"

    def runline(self, line):
        result = self.d.dispatch("desk", dict(line=line, whole=True))
        self.assertFalse(result.get("error"), result)
        self.assertFalse(result.get("text", "").startswith("ERR"), result)
        return result.get("text", "")

    def note(self, title, text, tag=None):
        self.runline("look " + self.d.world.root)
        receipt = self.runline(f'do create {self.d.world.root} kind=note title={q(title)} text={q(text)}')
        item = re.search(r"created (a\d+)", receipt)[1]
        if tag:
            self.runline(f"do tag {item} add={tag}")
        return item

    def test_inline_source_and_marks_are_world_authored(self):
        item = self.note("Materials", json.dumps(dict(mode="bars", unit="sheets", basis="inventory", records=[dict(label="Paper", value=3)])))
        rows = scene.rows(self.d, "charts:" + item)
        self.assertIn("Paper: 3 sheets", rows[0]["detail"])
        self.assertEqual(scene.rows(self.d, "charts:" + item + "/marks")[0]["label"], "Paper")

    def test_malformed_definition_and_recursive_source_are_visible(self):
        for text in ("not JSON", "[]", '{"source":"charts:anything"}'):
            item = self.note("Bad definition", text)
            self.assertEqual(scene.rows(self.d, "charts:" + item)[0]["status"], "error")

    def test_same_count_source_change_reaches_compiled_scene(self):
        state = [dict(label="Queue", value=2)]
        with patch.dict(scene.SOURCES, chartcheck=("chartcheck", ("label", "value"))), patch.dict(scene.SOURCE_FILES, chartcheck=dict(arg="none", open=False, rows=lambda *args: list(state))):
            item = self.note("Queue", json.dumps(dict(source="chartcheck", unit="cards")))
            self.note("test-graphic", f'root : column\n  rows : column\n    of charts:{item} as g\n    each body\nbody : text "$g.detail"', "lens")
            first = scene.scene_for(self.d, "test-graphic")[1]
            state[0] = dict(label="Queue", value=9)
            second = scene.scene_for(self.d, "test-graphic")[1]
            self.assertIn("Queue: 2 cards", first)
            self.assertIn("Queue: 9 cards", second)
            self.assertNotEqual(first, second)
            state.clear()
            third = scene.rows(self.d, "charts:" + item)[0]
            self.assertEqual(third["status"], "unknown")
            self.assertIn("empty and unavailable cannot be distinguished", third["detail"])

    def test_config_edit_and_repeated_updates_use_latest_values(self):
        item = self.note("Editable", json.dumps(dict(records=[dict(label="A", value=1)])))
        self.note("test-config", f'root : column\n  rows : column\n    of charts:{item} as g\n    each body\nbody : text "$g.detail"', "lens")
        for n in range(15):
            self.runline("read " + item)
            self.runline(f'do edit {item} text={q(json.dumps(dict(records=[dict(label="A", value=n)])))}')
            text = scene.scene_for(self.d, "test-config")[1]
            self.assertIn(f"A: {n} units", text)


if __name__ == "__main__":
    unittest.main()
