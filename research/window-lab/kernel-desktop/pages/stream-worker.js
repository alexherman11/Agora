// One kernel SSE connection per browser profile, shared by the desktop's windows.
// The door and its event payloads are unchanged. Nothing is stored.
"use strict";
const ports=new Set(), types=new Set();let source=null;
function send(port,message){try{port.postMessage(message);}catch(e){ports.delete(port);}}
function tell(message){for(const p of ports)send(p,message);}
function listen(type){if(types.has(type))return;types.add(type);source.addEventListener(type,e=>tell({type,data:e.data,lastEventId:e.lastEventId,state:source.readyState}));}
onconnect=e=>{
  const port=e.ports[0];ports.add(port);port.start();
  if(!source){source=new EventSource('/door/stream');types.clear();source.onopen=()=>tell({type:'open',state:source.readyState});source.onerror=()=>tell({type:'error',state:source.readyState});listen('message');}
  if(source.readyState===EventSource.OPEN)send(port,{type:'open',state:source.readyState});
  port.onmessage=e=>{
    if(e.data.close){ports.delete(port);port.close();if(!ports.size){source.close();source=null;}return;}
    if(e.data.listen)listen(e.data.listen);
  };
};
