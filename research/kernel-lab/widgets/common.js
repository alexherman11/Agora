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
const palette={paper:'#FFFFFF',rose:'#FBE9E8',peach:'#FFF0DC',sage:'#EAF3E9',sky:'#E8F1FA',lilac:'#F0EBF8'};
const priorities=['#CF514A','#C58332','#507EBC','#9BA3AC'];
const flag=p=>el('span',{class:'flag',style:{color:priorities[(+p||4)-1]},'aria-label':'Priority '+p},'⚑');
const tell = error => {const n=el('div',{class:'toast',role:'status'},String(error.message||error));document.body.append(n);setTimeout(()=>n.remove(),5000)};
const act = async (line,saw) => {try{return await agora.do(line,saw)}catch(e){tell(e);throw e}};
css(`:root{--paper:${theme.paper};--card:${theme.card};--ink:${theme.ink};--muted:${theme.muted};--accent:${theme.accent}}
body{font:14px/1.5 ${theme.font};color:var(--ink);background:var(--paper);-webkit-font-smoothing:antialiased}button,input,textarea,select{font:inherit}button{cursor:pointer;border:0;background:none;color:inherit}button:focus-visible,input:focus-visible,textarea:focus-visible,select:focus-visible{outline:2px solid #83a99a;outline-offset:3px}button{transition:background .16s,transform .16s}button:active{transform:scale(.97)}input,textarea,select{color:var(--ink);border:1px solid #e3e6e4;border-radius:9px;padding:10px 12px;background:white}textarea{resize:vertical}button.primary{background:#638779;color:white;border-radius:9px;padding:9px 16px;box-shadow:0 2px 3px #3d625317}button.soft{background:#edf1ee;border-radius:8px;padding:7px 12px}.muted{color:var(--muted)}.eyebrow{font-size:10px;font-weight:650;text-transform:uppercase;letter-spacing:1.8px;color:#8b9791}.toast{position:fixed;bottom:24px;left:24px;max-width:85%;padding:12px 18px;border:1px solid #e6d6ca;border-radius:12px;background:#fff5e9;color:#72563e;box-shadow:0 12px 40px #24352c18;z-index:1000}.flag{font-size:21px;line-height:1}.swatch{width:23px;height:23px;border-radius:50%;border:1px solid #283b4312;display:inline-block}.swatches{display:flex;gap:8px}h1,h2,h3,p{margin:0}h1{font-weight:650;letter-spacing:-1.4px;font-size:34px}h2{font-size:20px;letter-spacing:-.5px}a{color:#587e6b}@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important}}`);
