// Map components for the component painter. One module serves every name (it branches on api.node.component):
//   map-shell      the window: the map full-bleed, a left column (search, what you pressed) and a right one (layers)
//   geo-map        the surface (geo-engine.js draws it): tools, the add sheet, navigation; fires put, move
//   map-search     things, places, streets and towns (map.find); choosing one flies there
//   map-inspector  what you pressed, or what is new on the map; a building's card; fires put, adopt, open-page, say …
//   map-route      the route planner while the route tool is on; fires route
//   map-layers     layers: show or hide each for yourself, + Add a layer (a gallery of readings), the ground, the look
//   place-page     a page for one place (a window opened on a structure): its head, then any sections
//   place-head     the place's name, what it is, a small 3D view of it, and Show on the map
//   place-list     a section of things at the place (events, notes, …) with a form to add one
//   place-talk     posts about the place, and a box to say something
// Everything they change goes through the lens's gesture lines, so a community can change what each press does.
// Built by install.py as: geo-worker.js + geo-engine.js + this file.

const MAP_CSS=`
.gm-panel{min-width:0;width:100%}.gm-panel>.gm-shell{height:100%;min-height:280px}
.gm-panel-entry{display:flex;align-items:center;gap:8px;margin:8px 0}
.gm-panel-body{position:relative;min-width:0;overflow:hidden;border-radius:12px}
.gm-panel-body>.gm-shell{height:100%}
.gm-shell{position:relative;width:100%;height:100vh;overflow:hidden;background:var(--gm-sky,#cfe8f2);font:14px/1.45 var(--ag-font,system-ui,sans-serif);color:var(--ink,#26302c)}
.gm-shell>.gm-stage{position:absolute;inset:0;z-index:0;isolation:isolate}
.gm-col{position:absolute;top:12px;bottom:12px;display:flex;flex-direction:column;gap:10px;pointer-events:none;z-index:5;width:min(350px,calc(50% - 24px))}
.gm-col>*{pointer-events:auto}.gm-col.gm-left{left:12px}.gm-col.gm-right{right:12px;top:64px;bottom:96px;width:min(300px,calc(50% - 24px))}
.gm-col .gm-scroll{overflow:auto;display:flex;flex-direction:column;gap:10px;min-height:0;padding:0 2px 4px;scrollbar-width:thin}
.gm-shell.gm-folded .gm-right .gm-scroll{display:none}
.gm-fold{align-self:flex-end;border:0;border-radius:999px;padding:6px 12px;background:var(--card,#fff);color:inherit;box-shadow:0 2px 10px #1f2a2422;font:inherit;font-size:12px;cursor:pointer}
.gm-card{background:color-mix(in srgb,var(--card,#fff) 96%,transparent);border:1px solid color-mix(in srgb,var(--ink,#26302c) 9%,transparent);border-radius:16px;box-shadow:0 8px 28px #1f2a241c;padding:12px 14px}
.gm-card h3{margin:0 0 8px;font-size:11.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted,#5f6b66);font-weight:700;display:flex;align-items:center;gap:8px}
.gm-card h3 .gm-btn{margin-left:auto;text-transform:none;letter-spacing:0;font-weight:600}
.gm-root{position:relative;width:100%;height:100%;overflow:hidden;background:var(--gm-sky,#cfe8f2);touch-action:none;user-select:none}
.gm-canvas{position:absolute;inset:0;width:100%;height:100%;outline:none;cursor:grab;display:block}
.gm-canvas:active{cursor:grabbing}
.gm-root[data-tool=add] .gm-canvas,.gm-root[data-tool=route] .gm-canvas{cursor:crosshair}
.gm-canvas:focus-visible{box-shadow:inset 0 0 0 3px #2f7f8f88}
.gm-overlay{position:absolute;inset:0;pointer-events:none;overflow:hidden}
.gm-street{position:absolute;left:0;top:0;white-space:nowrap;font-size:11.5px;font-weight:600;letter-spacing:.02em;color:var(--gm-label,#463d33);text-shadow:0 0 3px var(--gm-halo,#fffcf5),0 0 3px var(--gm-halo,#fffcf5),0 0 6px var(--gm-halo,#fffcf5);transform-origin:0 0}
.gm-town{position:absolute;left:0;top:0;white-space:nowrap;font-weight:700;color:var(--gm-town,#2f2a24);text-shadow:0 0 3px var(--gm-halo,#fffcf5),0 0 4px var(--gm-halo,#fffcf5),0 0 8px var(--gm-halo,#fffcf5);font-size:13px;letter-spacing:.01em}
.gm-town[data-what=city]{font-size:17px;letter-spacing:.04em}.gm-town[data-what=state],.gm-town[data-what=country]{font-size:18px;text-transform:uppercase;letter-spacing:.2em;opacity:.75}
.gm-town[data-what=suburb],.gm-town[data-what=neighbourhood],.gm-town[data-what=quarter]{font-size:11.5px;text-transform:uppercase;letter-spacing:.14em;font-weight:650;opacity:.8}
.gm-place{position:absolute;left:0;top:0;display:flex;align-items:center;gap:4px;white-space:nowrap;font-size:11.5px;color:var(--gm-label,#3c3a33);text-shadow:0 0 3px var(--gm-halo,#fffcf5),0 0 3px var(--gm-halo,#fffcf5);pointer-events:auto;cursor:pointer;transform-origin:0 0}
.gm-place i{width:8px;height:8px;border-radius:50%;background:#9a8f80;box-shadow:0 0 0 2px var(--gm-halo,#fffcf5)}
.gm-place[data-cat=food] i{background:#d0603f}.gm-place[data-cat=nature] i{background:#4f9a4a}.gm-place[data-cat=community] i{background:#3f78b5}
.gm-place[data-cat=shop] i{background:#8a63b8}.gm-place[data-cat=move] i{background:#6d7680}.gm-place[data-cat=health] i{background:#c2477c}.gm-place[data-cat=water] i{background:#3f9fc9}
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
.gm-pin.gm-far{font-size:9px}.gm-pin.gm-far .gm-pin-label{display:none!important}
.gm-pin.gm-approx .gm-pin-head{background:repeating-linear-gradient(45deg,currentColor 0 4px,color-mix(in srgb,currentColor 55%,#fff) 4px 7px)}
.gm-pin.gm-dragging{z-index:999999!important}.gm-pin.gm-dragging .gm-pin-head{transform:rotate(-45deg) scale(1.3) translate(.2em,-.2em)}
.gm-pin.gm-look-dot .gm-pin-head{left:-.45em;top:-.45em;width:.9em;height:.9em;border-radius:50%;transform:none}.gm-pin.gm-look-dot .gm-pin-head::after{display:none}.gm-pin.gm-look-dot .gm-pin-shadow{display:none}
.gm-pin.gm-look-flag .gm-pin-head{left:0;top:-1.9em;width:1.15em;height:.75em;border-radius:1px 5px 5px 1px;transform:none}.gm-pin.gm-look-flag .gm-pin-head::after{display:none}.gm-pin.gm-look-flag::before{content:"";position:absolute;left:-.08em;top:-1.95em;width:.16em;height:1.95em;background:#3e3a33;border-radius:1px}.gm-pin.gm-look-flag .gm-pin-shadow{left:-.3em;width:.6em}.gm-pin.gm-look-flag:hover .gm-pin-head,.gm-pin.gm-look-flag.gm-selected .gm-pin-head{transform:scale(1.15)}
.gm-pin.gm-look-label .gm-pin-head,.gm-pin.gm-look-label .gm-pin-shadow{display:none}.gm-pin.gm-look-label .gm-pin-label{display:block;top:-.7em;color:currentColor}
.gm-pin.gm-look-place .gm-pin-head{left:-.75em;top:-2.05em;width:1.5em;height:1.25em;border-radius:3px 3px 4px 4px;transform:none;clip-path:polygon(50% 0,100% 42%,100% 100%,0 100%,0 42%)}
.gm-pin.gm-look-place .gm-pin-head::after{inset:auto .5em .12em;height:.45em;border-radius:2px 2px 0 0}
.gm-pin.gm-look-place .gm-pin-label{display:block;top:.2em;font-size:11px;font-weight:700}
.gm-pin.gm-look-place:hover .gm-pin-head,.gm-pin.gm-look-place.gm-selected .gm-pin-head{transform:scale(1.15)}
@media (prefers-reduced-motion:no-preference){.gm-pin{animation:gm-drop .38s cubic-bezier(.3,1.5,.6,1) both}@keyframes gm-drop{from{opacity:0;margin-top:-18px}to{opacity:1;margin-top:0}}}
.gm-tip{position:absolute;left:0;top:0;background:#26302cee;color:#fff;font-size:12px;padding:3px 8px;border-radius:6px;white-space:nowrap;pointer-events:none}
.gm-stop{position:absolute;left:0;top:0;width:22px;height:22px;margin:-11px 0 0 -11px;border-radius:50%;background:#2f7f8f;color:#fff;font-size:11px;font-weight:700;display:grid;place-items:center;box-shadow:0 0 0 3px #fff,0 2px 6px #0004}
.gm-draft{position:absolute;left:0;top:0;pointer-events:auto;transform-origin:0 0;z-index:1000000}
.gm-draft form{position:absolute;left:-150px;top:16px;width:300px;background:var(--card,#fff);color:var(--ink,#26302c);border-radius:14px;padding:12px;box-shadow:0 10px 32px #0003;display:flex;flex-direction:column;gap:8px}
.gm-draft input,.gm-draft select,.gm-draft textarea{font:inherit;padding:7px 9px;border-radius:9px;border:1px solid #d8d2c6;background:var(--paper,#fff);color:inherit}
.gm-draft .gm-row{display:flex;gap:6px;justify-content:flex-end}
.gm-draft .gm-at{font-size:12.5px;color:var(--muted,#5f6b66)}
.gm-btn{font:inherit;font-size:13px;border-radius:10px;border:1px solid color-mix(in srgb,var(--ink,#26302c) 16%,transparent);background:var(--card,#fff);color:inherit;padding:6px 11px;cursor:pointer;display:inline-flex;align-items:center;gap:6px}
.gm-btn:hover{background:color-mix(in srgb,var(--ink,#26302c) 6%,var(--card,#fff))}
.gm-btn.gm-primary{background:#2f6f62;border-color:#2f6f62;color:#fff}.gm-btn.gm-primary:hover{background:#285f54}
.gm-btn.gm-warm{background:#cf5a3c;border-color:#cf5a3c;color:#fff}.gm-btn.gm-warm:hover{background:#b94e33}
.gm-btn.gm-small{font-size:12px;padding:3px 9px;border-radius:8px}
.gm-btn:focus-visible{outline:2px solid #2f7f8f;outline-offset:2px}
.gm-hud{position:absolute;inset:0;pointer-events:none}
.gm-hud>*{pointer-events:auto}
.gm-tools{position:absolute;top:12px;left:50%;transform:translateX(-50%);display:flex;gap:3px;background:var(--card,#fff);border-radius:999px;padding:4px;box-shadow:0 6px 20px #1f2a2428;z-index:3}
.gm-tools>button{border:0;background:transparent;color:inherit;font:inherit;font-size:13px;font-weight:600;padding:7px 14px;border-radius:999px;cursor:pointer;display:flex;align-items:center;gap:6px}
.gm-tools>button[aria-pressed=true]{background:#2f6f62;color:#fff}
.gm-tools>button.gm-add{background:#cf5a3c;color:#fff}.gm-tools>button.gm-add[aria-pressed=true]{background:#a8432a}
.gm-menu{position:absolute;top:58px;left:50%;transform:translateX(-50%);background:var(--card,#fff);border-radius:14px;box-shadow:0 10px 30px #0003;padding:6px;display:flex;flex-direction:column;min-width:230px;z-index:4}
.gm-menu button{all:unset;cursor:pointer;padding:8px 10px;border-radius:9px;display:grid;grid-template-columns:22px 1fr;gap:2px 8px;font-size:13.5px}
.gm-menu button small{grid-column:2;color:var(--muted,#5f6b66);font-size:11.5px}
.gm-menu button:hover,.gm-menu button:focus-visible{background:color-mix(in srgb,#cf5a3c 12%,transparent)}
.gm-hint{position:absolute;top:60px;left:50%;transform:translateX(-50%);background:#26302cdd;color:#fff;font-size:12.5px;padding:5px 12px;border-radius:999px;white-space:nowrap}
.gm-nav{position:absolute;right:12px;bottom:40px;display:flex;flex-direction:row;gap:6px}
.gm-nav button{width:38px;height:38px;border-radius:12px;border:0;background:var(--card,#fff);color:inherit;box-shadow:0 3px 12px #1f2a2426;font:600 18px/1 system-ui;cursor:pointer;display:grid;place-items:center}
.gm-nav button:focus-visible{outline:2px solid #2f7f8f}
.gm-foot{position:absolute;right:12px;bottom:10px;display:flex;align-items:center;gap:8px;font-size:11px;color:#3e3a33}
.gm-scale{height:6px;border:2px solid #3e3a33;border-top:0;min-width:20px}
.gm-scale-wrap{display:flex;align-items:center;gap:6px;background:#fffdf8cc;padding:2px 8px;border-radius:6px}
.gm-attrib{background:#fffdf8cc;padding:2px 8px;border-radius:6px}
.gm-loading{position:absolute;left:50%;bottom:14px;transform:translateX(-50%);background:#fffdf8e6;color:#3e3a33;font-size:12px;padding:4px 12px;border-radius:999px;box-shadow:0 2px 10px #0002;display:flex;gap:8px;align-items:center}
.gm-loading i{width:10px;height:10px;border-radius:50%;border:2px solid #2f7f8f;border-right-color:transparent;animation:gm-spin .8s linear infinite}@keyframes gm-spin{to{transform:rotate(1turn)}}
.gm-status{position:absolute;inset:0;display:grid;place-items:center;font-size:15px;color:#3e3a33;pointer-events:none}
.gm-status span{background:#fffdf8e6;padding:10px 18px;border-radius:12px;box-shadow:0 4px 18px #0002;max-width:70%}
.gm-more{all:unset;cursor:pointer;padding:0 6px;border-radius:6px;color:var(--muted,#5f6b66);font-size:15px;line-height:1}.gm-more:hover,.gm-more:focus-visible{background:color-mix(in srgb,var(--ink,#26302c) 8%,transparent)}
.gm-layer{display:grid;grid-template-columns:auto auto 1fr auto auto;align-items:center;gap:8px;padding:5px 4px;border-radius:9px}
.gm-layer:hover{background:color-mix(in srgb,var(--ink,#26302c) 5%,transparent)}
.gm-layer input{accent-color:#2f6f62;width:16px;height:16px;margin:0}
.gm-layer label{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.gm-layer .gm-mine{font-size:10.5px;color:var(--muted,#5f6b66);border:1px solid color-mix(in srgb,var(--ink,#26302c) 18%,transparent);border-radius:5px;padding:0 4px;margin-left:4px}
.gm-swatch{width:12px;height:12px;border-radius:50%;box-shadow:inset 0 0 0 1px #0002}
.gm-count{font-size:12px;color:var(--muted,#5f6b66);font-variant-numeric:tabular-nums}
.gm-err{grid-column:2/-1;font-size:12px;color:#a2402a}
.gm-sub{font-size:11px;color:var(--muted,#5f6b66);margin:12px 0 4px;text-transform:uppercase;letter-spacing:.08em;font-weight:700}
.gm-form{display:flex;flex-direction:column;gap:8px;margin-top:8px}
.gm-form label{display:flex;flex-direction:column;gap:3px;font-size:12px;color:var(--muted,#5f6b66)}
.gm-form input,.gm-form select,.gm-form textarea{font:inherit;font-size:13px;padding:6px 8px;border-radius:8px;border:1px solid #d8d2c6;background:var(--paper,#fff);color:var(--ink,#26302c)}
.gm-chips{display:flex;gap:6px;flex-wrap:wrap}.gm-chips button{width:22px;height:22px;border-radius:50%;border:2px solid #fff;box-shadow:0 0 0 1px #0002;cursor:pointer}
.gm-chips button[aria-pressed=true]{box-shadow:0 0 0 2px #26302c}
.gm-gallery{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:6px}
.gm-gallery button{all:unset;cursor:pointer;border-radius:12px;padding:8px 10px;background:color-mix(in srgb,var(--ink,#26302c) 4%,transparent);border:1px solid transparent;display:flex;flex-direction:column;gap:2px;font-size:13px;font-weight:600}
.gm-gallery button small{font-weight:400;font-size:11.5px;color:var(--muted,#5f6b66)}
.gm-gallery button:hover,.gm-gallery button:focus-visible,.gm-gallery button[aria-pressed=true]{border-color:#2f6f62;background:color-mix(in srgb,#2f6f62 9%,transparent)}
.gm-styles{display:grid;grid-template-columns:repeat(4,1fr);gap:6px}
.gm-styles button{all:unset;cursor:pointer;border-radius:10px;height:42px;display:flex;align-items:flex-end;padding:4px 6px;font-size:11.5px;font-weight:650;box-shadow:inset 0 0 0 1px #0002}
.gm-styles button[aria-pressed=true]{box-shadow:inset 0 0 0 2px #2f6f62,0 0 0 2px #2f6f6233}
.gm-seg{display:flex;gap:2px;background:color-mix(in srgb,var(--ink,#26302c) 7%,transparent);border-radius:999px;padding:2px;width:max-content;flex-wrap:wrap}
.gm-seg button{border:0;background:transparent;color:inherit;font:inherit;font-size:12.5px;padding:4px 11px;border-radius:999px;cursor:pointer}
.gm-seg button[aria-pressed=true]{background:var(--card,#fff);box-shadow:0 1px 3px #0002}
.gm-search{position:relative}
.gm-search input{width:100%;box-sizing:border-box;font:inherit;font-size:14.5px;padding:11px 12px 11px 36px;border-radius:14px;border:1px solid transparent;background:var(--card,#fff);color:inherit;box-shadow:0 8px 26px #1f2a241c}
.gm-search input:focus{outline:2px solid #2f7f8f}
.gm-search svg{position:absolute;left:12px;top:13px;opacity:.55}
.gm-results{margin-top:6px;display:flex;flex-direction:column;background:var(--card,#fff);border-radius:14px;box-shadow:0 8px 26px #1f2a241c;overflow:hidden}
.gm-results button{all:unset;display:grid;grid-template-columns:1fr auto;gap:0 8px;padding:8px 12px;cursor:pointer;font-size:13.5px}
.gm-results button span.gm-rwhere{grid-column:1/-1;font-size:11.5px;color:var(--muted,#5f6b66)}
.gm-results button:hover,.gm-results button:focus-visible{background:color-mix(in srgb,#2f7f8f 12%,transparent)}
.gm-results small{color:var(--muted,#5f6b66)}
.gm-facts{display:grid;grid-template-columns:auto 1fr;gap:3px 12px;font-size:12.5px;margin:8px 0}
.gm-facts dt{color:var(--muted,#5f6b66)}.gm-link{all:unset;cursor:pointer;color:#2f6f62;text-decoration:underline;text-underline-offset:2px}.gm-link:focus-visible{outline:2px solid #2f7f8f}.gm-facts dd{margin:0;overflow-wrap:anywhere}
.gm-title{font-size:18px;font-weight:750;margin:0;display:flex;align-items:center;gap:8px;line-height:1.25}
.gm-kicker{display:flex;gap:6px;flex-wrap:wrap;margin:4px 0 6px}
.gm-tag{font-size:11.5px;border-radius:999px;padding:1px 8px;background:color-mix(in srgb,var(--ink,#26302c) 7%,transparent);color:var(--muted,#5f6b66)}
.gm-tag.gm-imagery{background:#e9f1f6;color:#2c5b75}
.gm-where{color:var(--muted,#5f6b66);font-size:13px;margin:3px 0 8px}
.gm-actions{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.gm-line{font:11.5px/1.4 ui-monospace,Consolas,monospace;color:var(--muted,#5f6b66);margin-top:8px;overflow-wrap:anywhere;white-space:pre-wrap}
.gm-list{display:flex;flex-direction:column;gap:2px;margin-top:6px}
.gm-list button,.gm-list .gm-item{all:unset;cursor:pointer;font-size:13px;display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:8px;padding:5px 6px;border-radius:8px}
.gm-list button:hover,.gm-list button:focus-visible{background:color-mix(in srgb,var(--ink,#26302c) 6%,transparent)}
.gm-list small{color:var(--muted,#5f6b66);font-size:11.5px;white-space:nowrap}
.gm-dot{width:9px;height:9px;border-radius:50%;background:currentColor}
.gm-talk{display:flex;flex-direction:column;gap:6px;margin-top:6px}
.gm-post{background:color-mix(in srgb,var(--ink,#26302c) 4%,transparent);border-radius:12px;padding:8px 10px;font-size:13px}
.gm-post small{display:block;color:var(--muted,#5f6b66);font-size:11.5px;margin-top:3px}
.gm-say{display:flex;gap:6px;margin-top:6px}.gm-say input{flex:1;font:inherit;font-size:13px;padding:7px 9px;border-radius:9px;border:1px solid #d8d2c6;background:var(--paper,#fff);color:inherit}
.gm-stops{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:4px;counter-reset:s}
.gm-stops li{display:grid;grid-template-columns:22px 1fr auto;gap:8px;align-items:center;font-size:13px}
.gm-stops li::before{counter-increment:s;content:counter(s);width:20px;height:20px;border-radius:50%;background:#2f7f8f;color:#fff;display:grid;place-items:center;font-size:11px;font-weight:700}
.gm-stops button{all:unset;cursor:pointer;color:var(--muted,#5f6b66);padding:0 4px}
.gm-big{font-size:22px;font-weight:750;font-variant-numeric:tabular-nums}
.gm-empty{font-size:13px;color:var(--muted,#5f6b66)}
.gm-empty code,.gm-card code{font:12px ui-monospace,Consolas,monospace;background:color-mix(in srgb,var(--ink,#26302c) 7%,transparent);padding:1px 4px;border-radius:4px}
.gm-hello p{margin:4px 0}
.gm-shell[data-style=night]{--card:#1f2629;--ink:#e8e2d6;--muted:#a9b0aa;--paper:#171d20}
.gm-shell[data-style=night] .gm-scale-wrap,.gm-shell[data-style=night] .gm-attrib,.gm-shell[data-style=night] .gm-loading{background:#1c211fcc;color:#d8d2c6}
.gm-shell[data-style=night] .gm-scale{border-color:#d8d2c6}
@media (max-width:760px){.gm-col.gm-left{top:auto;left:8px;right:8px;bottom:8px;width:auto;max-height:46vh}.gm-col.gm-right{display:none}.gm-tools{top:8px}.gm-nav{bottom:auto;top:64px;right:8px}}
/* a place's page */
.pp{min-height:100vh;box-sizing:border-box;background:var(--paper,#f6f3ec);color:var(--ink,#26302c);font:14px/1.5 var(--ag-font,system-ui,sans-serif);padding:0 0 24px}
.pp-wrap{max-width:720px;margin:0 auto;padding:0 16px;display:flex;flex-direction:column;gap:12px}
.pp-head{position:relative;border-radius:0 0 22px 22px;overflow:hidden;background:var(--gm-sky,#cfe8f2);min-height:220px;margin:0 -16px}
.pp-head .gm-root{position:absolute;inset:0;height:auto}
.pp-head::after{content:"";position:absolute;left:0;right:0;bottom:0;height:62%;background:linear-gradient(180deg,transparent,#0000002e 40%,#000000a6);pointer-events:none}
.pp-head .pp-title{position:absolute;left:16px;right:16px;bottom:14px;color:#fff;text-shadow:0 1px 10px #0009;pointer-events:none;z-index:1}
.pp-head h1{margin:0;font-size:26px;line-height:1.15;font-weight:800}
.pp-head .pp-badge{display:inline-block;background:var(--pp-accent,#2f6f62);color:#fff;text-shadow:none;border-radius:999px;font-size:12px;font-weight:700;padding:2px 10px;margin-bottom:6px}
.pp-head .pp-meta{font-size:13px;opacity:.95}
.pp-bar{display:flex;gap:6px;flex-wrap:wrap}
.pp-section{background:var(--card,#fff);border-radius:16px;padding:12px 14px;box-shadow:0 4px 18px #1f2a2412;border:1px solid color-mix(in srgb,var(--ink,#26302c) 7%,transparent)}
.pp-section h2{margin:0 0 6px;font-size:15px;display:flex;align-items:center;gap:8px}
.pp-section h2 .gm-btn{margin-left:auto}
.pp-when{font-variant-numeric:tabular-nums;color:var(--pp-accent,#2f6f62);font-weight:700;font-size:12.5px;white-space:nowrap}
.pp-none{padding:40px 16px;text-align:center;color:var(--muted,#5f6b66)}
`;

