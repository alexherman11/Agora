// CPU-only solver sample, NOT browser frames, DOM layout or drop latency.
const {performance}=require("node:perf_hooks");
const P=require("../../text-desk/notation/desk-shell/partition.js");
const tree={v:1,root:{axis:"x",kids:[
  {axis:"y",kids:[{id:"a"},{id:"b"}],weights:[1,1]},
  {axis:"y",kids:[{id:"c"},{id:"d"},{id:"e"}],weights:[1,1,1]}
],weights:[1,1]}};
const targets=["left","right","top","bottom","centre"].map(side=>({global:true,side}));
function sample(fn){
  for(let i=0;i<300;i++)fn(i);
  const times=[];
  for(let i=0;i<2000;i++){const start=performance.now();fn(i);times.push(performance.now()-start);}
  times.sort((a,b)=>a-b);
  return {samples:times.length,p50_ms:+times[1000].toFixed(4),p95_ms:+times[1900].toFixed(4),max_ms:+times.at(-1).toFixed(4)};
}
for(const [w,h] of [[2560,1440],[1280,800]]){
  const bounds={x:0,y:0,w,h}, options={minimum:[240,140],gap:16};
  console.log(JSON.stringify({
    kind:"CPU solver only; requested bounds, not measured viewport",
    bounds,
    original_plan:sample(i=>P.plan(tree,"a",targets[i%5],bounds,options)),
    preview_plan_and_geometry:sample(i=>{
      const p=P.previewPlan(tree,"a",targets[i%5],bounds,options);
      if(p)P.geometry(p.tree.root,bounds,options);
    })
  }));
}
