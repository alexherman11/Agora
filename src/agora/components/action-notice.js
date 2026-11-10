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
// Shared receipt outcome. Component-local feedback survives row remounts, never navigation.
// Only an explicit authored undo gesture can reverse the exact returned receipt.
export default {css:`
[data-component=action-notice][data-part=body]{position:sticky;top:var(--notice-top,0px);z-index:4;display:flex;align-items:center;flex-wrap:wrap;gap:var(--notice-gap,12px);padding:var(--notice-padding,12px);border:1px solid var(--notice-border,#cbdcd0);border-radius:var(--notice-radius,8px);background:var(--notice-background,var(--card,#fff));color:var(--notice-color,var(--ink,#303d37))}
[data-component=action-notice][hidden]{display:none}
[data-component=action-notice][data-part=message]{flex:1;min-width:0}
[data-component=action-notice] button{font:inherit;color:inherit;cursor:pointer;min-height:36px}
`,mount(api,s){
  const {P}=api,key=s.stateKey||'actionNotice',L=api.label,feedback=actionFeedback(api);
  const root=api.part('body','aside',{role:'status','aria-live':'polite'});
  const draw=notice=>{
  root.replaceChildren();root.hidden=!notice;
  if(!notice)return;
  const message=api.part('message','span',{},String(notice.text||''));
  root.append(message);
  const record=String(notice.record||'');
  const restore=notice.restore&&typeof notice.restore==='object'&&!Array.isArray(notice.restore)?notice.restore:null;
  if(!notice.pending&&(restore||(/^r\d+$/.test(record)&&api.node.gestures.some(g=>g.event==='undo')))){
    const undo=api.part('undo','button',{type:'button'},L('undo','Undo'));
    undo.addEventListener('click',async()=>{
      if(api.draft.busy||feedback.get(key)!==notice)return;api.draft.busy=true;undo.disabled=true;
      try{
        if(restore)await api.select(restore);
        else await api.fire('undo',{value:record});
        // A newer action can arrive while Undo is in flight. Do not erase its recovery.
        feedback.finish(notice.token,null,L('undone','Undone.'));
      }catch(e){message.textContent=String(e.message||e)}
      finally{api.draft.busy=false;undo.disabled=false}
    });
    root.append(undo);
  }
  root.append(api.part('dismiss','button',{type:'button',on:{click:()=>feedback.dismiss(key)}},L('dismiss','Dismiss')));
  };
  feedback.observe(key,s.scopeKeys,draw);
  return root;
}};
