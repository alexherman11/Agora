# health: room test
"""Mock-only model selection, admission and durable receipt regressions."""
import json
import os
import re
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

HERE = Path(__file__).resolve().parent
os.environ.setdefault("HOUSE_CLAUDE", "claude")
os.environ["DESKD"] = "off"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "window-lab"))
sys.path.insert(0, str(HERE.parents[1] / "codex-residents"))
import agora_tmp  # noqa: E402
import codex_worker  # noqa: E402
import house  # noqa: E402,F401
import roomworld  # noqa: E402
import worker_selection as selection  # noqa: E402
import workshop  # noqa: E402

MODEL = "claude-small-fixture"
CATALOG = [{"value": MODEL, "supportedEffortLevels": ["low", "medium"]}]
CFG = {"model": "claude-opus-5-5", "workers": "4",
       "worker_pool": "2 claude, 2 codex gpt-6-astra"}


class SelectionTests(unittest.TestCase):
    def test_request_is_distinct_and_exact(self):
        got = selection.resolve({"requested_model": MODEL, "requested_effort": "low",
                                 "actual_model": "wrong", "worker_model": "wrong"},
                                {}, "codex", "gpt-6-astra", CFG)
        self.assertEqual(got, {"provider": "claude", "model": MODEL, "effort": "low"})
        for name in ("haiku", "auto", "gpt-X", "../model"):
            with self.subTest(name=name), self.assertRaises(selection.Refused):
                selection.provider(name)

    def test_catalog_refuses_unavailable_and_unadvertised_effort(self):
        selection.validate_catalog(CATALOG, MODEL, "low")
        for name, level in (("claude-missing", "low"), (MODEL, "high")):
            with self.subTest(name=name), self.assertRaises(selection.Refused):
                selection.validate_catalog(CATALOG, name, level)
        with self.assertRaises(selection.Refused):
            selection.validate_catalog([{"value": MODEL}], MODEL, "low")

    def test_saved_model_provider_and_unknown_effort_are_fenced(self):
        saved = {"session": "old", "session_provider": "claude", "model": MODEL,
                 "effort": "low"}
        self.assertEqual(selection.resolve(
            {"requested_model": MODEL, "requested_effort": "low"},
            saved, "claude", MODEL, CFG)["effort"], "low")
        for props in ({"requested_model": "gpt-6-astra"},
                      {"requested_model": "claude-other"}, {"requested_effort": "medium"}):
            with self.subTest(props=props), self.assertRaises(selection.Refused):
                selection.resolve(props, saved, "claude", MODEL, CFG)
        saved.pop("effort")
        with self.assertRaises(selection.Refused):
            selection.resolve({"requested_effort": "low"}, saved, "claude", MODEL, CFG)

    def test_default_saved_effort_is_not_changed_by_global_settings(self):
        got = selection.resolve({}, {"session": "s", "model": MODEL, "effort": "low"},
                                "claude", MODEL, {"worker_claude_effort": "high"})
        self.assertEqual(got["effort"], "low")

    def test_ultra_does_not_admit_delegation(self):
        with self.assertRaises(selection.Refused):
            selection.resolve({"requested_effort": "ultra"}, {}, "codex", "gpt-6-astra", {})

    def test_initialize_only_claude_metadata_no_user_or_tools(self):
        response = {"type": "control_response", "response": {
            "subtype": "success", "request_id": "agora-model-capabilities",
            "response": {"models": CATALOG}}}
        results = [SimpleNamespace(returncode=0, stdout='{"loggedIn":true,"email":"ignored"}'),
                   SimpleNamespace(returncode=0, stdout=json.dumps(response))]
        with mock.patch.object(selection.subprocess, "run", side_effect=results) as run:
            self.assertEqual(selection.claude_catalog("claude", ".", {}), CATALOG)
        self.assertEqual(run.call_count, 2)
        cmd = run.call_args.args[0]
        msg = json.loads(run.call_args.kwargs["input"])
        self.assertEqual(msg["type"], "control_request")
        self.assertEqual(msg["request"]["subtype"], "initialize")
        self.assertEqual(cmd[cmd.index("--tools") + 1], "")
        self.assertIn("--no-session-persistence", cmd)
        self.assertNotIn("--resume", cmd)

    def test_missing_auth_and_malformed_catalog_fail_without_inference(self):
        for stdout in ('{"loggedIn":false}', "not-json", "[]"):
            with mock.patch.object(selection.subprocess, "run", return_value=
                                   SimpleNamespace(returncode=0, stdout=stdout)) as run:
                with self.assertRaises(selection.Refused):
                    selection.claude_catalog("claude", ".", {})
                self.assertEqual(run.call_count, 1)
        with mock.patch.object(selection.subprocess, "run", return_value=
                               SimpleNamespace(returncode=0, stdout='{"loggedIn":true}')):
            with self.assertRaises(selection.Refused):
                selection.claude_catalog("claude", ".", {})
        for stdout in ('[]', '{"type":"control_response","response":"broken"}'):
            results = [SimpleNamespace(returncode=0, stdout='{"loggedIn":true}'),
                       SimpleNamespace(returncode=0, stdout=stdout)]
            with mock.patch.object(selection.subprocess, "run", side_effect=results):
                with self.assertRaises(selection.Refused):
                    selection.claude_catalog("claude", ".", {})

    def test_receipts_keep_numeric_usage_only_and_unknown_effort_unknown(self):
        self.assertEqual(selection.receipt({"type": "system", "subtype": "init",
                                            "model": MODEL}), {"model": MODEL})
        self.assertEqual(selection.receipt({
            "type": "result", "usage": {"input_tokens": 5, "text": "private"},
            "modelUsage": {MODEL: {"cacheReadInputTokens": 2}}, "total_cost_usd": 0.01,
            "result": "private"}),
            {"usage": {"input_tokens": 5}, "modelUsage": {
                MODEL: {"cacheReadInputTokens": 2}}, "total_cost_usd": 0.01})
        self.assertEqual(selection.receipt({"type": "codex_event",
            "method": "thread/tokenUsage/updated", "data": {
                "tokenUsage": {"total": {"totalTokens": 12}}, "text": "private"}}),
            {"tokenUsage": {"total": {"totalTokens": 12}}})


