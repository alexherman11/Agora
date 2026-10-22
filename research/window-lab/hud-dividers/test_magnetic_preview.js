// Pure geometry/solver checks. No browser, network, world or host effects.
const assert = require("node:assert/strict");
const P = require("../../text-desk-lab/notation/desk-shell/partition.js");
let count=0;
function check(fn){fn();count++;}
const tree={v:1,root:{axis:"x",kids:[{id:"a"},{id:"b"}],weights:[1,1]}};
const bounds={x:0,y:0,w:1000,h:700};
const options={minimum:[240,140],gap:16};
const boxes=P.geometry(tree.root,bounds,options).boxes;
const original=JSON.stringify(tree);
let snap=P.magneticHit(bounds,boxes,{x:961,y:350},"a",null);
check(()=>assert.deepEqual(snap.target,{global:true,side:"right"}));
for(const x of [960,959,953,950,959,961]) {
  snap=P.magneticHit(bounds,boxes,{x,y:350},"a",snap);
  check(()=>assert.equal(snap?.target.global,true,"12px spatial deadband across global edge"));
}
snap=P.magneticHit(bounds,boxes,{x:947,y:350},"a",snap);
check(()=>assert.equal(snap.target.global,false,"intentional movement leaves global snap"));
check(()=>assert.equal(P.magneticHit(bounds,boxes,{x:300,y:350},"a",snap),null,"dragged panel clears preview"));
// Local b's quarter-width boundary is x=631. Re-entering jitter cannot
// oscillate between left split and centre tab with a stationary pickup frame.
snap=P.magneticHit(bounds,boxes,{x:628,y:350},"a",null);
check(()=>assert.equal(snap.target.side,"left"));
for(const x of [630,632,639,642,634,628]){
  snap=P.magneticHit(bounds,boxes,{x,y:350},"a",snap);
  check(()=>assert.equal(snap.target.side,"left"));
}
snap=P.magneticHit(bounds,boxes,{x:646,y:350},"a",snap);
check(()=>assert.equal(snap.target.side,"centre"));
for(const x of [633,630,624]){
  snap=P.magneticHit(bounds,boxes,{x,y:350},"a",snap);
  check(()=>assert.equal(snap.target.side,"centre","reverse transition also has a deadband"));
}
snap=P.magneticHit(bounds,boxes,{x:617,y:350},"a",snap);
check(()=>assert.equal(snap.target.side,"left"));
check(()=>assert.equal(P.magneticHit(bounds,boxes,{x:-1,y:350},"a",snap),null,"leaving bounds clears snap immediately"));
check(()=>assert.equal(P.magneticHit(bounds,boxes,{x:1001,y:350},"a",snap),null));
for(const viewport of [{w:2560,h:1440},{w:1280,h:800}]){
  const b={x:0,y:0,...viewport};
  for(const side of ["left","right","top","bottom","centre"]){
    const p=P.previewPlan(tree,"a",{global:true,side},b,options);
    check(()=>assert.ok(p));
    check(()=>assert.deepEqual(p.box,P.geometry(p.tree.root,b,options).boxes.a,"preview and commit use same solver"));
    check(()=>assert.deepEqual(P.model(P.encoded(p.tree),["a","b"]),p.tree,"candidate survives ordinary world-tree encoding"));
    const geometry=P.geometry(p.tree.root,b,options);
    for(const box of Object.values(geometry.boxes)){
      check(()=>assert.ok(box.w>=240 && box.h>=140,"declared physical minima respected"));
      check(()=>assert.ok(box.x>=0&&box.y>=0&&box.x+box.w<=b.w+.001&&box.y+box.h<=b.h+.001));
    }
  }
}
const small={x:0,y:0,w:400,h:300};
const fallback=P.previewPlan(tree,"a",{global:true,side:"right"},small,options);
check(()=>assert.equal(fallback.fallback,"tabs"));
check(()=>assert.equal(fallback.tree.root.axis,"tabs"));
check(()=>assert.equal(fallback.tree.root.active,"a"));
check(()=>assert.equal(fallback.target.side,"centre","fallback intent matches actual committed tabs"));
check(()=>assert.ok(fallback.box.w>=240&&fallback.box.h>=140));
check(()=>assert.equal(P.previewPlan(tree,"a",{global:true,side:"bottom"},{...small,h:150},options),null,"neither split nor tabs fit; no scaling"));
check(()=>assert.equal(P.previewPlan(tree,"a",{global:true,side:"left"},{...small,w:230},options),null,"no physical width cannot be manufactured"));
check(()=>assert.equal(P.previewPlan(tree,"a",null,bounds,options),null));
const nested={v:1,root:{axis:"x",kids:[{id:"a"},{axis:"y",kids:[{id:"b"},{id:"c"}],weights:[2,3]}],weights:[1,4]},
      focus_weights:{b:{b:13,c:6}}};
const nestedCopy=JSON.stringify(nested);
// Local fallback preserves unrelated subtree weights and focused weights.
const p=P.previewPlan(nested,"a",{global:false,target:"b",side:"right"},{x:0,y:0,w:400,h:700},options);
check(()=>assert.equal(p.fallback,"tabs"));
check(()=>assert.deepEqual(p.tree.root.weights,[2,3]));
check(()=>assert.equal(p.tree.root.kids[1].id,"c"));
check(()=>assert.deepEqual(p.tree.focus_weights,nested.focus_weights));
check(()=>assert.equal(JSON.stringify(nested),nestedCopy,"solver never changes pickup model"));
check(()=>assert.equal(JSON.stringify(tree),original));
check(()=>assert.deepEqual(P.ids(p.tree.root).sort(),["a","b","c"],"no new or orphan identity"));
console.log(`${count} magnetic preview geometry checks passed (no browser)`);