const MAP_LAYER_COLOURS=['#cf5a3c','#2f7f8f','#6c5bb3','#d39a2c','#4f9a4a','#c2477c','#3f78b5','#8a6a3c'];
const MAP_TEMPLATES=[
  {title:'Events coming up',blurb:'Every event with a place',shows:'rows event',look:'pin',color:'#cf5a3c'},
  {title:'Adopted places',blurb:'Buildings people gave a page',shows:'rows structure',look:'place',color:'#8a6a3c'},
  {title:'Notes',blurb:'Notes left at places',shows:'rows note',look:'dot',color:'#d39a2c'},
  {title:'A kind of thing',blurb:'Any kind in this world',ask:'kind',shows:'rows $kind',look:'pin'},
  {title:'Tagged…',blurb:'Spots with a tag',ask:'tag',shows:'rows spot tags=$tag',look:'dot'},
  {title:'Near a place',blurb:'What is placed close by',ask:'place',shows:'map.near $place within=400',look:'pin'},
  {title:'From the board',blurb:'A board reading',ask:'reading',shows:'board.',look:'pin'},
  {title:'Your own reading',blurb:'Any line that lists things',ask:'reading',shows:'',look:'pin'},
];
const MAP_KIND_ICON={spot:'📍',event:'📅',note:'📝',structure:'🏠',route:'🧭'};
const mapQ=s=>'"'+String(s).replace(/\\/g,'\\\\').replace(/"/g,'\\"')+'"';
const mapEl=(tag,attrs={},...kids)=>{const n=document.createElement(tag);for(const [k,v] of Object.entries(attrs||{})){if(v==null||v===false)continue;if(k==='on')for(const [e,f] of Object.entries(v))n.addEventListener(e,f);else if(k==='style'&&typeof v==='object')Object.assign(n.style,v);else if(k==='text')n.textContent=v;else n.setAttribute(k,v===true?'':v)}for(const c of kids.flat())if(c!=null&&c!==false)n.append(c.nodeType?c:document.createTextNode(String(c)));return n};
// View state holds plain values only (the broker refuses objects), so selection, stops and focus travel as JSON text.
function mapView(api){const v=api.view();const j=(x,d)=>{if(x&&typeof x==='object')return x;try{return x?JSON.parse(x):d}catch{return d}};return {tool:v.tool||'look',mode:v.mode||'walk',stops:j(v.stops,[]),selected:j(v.selected,null),focus:j(v.focus,null),target:v.target||''}}
const mapJ=v=>v==null?'':JSON.stringify(v);
// The frame has no allow-forms: a form's submit never fires, so the painter's P.submit handles Enter and the submit button.
function mapForm(api,attrs,fn,...kids){const f=mapEl('form',attrs,...kids);api.P.submit(f,fn);return f}
function mapName(t){return t?.title||t?.name||t?.label||(t?.text?String(t.text).slice(0,60):'')||t?.kind||''}
function mapRows(r){return Array.isArray(r)?r:(r?.rows||[])}
function mapHead(rows){return rows.find(r=>r.kind==='map')||{}}
function mapReadLayers(api,map){return api.read('map.layers '+mapQ(map)).then(mapRows)}
function mapHas(api,event){return (api.node.gestures||[]).some(g=>g.event===event)}
function mapLineOf(api,event){const g=(api.node.gestures||[]).find(g=>g.event===event);return g?g.line:''}
async function mapFire(api,event,values,okText){try{const out=await api.fire(event,values);if(okText)api.tell(okText);return out}catch(e){api.tell(String(e?.message||e).split('\n')[0]);return null}}
function mapAgo(iso){const t=Date.parse(iso);if(!isFinite(t))return '';const s=(Date.now()-t)/1000;if(s<60)return 'just now';if(s<3600)return Math.round(s/60)+' min ago';if(s<86400)return Math.round(s/3600)+' h ago';return Math.round(s/86400)+' d ago'}
function mapMetres(m){m=Number(m)||0;return m>=1000?(m/1000).toFixed(m>=10000?0:1)+' km':Math.round(m)+' m'}
function mapRefOf(sel){return sel?.ref||''}
// the place a press names, as map.add takes it: a building ref (with a point inside it), or a lat,lon
function mapPlaceArg(sel){return sel?.ref?sel.ref:(sel?.thing||(Number(sel?.lat).toFixed(6)+','+Number(sel?.lon).toFixed(6)))}
function mapIcon(name){const d={look:'M3 3l6 15 2-6 6-2z',add:'M10 4v12M4 10h12',route:'M5 15c0-5 10-5 10-10M5 15a2 2 0 1 0 0 .1M15 5a2 2 0 1 0 0 .1',
  home:'M3 10l7-6 7 6v7h-5v-4H8v4H3z',globe:'M10 3a7 7 0 1 0 0 14a7 7 0 1 0 0-14M3 10h14M10 3c3 3 3 11 0 14M10 3c-3 3-3 11 0 14',layers:'M10 3l8 4-8 4-8-4zM2 11l8 4 8-4'}[name]||'';
  const s=mapEl('span',{'aria-hidden':'true'});s.innerHTML=`<svg width="16" height="16" viewBox="0 0 20 20"><path d="${d}" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>`;return s}

// The panel composes the same map pieces as map.lens. Its facade keeps transient map state out of its
// parent's channel/thread/tool/target values. All world writes still use the panel's authored gestures.
function mapPanelApi(api,settings){
  const prefix='map.'+api.node.path+'.';
  const view=()=>Object.fromEntries(Object.entries(api.view()).filter(([k])=>k.startsWith(prefix)).map(([k,v])=>[k.slice(prefix.length),v]));
  const select=values=>api.select(Object.fromEntries(Object.entries(values).map(([k,v])=>[prefix+k,v])));
  const read=async line=>{
    const rows=mapRows(await api.read(line));
    if(!line.startsWith('map.layers '))return rows;
    const v=view();
    return rows.map(r=>r.kind==='map'?{...r,...(v.hide!==undefined?{hidden:v.hide}:{}),...(v.style?{mystyle:v.style}:{})}:r);
  };
  const localEvents=['hide','unhide','style'];
  const facade={...api,view,select,read,node:{...api.node,gestures:[...api.node.gestures,...localEvents.map(event=>({event}))]},
    fire:(event,values)=>{
      if(event==='hide'||event==='unhide'){
        const key=GEO_GROUND_KEYS.includes(values.layer)?'ground:'+values.layer:values.layer;
        return read('map.layers '+mapQ(settings.map)).then(rows=>{
          const hidden=new Set(String(mapHead(rows).hidden||'').split(/\s+/).filter(Boolean));
          (event==='hide'?hidden.add.bind(hidden):hidden.delete.bind(hidden))(key);
          return select({hide:[...hidden].join(' ')});
        });
      }
      if(event==='style')return select({style:values.style});
      // api.fire's post-action selection belongs to the containing lens, so namespace map-only values.
      const next=values.select?Object.fromEntries(Object.entries(values.select).map(([k,v])=>[prefix+k,v])):undefined;
      return api.fire(event,{...values,...(next?{select:next}:{})});
    },
    openThing:it=>{
      if(settings.board==='yes'&&it.kind==='post')return api.select({
        thread:it.thread||it.id,replyTo:it.thread||it.id,quote:'',source:'',page:1,documentPage:1,documentFile:''
      });
      if(mapHas(api,'open'))return api.fire('open',{thing:it.id,saw:{[it.id]:it.rev}});
    }};
  return facade;
}
const GEO_GROUND_KEYS=['buildings','streets','labels','places','props','water','green','shadows','names'];

function mountPanel(api,settings){
  if(!api.draft)return mapPaused(api);
  const local=mapPanelApi(api,settings),root=api.part('panel','section',{class:'gm-panel','aria-label':'Map'});
  const open=settings.board!=='yes'||local.view().open==='yes';
  if(settings.board==='yes')root.append(api.part('entry','button',{type:'button',class:'gm-btn gm-panel-entry',
    'aria-expanded':String(open),on:{click:()=>local.select({open:open?'no':'yes'})}},mapIcon('globe'),api.label('map','Map')));
  if(!open)return root;
  const body=mapEl('div',{class:'gm-panel-body'});
  body.style.height=/^\d+(?:\.\d+)?(px|vh|rem|%)$/.test(settings.height||'')?settings.height:'520px';
  body.style.minHeight='280px';
  // Each piece retains its own draft (engine, search text, editors) across parent repaints.
  const pieces=[['map','geo-map',mountGeoMap],['search','map-search',mountSearch],
    ['inspect','map-inspector',mountInspector],['layers','map-layers',mountLayers]];
  const children=pieces.map(([name,component])=>({name,component}));
  const composed={...local,children,render:child=>{
    const [name,,mount]=pieces.find(([name])=>name===child.name);
    const drafts=api.draft.pieces||(api.draft.pieces={});
    return mount({...local,draft:drafts[name]||(drafts[name]={})},settings);
  }};
  body.append(mountShell(composed));root.append(body);return root;
}

// ---- map-shell -----------------------------------------------------------------------------------------------------
function mountShell(api){
  const root=api.part('shell','div',{class:'gm-shell'});
  const stage=mapEl('div',{class:'gm-stage'}),left=mapEl('div',{class:'gm-col gm-left'}),right=mapEl('div',{class:'gm-col gm-right'});
  const lscroll=mapEl('div',{class:'gm-scroll'}),rscroll=mapEl('div',{class:'gm-scroll'});
  const folded=!!api.draft.folded;root.classList.toggle('gm-folded',folded);
  const fold=mapEl('button',{type:'button',class:'gm-fold','aria-expanded':String(!folded),on:{click:()=>{api.draft.folded=!api.draft.folded;root.classList.toggle('gm-folded',api.draft.folded);fold.textContent=api.draft.folded?'Layers':'Hide layers';fold.setAttribute('aria-expanded',String(!api.draft.folded))}}},folded?'Layers':'Hide layers');
  for(const child of api.children){
    if(child.component==='geo-map')stage.append(api.render(child));
    else if(child.component==='map-search')left.append(api.render(child));
    else if(child.component==='map-layers')rscroll.append(api.render(child));
    else lscroll.append(api.render(child));
  }
  left.append(lscroll);right.append(fold,rscroll);root.append(stage,left,right);
  return root;
}

// A paused (quarantined) part runs in a worker with no screen to draw on, and Try again keeps the pause (only a
// steward lifts it). So the paused map says so and offers its own button: the lens's `on resume` line
// (component-action … action=clear) starts it again for a steward, and says plainly why not for anyone else.
function mapPaused(api){
  const box=api.part('surface','div',{role:'status',style:{display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',gap:'10px',
    height:'100%',minHeight:'240px',padding:'24px',background:'#eef3f6',color:'#2c3a44',textAlign:'center',fontSize:'14px'}});
  const said=api.el('p',{style:{margin:'0',color:'#5b6b76'}},'The map paused itself after it stopped twice on this screen. It draws with the graphics card, so it cannot run while paused.');
  const go=api.el('button',{type:'button',style:{padding:'8px 14px',borderRadius:'8px',border:'1px solid #2f7f8f',background:'#2f7f8f',color:'#fff',fontSize:'14px'},
    on:{click:()=>{said.textContent='Starting the map again…';api.fire('resume',{}).catch?.(e=>{said.textContent=String(e?.message||e)})}}},'Start the map again');
  box.append(api.el('strong',{},'The map is paused'),said,go);return box;
}

// ---- geo-map ---------------------------------------------------------------------------------------------------------
function mountGeoMap(api,settings){
  if(!api.draft)return mapPaused(api);
  const d=api.draft;if(!d.engine)d.engine=new GeoEngine(String(geoWorkerMain));const E=d.engine;
  E.canvas.__engine=E;      // for measuring in tests (the page is sandboxed; nothing outside it can reach this)
  const view=mapView(api);const map=settings.map||'';
  const root=api.part('surface','div',{class:'gm-root',role:'application','aria-label':'Map of '+map});
  root.dataset.tool=view.tool||'look';
  E.attach(root,api);
  E.tool=view.tool;
  E.fetchTile=key=>E.api.rows('map.tile '+key).then(rows=>{const r=mapRows(rows)[0];if(!r||!r.chunk)throw Error('no tile '+key);return r.chunk});
  // stops: this map's own presses are newer than a repaint still carrying an older list
  {const vs=JSON.stringify(Array.isArray(view.stops)?view.stops:[]);E.sent=E.sent||new Set();
    const ours=vs===E.lastSent||(E.sent.has(vs)&&performance.now()-(E.sentAt||0)<2000);if(!ours)E.stops=JSON.parse(vs)}
  E.selectedId=view.selected?.thing||'';E.selRef=view.selected?.ref||'';
  // the HUD: tools, the add menu, hint, navigation, scale, loading and attribution
  const hud=mapEl('div',{class:'gm-hud'});
  const setTool=tool=>{E.draft=null;E.draftEl?.remove();E.tool=tool;root.dataset.tool=tool;d.menu=false;if(tool!=='route')E.stops=[];api.select({tool,stops:mapJ(tool==='route'?E.stops:[])})};
  const tools=mapEl('div',{class:'gm-tools',role:'toolbar','aria-label':'Map tools'});
  tools.append(mapEl('button',{type:'button','aria-pressed':String(E.tool==='look'),on:{click:()=>setTool('look')}},mapIcon('look'),'Look'));
  const addBtn=mapEl('button',{type:'button',class:'gm-add','aria-pressed':String(E.tool==='add'),'aria-haspopup':'menu','aria-expanded':String(!!d.menu),
    on:{click:()=>{d.menu=!d.menu;paintMenu()}}},mapIcon('add'),'Add');
  if(mapHas(api,'put'))tools.append(addBtn);
  // The route planner is an authored sibling in map.lens; panels may supply one separately.
  if(api.node.component!=='map-panel')tools.append(mapEl('button',{type:'button','aria-pressed':String(E.tool==='route'),on:{click:()=>setTool('route')}},mapIcon('route'),'Route'));
  const menuSlot=mapEl('div');
  const KINDS=[['spot','📍','A spot','A place people can find: a bench, a gate, a view'],['event','📅','An event','Something happening, with a time'],
    ['note','📝','A note','A few words left at a place'],['other','✳️','Something else…','Any kind this world knows']];
  function paintMenu(){menuSlot.replaceChildren();addBtn.setAttribute('aria-expanded',String(!!d.menu));if(!d.menu)return;
    const m=mapEl('div',{class:'gm-menu',role:'menu'});
    for(const [k,icon,label,blurb] of KINDS)m.append(mapEl('button',{type:'button',role:'menuitem',on:{click:()=>{d.addKind=k;d.menu=false;E.tool='add';root.dataset.tool='add';api.select({tool:'add',stops:'[]'})}}},
      mapEl('span',{},icon),mapEl('span',{},label),mapEl('small',{},blurb)));
    menuSlot.append(m);setTimeout(()=>m.querySelector('button')?.focus(),20)}
  hud.append(tools,menuSlot);paintMenu();
  const hints={add:'Press a building or the ground where it goes. Esc to stop.',route:E.stops.length?'Press the map or pins to add stops; save from the planner.':'Press the map, or a pin, for the first stop.'};
  if(hints[E.tool]&&!d.menu)hud.append(mapEl('div',{class:'gm-hint',role:'status'},hints[E.tool]));
  const needle=mapEl('span',{},'');needle.innerHTML='<svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true"><path d="M10 2 L13 10 L10 9 L7 10Z" fill="#cf5a3c"/><path d="M10 18 L13 10 L10 11 L7 10Z" fill="#8a8378"/></svg>';
  const home=()=>{const c=String(E.head?.centre||'').split(',').map(Number);if(c.length===2&&c.every(Number.isFinite)){const [x,y]=E.toXY(c[0],c[1]);E.flyTo({x,y,dist:1400*E.scaleAt(y),pitch:52},1400)}};
  const nav=mapEl('div',{class:'gm-nav'},
    mapEl('button',{type:'button','aria-label':'Zoom in',title:'Zoom in (+)',on:{click:()=>E.flyTo({dist:E.cam.dist*0.6},300)}},'+'),
    mapEl('button',{type:'button','aria-label':'Zoom out',title:'Zoom out (−)',on:{click:()=>E.flyTo({dist:E.cam.dist/0.6},300)}},'−'),
    mapEl('button',{type:'button',class:'gm-compass','aria-label':'Face north',title:'Face north (N)',on:{click:()=>E.flyTo({bearing:0},450)}},needle),
    mapEl('button',{type:'button','aria-label':'Tilt or flatten the map',title:'Tilt (T)',style:{fontSize:'12px'},on:{click:()=>E.flyTo({pitch:E.cam.pitch>8?0:52},500)}},E.cam.pitch>8?'2D':'3D'),
    mapEl('button',{type:'button','aria-label':'Back to '+map,title:'Back to '+map,on:{click:home}},mapIcon('home')),
    mapEl('button',{type:'button','aria-label':'See all of California',title:'See all of California',on:{click:()=>{const [x,y]=E.toXY(37.2,-119.5);E.flyTo({x,y,dist:2.2e6,pitch:20,bearing:0},2400)}}},mapIcon('globe')));
  const scale=mapEl('span',{class:'gm-scale'}),scaleText=mapEl('span',{},'');
  const loading=mapEl('div',{class:'gm-loading',hidden:true},mapEl('i'),mapEl('span'));
  const foot=mapEl('div',{class:'gm-foot'},mapEl('span',{class:'gm-scale-wrap'},scale,scaleText),
    mapEl('span',{class:'gm-attrib',title:'Streets, water, land and names: OpenStreetMap contributors (ODbL), tiles by OpenFreeMap. Buildings: Overture Maps Foundation (OpenStreetMap and machine-traced footprints).'},'© OpenStreetMap · OpenFreeMap · Overture'));
  const status=mapEl('div',{class:'gm-status',role:'status'});
  hud.append(nav,foot,loading,status);root.append(hud);
  const showStatus=()=>{status.replaceChildren(E.status?mapEl('span',{},E.status):'')};showStatus();
  // a frame also moves the compass, the scale and the overlay extras (the thing being placed, the route's stops)
  E.overlayExtras=()=>{
    needle.firstChild.style.transform=`rotate(${-E.cam.bearing}deg)`;
    const a=E.ground(E.w/2,E.h*0.62),b=E.ground(E.w/2+100,E.h*0.62);
    if(a&&b){const m=Math.hypot(a[0]-b[0],a[1]-b[1])/E.scaleAt(a[1]);const nice=[5,10,20,50,100,200,250,500,1000,2000,5000,10000,20000,50000,100000,200000,500000].find(n=>n/m*100>=60)||500000;scale.style.width=(nice/m*100).toFixed(0)+'px';scaleText.textContent=nice>=1000?nice/1000+' km':nice+' m'}
    const p=E.pending||0;loading.hidden=!p;if(p)loading.lastChild.textContent='Loading '+p+' tile'+(p===1?'':'s')+'…';
    let stops=E._stopEls||(E._stopEls=[]);stops.forEach(s=>s.remove());E._stopEls=stops=[];
    E.stops.forEach((s,i)=>{const [x,y]=E.toXY(s.lat,s.lon);const q=E.project(x,y,0);if(!q)return;const el=mapEl('div',{class:'gm-stop',style:{transform:`translate(${q[0]}px,${q[1]}px)`}},String(i+1));E.overlay.append(el);stops.push(el)});
    if(E.draft&&E.draftEl){const [x,y]=E.toXY(E.draft.lat,E.draft.lon);const q=E.project(x,y,0);if(q)E.draftEl.style.transform=`translate(${q[0]}px,${q[1]}px)`}
  };
  // presses: what each does depends on the tool; anything that changes the world goes through a gesture line
  const select=sel=>{E.selectedId=sel?.thing||'';E.selRef=sel?.ref||'';E.ask();return api.select({selected:mapJ(sel)})};
  const addStop=s=>{const stops=[...E.stops,s];E.stops=stops;const j=mapJ(stops);E.sent.add(j);E.lastSent=j;E.sentAt=performance.now();E.ask();return api.select({stops:j,tool:'route'})};
  E.onPress=p=>{
    if(E.api!==api)return;          // only the newest mount answers
    if(d.menu){d.menu=false;paintMenu()}
    const w=p.what;const label=w?.name||(w?.type==='building'&&w.number?w.number:'')||(p.lat!=null?p.lat.toFixed(5)+', '+p.lon.toFixed(5):'');
    if(E.tool==='route'){if(p.lat==null)return;addStop({label:label||'A point',lat:p.lat,lon:p.lon,ref:''});return}
    if(E.tool==='add'){if(p.lat==null)return;openDraft({lat:p.lat,lon:p.lon,kind:d.addKind||'spot',ref:w?.type==='building'?w.ref:'',where:w?.type==='building'?(geoDescribe(w)):(w?.name||'')});return}
    if(!w){select(null);return}
    if(w.type==='building')select({kind:'ground',type:'building',ref:w.ref,name:w.name,number:w.number,what:w.what,h:w.h,floors:w.floors,src:w.src,osm:w.osm,lat:p.lat,lon:p.lon});
    else select({kind:'ground',type:w.type,name:w.name,what:w.what,lat:p.lat,lon:p.lon});
  };
  E.onPin=(it)=>{
    if(E.api!==api)return;
    if(E.tool==='route'){addStop({label:mapName(it),lat:it.lat,lon:it.lon,ref:it.id});return}
    select({kind:'thing',thing:it.id,name:mapName(it),rev:it.rev,layer:it.layer?.name||'',ref:it.ref||''});
    if(api.openThing)Promise.resolve(api.openThing(it)).catch(e=>api.tell(String(e?.message||e)));
    else if(mapHas(api,'open'))mapFire(api,'open',{thing:it.id,saw:{[it.id]:it.rev}});
  };
  E.onMove=(it,lat,lon)=>{if(E.api!==api)return;mapFire(api,'move',{thing:it.id,lat:String(lat),lon:String(lon),saw:{[it.id]:it.rev}},'Moved '+mapName(it))};
  E.onEscape=()=>{if(E.api!==api)return;E.draft=null;E.draftEl?.remove();d.menu=false;paintMenu();api.select({tool:'look',stops:'[]'})};
  // The add sheet: what kind, its few words, and where (a building, or the ground). It fires put: map.add <place> kind= …
  function openDraft(dr){
    E.draft=dr;E.draftEl?.remove();
    const field=(name,attrs)=>mapEl('input',{type:'text','aria-label':name,...attrs});
    const name=field('Name',{placeholder:'What is here?'}),title=field('Title',{placeholder:'What is happening?'}),when=field('When',{placeholder:'Sat 10am, tomorrow 6pm, Nov 2 18:00'});
    const text=mapEl('textarea',{rows:3,'aria-label':'Note',placeholder:'A few words for whoever comes by'});
    const kindSel=mapEl('select',{'aria-label':'Kind'});const whenSaid=mapEl('div',{class:'gm-line'});const runs=mapEl('div',{class:'gm-line'});
    const parse=()=>{const r=api.P.parseDateEntry?api.P.parseDateEntry(when.value):{ok:false};whenSaid.textContent=when.value.trim()?(r.ok?r.label:r.message||'Say a day and a time'):'';return r};
    when.addEventListener('input',parse);
    const submit=mapEl('button',{type:'submit',class:'gm-btn gm-warm'});
    const seg=mapEl('div',{class:'gm-seg',role:'group','aria-label':'What to add'});
    const at=mapEl('div',{class:'gm-at'},'At '+(dr.ref?(dr.where||'this building'):(dr.where||dr.lat.toFixed(5)+', '+dr.lon.toFixed(5))));
    const setKind=k=>{dr.kind=k;seg.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.kind===k)));
      name.hidden=!(k==='spot'||k==='other');title.hidden=when.hidden=whenSaid.hidden=k!=='event';text.hidden=k!=='note';kindSel.hidden=k!=='other';
      submit.textContent={spot:'Add spot',event:'Add event',note:'Leave note',other:'Add'}[k];
      runs.textContent='runs: '+(mapLineOf(api,'put')||'(this lens arranges no put gesture)');
      setTimeout(()=>({spot:name,event:title,note:text,other:name}[k])?.focus(),20)};
    for(const [k,label] of [['spot','Spot'],['event','Event'],['note','Note'],['other','Other…']])seg.append(mapEl('button',{type:'button','data-kind':k,on:{click:()=>setKind(k)}},label));
    api.rows('rows kind').then(api.guard(rows=>{const skip=new Set(['map','map-layer','route','structure','kind','lens','widget','window','button','component','view-preference','part-style','grant','module','file','theme']);
      for(const r of mapRows(rows))if(r.name&&!skip.has(r.name)&&(r.compose_label||['spot','event','note','offer','ask','carpool'].includes(r.name)))kindSel.append(mapEl('option',{value:r.name},r.compose_label||r.name))}),()=>{});
    const close=()=>{E.draft=null;E.draftEl?.remove()};
    const form=mapForm(api,{},()=>{
      const k=dr.kind,fields={};
      if(dr.ref){fields.lat=String(dr.lat);fields.lon=String(dr.lon)}
      if(k==='spot'||k==='other'){if(!name.value.trim()){name.focus();return}fields.name=name.value.trim()}
      if(k==='event'){if(!title.value.trim()){title.focus();return}const r=parse();if(!r.ok){when.focus();return}fields.title=title.value.trim();fields.start=r.iso}
      if(k==='note'){if(!text.value.trim()){text.focus();return}fields.text=text.value.trim()}
      const kind=k==='other'?(kindSel.value||'spot'):k;
      close();mapFire(api,'put',{place:mapPlaceArg(dr),kind,fields,select:{tool:'look'}},'Added '+(fields.title||fields.name||'a note'))},
      seg,at,name,title,when,whenSaid,text,kindSel,mapEl('div',{class:'gm-row'},mapEl('button',{type:'button',class:'gm-btn',on:{click:close}},'Cancel'),submit),runs);
    setKind(dr.kind||'spot');
    E.draftEl=mapEl('div',{class:'gm-draft'},mapEl('div',{class:'gm-stop',style:{background:'#cf5a3c'}},'+'),form);E.overlay.append(E.draftEl);
    // place it now (not on the next frame), and open the form upward when the press is near the bottom
    {const [x,y]=E.toXY(dr.lat,dr.lon);E.matrices();const p=E.project(x,y,0);if(p){E.draftEl.style.transform=`translate(${p[0]}px,${p[1]}px)`;
      const fh=form.offsetHeight||230;if(p[1]+fh+24>E.h)form.style.top=(-fh-18)+'px';const fx=Math.max(8,Math.min(E.w-308,p[0]-150))-p[0];form.style.left=fx+'px'}}
    E.ask();
  }
  if(E.draft&&!E.draftEl?.isConnected)openDraft(E.draft);
  // the data: the layers every paint (a watched reading, so it is already here); tiles as the camera needs them
  mapReadLayers(api,map).then(api.guard(rows=>{
    const head=rows.find(r=>r.kind==='map');
    if(!head){E.status='No map called '+map+' here.';showStatus();return}
    E.head=head;
    if(head.mystyle||settings.style)E.setStyle(head.mystyle||settings.style);
    root.closest('.gm-shell')?.setAttribute('data-style',E.style);
    if(!E.started){E.started=true;
      const c=String(head.centre||'').split(',').map(Number);if(c.length===2&&c.every(Number.isFinite)){const [x,y]=E.toXY(c[0],c[1]);E.cam.x=x;E.cam.y=y;E.cam.dist=1400*E.scaleAt(y)}
      // GPU set-up is one-time and cannot be split below the part's 32 ms budget (see README, rough spots): it runs
      // just after this continuation, outside the part's ownership
      Promise.resolve().then(()=>{try{E.initGL()}catch(err){E.status='The map could not start drawing: '+(err.message||err)}showStatus();E.buildRoutes();E.ask()});
    }
    E.setLayers(rows,head.hidden||settings.hide||'');
    const fl=String(api.view().fly||'');if(fl&&fl!==E.lastFly){E.lastFly=fl;const r=E.routes.find(r=>r.id===fl.split('@')[0]);if(r)E.flyAlong(geoParsePath(r.path).map(([la,lo])=>E.toXY(la,lo)))}
    // fly to a focus asked for in words (map.show) or chosen in search
    const f=String(head.focus||settings.focus||'');if(f&&f!==E.lastFocus){E.lastFocus=f;const [ll]=f.split('@');const [la,lo]=ll.split(',').map(Number);if(Number.isFinite(la)){const [x,y]=E.toXY(la,lo);E.focusOn(x,y,Math.min(E.cam.dist,600*E.scaleAt(y)))}}
    const vf=view.focus;if(vf&&vf.stamp!==E.lastViewFocus){E.lastViewFocus=vf.stamp;const [x,y]=E.toXY(vf.lat,vf.lon);E.focusOn(x,y,(vf.dist||Math.min(E.cam.dist/E.scaleAt(E.cam.y),520))*E.scaleAt(y))}
    // the route being planned: its street path as a preview
    const key=JSON.stringify(E.stops.map(s=>[s.lat,s.lon]))+(view.mode||'walk');
    if(E.tool==='route'&&E.stops.length>1){if(key!==E.previewKey){E.previewKey=key;api.rows('map.path stops='+mapQ(E.stops.map(s=>s.ref||(s.lat.toFixed(6)+','+s.lon.toFixed(6))).join(' > '))+' mode='+(view.mode||'walk')+' map='+mapQ(map))
      .then(api.guard(r=>{const row=mapRows(r)[0];E.preview=row?geoParsePath(row.path):null;E.buildRoutes();E.ask()}),()=>{E.preview=null;E.buildRoutes();E.ask()})}}
    else if(E.preview){E.preview=null;E.previewKey='';E.buildRoutes()}
    E.ask();
  }),api.guard(err=>{E.status='The map words did not answer: '+String(err?.message||err).split('\n')[0];showStatus()}));
  return root;
}

