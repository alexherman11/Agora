export default {css:`
.work-line{height:58px;display:flex;align-items:center;gap:12px;padding:0 18px;border-bottom:1px solid var(--work-rule,#e5e9e2);min-width:0;font-size:13px}
.work-line button{all:unset;cursor:pointer;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;border-radius:4px}
.work-line button:hover{text-decoration:underline}
.work-line button:focus-visible{outline:2px solid var(--work-accent,#638779);outline-offset:3px}
.work-line .work-title{flex:2;min-width:70px;font-weight:550}
.work-line .work-owner{flex:1;min-width:45px;color:var(--work-muted,#647367)}
.work-status{flex:none;width:58px;font-size:11px;color:var(--work-accent,#0b6e55)}
.work-line[data-state=Blocked] .work-status{color:var(--work-blocked,#8a4b00)}
.work-blocker{flex:3;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:var(--work-muted,#647367)}
.work-blocker button{max-width:100%;vertical-align:bottom}
.work-inspect{max-width:min(680px,80vw);max-height:65vh;overflow:hidden}
.work-inspect h2{font-size:18px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.work-inspect p{display:-webkit-box;-webkit-line-clamp:5;-webkit-box-orient:vertical;overflow:hidden;overflow-wrap:anywhere}
@media(max-width:650px){.work-line{gap:7px;padding:0 10px;font-size:12px}.work-status{width:48px}.work-blocker{flex:2}}
`,mount(api,s){
  const {P}=api;
  const inspect=()=>{
    const content=P.node('section',{class:'work-inspect'},P.node('h2',{},s.title),P.node('p',{},s.state+' · '+s.owner));
    if(s.blocker)content.append(P.node('p',{},s.blocker+' · '+s.resolver));
    if(s.next)content.append(P.node('p',{},'Next: '+s.next));
    if(s.detail)content.append(P.node('p',{},s.detail));
    let overlay;
    content.prepend(P.press('Close',()=>overlay.close()));
    overlay=P.overlay('dialog',content,{label:s.title});
    Object.assign(overlay.node.style,{background:P.tokens.card,color:P.tokens.ink,maxWidth:'90vw',overflow:'hidden'});
    api.cleanup(()=>overlay.close());
  };
  const name=(label,cls)=>P.node('button',{type:'button',class:cls,title:label,on:{click:inspect}},label);
  const root=api.part('body','article',{class:'work-line','data-state':s.state});
  root.append(P.node('span',{class:'work-status'},s.state),name(s.title,'work-title'),name(s.owner,'work-owner'));
  if(s.blocker){
    const blocker=P.node('span',{class:'work-blocker',title:`${s.blocker} · ${s.resolver}`});
    blocker.append(name(`${s.blocker} · ${s.resolver}`,''));
    root.append(blocker);
  }
  return root;
}};
