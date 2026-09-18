"""Independent Media E2E checks: actual ephemeral Desk + frame + activation + typed actions.
No HTTP, browser, live sessions, component engines or native package installation.
"""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"text-desk-lab"/"notation"))
from explore import fresh
from compiler_bridge import CompilerBridge
from frame_contract import check_frame
from component_registry import ComponentRefusal, ComponentRegistry

SOURCE='''window : column
  items : free, of kind:note, each card
card : column, at item, on drag do do move $item to=$x,$y
  body : text $text, on edit do do rewrite $id text="$value"
'''


def command(desk,verb,target,**args):
    result=desk.dispatch("do",{"verb":verb,"target":target,"args":args})
    if result.get("error"):raise AssertionError(result["error"])
    return result


def create(desk,title,text,tags=""):
    before=set(desk.world.subjects)
    desk.dispatch("look",{"target":desk.world.root})
    command(desk,"create",desk.world.root,kind="note",title=title,text=text,tags=tags)
    subject=(set(desk.world.subjects)-before).pop()
    return subject,next(iter(desk.world.appearances_of(subject)))


def offered(bridge,frame,target,gesture="edit",appearance=None):
    for actions in frame["typed_actions"].values():
        for action in actions:
            if action.get("supported") and action["on"]==gesture:
                info=bridge.inspect(action["handle"])
                if info["target"]==target and (appearance is None or info["appearance"]==appearance):return action["handle"]
    raise AssertionError(f"No {gesture} offered for {target}")


