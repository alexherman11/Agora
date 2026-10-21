"""Fixture policy tests, NOT engine-origin isolation acceptance."""
import unittest
from request_policy import decision


class PolicyTests(unittest.TestCase):
    def test_trusted_targets_are_never_remote_destinations(self):
        for address, ips in (
            ("http://127.0.0.1:8794/api/snapshot", ["127.0.0.1"]),
            ("http://localhost:8794/lens.html", ["127.0.0.1"]),
            ("agora://fixture/item/report", []),
            ("local://selection/file", []),
        ):
            with self.subTest(address=address):
                self.assertTrue(decision(address, ips).startswith("deny:"))

    def test_unknown_mixed_rebound_private_and_obfuscated_addresses_deny(self):
        fixtures = [
            ("https://example.test/", []),
            ("https://example.test/", ["8.8.8.8", "10.0.0.1"]),
            ("https://example.test/", ["127.0.0.1"]),  # rebound peer
            ("http://localhost./", ["8.8.8.8"]),
            ("http://anything.local/", ["8.8.8.8"]),
            ("http://[::ffff:127.0.0.1]/", ["::ffff:127.0.0.1"]),
            ("http://[::1]/", ["::1"]),
            ("http://2130706433/", ["127.0.0.1"]),
            ("http://0177.0.0.1/", ["127.0.0.1"]),
            ("http://192.168.1.2/", ["192.168.1.2"]),
            ("http://169.254.169.254/", ["169.254.169.254"]),
            ("http://[fe80::1%25eth0]/", ["fe80::1"]),
            ("https://public.test:8794/", ["8.8.8.8"]),
            ("file:///C:/private", []),
            ("javascript:alert(1)", []),
            ("ws://public.test/", ["8.8.8.8"]),  # sockets unavailable in first stage
        ]
        for url, ips in fixtures:
            with self.subTest(url=url):
                self.assertTrue(decision(url, ips).startswith("deny:"))

    def test_public_fixture_and_redirect_recheck(self):
        self.assertTrue(decision("https://public.test/", ["8.8.8.8"]).startswith("allow:"))
        self.assertTrue(decision("http://public.test/", ["8.8.8.8"]).startswith("allow:"))
        self.assertTrue(decision("http://127.0.0.1/", ["127.0.0.1"]).startswith("deny:"))


if __name__ == "__main__":
    unittest.main()
