// Writing center components for the component painter. Builder draft by Claude, 27 Oct 2026, closely modelled on the
// old desk's Writing app (lenses a5911 writing and a6079 doc-page). One module serves seven names (api.node.component):
//   writing-shell  the window: a slim top bar (back, new document), the rail on the left, the desk on the right
//   doc-rail       Find a document, then the collections (doc-shelf children)
//   doc-shelf      one folding collection: its label, count, + for a new one, its documents or inner shelves
//   doc-row        one document in a shelf (look row) or on the home page (look card); pressing it opens it
//   doc-home       the desk with nothing open: plans waiting for you, recently changed
//   doc-page       one document: Markdown drawn as you write, Ctrl+E source, [[links]], comments on a selection,
//                  a plan's calls, and sending a passage or the whole document to JEFF
//   doc-comment    one comment in a page's margin: the words it is about, where they are now, reply, resolve, to JEFF
// What is open is this window's own view (open, back). Every lasting change is a gesture line in the lens.

const WR_CSS=`
html:has(.wr-shell),html:has(.wr-shell) body{overflow:clip;height:100%}
.wr-shell{position:fixed;inset:0;display:grid;grid-template-columns:var(--wr-rail,292px) minmax(0,1fr);grid-template-rows:auto minmax(0,1fr);overflow:clip;
  background:var(--ag-surface,#f7f5ef);color:var(--ag-ink,#2f3a35);font:var(--ag-text,15px)/1.5 var(--ag-font-ui,system-ui,sans-serif)}
.wr-top{grid-column:1/-1;display:flex;align-items:center;gap:6px;padding:9px 14px;border-bottom:var(--ag-border-w,1px) solid var(--ag-border,#e2dfd6);min-height:50px}
.wr-brand{display:flex;align-items:center;gap:9px;font:650 12px/1 var(--ag-font-display,inherit);letter-spacing:.16em;text-transform:uppercase;color:var(--ag-ink-muted,#7b847f);margin-right:10px;user-select:none}
.wr-brand i{display:grid;place-items:center;width:26px;height:26px;border-radius:9px;background:var(--ag-accent,#4f7a6c);color:var(--ag-accent-ink,#fff);font-style:normal;font-size:15px;letter-spacing:0}
.wr-crumb{color:var(--ag-ink-muted,#7b847f);font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}
.wr-crumb b{color:var(--ag-ink,#2f3a35);font-weight:600}
.wr-space{flex:1}
.wr-btn{all:unset;box-sizing:border-box;display:inline-flex;align-items:center;gap:6px;cursor:pointer;font:inherit;font-size:13px;line-height:1;padding:8px 12px;border-radius:var(--ag-radius-pill,999px);color:var(--ag-ink,#2f3a35);white-space:nowrap}
.wr-btn:hover{background:var(--ag-hover,#0000000d)}
.wr-btn:focus-visible{outline:2px solid var(--ag-focus,#4f7a6c);outline-offset:1px}
.wr-btn.wr-primary{background:var(--ag-accent,#4f7a6c);color:var(--ag-accent-ink,#fff);font-weight:600}
.wr-btn.wr-primary:hover{filter:brightness(1.07)}
.wr-btn.wr-soft{background:var(--ag-accent-soft,#e6efe9);color:var(--ag-ink,#2f3a35)}
.wr-btn.wr-quiet{color:var(--ag-ink-muted,#7b847f)}
.wr-btn[aria-pressed=true]{background:var(--ag-accent-soft,#e6efe9);color:var(--ag-ink,#2f3a35)}
.wr-btn[disabled]{opacity:.45;pointer-events:none}
.wr-key{font:11px/1 var(--ag-font-mono,monospace);padding:3px 5px;border-radius:5px;border:1px solid var(--ag-border,#e2dfd6);color:var(--ag-ink-muted,#7b847f)}
.wr-railbox{grid-row:2;min-height:0;display:flex;flex-direction:column;border-right:var(--ag-border-w,1px) solid var(--ag-border,#e2dfd6);
  background:color-mix(in srgb,var(--ag-raised,#fff) 45%,var(--ag-surface,#f7f5ef))}
.wr-deskbox{grid-row:2;min-height:0;min-width:0;display:flex;flex-direction:column}
.wr-deskbox>*,.wr-deskbox [data-layout=stack]{flex:1;min-height:0;display:flex;flex-direction:column}
.wr-deskbox .wr-desk,.wr-deskbox .wr-home{flex:1;min-height:0}
.wr-deskbox [data-layout=stack]:not(:has(.wr-desk,.wr-home)){flex:0 0 auto}
.wr-rail{display:flex;flex-direction:column;min-height:0;height:100%}
.wr-find{margin:12px 12px 6px;display:flex;align-items:center;gap:8px;padding:0 10px;border-radius:12px;background:var(--ag-surface,#f7f5ef);border:1px solid var(--ag-border,#e2dfd6)}
.wr-find:focus-within{border-color:var(--ag-accent,#4f7a6c);box-shadow:0 0 0 3px var(--ag-accent-soft,#e6efe9)}
.wr-find svg{flex:none;opacity:.6}
.wr-find input{all:unset;flex:1;min-width:0;padding:9px 0;font-size:14px;color:var(--ag-ink,#2f3a35)}
.wr-find input::placeholder{color:var(--ag-ink-muted,#7b847f)}
.wr-shelves{overflow:auto;padding:4px 8px 28px;min-height:0;flex:1;scrollbar-width:thin}
.wr-shelf{margin-top:10px}
.wr-shelf.wr-nested{margin:2px 0 0}
.wr-shelf-head{display:flex;align-items:center;gap:4px;border-radius:9px}
.wr-shelf-head:hover{background:var(--ag-hover,#0000000d)}
.wr-shelf-toggle{all:unset;flex:1;min-width:0;display:flex;align-items:center;gap:7px;cursor:pointer;padding:6px 8px;font:650 11.5px/1.2 var(--ag-font-ui,inherit);letter-spacing:.09em;text-transform:uppercase;color:var(--ag-ink-muted,#7b847f)}
.wr-nested>.wr-shelf-head .wr-shelf-toggle{font:500 13.5px/1.2 var(--ag-font-ui,inherit);letter-spacing:0;text-transform:none;color:var(--ag-ink,#2f3a35);padding-left:14px}
.wr-shelf-toggle:focus-visible{outline:2px solid var(--ag-focus,#4f7a6c);border-radius:8px}
.wr-chev{display:inline-block;width:10px;transition:transform .15s;opacity:.7}
.wr-shelf[data-open=true]>.wr-shelf-head .wr-chev{transform:rotate(90deg)}
.wr-count{margin-left:auto;font:600 11px/1 var(--ag-font-ui,inherit);letter-spacing:0;padding:3px 7px;border-radius:999px;background:var(--ag-hover,#0000000d);color:var(--ag-ink-muted,#7b847f)}
.wr-count.wr-hot{background:var(--ag-accent,#4f7a6c);color:var(--ag-accent-ink,#fff)}
.wr-plus{all:unset;cursor:pointer;width:24px;height:24px;display:grid;place-items:center;border-radius:7px;color:var(--ag-ink-muted,#7b847f);font-size:16px;opacity:0}
.wr-shelf-head:hover .wr-plus,.wr-plus:focus-visible{opacity:1}.wr-plus:hover{background:var(--ag-active,#0000001a);color:var(--ag-ink,#2f3a35)}
.wr-shelf-body{display:flex;flex-direction:column;gap:1px;padding:2px 0 2px}
.wr-shelf[data-open=false]>.wr-shelf-body{display:none}
.wr-empty{font-size:12.5px;color:var(--ag-ink-faint,var(--ag-ink-muted,#9aa29e));padding:4px 10px 6px 24px}
.wr-row{all:unset;box-sizing:border-box;cursor:pointer;display:flex;flex-direction:column;gap:1px;padding:7px 10px 7px 24px;border-radius:9px;position:relative}
.wr-nested .wr-row{padding-left:30px}
.wr-row:hover{background:var(--ag-hover,#0000000d)}
.wr-row:focus-visible{outline:2px solid var(--ag-focus,#4f7a6c);outline-offset:-2px}
.wr-row[aria-current=true]{background:var(--ag-accent-soft,#e6efe9)}
.wr-row[aria-current=true]::before{content:"";position:absolute;left:10px;top:9px;bottom:9px;width:3px;border-radius:3px;background:var(--ag-accent,#4f7a6c)}
.wr-nested .wr-row[aria-current=true]::before{left:16px}
.wr-row-title{font-size:14px;line-height:1.35;color:var(--ag-ink,#2f3a35);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.wr-row-meta{display:flex;align-items:center;gap:6px;font-size:11.5px;color:var(--ag-ink-muted,#7b847f);white-space:nowrap;overflow:hidden}
.wr-dot{width:7px;height:7px;border-radius:50%;background:var(--ag-warn,#c58332);flex:none}
.wr-chip{display:inline-flex;align-items:center;gap:5px;font-size:11.5px;line-height:1;padding:4px 8px;border-radius:999px;background:var(--ag-hover,#0000000d);color:var(--ag-ink-muted,#7b847f);white-space:nowrap}
.wr-chip.wr-claude{background:var(--ag-info-soft,#e7eef9);color:var(--ag-info,#507ebc)}
.wr-chip.wr-wait{background:var(--ag-warn-soft,#f8eedf);color:var(--ag-warn,#b5722a)}
.wr-chip.wr-done{background:var(--ag-ok-soft,#e5f1e8);color:var(--ag-ok,#3f8a5a)}
.wr-results{display:flex;flex-direction:column;gap:2px;padding:4px 0}
.wr-results .wr-row{padding-left:12px}
.wr-snip{font-size:12px;color:var(--ag-ink-muted,#7b847f);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.wr-snip b,.wr-row-title b{background:color-mix(in srgb,var(--ag-warn,#c58332) 30%,transparent);color:inherit;border-radius:3px;font-weight:inherit}
.wr-rail-foot{padding:8px 14px 12px;font-size:11.5px;color:var(--ag-ink-faint,var(--ag-ink-muted,#9aa29e));border-top:1px solid var(--ag-border,#e2dfd6)}
/* home */
.wr-home{overflow:auto;padding:52px 56px 64px;scrollbar-width:thin}
.wr-home-in{max-width:880px;margin:0 auto}
.wr-hello{font:600 calc(var(--ag-text,15px)*2.05)/1.15 var(--ag-font-display,inherit);margin:0 0 8px;letter-spacing:-.01em}
.wr-sub{margin:0 0 34px;color:var(--ag-ink-muted,#7b847f);font-size:15.5px}
.wr-h{font:650 11.5px/1 var(--ag-font-ui,inherit);letter-spacing:.12em;text-transform:uppercase;color:var(--ag-ink-muted,#7b847f);margin:30px 0 12px;display:flex;align-items:center;gap:8px}
.wr-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}
.wr-card{all:unset;box-sizing:border-box;cursor:pointer;display:flex;flex-direction:column;gap:8px;padding:16px 18px;border-radius:var(--ag-radius-m,16px);background:var(--ag-raised,#fff);border:1px solid var(--ag-border,#e2dfd6);transition:transform .12s,box-shadow .12s}
.wr-card:hover{transform:translateY(-1px);box-shadow:0 8px 24px #0000001f}
.wr-card:focus-visible{outline:2px solid var(--ag-focus,#4f7a6c)}
.wr-card .wr-row-title{font:600 16px/1.3 var(--ag-font-display,inherit)}
.wr-card .wr-snip{-webkit-line-clamp:3;font-size:13px}
.wr-list{display:flex;flex-direction:column;border-radius:var(--ag-radius-m,16px);border:1px solid var(--ag-border,#e2dfd6);overflow:hidden;background:var(--ag-raised,#fff)}
.wr-list .wr-row{flex-direction:row;align-items:center;justify-content:space-between;gap:12px;padding:11px 16px;border-radius:0;border-top:1px solid var(--ag-border,#e2dfd6)}
.wr-list .wr-row:first-child{border-top:0}
.wr-list .wr-row-title{-webkit-line-clamp:1}
.wr-tips{margin-top:40px;display:flex;flex-wrap:wrap;gap:8px 18px;color:var(--ag-ink-muted,#7b847f);font-size:13px}
.wr-tips span{display:inline-flex;align-items:center;gap:6px}
/* page */
.wr-desk{overflow:auto;min-height:0;scrollbar-width:thin}
.wr-page{display:grid;grid-template-columns:minmax(0,1fr) var(--wr-margin,300px);gap:28px;padding:28px 30px 80px 40px;max-width:1240px;margin:0 auto;align-items:start}
.wr-paper{min-width:0}
.wr-head{display:flex;flex-direction:column;gap:10px;margin:0 auto 18px;max-width:var(--wr-measure,740px)}
.wr-title{all:unset;box-sizing:border-box;width:100%;font:650 calc(var(--ag-text,15px)*2.1)/1.18 var(--ag-font-display,inherit);letter-spacing:-.012em;color:var(--ag-ink,#2f3a35);padding:2px 0;border-radius:8px}
.wr-title:focus{box-shadow:0 2px 0 var(--ag-accent,#4f7a6c)}
.wr-title::placeholder{color:var(--ag-ink-faint,#aab)}
.wr-meta{display:flex;flex-wrap:wrap;align-items:center;gap:6px;font-size:12.5px;color:var(--ag-ink-muted,#7b847f)}
.wr-meta .wr-sep{opacity:.5}
.wr-actions{display:flex;flex-wrap:wrap;align-items:center;gap:4px;margin-left:-10px}
.wr-plan{display:flex;flex-direction:column;gap:10px;margin:0 auto 22px;max-width:var(--wr-measure,740px);padding:14px 16px;border-radius:var(--ag-radius-m,16px);border:1px solid var(--ag-border,#e2dfd6);background:var(--ag-raised,#fff)}
.wr-plan-top{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:13.5px}
.wr-plan-top strong{font-weight:650}
.wr-plan-calls{display:flex;flex-wrap:wrap;gap:6px}
.wr-plan-calls .wr-btn{border:1px solid var(--ag-border,#e2dfd6)}
.wr-plan-calls .wr-btn[aria-pressed=true]{border-color:var(--ag-accent,#4f7a6c)}
.wr-open{font-size:13px;color:var(--ag-warn,#b5722a);display:flex;gap:8px;align-items:baseline}
.wr-sheet{max-width:var(--wr-measure,740px);margin:0 auto;position:relative;min-height:50vh}
.wr-sheet .cm-editor{min-height:50vh}
.wr-save{transition:color .2s}.wr-save-saving,.wr-save-editing{color:var(--ag-ink-faint,#a8b0ab)}.wr-save-failed{color:var(--ag-danger,#c0473f);font-weight:600}
.wr-md{font:16.5px/1.72 var(--ag-font-ui,inherit);color:var(--ag-ink,#2f3a35);overflow-wrap:anywhere;cursor:text}
.wr-md h1,.wr-md h2,.wr-md h3,.wr-md h4,.wr-md h5,.wr-md h6{font-family:var(--ag-font-display,inherit);line-height:1.25;margin:1.5em 0 .5em;letter-spacing:-.005em}
.wr-md h1{font-size:1.7em}.wr-md h2{font-size:1.32em}.wr-md h3{font-size:1.12em}.wr-md h4,.wr-md h5,.wr-md h6{font-size:1em}
.wr-md>:first-child{margin-top:0}
.wr-md p{margin:.65em 0}
.wr-md ul,.wr-md ol{margin:.5em 0;padding-left:1.5em}
.wr-md li{margin:.22em 0}.wr-md li>ul,.wr-md li>ol{margin:.15em 0}
.wr-md li.wr-task{list-style:none;margin-left:-1.4em;display:flex;gap:.55em;align-items:baseline}
.wr-md li.wr-task input{accent-color:var(--ag-accent,#4f7a6c);transform:translateY(2px);cursor:pointer}
.wr-md li.wr-task.wr-ticked>span{color:var(--ag-ink-muted,#7b847f);text-decoration:line-through;text-decoration-color:var(--ag-ink-faint,#aab)}
.wr-md blockquote{margin:.9em 0;padding:.2em 0 .2em 1em;border-left:3px solid var(--ag-accent,#4f7a6c);color:var(--ag-ink-muted,#5f6b66)}
.wr-md blockquote p{margin:.35em 0}
.wr-md code{font:.88em/1.4 var(--ag-font-mono,monospace);padding:.12em .38em;border-radius:6px;background:var(--ag-hover,#0000000d)}
.wr-md pre{margin:1em 0;padding:14px 16px;border-radius:12px;background:var(--ag-surface,#f7f5ef);border:1px solid var(--ag-border,#e2dfd6);overflow:auto}
.wr-md pre code{padding:0;background:none;font-size:13.5px;white-space:pre}
.wr-md hr{border:0;border-top:1px solid var(--ag-border,#e2dfd6);margin:2em 0}
.wr-md table{border-collapse:collapse;width:100%;margin:1em 0;font-size:14px;line-height:1.5}
.wr-md th,.wr-md td{text-align:left;vertical-align:top;padding:8px 10px;border-bottom:1px solid var(--ag-border,#e2dfd6)}
.wr-md th{font-weight:650;color:var(--ag-ink-muted,#5f6b66);font-size:12.5px;letter-spacing:.02em}
.wr-md tr:last-child td{border-bottom:0}
.wr-md strong{font-weight:650}
.wr-link{color:var(--ag-accent,#4f7a6c);text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:3px;cursor:pointer;border-radius:3px}
.wr-link:hover{background:var(--ag-accent-soft,#e6efe9)}
.wr-link.wr-missing{color:var(--ag-ink-muted,#7b847f);text-decoration-style:dashed}
.wr-ext{color:var(--ag-info,var(--ag-accent,#507ebc));text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:3px;cursor:pointer}
.wr-ext::after{content:" ↗";font-size:.8em;text-decoration:none;display:inline-block}
.wr-embed{display:flex;gap:10px;align-items:center;margin:1em 0;padding:12px 14px;border-radius:12px;border:1px solid var(--ag-border,#e2dfd6);background:var(--ag-surface,#f7f5ef);font-size:14px}
.wr-embed small{color:var(--ag-ink-muted,#7b847f)}
mark.wr-mark{background:color-mix(in srgb,var(--ag-warn,#e0a040) 26%,transparent);color:inherit;border-bottom:2px solid color-mix(in srgb,var(--ag-warn,#e0a040) 70%,transparent);border-radius:2px;cursor:pointer;transition:background .2s}
mark.wr-mark.wr-hot{background:color-mix(in srgb,var(--ag-warn,#e0a040) 55%,transparent)}
.wr-placeholder{color:var(--ag-ink-faint,#aab);font-style:italic}
.wr-tail{height:56px;cursor:text}
.wr-editor{display:block;width:100%;box-sizing:border-box;resize:none;overflow:hidden;font:15px/1.65 var(--ag-font-mono,monospace);color:var(--ag-ink,#2f3a35);
  background:color-mix(in srgb,var(--ag-accent-soft,#e6efe9) 55%,transparent);border:0;border-radius:10px;padding:10px 12px;margin:4px -12px;width:calc(100% + 24px);outline:2px solid var(--ag-accent,#4f7a6c);outline-offset:0}
.wr-source{display:block;width:100%;box-sizing:border-box;min-height:62vh;resize:vertical;font:14.5px/1.7 var(--ag-font-mono,monospace);color:var(--ag-ink,#2f3a35);background:transparent;border:0;outline:0;padding:0;tab-size:2}
.wr-srcnote{position:absolute;top:10px;right:16px;font:11px/1 var(--ag-font-mono,monospace);color:var(--ag-ink-muted,#7b847f);letter-spacing:.06em}
.wr-pick{position:absolute;z-index:40;min-width:280px;max-width:420px;max-height:260px;overflow:auto;padding:5px;border-radius:12px;background:var(--ag-raised,#fff);border:1px solid var(--ag-border,#e2dfd6);box-shadow:0 12px 32px #00000033}
.wr-pick button{all:unset;box-sizing:border-box;display:flex;justify-content:space-between;gap:12px;width:100%;padding:7px 10px;border-radius:8px;cursor:pointer;font-size:13.5px}
.wr-pick button small{color:var(--ag-ink-muted,#7b847f)}
.wr-pick button[aria-selected=true],.wr-pick button:hover{background:var(--ag-accent-soft,#e6efe9)}
.wr-pick p{margin:6px 10px;font-size:12px;color:var(--ag-ink-muted,#7b847f)}
.wr-banner{margin:0 auto 14px;max-width:var(--wr-measure,740px);padding:10px 14px;border-radius:12px;background:var(--ag-danger-soft,#fbe9e8);color:var(--ag-ink,#2f3a35);font-size:13.5px;display:flex;flex-direction:column;gap:8px}
.wr-banner textarea{font:13px/1.5 var(--ag-font-mono,monospace);min-height:80px;border-radius:8px;border:1px solid var(--ag-border,#e2dfd6);background:var(--ag-surface,#fff);color:inherit;padding:8px}
.wr-below{max-width:var(--wr-measure,740px);margin:26px auto 0;display:flex;flex-direction:column;gap:6px}
.wr-below .wr-row{padding-left:12px}
/* margin */
.wr-margin{position:sticky;top:0;display:flex;flex-direction:column;gap:10px;padding-top:6px}
.wr-page:has(>.wr-margin[data-shut]),.wr-page:has(>.wr-margin[data-over]){grid-template-columns:minmax(0,1fr)}
.wr-margin[data-over]{padding:14px 16px 24px}
.wr-shell:has(>.wr-railbox[data-shut]),.wr-shell:has(>.wr-railbox[data-over]){grid-template-columns:minmax(0,1fr)}
.wr-railbox[data-over]{border-right:0}
.wr-margin-head{display:flex;align-items:center;gap:8px;font:650 11.5px/1 var(--ag-font-ui,inherit);letter-spacing:.12em;text-transform:uppercase;color:var(--ag-ink-muted,#7b847f);padding:6px 2px}

.wr-hint{font-size:12.5px;color:var(--ag-ink-muted,#7b847f);line-height:1.5;padding:10px 12px;border-radius:12px;border:1px dashed var(--ag-border,#e2dfd6)}
.wr-c{display:flex;flex-direction:column;gap:7px;padding:12px 13px;border-radius:14px;background:var(--ag-raised,#fff);border:1px solid var(--ag-border,#e2dfd6);font-size:13.5px;line-height:1.5;transition:box-shadow .15s,border-color .15s}
.wr-c.wr-hot{border-color:var(--ag-warn,#e0a040);box-shadow:0 0 0 3px color-mix(in srgb,var(--ag-warn,#e0a040) 22%,transparent)}
.wr-c.wr-resolved{opacity:.72}
.wr-c-q{font-size:12.5px;color:var(--ag-ink-muted,#5f6b66);border-left:3px solid color-mix(in srgb,var(--ag-warn,#e0a040) 70%,transparent);padding:1px 0 1px 9px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;cursor:pointer;font-style:italic}
.wr-c-text{white-space:pre-wrap;overflow-wrap:anywhere}
.wr-c-who{display:flex;gap:6px;align-items:center;font-size:11.5px;color:var(--ag-ink-muted,#7b847f)}
.wr-c-who b{color:var(--ag-ink,#2f3a35);font-weight:600}
.wr-c-st{font-size:11.5px;color:var(--ag-ink-muted,#7b847f)}
.wr-c-st.wr-warn{color:var(--ag-warn,#b5722a)}
.wr-c-acts{display:flex;gap:2px;margin:0 -8px -6px}
.wr-c-acts .wr-btn{padding:6px 8px;font-size:12px;color:var(--ag-ink-muted,#7b847f)}
.wr-c-acts .wr-btn:hover{color:var(--ag-ink,#2f3a35)}
.wr-replies{display:flex;flex-direction:column;gap:8px;margin-left:4px;padding-left:10px;border-left:2px solid var(--ag-border,#e2dfd6)}
.wr-replies:empty{display:none}
.wr-replies .wr-c{padding:8px 0 4px;border:0;background:none;box-shadow:none}
.wr-reply{display:flex;flex-direction:column;gap:6px}
.wr-reply textarea,.wr-pop textarea{font:inherit;font-size:13.5px;line-height:1.45;min-height:64px;resize:vertical;border-radius:10px;border:1px solid var(--ag-border,#e2dfd6);background:var(--ag-surface,#fff);color:var(--ag-ink,#2f3a35);padding:8px 10px;outline:0}
.wr-reply textarea:focus,.wr-pop textarea:focus{border-color:var(--ag-accent,#4f7a6c);box-shadow:0 0 0 3px var(--ag-accent-soft,#e6efe9)}
.wr-more{all:unset;cursor:pointer;font-size:12.5px;color:var(--ag-ink-muted,#7b847f);padding:6px 2px}
.wr-more:hover{color:var(--ag-ink,#2f3a35)}
/* overlays */
.wr-menu{position:fixed;z-index:120;min-width:230px;padding:6px;border-radius:14px;background:var(--ag-raised,#fff);color:var(--ag-ink,#2f3a35);border:1px solid var(--ag-border,#e2dfd6);box-shadow:0 18px 44px #00000038;font:13.5px/1.3 var(--ag-font-ui,system-ui,sans-serif)}
.wr-menu>button{all:unset;box-sizing:border-box;display:flex;align-items:center;gap:10px;width:100%;padding:8px 10px;border-radius:9px;cursor:pointer}
.wr-menu>button:hover,.wr-menu>button:focus-visible{background:var(--ag-accent-soft,#e6efe9)}
.wr-menu>button small{margin-left:auto;color:var(--ag-ink-muted,#7b847f);font-size:11.5px}
.wr-menu>button.wr-danger{color:var(--ag-danger,#c0473f)}
.wr-menu>hr{border:0;border-top:1px solid var(--ag-border,#e2dfd6);margin:5px 4px}
.wr-menu>.wr-menu-q{font-size:12px;color:var(--ag-ink-muted,#7b847f);padding:6px 10px 4px;font-style:italic;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.wr-menu .menu-ask{margin:4px 2px 2px}
.wr-pop{position:fixed;z-index:130;width:min(420px,calc(100vw - 24px));display:flex;flex-direction:column;gap:10px;padding:14px;border-radius:16px;background:var(--ag-raised,#fff);color:var(--ag-ink,#2f3a35);border:1px solid var(--ag-border,#e2dfd6);box-shadow:0 22px 50px #00000040;font:14px/1.45 var(--ag-font-ui,system-ui,sans-serif)}
.wr-pop h4{margin:0;font-size:13px;font-weight:650;display:flex;align-items:center;gap:8px}
.wr-pop h4 i{font-style:normal;display:grid;place-items:center;width:22px;height:22px;border-radius:7px;background:var(--ag-accent,#4f7a6c);color:var(--ag-accent-ink,#fff);font-size:11px;font-weight:700}
.wr-pop blockquote{margin:0;padding:2px 0 2px 10px;border-left:3px solid color-mix(in srgb,var(--ag-warn,#e0a040) 70%,transparent);color:var(--ag-ink-muted,#5f6b66);font-size:13px;max-height:84px;overflow:auto}
.wr-pop-row{display:flex;align-items:center;gap:6px}
.wr-pop-row small{color:var(--ag-ink-muted,#7b847f);font-size:11.5px;margin-right:auto}
.wr-pop code{font:11.5px/1.4 var(--ag-font-mono,monospace);color:var(--ag-ink-muted,#7b847f);overflow-wrap:anywhere}
@media (max-width:980px){.wr-page{padding:20px 18px 60px}}
@media (prefers-reduced-motion:reduce){.wr-card,.wr-chev,.wr-c,mark.wr-mark{transition:none}}
`;