// ---- map-layers ------------------------------------------------------------------------------------------------------
function mountLayers(api,settings){
  const card=api.part('layers','section',{class:'gm-card','aria-label':'Layers'});
  const controlId=key=>'gm-'+String(api.node.path||'map').replace(/[^a-z0-9_-]/gi,'-')+'-'+key;
  const add=mapEl('button',{type:'button',class:'gm-btn gm-primary gm-small','aria-expanded':String(!!api.draft.newLayer)},'+ Add a layer');
  card.append(mapEl('h3',{},mapIcon('layers'),api.label('title','Layers'),mapHas(api,'make')?add:null));
  const body=mapEl('div');card.append(body);
  // local toggles (an editor open, the gallery) repaint this card only: the painter skips identical plans
  const paint=rows=>{
    const list=mapEl('div',{role:'list'});body.replaceChildren();
    const head=rows.find(r=>r.kind==='map')||{};const hidden=new Set(String(head.hidden||'').split(/\s+/).filter(Boolean));
    const layers=rows.filter(r=>r.kind!=='map');
    add.setAttribute('aria-expanded',String(!!api.draft.newLayer));add.textContent=api.draft.newLayer?'Close':'+ Add a layer';
    add.onclick=()=>{api.draft.newLayer=!api.draft.newLayer;api.draft.template=null;paint(rows)};
    if(api.draft.newLayer)body.append(gallery(rows,layers));
    body.append(list);
    if(!layers.length)list.append(mapEl('p',{class:'gm-empty'},'No layers yet. Add one, or say ',mapEl('code',{},'make kind=map-layer map='+(head.name||settings.map)+' name=… shows="rows spot"')));
    for(const L of layers){
      const on=!hidden.has(L.id)&&L.on!=='no';
      const box=mapEl('input',{type:'checkbox',id:controlId(L.id),'aria-label':'Show '+L.name,on:{change:()=>mapFire(api,box.checked?'unhide':'hide',{layer:L.id})}});box.checked=on;
      const row=api.part('layer','div',{class:'gm-layer',role:'listitem',title:'Shows: '+(L.shows||'')+(L.by?' · made by '+L.by:'')},
        box,mapEl('span',{class:'gm-swatch',style:{background:L.color||'#cf5a3c'}}),mapEl('label',{for:controlId(L.id)},L.name||'A layer',L.only==='me'||L.sees==='me'||String(L.sees||'').startsWith('person:')?mapEl('span',{class:'gm-mine'},'only you'):null),
        mapEl('span',{class:'gm-count'},String(L.count||0)+(L.unplaced?' · '+L.unplaced+' unplaced':'')));
      row.setAttribute('data-fact-layer',String(L.name||'').toLowerCase().replace(/[^a-z0-9-]+/g,'-'));
      if(L.error)row.append(mapEl('span',{class:'gm-err'},L.error));
      list.append(row);
      const canEdit=mapHas(api,'edit-layer');
      if(canEdit){const more=mapEl('button',{type:'button',class:'gm-more','aria-label':'Change '+L.name,'aria-expanded':String(api.draft.editLayer===L.id),on:{click:()=>{api.draft.editLayer=api.draft.editLayer===L.id?'':L.id;paint(rows)}}},'⋯');row.append(more)}
      if(canEdit&&api.draft.editLayer===L.id)list.append(editor(L,rows));
    }
    // the ground's own layers, for you
    list.append(mapEl('div',{class:'gm-sub'},'The ground'));
    for(const [key,label,sw] of [['buildings','Buildings','#efcfa9'],['shadows','Shadows','#8a8378'],['labels','Street and town names','#fffdf8'],['places','Shops, parks and stops','#4f9a4a']]){
      const id='ground:'+key;const box=mapEl('input',{type:'checkbox',id:controlId('g-'+key),on:{change:()=>mapFire(api,box.checked?'unhide':'hide',{layer:key})}});box.checked=!hidden.has(id);
      list.append(mapEl('div',{class:'gm-layer'},box,mapEl('span',{class:'gm-swatch',style:{background:sw}}),mapEl('label',{for:controlId('g-'+key)},label),mapEl('span'),mapEl('span')));
    }
    if(mapHas(api,'style')){
      list.append(mapEl('div',{class:'gm-sub'},'How it looks (for you)'));
      const cur=head.mystyle||'day';const st=mapEl('div',{class:'gm-styles',role:'radiogroup','aria-label':'Map look'});
      for(const [k,S] of Object.entries(GEO_STYLES))st.append(mapEl('button',{type:'button',role:'radio','aria-checked':String(cur===k),'aria-pressed':String(cur===k),
        style:{background:`linear-gradient(160deg,${S.sky} 0 38%,${S.land} 38% 62%,${S.area.water} 62%)`,color:S.town},on:{click:()=>mapFire(api,'style',{style:k})}},S.name));
      list.append(st);
    }
  };
  function editor(L,rows){
    const name=mapEl('input',{type:'text',value:L.name||'','aria-label':'Layer name'}),shows=mapEl('input',{type:'text',value:L.shows||'','aria-label':'The reading it shows'});
    const look=mapEl('select',{'aria-label':'How it looks'});for(const [v,label] of [['pin','Pins'],['dot','Dots'],['place','Little houses'],['label','Names only'],['path','Paths (routes)']])look.append(mapEl('option',{value:v,selected:(L.look||'pin')===v},label));
    let colour=L.color||'#cf5a3c';const chips=chipsFor(colour,c=>{colour=c});
    return mapForm(api,{class:'gm-form'},()=>{api.draft.editLayer='';mapFire(api,'edit-layer',{layer:L.id,fields:{name:name.value.trim()||L.name,shows:shows.value.trim()||L.shows,look:look.value,color:colour},saw:{[L.id]:L.rev}},'Changed '+(name.value.trim()||L.name))},
      mapEl('label',{},'Name',name),mapEl('label',{},'Shows',shows),mapEl('label',{},'Looks like',look),mapEl('label',{},'Colour',chips),
      mapEl('div',{class:'gm-actions'},mapEl('button',{type:'submit',class:'gm-btn gm-primary'},'Save'),
        mapHas(api,'make')?mapEl('button',{type:'button',class:'gm-btn',on:{click:()=>{api.draft.editLayer='';mapFire(api,'make',{map:mapHead(rows).id||settings.map,name:(L.name||'Layer')+' (mine)',shows:L.shows,color:L.color||'#cf5a3c',look:L.look||'pin'},'Made your own copy of '+L.name)}}},'Copy it'):null,
        mapHas(api,'forget-layer')?mapEl('button',{type:'button',class:'gm-btn',on:{click:()=>{api.draft.editLayer='';mapFire(api,'forget-layer',{layer:L.id,saw:{[L.id]:L.rev}},'Removed the layer. Undo brings it back.')}}},'Remove'):null),
      mapEl('div',{class:'gm-line'},'runs: '+mapLineOf(api,'edit-layer')));
  }
  function chipsFor(colour,set){const chips=mapEl('div',{class:'gm-chips',role:'radiogroup','aria-label':'Colour'});
    for(const c of MAP_LAYER_COLOURS){const b=mapEl('button',{type:'button',role:'radio','aria-checked':String(c===colour),'aria-pressed':String(c===colour),'aria-label':c,style:{background:c},on:{click:()=>{set(c);chips.querySelectorAll('button').forEach(x=>{const on=x===b;x.setAttribute('aria-pressed',String(on));x.setAttribute('aria-checked',String(on))})}}});chips.append(b)}
    return chips}
  // + Add a layer: start from something, see what it finds, name it, choose a look, share it or keep it
  function gallery(rows,layers){
    const box=mapEl('div',{class:'gm-form'});const t=api.draft.template;
    const g=mapEl('div',{class:'gm-gallery',role:'radiogroup','aria-label':'Start from'});
    MAP_TEMPLATES.forEach((T,i)=>g.append(mapEl('button',{type:'button',role:'radio','aria-pressed':String(t===i),'aria-checked':String(t===i),on:{click:()=>{api.draft.template=i;paint(rows)}}},T.title,mapEl('small',{},T.blurb))));
    box.append(g);if(t==null)return box;
    const T=MAP_TEMPLATES[t];const name=mapEl('input',{type:'text',value:T.ask?'':T.title,placeholder:'What shall it be called?','aria-label':'Layer name'});
    const ask=mapEl('input',{type:'text','aria-label':T.ask||'',placeholder:{kind:'carpool, offer, ask …',tag:'dogs',place:'Seabright & Murray',reading:T.shows||'rows spot tags=dogs'}[T.ask]||''});
    if(T.ask==='reading')ask.value=T.shows;
    const look=mapEl('select',{'aria-label':'How it looks'});for(const [v,label] of [['pin','Pins'],['dot','Dots'],['place','Little houses'],['label','Names only'],['path','Paths (routes)']])look.append(mapEl('option',{value:v,selected:T.look===v},label));
    let colour=T.color||MAP_LAYER_COLOURS[layers.length%MAP_LAYER_COLOURS.length];const chips=chipsFor(colour,c=>{colour=c});
    const who=mapEl('div',{class:'gm-seg',role:'group','aria-label':'Who sees it'});let mine=false;
    for(const [v,label] of [[false,'Everyone'],[true,'Only me']])who.append(mapEl('button',{type:'button','aria-pressed':String(v===mine),on:{click:e=>{mine=v;who.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b===e.currentTarget)))}}},label));
    const preview=mapEl('div',{class:'gm-empty'});
    const reading=()=>{const v=ask.value.trim();if(T.ask==='reading')return v;if(T.ask==='kind')return v?'rows '+v.split(/\s+/)[0]:'';if(T.ask==='tag')return v?'rows spot tags='+mapQ(v):'';if(T.ask==='place')return v?'map.near '+mapQ(v)+' within=400':'';return T.shows};
    let timer;const check=()=>{clearTimeout(timer);const r=reading();if(!r){preview.textContent='';return}preview.textContent='Looking…';
      timer=setTimeout(()=>api.rows(r).then(api.guard(rows=>{const n=mapRows(rows).filter(x=>x.id).length;preview.textContent='It finds '+n+' thing'+(n===1?'':'s')+' you can see now.'}),e=>{preview.textContent=String(e?.message||e).split('\n')[0]}),250)};
    ask.addEventListener('input',check);check();
    const form=mapForm(api,{class:'gm-form'},()=>{const r=reading();const n=name.value.trim()||(T.ask&&ask.value.trim()?T.title.replace('…','')+' '+ask.value.trim():T.title);if(!r){ask.focus();return}
      api.draft.newLayer=false;api.draft.template=null;mapFire(api,mine&&mapHas(api,'make-mine')?'make-mine':'make',{map:mapHead(rows).id||settings.map,name:n,shows:r,color:colour,look:look.value},'Made the layer '+n)},
      T.ask?mapEl('label',{},{kind:'Which kind',tag:'Which tag',place:'Near what',reading:'The reading'}[T.ask],ask):null,preview,
      mapEl('label',{},'Name',name),mapEl('label',{},'Looks like',look),mapEl('label',{},'Colour',chips),
      mapHas(api,'make-mine')?mapEl('label',{},'Who sees it',who):null,
      mapEl('button',{type:'submit',class:'gm-btn gm-primary'},'Make the layer'),mapEl('div',{class:'gm-line'},'runs: '+mapLineOf(api,'make')));
    box.append(form);return box;
  }
  mapReadLayers(api,settings.map||'').then(api.guard(paint),api.guard(err=>body.append(mapEl('p',{class:'gm-err'},String(err?.message||err)))));
  return card;
}

