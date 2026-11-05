// Nonvisual checks of the actual component facade and pin input handlers. No WebGL/browser window.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const code=fs.readFileSync(__dirname+'/map-components.bundle.js','utf8').replace('export default','const exported =');
vm.runInThisContext(code);

(async()=>{
  let state={tool:'board-tool',target:'board-target',thread:'old',channel:'neighbours',hide:'parent-hide'};
  const calls=[];
  const api={node:{path:'root/map',gestures:[]},draft:{},view:()=>state,
    select:async values=>{state={...state,...values}},
    read:async()=>[{kind:'map',id:'mp1',hidden:'ground:labels'}, {id:'mp2',name:'Board',items:[]}],
    fire:async(event,values)=>calls.push({event,values})};
  const a=mapPanelApi(api,{map:'Seabright',board:'yes'});
  const b=mapPanelApi({...api,node:{path:'root/another',gestures:[]}},{map:'Seabright'});
  await a.select({tool:'route',selected:'something'});
  assert.equal(a.view().tool,'route');assert.equal(b.view().tool,undefined);
  assert.equal(state.tool,'board-tool');assert.equal(state.target,'board-target');
  await a.fire('hide',{layer:'mp2'});
  assert.equal(mapHead(await a.read('map.layers "Seabright"')).hidden,'ground:labels mp2');
  await a.fire('unhide',{layer:'labels'});
  assert.equal(mapHead(await a.read('map.layers "Seabright"')).hidden,'mp2');
  await a.fire('unhide',{layer:'mp2'});
  assert.equal(mapHead(await a.read('map.layers "Seabright"')).hidden,'');
  assert.equal(mapHead(await b.read('map.layers "Seabright"')).hidden,'ground:labels');
  await a.openThing({id:'mp10',kind:'post',post_kind:'event'});
  assert.equal(state.thread,'mp10');assert.equal(state.replyTo,'mp10');
  await a.openThing({id:'mp11',thread:'mp10',kind:'post',post_kind:'ask'});
  assert.equal(state.thread,'mp10');assert.equal(state.channel,'neighbours');
  assert.equal(state.hide,'parent-hide');
  await a.fire('put',{fields:{title:'Meet'},select:{tool:'look'}});
  assert.deepEqual(calls[0].values.select,{'map.root/map.tool':'look'});
  const standalone=mapPanelApi({...api,node:{path:'root',gestures:[{event:'open'}]}},{map:'Seabright'});
  await standalone.openThing({id:'mp12',kind:'post',rev:4});
  assert.equal(calls[1].event,'open');assert.deepEqual(calls[1].values.saw,{mp12:4});

  function node(){return {dataset:{},style:{},listeners:{},classList:{add(){},remove(){}},
    setAttribute(k,v){this[k]=v},set innerHTML(v){this.html=v},querySelector(){return this.label||(this.label={})},
    addEventListener(k,v){this.listeners[k]=v},removeEventListener(k){delete this.listeners[k]},
    setPointerCapture(){},getBoundingClientRect(){return {left:10,top:10}}};}
  const E=Object.create(GeoEngine.prototype);
  E.api={node:{gestures:[]},part:(name,tag,attrs)=>Object.assign(node(),{part:name,tag,attrs})};
  E.root={getBoundingClientRect:()=>({left:0,top:0})};E.ask=()=>{};
  let opened=0,moved=0;E.onPin=()=>opened++;E.onMove=()=>moved++;
  const pin=E.pinEl({id:'mp10',kind:'post',post_kind:'event',title:'Garden',color:'red',layer:{name:'Board'},lat:36,lon:-122});
  assert.equal(pin.part,'pin');assert.equal(pin['data-fact-post_kind'],'event');
  assert.equal(pin['data-fact-layer'],'board');
  pin.listeners.click({detail:0});assert.equal(opened,1);
  pin.listeners.click({detail:1});assert.equal(opened,1);
  E.pinDown({stopPropagation(){},clientX:10,clientY:10,pointerId:1},pin);
  pin.listeners.pointercancel({type:'pointercancel'});assert.equal(opened,1);
  E.pinDown({stopPropagation(){},clientX:10,clientY:10,pointerId:1},pin);
  pin.listeners.pointerup({type:'pointerup'});assert.equal(opened,2);
  E.api.node.gestures=[{event:'move'}];pin._item.place='mp20';
  E.pinDown({stopPropagation(){},clientX:10,clientY:10,pointerId:1},pin);
  pin.listeners.pointermove({clientX:50,clientY:50});assert.equal(E.dragging,null);
  pin.listeners.pointercancel({type:'pointercancel'});assert.equal(moved,0);
  console.log('panel checks passed');
})().catch(err=>{console.error(err);process.exitCode=1});
