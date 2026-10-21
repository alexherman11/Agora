# health: room test
"""In-memory actual chat lens/compiler/dispatch coverage; no session files or real sends."""
import importlib.util
import json
from pathlib import Path
import re
import unittest
from unittest.mock import patch

import explore
import lens_ir
import scene

STAGE = Path(__file__).parents[2] / "window-lab" / "chat-markdown" / "slice1"
spec = importlib.util.spec_from_file_location("chat_md_stage", STAGE / "stage.py")
stage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stage)
ORIGINAL = json.loads((STAGE / "originals.json").read_text(encoding="utf-8"))


def walk(n):
    yield n
    for c in n.get("kids", []):
        yield from walk(c)


def quote(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("$", "\\$") + '"'


class ChatMarkdown(unittest.TestCase):
    def setUp(self):
        self.d = explore.fresh()
        self.d.world.me = "alex"
        self.do("look")
        self.chat = self.create('kind=chat title="Disposable fixture feed" with="alex,jeff"')
        self.draft = self.create('kind=note title="Fixture draft" role=conversation-draft actor=alex to=jeff view=all topic="Chosen item"')
        self.plan = self.create('kind=note title="Chosen item" text="Fixture document"')
        roles = sorted(set(re.findall(r"^\s+role ([\w.-]+)", "\n".join(ORIGINAL.values()), re.M)) | {"page"})
        self.create('kind=note title="fixture-style" tags=style text='
                    + quote("token ink = #123456\n" + "\n".join(f"role {r} : ink" for r in roles)))
        self.create('kind=note title="home-usage" tags=lens text=' + quote('x : text ""'))
        self.do(f"read {self.chat}")

    def do(self, line):
        r = self.d.dispatch("desk", {"line": line})
        if r.get("error"):
            raise AssertionError(r)
        return r

    def create(self, args):
        r = self.do(f"do create {self.d.world.root} {args}")
        match = re.search(r"created (a\d+)", r.get("text", ""))
        assert match, r
        return match.group(1)

    def render(self, item, patched=True):
        src = (stage.prepare(ORIGINAL) if patched else ORIGINAL)[item].replace("a5080", self.chat)
        # The production roles and media policy are separate; no files are read here.
        with patch.object(scene, "media_of", lambda t: [
            {"path": "media/film.mp4", "src": "/media/film.mp4", "kind": "video", "name": "Film"}
        ] if "media/film.mp4" in t else []):
            tree = lens_ir.evaluate(self.d, src, props={"style": "fixture-style"})
            scene.emit(tree)
            return scene.painter_view(tree)

    def incoming(self, text, **fields):
        self.d.world.me = "jeff"
        self.do(f"read {self.chat}")
        self.do(f"do append {self.chat} line={quote(text)} to=alex "
                + " ".join(f"{k}={quote(v)}" for k, v in fields.items()))
        self.d.world.me = "alex"
        self.do(f"read {self.chat}")

    def test_exact_patch_roundtrip_and_drift_atomicity(self):
        self.assertEqual(stage.prepare(stage.prepare(ORIGINAL), reverse=True), ORIGINAL)
        drift = {**ORIGINAL, "a5086": ORIGINAL["a5086"].replace("    marks", "    plain")}
        before = dict(drift)
        with self.assertRaises(ValueError):
            stage.prepare(drift)
        self.assertEqual(drift, before)

    def test_both_actual_message_bodies_compose_media_and_keep_composer_and_reply_contract(self):
        text = f"# Header\n| Doc | Value |\n| --- | --- |\n| {self.plan} | **yes** |\nmedia/film.mp4"
        self.incoming(text, about=self.plan)
        for item in ORIGINAL:
            before = self.render(item, False)
            after = self.render(item)
            bodies = [n for n in walk(after) if (n.get("paint") or {}).get("text") == text]
            self.assertEqual(len(bodies), 1, item)
            body = bodies[0]
            self.assertTrue(body["paint"]["markdown"])
            self.assertEqual(body["paint"]["media"]["items"][0]["path"], "media/film.mp4")
            self.assertIn(self.plan, body["paint"]["things"])
            self.assertNotIn("runs", body["paint"])
            self.assertFalse(any(a["on"] == "edit" for a in body["acts"]))
            self.assertTrue(any(a["on"] == "pop" for a in body["acts"]))
            self.assertTrue(any(a["on"] == "link" and a["line"].startswith("do view ") for a in body["acts"]))
            contracts = lambda tree: {n["key"]: n["acts"] for n in walk(tree)
                                      if any(a["on"] in ("edit", "click") for a in n.get("acts", []))}
            self.assertEqual(contracts(before), contracts(after), item)
            # Arrival and repaint cannot mutate the chosen topic or any world draft field.
            state = dict(self.d.world.subjects[self.d.world.nodes[self.draft]["subject"]]["props"])
            self.incoming("Incoming **update**")
            self.render(item)
            self.assertEqual(self.d.world.subjects[self.d.world.nodes[self.draft]["subject"]]["props"], state)

    def test_original_place_reply_dispatches_to_fixture_feed(self):
        self.incoming("Original line")
        tree = self.render("a5086")
        reply = next(n for n in walk(tree) if any(a["on"] == "edit" and "reply_to=" in a["line"]
                                                  and self.chat in a["line"] for a in n.get("acts", [])))
        action = next(a for a in reply["acts"] if a["on"] == "edit")
        self.do(action["line"].replace("$value", "Reply on original fixture"))
        read = self.do(f"read {self.chat}")["text"]
        self.assertIn("Reply on original fixture", read)
        self.assertIn("reply_to=", action["line"])


if __name__ == "__main__":
    unittest.main()
