// EDITING THE DESKTOP HOST (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
// This file is a seam between the world and Windows: it turns world facts into screen effects and screen events into world
// facts, through small words. It holds no preferences and no content. Which apps, what a button opens, sizes, names, ids and
// who may do what live in settings things it reads (shell-settings, wm-settings). It does not seed the world at start
// (people, chats, pins). New behaviour is a rule over the words offered here. Before writing a Windows or browser helper,
// use the shared one (gaming_gate for full-screen and desktop tests, widget_browser for hidden pages) instead of a copy.
//
/* Trusted host. No session, instance capability, native API or DOM crosses the wall. */
'use strict';
(() => {
  const q = new URLSearchParams(location.search), surface = document.querySelector('#widget-surface');
  // A shell page (pages/shell/top.html, dock.html) hosts its bar's painter here: window.AGORA_SHELL = {page, widget,
  // fallback(text)}. No chrome, no receipt, a transparent frame over the page's wallpaper slice, and the narrow native
  // bridge below when the broker says the widget holds window.native.
  const shell = window.AGORA_SHELL || null;
  let frame, instance, stopped = false, busy = 0, pollTimer, componentView=false, nativeGranted=false, lastLayout=null;
  const phases=new Map();let stallTimer,recovering=false,lastPong=performance.now();
  // A window that is minimised, tucked or covered is not a stopped window (27 Oct). Chromium slows a hidden page's
  // timers (after five minutes, chains wake about once a minute) and may freeze or discard its frame's renderer. So the
  // watchdog judges only while the page is seen and its own clock ticks on time; a frame lost while hidden is started
  // again when the window is seen; and a broker instance reaped for silence is opened again by itself.
  let lastTick=performance.now(),quietUntil=0,restartWanted=null,chromed=false,code=null,polling=false,pollFails=0,renewing=null;
  const restarts=[],heardWords=new Set();
  const forgive=()=>{const now=performance.now();lastPong=now;lastTick=now;for(const p of phases.values())p.at=now};
  const hooks = new Map();
  const waiting=[];
  let nextCall=0;
  async function callTurn(){const now=performance.now(),at=Math.max(now,nextCall);nextCall=at+40;if(at>now)await new Promise(resolve=>setTimeout(resolve,at-now))}
  const native = {paint:null, hits:[]};
  // A failure here, outside any line, is said to the kernel so it lands in `refusals` (kd.js KD.failed, card dk939).
  // A line the kernel refused is kept there already, so those errors are marked kept and not said again.
  let partName='',widgetId='';
  const failed=(why,line)=>{try{window.KD&&KD.failed&&KD.failed(why,line,shell?shell.page+'-bar':(partName||q.get('widget')||'widget'))}catch{}};
  const post = async (action, data={}) => {
    const r = await fetch('/desk/widget/'+action,{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({...data,instance})});
    if (!r.ok) throw Error('The widget door is unavailable.');
    return r.json();
  };
  const stop = text => {
    failed('stopped: '+text);
    // A shell bar never shows a whole-window card (its window is mostly see-through and clipped): the page paints the
    // hand-written bar instead, and the shell page tries the components again later.
    if(shell?.fallback){stopped=true;clearTimeout(pollTimer);frame?.remove();frame=null;shell.fallback(text,!!shell.painted);return}
    stopped=true; clearTimeout(pollTimer); frame?.remove(); frame=null;
    const receipt=document.querySelector('#receipt'); if(receipt) receipt.textContent=text;
    surface.dataset.stopped='true'; native.paint=null; native.hits=[];
    const card=document.createElement('section');card.setAttribute('role','status');card.style.cssText='padding:16px;background:var(--ag-surface,#FAF9F6);color:var(--ag-ink,#35433D);border-radius:var(--ag-radius-l,12px)';
    const label=document.createElement('strong');label.textContent='This part stopped';
    const detail=document.createElement('p');detail.textContent=text;
    const retry=document.createElement('button');retry.textContent='Try again';retry.onclick=()=>location.reload();card.append(label,detail,retry);surface.replaceChildren(card);
  };
  const send = data => frame?.contentWindow.postMessage(data,'*');
  const bootstrap = `(() => {
    const pending=new Map(), listeners=new Map();let n=0, setup, menuOn=false;
    // The theme this window wears. The host sends a new one whenever it changes; CSS variables repaint everything at once.
    function applyTheme(t){let s=document.getElementById('ag-theme');if(!s){s=document.createElement('style');s.id='ag-theme';document.head.append(s)}
      if(s.textContent!==t.css)s.textContent=t.css;
      for(const [k,v] of Object.entries(t.tokens||{}))document.documentElement.style.setProperty('--'+k,v);
      window.dispatchEvent(new CustomEvent('ag-theme',{detail:t}))}
    const ready=new Promise(r=>setup=r);
    function call(op,data={}){return new Promise((resolve,reject)=>{const id=++n;pending.set(id,{resolve,reject});parent.postMessage({agora:1,id,op,...data},'*')})}
    addEventListener('message',e=>{if(e.source!==parent||e.data?.agora!==1)return;const m=e.data;
      if(m.init){menuOn=m.menu===true;setup(Object.freeze(m.init));return}
      if(m.theme){applyTheme(m.theme);return}
      if(m.ping){parent.postMessage({agora:1,op:'widget-pong'},'*');return}
      if(m.event){for(const fn of listeners.get(m.event.word)||[])try{fn(m.event)}catch{};return}
      const p=pending.get(m.id);if(!p)return;pending.delete(m.id);m.error?p.reject(Error(m.error)):p.resolve(m.result);
    });
    const api={ready,do:(line,saw)=>call('do',{line,saw}),see:line=>call('see',{line}),
      project:view=>call('project',{view}),file:(target,variant='content')=>call('file',{target,variant}),
      download:target=>call('download',{target}),downloadReading:line=>call('download-reading',{line}),
      upload:async(file,group)=>{if(!(file instanceof Blob))throw Error('Choose a file');const bytes=new Uint8Array(await file.arrayBuffer());let raw='';for(let i=0;i<bytes.length;i+=32768)raw+=String.fromCharCode(...bytes.subarray(i,i+32768));return call('upload',{name:file.name||'Upload',data:btoa(raw),group})},
      hear:async(word,fn)=>{await call('hear',{word});if(!listeners.has(word))listeners.set(word,[]);listeners.get(word).push(fn);return()=>{listeners.set(word,listeners.get(word).filter(f=>f!==fn))}},
      theme:()=>call('theme').then(r=>r.theme),describe:text=>call('describe',{text}),
      componentPhase:data=>parent.postMessage({agora:1,op:'component-phase',...data},'*'),
      hitAreas:rects=>call('hits',{rects}),paintArea:rect=>call('paint',{rect}),
      native:(name,...args)=>call('native',{name,args})};
    Object.defineProperty(window,'agora',{value:Object.freeze(api),writable:false,configurable:false});
    // The shared right-click menu (card dk1344, pages/menu.js): every view inherits it with no wiring. This frame only
    // says where the press was, the words selected under it and the thing the pressed part shows (data-thing, or the
    // painter's data-fact-id); the trusted page reads that thing again as the viewer and draws the menu. A view that
    // draws its own menu (preventDefault) keeps it; the painter's ask-only menu (right_click=ask) gives way to this one,
    // which ends with the same ask box. Shift, inputs and editable words keep the browser's menu.
    let pressed=null,askOnly=false;
    // menuOn: the host draws the shared menu here (not in a shell bar, whose components keep their own ask menu)
    const shut=()=>{if(menuOn)parent.postMessage({agora:1,op:'context-close'},'*')};
    addEventListener('pointerdown',e=>{
      if(e.button!==2){shut();return}
      const s=getSelection();pressed=s&&s.rangeCount&&!s.isCollapsed?s.getRangeAt(0).cloneRange():null;
    },true);
    addEventListener('keydown',e=>{if(e.key==='Escape')shut()},true);
    addEventListener('contextmenu',()=>{askOnly=false},true);
    addEventListener('agora-menu',e=>{if(e.detail&&e.detail.open)askOnly=true});
    const near=(range,x,y)=>{if(!range)return false;for(const r of range.getClientRects())if(x>=r.left-3&&x<=r.right+3&&y>=r.top-3&&y<=r.bottom+3)return true;return false};
    addEventListener('contextmenu',e=>{
      const t=e.target instanceof Element?e.target:null;
      if(!menuOn||e.shiftKey||!t||t.closest('input,textarea,select,[contenteditable]:not([contenteditable=false])'))return;
      if(e.defaultPrevented&&!askOnly)return;
      if(askOnly)for(const n of document.querySelectorAll('.menu.ask-menu'))n.remove();
      e.preventDefault();
      const s=getSelection(),now=s&&s.rangeCount&&!s.isCollapsed?s.getRangeAt(0):null;
      const range=near(pressed,e.clientX,e.clientY)?pressed:near(now,e.clientX,e.clientY)?now:null;pressed=null;
      const from=range?(range.startContainer.nodeType===1?range.startContainer:range.startContainer.parentElement):t;
      const holder=(from&&from.closest('[data-thing],[data-fact-id]'))||t.closest('[data-thing],[data-fact-id]');
      const part=t.closest('[data-path]');
      parent.postMessage({agora:1,op:'context',x:e.clientX,y:e.clientY,quote:range?String(range).slice(0,2000):'',
        thing:holder?(holder.dataset.thing||holder.dataset.factId||''):'',
        label:holder?(holder.dataset.label||holder.dataset.factTitle||holder.dataset.factName||''):'',
        where:part?part.dataset.path:''},'*');
    });
  })();`;
  const csp = "default-src 'none'; connect-src 'none'; script-src 'unsafe-inline' blob:; style-src 'unsafe-inline'; img-src data: blob:; font-src 'none'; media-src blob:; object-src 'none'; frame-src 'none'; worker-src blob:; base-uri 'none'; form-action 'none'";
  const rect = r => {
    if(!r||!['x','y','width','height'].every(k=>Number.isFinite(r[k])))throw Error('Invalid surface rectangle');
    return {x:Math.max(0,Math.min(innerWidth,r.x)),y:Math.max(0,Math.min(innerHeight,r.y)),
      width:Math.max(0,Math.min(innerWidth-r.x,r.width)),height:Math.max(0,Math.min(innerHeight-r.y,r.height))};
  };
  addEventListener('message',async e=>{
    if(stopped||!frame||e.source!==frame.contentWindow||e.data?.agora!==1)return;
    const {id,op}=e.data;
    if(op==='widget-pong'){lastPong=performance.now();return}
    // the shared right-click menu (pages/menu.js): the frame says where and what; this page reads it as the viewer
    if(op==='context-close'){window.AgoraMenu&&AgoraMenu.close();return}
    if(op==='context'){
      if(shell||!window.AgoraMenu)return;
      const d=e.data,r=frame.getBoundingClientRect(),n=v=>Number.isFinite(+v)?+v:0,text=v=>String(v??'').slice(0,2000);
      AgoraMenu.open({x:r.left+n(d.x),y:r.top+n(d.y),thing:text(d.thing).slice(0,40),quote:text(d.quote),label:text(d.label).slice(0,160),
        where:[partName,text(d.where).slice(0,200)].filter(Boolean).join(' · '),about:widgetId,window:q.get('win')||''});
      return;
    }
    if(op==='component-phase'){
      const path=String(e.data.path||'').slice(0,500);
      if(e.data.end)phases.delete(path);
      else if(phases.size<150)phases.set(path,{path,component:String(e.data.component||'').slice(0,80),stage:e.data.stage,at:performance.now()});
      return;
    }
    if(!Number.isSafeInteger(id))return;
    if(busy>=8){
      if(waiting.length>=64){send({agora:1,id,error:'This view is busy. Please try again.'});return}
      await new Promise(resolve=>waiting.push(resolve));
      if(stopped){send({agora:1,id,error:'This view has stopped.'});return}
    }
    busy++;
    try{
      let result;
      if(op==='native'){result=await nativeCall(String(e.data.name||''),Array.isArray(e.data.args)?e.data.args:[]);send({agora:1,id,result});return}
      if(op==='hits'||op==='paint'){
        if(document.body.dataset.surface!=='overlay')throw Error('This surface is not an overlay');
        if(op==='hits')native.hits=(Array.isArray(e.data.rects)?e.data.rects:[]).slice(0,32).map(rect);
        else native.paint=rect(e.data.rect);
        result={ok:true};
      }else{
        if(!['do','see','hear','theme','describe','upload','project','file','download','download-reading'].includes(op))throw Error('Unknown bridge call');
        if(componentView)await callTurn();
        result=await call({op:['file','download'].includes(op)?'file-check':op==='download-reading'?'see':op,line:e.data.line,saw:e.data.saw,word:e.data.word,text:e.data.text,name:e.data.name,data:e.data.data,group:e.data.group,view:e.data.view,target:e.data.target,variant:e.data.variant});
        if(!result.ok){const kept=Error(result.text||'Refused');kept.kept=true;throw kept}
        if(op==='hear')heardWords.add(String(e.data.word||''));
        if(op==='file'||op==='download'){
          if(!/^\/files\/[a-zA-Z]+\d+\?variant=(content|thumbnail)$/.test(result.path))throw Error('Invalid file route');
          const response=await fetch(result.path,{credentials:'same-origin',cache:'no-store',redirect:'error'});
          if(!response.ok)throw Error('This file is no longer available to you.');
          const blob=await response.blob();
          if(op==='file')result={blob};
          else{
            const filename=/filename="([^"]+)"/.exec(response.headers.get('Content-Disposition')||'')?.[1]||'download';
            await downloadBlob(new Blob([blob],{type:'application/octet-stream'}),filename);result={ok:true};
          }
        }
        if(op==='download-reading'){
          const row=result.rows?.[0];if(!row||typeof row.text!=='string'||row.text.length>1048576)throw Error('This reading is not a downloadable text file.');
          await downloadBlob(new Blob([row.text],{type:'application/octet-stream'}),row.filename||'download.txt');result={ok:true};
        }
        if(op==='do'){
          const receipt=document.querySelector('#receipt');if(receipt)receipt.textContent=result.text;
          send({agora:1,event:{word:'widget.changed'}});
        }
      }
      send({agora:1,id,result});
    }catch(err){if(!err?.kept)failed(String(err?.message||err),op==='do'||op==='see'?String(e.data.line||''):op);send({agora:1,id,error:String(err.message||err)})}finally{busy--;waiting.shift()?.()}
  });
  // ---- window.native: what a shell bar may ask its own window, validated here, in the trusted page. Nothing else
  // crosses: no session, no DOM, no other host function. kd_window's PageApi also refuses outside a shell window.
  const finite=(v,lo,hi)=>Number.isFinite(+v)?Math.max(lo,Math.min(hi,+v)):lo;
  async function toWindow(name,...args){
    (window.__native=window.__native||[]).push([name,...args]);
    if(window.__native.length>200)window.__native.splice(0,100);
    const api=window.pywebview&&window.pywebview.api;
    if(!api||!api[name])return null;
    try{return await api[name](...args)}catch(err){return null}
  }
  async function nativeCall(name,args){
    if(!shell||!nativeGranted)throw Error('This view holds no native grant (window.native)');
    const W=innerWidth,H=innerHeight,dpr=window.devicePixelRatio||1;
    if(name==='layout'){
      const spec=args[0]&&typeof args[0]==='object'?args[0]:{};
      const shape=(Array.isArray(spec.shape)?spec.shape:[]).slice(0,32).map(r=>{
        const x=finite(r&&r.x,0,W),y=finite(r&&r.y,0,H);
        return {x,y,w:finite(r&&r.w,0,W-x),h:finite(r&&r.h,0,H-y),r:finite(r&&r.r,0,400)};
      }).filter(r=>r.w>0&&r.h>0);
      lastLayout={reserve:Math.round(finite(spec.reserve,0,400)),shape};
      window.__shape=lastLayout;
      return await toWindow('layout',JSON.stringify(lastLayout),dpr);
    }
    if(name==='thumbs'){
      const tiles=(Array.isArray(args[0])?args[0]:[]).slice(0,8).filter(t=>t&&/^\d{1,12}$/.test(String(t.hwnd||''))).map(t=>{
        const x=finite(t.x,0,W),y=finite(t.y,0,H);return {hwnd:String(t.hwnd),key:String(t.key||'').slice(0,80),x,y,w:finite(t.w,0,W-x),h:finite(t.h,0,H-y)};
      });
      window.__thumbs=tiles;
      return await toWindow('thumbs',JSON.stringify(tiles),dpr);
    }
    if(name==='title'){
      const handle=String(args[0]||'');
      if(!/^\d{1,12}$/.test(handle))throw Error('A window title needs a numeric window handle');
      return String((await toWindow('title',handle))||'').slice(0,300);
    }
    if(name==='icon'){
      // An app's icon for the frame, which has no network: the same owner-only routes the hand-written bar reads
      // (/desk/icon, an Agora app's svg), fetched here and handed back as bytes, as files are.
      const ref=String(args[0]||''),size=[64,96,128,192,256].includes(+args[1])?+args[1]:128;
      let url;
      if(/^agora:[a-z0-9-]{1,40}$/.test(ref))url='/desk/shell/apps/'+ref.slice(6)+'.svg';
      else if(/^(exe|hwnd|pkg|aumid):/.test(ref)&&ref.length<=600)url='/desk/icon?ref='+encodeURIComponent(ref)+'&size='+size;
      else throw Error('An icon needs an exe:, hwnd:, pkg:, aumid: or agora: reference');
      const r=await fetch(url,{credentials:'same-origin',redirect:'error'});
      if(!r.ok)return null;
      const blob=await r.blob();
      return /^image\//.test(blob.type)?{blob}:null;
    }
    throw Error('Unknown native call: layout, thumbs, title or icon');
  }
  // pywebview's API arrives a moment after the page; the last layout is sent again then, so no bar is left unshaped.
  addEventListener('pywebviewready',()=>{if(lastLayout)toWindow('layout',JSON.stringify(lastLayout),window.devicePixelRatio||1)});
  let downloadId=0;
  async function downloadBlob(blob,name){
    const url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;
    link.download=String(name).replace(/[\\/\x00-\x1f]/g,'_').slice(0,160);
    if(window.chrome?.webview){
      const id=++downloadId;
      await new Promise((resolve,reject)=>{
        const timer=setTimeout(()=>{removeEventListener('agora-download-ready',reply);reject(Error('The download chooser is unavailable.'))},4000);
        const reply=e=>{if(e.detail.id!==id)return;clearTimeout(timer);removeEventListener('agora-download-ready',reply);e.detail.ok?resolve():reject(Error('This download was not authorised.'))};
        addEventListener('agora-download-ready',reply);window.chrome.webview.postMessage(JSON.stringify({agora:'prepare-widget-download',id,url,name:link.download}));
      });
    }
    link.hidden=true;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),10000);
  }
  async function terminateOwnedRenderer(){
    if(!window.chrome?.webview)throw Error('Native renderer recovery is unavailable; reopen this view');
    return new Promise((resolve,reject)=>{
      const timeout=setTimeout(()=>{removeEventListener('agora-renderer-recovered',reply);reject(Error('Native renderer recovery timed out'))},4000);
      const reply=e=>{clearTimeout(timeout);removeEventListener('agora-renderer-recovered',reply);e.detail.ok?resolve():reject(Error(e.detail.error))};
      addEventListener('agora-renderer-recovered',reply);
      window.chrome.webview.postMessage(JSON.stringify({agora:'recover-widget-renderer'}));
    });
  }
  // The broker forgets an instance it has not heard from (a hidden page polls rarely): open a fresh one for the same
  // widget, hear the same words again, and carry on. Changed code restarts the frame instead.
  const gone=r=>!r.ok&&/no widget instance|widget host disconnected/.test(r.text||'');
  function renew(){
    if(!renewing)renewing=(async()=>{
      const data=await post('open',{widget:(shell&&shell.widget)||q.get('widget')});
      if(!data.ok)throw Error(data.text);
      if(data.code!==code){navigator.sendBeacon('/desk/widget/close',JSON.stringify({instance:data.instance}));restartFrame('This widget changed.');return false}
      instance=data.instance;nativeGranted=!!data.native;
      for(const word of heardWords){const r=await post('call',{op:'hear',word});if(!r.ok)heardWords.delete(word)}
      surface.dataset.renewals=String((+surface.dataset.renewals||0)+1);
      send({agora:1,event:{word:'widget.changed'}});
      return true;
    })().finally(()=>renewing=null);
    return renewing;
  }
  async function call(data){
    let r=await post('call',data);
    if(gone(r)&&await renew())r=await post('call',data);
    return r;
  }
  // Start the frame again (a fresh renderer, the same window), at most three times in two minutes; a hidden window
  // waits until it is seen. Only then does it show the stopped card, with Try again.
  async function restartFrame(why){
    if(document.hidden){restartWanted=why;return}
    restartWanted=null;
    const now=performance.now();
    while(restarts.length&&now-restarts[0]>120000)restarts.shift();
    if(restarts.length>=3){stop(why+' It stopped three times in two minutes.');return}
    restarts.push(now);recovering=true;failed('started again: '+why);
    try{
      clearTimeout(pollTimer);phases.clear();frame?.remove();frame=null;
      if(instance){const old=instance;instance=null;fetch('/desk/widget/close',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({instance:old})}).catch(()=>{})}
      stopped=false;heardWords.clear();
      await start();
      surface.dataset.restarts=String((+surface.dataset.restarts||0)+1);
    }catch(e){stop(String(e.message||e))}
    finally{recovering=false;quietUntil=performance.now()+3000}
  }
  document.addEventListener('visibilitychange',()=>{
    forgive();
    if(document.hidden)return;
    if(restartWanted)restartFrame(restartWanted);
    else if(!stopped&&!polling){clearTimeout(pollTimer);poll()}
  });
  document.addEventListener('resume',forgive);
  async function recoverStall(part){
    if(recovering||stopped)return;recovering=true;
    const old=frame;phases.clear();
    const card=document.createElement('section');card.className='component-stopped';card.setAttribute('role','status');
    const title=document.createElement('strong');title.textContent='This part stopped';
    const elapsed=Math.max(0,Math.round(performance.now()-part.at));
    const detail=document.createElement('p');detail.textContent=part.component+' · No response for '+elapsed+' ms. Recovering the view…';card.append(title,detail);
    try{
      const report=await post('stall',{path:part.path,stage:part.stage,elapsed_ms:elapsed});
      if(!report.ok)throw Error(report.text);
      // Removing a frame is not evidence that its hung renderer was killed.
      // Only the native host can verify process/frame ownership and terminate it.
      await terminateOwnedRenderer();
      frame=null;old?.remove();surface.replaceChildren(card);
      await post('close');instance=null;stopped=false;clearTimeout(pollTimer);
      await start();
      surface.dataset.recoveries=String((+surface.dataset.recoveries||0)+1);
    }catch(e){
      frame=null;old?.remove();surface.replaceChildren(card);
      detail.textContent=part.component+' · '+String(e.message||e).split('\n')[0];failed('a stalled '+part.component+' could not recover: '+String(e.message||e).split('\n')[0]);
      const retry=document.createElement('button');retry.textContent='Try again';retry.onclick=()=>location.reload();card.append(retry);
    }finally{recovering=false}
  }
  stallTimer=setInterval(()=>{
    // Judge only a seen page whose own clock is on time: a late tick means this page was slowed or frozen, so every
    // silence measured across it is the browser's, not the frame's.
    const now=performance.now(),late=now-lastTick>1500;lastTick=now;
    if(document.hidden||late){forgive();return}
    // Descendants are begun after their containers: attribute a blocked mount
    // to the deepest active part, rather than its innocent layout ancestors.
    const blocked=[...phases.values()].filter(p=>performance.now()-p.at>(p.stage==='module'?10000:2500)).sort((a,b)=>b.path.length-a.path.length);
    if(blocked.length)recoverStall(blocked[0]);
    else if(frame&&!stopped&&!recovering){
      send({agora:1,ping:true});
      if(performance.now()-lastPong>5000&&!phases.size){
        recovering=true;terminateOwnedRenderer().then(()=>{recovering=false;quietUntil=performance.now()+3000;return restartFrame('This window stopped answering for 5000 ms.')})
          .catch(e=>{recovering=false;stop(String(e.message||e))});
      }
    }
  },250);
  addEventListener('agora-frame-failed',()=>{
    // Our own recovery kills the renderer and its exit arrives a moment later: that is not a second failure.
    if(recovering||performance.now()<quietUntil)return;
    // Lost while hidden (Chromium may discard a background frame), or with no part mid-paint: start it again.
    // A part caught mid-paint while seen is quarantined, as before.
    const part=!document.hidden&&[...phases.values()].sort((a,b)=>b.path.length-a.path.length)[0];
    if(part)recoverStall(part);
    else restartFrame('This part stopped · its renderer exited.');
  });
  async function poll(){
    if(stopped||polling)return;
    polling=true;let wait=400;
    try{
      let r=await post('poll');
      if(gone(r)&&await renew())r=await post('poll');
      if(!r.ok){
        polling=false;
        if(/off or changed/.test(r.text||''))restartFrame(r.text);else stop(r.text);
        return;
      }
      pollFails=0;delete surface.dataset.offline;
      for(const event of r.events)send({agora:1,event});
    }catch{
      // The door may be restarting: wait longer each time, never give up on a window the person can still see.
      pollFails++;wait=Math.min(10000,400*2**pollFails);surface.dataset.offline='true';
    }
    polling=false;
    if(!stopped)pollTimer=setTimeout(poll,wait);
  }
  async function start(){
    forgive();
    const data=await post('open',{widget:(shell&&shell.widget)||q.get('widget')});if(!data.ok)throw Error(data.text);
    instance=data.instance;code=data.code;partName=String(data.name||'');widgetId=String(data.widget||'');if(window.AgoraMenu)AgoraMenu.about=widgetId;
    componentView=!!data.component_lens;
    nativeGranted=!!data.native;
    if(shell&&!nativeGranted)throw Error('The '+(data.name||'bar')+' widget holds no window.native grant');
    document.body.classList.toggle('quiet-receipts',data.receipts==='quiet');
    document.body.dataset.surface=data.surface;
    if(shell){document.body.classList.add('shell-frame');shell.painted=true}
    else if(q.get('slot'))document.body.classList.add('slot');
    else if(data.surface==='overlay'){document.body.classList.add('overlay');document.documentElement.style.background='transparent'}
    else if(!chromed){chromed=true;KD.chrome(data.title||data.name);document.querySelectorAll('#receipt')[1]?.remove()}
    frame=document.createElement('iframe');frame.title=data.name;frame.name='agora-widget';frame.setAttribute('sandbox','allow-scripts');
    frame.setAttribute('referrerpolicy','no-referrer');
    frame.setAttribute('allow',"camera 'none'; microphone 'none'; geolocation 'none'; clipboard-read 'none'; clipboard-write 'none'; fullscreen 'none'");
    // srcdoc has a unique opaque origin. Scripts run after the bridge bootstrap.
    const safe=s=>s.replace(/<\/script/gi,'<\\/script');
    frame.srcdoc=`<!doctype html><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="${csp}"><style id="ag-theme">${String(data.theme.css||'').replace(/<\/style/gi,'<\\/style')}</style><style>html,body{margin:0;min-height:100%;font-family:${data.theme.font};color:${data.theme.ink}}*{box-sizing:border-box}</style>${shell?'<style>html,body{background:transparent!important}:root{color-scheme:normal!important}</style>':''}<script>${safe(bootstrap)}<\/script><script type="module">${safe(data.code)}<\/script>`;
    // a window opened on a thing (window.open <lens> <thing>) hands its lens the thing as $view.target
    const target=/^[a-z]{1,8}\d+$/.test(q.get('target')||'')?q.get('target'):'';
    frame.onload=()=>send({agora:1,init:{widget:data.widget,name:data.name,surface:data.surface,theme:data.theme,target},menu:!shell&&!q.get('slot')&&data.surface==='window'});
    surface.replaceChildren(frame);poll();
  }
  // The page's theme changed (theme-live.js): the window inside wears it too, without a reload.
  addEventListener('ag-theme',e=>{const t=e.detail;send({agora:1,theme:{css:t.css,tokens:t.tokens,font:t.font,roles:t.roles,palette:t.palette,variant:t.variant}})});
  // Read-only native rendering metadata, never an authority channel.
  Object.defineProperty(window,'widgetSurface',{value:native});
  addEventListener('pagehide',()=>{if(instance)navigator.sendBeacon('/desk/widget/close',JSON.stringify({instance}))});
  start().catch(e=>stop(String(e.message||e)));
})();
