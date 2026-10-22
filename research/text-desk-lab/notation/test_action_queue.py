# health: room test
"""a9377: isolated in-memory worlds only; never loads a live/session world or a browser."""
import copy
import json
import unittest
from unittest.mock import patch

import action_queue
import lens_ir
import persons
import roomworld
import scene
from world import Refusal


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.d, self.rooms = roomworld.build(say=False)
        self.w = self.d.world
        self.say("alex", "person begin")
        self.alex = persons.today(self.w, "alex")
        self.juniper = persons.today(self.w, "juniper")
        self.policy = self.make("note", "Policy", action_recipient=self.alex,
                                action_designs="prop:fixture_design=waiting,-prop:fixture_answered",
                                action_reviews="tag:fixture_review", action_group_later="prop:fixture_defer=later",
                                action_review_later="prop:fixture_review=later",
                                action_question_news="prop:fixture_closed=yes",
                                action_design_label="Design decision", action_review_label="Review")
        self.target = self.make("note", "A shared target")
        self.chat = self.make("chat", "Questions", talk_of=self.target)

    def say(self, actor, *lines, refuse=False):
        self.w.me = actor
        # Freshness remains real: reads are explicit, no auto-read before the tested action.
        for line in lines:
            result = self.d.dispatch("desk", {"line": line, "whole": True})
            if refuse:
                return result
            self.assertNotIn("error", result, (line, result))
        return result.get("text", "")

    def make(self, kind, title, **props):
        tail = " ".join(f"{k}={json.dumps(v)}" for k, v in props.items())
        self.say("juniper", f"look {self.w.root} :1",
                 f"do create {self.w.root} kind={kind} title={json.dumps(title)} {tail}")
        return self.w.last_created

    def prop(self, target=None, **props):
        target = target or self.target
        tail = " ".join(f"{k}={json.dumps(v)}" for k, v in props.items())
        self.say("juniper", f"look {target} :3", f"do prop {target} {tail}")

    def ask(self, kind="question", actor="juniper", to="alex", chat=None, **fields):
        chat = chat or self.chat
        fields.update(mark="ask")
        if kind:
            fields["request_kind"] = kind
        tail = " ".join(f"{k}={json.dumps(v)}" for k, v in fields.items())
        self.say(actor, f"read {chat}", f'do append {chat} line="A request?" to={to} {tail}')
        return self.w.subjects[self.w.subject_of(chat)]["lines"][-1]["id"]

    def reply(self, root=None, actor="alex", chat=None, **fields):
        chat = chat or self.chat
        if root:
            fields["reply_to"] = root
        tail = " ".join(f"{k}={json.dumps(v)}" for k, v in fields.items())
        self.say(actor, f"read {chat}", f'do append {chat} line="A reply" to=juniper {tail}')
        return self.w.subjects[self.w.subject_of(chat)]["lines"][-1]["id"]

    def native(self, actor="juniper", to="alex", target=None):
        self.say(actor, f'ask to={to} "May I?" about={target or self.target}')
        return self.w.events[-1]["target"]

    def groups(self, counted=None, recipient="alex"):
        query = f"actions:{recipient}:{self.policy}"
        return scene.rows(self.d, query + (f" counted={counted}" if counted else ""))

    def reasons(self, group=None, recipient="alex"):
        group = group or self.groups()[0]
        return scene.rows(self.d, f"action-reasons:{recipient}:{self.policy}:{group['key']}")

    def all_reasons(self, recipient="alex"):
        return [r for g in self.groups(recipient=recipient) for r in self.reasons(g, recipient)]

    def test_dual_design_review_one_group_two_reasons_world_labels(self):
        self.prop(fixture_design="waiting")
        self.say("juniper", f"read {self.target}", f"do tag {self.target} add=fixture_review")
        groups = self.groups("yes")
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["reason_count"], 2)
        reasons = self.reasons(groups[0])
        self.assertEqual({r["kind"] for r in reasons}, {"design", "review"})
        self.assertEqual({r["label"] for r in reasons}, {"Design decision", "Review"})
        self.assertEqual(len({r["request_key"] for r in reasons}), 2)

    def test_two_questions_same_target_each_own_reply_and_evidence(self):
        one, two = self.ask(), self.ask()
        reply = self.reply(one)
        r = {r["source"]: r for r in self.all_reasons()}
        self.assertEqual(r[one]["resolution_evidence"], reply)
        self.assertEqual(r[two]["resolution_state"], "open")
        self.assertEqual(self.groups("yes")[0]["reason_count"], 1)

    def test_unrelated_later_and_third_party_exact_reply_do_not_answer(self):
        root = self.ask()
        self.reply()
        child = self.reply(root, actor="pike")
        self.reply(child)  # A descendant is not a reply_to of the requested root.
        self.assertEqual(self.all_reasons()[0]["resolution_state"], "open")
        self.assertEqual(self.all_reasons()[0]["resolution_evidence"], "")

    def test_same_chat_no_context_is_not_automatic_group(self):
        chat = self.make("chat", "A shared target")  # Same title deliberately supplies no about.
        one, two = self.ask(chat=chat), self.ask(chat=chat)
        self.assertEqual({g["target"] for g in self.groups("yes")}, {one, two})

    def test_permission_reply_is_not_approval_only_exact_authorized_terminal(self):
        root = self.ask("permission")
        self.reply(root)
        self.reply(root, actor="pike", resolution="accept")
        self.reply(root, actor="juniper", resolution="decline")
        self.reply(root, actor="juniper", request_kind="question")
        self.assertEqual(self.all_reasons()[0]["resolution_state"], "open")
        evidence = self.reply(root, resolution="accept")
        self.assertEqual(self.all_reasons()[0]["resolution_evidence"], evidence)
        self.assertEqual(self.groups("yes"), [])

    def test_comment_exact_recipient_reply_and_asker_resolve_evidence(self):
        self.say("juniper", f"read {self.target}",
                 f'do comment {self.target} line="Question to Alex" to=alex mark=ask')
        cid = self.w.subjects[self.w.subject_of(self.target)]["comments"][-1]["id"]
        # Comment storage supports marks, not arbitrary line fields. The asker types their exact root.
        self.say("juniper", f"read {self.target}",
                 f'do comment {self.target} id={cid} line="Ordinary question" mark=question')
        self.say("pike", f"read {self.target}", f'do comment {self.target} id={cid} line="Unrelated answer"')
        self.assertEqual(self.groups("yes")[0]["reason_count"], 1)
        self.say("alex", f"read {self.target}", f'do comment {self.target} id={cid} line="My answer"')
        self.assertEqual(self.all_reasons()[0]["resolution_evidence"], self.w.events[-1]["id"])
        self.assertEqual(self.groups("yes"), [])
        self.say("alex", f"undo {self.w.events[-1]['id']}")
        self.say("juniper", f"read {self.target}",
                 f'do resolve {self.target} id={cid} line="Answered by the target owner directly"')
        self.assertEqual(self.all_reasons()[0]["resolution_state"], "resolved")

    def test_permission_comment_generic_resolve_is_not_a_terminal(self):
        self.say("juniper", f"read {self.target}",
                 f'do comment {self.target} line="Permission" to=alex mark=ask')
        cid = self.w.subjects[self.w.subject_of(self.target)]["comments"][-1]["id"]
        self.say("juniper", f"read {self.target}",
                 f'do comment {self.target} id={cid} line="Permission type" mark=permission')
        self.say("alex", f"read {self.target}", f'do comment {self.target} id={cid} line="A reply"')
        self.assertEqual(self.groups("yes")[0]["reason_count"], 1)
        self.say("juniper", f"read {self.target}", f'do resolve {self.target} id={cid} line="Parent closed"')
        self.assertEqual(self.groups("yes")[0]["reason_count"], 1)
        self.say("juniper", f"undo {self.w.events[-1]['id']}")
        self.say("alex", f"read {self.target}",
                 f'do comment {self.target} id={cid} line="Declined" mark=decline')
        self.assertEqual(self.groups("yes"), [])

    def test_recipient_empty_resolve_is_not_a_question_reply(self):
        self.say("juniper", f"read {self.target}",
                 f'do comment {self.target} line="Question" to=alex mark=ask')
        cid = self.w.subjects[self.w.subject_of(self.target)]["comments"][-1]["id"]
        self.say("juniper", f"read {self.target}",
                 f'do comment {self.target} id={cid} line="Question type" mark=question')
        self.say("alex", f"read {self.target}", f"do resolve {self.target} id={cid}")
        self.assertEqual(self.groups("yes")[0]["reason_count"], 1)

    def test_typed_permission_decline_withdraw_and_undo(self):
        for act, actor in (("decline", "alex"), ("withdraw", "juniper")):
            with self.subTest(act=act):
                root = self.ask("permission")
                self.reply(root, actor=actor, resolution=act)
                eid = self.w.events[-1]["id"]
                r = next(r for r in self.all_reasons() if r["source"] == root)
                self.assertEqual(r["resolution_state"], "resolved")
                self.say(actor, f"undo {eid}")
                r = next(r for r in self.all_reasons() if r["source"] == root)
                self.assertEqual(r["resolution_state"], "open")

    def test_native_independent_requests_on_closed_target_and_terminal_paths(self):
        self.prop(fixture_closed="yes")
        one, two = self.native(), self.native()
        self.say("alex", f"read {one}", f"accept {one}")
        accept = self.w.events[-1]["id"]
        reasons = self.all_reasons()
        self.assertEqual(len(reasons), 2)
        self.assertEqual(sum(r["resolution_state"] == "open" for r in reasons), 1)
        self.assertIn(accept, {r["resolution_evidence"] for r in reasons})
        self.say("juniper", f"read {two}", f"withdraw {two}")
        self.assertEqual(self.groups("yes"), [])
        self.say("juniper", f"undo {self.w.events[-1]['id']}")
        self.assertEqual(self.groups("yes")[0]["reason_count"], 1)
        self.say("alex", f"read {two}", f"decline {two}")
        self.assertEqual(self.groups("yes"), [])

    def test_predecessor_identity_and_new_bearer_cannot_withdraw(self):
        root = self.ask("permission", actor="pike")
        native = self.native(actor="pike")
        original = persons.today(self.w, "pike")
        self.say("alex", "person new pike kind=resident")
        self.reply(root, actor="pike", resolution="withdraw")
        self.say("pike", f"read {native}")
        refusal = self.say("pike", f"withdraw {native}", refuse=True)
        self.assertIn("only", refusal.get("error", ""))
        reasons = self.all_reasons()
        self.assertEqual({r["asker"] for r in reasons}, {original})
        self.assertEqual({r["resolution_state"] for r in reasons}, {"open"})
        self.assertTrue(all("first" in r["asker_label"] for r in reasons))

    def test_ordinary_asker_answer_needs_exact_evidence_not_generic_mark(self):
        root, other = self.ask(), self.ask()
        unrelated = self.reply(other, actor="pike")
        self.reply(root, actor="juniper", mark="answered", evidence=unrelated)
        self.assertEqual(next(r for r in self.all_reasons() if r["source"] == root)["resolution_state"], "open")
        exact = self.reply(root, actor="pike")
        mark = self.reply(root, actor="juniper", mark="answered", evidence=exact)
        self.assertEqual(next(r for r in self.all_reasons() if r["source"] == root)["resolution_evidence"], mark)

    def test_untyped_is_diagnostic_until_original_asker_classifies(self):
        root = self.ask(kind=None)
        self.reply(root)
        self.assertEqual(self.groups("yes"), [])
        self.assertIn("untyped", self.all_reasons()[0]["uncertainty"])
        self.reply(root, actor="pike", request_kind="question")
        self.assertEqual(self.groups("yes"), [])
        self.reply(root, actor="juniper", request_kind="question")
        self.assertEqual(self.all_reasons()[0]["resolution_state"], "resolved")

    def test_later_review_does_not_defer_sibling_permission_explicit_group_only(self):
        self.prop(fixture_design="waiting", fixture_review="later")
        self.say("juniper", f"read {self.target}", f"do tag {self.target} add=fixture_review")
        self.native()
        self.assertEqual(self.groups("yes")[0]["later"], "no")
        self.assertEqual({r["kind"]: r["later"] for r in self.all_reasons()},
                         {"design": "no", "review": "yes", "permission": "no"})
        self.prop(fixture_defer="later")
        self.assertEqual(self.groups("yes")[0]["later"], "yes")
        self.assertEqual(self.groups("yes")[0]["reason_count"], 3)

    def test_finishing_review_does_not_answer_sibling_permission(self):
        self.say("juniper", f"read {self.target}", f"do tag {self.target} add=fixture_review")
        self.native()
        self.assertEqual(self.groups("yes")[0]["reason_count"], 2)
        self.say("juniper", f"read {self.target}", f"do tag {self.target} remove=fixture_review")
        self.assertEqual(self.groups("yes")[0]["reason_count"], 1)
        self.assertEqual(self.all_reasons()[0]["kind"], "permission")

    def test_accepting_an_offer_on_same_target_does_not_answer_request(self):
        self.native()
        self.say("pike", f'promise to=juniper "Independent work" about={self.target}')
        promise = self.w.events[-1]["target"]
        self.say("pike", f"read {promise}", f"carry {promise} to=alex")
        self.say("alex", f"read {promise}", f"accept {promise}")
        self.assertEqual(self.groups("yes")[0]["reason_count"], 1)
        self.assertEqual(self.all_reasons()[0]["resolution_state"], "open")

    def test_news_closed_questions_available_not_counted_permissions_preserved(self):
        self.ask()
        self.reply()  # Informational notice never becomes a reason.
        self.prop(fixture_closed="yes")
        self.assertEqual(self.groups("yes"), [])
        self.assertEqual(len(self.all_reasons()), 1)
        self.assertEqual(self.all_reasons()[0]["resolution_state"], "open")
        self.native()
        self.assertEqual(self.groups("yes")[0]["reason_count"], 1)
        self.assertEqual(len(scene.line_rows(self.d, self.chat)), 2)

    def test_unknown_recipient_and_invalid_authored_context_are_diagnostic(self):
        self.ask(to="nobody-real")
        self.assertEqual(self.groups("yes"), [])
        self.assertEqual(self.groups()[0]["recipient"], "")
        self.ask(context="missing-id")
        self.assertEqual(self.groups("yes"), [])
        self.assertTrue(any("target is unknown" in r["uncertainty"] for r in self.all_reasons()))
        with self.assertRaises(Refusal):
            self.groups(recipient="nobody-real")

    def test_mixed_diagnostic_reason_does_not_hide_a_known_permission(self):
        self.ask(kind=None)
        self.native()
        group = self.groups("yes")[0]
        self.assertEqual(group["reason_count"], 1)
        self.assertEqual(len(self.reasons(group)), 2)
        self.assertEqual(len(scene.rows(self.d, f"action-reasons:alex:{self.policy}:{group['key']} eligible=yes")), 1)

    def test_recipient_specific_no_default(self):
        self.ask(to="pike")
        self.assertEqual(self.groups("yes"), [])
        self.assertEqual(len(self.groups("yes", recipient="pike")), 1)
        with self.assertRaises(Refusal):
            scene.rows(self.d, f"actions::{self.policy}")

    def test_policy_missing_malformed_and_explicit_empty_refuse_or_zero(self):
        with self.assertRaises(Refusal):
            scene.rows(self.d, "actions:alex:missing")
        self.prop(self.policy, action_reviews="nonsense:bad")
        with self.assertRaises(Refusal):
            self.groups()
        self.prop(self.policy, action_reviews="none", action_designs="none")
        self.assertEqual(self.groups(), [])
        self.prop(self.policy, action_group_later="")
        with self.assertRaises(Refusal):
            self.groups()

    def test_keys_stable_alias_rename_reopen_new_design_reason(self):
        self.prop(fixture_design="waiting")
        group, reason = self.groups()[0], self.all_reasons()[0]
        self.say("juniper", f"read {self.target}", f'do retitle {self.target} title="Renamed"')
        sid = self.w.subject_of(self.target)
        self.assertEqual(group["key"], self.groups()[0]["key"])
        self.assertEqual(reason["request_key"], self.all_reasons()[0]["request_key"])
        self.assertEqual(group["key"], f"{self.alex}~{sid}")
        self.say("juniper", f"read {sid}", f"do place {sid} into={self.rooms.corner['pike']}")
        self.assertEqual(len(self.groups("yes")), 1)
        self.assertEqual(group["key"], self.groups()[0]["key"])
        self.assertEqual(reason["request_key"], self.all_reasons()[0]["request_key"])
        self.prop(fixture_design="answered")
        self.assertEqual(self.groups("yes"), [])
        self.prop(fixture_design="waiting")
        self.assertNotEqual(reason["request_key"], self.all_reasons()[0]["request_key"])

    def test_original_activation_author_survives_other_persons_tag_edit(self):
        self.say("pike", f"read {self.target}", f"do tag {self.target} add=fixture_review")
        before = self.all_reasons()[0]
        self.say("juniper", f"read {self.target}", f"do tag {self.target} add=unrelated")
        after = self.all_reasons()[0]
        self.assertEqual(after["request_key"], before["request_key"])
        self.assertEqual(after["asker"], persons.today(self.w, "pike"))

    def test_missing_activation_before_image_is_diagnostic_without_archive_reads(self):
        self.prop(fixture_design="waiting")
        self.w.events[-1]["undo"] = {"kept": "unavailable-test-archive"}
        import kept
        with patch.object(kept, "copy_of", side_effect=AssertionError("must not read external archive")):
            self.assertEqual(self.groups("yes"), [])
            self.assertIn("asker is unknown", self.all_reasons()[0]["uncertainty"])

    def test_query_name_and_bound_policy_keep_original_recipient_after_reuse(self):
        self.prop(fixture_design="waiting")
        old_key = self.groups("yes")[0]["key"]
        self.say("alex", "person new alex kind=human")
        self.assertEqual(self.groups("yes"), [])  # typed alex now means the new person
        self.assertEqual(self.groups("yes", recipient=self.alex)[0]["key"], old_key)

    def test_event_time_addressees_keep_old_recipient_for_chat_and_native(self):
        self.ask()
        self.native()
        self.say("alex", "person new alex kind=human")
        self.reply(self.w.subjects[self.w.subject_of(self.chat)]["lines"][0]["id"])
        self.assertEqual(self.groups("yes"), [])
        old = self.groups("yes", recipient=self.alex)
        self.assertEqual(old[0]["reason_count"], 2)
        self.assertEqual({r["recipient"] for r in self.reasons(old[0], self.alex)}, {self.alex})

    def test_request_confirm_report_and_release_are_not_permission_answers(self):
        request = self.native()
        self.say("juniper", f"read {request}", f"confirm {request}")
        # Existing promise lifecycle permits confirm; the action queue must not silently translate it.
        self.assertEqual(self.all_reasons()[0]["resolution_state"], "open")
        self.assertEqual(self.groups("yes")[0]["reason_count"], 1)

    def legacy_native(self, missing=False, **args):
        request = self.native()
        sid = self.w.subject_of(request)
        original = self.w.events[-1]
        if missing:
            self.w.events.remove(original)
            self.w.subjects[sid]["props"]["asked_by"] = "juniper"
        else:
            original.update(verb="prop", args=args)
        return request, sid

    def test_stored_single_bearers_missing_origin_are_labelled_and_read_only(self):
        _, sid = self.legacy_native(missing=True)
        before = copy.deepcopy((self.w.events, self.w.subjects, self.w.nodes))
        r = self.all_reasons()[0]
        self.assertEqual((r["recipient"], r["recipient_source"]), (self.alex, "stored"))
        self.assertEqual((r["asker"], r["asker_source"]), (self.juniper, "stored"))
        self.assertEqual((r["resolution_state"], r["resolution_evidence"]), ("open", ""))
        self.assertEqual(self.groups("yes")[0]["reason_count"], 1)
        self.assertEqual(before, (self.w.events, self.w.subjects, self.w.nodes))
        self.assertEqual(r["source"], sid)

    def test_stored_multi_bearer_recipient_and_asker_stay_diagnostic(self):
        self.legacy_native(missing=True)
        self.say("alex", "person new alex kind=human", "person new juniper kind=resident")
        r = self.all_reasons()[0]
        self.assertEqual((r["recipient"], r["asker"]), ("", ""))
        self.assertEqual((r["recipient_source"], r["asker_source"]), ("stored", "stored"))
        self.assertEqual(self.groups("yes"), [])
        self.assertEqual(r["resolution_state"], "open")

    def test_stored_person_ids_are_not_rebound_to_new_name_bearers(self):
        _, sid = self.legacy_native(missing=True)
        self.w.subjects[sid]["props"].update(to=self.alex, asked_by=self.juniper)
        self.say("alex", "person new alex kind=human", "person new juniper kind=resident")
        r = self.all_reasons(recipient=self.alex)[0]
        self.assertEqual((r["recipient"], r["asker"]), (self.alex, self.juniper))
        self.assertEqual(r["eligible"], "yes")

    def test_legacy_property_recipient_agrees_but_asker_remains_event_time(self):
        self.legacy_native(awaiting="alex")
        self.say("alex", "person new juniper kind=resident")
        r = self.all_reasons()[0]
        self.assertEqual((r["recipient"], r["recipient_source"]), (self.alex, "stored"))
        self.assertEqual((r["asker"], r["asker_source"]), (self.juniper, "event"))
        self.assertEqual(r["eligible"], "yes")

    def test_legacy_property_conflict_is_diagnostic_never_either_recipient(self):
        self.legacy_native(awaiting="pike")
        r = self.all_reasons()[0]
        self.assertEqual(r["recipient"], "")
        self.assertIn("disagrees", r["uncertainty"])
        self.assertEqual(self.groups("yes"), [])
        self.assertEqual(r["resolution_state"], "open")

    def test_legacy_property_without_addressee_uses_stored_single_bearer(self):
        self.legacy_native()
        r = self.all_reasons()[0]
        self.assertEqual((r["recipient"], r["recipient_source"]), (self.alex, "stored"))
        self.assertEqual(r["asker_source"], "event")
        self.assertEqual(r["eligible"], "yes")

    def test_legacy_matching_name_with_multiple_bearers_is_still_diagnostic(self):
        self.legacy_native(awaiting="alex")
        self.say("alex", "person new alex kind=human")
        r = self.all_reasons()[0]
        self.assertEqual((r["recipient"], r["recipient_source"]), ("", "stored"))
        self.assertEqual(self.groups("yes"), [])

    def test_other_retained_origins_and_missing_event_author_do_not_fallback(self):
        request = self.native()
        original = self.w.events[-1]
        self.w.subjects[self.w.subject_of(request)]["props"]["asked_by"] = self.juniper
        original.update(verb="comment", args={}, who=None)
        r = self.all_reasons()[0]
        self.assertEqual((r["recipient"], r["asker"]), ("", ""))
        self.assertEqual((r["recipient_source"], r["asker_source"]), ("event", "event"))
        self.assertEqual(self.groups("yes"), [])

    def test_native_origin_wins_even_missing_or_invalid_to(self):
        request = self.native()
        original = self.w.events[-1]
        self.w.subjects[self.w.subject_of(request)]["props"].update(to="pike", asked_by="pike")
        r = self.all_reasons()[0]
        self.assertEqual((r["recipient"], r["recipient_source"]), (self.alex, "event"))
        self.assertEqual((r["asker"], r["asker_source"]), (self.juniper, "event"))
        for args in ({}, {"to": "unknown-person"}, {"to": ""}):
            with self.subTest(args=args):
                original["args"] = args
                r = self.all_reasons()[0]
                self.assertEqual((r["recipient"], r["recipient_source"]), ("", "event"))
                self.assertEqual(self.groups("yes"), [])

    def test_undone_origin_does_not_enable_stored_fallback(self):
        self.native()
        self.w.events[-1]["undone"] = True
        self.assertEqual(self.all_reasons(), [])

    def test_missing_origin_terminal_checks_still_require_exact_actor_and_act(self):
        for act, actor in (("accept", "alex"), ("decline", "alex"), ("withdraw", "juniper")):
            with self.subTest(act=act):
                self.setUp()
                request = self.native()
                original = self.w.events[-1]
                sid = self.w.subject_of(request)
                self.say(actor, f"read {request}", f"{act} {request}")
                evidence = self.w.events[-1]
                self.w.events.remove(original)
                self.w.subjects[sid]["props"]["asked_by"] = self.juniper
                self.assertEqual(self.all_reasons()[0]["resolution_evidence"], evidence["id"])
                evidence["who"] = persons.today(self.w, "pike")
                self.assertEqual(self.all_reasons()[0]["resolution_state"], "open")
                evidence["who"] = persons.today(self.w, actor)
                self.w.subjects[sid]["promise"]["acts"][-1][1] = "confirm"
                self.assertEqual(self.all_reasons()[0]["resolution_state"], "open")

    def test_stale_actions_and_wrong_actor_preserve_viewer_draft_and_paused_branch(self):
        viewer = self.make("note", "Viewer", role="home-view", viewing=self.target, with_="reader")
        draft = self.make("note", "Draft", text="Unsent words", context="selected", reply_to="m1")
        paused = self.make("note", "Paused owner card", owner="pike", fixture_motion="paused")
        request = self.native()
        saved = copy.deepcopy([self.w.subjects[self.w.subject_of(x)] for x in (viewer, draft, paused)])
        self.groups("yes")
        self.say("pike", f"read {request}")
        refusal = self.say("pike", f"accept {request}", refuse=True)
        self.assertIn("only", refusal.get("error", ""))
        self.say("alex", f"read {request}", f"accept {request}")
        refusal = self.say("alex", f"decline {request}", refuse=True)
        self.assertIn("not a request", refusal.get("error", ""))
        self.assertEqual(saved, [self.w.subjects[self.w.subject_of(x)] for x in (viewer, draft, paused)])
        # A stale target edit (the ordinary source-linked action) still uses the desk's existing fence.
        self.say("alex", f"read {self.target}")
        stale_seen = copy.deepcopy(self.d.seen)
        self.say("juniper", f"read {self.target}", f'do retitle {self.target} title="Changed elsewhere"')
        self.d.seen = stale_seen
        refusal = self.say("alex", f'do retitle {self.target} title="Old action"', refuse=True)
        self.assertIn("stale", refusal.get("error", ""))
        self.assertEqual(saved, [self.w.subjects[self.w.subject_of(x)] for x in (viewer, draft, paused)])

    def test_shared_snapshot_defensive_rows_and_no_heuristic_or_side_effect(self):
        self.ask()
        before = copy.deepcopy((self.w.events, self.w.nodes, self.w.subjects, self.d.seen, self.d.open))
        with scene.still(self.w), patch.object(action_queue, "_evaluate", wraps=action_queue._evaluate) as run:
            group = self.groups()[0]
            self.reasons(group)
            group["title"] = "caller edit"
            self.assertNotEqual(self.groups()[0]["title"], "caller edit")
            self.assertEqual(run.call_count, 1)
        self.assertEqual(before, (self.w.events, self.w.nodes, self.w.subjects, self.d.seen, self.d.open))
        with patch.object(scene, "saying_rows", side_effect=AssertionError("legacy source forbidden")):
            self.assertEqual(len(self.groups("yes")), 1)

    def test_nested_scene_three_consumer_copies_same_membership_and_inverse(self):
        self.ask()
        src = (f"root : column, of actions:alex:{self.policy} counted=yes as group, each card\n"
               'card : column\n  title : text "$group.title"\n'
               f"  reasons : column, of action-reasons:alex:{self.policy}:$group.key eligible=yes as reason, each detail\n"
               'detail : text "$reason.kind $reason.resolution_state"')
        originals = ['root : text "Header before"', 'root : text "Board before"', 'root : text "Waiting before"']
        copies = [self.make("note", title, tags="lens", text=original)
                  for title, original in zip(("Fixture header", "Fixture Board", "Fixture waiting"), originals)]
        scenes = []
        for item in copies:
            self.say("juniper", f"read {item}", f"do edit {item} text={json.dumps(src)}")
            with scene.still(self.w):
                scenes.append(lens_ir.evaluate(self.d, self.w.subjects[self.w.subject_of(item)]["text"]))
        self.assertEqual([s["members"]["ids"] for s in scenes],
                         [scenes[0]["members"]["ids"]] * 3)
        self.assertEqual(scenes[0]["members"]["n"], 1)
        self.assertIn("question open", str(scenes[0]))
        # Exact inverse retained and exercised on full isolated consumer copies.
        for item, original in zip(copies, originals):
            self.say("juniper", f"read {item}", f"do edit {item} text={json.dumps(original)}")
            self.assertEqual(self.w.subjects[self.w.subject_of(item)]["text"], original)
        with scene.still(self.w):
            header = lens_ir.evaluate(self.d, f'root : count actions:alex:{self.policy} counted=yes, text "$count"')
        self.assertEqual(header["text"], "1")


if __name__ == "__main__":
    unittest.main()
