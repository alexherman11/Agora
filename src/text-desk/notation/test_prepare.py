# health: room test
"""House preparation on isolated Git repositories; no judging/live operations."""
import os
import json
from pathlib import Path
import shutil
import sys
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import preserved_work as pw
import workshop


class Prepare(unittest.TestCase):
    def setUp(self):
        self.tmp = HERE.parents[2] / (".prepare-test-" + uuid.uuid4().hex)
        self.tmp.mkdir()
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))
        self.live = self.tmp / "live"
        self.live.mkdir()
        self.tree = self.tmp / "a123"
        self.env = patch.dict(os.environ, dict(
            GIT_AUTHOR_NAME="Fixture", GIT_AUTHOR_EMAIL="fixture@example.invalid",
            GIT_COMMITTER_NAME="Fixture", GIT_COMMITTER_EMAIL="fixture@example.invalid"))
        self.env.start()
        self.addCleanup(self.env.stop)
        pw.git(self.live, "init", "-b", "main")
        (self.live / "base.txt").write_text("original\n")
        self.commit(self.live, "base")
        pw.git(self.live, "worktree", "add", "-b", "worker/a123", str(self.tree))
        self.receipt = self.tmp / "prepare.json"

    def commit(self, tree, title):
        pw.git(tree, "add", "-A")
        pw.git(tree, "commit", "-m", title)

    def run_prepare(self):
        return pw.prepare_main(self.live, self.tree, "a123", self.receipt, "e1")

    def test_clean_merge_changes_worker_only(self):
        (self.live / "main.txt").write_text("current main")
        self.commit(self.live, "main update")
        main = pw.head(self.live)
        result = self.run_prepare()
        self.assertEqual(result["phase"], "prepared")
        self.assertEqual((self.tree / "main.txt").read_text(), "current main")
        self.assertEqual(pw.head(self.live), main)
        self.assertEqual(result["main"], main)
        self.assertEqual(result["conflicts"], [])

    def test_uncommitted_and_partial_index_are_kept(self):
        file = self.tree / "base.txt"
        file.write_text("index version\n")
        pw.git(self.tree, "add", "base.txt")
        file.write_text("worktree version\n")
        (self.tree / "untracked.txt").write_text("preserved")
        result = self.run_prepare()
        checkpoint = result["receiver_checkpoint"]
        self.assertEqual(len(checkpoint["commits"]), 2)
        self.assertEqual(pw.git(self.tree, "show",
                               checkpoint["commits"][0] + ":base.txt").stdout, b"index version\n")
        self.assertEqual(file.read_text(), "worktree version\n")
        self.assertEqual((self.tree / "untracked.txt").read_text(), "preserved")
        self.assertIn("untracked.txt", checkpoint["files"])
        self.assertFalse(pw.git(self.tree, "status", "--porcelain").stdout)

    def test_conflict_left_in_files_with_checkpoint(self):
        (self.live / "base.txt").write_text("main version\n")
        self.commit(self.live, "main edit")
        (self.tree / "base.txt").write_text("worker uncommitted\n")
        main = pw.head(self.live)
        result = self.run_prepare()
        self.assertEqual(result["phase"], "prepare-conflict")
        self.assertEqual(result["conflicts"], ["base.txt"])
        self.assertIn("<<<<<<<", (self.tree / "base.txt").read_text())
        self.assertIn("worker uncommitted", (self.tree / "base.txt").read_text())
        self.assertEqual(pw.head(self.live), main)
        self.assertIn("base.txt", result["receiver_checkpoint"]["files"])
        self.assertEqual(self.run_prepare(), result)  # reporting retry, no second merge

    def test_unknown_crash_is_never_replayed(self):
        pw.write_receipt(self.receipt, dict(request="e1", phase="prepare-merging"))
        with patch.object(pw, "git", side_effect=AssertionError("must not execute")):
            with self.assertRaisesRegex(pw.Held, "not replaying"):
                self.run_prepare()

    def test_duplicate_clean_result_does_not_merge_again(self):
        result = self.run_prepare()
        with patch.object(pw, "git", wraps=pw.git) as git:
            self.assertEqual(self.run_prepare(), result)
        self.assertFalse(any("merge" in c.args[1:] for c in git.call_args_list))

    def test_wrong_registered_branch_refused(self):
        pw.git(self.tree, "switch", "-c", "wrong")
        with self.assertRaisesRegex(pw.Held, "different branch"):
            self.run_prepare()
        self.assertFalse(self.receipt.exists())

    def test_binary_conflict_does_not_choose_a_side(self):
        (self.live / "base.txt").write_bytes(b"main\0binary")
        self.commit(self.live, "binary main")
        (self.tree / "base.txt").write_bytes(b"worker\0binary")
        result = self.run_prepare()
        self.assertEqual(result["binary"], ["base.txt"])
        self.assertTrue(result["merge_aborted"])
        self.assertEqual((self.tree / "base.txt").read_bytes(), b"worker\0binary")
        self.assertFalse(pw.git(self.tree, "ls-files", "-u").stdout)

    def test_withdrawal_after_checkpoint_keeps_edits_without_merge(self):
        (self.tree / "draft.txt").write_text("kept")
        (self.live / "main.txt").write_text("not yet merged")
        self.commit(self.live, "main edit")
        def withdrawn():
            raise pw.Held("withdrawn")
        with self.assertRaisesRegex(pw.Held, "withdrawn"):
            pw.prepare_main(self.live, self.tree, "a123", self.receipt, "e1", admit=withdrawn)
        self.assertEqual((self.tree / "draft.txt").read_text(), "kept")
        self.assertFalse((self.tree / "main.txt").exists())
        self.assertFalse(pw.git(self.tree, "status", "--porcelain").stdout)

    def handler(self):
        import landing
        pool = object.__new__(workshop.Workshop)
        pool.workers, pool.landing = {}, {}
        pool.card_state = lambda cid: {}
        card = {"id": "s123", "props": {"commission": "prepare"}}
        world = SimpleNamespace(events=[
            {"id": "e1", "target": "a123", "args": {"commission": "prepare"}}])
        pool.house = SimpleNamespace(dir=self.tmp / "state", load=lambda: world)
        pool.commissions = lambda w: {"a123": (card, card["props"]["commission"])}
        reports, states = [], []
        pool.say = lambda cid, text, **kw: reports.append(text)
        pool.set_state = lambda cid, state, **kw: states.append((state, kw))
        pool.report_receiver_checkpoint = lambda *args: None
        return pool, card, reports, states, landing

    def test_real_prepare_handler_holds_lock_and_returns_working(self):
        pool, card, reports, states, landing = self.handler()
        (self.live / "current.txt").write_text("main")
        self.commit(self.live, "main edit")
        lock = object()
        with patch.object(workshop, "REPO", self.live), patch.object(
                workshop, "TREES", self.tmp), patch.object(landing, "_try_lock",
                return_value=lock), patch.object(landing, "_unlock") as unlock, patch.object(
                pool, "land", side_effect=AssertionError("never land")):
            pool.prepare("a123", card)
        unlock.assert_called_once_with(lock)
        self.assertEqual(states[-1][0], "working")
        self.assertEqual(states[-1][1]["prepare_status"], "prepared")
        self.assertIn("No judging, landing or restart", reports[-1])
        self.assertEqual((self.tree / "current.txt").read_text(), "main")

    def test_prepare_conflict_keeps_ordinary_ready_marker_fence(self):
        pool, card, reports, states, landing = self.handler()
        (self.live / "base.txt").write_text("main version\n")
        self.commit(self.live, "main edit")
        (self.tree / "base.txt").write_text("uncommitted worker version\n")
        with patch.object(workshop, "REPO", self.live), patch.object(
                workshop, "TREES", self.tmp), patch.object(landing, "_try_lock",
                return_value=object()), patch.object(landing, "_unlock"):
            pool.prepare("a123", card)
        state = json.loads((pool.house.dir / "worker-a123/state.json").read_text())
        self.assertEqual(state["house_merge"]["files"], ["base.txt"])
        self.assertEqual(states[-1][1]["prepare_status"], "prepare-conflict")
        self.assertIn("<<<<<<<", reports[-1])
        wk = SimpleNamespace(state=state, tree=self.tree, save=lambda: None)
        before = pw.head(self.tree)
        with patch.object(pool, "returned") as returned:
            self.assertFalse(pool.merge_resolved("a123", card, wk))
        returned.assert_called_once()
        self.assertEqual(pw.head(self.tree), before)

    def test_landing_lock_busy_does_not_touch_git_or_rewrite_request(self):
        pool, card, reports, states, landing = self.handler()
        pool.bring_props = lambda cid, **kw: card["props"].update(kw)
        with patch.object(landing, "_try_lock", return_value=None), patch.object(
                pw, "prepare_main", side_effect=AssertionError("must not merge")):
            pool.prepare("a123", card)
            pool.prepare("a123", card)
        self.assertEqual(states, [])
        self.assertEqual(len(reports), 1)
        self.assertEqual(card["props"]["commission"], "prepare")

    def test_earlier_unknown_blocks_new_request(self):
        receipt = self.tmp / "a123-e2.json"
        pw.write_receipt(self.tmp / "a123-e1.json",
                         {"request": "e1", "phase": "prepare-merging"})
        with self.assertRaisesRegex(pw.Held, "earlier prepare"):
            pw.prepare_main(self.live, self.tree, "a123", receipt, "e2")
        self.assertFalse(receipt.exists())

    def interrupted_checkpoint(self):
        (self.tree / "draft.txt").write_text("captured draft\n")
        files, staged = pw.receiver_edits(self.tree)
        saved = dict(before=pw.head(self.tree), files=files, index_files=staged)
        data = dict(request="e1", phase="receiver-preserving",
                    before=pw.head(self.tree), main=pw.head(self.live),
                    receiver_checkpoint=saved)
        pw.write_receipt(self.receipt, data)
        return data

    def test_interrupted_checkpoint_before_commit_can_resume(self):
        data = self.interrupted_checkpoint()
        result = self.run_prepare()
        self.assertEqual(result["phase"], "prepared")
        self.assertEqual(result["reconciliations"][0]["checkpoint"], data["receiver_checkpoint"])
        self.assertEqual((self.tree / "draft.txt").read_text(), "captured draft\n")
        self.assertFalse(pw.git(self.tree, "status", "--porcelain").stdout)

    def test_interrupted_git_add_can_resume_without_reset(self):
        self.interrupted_checkpoint()
        pw.git(self.tree, "add", "draft.txt")
        result = self.run_prepare()
        self.assertEqual(result["phase"], "prepared")
        self.assertEqual(len(result["receiver_checkpoint"]["commits"]), 1)

    def test_changed_files_hold_without_rewriting_receipt(self):
        self.interrupted_checkpoint()
        before = self.receipt.read_bytes()
        (self.tree / "draft.txt").write_text("newer draft\n")
        with self.assertRaisesRegex(pw.Held, "files changed"):
            self.run_prepare()
        self.assertEqual(self.receipt.read_bytes(), before)
        self.assertEqual((self.tree / "draft.txt").read_text(), "newer draft\n")

    def test_unknown_commit_is_not_reissued(self):
        self.interrupted_checkpoint()
        self.commit(self.tree, "unconfirmed commit")
        before = self.receipt.read_bytes()
        with self.assertRaisesRegex(pw.Held, "not replaying"):
            self.run_prepare()
        self.assertEqual(self.receipt.read_bytes(), before)

    def test_confirmation_failure_resumes_saved_checkpoint_once(self):
        (self.tree / "draft.txt").write_text("preserve once")
        with self.assertRaisesRegex(pw.Held, "not confirmed"):
            pw.prepare_main(self.live, self.tree, "a123", self.receipt, "e1",
                            report=lambda saved: (_ for _ in ()).throw(pw.Held("not confirmed")))
        kept = pw.head(self.tree)
        reports = []
        result = pw.prepare_main(self.live, self.tree, "a123", self.receipt, "e1",
                                 report=lambda saved: reports.append(saved["after"]))
        self.assertEqual(reports, [kept])
        self.assertEqual(result["receiver_checkpoint"]["commits"], [kept])
        self.assertEqual(result["phase"], "prepared")

    def test_changed_index_holds(self):
        self.interrupted_checkpoint()
        (self.tree / "base.txt").write_text("other staged change\n")
        pw.git(self.tree, "add", "base.txt")
        (self.tree / "base.txt").write_text("original\n")
        with self.assertRaisesRegex(pw.Held, "files changed|index changed"):
            self.run_prepare()


