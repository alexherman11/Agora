# health: room test
"""Install seed notes in a scratch world and execute their real verb bodies."""

import unittest

import task_flow
import task_flow_verbs
import test_task_flow


class WorkflowVerbTests(unittest.TestCase):
    run_line = test_task_flow.TaskFlowTests.run_line

    def setUp(self):
        test_task_flow.TaskFlowTests.setUp(self)
        for line in task_flow_verbs.lines(self.r.BOARD):
            self.run_line("juniper", line)

    def props(self):
        return self.w.subjects[self.w.nodes[self.card]["subject"]]["props"]

    def test_assign_accept_and_guard(self):
        self.run_line("juniper", f"assign-task {self.card} sable")
        self.assertEqual(self.props()["owner"], "sable")
        self.assertEqual(self.props()["lead"], "juniper")
        self.run_line("pike", f"accept-task {self.card}")
        self.assertNotIn("accepted_by", self.props())
        self.assertEqual(self.props()["status"], "asked")
        self.run_line("sable", f"accept-task {self.card}")
        self.assertEqual(self.props()["accepted_by"], "sable")
        self.assertEqual(task_flow.notices(self.w, self.w.events[-1])[0]["recipient"], "juniper")
        self.run_line("juniper", f"assign-task {self.card} pike")
        self.assertNotIn("accepted_by", self.props())

    def test_block_missing_or_empty_fields_has_no_partial_state(self):
        before = dict(self.props())
        with self.assertRaisesRegex(AssertionError, "needs 4 word"):
            self.run_line("pike", f'block-task {self.card} "Need browser" sable')
        self.assertEqual(self.props(), before)
        self.run_line("pike", f'block-task {self.card} "Need browser" "" "Browser available"')
        self.assertEqual(self.props(), before)
        self.run_line("pike", f'block-task {self.card} "Need browser" sable "Browser available"')
        self.assertEqual(self.props()["status"], "blocked")
        self.assertEqual(self.props()["resume_when"], "Browser available")
        notices = task_flow.notices(self.w, self.w.events[-1])
        self.assertEqual({n["recipient"] for n in notices}, {"juniper", "sable"})

    def test_worker_update_and_yield(self):
        self.run_line(
            "pike",
            f'worker-update {self.card} checkpoint "Tests pass; browser check next" "note:checks"',
        )
        notices = task_flow.notices(self.w, self.w.events[-1])
        self.assertEqual(notices[0]["summary"], "Tests pass; browser check next")
        self.assertEqual(notices[0]["evidence"], "note:checks")
        before = dict(self.props())
        self.run_line("pike", f'worker-update {self.card} nonsense "Wrong milestone" "note:checks"')
        self.assertEqual(self.props(), before)
        self.run_line("pike", f"yield-work {self.card}")
        self.assertEqual(self.props()["commission"], "yielded")


if __name__ == "__main__":
    unittest.main()
