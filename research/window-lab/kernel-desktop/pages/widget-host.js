/* Trusted host. No session, instance capability, native API or DOM crosses the wall. */
'use strict';
(() => {
  const q = new URLSearchParams(location.search), surface = document.querySelector('#widget-surface');
  let frame, instance, stopped = false, busy = 0, pollTimer;
  const hooks = new Map();
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
  };
  const send = data => frame?.contentWindow.postMessage(data,'*');
  const bootstrap = `(() => {
    const pending=new Map(), listeners=new Map();let n=0, setup;
    const ready=new Promise(r=>setup=r);
    function call(op,data={}){return new Promise((resolve,reject)=>{const id=++n;pending.set(id,{resolve,reject});parent.postMessage({agora:1,id,op,...data},'*')})}
    addEventListener('message',e=>{if(e.source!==parent||e.data?.agora!==1)return;const m=e.data;
      if(m.init){setup(Object.freeze(m.init));return}
      if(m.event){for(const fn of listeners.get(m.event.word)||[])try{fn(m.event)}catch{};return}
      const p=pending.get(m.id);if(!p)return;pending.delete(m.id);m.error?p.reject(Error(m.error)):p.resolve(m.result);
    });
    const api={ready,do:(line,saw)=>call('do',{line,saw}),see:line=>call('see',{line}),
      hear:async(word,fn)=>{await call('hear',{word});if(!listeners.has(word))listeners.set(word,[]);listeners.get(word).push(fn);return()=>{listeners.set(word,listeners.get(word).filter(f=>f!==fn))}},
      theme:()=>call('theme').then(r=>r.theme),describe:text=>call('describe',{text}),
      hitAreas:rects=>call('hits',{rects}),paintArea:rect=>call('paint',{rect})};
    Object.defineProperty(window,'agora',{value:Object.freeze(api),writable:false,configurable:false});
  })();`;
  const csp = "default-src 'none'; connect-src 'none'; script-src 'unsafe-inline' blob:; style-src 'unsafe-inline'; img-src data: blob:; font-src 'none'; media-src 'none'; object-src 'none'; frame-src 'none'; worker-src 'none'; base-uri 'none'; form-action 'none'";
  const rect = r => {
    if(!r||!['x','y','width','height'].every(k=>Number.isFinite(r[k])))throw Error('Invalid surface rectangle');
    return {x:Math.max(0,Math.min(innerWidth,r.x)),y:Math.max(0,Math.min(innerHeight,r.y)),
      width:Math.max(0,Math.min(innerWidth-r.x,r.width)),height:Math.max(0,Math.min(innerHeight-r.y,r.height))};
  };
  addEventListener('message',async e=>{
    if(stopped||!frame||e.source!==frame.contentWindow||e.data?.agora!==1)return;
    const {id,op}=e.data;
    if(!Number.isSafeInteger(id)||busy>=8)return;
    busy++;
    try{
      let result;
      if(op==='hits'||op==='paint'){
        if(document.body.dataset.surface!=='overlay')throw Error('This surface is not an overlay');
        if(op==='hits')native.hits=(Array.isArray(e.data.rects)?e.data.rects:[]).slice(0,32).map(rect);
        else native.paint=rect(e.data.rect);
        result={ok:true};
      }else{
        if(!['do','see','hear','theme','describe'].includes(op))throw Error('Unknown bridge call');
        result=await post('call',{op,line:e.data.line,saw:e.data.saw,word:e.data.word,text:e.data.text});
        if(!result.ok)throw Error(result.text||'Refused');
        if(op==='do'){
          const receipt=document.querySelector('#receipt');if(receipt)receipt.textContent=result.text;
          send({agora:1,event:{word:'widget.changed'}});
        }
      }
      send({agora:1,id,result});
    }catch(err){send({agora:1,id,error:String(err.message||err)})}finally{busy--}
  });
  async function poll(){
    if(stopped)return;
    try{const r=await post('poll');if(!r.ok){stop(r.text);return}for(const event of r.events)send({agora:1,event})}
    catch{stop('Widget disconnected. Reopen to continue.');return}
    pollTimer=setTimeout(poll,400);
  }
  async function start(){
    const data=await post('open',{widget:q.get('widget')});if(!data.ok)throw Error(data.text);
    instance=data.instance;
    document.body.dataset.surface=data.surface;
    if(q.get('slot'))document.body.classList.add('slot');
    else if(data.surface==='overlay'){document.body.classList.add('overlay');document.documentElement.style.background='transparent'}
    else {KD.chrome('Widget · '+data.name);document.querySelectorAll('#receipt')[1]?.remove()}
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
