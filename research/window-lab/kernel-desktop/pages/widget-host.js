/* Trusted host. No session, instance capability, native API or DOM crosses the wall. */
'use strict';
(() => {
  const q = new URLSearchParams(location.search), surface = document.querySelector('#widget-surface');
  let frame, instance, stopped = false, busy = 0, pollTimer, componentView=false;
  const phases=new Map();let stallTimer,recovering=false,lastPong=performance.now();
  const hooks = new Map();
  const waiting=[];
  let nextCall=0;
  async function callTurn(){const now=performance.now(),at=Math.max(now,nextCall);nextCall=at+40;if(at>now)await new Promise(resolve=>setTimeout(resolve,at-now))}
  const native = {paint:null, hits:[]};
  const post = async (action, data={}) => {
    const r = await fetch('/desk/widget/'+action,{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({...data,instance})});
    if (!r.ok) throw Error('The widget door is unavailable.');
    return r.json();
  };
  const stop = text => {
    stopped=true; clearTimeout(pollTimer); frame?.remove(); frame=null;
    const receipt=document.querySelector('#receipt'); if(receipt) receipt.textContent=text;
    surface.dataset.stopped='true'; native.paint=null; native.hits=[];
    const card=document.createElement('section');card.setAttribute('role','status');card.style.cssText='padding:16px;background:#FAF9F6;color:#35433D;border-radius:12px';
    const label=document.createElement('strong');label.textContent='This part stopped';
    const detail=document.createElement('p');detail.textContent=text;
    const retry=document.createElement('button');retry.textContent='Try again';retry.onclick=()=>location.reload();card.append(label,detail,retry);surface.replaceChildren(card);
  };
  const send = data => frame?.contentWindow.postMessage(data,'*');
  const bootstrap = `(() => {
    const pending=new Map(), listeners=new Map();let n=0, setup;
    const ready=new Promise(r=>setup=r);
    function call(op,data={}){return new Promise((resolve,reject)=>{const id=++n;pending.set(id,{resolve,reject});parent.postMessage({agora:1,id,op,...data},'*')})}
    addEventListener('message',e=>{if(e.source!==parent||e.data?.agora!==1)return;const m=e.data;
      if(m.init){setup(Object.freeze(m.init));return}
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
      hitAreas:rects=>call('hits',{rects}),paintArea:rect=>call('paint',{rect})};
    Object.defineProperty(window,'agora',{value:Object.freeze(api),writable:false,configurable:false});
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
      if(op==='hits'||op==='paint'){
        if(document.body.dataset.surface!=='overlay')throw Error('This surface is not an overlay');
        if(op==='hits')native.hits=(Array.isArray(e.data.rects)?e.data.rects:[]).slice(0,32).map(rect);
        else native.paint=rect(e.data.rect);
        result={ok:true};
      }else{
        if(!['do','see','hear','theme','describe','upload','project','file','download','download-reading'].includes(op))throw Error('Unknown bridge call');
        if(componentView)await callTurn();
        result=await post('call',{op:['file','download'].includes(op)?'file-check':op==='download-reading'?'see':op,line:e.data.line,saw:e.data.saw,word:e.data.word,text:e.data.text,name:e.data.name,data:e.data.data,group:e.data.group,view:e.data.view,target:e.data.target,variant:e.data.variant});
        if(!result.ok)throw Error(result.text||'Refused');
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
    }catch(err){send({agora:1,id,error:String(err.message||err)})}finally{busy--;waiting.shift()?.()}
  });
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
      detail.textContent=part.component+' · '+String(e.message||e).split('\n')[0];
      const retry=document.createElement('button');retry.textContent='Try again';retry.onclick=()=>location.reload();card.append(retry);
    }finally{recovering=false}
  }
  stallTimer=setInterval(()=>{
    // Descendants are begun after their containers: attribute a blocked mount
    // to the deepest active part, rather than its innocent layout ancestors.
    const blocked=[...phases.values()].filter(p=>performance.now()-p.at>(p.stage==='module'?10000:2500)).sort((a,b)=>b.path.length-a.path.length);
    if(blocked.length)recoverStall(blocked[0]);
    else if(frame&&!stopped&&!recovering){
      send({agora:1,ping:true});
      if(performance.now()-lastPong>5000&&!phases.size){
        recovering=true;terminateOwnedRenderer().then(()=>stop('This window stopped answering for 5000 ms.')).catch(e=>stop(String(e.message||e))).finally(()=>recovering=false);
      }
    }
  },250);
  addEventListener('agora-frame-failed',()=>{
    if(recovering)return;
    const part=[...phases.values()].sort((a,b)=>b.path.length-a.path.length)[0];
    if(part)recoverStall(part);
    else stop('This part stopped · its renderer exited. Reopen this window to try again.');
  });
  async function poll(){
    if(stopped)return;
    try{const r=await post('poll');if(!r.ok){stop(r.text);return}for(const event of r.events)send({agora:1,event})}
    catch{stop('Widget disconnected. Reopen to continue.');return}
    pollTimer=setTimeout(poll,400);
  }
  async function start(){
    lastPong=performance.now();
    const data=await post('open',{widget:q.get('widget')});if(!data.ok)throw Error(data.text);
    instance=data.instance;
    componentView=!!data.component_lens;
    document.body.classList.toggle('quiet-receipts',data.receipts==='quiet');
    document.body.dataset.surface=data.surface;
    if(q.get('slot'))document.body.classList.add('slot');
    else if(data.surface==='overlay'){document.body.classList.add('overlay');document.documentElement.style.background='transparent'}
    else {KD.chrome(data.title||data.name);document.querySelectorAll('#receipt')[1]?.remove()}
    frame=document.createElement('iframe');frame.title=data.name;frame.name='agora-widget';frame.setAttribute('sandbox','allow-scripts');
    frame.setAttribute('referrerpolicy','no-referrer');
    frame.setAttribute('allow',"camera 'none'; microphone 'none'; geolocation 'none'; clipboard-read 'none'; clipboard-write 'none'; fullscreen 'none'");
    // srcdoc has a unique opaque origin. Scripts run after the bridge bootstrap.
    const safe=s=>s.replace(/<\/script/gi,'<\\/script');
    frame.srcdoc=`<!doctype html><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="${csp}"><style>html,body{margin:0;min-height:100%;font-family:${data.theme.font};color:${data.theme.ink}}*{box-sizing:border-box}</style><script>${safe(bootstrap)}<\/script><script type="module">${safe(data.code)}<\/script>`;
    frame.onload=()=>send({agora:1,init:{widget:data.widget,name:data.name,surface:data.surface,theme:data.theme}});
    surface.replaceChildren(frame);poll();
  }
  // Read-only native rendering metadata, never an authority channel.
  Object.defineProperty(window,'widgetSurface',{value:native});
  addEventListener('pagehide',()=>{if(instance)navigator.sendBeacon('/desk/widget/close',JSON.stringify({instance}))});
  start().catch(e=>stop(String(e.message||e)));
})();
