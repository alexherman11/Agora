// Map components for the component painter. One module serves six names (it branches on api.node.component):
//   map-shell      the window: the map full-bleed, everything else floating beside it
//   geo-map        the surface (geo-engine.js draws it); fires add, move, route
//   map-layers     layers with your own show/hide, the ground's own layers, and a new-layer form; fires hide, unhide, make
//   map-search     names on the map (map.find); choosing one flies there
//   map-inspector  what you pressed: its facts, where it is, what is near; fires edit, forget, add
//   map-route      the route planner while the route tool is on; fires route
// Everything they change goes through the lens's gesture lines, so a community can change what each press does.
// Built by install.py as: geo-worker.js + geo-engine.js + this file.

const MAP_CSS=`
.gm-shell{position:relative;width:100%;height:100vh;overflow:hidden;background:var(--paper,#f4f1ea);font:14px/1.45 var(--ag-font,system-ui,sans-serif);color:var(--ink,#26302c)}
.gm-shell>.gm-stage{position:absolute;inset:0;z-index:0;isolation:isolate}
.gm-shell>.gm-side{position:absolute;top:12px;left:12px;bottom:12px;width:min(340px,calc(100% - 24px));display:flex;flex-direction:column;gap:10px;pointer-events:none;z-index:5}
.gm-shell>.gm-side>*{pointer-events:auto}
.gm-shell>.gm-side .gm-scroll{overflow:auto;display:flex;flex-direction:column;gap:10px;min-height:0;padding-bottom:4px;scrollbar-width:thin}
.gm-shell.gm-folded>.gm-side .gm-scroll{display:none}
.gm-fold{align-self:flex-start;border:0;border-radius:999px;padding:6px 12px;background:var(--card,#fff);color:inherit;box-shadow:0 2px 10px #1f2a2422;font:inherit;font-size:12px;cursor:pointer}
.gm-card{background:color-mix(in srgb,var(--card,#fff) 94%,transparent);backdrop-filter:blur(8px);border:1px solid color-mix(in srgb,var(--ink,#26302c) 10%,transparent);border-radius:14px;box-shadow:0 6px 24px #1f2a2418;padding:12px 14px}
.gm-card h3{margin:0 0 8px;font-size:12px;letter-spacing:.07em;text-transform:uppercase;color:var(--muted,#5f6b66);font-weight:650}
.gm-root{position:relative;width:100%;height:100%;overflow:hidden;background:linear-gradient(180deg,var(--gm-sky-top,#9fd2ec),var(--gm-sky-mid,#d3ebf3) 38%,var(--gm-sky-low,#eef2ea) 62%);touch-action:none;user-select:none}
.gm-canvas{position:absolute;inset:0;width:100%;height:100%;outline:none;cursor:grab}
.gm-canvas:active{cursor:grabbing}
.gm-root[data-tool=add] .gm-canvas,.gm-root[data-tool=route] .gm-canvas{cursor:crosshair}
.gm-canvas:focus-visible{box-shadow:inset 0 0 0 3px #2f7f8f88}
.gm-overlay{position:absolute;inset:0;pointer-events:none;overflow:hidden}
.gm-street{position:absolute;left:0;top:0;white-space:nowrap;font-size:11.5px;font-weight:600;letter-spacing:.02em;color:#4a4036;text-shadow:0 0 3px #fffdf7,0 0 3px #fffdf7,0 0 6px #fffdf7;transform-origin:0 0}
.gm-place{position:absolute;left:0;top:0;display:flex;align-items:center;gap:4px;white-space:nowrap;font-size:11.5px;color:#3c3a33;text-shadow:0 0 3px #fffdf7,0 0 3px #fffdf7;pointer-events:auto;cursor:pointer;transform-origin:0 0}
.gm-place i{width:8px;height:8px;border-radius:50%;background:#9a8f80;box-shadow:0 0 0 2px #fffdf7}
.gm-place[data-cat=food] i{background:#d0603f}.gm-place[data-cat=nature] i{background:#4f9a4a}.gm-place[data-cat=community] i{background:#3f78b5}
.gm-place[data-cat=shop] i{background:#8a63b8}.gm-place[data-cat=move] i{background:#6d7680}
.gm-place:hover span{text-decoration:underline}
.gm-pin{position:absolute;left:0;top:0;width:0;height:0;padding:0;border:0;background:none;pointer-events:auto;cursor:pointer;font:inherit;font-size:14px}
.gm-pin-head{position:absolute;left:-.82em;top:-2.3em;width:1.64em;height:1.64em;border-radius:50% 50% 50% 0;transform:rotate(-45deg);background:currentColor;box-shadow:0 0 0 .16em #fff,0 3px 8px #0004;transition:transform .15s}
.gm-pin-head::after{content:"";position:absolute;inset:.45em;border-radius:50%;background:#fff}
.gm-pin-shadow{position:absolute;left:-.45em;top:-.18em;width:.9em;height:.36em;border-radius:50%;background:#0003;filter:blur(1px)}
.gm-pin-label{position:absolute;left:50%;top:.35em;transform:translateX(-50%);white-space:nowrap;font-size:12px;font-weight:650;color:#2b2a26;background:#fffdf8ee;border-radius:6px;padding:1px 6px;box-shadow:0 1px 4px #0002;display:none}
.gm-pin:hover .gm-pin-label,.gm-pin:focus-visible .gm-pin-label,.gm-pin.gm-near .gm-pin-label,.gm-pin.gm-selected .gm-pin-label{display:block}
.gm-pin:hover .gm-pin-head,.gm-pin.gm-selected .gm-pin-head{transform:rotate(-45deg) scale(1.18)}
.gm-pin.gm-selected .gm-pin-head{box-shadow:0 0 0 .16em #fff,0 0 0 .42em color-mix(in srgb,currentColor 35%,transparent),0 3px 10px #0005}
.gm-pin:focus-visible{outline:none}.gm-pin:focus-visible .gm-pin-head{box-shadow:0 0 0 .16em #fff,0 0 0 .4em #2f7f8f}
.gm-pin.gm-approx .gm-pin-head{background:repeating-linear-gradient(45deg,currentColor 0 4px,color-mix(in srgb,currentColor 55%,#fff) 4px 7px)}
.gm-pin.gm-dragging{z-index:99999!important}.gm-pin.gm-dragging .gm-pin-head{transform:rotate(-45deg) scale(1.3) translate(.2em,-.2em)}
.gm-pin.gm-look-dot .gm-pin-head{left:-.45em;top:-.45em;width:.9em;height:.9em;border-radius:50%;transform:none}.gm-pin.gm-look-dot .gm-pin-head::after{display:none}.gm-pin.gm-look-dot .gm-pin-shadow{display:none}
.gm-pin.gm-look-flag .gm-pin-head{left:0;top:-1.9em;width:1.15em;height:.75em;border-radius:1px 5px 5px 1px;transform:none}.gm-pin.gm-look-flag .gm-pin-head::after{display:none}.gm-pin.gm-look-flag::before{content:"";position:absolute;left:-.08em;top:-1.95em;width:.16em;height:1.95em;background:#3e3a33;border-radius:1px}.gm-pin.gm-look-flag .gm-pin-shadow{left:-.3em;width:.6em}.gm-pin.gm-look-flag:hover .gm-pin-head,.gm-pin.gm-look-flag.gm-selected .gm-pin-head{transform:scale(1.15)}
.gm-pin.gm-look-label .gm-pin-head,.gm-pin.gm-look-label .gm-pin-shadow{display:none}.gm-pin.gm-look-label .gm-pin-label{display:block;top:-.7em;color:currentColor}
@media (prefers-reduced-motion:no-preference){.gm-pin{animation:gm-drop .38s cubic-bezier(.3,1.5,.6,1) both}@keyframes gm-drop{from{opacity:0;margin-top:-18px}to{opacity:1;margin-top:0}}}
.gm-tip{position:absolute;left:0;top:0;background:#26302cee;color:#fff;font-size:12px;padding:3px 8px;border-radius:6px;white-space:nowrap;pointer-events:none}
.gm-stop{position:absolute;left:0;top:0;width:22px;height:22px;margin:-11px 0 0 -11px;border-radius:50%;background:#2f7f8f;color:#fff;font-size:11px;font-weight:700;display:grid;place-items:center;box-shadow:0 0 0 3px #fff,0 2px 6px #0004}
.gm-draft{position:absolute;left:0;top:0;pointer-events:auto;transform-origin:0 0}
.gm-draft form{position:absolute;left:-130px;top:14px;width:260px;background:var(--card,#fff);color:var(--ink,#26302c);border-radius:12px;padding:10px;box-shadow:0 8px 28px #0003;display:flex;flex-direction:column;gap:8px}
.gm-draft input{font:inherit;padding:7px 9px;border-radius:8px;border:1px solid #d8d2c6;background:var(--paper,#fff);color:inherit}
.gm-draft .gm-row{display:flex;gap:6px;justify-content:flex-end}
.gm-btn{font:inherit;font-size:13px;border-radius:9px;border:1px solid color-mix(in srgb,var(--ink,#26302c) 18%,transparent);background:var(--card,#fff);color:inherit;padding:6px 11px;cursor:pointer}
.gm-btn:hover{background:color-mix(in srgb,var(--ink,#26302c) 6%,var(--card,#fff))}
.gm-btn.gm-primary{background:#2f6f62;border-color:#2f6f62;color:#fff}.gm-btn.gm-primary:hover{background:#285f54}
.gm-btn:focus-visible{outline:2px solid #2f7f8f;outline-offset:2px}
.gm-hud{position:absolute;inset:0;pointer-events:none}
.gm-hud>*{pointer-events:auto}
.gm-tools{position:absolute;top:12px;left:50%;transform:translateX(-50%);display:flex;gap:2px;background:var(--card,#fff);border-radius:999px;padding:3px;box-shadow:0 4px 16px #1f2a2426}
.gm-tools button{border:0;background:transparent;color:inherit;font:inherit;font-size:13px;padding:6px 13px;border-radius:999px;cursor:pointer}
.gm-tools button[aria-pressed=true]{background:#2f6f62;color:#fff}
.gm-hint{position:absolute;top:56px;left:50%;transform:translateX(-50%);background:#26302cdd;color:#fff;font-size:12.5px;padding:5px 12px;border-radius:999px;white-space:nowrap}
.gm-nav{position:absolute;right:14px;bottom:44px;display:flex;flex-direction:column;gap:6px}
.gm-nav button{width:38px;height:38px;border-radius:12px;border:0;background:var(--card,#fff);color:inherit;box-shadow:0 3px 12px #1f2a2426;font:600 18px/1 system-ui;cursor:pointer;display:grid;place-items:center}
.gm-nav button:focus-visible{outline:2px solid #2f7f8f}
.gm-compass svg{transition:transform .1s}
.gm-foot{position:absolute;right:12px;bottom:10px;display:flex;align-items:center;gap:10px;font-size:11px;color:#3e3a33}
.gm-scale{height:6px;border:2px solid #3e3a33;border-top:0;min-width:20px}
.gm-scale-wrap{display:flex;align-items:center;gap:6px;background:#fffdf8cc;padding:2px 8px;border-radius:6px}
.gm-attrib{background:#fffdf8cc;padding:2px 8px;border-radius:6px}
.gm-status{position:absolute;inset:0;display:grid;place-items:center;font-size:15px;color:#3e3a33;pointer-events:none}
.gm-status span{background:#fffdf8e6;padding:10px 18px;border-radius:12px;box-shadow:0 4px 18px #0002}
.gm-more{all:unset;cursor:pointer;padding:0 6px;border-radius:6px;color:var(--muted,#5f6b66);font-size:15px;line-height:1}.gm-more:hover,.gm-more:focus-visible{background:color-mix(in srgb,var(--ink,#26302c) 8%,transparent)}
.gm-layer{display:grid;grid-template-columns:auto auto 1fr auto auto;align-items:center;gap:8px;padding:5px 2px;border-radius:8px}
.gm-layer:hover{background:color-mix(in srgb,var(--ink,#26302c) 5%,transparent)}
.gm-layer input{accent-color:#2f6f62;width:16px;height:16px;margin:0}
.gm-swatch{width:12px;height:12px;border-radius:50%;box-shadow:inset 0 0 0 1px #0002}
.gm-count{font-size:12px;color:var(--muted,#5f6b66);font-variant-numeric:tabular-nums}
.gm-err{grid-column:2/-1;font-size:12px;color:#a2402a}
.gm-sub{font-size:12px;color:var(--muted,#5f6b66);margin:10px 0 4px;text-transform:uppercase;letter-spacing:.06em}
.gm-form{display:flex;flex-direction:column;gap:8px;margin-top:8px}
.gm-form label{display:flex;flex-direction:column;gap:3px;font-size:12px;color:var(--muted,#5f6b66)}
.gm-form input,.gm-form select{font:inherit;font-size:13px;padding:6px 8px;border-radius:8px;border:1px solid #d8d2c6;background:var(--paper,#fff);color:var(--ink,#26302c)}
.gm-chips{display:flex;gap:6px;flex-wrap:wrap}.gm-chips button{width:22px;height:22px;border-radius:50%;border:2px solid #fff;box-shadow:0 0 0 1px #0002;cursor:pointer}
.gm-chips button[aria-pressed=true]{box-shadow:0 0 0 2px #26302c}
.gm-search{position:relative}
.gm-search input{width:100%;box-sizing:border-box;font:inherit;font-size:14px;padding:10px 12px 10px 34px;border-radius:12px;border:1px solid transparent;background:var(--card,#fff);color:inherit;box-shadow:0 6px 24px #1f2a2418}
.gm-search input:focus{outline:2px solid #2f7f8f}
.gm-search svg{position:absolute;left:11px;top:12px;opacity:.55}
.gm-results{margin-top:6px;display:flex;flex-direction:column;background:var(--card,#fff);border-radius:12px;box-shadow:0 6px 24px #1f2a2418;overflow:hidden}
.gm-results button{all:unset;display:grid;grid-template-columns:1fr auto;gap:8px;padding:8px 12px;cursor:pointer;font-size:13.5px}
.gm-results button:hover,.gm-results button:focus-visible{background:color-mix(in srgb,#2f7f8f 12%,transparent)}
.gm-results small{color:var(--muted,#5f6b66)}
.gm-facts{display:grid;grid-template-columns:auto 1fr;gap:3px 12px;font-size:12.5px;margin:8px 0}
.gm-facts dt{color:var(--muted,#5f6b66)}.gm-link{all:unset;cursor:pointer;color:#2f6f62;text-decoration:underline;text-underline-offset:2px}.gm-link:focus-visible{outline:2px solid #2f7f8f}.gm-facts dd{margin:0;overflow-wrap:anywhere}
.gm-title{font-size:17px;font-weight:700;margin:0;display:flex;align-items:center;gap:8px}
.gm-where{color:var(--muted,#5f6b66);font-size:13px;margin:3px 0 8px}
.gm-actions{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.gm-line{font:11.5px/1.4 ui-monospace,Consolas,monospace;color:var(--muted,#5f6b66);margin-top:8px;overflow-wrap:anywhere}
.gm-near{display:flex;flex-direction:column;gap:2px;margin-top:6px}
.gm-near button{all:unset;cursor:pointer;font-size:13px;display:flex;justify-content:space-between;gap:8px;padding:3px 4px;border-radius:6px}
.gm-near button:hover{background:color-mix(in srgb,var(--ink,#26302c) 6%,transparent)}
.gm-stops{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:4px;counter-reset:s}
.gm-stops li{display:grid;grid-template-columns:22px 1fr auto;gap:8px;align-items:center;font-size:13px}
.gm-stops li::before{counter-increment:s;content:counter(s);width:20px;height:20px;border-radius:50%;background:#2f7f8f;color:#fff;display:grid;place-items:center;font-size:11px;font-weight:700}
.gm-stops button{all:unset;cursor:pointer;color:var(--muted,#5f6b66);padding:0 4px}
.gm-seg{display:flex;gap:2px;background:color-mix(in srgb,var(--ink,#26302c) 7%,transparent);border-radius:999px;padding:2px;width:max-content}
.gm-seg button{border:0;background:transparent;color:inherit;font:inherit;font-size:12.5px;padding:4px 11px;border-radius:999px;cursor:pointer}
.gm-seg button[aria-pressed=true]{background:var(--card,#fff);box-shadow:0 1px 3px #0002}
.gm-big{font-size:22px;font-weight:700;font-variant-numeric:tabular-nums}
.gm-empty{font-size:13px;color:var(--muted,#5f6b66)}
.gm-empty code{font:12px ui-monospace,Consolas,monospace;background:color-mix(in srgb,var(--ink,#26302c) 7%,transparent);padding:1px 4px;border-radius:4px}
@media (max-width:700px){.gm-shell>.gm-side{top:auto;left:8px;right:8px;bottom:8px;width:auto;max-height:46vh}.gm-tools{top:8px}.gm-nav{bottom:auto;top:60px;right:8px}}
@media (prefers-color-scheme:dark){.gm-street{color:#e4ddcf;text-shadow:0 0 3px #1c211f,0 0 3px #1c211f,0 0 6px #1c211f}.gm-place{color:#e6e1d6;text-shadow:0 0 3px #1c211f,0 0 3px #1c211f}.gm-place i{box-shadow:0 0 0 2px #1c211f}.gm-scale-wrap,.gm-attrib{background:#1c211fcc;color:#d8d2c6}.gm-scale{border-color:#d8d2c6}.gm-status{color:#e6e1d6}.gm-status span{background:#1c211fe6}}
`;

