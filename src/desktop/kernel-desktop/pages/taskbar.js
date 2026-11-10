"use strict";
const { el, see, doLine } = KD;
const icons = {feed:"rss",help:"circle-help",wave:"hand",lines:"terminal",thing:"pin",network:"wifi",volume:"volume-2",battery:"battery"};
const icon = (name) => `icons/${/^[a-z0-9-]+$/.test(name) ? name : "app-window"}.svg`;
function chip(label, src, run, cls="") {
  return el("button", {cls:`chip ${cls}`, title:label, "aria-label":label,
    on:{click:async()=>{const r=await doLine(run); if(r.ok===false) say(r.text); setTimeout(wins,200);}}},
    el("img", {src, alt:"", on:{error:(e)=>{e.target.onerror=null;e.target.src=icon("app-window");}}}));
}
function say(text) { const e=document.getElementById("say");e.textContent=text||"";clearTimeout(say.timer);say.timer=setTimeout(()=>e.textContent="",5000); }
let pinRows=[], pinButtons=[], windowsBusy=false;
async function pins() {
  const r=await see("rows any bar=taskbar"); pinRows=r.rows||[];
  const names={};
  for(const p of pinRows) if(p.kind!=="widget"&&p.shows&&!p.label&&!p.name) {
    const r=await see(`look ${p.shows}`); const t=(r.rows||[])[0]||{};names[p.id]=t.name||t.text||"Pinned thing";
  }
  const paint = p=> {
    const name=p.label||p.name||names[p.id]||p.text||"Pinned thing";
    const key=p.icon||icons[name.toLowerCase()]|| (p.does?"app-window":"pin");
    const run=p.does||`window.open thing ${p.shows||p.id}`;
    const b=chip(name,icon(key),run,p.slot|| (p.does?"btn":"pin"));
    if(p.slot)b.id=p.slot;
    if(p.confirm==="yes") {
      // Confirmation is data on the button, so a one-line button can request it.
      const safe=el("button",{cls:b.className,id:p.slot,title:name+" · click twice","aria-label":name,on:{click:()=>{
        if(safe.classList.contains("ask")){doLine(run);return;}
        safe.classList.add("ask");safe.title="Click again to confirm";setTimeout(()=>{safe.classList.remove("ask");safe.title=name+" · click twice";},4000);
      }}},el("img",{src:icon(key),alt:""}));return safe;
    }
    return b;
  };
  document.getElementById("shell").replaceChildren(...pinRows.filter(p=>["start","agora"].includes(p.slot)).map(paint));
  document.getElementById("off-slot").replaceChildren(...pinRows.filter(p=>p.slot==="off").map(paint));
  pinButtons=pinRows.filter(p=>!p.slot&&p.kind!=="widget").map(paint);
  document.getElementById("pins").replaceChildren(...pinButtons);
  document.getElementById("clock-slot").replaceChildren(...pinRows.filter(p=>p.slot==="clock").map(p=>el("button",{cls:"clock",id:"clock",title:"Date and time",on:{click:()=>p.does&&doLine(p.does)}})));
  clock();tray();holds();
}
async function wins() {
  if(windowsBusy)return; windowsBusy=true;
  try {
    const [a,b]=await Promise.all([see("window.list"),see("window.desktop")]);
    const agora=(a.rows||[]).filter(w=>w.kind==="window"&&w.shows!=="taskbar"&&!w.edge).sort((a,b)=>a.id.localeCompare(b.id,undefined,{numeric:true}));
    const native=(b.rows||[]).filter(w=>w.kind!=="pin-icon");
    const tasks=[...agora.map(w=>chip(w.name,icon(icons[w.shows]||"app-window"),`window.focus ${w.id}`,`running ${w.front?"front":""} ${w.shown?"":"tucked"}`)),
      ...native.map(w=>chip(`${w.name} · ${w.program}`,w.icon||icon("app-window"),`window.activate handle=${w.handle}`,`running ${w.front?"front":""} ${w.shown?"":"tucked"}`))];
    document.getElementById("wins").replaceChildren(...tasks);
    requestAnimationFrame(fit);
    for(const p of (b.rows||[]).filter(w=>w.kind==="pin-icon")) {
      const i=pinRows.filter(p=>!p.slot&&p.kind!=="widget").findIndex(x=>x.id===p.id); const image=document.querySelectorAll("#pins img")[i];if(image&&p.icon)image.src=p.icon;
    }
  } finally {windowsBusy=false;}
}
function fit() {
  const pinned=document.getElementById("pins");
  pinned.replaceChildren(...pinButtons);
  if(pinned.scrollWidth>pinned.clientWidth+1) {
    const width=innerWidth<=900?29:39;
    const capacity=Math.max(0,Math.floor(pinned.clientWidth/width)-1);
    pinButtons.slice(capacity).forEach(b=>b.remove());
    pinned.append(chip("All pinned things",icon("pin"),"window.open tasks"));
  }
  const box=document.getElementById("wins"), all=[...box.children];
  if(!all.length)return;
  const width=Math.max(22,Math.min(34,(box.clientWidth-5*(all.length-1))/all.length));
  for(const b of all)b.style.width=`${width}px`;
  if(box.scrollHeight>box.clientHeight+2) {
    for(const b of all)b.style.width="22px";
    const capacity=Math.max(0,Math.floor(box.clientWidth/27)-1);
    if(all.length>capacity) {
      all.slice(capacity).forEach(b=>b.remove());
      box.append(el("button",{cls:"chip",title:`${all.length-capacity} more windows`,"aria-label":"All running windows",on:{click:()=>doLine("window.open tasks")}},el("img",{src:icon("layout-grid"),alt:""})));
    }
  }
}
async function tray() {
  const r=await see("system.now");const readings=r.rows||[];
  document.getElementById("tray").replaceChildren(...pinRows.filter(p=>p.kind==="widget"&&p.side==="right").flatMap(p=>{
    const key=p.shows;
    const x=readings.find(x=>x.key===key);if(!x||!x.value)return [];
    return [chip(`${p.label||key}: ${x.value} ${x.detail||""}`,icon(p.icon||icons[key]||"app-window"),p.does||`window.open thing ${p.id}`)];
  }));
}
async function holds() {
  const widget=pinRows.find(p=>p.slot==="holds");
  const r=widget?await see("holds"):{rows:[]};document.getElementById("holds").replaceChildren(...(r.rows||[]).map(h=>
    el("span",{cls:"hold",title:`${h.by} holds ${h.word}`},el("img",{src:icon(widget.icon||"hand"),alt:""}))));
}
function clock() {const d=new Date(),c=document.getElementById("clock");if(!c)return;c.textContent=d.toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"});c.title=d.toLocaleDateString([],{weekday:"long",day:"numeric",month:"long"})+" · Date and time settings";}
let timer;KD.stream(h=>{if(["hello","world","hold.began","hold.ended","window.opened"].includes(h.word)){clearTimeout(timer);timer=setTimeout(()=>{pins();wins();holds();},120);}});
clock();pins();wins();holds();tray();setInterval(clock,1000);setInterval(wins,2500);setInterval(tray,4000);addEventListener("resize",fit);