class WorkshopTests(unittest.TestCase):
    def setUp(self):
        self.desk, room = roomworld.build(say=False)
        self.world = self.desk.world
        self.board = room.BOARD
        self.root = Path(agora_tmp.directory("selection-test-"))
        test = self

        class House:
            world = "selection-inmemory"
            fake = None
            claude = "claude.exe"
            dir = test.root / "house"

            def load(self):
                return test.world

            def act(self, who, line):
                from desk import split_batch
                return test.say(who, *split_batch(line))

        self.host = House()
        self.host.dir.mkdir()
        self.ws = workshop.Workshop(self.host)
        self.ws.land = mock.Mock()
        self.procs = []

        def popen(*args, **kwargs):
            kwargs["stderr"].close()  # fake process never inherits this handle
            proc = mock.MagicMock()
            proc.pid = 4500 + len(self.procs)
            proc.poll.return_value = None
            self.procs.append((args[0], proc))
            return proc

        for patch in (
            mock.patch.object(workshop, "TREES", self.root / "trees"),
            mock.patch.object(workshop, "git",
                              return_value=SimpleNamespace(returncode=0, stdout="", stderr="")),
            mock.patch.object(workshop.Workshop, "real_tree", return_value=True),
            mock.patch("door.copy_locked", return_value=None),
            mock.patch.object(workshop.subprocess, "Popen", side_effect=popen),
            mock.patch.object(workshop.threading, "Thread"),
            mock.patch.object(selection, "claude_catalog", return_value=CATALOG),
        ):
            patch.start()
            self.addCleanup(patch.stop)

    def say(self, actor, *lines):
        w, d = self.world, self.desk
        w.me = actor
        d.seen, d.open, d.last_event_seen = d._per.setdefault(actor, ({}, {w.root}, 0))
        d._window = ""
        out = ""
        for line in lines:
            result = d.dispatch("desk", {"line": line.strip(), "whole": True})
            self.assertFalse(result.get("error"), result)
            out = result.get("text", "")
        return out

    def card(self, **props):
        out = self.say("pike", f"look {self.board} :1",
                       f'do create {self.board} kind=task title="Mock task" owner=pike')
        cid = re.findall(r"created (a\d+)", out)[-1]
        self.setp(cid, commission="asked", **props)
        return cid

    def setp(self, cid, **props):
        self.say("pike", f"look {cid} :1", f"do prop {cid} " +
                 " ".join(f"{k}={json.dumps(v)}" for k, v in props.items()))

    def props(self, cid):
        return self.world.subjects[self.world.nodes[cid]["subject"]]["props"]

    def test_four_requested_models_in_same_pool_never_fifth(self):
        cards = [self.card(requested_model=MODEL, requested_effort="low") for _ in range(5)]
        self.ws.step(self.world, CFG)
        self.assertEqual(len(self.procs), 4)
        for cid, (cmd, proc) in zip(cards[:4], self.procs, strict=True):
            self.assertEqual(cmd[cmd.index("--model") + 1], MODEL)
            self.assertEqual(cmd[cmd.index("--effort") + 1], "low")
            self.assertTrue(proc.stdin.write.called)
            self.assertNotIn("--resume", cmd)
            self.assertEqual(self.props(cid)["resolved_model"], MODEL)
            self.assertEqual(self.props(cid)["actual_model"], "")
            self.assertIsNone(self.ws.workers[cid].builder)
        self.assertEqual(self.props(cards[4])["commission"], "asked")

    def test_refusal_is_durable_quiet_and_correctable(self):
        cid = self.card(requested_model="claude-unavailable", requested_effort="low")
        self.ws.step(self.world, CFG)
        self.assertEqual(len(self.procs), 0)
        count = len(self.world.events)
        self.ws.step(self.world, CFG)
        self.assertEqual(len(self.world.events), count)
        self.assertEqual(self.props(cid)["selection_status"], "refused")
        self.setp(cid, requested_model=MODEL)
        self.ws.step(self.world, CFG)
        self.assertEqual(len(self.procs), 1)
        self.assertEqual(self.props(cid)["selection_status"], "resolved")

    def test_explicit_retry_checks_metadata_once_without_automatic_polling(self):
        cid = self.card(requested_model=MODEL, requested_effort="low")
        with mock.patch.object(selection, "claude_catalog", side_effect=
                               selection.Refused("metadata temporarily unavailable")) as catalog:
            self.ws.step(self.world, CFG)
            self.ws.step(self.world, CFG)
            self.assertEqual(catalog.call_count, 1)
        self.setp(cid, requested_retry="retry-1")
        self.ws.step(self.world, CFG)
        self.assertEqual(len(self.procs), 1)
        self.assertEqual(self.props(cid)["selection_status"], "resolved")

    def test_bad_request_does_not_block_other_card(self):
        bad = self.card(requested_model="haiku")
        good = self.card(requested_model=MODEL, requested_effort="low")
        self.ws.step(self.world, CFG)
        self.assertEqual(self.props(bad)["selection_status"], "refused")
        self.assertIn(good, self.ws.workers)
        self.assertEqual(len(self.procs), 1)

    def test_compatible_saved_request_resumes_without_global_effort_change(self):
        cid = self.card(requested_model=MODEL, requested_effort="low")
        self.ws.step(self.world, CFG)
        wk = self.ws.workers[cid]
        wk.state["session"] = "kept"
        wk.save()
        wk.busy = False
        wk.proc = None  # simulate house replacement; fake runtime only
        wk.start(CFG["model"], self.host.world, None)
        cmd = self.procs[-1][0]
        self.assertEqual(cmd[cmd.index("--resume") + 1], "kept")
        self.assertEqual(cmd[cmd.index("--effort") + 1], "low")
        self.assertEqual(CFG.get("worker_claude_effort"), None)

    def test_incompatible_restart_preserves_session_and_pending_text(self):
        cid = self.card(requested_model=MODEL, requested_effort="low")
        self.ws.step(self.world, CFG)
        wk = self.ws.workers[cid]
        wk.state["session"] = "kept"
        wk.state["pending"] = {"carry": "untouched", "delivered": False}
        wk.busy, wk.proc = False, None
        wk.save()
        self.setp(cid, requested_effort="medium")
        self.ws.workers.clear()
        before = len(self.procs)
        self.ws.step(self.world, CFG)
        saved = self.ws.card_state(cid)
        self.assertEqual(len(self.procs), before)
        self.assertEqual(saved["session"], "kept")
        self.assertEqual(saved["pending"]["carry"], "untouched")
        self.assertEqual(self.props(cid)["selection_status"], "refused")

    def test_effort_only_request_uses_chosen_provider_and_real_catalog(self):
        cid = self.card(requested_effort="low")
        catalog = [{"value": CFG["model"], "supportedEffortLevels": ["low", "medium"]}]
        with mock.patch.object(selection, "claude_catalog", return_value=catalog):
            self.ws.step(self.world, CFG)
        self.assertEqual(self.props(cid)["resolved_model"], CFG["model"])
        self.assertEqual(self.props(cid)["resolved_effort"], "low")
        self.assertEqual(self.props(cid)["requested_effort"], "low")

    def test_codex_request_keeps_model_and_effort_in_command(self):
        cid = self.card(requested_model="gpt-6-astra", requested_effort="low")
        self.ws.step(self.world, CFG)
        cmd = self.procs[0][0]
        self.assertEqual(Path(cmd[1]).name, "codex_worker.py")
        self.assertEqual(cmd[cmd.index("--model") + 1], "gpt-6-astra")
        self.assertEqual(cmd[cmd.index("--reasoning") + 1], "low")
        self.assertEqual(self.props(cid)["actual_model"], "")

    def test_busy_changed_request_cannot_consume_or_send_next_news(self):
        cid = self.card(requested_model=MODEL, requested_effort="low")
        self.ws.step(self.world, CFG)
        wk = self.ws.workers[cid]
        wk.events.put({"type": "system", "subtype": "init", "model": MODEL,
                       "session_id": "same-context"})
        self.setp(cid, requested_effort="medium")
        wk.events.put({"type": "result", "result": "done"})
        before = self.procs[0][1].stdin.write.call_count
        with mock.patch.object(self.ws, "heard") as heard:
            self.ws.step(self.world, CFG)
        self.assertFalse(heard.called)
        self.assertEqual(self.procs[0][1].stdin.write.call_count, before)
        self.assertEqual(wk.state["session"], "same-context")
        self.assertEqual(wk.state["effort"], "low")
        self.assertEqual(self.props(cid)["selection_status"], "refused")
        self.setp(cid, requested_effort="low")
        self.assertTrue(self.ws.selection_allowed(
            cid, self.world.subjects[self.world.nodes[cid]["subject"]], CFG, wk))
        self.assertEqual(self.props(cid)["selection_status"], "observed")

    def test_actual_receipt_unknown_effort_and_numeric_usage_saved(self):
        cid = self.card(requested_model=MODEL, requested_effort="low")
        self.ws.step(self.world, CFG)
        wk = self.ws.workers[cid]
        wk.events.put({"type": "system", "subtype": "init", "model": MODEL, "session_id": "s"})
        wk.events.put({"type": "result", "usage": {"input_tokens": 3}, "result": "done"})
        wk.turns_ended()
        self.assertEqual(self.props(cid)["actual_model"], MODEL)
        self.assertEqual(self.props(cid)["actual_effort"], "")
        self.assertEqual(wk.state["selection"]["usage"], {"usage": {"input_tokens": 3}})
        count = len(self.world.events)
        wk.selection_props(actual_model=MODEL, actual_effort="", selection_status="observed")
        self.assertEqual(len(self.world.events), count)

    def test_stream_arrivals_during_receipts_wait_for_validation(self):
        cid = self.card(requested_model=MODEL, requested_effort="low")
        self.ws.step(self.world, CFG)
        wk = self.ws.workers[cid]
        incoming = wk.events
        wk.events.put({"type": "system", "subtype": "init", "model": MODEL, "session_id": "s"})
        interceptor = mock.Mock()
        self.host.host_route = SimpleNamespace(intercept=interceptor)

        def arrivals(*args):
            if args[0] == "runtime_receipt":
                incoming.put({"type": "system", "subtype": "init", "model": "claude-other"})
                incoming.put({"type": "assistant", "message": {
                    "content": [{"type": "text", "text": "> host-route {}"}]}})
                incoming.put({"type": "result", "result": "wrong runtime"})

        with mock.patch.object(wk, "log", side_effect=arrivals):
            self.assertEqual(wk.turns_ended(), [])
        self.assertIs(wk.events, incoming)
        self.assertEqual(wk.turns_ended()[0]["error"], "runtime_selection_mismatch")
        interceptor.assert_not_called()

    def test_runtime_mismatch_is_not_a_successful_result_or_repeated_failure(self):
        cid = self.card(requested_model=MODEL, requested_effort="low")
        self.ws.step(self.world, CFG)
        wk = self.ws.workers[cid]
        wk.events.put({"type": "system", "subtype": "init",
                       "model": "claude-other", "session_id": "s"})
        wk.events.put({"type": "result", "result": "not approved"})
        ended = wk.turns_ended()
        self.assertEqual(ended[0]["error"], "runtime_selection_mismatch")
        self.assertEqual(wk.turns_ended(), [])
        wk.busy = False
        self.setp(cid, commission="ready")
        self.ws.step(self.world, CFG)
        self.ws.land.assert_not_called()
        self.assertFalse(self.ws.selection_allowed(
            cid, self.world.subjects[self.world.nodes[cid]["subject"]], CFG, wk))
        self.setp(cid, requested_model="", requested_effort="")
        self.assertFalse(self.ws.selection_allowed(
            cid, self.world.subjects[self.world.nodes[cid]["subject"]], CFG, wk))
        starts = len(self.procs)
        recovered = workshop.Worker(self.host, cid, wk.tree, wk.branch, "pike")
        recovered.start(CFG["model"], self.host.world, None)
        self.assertEqual(len(self.procs), starts)

    def test_adapter_selection_refusal_is_not_retried_or_recounted(self):
        cid = self.card(requested_model="gpt-6-astra", requested_effort="low")
        self.ws.step(self.world, CFG)
        wk = self.ws.workers[cid]
        wk.events.put({"type": "result", "is_error": True, "subtype": "SelectionRefused",
                       "result": "Requested model unavailable; no substitution"})
        wk.events.put({"type": "exit", "code": 1})
        self.ws.step(self.world, CFG)
        count, starts = len(self.world.events), len(self.procs)
        for _ in range(3):
            self.ws.step(self.world, CFG)
        self.assertEqual(len(self.world.events), count)
        self.assertEqual(len(self.procs), starts)
        self.assertEqual(self.props(cid)["selection_status"], "refused")
        self.setp(cid, requested_retry="retry-1")
        self.ws.step(self.world, CFG)
        self.assertEqual(len(self.procs), starts + 1)
        # Adapter received text, but no model thread existed. Retry must include
        # the full pending commission, not refer to nonexistent earlier context.
        message = json.loads(self.procs[-1][1].stdin.write.call_args.args[0])
        self.assertIn("Mock task", message["message"]["content"][0]["text"])

    def test_different_builder_context_is_not_adopted_for_request(self):
        cid = self.card(requested_model=MODEL, requested_effort="low")
        wk = workshop.Worker(self.host, cid, self.root, f"worker/{cid}", "pike")
        wk.builder = "builder-1"
        builder = workshop.Builder(self.host, wk.builder)
        builder.state = {"session": "other-card", "provider": "claude",
                         "model": MODEL, "effort": "medium"}
        builder.save()
        wk.start(CFG["model"], self.host.world, None)
        self.assertEqual(self.procs, [])
        self.assertEqual(builder.state["session"], "other-card")
        self.assertEqual(self.props(cid)["selection_status"], "refused")

    def test_explicit_requests_never_quota_switch(self):
        cid = self.card(requested_model=MODEL, requested_effort="low")
        self.ws.step(self.world, CFG)
        wk = self.ws.workers[cid]
        wk.state["retry_kind"] = "quota"
        wk.state["retry_at"] = 99999999999
        wk.busy = False
        wk.proc = None
        wk.save()
        self.assertFalse(self.ws.limit_handoffs(self.world, CFG))
        self.assertEqual(self.props(cid)["worker_provider"], "claude")


