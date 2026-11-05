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
export default {mount(api,s){
  api=feedbackAPI(api);
  const f=api.facts,L=api.label,full=Number(f.seats_left||0)===0,root=api.part('body','section',{class:'nb-slots'});
  if(!f.id){root.append(api.P.node('p',{class:'nb-meta'},L('empty','Available places will appear here.')));return root}
  const description=api.P.node('div',{}),name=s.label||(f.event?(f.title||f.name):'');
  if(name)description.append(api.part('label','strong',{},L(name,name)),api.P.node('br',{}));
  const total=Number(f.seats||1),left=Number(f.seats_left||0);
  description.append(api.part('meter','meter',{min:0,max:total,value:total-left,'aria-label':L('filledplaces','Filled places')}),api.part('count','span',{},full?(total===1?L('onefilled','Place filled'):L('all','All')+' '+total+' '+L('filled','places filled')):left+' '+L('of','of')+' '+total+' '+L(total===1?'one-left':'left',total===1?'place left':'places left')));root.append(description);
  const closed=f.closes&&new Date(f.closes)<=new Date();
  const viewer=api.node.viewer?.id,claimed=!!(viewer&&f['claim:'+viewer]);
  const ownOffer=f.post_kind==='offer'&&viewer&&(f.for||f.made_by)===viewer;
  if(ownOffer){
    const reason=L('ownoffer','This is your offer. Other neighbours can take a place.');
    root.append(api.part('claim','button',{type:'button',class:'nb-primary',disabled:true,title:reason},L('claim','Take a place')),api.P.node('p',{role:'status'},reason));
  }else if(claimed)root.append(api.P.node('p',{role:'status'},L('reserved','Your place is reserved.')));
  else if(!full&&!closed){
    const b=api.part('claim','button',{type:'button',class:'nb-primary'},L('claim','Take a place'));
    b.disabled=!!api.draft.busy;b.addEventListener('click',async()=>{
      if(api.draft.busy)return;api.draft.busy=true;b.disabled=true;
      try{
        await api.feedback.run('claim',{},L('reserved','Your place is reserved.'));
      }catch(e){api.tell(String(e.message||e))}
      finally{api.draft.busy=false;b.disabled=false}
    });root.append(b);
  }return root;
}};
