// BEGIN SHARED ACTION FEEDBACK
// Shared component-local feedback; bundled into each importing component.
// No widget primitive, world write, persisted content or unqualified undo.
function actionFeedback(api) {
  const host=globalThis[Symbol.for('agora.action-feedback.v2')]??=
    {entries:new Map(),scopes:new Map(),listeners:new Set(),serial:0};
  const scope=(view,keys)=>JSON.stringify(Object.fromEntries(
    (keys?keys.split(/\s+/):Object.keys(view)).filter(k=>k&&!/Notice$/.test(k)).sort().map(k=>[k,view[k]??''])));
  const emit=()=>{for(const fn of [...host.listeners])fn()};
  const current=entry=>entry&&entry.scope===scope(api.view(),entry.keys);
  const clear=()=>{host.entries.clear();emit()};
  const feedback={
    observe(key,keys,draw){
      host.scopes.set(key,keys);
      const old=host.entries.get(key);
      if(old&&!current(old))host.entries.delete(key);
      // Register the authored scope even before the first action.
      if(!host.entries.has(key))host.entries.set(key,{keys,scope:scope(api.view(),keys)});
      const listener=()=>draw(feedback.get(key));
      host.listeners.add(listener);api.cleanup(()=>host.listeners.delete(listener));listener();
    },
    get(key='actionNotice'){
      const entry=host.entries.get(key);
      if(!current(entry)){host.entries.delete(key);return null}
      return entry?.notice||null;
    },
    begin(text,key='actionNotice'){
      const keys=host.scopes.get(key),token={id:++host.serial,key};
      host.entries.set(key,{keys,scope:scope(api.view(),keys),notice:{text,pending:true,token}});
      emit();return token;
    },
    finish(token,result,text,extra={}){
      const entry=host.entries.get(token.key);
      if(!current(entry)||entry.notice?.token!==token)return false;
      entry.notice={text,record:result?.records?.at(-1)||'',token,...extra};emit();return true;
    },
    fail(token,error){return feedback.finish(token,null,String(error?.message||error))},
    dismiss(key='actionNotice'){const entry=host.entries.get(key);if(entry){delete entry.notice;emit()}},
    clear,
    async run(event,values,text,key='actionNotice'){
      const token=feedback.begin(api.label('pending','Working…'),key);
      try{const result=await api.fire(event,values);feedback.finish(token,result,text);return result}
      catch(e){feedback.fail(token,e);throw e}
    },
    select(values){
      const next={...api.view(),...values};
      for(const entry of host.entries.values()){
        if(entry.scope!==scope(next,entry.keys)){clear();break}
      }
      return api.select(values);
    }
  };
  return feedback;
}
function feedbackAPI(api){
  const feedback=actionFeedback(api);
  const wrapped={};
  for(const key of Object.keys(api))if(key!=='select'&&key!=='feedback')
    Object.defineProperty(wrapped,key,{enumerable:true,get:()=>api[key]});
  return Object.assign(wrapped,{feedback,select:feedback.select});
}

// END SHARED ACTION FEEDBACK
export default {css:`
.work-line{height:58px;display:flex;align-items:center;gap:12px;padding:0 18px;border-bottom:1px solid var(--work-rule,#e5e9e2);min-width:0;font-size:13px}
.work-line button{all:unset;cursor:pointer;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;border-radius:4px}
.work-line button:hover{text-decoration:underline}
.work-line button:focus-visible{outline:2px solid var(--work-accent,#638779);outline-offset:3px}
.work-line .work-title{flex:2;min-width:70px;font-weight:550}
.work-line .work-owner{flex:1;min-width:45px;color:var(--work-muted,#647367)}
.work-status{flex:none;width:125px;font-size:11px;color:var(--work-accent,#0b6e55)}
.work-people{flex:1;min-width:70px;display:flex;flex-direction:column;gap:3px}
.work-people small{color:var(--work-muted,#647367);font-size:10px}
.work-line[data-state=Blocked] .work-status,.work-line[data-state-key=blocked] .work-status{color:var(--work-blocked,#8a4b00)}
.work-blocker{flex:3;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:var(--work-muted,#647367)}
.work-blocker button{max-width:100%;vertical-align:bottom}
.work-inspect{max-width:min(680px,80vw);max-height:65vh;overflow:hidden}
.work-inspect h2{font-size:18px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.work-inspect p{display:-webkit-box;-webkit-line-clamp:5;-webkit-box-orient:vertical;overflow:hidden;overflow-wrap:anywhere}
@media(max-width:650px){.work-line{gap:7px;padding:0 10px;font-size:12px}.work-status{width:85px}.work-blocker{flex:2}}
`,mount(api,s){
  api=feedbackAPI(api);
  const {P}=api;
  const inspect=()=>{
    const content=P.node('section',{class:'work-inspect'},P.node('h2',{},s.title),P.node('p',{},s.state));
    content.append(P.node('p',{},s.lead?'Lead: '+s.lead:s.owner));
    if(s.lead)content.append(P.node('p',{},'Executing: '+(s.executor||'No current execution')));
    if(s.delivery)content.append(P.node('p',{},'Delivery: '+s.delivery));
    if(s.blocker)content.append(P.node('p',{},s.blocker+' · '+s.resolver));
    if(s.next)content.append(P.node('p',{},'Next: '+s.next));
    if(s.acceptance)content.append(P.node('p',{},'Acceptance: '+s.acceptance));
    if(s.detail)content.append(P.node('p',{},s.detail));
    let overlay;
    content.prepend(P.press('Close',()=>overlay.close()));
    overlay=P.overlay('dialog',content,{label:s.title});
    Object.assign(overlay.node.style,{background:P.tokens.card,color:P.tokens.ink,maxWidth:'90vw',overflow:'hidden'});
    api.cleanup(()=>overlay.close());
  };
  const name=(label,cls)=>P.node('button',{type:'button',class:cls,title:label,on:{click:inspect}},label);
  const root=api.part('body','article',{class:'work-line','data-state':s.state,'data-state-key':s.stateKey||''});
  const people=P.node('div',{class:'work-people'},name(s.lead||s.owner||'Unassigned','work-owner'));
  if(s.executor)people.append(name('Executing: '+s.executor,'work-owner'));
  else if(s.lead)people.append(P.node('small',{},'Lead'));
  root.append(P.node('span',{class:'work-status'},s.state),name(s.title,'work-title'),people);
  if(s.blocker){
    const blocker=P.node('span',{class:'work-blocker',title:`${s.blocker} · ${s.resolver}`});
    blocker.append(name(`${s.blocker} · ${s.resolver}`,''));
    root.append(blocker);
  }else if(s.resolver||s.next){
    const next=P.node('span',{class:'work-blocker',title:s.next||s.resolver});
    if(s.resolver)next.append(name(s.resolver,''),P.node('span',{},s.next?' · '+s.next:''));
    else next.append(P.node('span',{},s.next));
    root.append(next);
  }
  if(api.node.gestures.some(g=>g.event==='done')&&!['done','cancelled'].includes(s.stateKey)&&s.state!=='Done'){
    const done=api.part('done','button',{type:'button'},api.label('done','Mark done'));
    done.disabled=!!api.draft.doneBusy;
    done.addEventListener('click',async()=>{
      if(api.draft.doneBusy)return;api.draft.doneBusy=true;done.disabled=true;
      try{await api.feedback.run('done',{},api.label('completed','Marked done.'),'workNotice')}
      catch(e){api.tell(String(e.message||e))}
      finally{api.draft.doneBusy=false;done.disabled=false}
    });root.append(done);
  }
  return root;
}};
