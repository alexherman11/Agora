"""Predicate semantics and copy restore ordering; no browser or saved world."""
import asyncio
import json
from pathlib import Path
import subprocess
import sys
import unittest
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from playtest_steps.partition_navigation import bind, carry_point_js, carry_trace_js, divider_candidate_js, edge_predicate, restore_fixture


class NavigationStep(unittest.TestCase):
    def run_js(self, setup, expression):
        return json.loads(subprocess.check_output(
            ["node", "-e", setup + "process.stdout.write(JSON.stringify(" + expression + "));"],
            text=True))

    def matches(self, side, box, tree="after"):
        pred = edge_predicate("panel", side, [16, 20, 1248, 700], "before")
        script = (
            "const panel={getBoundingClientRect:()=>(" + json.dumps(box) + ")};"
            "const document={querySelector:()=>({_n:{paint:{partition:{focus:'',tree:"
            + json.dumps(tree) + "}}}})};"
            "process.stdout.write(JSON.stringify(" + pred + "));"
        )
        return json.loads(subprocess.check_output(["node", "-e", script], text=True))

    def test_top_and_bottom_cannot_match_same_half(self):
        bottom = dict(left=16, top=378, right=1264, bottom=720, width=1248, height=342)
        self.assertTrue(self.matches("bottom", bottom))
        self.assertFalse(self.matches("top", bottom))
        top = {**bottom, "top": 20, "bottom": 362}
        self.assertTrue(self.matches("top", top))
        self.assertFalse(self.matches("bottom", top))

    def test_left_and_right_and_persistence(self):
        left = dict(left=16, top=20, right=632, bottom=720, width=616, height=700)
        self.assertTrue(self.matches("left", left))
        self.assertFalse(self.matches("right", left))
        right = {**left, "left": 648, "right": 1264}
        self.assertTrue(self.matches("right", right))
        self.assertFalse(self.matches("left", right))
        self.assertFalse(self.matches("left", left, tree="before"),
                         "an optimistic rectangle alone is not a persisted result")

    def restore(self, answers):
        calls = []

        class Page:
            async def js(self, source):
                # The restore must await a pending-answer check before reading.
                self_test.assertIn('data-sending="1"', source)
                self_test.assertIn("reject", source)
                calls.append("settled")

        class Copy:
            def do(self, line, who):
                calls.append(line)
                return answers.pop(0) if line.startswith("do prop") else "read"

        self_test = self
        asyncio.run(restore_fixture(Page(), Copy(),
                    dict(layout="layout", tree="", focus="")))
        return calls

    def test_restore_waits_and_rereads_after_stale_answer(self):
        calls = self.restore(["ERR changed since you looked", "ok"])
        self.assertEqual(calls[0], "settled")
        self.assertEqual(calls[1::2], ["look layout", "look layout"])
        self.assertEqual(len(calls), 5)

    def test_restore_refusal_is_not_hidden(self):
        with self.assertRaisesRegex(AssertionError, "permission denied"):
            self.restore(["ERR permission denied"])

    def test_restore_no_change_is_allowed(self):
        self.assertEqual(len(self.restore(["ERR already has that;"])), 3)

    def test_grip_covered_by_ancestor_is_not_a_valid_carry_point(self):
        setup = """
          const grip={_n:{fence:{item:'a'}},hidden:false,getClientRects:()=>[{}],getBoundingClientRect:()=>({left:20,top:30,width:100,height:8}),
            contains:e=>e===grip};
          const panel={_n:{paint:{partition_item:'a'}},querySelectorAll:()=>[grip]};
          const document={elementFromPoint:()=>panel};
        """
        self.assertIsNone(self.run_js(setup, carry_point_js("panel")))
        self.assertEqual(self.run_js(setup + "document.elementFromPoint=()=>grip;",
                                   carry_point_js("panel")), [70, 34])

    def test_grip_control_is_excluded_without_scrolling_or_selection_clear(self):
        setup = """
          const grip={_n:{fence:{item:'a'}},hidden:false,getClientRects:()=>[{}],getBoundingClientRect:()=>({left:20,top:30,width:100,height:8}),
            contains:e=>e===grip||e===control};
          const control={tagName:'BUTTON',parentElement:grip};
          const panel={_n:{paint:{partition_item:'a'}},querySelectorAll:()=>[grip]};
          const document={elementFromPoint:x=>x>50?control:grip};
        """
        self.assertEqual(self.run_js(setup, carry_point_js("panel")), [30, 34])

    def test_copy_trace_records_actual_target_and_final_default_without_interfering(self):
        setup = """
          const listeners={},tasks=[];
          const document={addEventListener:(t,f)=>listeners[t]=f,
            removeEventListener:t=>delete listeners[t]};
          const window={getSelection:()=>'selected'};
          const queueMicrotask=f=>tasks.push(f);
          const grip={dataset:{key:'title'},getBoundingClientRect:()=>({left:10,top:20,width:200,height:25})};
          const target={tagName:'SPAN',dataset:{key:'count'},parentElement:grip,_clicks:true,getBoundingClientRect:()=>({left:30,top:20,width:90,height:25}),
            closest:s=>s==='[data-carry]'?grip:null};
        """
        result = self.run_js(setup + carry_trace_js() + ";"
            "const e={target,clientX:35,clientY:30,defaultPrevented:false};"
            "listeners.pointerdown(e);e.defaultPrevented=true;tasks.forEach(f=>f());",
            "({trace:window.__partitionCarryTrace(),remaining:Object.keys(listeners).length})")
        self.assertEqual(result["remaining"], 0)
        self.assertEqual(result["trace"][0]["key"], "count")
        self.assertEqual(result["trace"][0]["gripRect"], [10,20,200,25])
        self.assertEqual(result["trace"][0]["ancestry"][0]["clicks"], True)
        self.assertTrue(result["trace"][0]["prevented"])
        self.assertEqual(result["trace"][0]["selected"], 8)

    def divider(self, tree, width=1248, height=383):
        shell = HERE.parents[1] / "text-desk-lab/notation/desk-shell/partition.js"
        setup = """
          const P=require(PATH);globalThis.window={Partition:P};
          const tree=TREE,bounds={x:0,y:0,w:WIDTH,h:HEIGHT};
          const options={minimum:[240,140],gap:16};
          const geo=P.geometry(tree.root,bounds,options),handles=[];
          for(const s of geo.splits)for(let i=0;i<s.children.length-1;i++){
            const a=s.children[i],x=s.node.axis==='x',b=x?
              {left:a.x+a.w+2,top:a.y,width:12,height:a.h}:
              {left:a.x,top:a.y+a.h+2,width:a.w,height:12};
            const h={className:'l-divider',getAttribute:()=>'Resize neighbouring panels',
              getBoundingClientRect:()=>b,contains:e=>e===h};handles.push(h);
          }
          const members=P.ids(tree.root).map(id=>({_n:{paint:{partition_item:id}}}));
          const root={clientWidth:WIDTH,clientHeight:HEIGHT,children:[...members,...handles],
            _n:{paint:{partition:{tree:JSON.stringify(tree),minimum:options.minimum,gap:16}}}};
          const document={querySelector:()=>root,elementFromPoint:(x,y)=>handles.find(h=>{
            const b=h.getBoundingClientRect();return x>=b.left&&x<=b.left+b.width&&y>=b.top&&y<=b.top+b.height;})};
        """
        setup = setup.replace("PATH", json.dumps(str(shell))).replace("TREE", json.dumps(tree))
        setup = setup.replace("WIDTH", str(width)).replace("HEIGHT", str(height))
        return self.run_js(setup, divider_candidate_js())

    def test_divider_chooses_direction_with_real_geometric_change(self):
        tree = dict(v=1, root=dict(axis="y", kids=[dict(id="a"), dict(id="b")],
                                  weights=[10000, 1]))
        self.assertEqual(self.divider(tree)["dy"], -40, "positive move is clamped, negative moves")
        self.assertIsNone(self.divider(tree, height=296), "both panels at minima: no fake success")

    def test_divider_skips_immovable_axis_for_movable_shared_boundary(self):
        tree = dict(v=1, root=dict(axis="x", kids=[
            dict(axis="y", kids=[dict(id="a"), dict(id="b")], weights=[1, 1]),
            dict(id="c")], weights=[1, 1]))
        result = self.divider(tree, height=296)
        self.assertEqual(result["dx"], 40)
        self.assertEqual(result["dy"], 0)

    def failed_step_with_cleanup_refusal(self, input_failure=False):
        class Page:
            async def js(self, source):
                if "data-sending" in source:
                    return True
                if "root &&" in source:
                    return dict(layout="layout", tree="before", focus="", id="a")
                if "const surface=" in source:
                    return [100, 100]
                if "return [b.left,b.top,b.width,b.height]" in source:
                    return [16, 20, 1248, 700]
                return "before"

            async def click(self, *args):
                if input_failure:
                    raise AssertionError("original input failure")

            async def drag(self, *args):
                pass

        class Copy:
            def do(self, line, who):
                return "ERR permission denied" if line.startswith("do prop") else "ok"

        async def timed(*args):
            return dict(ok=False, ms=None)

        play = SimpleNamespace(w=Page(), copy=Copy(), needs=lambda *args: None, timed=timed)
        return asyncio.run(bind(play, None)())

    def test_cleanup_refusal_keeps_failed_journey_result(self):
        result = self.failed_step_with_cleanup_refusal()
        self.assertFalse(result["ok"])
        self.assertIn("global bottom drop", result["want"])
        self.assertIn("cleanup also failed", result["want"])

    def test_cleanup_refusal_keeps_original_input_exception(self):
        with self.assertRaisesRegex(AssertionError, "original input failure;.*cleanup also failed"):
            self.failed_step_with_cleanup_refusal(input_failure=True)


if __name__ == "__main__":
    unittest.main()
