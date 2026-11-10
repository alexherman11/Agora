"""Guarded-copy spatial navigation check; never sends a Conversation line."""
import sys
from playtest_steps import Step
from playtest_steps._support import Missing, json, q

ROOT = "document.querySelector('[data-partition]')"
PANEL = ("[...document.querySelector('[data-partition]').children]"
         ".find(e => e._n?.paint.partition_item && !e.hidden && e.style.display !== 'none' && e.querySelector('[data-carry]'))")

def carry_trace_js():
    # Copy-only observation: never cancel input, clear selection or send a line.
    return """(() => {
      const trace=[],listeners=[];
      const rect=e=>{if(!e)return null;const b=e.getBoundingClientRect();
        return [b.left,b.top,b.width,b.height];};
      for(const type of ['pointerdown','mousedown','dragstart','pointercancel']){
        const fn=e=>{
          const target=e.target,grip=target.closest?.('[data-carry]');
          if(!grip)return;
          const ancestry=[];
          for(let n=target;n&&ancestry.length<12;n=n.parentElement){
            ancestry.push({tag:n.tagName,key:n.dataset?.key,role:n._n?.paint?.role,
              clicks:!!n._clicks,editable:!!n.isContentEditable,carry:n.dataset?.carry,
              fence:n._n?.fence?.item,panel:n._n?.paint?.partition_item});
            if(n._n?.paint?.partition)break;
          }
          const entry={type,x:e.clientX,y:e.clientY,target:target.tagName,
            key:target.dataset?.key,grip:grip.dataset?.key,gripRect:rect(grip),
            targetRect:rect(target),ancestry};
          trace.push(entry);if(trace.length>80)trace.shift();
          queueMicrotask(()=>{entry.prevented=e.defaultPrevented;
            entry.selected=String(window.getSelection()).length;});
        };
        document.addEventListener(type,fn,true);listeners.push([type,fn]);
      }
      window.__partitionCarryTrace=()=>{for(const [type,fn] of listeners)
        document.removeEventListener(type,fn,true);return trace;};
      return true;
    })()"""


def edge_predicate(panel, side, bounds, old_tree):
    bx, by, bw, bh = bounds
    dimension, expected = ("width", bw) if side in ("top", "bottom") else ("height", bh)
    edge, coordinate = {"top": ("top", by), "bottom": ("bottom", by + bh),
                        "left": ("left", bx), "right": ("right", bx + bw)}[side]
    return (f"(() => {{ const p={panel}, r=p && p.getBoundingClientRect(); "
            f"return !!r && Math.abs(r.{dimension} - {expected}) <= 1 && "
            f"Math.abs(r.{edge} - {coordinate}) <= 1 && "
            f"({ROOT})._n.paint.partition.tree !== {json.dumps(old_tree)} && "
            f"({ROOT})._n.paint.partition.focus === ''; }})()")


def carry_point_js(panel):
    # Check the actual grip and hit element, not a parent that happens to cover
    # its centre. Do not scroll the desk or clear selection to make a test pass.
    return f"""(() => {{
      const surface={panel};
      for (const grip of surface.querySelectorAll('[data-carry]')) {{
        if(grip._n?.fence?.item!==surface._n.paint.partition_item)continue;
        if (grip.hidden || !grip.getClientRects().length) continue;
        const b=grip.getBoundingClientRect();
        for (const fy of [.5,.25,.75]) for (const fx of [.5,.1,.9]) {{
          const x=b.left+b.width*fx,y=b.top+b.height*fy,at=document.elementFromPoint(x,y);
          if (!at || !grip.contains(at)) continue;
          let control=false;
          for(let n=at;n&&n!==grip;n=n.parentElement)
            if(n.isContentEditable||/^(BUTTON|INPUT|TEXTAREA|SELECT|A)$/.test(n.tagName)||n._clicks||n.dataset?.tool) control=true;
          if(!control)return [x,y];
        }}
      }}
      return null;
    }})()"""


def divider_candidate_js():
    return f"""(() => {{
      const root={ROOT},P=window.Partition,spec=root._n.paint.partition;
      const members=[...root.children].filter(e=>e._n?.paint.partition_item);
      const visible=new Set(members.filter(e=>!e.hidden&&!e._n.paint.absent).map(e=>e._n.paint.partition_item));
      const tree=P.model(spec.tree,members.map(e=>e._n.paint.partition_item));
      const bounds={{x:0,y:0,w:root.clientWidth,h:root.clientHeight}};
      const options={{minimum:spec.minimum,gap:spec.gap,visible}};
      const geo=P.geometry(tree.root,bounds,options);
      const handles=[...root.children].filter(e=>e.className==='l-divider'&&
        /^Resize neighbouring /.test(e.getAttribute('aria-label')||''));
      let hindex=0;
      for(const split of geo.splits)for(let i=0;i<split.children.length-1;i++){{
        const h=handles[hindex++]; if(!h)continue;
        const b=h.getBoundingClientRect(),x=b.left+b.width/2,y=b.top+b.height/2;
        if(!h.contains(document.elementFromPoint(x,y)))continue;
        for(const delta of [40,-40]){{
          const next=P.resize(tree,split.path,i,delta,bounds,options);
          const after=P.geometry(next.root,bounds,options).splits.find(s=>JSON.stringify(s.path)===JSON.stringify(split.path));
          const axis=split.node.axis==='x'?'w':'h';
          if(after&&Math.abs(after.children[i][axis]-split.children[i][axis])>1)
            return {{x,y,dx:axis==='w'?delta:0,dy:axis==='h'?delta:0}};
        }}
      }}
      return null;
    }})()"""


