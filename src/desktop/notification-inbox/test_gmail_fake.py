"""Invented fixtures only; no socket, OAuth launch, host query or disk store."""
import base64
import hashlib
import json
import unittest
from urllib.parse import parse_qs, urlencode, urlsplit

from gmail_fake import OfflineGmail, ScriptedExchange, FakeResponse as R, SCOPE, live_request

CLEAR = {"awake": True, "unlocked": True, "game": "clear"}


def token(**changes):
    return R(data={"access_token": "FAKE-ACCESS", "refresh_token": "FAKE-REFRESH",
                   "scope": SCOPE, "token_type": "Bearer", "expires_in": 3600, **changes})


def metadata(unread=True, subject="INVENTED-PRIVATE-SUBJECT"):
    return R(data={"id": "FAKE-ID", "labelIds": ["INBOX"] + (["UNREAD"] if unread else []),
                   "internalDate": "123", "snippet": "MUST-NOT-RETAIN",
                   "payload": {"body": {"data": "MUST-NOT-RETAIN"},
                               "headers": [{"name": "From", "value": "invented@example.invalid"},
                                           {"name": "Subject", "value": subject},
                                           {"name": "X-Private", "value": "MUST-NOT-RETAIN"}]}})


class GmailTests(unittest.TestCase):
    def setUp(self):
        self.now = 1000
        self.api = ScriptedExchange()
        self.g = OfflineGmail(self.api, lambda: self.now)

    def begin(self):
        url = self.g.begin(49152, CLEAR)
        self.auth = parse_qs(urlsplit(url).query)
        return self.g.pending.redirect + "?" + urlencode(
            {"state": self.g.pending.state, "code": "INVENTED-CODE"})

    def connect(self):
        callback = self.begin()
        self.api.responses.append(token())
        self.assertTrue(self.g.callback(callback, CLEAR))

    def snapshot(self, **changes):
        self.api.responses.extend([R(data={"messages": [{"id": "FAKE-ID"}, {"id": "FAKE-ID"}]}),
                                   metadata(**changes)])
        self.assertTrue(self.g.sync(CLEAR))

    def test_pkce_exact_scope_and_single_use(self):
        callback = self.begin()
        p = self.g.pending
        challenge = base64.urlsafe_b64encode(hashlib.sha256(p.verifier.encode()).digest()).rstrip(b"=").decode()
        self.assertEqual(self.auth["code_challenge"], [challenge])
        self.assertEqual(self.auth["code_challenge_method"], ["S256"])
        self.assertEqual(self.auth["scope"], [SCOPE])
        self.assertEqual(self.auth["access_type"], ["offline"])
        self.api.responses.append(token())
        self.assertTrue(self.g.callback(callback, CLEAR))
        self.assertEqual(self.api.requests[0][1]["code_verifier"], p.verifier)
        self.assertEqual(self.api.requests[0][1]["grant_type"], "authorization_code")
        self.assertFalse(self.g.callback(callback, CLEAR))
        self.assertEqual(len(self.api.requests), 1)

    def test_forged_callback(self):
        callback = self.begin()
        for url in (callback.replace("127.0.0.1", "evil.invalid"),
                    callback.replace(":49152", ":49153"),
                    callback.replace("/oauth/callback", "/wrong"),
                    callback + "&state=other", callback + "&code=other",
                    callback.replace(self.g.pending.state, "forged"),
                    callback + "#fragment", callback + "&scope=" + SCOPE):
            self.assertFalse(self.g.callback(url, CLEAR))
        self.assertEqual(self.api.requests, [])

    def test_expired_or_denied_callback(self):
        callback = self.begin()
        self.now += 300
        self.assertFalse(self.g.callback(callback, CLEAR))
        self.assertIsNone(self.g.pending)
        callback = self.begin().replace("code=INVENTED-CODE", "error=access_denied")
        self.assertFalse(self.g.callback(callback, CLEAR))
        self.assertEqual(self.api.requests, [])

    def test_scope_escalation_refused(self):
        for scope in ("", SCOPE + " https://mail.google.com/", "https://mail.google.com/"):
            self.setUp()
            callback = self.begin()
            self.api.responses.append(token(scope=scope))
            self.assertFalse(self.g.callback(callback, CLEAR))
            self.assertEqual(self.g.state, "permission-lost")
            self.assertIsNone(self.g.access)

    def test_missing_refresh_or_bad_expiry_refused(self):
        for change in ({"refresh_token": ""}, {"expires_in": 0}, {"expires_in": "3600"}):
            self.setUp()
            callback = self.begin()
            self.api.responses.append(token(**change))
            self.assertFalse(self.g.callback(callback, CLEAR))

    def test_duplicate_update_dismiss_and_remote_unread(self):
        self.connect()
        self.snapshot()
        self.assertEqual(len(self.g.items), 1)
        self.g.dismiss("FAKE-ID")
        status = self.g.public_status()
        self.assertEqual((status["unread_count"], status["visible_count"]), (1, 0))
        self.snapshot(unread=False, subject="INVENTED-UPDATED")
        self.assertEqual(self.g.items["FAKE-ID"]["headers"]["subject"], "INVENTED-UPDATED")
        self.assertIn("FAKE-ID", self.g.dismissed)
        self.g.dismiss("FAKE-ID", False)
        self.assertEqual(self.g.public_status()["visible_count"], 1)
        self.assertEqual(self.g.public_status()["unread_count"], 0)
        for op, params in self.api.requests:
            self.assertIn(op, {"token", "list", "metadata"})
            self.assertNotIn("q", params)
            if op == "list":
                self.assertEqual(params["labelIds"], ["INBOX"])
            if op == "metadata":
                self.assertEqual(params["format"], "metadata")
                self.assertEqual(params["metadataHeaders"], ["From", "Subject", "Date"])

    def test_pages_commit_atomically_and_reconcile_removed(self):
        self.connect()
        self.snapshot()
        self.api.responses.extend([R(data={"messages": [], "nextPageToken": "PRIVATE-CURSOR"}),
                                   R(503)])
        self.assertFalse(self.g.sync(CLEAR))
        self.assertEqual(len(self.g.items), 1)
        self.now = self.g.retry_at
        self.api.responses.extend([R(data={"messages": [], "nextPageToken": "PRIVATE-CURSOR"}),
                                   R(data={"messages": []})])
        self.assertTrue(self.g.sync(CLEAR))
        self.assertEqual(self.g.items, {})

    def test_refresh_expiry_and_rotation(self):
        self.connect()
        self.now = self.g.expires - 30
        self.api.responses.extend([token(access_token="FAKE-NEW", refresh_token="FAKE-ROTATED"),
                                   R(data={"messages": []})])
        self.assertTrue(self.g.sync(CLEAR))
        self.assertEqual(self.api.requests[1][0], "refresh")
        self.assertEqual(self.api.requests[1][1]["grant_type"], "refresh_token")
        self.assertEqual(self.g.refresh, "FAKE-ROTATED")

    def test_revoked_refresh_purges_private_state(self):
        self.connect()
        self.snapshot()
        self.now = self.g.expires
        self.api.responses.append(R(400, {"error": "invalid_grant"}))
        self.assertFalse(self.g.sync(CLEAR))
        self.assertEqual(self.g.state, "permission-lost")
        self.assertEqual(self.g.items, {})
        self.assertIsNone(self.g.refresh)

    def test_permission_loss_no_reprompt(self):
        for status in (401, 403):
            self.setUp()
            self.connect()
            self.snapshot()
            self.api.responses.append(R(status, {"details": "PRIVATE-SERVER-ERROR"}))
            self.assertFalse(self.g.sync(CLEAR))
            calls = len(self.api.requests)
            self.assertFalse(self.g.sync(CLEAR))
            self.assertEqual(len(self.api.requests), calls)
            self.assertNotIn("PRIVATE", json.dumps(self.g.public_status()))

    def test_backoff_429_403_rate_and_server_error(self):
        for response in (R(429, retry_after=120),
                         R(403, {"reason": "rateLimitExceeded"}, 120), R(503)):
            self.setUp()
            self.connect()
            self.api.responses.append(response)
            self.assertFalse(self.g.sync(CLEAR))
            calls = len(self.api.requests)
            self.assertFalse(self.g.sync(CLEAR))
            self.assertEqual(len(self.api.requests), calls)
            self.now = self.g.retry_at
            self.api.responses.append(R(data={"messages": []}))
            self.assertTrue(self.g.sync(CLEAR))

    def test_disconnect_revocation_receipts_and_purge(self):
        self.connect()
        self.snapshot()
        self.api.responses.append(R(503))
        self.assertFalse(self.g.disconnect(CLEAR))
        self.assertEqual(self.g.items, {})
        self.assertIsNone(self.g.access)
        self.assertEqual(self.g.public_status()["revocation"], "pending")
        self.assertIsNone(self.g.begin(49152, CLEAR))
        self.api.responses.append(R())
        self.assertTrue(self.g.disconnect(CLEAR))
        self.assertEqual(self.g.state, "disconnected")
        self.assertIsNone(self.g.public_status()["unread_count"])

    def test_guard_no_work_unknown_game_sleep_locked(self):
        for guard in ({}, {**CLEAR, "awake": False}, {**CLEAR, "game": "unknown"},
                      {**CLEAR, "game": "playing"}, {**CLEAR, "unlocked": False}):
            self.setUp()
            self.assertIsNone(self.g.begin(49152, guard))
            callback = self.begin()
            self.assertFalse(self.g.callback(callback, guard))
            self.api.responses.append(token())
            self.assertTrue(self.g.callback(callback, CLEAR))
            calls = len(self.api.requests)
            self.assertFalse(self.g.sync(guard))
            self.assertFalse(self.g.disconnect(guard))
            self.assertEqual(len(self.api.requests), calls)
            self.assertEqual(self.g.state, "disconnected")

    def test_no_external_content_in_public_projection_or_errors(self):
        self.connect()
        self.snapshot()
        self.assertNotIn("MUST-NOT-RETAIN", repr(self.g.items))
        self.api.responses.append(RuntimeError("FAKE-ACCESS PRIVATE-SERVER-ERROR"))
        self.assertFalse(self.g.sync(CLEAR))
        output = json.dumps(self.g.public_status())
        for secret in ("FAKE", "INVENTED", "PRIVATE", "@", "CURSOR", "http"):
            self.assertNotIn(secret, output)
        self.assertEqual(set(self.g.public_status()), {
            "schema", "source", "state", "unread_count", "visible_count", "last_sync",
            "retry_at", "revocation", "permissions", "previews"})

    def test_public_caller_claims_never_enable_runtime(self):
        for request in ({"as": "alex"}, {"as": "jeff", "connected": True},
                        {"headers": {"Authorization": "forged"}, "action": "read"},
                        {"actor": "worker", "grant": True}, {}):
            self.assertEqual(live_request(**request)["state"], "disabled")
        self.assertEqual(self.api.requests, [])

    def test_malformed_metadata_is_sanitized_and_previous_snapshot_survives(self):
        self.connect()
        self.snapshot()
        self.api.responses.extend([R(data={"messages": [{"id": "FAKE-ID"}]}),
                                   R(data={"id": "FAKE-ID", "labelIds": ["INBOX"],
                                           "payload": {"headers": ["PRIVATE-BAD-DATA"]}})])
        self.assertFalse(self.g.sync(CLEAR))
        self.assertEqual(self.g.state, "delayed")
        self.assertEqual(len(self.g.items), 1)
        self.assertNotIn("PRIVATE", json.dumps(self.g.public_status()))

    def test_failed_code_exchange_requires_new_explicit_flow_after_backoff(self):
        callback = self.begin()
        self.api.responses.append(R(503))
        self.assertFalse(self.g.callback(callback, CLEAR))
        self.assertFalse(self.g.callback(callback, CLEAR))
        self.assertIsNone(self.g.begin(49152, CLEAR))
        self.now = self.g.retry_at
        self.assertIsNotNone(self.g.begin(49152, CLEAR))
        self.assertEqual(len(self.api.requests), 1)


if __name__ == "__main__":
    unittest.main()
