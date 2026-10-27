"""Definition sharing, adverse imports and independence over the real HTTP door."""
import copy
import json
import secrets
import shutil
import sys
import tempfile
import threading
import unittest
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(LAB), str(LAB / "tests"), str(LAB / "proof")]
from kernel.kernel import Kernel
from kernel.door import serve
from test_skeleton import StandInEntry, post
from test_painter import quoted
import kits


class Kits(unittest.TestCase):
    def setUp(self):
        self.resources = []
        self.s, self.surl, self.sg, self.sm = self.world("aa")
        self.t, self.turl, self.tg, self.tm = self.world("bb")

    def world(self, tag):
        folder = tempfile.mkdtemp(prefix="kits-test-")
        entry = StandInEntry(secrets.token_hex(16))
        k = Kernel(folder, {"tag": tag, "name": tag, "steward": {"account": "owner", "name": "Owner"},
            "invites_counted_by": "kernel", "invites": [{"code": "join", "uses": 5}],
            "groups": [{"name": "Workshop", "open": True}, {"name": "Private"}]})
        srv, host = serve(k, entry.url, entry.secret, 0, LAB)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{srv.server_address[1]}"
        entry.kernel_url = url
        entry.sessions["owner"] = {"account": "owner", "method": "google"}
        member, _ = entry.sign_in("member", "Member", invite="join")
        self.resources.append((folder, srv, host, entry))
        return k, url, k.things("group")[0], member

    def tearDown(self):
        for folder, srv, host, entry in self.resources:
            host.stop_all()
            for server in (srv, entry.srv):
                server.shutdown()
                server.server_close()
            shutil.rmtree(folder, ignore_errors=True)

    def line(self, url, line, token="owner", ok=True):
        code, out = post(url + "/do", {"line": line}, token=token)
        self.assertEqual(code, 200, out)
        self.assertEqual(out["ok"], ok, out)
        return out

    def bundle(self):
        self.word = self.line(self.surl, f'verb greet steps="post Hello" help="Say hello" in={self.sg}')["made"][0]
        self.lens = self.line(self.surl, f'make kind=lens name=welcome text="root : text Hello" in={self.sg}')["made"][0]
        kit = self.line(self.surl, f"kit {self.sg}")["made"][0]
        return self.line(self.surl, f"look {kit}")["rows"][0]["bundle"]

    def take(self, bundle, group=None, ok=True, token="owner"):
        before = len(self.t.log.records)
        out = self.line(self.turl, f"take bundle={quoted(json.dumps(bundle))} in={group or self.tg}", token, ok)
        if not ok:
            self.assertEqual(len(self.t.log.records), before)
        return out

    def replay(self, k):
        self.assertEqual(Kernel(k.dir).state.snapshot(), k.state.snapshot())

    def test_take_is_atomic_independent_undoable_and_remembers_origin(self):
        b = self.bundle()
        snapshot = self.s.state.snapshot()
        r = self.take(b)
        self.assertEqual(len(r["records"]), 1)
        for t, d in zip(r["made"], b["definitions"]):
            self.assertEqual(self.t.state.get(t, "origin"), {"world": b["source"], "thing": d["id"]})
        word = self.t.find_entry("greet", self.tg)
        self.line(self.turl, f"look {word}")
        self.line(self.turl, f'rename {word} word=hello aliases="hola saludar" in={self.tg}')
        self.line(self.turl, f"hola in={self.tg}")
        self.assertEqual(self.s.state.snapshot(), snapshot)
        self.line(self.turl, "undo")  # post from hola
        self.line(self.turl, "undo " + r["records"][0], ok=False)  # rename still depends on imported word
        self.replay(self.s)
        self.replay(self.t)

    def test_take_can_be_undone_as_one_act_and_local_kit_can_be_taken(self):
        self.bundle()
        kit = self.s.things("kit")[0]
        private = self.s.things("group")[1]
        result = self.line(self.surl, f"take {kit} in={private}")
        self.line(self.surl, "undo " + result["records"][0])
        self.assertTrue(all(not self.s.state.things[t] for t in result["made"]))
        self.replay(self.s)

    def test_no_live_data_or_authority_is_gathered(self):
        for text in ('make kind=poll options="yes no"', 'make kind=item seats=2',
                     'post Private discussion', 'make kind=research text=555-1234'):
            self.line(self.surl, text + f" in={self.sg}")
        item = self.s.things("item")[0]
        self.line(self.surl, f"claim {item} phone=555-1234")
        poll = self.s.things("poll")[0]
        self.line(self.surl, f"vote {poll} yes")
        b = self.bundle()
        encoded = json.dumps(b)
        for forbidden in ("555-1234", "Private discussion", "claim:", "vote:", "member:", "run", "grants"):
            self.assertNotIn(forbidden, encoded)
        self.take(b)
        for kind in ("post", "poll", "item", "research", "module", "grant"):
            self.assertFalse(self.t.things(kind))

    def test_import_refuses_forged_data_kinds_authority_and_implementation(self):
        b = self.bundle()
        variants = []
        for key, value in (("kind", "person"), ("contact:aa2", "555-1234"), ("made_by", "aa2"),
                           ("run", ["bad"]), ("from", "kernel"), ("origin", {"world": "forged"})):
            bad = copy.deepcopy(b)
            word = next(d for d in bad["definitions"] if d["facts"]["kind"] == "word")
            word["facts"][key] = value
            variants.append(bad)
        variants += [None, [], {}, {**b, "version": 2}, {**b, "definitions": "not a list"},
                     {**b, "source": "not an origin digest"},
                     {**b, "definitions": [{"id": "aa500", "facts": {"kind": []}}]}]
        for bad in variants:
            with self.subTest(bundle=bad):
                self.take(bad, ok=False)

    def test_data_references_are_refused_and_internal_definition_references_remap(self):
        b = self.bundle()
        for d in b["definitions"]:
            if d["facts"]["kind"] == "word":
                d["facts"]["steps"] = f"look {self.lens}"
        out = self.take(b)
        copied_lens = next(t for t in out["made"] if self.t.state.get(t, "kind") == "lens")
        word = self.t.find_entry("greet", self.tg)
        self.assertEqual(self.t.state.get(word, "steps"), f"look {copied_lens}")
        bad = copy.deepcopy(b)
        bad["definitions"][0]["facts"]["help" if bad["definitions"][0]["facts"]["kind"] == "word" else "text"] = "look aa9999"
        self.take(bad, ok=False)
        post_id = self.line(self.surl, "post personal information")["made"][0]
        self.line(self.surl, f'verb leak steps="look {post_id}" help="Reads live data" in={self.sg}')
        before = len(self.s.log.records)
        self.line(self.surl, f"kit {self.sg}", ok=False)
        self.assertEqual(len(self.s.log.records), before)

    def test_permissions_collisions_and_origin_are_protected(self):
        b = self.bundle()
        self.take(b, token=self.tm, ok=False)
        self.line(self.surl, f"kit {self.sg}", token=self.sm, ok=False)
        out = self.take(b)
        self.take(b, ok=False)
        word = self.t.find_entry("greet", self.tg)
        self.line(self.turl, f"look {word}")
        self.line(self.turl, f'rename {word} aliases=look in={self.tg}', ok=False)
        self.line(self.turl, f'rename {word} word=stolen in={self.tg}', token=self.tm, ok=False)
        self.line(self.turl, f'set {out["made"][0]} origin=forged', ok=False)
        self.replay(self.t)

    def test_module_entries_have_help_and_stay_unbound_without_installation(self):
        b = self.bundle()
        b["definitions"] = [{"id": "aa500", "facts": {"kind": "word", "word": "adapter.read",
            "bound": "adapter.read", "word_kind": "see", "help": "Read from the local adapter",
            "from": "module:adapter", "may": "anyone"}}]
        self.take(b)
        help_ = self.line(self.turl, f"help adapter.read in={self.tg}")
        self.assertIn("unbound", help_["text"])
        self.line(self.turl, f"adapter.read in={self.tg}", ok=False)
        self.assertFalse(self.t.things("module"))

    def test_kernel_entry_references_rebind_to_destination_dictionary(self):
        b = self.bundle()
        look = self.s.find_entry("look")
        b["kernel"] = {look: "look"}
        for d in b["definitions"]:
            if d["facts"]["kind"] == "word":
                d["facts"]["steps"] = f"look {look}"
        self.take(b)
        word = self.t.find_entry("greet", self.tg)
        self.assertEqual(self.t.state.get(word, "steps"), f"look {self.t.find_entry('look')}")
        self.line(self.turl, f"greet in={self.tg}")
        self.replay(self.t)


@unittest.skipUnless(shutil.which("node"), "agenda needs Node")
class KitsProof(unittest.TestCase):
    def test_two_communities_over_http(self):
        with tempfile.TemporaryDirectory(prefix="kits-evidence-") as folder:
            evidence = kits.run(Path(folder))
            self.assertEqual(evidence["passed"], evidence["of"])
            self.assertTrue(evidence["complete"])


if __name__ == "__main__":
    unittest.main()