// ---- small helpers ----------------------------------------------------------------------------------------------------
const wrEl=(tag,attrs={},...kids)=>{const n=document.createElement(tag);for(const [k,v] of Object.entries(attrs||{})){if(v==null||v===false)continue;
  if(k==='on')for(const [e,f] of Object.entries(v))n.addEventListener(e,f);else if(k==='style'&&typeof v==='object')Object.assign(n.style,v);
  else if(k==='text')n.textContent=v;else if(k==='value')n.value=v;else n.setAttribute(k,v===true?'':v)}
  for(const c of kids.flat())if(c!=null&&c!==false)n.append(c.nodeType?c:document.createTextNode(String(c)));return n};
const wrRows=x=>Array.isArray(x)?x:(x?.rows||[]);
const wrTitle=d=>String(d?.title||d?.name||'Untitled');
const wrNorm=s=>String(s||'').replace(/\s+/g,' ').trim();
const wrSvg=p=>{const s=document.createElementNS('http://www.w3.org/2000/svg','svg');s.setAttribute('viewBox','0 0 24 24');s.setAttribute('width','16');s.setAttribute('height','16');
  s.setAttribute('fill','none');s.setAttribute('stroke','currentColor');s.setAttribute('stroke-width','2');s.setAttribute('stroke-linecap','round');s.setAttribute('stroke-linejoin','round');s.innerHTML=p;return s};
