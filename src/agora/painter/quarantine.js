// EDITING THE PAINTER (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
// The painter's vocabulary (formats, handles, scopes, parts) is shared by every app. Add to it only what any lens could
// use, documented where lens authors read it (ARRANGEMENT.md); never a handle, format or branch for one app. If one app
// needs something, the general form of it is the change.
//
// Worker-side DOM vocabulary. A quarantine is a thread boundary, not a browser
// renderer process. Unsupported DOM facilities stop this part explicitly.
function quarantineWorker(){
  const callbacks=new Map(),nodes=new Map();let sequence=0,root,api,dirty=false;
  const send=globalThis.postMessage.bind(globalThis);
  const fail=e=>send({kind:'error',error:String(e?.message||e).split('\n')[0]});
  const schedule=()=>{if(dirty)return;dirty=true;nativeTimeout(()=>{dirty=false;if(root)send({kind:'paint',tree:encode(root)})},16)};
  class Node{
    constructor(tag='div'){this.id=++sequence;nodes.set(this.id,this);this.tag=tag;this.attrs={};this.style={};this.dataset={};this.children=[];this.listeners={};this._text='';this.hidden=false;
      this.classList={add:(...v)=>{this.attrs.class=[...new Set((this.attrs.class||'').split(' ').concat(v))].join(' ');schedule()},remove:(...v)=>{this.attrs.class=(this.attrs.class||'').split(' ').filter(x=>!v.includes(x)).join(' ');schedule()},contains:v=>(this.attrs.class||'').split(' ').includes(v),toggle:(v,on)=>{const next=on??!this.classList.contains(v);this.classList[next?'add':'remove'](v);return next}}}
    set textContent(v){this._text=String(v??'');this.children=[];schedule()}
    get textContent(){return this._text+this.children.map(x=>typeof x==='string'?x:x.textContent).join('')}
    set className(v){this.attrs.class=v}get className(){return this.attrs.class||''}
    append(...children){for(const c of children.flat()){if(c===null||c===undefined)continue;if(c instanceof Node)c.parentElement=this;this.children.push(c instanceof Node?c:String(c))}schedule()}
    replaceChildren(...c){this.children=[];this.append(...c)}
    addEventListener(event,fn){(this.listeners[event]??=[]).push(fn)}
    removeEventListener(event,fn){this.listeners[event]=(this.listeners[event]||[]).filter(x=>x!==fn)}
    setAttribute(k,v){if(k==='style')throw Error('Worker DOM uses style properties');this.attrs[k]=String(v);schedule()}
    getAttribute(k){return this.attrs[k]??null}
    removeAttribute(k){delete this.attrs[k];schedule()}
    remove(){if(this.parentElement)this.parentElement.children=this.parentElement.children.filter(x=>x!==this);schedule()}
    focus(){}setPointerCapture(){}releasePointerCapture(){}
    matches(s){return s.split(',').some(q=>q.trim().startsWith('.')?this.classList.contains(q.trim().slice(1)):this.tag===q.trim())}
    closest(s){return this.matches(s)?this:this.parentElement?.closest(s)||null}
    querySelectorAll(s){return this.children.filter(x=>x instanceof Node).flatMap(x=>[...(x.matches(s)?[x]:[]),...x.querySelectorAll(s)])}
    querySelector(s){return this.querySelectorAll(s)[0]||null}
    getBoundingClientRect(){throw Error('Worker quarantine cannot synchronously measure DOM; use arranged layout')}
    animate(){return {cancel(){}}}
  }
  const encode=n=>typeof n==='string'?n:({id:n.id,tag:n.tag,attrs:n.attrs,style:n.style,dataset:n.dataset,text:n._text,
    hidden:n.hidden,value:n.value,checked:n.checked,events:Object.keys(n.listeners),children:n.children.map(encode)});
  const make=(tag,attrs={},...kids)=>{const n=new Node(tag);for(const [k,v]of Object.entries(attrs)){if(k==='on')for(const [e,f]of Object.entries(v))n.addEventListener(e,f);else if(k==='style')Object.assign(n.style,v);else if(k==='value')n.value=v;else n.setAttribute(k,v)}n.append(...kids);return n};
  globalThis.document={createElement:tag=>new Node(tag),querySelector:s=>root?.querySelector(s),querySelectorAll:s=>root?.querySelectorAll(s)||[]};
  globalThis.window=globalThis;
  const nativeTimeout=setTimeout,nativeInterval=setInterval,nativeMicrotask=queueMicrotask;
  const guard=fn=>(...args)=>{try{const out=fn(...args);if(out?.then)out.then(schedule,fail);schedule();return out}catch(e){fail(e)}};
  globalThis.setTimeout=(fn,ms,...args)=>nativeTimeout(guard(fn),ms,...args);
  globalThis.setInterval=(fn,ms,...args)=>nativeInterval(guard(fn),Math.max(16,ms||0),...args);
  globalThis.queueMicrotask=fn=>nativeMicrotask(guard(fn));
  globalThis.requestAnimationFrame=fn=>setTimeout(()=>fn(performance.now()),16);
  globalThis.cancelAnimationFrame=clearTimeout;
  addEventListener('error',e=>{e.preventDefault();fail(e.error||e.message)});
  addEventListener('unhandledrejection',e=>{e.preventDefault();fail(e.reason)});
  nativeInterval(()=>send({kind:'heartbeat'}),250);
  addEventListener('message',guard(async e=>{
    const m=e.data;
    if(m.kind==='event'){
      const n=nodes.get(m.id);if(!n)return;n.value=m.value;n.checked=m.checked;
      const ev={...m.event,target:n,currentTarget:n,preventDefault(){},stopPropagation(){}};
      for(const f of n.listeners[m.event.type]||[])await f(ev);schedule();return;
    }
    if(m.kind!=='start')return;
    const node=m.node;
    const P={tokens:m.tokens,node:make,press:(label,fn,cls='')=>make('button',{class:cls,on:{click:fn}},label),
      layout:(mode,attrs={},...kids)=>make('div',{...attrs,'data-layout':mode,style:{display:mode==='grid'?'grid':'flex',flexDirection:mode==='row'?'row':'column',...attrs.style}},...kids),
      content:(kind,value,attrs={})=>make('span',attrs,kind==='avatar'?String(value).split(/\s+/).map(w=>w[0]).join('').slice(0,2).toUpperCase():value),
      input:(kind,attrs)=>make(kind==='multiline'?'textarea':'input',attrs),navigation:n=>n,
      motion:()=>({cancel(){}})};
    const fire=(event,values={})=>{send({kind:'gesture',event,values});return Promise.resolve()};
    api={P,el:make,button:P.press,node,facts:node.facts,settings:node.settings,children:node.children,
      display:key=>node.display?.[key]??node.settings[key],part:(name,tag='div',attrs={},...kids)=>make(tag,{...attrs,'data-part':name},...kids),
      setTimeout:globalThis.setTimeout,setInterval:globalThis.setInterval,requestAnimationFrame:globalThis.requestAnimationFrame,guard,
      fire,fireLatest:(_,event,values)=>fire(event,values),latest:()=>node,
      palette:m.palette,flag:p=>make('span',{},'⚑'),Q:JSON.stringify,tell:fail,
      render:()=>{throw Error('Worker quarantine cannot nest arbitrary component modules; arrange siblings outside it')},
      rows:()=>{throw Error('Worker quarantine takes projected facts; arrange data through the lens')},
      beginDrag:()=>{throw Error('Worker quarantine does not own native drag; use an in-page wrapper')},
      redraw:schedule,openMenu:()=>{throw Error('Worker quarantine menus need an arranged sibling')},closeMenu(){}};
    const url=URL.createObjectURL(new Blob([m.code+'\n//# sourceURL=agora-component/'+node.component+'.js'],{type:'text/javascript'}));
    try{const mod=await import(url);root=await mod.default.mount(api,node.settings);if(!(root instanceof Node))throw Error('mount must return a DOM primitive');schedule()}finally{URL.revokeObjectURL(url)}
  }));
}

