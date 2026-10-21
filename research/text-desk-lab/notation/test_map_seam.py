# health: room test
"""a7950: the living map's seam (map_seam.py) on a fresh in-memory world, with real desk commands; never Alex's world.

The done-when list of a7950, by name: (1) test_1_lat_by_line_moves_the_pin_in_the_draw; (2) test_2_a_move_is_one_
undoable_command and test_2_a_stale_move_is_refused_and_overwrites_nothing; (3) test_3_a_three_pin_route_goes_in_order_
and_a_rename_keeps_it; (4) test_4_*: one test per refusal (origin is judged by the host page, in the browser test
research/window-lab/living-map/seam_browser.py); (5) is the browser test's (the frame against the real bridge)."""
import math
import re
import unittest
import uuid

import explore
import map_seam as M


class SeamTests(unittest.TestCase):
    def setUp(self):
        self.d = explore.fresh()
        self.d._session = "fixture"
        self.w = self.d.world
        self.w.me = "alex"
        self.line("look")
        root = self.w.root
        self.kinds = self.make(root, "kind=surface title=Kinds")
        self.make(self.kinds, 'kind=note title=pin tags=kind is=note text="A place on the living map."')
        self.make(self.kinds, 'kind=note title=route tags=kind is=note text="An authored route."')
        self.map = self.make(root, "kind=surface title=Map")
        # synthetic places (a7875: real pin notes wait for the ground worker's verified coordinates)
        self.p1 = self.make(self.map, 'kind=pin title="Synthetic one" lat=51.5194 lon=-0.1270 label="Synthetic one"')
        self.p2 = self.make(self.map, 'kind=pin title="Synthetic two" lat=51.5180 lon=-0.1260 label="Synthetic two" colour=teal')
        self.p3 = self.make(self.map, 'kind=pin title="Synthetic three" lat=51.5200 lon=-0.1250 label="Synthetic three" height=12')
        self.route = self.make(self.map, f'kind=route title="Synthetic walk" label="Synthetic walk" text="{self.p2}\\n[[{self.p1}]]\\n{self.p3}"')
        self.elsewhere = self.make(root, 'kind=note title="Not a pin"')

    # ---- helpers ---------------------------------------------------------------------------------------------------
    def line(self, line, ok=True):
        r = self.d.dispatch("desk", {"line": line, "whole": True, "reply": uuid.uuid4().hex})
        text = r.get("text", "")
        failed = bool(r.get("error") or re.search(r"(^|\n)(ERR|!!)", text))
        self.assertEqual(failed, not ok, f"{line}\n{r}")
        return text

    def make(self, parent, body):
        self.line(f"look {parent}")
        return re.search(r"created ([af]\d+)", self.line(f"do create {parent} {body}"))[1]

    def drawn(self, scope="map"):
        return M.draw(self.w, self.map if scope == "map" else scope)

    def pin(self, pid, scope="map"):
        return next(p for p in self.drawn(scope)["draw"]["pins"] if p["id"] == pid)

    def msg(self, **kw):
        return {"channel": M.CHANNEL, **kw}

    def refused(self, msg, words):
        with self.assertRaises(M.Refused) as e:
            M.check(self.w, msg, self.map)
        self.assertIn(words, str(e.exception))
        return str(e.exception)

    # ---- (1) ------------------------------------------------------------------------------------------------------
    def test_1_lat_by_line_moves_the_pin_in_the_draw(self):
        before = self.pin(self.p1)
        self.assertEqual((51.5194, -0.127), (before["lat"], before["lon"]))
        self.line(f"look {self.p1}")
        self.line(f"do prop {self.p1} lat=51.5201")
        after = self.pin(self.p1)
        self.assertEqual(51.5201, after["lat"])
        self.assertEqual(-0.127, after["lon"])
        self.assertGreater(after["rev"], before["rev"], "the frame must see a new revision")
        d = self.drawn()["draw"]
        self.assertEqual({"channel", "op", "pins", "routes"}, set(d))
        self.assertEqual({"id", "rev", "lat", "lon", "height", "label"}, set(after))

    # ---- (2) ------------------------------------------------------------------------------------------------------
    def test_2_a_move_is_one_undoable_command(self):
        p = self.pin(self.p1)
        out = M.check(self.w, self.msg(op="move", id=self.p1, rev=p["rev"], lat=51.5, lon=-0.13), self.map)
        self.assertEqual(f"do prop {self.p1} lat=51.5 lon=-0.13", out["line"])
        self.assertEqual({"item": self.p1, "rev": p["rev"]}, out["observed"])
        n0 = len(self.w.events)
        self.line(f"look {self.p1}")
        self.line(out["line"])
        self.assertEqual(n0 + 1, len(self.w.events), "exactly one world event")
        ev = self.w.events[-1]
        self.assertEqual("prop", ev["verb"])
        self.assertEqual((51.5, -0.13), (self.pin(self.p1)["lat"], self.pin(self.p1)["lon"]))
        self.line(f"undo {ev['id']}")
        self.assertEqual((51.5194, -0.127), (self.pin(self.p1)["lat"], self.pin(self.p1)["lon"]))

    def test_2_a_stale_move_is_refused_and_overwrites_nothing(self):
        seen = self.pin(self.p1)
        self.line(f"look {self.p1}")
        self.line(f"do prop {self.p1} lat=51.5210")          # someone else, by line, after the frame drew it
        n0, newer = len(self.w.events), self.pin(self.p1)
        why = self.refused(self.msg(op="move", id=self.p1, rev=seen["rev"], lat=10.0, lon=10.0), "stale")
        self.assertIn(str(newer["rev"]), why)
        self.assertEqual(n0, len(self.w.events), "nothing written")
        self.assertEqual(51.521, self.pin(self.p1)["lat"], "the newer edit stands")

    # ---- (3) ------------------------------------------------------------------------------------------------------
    def test_3_a_three_pin_route_goes_in_order_and_a_rename_keeps_it(self):
        d = self.drawn()["draw"]
        self.assertEqual([{"id": self.route, "rev": d["routes"][0]["rev"], "label": "Synthetic walk", "pins": [self.p2, self.p1, self.p3]}], d["routes"])
        self.assertEqual({self.p1, self.p2, self.p3}, {p["id"] for p in d["pins"]})
        self.line(f"look {self.p1}")
        self.line(f'do retitle {self.p1} title="Renamed place"')
        self.line(f"look {self.p1}")
        self.line(f'do prop {self.p1} label="Renamed place"')
        d2 = self.drawn()["draw"]
        self.assertEqual([self.p2, self.p1, self.p3], d2["routes"][0]["pins"])
        self.assertEqual("Renamed place", self.pin(self.p1)["label"])

    def test_3_a_route_pulls_in_a_pin_kept_elsewhere_and_a_bad_line_is_named(self):
        far = self.make(self.kinds, 'kind=pin title=Far lat=51.6 lon=-0.2 label=Far')
        r = self.make(self.map, f'kind=route title=Out text="{self.p1}\\n{far}"')
        d = self.drawn()
        self.assertIn(far, {p["id"] for p in d["draw"]["pins"]})
        bad = self.make(self.map, f'kind=route title=Broken text="{self.p1}\\n{self.elsewhere}"')
        d = self.drawn()
        self.assertNotIn(bad, {x["id"] for x in d["draw"]["routes"]})
        self.assertIn(bad, dict(d["problems"]))
        self.assertIn(r, {x["id"] for x in d["draw"]["routes"]})

    def test_a_pin_that_cannot_be_placed_is_left_out_and_named(self):
        odd = self.make(self.map, 'kind=pin title=Odd lat=north lon=-0.1 label=Odd')
        far = self.make(self.map, 'kind=pin title=Pole lat=91 lon=0 label=Pole')
        d = self.drawn()
        ids = {p["id"] for p in d["draw"]["pins"]}
        self.assertNotIn(odd, ids)
        self.assertNotIn(far, ids)
        self.assertIn("not a number", dict(d["problems"])[odd])
        self.assertIn("out of range", dict(d["problems"])[far])

    # ---- (4) one refusal each (origin: the browser test) ------------------------------------------------------------
    def test_4_wrong_channel(self):
        self.refused({"channel": "agora-map/2", "op": "press", "id": self.p1}, "wrong channel")
        self.refused({"op": "press", "id": self.p1}, "wrong channel")

    def test_4_unknown_operation(self):
        self.refused(self.msg(op="delete", id=self.p1), "unknown op")
        self.refused(self.msg(op="draw", pins=[]), "unknown op")      # draw goes in, never out

    def test_4_non_finite_coordinates(self):
        rev = self.pin(self.p1)["rev"]
        for v in (math.nan, math.inf, -math.inf):
            self.refused(self.msg(op="move", id=self.p1, rev=rev, lat=v, lon=0.0), "finite")
        self.refused(self.msg(op="drop", lat=0.0, lon=math.nan), "finite")

    def test_4_out_of_range_coordinates(self):
        rev = self.pin(self.p1)["rev"]
        self.refused(self.msg(op="move", id=self.p1, rev=rev, lat=90.5, lon=0.0), "out of range")
        self.refused(self.msg(op="move", id=self.p1, rev=rev, lat=0.0, lon=-180.01), "out of range")
        self.refused(self.msg(op="drop", lat=-91, lon=0), "out of range")

    def test_4_coordinates_are_named_numbers_not_strings_or_arrays(self):
        rev = self.pin(self.p1)["rev"]
        self.refused(self.msg(op="move", id=self.p1, rev=rev, lat="51.5", lon=0.0), "must be a number")
        self.refused(self.msg(op="move", id=self.p1, rev=rev, lat=[51.5, 0.0], lon=0.0), "must be a number")
        self.refused(self.msg(op="move", id=self.p1, rev=rev, lat=True, lon=0.0), "must be a number")

    def test_4_unknown_thing(self):
        self.refused(self.msg(op="press", id="a999999"), "not a pin on this map")
        self.refused(self.msg(op="press", id=self.elsewhere), "not a pin on this map")
        outside = self.make(self.kinds, 'kind=pin title=Outside lat=1 lon=1 label=Outside')
        self.refused(self.msg(op="press", id=outside), "not a pin on this map")   # a pin, but not on this map

    def test_4_any_command_string_is_refused(self):
        rev = self.pin(self.p1)["rev"]
        self.refused(self.msg(op="press", id=f"{self.p1}; do remove {self.p1}"), "world id")
        self.refused(self.msg(op="move", id=self.p1, rev=rev, lat=1.0, lon=1.0, line=f"do remove {self.p1}"), "carries only")
        self.refused(self.msg(op=f"do remove {self.p1}"), "unknown op")
        self.refused(self.msg(op="move", id=self.p1, rev=f"{rev}; do remove {self.p1}", lat=1.0, lon=1.0), "whole number")
        self.refused(f"do remove {self.p1}", "JSON object")
        n0 = len(self.w.events)
        self.assertEqual(n0, len(self.w.events))

    def test_a_drop_is_one_undoable_create_in_the_scope(self):
        out = M.check(self.w, self.msg(op="drop", lat=51.51912345, lon=-0.12654321), self.map)
        self.assertEqual(f'do create {self.map} kind=pin title="New pin" label="New pin" lat=51.519123 lon=-0.126543', out["line"])
        self.assertEqual({"item": self.map, "rev": self.w.nodes[self.map]["rev"]}, out["observed"])
        n0 = len(self.w.events)
        made = re.search(r"created (a\d+)", self.line(out["line"]))[1]
        self.assertEqual(n0 + 1, len(self.w.events))
        p = self.pin(made)
        self.assertEqual((51.519123, -0.126543, "New pin"), (p["lat"], p["lon"], p["label"]))
        self.line(f"undo {self.w.events[-1]['id']}")
        self.assertNotIn(made, {x["id"] for x in self.drawn()["draw"]["pins"]})
        with self.assertRaises(M.Refused) as e:
            M.check(self.w, self.msg(op="drop", lat=51.5, lon=-0.12), None)
        self.assertIn("scope surface", str(e.exception))

    def test_a_press_views_only_the_pin(self):
        out = M.check(self.w, self.msg(op="press", id=self.p1), self.map)
        self.assertEqual(f"do view {self.p1}", out["line"])
        self.assertIsNone(out["observed"])

    def test_coordinates_are_written_as_plain_decimals(self):
        rev = self.pin(self.p1)["rev"]
        out = M.check(self.w, self.msg(op="move", id=self.p1, rev=rev, lat=0.00001, lon=-0.000000001), self.map)
        self.assertEqual(f"do prop {self.p1} lat=0.00001 lon=0", out["line"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
