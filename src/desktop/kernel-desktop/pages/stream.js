// Host lifecycle/transport adapter. The shared lens painter still calls EventSource
// normally; multiple windows cannot exhaust HTTP/1's six connections per origin.
"use strict";
(()=>{
  const Native=window.EventSource;
  if(!Native||!window.SharedWorker)return;
  class DesktopStream extends EventTarget {
    static CONNECTING=0;static OPEN=1;static CLOSED=2;
    CONNECTING=0;OPEN=1;CLOSED=2;readyState=0;withCredentials=false;
    constructor(url,options){
      super();this.url=new URL(url,location.href).href;
      if(new URL(this.url).origin!==location.origin || !['/door/stream','/stream'].includes(new URL(this.url).pathname))return new Native(url,options);
      try{this.worker=new SharedWorker('/desk/stream-worker.js',{name:'agora-desktop-stream-v2'});}catch(e){return new Native(url,options);}
      this.worker.port.onmessage=e=>{
        if(this.readyState===2)return;
        const m=e.data;this.readyState=m.state;
        const event=m.data===undefined?new Event(m.type):new MessageEvent(m.type,{data:m.data,lastEventId:m.lastEventId||'',origin:location.origin});
        this.dispatchEvent(event);this['on'+m.type]?.(event);
      };
      this.worker.port.start();
      this.worker.port.postMessage({listen:'message'});
      window.addEventListener('pagehide',()=>this.close(),{once:true});
    }
    addEventListener(type,...args){super.addEventListener(type,...args);if(!['open','error'].includes(type))this.worker.port.postMessage({listen:type});}
    close(){if(this.readyState===2)return;this.readyState=2;this.worker.port.postMessage({close:true});this.worker.port.close();}
  }
  window.EventSource=DesktopStream;
})();
