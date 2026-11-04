// EDITING THE PAINTER (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
// The painter's vocabulary (formats, handles, scopes, parts) is shared by every app. Add to it only what any lens could
// use, documented where lens authors read it (ARRANGEMENT.md); never a handle, format or branch for one app. If one app
// needs something, the general form of it is the change.
//
// Trusted arrangement runtime; component code supplies pixels, never the reading.
// The entire painter uses the existing guarded widget surface and bridge.
const {widget, target} = await agora.ready;
const definition = (await rows('rows widget')).find(w=>w.id===widget.id||w.id===widget);
const lensName = definition.component_lens;
let mounted, dragging=false, refreshTimer, menu, menuReturnFocus, currentPlan;
// A window opened on a thing starts with it as $view.target (window.open <lens> <thing>)
let viewState=target?{target}:{}, renderReadings=new Map();
const moduleCache=new Map();
const interpolate=(text,env)=>String(text).replace(/\$([\w.-]+)/g,(matched,path,offset,source)=>{
  let value=env;for(const bit of path.split('.'))value=value?.[bit];
  if(value&&typeof value==='object')value=value.id;
  // Every dynamic value is data, including inside an authored quoted argument.
  let quoted=false,escaped=false;
  for(const ch of source.slice(0,offset)){if(escaped){escaped=false;continue}if(ch==='\\'){escaped=true;continue}if(ch==='"')quoted=!quoted}
  return quoted?String(value??'').replace(/\\/g,'\\\\').replace(/"/g,'\\"'):Q(value);
});
function closeMenu(){const had=!!menu;menu?.remove();menu=null;if(menuReturnFocus?.isConnected)menuReturnFocus.focus();menuReturnFocus=null;if(had)dispatchEvent(new CustomEvent('agora-menu',{detail:{open:false}}))}
// 26 Oct (Alex): every menu ends with a box to ask, in your own words, for a change to what it is about.
// The world's `ask` word decides where it goes (the kernel desk: a request relayed into the Conversation for Claude).
function askBox(node){
  // A part with no bound thing (a bar's clock) asks about its lens: the thing that arranges it.
  const thing=Object.keys(node.saw||{})[0]||node.gestures?.map(g=>g.env&&Object.values(g.env).find(v=>v&&typeof v==='object'&&v.id)?.id).find(Boolean)||currentPlan?.lens||'-';
  const box=document.createElement('input');box.type='text';box.placeholder='Ask for a change…';
  box.setAttribute('aria-label','Ask for a change to this, in your own words');box.className='menu-ask';
  box.style.cssText='display:block;box-sizing:border-box;width:100%;margin-top:6px;padding:7px 10px;font:inherit;font-size:12px;border:1px solid var(--ag-border,#e4e7e1);border-radius:8px;background:var(--ag-surface,#fff);color:inherit';
  box.addEventListener('keydown',async e=>{
    e.stopPropagation();
    if(e.key==='Escape'){e.preventDefault();closeMenu();return}
    if(e.key!=='Enter'||e.isComposing||!box.value.trim())return;
    e.preventDefault();const words=box.value.trim();closeMenu();
    try{await act('ask '+thing+' text='+Q(words)+' where='+Q(lensName+' · '+node.path),{});tell('Asked — it is in the Conversation')}
    catch(err){tell('Not sent: '+(err?.message||err))}
  });
  return box;
}
function openMenu(node,x,y){
  if(!node)return;closeMenu();menuReturnFocus=document.activeElement;menu=render(node);menu.hidden=false;menu.classList.add('menu');
  menu.append(askBox(node));
  document.body.append(menu);const r=menu.getBoundingClientRect();
  menu.style.left=Math.max(8,Math.min(x,innerWidth-r.width-10))+'px';
  menu.style.top=Math.max(8,Math.min(y,innerHeight-r.height-10))+'px';
  P.navigation(menu,{menu:true});menu.querySelector('button')?.focus();
}
// 26 Oct (shell components): right-click any part to ask. A component calls api.ask(event); a lens with the fact
// right_click=ask gives every part that does not handle right-click itself the same menu.
function openAsk(node,x,y){
  if(!node)return;closeMenu();menuReturnFocus=document.activeElement;
  const label=String(node.name||node.component||'part').replace(/[-_]+/g,' ');
  menu=el('div',{class:'menu ask-menu',role:'menu','aria-label':'Ask for a change to '+label,'data-path':node.path});
  const kind=node.component.replace(/^shell-/,'').replace(/-/g,' ');
  menu.append(el('div',{class:'ask-head'},el('strong',{},label),kind!==label?el('small',{},kind):''),askBox(node));
  document.body.append(menu);const r=menu.getBoundingClientRect();
  menu.style.left=Math.max(8,Math.min(x,innerWidth-r.width-10))+'px';
  menu.style.top=Math.max(8,Math.min(y,innerHeight-r.height-10))+'px';
  menu.querySelector('input')?.focus();
  dispatchEvent(new CustomEvent('agora-menu',{detail:{open:true}}));
}
function nodeAt(target){
  const n=target?.closest?.('[data-path]');if(!n||!currentPlan)return null;
  const path=n.dataset.path,base=path.split('#')[0];
  const found=findNode(currentPlan.tree,path)||findNode(currentPlan.tree,base);
  return found&&path!==found.path?{...found,path}:found;
}
document.addEventListener('contextmenu',e=>{
  if(e.defaultPrevented||currentPlan?.options?.right_click!=='ask')return;
  if(e.target.closest?.('input,textarea,[contenteditable=true],.menu'))return;
  const node=nodeAt(e.target);if(!node)return;
  e.preventDefault();openAsk(node,e.clientX,e.clientY);
});
async function fire(node,event,values={}){
  const gesture=node.gestures.find(g=>g.event===event);
  if(!gesture)throw Error('No gesture '+event+' on '+node.path);
  const fields=values.fields;
  const authored=fields&&typeof fields==='object'?gesture.line.replace(/\$fields\b/g,'__AGORA_FIELD_VALUES__'):gesture.line;
  let line=interpolate(authored,{...gesture.env,...values});
  if(fields&&typeof fields==='object')line=line.replace('__AGORA_FIELD_VALUES__',()=>Object.entries(fields).map(([key,value])=>{
    if(!/^[a-z_][a-z0-9_.-]*$/.test(key))throw Error('Invalid field name');return key+'='+Q(value);
  }).join(' '));
  const saw={...node.saw,...values.saw};
  const out=await act(line,saw);
  // Commit-related local selection (for example dismissing a dialog) belongs
  // before the first repaint. A refused word leaves both view and draft intact.
  if(values.select&&typeof values.select==='object'&&!Array.isArray(values.select))viewState={...viewState,...values.select};
  // A previous read may have started before this act. Drain it, then request a
  // reading begun after admission, so a sequential editor save uses fresh revs.
  if(refreshInFlight)await refreshInFlight;
  await refresh();return out;
}
function part(node,name,tag='div',attrs={},...kids){
  const n=P.node(tag,attrs,...kids);n.dataset.component=node.component;n.dataset.part=name;n.dataset.path=node.path;
  n.dataset.facts=JSON.stringify(node.facts);n.dataset.settings=JSON.stringify(node.settings);
  for(const [key,value]of Object.entries(node.facts))if(/^[a-z][a-z0-9_-]*$/.test(key)&&typeof value!=='object')n.setAttribute('data-fact-'+key,String(value));
  return n;
}
function render(node){return renderBoundary(node)}
function renderTrusted(node){
  if(['column','row','text','grid','wrap','split','layers','absolute','scroll'].includes(node.component)){
    const n=part(node,node.name,'div',{class:node.component});
    if(node.role&&/^[\w-]+$/.test(node.role))n.classList.add(node.role);
    if(node.component!=='text'){
      n.dataset.layout=node.component==='column'?'stack':node.component;
      const layout=P.layout(node.component==='column'?'stack':node.component);n.style.cssText=layout.style.cssText;
      n.style.gap=P.tokens[node.settings.gap]||(/^[\d.]+(px|rem|%)$/.test(node.settings.gap||'')?node.settings.gap:'0px');
      if(node.component==='grid'&&/^(?:\d+(?:\.\d+)?(?:fr|px|%)\s*)+$/.test(node.settings.columns||''))n.style.gridTemplateColumns=node.settings.columns;
      for(const key of ['width','height','minHeight','maxHeight','padding']){const val=P.tokens[node.settings[key]]||node.settings[key];if(/^[\d.]+(px|rem|%|vh|vw)$/.test(val||''))n.style[key]=val}
      if(node.component==='absolute')for(const [key,prop] of [['x','left'],['y','top'],['z','zIndex']]){const val=Number(node.settings[key]);if(Number.isFinite(val))n.style[prop]=val+(key==='z'?'':'px')}
    }
    if(node.component==='text')n.textContent=node.display?.text??node.settings.text??'';
    for(const child of node.children)n.append(render(child));n.dataset.root='true';
    if(node.component==='split'){
      const split=P.layout('split',{},...[...n.children]);for(const attr of n.attributes)if(attr.name!=='style')split.setAttribute(attr.name,attr.value);
      for(const key of n.style)if(key!=='grid-template-columns')split.style.setProperty(key,n.style.getPropertyValue(key));
      return split;
    }
    return n;
  }
  const module=moduleCache.get(node.component);
  if(!module)throw Error('Component module did not load');
  const owner=componentOwners.get(node.path);
  const generation=owner.generation;
  const boundP=Object.fromEntries(Object.entries(P).map(([key,value])=>[key,typeof value==='function'?owned(value,owner):value]));
  const api={P:boundP,el:owned(P.node,owner),button:owned(P.press,owner),part:owned((name,tag,attrs,...kids)=>part(node,name,tag,attrs,...kids),owner),palette,flag,Q,
    children:node.children,render,settings:node.settings,facts:node.facts,node,
    child:(name,settings={},key)=>{const child=node.children.find(c=>c.name===name);if(!child)throw Error('Arrange child slot '+name);
      // key: one owner (health, failure, cleanup) per repeated instance, painted at <slot path>#<key>
      const path=key===undefined||key===null?child.path:child.path+'#'+String(key).replace(/[^\w.:-]/g,'_').slice(0,120);
      return render({...child,path,settings:{...child.settings,...settings},display:{...child.display,...settings}})},
    askBox:()=>askBox(node),
    ask:(event,target)=>{event?.preventDefault?.();const n=target?nodeAt(target)||node:nodeAt(event?.target)||node;openAsk(n,event?.clientX??0,event?.clientY??0)},
    display:key=>node.display?.[key]??node.settings[key],format:(key,value,fallback='text')=>P.formatValue(value,node.formats?.[key]||fallback),guard:fn=>owned(fn,owner),
    setTimeout:(fn,ms)=>scoped(owner,()=>setTimeout(fn,ms)),setInterval:(fn,ms)=>scoped(owner,()=>setInterval(fn,ms)),
    requestAnimationFrame:fn=>scoped(owner,()=>requestAnimationFrame(fn)),
    fire:(event,values)=>fire(node,event,values),openMenu,closeMenu,rows,tell,
    fireLatest:(latest,event,values)=>fire(latest,event,values),
    view:()=>({...viewState}), select:values=>{viewState={...viewState,...values};return refresh()},
    // the window's side panels: a button for each on that side, for a component to place in its top bar
    panelButtons:side=>panelsIn(currentPlan?.tree).filter(n=>n.panel.side===side).map(panelButton),
    panelOpen:name=>panelOpen(name), panel:(name,open)=>setPanel(name,!!open),
    read:line=>{if(!renderReadings.has(line))renderReadings.set(line,rows(line));return renderReadings.get(line)},
    draft:owner.draft||(owner.draft={}),
    cleanup:fn=>{if(owner.closed||owner.generation!==generation)fn();else owner.dispose.push(fn)},
    file:async(target,variant='content')=>{
      const {blob}=await agora.file(target,variant);const url=URL.createObjectURL(blob);
      if(owner.closed||owner.generation!==generation){URL.revokeObjectURL(url);throw Error('This file view changed. Please open it again.')}
      owner.dispose.push(()=>URL.revokeObjectURL(url));return {blob,url};
    }, upload:(file,group)=>agora.upload(file,group),
    download:target=>agora.download(target),downloadReading:line=>agora.downloadReading(line),
    downloadGesture:(event,values={})=>{const gesture=node.gestures.find(g=>g.event===event);if(!gesture)throw Error('Arrange a '+event+' gesture');return agora.downloadReading(interpolate(gesture.line,{...gesture.env,...values}))},
    label:(key,fallback=key)=>{if(node.labels?.[key]||node.labels?.[fallback])return node.labels[key]||node.labels[fallback];try{return JSON.parse(api.display('labels')||'{}')[key]||fallback}catch{return fallback}},
    beginDrag:(event,card)=>beginDrag(event,card,node),
    latest:()=>findNode(currentPlan.tree,node.path)||node,
    redraw:refresh};
  const n=module.mount(api,node.settings);n.dataset.component=node.component;n.dataset.path=node.path;n.dataset.root='true';return n;
}
function findNode(node,path){if(node.path===path)return node;for(const c of node.children){const n=findNode(c,path);if(n)return n}}
function beginDrag(e,card,node){
  if(e.button!==0||e.target.closest('button,input,textarea'))return;
  const start={x:e.clientX,y:e.clientY},bounds=card.getBoundingClientRect();let ghost,target,active=false,spring;
  card.setPointerCapture(e.pointerId);
  const move=ev=>{
    if(!active&&Math.hypot(ev.clientX-start.x,ev.clientY-start.y)>5){active=dragging=true;ghost=card.cloneNode(true);ghost.classList.add('dragging');ghost.style.width=bounds.width+'px';document.body.append(ghost);card.style.opacity='.25';spring=P.spring((x,y)=>{ghost.style.left=x+'px';ghost.style.top=y+'px'},{x:bounds.x,y:bounds.y})}
    if(!active)return;spring.to(bounds.x+ev.clientX-start.x,bounds.y+ev.clientY-start.y);
    target=[...document.querySelectorAll('[data-drop]')].find(l=>{const r=l.getBoundingClientRect();return ev.clientX>=r.left&&ev.clientX<=r.right&&ev.clientY>=r.top&&ev.clientY<=r.bottom});document.querySelectorAll('[data-drop]').forEach(l=>l.classList.toggle('over',l===target));
  };
  const finish=async ev=>{
    card.removeEventListener('pointermove',move);card.removeEventListener('pointerup',finish);card.removeEventListener('pointercancel',finish);spring?.stop();ghost?.remove();card.style.opacity='';document.querySelectorAll('.over').forEach(l=>l.classList.remove('over'));dragging=false;
    if(active&&ev.type!=='pointercancel'&&target){const receiver=target._node;try{await fire(receiver,'drop card',{carried:node.facts.id,saw:node.saw})}catch(e){tell(e)}}
    await refresh();
  };
  card.addEventListener('pointermove',move);card.addEventListener('pointerup',finish);card.addEventListener('pointercancel',finish);
}
const defaultTokens=P.tokens;
// The viewer's theme gives the painter's tokens; a lens's own colours are worn through it (themed.js) unless it pins them.
const NOT_TOKENS=new Set(['css','source','hash','variant','name','style']);
const themeTokens=()=>Object.fromEntries(Object.entries(theme).filter(([k,v])=>typeof v==='string'&&!NOT_TOKENS.has(k)));
function applyTokens(plan){
  const worn=Themed.pinned(plan.tokens)?plan.tokens:Themed.tokens(plan.tokens);
  const all={...P.tokens,...themeTokens(),...worn};
  for(const [key,value] of Object.entries(all))if(typeof value==='string')document.documentElement.style.setProperty('--'+key,value);
  if(!Themed.pinned(plan.tokens))Themed.rootVars(new Set(Object.keys(all)));
}
function applyStyles(plan){
  document.querySelector('#part-styles')?.remove();
  const wear=Themed.pinned(plan.tokens)?(v=>v):(v=>Themed.lift(v));
  const tokens={...defaultTokens,...theme,...plan.tokens};
  const rules=[];
  for(const rule of plan.styles){
    if(rule.target==='tokens')continue;
    const m=/^([\w-]+)(?:\.([\w-]+))?(?:\[([\w-]+)=([\w-]+)\])?$/.exec(rule.target||'');
    if(!m)continue;
    const [,component,partName,fact,value]=m;
    const selector=`[data-component="${component}"]`+(partName?`[data-part="${partName}"]`:'[data-root]')+(fact?`[data-fact-${fact}="${value}"]`:'');
    const declarations=[];
    for(const [key,val] of Object.entries(rule.paint||{})){
      if(key==='lines')declarations.push(`display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:${val};overflow:hidden`);
      else if(key==='emphasis')declarations.push('font-weight:'+val);
      else if(key==='glow')declarations.push(`box-shadow:0 0 18px ${wear(val)}`);
      else declarations.push(({radius:'border-radius',size:'font-size'}[key]||key)+':'+(key==='color'||key==='background'?wear(val):val));
    }
    rules.push(selector+'{'+declarations.map(d=>d.replace(/;|$/g,m=>m===';'?'!important;':'!important')).join(';')+'}');
  }
  const style=el('style',{id:'part-styles'},rules.join('\n'));document.head.append(style);
}
let refreshInFlight,refreshAgain=false,repaintAll=false;
function keepTextSelection(){
  const selection=getSelection();if(!selection||selection.isCollapsed)return;
  const root=selection.anchorNode?.parentElement?.closest('[data-path][data-part]');
  if(!root||!root.contains(selection.focusNode))return;
  const offset=(node,n)=>{const range=document.createRange();range.selectNodeContents(root);range.setEnd(node,n);return range.toString().length};
  return {path:root.dataset.path,part:root.dataset.part,text:root.textContent,anchor:offset(selection.anchorNode,selection.anchorOffset),focus:offset(selection.focusNode,selection.focusOffset)};
}
function restoreTextSelection(saved){
  if(!saved)return;const root=[...document.querySelectorAll('[data-path][data-part]')].find(n=>n.dataset.path===saved.path&&n.dataset.part===saved.part);
  if(!root||root.textContent!==saved.text)return;
  const at=offset=>{const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);let node,last;while(node=walker.nextNode()){last=node;if(offset<=node.length)return [node,offset];offset-=node.length}return last?[last,last.length]:[root,0]};
  getSelection().setBaseAndExtent(...at(saved.anchor),...at(saved.focus));
}
function refresh(){
  if(refreshInFlight){refreshAgain=true;return refreshInFlight}
  refreshInFlight=refreshOnce().finally(()=>{refreshInFlight=null;if(refreshAgain){refreshAgain=false;queueMicrotask(()=>refresh().catch(tell))}});
  return refreshInFlight;
}
async function refreshOnce(settling=0){
  if(dragging)return;
  const plan=(await agora.project(viewState)).rows[0];
  viewState={...plan.view,...viewState};
  // the window's size (the lens's `sizes`), and panels following their layout: read again once if either changed
  if(settling<3&&(settleSize(plan)|settlePanels(plan)))return refreshOnce(settling+1);
  // A read begun before pointer capture may finish during a drag. Never replace
  // that captured DOM; its old facts must survive until the fenced drop.
  if(dragging)return;
  const fingerprint=p=>JSON.stringify(p,(key,value)=>key==='parts'?undefined:key==='health'?{quarantined:value.quarantined,action_epoch:value.action_epoch}:value);
  if(currentPlan&&!repaintAll&&fingerprint(plan)===fingerprint(currentPlan)){currentPlan=plan;return}
  repaintAll=false;
  for(const c of plan.components){
    const old=moduleCache.get(c.name);if(old?._source===c.code)continue;
    if(!c.trusted||!plan.parts.some(p=>p.component===c.name&&!p.health.quarantined)){moduleCache.delete(c.name);continue}
    const importing=plan.parts.find(p=>p.component===c.name);
    agora.componentPhase?.({path:importing.part,component:c.name,stage:'module'});
    const url=URL.createObjectURL(new Blob([c.code+'\n//# sourceURL=agora-component/'+c.name+'/'+c.reviewed_code+'.js'],{type:'text/javascript'}));
    try{const mod=await Promise.race([import(url),new Promise((_,reject)=>nativeTimers.setTimeout(()=>reject(Error('Module load exceeded 10000 ms')),10000))]);moduleCache.set(c.name,{...mod.default,_source:c.code});if(mod.default.css)css(mod.default.css)}
    catch(error){moduleCache.set(c.name,{mount(){throw error},_source:c.code})}finally{URL.revokeObjectURL(url);agora.componentPhase?.({path:importing.part,end:true})}
  }
  if(dragging)return;
  const previousPlan=currentPlan;currentPlan=plan;renderReadings=new Map((plan.watches||[]).map(w=>[w.line,Promise.resolve(w.rows)]));
  const focus=document.activeElement;const focused=focus?.dataset.path;const focusedPart=focus?.dataset.part;const selection=focus?.selectionStart;const value=focus?.value;
  const passage=keepTextSelection();
  const next=render(plan.tree);mounted?.remove();document.body.append(next);mounted=next;
  mounted.dataset.view=JSON.stringify(plan.view||{});
  applyTokens(plan);
  document.documentElement.dataset.painter='components';
  if(focused){const n=[...document.querySelectorAll('[data-path]')].find(n=>n.dataset.path===focused&&n.dataset.part===focusedPart);if(n){if(value!==undefined)n.value=value;n.focus();if(typeof selection==='number'&&n.setSelectionRange)n.setSelectionRange(selection,selection)}}
  restoreTextSelection(passage);
  applyStyles(plan);
  applyPanels();
  for(const owner of componentOwners.values())if(owner.element?.isConnected){
    if(!owner.failed&&!owner.node.disabled){
      if(owner.worker&&!owner.workerPainted)continue;
      owner.lastGood=owner.element.cloneNode(true);
      if(!owner.element.dataset.slow)observeComponent(owner,'healthy','',owner.elapsed||0);
      const old=previousPlan&&findNode(previousPlan.tree,owner.node.path);
      for(const binding of owner.node.motions||[]){
        const match=/^fact ([\w.-]+) changes$/.exec(binding.trigger);
        if(match&&old&&old.facts[match[1]]!==owner.node.facts[match[1]])playMotion(owner,binding.token);
      }
    }
  }else if(!findNode(plan.tree,owner.node.path)){owner.closed=true;for(const dispose of owner.dispose.splice(0))try{dispose()}catch{};componentOwners.delete(owner.node.path)}
  for(const owner of componentOwners.values())for(const m of owner.node.motions||[])if(m.trigger.startsWith('happening ')){
    try{await hearMotion(m.trigger.slice(10))}catch(e){observeComponent(owner,'healthy','Motion subscription refused: '+String(e.message||e))}
  }
}
// ---- Panels and sizes (Alex, 4 Nov 2026) -----------------------------------------------------------------------------
// A lens names its window's widths (`sizes narrow 0, middle 1080, wide 1460`): the window's $view.size, which any part
// can read. A part with `panel left|right` is a side panel: open, or shut with no width, from a button in the top bar.
// `shut when <sizes or condition>` is the layout's wish. A panel the layout shut opens again when the wish ends; one you
// shut stays shut; one you open while the layout wants it shut lies over the page. Which panels are open is this
// window's own view ($view.<panel> = open|shut): screen state, sent with each reading so look-view can show it, never
// recorded. `view <window> rail=open` in Lines reaches it too.
const panelBy={},layoutWish={};
function panelsIn(tree){const out=[];(function walk(n){if(!n)return;if(n.panel)out.push(n);for(const c of n.children||[])walk(c)})(tree);return out}
function sizeFor(sizes,width){let name='';for(const [n,from] of sizes||[])if(width>=from)name=n;return name}
function settleSize(plan){const size=sizeFor(plan.sizes,innerWidth);if(!size||viewState.size===size)return false;viewState.size=size;return true}
function settlePanels(plan){
  let changed=false;
  for(const n of panelsIn(plan.tree)){
    const name=n.name,wish=!!n.panel.shut_now,was=layoutWish[name];layoutWish[name]=wish;
    if(was===wish)continue;
    const open=(viewState[name]||'open')!=='shut';
    if(wish&&open){viewState[name]='shut';panelBy[name]='layout';changed=true}
    else if(!wish&&!open&&panelBy[name]==='layout'){viewState[name]='open';delete panelBy[name];changed=true}
  }
  return changed;
}
const panelOpen=name=>(viewState[name]||'open')!=='shut';
function setPanel(name,open,why='you'){
  viewState[name]=open?'open':'shut';if(open)delete panelBy[name];else panelBy[name]=why;
  // one panel lies over the page at a time
  if(open&&layoutWish[name])for(const n of panelsIn(currentPlan?.tree))if(n.name!==name&&layoutWish[n.name]&&panelOpen(n.name)){viewState[n.name]='shut';panelBy[n.name]='layout'}
  applyPanels();return refresh();
}
function panelLabel(n){return String(n.panel.label||n.name)}
function panelButton(n){
  const b=P.node('button',{type:'button',class:'ag-panel-toggle','data-panel-toggle':n.name,'aria-label':panelLabel(n)},P.icon(n.panel.icon||(n.panel.side==='left'?'sidebar':'sidebar-right')));
  b.addEventListener('click',e=>{e.stopPropagation();setPanel(n.name,!panelOpen(n.name)).catch(tell)});return b;
}
function applyPanels(){
  if(!currentPlan)return;let over=false;const panels=panelsIn(currentPlan.tree);
  for(const n of panels){
    const open=panelOpen(n.name),lying=open&&!!layoutWish[n.name];over||=lying;
    // a component that holds the panel in a container of its own marks it data-panel-frame (="<panel>", or empty for
    // the panel inside it): that container opens and shuts. Otherwise the part's own element does.
    const frames=new Set([...document.querySelectorAll('[data-panel-frame]')].filter(f=>f.dataset.panelFrame===n.name));
    for(const el of document.querySelectorAll('[data-path]'))if(el.dataset.path===n.path){
      const f=el.closest('[data-panel-frame]');frames.add(f&&(f.dataset.panelFrame===''||f.dataset.panelFrame===n.name)?f:el)}
    for(const frame of frames){
      frame.dataset.panel=n.panel.side;frame.dataset.panelName=n.name;
      frame.toggleAttribute('data-shut',!open);frame.toggleAttribute('data-over',lying);
      const w=parseInt(n.panel.width,10);if(w>0)frame.style.setProperty('--panel-width',w+'px');
    }
  }
  // a lens whose components place no buttons still gets them, floating at the top corners
  for(const side of ['left','right']){
    const missing=panels.filter(n=>n.panel.side===side&&![...document.querySelectorAll('[data-panel-toggle]')].some(b=>b.dataset.panelToggle===n.name&&!b.closest('.ag-panel-float')));
    let float=document.querySelector('.ag-panel-float.'+side);
    if(!missing.length){float?.remove();continue}
    if(!float){float=P.node('div',{class:'ag-panel-float '+side});document.body.append(float)}
    float.replaceChildren(...missing.map(panelButton));
  }
  for(const b of document.querySelectorAll('[data-panel-toggle]')){
    const n=panels.find(p=>p.name===b.dataset.panelToggle);if(!n)continue;const open=panelOpen(n.name);
    b.setAttribute('aria-pressed',String(open));b.title=(open?'Hide ':'Show ')+panelLabel(n).toLowerCase();
  }
  const bar=document.querySelector('[data-panel-toggle]')?.closest('header,[role=banner]');
  document.documentElement.style.setProperty('--ag-panel-top',(bar?Math.round(bar.getBoundingClientRect().bottom):0)+'px');
  document.documentElement.toggleAttribute('data-panel-over',over);
}
// a click on the page, or Escape, shuts a panel lying over it
document.addEventListener('pointerdown',e=>{
  if(!document.documentElement.hasAttribute('data-panel-over')||e.target.closest('[data-panel][data-over],[data-panel-toggle],.ag-panel-float'))return;
  for(const n of panelsIn(currentPlan?.tree))if(layoutWish[n.name]&&panelOpen(n.name)){viewState[n.name]='shut';panelBy[n.name]='layout'}
  applyPanels();refresh().catch(tell);
},true);
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&document.documentElement.hasAttribute('data-panel-over')){
  for(const n of panelsIn(currentPlan?.tree))if(layoutWish[n.name]&&panelOpen(n.name)){viewState[n.name]='shut';panelBy[n.name]='layout'}
  applyPanels();refresh().catch(tell)}});
