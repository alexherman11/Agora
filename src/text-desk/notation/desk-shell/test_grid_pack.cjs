// Offline geometry and actual adapter, with deterministic CSS/observer fixtures.
const assert = require("node:assert/strict");
const { solve, span, painter } = require("./grid-pack.js");
let checks = 0;
function eq(a, b) { checks++; assert.deepEqual(a, b); }
function ok(a) { checks++; assert.ok(a); }
eq(solve(3, 8, []), []);
eq(solve(3, 8, [{span: 1, height: 20}]), [{x:0,y:0,span:1,height:20}]);
const mixed = solve(2, 10, [100, 20, 20, 20].map(height => ({span:1,height})));
eq(mixed.map(p => [p.x,p.y]), [[0,0],[1,0],[1,30],[1,60]]);
const holes = solve(3, 0, [{span:1,height:100},{span:2,height:20},{span:2,height:40},{span:1,height:20}]);
eq(holes.map(p => [p.x,p.y]), [[0,0],[1,0],[1,20],[1,60]]);
eq(span(210, 100, 10, 4), 2);
eq(span(211, 100, 10, 4), 3);
eq(span(900, 100, 10, 4), 4);
// Generated variable sizes: no overlap, deterministic, bounded by real columns.
for (let columns = 1; columns <= 8; columns++) {
  const items = Array.from({length:70}, (_,i) => ({span:1+i%columns,height:1+(i*37)%211}));
  const out = solve(columns, 7, items);
  eq(out, solve(columns, 7, items));
  out.forEach((a,i) => {
    ok(a.x >= 0 && a.x+a.span <= columns);
    out.slice(i+1).forEach(b => ok(a.x+a.span <= b.x || b.x+b.span <= a.x ||
      a.y+a.height+7 <= b.y || b.y+b.height+7 <= a.y));
  });
}

// A CSSStyleDeclaration fixture that preserves authored values across measure phases.
function style(initial = {}) {
  let props = {...initial};
  return new Proxy({}, {
    get(_, k) { return k === "cssText" ? JSON.stringify(props) : props[k] || ""; },
    set(_, k, v) { if (k === "cssText") props = JSON.parse(v); else props[k] = v; return true; }
  });
}
let frames = [], resize, mutations, resized, readsWithOldSpans = 0;
const observers = [];
const root = {children:[],dataset:{key:"items"},style:style(),isConnected:true,clientWidth:320,
  contains(t) {return t === this || this.children.includes(t);},
  getBoundingClientRect() {return {width:this.clientWidth,height:400};}};
function child(key, min, natural) {
  return {dataset:{key},style:style({color:"blue"}),hidden:false,min,natural,
    getBoundingClientRect() {
      const width = this.style.width === "min-content" ? this.min :
        Math.min(root.clientWidth, (parseInt(this.style.gridColumn.match(/span (\d+)/)?.[1]) || 1) * 110 - 10);
      return {width,height:this.natural + (width < 150 ? 10 : 0)};
    }};
}
const first = child("first", 70, 100), wide = child("wide", 190, 30), last = child("last", 70, 20);
root.children = [first, wide, last];
const env = {
  requestAnimationFrame(f) {frames.push(f);return 1;},
  addEventListener(name,f) {if(name === "resize") resized = f;},
  document:{documentElement:{},fonts:{addEventListener(){}}},
  ResizeObserver:class {
    constructor(f){resize=f;this.seen=new Set();this.disconnected=false;observers.push(this);}
    observe(c){this.seen.add(c);} unobserve(c){this.seen.delete(c);} disconnect(){this.disconnected=true;}
  },
  MutationObserver:class {constructor(f){mutations=f;} observe(){}},
  getComputedStyle(el) {
    if(el !== root) return {display:"block",marginLeft:"0",marginRight:"0",marginTop:"0",marginBottom:"0"};
    if(root.children.some(c => c.style.gridColumn && !c.style.gridColumn.startsWith("span"))) readsWithOldSpans++;
    return {paddingLeft:"0",paddingRight:"0",columnGap:"10px",
      gridTemplateColumns: Array.from({length: Math.max(1,Math.floor((root.clientWidth+10)/110))}, () => "100px").join(" ")};
  }
};
function flush() {const f=frames;frames=[];f.forEach(fn=>fn());}
const grid = painter(env);
root.clientWidth=0;
grid.attach(root); grid.attach(root);
eq(frames.length,1); flush();
eq(grid.geometry(root),[]);
resize([{target:root}]); eq(frames.length,0);
root.clientWidth=320; resize([{target:root}]); eq(frames.length,1); flush();
eq(root.children,[first,wide,last]); // same nodes/order, no focus/text API exists in adapter
eq(grid.geometry(root).map(p=>p.span),[1,2,1]);
eq(wide.style.color,"blue");
resize([root,...root.children].map(target=>({target})));
eq(frames.length,0); // own final dimensions do not recursively repack
root.clientWidth=0; resize([{target:root}]); flush();
root.clientWidth=320; resize([{target:root}]); eq(frames.length,1); flush();
root.clientWidth=210; resize([{target:root}]); eq(frames.length,1); flush();
eq(readsWithOldSpans,0);
eq(grid.geometry(root).map(p=>p.span),[1,2,1]);
root.clientWidth=100; resized(); flush();
eq(grid.geometry(root).map(p=>p.span),[1,1,1]);
eq(wide.style.overflowX,"auto"); // impossible width is local, not clipped/scaled
root.clientWidth=320; resized(); flush(); eq(wide.style.overflowX,"");
first.natural=170; resize([{target:first}]); flush();
eq(grid.geometry(root)[0].height,180);
root.children=[wide,last]; mutations([{target:root}]); flush();
eq(first.style.gridRow,""); eq(first.style.color,"blue"); ok(!observers[0].seen.has(first));
root.children=[]; mutations([{target:root}]); flush(); eq(grid.geometry(root),[]);
root.children=[last]; mutations([{target:root}]); flush(); eq(grid.geometry(root).length,1);
root.isConnected=false; mutations([{target:root}]); flush(); ok(observers[0].disconnected);
eq(grid.geometry(root),[]);
// attach before insertion is supported; attaching an unrelated normal grid does not occur.
root.isConnected=false; grid.attach(root); flush();
root.isConnected=true; grid.attach(root); flush(); eq(grid.geometry(root).length,1);
console.log(`grid pack: ${checks} assertions passed (geometry + fake DOM; no browser proof)`);
