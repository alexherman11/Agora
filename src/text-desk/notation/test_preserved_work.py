# health: room test
"""Real isolated Git repositories; no live worktrees, workers, or host actions."""
import hashlib
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "desktop"))
import agora_tmp
import landing
import preserved_work as pw
import workshop
from fixture_cleanup import remove_tree


class Handoffs(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(agora_tmp.directory("bring-"))
        self.addCleanup(self.clean_fixture)
        self.live, self.trees = self.tmp / "live", self.tmp / "trees"
        self.live.mkdir()
        self.trees.mkdir()
        self.state = self.tmp / "state"
        self.state.mkdir()
        env = dict(GIT_AUTHOR_NAME="fixture", GIT_COMMITTER_NAME="fixture",
                   GIT_AUTHOR_EMAIL="fixture@example.invalid", GIT_COMMITTER_EMAIL="fixture@example.invalid")
        self.patches = [patch.dict(os.environ, env), patch.object(landing, "LIVE", self.live),
                        patch.object(landing, "STATE", self.state), patch.object(workshop, "REPO", self.live),
                        patch.object(workshop, "TREES", self.trees)]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)
        pw.git(self.live, "init", "-b", "main")
        pw.git(self.live, "config", "core.autocrlf", "false")
        self.put(self.live, ".gitignore", "src/text-desk/notation/sessions/\nignored/\n")
        self.put(self.live, "research/pkg/existing.txt", "base\n")
        self.commit(self.live)
        self.base = pw.head(self.live)
        self.source, self.dest = self.trees / "a1", self.trees / "a2"
        for card, path in [("a1", self.source), ("a2", self.dest)]:
            pw.git(self.live, "worktree", "add", "-b", f"worker/{card}", str(path), "HEAD")
        self.receipt = self.state / "receipt.json"

    def clean_fixture(self):
        self.assertEqual(remove_tree(self.tmp, readonly=True), [],
                         "private preserved-work fixture must be removed")

    def put(self, root, name, text):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode() if isinstance(text, str) else text)

    def commit(self, root):
        pw.git(root, "add", "-A")
        pw.git(root, "commit", "-m", "fixture")

    def run_transfer(self, source="a1", paths=None):
        return pw.transfer(landing, self.live if source == "main" else self.source,
                           self.dest, source, "a2", paths or ["research/pkg/"],
                           self.receipt, "fixture-key")

    def test_worker_package_hashes_scope_and_retry(self):
        self.put(self.source, "research/pkg/new.bin", b"\0exact\r\nbytes")
        self.put(self.source, "unrelated.txt", "held deployment\n")
        self.commit(self.source)
        self.put(self.source, "research/pkg/existing.txt", "preserved\n")
        self.put(self.source, "uncommitted.txt", "also untouched")
        data = self.run_transfer()
        self.assertEqual(data["phase"], "applied")
        self.assertEqual((self.dest / "research/pkg/new.bin").read_bytes(), b"\0exact\r\nbytes")
        self.assertFalse((self.dest / "unrelated.txt").exists())
        self.assertFalse((self.dest / "uncommitted.txt").exists())
        self.assertEqual((self.source / "uncommitted.txt").read_text(), "also untouched")
        raw = hashlib.sha256(b"\0exact\r\nbytes").hexdigest()
        self.assertEqual(data["files"]["research/pkg/new.bin"]["sha256"], raw)
        self.assertEqual(data["committed_files"], data["received_files"])
        old = pw.head(self.dest)
        self.assertEqual(self.run_transfer()["recipient_after"], old)
        self.assertEqual(pw.head(self.live), self.base)

    def test_main_inputs_reuse_hand_without_landing_or_index_changes(self):
        self.put(self.live, "research/pkg/browser.md", "exact takeover\n")
        self.put(self.live, "unrelated.txt", "author keeps this")
        pw.git(self.live, "add", "unrelated.txt")
        index = pw.git(self.live, "diff", "--cached").stdout
        with patch.object(landing, "hand", wraps=landing.hand) as hand:
            data = self.run_transfer("main", ["research/pkg/browser.md"])
        hand.assert_called_once()
        self.assertEqual((self.dest / "research/pkg/browser.md").read_text(), "exact takeover\n")
        self.assertEqual(pw.head(self.live), self.base)
        self.assertEqual(pw.git(self.live, "diff", "--cached").stdout, index)
        self.assertTrue((self.live / "research/pkg/browser.md").exists())
        self.assertTrue(data["source_branch"].startswith("hand/"))
        self.assertFalse((self.dest / "unrelated.txt").exists())

    def test_conflict_keeps_source_commit_and_receiver_exact(self):
        self.put(self.source, "research/pkg/existing.txt", "source\n")
        self.put(self.dest, "research/pkg/existing.txt", "receiver\n")
        self.commit(self.dest)
        before = pw.head(self.dest)
        with self.assertRaisesRegex(pw.Held, "conflict"):
            self.run_transfer()
        self.assertEqual(pw.head(self.dest), before)
        self.assertEqual((self.dest / "research/pkg/existing.txt").read_text(), "receiver\n")
        self.assertEqual(pw.git(self.dest, "status", "--porcelain").stdout, b"")
        self.assertEqual(pw.out(self.source, "show", "HEAD:research/pkg/existing.txt"), "source")
        self.assertEqual(json.loads(self.receipt.read_text())["phase"], "conflict")

    def test_dirty_receiver_conflict_is_checkpointed_without_losing_either_side(self):
        self.put(self.source, "research/pkg/new.txt", "source")
        self.put(self.dest, "research/pkg/new.txt", "my untracked work")
        with self.assertRaisesRegex(pw.Held, "conflict"):
            self.run_transfer()
        self.assertEqual((self.dest / "research/pkg/new.txt").read_text(), "my untracked work")
        data = pw.read_receipt(self.receipt)
        self.assertEqual(data["phase"], "conflict")
        self.assertEqual(pw.head(self.dest), data["receiver_checkpoint"]["after"])
        self.assertEqual(pw.out(self.dest, "show", "HEAD:research/pkg/new.txt"), "my untracked work")
        self.assertEqual(pw.out(self.source, "show", "HEAD:research/pkg/new.txt"), "source")
        self.assertEqual(pw.git(self.dest, "status", "--porcelain").stdout, b"")
        again = pw.head(self.dest)
        with self.assertRaisesRegex(pw.Held, "conflict"):
            self.run_transfer()
        self.assertEqual(pw.head(self.dest), again)

    # a10253: a conflict staged beside the receiver's files, for a hand merge
    def beside_fixture(self):
        self.put(self.source, "research/pkg/existing.txt", "source\n")       # both changed: a real conflict
        self.put(self.source, "research/pkg/new.txt", "only the source has me\n")
        self.put(self.dest, "research/pkg/existing.txt", "receiver painter change\n")
        self.commit(self.dest)
        return pw.head(self.dest)

    def run_beside(self, name="r1"):
        return pw.transfer(landing, self.source, self.dest, "a1", "a2", ["research/pkg/"], self.receipt,
                           "fixture-key", conflict="beside", stage_name=name)

    def test_conflict_beside_stages_incoming_and_base_and_leaves_receiver_files(self):
        before = self.beside_fixture()
        data = self.run_beside()
        self.assertEqual((data["phase"], data["mode"], data["stage"]), ("applied", "beside", ".incoming/r1"))
        d = self.dest
        self.assertEqual((d / "research/pkg/existing.txt").read_text(), "receiver painter change\n")
        self.assertFalse((d / "research/pkg/new.txt").exists())
        self.assertEqual((d / ".incoming/r1/incoming/research/pkg/existing.txt").read_text(), "source\n")
        self.assertEqual((d / ".incoming/r1/base/research/pkg/existing.txt").read_text(), "base\n")
        self.assertEqual((d / ".incoming/r1/incoming/research/pkg/new.txt").read_text(), "only the source has me\n")
        self.assertFalse((d / ".incoming/r1/base/research/pkg/new.txt").exists())
        inv = json.loads((d / ".incoming/r1/INVENTORY.json").read_text())
        self.assertEqual({k: v["status"] for k, v in inv["files"].items()},
                         {"research/pkg/existing.txt": "both-changed", "research/pkg/new.txt": "incoming-only"})
        row = inv["files"]["research/pkg/existing.txt"]
        for side, text in (("base", "base\n"), ("incoming", "source\n"), ("current", "receiver painter change\n")):
            self.assertEqual(row[side]["sha256"], hashlib.sha256(text.encode()).hexdigest(), side)
        self.assertEqual(inv["files"], data["inventory"])
        # one new commit on the receiver's HEAD that only adds .incoming/; the tree is clean
        self.assertEqual(pw.out(d, "rev-parse", "HEAD^"), before)
        self.assertEqual(pw.git(d, "rev-parse", "-q", "--verify", "HEAD^2", check=False).returncode, 1)
        changed = pw.out(d, "diff", "--name-only", before, "HEAD").splitlines()
        self.assertTrue(changed and all(p.startswith(".incoming/r1/") for p in changed), changed)
        self.assertEqual(pw.git(d, "status", "--porcelain").stdout, b"")
        # the source's change is not recorded as merged, so a later ordinary merge still sees it
        self.assertNotEqual(pw.git(d, "merge-base", "--is-ancestor", data["projection"], "HEAD",
                                   check=False).returncode, 0)
        self.assertEqual(sorted(data["received_files"]), sorted(data["staged"]))
        # the receiver's own files, byte for byte, before and after staging (Rowan c10297)
        own = data["receiver_own_files"]
        self.assertEqual(own, data["receiver_own_files_after"])
        self.assertEqual(list(own), ["research/pkg/existing.txt"])
        self.assertEqual(own["research/pkg/existing.txt"]["sha256"],
                         hashlib.sha256((d / "research/pkg/existing.txt").read_bytes()).hexdigest())
        # retry is idempotent: no second staging commit
        self.assertEqual(self.run_beside()["recipient_after"], data["recipient_after"])
        self.assertEqual(pw.head(d), data["recipient_after"])

    def test_beside_after_hand_merge_and_removal_stays_reconciled(self):
        self.beside_fixture()
        data = self.run_beside()
        self.put(self.dest, "research/pkg/existing.txt", "receiver painter change\nsource\n")
        pw.git(self.dest, "rm", "-r", "-q", ".incoming")
        self.commit(self.dest)
        self.assertEqual(self.run_beside()["recipient_after"], data["recipient_after"])
        files = pw.out(self.dest, "diff", "--name-only", data["recipient_after"] + "^", "HEAD").splitlines()
        self.assertEqual(files, ["research/pkg/existing.txt"])        # .incoming came and went: nothing to land
        # the staged commit stays reachable: its inventory and versions remain in the branch's history
        self.assertEqual(pw.git(self.dest, "merge-base", "--is-ancestor", data["recipient_after"], "HEAD",
                                check=False).returncode, 0)
        kept = json.loads(pw.out(self.dest, "show", data["recipient_after"] + ":.incoming/r1/INVENTORY.json"))
        self.assertEqual(kept["files"], data["inventory"])

    def test_beside_dirty_receiver_is_checkpointed_first(self):
        self.beside_fixture()
        self.put(self.dest, "research/pkg/existing.txt", "uncommitted receiver work\n")
        data = self.run_beside()
        self.assertEqual((self.dest / "research/pkg/existing.txt").read_text(), "uncommitted receiver work\n")
        self.assertEqual(data["inventory"]["research/pkg/existing.txt"]["current"]["sha256"],
                         hashlib.sha256(b"uncommitted receiver work\n").hexdigest())
        self.assertEqual(pw.git(self.dest, "status", "--porcelain").stdout, b"")

    def test_beside_without_conflict_merges_as_before(self):
        self.put(self.source, "research/pkg/new.txt", "clean\n")
        data = self.run_beside()
        self.assertNotIn("mode", data)
        self.assertEqual((self.dest / "research/pkg/new.txt").read_text(), "clean\n")
        self.assertFalse((self.dest / ".incoming").exists())

    def test_beside_refuses_an_occupied_stage_and_changes_nothing(self):
        self.beside_fixture()
        self.put(self.dest, ".incoming/r1/INVENTORY.json", "{}")
        self.commit(self.dest)
        before = pw.head(self.dest)
        with self.assertRaisesRegex(pw.Held, "already holds"):
            self.run_beside()
        self.assertEqual(pw.head(self.dest), before)
        self.assertEqual((self.dest / "research/pkg/existing.txt").read_text(), "receiver painter change\n")

    def test_beside_stage_name_is_a_plain_word_or_the_key(self):
        self.assertEqual(pw.stage_dir("a9352-window-plumbing-3", "k" * 64), ".incoming/a9352-window-plumbing-3")
        self.assertEqual(pw.stage_dir("../x", "abcdef0123456789zz"), ".incoming/abcdef0123456789")
        self.assertEqual(pw.stage_dir("", "abcdef0123456789zz"), ".incoming/abcdef0123456789")

    def test_request_conflict_mode_is_part_of_the_key_and_checked(self):
        plain = json.dumps({"source": "a1", "paths": ["research/pkg/"], "request": "r"})
        beside = json.dumps({"source": "a1", "paths": ["research/pkg/"], "request": "r", "conflict": "beside"})
        self.assertNotEqual(pw.request(plain, "a2")[1], pw.request(beside, "a2")[1])
        with self.assertRaisesRegex(pw.Held, "conflict must be"):
            pw.request(json.dumps({"source": "a1", "paths": ["x"], "conflict": "overwrite"}), "a2")

    def test_landing_refuses_a_branch_still_holding_incoming(self):
        self.assertTrue(".incoming/r1/INVENTORY.json".startswith(landing.BANNED))
        self.assertFalse("research/pkg/x".startswith(landing.BANNED))

    def test_house_posts_the_beside_inventory_once(self):
        self.beside_fixture()
        ws, subject = self.fake_workshop()
        subject["props"]["brings"] = json.dumps({"source": "a1", "paths": ["research/pkg/"],
                                                 "request": "r1", "conflict": "beside"})
        self.assertTrue(ws.bring("a2", subject))
        self.assertTrue(ws.bring("a2", subject))
        said = [t for c, t in self.messages if "staged" in t and "beside" in t]
        self.assertEqual(len(said), 1, self.messages)
        self.assertIn("research/pkg/existing.txt: both-changed", said[0])
        self.assertIn(".incoming/r1/INVENTORY.json", said[0])
        self.assertTrue(subject["props"]["brings_status"].startswith("staged beside"))
        self.assertEqual((self.dest / "research/pkg/existing.txt").read_text(), "receiver painter change\n")

    def test_staged_source_is_not_changed_or_receiver_checkpointed(self):
        self.put(self.source, "research/pkg/new.txt", "source")
        self.put(self.dest, "own.txt", "receiver work")
        self.assertEqual(pw.head(self.source), self.base)
        pw.git(self.source, "add", "research/pkg/new.txt")
        staged = pw.git(self.source, "diff", "--cached").stdout
        with self.assertRaisesRegex(pw.Held, "staged"):
            self.run_transfer()
        self.assertEqual(pw.git(self.source, "diff", "--cached").stdout, staged)
        self.assertEqual(pw.head(self.dest), self.base)
        self.assertEqual((self.dest / "own.txt").read_text(), "receiver work")

    def test_dirty_receiver_checkpoints_own_edits_then_receives_main(self):
        self.put(self.live, "research/pkg/browser.md", "main input")
        self.put(self.dest, "own.txt", b"own raw\r\nbytes")
        self.put(self.dest, "research/pkg/existing.txt", "receiver edit\n")
        self.put(self.dest, "src/text-desk/notation/sessions/copy.pickle", "not source")
        ws, subject = self.fake_workshop(source="main")
        original_say = ws.say
        def say(card, text, **kw):
            if text.startswith("Receiver work checkpointed"):
                self.assertFalse((self.dest / "research/pkg/browser.md").exists())
                self.assertEqual(pw.out(self.dest, "show", "HEAD:own.txt"), "own raw\r\nbytes")
                self.assertIn(hashlib.sha256(b"own raw\r\nbytes").hexdigest(), text)
            original_say(card, text, **kw)
        ws.say = say
        self.assertTrue(ws.bring("a2", subject))
        self.assertEqual(subject["props"]["commission"], "paused")
        self.assertEqual((self.dest / "research/pkg/existing.txt").read_text(), "receiver edit\n")
        self.assertEqual((self.dest / "research/pkg/browser.md").read_text(), "main input")
        data = pw.read_receipt(Path(subject["props"]["brings_receipt"]))
        checkpoint = data["receiver_checkpoint"]
        self.assertEqual(set(checkpoint["files"]), {"own.txt", "research/pkg/existing.txt"})
        self.assertTrue(checkpoint["reported"])
        self.assertNotEqual(checkpoint["after"], self.base)
        self.assertEqual(data["recipient_before"], checkpoint["after"])
        self.assertEqual(len(self.messages), 2)
        self.assertTrue(ws.bring("a2", subject))
        self.assertEqual(len(self.messages), 2)
        self.assertEqual(pw.head(self.live), self.base)
        self.assertEqual(ws.workers, {})

    def test_partial_index_and_worktree_versions_both_survive(self):
        self.put(self.source, "research/pkg/new.txt", "source")
        self.put(self.dest, "research/pkg/existing.txt", "staged version")
        pw.git(self.dest, "add", "research/pkg/existing.txt")
        self.put(self.dest, "research/pkg/existing.txt", "working version")
        data = self.run_transfer(paths=["research/pkg/new.txt"])
        checkpoint = data["receiver_checkpoint"]
        self.assertEqual(len(checkpoint["commits"]), 2)
        self.assertEqual(pw.out(self.dest, "show", checkpoint["commits"][0] +
                                ":research/pkg/existing.txt"), "staged version")
        self.assertEqual(pw.out(self.dest, "show", checkpoint["after"] +
                                ":research/pkg/existing.txt"), "working version")
        self.assertEqual(checkpoint["index_files"]["research/pkg/existing.txt"]["sha256"],
                         hashlib.sha256(b"staged version").hexdigest())
        self.assertEqual((self.dest / "research/pkg/existing.txt").read_text(), "working version")

    def test_receiver_staged_rename_deletion_and_untracked_bytes_survive(self):
        self.put(self.dest, "delete.txt", "kept in old history")
        self.commit(self.dest)
        pw.git(self.dest, "rm", "delete.txt")  # fixture-owned only
        pw.git(self.dest, "mv", "research/pkg/existing.txt", "research/pkg/renamed.txt")
        self.put(self.dest, "new.bin", b"\x00receiver")
        self.put(self.source, "research/pkg/new.txt", "source")
        data = self.run_transfer(paths=["research/pkg/new.txt"])
        checkpoint = data["receiver_checkpoint"]
        self.assertEqual(checkpoint["files"]["delete.txt"], {"deleted": True})
        self.assertEqual(checkpoint["index_files"]["delete.txt"], {"deleted": True})
        self.assertEqual((self.dest / "research/pkg/renamed.txt").read_text(), "base\n")
        self.assertEqual((self.dest / "new.bin").read_bytes(), b"\x00receiver")
        self.assertFalse((self.dest / "delete.txt").exists())
        self.assertEqual(pw.git(self.dest, "status", "--porcelain").stdout, b"")

    def test_interrupted_receiver_checkpoint_never_repeats_commit(self):
        self.put(self.source, "research/pkg/new.txt", "source")
        self.put(self.dest, "own.txt", "receiver")
        write = pw.write_receipt
        def fail_preserved(path, data):
            if data.get("phase") == "receiver-preserved":
                raise OSError("fixture lost checkpoint acknowledgement")
            write(path, data)
        with patch.object(pw, "write_receipt", side_effect=fail_preserved):
            with self.assertRaises(OSError):
                self.run_transfer()
        after = pw.head(self.dest)
        self.assertNotEqual(after, self.base)
        with self.assertRaisesRegex(pw.Held, "recipient checkpoint was interrupted"):
            self.run_transfer()
        self.assertEqual(pw.head(self.dest), after)
        self.assertEqual(pw.head(self.source), self.base)
        self.assertEqual((self.dest / "own.txt").read_text(), "receiver")

    def test_checkpoint_reporting_failure_holds_delivery_and_resumes_saved_checkpoint(self):
        self.put(self.source, "research/pkg/new.txt", "source")
        self.put(self.dest, "own.txt", "receiver")
        def fail_report(saved):
            raise OSError("fixture card report unavailable")
        args = (landing, self.source, self.dest, "a1", "a2",
                ["research/pkg/new.txt"], self.receipt, "fixture-key")
        with self.assertRaises(OSError):
            pw.transfer(*args, report_checkpoint=fail_report)
        after = pw.head(self.dest)
        self.assertEqual(pw.head(self.source), self.base)
        self.assertFalse((self.dest / "research/pkg/new.txt").exists())
        reports = []
        data = pw.transfer(*args, report_checkpoint=reports.append)
        self.assertEqual(data["receiver_checkpoint"]["after"], after)
        self.assertEqual(len(reports), 1)
        self.assertEqual(data["phase"], "applied")

    def test_private_receiver_input_is_held_without_mutation(self):
        self.put(self.source, "research/pkg/new.txt", "source")
        self.put(self.dest, "private/fixture.txt", "fixture private path")
        with self.assertRaisesRegex(pw.Held, "not transferable"):
            self.run_transfer()
        self.assertEqual(pw.head(self.dest), self.base)
        self.assertEqual(pw.head(self.source), self.base)

    def test_missing_ignored_private_and_escape_inputs_refuse(self):
        for name in ("../outside", "/absolute", ".git/config", ".env", "a/.env.local",
                     "src/text-desk/notation/sessions/frontier.pickle", "a\\b", "a*",
                     ".git./config", "src/text-desk/notation/sessions./world", "NUL", "a/CON.txt"):
            with self.subTest(name=name), self.assertRaises(pw.Held):
                pw.request(json.dumps({"source": "main", "paths": [name]}), "a2")
        self.put(self.source, "ignored/report.txt", "not public")
        for name in ("research/pkg/missing", "ignored/report.txt"):
            with self.subTest(name=name), self.assertRaises(pw.Held):
                self.run_transfer(paths=[name])
        self.assertEqual(pw.head(self.dest), self.base)

    def test_ignored_receiver_collision_refuses_without_overwrite(self):
        self.put(self.source, "research/pkg/new.txt", "source")
        self.put(self.dest, "research/pkg/.gitignore", "new.txt\n")
        self.commit(self.dest)
        self.put(self.dest, "research/pkg/new.txt", "ignored receiver work")
        before = pw.head(self.dest)
        with self.assertRaisesRegex(pw.Held, "ignored"):
            self.run_transfer(paths=["research/pkg/new.txt"])
        self.assertEqual((self.dest / "research/pkg/new.txt").read_text(), "ignored receiver work")
        self.assertEqual(pw.head(self.dest), before)

    def test_preserved_selector_is_bounded_to_source_edits_not_worlds(self):
        self.put(self.source, "research/pkg/new.txt", "new")
        self.put(self.source, "src/text-desk/notation/sessions/copy.pickle", "fixture only")
        data = self.run_transfer(paths=["@preserved"])
        self.assertEqual(list(data["files"]), ["research/pkg/new.txt"])
        with self.assertRaisesRegex(pw.Held, "main requires explicit"):
            pw.request(json.dumps({"source": "main", "paths": ["@preserved"]}), "a2")

    def test_wrong_branch_and_in_progress_merge_refuse(self):
        pw.git(self.dest, "checkout", "-b", "not-the-card")
        with self.assertRaisesRegex(pw.Held, "different branch"):
            self.run_transfer()
        pw.git(self.dest, "checkout", "worker/a2")
        merge_head = Path(pw.out(self.dest, "rev-parse", "--path-format=absolute", "--git-path", "MERGE_HEAD"))
        merge_head.write_text(self.base + "\n")
        with self.assertRaisesRegex(pw.Held, "unfinished merge"):
            self.run_transfer()

    def test_surviving_planned_receipt_reconciles_without_replay(self):
        self.put(self.source, "research/pkg/new.txt", "source")
        write = pw.write_receipt
        def fail_applied(path, data):
            if data.get("phase") == "applied":
                raise OSError("fixture crash after fast-forward")
            write(path, data)
        with patch.object(pw, "write_receipt", side_effect=fail_applied):
            with self.assertRaises(OSError):
                self.run_transfer()
        before_source, before_dest = pw.head(self.source), pw.head(self.dest)
        recovered = self.run_transfer()
        self.assertEqual(recovered["phase"], "applied")
        self.assertEqual(recovered["received_files"], recovered["committed_files"])
        self.assertIn("received_worktree_files", recovered)
        self.assertEqual((pw.head(self.source), pw.head(self.dest)), (before_source, before_dest))

    def test_ambiguous_interruption_refuses_instead_of_replaying(self):
        self.receipt.write_text(json.dumps({"phase": "preserving"}))
        with self.assertRaisesRegex(pw.Held, "interrupted"):
            self.run_transfer()
        self.assertEqual(pw.head(self.dest), self.base)

    def fake_workshop(self, source="a1"):
        spec = json.dumps({"source": source, "paths": ["research/pkg/"]})
        self.subjects = {"a1": ({"props": {"commission": "paused"}}, "paused"),
                         "a2": ({"props": {"commission": "paused", "brings": spec}}, "paused")}
        house = SimpleNamespace(dir=self.state, load=lambda: None)
        ws = workshop.Workshop(house)
        ws.commissions = lambda w: self.subjects
        self.messages = []
        def say(card, text, **kw):
            self.messages.append((card, text))
            self.subjects[card][0].setdefault("comments", []).append(
                {"by": "house", "text": text})
        ws.say = say
        def set_state(card, state, **props):
            self.subjects[card][0]["props"].update(commission=state, **props)
        ws.set_state = set_state
        ws.bring_props = lambda card, **props: self.subjects[card][0]["props"].update(**props)
        return ws, self.subjects["a2"][0]

    def test_house_paused_delivery_does_not_start_models_and_reports_once(self):
        self.put(self.source, "research/pkg/new.txt", "source")
        ws, subject = self.fake_workshop()
        self.assertTrue(ws.bring("a2", subject))
        self.assertTrue(ws.bring("a2", subject))
        self.assertEqual(subject["props"]["commission"], "paused")
        self.assertEqual(len(self.messages), 1)
        self.assertEqual(ws.workers, {})

    def test_house_requires_card_inventory_receipt_before_delivery(self):
        self.put(self.source, "research/pkg/new.txt", "source")
        self.put(self.dest, "own.txt", "receiver")
        ws, subject = self.fake_workshop()
        real_say = ws.say
        ws.say = lambda *args, **kw: None  # world refuses silently, not an exception
        self.assertFalse(ws.bring("a2", subject))
        self.assertIn("inventory not confirmed", subject["props"]["brings_status"])
        after = pw.head(self.dest)
        self.assertNotEqual(after, self.base)
        self.assertEqual(pw.head(self.source), self.base)
        self.assertFalse((self.dest / "research/pkg/new.txt").exists())
        self.assertEqual(subject["props"]["commission"], "paused")
        ws.say = real_say
        self.assertTrue(ws.bring("a2", subject))
        data = pw.read_receipt(Path(subject["props"]["brings_receipt"]))
        self.assertEqual(data["receiver_checkpoint"]["after"], after)
        self.assertEqual(len(self.messages), 2)

    def use_real_card_comments(self, ws, subject):
        """Exercise the actual desk quoting/parser/storage, not an echo mock."""
        import roomworld
        desk, _ = roomworld.build(say=False)
        desk.batch = True  # House.act uses the batched desk transport.
        world = desk.world
        world.me = "house"
        for line in (f"look {world.root} :1",
                     f'do create {world.root} kind=note title="Receiver fixture"'):
            result = desk.dispatch("desk", {"line": line, "whole": True})
            self.assertNotIn("error", result, result)
        target = world.last_created
        stored = world.subjects[world.subject_of(target)]
        subject["comments"] = stored["comments"]

        def act(actor, line):
            world.me = actor
            line = line.replace("read a2;", f"read {target};").replace(
                "do comment a2 ", f"do comment {target} ")
            result = desk.dispatch("desk", {"line": line, "whole": False})
            self.assertNotIn("error", result, result)
            self.assertFalse(result.get("batch_error"), result)
            return result

        ws.house.act = act
        ws.say = workshop.Workshop.say.__get__(ws)

    def test_live_card_parser_confirms_new_inventory_and_retry_does_not_repost(self):
        self.put(self.source, "research/pkg/new.txt", "source")
        self.put(self.dest, "own.txt", "receiver")
        ws, subject = self.fake_workshop()
        self.use_real_card_comments(ws, subject)
        self.assertTrue(ws.bring("a2", subject))
        checkpoint = [c for c in subject["comments"]
                      if c["text"].startswith("Receiver work checkpointed")]
        self.assertEqual(len(checkpoint), 1)
        data = pw.read_receipt(Path(subject["props"]["brings_receipt"]))
        self.assertIn(data["request"], checkpoint[0]["text"])
        self.assertTrue(data["receiver_checkpoint"]["reported"])
        after = pw.head(self.dest)
        self.assertTrue(ws.bring("a2", subject))
        self.assertEqual(pw.head(self.dest), after)
        self.assertEqual(len(subject["comments"]), 2)  # inventory + delivery
        self.assertEqual(subject["props"]["commission"], "paused")

    def test_live_legacy_inventory_with_decoded_windows_path_is_reused(self):
        self.put(self.source, "research/pkg/new.txt", "source")
        self.put(self.dest, "own.txt", "receiver")
        ws, subject = self.fake_workshop()
        ws.say = lambda *args, **kw: None
        self.assertFalse(ws.bring("a2", subject))
        _, key = pw.request(subject["props"]["brings"], "a2")
        receipt = self.state / "brings" / f"a2-{key}.json"
        data = pw.read_receipt(receipt)
        saved = data["receiver_checkpoint"]
        checkpoint = pw.head(self.dest)
        self.use_real_card_comments(ws, subject)
        windows = "C:\\Projects\\Agora4\\src\\text-desk\\notation\\house-state\\frontier\\brings\\"
        legacy = ("Receiver work checkpointed before handoff: " + json.dumps(saved, sort_keys=True) +
                  f". Durable inventory: {windows}{receipt.name}. Own worker branch only; not ready or landed.")
        ws.say("a2", legacy, to="nobody")
        self.assertNotEqual(subject["comments"][0]["text"], legacy)
        self.assertIn("\notation", subject["comments"][0]["text"])
        # Old duplicate entries/other comments and their position are immaterial.
        ws.say("a2", "Unrelated later context", to="nobody")
        self.assertTrue(ws.bring("a2", subject))
        self.assertEqual(sum(c["text"].startswith("Receiver work checkpointed")
                             for c in subject["comments"]), 1)
        data = pw.read_receipt(receipt)
        self.assertEqual(data["receiver_checkpoint"]["after"], checkpoint)
        self.assertTrue(data["receiver_checkpoint"]["reported"])
        self.assertEqual((self.dest / "research/pkg/new.txt").read_text(), "source")
        self.assertEqual(subject["props"]["commission"], "paused")

    def test_checkpoint_confirmation_requires_request_author_and_all_hashes(self):
        ws, subject = self.fake_workshop()
        receipt = self.state / "a2-current-request.json"
        saved = {"after": "a" * 40, "before": "b" * 40, "commits": ["a" * 40],
                 "files": {"own.txt": {"sha256": "c" * 64, "bytes": 5}},
                 "index_files": {}, "committed_files": {}}
        prefix = "Receiver work checkpointed before handoff: "
        good = {"request": "current-request", "checkpoint": saved}
        wrong_hash = json.loads(json.dumps(good))
        wrong_hash["checkpoint"]["files"]["own.txt"]["sha256"] = "d" * 64
        subject["comments"] = [
            {"by": "house", "text": prefix + "{broken"},
            {"by": "rowan", "text": prefix + json.dumps(good)},
            {"by": "house", "text": prefix + json.dumps(dict(good, request="other"))},
            {"by": "house", "text": prefix + json.dumps(wrong_hash)},
            {"by": "house", "text": prefix + json.dumps(saved) +
             ". Durable inventory: C:/brings/a2-other.json. "},
        ]
        ws.say = lambda *args, **kw: None
        with self.assertRaisesRegex(pw.Held, "inventory not confirmed"):
            ws.report_receiver_checkpoint("a2", receipt, saved)
        subject["comments"].insert(1, {"by": "house", "text": prefix + json.dumps(good)})
        ws.report_receiver_checkpoint("a2", receipt, dict(saved, reported=False))

    def test_main_input_hold_is_satisfied_only_by_real_import(self):
        self.put(self.live, "research/pkg/new.txt", "main artifact")
        ws, subject = self.fake_workshop(source="main")
        subject.update(title="Review", text="Read research/pkg/new.txt")
        import shared
        self.assertEqual(shared.check(subject, self.live)["hold"], ["research/pkg/new.txt"])
        self.assertEqual(ws.brought_paths("a2", subject), set())
        self.assertTrue(ws.bring("a2", subject))
        self.assertFalse(ws.uncommitted(None, "a2", subject))
        self.assertFalse(shared.check(subject, self.live, available=ws.brought_paths("a2", subject))["worker"])
        # The main files remain uncommitted; no blanket uncommitted=ok is set.
        self.assertEqual(pw.head(self.live), self.base)
        self.assertNotIn("uncommitted", subject["props"])

    def test_house_busy_worker_and_real_process_lease_hold(self):
        ws, subject = self.fake_workshop()
        ws.workers["a1"] = SimpleNamespace(busy=True, alive=lambda: True)
        self.assertFalse(ws.bring("a2", subject))
        self.assertFalse(ws.bring("a2", subject))
        self.assertEqual(len(self.messages), 1)
        ws.workers.clear()
        # A surviving adapter outside Workshop's in-memory registry still owns
        # its process-held lease. A separate process holds it deterministically.
        import subprocess
        code = ("import sys;sys.path.insert(0,sys.argv[1]);"
                "from worker_lease import worker_leases;"
                "lease=worker_leases([sys.argv[2]]);lease.__enter__();"
                "print('held',flush=True);sys.stdin.readline()")
        child = subprocess.Popen([sys.executable, "-c", code, str(HERE.parents[1] / "codex"),
                                  str(self.state / "worker-a1/worker.lock")],
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        try:
            self.assertEqual(child.stdout.readline().strip(), "held")
            self.assertFalse(ws.bring("a2", subject))
            self.assertIn("lease", subject["props"]["brings_status"].lower())
            self.assertEqual(pw.head(self.dest), self.base)
        finally:
            child.communicate("\n", timeout=10)

    def test_unleased_saved_runtime_is_unknown_not_assumed_stopped(self):
        ws, subject = self.fake_workshop()
        ws.card_state = lambda card: {"session": "old", "session_provider": "claude"} if card == "a1" else {}
        self.assertFalse(ws.bring("a2", subject))
        self.assertIn("unleased", subject["props"]["brings_status"])
        self.assertEqual(pw.head(self.dest), self.base)

    def test_house_creates_only_absent_recipient_worktree(self):
        pw.git(self.live, "worktree", "remove", str(self.dest))
        self.put(self.source, "research/pkg/new.txt", "source")
        ws, subject = self.fake_workshop()
        self.assertTrue(ws.bring("a2", subject))
        self.assertEqual((self.dest / "research/pkg/new.txt").read_text(), "source")

    def test_step_processes_paused_request_before_resume_and_never_starts(self):
        self.put(self.source, "research/pkg/new.txt", "source")
        ws, subject = self.fake_workshop()
        ws.compare_lived = lambda w: None
        ws.keeper_reverts = lambda w: False
        ws.limit_handoffs = lambda w, cfg: False
        ws.ordered = lambda cs, cfg: cs.items()
        with patch.object(ws, "resume") as resume, patch.object(ws, "begin") as begin:
            ws.step(None, {})
        resume.assert_not_called()
        begin.assert_not_called()
        self.assertEqual((self.dest / "research/pkg/new.txt").read_text(), "source")
        self.assertEqual(subject["props"]["commission"], "paused")

    def test_changed_request_and_busy_landing_do_not_mutate(self):
        ws, subject = self.fake_workshop()
        with patch.object(landing, "_try_lock", return_value=None):
            self.assertFalse(ws.bring("a2", subject))
        self.assertEqual(pw.head(self.dest), self.base)
        initial = self.subjects
        calls = 0
        def changed(_):
            nonlocal calls
            calls += 1
            return initial if calls == 1 else {"a2": ({"props": {"brings": "{}"}}, "paused")}
        ws.commissions = changed
        self.assertFalse(ws.bring("a2", subject))
        self.assertIn("changed", subject["props"]["brings_status"])
        self.assertEqual(pw.head(self.source), self.base)
        self.assertEqual(pw.head(self.dest), self.base)

    def test_delivery_order_requires_actual_prior_receipt_not_status_prop(self):
        ws, subject = self.fake_workshop()
        spec = json.loads(subject["props"]["brings"])
        spec["after"] = "a1"
        subject["props"]["brings"] = json.dumps(spec)
        self.subjects["a1"][0]["props"].update(brings=json.dumps({
            "source": "main", "paths": ["research/pkg/existing.txt"]}), brings_status="applied forged")
        self.assertFalse(ws.bring("a2", subject))
        self.assertIn("receipt", subject["props"]["brings_status"])
        self.assertEqual(pw.head(self.dest), self.base)

    def test_order_survives_prior_review_worktree_removal(self):
        ws, subject = self.fake_workshop(source="main")
        prior_raw = json.dumps({"source": "main", "paths": ["research/pkg/existing.txt"]})
        self.subjects["a1"][0]["props"]["brings"] = prior_raw
        _, key = pw.request(prior_raw, "a1")
        prior_path = self.state / "brings" / f"a1-{key}.json"
        pw.transfer(landing, self.live, self.source, "main", "a1",
                    ["research/pkg/existing.txt"], prior_path, key)
        pw.git(self.live, "worktree", "remove", str(self.source))
        self.put(self.live, "research/pkg/new.txt", "browser")
        spec = json.loads(subject["props"]["brings"])
        spec["after"] = "a1"
        subject["props"]["brings"] = json.dumps(spec)
        self.assertTrue(ws.bring("a2", subject))
        self.assertEqual((self.dest / "research/pkg/new.txt").read_text(), "browser")


if __name__ == "__main__":
    unittest.main()