async def restore_fixture(w, c, state):
    # Wait for the actual outstanding answer, not a fixed sleep. A geometry
    # predicate can become true optimistically before the page commits it.
    await w.js("""new Promise((resolve, reject) => {
      const start=performance.now();
      const tick=()=> {
        if (!document.querySelector('[data-sending="1"]')) return resolve(true);
        if (performance.now()-start>4000) return reject(new Error('navigation restore: answer still pending'));
        requestAnimationFrame(tick);
      }; tick();
    })""")
    for attempt in range(3):
        c.do(f"look {state['layout']}", "hud-playtest")
        said = c.do(f"do prop {state['layout']} tree={q(state['tree'])} full={q(state['focus'])}", "hud-playtest")
        if "ERR" not in said or "already has that;" in said:
            return
        if not any(word in said.lower() for word in ("stale", "changed since")):
            break
    raise AssertionError("copy navigation fixture restore refused: " + said[:300])


def bind(play, opened):
    async def check():
        play.needs("a7045", "world tree panel navigation", ("home-tiling", "partition tree"))
        w, c = play.w, play.copy
        state = await w.js(f"""(() => {{
          const root={ROOT}, panel=root && {PANEL};
          if (!root || !panel) return null;
          return {{layout:root._n.fence.item, tree:root._n.paint.partition.tree,
            focus:root._n.paint.partition.focus || '', id:panel._n.paint.partition_item}};
        }})()""")
        if not state:
            raise Missing("no visible partition and carried panel in the copied world")
        panel = f"[...({ROOT}).children].find(e => e._n?.paint.partition_item === {json.dumps(state['id'])})"
        async def title_point():
            point = await w.js(carry_point_js(panel))
            if not point:
                raise AssertionError("no visible, uncovered non-control carry point in the panel title")
            hit = await w.js(f"""(() => {{
              const [x,y]={json.dumps(point)}, at=document.elementFromPoint(x,y);
              const grip=at?.closest('[data-carry]');
              const rect=e=>{{if(!e)return null;const b=e.getBoundingClientRect();
                return [b.left,b.top,b.width,b.height];}};
              return {{point:[x,y],target:at?.tagName,key:at?.dataset?.key,
                grip:grip?.dataset?.key,gripRect:rect(grip),targetRect:rect(at)}};
            }})()""")
            print("partition_navigation carry hit: " + json.dumps(hit), flush=True)
            return point
        results = []
        await w.js(carry_trace_js())
        try:
            # A click is deliberately measured independently of all drags.
            before = await w.js(f"JSON.stringify(({ROOT})._n.paint.partition)")
            x, y = await title_point()
            await w.click(x, y)
            if await w.js(f"JSON.stringify(({ROOT})._n.paint.partition)") != before:
                raise AssertionError("stationary title click changed the world tree/focus")
            for side in ["bottom", "top", "left", "right"]:
                bounds = await w.js(f"""(() => {{
                  const b=({ROOT}).getBoundingClientRect();return [b.left,b.top,b.width,b.height];
                }})()""")
                bx, by, bw, bh = bounds
                target = {"bottom": (bx + bw / 2, by + bh - 2),
                          "top": (bx + bw / 2, by + 2),
                          "left": (bx + 2, by + bh / 2),
                          "right": (bx + bw - 2, by + bh / 2)}[side]
                x, y = await title_point()
                old_tree = await w.js(f"({ROOT})._n.paint.partition.tree")
                pred = edge_predicate(panel, side, bounds, old_tree)
                result = await play.timed(pred, lambda: w.drag(x, y, *target))
                results.append(result)
                if not result["ok"]:
                    result["want"] = f"global {side} drop did not persist at that desk edge"
                    return result
            # One divider gesture; the manual acceptance checklist covers every
            # split/axis, minima, preview shots and the second viewport.
            candidate = await w.js(divider_candidate_js())
            if not candidate:
                raise AssertionError("no uncovered shared divider can move by more than 1px at these minima")
            x, y, dx, dy = (candidate[key] for key in ("x", "y", "dx", "dy"))
            old = await w.js(f"({ROOT})._n.paint.partition.tree")
            changed = f"({ROOT})._n.paint.partition.tree !== {json.dumps(old)}"
            result = await play.timed(changed, lambda: w.drag(x, y, x + dx, y + dy))
            results.append(result)
            if not result["ok"]:
                result["want"] = "divider release did not persist the tree weights"
                return result
            return {**results[-1], "ms": max(r["ms"] for r in results),
                    "note": "title click unchanged; four global edge spans; one divider persisted; copy fixture restored"}
        finally:
            try:
                trace = await w.js("window.__partitionCarryTrace?.()")
                print("partition_navigation carry events: " + json.dumps(trace), flush=True)
            except Exception as diagnostic:
                print("partition_navigation trace unavailable: " + str(diagnostic), flush=True)
            # Restore only the disposable copy's fixture, including an empty prop.
            original = sys.exc_info()[1]
            try:
                await restore_fixture(w, c, state)
            except Exception as cleanup:
                if original:
                    raise AssertionError(f"{original}; copy fixture cleanup also failed: {cleanup}") from original
                if results and not results[-1]["ok"]:
                    results[-1]["want"] += f"; copy fixture cleanup also failed: {cleanup}"
                else:
                    raise
    return check


STEP = Step(name="partition_navigation",
            description="title click, four desk edges and a persistent divider",
            order=1850, needs=(("a7045", "world tree panel navigation"),), script=bind,
            assertion="title click leaves geometry; global drops span desk; divider saves weights",
            budget=(100, 300))