class CodexTests(unittest.TestCase):
    @staticmethod
    def metadata():
        return SimpleNamespace(model="gpt-fixture", model_dump=lambda **kw: {
            "model": "gpt-fixture", "supportedReasoningEfforts": [
                {"reasoningEffort": "low"}, {"reasoningEffort": "ultra"}]})

    def test_runtime_effort_validated_before_thread_and_turn(self):
        args = SimpleNamespace(model="gpt-fixture", reasoning="high",
                               prompt_file="fixture", mcp_config="fixture", resume=None)
        client = mock.MagicMock()
        client.model_list.return_value.data = [self.metadata()]
        with (mock.patch.object(codex_worker, "runtime_config"),
              mock.patch.object(codex_worker, "CodexClient") as factory,
              mock.patch.object(codex_worker, "child_job"),
              mock.patch.object(codex_worker, "require_subscription") as auth,
              mock.patch.object(codex_worker.threading, "Thread"),
              mock.patch.object(Path, "read_text", return_value="fixture prompt")):
            factory.return_value.__enter__.return_value = client
            with self.assertRaisesRegex(RuntimeError, "effort unavailable"):
                codex_worker.serve(args)
        auth.assert_called_once_with(client)
        client.initialize.assert_called_once()
        client.model_list.assert_called_once_with(True)
        client.request.assert_not_called()
        client.turn_start.assert_not_called()

    def test_codex_unavailable_and_ultra_refused(self):
        for model, effort in (("gpt-missing", "low"), ("gpt-fixture", "ultra")):
            with self.subTest(model=model), self.assertRaises(RuntimeError):
                codex_worker.validate_selection([self.metadata()], model, effort)
        codex_worker.validate_selection([self.metadata()], "gpt-fixture", "low")


if __name__ == "__main__":
    unittest.main()
