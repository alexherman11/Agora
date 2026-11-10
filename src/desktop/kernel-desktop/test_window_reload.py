"""window.reload: a page again from disk, in place. MemScreen only; no real windows."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

import kd_window


class WindowReload(unittest.TestCase):
    def host(self, rows):
        h = kd_window.WindowHost.__new__(kd_window.WindowHost)
        h.owner, h.rows, h.intent = "alex", {r["id"]: r for r in rows}, {}
        h.m = SimpleNamespace(see=Mock(return_value={"ok": True, "rows": rows}))
        h.screen = kd_window.MemScreen()
        for r in rows:
            h.screen.wins[r["id"]] = {"box": (0, 0, 800, 600), "min": r.get("tucked", False)}
        return h

    def say(self, h, target=None, words=""):
        return h._call({"word": "window.reload", "caller": {"person": "alex"}, "use": "s",
                        "args": {"words": words, "target": target, "kv": {}}})

    def test_one_window_reloads_and_stays_put(self):
        h = self.host([{"id": "w1", "name": "Writing", "rev": 1}, {"id": "w2", "name": "Map", "rev": 1, "tucked": True}])
        r = self.say(h, "w2")
        self.assertEqual(r.get("text"), "Map reloaded")
        self.assertNotIn("lines", r)                       # nothing recorded in the world
        self.assertEqual(h.screen.wins["w2"]["reloads"], 1)
        self.assertTrue(h.screen.wins["w2"]["min"])        # a tucked window stays tucked
        self.assertNotIn("reloads", h.screen.wins["w1"])

    def test_all_reloads_every_window(self):
        h = self.host([{"id": "w1", "name": "A", "rev": 1}, {"id": "w2", "name": "B", "rev": 1}])
        for how in ({"target": "all"}, {"words": "all"}):
            with self.subTest(**how):
                self.assertIn("2 windows reloaded", self.say(h, **how)["text"])

    def test_unknown_window_is_refused(self):
        self.assertIn("refused", self.say(self.host([]), "nope"))


if __name__ == "__main__":
    unittest.main()
