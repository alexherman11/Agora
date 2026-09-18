import {Engine,canonical,clone} from './engine.mjs';
const trial=new URL(location.href).searchParams.get('trial')??'03-scene';
const stage=document.getElementById('stage'),status=document.getElementById('status'),details=document.getElementById('details');
const paint=document.getElementById('paint');
let engine,saved,signature='',moduleSignature='',drag=null,raf=null,notice='',issues=[],nodes=new WeakMap(),drafts={},draftVersions={},paintFrame=()=>{};
let nativeHold=null,deferredRender=false,incoming=null,incomingFrame=null,boundViews=[];
const metrics={renders:0,renderMs:0,maxRenderMs:0,previewFrames:0,previewMs:0,commits:0};
const env=()=>({width:innerWidth,height:innerHeight});
const match=(v,s)=>s===`id:${v.id}`||s===`widget:${v.widget}`||String(v.role??'').split(' ').some(r=>s===`role:${r}`);
const cssAllow=new Set(('background backgroundColor backgroundImage backgroundSize backgroundPosition color border borderTop borderBottom borderLeft borderRight borderColor borderRadius boxShadow textShadow padding paddingTop paddingBottom paddingLeft paddingRight margin marginTop marginBottom marginLeft marginRight gap rowGap columnGap display position left top right bottom width height minWidth minHeight maxWidth maxHeight zIndex transform transformOrigin transition overflow overflowX overflowY opacity visibility cursor pointerEvents userSelect fontFamily fontSize fontWeight fontStyle letterSpacing lineHeight textAlign textTransform textDecoration whiteSpace wordBreak flex flexGrow flexShrink flexBasis flexDirection flexWrap alignItems alignSelf justifyContent justifyItems gridTemplateColumns gridTemplateRows gridColumn gridRow gridAutoRows gridAutoFlow placeItems stroke strokeWidth strokeDasharray fill backdropFilter filter outline').split(' '));
const unitless=new Set(['zIndex','opacity','fontWeight','lineHeight','flexGrow','flexShrink','order','strokeWidth']);
cssAllow.add('inset');
const px=(k,v)=>typeof v==='number'&&!unitless.has(k)?`${v}px`:String(v??'');
const camel=s=>s.replace(/-([a-z])/g,(_,c)=>c.toUpperCase());
const cssScratch=document.createElement('div');
const expandedAllow=new Set(cssAllow);
for(const key of cssAllow){cssScratch.style.cssText='';cssScratch.style[key]='initial';for(const longhand of cssScratch.style)expandedAllow.add(camel(longhand));}
const expansionCache=new Map();
function expandStyle(key,value){
 if(!cssAllow.has(key)||/url\s*\(|expression\s*\(/i.test(String(value)))return {};
 const signature=key+'|'+value;if(expansionCache.has(signature))return expansionCache.get(signature);
 cssScratch.style.cssText='';cssScratch.style[key]=px(key,value);const fields=Object.fromEntries([...cssScratch.style].map(k=>[camel(k),cssScratch.style.getPropertyValue(k)]));
 if(expansionCache.size>4000)expansionCache.clear();expansionCache.set(signature,fields);return fields;
}
function style(n,values){for(const[k,v]of Object.entries(values)){if(!cssAllow.has(k)||/url\s*\(|expression\s*\(/i.test(String(v)))continue;n.style[k]=px(k,v);}}
function resolvedStyle(n,values){for(const[k,v]of Object.entries(values))if(expandedAllow.has(k))n.style[k]=String(v);}
function locals(ctx,scope){
 const result={...(drafts.root??{}),...(drafts[scope]??{})};
 for(const v of boundViews)if(!(v.bind in result)){
  try{result[v.bind]=v.value!==undefined?engine.eval(v.value,{...ctx,local:result}):v.widget==='select'?engine.eval(v.options??['lit',[]],{...ctx,local:result})[0]?.id??'':v.inputType==='number'?0:'';}catch{result[v.bind]='';}
 }return result;
}
function accept(data){
 if(saved&&data.serial<saved.serial)return;
 const next={...saved,...data},nextSignature=data.modules?canonical(data.modules):moduleSignature;
 if(saved&&nextSignature===moduleSignature&&next.serial===saved.serial&&canonical(next.state)===canonical(saved.state)&&canonical(next.conflicts)===canonical(saved.conflicts)&&canonical(next.diagnostics)===canonical(saved.diagnostics)){saved=next;return;}
 if(!engine||nextSignature!==moduleSignature){
  if(drag){drag.ghost?.remove();drag=null;notice='Motion cancelled because its program changed';}
  engine=new Engine(next.modules,next);moduleSignature=nextSignature;
 }else{engine.state=clone(next.state);engine.versions=clone(next.versions);engine.serial=next.serial;engine.conflicts=clone(next.conflicts??[]);}
 saved=next;
 if(drag){drag.baseState=clone(next.state);if(drag.latest)preview(drag.latest);}
 else render();
}
async function commit(commands,expected=saved.versions,clearScope){
 const response=await fetch(`/api/action?trial=${trial}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({commands,expected})});
 const data=await response.json();if(!data.result)throw Error(data.error);
 metrics.commits++;notice=data.result.ok?`Committed ${commands.map(c=>c.action).join(' + ')}`:`Refused: ${data.result.conflict.code} · ${JSON.stringify(data.result.conflict.detail)}`;
 if(data.result.ok&&clearScope){delete drafts[clearScope];delete draftVersions[clearScope];}
 accept(data);return data.result;
}
function render(){
 if(nativeHold){deferredRender=true;return;}
 if(!engine)return;const renderStarted=performance.now();metrics.renders++;issues=[...engine.diagnostics,...(saved.diagnostics??[]).filter(d=>!engine.diagnostics.some(x=>canonical(x)===canonical(d)))];nodes=new WeakMap();
 const viewDefs=Object.values(engine.program.view),children=new Map(),frameCache=new Map();boundViews=viewDefs.filter(v=>v.bind);
 for(const v of viewDefs){if(!children.has(v.parent))children.set(v.parent,[]);children.get(v.parent).push(v);}
 for(const list of children.values())list.sort((a,b)=>(a.order??0)-(b.order??0)||a.id.localeCompare(b.id));
 const readsFrame=(value,seen=new Set())=>{
  if(Array.isArray(value)){
   if(value[0]==='lit')return false;if(value[0]==='frame')return true;
   if(value[0]==='use'||value[0]==='query'){const kind=value[0]==='use'?'derive':'query',key=`${kind}:${value[1]}`;if(!seen.has(key)&&readsFrame(engine.program[kind][value[1]],new Set([...seen,key])))return true;}
   return value.some(v=>readsFrame(v,seen));
  }
  return !!value&&typeof value==='object'&&Object.values(value).some(v=>readsFrame(v,seen));
 };
 const needsFrame=(id,seen=new Set())=>{if(frameCache.has(id))return frameCache.get(id);if(seen.has(id))return false;const next=new Set([...seen,id]);const value=(children.get(id)??[]).some(v=>readsFrame(v)||needsFrame(v.id,next));frameCache.set(id,value);return value;};
 const focus=document.activeElement?.dataset.key,selection=document.activeElement?.selectionStart,selectionEnd=document.activeElement?.selectionEnd;
 const scrolls=new Map([...stage.querySelectorAll('[data-key]')].map(n=>[n.dataset.key,[n.scrollLeft,n.scrollTop]]));
 stage.replaceChildren();paint.replaceChildren();const portals=[],targets=new Map(),vectors=[],measurables=[];
 const element=(v,parentCtx={},scope='root',ancestry=[],parentDom=stage)=>{
  if(ancestry.includes(v.id)){issues.push({code:'cycle',id:v.id});return null;}
  let ctx={...parentCtx,env:env()};
  try{
   if(v.context!==undefined){ctx={...ctx,parent:ctx.row,row:engine.eval(v.context,ctx)};scope+=`/${v.id}/${ctx.row?.id??'none'}`;}
   ctx.local=locals(ctx,scope);const ev=x=>engine.eval(x,ctx);
   if(v.visible!==undefined&&!ev(v.visible))return null;
   const tag={text:'p',badge:'span',input:'input',textarea:'textarea',select:'select',button:'button',link:'a'}[v.widget]??'div';
   const n=document.createElement(tag);n.dataset.view=v.id;n.dataset.scope=scope;n.dataset.key=`${scope}:${v.id}`;n.dataset.role=v.role??'';
   if(v.dropRole)n.dataset.dropRole=v.dropRole;
   nodes.set(n,{v,ctx,scope});if(!targets.has(v.id))targets.set(v.id,n);else targets.set(v.id,null);
   const defaults={scene:{position:'relative',width:'100%',height:'100%',overflow:'hidden'},surface:{position:'absolute',overflow:'hidden'},canvas:{position:'relative'},stack:{display:'flex',flexDirection:'column'},row:{display:'flex',alignItems:'center'},grid:{display:'grid'},portal:{display:'contents'},text:{margin:0},badge:{display:'inline-block'},input:{minWidth:0},textarea:{minWidth:0},list:{display:'contents'}};
   style(n,defaults[v.widget]??{});
   if(v.box){const box=ev(v.box);style(n,{position:'absolute',left:box.x,top:box.y,width:box.width,height:box.height,zIndex:box.z??1});}
   const appearance=engine.styleFor(v,ctx,expandStyle);resolvedStyle(n,appearance.values);issues.push(...appearance.conflicts);
   parentDom.append(n);
   measurables.push({n,id:v.id,rowId:ctx.row?.id??''});
   if(v.widget==='surface'&&needsFrame(v.id)){const r=n.getBoundingClientRect();ctx.frame={width:r.width,height:r.height,x:r.x,y:r.y};}
   if(v.title){const h=document.createElement('div');h.textContent=ev(v.title);n.append(h);}
   if(['input','textarea','select'].includes(v.widget)){
    if(v.widget==='select')for(const r of ev(v.options??['lit',[]])){const o=document.createElement('option');o.value=r.id;o.textContent=r[v.optionLabel??'title']??r.id;n.append(o);}
    if(v.inputType)n.type=v.inputType;n.value=ctx.local[v.bind]??'';n.placeholder=v.placeholder??'';n.setAttribute('aria-label',v.placeholder??v.bind??v.id);
    const input=async()=>{
     const value=v.inputType==='number'?Number(n.value):n.value;(drafts[scope]??={})[v.bind]=value;(draftVersions[scope]??={})[v.bind]??=clone(saved.versions);
     if(v.onChange){try{await commit([{action:v.onChange.action,args:engine.eval(v.onChange.args??{},{...ctx,event:{value},local:locals(ctx,scope)})}],saved.versions,scope);}catch(e){notice=e.message;render();}}
     else render();
    };n.addEventListener(v.onChange?'change':'input',input);
   }else if(v.widget==='button'){
    n.textContent=String(ev(v.text)??v.id);n.disabled=!!(v.disabled!==undefined&&ev(v.disabled))||!engine.program.action[v.action];
    n.onclick=async()=>{try{const context={...ctx,env:env(),local:{...locals(ctx,scope),newId:crypto.randomUUID()}};const expected={...(nativeHold?.versions??saved.versions)};for(const versions of Object.values(draftVersions[scope]??{}))for(const key of new Set([...Object.keys(expected),...Object.keys(versions)]))expected[key]=versions[key]??0;await commit([{action:v.action,args:engine.eval(v.args??{},context)}],expected,scope);}catch(e){notice=e.message;render();}};
   }else if(v.widget==='link'){
    n.textContent=String(ev(v.text)??'');const href=String(ev(v.href)??'');if(/^https?:\/\//i.test(href)){n.href=href;n.target='_blank';n.rel='noopener noreferrer';}
   }else if(['line','circle'].includes(v.widget)){
    const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.classList.add('t-vector');const shape=document.createElementNS(svg.namespaceURI,v.widget);
    shape.setAttribute('stroke',appearance.values.stroke??'#aab');shape.setAttribute('stroke-width',appearance.values.strokeWidth??2);shape.setAttribute('fill',appearance.values.fill??'none');if(appearance.values.strokeDasharray)shape.setAttribute('stroke-dasharray',appearance.values.strokeDasharray);if(appearance.values.opacity)shape.setAttribute('opacity',appearance.values.opacity);svg.append(shape);n.style.display='contents';
    if(v.space==='viewport'){svg.style.position='absolute';paint.append(svg);}else n.append(svg);
    vectors.push({v,ctx,shape});
   }else if(v.text!==undefined)n.append(document.createTextNode(String(ev(v.text)??'')));
   if(String(v.role??'').includes('grip'))n.classList.add('t-grip');
   const next=[...ancestry,v.id];
   if(v.widget==='list'){
    for(const row of engine.eval(['query',v.query],ctx))for(const c of children.get(v.id)??[])element(c,{...ctx,parent:ctx.row,row},`${scope}/${v.query}/${row.id}`,next,n);
   }else for(const c of children.get(v.id)??[])element(c,ctx,scope,next,n);
   if(v.widget==='portal')portals.push({n,to:ev(v.to)});
   return n;
  }catch(e){issues.push({code:'view-error',view:v.id,message:e.message});const n=document.createElement('div');n.className='t-error';n.textContent=`${v.id}: ${e.message}`;parentDom.append(n);return n;}
 };
 for(const root of viewDefs.filter(v=>!v.parent))element(root);
 for(const{n,to}of portals){const target=targets.get(to);if(!target||n.contains(target)){issues.push({code:'portal-target',target:to});n.classList.add('t-orphan');n.style.display='block';}else target.append(n);}
 for(const n of stage.querySelectorAll('[data-key]')){const s=scrolls.get(n.dataset.key);if(s){n.scrollLeft=s[0];n.scrollTop=s[1];}}
 paintFrame=()=>{
  const geometry={};for(const{n,id,rowId}of measurables){if(!n.isConnected)continue;const r=n.getBoundingClientRect(),key=`${id}|${rowId}`;geometry[key]={x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom,centerX:r.x+r.width/2,centerY:r.y+r.height/2};}
  for(const{v,ctx,shape}of vectors)try{let absent=false;for(const k of v.widget==='line'?['x1','y1','x2','y2']:['cx','cy','r']){const value=engine.eval(v[k]??0,{...ctx,geometry});shape.setAttribute(k,value??0);absent||=value===null;}shape.style.visibility=absent?'hidden':'';}catch(e){issues.push({code:'paint-error',id:v.id,message:e.message});}
 };
 paintFrame();
 if(focus){const n=[...stage.querySelectorAll('[data-key]')].find(n=>n.dataset.key===focus);if(n){n.focus({preventScroll:true});if(selection!=null&&n.type!=='number')n.setSelectionRange?.(selection,selectionEnd);}}
 status.textContent=`${engine.modules.length-1} authors · ${Object.keys(engine.program.view).length} views · ${issues.length} conflicts${drag?' · local preview':''}${notice?' · '+notice:''}`;
 details.textContent=JSON.stringify({issues,metrics,provenance:engine.provenance,conflicts:engine.conflicts.slice(-5)},null,2);
 const layers=document.getElementById('layers');layers.replaceChildren();
 for(const m of engine.modules.filter(m=>m.id!=='base')){
  const label=document.createElement('label'),input=document.createElement('input');input.type='checkbox';input.checked=m.enabled!==false;input.dataset.module=m.id;
  input.onchange=async()=>{const enabled=[...layers.querySelectorAll('input:checked')].map(n=>n.dataset.module);try{const data=await(await fetch(`/api/layers?trial=${trial}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled})})).json();if(data.error)throw Error(data.error);accept(data);}catch(e){notice=e.message;render();}};
  label.append(input,document.createTextNode(m.id));layers.append(label);
 }
 window.tessera={metrics,issues,get state(){return clone(engine.state);},get saved(){return clone(saved);}};
 const elapsed=performance.now()-renderStarted;metrics.renderMs+=elapsed;metrics.maxRenderMs=Math.max(metrics.maxRenderMs,elapsed);
}
function gestureValues(d,e){
 const dx=e.clientX-d.pointerX,dy=e.clientY-d.pointerY;
 let drop=null;
 const dropRole=d.gestures.find(g=>g.dropRole)?.dropRole;
 if(dropRole){const hit=document.elementsFromPoint(e.clientX,e.clientY).find(n=>n.dataset?.dropRole===dropRole);drop=hit?.dataset.view??null;}
 return {dx,dy,x:d.x+dx,y:d.y+dy,width:d.width+dx,height:d.height+dy,startX:d.x,startY:d.y,startWidth:d.width,startHeight:d.height,pointerX:e.clientX,pointerY:e.clientY,drop};
}
function preview(e){
 if(!drag)return;const started=performance.now(),d=drag,g=gestureValues(d,e);d.last=g;
 engine.state=clone(d.baseState);const ps=new Map();
 try{
  for(const contribution of d.gestures)for(const effect of contribution.preview??[]){const ctx={...d.ctx,gesture:g,env:env()},id=engine.eval(effect.id,ctx),value=engine.eval(effect.value,ctx),address=`${effect.collection}/${id}/${effect.field}`;if(!ps.has(address))ps.set(address,[]);ps.get(address).push({...effect,id,value,by:contribution.id});}
  for(const[address,proposals]of ps){const p=proposals[0],record=engine.state[p.collection]?.[p.id];if(!record)throw Error(`Missing preview address ${address}`);if(new Set(proposals.map(p=>p.op)).size>1||p.op==='set'&&new Set(proposals.map(p=>canonical(p.value))).size>1)throw Error(`Gesture conflict at ${address}: ${proposals.map(p=>p.by).join(', ')}`);if(p.op==='set')record[p.field]=p.value;else if(p.op==='add')record[p.field]+=proposals.reduce((s,p)=>s+p.value,0);else if(p.op==='union')record[p.field]=[...new Set([...record[p.field],...proposals.flatMap(p=>p.value)])];else throw Error('Unsupported preview operation');}
  engine.validate(engine.state);render();
  if(d.ghost){d.ghost.style.left=`${d.screenX+g.dx}px`;d.ghost.style.top=`${d.screenY+g.dy}px`;}
  metrics.previewFrames++;metrics.previewMs+=performance.now()-started;
 }catch(error){notice=error.message;d.invalid=true;engine.state=clone(d.baseState);render();}
}
// Preserve native activation from pointerdown through click. Incoming snapshots
// may advance, but cannot replace a held button or its captured revision basis.
window.addEventListener('pointerdown',e=>{
 const control=e.target.closest?.('button,input,textarea,select,a,[contenteditable="true"]');
 if(e.button===0&&control&&(stage.contains(control)||document.getElementById('layers').contains(control)))nativeHold={pointerId:e.pointerId,versions:clone(saved.versions)};
},true);
function releaseNative(){nativeHold=null;if(deferredRender){deferredRender=false;render();}}
window.addEventListener('pointerup',()=>{if(nativeHold)setTimeout(releaseNative,0);});
window.addEventListener('pointercancel',releaseNative);window.addEventListener('blur',releaseNative);
stage.addEventListener('pointerdown',e=>{
 if(e.button!==0||drag)return;const path=e.composedPath();
 // A control inside a handle keeps its native activation; dragging uses handle space.
 if(path.some(n=>n instanceof Element&&n.matches('button,input,textarea,select,a,[contenteditable="true"]')))return;
 let found;
 for(const n of path){const info=nodes.get(n);if(!info)continue;const gestures=Object.values(engine.program.gesture).filter(g=>match(info.v,g.selector)&&(g.when===undefined||engine.eval(g.when,info.ctx))&&(!g.handle||path.slice(0,path.indexOf(n)+1).some(child=>nodes.has(child)&&match(nodes.get(child).v,g.handle))));if(gestures.length){found={n,...info,gestures};break;}}
 if(!found)return;e.preventDefault();
 const rect=found.n.getBoundingClientRect(),computed=getComputedStyle(found.n);
 drag={...found,pointerX:e.clientX,pointerY:e.clientY,x:parseFloat(computed.left)||0,y:parseFloat(computed.top)||0,width:rect.width,height:rect.height,screenX:rect.left,screenY:rect.top,baseState:clone(engine.state),versions:clone(saved.versions)};
 if(found.gestures.some(g=>g.dropRole)){const ghost=found.n.cloneNode(true);ghost.removeAttribute('data-key');Object.assign(ghost.style,{position:'fixed',left:`${rect.left}px`,top:`${rect.top}px`,width:`${rect.width}px`,height:`${rect.height}px`,zIndex:2147483640,pointerEvents:'none',opacity:'.85',transform:'none'});document.body.append(ghost);drag.ghost=ghost;}
});
window.addEventListener('pointermove',e=>{if(!drag)return;drag.latest=e;if(!raf)raf=requestAnimationFrame(()=>{raf=null;if(drag)preview(drag.latest);});});
window.addEventListener('pointerup',async e=>{
 if(!drag)return;if(raf){cancelAnimationFrame(raf);raf=null;}preview(e);const d=drag,g=d.last??gestureValues(d,e);drag=null;d.ghost?.remove();engine.state=clone(d.baseState);
 if(d.invalid){render();return;}
 try{const context={...d.ctx,gesture:g,env:env(),local:{...d.ctx.local,newId:crypto.randomUUID()}};const commands=d.gestures.filter(g=>g.commit).map(c=>({action:c.commit.action,args:engine.eval(c.commit.args??{},context)}));if(commands.length)await commit(commands,d.versions);else render();}catch(error){notice=error.message;render();}
});
window.addEventListener('keydown',e=>{if(e.key==='Escape'&&drag){drag.ghost?.remove();engine.state=clone(drag.baseState);drag=null;notice='Motion cancelled';render();}});
window.addEventListener('resize',()=>render());
stage.addEventListener('scroll',()=>requestAnimationFrame(paintFrame),true);
document.getElementById('status').onclick=()=>document.getElementById('diagnostic').classList.toggle('open');
async function refresh(){try{const data=await(await fetch(`/api/state?trial=${trial}`)).json();if(data.error)throw Error(data.error);const key=canonical(data);if(key!==signature){signature=key;accept(data);}}catch(error){notice=error.message;status.textContent=notice;}}
await refresh();setInterval(refresh,1200);
const stream=new EventSource(`/api/stream?trial=${trial}`);
stream.onmessage=e=>{try{const data=JSON.parse(e.data);if(data.serial<saved.serial)return;incoming={...(incoming??{}),...data};if(!incomingFrame)incomingFrame=requestAnimationFrame(()=>{incomingFrame=null;const data=incoming;incoming=null;try{accept(data);}catch(error){notice=error.message;status.textContent=notice;}});}catch(error){notice=error.message;status.textContent=notice;}};