const WR_ICON={search:'<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',plus:'<path d="M12 5v14M5 12h14"/>',back:'<path d="M15 18l-6-6 6-6"/>',
  jeff:'<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/>',code:'<path d="m8 8-4 4 4 4M16 8l4 4-4 4"/>',more:'<circle cx="5" cy="12" r="1.3"/><circle cx="12" cy="12" r="1.3"/><circle cx="19" cy="12" r="1.3"/>',
  comment:'<path d="M4 5h16v11H8l-4 4z"/>',check:'<path d="m5 12 4.5 4.5L19 7"/>',pen:'<path d="M4 20h4L19 9l-4-4L4 16z"/>'};
const wrIcon=name=>wrSvg(WR_ICON[name]||'');
function wrAgo(api,iso){return iso?api.P.formatValue(iso,'short-relative'):''}
function wrMade(out){return (out?.made||[])[0]||(/\b(dk\d+)\b/.exec(out?.text||'')||[])[1]||''}
// act() already shows a refusal in the window's toast; keep the caller's own state and say nothing twice
async function wrFire(api,event,values,okText){const out=await api.fireLatest(api.latest(),event,values);if(okText)api.tell(okText);return out}
function wrOpen(api,id){const v=api.view();if(!id||v.open===id)return;return api.select({open:id,back:v.open||''})}
function wrHasGesture(api,event){return (api.node.gestures||[]).some(g=>g.event===event)}
function wrLineOf(api,event){return ((api.node.gestures||[]).find(g=>g.event===event)||{}).line||''}
const WR_COLLECTIONS={plans:'Plans',notes:'Notes',documentation:'Agora documentation',personal:'Personal writing'};
const wrCollection=d=>d.kind==='note'?'Notes':d.file_source?'a file':WR_COLLECTIONS[d.collection]||d.collection||'unsorted';
function wrPlanState(d){return d.plan==='waiting'?'waiting':d.plan==='answered'?'answered':''}
const WR_VERDICTS=[['build','Build it'],['changes','Build it, with my comments'],['questions','Not yet, I have questions'],['wrong','Wrong shape']];
const wrVerdictName=v=>(WR_VERDICTS.find(x=>x[0]===v)||[,v])[1];
function wrDocs(rowsA,rowsB){return [...wrRows(rowsA).filter(d=>d.kind==='document'),...wrRows(rowsB).filter(d=>d.kind==='note')]}
function wrReadDocs(api){return Promise.all([api.read('rows document'),api.read('rows note')]).then(([a,b])=>wrDocs(a,b))}
// Who made a thing, by name: a person, or an agent "for" its person (Claude for Alex). Facts carry only ids.
let WR_NAMES=null;
function wrNames(api){if(WR_NAMES&&Date.now()-WR_NAMES.at<60000)return WR_NAMES.p;
  const p=Promise.all([api.read('rows person'),api.read('rows agent')]).then(([people,agents])=>{const m=new Map(wrRows(people).map(x=>[x.id,x.name]));
    for(const a of wrRows(agents)){const l=String(a.label||'agent');m.set(a.id,l[0].toUpperCase()+l.slice(1)+(m.get(a.for)?' for '+m.get(a.for):''))}return m});
  WR_NAMES={at:Date.now(),p};return p}
function wrWho(api,f,node,prefix=''){node.textContent=prefix+(f.by&&!/^dk\d+$/.test(f.by)?f.by:'…');
  wrNames(api).then(m=>{const n=m.get(f.made_by)||m.get(f.for);if(n)node.textContent=prefix+n}).catch(()=>{});return node}
function wrResolver(docs){
  const by=new Map();for(const d of docs){by.set(d.id,d);for(const k of [d.title,d.name,String(d.source||'').split(/[\\/]/).pop().replace(/\.md$/i,'')])if(k&&!by.has(String(k).toLowerCase()))by.set(String(k).toLowerCase(),d)}
  return ref=>{ref=String(ref||'').trim();return by.get(ref)||by.get(ref.toLowerCase())||null};
}

