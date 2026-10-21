// A DOM/event stand-in exercises gesture lifetime and commands, not visual acceptance.
const assert = require("node:assert/strict");
const {install} = require("../../text-desk-lab/notation/desk-shell/dividers.js");
class Element {
  constructor(key, flow, rect, n) {
    this.dataset = key ? {key} : {}; this.rect = rect; this._n = n;
    this.children = []; this.listeners = {}; this.style = {}; this.hidden = false;
    this.clientWidth = rect.width; this.clientHeight = rect.height; this.clientLeft = this.clientTop = 0;
    this.classList = {contains: c => c === flow};
  }
  appendChild(e) { this.children.push(e); e.parentElement = this; }
  remove() { this.parentElement.children = this.parentElement.children.filter(e => e !== this); }
  getBoundingClientRect() { return {...this.rect, right:this.rect.left+this.rect.width, bottom:this.rect.top+this.rect.height}; }
  getClientRects() { return this.hidden ? [] : [this.rect]; }
  setAttribute(k,v) { this[k] = v; }
  setPointerCapture() {}
  addEventListener(k,f) { (this.listeners[k] ||= []).push(f); }
  removeEventListener(k,f) { this.listeners[k] = (this.listeners[k] || []).filter(x => x !== f); }
  fire(k, data={}) { for (const f of [...(this.listeners[k] || [])]) f({type:k,button:0,clientX:500,clientY:250,preventDefault(){},stopPropagation(){},...data}); }
}
let resize;
global.ResizeObserver = class { constructor(f){ resize=f; } observe(){} disconnect(){} };
global.getComputedStyle = el => ({
  display:"flex",boxSizing:"border-box",columnGap:"16",rowGap:"16",paddingLeft:"0",paddingRight:"0",paddingTop:"0",paddingBottom:"0",
  borderLeftWidth:"0",borderRightWidth:"0",borderTopWidth:"0",borderBottomWidth:"0"
});
global.document = new Element(null,null,{});
document.documentElement = {dataset:{}};
document.createElement = () => new Element(null,null,{});
global.window = new Element(null,null,{});
function node(id) {
  return {key:id,paint:{share:1,resize:["weight",140]},acts:[{on:"resize",line:`do prop ${id} weight=$value`}],
    fence:{item:id,reads:[[id,1,["prop:weight"]]],defpart:{path:"root/panel",hash:"hash",lens:"tiles"}}};
}
async function main() {
  const paint = new Element("paint",null,{});
  const parent = new Element("root","l-row",{left:0,top:0,width:1016,height:500});
  const a = new Element("a","l-column",{left:0,top:0,width:500,height:500},node("a"));
  const b = new Element("b","l-column",{left:516,top:0,width:500,height:500},node("b"));
  paint.appendChild(parent); parent.appendChild(a); parent.appendChild(b);
  paint.querySelectorAll = () => [parent,a,b];
  const sent=[],held=[]; let busy=false, refreshed=0;
  const controller = install(paint,{busy:()=>busy,hold:v=>held.push(v),send:async(n,line)=>sent.push({n,line}),refresh:()=>refreshed++});
  const handle = () => parent.children.find(e=>e.className==="l-divider");
  controller.sync();
  assert.equal(handle().style.width,"12px");
  assert.equal(handle()["aria-orientation"],"vertical");
  assert.equal(a.style.flex,"1 1 140px");
  handle().fire("pointerdown"); assert.ok(controller.busy());
  handle().fire("pointermove",{clientX:600});
  assert.ok(Number(a.style.flexGrow)>1 && Number(b.style.flexGrow)<1);
  resize(); assert.ok(controller.busy(),"preview resize observer must not cancel the drag");
  handle().fire("pointercancel");
  assert.equal(sent.length,0); assert.equal(a.style.flexGrow,"1"); assert.equal(held.at(-1),false);
  controller.sync();
  handle().fire("pointerdown"); handle().fire("pointermove",{clientX:600}); handle().fire("pointerup");
  await Promise.resolve(); await Promise.resolve();
  assert.equal(sent.length,1);
  assert.match(sent[0].line,/^do prop a weight=[\d.]+; do prop b weight=[\d.]+$/);
  assert.deepEqual(sent[0].n.fence.reads,[["a",1,["prop:weight"]],["b",1,["prop:weight"]]]);
  assert.equal(held.at(-1),false); assert.equal(refreshed,1);
  controller.sync();
  handle().fire("keydown",{key:"ArrowLeft"}); document.fire("keydown",{key:"Escape"});
  assert.equal(sent.length,1); assert.ok(!controller.busy());
  handle().fire("pointerdown"); handle().fire("pointermove",{clientX:550}); window.fire("blur");
  assert.equal(sent.length,1); assert.ok(!controller.busy());
  busy=true; handle().fire("pointerdown"); assert.ok(!controller.busy()); busy=false;
  b.hidden=true; controller.sync(); assert.equal(handle(),undefined);
  b.hidden=false; b._n.fence.defpart.hash="changed";
  controller.sync(); assert.equal(handle(),undefined,"different definitions cannot share a single fenced proposal");
  b._n.fence.defpart.hash="hash"; parent.classList.contains=c=>c==="l-column";
  parent.clientHeight=1016; parent.rect.height=1016;
  b.rect={left:0,top:516,width:500,height:500};
  controller.sync(); assert.equal(handle()["aria-orientation"],"horizontal");
  handle().fire("keydown",{key:"ArrowDown"}); handle().fire("keydown",{key:"Enter"});
  await Promise.resolve(); await Promise.resolve();
  assert.equal(sent.length,2);
  console.log("12 divider pointer/keyboard/fence scenarios passed (DOM stand-in; no window)");
}
main().catch(e=>{console.error(e);process.exitCode=1;});
