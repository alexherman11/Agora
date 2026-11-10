# health: room test
"""Disposable in-memory source passages; no live world, clipboard or Conversation."""
import copy
import re
import unittest
from unittest.mock import patch

import explore
import lens_ir
import scene
from selection_snapshot import capture
from world import Refusal


class PassageTests(unittest.TestCase):
    def setUp(self):
        self.d = explore.fresh()
        self.d._session = "selection-fixture"
        self.w = self.d.world
        self.w.me = "alex"
        self.line("look")
        self.item = self.make('kind=note title="Fixture source" text="same 😀 same **bold** end"')
        self.sid = self.w.nodes[self.item]["subject"]

    def line(self, line):
        result = self.d.dispatch("desk", {"line": line, "whole": True})
        self.assertFalse(result.get("error"), result)
        text = result.get("text", "")
        self.assertFalse(re.search(r"(^|\n)(ERR|!!)", text), text)
        return text

    def make(self, body):
        self.line(f"look {self.w.root}")
        return re.search(r"created ([af]\d+)", self.line(f"do create {self.w.root} {body}"))[1]

    def packet(self):
        return dict(item=self.sid, rev=self.w.subjects[self.sid]["rev"], field="text",
                    start=8, end=12, quote="same", context={})

    def test_repeated_utf16_and_no_mutation(self):
        before = copy.deepcopy(self.w.__dict__)
        got = capture(self.d, self.packet())
        self.assertEqual((got["start"], got["end"], got["quote"]), (8, 12, "same"))
        self.assertEqual(got["before"], "same 😀")
        self.assertEqual(got["after"], "**bold** end")
        self.assertEqual(before, self.w.__dict__)

    def test_source_title_context_and_refusals(self):
        p = self.packet()
        p["context"] = {"item": {"item": self.item, "rev": self.w.nodes[self.item]["rev"]}}
        self.assertEqual(capture(self.d, p)["context"], p["context"])
        for change in [dict(rev=-1), dict(quote="bold"), dict(start=True), dict(start=6, end=7, quote="x"),
                       dict(field="password"), dict(item="s999999"), dict(context={"about": {}})]:
            with self.subTest(change=change), self.assertRaises(Refusal):
                capture(self.d, {**p, **change})
        with patch.object(lens_ir, "may_read", return_value="private"), self.assertRaises(Refusal):
            capture(self.d, p)
        title = dict(item=self.sid, rev=p["rev"], field="title", start=0, end=7, quote="Fixture")
        self.assertEqual(capture(self.d, title)["quote"], "Fixture")
        self.line(f"read {self.item}")
        self.line(f'do rewrite {self.item} text="changed"')
        with self.assertRaises(Refusal):
            capture(self.d, p)

    def test_prepare_compiles_and_direct_source_only(self):
        src = 'root : column\n  words : text $text\n    on menu "Comment" prepare root/say\n  label : text "Generated $title"\n  say : text ""\n    on edit do rewrite $item text="$value"\n    on edit quoted do rewrite $item text="$value $quote_text"\n    commit explicit'
        lens = self.make('kind=note title=selection-fixture tags=lens text="' +
                         src.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"')
        self.line(f"read {lens}")
        result = self.line(f"scene selection-fixture on {self.item}")
        self.assertIn("prepare root/say", result)
        s = self.w.subjects[self.w.nodes[lens]["subject"]]
        sc = lens_ir.compile_lens(self.d, s, [], [0], [], on=self.item)
        def walk(n):
            yield n
            for k in n.get("kids", []):
                yield from walk(k)
        nodes = list(walk(sc))
        direct = [n for n in nodes if n.get("text") == "same 😀 same **bold** end"]
        self.assertTrue(direct)
        self.assertEqual(direct[0]["source"]["item"], self.sid)
        generated = [n for n in nodes if str(n.get("text", "")).startswith("Generated")]
        self.assertNotIn("source", generated[0])
        say = next(n for n in nodes if any(a["on"] == "edit-quoted" for a in n.get("acts", [])))
        self.assertEqual([a["on"] for a in say["acts"]], ["edit", "edit-quoted"])
        self.assertIn("$quote_text", say["acts"][1]["line"])
        for bad in [
            src.replace("commit explicit", "commit enter"),
            src.replace('    on edit do rewrite $item text="$value"\n', ""),
            src.replace('on edit do rewrite $item text="$value"', 'on edit do rewrite $item text="$quote_text"'),
            src.replace('on edit quoted do rewrite $item text="$value $quote_text"', 'on edit quoted do rewrite $item text="$value"'),
        ]:
            with self.subTest(bad=bad), self.assertRaises(scene.LensRefusal):
                scene.parse(bad)

    def compiled_actions(self, actions):
        src = 'root : text ""\n  commit explicit\n' + "\n".join("  " + a for a in actions)
        lens = self.make('kind=note title=paired-fixture tags=lens text="' +
                         src.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"')
        s = self.w.subjects[self.w.nodes[lens]["subject"]]
        return lens_ir.compile_lens(self.d, s, [], [0], [], on=self.item)["acts"]

    def test_guarded_routes_and_full_batches(self):
        quoted = 'on edit quoted when $mode = "one" do rewrite $item text="$value $quote_text"; read $item; do prop $item quoted=yes'
        plain = ['on edit when $mode = "' + mode + '" do rewrite $item text="$value"; read $item; do prop $item route=' + mode
                 for mode in ("one", "two", "three", "four")]
        for mode in ("one", "two", "three", "four"):
            self.line(f"read {self.item}")
            self.line(f"do prop {self.item} mode={mode}")
            acts = self.compiled_actions(plain + [quoted])
            self.assertEqual(sum(a["on"] == "edit" for a in acts), 1)
            self.assertEqual(sum(a["on"] == "edit-quoted" for a in acts), mode == "one")
            self.assertTrue(acts[0]["line"].endswith("route=" + mode))
            self.assertEqual(len(scene.split_batch(acts[0]["line"])), 3)
        for actions in (plain + [plain[-1], quoted], [plain[0], quoted],
                        plain + [quoted.replace('$mode = "one"', '$mode = "four"')] * 2):
            with self.subTest(actions=actions), self.assertRaises(scene.LensRefusal):
                self.compiled_actions(actions)

    def test_native_batch_partial_failure_is_not_atomic(self):
        # Existing dispatcher stops later commands on this path. Preserve and
        # report it; branching must not imply rollback or cleanup recovery.
        chat = self.make('kind=chat title="Disposable batch"')
        result = self.d.dispatch("desk", {"line":
            f'read {chat}; do append {chat} line="kept"; do prop a999999 topic=""; '
            f'read {self.item}; do prop {self.item} continued=yes', "whole": False})
        self.assertIn("ERR", result.get("text", ""))
        self.assertIn("later command(s) not run", result.get("text", ""))
        self.assertNotIn("continued=yes", self.line(f"read {self.item}"))
        self.assertIn("kept", self.line(f"read {chat}"))


if __name__ == "__main__":
    unittest.main()
