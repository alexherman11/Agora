"""a10672: the paint lane's pure parts (no browser, desktop or job): tiles, the overview's scale, names, regions."""
import re
import sys
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paint  # noqa: E402


class Parts(unittest.TestCase):
    def test_a_1280_page_at_150_fits_whole(self):
        self.assertTrue(paint.fits([1920, 1200]))
        self.assertEqual(paint.overview_scale(1280, 800, 1.5), 1.0)

    def test_a_2560_page_at_150_is_drawn_smaller_to_fit(self):
        self.assertFalse(paint.fits([3840, 2160]))
        s = paint.overview_scale(2560, 1440, 1.5)
        self.assertLessEqual(round(2560 * 1.5 * s), 2048)
        self.assertLessEqual(round(1440 * 1.5 * s), 2048)
        self.assertEqual(round(2560 * 1.5 * s), 2048)              # the long side uses the whole limit

    def test_tiles_cover_the_rect_and_each_fits(self):
        rect = [0, 109, 2560, 714]
        got = paint.tiles(rect, 1.5)
        self.assertEqual(len(got), 2)                              # 3840 px wide: two tiles across, one down
        for _, _, (x, y, w, h) in got:
            self.assertLessEqual(w * 1.5, 2048 + 1e-9)
            self.assertLessEqual(h * 1.5, 2048 + 1e-9)
        self.assertAlmostEqual(sum(t[2][2] for t in got), 2560)
        self.assertEqual(got[1][2][0], 2048 / 1.5)

    def test_a_small_rect_is_one_tile_as_it_is(self):
        self.assertEqual(paint.tiles([10, 20, 300, 40], 1.5), [(0, 0, [10, 20, 300, 40])])

    def test_names_fit_the_delivery_route(self):
        self.assertTrue(re.fullmatch(r"\d{4}-\d\d-\d\d-\d{6}-(?:1280x800|2560x1440)", paint.run_name("2560x1440", 0)))
        self.assertTrue(re.fullmatch(r"[a-zA-Z0-9_-]+", paint.slug("board/sections/working")))
        self.assertEqual(paint.slug("///"), "part")

    def test_regions(self):
        self.assertEqual(paint.region("0,0,640,480"), [0, 0, 640, 480])
        for bad in ("1,2,3", "0,0,0,5", "a,b,c,d", "0,0,nan,2", "0,0,inf,2", "-1,0,4,5"):
            with self.assertRaises(ValueError):
                paint.region(bad)

    def test_the_token_is_read(self):
        t = paint.token_facts()
        self.assertTrue(t["readable"])
        self.assertIn("restricted", t)

    def test_acceptance_requires_cleanup_verifier_guard_and_admission(self):
        good = {"rows": [{"outcome": "pass"}], "guard": [0, "untouched"],
                "cleanup": {"ok": True}, "verification": {"allow_interaction": True,
                                                          "network_label": "network: observed, not contained"},
                "post_admission": {"admitted": True}}
        self.assertTrue(paint.accepted(good))
        # a13146: an accepted paint always says what the network was, and never more than 'observed, not contained'
        for label in (None, "network: observed", "network: contained", "network: unknown, not contained"):
            bad = deepcopy(good)
            bad["verification"]["network_label"] = label
            self.assertFalse(paint.accepted(bad), label)
        for field in ("cleanup", "verification", "post_admission", "guard"):
            bad = deepcopy(good)
            del bad[field]
            self.assertFalse(paint.accepted(bad), field)
        for extra in ({"error": "refused"}, {"missing": ["unpainted crop"]}):
            self.assertFalse(paint.accepted(dict(good, **extra)))

    def test_refused_admission_creates_no_copy_or_browser(self):
        import guard_context
        with patch.object(guard_context, "read", return_value={"admitted": False, "reason": "stale"}), \
             patch.object(paint, "Copy") as copy:
            self.assertEqual(paint.main(["home-base"]), 1)
            copy.assert_not_called()

    def test_delivery_never_overrides_disabled_runtime_route(self):
        rep = {"rows": [{"outcome": "pass", "shots": []}], "guard": [0],
               "cleanup": {"ok": True}, "verification": {"allow_interaction": True,
                                                         "network_label": "network: observed, not contained"},
               "post_admission": {"admitted": True}, "size": "1280x800"}
        with patch.dict(paint.os.environ, {"DESKD": "off"}), \
             patch.object(paint.subprocess, "run") as send:
            result = paint.deliver(paint.DEMO_ROOT, "run", rep, "pike", "card", None, "worker")
            self.assertIn("disabled", result[0])
            send.assert_not_called()

    def test_failed_size_stops_request_and_copy_is_closed(self):
        import guard_context
        copy = unittest.mock.MagicMock()
        rep = {"result": "failed", "rows": [{"outcome": "fail"}], "shots": {}}
        with patch.object(guard_context, "read", return_value={"admitted": True}), \
             patch.object(paint, "Copy", return_value=copy), \
             patch.object(paint, "paint_one", return_value=("run", rep)) as one:
            self.assertEqual(paint.main(["home-base"]), 1)
            self.assertEqual(one.call_count, 1)
            copy.close.assert_called_once()


