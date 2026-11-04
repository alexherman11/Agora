// EDITING THE PAINTER (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
// The painter's vocabulary (formats, handles, scopes, parts) is shared by every app. Add to it only what any lens could
// use, documented where lens authors read it (ARRANGEMENT.md); never a handle, format or branch for one app. If one app
// needs something, the general form of it is the change.
//
// Core drawing vocabulary. All first-party components use these primitives.
// Momentary DOM state is local; lasting changes go through a gesture/door.
const P = (()=>{
  const tokens={paper:'#FAF9F6',card:'#FFFFFF',ink:'#35433D',muted:'#929B99',accent:'#638779',
    red:'#CF514A',orange:'#C58332',blue:'#507EBC',grey:'#9BA3AC',rose:'#FBE9E8',peach:'#FFF0DC',
    sage:'#EAF3E9',sky:'#E8F1FA',lilac:'#F0EBF8',small:'8px',medium:'12px',large:'16px',soft:'12px',round:'50%',
    ...theme};
  const node=(tag,attrs={},...children)=>el(tag,attrs,...children);
  // Data-only display formatters; arrangement/personal format handles choose these.
  function formatValue(value,format='text',now=new Date()){
    if(format==='initials')return String(value).split(/\s+/u).map(w=>w.match(/\p{L}/u)?.[0]||'').filter(Boolean).slice(0,2).join('').toUpperCase();
    if(format==='text')return String(value??'');
    if(!value)return '';
    if(format==='count')return Number(value).toLocaleString(undefined,{maximumFractionDigits:0});
    const d=new Date(value);if(!Number.isFinite(+d))return '';
    const day=new Date(now.getFullYear(),now.getMonth(),now.getDate()),other=new Date(d.getFullYear(),d.getMonth(),d.getDate()),days=Math.round((day-other)/86400000),seconds=(now-d)/1000;
    if(format==='relative-date')return days===0?'Today':days===-1?'Tomorrow':days===1?'Yesterday':days<0?`In ${-days} days`:`${days} days ago`;
    if(format==='short-relative')return seconds>=0&&seconds<60?'now':seconds>=0&&seconds<3600?Math.floor(seconds/60)+'m':days===0&&seconds>=0?Math.floor(seconds/3600)+'h':days>=0&&days<7?d.toLocaleDateString(undefined,{weekday:'short'}):d.toLocaleDateString(undefined,{month:'short',day:'numeric',...(d.getFullYear()!==now.getFullYear()?{year:'numeric'}:{})});
    if(format==='calendar-date')return d.toLocaleDateString(undefined,{day:'numeric',month:'short',...(d.getFullYear()!==now.getFullYear()?{year:'numeric'}:{})});
    if(format==='month')return d.toLocaleDateString(undefined,{month:'short'});
    if(format==='day')return String(d.getDate());
    if(format==='weekday')return d.toLocaleDateString(undefined,{weekday:'short'});
    if(format==='time')return d.toLocaleTimeString('en-US',{hour:'numeric',minute:'2-digit',hour12:true}).toLowerCase();
    return String(value);
  }
  // Deliberately bounded English smart entry. No model, network or Date.parse guesses.
  function parseDateEntry(value,now=new Date()){
    const text=String(value).trim(),iso=/^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{1,2}):(\d{2}))?$/.exec(text);
    const build=(y,m,d,h=0,min=0)=>{const out=new Date(y,m-1,d,h,min);return out.getFullYear()===y&&out.getMonth()===m-1&&out.getDate()===d&&h<24&&min<60?out:null};
    let date;
    if(iso)date=build(...iso.slice(1).map(x=>Number(x||0)).map((x,i)=>i<3?x:x));
    else{
      const match=/^(today|tomorrow|sun(?:day)?|mon(?:day)?|tue(?:sday)?|wed(?:nesday)?|thu(?:rsday)?|fri(?:day)?|sat(?:urday)?)\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$/i.exec(text);
      if(!match)return {ok:false,message:'Try Thu 6pm, tomorrow 9:30am, or 2026-11-04 18:00.'};
      let [,word,hour,minute,period]=match;word=word.toLowerCase();hour=Number(hour);minute=Number(minute||0);
      if(period&&(hour<1||hour>12)||hour>23||minute>59)return {ok:false,message:'Check the time.'};
      if(period)hour=hour%12+(period.toLowerCase()==='pm'?12:0);
      date=new Date(now.getFullYear(),now.getMonth(),now.getDate(),hour,minute);
      let delta=word==='today'?0:word==='tomorrow'?1:('sun mon tue wed thu fri sat'.split(' ').indexOf(word.slice(0,3))-now.getDay()+7)%7;
      if(!['today','tomorrow'].includes(word)&&delta===0&&date<=now)delta=7;
      date.setDate(date.getDate()+delta);
    }
    if(!date||!Number.isFinite(+date))return {ok:false,message:'Check the date and time.'};
    return {ok:true,iso:date.toISOString(),local:`${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}T${String(date.getHours()).padStart(2,'0')}:${String(date.getMinutes()).padStart(2,'0')}`,label:date.toLocaleDateString(undefined,{weekday:'long',month:'short',day:'numeric',year:'numeric'})+' at '+formatValue(date,'time')};
  }
  function selectionAction(source,draft,sourceKey,activate,{label='Quote selection'}={}){
    const selected= P.selected(source,draft,sourceKey),button=node('button',{type:'button',class:'selection-action',hidden:''},label);
    const commit=()=>{const value=selected(),result=activate(value);if(value){getSelection()?.removeAllRanges();button.hidden=true}return result};
    button.addEventListener('pointerdown',e=>{selected();e.preventDefault()});button.addEventListener('click',commit);
    const update=()=>{const selection=getSelection(),inside=selection&&!selection.isCollapsed&&source.contains(selection.anchorNode)&&source.contains(selection.focusNode);button.hidden=!inside;if(inside){const r=selection.getRangeAt(0).getBoundingClientRect();Object.assign(button.style,{position:'fixed',left:Math.max(8,Math.min(r.left,innerWidth-160))+'px',top:Math.max(8,r.top-44)+'px',zIndex:90})}};
    document.addEventListener('selectionchange',update);document.addEventListener('scroll',update,true);source.after(button);
    return {button,selected,quote:commit,dispose:()=>{document.removeEventListener('selectionchange',update);document.removeEventListener('scroll',update,true)}};
  }
  const layout=(mode,attrs={},...children)=>{
    const n=node('div',attrs,...children);n.dataset.layout=mode;
    Object.assign(n.style,({stack:{display:'flex',flexDirection:'column'},row:{display:'flex',alignItems:'center'},
      grid:{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(min(220px,100%),1fr))'},wrap:{display:'flex',flexWrap:'wrap'},
      split:{display:'grid',gridTemplateColumns:'minmax(0,1fr) minmax(0,1fr)',resize:'horizontal',overflow:'auto'},
      layers:{position:'relative'},scroll:{overflow:'auto',minHeight:0},absolute:{position:'absolute'}})[mode]||{});
    if(mode==='split'&&children.flat().length>=2){
      let ratio=50;const divider=node('div',{role:'separator',tabindex:0,'aria-orientation':'vertical','aria-label':'Resize panes','aria-valuemin':10,'aria-valuemax':90,'aria-valuenow':ratio,style:{cursor:'col-resize',background:tokens.muted,opacity:'.3',minWidth:'6px'}});
      const set=value=>{ratio=Math.max(10,Math.min(90,value));n.style.gridTemplateColumns=`minmax(0,${ratio}fr) 6px minmax(0,${100-ratio}fr)`;divider.setAttribute('aria-valuenow',Math.round(ratio))};
      n.insertBefore(divider,n.children[1]);set(50);
      divider.addEventListener('keydown',e=>{if(['ArrowLeft','ArrowRight'].includes(e.key)){e.preventDefault();set(ratio+(e.key==='ArrowLeft'?-5:5))}});
      divider.addEventListener('pointerdown',e=>{divider.setPointerCapture(e.pointerId);const move=ev=>{const r=n.getBoundingClientRect();set((ev.clientX-r.left)/r.width*100)};const end=()=>{divider.removeEventListener('pointermove',move);divider.removeEventListener('pointerup',end);divider.removeEventListener('pointercancel',end)};divider.addEventListener('pointermove',move);divider.addEventListener('pointerup',end);divider.addEventListener('pointercancel',end)});
    }
    return n;
  };
  function markdown(value){
    const n=node('div',{class:'rich-text'});
    for(const line of String(value||'').split('\n')){
      const check=/^- \[([ x])\] (.*)/.exec(line), heading=/^(#{1,6}) (.*)/.exec(line);
      const p=node(heading?'h'+heading[1].length:'p');
      if(check)p.append(node('input',{type:'checkbox','aria-label':check[2],...(check[1]==='x'?{checked:''}:{}) ,disabled:''}));
      const text=check?check[2]:heading?heading[2]:line;
      // No authored HTML, URLs, script, or raw innerHTML.
      for(const piece of text.split(/(\*\*[^*]+\*\*|_[^_]+_|`[^`]+`)/g)){
        const strong=piece.startsWith('**'),em=piece.startsWith('_'),code=piece.startsWith('`');
        p.append(strong?node('strong',{},piece.slice(2,-2)):em?node('em',{},piece.slice(1,-1)):code?node('code',{},piece.slice(1,-1)):piece);
      }
      n.append(p);
    }return n;
  }
  const content=(kind,value='',attrs={})=>{
    if(['markdown','rich-text'].includes(kind))return Object.assign(markdown(value),attrs);
    if(['image','avatar'].includes(kind)){
      const n=/^(data:image\/(png|jpeg|webp|gif);base64,|blob:)/.test(value)?node('img',{src:value,alt:attrs.alt||'',...attrs}):node('span',{...attrs},kind==='avatar'?String(value).split(/\s+/).map(x=>x[0]||'').join('').slice(0,2).toUpperCase():value);
      if(kind==='avatar')n.classList.add('avatar');return n;
    }
    if(kind==='media')return node('audio',{controls:'','aria-label':attrs.label||'Media',...(/^(data:audio\/|blob:)/.test(value)?{src:value}:{}),...attrs});
    return node(kind==='code'?'pre':'span',attrs,value);
  };
  const press=(label,fn,cls='')=>node('button',{type:'button',class:cls,on:{click:fn}},label);
  function selected(root,memory={},version=()=>root.textContent){
    const capture=()=>{const s=getSelection(),value=s?.toString();if(value&&root.contains(s.anchorNode)&&root.contains(s.focusNode)){memory.passage={value,version:version()};return value}return ''};
    root.addEventListener('pointerup',capture);
    return ()=>capture()||(memory.passage?.version===version()?memory.passage.value:'');
  }
  function submit(form,fn){
    // The frame deliberately lacks allow-forms. Native submission can be
    // blocked before a submit event; keep validation and keyboard activation
    // local, then invoke the authored guarded word rather than navigation.
    const send=e=>{e.preventDefault();if(form.checkValidity())return fn(e);form.reportValidity()};
    const click=e=>{const b=e.target.closest('button[type=submit]');if(b&&form.contains(b))return send(e)};
    const key=e=>{if(e.key==='Enter'&&(e.ctrlKey||e.metaKey||e.target.matches('input:not([type=file])')))return send(e)};
    form.addEventListener('click',click,true);form.addEventListener('keydown',key);
  }
  const input=(kind,attrs={})=>node(kind==='multiline'?'textarea':kind==='choice'?'select':'input',{
    ...(kind==='toggle'?{type:'checkbox'}:{}),...attrs});
  const focusable=n=>[...n.querySelectorAll('button,input,textarea,select,[tabindex="0"],a[href]')].filter(x=>!x.disabled&&!x.hidden);
  function navigation(n,{menu=false}={}){
    n.addEventListener('keydown',e=>{
      if(!['ArrowDown','ArrowUp','Home','End'].includes(e.key)||e.target.matches('input,textarea,select'))return;
      const items=focusable(n);if(!items.length)return;
      const i=items.indexOf(document.activeElement);e.preventDefault();
      items[e.key==='Home'?0:e.key==='End'?items.length-1:(i+(e.key==='ArrowUp'?-1:1)+items.length)%items.length].focus();
    });return n;
  }
  function overlay(kind,body,{label='Details',anchor,close:closed}={}){
    const previous=document.activeElement,modal=['dialog','drawer'].includes(kind);
    const veil=node('div',{class:modal?'veil':'overlay-anchor'});
    const attrs={class:kind,role:modal?'dialog':kind==='menu'?'menu':kind==='tooltip'?'tooltip':'status',
      'aria-label':label,...(modal?{'aria-modal':'true'}:{})};
    const n=body?.classList?.contains(kind)?body:node('section',attrs,body);
    for(const [key,value] of Object.entries(attrs))n.setAttribute(key,value);veil.append(n);
    let disposed=false;
    const close=(silent=false)=>{if(disposed)return;disposed=true;veil.remove();document.removeEventListener('keydown',key);if(previous?.isConnected)previous.focus();if(silent!==true)closed?.()};
    const key=e=>{if(e.key==='Escape'){e.preventDefault();close()}if(modal&&e.key==='Tab'){
      const items=focusable(n);if(!items.length){e.preventDefault();n.focus();return}
      if(e.shiftKey&&document.activeElement===items[0]){e.preventDefault();items.at(-1).focus()}
      else if(!e.shiftKey&&document.activeElement===items.at(-1)){e.preventDefault();items[0].focus()}
    }};
    veil.addEventListener('click',e=>{if(e.target===veil)close()});document.addEventListener('keydown',key);
    document.body.append(veil);navigation(n,{menu:kind==='menu'});
    if(anchor){const r=n.getBoundingClientRect();Object.assign(n.style,{position:'fixed',left:Math.max(8,Math.min(anchor.x,innerWidth-r.width-8))+'px',top:Math.max(8,Math.min(anchor.y,innerHeight-r.height-8))+'px'})}
    if(modal||kind==='menu'){n.tabIndex=-1;(focusable(n)[0]||n).focus()}
    if(kind==='toast')setTimeout(close,5000);
    return {node:n,close};
  }
  function motion(n,{from={opacity:0,transform:'translateY(6px)'},to={opacity:1,transform:'none'},duration=200}={}){
    if(matchMedia('(prefers-reduced-motion:reduce)').matches)return {cancel(){}};
    return n.animate([from,to],{duration,easing:'cubic-bezier(.2,.7,.2,1)',fill:'none'});
  }
  function spring(update,{x=0,y=0}={}){
    let tx=x,ty=y,vx=0,vy=0,raf,stopped=false;
    const tick=()=>{if(stopped)return;vx=(vx+(tx-x)*.24)*.65;vy=(vy+(ty-y)*.24)*.65;x+=vx;y+=vy;update(x,y);raf=requestAnimationFrame(tick)};tick();
    return {to(a,b){tx=a;ty=b},stop(){stopped=true;cancelAnimationFrame(raf)}};
  }
  function canvas({width=320,height=180,label='Drawn surface',pixels,series}={}){
    width=Math.max(1,Math.min(4096,Math.round(width)));height=Math.max(1,Math.min(4096,Math.round(height)));
    const n=node('canvas',{width,height,role:'img','aria-label':label,tabindex:0});
    n.style.maxWidth='100%';const c=n.getContext('2d');c.imageSmoothingEnabled=false;
    const draw=()=>{c.clearRect(0,0,width,height);if(pixels){const rows=typeof pixels==='string'?pixels.split('\n'):pixels;const h=height/rows.length,w=width/Math.max(...rows.map(r=>r.length));rows.forEach((r,y)=>[...r].forEach((v,x)=>{if(v!=='.'&&v!==' '){c.fillStyle=tokens[v]||tokens.accent;c.fillRect(x*w,y*h,w,h)}}))}
      if(series?.length){const max=Math.max(...series,1);c.strokeStyle=tokens.accent;c.lineWidth=2;c.beginPath();series.forEach((v,i)=>{const x=i*width/Math.max(1,series.length-1),y=height-v/max*(height-8);i?c.lineTo(x,y):c.moveTo(x,y)});c.stroke()}};
    draw();return n;
  }
  function virtual(children,{height=320,rowHeight=40,overscan=4}={}){
    height=Math.max(40,Math.min(4096,height));rowHeight=Math.max(12,rowHeight);
    const view=layout('scroll',{'aria-label':'Windowed collection',tabindex:0});Object.assign(view.style,{height:height+'px',position:'relative'});
    const space=node('div',{style:{height:children.length*rowHeight+'px',position:'relative'}});view.append(space);
    let start=-1;const draw=()=>{const next=Math.max(0,Math.floor(view.scrollTop/rowHeight)-overscan);if(next===start)return;start=next;space.replaceChildren();
      children.slice(start,start+Math.ceil(height/rowHeight)+2*overscan).forEach((make,i)=>space.append(node('div',{style:{position:'absolute',top:(start+i)*rowHeight+'px',height:rowHeight+'px',width:'100%'}},typeof make==='function'?make():make)))};
    view.addEventListener('scroll',draw);draw();return view;
  }
  // A few line icons any part can use (P.icon(name)): panel buttons take theirs from the lens (panel left, icon sidebar).
  const ICONS={sidebar:'<rect x="3.5" y="4.5" width="17" height="15" rx="2.5"/><path d="M9 4.5v15"/>',
    'sidebar-right':'<rect x="3.5" y="4.5" width="17" height="15" rx="2.5"/><path d="M15 4.5v15"/>',
    comment:'<path d="M5 5.5h14a1.5 1.5 0 0 1 1.5 1.5v8.5A1.5 1.5 0 0 1 19 17H10l-4.5 3.5V17H5a1.5 1.5 0 0 1-1.5-1.5V7A1.5 1.5 0 0 1 5 5.5z"/>',
    list:'<path d="M8 7h12M8 12h12M8 17h12"/><circle cx="4.5" cy="7" r=".8"/><circle cx="4.5" cy="12" r=".8"/><circle cx="4.5" cy="17" r=".8"/>',
    outline:'<path d="M4 6h16M7 11h13M10 16h10"/>',info:'<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5M12 8h.01"/>',
    files:'<path d="M4 6.5A1.5 1.5 0 0 1 5.5 5h4l2 2h7A1.5 1.5 0 0 1 20 8.5v9a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 17.5z"/>',
    chat:'<path d="M4 6.5A1.5 1.5 0 0 1 5.5 5h13A1.5 1.5 0 0 1 20 6.5v8a1.5 1.5 0 0 1-1.5 1.5H9l-5 4z"/>',
    people:'<circle cx="9" cy="9" r="3"/><path d="M3.5 19a5.5 5.5 0 0 1 11 0M16 6.5a3 3 0 0 1 0 5.5M17.5 19a5 5 0 0 0-2.5-4.3"/>'};
  function icon(name){const n=document.createElementNS('http://www.w3.org/2000/svg','svg');n.setAttribute('viewBox','0 0 24 24');n.setAttribute('fill','none');
    n.setAttribute('stroke','currentColor');n.setAttribute('stroke-width','1.7');n.setAttribute('stroke-linecap','round');n.setAttribute('stroke-linejoin','round');
    n.setAttribute('aria-hidden','true');n.classList.add('ag-icon');n.innerHTML=ICONS[name]||ICONS[name==='left'?'sidebar':'sidebar-right']||ICONS.sidebar;return n}
  // Side panels (painter.js marks them): shut is no width at all; over lies on the page when the window is too small.
  css(`[data-panel][data-shut]{display:none!important}[data-panel][data-over]{position:fixed!important;top:var(--ag-panel-top,0px);bottom:0;z-index:40;width:min(var(--panel-width,300px),calc(100vw - 48px))!important;max-width:none!important;overflow:auto;background:var(--ag-raised,var(--card,#fff));box-shadow:0 18px 50px #00000026,0 1px 0 #0000000d}[data-panel=left][data-over]{left:0;border-radius:0 14px 14px 0}[data-panel=right][data-over]{right:0;border-radius:14px 0 0 14px}.ag-panel-toggle{width:32px;height:32px;display:inline-grid;place-items:center;border:0;border-radius:8px;background:none;color:inherit;cursor:pointer;padding:0;flex:none}.ag-panel-toggle:hover{background:var(--ag-hover,rgba(0,0,0,.05))}.ag-panel-toggle[aria-pressed=true]{color:var(--ag-accent,#3f7564);background:var(--ag-accent-soft,rgba(63,117,100,.12))}.ag-panel-toggle:focus-visible{outline:2px solid var(--ag-accent,#3f7564);outline-offset:1px}.ag-icon{width:18px;height:18px}.ag-panel-float{position:fixed;top:8px;z-index:41;display:flex;gap:4px}.ag-panel-float.left{left:8px}.ag-panel-float.right{right:8px}@media (prefers-reduced-motion:no-preference){[data-panel][data-over]{animation:ag-panel-in .16s ease-out}}@keyframes ag-panel-in{from{opacity:.4;translate:var(--panel-from,0) 0}to{opacity:1;translate:0 0}}[data-panel=left][data-over]{--panel-from:-24px}[data-panel=right][data-over]{--panel-from:24px}`);
  css(`*{box-sizing:border-box}[hidden]{display:none!important}[data-layout]{gap:var(--space,12px);min-width:0}.overlay-anchor{position:fixed;inset:0;pointer-events:none;z-index:100}.overlay-anchor>*{pointer-events:auto}.dialog{margin:auto;background:var(--card);padding:24px;border-radius:12px;min-width:min(420px,90vw);max-width:90vw}.popover,.tooltip{background:var(--card);border:1px solid var(--ag-border,#e5e8e2);padding:12px;border-radius:10px;box-shadow:var(--ag-shadow,0 12px 40px #24352c18)}.rich-text p{white-space:pre-wrap}.gallery-example{padding:16px;border:1px solid var(--ag-border,#e5e8e2);border-radius:12px;background:var(--card)}.catalogue{padding:24px}.catalogue pre{white-space:pre-wrap;font-size:11px}.catalogue>section{padding:18px;margin:14px 0;background:var(--card);border:1px solid var(--ag-border,#e5e8e2);border-radius:12px}table{border-collapse:collapse;width:100%}td,th{padding:10px;text-align:left;border-bottom:1px solid var(--ag-border,#e5e8e2)}@media(max-width:650px){[data-layout=split],[data-layout=grid],.board{grid-template-columns:1fr!important}body{min-width:0!important;padding:18px!important}.tools,.filters{flex-wrap:wrap}.drawer{width:100%}}`);
  return {tokens,node,layout,content,press,selected,submit,input,overlay,motion,spring,canvas,virtual,navigation,markdown,formatValue,parseDateEntry,selectionAction,icon};
})();
