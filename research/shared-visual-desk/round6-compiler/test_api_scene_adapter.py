"""Hostile authoritative-packet tests. No HTTP endpoint or live session is used."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"text-desk-lab"/"notation"))
from explore import fresh
from api_scene_adapter import ScenePacketBridge
from test_bridge_contract import SOURCE,command,create,offered


def nodes(node):
    yield node
    for child in node["kids"]:yield from nodes(child)


class ScenePacketChecks(unittest.TestCase):
    def setUp(self):
        desk=fresh();desk.dispatch("look",{"target":desk.world.root});command(desk,"untile",desk.world.root)
        self.subject,self.appearance=create(desk,"Material","original")
        self.definition,_=create(desk,"Main",SOURCE,"lens")
        self.inner,_=create(desk,"Inner",SOURCE,"lens")
        self.outer,_=create(desk,"Outer","window : column\n  inner : lens Inner\n","lens")
        self.fixture_desk=deepcopy(desk)
        self.bridge=ScenePacketBridge(desk)

    def capture(self,name="Main",actor="alex"):
        return self.bridge.capture(actor,name)

    def offer(self,capture,actor="alex",packet=None):
        return self.bridge.offer_capture(actor,capture["capture_id"],packet=packet)

    def test_exact_literal_and_empty_are_native_values_after_authoritative_capture(self):
        for value in ('', '  print("hello")\n\t$& \\n ; do remove a01  '):
            capture=self.capture();packet=self.offer(capture,packet=deepcopy(capture["packet"]))
            handle=offered(self.bridge,packet,self.subject)
            self.bridge.invoke("alex",handle,{"value":value})
            self.assertEqual(self.bridge.snapshot()["subjects"][self.subject]["text"],value)

    def test_client_line_target_and_revision_tampering_cannot_mint_handles(self):
        for mode in ("line","target","revision"):
            with self.subTest(mode=mode):
                capture=self.capture();forged=deepcopy(capture["packet"])
                node=next(n for n in nodes(forged["scene"]) if n.get("item")==self.appearance and any(a["on"]=="edit" for a in n["acts"]))
                if mode=="line":node["acts"][0]["line"]='do rewrite '+self.inner+' text="$value"'
                elif mode=="target":node["item"]=next(n["item"] for n in nodes(forged["scene"]) if n.get("item") and n["item"]!=self.appearance)
                else:node["rev"]=999999
                before=self.bridge.snapshot()
                with self.assertRaises(ValueError):self.offer(capture,packet=forged)
                self.assertEqual(self.bridge.snapshot(),before)

    def test_unknown_capture_and_actor_mismatch_refuse(self):
        with self.assertRaises(ValueError):self.bridge.offer_capture("alex","not-a-capture")
        capture=self.capture()
        with self.assertRaises(ValueError):self.offer(capture,actor="another-actor",packet=capture["packet"])

    def test_material_change_between_capture_and_offer_refuses_old_capture(self):
        old=self.capture();new=self.capture()
        offered_new=self.offer(new);handle=offered(self.bridge,offered_new,self.subject)
        self.bridge.invoke("alex",handle,{"value":"newer material"})
        with self.assertRaises(ValueError):self.offer(old)
        self.assertEqual(self.bridge.snapshot()["subjects"][self.subject]["text"],"newer material")

    def test_inner_definition_change_after_mint_invalidates_outer_action(self):
        packet=self.offer(self.capture("Outer"))
        old=offered(self.bridge,packet,self.subject)
        edit_inner=offered(self.bridge,packet,self.inner)
        self.bridge.invoke("alex",edit_inner,{"value":SOURCE+"# changed nested definition\n"})
        before=self.bridge.snapshot()
        with self.assertRaises(ValueError):self.bridge.invoke("alex",old,{"value":"must not land"})
        self.assertEqual(self.bridge.snapshot(),before)

    def test_last_good_fallback_never_silently_offers_old_actions(self):
        packet=self.offer(self.capture())
        edit_definition=offered(self.bridge,packet,self.definition)
        self.bridge.invoke("alex",edit_definition,{"value":"window : not-valid"})
        fallback=self.capture()
        self.assertTrue(fallback["packet"]["scene"].get("broken"))
        before=self.bridge.snapshot()
        with self.assertRaises(ValueError):self.offer(fallback)
        self.assertEqual(self.bridge.snapshot(),before)

    def test_external_worktrees_are_refused_before_saved_session_access(self):
        desk=fresh();desk._session="hostile-probe"
        create(desk,"External","window : column, of worktrees, each row\nrow : text $name\n","lens")
        bridge=ScenePacketBridge(desk)
        class NoSavedSessionAccess:
            def glob(self,pattern):
                raise AssertionError("External saved-session enumeration reached")
        import worktree
        with patch.object(worktree,"SESSIONS",NoSavedSessionAccess()):
            with self.assertRaises(ValueError):bridge.capture("alex","External")
    def test_invalid_first_candidate_does_not_borrow_another_lens_fallback(self):
        desk=deepcopy(self.fixture_desk)
        create(desk,"Never-valid","window : not-valid","lens")
        bridge=ScenePacketBridge(desk)
        bridge.capture("alex","Main")  # A different lens now has a last-good cache.
        before=bridge.snapshot()
        with self.assertRaisesRegex(Exception,"cannot say"):
            bridge.capture("alex","Never-valid")
        self.assertEqual(bridge.snapshot(),before)

    def test_dynamic_nested_definition_change_invalidates_offered_outer_action(self):
        desk=deepcopy(self.fixture_desk)
        create(desk,"Inner","a selector points at an installed lens title","embed")
        create(desk,"Dynamic","window : column, of tag:embed, each slot\nslot : lens $title\n","lens")
        bridge=ScenePacketBridge(desk)
        capture=bridge.capture("alex","Dynamic")
        packet=bridge.offer_capture("alex",capture["capture_id"])
        old=offered(bridge,packet,self.subject)
        edit_inner=offered(bridge,packet,self.inner)
        bridge.invoke("alex",edit_inner,{"value":SOURCE+"# dynamic nested edit\n"})
        before=bridge.snapshot()
        with self.assertRaises(ValueError):bridge.invoke("alex",old,{"value":"must not land"})
        self.assertEqual(bridge.snapshot(),before)
    def test_owner_handoff_rechecks_peer_update_on_current_authoritative_desk(self):
        owner=deepcopy(self.fixture_desk)
        packet=self.bridge.offer_from_owner(owner,"alex","Main")
        handle=offered(self.bridge,packet,self.subject)
        current=deepcopy(owner);current.world.me="peer"
        current.dispatch("read",{"target":self.subject})
        command(current,"rewrite",self.subject,text="peer edit after offer")
        before=current.snapshot();events=deepcopy(current.world.events)
        with self.assertRaises(ValueError):
            self.bridge.invoke_on_owner(current,"alex",handle,{"value":"stale replacement"})
        self.assertEqual(current.snapshot(),before)
        self.assertEqual(current.world.events,events)
        self.assertEqual(current.world.subjects[self.subject]["text"],"peer edit after offer")

    def test_successful_owner_handoff_returns_new_desk_without_mutating_input(self):
        owner=deepcopy(self.fixture_desk)
        packet=self.bridge.offer_from_owner(owner,"alex","Main")
        handle=offered(self.bridge,packet,self.subject)
        before=owner.snapshot();events=deepcopy(owner.world.events);seen=deepcopy(owner.seen)
        new_owner,receipt=self.bridge.invoke_on_owner(owner,"alex",handle,{"value":'  exact "new"\n'})
        self.assertIsNot(new_owner,owner)
        self.assertEqual(new_owner.world.subjects[self.subject]["text"],'  exact "new"\n')
        self.assertEqual(owner.snapshot(),before)
        self.assertEqual(owner.world.events,events)
        self.assertEqual(owner.seen,seen)
        self.assertEqual(receipt["events"][-1]["by"],"alex")

    def test_owner_with_rules_hooks_or_follow_is_refused_before_staging(self):
        owner=deepcopy(self.fixture_desk)
        packet=self.bridge.offer_from_owner(owner,"alex","Main")
        handle=offered(self.bridge,packet,self.subject)
        for field,value in (("rules",["must not execute"]),("hooks",{"x":"must not execute"}),("follow",True)):
            with self.subTest(field=field):
                changed=deepcopy(owner);setattr(changed,field,value)
                before=deepcopy((changed.world.subjects,changed.world.nodes,changed.world.events))
                with self.assertRaises(ValueError):self.bridge.offer_from_owner(changed,"alex","Main")
                with self.assertRaises(ValueError):self.bridge.invoke_on_owner(changed,"alex",handle,{"value":"x"})
                self.assertEqual((changed.world.subjects,changed.world.nodes,changed.world.events),before)
    def test_echo_is_optional_but_capture_is_single_use(self):
        capture=self.capture();packet=self.offer(capture)
        self.assertIn("typed_actions",packet)
        with self.assertRaises(ValueError):self.offer(capture)


if __name__=="__main__":unittest.main()