const MAP_LAYER_COLOURS=['#cf5a3c','#2f7f8f','#6c5bb3','#d39a2c','#4f9a4a','#c2477c','#3f78b5','#7a6a58'];
const MAP_SHOWS=[['Spots','rows spot'],['Events','rows event'],['Routes','rows route'],['Carpools','rows carpool'],['Offers of help','rows offer'],['Asks for help','rows ask']];
const mapQ=s=>'"'+String(s).replace(/\\/g,'\\\\').replace(/"/g,'\\"')+'"';
const mapEl=(tag,attrs={},...kids)=>{const n=document.createElement(tag);for(const [k,v] of Object.entries(attrs||{})){if(v==null||v===false)continue;if(k==='on')for(const [e,f] of Object.entries(v))n.addEventListener(e,f);else if(k==='style'&&typeof v==='object')Object.assign(n.style,v);else if(k==='text')n.textContent=v;else n.setAttribute(k,v===true?'':v)}for(const c of kids.flat())if(c!=null&&c!==false)n.append(c.nodeType?c:document.createTextNode(String(c)));return n};
function mapDark(){try{const v=getComputedStyle(document.documentElement).getPropertyValue('--paper').trim()||getComputedStyle(document.body).backgroundColor;const c=document.createElement('canvas').getContext('2d');c.fillStyle=v;const h=c.fillStyle;if(!/^#/.test(h))return false;const n=parseInt(h.slice(1),16);return ((n>>16&255)*0.3+(n>>8&255)*0.59+(n&255)*0.11)<110}catch{return false}}
// View state holds plain values only (the broker refuses objects), so selection, stops and focus travel as JSON text.
function mapView(api){const v=api.view();const j=(x,d)=>{if(x&&typeof x==='object')return x;try{return x?JSON.parse(x):d}catch{return d}};return {tool:v.tool||'look',mode:v.mode||'walk',stops:j(v.stops,[]),selected:j(v.selected,null),focus:j(v.focus,null)}}
const mapJ=v=>v==null?'':JSON.stringify(v);
// The frame has no allow-forms: a form's submit never fires, so the painter's P.submit handles Enter and the submit button.
function mapForm(api,attrs,fn,...kids){const f=mapEl('form',attrs,...kids);api.P.submit(f,fn);return f}
function mapName(t){return t?.title||t?.name||t?.label||t?.text||t?.id||''}
function mapReadLayers(api,map){return api.read('map.layers '+mapQ(map)).then(rows=>Array.isArray(rows)?rows:(rows?.rows||[]))}
function mapLineOf(api,event){const g=(api.node.gestures||[]).find(g=>g.event===event);return g?g.line:''}
async function mapFire(api,event,values,okText){try{await api.fire(event,values);if(okText)api.tell(okText)}catch(e){api.tell(String(e?.message||e).split('\n')[0])}}

// ---- map-shell -----------------------------------------------------------------------------------------------------
function mountShell(api){
  const root=api.part('shell','div',{class:'gm-shell'});
  const stage=mapEl('div',{class:'gm-stage'}),side=mapEl('div',{class:'gm-side'}),scroll=mapEl('div',{class:'gm-scroll'});
  const folded=!!api.draft.folded;root.classList.toggle('gm-folded',folded);
  const fold=mapEl('button',{type:'button',class:'gm-fold','aria-expanded':String(!folded),on:{click:()=>{api.draft.folded=!api.draft.folded;root.classList.toggle('gm-folded',api.draft.folded);fold.textContent=api.draft.folded?'Show panels':'Hide panels';fold.setAttribute('aria-expanded',String(!api.draft.folded))}}},folded?'Show panels':'Hide panels');
  for(const child of api.children){
    if(child.component==='geo-map')stage.append(api.render(child));
    else if(child.name==='search'||child.component==='map-search')side.append(api.render(child));
    else scroll.append(api.render(child));
  }
  side.append(fold,scroll);root.append(stage,side);return root;
}

// ---- geo-map ---------------------------------------------------------------------------------------------------------
function mountGeoMap(api,settings){
  const d=api.draft;if(!d.engine)d.engine=new GeoEngine(String(geoWorkerMain));const E=d.engine;
  E.canvas.__engine=E;      // for measuring in tests (the page is sandboxed; nothing outside it can reach this)
  const view=mapView(api);const map=settings.map||'';
  const root=api.part('surface','div',{class:'gm-root',role:'application','aria-label':'Map of '+map});
  root.dataset.tool=view.tool||'look';
  E.attach(root,api);
  E.tool=view.tool;
  // stops: this map's own presses are newer than a repaint still carrying an older list; anything else (the planner's x,
  // Route from here, Cancel) is taken from the view
  {const vs=JSON.stringify(Array.isArray(view.stops)?view.stops:[]);E.sent=E.sent||new Set();
    const ours=vs===E.lastSent||(E.sent.has(vs)&&performance.now()-(E.sentAt||0)<2000);if(!ours)E.stops=JSON.parse(vs)}
  E.selectedId=view.selected?.thing||'';E.sel=view.selected?.pick||0;
  E.curve=settings.curve===undefined?2400:Number(settings.curve)||0;
  // the HUD: tools, hint, navigation, scale and attribution
  const hud=mapEl('div',{class:'gm-hud'});
  const tools=mapEl('div',{class:'gm-tools',role:'toolbar','aria-label':'Map tools'});
  for(const [tool,label] of [['look','Look'],['add','Add a spot'],['route','Plan a route']])
    tools.append(mapEl('button',{type:'button','aria-pressed':String(E.tool===tool),on:{click:()=>{E.draft=null;E.draftEl?.remove();E.tool=tool;root.dataset.tool=tool;if(tool!=='route')E.stops=[];api.select({tool,stops:mapJ(tool==='route'?E.stops:[])})}}},label));
  const hints={add:'Press the map where the spot is. Esc to stop.',route:E.stops.length?'Press the map to add stops; save from the planner.':'Press the map, or a pin, for the first stop.'};
  hud.append(tools);if(hints[E.tool])hud.append(mapEl('div',{class:'gm-hint',role:'status'},hints[E.tool]));
  const needle=mapEl('span',{},'');needle.innerHTML='<svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true"><path d="M10 2 L13 10 L10 9 L7 10Z" fill="#cf5a3c"/><path d="M10 18 L13 10 L10 11 L7 10Z" fill="#8a8378"/></svg>';
  const nav=mapEl('div',{class:'gm-nav'},
    mapEl('button',{type:'button','aria-label':'Zoom in',on:{click:()=>E.flyTo({dist:E.cam.dist*0.6},300)}},'+'),
    mapEl('button',{type:'button','aria-label':'Zoom out',on:{click:()=>E.flyTo({dist:E.cam.dist/0.6},300)}},'−'),
    mapEl('button',{type:'button',class:'gm-compass','aria-label':'Face north',on:{click:()=>E.flyTo({bearing:0},450)}},needle),
    mapEl('button',{type:'button','aria-label':'Tilt or flatten the map',style:{fontSize:'12px'},on:{click:()=>E.flyTo({pitch:E.cam.pitch>8?0:48},500)}},E.cam.pitch>8?'2D':'3D'));
  const scale=mapEl('span',{class:'gm-scale'}),scaleText=mapEl('span',{},'');
  const foot=mapEl('div',{class:'gm-foot'},mapEl('span',{class:'gm-scale-wrap'},scale,scaleText),mapEl('span',{class:'gm-attrib'},E.data?.attribution||'© OpenStreetMap contributors · ODbL'));
  const status=mapEl('div',{class:'gm-status',role:'status'});
  hud.append(nav,foot,status);root.append(hud);
  const showStatus=()=>{status.replaceChildren(E.status?mapEl('span',{},E.status):'')};showStatus();
  // a frame also moves the compass, the scale and the overlay extras (the spot being placed, the route's stops)
  E.overlayExtras=()=>{
    needle.firstChild.style.transform=`rotate(${-E.cam.bearing}deg)`;
    const a=E.ground(E.w/2,E.h*0.62),b=E.ground(E.w/2+100,E.h*0.62);
    if(a&&b){const m=Math.hypot(a[0]-b[0],a[1]-b[1]);const nice=[10,20,50,100,200,250,500,1000,2000].find(n=>n/m*100>=60)||2000;scale.style.width=(nice/m*100).toFixed(0)+'px';scaleText.textContent=nice>=1000?nice/1000+' km':nice+' m'}
    let stops=E._stopEls||(E._stopEls=[]);stops.forEach(s=>s.remove());E._stopEls=stops=[];
    E.stops.forEach((s,i)=>{const [x,y]=E.toXY(s.lat,s.lon);const p=E.project(x,y,0);if(!p)return;const el=mapEl('div',{class:'gm-stop',style:{transform:`translate(${p[0]}px,${p[1]}px)`}},String(i+1));E.overlay.append(el);stops.push(el)});
    if(E.draft&&E.draftEl){const [x,y]=E.toXY(E.draft.lat,E.draft.lon);const p=E.project(x,y,0);if(p)E.draftEl.style.transform=`translate(${p[0]}px,${p[1]}px)`}
  };
  // presses: what each does depends on the tool; anything that changes the world goes through a gesture line
  const select=sel=>{E.selectedId=sel?.thing||'';E.sel=sel?.pick||0;E.ask();return api.select({selected:mapJ(sel)})};
  const addStop=s=>{const stops=[...E.stops,s];E.stops=stops;const j=mapJ(stops);E.sent.add(j);E.lastSent=j;E.sentAt=performance.now();E.ask();return api.select({stops:j,tool:'route'})};
  E.onPress=p=>{
    const api2=E.api;if(api2!==api)return;          // only the newest mount answers
    const label=p.what?.name||p.text||(p.lat!=null?p.lat.toFixed(5)+', '+p.lon.toFixed(5):'');
    if(E.tool==='route'){if(p.lat==null&&p.x==null)return;const ll=p.lat!=null?[p.lat,p.lon]:E.toLL(p.x,p.y);addStop({label:label||'A point',lat:ll[0],lon:ll[1],ref:''});return}
    if(E.tool==='add'){if(p.lat==null)return;openDraft({lat:p.lat,lon:p.lon,name:['building','area','place'].includes(p.what?.type)?p.what.name:'',osm:p.what?.type==='street'?'':p.what?.id||''});return}
    if(p.type==='place'){select({kind:'ground',type:'place',name:p.what.name,what:p.what.what,address:p.what.address,osm:p.what.id,lat:p.lat,lon:p.lon});return}
    if(p.what)select({kind:'ground',type:p.what.type,name:p.what.name,what:p.what.what,address:p.what.address||'',h:p.what.h,hs:p.what.hs,osm:p.what.id,pick:p.pickId,lat:p.lat,lon:p.lon});
    else select(null);
  };
  E.onPin=(it)=>{
    if(E.api!==api)return;
    if(E.tool==='route'){addStop({label:mapName(it),lat:it.lat,lon:it.lon,ref:it.id});return}
    select({kind:'thing',thing:it.id,name:mapName(it),rev:it.rev,layer:it.layer?.name||''});
  };
  E.onMove=(it,lat,lon)=>{if(E.api!==api)return;mapFire(api,'move',{thing:it.id,lat:String(lat),lon:String(lon),saw:{[it.id]:it.rev}},'Moved '+mapName(it))};
  E.onEscape=()=>{if(E.api!==api)return;E.draft=null;E.draftEl?.remove();api.select({tool:'look',stops:'[]'})};
  // The new-thing form: a spot by default; an event too when the lens arranges an add-event gesture.
  function openDraft(dr){
    E.draft=dr;E.draftEl?.remove();dr.kind=dr.kind||'spot';
    const canEvent=(api.node.gestures||[]).some(g=>g.event==='add-event');
    const input=mapEl('input',{type:'text',placeholder:'What is here?','aria-label':'Name','value':dr.name||''});
    const when=mapEl('input',{type:'text',placeholder:'When? Sat 10am, tomorrow 6pm, 2026-11-02 18:00','aria-label':'When'});
    const whenSaid=mapEl('div',{class:'gm-line'});const runs=mapEl('div',{class:'gm-line'});
    const parse=()=>{const r=api.P.parseDateEntry?api.P.parseDateEntry(when.value):{ok:false};whenSaid.textContent=when.value.trim()?(r.ok?r.label:r.message||'Say a day and a time'):'';return r};
    when.addEventListener('input',parse);
    const submit=mapEl('button',{type:'submit',class:'gm-btn gm-primary'});
    const seg=mapEl('div',{class:'gm-seg',role:'group','aria-label':'What to add'});
    const setKind=k=>{dr.kind=k;seg.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.kind===k)));
      when.hidden=whenSaid.hidden=k!=='event';input.placeholder=k==='event'?'What is happening?':'What is here?';submit.textContent=k==='event'?'Add event':'Add spot';
      runs.textContent='runs: '+(mapLineOf(api,k==='event'?'add-event':'add')||'(this lens arranges no such gesture)')};
    for(const [k,label] of [['spot','A spot'],['event','An event']])seg.append(mapEl('button',{type:'button','data-kind':k,on:{click:()=>setKind(k)}},label));
    const form=mapForm(api,{},()=>{const name=input.value.trim();if(!name){input.focus();return}
      const d=E.draft;
      if(d.kind==='event'){const r=parse();if(!r.ok){when.focus();return}
        E.draft=null;E.draftEl?.remove();mapFire(api,'add-event',{title:name,start:r.iso,lat:String(d.lat),lon:String(d.lon),select:{tool:'look'}},'Added '+name);return}
      E.draft=null;E.draftEl?.remove();
      mapFire(api,'add',{name,lat:String(d.lat),lon:String(d.lon),osm:d.osm||'',select:{tool:'look'}},'Added '+name)},
      canEvent?seg:null,input,when,whenSaid,mapEl('div',{class:'gm-row'},mapEl('button',{type:'button',class:'gm-btn',on:{click:()=>{E.draft=null;E.draftEl.remove()}}},'Cancel'),submit),runs);
    setKind(dr.kind);
    E.draftEl=mapEl('div',{class:'gm-draft'},mapEl('div',{class:'gm-stop',style:{background:'#cf5a3c'}},'+'),form);E.overlay.append(E.draftEl);
    // place it now (not on the next frame), and open the form upward when the press is near the bottom
    {const [x,y]=E.toXY(dr.lat,dr.lon);E.matrices();const p=E.project(x,y,0);if(p){E.draftEl.style.transform=`translate(${p[0]}px,${p[1]}px)`;
      const fh=form.offsetHeight||190;if(p[1]+fh+24>E.h)form.style.top=(-fh-18)+'px';const fx=Math.max(8,Math.min(E.w-268,p[0]-130))-p[0];form.style.left=fx+'px'}}
    E.ask();setTimeout(()=>input.focus(),30);
  }
  if(E.draft&&!E.draftEl?.isConnected)openDraft(E.draft);
  // the data: the ground once, the layers every paint (a watched reading, so it is already here)
  mapReadLayers(api,map).then(api.guard(rows=>{
    const head=rows.find(r=>r.kind==='map');
    if(!head){E.status='No map called '+map+' here.';showStatus();return}
    if(head.ground_error){E.status=head.ground_error;showStatus()}
    E.setLayers(rows,head.hidden||settings.hide||'');
    if(!E.data&&!E.loadingGround&&head.ground){
      E.loadingGround=true;E.status='Drawing '+(head.name||'the map')+'…';showStatus();
      api.file(head.ground,'content').then(f=>f.blob.text()).then(text=>E.load(text,mapDark())).then(data=>{
        // GPU set-up is one-time and cannot be split below the part's 32 ms budget (see README, rough spots)
        try{E.initGL()}catch(err){E.status='The map could not start drawing: '+(err.message||err)}
        if(E.gl){E.upload(data);const c=head.centre?String(head.centre).split(',').map(Number):null;
          const f=c&&c.length===2&&c.every(Number.isFinite)?E.toXY(c[0],c[1]):[(data.bounds[0]+data.bounds[2])/2,(data.bounds[1]+data.bounds[3])/2];
          E.cam.x=f[0];E.cam.y=f[1];E.setLayers(E.layersRows||rows,E.hiddenText||'')}
        E.loadingGround=false;E.ask();const s=E.api?.node?E.root?.querySelector('.gm-status'):null;if(s)s.replaceChildren(E.status?mapEl('span',{},E.status):'');
      }).catch(err=>{E.loadingGround=false;E.loading=null;E.status=String(err?.message||err);const s=E.root?.querySelector('.gm-status');if(s)s.replaceChildren(mapEl('span',{},E.status))});
    }
    E.layersRows=rows;E.hiddenText=head.hidden||settings.hide||'';
    const fl=String(api.view().fly||'');if(fl&&fl!==E.lastFly&&E.data){E.lastFly=fl;const r=E.routes.find(r=>r.id===fl.split('@')[0]);if(r)E.flyAlong(geoParsePath(r.path).map(([la,lo])=>E.toXY(la,lo)))}
    // fly to a focus asked for in words (map.show) or chosen in search
    const f=String(head.focus||settings.focus||'');if(f&&f!==E.lastFocus&&E.data){E.lastFocus=f;const [ll]=f.split('@');const [la,lo]=ll.split(',').map(Number);if(Number.isFinite(la)){const [x,y]=E.toXY(la,lo);E.focusOn(x,y,Math.min(E.cam.dist,520))}}
    const vf=view.focus;if(vf&&vf.stamp!==E.lastViewFocus&&E.data){E.lastViewFocus=vf.stamp;const [x,y]=E.toXY(vf.lat,vf.lon);E.focusOn(x,y,Math.min(E.cam.dist,vf.dist||480))}
    // the route being planned: its street path as a preview
    const key=JSON.stringify(E.stops.map(s=>[s.lat,s.lon]))+(view.mode||'walk');
    if(E.tool==='route'&&E.stops.length>1){if(key!==E.previewKey){E.previewKey=key;api.read('map.path stops='+mapQ(E.stops.map(s=>s.ref||(s.lat.toFixed(6)+','+s.lon.toFixed(6))).join(' > '))+' mode='+(view.mode||'walk')+' map='+mapQ(map))
      .then(api.guard(r=>{const row=(Array.isArray(r)?r:r?.rows||[])[0];E.preview=row?geoParsePath(row.path):null;E.buildRoutes();E.ask()}),()=>{E.preview=null;E.buildRoutes();E.ask()})}}
    else if(E.preview){E.preview=null;E.previewKey='';E.buildRoutes()}
    E.ask();
  }),api.guard(err=>{E.status='The map words did not answer: '+String(err?.message||err).split('\n')[0];showStatus()}));
  return root;
}

// ---- map-layers ------------------------------------------------------------------------------------------------------
function mountLayers(api,settings){
  const card=api.part('layers','section',{class:'gm-card','aria-label':'Layers'});card.append(mapEl('h3',{},api.label('title','Layers')));
  const body=mapEl('div');card.append(body);
  // local toggles (an editor open, the new-layer form) repaint this card only: the painter skips identical plans
  const paint=rows=>{
    const list=mapEl('div',{role:'list'});body.replaceChildren(list);
    const head=rows.find(r=>r.kind==='map')||{};const hidden=new Set(String(head.hidden||'').split(/\s+/).filter(Boolean));
    const layers=rows.filter(r=>r.kind!=='map');
    if(!layers.length)list.append(mapEl('p',{class:'gm-empty'},'No layers yet. Make one below, or say ',mapEl('code',{},'make kind=map-layer map='+(head.name||settings.map)+' name=… shows="rows spot"')));
    for(const L of layers){
      const on=!hidden.has(L.id)&&L.on!=='no';
      const box=mapEl('input',{type:'checkbox',id:'gm-layer-'+L.id,'aria-label':'Show '+L.name,on:{change:()=>mapFire(api,box.checked?'unhide':'hide',{layer:L.id})}});box.checked=on;
      const row=mapEl('div',{class:'gm-layer',role:'listitem',title:'Shows: '+(L.shows||'')+(L.by?' · made by '+L.by:'')},
        box,mapEl('span',{class:'gm-swatch',style:{background:L.color||'#cf5a3c'}}),mapEl('label',{for:'gm-layer-'+L.id},L.name||L.id),
        mapEl('span',{class:'gm-count'},String(L.count||0)+(L.unplaced?' · '+L.unplaced+' without a place':'')));
      if(L.error)row.append(mapEl('span',{class:'gm-err'},L.error));
      list.append(row);
      const canEdit=(api.node.gestures||[]).some(g=>g.event==='edit-layer');
      if(canEdit){const more=mapEl('button',{type:'button',class:'gm-more','aria-label':'Change '+L.name,'aria-expanded':String(api.draft.editLayer===L.id),on:{click:()=>{api.draft.editLayer=api.draft.editLayer===L.id?'':L.id;paint(rows)}}},'⋯');row.append(more)}
      if(canEdit&&api.draft.editLayer===L.id){
        const name=mapEl('input',{type:'text',value:L.name||'','aria-label':'Layer name'}),shows=mapEl('input',{type:'text',value:L.shows||'','aria-label':'The reading it shows'});
        const look=mapEl('select',{'aria-label':'How it looks'});for(const [v,label] of [['pin','Pins'],['dot','Dots'],['label','Names only'],['path','Paths (routes)']])look.append(mapEl('option',{value:v,selected:(L.look||'pin')===v},label));
        let colour=L.color||'#cf5a3c';const chips=mapEl('div',{class:'gm-chips',role:'radiogroup','aria-label':'Colour'});
        for(const col of MAP_LAYER_COLOURS){const b=mapEl('button',{type:'button',role:'radio','aria-checked':String(col===colour),'aria-pressed':String(col===colour),'aria-label':col,style:{background:col},on:{click:()=>{colour=col;chips.querySelectorAll('button').forEach(x=>{x.setAttribute('aria-pressed',String(x===b));x.setAttribute('aria-checked',String(x===b))})}}});chips.append(b)}
        const form=mapForm(api,{class:'gm-form'},()=>{api.draft.editLayer='';mapFire(api,'edit-layer',{layer:L.id,fields:{name:name.value.trim()||L.name,shows:shows.value.trim()||L.shows,look:look.value,color:colour},saw:{[L.id]:L.rev}},'Changed '+(name.value.trim()||L.name))},
          mapEl('label',{},'Name',name),mapEl('label',{},'Shows',shows),mapEl('label',{},'Looks like',look),mapEl('label',{},'Colour',chips),
          mapEl('div',{class:'gm-actions'},mapEl('button',{type:'submit',class:'gm-btn gm-primary'},'Save'),
            (api.node.gestures||[]).some(g=>g.event==='forget-layer')?mapEl('button',{type:'button',class:'gm-btn',on:{click:()=>{api.draft.editLayer='';mapFire(api,'forget-layer',{layer:L.id,saw:{[L.id]:L.rev}},'Removed the layer. Undo brings it back.')}}},'Remove layer'):null),
          mapEl('div',{class:'gm-line'},'runs: '+mapLineOf(api,'edit-layer')));
        list.append(form);
      }
    }
    list.append(mapEl('div',{class:'gm-sub'},'The ground'));
    for(const [key,label] of [['buildings','Buildings'],['labels','Street names'],['places','Named places']]){
      const id='ground:'+key;const box=mapEl('input',{type:'checkbox',id:'gm-g-'+key,on:{change:()=>mapFire(api,box.checked?'unhide':'hide',{layer:key})}});box.checked=!hidden.has(id);
      list.append(mapEl('div',{class:'gm-layer'},box,mapEl('span',{class:'gm-swatch',style:{background:key==='buildings'?'#efcfa9':key==='labels'?'#fffdf8':'#4f9a4a'}}),mapEl('label',{for:'gm-g-'+key},label),mapEl('span')));
    }
    if((api.node.gestures||[]).some(g=>g.event==='make')){
      const open=!!api.draft.newLayer;const btn=mapEl('button',{type:'button',class:'gm-btn',style:{marginTop:'8px'},'aria-expanded':String(open),on:{click:()=>{api.draft.newLayer=!api.draft.newLayer;paint(rows)}}},open?'Close':'New layer');
      body.append(btn);
      if(open){
        const name=mapEl('input',{type:'text',required:true,placeholder:'Dog friendly'});const shows=mapEl('select',{});
        for(const [label,line] of MAP_SHOWS)shows.append(mapEl('option',{value:line},label+'  ·  '+line));
        shows.append(mapEl('option',{value:''},'Another reading…'));const custom=mapEl('input',{type:'text',placeholder:'rows spot tags=dogs',hidden:true});
        shows.addEventListener('change',()=>{custom.hidden=shows.value!==''});
        let colour=MAP_LAYER_COLOURS[layers.length%MAP_LAYER_COLOURS.length];const chips=mapEl('div',{class:'gm-chips',role:'radiogroup','aria-label':'Colour'});
        for(const c of MAP_LAYER_COLOURS){const b=mapEl('button',{type:'button',role:'radio','aria-checked':String(c===colour),'aria-pressed':String(c===colour),'aria-label':c,style:{background:c},on:{click:()=>{colour=c;chips.querySelectorAll('button').forEach(x=>{const on=x===b;x.setAttribute('aria-pressed',String(on));x.setAttribute('aria-checked',String(on))})}}});chips.append(b)}
        const form=mapForm(api,{class:'gm-form'},()=>{const reading=shows.value||custom.value.trim();if(!name.value.trim()||!reading)return;
          api.draft.newLayer=false;mapFire(api,'make',{name:name.value.trim(),shows:reading,color:colour,look:'pin'},'Made the layer '+name.value.trim())},
          mapEl('label',{},'Name',name),mapEl('label',{},'Shows',shows,custom),mapEl('label',{},'Colour',chips),
          mapEl('button',{type:'submit',class:'gm-btn gm-primary'},'Make layer'),mapEl('div',{class:'gm-line'},'runs: '+mapLineOf(api,'make')));
        body.append(form);
      }
    }
  };
  mapReadLayers(api,settings.map||'').then(api.guard(paint),api.guard(err=>body.append(mapEl('p',{class:'gm-err'},String(err?.message||err)))));
  return card;
}

// ---- map-search ------------------------------------------------------------------------------------------------------
function mountSearch(api,settings){
  const box=api.part('search','div',{class:'gm-search'});
  const d=api.draft;const input=mapEl('input',{type:'search',placeholder:api.label('placeholder','Search streets, places, spots'),'aria-label':'Search the map',value:d.text||''});
  const icon=mapEl('span');icon.innerHTML='<svg width="15" height="15" viewBox="0 0 16 16" aria-hidden="true"><circle cx="7" cy="7" r="5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M11 11l4 4" stroke="currentColor" stroke-width="2"/></svg>';
  const results=mapEl('div',{class:'gm-results',role:'listbox',hidden:!(d.rows&&d.rows.length)});
  const choose=r=>{d.rows=[];results.hidden=true;const stamp=Date.now();
    const sel=r.id?{kind:'thing',thing:r.id,name:r.name}:{kind:'ground',type:'place',name:r.name,what:r.what,address:r.address||'',osm:r.osm,lat:r.lat,lon:r.lon};
    api.select({focus:mapJ({lat:r.lat,lon:r.lon,stamp}),selected:mapJ(sel)})};
  const show=rows=>{d.rows=rows;results.replaceChildren(...rows.map(r=>mapEl('button',{type:'button',role:'option',on:{click:()=>choose(r)}},mapEl('span',{},r.name),mapEl('small',{},String(r.what||'').replace(/^shop:/,'').replace(/_/g,' ')))));
    results.hidden=!rows.length};
  if(d.rows)show(d.rows);
  let timer;input.addEventListener('input',()=>{d.text=input.value;clearTimeout(timer);const text=input.value.trim();if(text.length<2){show([]);return}
    timer=setTimeout(()=>api.rows('map.find '+text.replace(/[;\n]/g,' ')+' map='+mapQ(settings.map||'')).then(api.guard(rows=>{if(input.value.trim()===text)show(rows)}),()=>show([])),180)});
  input.addEventListener('keydown',e=>{if(e.key==='Enter'&&d.rows?.length){e.preventDefault();choose(d.rows[0])}if(e.key==='Escape'){input.value='';d.text='';show([])}});
  box.append(icon,input,results);return box;
}

// ---- map-inspector ---------------------------------------------------------------------------------------------------
function mountInspector(api,settings){
  const card=api.part('inspector','section',{class:'gm-card','aria-label':'Selected on the map','aria-live':'polite'});
  const sel=mapView(api).selected;
  if(!sel){
    card.append(mapEl('h3',{},'On the map'),mapEl('p',{class:'gm-empty'},'Press a pin, a building, a street or a park. Drag a pin to move it. ',
      'Everything here is also a line: ',mapEl('code',{},'map.find Seabright & Murray'),', ',mapEl('code',{},'map.near "Java Junction"'),'.'));
    return card;
  }
  const actions=mapEl('div',{class:'gm-actions'}),lines=mapEl('div',{class:'gm-line'});
  const close=mapEl('button',{type:'button',class:'gm-btn','aria-label':'Close',style:{marginLeft:'auto',padding:'2px 8px'},on:{click:()=>api.select({selected:''})}},'×');
  const routeFrom=(label,lat,lon,ref)=>mapEl('button',{type:'button',class:'gm-btn',on:{click:()=>api.select({tool:'route',stops:mapJ([{label,lat,lon,ref:ref||''}])})}},'Route from here');
  if(sel.kind==='ground'){
    const title=sel.name||(sel.address)||({building:'A building',street:'A street',area:'An area',place:'A place'}[sel.type]||'Here');
    card.append(mapEl('h3',{},'From the ground'),mapEl('p',{class:'gm-title'},title,close));
    const facts=mapEl('dl',{class:'gm-facts'});const add=(k,v)=>{if(v!==undefined&&v!=='')facts.append(mapEl('dt',{},k),mapEl('dd',{},String(v)))};
    add('What',String(sel.what||sel.type||'').replace(/^shop:/,'shop: ').replace(/_/g,' '));add('Address',sel.address);
    if(sel.h)add('Height','about '+sel.h+' m, '+({tag:'as mapped',levels:'from its floors',guess:'guessed from its kind'}[sel.hs]||''));
    add('OpenStreetMap',sel.osm);card.append(facts);
    const where=mapEl('p',{class:'gm-where'},'…');card.insertBefore(where,facts);
    if(sel.lat!=null)api.rows('map.where '+sel.lat.toFixed(6)+','+sel.lon.toFixed(6)+' map='+mapQ(settings.map||'')).then(api.guard(r=>{where.textContent=(r[0]?.where)||''}),()=>where.remove());else where.remove();
    if((api.node.gestures||[]).some(g=>g.event==='add')&&sel.lat!=null){
      actions.append(mapEl('button',{type:'button',class:'gm-btn gm-primary',on:{click:()=>mapFire(api,'add',{name:sel.name||sel.address||'A spot',lat:String(sel.lat),lon:String(sel.lon),osm:sel.osm||'',select:{selected:''}},'Added '+(sel.name||'a spot'))}},'Add as a spot'));
      lines.textContent='Add runs: '+mapLineOf(api,'add');
    }
    if(sel.lat!=null)actions.append(routeFrom(title,sel.lat,sel.lon));
    card.append(actions,lines);return card;
  }
  // a thing in the world: every fact it has (as you may see it), where it is, what is near
  card.append(mapEl('h3',{},sel.layer||'In the world'),mapEl('p',{class:'gm-title'},sel.name||sel.thing,close));
  const where=mapEl('p',{class:'gm-where'},'…'),facts=mapEl('dl',{class:'gm-facts'}),near=mapEl('div',{class:'gm-near'});
  card.append(where,facts,actions,near,lines);
  api.rows('map.where '+sel.thing+' map='+mapQ(settings.map||'')).then(api.guard(r=>{if(!where.querySelector('.gm-big'))where.textContent=r[0]?.where||''}),()=>{if(!where.querySelector('.gm-big'))where.textContent=''});
  api.read('look '+sel.thing).then(api.guard(rows=>{
    const t=(Array.isArray(rows)?rows:rows?.rows||[])[0];if(!t){facts.append(mapEl('dd',{},'You cannot see this any more.'));return}
    const skip=new Set(['id','rev','groups','sees','path','stop_points','made_by']);
    for(const [k,v] of Object.entries(t)){if(skip.has(k)||k.startsWith('in:')||k.startsWith('member:')||typeof v==='object')continue;
      const shown=['made','changed','planned'].includes(k)?api.P.formatValue(v,'short-relative'):String(v).slice(0,240);
      const dd=mapEl('dd',{title:String(v)},shown);facts.append(mapEl('dt',{},k.replace(/_/g,' ')),dd);
      // ids inside longer text (a route's stops) read as names too
      if(!/^[a-z]{2,4}\d+$/.test(String(v))&&/\b[a-z]{2,4}\d+\b/.test(String(v))){const ids=[...new Set(String(v).match(/\b[a-z]{2,4}\d+\b/g))];
        Promise.all(ids.map(id=>api.read('look '+id).then(r=>[id,(Array.isArray(r)?r:r?.rows||[])[0]],()=>[id,null]))).then(api.guard(pairs=>{let text=String(v);
          for(const [id,o] of pairs)if(o)text=text.replace(new RegExp('\b'+id+'\b','g'),mapName(o));dd.textContent=text.slice(0,240)}))}
      // an id is shown as the thing's name, and pressing it goes there (never a bare id)
      if(/^[a-z]{2,4}\d+$/.test(String(v))&&k!=='kind')api.read('look '+v).then(api.guard(rows=>{const o=(Array.isArray(rows)?rows:rows?.rows||[])[0];if(!o)return;
        dd.replaceChildren(mapEl('button',{type:'button',class:'gm-link',on:{click:()=>api.select({selected:mapJ({kind:'thing',thing:o.id,name:mapName(o)}),...(o.lat?{focus:mapJ({lat:Number(o.lat),lon:Number(o.lon),stamp:Date.now()})}:{})})}},mapName(o)))}),()=>{})}
    const field=t.title!==undefined?'title':'name';
    if((api.node.gestures||[]).some(g=>g.event==='edit')){
      const editing=api.draft.editing===sel.thing;
      if(editing){const input=mapEl('input',{type:'text',value:t[field]||'','aria-label':'New '+field});
        const form=mapForm(api,{class:'gm-form'},()=>{api.draft.editing='';mapFire(api,'edit',{thing:sel.thing,fields:{[field]:input.value.trim()},saw:{[sel.thing]:t.rev},select:{selected:mapJ({...sel,name:input.value.trim()})}},'Renamed')},
          input,mapEl('div',{class:'gm-actions'},mapEl('button',{type:'submit',class:'gm-btn gm-primary'},'Save'),mapEl('button',{type:'button',class:'gm-btn',on:{click:()=>{api.draft.editing='';card.replaceWith(mountInspector(api,settings))}}},'Cancel')));
        actions.append(form);setTimeout(()=>input.focus(),20)}
      else actions.append(mapEl('button',{type:'button',class:'gm-btn',on:{click:()=>{api.draft.editing=sel.thing;card.replaceWith(mountInspector(api,settings))}}},'Rename'));
    }
    if(t.kind==='route'){
      where.replaceChildren(mapEl('span',{class:'gm-big'},(Number(t.metres)>=1000?(t.metres/1000).toFixed(2)+' km':t.metres+' m')+' · '+t.minutes+' min'),' ',mapEl('span',{},t.mode==='bike'?'by bike':'on foot'));
      actions.append(mapEl('button',{type:'button',class:'gm-btn gm-primary',on:{click:()=>api.select({fly:sel.thing+'@'+Date.now()})}},'Fly along it'));
      if((api.node.gestures||[]).some(g=>g.event==='replan'))actions.append(mapEl('button',{type:'button',class:'gm-btn',on:{click:()=>mapFire(api,'replan',{route:sel.thing,saw:{[sel.thing]:t.rev}},'Replanned')}},'Replan'));
    }
    else if(t.lat!==undefined||t.at||t.place){const ll=[Number(t.lat),Number(t.lon)];if(ll.every(Number.isFinite))actions.append(routeFrom(sel.name,ll[0],ll[1],sel.thing))}
    if((api.node.gestures||[]).some(g=>g.event==='forget'))actions.append(mapEl('button',{type:'button',class:'gm-btn',on:{click:()=>mapFire(api,'forget',{thing:sel.thing,saw:{[sel.thing]:t.rev},select:{selected:''}},'Removed. Undo brings it back.')}},'Remove'));
    lines.textContent=['edit','forget','replan'].map(e=>mapLineOf(api,e)).filter(Boolean).map(l=>'runs: '+l).join('\n');
  }),api.guard(e=>facts.append(mapEl('dd',{},String(e?.message||e)))));
  api.rows('map.near '+sel.thing+' within=250 map='+mapQ(settings.map||'')).then(api.guard(rows=>{
    rows=rows.filter(r=>r.id!==sel.thing).slice(0,6);if(!rows.length)return;
    near.append(mapEl('div',{class:'gm-sub'},'Near here'));
    for(const r of rows)near.append(mapEl('button',{type:'button',on:{click:()=>api.select({selected:mapJ({kind:'thing',thing:r.id,name:mapName(r)}),focus:mapJ({lat:r.lat,lon:r.lon,stamp:Date.now()})})}},mapEl('span',{},mapName(r)),mapEl('small',{},r.metres+' m')));
  }),()=>{});
  return card;
}

// ---- map-route -------------------------------------------------------------------------------------------------------
function mountRoute(api,settings){
  const v=mapView(api);const stops=Array.isArray(v.stops)?v.stops:[];const mode=v.mode;
  const card=api.part('route','section',{class:'gm-card','aria-label':'Route planner'});
  card.append(mapEl('h3',{},'Plan a route'));
  if(!stops.length){card.append(mapEl('p',{class:'gm-empty'},'Press the map or a pin for each stop, in order.'))}
  const list=mapEl('ol',{class:'gm-stops'});
  stops.forEach((s,i)=>list.append(mapEl('li',{},mapEl('span',{},s.label||'A point'),mapEl('button',{type:'button','aria-label':'Remove stop '+(i+1),on:{click:()=>api.select({stops:mapJ(stops.filter((_,j)=>j!==i))})}},'×'))));
  card.append(list);
  const seg=mapEl('div',{class:'gm-seg',role:'group','aria-label':'Travel by'});
  for(const [m,label] of [['walk','On foot'],['bike','By bike']])seg.append(mapEl('button',{type:'button','aria-pressed':String(m===mode),on:{click:()=>api.select({mode:m})}},label));
  card.append(mapEl('div',{style:{marginTop:'10px'}},seg));
  const numbers=mapEl('div',{style:{margin:'10px 0'}});card.append(numbers);
  if(stops.length>1){
    const line='map.path stops='+mapQ(stops.map(s=>s.ref||(s.lat.toFixed(6)+','+s.lon.toFixed(6))).join(' > '))+' mode='+mode+' map='+mapQ(settings.map||'');
    api.read(line).then(api.guard(r=>{const row=(Array.isArray(r)?r:r?.rows||[])[0];if(!row)return;
      numbers.replaceChildren(mapEl('div',{class:'gm-big'},(row.metres>=1000?(row.metres/1000).toFixed(2)+' km':row.metres+' m')+' · '+row.minutes+' min'),
        mapEl('div',{class:'gm-empty'},row.streets?.length?'Along '+row.streets.slice(0,4).join(', '):''))}),e=>numbers.replaceChildren(mapEl('p',{class:'gm-err'},String(e?.message||e))));
    const name=mapEl('input',{type:'text',placeholder:'Flyers: Murray to the beach','aria-label':'Route name',value:api.draft.name||''});
    name.addEventListener('input',()=>{api.draft.name=name.value});
    const form=mapForm(api,{class:'gm-form'},()=>{const stopsText=stops.map(s=>s.ref||(s.lat.toFixed(6)+','+s.lon.toFixed(6))).join(' > ');
      api.draft.name='';mapFire(api,'route',{name:name.value.trim()||(stops[0].label+' to '+stops[stops.length-1].label),stops:stopsText,mode,select:{tool:'look',stops:'[]'}},'Saved the route')},
      mapEl('label',{},'Name',name),mapEl('div',{class:'gm-actions'},mapEl('button',{type:'submit',class:'gm-btn gm-primary'},'Save route'),mapEl('button',{type:'button',class:'gm-btn',on:{click:()=>api.select({tool:'look',stops:'[]'})}},'Cancel')),
      mapEl('div',{class:'gm-line'},'runs: '+mapLineOf(api,'route')));
    card.append(form);
  }else card.append(mapEl('button',{type:'button',class:'gm-btn',on:{click:()=>api.select({tool:'look',stops:'[]'})}},'Cancel'));
  return card;
}

export default {css:MAP_CSS,mount(api,settings){
  switch(api.node.component){
    case 'map-shell':return mountShell(api,settings);
    case 'geo-map':return mountGeoMap(api,settings);
    case 'map-layers':return mountLayers(api,settings);
    case 'map-search':return mountSearch(api,settings);
    case 'map-inspector':return mountInspector(api,settings);
    case 'map-route':return mountRoute(api,settings);
    default:throw Error('map components: no '+api.node.component);
  }
}};
