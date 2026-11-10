# health: room test
"""a13300: real journal cache/recovery regressions; no supplied worlds or hosts."""
import json
import os
from pathlib import Path
import shutil
import unittest
from unittest import mock

import test_atomic_world as T
import agora_tmp
import atomic_world
import store


class JournalCache(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(agora_tmp.directory("journal-cache-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.log = store.Log(self.tmp / "test.jsonl")

    def record(self, title):
        flat = {("s1", "title"): title}
        return {"state": store.digest(flat),
                "parts": [{"facts": store._enc(store.diff({}, flat), {})}]}, flat

    def seed(self, title="One"):
        rec, flat = self.record(title)
        self.log.append(rec, flat)
        return flat

    def replace(self, title="Two"):
        replacement = store.Log(self.tmp / "replacement.jsonl")
        rec, flat = self.record(title)
        replacement.append(rec, flat)
        self.assertEqual(replacement.path.stat().st_size, self.log.path.stat().st_size)
        os.replace(replacement.path, self.log.path)
        return flat

    def test_equal_length_replacement_reads_actual_head_and_facts(self):
        self.seed()
        expected = self.replace()
        self.assertEqual(self.log.head(), (1, store.digest(expected)))
        self.assertEqual(self.log.flat(), (expected, 1, store.digest(expected)))

    def test_same_bytes_rotation_rereads_without_manual_eviction(self):
        expected = self.seed()
        raw = self.log.path.read_bytes()
        self.log.path.rename(self.tmp / "rotated.jsonl")
        self.log.path.write_bytes(raw)
        with mock.patch.object(self.log, "records", wraps=self.log.records) as records:
            self.assertEqual(self.log.flat()[0], expected)
        records.assert_called_once_with(0)

    def test_same_file_rewrite_with_preserved_length_rereads(self):
        self.seed()
        rec, expected = self.record("Two")
        replacement = store.Log(self.tmp / "rewrite.jsonl")
        replacement.append(rec, expected)
        raw = replacement.path.read_bytes()
        with self.log.path.open("r+b") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        self.assertEqual(self.log.flat()[0], expected)

    def test_actual_tail_digest_checked_even_if_stat_version_unchanged(self):
        self.seed()
        stamp = store._journal_stamp(self.log.path.stat())
        expected = self.replace()
        with mock.patch.object(store, "_journal_stamp", return_value=stamp):
            self.assertEqual(self.log.head(), (1, store.digest(expected)))
            self.assertEqual(self.log.flat()[0], expected)

    def test_actual_tail_sequence_checked_even_with_same_digest(self):
        expected = self.seed()
        raw = self.log.path.read_bytes().replace(b'"seq": 1', b'"seq": 9')
        self.log.path.write_bytes(raw)
        self.assertEqual(self.log.head(), (9, store.digest(expected)))
        self.assertEqual(self.log.flat(), (expected, 9, store.digest(expected)))

    def test_ordinary_append_supplied_facts_reuse_verified_cache(self):
        self.seed()
        rec, expected = self.record("Two")
        self.log.append(rec, expected)
        with mock.patch.object(self.log, "records", side_effect=AssertionError("unneeded replay")):
            self.assertEqual(self.log.head(), (2, store.digest(expected)))
            self.assertEqual(self.log.flat(), (expected, 2, store.digest(expected)))

    def test_external_append_without_facts_replays_current_records(self):
        self.seed()
        rec, expected = self.record("Two")
        store.Log(self.log.path).append(rec)
        self.assertEqual(self.log.flat(), (expected, 2, store.digest(expected)))

    def test_truncation_rereads_and_drops_newer_facts(self):
        expected = self.seed()
        first = self.log.path.read_bytes()
        rec, later = self.record("Two")
        self.log.append(rec, later)
        with self.log.path.open("r+b") as stream:
            stream.truncate(len(first))
        self.assertEqual(self.log.flat(), (expected, 1, store.digest(expected)))

    def test_missing_file_never_returns_cached_facts(self):
        self.seed()
        self.log.path.rename(self.tmp / "moved.jsonl")
        self.assertIsNone(self.log.head())
        self.assertEqual(self.log.flat(), ({}, 0, None))

    def test_growing_replacement_replays_from_beginning(self):
        self.seed()
        replacement = store.Log(self.tmp / "growing.jsonl")
        for title in ("Two", "New"):
            rec, expected = self.record(title)
            replacement.append(rec, expected)
        os.replace(replacement.path, self.log.path)
        with mock.patch.object(self.log, "records", wraps=self.log.records) as records:
            self.assertEqual(self.log.flat(), (expected, 2, store.digest(expected)))
        records.assert_called_once_with(0)

    def test_replacement_during_replay_refuses_and_does_not_cache(self):
        self.seed()
        self.log.path.write_bytes(self.log.path.read_bytes() + b" ")  # invalidates original version
        replacement = store.Log(self.tmp / "racing.jsonl")
        rec, expected = self.record("Two")
        replacement.append(rec, expected)
        records = self.log.records

        def racing(start=0):
            yield from records(start)
            os.replace(replacement.path, self.log.path)

        with mock.patch.object(self.log, "records", side_effect=racing):
            with self.assertRaises(OSError):
                self.log.flat()
        self.assertNotIn(str(self.log.path), store._HEADS)
        self.assertEqual(self.log.flat()[0], expected)

    def test_same_bytes_rotation_allows_full_kernel_recovery(self):
        f = T.AtomicWorldTests()
        f.setUp()
        self.addCleanup(f.doCleanups)
        f.normal(f"do create {f.desk.world.root} kind=note title=One")
        original = atomic_world.capture(f.desk)
        replacement = f.log.path.with_suffix(".rotation")
        replacement.write_bytes(f.log.path.read_bytes())
        os.replace(replacement, f.log.path)
        session = f.session()
        with session:
            self.assertEqual(atomic_world.status(session, "rotation-status-check")["status"], "absent")
        self.assertEqual(atomic_world.capture(f.desk), original)

    def replacement_fixture(self):
        f = T.AtomicWorldTests()
        f.setUp()
        self.addCleanup(f.doCleanups)
        f.normal(f"do create {f.desk.world.root} kind=note title=One")
        subject = f.desk.world.nodes[f.desk.world.last_created]["subject"]
        flat = store.flatten(f.desk.world)
        flat[subject, "title"] = "Two"
        raw = f.log.path.read_bytes()
        records = [json.loads(line) for line in raw.splitlines()]
        records[-1]["state"] = store.digest(flat)
        alternate = b"".join((json.dumps(r, ensure_ascii=False) + "\n").encode("utf-8")
                             for r in records).replace(b'"One"', b'"Two"')
        self.assertEqual(len(alternate), len(raw))
        replacement = f.log.path.with_suffix(".replacement")
        replacement.write_bytes(alternate)
        self.assertEqual(store.Log(replacement).flat()[0][subject, "title"], "Two")
        self.assertEqual(store.Log(replacement).head()[1], store.digest(flat))
        os.replace(replacement, f.log.path)
        return f, subject

    def test_reviewer_A2_recovery_refuses_valid_same_length_replacement(self):
        f, _ = self.replacement_fixture()
        session = f.session()
        with self.assertRaises(atomic_world.UnknownCommit):
            with session:
                atomic_world.status(session, "cache-replacement-check")

    def test_ordinary_begin_does_not_reuse_old_facts_after_replacement(self):
        # begin's weak world mark also names path/size: head() must invalidate
        # the cache before that quick path can use it.
        f, subject = self.replacement_fixture()
        ctx = store.begin(f.desk, f.path)
        self.assertIsNone(ctx.quick)
        self.assertIn(subject, ctx.outside_touched)


if __name__ == "__main__":
    unittest.main(verbosity=2)