let sizeTimer;
addEventListener('resize',()=>{applyPanels();clearTimeout(sizeTimer);sizeTimer=setTimeout(()=>{if(currentPlan&&sizeFor(currentPlan.sizes,innerWidth)!==(viewState.size||''))refresh().catch(tell)},120)});
// view <window> key=value from Lines: only this person's own windows are told (the kernel addresses it to them)
async function hearViews(){try{await agora.hear('view',event=>{
  if(event.target!==(definition.id||widget.id||widget))return;
  let values={};try{values=JSON.parse(event.text||'{}')}catch{return}
  for(const [key,value] of Object.entries(values)){
    const n=panelsIn(currentPlan?.tree).find(p=>p.name===key);
    if(n&&(value==='open'||value==='shut')){viewState[key]=value;if(value==='open')delete panelBy[key];else panelBy[key]='you'}
    else viewState[key]=value;
  }
  applyPanels();refresh().catch(tell);
})}catch{/* a widget installed before 4 Nov holds no hear:view grant; its panels still work from the buttons */}}
// The theme changed (the host sends it; common.js has already updated `theme`): repaint the tokens and styles at once.
addEventListener('ag-theme',()=>{
  Object.assign(P.tokens,themeTokens());
  // Components that took colours at mount (a card's tint) are mounted again; drafts live in api.draft and survive.
  // (repaintAll, not currentPlan=null: a part that paints on its own clock, a dock adding an app, still has a plan)
  if(currentPlan){applyTokens(currentPlan);applyStyles(currentPlan);repaintAll=true;refresh().catch(tell)}
});
function playMotion(owner,token){
  const defaults={settle:{from:{opacity:.5,transform:'translateY(6px)'},to:{opacity:1,transform:'none'},duration:200},pulse:{from:{transform:'scale(.96)'},to:{transform:'scale(1)'},duration:180}};
  const motion=currentPlan.tokens?.['motion-'+token]||defaults[token];
  if(!motion){tell('Unknown theme motion '+token);return}
  P.motion(owner.element,motion);owner.element.dataset.lastMotion=token;
}
document.addEventListener('click',e=>{if(menu&&!menu.contains(e.target)&&!e.target.closest('.cardtop'))closeMenu()});
document.addEventListener('keydown',e=>{if(e.key==='Escape'){closeMenu();document.querySelector('.veil')?.remove()}if(e.key.toLowerCase()==='n'&&!e.ctrlKey&&!e.metaKey&&!['INPUT','TEXTAREA'].includes(document.activeElement.tagName)){e.preventDefault();document.querySelector('[aria-label="Add a task"]')?.focus()}});
const heard=new Set();
async function hearMotion(word){if(heard.has(word))return;heard.add(word);await agora.hear(word,event=>{
  for(const owner of componentOwners.values())if(owner.element?.isConnected&&!owner.failed&&Object.hasOwn(owner.node.saw,event.target)){
    for(const binding of owner.node.motions||[])if(binding.trigger==='happening '+word)playMotion(owner,binding.token);
  }
  soon();
})}
// A hidden window (minimised, tucked, covered) reads nothing: what it heard, and its safety reread, wait until it is
// seen again, then one fresh plan catches it up. Six tucked boards no longer replan the world on every act (27 Oct).
function soon(){if(document.hidden)return;clearTimeout(refreshTimer);refreshTimer=setTimeout(()=>refresh().catch(tell),80)}
document.addEventListener('visibilitychange',()=>{if(document.hidden)return;clearTimeout(refreshTimer);refresh().catch(tell)});
for(const word of ['make','set','forget','undo','component','component-action'])await hearMotion(word);
await hearViews();
await refresh();
// A forgotten/private target may no longer be hearable. Time-dependent bindings
// also have no world happening. Reconcile the visible projection, without
// widening the event stream or revealing why a row disappeared.
// A lens may ask for a slower (or faster) safety reread: reconcile_ms, 500..60000 (default 5000; was 1500 until 27 Oct,
// when each reread was a whole-world plan and six windows kept the kernel busy). Heard happenings still refresh at once.
let reconcileMs=0,reconcileTimer;
const reconcileWanted=()=>Math.max(500,Math.min(60000,Number(currentPlan?.options?.reconcile_ms)||5000));
(function reconcile(){
  reconcileMs=reconcileWanted();nativeTimers.clearInterval(reconcileTimer);
  reconcileTimer=nativeTimers.setInterval(()=>{if(!document.hidden)refresh().catch(tell);if(reconcileWanted()!==reconcileMs)reconcile()},reconcileMs);
})();
