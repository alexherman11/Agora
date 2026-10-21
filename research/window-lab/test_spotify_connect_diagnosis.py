"""Connection-boundary probes: in-memory HTTP doubles, no sockets or private store.

These cover the diagnosed lifecycle and its bounded error-reporting repair.
They do not establish Alex's historical failure.
"""

import contextlib
import io
import socket
import sys
import types
import unittest
import urllib.parse
from unittest.mock import Mock, patch

import host_verbs
import spotify_connect as setup
import spotify_like as sl

CID = "0123456789abcdef0123456789abcdef"


class InlineThread:
    def __init__(self, target, args=(), **kwargs):
        self.target, self.args = target, args

    def start(self):
        self.target(*self.args)


class Server:
    """Construct handler instances without a socket or BaseHTTPRequestHandler I/O."""

    def __init__(self, address, handler):
        self.server_port = address[1] or 12345
        self.handler = handler
        self.closed = False
        self.action = lambda server: None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.server_close()

    def server_close(self):
        self.closed = True

    def handle_request(self):
        self.action(self)

    def request(self, method, path, form=None):
        h = object.__new__(self.handler)
        body = urllib.parse.urlencode(form or {}).encode()
        h.path = path
        h.headers = {"Content-Length": str(len(body))}
        h.rfile, h.wfile = io.BytesIO(body), io.BytesIO()
        h.send_response = lambda code: setattr(h, "status", code)
        h.send_header = lambda *args: None
        h.end_headers = lambda: None
        getattr(h, "do_" + method)()
        return h.status, h.wfile.getvalue()