class Dispatch(unittest.TestCase):
    def test_prepare_has_its_own_dispatch_branch(self):
        pool = object.__new__(workshop.Workshop)
        pool.workers = {}
        pool.compare_lived = lambda w: None
        pool.keeper_reverts = lambda w: False
        pool.limit_handoffs = lambda w, cfg: False
        pool.commissions = lambda w: {"a123": ({"props": {}}, "prepare")}
        pool.ordered = lambda cs, cfg: cs.items()
        with patch.object(pool, "prepare") as prepare, patch.object(pool, "land",
                side_effect=AssertionError("must never land")):
            pool._step(object(), {})
        prepare.assert_called_once()

    def test_busy_owner_holds_without_taking_lock(self):
        pool = object.__new__(workshop.Workshop)
        pool.workers = {"a123": SimpleNamespace(busy=True)}
        card = {"props": {}}
        pool.house = SimpleNamespace(load=lambda: object())
        pool.commissions = lambda w: {"a123": (card, "prepare")}
        pool.set_state = lambda *args, **kwargs: None
        pool.bring_props = lambda *args, **kwargs: None
        pool.say = lambda *args, **kwargs: None
        import landing
        with patch.object(landing, "_try_lock", side_effect=AssertionError("busy owner")):
            pool.prepare("a123", card)


if __name__ == "__main__":
    unittest.main()