// ---- map-search ------------------------------------------------------------------------------------------------------
function mountSearch(api,settings){
  const box=api.part('search','div',{class:'gm-search'});
  const d=api.draft;const input=mapEl('input',{type:'search',placeholder:api.label('placeholder','Search places, streets, towns, things'),'aria-label':'Search the map',value:d.text||''});
  const icon=mapEl('span');icon.innerHTML='<svg width="15" height="15" viewBox="0 0 16 16" aria-hidden="true"><circle cx="7" cy="7" r="5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M11 11l4 4" stroke="currentColor" stroke-width="2"/></svg>';
  const results=mapEl('div',{class:'gm-results',role:'listbox',hidden:!(d.rows&&d.rows.length)});
  const choose=r=>{d.rows=[];results.hidden=true;const stamp=Date.now();
    const far=/administrative|city|town|county|state/.test(String(r.what||''));
    const sel=r.id?{kind:'thing',thing:r.id,name:r.name}:{kind:'ground',type:'place',name:r.name,what:r.what,lat:r.lat,lon:r.lon};
    api.select({focus:mapJ({lat:r.lat,lon:r.lon,stamp,dist:far?9000:450}),selected:mapJ(sel)})};
  const show=rows=>{d.rows=rows;results.replaceChildren(...rows.map(r=>mapEl('button',{type:'button',role:'option',on:{click:()=>choose(r)}},mapEl('span',{},r.name),mapEl('small',{},String(r.what||'').replace(/_/g,' ')),r.where?mapEl('span',{class:'gm-rwhere'},r.where):null)));
    results.hidden=!rows.length};
  if(d.rows)show(d.rows);
  let timer;input.addEventListener('input',()=>{d.text=input.value;clearTimeout(timer);const text=input.value.trim();if(text.length<2){show([]);return}
    timer=setTimeout(()=>{const eng=document.querySelector('.gm-canvas')?.__engine;const c=eng?eng.toLL(eng.cam.x,eng.cam.y):null;
      api.rows('map.find '+text.replace(/[;\n"]/g,' ')+' map='+mapQ(settings.map||'')+(c?' near='+c[0].toFixed(4)+','+c[1].toFixed(4):'')).then(api.guard(rows=>{if(input.value.trim()===text)show(mapRows(rows))}),()=>show([]))},260)});
  input.addEventListener('keydown',e=>{if(e.key==='Enter'&&d.rows?.length){e.preventDefault();choose(d.rows[0])}if(e.key==='Escape'){input.value='';d.text='';show([])}});
  box.append(icon,input,results);return box;
}

// ---- map-inspector ---------------------------------------------------------------------------------------------------
function mountInspector(api,settings){
  const card=api.part('inspector','section',{class:'gm-card','aria-label':'Selected on the map','aria-live':'polite'});
  const sel=mapView(api).selected;const map=settings.map||'';
  const close=mapEl('button',{type:'button',class:'gm-btn gm-small','aria-label':'Close',style:{marginLeft:'auto'},on:{click:()=>api.select({selected:''})}},'×');
  const fly=(r,dist)=>api.select({selected:mapJ({kind:'thing',thing:r.id,name:mapName(r),ref:r.ref||''}),focus:mapJ({lat:Number(r.lat),lon:Number(r.lon),stamp:Date.now(),dist:dist||420})});
  if(!sel){
    // nothing pressed: what is new on the map, and how to start
    card.classList.add('gm-hello');card.append(mapEl('h3',{},'New on the map'));
    const list=mapEl('div',{class:'gm-list'});card.append(list);
    mapReadLayers(api,map).then(api.guard(rows=>{
      const items=[];for(const L of rows.filter(r=>r.kind!=='map'))for(const it of L.items||[])items.push({...it,color:L.color});
      items.sort((a,b)=>String(b.made||'').localeCompare(String(a.made||'')));
      const seen=new Set();for(const it of items){if(seen.has(it.id))continue;seen.add(it.id);if(seen.size>7)break;
        list.append(mapEl('button',{type:'button',style:{color:it.color||'#cf5a3c'},on:{click:()=>fly(it)}},mapEl('span',{class:'gm-dot'}),mapEl('span',{style:{color:'var(--ink,#26302c)'}},mapName(it)),mapEl('small',{},(it.by?it.by+' · ':'')+mapAgo(it.made))))}
      if(!seen.size)list.append(mapEl('p',{class:'gm-empty'},'Nothing placed yet. Be the first: press Add.'))}),()=>{});
    card.append(mapEl('p',{class:'gm-empty',style:{marginTop:'10px'}},'Press a building to see what happens there. Press ',mapEl('b',{},'Add'),' to put a spot, an event or a note anywhere. Every press is also a line: ',
      mapEl('code',{},'map.add "Seabright & Murray" kind=spot name="Bench"'),'.'));
    return card;
  }
  const actions=mapEl('div',{class:'gm-actions'}),lines=mapEl('div',{class:'gm-line'});
  const routeFrom=(label,lat,lon,ref)=>mapEl('button',{type:'button',class:'gm-btn',on:{click:()=>api.select({tool:'route',stops:mapJ([{label,lat,lon,ref:ref||''}])})}},'Route from here');
  // a building, or an adopted one: its card is about the place, and what happens there
  if(sel.ref){return placeCard(api,settings,card,sel,close)}
  if(sel.kind==='ground'){
    const title=sel.name||({street:'A street',area:'An area',place:'A place'}[sel.type]||'Here');
    card.append(mapEl('h3',{},'On the ground',close),mapEl('p',{class:'gm-title'},title));
    const facts=mapEl('dl',{class:'gm-facts'});const add=(k,v)=>{if(v!==undefined&&v!=='')facts.append(mapEl('dt',{},k),mapEl('dd',{},String(v)))};
    add('What',String(sel.what||sel.type||'').replace(/_/g,' '));card.append(facts);
    const where=mapEl('p',{class:'gm-where'},'…');card.insertBefore(where,facts);
    if(sel.lat!=null)api.rows('map.where '+Number(sel.lat).toFixed(6)+','+Number(sel.lon).toFixed(6)+' map='+mapQ(map)).then(api.guard(r=>{where.textContent=(mapRows(r)[0]?.where)||''}),()=>where.remove());else where.remove();
    if(mapHas(api,'put')&&sel.lat!=null){
      actions.append(mapEl('button',{type:'button',class:'gm-btn gm-warm',on:{click:()=>mapFire(api,'put',{place:mapPlaceArg(sel),kind:'spot',fields:{name:sel.name||'A spot'},select:{selected:''}},'Added '+(sel.name||'a spot'))}},'Add as a spot'));
      lines.textContent='Add runs: '+mapLineOf(api,'put');
    }
    if(sel.lat!=null)actions.append(routeFrom(title,Number(sel.lat),Number(sel.lon)));
    card.append(actions,lines);return card;
  }
  // a thing in the world: every fact it has (as you may see it), where it is, what is near
  card.append(mapEl('h3',{},sel.layer||'In the world',close),mapEl('p',{class:'gm-title'},sel.name||'A thing'));
  const where=mapEl('p',{class:'gm-where'},'…'),facts=mapEl('dl',{class:'gm-facts'}),near=mapEl('div',{class:'gm-list'});
  card.append(where,facts,actions,near,lines);
  api.rows('map.where '+sel.thing+' map='+mapQ(map)).then(api.guard(r=>{if(!where.querySelector('.gm-big'))where.textContent=mapRows(r)[0]?.where||''}),()=>{if(!where.querySelector('.gm-big'))where.textContent=''});
  api.read('look '+sel.thing).then(api.guard(rows=>{
    const t=mapRows(rows)[0];if(!t){facts.append(mapEl('dd',{},'You cannot see this any more.'));return}
    if(t.kind==='structure'&&t.ref){card.replaceChildren();placeCard(api,settings,card,{...sel,ref:t.ref,thing:t.id,name:t.name,lat:t.lat,lon:t.lon},close);return}
    const skip=new Set(['id','rev','groups','sees','path','stop_points','made_by','for']);
    for(const [k,v] of Object.entries(t)){if(skip.has(k)||k.startsWith('in:')||k.startsWith('member:')||typeof v==='object')continue;
      const shown=['made','changed','planned'].includes(k)?api.P.formatValue(v,'short-relative'):String(v).slice(0,240);
      const dd=mapEl('dd',{title:String(v)},shown);facts.append(mapEl('dt',{},k.replace(/_/g,' ')),dd);
      // an id is shown as the thing's name, and pressing it goes there (never a bare id)
      if(/^[a-z]{2,4}\d+$/.test(String(v))&&k!=='kind')api.read('look '+v).then(api.guard(rows=>{const o=mapRows(rows)[0];if(!o)return;
        dd.replaceChildren(mapEl('button',{type:'button',class:'gm-link',on:{click:()=>api.select({selected:mapJ({kind:'thing',thing:o.id,name:mapName(o),ref:o.ref||''}),...(o.lat?{focus:mapJ({lat:Number(o.lat),lon:Number(o.lon),stamp:Date.now()})}:{})})}},mapName(o)))}),()=>{});
      else if(/\b[a-z]{2,4}\d+\b/.test(String(v))){const ids=[...new Set(String(v).match(/\b[a-z]{2,4}\d+\b/g))];
        Promise.all(ids.map(id=>api.read('look '+id).then(r=>[id,mapRows(r)[0]],()=>[id,null]))).then(api.guard(pairs=>{let text=String(v);
          for(const [id,o] of pairs)if(o)text=text.split(id).join(mapName(o));dd.textContent=text.slice(0,240)}))}
    }
    const field=t.title!==undefined?'title':'name';
    if(mapHas(api,'edit')){
      const editing=api.draft.editing===sel.thing;
      if(editing){const input=mapEl('input',{type:'text',value:t[field]||'','aria-label':'New '+field});
        const form=mapForm(api,{class:'gm-form'},()=>{api.draft.editing='';mapFire(api,'edit',{thing:sel.thing,fields:{[field]:input.value.trim()},saw:{[sel.thing]:t.rev},select:{selected:mapJ({...sel,name:input.value.trim()})}},'Renamed')},
          input,mapEl('div',{class:'gm-actions'},mapEl('button',{type:'submit',class:'gm-btn gm-primary'},'Save'),mapEl('button',{type:'button',class:'gm-btn',on:{click:()=>{api.draft.editing='';card.replaceWith(mountInspector(api,settings))}}},'Cancel')));
        actions.append(form);setTimeout(()=>input.focus(),20)}
      else actions.append(mapEl('button',{type:'button',class:'gm-btn',on:{click:()=>{api.draft.editing=sel.thing;card.replaceWith(mountInspector(api,settings))}}},'Rename'));
    }
    if(t.kind==='route'){
      where.replaceChildren(mapEl('span',{class:'gm-big'},mapMetres(t.metres)+' · '+t.minutes+' min'),' ',mapEl('span',{},t.mode==='bike'?'by bike':'on foot'));
      actions.append(mapEl('button',{type:'button',class:'gm-btn gm-primary',on:{click:()=>api.select({fly:sel.thing+'@'+Date.now()})}},'Fly along it'));
      if(mapHas(api,'replan'))actions.append(mapEl('button',{type:'button',class:'gm-btn',on:{click:()=>mapFire(api,'replan',{route:sel.thing,saw:{[sel.thing]:t.rev}},'Replanned')}},'Replan'));
    }
    else if(t.lat!==undefined){const ll=[Number(t.lat),Number(t.lon)];if(ll.every(Number.isFinite))actions.append(routeFrom(sel.name,ll[0],ll[1],sel.thing))}
    if(mapHas(api,'forget'))actions.append(mapEl('button',{type:'button',class:'gm-btn',on:{click:()=>mapFire(api,'forget',{thing:sel.thing,saw:{[sel.thing]:t.rev},select:{selected:''}},'Removed. Undo brings it back.')}},'Remove'));
    lines.textContent=['edit','forget','replan'].map(e=>mapLineOf(api,e)).filter(Boolean).map(l=>'runs: '+l).join('\n');
  }),api.guard(e=>facts.append(mapEl('dd',{},String(e?.message||e)))));
  api.rows('map.near '+sel.thing+' within=250 map='+mapQ(map)).then(api.guard(rows=>{
    rows=mapRows(rows).filter(r=>r.id!==sel.thing).slice(0,6);if(!rows.length)return;
    near.append(mapEl('div',{class:'gm-sub'},'Near here'));
    for(const r of rows)near.append(mapEl('button',{type:'button',on:{click:()=>fly(r)}},mapEl('span',{}),mapEl('span',{},mapName(r)),mapEl('small',{},r.metres+' m')));
  }),()=>{});
  return card;
}
// A building's card: what it is, what is at it, the talk about it, and its page. Nothing is made until someone adds.
function placeCard(api,settings,card,sel,close){
  const map=settings.map||'';
  const head=mapEl('div');const at=mapEl('div',{class:'gm-list'});const talk=mapEl('div',{class:'gm-talk'});const actions=mapEl('div',{class:'gm-actions'});const lines=mapEl('div',{class:'gm-line'});
  card.append(mapEl('h3',{},sel.thing?'A place':'A building',close),head,actions,at,talk,lines);
  head.append(mapEl('p',{class:'gm-title'},sel.name||(sel.number?sel.number:'A building')));
  const line='map.place '+(sel.thing||sel.ref)+(sel.thing?'':' lat='+Number(sel.lat).toFixed(6)+' lon='+Number(sel.lon).toFixed(6));
  api.rows(line).then(api.guard(rows=>{
    rows=mapRows(rows);const P=rows.find(r=>r.row==='place')||{};const things=rows.filter(r=>r.row==='at'),posts=rows.filter(r=>r.row==='talk');
    head.replaceChildren(mapEl('p',{class:'gm-title'},P.name||sel.name||'A building'));
    const kick=mapEl('div',{class:'gm-kicker'});const what=String(P.class||P.subtype||sel.what||'building').replace(/_/g,' ');kick.append(mapEl('span',{class:'gm-tag'},what));
    if(P.height||sel.h)kick.append(mapEl('span',{class:'gm-tag'},'about '+Math.round(Number(P.height||sel.h))+' m tall'+(P.num_floors||sel.floors?' · '+(P.num_floors||sel.floors)+' floors':'')));
    const src=P.src||sel.src;if(src&&!/OpenStreetMap/.test(src))kick.append(mapEl('span',{class:'gm-tag gm-imagery',title:src},'traced from imagery'));
    if(P.street)kick.append(mapEl('span',{class:'gm-tag'},'on '+P.street));
    head.append(kick);
    const thing=P.thing||sel.thing||'';const place=thing||P.ref||sel.ref;
    // what is here
    if(things.length){at.append(mapEl('div',{class:'gm-sub'},'Here'));
      things.sort((a,b)=>String(a.start||'z').localeCompare(String(b.start||'z')));
      for(const t of things.slice(0,8))at.append(mapEl('button',{type:'button',on:{click:()=>api.select({selected:mapJ({kind:'thing',thing:t.id,name:mapName(t)})})}},mapEl('span',{},MAP_KIND_ICON[t.kind]||'•'),mapEl('span',{},mapName(t)),mapEl('small',{},t.start?geoWhen(t.start):(t.by||''))))}
    else at.append(mapEl('p',{class:'gm-empty'},thing?'Nothing is planned here yet.':'Nobody has put anything here yet. Be the first.'));
    if(posts.length){talk.append(mapEl('div',{class:'gm-sub'},'Talk'));for(const p of posts.slice(-3))talk.append(mapEl('div',{class:'gm-post'},String(p.text||''),mapEl('small',{},(p.by||'')+' · '+mapAgo(p.made))))}
    if(thing&&mapHas(api,'say')){const input=mapEl('input',{type:'text',placeholder:'Say something about this place','aria-label':'Say something'});
      // a post changes nothing this window watches, so the card reads its place again itself
      talk.append(mapForm(api,{class:'gm-say'},()=>{const v=input.value.trim();if(!v)return;input.value='';mapFire(api,'say',{text:v,thing},'Said').then(api.guard(()=>card.replaceWith(mountInspector(api,settings))))},input,mapEl('button',{type:'submit',class:'gm-btn gm-small'},'Say')))}
    // what you can do here
    const put=(kind,label,fields)=>mapEl('button',{type:'button',class:'gm-btn'+(kind==='event'?' gm-warm':''),on:{click:()=>{
      const E=document.querySelector('.gm-canvas')?.__engine;if(!E){return}
      const [x,y]=E.toXY(Number(P.lat||sel.lat),Number(P.lon||sel.lon));E.tool='add';E.api&&(E.api.draft.addKind=kind);
      E.onPress?.({type:'building',what:{type:'building',ref:P.ref||sel.ref,name:P.name||sel.name,number:P.number||sel.number},lat:Number(sel.lat||P.lat),lon:Number(sel.lon||P.lon)})}}},label);
    if(mapHas(api,'put')){actions.append(put('event','+ Event here'),put('note','+ Note'))}
    const page=P.page||'place-page';
    if(thing&&mapHas(api,'open-page'))actions.append(mapEl('button',{type:'button',class:'gm-btn gm-primary',on:{click:()=>mapFire(api,'open-page',{page,thing},'Opening its page')}},'Open its page'));
    if(!thing&&mapHas(api,'adopt'))actions.append(mapEl('button',{type:'button',class:'gm-btn gm-primary',on:{click:async()=>{
      const out=await mapFire(api,'adopt',{place:P.ref||sel.ref,lat:String(sel.lat),lon:String(sel.lon),name:P.name||sel.name||''},'It has a page now');
      const made=out?.made?.[0]||out?.rows?.[0]?.id;if(made&&mapHas(api,'open-page'))mapFire(api,'open-page',{page,thing:made})}}},'Give it a page'));
    lines.textContent=['put','adopt','open-page','say'].filter(e=>mapHas(api,e)).map(e=>e+' runs: '+mapLineOf(api,e)).join('\n');
  }),api.guard(e=>head.append(mapEl('p',{class:'gm-err'},String(e?.message||e).split('\n')[0]))));
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
    api.read(line).then(api.guard(r=>{const row=mapRows(r)[0];if(!row)return;
      numbers.replaceChildren(mapEl('div',{class:'gm-big'},mapMetres(row.metres)+' · '+row.minutes+' min'),
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

// ---- a place's page ---------------------------------------------------------------------------------------------------
// The page is a window opened on a structure (window.open <page> <structure>): the painter's view says which, as
// $view.target. Each part reads `map.place $view.target` (a watched reading), so the page stays live.
function mapPlaceRows(api){return api.read('map.place '+mapQ(mapView(api).target||'')).then(mapRows)}
function mountPlacePage(api,settings){
  const root=api.part('page','div',{class:'pp'});if(settings.accent)root.style.setProperty('--pp-accent',settings.accent);
  const wrap=mapEl('div',{class:'pp-wrap'});root.append(wrap);
  if(!mapView(api).target){wrap.append(mapEl('div',{class:'pp-none'},'This page is not about a place yet. Open it from the map: press a building, then Open its page.'));return root}
  for(const child of api.children)wrap.append(api.render(child));
  return root;
}
function mountPlaceHead(api,settings){
  const head=api.part('head','header',{class:'pp-head'});
  const title=mapEl('div',{class:'pp-title'});head.append(title);
  const bar=mapEl('div',{class:'pp-bar',style:{marginTop:'10px'}});
  const outer=mapEl('div',{},head,bar);
  mapPlaceRows(api).then(api.guard(rows=>{
    const P=rows.find(r=>r.row==='place');if(!P){title.append(mapEl('h1',{},'A place'));return}
    title.replaceChildren(...[settings.badge?mapEl('span',{class:'pp-badge'},settings.badge):null].filter(Boolean),mapEl('h1',{},P.name||'A place'),
      mapEl('div',{class:'pp-meta'},[String(P.class||P.subtype||'').replace(/_/g,' '),P.street?'on '+P.street:'',P.height?'about '+Math.round(P.height)+' m tall':''].filter(Boolean).join(' · ')));
    // a small 3D view of the place, the same engine as the map
    const d=api.draft;if(!d.engine)d.engine=new GeoEngine(String(geoWorkerMain));const E=d.engine;
    const root=mapEl('div',{class:'gm-root'});head.prepend(root);E.attach(root,api);
    E.fetchTile=key=>E.api.rows('map.tile '+key).then(r=>{const x=mapRows(r)[0];if(!x||!x.chunk)throw Error('no tile');return x.chunk});
    E.selRef=P.ref||'';E.hidden=new Set(['ground:places']);
    if(!d.placed){d.placed=true;const [x,y]=E.toXY(Number(P.lat),Number(P.lon));Object.assign(E.cam,{x,y,dist:230*E.scaleAt(y),pitch:56,bearing:-25})}
    Promise.resolve().then(()=>{try{E.initGL()}catch{}E.ask()});
    if(P.thing&&settings.show!=='no'&&mapHas(api,'show'))bar.append(mapEl('button',{type:'button',class:'gm-btn',on:{click:()=>mapFire(api,'show',{thing:P.thing},'Your map turns there')}},'Show on the map'));
    if(P.thing&&mapHas(api,'edit')){const editing=!!d.renaming;
      if(editing){const input=mapEl('input',{type:'text',value:P.name||'','aria-label':'Name'});bar.append(mapForm(api,{class:'gm-say'},()=>{d.renaming=false;mapFire(api,'edit',{thing:P.thing,fields:{name:input.value.trim()},saw:{[P.thing]:P.rev}},'Renamed')},input,mapEl('button',{type:'submit',class:'gm-btn gm-small'},'Save')))}
      else bar.append(mapEl('button',{type:'button',class:'gm-btn',on:{click:()=>{d.renaming=true;outer.replaceWith(mountPlaceHead(api,settings))}}},'Rename'))}
  }),()=>title.append(mapEl('h1',{},'A place')));
  return outer;
}
function mountPlaceList(api,settings){
  const sec=api.part('section','section',{class:'pp-section'});
  const fields=String(settings.fields||'title start').split(/\s+/).filter(Boolean);
  const addLabel=settings.add||'Add';const open=!!api.draft.adding;
  const btn=mapHas(api,'add')?mapEl('button',{type:'button',class:'gm-btn gm-small'+(open?'':' gm-primary'),on:{click:()=>{api.draft.adding=!api.draft.adding;sec.replaceWith(mountPlaceList(api,settings))}}},open?'Close':'+ '+addLabel):null;
  sec.append(mapEl('h2',{},settings.title||'Here',btn));
  const list=mapEl('div',{class:'gm-list'});sec.append(list);
  if(open){
    const inputs={};const said=mapEl('div',{class:'gm-line'});
    for(const f of fields){inputs[f]=f==='text'?mapEl('textarea',{rows:3,'aria-label':f}):mapEl('input',{type:'text','aria-label':f,placeholder:{title:'What is it?',start:'When? Sat 7pm, Nov 2 18:00',name:'Name',text:'A few words'}[f]||f});
      if(f==='start')inputs[f].addEventListener('input',()=>{const r=api.P.parseDateEntry?.(inputs.start.value);said.textContent=inputs.start.value.trim()?(r?.ok?r.label:r?.message||''):''})}
    const form=mapForm(api,{class:'gm-form'},()=>{const out={};for(const f of fields){let v=inputs[f].value.trim();if(!v){inputs[f].focus();return}
        if(f==='start'){const r=api.P.parseDateEntry?.(v);if(!r?.ok){inputs[f].focus();return}v=r.iso}out[f]=v}
      if(settings.type)out.type=settings.type;
      api.draft.adding=false;mapPlaceRows(api).then(rows=>{const P=rows.find(r=>r.row==='place');mapFire(api,'add',{thing:P?.thing||mapView(api).target,fields:out},'Added')})},
      ...fields.map(f=>mapEl('label',{},{title:'What',start:'When',name:'Name',text:'Note'}[f]||f,inputs[f])),said,
      mapEl('button',{type:'submit',class:'gm-btn gm-primary'},addLabel),mapEl('div',{class:'gm-line'},'runs: '+mapLineOf(api,'add')));
    sec.append(form);
  }
  mapPlaceRows(api).then(api.guard(rows=>{
    let items=rows.filter(r=>r.row==='at'&&(!settings.kind||r.kind===settings.kind)&&(!settings.type||r.type===settings.type));
    const now=new Date().toISOString().slice(0,16);
    if(settings.kind==='event'){items.sort((a,b)=>String(a.start||'').localeCompare(String(b.start||'')));if(settings.past!=='yes')items=items.filter(i=>!i.start||String(i.start)>=now.slice(0,10))}
    else items.sort((a,b)=>String(b.made||'').localeCompare(String(a.made||'')));
    if(!items.length){list.append(mapEl('p',{class:'gm-empty'},settings.empty||'Nothing here yet.'));return}
    for(const it of items)list.append(mapEl('div',{class:'gm-item'},it.start?mapEl('span',{class:'pp-when'},geoWhen(it.start)):mapEl('span',{},MAP_KIND_ICON[it.kind]||'•'),
      mapEl('span',{},mapName(it)),mapEl('small',{},(it.by||'')+(it.made?' · '+mapAgo(it.made):''))));
  }),()=>{});
  return sec;
}
function mountPlaceTalk(api,settings){
  const sec=api.part('talk','section',{class:'pp-section'});sec.append(mapEl('h2',{},settings.title||'Talk'));
  const list=mapEl('div',{class:'gm-talk'});sec.append(list);
  mapPlaceRows(api).then(api.guard(rows=>{
    const P=rows.find(r=>r.row==='place');const posts=rows.filter(r=>r.row==='talk');
    if(!posts.length)list.append(mapEl('p',{class:'gm-empty'},settings.empty||'No one has said anything yet.'));
    for(const p of posts)list.append(mapEl('div',{class:'gm-post'},String(p.text||''),mapEl('small',{},(p.by||'')+' · '+mapAgo(p.made),
      mapHas(api,'like')?mapEl('button',{type:'button',class:'gm-link',style:{marginLeft:'8px'},on:{click:()=>mapFire(api,'like',{post:p.id},'Liked')}},'♥ '+(p.likes||'')):null)));
    if(P?.thing&&mapHas(api,'say')){const input=mapEl('input',{type:'text',placeholder:settings.prompt||'Say something','aria-label':'Say something'});
      sec.append(mapForm(api,{class:'gm-say'},()=>{const v=input.value.trim();if(!v)return;input.value='';mapFire(api,'say',{text:v,thing:P.thing},'Said')},input,mapEl('button',{type:'submit',class:'gm-btn gm-primary gm-small'},'Say')),
        mapEl('div',{class:'gm-line'},'runs: '+mapLineOf(api,'say')))}
  }),()=>{});
  return sec;
}

export default {css:MAP_CSS,mount(api,settings){
  switch(api.node.component){
    case 'map-panel':return mountPanel(api,settings);
    case 'map-shell':return mountShell(api,settings);
    case 'geo-map':return mountGeoMap(api,settings);
    case 'map-layers':return mountLayers(api,settings);
    case 'map-search':return mountSearch(api,settings);
    case 'map-inspector':return mountInspector(api,settings);
    case 'map-route':return mountRoute(api,settings);
    case 'place-page':return mountPlacePage(api,settings);
    case 'place-head':return mountPlaceHead(api,settings);
    case 'place-list':return mountPlaceList(api,settings);
    case 'place-talk':return mountPlaceTalk(api,settings);
    default:throw Error('map components: no '+api.node.component);
  }
}};
