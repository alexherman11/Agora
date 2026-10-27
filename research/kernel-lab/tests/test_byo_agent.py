"""The neighbour story and the adapter's public wire contract. Never calls a model."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LAB / "proof"))
sys.path.insert(0, str(LAB / "mcp"))
import byo_agent  # noqa: E402
import agora_mcp  # noqa: E402


class BYOStory(unittest.TestCase):
    def test_the_neighbour_builds_and_lends_over_real_mcp(self):
        with tempfile.TemporaryDirectory(prefix="byo-evidence-") as out:
            self.assertEqual(byo_agent.main(["--out", out]), 0)
            evidence = json.loads((Path(out) / "byo-agent.json").read_text(encoding="utf-8"))
            self.assertTrue(evidence["complete"])
            self.assertGreater(len(evidence["checks"]), 15)
            self.assertTrue(all(c["ok"] for c in evidence["checks"]))
            self.assertEqual(evidence["adapter_exit"], 0)

    def test_the_guide_uses_ordinary_genesis_things_and_stays_in_sync(self):
        seed = json.loads((LAB / "genesis.example.json").read_text(encoding="utf-8"))
        guides = [t for t in seed["things"] if t.get("kind") == "guide"]
        self.assertEqual(len(guides), 1)
        self.assertEqual(guides[0]["title"], "How to build here")
        self.assertEqual(guides[0]["text"], byo_agent.GUIDE.read_text(encoding="utf-8"))


class MCPWire(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(prefix="byo-wire-")
        self.place = byo_agent.Place(self.folder.name)
        self.client = byo_agent.MCP(self.place.url, self.place.agent_token)

    def tearDown(self):
        self.client.close()
        self.place.close()
        self.folder.cleanup()

    def test_initialize_notifications_errors_and_unicode_are_real_wire(self):
        early = self.client.request("tools/list")
        self.assertEqual(early["error"]["code"], -32002)
        initialized = self.client.initialize("2030-01-01")
        self.assertEqual(initialized["protocolVersion"], "2025-11-25")
        # Unknown notification must not leave a spurious reply before ping's matching id.
        self.client.send({"jsonrpc": "2.0", "method": "notifications/not-supported"})
        self.assertEqual(self.client.request("ping")["result"], {})
        self.assertEqual(self.client.request("resources/list")["error"]["code"], -32601)
        line = 'post "Prête la perceuse — mañana 🛠"'
        sent = self.client.tool("do", line)
        self.assertEqual(sent["as"], "agent for Lena")
        feed = self.client.tool("see", "look")
        self.assertIn("Prête la perceuse — mañana 🛠", feed["text"])
        before = len(self.place.kernel.log.records)
        denied = self.client.tool("see", 'post "cannot act"', ok=False)
        self.assertIn("/see", denied["text"])
        self.assertEqual(len(self.place.kernel.log.records), before)

    def test_unknown_tools_and_extra_arguments_do_not_reach_the_door(self):
        self.client.initialize()
        before = len(self.place.kernel.log.records)
        for params in ({"name": "exec", "arguments": {"line": "help"}},
                       {"name": "do", "arguments": {"line": "post hello", "as": "Alex"}},
                       {"name": "do", "arguments": {"line": "post hello", "url": "http://example.org"}},
                       {"name": "see", "arguments": {"line": 4}},
                       {"name": "see", "arguments": {"line": " "}},
                       {"name": "do", "arguments": []}):
            with self.subTest(params=params):
                self.assertEqual(self.client.request("tools/call", params)["error"]["code"], -32602)
        self.assertEqual(len(self.place.kernel.log.records), before)

    def test_bad_json_invalid_requests_and_eof(self):
        self.client.process.stdin.write(b'not-json\n')
        self.client.process.stdin.flush()
        self.assertEqual(self.client.receive()["error"]["code"], -32700)
        self.client.send([])
        self.assertEqual(self.client.receive()["error"]["code"], -32600)
        self.client.initialize()
        self.assertEqual(self.client.request("ping")["result"], {})
        self.client.close()
        self.assertEqual(self.client.process.returncode, 0)
        self.assertEqual(self.client.stderr, [])


class DoorBoundary(unittest.TestCase):
    def test_only_loopback_origins_and_one_private_credential_are_accepted(self):
        for url in ("https://example.org", "http://example.org", "http://127.0.0.1:8810/other",
                    "http://user:secret@127.0.0.1:8810", "http://127.0.0.1:8810?token=secret"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                agora_mcp.Door(url, bearer="private")
        for args in ({}, {"bearer": "a", "session": "b"}, {"bearer": "a\r\nb"}, {"session": "a;b"}):
            with self.subTest(args=args), self.assertRaises(ValueError):
                agora_mcp.Door("http://127.0.0.1:8810", **args)

    def test_credentials_are_headers_and_the_body_is_only_the_line(self):
        # Inspect the actual urllib Request created at the final outbound boundary.
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def read(self):
                return b'{"ok": true, "text": "done", "rows": [], "records": []}'

        class Capture:
            def open(self, request, timeout):
                self.request = request
                return Response()

        for credential, header, value in (({"bearer": "private"}, "Authorization", "Bearer private"),
                                          ({"session": "private"}, "Cookie", "agora_session=private")):
            door = agora_mcp.Door("http://127.0.0.1:8810", **credential)
            door.opener = capture = Capture()
            result = door.call("see", "help")
            self.assertEqual(capture.request.full_url, "http://127.0.0.1:8810/see")
            self.assertEqual(capture.request.get_header(header), value)
            self.assertEqual(json.loads(capture.request.data), {"line": "help"})
            self.assertNotIn("private", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