function quarantinedMount(node,definition,owner){
  owner.workerPainted=false;
  const root=part(node,node.name,'section',{'aria-label':node.component+' in quarantine'});
  root.dataset.quarantined='true';root.textContent='Starting '+node.component+'…';
  const url=URL.createObjectURL(new Blob(['('+quarantineWorker.toString()+')()'],{type:'text/javascript'}));
  let worker;
  try{worker=new Worker(url)}finally{URL.revokeObjectURL(url)}
  let last=performance.now(),painted=false,closed=false;
  const kill=()=>{if(closed)return;closed=true;clearInterval(watch);worker.terminate()};
  const watch=setInterval(()=>{if(performance.now()-last>2500){kill();componentFailed(owner,Error('No heartbeat for 2500 ms; isolated worker stopped'))}},250);
  owner.dispose.push(kill);
  const tags=new Set('div section article main header footer span p strong em code pre h1 h2 h3 button input textarea select option label progress ul ol li img table thead tbody tr th td details summary i b small'.split(' '));
  const paint=(tree,depth=0,counter={n:0})=>{
    if(++counter.n>2000||depth>32)throw Error('Worker drawing exceeded 2000 nodes or 32 levels');
    if(typeof tree==='string')return document.createTextNode(tree.slice(0,10000));
    if(!tags.has(tree.tag))throw Error('Worker drawing tag is not a primitive: '+tree.tag);
    const n=document.createElement(tree.tag);
    for(const [key,value]of Object.entries(tree.attrs||{}))if(/^(?:class|title|role|type|placeholder|tabindex|disabled|readonly|max|min|alt|scope|aria-[\w-]+|data-[\w-]+)$/.test(key))n.setAttribute(key,String(value).slice(0,1000));
    for(const [key,value]of Object.entries(tree.style||{}))if(/^[a-zA-Z]+$/.test(key)&&!/(?:url|expression|@import)/i.test(String(value)))n.style[key]=String(value).slice(0,1000);
    for(const [key,value]of Object.entries(tree.dataset||{}))if(/^[\w]+$/.test(key))n.dataset[key]=String(value).slice(0,1000);
    n.textContent=String(tree.text||'').slice(0,10000);n.hidden=!!tree.hidden;
    if(tree.value!==undefined)n.value=tree.value;if(tree.checked!==undefined)n.checked=tree.checked;
    for(const event of tree.events||[])if(['click','change','input','keydown','keyup','contextmenu','dblclick','pointerdown','pointerup'].includes(event))n.addEventListener(event,e=>{
      if(event==='contextmenu')e.preventDefault();
      worker.postMessage({kind:'event',id:tree.id,value:n.value,checked:n.checked,event:{type:event,key:e.key,button:e.button,clientX:e.clientX,clientY:e.clientY,ctrlKey:e.ctrlKey,metaKey:e.metaKey}})
    });
    for(const child of tree.children||[])n.append(paint(child,depth+1,counter));return n;
  };
  worker.onmessage=e=>{
    if(closed)return;
    const m=e.data;if(m?.kind==='heartbeat'){last=performance.now();return}
    if(m?.kind==='error'){kill();componentFailed(owner,Error(m.error));return}
    if(m?.kind==='gesture'){scoped(owner,()=>fire(node,m.event,m.values));return}
    if(m?.kind==='paint')try{
      root.replaceChildren(paint(m.tree));painted=true;owner.workerPainted=true;owner.lastGood=root.cloneNode(true);owner.element=root;
      observeComponent(owner,'healthy');
    }catch(e){kill();componentFailed(owner,e)}
  };
  worker.onerror=e=>{e.preventDefault();kill();componentFailed(owner,Error(e.message))};
  worker.postMessage({kind:'start',node,code:definition.code,tokens:P.tokens,palette});
  return root;
}
