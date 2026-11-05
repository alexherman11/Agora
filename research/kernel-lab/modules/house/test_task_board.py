"""In-memory combined-board checks. No world, temp directories, Git or desktop."""
import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(LAB))
import task_board as B
from painter.arrangement import parse


def card(**facts):
    return dict({"id": "dk10", "title": "Repair dock", "who": "Sable", "lane": "Now"}, **facts)


def worker(**facts):
    return dict({"task": "dk10", "name": "Codex \u2014 Repair dock", "doing": "working",
                 "build_run": "current"}, **facts)


def builders(live=True, **facts):
    state = dict(run="current", phase="working", session="authenticated", turn_started="2026-11-04T01:00:01Z",
                 pid=123, **facts)
    return NS(rows=Mock(return_value=[worker()]), states={"dk10": state},
              children={"dk10": NS(alive=lambda: live, proc=NS(pid=123))})


class ProjectionTests(unittest.TestCase):
    def project(self, cards=None, pool=None, agents=None, settings=None):
        collections = {
            "rows taskboard-task": cards if cards is not None else [card(build_run="current")],
            "rows person": [dict(id="dk2", name="Sable"), dict(id="dk3", name="Pike"),
                            dict(id="dk4", name="Rowan")],
            "rows work-settings": settings or [],
        }
        see = Mock(side_effect=lambda line, use: dict(rows=collections[line]))
        pool = pool or NS(rows=Mock(return_value=[]), states={}, children={})
        pool.rows.reset_mock()
        out = B.rows(NS(see=see, hello={"for": "dk2"}), agents or {}, pool, "viewer")
        self.assertTrue(all(call.kwargs["use"] == "viewer" for call in see.call_args_list))
        pool.rows.assert_called_once_with({"use": "viewer"})
        return out

    def test_actual_authenticated_live_worker_is_running(self):
        row = self.project(pool=builders())[0]
        self.assertEqual((row["state_key"], row["executor"], row["lead"]), ("running", "Codex", "Sable"))
        self.assertEqual(row["execution"]["kind"], "authenticated-worker-turn")

    def test_saved_phase_and_owner_never_prove_execution(self):
        row = self.project([card(build_run="current", build_phase="working")])[0]
        self.assertEqual(row["state_key"], "queued")
        self.assertFalse(row["execution"])

    def test_dead_child_is_not_running(self):
        self.assertEqual(self.project(pool=builders(False))[0]["state_key"], "queued")

    def test_old_run_and_replaced_child_do_not_prove_execution(self):
        pool = builders()
        pool.states["dk10"]["run"] = "old"
        self.assertEqual(self.project(pool=pool)[0]["state_key"], "queued")
        pool.states["dk10"]["run"] = "current"
        pool.children["dk10"].proc.pid = 999
        self.assertEqual(self.project(pool=pool)[0]["state_key"], "queued")

    def test_missing_authentication_or_turn_start_is_not_running(self):
        for field in ("session", "turn_started"):
            with self.subTest(field=field):
                pool = builders()
                pool.states["dk10"][field] = ""
                self.assertEqual(self.project(pool=pool)[0]["state_key"], "queued")

    def test_received_result_cannot_reuse_the_previous_turn_evidence(self):
        pool = builders(result_received="2026-11-04T01:00:02Z")
        self.assertEqual(self.project(pool=pool)[0]["state_key"], "queued")

    def test_wrong_builder_name_does_not_prove_execution(self):
        self.assertEqual(self.project([card(build_run="current", builder="Other")],
                                     builders())[0]["state_key"], "queued")

    def test_hold_overrides_live_execution_and_authored_done(self):
        for hold in (dict(effect_state="unknown"), dict(task_held="yes"), dict(paused="yes"),
                     dict(authority="permission")):
            with self.subTest(hold=hold):
                row = self.project([card(build_run="current", lane="Done", **hold)], builders())[0]
                self.assertEqual(row["state_key"], "blocked")
                self.assertTrue(row["blocker"] and row["resolver"] and row["next_action"])
                self.assertFalse(row["execution"] or row["executor"])

    def test_named_cause_resolver_and_next_action(self):
        row = self.project([card(blocker="Needs dk3", resolver="dk3", next_action="Pike reviews")])[0]
        self.assertEqual((row["blocker"], row["resolver"], row["resolver_id"]),
                         ("Needs Pike", "Pike", "dk3"))
        self.assertEqual(row["next_action"], "Pike reviews")

    def test_recorded_scope_denial_remains_blocked(self):
        row = self.project([card(build_run="current", scope_blocked="yes",
                                 scope_resolver="dk2")], builders())[0]
        self.assertEqual((row["state_key"], row["resolver"]), ("blocked", "Sable"))
        self.assertIn("handoff", row["next_action"])
        self.assertFalse(row["execution"])

    def test_existing_manager_scope_is_assessed_without_writing_it(self):
        agent = NS(person="dk4", cfg={"role": "manager"})
        with patch("manager.permit", side_effect=RuntimeError("outside manager approval")) as permit:
            row = self.project([card(who="Rowan")], agents={"rowan": agent})[0]
            self.assertEqual(row["state_key"], "blocked")
            self.assertEqual(row["blocker"], "outside manager approval")
            permit.assert_called_once()

    def test_delivery_phases_remain_visible_without_claiming_execution(self):
        for phase, key in (("received", "review"), ("reviewed", "review"),
                           ("landed", "activation"), ("reviewing", "review"), ("landing", "activation")):
            with self.subTest(phase=phase):
                row = self.project([card(build_phase=phase)])[0]
                self.assertEqual(row["state_key"], key)
                self.assertTrue(row["resolver"] and row["next_action"])
                self.assertFalse(row["execution"])

    def test_restart_uncertainty_has_resolver_and_next_step(self):
        row = self.project([card(build_phase="recovery-needed", build_detail="Reconcile retained child")])[0]
        self.assertEqual(row["state_key"], "blocked")
        self.assertEqual(row["blocker"], "Reconcile retained child")
        self.assertTrue(row["resolver"] and row["next_action"])

    def test_state_order_is_running_queued_blocked_delivery_done(self):
        cards = [card(id="dk15", lane="Done"), card(id="dk14", build_phase="landed"),
                 card(id="dk13", build_phase="received"), card(id="dk12", blocker="Needs review"),
                 card(id="dk11", lane="Later", priority="urgent"), card(build_run="current", priority="low")]
        rows = self.project(cards, builders())
        self.assertEqual([r["state_key"] for r in rows],
                         ["running", "queued", "blocked", "review", "activation", "done"])

    def test_done_history_and_cancelled_are_authored_states_not_execution(self):
        rows = self.project([card(lane="Done"), card(id="dk11", status="cancelled")])
        self.assertEqual([r["state_key"] for r in rows], ["done", "cancelled"])
        self.assertTrue(all(not r["execution"] for r in rows))

    def test_cfg_task_and_busy_owner_are_not_task_execution_evidence(self):
        agent = NS(person="dk2", name="Sable", cfg={"task": "dk10"}, turn={},
                   busy=True, child=NS(alive=lambda: True))
        self.assertEqual(self.project(agents={"sable": agent})[0]["state_key"], "queued")

    def test_resident_execution_requires_current_task_claim_and_evidence(self):
        agent = NS(person="dk2", name="Sable", cfg={}, busy=True, child=NS(alive=lambda: True),
                   turn=dict(task="dk10", task_claim="claim", execution_started="now"))
        row = self.project([card(current_executor="dk2", executor_claim="claim")],
                           agents={"sable": agent})[0]
        self.assertEqual((row["state_key"], row["executor"]), ("running", "Sable"))

    def test_viewer_visibility_bounds_worker_and_task_join(self):
        pool = builders()
        self.assertEqual(self.project([], pool), [])

    def test_read_refusal_is_not_an_empty_board(self):
        with self.assertRaisesRegex(RuntimeError, "not visible"):
            B.rows(NS(see=lambda *a, **kw: {"refused": "not visible"}), {}, None, "viewer")

    def test_only_house_owned_settings_change_words(self):
        other = dict(kind="work-settings", made_by="dk3", board_queued="Hijacked")
        own = dict(kind="work-settings", made_by="dk2", board_queued="Ready")
        self.assertEqual(self.project(settings=[other])[0]["state"], "Queued")
        row = self.project(settings=[other, own])[0]
        self.assertEqual((row["state"], row["state_key"]), ("Ready", "queued"))


class WiringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = LAB / "apps/work/install.py"
        spec = importlib.util.spec_from_file_location("task_work_install_check", path)
        cls.installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.installer)

    def test_lens_uses_read_only_board_and_stable_state_keys(self):
        tree = parse((LAB / "apps/work/task-work.lens").read_text(encoding="utf-8"))
        self.assertEqual(tree["root"]["settings"]["board"], "true")
        self.assertEqual(tree["root"]["children"][0]["query"], 'reading:"house.board" as t')
        self.assertEqual(tree["work-line"]["settings"]["stateKey"], "$t.state_key")
        self.assertIn('reading:"house.active"', (LAB / "apps/work/work.lens").read_text(encoding="utf-8"))

    def test_widget_wiring_and_app_are_additive(self):
        I = self.installer
        door = NS(rows=lambda kind, **kw: [dict(id="widget", on="")] if kind == "widget" else [],
                  say=Mock(return_value={}))
        with patch.object(I.painter, "upsert", return_value="widget") as upsert, \
                patch.object(I.painter, "widget_source", return_value="reviewed painter"), \
                patch.object(I.painter, "app") as app:
            self.assertEqual(I.combined_widget(door), "widget")
            self.assertEqual(upsert.call_args.args[1:3], ("widget", "task-work"))
            self.assertEqual(upsert.call_args.kwargs["component_lens"], "task-work")
            self.assertIn("house.board", I.BOARD_GRANTS.split())
            self.assertIn("house.active", I.GRANTS.split())
            self.assertTrue(any("only=kind:work-view" in c.args[0] for c in door.say.call_args_list))
            app.assert_called_once_with(door, "task-work", "Tasks & work", "task-work")

    def test_matching_widget_does_not_toggle_or_regrant(self):
        I = self.installer
        door = NS(rows=lambda kind, **kw: [dict(id="widget", on="yes")] if kind == "widget"
                  else [dict(words=I.BOARD_GRANTS)], say=Mock())
        with patch.object(I.painter, "upsert", return_value="widget"), \
                patch.object(I.painter, "widget_source", return_value="reviewed painter"), \
                patch.object(I.painter, "app"):
            I.combined_widget(door)
            door.say.assert_not_called()

    def test_schema_accepts_the_combined_lens_settings(self):
        import json
        I = self.installer
        schema = json.loads(I.COMPONENTS["work-line"]["settings"])
        for field in ("lead", "executor", "stateKey", "resolver", "delivery", "acceptance"):
            self.assertIn(field, schema)
        self.assertEqual(json.loads(I.COMPONENTS["work-overview"]["settings"])["board"]["type"], "boolean")

    def test_installer_keeps_old_work_and_adds_combined_lens_widget_and_app(self):
        I = self.installer
        settings = dict(id="settings", kind="work-settings", made_by="dk2", **B.DEFAULTS)
        def rows(kind, **kv):
            if kind == "widget":
                return [dict(id=kv["name"] + "-id", on="yes")]
            if kind == "grant":
                words = I.BOARD_GRANTS if kv["to"] == "task-work-id" else I.GRANTS
                return [dict(words=words)]
            if kind == "work-view":
                return [dict(id="private-view")]
            if kind == "work-settings":
                return [settings]
            return []
        door = NS(rows=Mock(side_effect=rows), say=Mock())
        with patch.object(I, "components"), \
                patch.object(I.painter, "upsert", side_effect=lambda d, k, n, **kw: n + "-id") as upsert, \
                patch.object(I.painter, "widget_source", return_value="reviewed painter"), \
                patch.object(I.painter, "app") as app:
            result = I.install(door)
            self.assertEqual(result["widget"], "work-id")
            self.assertEqual(result["combined_widget"], "task-work-id")
            self.assertEqual(result["combined_lens"], "task-work-id")
            self.assertEqual({c.args[2] for c in upsert.call_args_list if c.args[1] == "lens"},
                             {"work", "task-work"})
            self.assertEqual({c.args[1] for c in app.call_args_list}, {"work", "task-work"})
            door.say.assert_not_called()  # Idempotent setup leaves existing facts alone.


if __name__ == "__main__":
    unittest.main(verbosity=2)
