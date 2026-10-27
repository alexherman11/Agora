// DOM stand-in: actual adapter events/commands, not browser/layout acceptance.
const assert = require("node:assert/strict");
const P = require("../../text-desk-lab/notation/desk-shell/partition.js");
const { install } = require("../../text-desk-lab/notation/desk-shell/partition-ui.js");
const CarryTargets = require("../../text-desk-lab/notation/desk-shell/carry-targets.js");
class Element {
  constructor(tag="DIV", n=null) {
    this.tagName=tag; this._n=n; this.children=[]; this.dataset={}; this.style={}; this.listeners={};
    this.clientWidth=1280; this.clientHeight=800; this.hidden=false; this.textContent="";
    if(n) this.dataset.key=n.key;
  }
  get isConnected(){return !!this.parentElement || this===document.body;}
  get firstElementChild(){return this.children[0];}
  appendChild(e){this.children.push(e); e.parentElement=this; return e;}
  remove(){if(this.parentElement)this.parentElement.children=this.parentElement.children.filter(e=>e!==this); this.parentElement=null;}
  contains(el){return this===el || this.children.some(c=>c.contains(el));}
  getBoundingClientRect(){
    const p=this.parentElement?.getBoundingClientRect() || {left:0,top:0};
    return {left:p.left+(parseFloat(this.style.left)||0),top:p.top+(parseFloat(this.style.top)||0),
      width:parseFloat(this.style.width)||this.clientWidth,height:parseFloat(this.style.height)||this.clientHeight};
  }
  getClientRects(){return this.hidden || this.style.display==="none" ? [] : [this.getBoundingClientRect()];}
  setAttribute(k,v){this[k]=v;}
  removeAttribute(k){if(k==="data-key")delete this.dataset.key;else delete this[k];}
  addEventListener(k,f){(this.listeners[k] ||= []).push(f);}
  removeEventListener(k,f){this.listeners[k]=(this.listeners[k]||[]).filter(x=>x!==f);}
  fire(k,data={}){
    const e={type:k,button:0,pointerId:1,clientX:200,clientY:100,target:this,preventDefault(){this.prevented=true;},stopPropagation(){this.stopped=true;},...data};
    for(const f of [...(this.listeners[k]||[])])f(e); return e;
  }
  querySelectorAll(selector){
    const all=this.children.flatMap(c=>[c,...c.querySelectorAll("*")]);
    if(selector==="*")return all;
    if(selector==="[data-key]")return all.filter(e=>e.dataset.key);
    if(selector==="[data-drop]")return all.filter(e=>e.dataset.drop);
    if(selector==="[id],[data-key]")return all.filter(e=>e.id||e.dataset.key);
    if(selector==="[data-carry]")return all.filter(e=>e.dataset.carry);
    if(selector==="iframe,video,audio")return all.filter(e=>["IFRAME","VIDEO","AUDIO"].includes(e.tagName));
    return [];
  }
  querySelector(s){return this.querySelectorAll(s)[0];}
  matches(selector){
    return selector.split(",").some(s=>s==='[role="button"]' ? this.role==="button" :
      s==='[role="link"]' ? this.role==="link" : s.startsWith(".") && (this.className||"").split(" ").includes(s.slice(1)));
  }
  cloneNode(deep){
    const e=new Element(this.tagName,this._n); e.dataset={...this.dataset}; e.style={...this.style};
    e.clientWidth=this.clientWidth;e.clientHeight=this.clientHeight;e.textContent=this.textContent;
    if(deep)this.children.forEach(c=>e.appendChild(c.cloneNode(true)));return e;
  }
}
global.document=new Element(); document.body=new Element(); document.documentElement={dataset:{}};
document.createElement=tag=>new Element(tag.toUpperCase());
global.window=new Element(); let onResize;
let selectionClears=0;
window.getSelection=()=>({removeAllRanges(){selectionClears++;}});
window.CarryTargets=CarryTargets;
global.CarryTargets=CarryTargets; // CommonJS adapter captures globalThis at import.
let hits=[]; document.elementsFromPoint=()=>hits;
global.ResizeObserver=class {constructor(fn){onResize=fn;}observe(){}disconnect(){}};
let count=0;
function ok(fn){fn();count++;}
const settle=async()=>{await Promise.resolve();await Promise.resolve();await Promise.resolve();};
function treeFrom(line){
  const encoded=/tree="((?:\\.|[^"])*)"/.exec(line)[1];
  return P.model(JSON.parse(JSON.parse('"'+encoded.replace(/\\\$/g,"$")+'"')),["a","b","c"]);
}
async function main(){
  const tree={v:1,root:{axis:"x",kids:[{axis:"y",kids:[{id:"a"},{id:"c"}],weights:[1,1]},{id:"b"}],weights:[1,1]}};
  const n={key:"tiles",paint:{partition:{tree:JSON.stringify(tree),minimum:[240,140],gap:16,focus:"",magnetic:true}},
    acts:[{on:"arrange",line:'do prop layout tree="$value" full="$partition_focus"'},{on:"partition-focus",line:'do prop layout full="$value"'}],
    fence:{item:"layout",reads:[["layout",3,["prop:tree","prop:full"]]],defpart:{path:"root/tiles",hash:"one"}}};
  const paint=new Element(), root=new Element("DIV",n); paint.appendChild(root); document.body.appendChild(paint);
  function panel(id){
    const el=new Element("DIV",{key:id,paint:{partition_item:id,tip:[id,""]},acts:[]});
    const grip=new Element("DIV",{key:id+"/grip",part:"grip",paint:{},acts:[{on:"carry"}],fence:{item:id}});grip.dataset.carry="grip";grip.textContent=id;
    const draft=new Element("TEXTAREA");draft.value="keep this unsent";draft.selectionStart=4;
    el.appendChild(grip);el.appendChild(draft); root.appendChild(el); return {el,grip,draft};
  }
  const a=panel("a"),c=panel("c"),b=panel("b");
  b.el._n.paint.companion=true;
  const sent=[],holds=[];let refreshed=0,refuse=false,externalBusy=false,finishSend=null;
  let previewPlans=0;
  const ui=install(paint,{busy:()=>externalBusy,hold:x=>holds.push(x),refresh:()=>refreshed++,
    send:async(node,line,value,extra)=>{sent.push({node,line,extra});if(finishSend)await new Promise(resolve=>{finishSend=resolve;});if(!refuse&&line.includes(' tree="'))n.paint.partition.tree=JSON.stringify(P.encoded(treeFrom(line)));return refuse?{error:"stale"}:{};}},
    {...P,previewPlan(...args){previewPlans++;return P.previewPlan(...args);}});
  ui.sync();
  document.body.style.userSelect="text";
  ok(()=>assert.equal(root.dataset.partition,"1"));
  let lastPress;
  function begin(grip=a.grip,target=grip){
    lastPress={button:0,pointerId:1,clientX:200,clientY:100,target,preventDefault(){this.prevented=true;}};
    return ui.carry(grip,lastPress);
  }
  begin(); document.fire("pointermove",{clientX:202,clientY:102});document.fire("pointerup");
  ok(()=>assert.equal(sent.length,0,"click below threshold never writes geometry"));
  ok(()=>assert.equal(holds.length,0,"click never takes layout hold"));
  ok(()=>assert.equal(selectionClears,0,"stationary/sub-threshold clicks preserve selection"));
  ok(()=>assert.equal(document.body.style.userSelect,"text"));
  const tool=new Element("BUTTON");a.grip.appendChild(tool);begin(a.grip,tool);
  document.fire("pointermove",{clientX:700,clientY:799});document.fire("pointerup");
  ok(()=>assert.equal(sent.length,0,"header control never starts a drag"));
  ok(()=>assert.equal(selectionClears,0,"controls preserve selection"));
  const pickupTree=n.paint.partition.tree, pickupBoxes=P.geometry(tree.root,{x:0,y:0,w:1280,h:800}).boxes;
  const pickupDraft=a.draft, pickupParent=a.draft.parentElement;
  begin();document.fire("pointermove",{clientX:640,clientY:799});
  const hoverPlan=P.previewPlan(tree,"a",{global:true,side:"bottom"},{x:0,y:0,w:1280,h:800});
  for(const panel of [a,b,c]) {
    const box=P.geometry(hoverPlan.tree.root,{x:0,y:0,w:1280,h:800}).boxes[panel.el._n.paint.partition_item];
    ok(()=>assert.equal(parseFloat(panel.el.style.left),box.x,"hover reflows each real panel"));
    ok(()=>assert.equal(parseFloat(panel.el.style.height),box.h));
  }
  ok(()=>assert.notEqual(b.el.style.height,pickupBoxes.b.h+"px","neighbor moves before release"));
  ok(()=>assert.equal(n.paint.partition.tree,pickupTree,"hover does not write the world"));
  ok(()=>assert.equal(sent.length,0));
  ok(()=>assert.equal(a.draft,pickupDraft,"editor identity retained"));
  ok(()=>assert.equal(a.draft.parentElement,pickupParent,"editor never reparented"));
  const solved=previewPlans;
  for(let i=0;i<20;i++)document.fire("pointermove",{clientX:640+i*.1,clientY:799});
  ok(()=>assert.equal(previewPlans,solved,"stable target avoids solving on every ghost move"));
  // This point is in the original b, but the reflowed a now occupies it.
  // Hit testing our own preview would either cancel or oscillate.
  document.fire("pointermove",{clientX:900,clientY:500});
  const frozenTarget=P.hit({x:0,y:0,w:1280,h:800},pickupBoxes,{x:900,y:500},"a");
  const frozenPlan=P.previewPlan(tree,"a",frozenTarget,{x:0,y:0,w:1280,h:800});
  const frozenGeo=P.geometry(frozenPlan.tree.root,{x:0,y:0,w:1280,h:800});
  for(const panel of [a,b,c])ok(()=>assert.equal(panel.el.style.display,frozenGeo.boxes[panel.el._n.paint.partition_item]?"":"none","snap uses pickup geometry"));
  ui.sync();ok(()=>assert.equal(n.paint.partition.tree,pickupTree,"incoming sync during preview cannot rebase the tree"));
  document.fire("pointermove",{clientX:640,clientY:799});
  ok(()=>assert.equal(selectionClears,1,"threshold drag clears native text selection"));
  ok(()=>assert.equal(document.body.style.userSelect,"none","carry cannot select article text"));
  const ghost=document.body.children.find(e=>e!==paint), preview=root.children.find(e=>e.className==="landing-box");
  ok(()=>assert.equal(ghost.style.height,a.el.style.height,"whole panel, not grip, is cloned"));
  ok(()=>assert.equal(ghost.querySelectorAll("[data-key]").length,0));
  ok(()=>assert.equal(parseFloat(preview.style.width),1280,"global bottom preview spans desk"));
  const proposed={x:parseFloat(preview.style.left),y:parseFloat(preview.style.top),w:parseFloat(preview.style.width),h:parseFloat(preview.style.height)};
  onResize();ok(()=>assert.ok(ui.busy(),"observer cannot replace a drag"));
  const oldTools=root.children.filter(e=>e.className==="l-divider"||e.className==="partition-tool");
  finishSend=true;
  document.fire("pointerup",{clientX:640,clientY:799});
  ok(()=>assert.equal(document.body.style.userSelect,"text","release restores prior selection policy"));
  ok(()=>assert.ok(oldTools.every(e=>!e.parentElement),"old geometry tools removed before world answer"));
  ok(()=>assert.equal(root.children.filter(e=>e.className==="l-divider"||e.className==="partition-tool").length,0));
  ok(()=>assert.equal(parseFloat(a.el.style.width),proposed.w,"released geometry remains while answer is delayed"));
  ok(()=>assert.equal(ui.busy(),true,"pending geometry cannot accept a second write"));
  const pendingClears=selectionClears;
  begin();ok(()=>assert.equal(lastPress.prevented,true,"pending title press cancels native selection/drag default"));
  document.fire("pointermove",{clientX:1279,clientY:400});document.fire("pointerup");
  ok(()=>assert.equal(selectionClears,pendingClears,"declined carry preserves unrelated page ranges"));
  ok(()=>assert.equal(document.body.style.userSelect,"text","declined carry needs no leaked policy override"));
  ok(()=>assert.equal(sent.length,1,"declined carry sends no second write"));
  begin(a.grip,tool);
  ok(()=>assert.equal(lastPress.prevented,true,"pending grip action guards selection; its click remains separate"));
  onResize();ui.sync();
  ok(()=>assert.equal(root.children.filter(e=>e.className==="l-divider"||e.className==="partition-tool").length,0,
    "observer and sync cannot resurrect stale tools during a delayed answer"));
  finishSend();finishSend=null;await settle();ui.sync();
  ok(()=>assert.ok(root.children.some(e=>e.className==="l-divider"),"answered tree rebuilds tools"));
  ok(()=>assert.equal(sent.length,1));
  ok(()=>assert.deepEqual(sent[0].node.fence,n.fence,"one whole-tree fenced gesture"));
  ok(()=>assert.deepEqual(P.geometry(treeFrom(sent[0].line).root,{x:0,y:0,w:1280,h:800}).boxes.a,proposed));
  ok(()=>assert.equal(a.draft.value,"keep this unsent"));
  ok(()=>assert.equal(a.draft.selectionStart,4));
  // Reload from the persisted prop reconstructs the same rectangle.
  ok(()=>assert.equal(parseFloat(a.el.style.width),proposed.w));
  for(const cancel of ["pointercancel","Escape","blur","resize"]){
    const original=[a,b,c].map(p=>({...p.el.style})), model=n.paint.partition.tree;
    a.draft.scrollTop=37;
    begin();document.fire("pointermove",{clientX:20,clientY:300});
    a.draft.scrollTop=0; // stand-in for scroll clamping caused by smaller allocation
    if(cancel==="Escape")document.fire("keydown",{key:"Escape"});
    else if(cancel==="pointercancel")document.fire("pointercancel");
    else window.fire(cancel);
    await settle();
    ok(()=>assert.equal(sent.length,1,`${cancel} does not persist`));
    ok(()=>assert.ok(!ui.busy()));
    ok(()=>assert.equal(document.body.style.userSelect,"text",`${cancel} restores selection policy`));
    ok(()=>assert.equal(n.paint.partition.tree,model,`${cancel} preserves exact tree`));
    ok(()=>assert.equal(a.draft.scrollTop,37,`${cancel} restores reading offset`));
    for(let i=0;i<3;i++)ok(()=>assert.deepEqual([a,b,c][i].el.style,original[i],`${cancel} restores original panel allocation`));
  }
  ui.sync();
  let handle=root.children.find(e=>e.className==="l-divider"&&e.dataset.axis==="y");
  ok(()=>assert.equal(handle["aria-orientation"],"horizontal"));
  handle.fire("keydown",{key:"ArrowDown"});handle.fire("keydown",{key:"ArrowDown"});handle.fire("keydown",{key:"Enter"});
  await settle();ui.sync();ok(()=>assert.equal(sent.length,2,"keyboard divider commits once"));
  handle=root.children.find(e=>e.className==="l-divider"&&e.dataset.axis==="x");
  handle.fire("pointerdown");document.fire("pointermove",{clientX:250});document.fire("pointerup");await settle();ui.sync();
  ok(()=>assert.equal(sent.length,3,"vertical divider commits once"));
  externalBusy=true;begin();document.fire("pointermove",{clientY:799});document.fire("pointerup");
  ok(()=>assert.equal(lastPress.prevented,true,"other adapter's busy state also cancels native title selection"));
  externalBusy=false;ok(()=>assert.equal(sent.length,3,"another carry excludes a second gesture"));
  const before=n.paint.partition.tree;refuse=true;
  begin();document.fire("pointermove",{clientX:1279,clientY:400});document.fire("pointerup");await settle();ui.sync();
  ok(()=>assert.equal(n.paint.partition.tree,before,"a refusal leaves the durable tree untouched"));refuse=false;
  ok(()=>assert.equal(parseFloat(a.el.style.width),P.geometry(P.model(before,["a","b","c"]).root,{x:0,y:0,w:1280,h:800}).boxes.a.w,"refusal repaints world geometry"));
  const nested=new Element("DIV",{key:"inner-card",paint:{},fence:{item:"another-thing"}});
  a.el.appendChild(nested);
  ok(()=>assert.equal(begin(nested),false,"nested application carry remains the application's gesture"));
  const sentBefore=sent.length;
  begin();ui.sync();document.fire("pointermove",{clientX:30,clientY:500});document.fire("pointerup");
  ok(()=>assert.equal(sent.length,sentBefore,"repaint while merely armed cannot rebase an old plan onto a fresh fence"));
  // Tab centre is an explicit model move; selecting it writes that same model.
  n.paint.partition.tree=JSON.stringify(P.drop(P.model(before,["a","b","c"]),"a","b","centre"));
  ui.sync();
  const tab=root.children.find(e=>e.tagName==="BUTTON"&&e.title==="Show b");tab.fire("click");await settle();ui.sync();
  ok(()=>assert.ok(JSON.parse(n.paint.partition.tree).root));
  ok(()=>assert.equal(a.el.style.display,"none"));
  const fit=root.children.find(e=>e.tagName==="BUTTON"&&e.title==="Fit content");fit.fire("click");await settle();ui.sync();
  ok(()=>assert.ok(n.paint.partition.tree.includes('"size":"content"')));
  n.paint.partition.focus="a";ui.sync();
  ok(()=>assert.notEqual(b.el.style.display,"none","pinned companion remains beside focus"));
  const ordinaryRoot=JSON.parse(n.paint.partition.tree).root;
  handle=root.children.find(e=>e.className==="l-divider"&&e.dataset.axis==="x");
  handle.fire("keydown",{key:"ArrowRight"});handle.fire("keydown",{key:"Enter"});
  await settle();ui.sync();
  ok(()=>assert.ok(P.model(n.paint.partition.tree,["a","b","c"]).focus_weights.a.b>0,"focused divider weights persist"));
  ok(()=>assert.deepEqual(JSON.parse(n.paint.partition.tree).root,ordinaryRoot,"focused resize preserves ordinary tree"));
  ok(()=>assert.ok(sent.at(-1).line.endsWith('full="a"'),"focused resize keeps full selection"));
  const restoreBefore=n.paint.partition.tree;
  n.paint.partition.focus="";ui.sync();
  ok(()=>assert.equal(n.paint.partition.tree,restoreBefore,"focus does not destroy the normal tree"));
  // Keyboard whole-panel move.
  ui.key(b.grip,{key:" ",target:b.grip,preventDefault(){}});
  ui.key(b.grip,{key:"ArrowDown",target:b.grip,preventDefault(){}});
  ui.key(b.grip,{key:"Enter",target:b.grip,preventDefault(){}});
  await settle();
  ok(()=>assert.equal(JSON.parse(n.paint.partition.tree).root.axis,"y"));
  ok(()=>assert.equal(holds.at(-1),false));
  ok(()=>assert.ok(refreshed>0));
  // A bare app has its own carry region; source supplies that region without
  // turning the playback surface into a draggable catch-all.
  a.el._n.paint.chrome="none";a.el._n.paint.sizing="content";
  n.paint.partition.tree=JSON.stringify(P.encoded(tree));n.paint.partition.focus="";
  ui.sync();
  ok(()=>assert.equal(root.children.filter(e=>e.tagName==="BUTTON"&&e.title==="Fit content").length,2,
    "bare surface has no generated Fit/fill chrome"));
  const contentHandle=root.children.find(e=>e["aria-label"]==="Resize content width");
  contentHandle.fire("keydown",{key:"ArrowLeft"});contentHandle.fire("keydown",{key:"Enter"});
  await settle();ui.sync();
  ok(()=>assert.ok(n.paint.partition.tree.includes('"extent":['),"bare content edge persists manual extent"));
  const playback=new Element("BUTTON");a.el.appendChild(playback);
  const beforeBare=sent.length;begin(a.grip,playback);
  document.fire("pointermove",{clientY:799});document.fire("pointerup");
  ok(()=>assert.equal(sent.length,beforeBare,"playback/heart control never becomes a panel drag"));
  begin();document.fire("pointermove",{clientX:600,clientY:799});document.fire("pointerup");await settle();
  ok(()=>assert.equal(sent.length,beforeBare+1,"bare app grip still moves the whole panel"));
  ui.sync();
  // Combined adapter contract: use the real CarryTargets session, with DOM
  // stand-ins only. The dock is a separate placed lens outside the partition.
  const dock=new Element("DIV",{key:"dock",paint:{},fence:{item:"dock",rev:3}});
  dock.dataset.drop="any";dock._drops=[{part:"any",line:"do dock-pin $carried"}];
  dock.style.top="804px";dock.style.height="36px";paint.appendChild(dock);
  const internal=new Element("DIV",{key:"inside",paint:{},fence:{item:"inside"}});
  internal.dataset.drop="any";internal._drops=[{part:"any",line:"do old-column-drop"}];
  root.appendChild(internal);
  const moveDock=()=>{hits=[dock];document.fire("pointermove",{clientX:600,clientY:820});};
  let baseline=sent.length;
  hits=[dock];begin();document.fire("pointermove",{clientX:203,clientY:102});document.fire("pointerup");
  ok(()=>assert.equal(sent.length,baseline,"sub-threshold move over dock never pins or resizes"));
  ok(()=>assert.equal(document.body.children.filter(e=>e.className==="landing-box").length,0));
  hits=[];
  const unchanged=n.paint.partition.tree, sourceFence=a.grip._n.fence, receiverFence=dock._n.fence;
  begin();document.fire("pointermove",{clientX:600,clientY:799});moveDock();
  ok(()=>assert.equal(root.children.find(e=>e.className==="landing-box").hidden,true,
    "external receiver hides the split preview"));
  ok(()=>assert.equal(document.body.children.filter(e=>e.className==="landing-box").length,1,
    "one external landing box accompanies the whole-panel ghost"));
  finishSend=true;
  document.fire("pointerup",{clientX:600,clientY:820});
  ok(()=>assert.equal(sent.length,baseline+1,"dock release sends once, never a split too"));
  ok(()=>assert.equal(sent.at(-1).line,"do dock-pin $carried"));
  ok(()=>assert.deepEqual(sent.at(-1).extra,{carried:sourceFence,receiver:receiverFence},
    "source and receiver pickup fences both reach transport"));
  ok(()=>assert.equal(sent.at(-1).node.fence,receiverFence));
  ok(()=>assert.equal(n.paint.partition.tree,unchanged,"external pin never rearranges the durable tree"));
  ok(()=>assert.equal(ui.busy(),true,"pending dock answer excludes another gesture"));
  ok(()=>assert.equal(document.body.style.userSelect,"text","dock release restores selection policy"));
  begin();document.fire("pointermove",{clientX:800,clientY:820});document.fire("pointerup");
  ok(()=>assert.equal(sent.length,baseline+1));
  finishSend();finishSend=null;await settle();await settle();ui.sync();
  ok(()=>assert.equal(ui.busy(),false));
  ok(()=>assert.equal(document.body.children.filter(e=>e.className==="landing-box").length,0));
  // Leaving the dock restores the normal split planner; internal old receivers
  // under the partition must never steal that plan.
  baseline=sent.length;begin();moveDock();hits=[internal];
  document.fire("pointermove",{clientX:640,clientY:799});document.fire("pointerup");
  await settle();ui.sync();
  ok(()=>assert.equal(sent.length,baseline+1));
  ok(()=>assert.ok(sent.at(-1).line.includes(' tree="'),"leaving dock commits only the split"));
  for(const cancel of ["pointercancel","Escape","blur","resize"]){
    baseline=sent.length;begin();moveDock();
    if(cancel==="Escape")document.fire("keydown",{key:"Escape"});
    else if(cancel==="pointercancel")document.fire("pointercancel");
    else window.fire(cancel);
    await settle();ui.sync();
    ok(()=>assert.equal(sent.length,baseline,`external ${cancel} sends nothing`));
    ok(()=>assert.equal(document.body.children.filter(e=>e.className==="landing-box").length,0));
  }
  // Repainting/changing a receiver cannot substitute its fresh act/fence.
  baseline=sent.length;begin();moveDock();
  dock._n={...dock._n,fence:{item:"dock",rev:99}};
  dock._drops=[{part:"any",line:"do surprise"}];
  a.grip._n={...a.grip._n,fence:{item:"a",rev:99}};
  moveDock();refuse=true;
  const beforeRefusal=n.paint.partition.tree;
  document.fire("pointerup");await settle();await settle();ui.sync();refuse=false;
  ok(()=>assert.equal(sent.length,baseline+1));
  ok(()=>assert.equal(sent.at(-1).line,"do dock-pin $carried"));
  ok(()=>assert.equal(sent.at(-1).extra.carried,sourceFence));
  ok(()=>assert.equal(sent.at(-1).extra.receiver,receiverFence));
  ok(()=>assert.equal(n.paint.partition.tree,beforeRefusal,"refused external drop never falls through to split"));
  ok(()=>assert.equal(a.draft.value,"keep this unsent"));
  ok(()=>assert.equal(a.draft.selectionStart,4));
  // A newly painted receiver after pickup was never an offered destination.
  baseline=sent.length;begin();hits=[];document.fire("pointermove",{clientX:640,clientY:799});
  const late=new Element("DIV",{key:"late",paint:{},fence:{item:"late"}});
  late.dataset.drop="any";late._drops=[{part:"any",line:"do late"}];paint.appendChild(late);
  hits=[late];document.fire("pointermove",{clientX:600,clientY:820});
  ok(()=>assert.equal(document.body.children.filter(e=>e.className==="landing-box").length,0,
    "receiver painted after pickup offers no external preview"));
  document.fire("pointercancel");await settle();
  ok(()=>assert.equal(sent.length,baseline));
  hits=[];
  // Consecutive carries need no harness selection-clearing workaround.
  ui.sync();
  let clearsBefore=selectionClears;
  begin();document.fire("pointermove",{clientX:640,clientY:799});
  document.fire("pointerup");await settle();ui.sync();
  begin();document.fire("pointermove",{clientX:1,clientY:400});
  ok(()=>assert.equal(selectionClears,clearsBefore+2,"both consecutive carries clear only on pickup"));
  ok(()=>assert.equal(document.body.style.userSelect,"none"));
  document.fire("pointercancel");await settle();ui.sync();
  ok(()=>assert.equal(document.body.style.userSelect,"text"));
  // Refusal restores authoritative geometry and freshly generated controls.
  const durable=n.paint.partition.tree;
  const oldRect={...a.el.style};
  const obsolete=root.children.filter(e=>e.className==="l-divider"||e.className==="partition-tool");
  refuse=true;finishSend=true;
  begin();document.fire("pointermove",{clientX:1279,clientY:400});document.fire("pointerup");
  ok(()=>assert.ok(obsolete.every(e=>!e.parentElement),"refused-but-unanswered drop has no obsolete hit targets"));
  const writes=sent.length;
  begin();document.fire("pointermove",{clientX:1,clientY:400});document.fire("pointerup");
  ok(()=>assert.equal(sent.length,writes,"immediate press cannot write against pending geometry"));
  finishSend();finishSend=null;await settle();ui.sync();refuse=false;
  ok(()=>assert.equal(n.paint.partition.tree,durable));
  ok(()=>assert.equal(a.el.style.left,oldRect.left,"refusal restores authoritative placement"));
  ok(()=>assert.equal(a.el.style.width,oldRect.width));
  ok(()=>assert.ok(root.children.some(e=>e.className==="l-divider"),"rollback rebuilds current separators"));
  ok(()=>assert.equal(a.draft.value,"keep this unsent"));
  ok(()=>assert.equal(a.draft.selectionStart,4,"composer caret is independent of page selection"));
  // Resizing has the same delayed-answer boundary, including keyboard handles.
  handle=root.children.find(e=>e.className==="l-divider");
  const arrow=handle.dataset.axis==="x"?"ArrowRight":"ArrowDown";
  handle.fire("keydown",{key:arrow});finishSend=true;
  handle.fire("keydown",{key:"Enter"});
  ok(()=>assert.equal(root.children.filter(e=>e.className==="l-divider"||e.className==="partition-tool").length,0,
    "divider release also removes obsolete targets before the answer"));
  finishSend();finishSend=null;await settle();ui.sync();
  // Simulate the measured 380/383 focus-sensitive frame. Size/layout
  // containment is a CSS contract, not a stand-in browser layout proof.
  Object.defineProperty(root,"clientHeight",{configurable:true,
    get:()=>root.style.contain==="size layout"?383:(n.paint.partition.focus?380:383)});
  root.clientWidth=1248;
  n.paint.partition.focus="a";ui.sync();
  ok(()=>assert.equal(root.style.contain,"size layout","partition establishes its own bounded sizing/baseline context"));
  begin(b.grip);document.fire("pointermove",{clientX:600,clientY:382});
  const focusPreview=root.children.find(e=>e.className==="landing-box");
  const focusBox={left:focusPreview.style.left,top:focusPreview.style.top,
    width:focusPreview.style.width,height:focusPreview.style.height};
  document.fire("pointerup");await settle();
  n.paint.partition.focus="";ui.sync();
  ok(()=>assert.equal(b.el.style.top,focusBox.top,"focus exit uses the same simulated frame as its preview"));
  ok(()=>assert.equal(b.el.style.height,focusBox.height));
  // Round 5: passive named-lens descendants are grip interior, not controls.
  // These are event/default-policy stand-ins, not Chromium selection evidence.
  await new Promise(resolve=>setTimeout(resolve,0));
  const summary=new Element("DIV",{key:"a/grip/sum/lens:summary",paint:{},fence:{item:"summary-definition"}});
  a.grip.appendChild(summary);
  for(const title of ["The board","7 need you","1 moving","1 wait on JEFF"]){
    const text=new Element("DIV",{key:"summary/"+title,paint:{},fence:{item:"summary-definition"}});
    text.textContent=title;summary.appendChild(text);
    let baseline=sent.length, clears=selectionClears;
    ok(()=>assert.equal(begin(a.grip,text),true));
    ok(()=>assert.equal(lastPress.prevented,true,`${title}: owns initial press before native selection`));
    document.fire("pointermove",{clientX:202,clientY:102});document.fire("pointerup");
    ok(()=>assert.equal(sent.length,baseline,`${title}: click cannot write/snap`));
    ok(()=>assert.equal(selectionClears,clears,`${title}: click preserves ranges`));
    externalBusy=true;begin(a.grip,text);
    ok(()=>assert.equal(lastPress.prevented,true,`${title}: busy press still owns native default`));
    document.fire("pointermove",{clientX:600,clientY:378});document.fire("pointerup");
    externalBusy=false;
    ok(()=>assert.equal(selectionClears,clears,`${title}: busy decline keeps ranges`));
    ok(()=>assert.equal(sent.length,baseline,`${title}: busy decline cannot queue a write`));
    begin(a.grip,text);document.fire("pointermove",{clientX:600,clientY:378});
    ok(()=>assert.equal(document.body.children.filter(e=>e!==paint).length,1,`${title}: one whole-panel ghost`));
    ok(()=>assert.equal(selectionClears,clears+1,`${title}: one threshold pickup`));
    document.fire("pointercancel");await settle();ui.sync();
    ok(()=>assert.equal(sent.length,baseline,`${title}: cancel cannot persist`));
    ok(()=>assert.equal(document.body.style.userSelect,"text"));
  }
  // Only real click dispatch in Chromium can certify activation behavior.
  // Here exercise the adapter's actual capture guard before stand-in actions.
  await new Promise(resolve=>setTimeout(resolve,0));
  async function click(control){
    const event=window.fire("click",{target:control});
    if(!event.stopped)control.fire("click");
    await new Promise(resolve=>setTimeout(resolve,0));
    return event;
  }
  for(const name of ["pin","away","native button","native link","role button","marked name"]){
    const control=new Element(name==="native button"?"BUTTON":name==="native link"?"A":"DIV");
    if(name==="role button")control.role="button";
    else if(name==="marked name")control.className="t-mark-thing";
    else if(!name.startsWith("native"))control._clicks=true;
    const label=new Element("SPAN");control.appendChild(label);a.grip.appendChild(control);
    let actions=0;control.addEventListener("click",()=>actions++);
    const baseline=sent.length, clears=selectionClears;
    begin(a.grip,label);
    ok(()=>assert.equal(lastPress.prevented,true,`${name}: no native page selection`));
    document.fire("pointerup");
    await click(control);
    ok(()=>assert.equal(actions,1,`${name}: stationary click remains an action`));
    begin(a.grip,label);document.fire("pointermove",{clientX:240});
    document.fire("pointermove",{clientX:200});document.fire("pointerup");
    const draggedClick=await click(control);
    ok(()=>assert.equal(draggedClick.prevented,true,`${name}: returning drag cannot activate`));
    ok(()=>assert.equal(actions,1));
    ok(()=>assert.equal(sent.length,baseline,`${name}: no panel carry`));
    ok(()=>assert.equal(selectionClears,clears,`${name}: preserves composer/page ranges`));
    ok(()=>assert.equal(document.body.style.userSelect,"text"));
    for(const cancel of ["Escape","blur","resize","pointercancel"]){
      begin(a.grip,label);
      if(cancel==="Escape")document.fire("keydown",{key:"Escape"});
      else if(cancel==="pointercancel")document.fire("pointercancel");
      else window.fire(cancel);
      if(cancel!=="pointercancel"){
        // Non-pointer cancellation can precede the physical release by a while.
        await new Promise(resolve=>setTimeout(resolve,0));
        document.fire("pointerup");
      }
      const cancelledClick=await click(control);
      ok(()=>assert.equal(cancelledClick.prevented,true,`${name}: ${cancel} suppresses release click`));
      ok(()=>assert.equal(actions,1));
    }
    externalBusy=true;begin(a.grip,label);document.fire("pointermove",{clientX:240});document.fire("pointerup");
    await click(control);externalBusy=false;
    ok(()=>assert.equal(actions,1,`${name}: busy control drag cannot activate`));
    ok(()=>assert.equal(sent.length,baseline));
    ok(()=>assert.equal(a.draft.selectionStart,4));
  }
  for(const tag of ["INPUT","TEXTAREA","SELECT","DIV"]){
    const editor=new Element(tag);if(tag==="DIV")editor.isContentEditable=true;
    const child=tag==="DIV"?new Element("SPAN"):editor;
    if(child!==editor)editor.appendChild(child);
    a.grip.appendChild(editor);
    const baseline=sent.length, clears=selectionClears;
    begin(a.grip,child);document.fire("pointermove",{clientX:600});document.fire("pointerup");
    ok(()=>assert.notEqual(lastPress.prevented,true,`${tag}: native input is untouched`));
    ok(()=>assert.equal(sent.length,baseline));
    ok(()=>assert.equal(selectionClears,clears));
  }
  ok(()=>assert.equal(a.draft.value,"keep this unsent"));
  ok(()=>assert.equal(a.draft.selectionStart,4,"grip and control guards never alter draft selection"));
  // The tab fallback uses the same DOM and candidate for keyboard carries.
  Object.defineProperty(root,"clientHeight",{configurable:true,writable:true,value:480});
  delete a.el._n.paint.sizing;
  const narrowTree={v:1,root:{axis:"y",kids:[{id:"a"},{id:"b"},{id:"c"}],weights:[1,1,1]}};
  for(const width of [320,420,600]){
    root.clientWidth=width;root.clientHeight=480;n.paint.partition.tree=JSON.stringify(narrowTree);n.paint.partition.focus="";ui.sync();
    const saved=n.paint.partition.tree, beforeSend=sent.length;
    ui.key(a.grip,{key:" ",target:a.grip,preventDefault(){}});
    ui.key(a.grip,{key:"ArrowRight",target:a.grip,preventDefault(){}});
    const preview=root.children.find(e=>e.className==="landing-box");
    ok(()=>assert.ok(parseFloat(preview.style.width)>=240,`narrow ${width}: ${JSON.stringify(preview.style)} hidden=${preview.hidden}`));
    for(const panel of [a,b,c])if(panel.el.style.display!=="none"){
      ok(()=>assert.ok(parseFloat(panel.el.style.width)>=240));
      ok(()=>assert.ok(parseFloat(panel.el.style.height)>=140));
    }
    document.fire("keydown",{key:"Escape"});
    ok(()=>assert.equal(n.paint.partition.tree,saved));
    ok(()=>assert.equal(sent.length,beforeSend));
    ok(()=>assert.equal(a.draft.parentElement,pickupParent));
  }
  root.clientWidth=1280;root.clientHeight=800;n.paint.partition.tree=JSON.stringify(tree);ui.sync();
  // A real newer authoritative scene wins after an old fenced drop refuses.
  begin();document.fire("pointermove",{clientX:640,clientY:799});
  const concurrent={...tree,root:{...tree.root,weights:[3,1]}}, newText=JSON.stringify(concurrent);
  n.paint.partition.tree=newText;ui.sync();refuse=true;
  document.fire("pointerup");await settle();ui.sync();refuse=false;
  ok(()=>assert.equal(n.paint.partition.tree,newText,"refused old candidate cannot overwrite newer layout"));
  const current=P.geometry(concurrent.root,{x:0,y:0,w:1280,h:800});
  for(const panel of [a,b,c])ok(()=>assert.equal(parseFloat(panel.el.style.width),current.boxes[panel.el._n.paint.partition_item].w,"latest scene converges"));
  // Stand-in focus loss: restore body-only loss, never an intentional new
  // editor, and never replay an obsolete pickup-time caret after typing.
  a.draft.focus=()=>{document.activeElement=a.draft;};
  document.activeElement=a.draft;
  begin();document.fire("pointermove",{clientX:640,clientY:799});
  a.draft.value+=" more";a.draft.selectionStart=9;document.activeElement=document.body;
  document.fire("pointercancel");await settle();ui.sync();
  ok(()=>assert.equal(document.activeElement,a.draft));
  ok(()=>assert.equal(a.draft.selectionStart,9,"new caret is not reset to pickup position"));
  ok(()=>assert.equal(a.draft.value,"keep this unsent more"));
  begin();document.fire("pointermove",{clientX:640,clientY:799});
  document.activeElement=b.draft;
  document.fire("pointercancel");await settle();ui.sync();
  ok(()=>assert.equal(document.activeElement,b.draft,"intentional focus move is not stolen"));
  console.log(`${count} partition DOM gesture checks passed (stand-in; no browser)`);
}
main().catch(e=>{console.error(e);process.exitCode=1;});