class Diagnosis(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        # An accidental transport/store use must fail rather than reach the PC.
        self.stack.enter_context(
            patch.object(socket, "socket", side_effect=AssertionError("no sockets"))
        )
        self.stack.enter_context(
            patch.object(sl.Library, "_read", side_effect=AssertionError("no private reads"))
        )
        self.stack.enter_context(
            patch.object(sl.Library, "_write", side_effect=AssertionError("no private writes"))
        )
        self.stack.enter_context(
            patch.object(sl.urllib.request, "urlopen", side_effect=AssertionError("no network"))
        )
        self.stack.enter_context(patch.object(sl.threading, "Thread", InlineThread))

    def test_setup_expires_before_developer_setup_completes(self):
        library = types.SimpleNamespace(client_id=lambda: "", connect=Mock())
        made = []

        def make(*args):
            made.append(Server(*args))
            return made[-1]

        with (
            patch.object(setup, "HTTPServer", side_effect=make),
            patch.object(setup.time, "monotonic", side_effect=[0, 301]),
        ):
            with self.assertRaisesRegex(sl.ConnectionFailure, "Client ID setup page expired"):
                setup.connect(library, lambda url: True)
        self.assertTrue(made[0].closed)
        library.connect.assert_not_called()

    def test_false_setup_browser_open_is_reported_before_timeout(self):
        library = types.SimpleNamespace(client_id=lambda: "", connect=Mock())
        opener = Mock(return_value=False)
        with (
            patch.object(setup, "HTTPServer", side_effect=Server),
            patch.object(setup.time, "monotonic", side_effect=[0, 301]),
        ):
            with self.assertRaisesRegex(sl.ConnectionFailure, "browser could not open"):
                setup.connect(library, opener)
        opener.assert_called_once()
        library.connect.assert_not_called()

    def test_form_rejects_forgery_and_continues_only_after_client_id_submission(self):
        library = types.SimpleNamespace(
            client_id=lambda: "", connect=Mock(return_value="fake consent")
        )
        urls, statuses = [], []

        def make(*args):
            server = Server(*args)

            def submit(s):
                nonce = urllib.parse.parse_qs(urllib.parse.urlparse(urls[0]).query)["state"][0]
                statuses.append(
                    s.request("POST", "/setup", {"state": "forged", "client_id": CID})[0]
                )
                statuses.append(s.request("POST", "/setup", {"state": nonce, "client_id": CID})[0])

            server.action = submit
            return server

        with patch.object(setup, "HTTPServer", side_effect=make):
            self.assertEqual(setup.connect(library, urls.append), "fake consent")
        self.assertEqual(statuses, [400, 200])
        self.assertEqual(library.connect.call_args.args[1], CID)

    def test_pkce_redirect_and_scopes_without_secret(self):
        library = sl.Library()
        urls, forms = [], []
        library._keep = Mock()

        def post(url, form):
            forms.append(form)
            return {"access_token": "fixture-only", "refresh_token": "fixture-only"}

        library._post_form = post
        library._write = Mock()

        def make(*args):
            server = Server(*args)

            def callback(s):
                query = urllib.parse.parse_qs(urllib.parse.urlparse(urls[0]).query)
                s.request(
                    "GET",
                    "/callback?"
                    + urllib.parse.urlencode({"state": query["state"][0], "code": "fixture-code"}),
                )

            server.action = callback
            return server

        with patch.object(sl, "HTTPServer", side_effect=make):
            self.assertTrue(library.connect(urls.append, CID).startswith("connected:"))
        query = urllib.parse.parse_qs(urllib.parse.urlparse(urls[0]).query)
        self.assertEqual(query["redirect_uri"], ["http://127.0.0.1:8797/callback"])
        self.assertEqual(query["code_challenge_method"], ["S256"])
        self.assertEqual(
            set(query["scope"][0].split()),
            {"user-library-read", "user-library-modify", "user-read-currently-playing"},
        )
        self.assertEqual(forms[0]["redirect_uri"], query["redirect_uri"][0])
        self.assertNotIn("client_secret", forms[0])
        self.assertIn("code_verifier", forms[0])
        library._write.assert_called_once_with("app.json", {"client_id": CID})

    def test_saved_client_id_skips_form_but_still_requires_consent(self):
        library = types.SimpleNamespace(
            client_id=lambda: CID, connect=Mock(return_value="fake consent")
        )
        with patch.object(setup, "HTTPServer", side_effect=AssertionError("no setup listener")):
            self.assertEqual(setup.connect(library, Mock()), "fake consent")
        library.connect.assert_called_once()

    def test_host_allowlists_typed_failures_and_masks_unexpected_errors(self):
        library = types.SimpleNamespace(connect_status="")
        hud = types.SimpleNamespace(say_desktop=Mock())
        media = types.SimpleNamespace(likes=lambda: library)
        for failure in (
            sl.ConnectionFailure("setup_expired"),
            sl.Refused("fixture-private-detail"),
            OSError("fixture-private-detail"),
        ):
            with (
                self.subTest(failure=type(failure).__name__),
                patch.dict(sys.modules, {"media": media}),
                patch.object(setup, "connect", side_effect=failure),
            ):
                self.assertEqual(host_verbs._connect(hud, ""), "opening Spotify connection")
            self.assertEqual(
                library.connect_status,
                sl.connection_message(failure),
            )
            self.assertNotIn("fixture-private-detail", library.connect_status)
        self.assertEqual(hud.say_desktop.call_count, 3)

    def test_setup_closes_before_callback_binds_but_consent_opens_after_bind(self):
        library = sl.Library()
        library.client_id = lambda: ""
        library._keep = Mock()
        library._write = Mock()
        library._post_form = Mock(return_value={
            "access_token": "fixture-only", "refresh_token": "fixture-only"})
        servers, urls, stages = [], [], []

        def opened(url):
            urls.append(url)
            stages.append("setup" if "/setup?" in url else "consent")
            self.assertFalse(servers[-1].closed)
            if stages[-1] == "consent":
                self.assertTrue(servers[0].closed)
                self.assertEqual(servers[-1].server_port, sl.PORT)
            return True

        def make(address, handler):
            server = Server(address, handler)
            servers.append(server)
            if address[1] == 0:

                def submit(s):
                    state = urllib.parse.parse_qs(urllib.parse.urlparse(urls[-1]).query)["state"][0]
                    self.assertEqual(
                        s.request("POST", "/setup", {"state": state, "client_id": CID})[0], 200
                    )
            else:

                def submit(s):
                    state = urllib.parse.parse_qs(urllib.parse.urlparse(urls[-1]).query)["state"][0]
                    self.assertEqual(
                        s.request(
                            "GET",
                            "/callback?"
                            + urllib.parse.urlencode({"state": state, "code": "fixture-only"}),
                        )[0],
                        200,
                    )

            server.action = submit
            return server

        with (
            patch.object(setup, "HTTPServer", side_effect=make),
            patch.object(sl, "HTTPServer", side_effect=make),
        ):
            self.assertTrue(setup.connect(library, opened).startswith("connected:"))
        self.assertEqual(stages, ["setup", "consent"])
        self.assertTrue(all(s.closed for s in servers))
        library._post_form.assert_called_once()

    def test_callback_bind_failure_prevents_consent_launch_and_exchange(self):
        library = sl.Library()
        library._post_form = Mock()
        opener = Mock()
        with patch.object(sl, "HTTPServer", side_effect=OSError("fixture-bind-unavailable")):
            with self.assertRaisesRegex(sl.ConnectionFailure, "return listener could not start"):
                library.connect(opener, CID)
        opener.assert_not_called()
        library._post_form.assert_not_called()

    def test_callback_timeout_closes_listener_without_exchange(self):
        library = sl.Library()
        library._post_form = Mock()
        server = Server(("127.0.0.1", sl.PORT), None)
        with (
            patch.object(sl, "HTTPServer", return_value=server),
            patch.object(sl.time, "monotonic", side_effect=[0, 301]),
        ):
            with self.assertRaisesRegex(sl.ConnectionFailure, "return listener expired"):
                library.connect(Mock(return_value=True), CID)
        self.assertTrue(server.closed)
        library._post_form.assert_not_called()

    def test_wrong_callback_path_and_state_do_not_end_active_wait(self):
        library = sl.Library()
        library._keep = Mock()
        library._write = Mock()
        library._post_form = Mock(return_value={
            "access_token": "fixture-only", "refresh_token": "fixture-only"})
        urls, statuses = [], []

        def make(address, handler):
            server = Server(address, handler)

            def requests(s):
                state = urllib.parse.parse_qs(urllib.parse.urlparse(urls[0]).query)["state"][0]
                statuses.append(s.request("GET", "/wrong-path")[0])
                statuses.append(s.request("GET", "/callback?state=forged&code=fixture-only")[0])
                library._post_form.assert_not_called()
                statuses.append(
                    s.request(
                        "GET",
                        "/callback?"
                        + urllib.parse.urlencode({"state": state, "code": "fixture-only"}),
                    )[0]
                )

            server.action = requests
            return server

        with patch.object(sl, "HTTPServer", side_effect=make):
            library.connect(urls.append, CID)
        self.assertEqual(statuses, [404, 200, 200])
        library._post_form.assert_called_once()

    def test_host_dispatch_duplicate_guard_and_failure_release(self):
        pending = []

        class DeferredThread(InlineThread):
            def start(self):
                pending.append(self.target)

        library = types.SimpleNamespace(connect_status="")
        hud = types.SimpleNamespace(say_desktop=Mock())
        media = types.SimpleNamespace(likes=lambda: library)
        with (
            patch.dict(sys.modules, {"media": media}),
            patch.object(host_verbs.threading, "Thread", DeferredThread),
            patch.object(
                setup, "connect", side_effect=OSError("fixture-bind-unavailable")
            ) as connect,
        ):
            try:
                self.assertEqual(
                    host_verbs.call(hud, "media.connect"), "ok opening Spotify connection"
                )
                self.assertEqual(
                    host_verbs.call(hud, "media.connect"), "ok Spotify connection is already open"
                )
                self.assertEqual(len(pending), 1)
                pending.pop()()
                connect.assert_called_once()
                self.assertFalse(host_verbs._CONNECT_LOCK.locked())
                self.assertEqual(
                    host_verbs.call(hud, "media.connect"), "ok opening Spotify connection"
                )
                pending.pop()()
            finally:
                # Keep this process's test lock clean even if an assertion fails.
                if host_verbs._CONNECT_LOCK.locked():
                    host_verbs._CONNECT_LOCK.release()

    def test_setup_bind_failure_does_not_open_or_advance(self):
        library = types.SimpleNamespace(client_id=lambda: "", connect=Mock())
        opener = Mock()
        with patch.object(setup, "HTTPServer", side_effect=OSError("private bind details")):
            with self.assertRaises(sl.ConnectionFailure) as raised:
                setup.connect(library, opener)
        self.assertEqual(raised.exception.reason, "setup_bind")
        self.assertNotIn("private", str(raised.exception))
        opener.assert_not_called()
        library.connect.assert_not_called()

    def test_browser_false_or_exception_closes_each_listener_without_exchange(self):
        for stage in ("setup", "callback"):
            for raises in (False, True):
                with self.subTest(stage=stage, raises=raises):
                    library = sl.Library()
                    library.client_id = lambda: ""
                    library._post_form = Mock()
                    library._keep, library._write = Mock(), Mock()
                    server = Server(("127.0.0.1", 12345), None)
                    opener = Mock(side_effect=OSError("private URL and code")) if raises else Mock(
                        return_value=False)
                    module = setup if stage == "setup" else sl
                    with patch.object(module, "HTTPServer", return_value=server):
                        with self.assertRaises(sl.ConnectionFailure) as raised:
                            if stage == "setup":
                                setup.connect(library, opener)
                            else:
                                library.connect(opener, CID)
                    self.assertEqual(raised.exception.reason, stage + "_browser")
                    self.assertNotIn("private", str(raised.exception))
                    self.assertTrue(server.closed)
                    library._post_form.assert_not_called()
                    library._keep.assert_not_called()
                    library._write.assert_not_called()

    def test_request_loop_error_is_safe_and_closes_each_listener(self):
        for stage in ("setup", "callback"):
            with self.subTest(stage=stage):
                library = sl.Library()
                library.client_id = lambda: ""
                library._post_form = Mock()
                server = Server(("127.0.0.1", 12345), None)
                server.handle_request = Mock(side_effect=OSError("private request"))
                module = setup if stage == "setup" else sl
                with patch.object(module, "HTTPServer", return_value=server):
                    with self.assertRaises(sl.ConnectionFailure) as raised:
                        if stage == "setup":
                            setup.connect(library, lambda url: True)
                        else:
                            library.connect(lambda url: True, CID)
                self.assertEqual(raised.exception.reason, stage + "_wait")
                self.assertTrue(server.closed)
                library._post_form.assert_not_called()

    def callback_flow(self, library, callback_fields):
        urls, servers = [], []

        def make(address, handler):
            server = Server(address, handler)
            servers.append(server)

            def callback(s):
                state = urllib.parse.parse_qs(urllib.parse.urlparse(urls[0]).query)["state"][0]
                s.request("GET", "/callback?" + urllib.parse.urlencode({
                    "state": state, **callback_fields}))

            server.action = callback
            return server

        with patch.object(sl, "HTTPServer", side_effect=make):
            try:
                return library.connect(urls.append, CID)
            finally:
                self.assertTrue(servers[0].closed)

    def test_consent_error_is_allowlisted_without_echoing_provider_fields(self):
        library = sl.Library()
        library._post_form = Mock()
        with self.assertRaises(sl.ConnectionFailure) as raised:
            self.callback_flow(library, {"error": "private-provider-text"})
        self.assertEqual(raised.exception.reason, "consent")
        self.assertNotIn("private", str(raised.exception))
        library._post_form.assert_not_called()

    def test_exchange_error_or_missing_sign_in_fields_never_persist(self):
        for response in (OSError("private-response"), {}, {"access_token": "fixture-only"}):
            with self.subTest(response=type(response).__name__):
                library = sl.Library()
                library._post_form = Mock(**(
                    {"side_effect": response} if isinstance(response, Exception)
                    else {"return_value": response}))
                library._keep, library._write = Mock(), Mock()
                with self.assertRaises(sl.ConnectionFailure) as raised:
                    self.callback_flow(library, {"code": "fixture-only"})
                self.assertEqual(raised.exception.reason, "exchange")
                self.assertNotIn("private", str(raised.exception))
                library._keep.assert_not_called()
                library._write.assert_not_called()

    def test_each_persistence_failure_is_reported_without_claiming_connection(self):
        for failing in ("_keep", "_write"):
            with self.subTest(failing=failing):
                library = sl.Library()
                library._post_form = Mock(return_value={
                    "access_token": "fixture-only", "refresh_token": "fixture-only"})
                library._keep, library._write = Mock(), Mock()
                getattr(library, failing).side_effect = OSError("private file and token")
                with self.assertRaises(sl.ConnectionFailure) as raised:
                    self.callback_flow(library, {"code": "fixture-only"})
                self.assertEqual(raised.exception.reason, "persistence")
                self.assertNotIn("private", str(raised.exception))
                if failing == "_keep":
                    library._write.assert_not_called()

    def test_public_messages_are_closed_allowlist_including_tampered_failure(self):
        marker = "https://private.invalid/?code=fixture-token"
        errors = [OSError(marker), sl.Refused(marker), sl.ConnectionFailure(marker)]
        tampered = sl.ConnectionFailure("exchange")
        tampered.reason = marker
        errors.append(tampered)
        for error in errors:
            self.assertEqual(sl.connection_message(error),
                             sl.CONNECT_ERRORS["unexpected"] + sl.CONNECT_RECOVERY)
        for reason in sl.CONNECT_ERRORS:
            failure = sl.ConnectionFailure(reason)
            self.assertEqual(sl.connection_message(failure), str(failure))
            self.assertIn("Press Connect Spotify", str(failure))
            self.assertNotIn(marker, str(failure))

    def test_host_thread_start_failure_releases_duplicate_guard(self):
        class BrokenThread:
            def __init__(self, **kwargs):
                pass

            def start(self):
                raise OSError("private worker detail")

        library = types.SimpleNamespace(connect_status="")
        hud = types.SimpleNamespace(say_desktop=Mock())
        with (
            patch.dict(sys.modules, {"media": types.SimpleNamespace(likes=lambda: library)}),
            patch.object(host_verbs.threading, "Thread", BrokenThread),
        ):
            result = host_verbs.call(hud, "media.connect")
            self.assertTrue(result.startswith("ERR "))
            self.assertIn("fresh attempt", result)
        self.assertFalse(host_verbs._CONNECT_LOCK.locked())
        self.assertNotIn("private", library.connect_status)
        hud.say_desktop.assert_called_once()

    def test_host_initialization_failure_is_redacted_and_does_not_hold_guard(self):
        hud = types.SimpleNamespace(say_desktop=Mock())
        with patch.dict(sys.modules, {"media": types.SimpleNamespace(
            likes=Mock(side_effect=OSError("private path and token")))}):
            result = host_verbs.call(hud, "media.connect")
        self.assertTrue(result.startswith("ERR "))
        self.assertNotIn("private", result)
        self.assertFalse(host_verbs._CONNECT_LOCK.locked())

    def test_refresh_failure_does_not_leak_or_turn_success_into_launch_error(self):
        library = types.SimpleNamespace(connect_status="")
        hud = types.SimpleNamespace(say_desktop=Mock(side_effect=OSError("private refresh")))
        with (
            patch.dict(sys.modules, {"media": types.SimpleNamespace(likes=lambda: library)}),
            patch.object(setup, "connect", return_value="connected"),
        ):
            result = host_verbs.call(hud, "media.connect")
        self.assertEqual(result, "ok opening Spotify connection")
        self.assertEqual(library.connect_status, "")
        self.assertFalse(host_verbs._CONNECT_LOCK.locked())

    def test_delayed_browser_failure_is_observed_during_each_wait(self):
        for stage in ("setup", "callback"):
            with self.subTest(stage=stage):
                launches = []

                class DeferredThread(InlineThread):
                    def start(self, launches=launches):
                        launches.append(self.target)

                library = sl.Library()
                library.client_id = lambda: ""
                library._post_form = Mock()
                server = Server(("127.0.0.1", 12345), None)
                server.action = lambda s, launches=launches: launches.pop()()
                module = setup if stage == "setup" else sl
                with (
                    patch.object(module, "HTTPServer", return_value=server),
                    patch.object(sl.threading, "Thread", DeferredThread),
                ):
                    with self.assertRaises(sl.ConnectionFailure) as raised:
                        if stage == "setup":
                            setup.connect(library, lambda url: False)
                        else:
                            library.connect(lambda url: False, CID)
                self.assertEqual(raised.exception.reason, stage + "_browser")
                self.assertTrue(server.closed)
                library._post_form.assert_not_called()

    def test_setup_form_explains_finite_lifetime_without_echoing_submission(self):
        library = types.SimpleNamespace(client_id=lambda: "", connect=Mock())
        urls, pages = [], []

        def make(address, handler):
            server = Server(address, handler)

            def read_and_submit(s):
                pages.append(s.request("GET", urllib.parse.urlparse(urls[0]).path
                                       + "?" + urllib.parse.urlparse(urls[0]).query)[1])
                nonce = urllib.parse.parse_qs(urllib.parse.urlparse(urls[0]).query)["state"][0]
                s.request("POST", "/setup", {"state": nonce, "client_id": CID})

            server.action = read_and_submit
            return server

        with patch.object(setup, "HTTPServer", side_effect=make):
            setup.connect(library, urls.append)
        self.assertIn(b"temporary page expires", pages[0])
        self.assertIn(b"Connect Spotify for a fresh page", pages[0])
        self.assertNotIn(CID.encode(), pages[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
