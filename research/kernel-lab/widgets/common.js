// Shared authored widget vocabulary. Installed inline with each definition.
const context = await agora.ready;
const theme = context.theme;
const Q = value => '"'+String(value??'').replace(/\\/g,'\\\\').replace(/"/g,'\\"')+'"';
const el = (tag, attrs={}, ...kids) => {
  const node=document.createElement(tag);
  for(const [k,v] of Object.entries(attrs)) {
    if(k==='on')for(const [event,fn]of Object.entries(v))node.addEventListener(event,fn);
    else if(k==='class')node.className=v;
    else if(k==='style')Object.assign(node.style,v);
    else if(k==='value')node.value=v;
    else node.setAttribute(k,v);
  }
  for(const kid of kids.flat())if(kid!==null&&kid!==undefined)node.append(kid?.nodeType?kid:String(kid));
  return node;
};
const css = text => document.head.append(el('style',{},text));
const button=(label,fn,cls='')=>el('button',{class:cls,on:{click:fn}},label);
const rows=async line=>(await agora.see(line)).rows;
// Tints and priority colours are the theme's (the painter's colour names mapped onto its palette); older hosts give none.
const tint=(key,fallback)=>theme[key]||fallback;
const palette={paper:tint('card','#FFFFFF'),rose:tint('rose','#FBE9E8'),peach:tint('peach','#FFF0DC'),sage:tint('sage','#EAF3E9'),sky:tint('sky','#E8F1FA'),lilac:tint('lilac','#F0EBF8')};
const priorities=[tint('red','#CF514A'),tint('orange','#C58332'),tint('blue','#507EBC'),tint('grey','#9BA3AC')];
// The window is told when its theme changes (widget-host.js): keep the shared values current, repaint through CSS variables.
addEventListener('ag-theme',e=>{
  Object.assign(theme,e.detail.tokens,{roles:e.detail.roles,palette:e.detail.palette,variant:e.detail.variant,font:e.detail.font||theme.font});
  Object.assign(palette,{paper:tint('card','#FFFFFF'),rose:tint('rose','#FBE9E8'),peach:tint('peach','#FFF0DC'),sage:tint('sage','#EAF3E9'),sky:tint('sky','#E8F1FA'),lilac:tint('lilac','#F0EBF8')});
  priorities.splice(0,4,tint('red','#CF514A'),tint('orange','#C58332'),tint('blue','#507EBC'),tint('grey','#9BA3AC'));
});
const flag=p=>el('span',{class:'flag',style:{color:priorities[(+p||4)-1]},'aria-label':'Priority '+p},'⚑');
const tell = error => {const n=el('div',{class:'toast',role:'status'},String(error.message||error));document.body.append(n);setTimeout(()=>n.remove(),5000)};
const act = async (line,saw) => {try{return await agora.do(line,saw)}catch(e){tell(e);throw e}};
css(`:root{--paper:var(--ag-surface,${theme.paper});--card:var(--ag-raised,${theme.card});--ink:var(--ag-ink,${theme.ink});--muted:var(--ag-ink-muted,${theme.muted});--accent:var(--ag-accent,${theme.accent})}
body{font:var(--ag-text,14px)/1.5 var(--ag-font-ui,${theme.font});color:var(--ink);background:var(--paper);-webkit-font-smoothing:antialiased}button,input,textarea,select{font:inherit}button{cursor:pointer;border:0;background:none;color:inherit}button:focus-visible,input:focus-visible,textarea:focus-visible,select:focus-visible{outline:2px solid var(--ag-focus,#83a99a);outline-offset:3px}button{transition:background var(--ag-dur-fast,.16s),transform var(--ag-dur-fast,.16s)}button:active{transform:scale(.97)}input,textarea,select{color:var(--ink);border:1px solid var(--ag-border,#e3e6e4);border-radius:var(--ag-radius-m,9px);padding:10px 12px;background:var(--card)}textarea{resize:vertical}button.primary{background:var(--accent);color:var(--ag-accent-ink,white);border-radius:var(--ag-radius-m,9px);padding:9px 16px;box-shadow:0 2px 3px rgba(0,0,0,.08)}button.soft{background:var(--ag-accent-soft,#edf1ee);border-radius:var(--ag-radius-s,8px);padding:7px 12px}.muted{color:var(--muted)}.eyebrow{font-size:10px;font-weight:650;text-transform:uppercase;letter-spacing:1.8px;color:var(--muted)}.toast{position:fixed;bottom:24px;left:24px;max-width:85%;padding:12px 18px;border:1px solid var(--ag-border,#e6d6ca);border-radius:var(--ag-radius-l,12px);background:var(--ag-warn-soft,#fff5e9);color:var(--ink);box-shadow:var(--ag-shadow,0 12px 40px #24352c18);z-index:1000}.flag{font-size:21px;line-height:1}.swatch{width:23px;height:23px;border-radius:50%;border:1px solid #283b4312;display:inline-block}.swatches{display:flex;gap:8px}h1,h2,h3,p{margin:0}h1{font-weight:650;letter-spacing:-1.4px;font-size:34px}h2{font-size:20px;letter-spacing:-.5px}a{color:var(--accent)}@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important}}`);
