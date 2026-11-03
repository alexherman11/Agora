export default {css:`
body:has(.smart-search){background:#f6f8f5!important;color:#233c34!important}
.smart-search{max-width:880px;margin:32px auto;padding:20px;font:15px system-ui}
.smart-search h1{font-size:27px;margin:0 0 8px}.smart-search p{line-height:1.5}
.smart-search form,.search-options{display:flex;gap:10px;margin:16px 0}
.smart-search input{flex:1;min-width:80px;font:inherit;border:1px solid #a9bbb3;border-radius:12px;padding:12px;background:white;color:#233c34}
.smart-search button,.smart-search select{font:inherit;padding:9px 13px;border:1px solid #a9bbb3;border-radius:9px;background:white;color:#233c34;cursor:pointer}
.smart-search button:focus-visible,.smart-search input:focus-visible{outline:3px solid #47836e}
.search-coverage{font-size:12px;color:#52665d}.search-hit{background:white;border:1px solid #d9e3dc;border-radius:14px;padding:16px;margin:12px 0}
.search-hit h2{font-size:17px;margin:0 0 6px}.search-hit small{color:#52665d}.search-hit p{white-space:pre-wrap;overflow-wrap:anywhere}
.search-actions{display:flex;gap:10px}.search-status{min-height:24px}
`,mount(api){
  const {P}=api,D=api.draft;
  let closed=false,serial=0;
  const el=(tag,attrs,...kids)=>P.node(tag,attrs,...kids);
  const root=api.part('body','main',{class:'smart-search'});
  const input=el('input',{type:'search',placeholder:'What are you looking for?','aria-label':'Search everything',maxlength:'1200',value:D.query||''});
  input.value=D.query||'';
  const filter=el('select',{'aria-label':'Sources'},...['All available','Apps','World'].map(v=>el('option',{value:v},v)));
  filter.value=D.source||'All available';
  const status=el('p',{class:'search-status',role:'status','aria-live':'polite'});
  const coverage=el('p',{class:'search-coverage'},'Apps · known Agora entries and pins | World · visible text | Files, Email, Web · not connected');
  const results=el('section',{'aria-label':'Search results'});
  const submit=el('button',{type:'submit'},'Search');
  const semantic=el('button',{type:'button'},'Understand locally');
  const form=el('form',{},input,submit);
  const Q=api.Q;
  const read=async(mode,q,extra='')=>{
    const out=await api.read('model.search q='+Q(q)+' mode='+mode+' request='+Date.now()+'-'+(++serial)+extra);
    // api.read returns rows directly (the painter adapter), not a door envelope.
    return Array.isArray(out)?out:(out.rows||[]);
  };
  const activate=async(hit,app)=>{
    try{
      const checked=await read('check',D.query,' id='+Q(hit.id)+' rev='+Q(String(hit.rev)));
      const current=checked[0];
      if(!current){status.textContent='This result changed or is no longer available. Search again.';return;}
      if(app){
        if(!/^[a-z][a-z0-9_-]{0,79}$/.test(current.app||''))return;
        await api.fire('app',{app:current.app});
      }else{
        if(!/^[a-z]{2,4}\d+$/.test(current.id||''))return;
        await api.fire('evidence',{id:current.id});
      }
    }catch(e){status.textContent=String(e.message||e);}
  };
  const draw=(data)=>{
    status.textContent=data.state+' · '+(data.constraints?.join(', ')||'No hard constraints resolved');
    coverage.textContent=(data.coverage||[]).map(c=>c.source+' · '+c.state).join(' | ');
    results.replaceChildren();
    const hits=(data.hits||[]).filter(r=>filter.value==='All available'||r.source===filter.value);
    for(const hit of hits){
      const title=el('button',{type:'button',on:{click:()=>activate(hit,false)}},hit.title);
      const actions=el('div',{class:'search-actions'},
        el('button',{type:'button',on:{click:()=>activate(hit,false)}},'View evidence'));
      // Open is available only for a host-validated current Agora widget.
      if(hit.app)actions.append(el('button',{type:'button',on:{click:()=>activate(hit,true)}},'Open app'));
      results.append(el('article',{class:'search-hit'},el('h2',{},title),
        el('small',{},hit.source+' · '+hit.match),el('p',{},hit.evidence||hit.text),actions));
    }
    if(!hits.length)results.append(el('p',{},'No matching evidence in the available sources.'));
    if(data.semantic_scope)results.append(el('p',{class:'search-coverage'},data.semantic_scope));
  };
  const search=async(mode)=>{
    const query=input.value.trim();D.query=input.value;D.source=filter.value;
    if(!query)return;
    const ticket=++serial;results.replaceChildren();
    status.textContent=mode==='semantic'?'Checking with the local model…':'Searching visible text…';
    submit.disabled=semantic.disabled=true;
    try{
      const rows=await read(mode,query);
      if(!closed&&ticket<=serial&&input.value.trim()===query)draw(rows[0]||{state:'Search unavailable',hits:[]});
    }catch(e){if(!closed)status.textContent=String(e.message||e);}
    finally{if(!closed)submit.disabled=semantic.disabled=false;}
  };
  form.onsubmit=e=>{e.preventDefault();search('lexical');};
  semantic.onclick=()=>search('semantic');
  input.oninput=()=>{D.query=input.value;};
  filter.onchange=()=>{D.source=filter.value;search('lexical');};
  root.append(el('h1',{},'Search everything'),el('p',{},'Find tools and discussions. Searches stay on this computer.'),
    form,el('div',{class:'search-options'},filter,semantic),coverage,status,results);
  api.cleanup(()=>{closed=true;});
  return root;
}};
