"""Pure fixtures. These tests establish no WebView or filesystem containment."""
import copy
import unittest

from navigation import Browser, NavigationError, Target


A = "agora://fixture/item/report?lens=doc-page#summary"
W = "https://example.test/start"
L = "local://selection/fixture-selected-file"


class NavigationTests(unittest.TestCase):
    def opened(self, b, key, address, title="Fixture"):
        g = b.begin(key, address)
        self.assertTrue(b.commit(key, g, title))

    def test_mixed_tabs_deep_link_and_state_roundtrip(self):
        b = Browser()
        for address in (A, W, L):
            key = b.new_tab()
            self.opened(b, key, address)
            b.position(key, 123, 1.25)
        b.select("tab-1")
        saved = b.snapshot()
        restored = Browser.restore(copy.deepcopy(saved))
        self.assertEqual(saved, restored.snapshot())
        self.assertEqual([], restored.visits)
        self.assertEqual(A, restored.tabs["tab-1"].entries[0].target.address)
        # A local placeholder is preserved, NOT permission to open that file.
        self.assertEqual("local", restored.tabs["tab-3"].entries[0].target.kind)

    def test_real_stack_not_two_target_toggle_and_branch(self):
        b = Browser()
        key = b.new_tab()
        for address in (A, W, L):
            self.opened(b, key, address)
        self.assertEqual(W, b.move(key, -1).address)
        self.assertEqual(A, b.move(key, -1).address)
        self.assertEqual(W, b.move(key, 1).address)
        self.opened(b, key, "https://example.test/branch")
        with self.assertRaises(NavigationError):
            b.move(key, 1)
        self.assertEqual(3, len(b.tabs[key].entries))
        self.assertEqual(4, len(b.visits))  # traversal is not a new document commit

    def test_reload_redirect_replace_and_loading(self):
        b = Browser()
        key = b.new_tab()
        g = b.begin(key, W)
        self.assertEqual([], b.tabs[key].entries)
        b.commit(key, g, "Arrived", "https://example.test/final")
        self.assertEqual(1, len(b.tabs[key].entries))
        b.position(key, 77)
        g = b.begin(key, "https://example.test/final", "reload")
        b.commit(key, g, "Reloaded")
        self.assertEqual(77, b.tabs[key].entries[0].view["scroll"])
        g = b.begin(key, "https://example.test/replaced", "replace")
        b.commit(key, g, "Replaced")
        self.assertEqual(1, len(b.tabs[key].entries))

    def test_late_completion_close_and_failure_are_truthful(self):
        b = Browser()
        key = b.new_tab()
        old = b.begin(key, W)
        current = b.begin(key, A)
        self.assertFalse(b.commit(key, old, "Stale"))
        self.assertTrue(b.fail(key, current))
        self.assertEqual(-1, b.tabs[key].index)
        self.assertIn("Could not open", b.tabs[key].error)
        self.assertNotIn("browser", b.tabs[key].error)
        self.assertEqual(A, b.tabs[key].failed.address)
        g = b.begin(key, A)
        b.close(key)
        self.assertFalse(b.commit(key, g, "Closed"))
        self.assertIsNone(b.active)

    def test_failed_replacement_keeps_last_good_location_and_typed_fallback(self):
        b = Browser()
        key = b.new_tab()
        self.opened(b, key, A)
        g = b.begin(key, W)
        b.fail(key, g)
        self.assertEqual(A, b.tabs[key].entries[b.tabs[key].index].target.address)
        self.assertEqual(W, b.tabs[key].failed.address)
        self.assertIn("Open in browser", b.tabs[key].error)
        g = b.begin(key, L)
        self.assertIsNone(b.tabs[key].failed)
        b.fail(key, g)
        self.assertIn("Choose the file", b.tabs[key].error)

    def test_traversal_cancels_pending_and_preserves_positions(self):
        b = Browser()
        key = b.new_tab()
        self.opened(b, key, A)
        b.position(key, 200)
        self.opened(b, key, W)
        g = b.begin(key, L)
        b.move(key, -1)
        self.assertFalse(b.commit(key, g, "Late file"))
        self.assertEqual(200, b.tabs[key].entries[0].view["scroll"])

    def test_protocol_and_file_path_denials_do_not_change_state(self):
        b = Browser()
        key = b.new_tab()
        self.opened(b, key, A)
        before = b.snapshot()
        for address in ("javascript:alert(1)", "data:text/html,hi", "file:///C:/private.txt",
                        "C:/private.txt", r"\\server\share\file.txt", "ms-settings:display",
                        "https://user:pass@example.test/", "https://@example.test/", "https://example.test:wrong/",
                        "https://example.test\\@localhost/", "local://selection/../private",
                        "agora://fixture/item/../../private", "local://selection/a?path=C:/secret",
                        "agora://fixture/item/report?as=alex", "https://example.test/\n"):
            with self.subTest(address=address), self.assertRaises(NavigationError):
                b.begin(key, address)
        self.assertEqual(before, b.snapshot())

    def test_renderer_cannot_redirect_to_trusted_target(self):
        b = Browser()
        key = b.new_tab()
        g = b.begin(key, W)
        with self.assertRaises(NavigationError):
            b.commit(key, g, "Forged", A)
        self.assertEqual([], b.tabs[key].entries)

    def test_selection_and_close_do_not_lose_other_tab_history(self):
        b = Browser()
        for address in (A, W, L):
            self.opened(b, b.new_tab(), address)
        b.select("tab-1")
        b.position("tab-1", 222)
        b.close("tab-2")
        self.assertEqual("tab-1", b.active)
        self.assertEqual(222, b.tabs["tab-1"].entries[0].view["scroll"])
        b.close("tab-1")
        self.assertEqual("tab-3", b.active)

    def test_invalid_persisted_state_is_not_a_target_bypass(self):
        b = Browser()
        self.opened(b, b.new_tab(), A)
        for mutate in (
            lambda v: v["tabs"][0]["entries"][0]["target"].update(address="file:///C:/secret"),
            lambda v: v["tabs"][0]["entries"][0]["target"].update(kind="web"),
            lambda v: v["tabs"][0].update(index=12),
            lambda v: v.update(active="tab-999"),
            lambda v: v["tabs"].append(copy.deepcopy(v["tabs"][0])),
            lambda v: v["tabs"][0]["entries"][0].pop("target"),
            lambda v: v["tabs"][0]["entries"][0].update(view={"scroll": -1}),
        ):
            saved = b.snapshot()
            mutate(saved)
            with self.assertRaises(NavigationError):
                Browser.restore(saved)


if __name__ == "__main__":
    unittest.main()