class LaunchGate(unittest.TestCase):
    """Fake OS/browser only: admission must precede every CDP interaction."""

    def run_launch(self, refuse, local_only=False):
        import sandbox_window as sb
        import sandbox_receipts
        from contextlib import ExitStack
        events = []
        state = {"pid": 123, "port": 456}

        def gate(st):
            self.assertIs(st, state)
            events.append("gate")
            if refuse:
                raise RuntimeError("fixture refusal")

        client = MagicMock()
        client.js.return_value = "complete"
        def connect(port):
            events.append("cdp")
            return client
        manifest = MagicMock()
        manifest.exists.return_value = False
        fake_state = MagicMock()
        fake_state.__truediv__.return_value = Path("fixture-profile")
        with ExitStack() as stack:
            for name, value in (
                ("STATE", fake_state), ("state_file", MagicMock(return_value=manifest)),
                ("free_port", MagicMock(return_value=456)), ("start", MagicMock(return_value=123)),
                ("wait_cdp", MagicMock(return_value=True)),
                ("top_windows", MagicMock(return_value=[(0, 0, 0, True, True, [0, 0, 200])])),
                ("Cdp", MagicMock(side_effect=connect)),
                ("start_failure", MagicMock(return_value="fixture failure")),
                ("close", MagicMock(side_effect=lambda *a, **k: events.append("cleanup"))),
            ):
                stack.enter_context(patch.object(sb, name, value))
            stack.enter_context(patch.object(sandbox_receipts, "update_manifest", return_value=state))
            scope = object()
            if refuse:
                with self.assertRaisesRegex(SystemExit, "fixture failure"):
                    sb.open_edge("fixture", "http://127.0.0.1:456/page", tries=1, viewport=False,
                                 job=scope, before_cdp=gate, local_only=local_only)
                self.assertEqual(events, ["gate", "cleanup"])
                sb.Cdp.assert_not_called()
            else:
                sb.open_edge("fixture", "http://127.0.0.1:456/page", tries=1, viewport=False,
                             job=scope, before_cdp=gate, local_only=local_only)
                self.assertEqual(events, ["gate", "cdp"])
                client.close.assert_called_once()
            self.assertIs(sb.start.call_args.kwargs["job"], scope)
            sb.start.assert_called_once()
            return sb.start.call_args.args[1]

    def test_refused_gate_cleans_owned_launch_without_cdp_or_retry(self):
        self.run_launch(refuse=True)

    def test_admitted_gate_precedes_cdp_with_same_retained_job(self):
        self.run_launch(refuse=False)

    def test_local_refusal_still_cleans_once_before_any_cdp(self):
        self.run_launch(refuse=True, local_only=True)

    def test_local_flags_are_additive_and_ordinary_argv_is_unchanged(self):
        import sandbox_window as sb
        ordinary = self.run_launch(refuse=False)
        local = self.run_launch(refuse=False, local_only=True)
        added = sb.local_paint_switches("http://127.0.0.1:456/page")
        self.assertEqual([a for a in local if a not in added], ordinary)
        self.assertTrue(all(a in local for a in added))
        self.assertEqual(len(local), len(ordinary) + len(added))
        for forbidden in ("--no-sandbox", "--ignore-certificate-errors", "--disable-web-security"):
            self.assertNotIn(forbidden, local)

    def test_remote_or_ambiguous_url_refused_before_any_effect(self):
        import sandbox_window as sb
        bad = ("https://example.org", "http://example.org:456", "file:///tmp/a",
               "http://127.0.0.1:456@evil.invalid", "http://x@127.0.0.1:456",
               "http://127.0.0.1:456\\@evil.invalid", "http://127.0.0.1",
               "http://localhost:456", "http://127.1:456", "http://2130706433:456",
               "http://127.0.0.1:0", "http://127.0.0.1:65536", "http://127.0.0.1:456/\n",
               " http://127.0.0.1:456", "data:text/html,hi", None)
        with patch.object(sb, "start") as start, patch.object(sb, "state_file") as state:
            for url in bad:
                with self.subTest(url=url), self.assertRaises(ValueError):
                    sb.open_edge("fixture", url, tries=1, job=object(),
                                 before_cdp=lambda st: None, local_only=True)
            start.assert_not_called()
            state.assert_not_called()

    def test_local_requires_owned_single_attempt_and_gate(self):
        import sandbox_window as sb
        with patch.object(sb, "start") as start, patch.object(sb, "state_file") as state:
            for kwargs in ({"job": None, "before_cdp": lambda st: None, "tries": 1},
                           {"job": object(), "before_cdp": None, "tries": 1},
                           {"job": object(), "before_cdp": lambda st: None, "tries": 2}):
                with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                    sb.open_edge("fixture", "http://127.0.0.1:456/page", local_only=True, **kwargs)
            start.assert_not_called()
            state.assert_not_called()