class HostileBridgeTests(unittest.TestCase):
    def setUp(self):
        desk=fresh();desk.dispatch("look",{"target":desk.world.root});command(desk,"untile",desk.world.root)
        self.subject,self.first=create(desk,"Code material","original")
        self.definition,_=create(desk,"Lens definition",SOURCE,"lens")
        desk.dispatch("read",{"target":self.subject});command(desk,"place",self.subject,into=desk.world.root)
        self.appearances=list(desk.world.appearances_of(self.subject))
        self.registry=ComponentRegistry()
        self.original_desk=deepcopy(desk)
        self.bridge=CompilerBridge(desk,self.definition)

    def revision(self):return self.bridge.lifecycle_state()["activation_revision"]

    def test_transport_handles_do_not_invalidate_semantic_frame(self):
        packet=self.bridge.offer("alex")
        self.assertEqual(packet["frame_id"],packet["semantic_frame"]["frame_id"])
        self.assertTrue(check_frame(self.original_desk,packet["semantic_frame"])["ok"])
        changed=deepcopy(packet["semantic_frame"]);changed["scene"]["text"]="forged"
        self.assertFalse(check_frame(self.original_desk,changed)["ok"])
    def test_exact_code_empty_and_literal_metacharacters_through_native_rewrite(self):
        for value in ('', '  print("hi")\n\t$& $value \\n  ', 'x; do remove a01\n# keep literal'):
            frame=self.bridge.offer("alex");handle=offered(self.bridge,frame,self.subject)
            self.bridge.invoke("alex",handle,{"value":value})
            self.assertEqual(self.bridge.snapshot()["subjects"][self.subject]["text"],value)

    def test_successful_definition_activation_stales_prior_offered_handle(self):
        old=offered(self.bridge,self.bridge.offer("alex"),self.subject)
        revision=self.revision()
        candidate=self.bridge.propose(SOURCE+"# a new definition edition\n",revision)
        self.assertTrue(candidate["ok"],candidate)
        result=self.bridge.activate(candidate["candidate_id"],revision)
        self.assertTrue(result["ok"],result)
        before=self.bridge.snapshot()
        with self.assertRaises(ValueError):self.bridge.invoke("alex",old,{"value":"must not land"})
        self.assertEqual(self.bridge.snapshot(),before)

    def test_distinct_appearances_share_content_but_not_position(self):
        first,second=self.appearances
        before=self.bridge.snapshot()["nodes"][second]
        handle=offered(self.bridge,self.bridge.offer("alex"),first,"drag",first)
        self.bridge.invoke("alex",handle,{"x":93,"y":147})
        current=self.bridge.snapshot()
        self.assertEqual(current["nodes"][first]["x"],93)
        self.assertEqual(current["nodes"][second],before)
        handle=offered(self.bridge,self.bridge.offer("alex"),self.subject,"edit",second)
        self.bridge.invoke("alex",handle,{"value":"same material via second appearance"})
        current=self.bridge.snapshot()
        self.assertTrue(all(current["nodes"][a]["subject"]==self.subject for a in self.appearances))
        self.assertEqual(current["subjects"][self.subject]["text"],"same material via second appearance")

    def test_failed_candidate_retains_active_frame_and_exact_draft_selection(self):
        draft={"text":'  unsaved "draft"\n',"selection":{"anchor":2,"focus":12},"composing":True}
        self.bridge.set_view_state("editor-one",draft)
        before=self.bridge.lifecycle_state();world=self.bridge.snapshot()
        candidate=self.bridge.propose("window : unsupported-engine magic",self.revision())
        self.assertFalse(candidate["ok"])
        self.assertEqual(self.bridge.lifecycle_state(),before)
        self.assertEqual(self.bridge.snapshot(),world)

    def test_missing_component_refuses_at_separate_registry_boundary(self):
        # CompilerBridge does not accept/mount component declarations in this slice.
        # Refusal here is intentionally not reported as integrated compilation evidence.
        self.bridge.set_view_state("editor-one",{"draft":"retained"})
        before=self.bridge.lifecycle_state()
        with self.assertRaises(ComponentRefusal) as cm:
            self.registry.resolve([{"instance":"future-surface",
                "component":{"id":"future.vector-editor","version":1},"material":{}}])
        self.assertEqual(cm.exception.code,"missing-capability")
        self.assertEqual(self.bridge.lifecycle_state(),before)

    def test_candidate_preview_does_not_pin_old_world_for_later_activation(self):
        revision=self.revision();candidate=self.bridge.propose(SOURCE+"# pending\n",revision)
        self.assertTrue(candidate["ok"],candidate)
        handle=offered(self.bridge,self.bridge.offer("alex"),self.subject)
        self.bridge.invoke("alex",handle,{"value":"new committed material"})
        before=self.bridge.snapshot();active=self.bridge.lifecycle_state()["active_source"]
        result=self.bridge.activate(candidate["candidate_id"],revision)
        self.assertFalse(result["ok"],"A candidate against old material must recompile/refuse")
        self.assertEqual(self.bridge.snapshot(),before)
        self.assertEqual(self.bridge.lifecycle_state()["active_source"],active)

    def test_public_offer_retains_active_nested_definition_after_invalid_rewrite(self):
        desk=deepcopy(self.original_desk)
        inner,_=create(desk,"Inner",SOURCE,"lens")
        outer_source="window : column\n  slot : lens Inner\n"
        outer,_=create(desk,"Outer",outer_source,"lens")
        bridge=CompilerBridge(desk,outer)
        bridge.set_view_state("editor",{"draft":'  held "draft"',"selection":[2,7]})
        material=offered(bridge,bridge.offer("alex"),self.subject)
        bridge.invoke("alex",material,{"value":"new material survives active fallback"})
        edit_inner=offered(bridge,bridge.offer("alex"),inner)
        bridge.invoke("alex",edit_inner,{"value":"window : definitely-invalid"})
        before=bridge.snapshot();active=bridge.lifecycle_state()
        refused=bridge.propose(outer_source,active["activation_revision"])
        self.assertFalse(refused["ok"])
        packet=bridge.offer("alex")
        self.assertTrue(packet["scene"])
        self.assertIn("new material survives active fallback",packet["text"])
        self.assertEqual(bridge.snapshot(),before)
        self.assertEqual(bridge.lifecycle_state()["view_states"],active["view_states"])
        self.assertEqual(bridge.lifecycle_state()["activation_revision"],active["activation_revision"])
        self.assertEqual(before["subjects"][inner]["text"],"window : definitely-invalid")
    def test_restore_definition_preserves_current_material_and_draft(self):
        original=self.revision();candidate=self.bridge.propose(SOURCE+"# revised\n",original)
        self.assertTrue(self.bridge.activate(candidate["candidate_id"],original)["ok"])
        handle=offered(self.bridge,self.bridge.offer("alex"),self.subject)
        self.bridge.invoke("alex",handle,{"value":"later material must survive restore"})
        self.bridge.set_view_state("editor-one",{"draft":"still unsaved","selection":[0,5]})
        world=self.bridge.snapshot();views=self.bridge.lifecycle_state()["view_states"]
        result=self.bridge.restore(original,self.revision());self.assertTrue(result["ok"],result)
        self.assertEqual(self.bridge.snapshot(),world)
        self.assertEqual(self.bridge.lifecycle_state()["view_states"],views)


if __name__=="__main__":unittest.main()
