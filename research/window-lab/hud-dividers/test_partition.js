const assert = require("node:assert/strict");
const P = require("../../text-desk-lab/notation/desk-shell/partition.js");
let checks = 0;
function check(fn) { fn(); checks++; }
const tree = { v: 1, root: { axis: "x", kids: [
  { axis: "y", kids: [{ id: "music" }, { id: "board" }], weights: [1, 1] },
  { axis: "y", kids: [{ id: "viewer" }, { id: "chat" }], weights: [1, 1] }
], weights: [1, 1] } };
const members = P.ids(tree.root);
const close = (a, b) => assert.ok(Math.abs(a - b) < .00001, `${a} != ${b}`);
function inBounds(boxes, b) {
  for (const r of Object.values(boxes)) {
    assert.ok(r.x >= b.x - .001 && r.y >= b.y - .001);
    assert.ok(r.w >= 0 && r.h >= 0);
    assert.ok(r.x + r.w <= b.x + b.w + .001 && r.y + r.h <= b.y + b.h + .001);
  }
}
for (const [w, h] of [[2560,1440],[1280,800],[600,400],[200,100],[0,0]]) {
  const bounds = { x: 0, y: 0, w, h };
  check(() => inBounds(P.geometry(tree.root, bounds).boxes, bounds));
  for (const side of ["left","right","top","bottom"]) {
    const plan = P.plan(tree, "chat", { global: true, side }, bounds);
    check(() => {
      assert.equal(plan.tree.root.axis, ["left","right"].includes(side) ? "x" : "y");
      assert.deepEqual(P.ids(plan.tree.root).sort(), members.slice().sort());
      assert.deepEqual(plan.box, P.geometry(plan.tree.root, bounds).boxes.chat, "preview and final use identical geometry");
      inBounds(P.geometry(plan.tree.root, bounds).boxes, bounds);
      if (side === "bottom") {
        close(plan.box.w, w);
        if (h >= 600) close(plan.box.h, (h - 16) / 2);
      }
    });
  }
  for (const side of ["left","right","top","bottom","centre"]) {
    check(() => {
      const plan = P.plan(tree, "chat", { target: "music", side, global: false }, bounds);
      assert.equal(plan.tree.root.axis, "x");
      assert.deepEqual(plan.box, P.geometry(plan.tree.root, bounds).boxes.chat);
      assert.deepEqual(P.ids(plan.tree.root).sort(), members.slice().sort());
      inBounds(P.geometry(plan.tree.root, bounds).boxes, bounds);
    });
  }
  for (const split of P.geometry(tree.root, bounds).splits) {
    for (const delta of [-10000,-200,-10,0,10,200,10000]) check(() => {
      const next = P.resize(tree, split.path, 0, delta, bounds);
      inBounds(P.geometry(next.root, bounds).boxes, bounds);
      const after = P.geometry(next.root, bounds).splits.find(s => JSON.stringify(s.path) === JSON.stringify(split.path));
      const dim = split.node.axis === "x" ? "w" : "h";
      close(after.children.reduce((s,c)=>s+c[dim],0), split.children.reduce((s,c)=>s+c[dim],0));
      assert.deepEqual(P.model(JSON.stringify(next), members), next, "weights survive a world round-trip");
    });
  }
}
check(() => assert.equal(P.drop(tree,"chat","chat","left"),null));
check(() => assert.equal(P.drop({v:1,root:{id:"chat"}},"chat",null,"bottom",true),null));
check(() => assert.equal(P.drop(tree,"missing","chat","left"),null));
check(() => {
  const b = {x:0,y:0,w:1280,h:800}, boxes = P.geometry(tree.root,b).boxes;
  for (const [point, side] of [[{x:640,y:799},"bottom"],[{x:640,y:1},"top"],[{x:1,y:400},"left"],[{x:1279,y:400},"right"]]) {
    assert.deepEqual(P.hit(b,boxes,point,"chat"), {global:true,side});
  }
  assert.equal(P.hit(b,boxes,{x:0,y:801},"chat"),null);
  assert.equal(P.hit(b,boxes,{x:200,y:160},"chat").side,"centre");
});
check(() => {
  const next = P.drop(tree,"chat","music","centre");
  const selected = P.activate(next.root,"music");
  assert.ok(P.geometry(selected,{x:0,y:0,w:1200,h:800}).boxes.music);
  assert.equal(P.geometry(selected,{x:0,y:0,w:1200,h:800}).boxes.chat,undefined);
  assert.deepEqual(P.ids(next.root).sort(),members.slice().sort());
});
check(() => {
  const content = P.replace(tree.root,"music",n=>({...n,size:"content"}));
  const bounds = {x:0,y:0,w:1280,h:800};
  const result = P.geometry(content,bounds,{intrinsic:{music:[280,170]}});
  assert.equal(result.boxes.music.w,280); assert.equal(result.boxes.music.h,170);
  assert.deepEqual(P.model(JSON.stringify({v:1,root:content}),members).root,content);
});
check(() => {
  const visible = new Set(["music","viewer","chat"]), bounds={x:0,y:0,w:1280,h:800};
  const next = P.resize(tree,[],0,100,bounds,{visible});
  assert.deepEqual(P.ids(next.root).sort(),members.slice().sort());
  assert.equal(P.geometry(next.root,bounds,{visible}).boxes.board,undefined);
  assert.ok(P.geometry(next.root,bounds).boxes.board, "restore remembers the leaf");
  assert.deepEqual(P.model(JSON.stringify(next),members),next,"guarded member retained");
  assert.ok(!P.ids(P.model(JSON.stringify(next),["music","viewer","chat"]).root).includes("board"),"closed member removed");
});
check(() => {
  const next=P.model('{"v":1,"root":{"axis":"y","kids":[{"id":"music"},{"id":"music"},{"id":"viewer"}],"weights":[0,-1,5]}}',["music","viewer","chat"]);
  assert.deepEqual(P.ids(next.root).sort(),["chat","music","viewer"]);
  inBounds(P.geometry(next.root,{x:0,y:0,w:800,h:600}).boxes,{x:0,y:0,w:800,h:600});
  assert.ok(P.model("broken",members).root);
});
check(() => {
  const n={acts:[{on:"arrange",line:'do prop layout tree="$value" full="$partition_focus"'}]};
  const line=P.command(n,{v:1,root:{id:'a"$partition_focus\\'}},"");
  assert.match(line,/^do prop layout tree="/);
  assert.ok(line.includes("\\$partition_focus"),"values are escaped and never expanded a second time");
  assert.ok(line.endsWith(' full=""'));
});
check(() => {
  const next={...P.drop(tree,"chat","music","centre"),focus_weights:{chat:{chat:13,music:6}}};
  const raw=P.encoded(next);
  assert.deepEqual(P.model(JSON.stringify(raw),members),next);
  assert.deepEqual(raw.focus_weights[0].panel,{$ref:"chat"});
  assert.deepEqual(raw.focus_weights[0].members[1].panel,{$ref:"music"});
  assert.ok(JSON.stringify(raw).includes('"active":{"$ref":"chat"}'));
});
check(() => {
  const preferred=P.model(P.encoded(tree),members,{music:"content"});
  assert.equal(P.nodeAt(P.replace(preferred.root,"music",n=>n),[0,0]).size,"content");
  const explicit={v:1,root:{id:"music",size:"stretch"}};
  assert.equal(P.model(P.encoded(explicit),["music"],{music:"content"}).root.size,"stretch");
  const bounds={x:0,y:0,w:1280,h:800},options={intrinsic:{music:[280,170]}};
  const plan=P.plan(preferred,"music",{global:true,side:"bottom"},bounds,options);
  assert.equal(plan.box.w,1280,"intentional edge placement fills its preview");
  const resized=P.resize({v:1,root:{axis:"x",kids:[{id:"music",size:"content"},{id:"chat"}],weights:[1,1]}},
    [],0,80,bounds,options);
  assert.equal(resized.root.kids[0].size,"stretch","explicit divider size supersedes natural preference");
  const sized={v:1,root:{id:"music",size:"content",extent:[310,180]}};
  const saved=P.model(P.encoded(sized),["music"]);
  assert.deepEqual(P.geometry(saved.root,bounds).boxes.music,{x:0,y:0,w:310,h:180});
  assert.deepEqual(P.geometry(saved.root,{x:0,y:0,w:200,h:100}).boxes.music,{x:0,y:0,w:200,h:100});
});
check(() => {
  let root={id:"old"};
  for(let i=0;i<32;i++)root={axis:i%2?"x":"y",kids:[root,{id:"p"+i}],weights:[1,1]};
  const deep={v:1,root:{axis:"x",kids:[root,{id:"moving"}],weights:[1,1]}};
  assert.equal(P.drop(deep,"moving",null,"bottom",true),null,"unsupported depth is refused before preview/save");
});
console.log(`${checks} partition geometry/model checks passed`);
