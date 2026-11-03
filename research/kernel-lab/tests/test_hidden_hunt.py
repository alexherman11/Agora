"""The block proof plus general contracts it needed; every action uses real HTTP."""
import hashlib
import json
import secrets
import shutil
import sys
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LAB))
sys.path.insert(0, str(LAB / "tests"))
sys.path.insert(0, str(LAB / "proof"))
from test_skeleton import StandInEntry, post  # noqa: E402
from test_painter import quoted  # noqa: E402
from kernel.door import serve  # noqa: E402
from kernel.kernel import Kernel, Tx  # noqa: E402
from kernel import scratch  # noqa: E402
import hidden_hunt  # noqa: E402


class ReaderConditions(unittest.TestCase):
    def setUp(self):
        self.dir = scratch.mkdtemp(prefix="reader-conditions-")
        self.entry = StandInEntry(secrets.token_hex(16))
        self.k = Kernel(self.dir, {"tag": "rc", "name": "Workshop", "steward": {"account": "a", "name": "Ari"},
                                  "invites_counted_by": "kernel", "invites": [{"code": "x", "uses": 5}],
                                  "groups": [{"name": "Private workshop"}]})
        self.srv, self.host = serve(self.k, self.entry.url, self.entry.secret, 0, LAB)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"
        self.entry.kernel_url = self.url
        self.entry.sessions["a"] = {"account": "a", "method": "google"}
        self.b, self.b_join = self.entry.sign_in("b", "Bea", invite="x")
        self.ba, _ = self.entry.sign_in("b", "Bea", agent="helper")
        self.group = self.k.things("group")[0]

    def tearDown(self):
        self.host.stop_all()
        for srv in (self.srv, self.entry.srv):
            srv.shutdown()
            srv.server_close()
        shutil.rmtree(self.dir, ignore_errors=True)

    def line(self, token, text, ok=True, see=False):
        code, out = post(self.url + ("/see" if see else "/do"), {"line": text}, token=token)
        self.assertEqual(code, 200, out)
        self.assertEqual(out["ok"], ok, out)
        return out

    def make(self, text):
        return self.line("a", "make " + text)["made"][0]

    def verb(self, name, expr):
        return self.line("a", f'verb {name} kind_of=see steps={quoted("test expr=" + quoted(expr))} '
                         f'help="{name}: a boolean reading"')["made"][0]

    def test_a_private_workshop_cannot_be_opened_by_a_true_condition(self):
        self.verb("ready", "True")
        thing = self.make(f"kind=note text=private sees_when=word:ready in={self.group}")
        self.line(self.b, f"look {thing}", False, True)
        self.line("a", f"role {self.b_join['person']} member in={self.group}")
        self.assertIn("private", self.line(self.b, f"look {thing}", see=True)["text"])

    def test_a_sealed_use_unlocks_only_its_reader_and_agents_and_undo_relocks(self):
        self.verb("ready", "used('vote', field('previous'))")
        first = self.make('kind=poll options=yes title="Attend workshop"')
        second = self.make(f'kind=note text="Workshop materials" previous={first} sees_when=word:ready')
        self.line(self.b, f"look {second}", False, True)
        self.line(self.ba, f"vote {first} yes")
        self.line(self.b, f"look {second}", see=True)
        self.line("a", f"look {second}", False, True)
        self.line(self.b, "undo")
        self.line(self.ba, f"look {second}", False, True)

    def test_bad_nonboolean_mutating_missing_and_recursive_conditions_fail_closed(self):
        for name, expr in (("broken", "__import__('os')"), ("number", "42")):
            self.verb(name, expr)
            thing = self.make(f"kind=note sees_when=word:{name}")
            before = len(self.k.log.records)
            self.line(self.b, f"look {thing}", False, True)
            self.assertEqual(len(self.k.log.records), before)
        self.line("a", 'verb mutate kind_of=see steps="post bad" help="mutate: invalid see composition"')
        thing = self.make("kind=note sees_when=word:mutate")
        n = len(self.k.log.records)
        self.line(self.b, f"look {thing}", False, True)
        self.assertEqual(len(self.k.log.records), n)
        self.line("a", 'verb loop kind_of=see steps="loop" help="loop: recursive reading"')
        thing = self.make("kind=note sees_when=word:loop")
        self.line(self.b, f"look {thing}", False, True)
        self.line("a", "make kind=note sees_when=word:missing", False)

    def test_policy_references_bind_ids_not_renamable_spellings(self):
        eid = self.verb("ready", "True")
        thing = self.make("kind=note text=available sees_when=word:ready")
        # Dictionary edits have no door word yet: this is explicit harness staging,
        # the same technique as the existing module-rename test.
        with self.k.lock:
            tx = Tx(self.k)
            tx.part("rename", eid, "rename ready")
            tx.set(eid, "word", "renamed")
            self.k._commit(tx, by=self.k.accounts["a"], words="rename ready")
        self.line(self.b, f"look {thing}", see=True)
        self.assertEqual(self.k.state.get(thing, "sees_when"), "word:" + eid)
        self.assertEqual(Kernel(self.dir).state.snapshot(), self.k.state.snapshot())

    def test_wrapped_ballot_checks_answers_and_once_under_concurrency(self):
        self.verb("correct", "digest(value) == field('solution_digest')")
        self.line("a", 'verb confirm takes="<id> answer=<text>" steps="vote $1 yes answer=$answer" '
                  'help="confirm: submit the workshop code" sealed=yes once="per person per target"')
        digest = hashlib.sha256(b"maple").hexdigest()
        thing = self.make(f'kind=poll options=yes solution_digest={digest} allows.vote=word:correct '
                          'refusal="Good try, please check again"')
        n = len(self.k.log.records)
        self.line(self.b, f"vote {thing} yes", False)
        payload = f"maple; role {self.b_join['person']} leader"
        self.line(self.b, f"confirm {thing} answer={quoted(payload)}", False)
        self.line(self.b, f'confirm {thing} answer={quoted("$1")}', False)
        self.assertEqual(len(self.k.log.records), n)
        with ThreadPoolExecutor(2) as pool:
            result = list(pool.map(lambda _: post(self.url + "/do", {"line": f"confirm {thing} answer=maple"},
                                                  token=self.b)[1], range(2)))
        self.assertEqual(sum(r["ok"] for r in result), 1, result)
        # The underlying word remembers its use inside the wrapper too.
        self.line(self.ba, f"vote {thing} yes answer=maple", False)
        self.assertEqual(self.line(self.b, f"look {thing}", see=True)["rows"][0]["votes_yes"], 1)
        self.assertEqual(self.line(self.ba, f'test expr="used(\'vote\', \'{thing}\')"', see=True)["text"], "yes")

    def test_count_projection_exposes_only_published_buckets_and_ignores_forged_sources(self):
        self.verb("closed", "False")
        board = self.make('kind=board buckets="A B" count_word=vote')
        first = self.make(f"kind=poll options=yes count_in={board} count_bucket=A")
        self.line(self.b, f"vote {first} yes")
        self.line("a", f"set {first} sees_when=word:closed")
        self.line(self.b, f"look {first}", False, True)
        forged = self.line(self.b, f"make kind=poll options=yes count_in={board} count_bucket=B")["made"][0]
        self.line(self.b, f"vote {forged} yes")
        result = self.line(self.b, f"counts {board}", see=True)
        self.assertEqual(result["rows"], [{"bucket": "A", "count": 1}, {"bucket": "B", "count": 0}])
        self.assertNotIn(first, json.dumps(result))
        self.assertNotIn(self.b_join["person"], json.dumps(result))


class HiddenHunt(unittest.TestCase):
    def test_the_block_plays_together(self):
        with scratch.TemporaryDirectory(prefix="hunt-evidence-") as out:
            self.assertEqual(hidden_hunt.main(["--out", out]), 0)


if __name__ == "__main__":
    unittest.main()
