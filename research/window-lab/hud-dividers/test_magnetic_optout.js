// Differential DOM-double proof against captured main; no browser or world.
const fs = require("node:fs"), vm = require("node:vm"), path = require("node:path");
const {createRequire} = require("node:module");
const assert = require("node:assert/strict");
const base = "09ef2530ec848cbbcf0afc5d0934737095c3cc69";
const prefix = "research/text-desk-lab/notation/desk-shell/";
const localRequire = createRequire(__filename);
function baseline(file) {
  const module = {exports:{}};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,"magnetic-baseline",file),"utf8"),
    {module, globalThis:{}}, {filename:"captured-main/"+file});
  return module.exports;
}
const original = {P:baseline("partition.js"), UI:baseline("partition-ui.js")};
const candidate = {
  P:localRequire("../../text-desk-lab/notation/desk-shell/partition.js"),
  UI:localRequire("../../text-desk-lab/notation/desk-shell/partition-ui.js")
};
const harness = fs.readFileSync(path.join(__dirname,"test_partition_ui.js"),"utf8").split("async function main(){")[0];
async function trace(source, setting, mode) {
  const uiSource = source === original
    ? fs.readFileSync(path.join(__dirname,"magnetic-baseline/partition-ui.js"),"utf8")
    : fs.readFileSync(path.join(__dirname,"../../text-desk-lab/notation/desk-shell/partition-ui.js"),"utf8");
  const context = {
    console, setTimeout:()=>0, setting, mode,
    require(name) {
      if(name.endsWith("/partition.js")) return source.P;
      if(name.endsWith("/partition-ui.js"))
        return vm.runInContext("(function(module){"+uiSource+";return module.exports;})({exports:{}})",context);
      if(name.endsWith("/carry-targets.js")) {
        const code=fs.readFileSync(path.join(__dirname,"../../text-desk-lab/notation/desk-shell/carry-targets.js"),"utf8");
        return vm.runInContext("(function(module){"+code+";return module.exports;})({exports:{}})",context);
      }
      return localRequire(name);
    }
  };
  context.global=context; context.globalThis=context;
  vm.createContext(context);
  return vm.runInContext(harness+`
  (async()=>{
    const tree={v:1,root:{axis:"x",kids:[{id:"a"},{id:"b"}],weights:[1,1]}};
    const spec={tree:JSON.stringify(tree),minimum:[240,140],gap:16,focus:""};
    if(setting!==undefined) spec.magnetic=setting;
    const n={key:"tiles",paint:{partition:spec},fence:{item:"layout"},acts:[
      {on:"arrange",line:'do prop layout tree="$value" full="$partition_focus"'}]};
    const paint=new Element(),root=new Element("DIV",n);paint.appendChild(root);document.body.appendChild(paint);
    const panels=["a","b"].map(id=>{
      const el=new Element("DIV",{key:id,paint:{partition_item:id}});
      const grip=new Element("DIV",{key:id+"/grip",paint:{},fence:{item:id}});
      el.appendChild(grip);root.appendChild(el);return {el,grip};
    });
    const sends=[],holds=[],snapshots=[];let refreshes=0;
    const ui=install(paint,{busy:()=>false,hold:x=>holds.push(x),refresh:()=>{refreshes++;},
      send:async(n,line)=>{sends.push(line);return {};}},P);
    ui.sync();
    const take=()=>snapshots.push(JSON.stringify(root.children.map(el=>({
      key:el.dataset.key,style:el.style,hidden:el.hidden,text:el.textContent,
      label:el["aria-label"],className:el.className
    }))));
    take();
    const grip=panels[0].grip;
    if(mode==="keyboard"){
      ui.key(grip,{target:grip,key:" ",preventDefault(){}});
      ui.key(grip,{target:grip,key:"ArrowDown",preventDefault(){}});
      take();ui.key(grip,{target:grip,key:"Enter",preventDefault(){}});
    }else{
      ui.carry(grip,{button:0,pointerId:1,clientX:200,clientY:100,target:grip,preventDefault(){}});
      for(const point of [{clientX:202,clientY:102},{clientX:640,clientY:799},{clientX:640,clientY:790}]){
        document.fire("pointermove",point);take();
      }
      if(mode==="cancel")document.fire("keydown",{key:"Escape"});
      document.fire("pointerup");
    }
    await settle();take();
    return JSON.stringify({sends,holds,refreshes,snapshots,tree:spec.tree,selectionClears,busy:ui.busy()});
  })()
  `,context);
}
(async()=>{
  let count=0;
  for(const setting of [undefined,false,"true",1]) for(const mode of ["pointer","keyboard","cancel"]){
    assert.equal(await trace(candidate,setting,mode),await trace(original,setting,mode),
      `off-path differs: ${setting}/${mode}`);
    count++;
  }
  console.log(`${count} captured-main/off-path byte-identical DOM/command traces passed`);
})().catch(e=>{console.error(e);process.exitCode=1;});
