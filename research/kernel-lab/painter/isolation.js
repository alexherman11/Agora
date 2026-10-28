// Trusted, deliberately small ownership boundary. In-page modules are reviewed,
// cooperative code: a synchronous infinite loop requires native host recovery.
const componentOwners=new Map(),pendingObservations=new Map();
let activeOwner=null,observationTimer;
const nativeTimers=Object.fromEntries(Object.entries({setTimeout,clearTimeout,setInterval,clearInterval,requestAnimationFrame,cancelAnimationFrame,queueMicrotask}).map(([key,fn])=>[key,fn.bind(globalThis)]));
function scoped(owner,fn){
  const previous=activeOwner;activeOwner=owner;const started=performance.now(),timed=owner&&!owner.phaseDepth;
  beginPhase(owner,'callback');
  try{const out=fn();if(out?.then)return out.catch(e=>componentFailed(owner,e));return out}
  catch(e){componentFailed(owner,e)}finally{
    const elapsed=performance.now()-started;
    if(timed&&elapsed>32&&!owner.failed)slowed(owner,'Callback exceeded 32 ms',elapsed);
    endPhase(owner);activeOwner=previous;
  }
}
// One slow moment (a GPU compiling shaders, a big window resizing, a pause) is not a slow part. A part counts toward
// quarantine only when it is slow again within 10 s; before, every slow callback counted for the life of the window,
// so a map animating for an hour on a 4K screen was always quarantined in the end (28 Oct).
function slowed(owner,message,elapsed){
  const now=performance.now(),again=owner.slowAt&&now-owner.slowAt<10000;owner.slowAt=now;
  if(!again)return;
  owner.failures++;observeComponent(owner,'slow',message,elapsed);
}
function beginPhase(owner,stage){if(!owner)return;if(!owner.phaseDepth++)agora.componentPhase?.({path:owner.node.path,component:owner.node.component,stage})}
function endPhase(owner){if(owner&&!--owner.phaseDepth)agora.componentPhase?.({path:owner.node.path,end:true})}
function owned(fn,owner=activeOwner){return !owner||typeof fn!=='function'?fn:function(...args){return scoped(owner,()=>fn.apply(this,args))}}
for(const name of ['setTimeout','setInterval','requestAnimationFrame','queueMicrotask'])globalThis[name]=function(fn,...args){
  const owner=activeOwner,token=nativeTimers[name](owned(fn,owner),...args);
  if(owner&&name!=='queueMicrotask')owner.dispose.push(()=>nativeTimers[name==='setInterval'?'clearInterval':name==='requestAnimationFrame'?'cancelAnimationFrame':'clearTimeout'](token));
  return token;
};
const addListener=EventTarget.prototype.addEventListener,removeListener=EventTarget.prototype.removeEventListener;
const listenerOwners=new WeakMap();
EventTarget.prototype.addEventListener=function(event,fn,options){
  if(activeOwner&&typeof fn==='function'){
    let registrations=listenerOwners.get(this);if(!registrations)listenerOwners.set(this,registrations=[]);
    const capture=typeof options==='boolean'?options:!!options?.capture;
    let record=registrations.find(r=>r.event===event&&r.fn===fn&&r.capture===capture);
    if(!record){record={event,fn,capture,wrapped:owned(fn)};registrations.push(record)}
    return addListener.call(this,event,record.wrapped,options);
  }
  return addListener.call(this,event,fn,options);
};
EventTarget.prototype.removeEventListener=function(event,fn,options){
  const capture=typeof options==='boolean'?options:!!options?.capture;
  const r=listenerOwners.get(this)?.find(r=>r.event===event&&r.fn===fn&&r.capture===capture);
  return removeListener.call(this,event,r?.wrapped||fn,options);
};
function ownerFor(node){
  let owner=componentOwners.get(node.path);
  if(!owner){owner={node,dispose:[],failures:0,element:null,lastGood:null,failed:false,epoch:0,phaseDepth:0};componentOwners.set(node.path,owner)}
  // Try again, clear or off (each a new action epoch) starts the part's count afresh on this page too.
  const epoch=node.health?.action_epoch||0;if(epoch!==owner.epoch){owner.failures=0;owner.slowAt=0}
  owner.node=node;owner.epoch=epoch;return owner;
}
function paintedParts(owner){
  const root=owner.element;if(!root)return [];
  return [root,...root.querySelectorAll('[data-part]')].filter(n=>n.dataset.path===owner.node.path||!n.dataset.path).slice(0,60).map(n=>{
    const style=getComputedStyle(n);return {part:n.dataset.part||owner.node.name,text:n.hidden?'':(n.innerText||n.textContent||'').slice(0,400),
      visible:!n.hidden&&style.display!=='none'&&style.visibility!=='hidden',styles:{color:style.color,background:style.backgroundColor,padding:style.padding,radius:style.borderRadius,glow:style.boxShadow},stale:n.closest('[data-stale]')!==null}
  });
}
function observeComponent(owner,health,error='',elapsed=0){
  // Only failures, and the recovery after one, are reported, and only to this screen's health table (painter/health.py:
  // kernel memory, never the log). Painted text and styles are never sent (Alex, 26 Oct: "visual state should not live
  // in the world"). paintedParts() is still here for a local reader.
  const bad=health==='stopped'||health==='slow';
  if(!bad&&!owner.reportedBad)return;
  owner.reportedBad=bad;
  const report={path:owner.node.path,health,last_error:String(error?.message||error).split('\n')[0].slice(0,300),elapsed_ms:elapsed,
    source:owner.sourceTag||'',painted:[]};
  const key=JSON.stringify({...report,elapsed_ms:0});
  if(owner.observed===key)return;owner.observed=key;pendingObservations.set(owner.node.path,report);
  nativeTimers.clearTimeout(observationTimer);observationTimer=nativeTimers.setTimeout(flushObservations,180);
}
async function flushObservations(){
  if(!currentPlan||!pendingObservations.size)return;
  const reports=[...pendingObservations.values()];pendingObservations.clear();
  // Stay below the ordinary bridge's line bound. No telemetry uses task writes.
  const chunks=[];let chunk=[];
  for(const r of reports){if(JSON.stringify([...chunk,r]).length>42000){chunks.push(chunk);chunk=[]}chunk.push(r)}if(chunk.length)chunks.push(chunk);
  for(const data of chunks)try{await agora.do('component-health '+currentPlan.lens+' data='+Q(JSON.stringify(data)))}catch(e){console.warn('Component report refused',String(e.message||e))}
}
function stoppedCard(owner,error,off=false){
  const node=owner.node,card=part(node,'stopped','section',{class:'component-stopped',role:'status'});if(off)card.dataset.off='yes';
  card.append(el('strong',{},off?'This part is turned off':'This part stopped'),el('div',{},node.component.replace(/-/g,' ')),
    el('p',{},String(error?.message||error||'Try again when you are ready.').split('\n')[0].slice(0,300)));
  const controls=el('div',{class:'component-recovery'});
  for(const [label,action]of [['Try again','retry'],['Use the previous version','previous'],['Turn it off','off']]){
    controls.append(el('button',{type:'button',on:{click:async()=>{
      try{
        const fresh=(await rows('look-view '+Q(lensName)+' plan=yes'))[0];
        const preferences=await rows('rows view-preference');
        const saw=Object.fromEntries([...(fresh.components||[]),...(fresh.styles||[]),...preferences].map(c=>[c.id,c.rev]));
        // Lens and personal preferences are marked by look-view; explicit fresh
        // revisions cover rollback without accidentally undoing a neighbour.
        const lens=(await rows('look '+fresh.lens))[0];saw[fresh.lens]=lens.rev??(await rows('rows lens')).find(l=>l.id===fresh.lens)?.rev;
        await agora.do('component-action '+fresh.lens+' path='+Q(node.path)+' action='+action,saw);
        owner.failed=false;owner.observed=null;owner.source=null;await refresh();
      }catch(e){card.querySelector('p').textContent=String(e.message||e).split('\n')[0]}
    }}},label));
  }
  card.append(controls);return card;
}
function componentFailed(owner,error){
  if(!owner)return console.error(error);
  if(owner.element?.isConnected&&!owner.element.classList.contains('component-stopped')&&(!owner.worker||owner.workerPainted))owner.lastGood=owner.element.cloneNode(true);
  owner.failed=true;owner.failures++;owner.error=error;
  for(const dispose of owner.dispose.splice(0))try{dispose()}catch{}
  const shell=stoppedCard(owner,error);
  if(owner.lastGood){const stale=owner.lastGood.cloneNode(true);stale.dataset.stale='true';stale.inert=true;stale.setAttribute('aria-label','Last good rendering, stale');
    // File URLs are revoked when their owner stops. Keep the readable stale
    // content, with an honest placeholder rather than a broken/revoked player.
    for(const media of stale.querySelectorAll('img,audio,video'))if((media.getAttribute('src')||'').startsWith('blob:'))media.replaceWith(el('p',{class:'component-stale-media'},'Previous attachment preview · retry to reopen'));
    shell.prepend(el('small',{},'Last good rendering · stale'),stale)}
  owner.element?.replaceWith(shell);owner.element=shell;
  observeComponent(owner,'stopped',error);return shell;
}
function renderBoundary(node){
  const primitive=['column','row','text','grid','wrap','split','layers','absolute','scroll'].includes(node.component);
  const owner=ownerFor(node),definition=currentPlan.components.find(c=>c.name===node.component);
  const source=JSON.stringify([definition?.code,node.settings,node.display,node.facts,node.error,node.disabled,node.health?.action_epoch,node.health?.quarantined]);
  if(owner.failed&&owner.source===source)return owner.element;
  if(owner.worker&&owner.source===source)return owner.element;
  owner.generation=(owner.generation||0)+1;owner.closed=false;
  owner.source=source;owner.sourceTag=definition?.reviewed_code||'unreviewed';owner.failed=false;
  for(const dispose of owner.dispose.splice(0))try{dispose()}catch{}
  if(node.disabled){owner.element=stoppedCard(owner,'Turned off for this viewer.',true);return owner.element}
  if(node.error){owner.element=componentFailed(owner,Error(node.error));return owner.element}
  if(!definition&&!primitive){owner.element=componentFailed(owner,Error('Component module is missing'));return owner.element}
  if(!primitive&&(node.health?.quarantined||owner.failures>=2)){
    const previous=activeOwner;activeOwner=owner;
    try{owner.worker=true;owner.element=quarantinedMount(node,definition,owner);return owner.element}catch(e){return componentFailed(owner,e)}finally{activeOwner=previous}
  }
  owner.worker=false;
  const started=performance.now(),previous=activeOwner;owner.childrenTime=0;activeOwner=owner;
  if(!primitive)beginPhase(owner,'mount');
  try{
    const n=renderTrusted(node);if(!n?.nodeType)throw Error('mount must return a DOM node');
    owner.element=n;
    const elapsed=Math.max(0,performance.now()-started-owner.childrenTime);owner.elapsed=elapsed;
    owner.lastGood=n.cloneNode(true);
    if(!primitive&&elapsed>32){n.dataset.slow='true';n.title='This part took '+elapsed.toFixed(1)+' ms (budget 32 ms)';slowed(owner,'Mount/update exceeded 32 ms',elapsed)}
    return n;
  }catch(e){return componentFailed(owner,e)}finally{if(!primitive)endPhase(owner);activeOwner=previous;if(previous)previous.childrenTime=(previous.childrenTime||0)+performance.now()-started}
}
css(`.component-stopped{padding:12px;border:1px solid #e1d9c9;border-radius:var(--radius,12px);background:var(--card);color:var(--ink);font-size:13px}.component-stopped p{color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:55ch}.component-recovery{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}.component-recovery button{border:1px solid #d8e0d8;border-radius:8px;padding:5px 8px;background:var(--paper)}[data-stale]{opacity:.6;pointer-events:none}[data-slow]{outline:1px dashed #c9ac79}`);
