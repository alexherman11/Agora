# health: room test
"""a8191: artifact-view through the actual resident reader and host-route dispatcher. Disposable fixtures, a fake door;
no capture, no window, no model, no world."""
import base64
import hashlib
import io
import json
import os
import queue
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ["DESKD"] = "off"
os.environ.setdefault("HOUSE_CLAUDE", "claude")
import artifact_view
import house
import workshop
from host_route_parent import ParentDispatcher

RUN = "2026-10-21-120000-1280x800"
GUARD = [0, "alex: untouched by the sandbox (foreground, focus, cursor and input desktop polled every 20 ms)"]


class Pause(BaseException):
    pass


def initialize(r, h, rid):
    r.house, r.rid, r.proc = h, rid, None
    r.state, r.events = {}, queue.Queue()
    r.reply, r.reply_source, r.busy = [], None, False
    r.log, r.save, r.send = Mock(), Mock(), Mock()


def png(colour):
    from PIL import Image
    out = io.BytesIO()
    Image.new("RGB", (64, 40), colour).save(out, "PNG")
    return out.getvalue()


class Door:
    """The desk door as the house sees it: a snapshot, and /api/do that keeps gesture ids as deskd does."""

    def __init__(self, snapshot):
        self.snapshot, self.calls, self.done, self.fail, self.refuse = snapshot, [], {}, 0, False

    def __call__(self, path, body=None):
        self.calls.append((path, body))
        if path.startswith("/api/snapshot"):
            return self.snapshot
        if self.fail:
            self.fail -= 1
            raise TimeoutError("the door did not answer")
        if body["gesture"] in self.done:
            return {"text": f"already done, as {self.done[body['gesture']]}: nothing new was done", "error": None,
                    "events": [], "already": [self.done[body["gesture"]]]}
        if self.refuse:
            return {"text": "refused: a10 changed since this was painted; nothing was done", "error": "refused"}
        e = f"e{100 + len(self.done)}"
        self.done[body["gesture"]] = e
        return {"text": f"ok comment a10 line=...  [{e}] → created c{500 + len(self.done)}", "error": None, "events": [e]}

    def sends(self):
        return [b for p, b in self.calls if p == "/api/do"]


class ArtifactViewTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name) / "demos"
        (self.root / RUN).mkdir(parents=True)
        self.raw = png((30, 120, 200))
        (self.root / RUN / "01-map.png").write_bytes(self.raw)
        (self.root / RUN / "02-other.png").write_bytes(png((200, 30, 30)))
        report = {"guard": GUARD, "size": [1280, 800], "world_at": "e1",
                  "rows": [{"id": "map", "shots": ["01-map.png"], "outcome": "pass"},
                           {"id": "other", "shots": ["02-other.png"], "outcome": "fail"}]}
        (self.root / RUN / "report.json").write_text(json.dumps(report), encoding="utf-8")
        self.sha = hashlib.sha256(self.raw).hexdigest()
        corners = {rid: {"id": rid, "type": "surface", "rev": 3,
                         "props": {"role": "resident", "actor": actor, "provider": "claude", "model": "claude-opus-5-5"}}
                   for rid, actor in (("f1", "jeff"), ("f2", "rowan"), ("f3", "pike"))}
        self.corners = corners
        snapshot = {"nodes": {**corners, "f9": {"id": "f9", "type": "surface", "rev": 1,
                                                "props": {"role": "resident", "actor": "mallory", "model": "claude-opus-5-5"}},
                              "a10": {"id": "a10", "type": "appearance", "subject": "s9", "rev": 2}},
                    "subjects": {"s9": {"id": "s9", "kind": "task", "title": "a card", "text": "the card", "rev": 4}}}
        self.door = Door(snapshot)
        self.h = SimpleNamespace(dir=Path(tmp.name) / "house", world="frontier-test", residents={},
                                 load=lambda: None, corners=lambda w: self.corners)
        self.route = ParentDispatcher(house=self.h)
        self.route.artifact_view.door, self.route.artifact_view.root = self.door, self.root
        self.h.host_route = self.route
        self.r = {}
        for rid in ("f1", "f2", "f3"):
            r = object.__new__(house.Resident)
            initialize(r, self.h, rid)
            self.h.residents[rid] = self.r[rid] = r
            r.proc = SimpleNamespace(stdout=(), wait=Mock(return_value=0), pid=1)
            r._bind_child(r.proc)

    def turn(self, r, text):
        p = r.proc
        events = [{"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}, {"type": "result"}]

        def stream():
            for e in events:
                yield json.dumps(e) + "\n"
            raise Pause()
        p.stdout = stream()
        with self.assertRaises(Pause):
            r._read(p, self.route.sessions[r])
        return r.turns_ended()[0]

    def ask(self, r=None, **over):
        payload = {"action": "artifact-view", "request": "map-1", "artifact": f"{RUN}/01-map.png", "sha256": self.sha,
                   "recipient": "rowan", "target": "a10", "prompt": "Name three things you see."}
        payload.update(over)
        text = self.turn(r or self.r["f1"], "> look a10\n> host-route " + json.dumps(payload))
        self.assertEqual(text, "> look a10", "the intent never reaches the desk; the line beside it does")
        return json.loads(text.host_receipts[0].split(": ", 1)[1])

    def test_delivers_one_addressed_image_comment_signed_by_the_issuer(self):
        got = self.ask()
        self.assertEqual(got["status"], "delivered", got)
        self.assertEqual((got["comment"], got["issuer"], got["recipient"]), ("c501", "jeff", "rowan"))
        [sent] = self.door.sends()
        self.assertEqual(sent["as"], "jeff")
        self.assertTrue(sent["line"].startswith('do comment a10 line="@rowan: Targeted visual review'))
        data = sent["image_context"]["data_url"].split(",", 1)[1]
        self.assertEqual(hashlib.sha256(base64.b64decode(data)).hexdigest(), self.sha)
        self.assertTrue(sent["gesture"].startswith("artifact-view-") and sent["whole"])

    def test_two_recipients_get_the_same_pixels(self):
        a, b = self.ask(recipient="rowan", request="r"), self.ask(recipient="pike", request="p")
        self.assertEqual((a["status"], b["status"]), ("delivered", "delivered"))
        x, y = self.door.sends()
        self.assertEqual(x["image_context"]["data_url"], y["image_context"]["data_url"])
        self.assertIn("@pike:", y["line"])

    def test_repeat_is_kept_not_resent(self):
        first = self.ask()
        again = self.ask()
        self.assertTrue(again["repeat"])
        self.assertEqual(again["comment"], first["comment"])
        self.assertEqual(len(self.door.sends()), 1)

    def test_same_id_other_words_refused(self):
        self.ask()
        got = self.ask(prompt="something else")
        self.assertEqual(got["status"], "refused")
        self.assertIn("another request", got["reason"])
        self.assertEqual(len(self.door.sends()), 1)

    def test_unknown_then_repeat_settles_without_a_second_comment(self):
        self.door.fail = 1
        got = self.ask()
        self.assertEqual(got["status"], "unknown", got)
        self.door.done[self.door.sends()[0]["gesture"]] = "e100"      # the door had acted before it went quiet
        settled = self.ask()
        self.assertEqual(settled["status"], "delivered")
        self.assertTrue(settled["already"])
        self.assertEqual(len(self.door.done), 1)

    def test_desk_refusal_is_refused_and_kept(self):
        self.door.refuse = True
        got = self.ask()
        self.assertEqual(got["status"], "refused")
        self.assertIn("the desk refused: refused: a10 changed", got["reason"])
        self.door.refuse = False
        self.assertEqual(self.ask()["status"], "refused", "kept: the same request is not sent again")
        self.assertEqual(len(self.door.sends()), 1)

    def test_builder_card_session_refused(self):
        with patch.object(house.Resident, "__init__", initialize):
            w = workshop.Worker(self.h, "card-1", ".", "branch", "jeff")
        w.proc = SimpleNamespace(stdout=(), wait=Mock(return_value=0), pid=2)
        source = w._bind_child(w.proc)
        got = self.route.handle(source, {"action": "artifact-view", "request": "x", "artifact": f"{RUN}/01-map.png",
                                         "sha256": self.sha, "recipient": "rowan", "target": "a10", "prompt": "p"})
        self.assertEqual(got["status"], "refused")
        self.assertEqual(self.door.calls, [])

    def test_unattested_text_is_refused(self):
        text = self.route.intercept(None, '> host-route {"action": "artifact-view"}')
        self.assertIn('"refused"', text.host_receipts[0])
        stale = self.route.sessions[self.r["f1"]]
        self.r["f1"]._bind_child(self.r["f1"].proc)          # a new child: the old session is no longer current
        got = self.route.handle(stale, {"action": "artifact-view", "request": "x", "artifact": f"{RUN}/01-map.png",
                                        "sha256": self.sha, "recipient": "rowan", "target": "a10", "prompt": "p"})
        self.assertIn("current resident turn", got["reason"])
        self.assertEqual(self.door.calls, [])

    def test_resident_not_served_cannot_receive_even_with_world_props(self):
        got = self.ask(recipient="mallory")          # a role=resident surface in the world, but no resident the house serves
        self.assertEqual(got["status"], "refused")
        self.assertIn("this house serves", got["reason"])
        self.assertEqual(self.door.calls, [])

    def test_issuer_cannot_take_another_residents_name(self):
        self.corners["f1"]["props"]["actor"] = "rowan"      # a writable prop says the issuer is rowan
        got = self.ask(recipient="pike")
        self.assertEqual(got["status"], "refused")
        self.assertIn("another corner claims", got["reason"])
        self.assertEqual(self.door.calls, [])

    def test_only_guarded_passed_named_shots(self):
        cases = {"research/map-lab/ground/shots/map-800x600.png": "paths and URLs are refused",
                 f"{RUN}/02-other.png": "passed guarded journey",
                 "https://example.com/x.png": "paths and URLs are refused",
                 f"{RUN}/../../x.png": "paths and URLs are refused"}
        for k, (artifact, why) in enumerate(cases.items()):
            got = self.ask(artifact=artifact, request=f"c{k}", sha256=self.sha)
            self.assertEqual(got["status"], "refused", artifact)
            self.assertIn(why, got["reason"], artifact)
        got = self.ask(request="sha", sha256="0" * 64)
        self.assertIn("SHA256 does not match", got["reason"])
        self.assertEqual(self.door.sends(), [])

    def test_exact_fields(self):
        for k, bad in enumerate(({"request": "b0", "extra": "x"}, {"request": "has space"}, {"request": "b2", "prompt": 3})):
            got = self.ask(**bad)
            self.assertEqual(got["status"], "refused", bad)
        self.assertEqual(self.door.calls, [])

    def test_no_door_nothing_sent_and_not_kept(self):
        self.route.artifact_view.door = artifact_view.door_post      # DESKD=off here
        got = self.ask()
        self.assertEqual(got["status"], "refused")
        self.assertIn("no local desk door", got["reason"])
        self.route.artifact_view.door = self.door
        self.assertEqual(self.ask()["status"], "delivered", "a door that answers later may be asked again")

    def test_other_actions_still_refused(self):
        got = self.route.handle(self.route.sessions[self.r["f1"]], {"action": "grant", "card": "x", "generation": "y"})
        self.assertEqual(got["reason"], "host route disabled pending review")
        self.assertIsNone(ParentDispatcher().artifact_view, "with no house (fake, tests) nothing answers")


if __name__ == "__main__":
    unittest.main(verbosity=1)
