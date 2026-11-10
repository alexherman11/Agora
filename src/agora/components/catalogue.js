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
// Catalogue pieces compose core primitives. They have no private fact store.
export default {css:`
[data-component=input][data-part=body]{display:grid;gap:var(--input-gap,8px);min-width:0}
[data-component=input] input{width:100%;min-width:0;box-sizing:border-box}
[data-component=input] label{display:grid;gap:var(--input-gap,8px)}
[data-component=input][data-part=status]:empty{display:none}
[data-component=badge][data-part=body]{padding:var(--badge-padding,4px 8px);border-radius:var(--badge-radius,8px);background:var(--badge-background,var(--card,#fff));color:var(--badge-color,var(--ink,#303d37))}
`,mount(api,s){
  api=feedbackAPI(api);
  const {P}=api,kind=api.node.component,children=()=>api.children.map(api.render);
  const root=api.part('body','section',{'aria-label':s.label||kind});
  const label=api.display('label')||kind;
  const fire=event=>values=>api.fire(event,values).catch(api.tell);
  if(kind==='button'){
    const button=api.part('control','button',{type:'button'},label);
    api.draft.updateButton=()=>{button.disabled=!!api.draft.busy};api.draft.updateButton();
    button.addEventListener('click',async()=>{
      if(api.draft.busy)return;api.draft.busy=true;button.disabled=true;
      try{
        if(s.selectKey)await api.select(Object.fromEntries(s.selectKey.split(/\s+/).filter(Boolean).map(key=>[key,s.value])));
        else{
          if(s.completionText)await api.feedback.run('press',{},s.completionText,s.noticeKey||'actionNotice');
          else await api.fire('press',{});
        }
      }catch(e){api.tell(String(e.message||e))}
      finally{api.draft.busy=false;api.draft.updateButton?.()}
    });return button;
  }
  if(['input','editor','choice','switch'].includes(kind)){
    const type=kind==='editor'?'multiline':kind==='choice'?'choice':kind==='switch'?'toggle':'text';
    const explicit=kind==='input'&&s.commit==='submit';
    const n=api.part('control',type==='multiline'?'textarea':type==='choice'?'select':'input',{'aria-label':label,value:explicit?(api.draft.value??s.value??''):s.value||'',placeholder:s.hint||'',...(type==='toggle'?{type:'checkbox'}:{})});
    if(explicit){
      const status=api.part('status','p',{role:'status','aria-live':'polite'},api.draft.outcome||'');
      const submit=api.part('submit','button',{type:'button'},s.submitLabel||api.label('submit','Submit'));
      const ready=()=>{submit.disabled=!!api.draft.busy||!n.value.trim()};
      api.draft.updateSubmit=()=>{n.value=api.draft.busy?'':api.draft.value??n.value;n.disabled=!!api.draft.busy;status.textContent=api.draft.outcome||'';ready()};
      n.addEventListener('input',()=>{api.draft.value=n.value;ready()});
      const send=async()=>{
        if(api.draft.busy||!n.value.trim())return;
        const value=n.value;api.draft.value=value;api.draft.busy=true;api.draft.outcome=api.label('sending','Sending…');api.draft.updateSubmit();
        try{await api.fire('submit',{value});if(api.draft.value===value){api.draft.value='';n.value=''}api.draft.outcome=status.textContent=api.label('sent','Sent.')}
        catch(e){api.draft.outcome=status.textContent=String(e.message||e)}
        finally{api.draft.busy=false;api.draft.updateSubmit()}
      };
      n.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.isComposing){e.preventDefault();send()}});
      submit.addEventListener('click',send);api.draft.updateSubmit();
      root.append(P.node('label',{},label,n),submit,status);return root;
    }
    if(type==='choice')for(const value of String(s.options).split('|'))n.append(P.node('option',{value},value));
    if(type==='toggle')n.checked=!!s.checked;
    const commit=()=>s.selectKey?api.select({[s.selectKey]:n.value}).catch(api.tell):fire('change')({value:type==='toggle'?(n.checked?'yes':'no'):n.value});
    n.addEventListener('change',commit);root.append(P.node('label',{},label),n);return root;
  }
  if(['text-block','markdown','code','icon','image','avatar','player'].includes(kind)){
    const type=({'text-block':'text',player:'media'})[kind]||kind;
    root.append(P.content(type,api.display('value')||label,{'aria-label':label}));return root;
  }
  if(['badge','progress','empty-state'].includes(kind)){
    if(kind==='progress')root.append(P.node('progress',{max:s.max,value:s.value,'aria-label':label}),P.content('text',label));
    else root.append(P.content('text',label));return root;
  }
  if(['dialog','popover','tooltip','toast','drawer'].includes(kind)){
    root.append(P.press(label,()=>P.overlay(kind,P.layout('stack',{},P.content('text',s.text||label),...children()),{label,anchor:{x:80,y:80}})));
    return root;
  }
  if(kind==='palette'){
    const input=P.input('text',{'aria-label':label,placeholder:'Find a command…'}),list=P.layout('stack',{},...children());
    input.addEventListener('input',()=>{for(const n of list.children)n.hidden=!n.textContent.toLowerCase().includes(input.value.toLowerCase())});
    return P.navigation(P.layout('stack',{},input,list));
  }
  if(['chart','map','pixel-surface'].includes(kind)){
    const data=s.data||[];
    const surface=P.canvas({width:s.width,height:s.height,label,pixels:kind==='pixel-surface'?s.pixels:null,series:kind==='chart'?data:null});
    if(kind==='map'){
      const ctx=surface.getContext('2d');ctx.fillStyle=P.tokens.accent;
      for(const point of data){ctx.beginPath();ctx.arc(+point.x||0,+point.y||0,5,0,Math.PI*2);ctx.fill()}
    }
    surface.addEventListener('click',e=>{if(api.node.gestures.some(g=>g.event==='press')){const r=surface.getBoundingClientRect();fire('press')({x:(e.clientX-r.left)*surface.width/r.width,y:(e.clientY-r.top)*surface.height/r.height})}});
    root.append(surface,P.content('text',s.caption||''));return root;
  }
  if(kind==='table'){
    const table=P.node('table',{'aria-label':label}),cols=String(s.columns).split('|');
    const body=P.node('tbody');let data=[...(s.data||[])],direction=1;
    const draw=()=>{body.replaceChildren();for(const row of data)body.append(P.node('tr',{},...cols.map(c=>P.node('td',{},row[c]??''))))};
    table.append(P.node('thead',{},P.node('tr',{},...cols.map(x=>P.node('th',{scope:'col'},s.sortable?P.press(x,()=>{data.sort((a,b)=>String(a[x]??'').localeCompare(String(b[x]??''),undefined,{numeric:true})*direction);direction*=-1;draw()}):x)))));
    draw();
    table.append(body);root.append(table,...children());return root;
  }
  if(kind==='calendar'){
    const [year,month]=s.month.split('-').map(Number),start=new Date(Date.UTC(year,month-1,1)),days=new Date(Date.UTC(year,month,0)).getUTCDate();
    const grid=P.layout('grid',{role:'grid','aria-label':label});grid.style.gridTemplateColumns='repeat(7,minmax(0,1fr))';
    for(const name of ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'])grid.append(P.content('text',name));
    for(let i=0;i<start.getUTCDay();i++)grid.append(P.content('text',''));
    for(let day=1;day<=days;day++)grid.append(P.press(String(day),()=>fire('select')({value:`${s.month}-${String(day).padStart(2,'0')}`})));
    root.append(P.content('text',s.month),grid,...children());return P.navigation(root);
  }
  if(kind==='tree'){
    root.setAttribute('role','tree');for(const child of children()){const d=P.node('details',{},P.node('summary',{},child.getAttribute('aria-label')||child.dataset.component||'Item'),child);root.append(d)}
    return P.navigation(root);
  }
  if(kind==='virtual-list')return P.virtual(api.children.map(n=>()=>api.render(n)),{height:s.height,rowHeight:s.row_height});
  const mode=kind==='gallery'?'grid':kind==='timeline'?'row':kind==='toolbar'||kind==='tabs'?'row':kind==='split-pane'?'split':'stack';
  root.append(P.layout(mode,{},...children()));return P.navigation(root);
}};