class NetworkContract(unittest.TestCase):
    """Use the production verifier with its fake kernel, never this PC's sockets."""

    def test_runner_requests_local_mode_and_keeps_fail_closed_policy(self):
        import guard_context
        import sandbox_window as sb
        import native_run_verify as nv
        from contextlib import ExitStack
        scope = MagicMock()
        scope.descriptor = {}
        guard = MagicMock()
        guard.first = {"foreground": 1}
        guard.verdict.return_value = (0, "untouched")
        verifier = MagicMock()
        verifier.gate.return_value = {"allow_interaction": False}
        verifier.verdict.return_value = {"allow_interaction": False}
        state = MagicMock()
        state.exists.return_value = False

        def fake_launch(*args, **kwargs):
            self.assertTrue(kwargs["local_only"])
            self.assertEqual(kwargs["tries"], 1)
            self.assertIs(kwargs["job"], scope)
            kwargs["before_cdp"]({"owners": []})

        with ExitStack() as stack:
            stack.enter_context(patch.object(guard_context, "read", return_value={"admitted": True}))
            stack.enter_context(patch.object(paint, "token_facts", return_value={"fake": True}))
            stack.enter_context(patch.object(sb, "Guard", return_value=guard))
            stack.enter_context(patch.object(sb, "job_scope")).return_value.__enter__.return_value = scope
            stack.enter_context(patch.object(sb, "state_file", return_value=state))
            launch = stack.enter_context(patch.object(sb, "open_edge", side_effect=fake_launch))
            cdp = stack.enter_context(patch.object(sb, "Cdp"))
            constructor = stack.enter_context(patch.object(nv, "Verifier", return_value=verifier))
            copy = MagicMock()
            copy.at = 123
            copy.url.return_value = "http://127.0.0.1:456/lens.html?session=s&as=a&lens=fixture"
            _, report = paint.paint_one(copy, "fixture", "fixture", "1280x800", [], [], MagicMock())
            spec = constructor.call_args.args[0]
            self.assertEqual(spec["allow_remote"], [])
            self.assertTrue(spec["allow_loopback"])
            self.assertEqual((spec["network_mode"], spec["pages"]), ("local-page", [copy.url.return_value]))
            self.assertEqual(launch.call_args.args[1], copy.url.return_value)       # the page judged is the page opened
            self.assertEqual(report["network_policy"], paint.local_network_policy(copy.url.return_value))
            self.assertIn("network", report)
            self.assertFalse(paint.accepted(report))
            self.assertEqual(report["error"]["type"], "RuntimeError")
            self.assertFalse(report["interaction_gate"]["allow_interaction"])
            self.assertEqual(report["failed_at"], "edge")
            launch.assert_called_once()
            cdp.assert_not_called()
            verifier.stop_sampling.assert_called_once()
            verifier.after.assert_called_once()

    PAGE = "http://127.0.0.1:456/lens.html?session=s&as=a&lens=fixture"

    def test_the_browsers_background_traffic_is_listed_and_labelled_others_still_refuse(self):
        # a13146 (JEFF m13143): under the paint's own policy, the job's browser's background traffic (as a11403's real
        # run saw: IPv6 :443 and mDNS) is observed and listed; a launcher's traffic, an unreadable table, a public or
        # account page, and the same traffic without the mode are not accepted
        import test_native_run_verify as fixture
        edge = [(101, 5, "fd00::2", 50000, "2001:db8::1", 443), (102, 5, "10.0.0.2", 50001, "203.0.113.1", 443),
                (101, 5, "127.0.0.1", 50002, "127.0.0.1", 456)]
        cases = {   # name: (tcp rows, udp rows, net fails, page, mode on, expected status)
            "browser-background": (edge, [(101, "0.0.0.0", 5353)], False, self.PAGE, True, "observed"),
            "launcher-traffic": ([(100, 5, "10.0.0.2", 50003, "198.51.100.9", 443)], [], False, self.PAGE, True,
                                 "violation"),
            "unreadable": ([], [], True, self.PAGE, True, "unknown"),
            "public-page": (edge, [], False, "https://example.org/", True, "violation"),
            "account-page": (edge, [], False, "http://alex:pw@127.0.0.1:456/", True, "violation"),
            "without-the-mode": (edge, [], False, self.PAGE, False, "violation"),
        }
        for name, (tcp, udp, fails, page, mode, expected) in cases.items():
            with self.subTest(name=name):
                f = fixture.Case()
                f.setUp()
                try:
                    f.n.tcp_rows, f.n.udp_rows, f.n.net_fails = tcp, udp, fails
                    policy = paint.local_network_policy(page)
                    if not mode:
                        policy = {k: v for k, v in policy.items() if k not in ("network_mode", "pages")}
                    verdict = f.whole(f.verifier(**policy))
                    self.assertEqual(verdict["network"]["status"], expected, verdict["network"]["reasons"])
                    self.assertEqual(verdict["allow_interaction"], expected == "observed")
                    summary = paint.network_summary(verdict)
                    if mode:
                        self.assertEqual(summary["label"], f"network: {expected}, not contained")
                    else:
                        self.assertEqual(summary["label"], "network: violation")
                    if name == "browser-background":
                        self.assertEqual({(c["process"], c["protocol"], c["address"], c["port"])
                                          for c in summary["connections"]},
                                         {("msedgewebview2.exe", "tcp", "2001:db8::1", 443),
                                          ("msedgewebview2.exe", "tcp", "203.0.113.1", 443),
                                          ("msedgewebview2.exe", "udp", "0.0.0.0", 5353)})
                    self.assertEqual(policy["allow_remote"], [])
                finally:
                    f.tearDown()


if __name__ == "__main__":
    unittest.main()
