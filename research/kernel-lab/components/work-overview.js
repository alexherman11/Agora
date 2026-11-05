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
// Local to this component module: existing widget runtimes need no upgrade.
function pageBounds(total,size,page=0){
  total=Math.max(0,Math.floor(Number(total)||0));size=Math.max(1,Math.floor(Number(size)||1));
  const pages=Math.max(1,Math.ceil(total/size));
  page=Math.max(0,Math.min(pages-1,Math.floor(Number(page)||0)));
  return {page,pages,start:page*size,end:Math.min(total,(page+1)*size),previous:page>0,next:page<pages-1};
}
export default {css:`
body:has(.work-overview){padding:24px!important;min-width:0!important;overflow:hidden}
.work-overview{height:calc(100dvh - 48px);min-height:0;display:flex;flex-direction:column;gap:20px;color:var(--work-ink,#293d35)}
.work-heading{display:flex;align-items:baseline;gap:14px;flex:none}
.work-heading h1{margin:0;font-size:26px;font-weight:600;letter-spacing:-.03em}
.work-caption{color:var(--work-muted,#647367);font-size:13px}
.work-filters{display:flex;gap:6px;flex-wrap:wrap}
.work-filters button{font:inherit;font-size:12px;border:1px solid var(--work-rule,#dce4da);border-radius:8px;padding:6px 10px;background:var(--work-card,#fffef9);color:inherit;cursor:pointer}
.work-filters button[aria-pressed=true]{border-color:var(--work-accent,#638779);font-weight:600}
.work-rows{flex:1;min-height:0;overflow:hidden;border:1px solid var(--work-rule,#dce4da);border-radius:14px;background:var(--work-card,#fffef9)}
.work-pagination{display:flex;align-items:center;justify-content:space-between;gap:12px;flex:none;font-size:12px}
.work-pagination button{font:inherit;border:1px solid var(--work-rule,#dce4da);border-radius:8px;padding:6px 12px;background:var(--work-card,#fffef9);color:inherit}
.work-pagination button:disabled{opacity:.45}
.work-quiet{padding:24px;color:var(--work-muted,#647367)}
`,mount(api,s){
  api=feedbackAPI(api);
  const {P}=api,t=P.tokens,root=api.part('body','main',{class:'work-overview',style:{
    '--work-ink':t.ink,'--work-muted':t.muted,'--work-card':t.card,'--work-rule':t.muted+'40',
    '--work-accent':t.accent,'--work-blocked':t.orange}});
  const all=api.children.filter(n=>n.name!=='notice').flatMap(n=>n.children||[]);
  const groups={All:()=>true,Running:n=>n.settings.stateKey==='running',
    Queued:n=>n.settings.stateKey==='queued',Blocked:n=>n.settings.stateKey==='blocked',
    Waiting:n=>['review','activation'].includes(n.settings.stateKey),
    Done:n=>['done','cancelled'].includes(n.settings.stateKey)};
  const chosen=Object.hasOwn(groups,api.view().workFilter)?api.view().workFilter:'All';
  const rows=s.board?all.filter(groups[chosen]):all;
  const running=all.filter(groups.Running).length;
  const heading=P.node('header',{class:'work-heading'},P.node('h1',{},s.title||(s.board?'Tasks & work':'Work')),
    P.node('span',{class:'work-caption'},s.board?`${running} running · ${all.length} tasks`:`Active and blocked · ${all.length}`));
  const filters=P.node('nav',{class:'work-filters','aria-label':'Task states'});
  for(const [label,accept]of Object.entries(groups)){
    const button=P.node('button',{type:'button','aria-pressed':String(chosen===label)},`${label} ${all.filter(accept).length}`);
    button.onclick=()=>api.select({workFilter:label,workPage:0}).catch(api.tell);filters.append(button);
  }
  const list=P.node('div',{class:'work-rows','aria-label':s.board?'Tasks and work':'Current work'});
  const footer=P.node('nav',{class:'work-pagination','aria-label':'Work pages'});
  const prev=P.node('button',{type:'button',disabled:true},'Previous'),next=P.node('button',{type:'button',disabled:true},'Next'),count=P.node('span',{'aria-live':'polite'});
  footer.append(prev,count,next);root.append(heading,...api.children.filter(n=>n.name==='notice').map(api.render));if(s.board)root.append(filters);root.append(list,footer);
  let page=Math.max(0,Math.floor(Number(api.view().workPage)||0));
  function draw(){
    const size=Math.max(1,Math.floor((list.getBoundingClientRect().height-2)/58));
    const bounds=pageBounds(rows.length,size,page);page=bounds.page;
    list.replaceChildren(...rows.slice(bounds.start,bounds.end).map(api.render));
    if(!rows.length)list.append(P.node('p',{class:'work-quiet'},'No tasks in this view.'));
    prev.disabled=!bounds.previous;next.disabled=!bounds.next;
    count.textContent=rows.length?`${page*size+1}–${Math.min(rows.length,(page+1)*size)} of ${rows.length}`:'All clear';
  }
  prev.onclick=()=>api.select({workPage:Math.max(0,page-1)}).catch(api.tell);
  next.onclick=()=>api.select({workPage:page+1}).catch(api.tell);
  const resize=new ResizeObserver(api.guard(draw));resize.observe(list);api.cleanup(()=>resize.disconnect());
  api.requestAnimationFrame(draw);return root;
}};
