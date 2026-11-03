// Interim evidence window only. Semantic activation requires separate source/grant review.
export default {css:`
body:has(.smart-search){background:#f6f8f5!important;color:#233c34!important}
.smart-search{max-width:880px;margin:32px auto;padding:20px;font:15px system-ui}
.smart-search h1{font-size:27px}.smart-search p{line-height:1.5}
.smart-search form{display:flex;gap:10px;margin:16px 0}
.smart-search input{flex:1;min-width:80px;font:inherit;padding:12px;border:1px solid #a9bbb3;border-radius:10px;background:white;color:#233c34}
.smart-search button,.smart-search select{font:inherit;padding:9px 13px;border:1px solid #a9bbb3;border-radius:9px;background:white;color:#233c34}
.smart-search :focus-visible{outline:3px solid #47836e}
.search-hit{background:white;border:1px solid #d9e3dc;border-radius:14px;padding:16px;margin:12px 0}
.search-hit p{white-space:pre-wrap;overflow-wrap:anywhere}.search-hit h2{font-size:18px}
.search-coverage{font-size:13px;color:#52665d}
`,mount(api){
  const {P}=api,D=api.draft,Q=api.Q;
  const el=(tag,attrs,...kids)=>P.node(tag,attrs,...kids);
  const kinds=new Set(['note','document','taskboard-task','said','post','reply','widget','button']);
  const idPattern=/^[a-z]{2,4}\d+$/;
  const source=r=>['widget','button'].includes(r.kind)?'Apps':'World';
  const supported=r=>r&&kinds.has(r.kind)&&idPattern.test(r.id||'')&&
    Number.isInteger(r.rev)&&r.rev>=0&&!r.forgotten;
  let closed=false,generation=0,hits=[],opening=false;
  const root=api.part('body','main',{class:'smart-search'});
  const input=el('input',{type:'search','aria-label':'Search Apps and World text',
    maxlength:'1200',value:D.query||'',placeholder:'Words to find'});
  input.value=D.query||'';
  const filter=el('select',{'aria-label':'Sources'},
    ...['All available','Apps','World'].map(v=>el('option',{value:v},v)));
  filter.value=D.source||'All available';
  const submit=el('button',{type:'submit'},'Search');
  const status=el('p',{role:'status','aria-live':'polite'});
  const results=el('section',{'aria-label':'Search results'});
  const form=el('form',{},input,submit);
  const view=async(hit,ticket)=>{
    if(closed||opening||ticket!==generation)return;
    opening=true;
    try{
      // api.rows is the painter's uncached caller-filtered reading. api.read
      // memoizes within a render and cannot establish fresh click admission.
      const fresh=await api.rows('rows any');
      if(closed||ticket!==generation)return;
      const current=Array.isArray(fresh)&&fresh.find(r=>supported(r)&&
        r.id===hit.id&&r.rev===hit.rev&&r.kind===hit.kind);
      if(!current){status.textContent='This evidence changed or is no longer available. Search again.';return;}
      await api.fire('evidence',{id:current.id,saw:{[current.id]:current.rev}});
    }catch(e){if(!closed)status.textContent=String(e.message||e);}
    finally{opening=false;}
  };
  const draw=()=>{
    results.replaceChildren();
    const ticket=generation;
    const visible=hits.filter(r=>filter.value==='All available'||source(r)===filter.value);
    for(const hit of visible){
      const name=String(hit.name||hit.title||'Untitled evidence');
      const title=el('button',{type:'button',on:{click:()=>view(hit,ticket)}},name);
      results.append(el('article',{class:'search-hit'},el('h2',{},title),
        el('small',{},source(hit)+' | '+String(hit.match||'word match')),
        el('p',{},String(hit.snippet||'Open the source to read its text.')),
        el('button',{type:'button',on:{click:()=>view(hit,ticket)}},'View evidence')));
    }
    if(!visible.length)results.append(el('p',{},'No supported evidence in this result page. Other matches may exist beyond the retrieval limit.'));
  };
  const search=async()=>{
    const query=input.value.trim();D.query=input.value;
    const ticket=++generation;hits=[];results.replaceChildren();
    if(!query){status.textContent='Enter words to search.';return;}
    if(query.length>1200){status.textContent='Use at most 1200 characters.';return;}
    submit.disabled=true;status.textContent='Matching words in available text...';
    try{
      // Quoted data only. Query submission never fires a gesture.
      const rows=await api.rows('search '+Q(query)+' limit=50');
      if(closed||ticket!==generation||query!==input.value.trim())return;
      hits=(Array.isArray(rows)?rows:[]).filter(supported).slice(0,50);
      status.textContent='Word matches only. Up to 50 kernel results, then supported-kind and source filters; coverage is incomplete.';
      draw();
    }catch(e){if(!closed&&ticket===generation)status.textContent=String(e.message||e);}
    finally{if(!closed&&ticket===generation)submit.disabled=false;}
  };
  form.onsubmit=e=>{e.preventDefault();return search();};
  input.oninput=()=>{D.query=input.value;++generation;hits=[];results.replaceChildren();submit.disabled=false;};
  filter.onchange=()=>{D.source=filter.value;draw();};
  root.append(el('h1',{},'Apps and World text search'),
    el('p',{},'Matches words in available text; does not verify requested capabilities. Files, Email and Web are not connected.'),
    form,filter,el('p',{class:'search-coverage'},'Apps: visible Agora entries. World: supported visible text kinds. Results are limited before display filters; this is not complete search.'),
    status,results);
  api.cleanup(()=>{closed=true;++generation;});
  return root;
}};
