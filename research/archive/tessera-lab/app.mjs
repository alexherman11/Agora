import {Engine,canonical} from './engine.mjs';
let engine, trial, signature='', drafts = {}, draftVersions = {}, inactive = new Set();
const $ = id => document.getElementById(id), el = tag => document.createElement(tag);
const allowedStyles = new Set(['background','backgroundColor','color','borderRadius','padding','margin','gap','fontSize','fontWeight','border','boxShadow','opacity','width','maxWidth','minWidth','display','gridTemplateColumns','alignItems','justifyContent','flexWrap']);
const names = {'01-workspace':'01 · Shared research workspace','02-expedition':'02 · Expedition dispatch'};
function notify(text,bad=false) { $('notice').textContent=text; $('notice').className=bad?'error':'success'; }
function scopeLocal(scope) { return {...(drafts['root']??{}),...(drafts[scope]??{})}; }
function defaultsFor(ctx,scope) {
  const local=scopeLocal(scope);
  for(const v of Object.values(engine.program.view)) if(v.bind && !(v.bind in local)) {
    try {
      const value=v.value===undefined ? undefined : engine.eval(v.value,{...ctx,local});
      local[v.bind]=value ?? (v.widget==='select' ? engine.eval(v.options??['lit',[]],{...ctx,local})[0]?.id??'' : v.inputType==='number'?0:'');
    } catch {local[v.bind]='';}
  }
  return local;
}
function render() {
  if (!engine) return;
  const active = document.activeElement, focusKey = active?.dataset.key, start = active?.selectionStart, end = active?.selectionEnd;
  const app = $('app'); app.replaceChildren();
  function node(v,ctx={row:null},scope='root',ancestors=[]) {
    if (ancestors.includes(v.id)) return null;
    const local = defaultsFor(ctx,scope), context = {...ctx,local};
    const ev = x => engine.eval(x,context);
    try {
      if (v.visible !== undefined && !ev(v.visible)) return null;
      const tag = {input:'input',textarea:'textarea',select:'select',button:'button',link:'a',text:'p',badge:'span'}[v.widget] ?? 'div';
      const n = el(tag); n.className=`widget ${v.widget}`; n.dataset.view=v.id; n.dataset.scope=scope;
      n.title = `Contributed by ${v.authors.join(', ')}`;
      const style = engine.styleFor(v); for (const [k,value] of Object.entries(style.values)) if(allowedStyles.has(k)) n.style[k]=value;
      if (v.title) { const h=el('h2');h.textContent=v.title;n.append(h); }
      if (['input','textarea','select'].includes(v.widget)) {
        if(v.widget==='select') for(const record of ev(v.options??['lit',[]])) {const o=el('option');o.value=record.id;o.textContent=record[v.optionLabel??'title']??record.id;n.append(o);}
        if(v.widget==='input' && v.inputType) n.type=v.inputType;
        const value = local[v.bind];
        n.value = value ?? ''; n.placeholder=v.placeholder ?? ''; n.setAttribute('aria-label',v.placeholder ?? v.bind);
        n.dataset.key=`${scope}:${v.id}`;
        // Untouched fallbacks are visible to sibling buttons but do not become stale drafts.
        context.local[v.bind] = n.value;
        n.addEventListener('input',()=>{(drafts[scope]??={})[v.bind]=v.inputType==='number'?Number(n.value):n.value; (draftVersions[scope]??={})[v.bind] ??= structuredClone(engine.versions); render();});
      } else if (v.widget==='button') {
        n.textContent=ev(v.text) ?? v.id;
        n.disabled=!!(v.disabled !== undefined && ev(v.disabled)) || !engine.program.action[v.action];
        n.onclick=async()=>{
          try {
            const locals = {...defaultsFor(ctx,scope),newId:crypto.randomUUID()};
            for (const input of app.querySelectorAll('input[data-scope],textarea[data-scope],select[data-scope]')) if(input.dataset.scope===scope || input.dataset.scope==='root') {
              const def=engine.program.view[input.dataset.view]; if(def?.bind && !(def.bind in locals)) locals[def.bind]=input.value;
            }
            const args=engine.eval(v.args??{},{...ctx,local:locals});
            const expected={...engine.versions};
            // Drafts carry their original cell versions, so live refresh cannot silently rebase edits.
            for (const versions of Object.values(draftVersions[scope]??{})) for(const [key,value] of Object.entries({...engine.versions,...versions})) expected[key]=versions[key]??0;
            const response=await fetch(`/api/action?trial=${trial}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:v.action,args,expected})});
            const data=await response.json();if(!data.result) throw Error(data.error);
            if(data.result.ok) { delete drafts[scope]; delete draftVersions[scope];notify(`${v.action} · committed with ${data.result.handlers.length} contributor${data.result.handlers.length===1?'':'s'}`); }
            else notify(`${data.result.conflict.code}: ${JSON.stringify(data.result.conflict.detail)}`,true);
            engine=new Engine(engine.modules,data);render();
          } catch(error){notify(error.message,true);}
        };
      } else if(v.widget==='link') {
        n.textContent=ev(v.text)??'';const href=String(ev(v.href)??'');
        if(/^https?:\/\//i.test(href)) {n.href=href;n.target='_blank';n.rel='noopener noreferrer';}
      } else if(v.text!==undefined) n.append(document.createTextNode(String(ev(v.text)??'')));
      const next=[...ancestors,v.id];
      if(v.widget==='list') {
        const rows=engine.eval(['query',v.query],context);
        if(!rows.length){const empty=el('p');empty.className='empty';empty.textContent='Nothing here yet.';n.append(empty);}
        for(const row of rows) for(const child of engine.children(v.id)) {const c=node(child,{...ctx,parent:ctx.row,row},`${scope}/${v.query}/${row.id}`,next);if(c)n.append(c);}
      } else for(const child of engine.children(v.id)) {const c=node(child,ctx,scope,next);if(c)n.append(c);}
      return n;
    }catch(error){const n=el('div');n.className='error';n.textContent=`${v.id}: ${error.message}`;return n;}
  }
  for(const root of Object.values(engine.program.view).filter(v=>!v.parent)){const n=node(root);if(n)app.append(n);}
  $('stats').textContent=`${engine.modules.length-1} builders · ${Object.keys(engine.program.view).length} views · ${Object.keys(engine.program.action).length} actions`;
  const issues=[...engine.diagnostics,...engine.conflicts];
  $('inspection').replaceChildren();const pre=el('pre');pre.textContent=JSON.stringify({modules:engine.modules.map(m=>({id:m.id,claims:m.claims.length})),issues,serial:engine.serial,provenance:engine.provenance},null,2);$('inspection').append(pre);
  if(focusKey){const target=[...app.querySelectorAll('[data-key]')].find(n=>n.dataset.key===focusKey);if(target){target.focus();if(start!==null&&start!==undefined&&target.type!=='number')target.setSelectionRange?.(start,end);}}
}
async function refresh(force=false){
  try{
    const data=await(await fetch(`/api/state?trial=${trial}`)).json();if(data.error)throw Error(data.error);
    const next=canonical(data);if(force||next!==signature){signature=next;engine=new Engine(data.modules.filter(m=>!inactive.has(m.id)),data);render();
      $('authors').replaceChildren();for(const m of data.modules.filter(m=>m.id!=='base')){const b=el('span');b.className='author';b.textContent=`● ${m.id}`;$('authors').append(b);}
    }
  }catch(error){notify(error.message,true);}
}
$('inspect').onclick=()=>{$('inspector').hidden=!$('inspector').hidden;};
const trials=await(await fetch('/api/trials')).json();for(const t of trials){const option=el('option');option.value=t;option.textContent=names[t]??t;$('trial').append(option);}
trial=new URL(location.href).searchParams.get('trial')??trials[0];$('trial').value=trial;
$('trial').onchange=()=>{trial=$('trial').value;drafts={};draftVersions={};inactive.clear();history.replaceState({},'',`?trial=${trial}`);refresh(true);};
await refresh(true);setInterval(()=>refresh(),1200);
