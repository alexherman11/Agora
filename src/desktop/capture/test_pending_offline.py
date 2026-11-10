"""Capture reservation regressions; fake Desk only, no windows/files/account calls."""
import argparse
import re
import unittest
from unittest.mock import Mock, patch

import capture as C


class Drafts:
    def __init__(self):
        self.current = "a1"
        self.rows = {"a1": ([], []), "a2": ([], [])}
        self.refuse = False
        self.conflict_once = False
        self.writes = []

    def do(self, line):
        if line.startswith("find "):
            return True, f"  {self.current} note"
        if line.startswith("examine "):
            ctx, pending = self.rows[line.split()[1]]
            return True, f'context={" ".join(ctx)} pending={" ".join(pending)} · draft'
        if line.startswith("do prop "):
            if self.refuse:
                return False, "ERR write refused"
            if self.conflict_once:
                self.conflict_once = False
                return False, "ERR changed since your last look"
            draft = line.split()[2]
            ctx = re.search(r'context="([^"]*)"', line)[1].split()
            pending = re.search(r'pending="([^"]*)"', line)[1].split()
            self.rows[draft] = (ctx, pending)
            self.writes.append(line)
            return True, "ok"
        raise AssertionError(line)


class PendingTests(unittest.TestCase):
    def setUp(self):
        self.desk = Drafts()
        self.args = argparse.Namespace(draft="auto", who="fixture", do=self.desk.do)

    def mark(self):
        p = C.Pending(self.args)
        p.mark()
        self.assertTrue(p.admitted)
        return p

    def test_mark_before_delivery_then_atomic_replacement(self):
        p = self.mark()
        self.assertEqual(self.desk.rows["a1"], ([], [p.token]))
        self.assertTrue(C.deliver("cap-1", self.args, p)[0])
        self.assertEqual(self.desk.rows["a1"], (["cap-1"], []))

    def test_cancelled_token_never_delivers_to_next_words(self):
        p = self.mark()
        self.desk.rows["a1"] = ([], [])
        before = list(self.desk.writes)
        self.assertFalse(C.deliver("cap-1", self.args, p)[0])
        self.assertEqual(self.desk.rows["a1"], ([], []))
        self.assertEqual(self.desk.writes, before)

    def test_failed_mark_does_not_fall_back_to_new_draft(self):
        self.desk.refuse = True
        p = C.Pending(self.args)
        p.mark()
        self.desk.refuse = False
        self.desk.current = "a2"
        self.assertFalse(C.deliver("cap-1", self.args, p)[0])
        self.assertEqual(self.desk.rows["a2"], ([], []))
        self.assertEqual(self.desk.writes, [])

    def test_unknown_mark_does_not_deliver(self):
        p = C.Pending(self.args)
        p.marked = Mock()
        p.marked.wait.return_value = False
        self.assertFalse(C.deliver("cap-1", self.args, p)[0])
        self.assertEqual(self.desk.writes, [])

    def test_later_draft_does_not_receive_earlier_capture(self):
        p = self.mark()
        self.desk.current = "a2"
        self.assertTrue(C.deliver("cap-1", self.args, p)[0])
        self.assertEqual(self.desk.rows["a2"], ([], []))

    def test_two_out_of_order_deliveries_consume_only_own_token(self):
        a, b = self.mark(), self.mark()
        self.assertTrue(C.deliver("cap-2", self.args, b)[0])
        self.assertEqual(self.desk.rows["a1"], (["cap-2"], [a.token]))
        self.assertTrue(C.deliver("cap-1", self.args, a)[0])
        self.assertEqual(self.desk.rows["a1"], (["cap-2", "cap-1"], []))

    def test_capacity_failure_keeps_send_blocked(self):
        p = self.mark()
        ids = [f"cap-{i}" for i in range(8)]
        self.desk.rows["a1"] = (ids, [p.token])
        self.assertFalse(C.deliver("cap-9", self.args, p)[0])
        self.assertEqual(self.desk.rows["a1"], (ids, [p.token]))

    def test_explicit_cancel_preserves_other_reservations(self):
        a, b = self.mark(), self.mark()
        self.assertTrue(a.drop()[0])
        self.assertEqual(self.desk.rows["a1"], ([], [b.token]))
        self.assertFalse(C.deliver("cap-1", self.args, a)[0])

    def test_delivery_failure_leaves_reservation_visible(self):
        p = self.mark()
        with patch.object(C, "deliver", side_effect=RuntimeError("fake failure")), patch("builtins.print"):
            C.report("cap-1", {"rect": [0, 0, 10, 10], "native": "none",
                             "refs": [], "image_size": None}, {"kept": 0}, self.args, p)
        self.assertEqual(self.desk.rows["a1"], ([], [p.token]))

    def test_stale_write_is_re_read_before_delivery(self):
        p = self.mark()
        self.desk.conflict_once = True
        self.assertTrue(C.deliver("cap-1", self.args, p)[0])
        self.assertEqual(self.desk.rows["a1"], (["cap-1"], []))

    def test_duplicate_delivery_does_not_append_twice(self):
        p = self.mark()
        self.assertTrue(C.deliver("cap-1", self.args, p)[0])
        self.assertFalse(C.deliver("cap-1", self.args, p)[0])
        self.assertEqual(self.desk.rows["a1"], (["cap-1"], []))


if __name__ == "__main__":
    unittest.main()