// ---- Markdown: blocks keep their source lines, so a block can be edited in place --------------------------------------
const WR_RE={fence:/^\s*(```+|~~~+)\s*([\w+.-]*)\s*$/,head:/^(#{1,6})\s+(.*?)\s*#*\s*$/,hr:/^\s{0,3}([-*_])(\s*\1){2,}\s*$/,item:/^(\s*)([-*+]|\d{1,9}[.)])\s+(.*)$/,
  tsep:/^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$/,embed:/^\s*!\[\[([^\]|]+)(?:\|([^\]]*))?\]\]\s*$/,quote:/^\s{0,3}>/};
function mdParse(src,base=0){
  const lines=String(src||'').replace(/\r\n?/g,'\n').split('\n'),blocks=[],blank=l=>!l.trim();let i=0;
  const starts=l=>WR_RE.head.test(l)||WR_RE.fence.test(l)||WR_RE.quote.test(l)||WR_RE.item.test(l)||WR_RE.hr.test(l)||WR_RE.embed.test(l);
  while(i<lines.length){
    const l=lines[i],s=i;let m;
    if(blank(l)){i++;continue}
    if((m=WR_RE.fence.exec(l))){const close=new RegExp('^\\s*'+m[1][0]+'{'+m[1].length+',}\\s*$'),body=[];i++;while(i<lines.length&&!close.test(lines[i]))body.push(lines[i++]);if(i<lines.length)i++;
      blocks.push({t:'code',lang:m[2],text:body.join('\n'),l0:base+s,l1:base+i});continue}
    if((m=WR_RE.head.exec(l))){i++;blocks.push({t:'h',level:m[1].length,text:m[2],l0:base+s,l1:base+i});continue}
    if(WR_RE.hr.test(l)){i++;blocks.push({t:'hr',l0:base+s,l1:base+i});continue}
    if((m=WR_RE.embed.exec(l))){i++;blocks.push({t:'embed',ref:m[1].trim(),label:m[2]||'',l0:base+s,l1:base+i});continue}
    if(WR_RE.quote.test(l)){const body=[];while(i<lines.length&&WR_RE.quote.test(lines[i]))body.push(lines[i++].replace(/^\s{0,3}>\s?/,''));
      blocks.push({t:'quote',blocks:mdParse(body.join('\n')),l0:base+s,l1:base+i});continue}
    if(l.includes('|')&&i+1<lines.length&&WR_RE.tsep.test(lines[i+1])){
      const cells=r=>{let t=r.trim();if(t.startsWith('|'))t=t.slice(1);if(t.endsWith('|')&&!t.endsWith('\\|'))t=t.slice(0,-1);return t.split(/(?<!\\)\|/).map(c=>c.trim().replace(/\\\|/g,'|'))};
      const head=cells(l),align=cells(lines[i+1]).map(c=>c.startsWith(':')&&c.endsWith(':')?'center':c.endsWith(':')?'right':'');i+=2;const rows=[];
      while(i<lines.length&&!blank(lines[i])&&lines[i].includes('|'))rows.push(cells(lines[i++]));
      blocks.push({t:'table',head,align,rows,l0:base+s,l1:base+i});continue}
    if(WR_RE.item.test(l)){const body=[];
      while(i<lines.length){const x=lines[i];
        if(blank(x)){let j=i;while(j<lines.length&&blank(lines[j]))j++;if(j<lines.length&&(WR_RE.item.test(lines[j])||/^\s{2,}\S/.test(lines[j]))){while(i<j)body.push(lines[i++]);continue}break}
        if(!WR_RE.item.test(x)&&!/^\s/.test(x)&&starts(x))break;
        body.push(x);i++}
      while(body.length&&blank(body[body.length-1]))body.pop();
      blocks.push({...mdList(body,base+s),l0:base+s,l1:base+s+body.length});i=s+body.length;continue}
    const body=[];while(i<lines.length&&!blank(lines[i])&&(body.length===0||!starts(lines[i])))body.push(lines[i++]);
    blocks.push({t:'p',text:body.join('\n'),l0:base+s,l1:base+i});
  }
  return blocks;
}
function mdList(lines,base){
  const top={t:'list',ordered:false,items:[],indent:null};const stack=[top];
  lines.forEach((raw,n)=>{
    const m=WR_RE.item.exec(raw);
    if(!m){const last=stack[stack.length-1].items.at(-1);if(last&&raw.trim())last.text+='\n'+raw.trim();return}
    const ind=m[1].replace(/\t/g,'    ').length;
    if(top.indent===null){top.indent=ind;top.ordered=/\d/.test(m[2]);top.start=parseInt(m[2])||1}
    while(stack.length>1&&ind<stack[stack.length-1].indent)stack.pop();
    let list=stack[stack.length-1];
    if(ind>list.indent&&list.items.length){const parent=list.items.at(-1);parent.sub=parent.sub||{t:'list',ordered:/\d/.test(m[2]),start:parseInt(m[2])||1,items:[],indent:ind};list=parent.sub;stack.push(list)}
    const task=/^\[([ xX])\]\s+(.*)$/.exec(m[3]);
    list.items.push({text:task?task[2]:m[3],task:task?task[1]!==' ':null,line:base+n});
  });
  return top;
}
const WR_INLINE=/(`+)([^`]|[^`][\s\S]*?[^`])\1(?!`)|\[\[([^\]|\n]+)(?:\|([^\]\n]*))?\]\]|\[([^\]\n]+)\]\(([^)\s]+)(?:\s+"[^"]*")?\)|(\*\*|__)(?=\S)([\s\S]*?\S)\7|\*(?=[^\s*])([\s\S]*?[^\s*])\*|(?<![\w])_(?=\S)([^_]*?\S)_(?![\w])|~~(?=\S)([\s\S]*?\S)~~|(https?:\/\/[^\s<>()]*[^\s<>().,;:!?'"*_])/g;
function mdInline(text,ctx){
  // its own regex each call: mdInline recurses (bold inside a link), and a shared lastIndex would restart the outer scan
  const out=[];let last=0;const src=String(text||''),re=new RegExp(WR_INLINE.source,'g');let m;
  const push=s=>{if(!s)return;const parts=s.split(/ {2,}\n|\\\n/);parts.forEach((p,i)=>{if(i)out.push(wrEl('br'));out.push(document.createTextNode(p.replace(/\\([\\`*_{}\[\]()#+\-.!|>~])/g,'$1')))})};
  while((m=re.exec(src))){
    push(src.slice(last,m.index));last=re.lastIndex;
    if(m[1])out.push(wrEl('code',{},m[2]));
    else if(m[3]!==undefined){const ref=m[3].trim(),doc=ctx.resolve?.(ref),label=(m[4]||'').trim()||(doc?wrTitle(doc):ref);
      out.push(doc?wrEl('a',{class:'wr-link','data-doc':doc.id,title:wrTitle(doc),tabindex:'0',role:'link'},label)
                 :wrEl('a',{class:'wr-link wr-missing','data-missing':ref,title:'No document called '+ref+' yet. Press to start it.',tabindex:'0',role:'link'},label))}
    else if(m[5]!==undefined){const url=m[6];
      if(/^(dk\d+)$/.test(url)||ctx.resolve?.(url)){const doc=ctx.resolve?.(url);out.push(wrEl('a',{class:'wr-link','data-doc':doc?.id||url,tabindex:'0',role:'link'},...mdInline(m[5],ctx)))}
      else out.push(wrEl('a',{class:'wr-ext','data-url':url,title:url,tabindex:'0',role:'link'},...mdInline(m[5],ctx)))}
    else if(m[7])out.push(wrEl('strong',{},...mdInline(m[8],ctx)));
    else if(m[9]!==undefined)out.push(wrEl('em',{},...mdInline(m[9],ctx)));
    else if(m[10]!==undefined)out.push(wrEl('em',{},...mdInline(m[10],ctx)));
    else if(m[11]!==undefined)out.push(wrEl('s',{},...mdInline(m[11],ctx)));
    else if(m[12])out.push(wrEl('a',{class:'wr-ext','data-url':m[12],title:m[12],tabindex:'0',role:'link'},m[12].replace(/^https?:\/\//,'')));
  }
  push(src.slice(last));return out;
}
function mdRender(blocks,ctx,top=true){
  const out=[];
  for(const b of blocks){let n;
    if(b.t==='h')n=wrEl('h'+b.level,{},...mdInline(b.text,ctx));
    else if(b.t==='p')n=wrEl('p',{},...mdInline(b.text,ctx));
    else if(b.t==='code')n=wrEl('pre',{},wrEl('code',{'data-lang':b.lang||null},b.text));
    else if(b.t==='quote')n=wrEl('blockquote',{},...mdRender(b.blocks,ctx,false));
    else if(b.t==='hr')n=wrEl('hr');
    else if(b.t==='table'){const cell=(tag,c,i)=>wrEl(tag,{style:b.align[i]?{textAlign:b.align[i]}:null},...mdInline(c,ctx));
      n=wrEl('table',{},wrEl('thead',{},wrEl('tr',{},...b.head.map((c,i)=>cell('th',c,i)))),wrEl('tbody',{},...b.rows.map(r=>wrEl('tr',{},...b.head.map((_,i)=>cell('td',r[i]??'',i))))))}
    else if(b.t==='list')n=mdRenderList(b,ctx);
    else if(b.t==='embed'){const doc=ctx.resolve?.(b.ref);n=wrEl('div',{class:'wr-embed'},wrEl('span',{},'▤'),doc?wrEl('a',{class:'wr-link','data-doc':doc.id,tabindex:'0',role:'link'},b.label||wrTitle(doc)):wrEl('span',{},b.label||b.ref),
      wrEl('small',{},doc?(doc.kind+(doc.changed?' · changed '+(ctx.ago?.(doc.changed)||''):'')):'a thing this page embeds ('+b.ref+')'))}
    if(!n)continue;
    if(top){n.classList.add('wr-block');n.dataset.l0=b.l0;n.dataset.l1=b.l1}
    out.push(n);
  }
  return out;
}
function mdRenderList(list,ctx){
  const n=wrEl(list.ordered?'ol':'ul',list.ordered&&list.start!==1?{start:list.start}:{});
  for(const it of list.items){
    const li=wrEl('li',{});
    if(it.task!==null){li.classList.add('wr-task');if(it.task)li.classList.add('wr-ticked');
      li.append(wrEl('input',{type:'checkbox','data-line':it.line,'aria-label':it.text,checked:it.task||null,disabled:ctx.readonly?'':null}),wrEl('span',{},...mdInline(it.text,ctx)))}
    else li.append(...mdInline(it.text,ctx));
    if(it.sub)li.append(mdRenderList(it.sub,ctx));
    n.append(li);
  }
  return n;
}
// The words as a reader sees them (whitespace folded), and the heading each block sits under: what a comment's quote,
// words before and after, and section are measured against. One cache per text.
function wrPlain(node){let s='';const walk=n=>{if(n.nodeType===3){s+=n.data;return}if(n.nodeType!==1)return;if(n.tagName==='INPUT')return;
  const block=/^(P|H\d|LI|TR|TD|TH|PRE|BLOCKQUOTE|DIV|TABLE|UL|OL)$/.test(n.tagName);if(block)s+=' ';for(const c of n.childNodes)walk(c);if(block)s+=' '};walk(node);return wrNorm(s)}
const WR_OUTLINE=new Map();
function wrOutline(text){
  const key=String(text||'');if(WR_OUTLINE.has(key))return WR_OUTLINE.get(key);
  const out=wrSourcePlain(key);if(WR_OUTLINE.size>40)WR_OUTLINE.clear();WR_OUTLINE.set(key,out);return out;
}
function wrAround(outline,quote){
  const q=wrNorm(quote),at=outline.plain.indexOf(q);if(at<0)return {before:'',after:'',heading:''};
  return {before:outline.plain.slice(0,at).split(' ').filter(Boolean).slice(-6).join(' '),after:outline.plain.slice(at+q.length).split(' ').filter(Boolean).slice(0,6).join(' '),heading:outline.headingAt(at)};
}
// Wrap each occurrence of a quote inside one block in <mark>, across inline elements.
function wrMarkQuote(block,quote,id){
  const q=wrNorm(quote);if(!q||q.length<2)return null;
  const nodes=[],walker=document.createTreeWalker(block,NodeFilter.SHOW_TEXT);let t;while((t=walker.nextNode()))if(!t.parentElement.closest('input,textarea,button,.wr-pick'))nodes.push(t);
  let norm='';const map=[];let space=true;
  for(const node of nodes)for(let i=0;i<node.data.length;i++){const ch=node.data[i];if(/\s/.test(ch)){if(!space){norm+=' ';map.push([node,i]);space=true}}else{norm+=ch;map.push([node,i]);space=false}}
  const at=norm.indexOf(q);if(at<0)return null;
  const [sn,so]=map[at],[en,eo]=map[at+q.length-1];const first=[];
  const segs=[];let on=false;for(const node of nodes){if(node===sn)on=true;if(on)segs.push([node,node===sn?so:0,node===en?eo+1:node.data.length]);if(node===en)break}
  for(const [node,a,b] of segs.reverse()){if(b<=a)continue;const r=document.createRange();r.setStart(node,a);r.setEnd(node,b);const mk=wrEl('mark',{class:'wr-mark','data-comment':id});try{r.surroundContents(mk);first.unshift(mk)}catch{}}
  return first[0]||null;
}

// ---- overlays: a menu and a composer, owned by the window, closed on Escape or outside press -------------------------
let WR_OVERLAY=null;
function wrClose(){const o=WR_OVERLAY;WR_OVERLAY=null;if(o){o.node.remove();document.removeEventListener('pointerdown',o.outside,true);document.removeEventListener('keydown',o.key,true);o.onclose?.()}}
function wrPlace(node,x,y){document.body.append(node);const r=node.getBoundingClientRect();node.style.left=Math.max(8,Math.min(x,innerWidth-r.width-8))+'px';node.style.top=Math.max(8,Math.min(y,innerHeight-r.height-8))+'px'}
function wrOverlay(node,x,y,onclose){
  wrClose();wrPlace(node,x,y);
  const outside=e=>{if(!node.contains(e.target))wrClose()},key=e=>{if(e.key==='Escape'){e.preventDefault();e.stopPropagation();wrClose()}};
  document.addEventListener('pointerdown',outside,true);document.addEventListener('keydown',key,true);WR_OVERLAY={node,outside,key,onclose};return node;
}
function wrMenu(x,y,items,extra){
  const menu=wrEl('div',{class:'wr-menu',role:'menu'});
  for(const it of items){if(it==='-'){menu.append(wrEl('hr'));continue}if(it.quote){menu.append(wrEl('div',{class:'wr-menu-q'},'“'+it.quote+'”'));continue}
    menu.append(wrEl('button',{type:'button',role:'menuitem',class:it.danger?'wr-danger':null,on:{click:()=>{wrClose();it.run()}}},it.icon?wrIcon(it.icon):null,it.label,it.key?wrEl('small',{},it.key):null))}
  if(extra)menu.append(extra);
  wrOverlay(menu,x,y);menu.querySelector('button')?.focus();return menu;
}
// One composer for a margin comment, a reply and a line to JEFF. send(words) resolves to close it, or throws to keep it.
function wrComposer({x,y,title,badge,quote,hint,send,label,line,keep}){
  const ta=wrEl('textarea',{placeholder:hint,'aria-label':title,value:keep?.words||''});
  const status=wrEl('small',{},'Enter sends · Shift+Enter, a new line');
  const go=async()=>{const words=ta.value.trim();if(!words&&!quote)return ta.focus();ok.disabled=true;
    try{await send(words);if(keep)keep.words='';wrClose()}catch(e){status.textContent=String(e?.message||e).split('\n')[0];ok.disabled=false;ta.focus()}};
  const ok=wrEl('button',{type:'button',class:'wr-btn wr-primary',on:{click:go}},label);
  ta.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();go()}});
  ta.addEventListener('input',()=>{if(keep)keep.words=ta.value});
  const pop=wrEl('div',{class:'wr-pop',role:'dialog','aria-label':title},wrEl('h4',{},badge?wrEl('i',{},badge):null,title),quote?wrEl('blockquote',{},quote):null,ta,
    wrEl('div',{class:'wr-pop-row'},status,wrEl('button',{type:'button',class:'wr-btn wr-quiet',on:{click:wrClose}},'Cancel'),ok),line?wrEl('code',{},'runs: '+line):null);
  wrOverlay(pop,x,y);ta.focus();return pop;
}
function wrExternal(api,url,x,y){
  const copy=()=>{const t=wrEl('textarea',{value:url,style:{position:'fixed',opacity:'0'}});document.body.append(t);t.select();let ok=false;try{ok=document.execCommand('copy')}catch{}t.remove();api.tell(ok?'Copied the address':'Select the address and press Ctrl+C')};
  const pop=wrEl('div',{class:'wr-pop',role:'dialog','aria-label':'A page outside Agora'},wrEl('h4',{},'A page outside Agora'),
    wrEl('code',{style:{fontSize:'12.5px',userSelect:'all'}},url),wrEl('small',{style:{color:'var(--ag-ink-muted)'}},'Agora windows do not open web pages yet. Copy the address into your browser.'),
    wrEl('div',{class:'wr-pop-row'},wrEl('small',{}),wrEl('button',{type:'button',class:'wr-btn wr-quiet',on:{click:wrClose}},'Close'),wrEl('button',{type:'button',class:'wr-btn wr-primary',on:{click:()=>{copy();wrClose()}}},'Copy address')));
  wrOverlay(pop,x,y);
}
// What goes to JEFF: Alex's words, the passage quoted, and a link back to the document (as Markdown, as the chat draws it).
function wrToJeff(words,quote,doc){
  const link='[['+doc.id+'|'+wrTitle(doc)+']]';
  return [words,quote?quote.split('\n').map(l=>'> '+l).join('\n'):'',(quote?'— from ':'— about ')+link].filter(Boolean).join('\n\n');
}

// ---- writing-shell -----------------------------------------------------------------------------------------------------
// window.wrSeeded: the target this page has already opened (one window per page; kept on the page, since component
// code can be evaluated again on a repaint)
function mountShell(api,s){
  const view=api.view(),root=api.part('body','div',{class:'wr-shell'});
  // window.open writing <document> starts on that document (the window's $view.target), once
  if(view.target&&window.wrSeeded!==view.target){window.wrSeeded=view.target;queueMicrotask(()=>api.select({open:view.target,back:view.open||''}))}
  const back=view.back&&view.back!==view.open;
  const top=wrEl('header',{class:'wr-top'},...api.panelButtons('left'),wrEl('div',{class:'wr-brand'},wrEl('i',{},'✎'),s.title||'Writing'));
  if(back)top.append(wrEl('button',{type:'button',class:'wr-btn','aria-label':'Back to the document before',title:'Back (Alt+←)',on:{click:()=>api.select({open:view.back,back:view.open})}},wrIcon('back'),'Back'));
  if(view.open)top.append(wrEl('button',{type:'button',class:'wr-btn wr-quiet',on:{click:()=>api.select({open:'',back:view.open})}},'Home'));
  top.append(wrEl('span',{class:'wr-space'}),...api.panelButtons('right'));
  if(wrHasGesture(api,'new'))top.append(wrEl('button',{type:'button',class:'wr-btn wr-primary',title:wrLineOf(api,'new'),on:{click:async()=>{
    try{const id=wrMade(await wrFire(api,'new',{}));if(id)api.select({open:id,back:api.view().open||'',fresh:id})}catch{}}}},wrIcon('plus'),'New document'));
  // the rail's box is the frame that opens and shuts when the rail is a panel (the lens's `panel left`)
  const railbox=wrEl('aside',{class:'wr-railbox','aria-label':'Documents','data-panel-frame':''}),deskbox=wrEl('main',{class:'wr-deskbox'});
  for(const child of api.children)(child.name==='rail'||child.component==='doc-rail'?railbox:deskbox).append(api.render(child));
  root.append(top,railbox,deskbox);
  const keys=e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();document.querySelector('.wr-find input')?.focus()}
    if(e.altKey&&e.key==='ArrowLeft'&&back){e.preventDefault();api.select({open:view.back,back:view.open})}};
  document.addEventListener('keydown',keys);api.cleanup(()=>document.removeEventListener('keydown',keys));
  return root;
}

// ---- doc-rail ----------------------------------------------------------------------------------------------------------
function mountRail(api,s){
  const D=api.draft,root=api.part('body','nav',{class:'wr-rail','aria-label':'Documents'});
  const input=api.part('find','input',{type:'search',placeholder:s.hint||'Find a document',value:D.find||'','aria-label':'Find a document',autocomplete:'off',spellcheck:'false'});
  const shelves=wrEl('div',{class:'wr-shelves'}),results=wrEl('div',{class:'wr-results',role:'list'});
  for(const child of api.children)shelves.append(api.render(child));
  root.append(wrEl('label',{class:'wr-find'},wrIcon('search'),input,wrEl('span',{class:'wr-key'},'Ctrl K')),shelves);
  let docs=[];
  const draw=()=>{
    const q=wrNorm(input.value).toLowerCase();D.find=input.value;
    if(!q){results.remove();shelves.replaceChildren(...shelves.__kids);return}
    const words=q.split(' '),hits=[];
    for(const d of docs){const title=wrTitle(d),hay=(title+' '+(d.text||'')).toLowerCase();if(!words.every(w=>hay.includes(w)))continue;
      hits.push({d,score:words.reduce((n,w)=>n+(title.toLowerCase().includes(w)?10:0)+(hay.split(w).length-1),0)})}
    hits.sort((a,b)=>b.score-a.score);
    const mark=(text,limit)=>{const out=[];const t=String(text).slice(0,limit);const re=new RegExp('('+words.map(w=>w.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')).join('|')+')','gi');let last=0,m;
      while((m=re.exec(t))){out.push(t.slice(last,m.index),wrEl('b',{},m[0]));last=re.lastIndex;if(!m[0])re.lastIndex++}out.push(t.slice(last));return out};
    const view=api.view();
    results.replaceChildren(...hits.slice(0,40).map(({d})=>{const body=wrNorm(String(d.text||'').replace(/[#>*_`|\[\]]/g,' ')),at=Math.max(0,body.toLowerCase().indexOf(words[0])-40);
      return wrEl('button',{type:'button',class:'wr-row',role:'listitem','aria-current':String(view.open===d.id),on:{click:()=>wrOpen(api,d.id)}},wrEl('span',{class:'wr-row-title'},...mark(wrTitle(d),200)),
        wrEl('span',{class:'wr-snip'},...mark((at?'…':'')+body.slice(at,at+160),200)))}));
    if(!hits.length)results.append(wrEl('p',{class:'wr-empty',style:{paddingLeft:'12px'}},'No document holds those words.'));
    shelves.replaceChildren(results);
  };
  shelves.__kids=[...shelves.children];
  input.addEventListener('input',draw);
  input.addEventListener('keydown',e=>{if(e.key==='Escape'){input.value='';draw()}if(e.key==='Enter'){e.preventDefault();results.querySelector('button')?.click()}
    if(e.key==='ArrowDown'){e.preventDefault();results.querySelector('button')?.focus()}});
  shelves.addEventListener('scroll',()=>{D.scroll=shelves.scrollTop},{passive:true});
  wrReadDocs(api).then(api.guard(rows=>{docs=rows;if(input.value)draw()})).catch(()=>{});
  queueMicrotask(()=>{if(D.scroll)shelves.scrollTop=D.scroll});
  if(D.find)draw();
  root.append(wrEl('div',{class:'wr-rail-foot'},'Documents belong to the people who make them.'));
  return root;
}

// ---- doc-shelf ---------------------------------------------------------------------------------------------------------
function wrRowsUnder(node){let n=0;for(const c of node.children||[])n+=c.component==='doc-row'?1:wrRowsUnder(c);return n}
function mountShelf(api,s){
  const D=api.draft;if(D.open===undefined)D.open=!!s.open;
  const root=api.part('body','section',{class:'wr-shelf'+(s.nested?' wr-nested':''),'data-open':String(D.open),'aria-label':s.label});
  const total=wrRowsUnder(api.node),hot=s.hot&&total>0;
  const toggle=wrEl('button',{type:'button',class:'wr-shelf-toggle','aria-expanded':String(D.open),on:{click:()=>{D.open=!D.open;root.dataset.open=String(D.open);toggle.setAttribute('aria-expanded',String(D.open))}}},
    wrEl('span',{class:'wr-chev'},'›'),wrEl('span',{},api.display('label')||s.label||'Documents'),wrEl('span',{class:'wr-count'+(hot?' wr-hot':'')},String(total)));
  const head=wrEl('div',{class:'wr-shelf-head'},toggle);
  if(wrHasGesture(api,'new'))head.append(wrEl('button',{type:'button',class:'wr-plus','aria-label':'New document in '+s.label,title:wrLineOf(api,'new'),on:{click:async()=>{
    try{const id=wrMade(await wrFire(api,'new',{}));D.open=true;if(id)api.select({open:id,back:api.view().open||'',fresh:id})}catch{}}}},'+'));
  const body=wrEl('div',{class:'wr-shelf-body'});
  const rows=[],shelves=[];
  for(const child of api.children){
    if(child.component==='doc-shelf'){shelves.push(child);continue}
    const kids=child.component==='doc-row'?[child]:(child.children||[]).filter(k=>k.component==='doc-row');
    rows.push(...kids);
  }
  rows.sort((a,b)=>String(b.facts?.changed||'').localeCompare(String(a.facts?.changed||'')));
  for(const r of rows)body.append(api.render(r));
  for(const sh of shelves)body.append(api.render(sh));
  if(!total&&!shelves.length)body.append(wrEl('div',{class:'wr-empty'},s.empty||'Nothing here yet'));
  root.append(head,body);return root;
}

// ---- doc-row -------------------------------------------------------------------------------------------------------------
function wrExcerpt(text){const lines=String(text||'').split('\n').filter(l=>l.trim()&&!/^#{1,6}\s/.test(l)&&!/^\s*\|?\s*:?-{2,}/.test(l));
  return wrNorm(lines.join(' ').replace(/\[\[[^\]|]+\|([^\]]+)\]\]/g,'$1').replace(/\[\[([^\]]+)\]\]/g,'$1').replace(/\[([^\]]+)\]\([^)]+\)/g,'$1').replace(/[#>*_`|~]/g,' ')).slice(0,240)}
function mountRow(api,s){
  const d=api.facts,view=api.view(),card=s.look==='card',list=s.look==='list';
  const meta=wrEl('span',{class:'wr-row-meta'});
  const plan=wrPlanState(d);
  if(plan==='waiting')meta.append(wrEl('span',{class:'wr-dot','aria-hidden':'true'}),'Waiting for you');
  else if(plan==='answered'&&d.verdict)meta.append(wrVerdictName(d.verdict));
  else if(plan==='answered')meta.append('Answered');
  if(d.still_open&&plan!=='waiting')meta.append(wrEl('span',{class:'wr-sep'},'·'),wrEl('span',{class:'wr-dot',title:d.still_open}),'still open');
  if(d.file_source)meta.append('from a file');
  if(meta.childNodes.length)meta.append(wrEl('span',{class:'wr-sep'},'·'));
  meta.append(wrAgo(api,d.changed||d.made));
  const n=api.part('row','button',{type:'button',class:card?'wr-card':'wr-row','aria-current':String(view.open===d.id),...(card?{}:{title:wrTitle(d)}),on:{click:()=>wrOpen(api,d.id)}});
  if(card){n.append(wrEl('span',{class:'wr-row-meta'},d.drafted_by?wrEl('span',{class:'wr-chip wr-claude'},'Draft by '+d.drafted_by):null,plan==='waiting'?wrEl('span',{class:'wr-chip wr-wait'},'Waiting for you'):null),
    wrEl('span',{class:'wr-row-title'},wrTitle(d)),wrEl('span',{class:'wr-snip'},wrExcerpt(d.text)),wrEl('span',{class:'wr-row-meta'},wrWho(api,d,wrEl('span',{})),'· '+wrAgo(api,d.changed||d.made)))}
  else if(list)n.append(wrEl('span',{class:'wr-row-title'},wrTitle(d)),wrEl('span',{class:'wr-row-meta'},wrCollection(d)+' · '+wrAgo(api,d.changed||d.made)));
  else n.append(wrEl('span',{class:'wr-row-title'},wrTitle(d)),meta);
  return n;
}

// ---- doc-home ------------------------------------------------------------------------------------------------------------
function mountHome(api,s){
  const D=api.draft,root=api.part('body','section',{class:'wr-home','aria-label':'Writing home'}),inner=wrEl('div',{class:'wr-home-in'});
  const who=(api.node.viewer?.name||'').split(' ')[0],hour=new Date().getHours();
  const kids=name=>{const c=api.children.find(x=>x.name===name);return c?(c.children||[]).filter(k=>k.component==='doc-row'):[]};
  const waiting=kids('waiting'),recent=kids('recent').sort((a,b)=>String(b.facts?.changed||'').localeCompare(String(a.facts?.changed||''))).slice(0,Number(s.recent)||8);
  inner.append(wrEl('h1',{class:'wr-hello'},(hour<5?'Still up':hour<12?'Good morning':hour<18?'Good afternoon':'Good evening')+(who?', '+who:'')+'.'),
    wrEl('p',{class:'wr-sub'},waiting.length?(waiting.length===1?'One plan is waiting for you.':waiting.length+' plans are waiting for you.')+' Everything else can wait.':'Nothing is waiting for you. Write something, or open a document on the left.'));
  if(waiting.length)inner.append(wrEl('h2',{class:'wr-h'},'Plans waiting for you'),wrEl('div',{class:'wr-cards'},...waiting.map(api.render)));
  if(recent.length)inner.append(wrEl('h2',{class:'wr-h'},'Recently changed'),wrEl('div',{class:'wr-list'},...recent.map(api.render)));
  if(wrHasGesture(api,'new'))inner.append(wrEl('div',{style:{marginTop:'28px'}},wrEl('button',{type:'button',class:'wr-btn wr-soft',title:wrLineOf(api,'new'),on:{click:async()=>{
    try{const id=wrMade(await wrFire(api,'new',{}));if(id)api.select({open:id,back:'',fresh:id})}catch{}}}},wrIcon('pen'),'Start a new document')));
  inner.append(wrEl('div',{class:'wr-tips'},wrEl('span',{},wrEl('span',{class:'wr-key'},'Ctrl E'),'a document’s Markdown source'),wrEl('span',{},wrEl('span',{class:'wr-key'},'[['),'link another document'),
    wrEl('span',{},wrEl('span',{class:'wr-key'},'right-click'),'selected words to comment, or send them to JEFF'),wrEl('span',{},wrEl('span',{class:'wr-key'},'Ctrl K'),'find')));
  root.append(inner);root.addEventListener('scroll',()=>{D.scroll=root.scrollTop},{passive:true});queueMicrotask(()=>{if(D.scroll)root.scrollTop=D.scroll});
  return root;
}

// ---- doc-page ------------------------------------------------------------------------------------------------------------
// One continuous editor per document (4 Nov, Alex: "make it so its a continous document ... work about as well as
// obsidian"): CodeMirror with a live preview (doc-editor.bundle.js, read here as WR_CM). The editor outlives repaints:
// each document's editor is kept below (WR_EDITORS) and its element moved into the new page, so the caret, the selection
// and undo survive a save. Saves go through the lens's `write` gesture (the kernel's `edit`: changed spans and the text
// they were made against); the kernel keeps every change in the document's CRDT history.
const WR_EDITORS=new Map();
const WR_PLACES=new Map();   // each document's scroll place, kept while the window lives (the part's draft does not outlive a document)
const WR_SAVE_MS=700;
// The words of some Markdown as a reader sees them, each with where it stands in the source: what comments quote and
// are found by. Headings, list and quote marks, emphasis, code ticks and link addresses are left out.
function wrSourcePlain(src){
  src=String(src||'');let plain='',heading='',space=true,fence=false;const map=[],sections=[];
  const put=(ch,at)=>{if(/\s/.test(ch)){if(!space){plain+=' ';map.push(at);space=true}}else{plain+=ch;map.push(at);space=false}};
  let at=0;
  for(const raw of src.split('\n')){
    const start=at;at+=raw.length+1;
    if(/^\s*(```|~~~)/.test(raw)){fence=!fence;put('\n',start);continue}
    if(!fence&&(/^\s{0,3}([-*_])(\s*\1){2,}\s*$/.test(raw)||/^\s*\|?\s*:?-{2,}/.test(raw))){put('\n',start);continue}
    let i=0;
    if(!fence){
      const h=/^\s{0,3}(#{1,6})\s+/.exec(raw);
      const pre=h||/^(\s*>\s?)+/.exec(raw)||/^\s*([-*+]|\d{1,9}[.)])\s+(\[[ xX]\]\s+)?/.exec(raw);
      if(pre)i=pre[0].length;
      if(h){heading=wrNorm(raw.slice(i).replace(/[*_`~]|\[\[[^\]|]*\||\]\]|\[\[/g,'').replace(/#+\s*$/,''));sections.push({at:plain.length+(plain&&!space?1:0),heading})}
    }
    while(i<raw.length){
      const rest=raw.slice(i);let m;
      if(fence){put(raw[i],start+i);i++;continue}
      if((m=/^\[\[([^\]|\n]+)\|([^\]\n]*)\]\]/.exec(rest))){const t0=i+2+m[1].length+1;for(let j=0;j<m[2].length;j++)put(m[2][j],start+t0+j);i+=m[0].length;continue}
      if((m=/^\[\[([^\]|\n]+)\]\]/.exec(rest))){for(let j=0;j<m[1].length;j++)put(m[1][j],start+i+2+j);i+=m[0].length;continue}
      if((m=/^!?\[([^\]\n]*)\]\([^)\n]*\)/.exec(rest))){const t0=i+(rest[0]==='!'?2:1);for(let j=0;j<m[1].length;j++)put(m[1][j],start+t0+j);i+=m[0].length;continue}
      if((m=/^(\*\*|__|~~|\*|`+)/.exec(rest))){i+=m[0].length;continue}
      if(rest[0]==='_'&&!/\w/.test(raw[i-1]||'')){i++;continue}
      if(rest[0]==='_'&&!/\w/.test(raw[i+1]||'')){i++;continue}
      if(rest[0]==='|'){put(' ',start+i);i++;continue}
      if(rest[0]==='\\'&&i+1<raw.length){i++;put(raw[i],start+i);i++;continue}
      put(raw[i],start+i);i++;
    }
    put('\n',start+raw.length);
  }
  while(plain.endsWith(' ')){plain=plain.slice(0,-1);map.pop()}
  return {plain,map,sections,headingAt:x=>{let h='';for(const s of sections){if(s.at>x)break;h=s.heading}return h}};
}
// where a quote's words stand in the source, or null
function wrFindQuote(sp,quote){const q=wrNorm(quote);if(!q||q.length<2)return null;const a=sp.plain.indexOf(q);if(a<0)return null;
  return {from:sp.map[a],to:sp.map[a+q.length-1]+1}}

function wrEditorEntry(api,d,cfg){
  const id=d.id,text=String(d.text||'');
  let e=WR_EDITORS.get(id);
  if(e){WR_EDITORS.delete(id);WR_EDITORS.set(id,e);return e}          // newest last
  const CM=WR_CM;
  e={id,base:{text,version:''},pending:CM.ChangeSet.empty(text.length),inflight:null,timer:0,status:'',hooks:{...(cfg.hooks||{})},api};
  e.ed=CM.createEditor({doc:text,label:'Text of '+wrTitle(d),readonly:cfg.readonly,
    placeholder:'Start writing…  # a heading, - a list, **bold**, [[ to link a document',
    resolve:ref=>e.hooks.resolve?.(ref),documents:()=>e.hooks.documents?.()||[],drawTable:src=>e.hooks.drawTable?.(src),
    onLink:(l,ev)=>e.hooks.link?.(l,ev),onContextMenu:(ev,v)=>e.hooks.menu?.(ev,v),onCommentPress:(cid,ev)=>e.hooks.commentPress?.(cid,ev),
    onSave:()=>wrSave(e,true),onEscape:()=>wrSave(e,true),onBlur:()=>wrSave(e,true),onToggleSource:()=>e.hooks.toggleSource?.(),
    onUpdate:u=>{
      if(!u.docChanged)return;
      for(const tr of u.transactions){if(!tr.docChanged||tr.isUserEvent('agora.remote'))continue;
        if(e.inflight)e.inflight.buffer=e.inflight.buffer.compose(tr.changes);else e.pending=e.pending.compose(tr.changes)}
      if(u.transactions.some(tr=>tr.docChanged&&!tr.isUserEvent('agora.remote'))){wrStatus(e,'editing');wrAfter(e,()=>wrSave(e),WR_SAVE_MS)}
      e.hooks.changed?.();
    }});
  // Windows line ends arrive from files: the editor counts \r as a character, so take them out as a first change
  if(text.includes('\r')){const c=[];for(let i=0;i<text.length;i++)if(text[i]==='\r')c.push({from:i,to:i+1});e.ed.view.dispatch({changes:c,annotations:CM.Transaction.addToHistory.of(false)})}
  WR_EDITORS.set(id,e);
  // keep a few documents' editors (and their undo); let go of the oldest that has nothing waiting to be kept
  for(const [k,x] of WR_EDITORS){if(WR_EDITORS.size<=8)break;if(k!==id&&!x.inflight&&x.pending.empty){x.ed.view.destroy();WR_EDITORS.delete(k)}}
  return e;
}
// Speak to an editor from outside any paint (see mountPage): a press on a painted button runs inside its paint
const wrLater=fn=>Promise.resolve().then(fn).catch(()=>{});
// An editor's save timer, made outside any paint so a repaint never drops it
function wrAfter(e,fn,ms){clearTimeout(e.timer);const g=e.timerGen=(e.timerGen||0)+1;Promise.resolve().then(()=>{if(g===e.timerGen)e.timer=setTimeout(fn,ms)})}
function wrStatus(e,s,why){e.status=s;e.why=why||'';e.hooks.status?.(s,e.why)}
// The world's text changed by another hand (an agent, undo, another window): apply that change here, under ours
function wrFollow(e,text){
  const CM=WR_CM;if(e.inflight||text===e.base.text)return;
  const R=CM.diff(e.base.text,text);
  e.ed.view.dispatch({changes:R.map(e.pending),userEvent:'agora.remote',annotations:CM.Transaction.addToHistory.of(false)});
  e.pending=e.pending.map(R,true);e.base={text,version:''};
}
// Keep what was typed: send the changed spans and the text they were made against
async function wrSave(e,now){
  const CM=WR_CM;clearTimeout(e.timer);e.timerGen=(e.timerGen||0)+1;
  if(e.inflight){if(now)e.again=true;return}
  if(e.pending.empty){if(e.status!=='failed')wrStatus(e,'saved');return}
  const changes=e.pending,base=e.base,sent=changes.apply(CM.Text.of(base.text.split('\n'))).toString();
  e.inflight={buffer:CM.ChangeSet.empty(changes.newLength)};e.pending=CM.ChangeSet.empty(changes.newLength);
  wrStatus(e,'saving');e.sentAt=performance.now();
  try{
    
    const out=await e.api.fire('write',{changes:JSON.stringify(CM.spans(changes)),base:CM.fingerprint(base.text),version:base.version||''});
    const row=(out?.rows||[]).find(r=>r.id===e.id)||{};
    const server=row.merged&&typeof row.text==='string'?row.text:sent;
    const B=e.inflight.buffer;e.inflight=null;
    if(server!==sent){const R=CM.diff(sent,server);e.ed.view.dispatch({changes:R.map(B),userEvent:'agora.remote',annotations:CM.Transaction.addToHistory.of(false)});e.pending=B.map(R,true)}
    else e.pending=B;
    e.base={text:server,version:CM.fingerprint(server)===row.base?row.version||'':''};
    e.tries=0;wrStatus(e,e.pending.empty?'saved':'editing');
  }catch(err){
    
    const B=e.inflight?.buffer||CM.ChangeSet.empty(changes.newLength);e.inflight=null;
    const all=changes.compose(B),why=String(err?.message||err).split('\n')[0];
    e.pending=all;
    if(/stale/i.test(why)&&(e.tries=(e.tries||0)+1)<4){
      // the text changed meanwhile: read it, put our changes on top of it, and send again
      try{await e.api.redraw()}catch{}
      const latest=e.api.latest?.();const now=latest?.facts?.id===e.id?String(latest.facts.text??''):null;
      if(now!=null&&now!==base.text){const R=CM.diff(base.text,now);e.ed.view.dispatch({changes:R.map(all),userEvent:'agora.remote',annotations:CM.Transaction.addToHistory.of(false)});e.pending=all.map(R,true);e.base={text:now,version:''}}
      wrAfter(e,()=>wrSave(e),150);return;
    }
    wrStatus(e,'failed',why);return;
  }
  if(e.again||!e.pending.empty){e.again=false;wrAfter(e,()=>wrSave(e),e.pending.empty?0:WR_SAVE_MS)}
}
// before leaving a document (another opens, the window closes): keep what was typed in every editor
function wrSaveAll(){for(const e of WR_EDITORS.values())if(!e.pending.empty&&!e.inflight)wrSave(e,true)}
addEventListener('pagehide',wrSaveAll);addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden')wrSaveAll()});

function wrCopy(text){try{navigator.clipboard?.writeText(text).catch(()=>fallback())}catch{fallback()}
  function fallback(){const t=wrEl('textarea',{value:text,style:{position:'fixed',opacity:'0'}});document.body.append(t);t.select();try{document.execCommand('copy')}catch{}t.remove()}}

function mountPage(api,s){
  const d=api.facts,id=d.id,D=api.draft,view=api.view();
  const readonly=!!d.file_source,text=String(d.text||''),plan=wrPlanState(d)||(d.collection==='plans'?'waiting':'');
  if(!D.docs)D.docs=[];
  const desk=wrEl('div',{class:'wr-desk'}),root=api.part('body','article',{class:'wr-page','aria-label':wrTitle(d)});desk.append(root);
  // the margin is the frame of this page's panel (the lens's `panel right` on its comments): shut, it has no width
  const panelName=api.children.find(c=>c.panel)?.name||'';
  const margin=wrEl('aside',{class:'wr-margin','aria-label':'Comments','data-panel-frame':panelName}),paper=wrEl('div',{class:'wr-paper'});root.append(paper,margin);
  if(/^\d{3,4}$/.test(String(s.measure||'')))root.style.setProperty('--wr-measure',s.measure+'px');

  // the head: title, who and when, the tools
  const title=api.part('title','input',{class:'wr-title',value:wrTitle(d),placeholder:'Untitled','aria-label':'Title',...(readonly?{readonly:''}:{})});
  // kept on Enter or leaving (not 'change': a repaint while it has focus hands its words to a new input, which then never changes)
  const retitle=()=>{const v=title.value.trim();if(!v||v===wrTitle(d)||D.retitling===v)return;D.retitling=v;wrFire(api,'retitle',{value:v}).catch(()=>{title.value=wrTitle(d)}).finally(()=>{D.retitling=''})};
  title.addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key==='ArrowDown'){ev.preventDefault();retitle();const k=ev.key;wrLater(()=>{const v=entry?.ed.view;if(v){v.focus();if(k==='Enter')v.dispatch({selection:{anchor:0}})}})}if(ev.key==='Escape'){title.value=wrTitle(d);title.blur()}});
  title.addEventListener('blur',()=>{if(title.isConnected)retitle()});
  const meta=wrEl('div',{class:'wr-meta'});
  if(d.drafted_by)meta.append(wrEl('span',{class:'wr-chip wr-claude',title:'Everything here not quoted as Alex’s words is '+d.drafted_by+'’s'},'Draft by '+d.drafted_by));
  meta.append(wrEl('span',{},d.kind==='note'?'a note':readonly?'from a file':(d.collection?{plans:'a plan',notes:'a note',documentation:'Agora documentation',personal:'personal writing'}[d.collection]||d.collection:'a document')));
  if(d.made_by)meta.append(wrEl('span',{class:'wr-sep'},'·'),wrWho(api,d,wrEl('span',{}),'by '));
  meta.append(wrEl('span',{class:'wr-sep'},'·'),wrEl('span',{title:d.changed||''},'changed '+wrAgo(api,d.changed||d.made)));
  const countWords=t=>wrNorm(t.replace(/[#>*_`|\-\[\]]/g,' ')).split(' ').filter(Boolean).length;
  const wordsNode=wrEl('span',{});meta.append(wrEl('span',{class:'wr-sep'},'·'),wordsNode);
  const setWords=t=>{const n=countWords(t);wordsNode.textContent=n.toLocaleString()+(n===1?' word':' words')};setWords(text);
  const saveNode=wrEl('span',{class:'wr-save','aria-live':'polite'});
  if(!readonly)meta.append(wrEl('span',{class:'wr-sep'},'·'),saveNode);
  if(d.page)meta.append(wrEl('span',{class:'wr-sep'},'·'),wrEl('a',{class:'wr-ext',title:d.page,tabindex:'0',role:'link',on:{click:ev=>wrExternal(api,d.page,ev.clientX,ev.clientY)}},'its design page'));
  const actions=wrEl('div',{class:'wr-actions'});
  const srcBtn=wrEl('button',{type:'button',class:'wr-btn','aria-pressed':'false',title:'Show every Markdown mark (Ctrl+E)',on:{click:()=>toggleSource()}},wrIcon('code'),'Marks',wrEl('span',{class:'wr-key'},'Ctrl E'));
  if(!readonly)actions.append(srcBtn);
  if(wrHasGesture(api,'ask-jeff'))actions.append(wrEl('button',{type:'button',class:'wr-btn',title:'Send this document into JEFF’s Conversation',on:{click:ev=>{const r=ev.currentTarget.getBoundingClientRect();jeff('',r.left,r.bottom+6)}}},wrIcon('jeff'),'Send to JEFF'));
  actions.append(wrEl('button',{type:'button','aria-label':'More',class:'wr-btn',on:{click:ev=>{const r=ev.currentTarget.getBoundingClientRect();moreMenu(r.left,r.bottom+6)}}},wrIcon('more')));
  paper.append(wrEl('header',{class:'wr-head'},title,meta,actions));

  // a plan: Alex's call on it, as the old desk's design review had it
  if(plan){
    const box=api.part('plan','section',{class:'wr-plan','aria-label':'Your call on this plan'});
    const top=wrEl('div',{class:'wr-plan-top'},wrEl('span',{class:'wr-chip '+(plan==='waiting'?'wr-wait':'wr-done')},plan==='waiting'?'Waiting for you':'Answered'),
      wrEl('strong',{},plan==='waiting'?'Your call':d.verdict?'You said: '+wrVerdictName(d.verdict):'You answered this plan'));
    box.append(top);
    if(d.still_open)box.append(wrEl('div',{class:'wr-open'},wrEl('span',{class:'wr-dot'}),wrEl('span',{},'Still open: '+d.still_open)));
    if(wrHasGesture(api,'verdict')){const calls=wrEl('div',{class:'wr-plan-calls'});
      for(const [v,label] of WR_VERDICTS)calls.append(wrEl('button',{type:'button',class:'wr-btn','aria-pressed':String(d.verdict===v),title:wrLineOf(api,'verdict').replace('$value',v),on:{click:()=>wrFire(api,'verdict',{value:v},'Recorded: '+label).catch(()=>{})}},label));
      if(plan!=='waiting'&&wrHasGesture(api,'waiting'))calls.append(wrEl('button',{type:'button',class:'wr-btn wr-quiet',on:{click:()=>wrFire(api,'waiting',{},'Back to waiting').catch(()=>{})}},'Back to waiting'));
      box.append(calls)}
    paper.append(box);
  }

  // the sheet: one continuous editor (a file's pages are only read)
  const sheet=api.part('editor','div',{class:'wr-sheet'});paper.append(sheet);
  let resolve=wrResolver(D.docs),docsSeen=JSON.stringify(D.docs.map(x=>[x.id,wrTitle(x),x.source]));
  const ctx={resolve:ref=>resolve(ref),ago:iso=>wrAgo(api,iso),readonly:true};
  const comments=[];for(const col of api.children)for(const c of (col.component==='doc-comment'?[col]:col.children||[]))if(c.component==='doc-comment')comments.push(c);
  let entry=null;
  if(readonly){
    const md=wrEl('div',{class:'wr-md'});sheet.append(md);md.replaceChildren(wrEl('p',{class:'wr-placeholder'},'Opening the file’s pages…'));
    api.read('file-read '+id).then(api.guard(r=>{const data=wrRows(r)[0]||{};md.replaceChildren(...(data.pages||[]).map((p,i)=>wrEl('section',{class:'wr-block'},wrEl('h4',{},'Page '+(i+1)),wrEl('pre',{},wrEl('code',{},String(p).slice(0,20000))))));
      if(!(data.pages||[]).length)md.replaceChildren(wrEl('p',{class:'wr-placeholder'},data.reason||'This file has no readable pages.'))})).catch(()=>md.replaceChildren(wrEl('p',{class:'wr-placeholder'},'This file is not readable here.')));
  }else if(typeof WR_CM==='undefined'||!wrHasGesture(api,'write')){
    sheet.append(wrEl('p',{class:'wr-placeholder'},typeof WR_CM==='undefined'?'The editor did not load.':'This window has no write gesture, so the document is only shown.'),wrEl('div',{class:'wr-md'},...mdRender(mdParse(text),ctx)));
  }else{
    // The editor lives outside this paint: it is made, and spoken to, from a promise, where no part is painting. The
    // painter ties timers and listeners made while a part paints to that paint and drops them at the next one;
    // CodeMirror's own (parsing, measuring) and the save timer must outlast every repaint.
    const host=wrEl('div',{class:'wr-cm-host'});sheet.append(host);
    const kept=WR_EDITORS.get(id);
    const focused=kept&&kept.ed.view.dom.contains(document.activeElement)?document.activeElement:null;   // the text, or its find box
    if(kept){entry=kept;entry.api=api;host.append(kept.ed.view.dom)}  // moved in now, so nothing flickers
    if(kept)srcBtn.setAttribute('aria-pressed',String(kept.ed.source()));
    if(kept)showStatus(kept.status||'saved',kept.why);
    Promise.resolve().then(()=>{
      if(!host.isConnected)return;                                   // a newer paint took its place
      // what the editor asks of this page, as this paint knows it (given before a new editor first draws)
      const hooks={
        resolve:ref=>{const x=resolve(ref);return x?{id:x.id,title:wrTitle(x)}:null},
        documents:()=>D.docs.filter(x=>x.id!==id).map(x=>({id:x.id,title:wrTitle(x),detail:wrCollection(x)})),
        drawTable:src=>{const el=mdRender(mdParse(src),ctx,false)[0];return el||null},
        link:async(l,ev)=>{await wrSave(entry,true);
          if(l.doc)wrOpen(api,l.doc);else if(l.url)wrExternal(api,l.url,ev.clientX,ev.clientY);
          else if(l.missing&&wrHasGesture(api,'new'))wrFire(api,'new',{title:l.missing}).then(out=>{const nid=wrMade(out);if(nid)api.select({open:nid,back:id,fresh:''})}).catch(()=>{})},
        menu:(ev,vw)=>contextMenu(ev,vw),
        commentPress:cid=>hot(cid,true),
        toggleSource:()=>toggleSource(),
        status:(st,why)=>showStatus(st,why),
        changed:()=>{clearTimeout(entry.countTimer);entry.countTimer=setTimeout(()=>{if(wordsNode.isConnected)setWords(entry.ed.view.state.doc.toString())},250)},
      };
      entry=wrEditorEntry(api,d,{readonly,hooks});entry.api=api;Object.assign(entry.hooks,hooks);
      const ed=entry.ed,v=ed.view;
      v.dom.wrView=v;                           // for a test walk to read (not global)
      if(v.dom.parentNode!==host)host.append(v.dom);
      wrFollow(entry,text);                     // what the world says now, under anything not yet kept
      srcBtn.setAttribute('aria-pressed',String(ed.source()));
      // comments: marks on the words they are about
      const sp=wrSourcePlain(v.state.doc.toString()),list=[];
      for(const c of comments){const f=c.facts||{};if(f.reply_to||f.resolved==='yes'||!f.quote)continue;const r=wrFindQuote(sp,f.quote);if(r)list.push({id:f.id,...r})}
      ed.setComments(list);ed.relink();
      showStatus(entry.status||'saved',entry.why);
      if(v.state.doc.toString()!==text)setWords(v.state.doc.toString());
      // moved into a new page: measure again, and give the caret back if it had it
      v.requestMeasure();
      if(focused&&focused!==v.contentDOM&&focused.isConnected)focused.focus();else if(focused||D.focusEditor){D.focusEditor=false;v.focus()}
    });
  }
  function showStatus(st,why){if(!saveNode.isConnected&&!saveNode.parentNode)return;
    saveNode.className='wr-save wr-save-'+st;saveNode.title=why||'';
    saveNode.textContent=st==='saving'?'Saving…':st==='editing'?'Editing':st==='failed'?'Not saved: '+(why||'refused')+' · your words stay here':'Saved'}
  function hot(cid,scroll){for(const n of desk.querySelectorAll('.wr-hot'))n.classList.remove('wr-hot');
    if(scroll&&panelName&&!api.panelOpen(panelName))api.panel(panelName,true);   // a comment's words were pressed: show it
    const card=margin.querySelector('[data-comment-card="'+cid+'"]');card?.classList.add('wr-hot');wrLater(()=>entry?.ed.hotComment(cid));
    if(scroll==='mark'&&entry)wrLater(()=>{const c=entry.ed.comments().find(x=>x.id===cid);if(c){entry.ed.view.dispatch({selection:{anchor:c.from,head:c.to},scrollIntoView:true});entry.ed.view.focus()}})
    else if(scroll)card?.scrollIntoView({block:'center',behavior:'smooth'})}
  function toggleSource(){wrLater(()=>{if(!entry)return;const on=!entry.ed.source();entry.ed.setSource(on);srcBtn.setAttribute('aria-pressed',String(on));entry.ed.view.focus()})}

  // right-click on selected words: comment on them, send them to JEFF, copy or cut. With nothing selected the browser's
  // own menu shows (spelling, paste)
  function contextMenu(ev,vw){
    const r=vw.state.selection.main;if(r.empty)return false;
    const srcText=vw.state.sliceDoc(r.from,r.to),quote=wrSourcePlain(srcText).plain.slice(0,1200);
    if(!quote)return false;
    ev.preventDefault();
    const x=ev.clientX,y=ev.clientY,items=[{quote:quote.length>140?quote.slice(0,140)+'…':quote}];
    if(wrHasGesture(api,'comment'))items.push({icon:'comment',label:'Comment',key:'in the margin',run:()=>comment(quote,x,y)});
    if(wrHasGesture(api,'ask-jeff'))items.push({icon:'jeff',label:'Send to JEFF',key:'Conversation',run:()=>jeff(quote,x,y)});
    items.push('-',{label:'Copy',key:'Ctrl C',run:()=>{wrCopy(srcText);vw.focus()}});
    if(!readonly)items.push({label:'Cut',key:'Ctrl X',run:()=>{wrCopy(srcText);vw.dispatch({changes:{from:r.from,to:r.to},userEvent:'delete.cut'});vw.focus()}});
    wrMenu(x,y,items,api.askBox?.());
    return true;
  }
  function comment(quote,x,y){
    const sp=wrSourcePlain(entry?entry.ed.view.state.doc.toString():text),around=wrAround(sp,quote);
    wrComposer({x,y,title:'Comment',badge:'✎',quote,hint:'Your comment on these words…',label:'Comment',line:wrLineOf(api,'comment'),keep:D,
      send:async w=>{if(!w)throw Error('Write your comment first');if(entry)await wrSave(entry,true);await wrFire(api,'comment',{value:w,quote,before:around.before,after:around.after,heading:around.heading},'Comment added')}});
  }
  function jeff(quote,x,y){
    wrComposer({x,y,title:quote?'Send these words to JEFF':'Send “'+wrTitle(d)+'” to JEFF',badge:'J',quote,hint:quote?'What should JEFF know or do about them? (optional)':'What should JEFF know or do about this document?',
      label:'Send to JEFF',line:wrLineOf(api,'ask-jeff'),keep:D,send:async w=>{if(!w&&!quote)throw Error('Say something to JEFF first');if(entry)await wrSave(entry,true);await wrFire(api,'ask-jeff',{value:wrToJeff(w,quote,d)},'Sent to JEFF · it is in the Conversation');
        // a said line is not bound into this view, so nothing repaints: read what was sent again, uncached
        api.rows('rows said about='+id).then(api.guard(sent=>drawBelow(D.docs,wrRows(sent)))).catch(()=>{})}});
  }
  function moreMenu(x,y){
    const items=[];
    if(!readonly&&d.kind!=='note'&&wrHasGesture(api,'move'))for(const [c,label] of [['notes','Notes'],['documentation','Agora documentation'],['personal','Personal writing'],['plans','Plans']])
      if(d.collection!==c)items.push({label:'Move to '+label,run:()=>wrFire(api,'move',{value:c},'Moved to '+label).catch(()=>{})});
    if(entry)items.push({icon:'search',label:'Find in this document',key:'Ctrl F',run:()=>wrLater(()=>{entry.ed.view.focus();WR_CM.openSearchPanel(entry.ed.view)})});
    items.push({icon:'code',label:'Copy its id',key:id,run:()=>{wrCopy(id);api.tell('Copied '+id)}});
    if(wrHasGesture(api,'forget'))items.push('-',{label:'Forget this document…',danger:true,run:()=>{if(confirm('Forget “'+wrTitle(d)+'”? Undo brings it back.'))wrFire(api,'forget',{},'Forgotten · undo brings it back').then(()=>api.select({open:view.back&&view.back!==id?view.back:'',back:''})).catch(()=>{})}});
    wrMenu(x,y,items);
  }
  const keys=ev=>{if(ev.defaultPrevented)return;if((ev.ctrlKey||ev.metaKey)&&ev.key.toLowerCase()==='e'&&!ev.target.closest?.('textarea,input')){ev.preventDefault();toggleSource()}};
  document.addEventListener('keydown',keys);api.cleanup(()=>document.removeEventListener('keydown',keys));

  // the margin: comments, open first, in the order their words stand in the document
  const outline=wrOutline(text);
  const top=comments.filter(c=>!c.facts?.reply_to),replies=comments.filter(c=>c.facts?.reply_to);
  const pos=c=>{const i=outline.plain.indexOf(wrNorm(c.facts?.quote||''));return i<0?1e9:i};
  const open=top.filter(c=>c.facts?.resolved!=='yes').sort((a,b)=>pos(a)-pos(b)),done=top.filter(c=>c.facts?.resolved==='yes');
  margin.append(wrEl('div',{class:'wr-margin-head'},wrIcon('comment'),open.length?open.length+(open.length===1?' comment':' comments'):'Comments'));
  if(!open.length)margin.append(wrEl('div',{class:'wr-hint'},'Select words, then right-click to comment on them, or to send them to JEFF. A comment stays beside the words it is about, and says so if they change.'));
  const card=c=>{const n=api.render(c);const box=n.querySelector?.('.wr-replies');if(box)for(const r of replies.filter(r=>r.facts.reply_to===c.facts.id))box.append(api.render(r));
    n.addEventListener('mouseenter',()=>wrLater(()=>entry?.ed.hotComment(c.facts.id)));
    n.addEventListener('mouseleave',()=>wrLater(()=>entry?.ed.hotComment('')));
    n.querySelector('.wr-c-q')?.addEventListener('click',()=>hot(c.facts.id,'mark'));return n};
  for(const c of open)margin.append(card(c));
  if(done.length){const more=wrEl('button',{type:'button',class:'wr-more','aria-expanded':String(!!D.showDone),on:{click:()=>{D.showDone=!D.showDone;list.hidden=!D.showDone;more.textContent=(D.showDone?'Hide ':'Show ')+done.length+' resolved'}}},(D.showDone?'Hide ':'Show ')+done.length+' resolved');
    const list=wrEl('div',{style:{display:'flex',flexDirection:'column',gap:'10px'},hidden:D.showDone?null:''},...done.map(card));margin.append(more,list)}

  // below the sheet: what links here, and what was sent to JEFF about it
  const below=wrEl('section',{class:'wr-below','aria-label':'Linked from'});paper.append(below);
  const drawBelow=(docs,sent)=>{below.replaceChildren();
    // every [[ref]] in every other document, resolved the way its page draws it (id, title, name or file name)
    const links=docs.filter(x=>x.id!==id&&[...String(x.text||'').matchAll(/\[\[([^\]|\n]+)(?:\|[^\]\n]*)?\]\]/g)].some(m=>resolve(m[1])?.id===id));
    if(links.length)below.append(wrEl('h2',{class:'wr-h'},'Linked from '+links.length),...links.map(x=>wrEl('button',{type:'button',class:'wr-row',on:{click:()=>wrOpen(api,x.id)}},wrEl('span',{class:'wr-row-title'},wrTitle(x)),wrEl('span',{class:'wr-row-meta'},wrAgo(api,x.changed)))));
    if(sent.length)below.append(wrEl('h2',{class:'wr-h'},'Sent to JEFF · '+sent.length),...sent.slice(-5).reverse().map(x=>wrEl('div',{class:'wr-row',style:{cursor:'default'}},wrEl('span',{class:'wr-snip'},wrNorm(String(x.text||'').replace(/^>.*$/gm,'').replace(/— (from|about) \[\[[^\]]*\]\]/,''))||'(a passage)'),wrEl('span',{class:'wr-row-meta'},wrWho(api,x,wrEl('span',{})),' · '+wrAgo(api,x.made)))));
  };
  // the documents list draws [[links]] and fills the picker; it is watched, so it is usually already here
  wrReadDocs(api).then(api.guard(docs=>{D.docs=docs;const seen=JSON.stringify(docs.map(x=>[x.id,wrTitle(x),x.source]));
    if(seen!==docsSeen){docsSeen=seen;resolve=wrResolver(docs);entry?.ed.relink()}
    api.read('rows said about='+id).then(api.guard(sent=>drawBelow(docs,wrRows(sent)))).catch(()=>drawBelow(docs,[]))})).catch(()=>{});
  // each document keeps its own place (5 Nov: one place for every document opened a short one at its bottom);
  // a document not seen yet opens at its top. Not until the place is put back does scrolling count, so a page
  // still short while it draws cannot overwrite the remembered place with a clamped one.
  let placing=true;
  desk.addEventListener('scroll',()=>{if(!placing)WR_PLACES.set(id,desk.scrollTop)},{passive:true});
  queueMicrotask(()=>{const want=WR_PLACES.get(id)||0;let tries=0;
    const put=()=>{if(!desk.isConnected)return;desk.scrollTop=want;
      if(Math.abs(desk.scrollTop-want)>2&&++tries<20)return requestAnimationFrame(put);placing=false};put()});
  // the empty page: beside a line puts the caret on that line; below the text, at the end, as a word processor does
  desk.addEventListener('mousedown',ev=>{if(!entry||ev.button!==0)return;if(ev.target!==desk&&ev.target!==root&&ev.target!==paper&&ev.target!==sheet)return;
    const v=entry.ed.view,r=v.contentDOM.getBoundingClientRect();if(ev.clientY<r.top)return;ev.preventDefault();
    let at=v.state.doc.length;
    if(ev.clientY<=r.bottom-2){    // beside the text: the line at that height (a heading's spacing must not give the line above)
      const b=v.lineBlockAtHeight(ev.clientY-v.documentTop);
      at=v.posAtCoords({x:Math.min(Math.max(ev.clientX,r.left+4),r.right-4),y:ev.clientY});
      if(at==null||at<b.from||at>b.to)at=ev.clientX<r.left+r.width/2?b.from:b.to}wrLater(()=>{v.focus();v.dispatch({selection:{anchor:at}})})});
  if(view.fresh===id&&!readonly&&!D.welcomed){D.welcomed=true;queueMicrotask(()=>{title.focus();title.select()})}
  return desk;
}

