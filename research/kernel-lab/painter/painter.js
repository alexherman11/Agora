// Trusted arrangement runtime; component code supplies pixels, never the reading.
// The entire painter uses the existing guarded widget surface and bridge.
const {widget} = await agora.ready;
const definition = (await rows('rows widget')).find(w=>w.id===widget.id||w.id===widget);
const lensName = definition.component_lens;
let mounted, dragging=false, refreshTimer, menu, menuReturnFocus, currentPlan;
const moduleCache=new Map();
const interpolate=(text,env)=>String(text).replace(/\$([\w.-]+)/g,(matched,path,offset,source)=>{
  let value=env;for(const bit of path.split('.'))value=value?.[bit];
  if(value&&typeof value==='object')value=value.id;
  // Every dynamic value is data, including inside an authored quoted argument.
  let quoted=false,escaped=false;
  for(const ch of source.slice(0,offset)){if(escaped){escaped=false;continue}if(ch==='\\'){escaped=true;continue}if(ch==='"')quoted=!quoted}
  return quoted?String(value??'').replace(/\\/g,'\\\\').replace(/"/g,'\\"'):Q(value);
});
function closeMenu(){menu?.remove();menu=null;if(menuReturnFocus?.isConnected)menuReturnFocus.focus();menuReturnFocus=null}
function openMenu(node,x,y){
  if(!node)return;closeMenu();menuReturnFocus=document.activeElement;menu=render(node);menu.hidden=false;menu.classList.add('menu');
  document.body.append(menu);const r=menu.getBoundingClientRect();
  menu.style.left=Math.max(8,Math.min(x,innerWidth-r.width-10))+'px';
  menu.style.top=Math.max(8,Math.min(y,innerHeight-r.height-10))+'px';
  P.navigation(menu,{menu:true});menu.querySelector('button')?.focus();
}
async function fire(node,event,values={}){
  const gesture=node.gestures.find(g=>g.event===event);
  if(!gesture)throw Error('No gesture '+event+' on '+node.path);
  const line=interpolate(gesture.line,{...gesture.env,...values});
  const saw={...node.saw,...values.saw};
  const out=await act(line,saw);
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
function render(node){
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
    if(node.component==='text')n.textContent=node.settings.text||'';
    for(const child of node.children)n.append(render(child));n.dataset.root='true';
    if(node.component==='split'){
      const split=P.layout('split',{},...[...n.children]);for(const attr of n.attributes)if(attr.name!=='style')split.setAttribute(attr.name,attr.value);
      for(const key of n.style)if(key!=='grid-template-columns')split.style.setProperty(key,n.style.getPropertyValue(key));
      return split;
    }
    return n;
  }
  const module=moduleCache.get(node.component);
  const api={P,el:P.node,button:P.press,part:(name,tag,attrs,...kids)=>part(node,name,tag,attrs,...kids),palette,flag,Q,
    children:node.children,render,settings:node.settings,facts:node.facts,node,
    fire:(event,values)=>fire(node,event,values),openMenu,closeMenu,rows,tell,
    fireLatest:(latest,event,values)=>fire(latest,event,values),
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
function applyStyles(plan){
  document.querySelector('#part-styles')?.remove();
  const tokens={...defaultTokens,...theme,...Object.fromEntries(plan.styles.filter(s=>s.target==='tokens').flatMap(s=>Object.entries(s).filter(([k])=>!['id','rev','by','kind','lens','target','made_by','made_at','changed_at'].includes(k))))};
  const rules=[];
  for(const rule of plan.styles){
    if(rule.target==='tokens')continue;
    const m=/^([\w-]+)(?:\.([\w-]+))?(?:\[([\w-]+)=([\w-]+)\])?$/.exec(rule.target||'');
    if(!m)throw Error('Style target must be component.part[fact=value]');
    const [,component,partName,fact,value]=m;
    const selector=`[data-component="${component}"]`+(partName?`[data-part="${partName}"]`:'[data-root]')+(fact?`[data-fact-${fact}="${value}"]`:'');
    const declarations=[];
    for(const key of ['color','background','radius','padding','gap','glow','lines','emphasis'])if(rule[key]!==undefined){
      const val=tokens[rule[key]]??rule[key];
      if(key==='lines'){if(!/^[1-9]$/.test(String(val)))throw Error('lines: 1..9');declarations.push(`display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:${val};overflow:hidden`)}
      else if(key==='emphasis'){if(!['normal','bold'].includes(val))throw Error('emphasis: normal|bold');declarations.push('font-weight:'+val)}
      else if(key==='glow'){if(!/^#[\da-f]{6}$/i.test(val))throw Error('glow needs a colour token');declarations.push(`box-shadow:0 0 18px ${val}55`)}
      else {if(!/^(#[\da-f]{3,8}|\d+(?:\.\d+)?(?:px|rem|%)|transparent)$/i.test(val))throw Error('style needs a colour or measure token');declarations.push(({radius:'border-radius'}[key]||key)+':'+val)}
    }
    rules.push(selector+'{'+declarations.map(d=>d.replace(/;|$/g,m=>m===';'?'!important;':'!important')).join(';')+'}');
  }
  const style=el('style',{id:'part-styles'},rules.join('\n'));document.head.append(style);
}
let refreshInFlight,refreshAgain=false;
function refresh(){
  if(refreshInFlight){refreshAgain=true;return refreshInFlight}
  refreshInFlight=refreshOnce().finally(()=>{refreshInFlight=null;if(refreshAgain){refreshAgain=false;queueMicrotask(()=>refresh().catch(tell))}});
  return refreshInFlight;
}
async function refreshOnce(){
  if(dragging)return;
  const plan=(await rows('look-view '+Q(lensName)))[0];
  // A read begun before pointer capture may finish during a drag. Never replace
  // that captured DOM; its old facts must survive until the fenced drop.
  if(dragging)return;
  if(JSON.stringify(plan)===JSON.stringify(currentPlan))return;
  for(const c of plan.components){
    const old=moduleCache.get(c.name);if(old?._source===c.code)continue;
    if(!c.reviewed_code)continue;
    const url=URL.createObjectURL(new Blob([c.code],{type:'text/javascript'}));
    try{const mod=await import(url);moduleCache.set(c.name,{...mod.default,_source:c.code});if(mod.default.css)css(mod.default.css)}finally{URL.revokeObjectURL(url)}
  }
  if(dragging)return;
  currentPlan=plan;
  const focus=document.activeElement;const focused=focus?.dataset.path;const focusedPart=focus?.dataset.part;const selection=focus?.selectionStart;const value=focus?.value;
  const next=render(plan.tree);mounted?.remove();document.body.append(next);mounted=next;
  if(focused){const n=[...document.querySelectorAll('[data-path]')].find(n=>n.dataset.path===focused&&n.dataset.part===focusedPart);if(n){if(value!==undefined)n.value=value;n.focus();if(typeof selection==='number'&&n.setSelectionRange)n.setSelectionRange(selection,selection)}}
  applyStyles(plan);
}
document.addEventListener('click',e=>{if(menu&&!menu.contains(e.target)&&!e.target.closest('.cardtop'))closeMenu()});
document.addEventListener('keydown',e=>{if(e.key==='Escape'){closeMenu();document.querySelector('.veil')?.remove()}if(e.key.toLowerCase()==='n'&&!e.ctrlKey&&!e.metaKey&&!['INPUT','TEXTAREA'].includes(document.activeElement.tagName)){e.preventDefault();document.querySelector('[aria-label="Add a task"]')?.focus()}});
for(const word of ['make','set','forget','undo','component'])await agora.hear(word,()=>{clearTimeout(refreshTimer);refreshTimer=setTimeout(()=>refresh().catch(tell),80)});
await refresh();
// A forgotten/private target may no longer be hearable. Time-dependent bindings
// also have no world happening. Reconcile the visible projection, without
// widening the event stream or revealing why a row disappeared.
setInterval(()=>refresh().catch(tell),1500);