// ---- doc-comment ---------------------------------------------------------------------------------------------------------
function mountComment(api,s){
  const c=api.facts,D=api.draft,doc=s.doctext||'',reply=!!c.reply_to;
  const root=api.part('body','article',{class:'wr-c'+(c.resolved==='yes'?' wr-resolved':''),'data-comment-card':c.id,'aria-label':'Comment'});
  if(c.quote&&!reply)root.append(api.part('quote','div',{class:'wr-c-q',title:'Show these words in the document'},'“'+c.quote+'”'));
  root.append(api.part('text','div',{class:'wr-c-text'},c.text||''));
  root.append(wrEl('div',{class:'wr-c-who'},wrWho(api,c,wrEl('b',{})),wrEl('span',{},'· '+wrAgo(api,c.made)),c.resolved==='yes'?wrEl('span',{},'· resolved'):null));
  if(c.quote&&!reply){
    const o=wrOutline(doc),q=wrNorm(c.quote),found=o.plain.includes(q);let st='',warn=false;
    if(found){const now=o.headingAt(o.plain.indexOf(q)),was=c.heading||'';st=now&&was&&now!==was?(warn=true,'moved: now under § '+now+', it was under § '+was):now?'under § '+now:''}
    else{const near=[c.before,c.after].some(w=>w&&o.plain.includes(wrNorm(w)));warn=true;st=near?'changed: the words around it are still here, these words are not':'gone: these words are no longer in the text'}
    if(st)root.append(wrEl('div',{class:'wr-c-st'+(warn?' wr-warn':'')},st));
  }
  const acts=wrEl('div',{class:'wr-c-acts'});
  const replyBox=wrEl('div',{class:'wr-reply',hidden:D.replying?null:''});
  if(!reply&&wrHasGesture(api,'reply')){
    const ta=api.part('reply','textarea',{placeholder:'Reply… (Enter sends)','aria-label':'Reply to this comment',value:D.reply||''});
    ta.addEventListener('input',()=>{D.reply=ta.value});
    ta.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();const v=ta.value.trim();if(!v)return;wrFire(api,'reply',{value:v}).then(()=>{D.reply='';D.replying=false}).catch(()=>{})}
      if(e.key==='Escape'){D.replying=false;replyBox.hidden=true}});
    replyBox.append(ta);
    acts.append(wrEl('button',{type:'button',class:'wr-btn',on:{click:()=>{D.replying=!D.replying;replyBox.hidden=!D.replying;if(D.replying)ta.focus()}}},'Reply'));
  }
  if(c.resolved==='yes'){if(wrHasGesture(api,'reopen'))acts.append(wrEl('button',{type:'button',class:'wr-btn',on:{click:()=>wrFire(api,'reopen',{}).catch(()=>{})}},'Reopen'))}
  else if(!reply&&wrHasGesture(api,'resolve'))acts.append(wrEl('button',{type:'button',class:'wr-btn',title:wrLineOf(api,'resolve'),on:{click:()=>wrFire(api,'resolve',{},'Resolved').catch(()=>{})}},wrIcon('check'),'Resolve'));
  if(!reply&&wrHasGesture(api,'ask-jeff'))acts.append(wrEl('button',{type:'button',class:'wr-btn',title:'Send this comment into JEFF’s Conversation',on:{click:e=>{
    const r=e.currentTarget.getBoundingClientRect();
    wrComposer({x:r.left-120,y:r.bottom+6,title:'Send this comment to JEFF',badge:'J',quote:(c.quote?'“'+c.quote+'” — ':'')+(c.text||''),hint:'Anything to add? (optional)',label:'Send to JEFF',line:wrLineOf(api,'ask-jeff'),
      send:async w=>{const d={id:c.about,title:s.doctitle||'the document'};await wrFire(api,'ask-jeff',{value:wrToJeff([w,'A comment: '+(c.text||'')].filter(Boolean).join('\n\n'),c.quote||'',d)},'Sent to JEFF · it is in the Conversation')}})}}},wrIcon('jeff'),'JEFF'));
  root.append(wrEl('div',{class:'wr-replies'}),replyBox);
  if(acts.childNodes.length)root.append(acts);
  return root;
}

export default {css:WR_CSS,mount(api,settings){
  switch(api.node.component){
    case 'writing-shell':return mountShell(api,settings);
    case 'doc-rail':return mountRail(api,settings);
    case 'doc-shelf':return mountShelf(api,settings);
    case 'doc-row':return mountRow(api,settings);
    case 'doc-home':return mountHome(api,settings);
    case 'doc-page':return mountPage(api,settings);
    case 'doc-comment':return mountComment(api,settings);
    default:throw Error('writing components: no '+api.node.component);
  }
}};
