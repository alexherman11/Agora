// console: a live monospaced log, newest at the bottom, with an optional prompt line under it (a coder's terminal).
// value: one entry per line, `kind<TAB>time<TAB>who<TAB>text` (a line without tabs is plain); kinds: said (the log's
// own person), heard (someone else), act (a receipt of what was done), own (outside any chat), now (doing now), error.
// Settings: value, label, hint (the prompt's placeholder), empty. Gesture: say {value}, when the prompt is authored.
export default {css:`
.console{display:flex;flex-direction:column;width:100%;box-sizing:border-box;height:max(280px,calc(100vh - var(--console-offset,104px)));border-radius:12px;overflow:hidden;border:1px solid var(--console-rule)}
.console-log{flex:1 1 auto;min-height:0;overflow:auto;margin:0;padding:12px 14px 10px;font:12.5px/1.6 var(--ag-font-mono,ui-monospace,"Cascadia Code",Consolas,monospace)}
.console-line{display:grid;grid-template-columns:5.2ch 9ch 1fr;column-gap:1ch;white-space:pre-wrap;word-break:break-word}
.console-line.plain{display:block}
.console-time,.console-who{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.console-prompt{display:flex;align-items:center;gap:1ch;padding:9px 14px;border-top:1px solid var(--console-rule);font:13px/1.4 var(--ag-font-mono,ui-monospace,"Cascadia Code",Consolas,monospace)}
.console-prompt input{all:unset;flex:1;min-width:0;font:inherit}
`,mount(api,s){
  const {P}=api,t=P.tokens;
  const colour={said:t.accent,heard:t.ink,act:t.muted,own:t.blue,now:t.orange,error:t.red};
  const root=api.part('body','section',{class:'console','aria-label':s.label||'Log',
    style:{background:t.card,color:t.ink,'--console-rule':t.muted+'40'}});
  const log=api.part('log','div',{class:'console-log',role:'log','aria-live':'polite'});
  const lines=String(s.value||'').split('\n').filter(x=>x.trim());
  for(const raw of lines){
    const parts=raw.split('\t');
    if(parts.length<4){log.append(P.node('div',{class:'console-line plain'},raw));continue}
    const [kind,time,who,...rest]=parts,text=rest.join('\t');
    log.append(P.node('div',{class:'console-line '+kind,style:{color:colour[kind]||t.ink}},
      P.node('span',{class:'console-time',style:{color:t.muted}},time),
      P.node('span',{class:'console-who',style:{color:kind==='act'?t.muted:colour[kind]||t.ink}},kind==='act'?'  ↳':who),
      P.node('span',{},text)));
  }
  if(!lines.length)log.append(P.node('div',{class:'console-line plain',style:{color:t.muted}},s.empty||'Nothing yet.'));
  root.append(log);
  if(api.node.gestures.some(g=>g.event==='say')){
    const input=api.part('input','input',{type:'text',placeholder:s.hint||'','aria-label':s.hint||s.label||'Say',
      autocomplete:'off',spellcheck:'true',style:{color:t.ink}});
    input.addEventListener('keydown',e=>{
      if(e.key!=='Enter'||e.shiftKey||!input.value.trim())return;
      e.preventDefault();const value=input.value;input.readOnly=true;
      api.fire('say',{value}).then(()=>{for(const box of [input,...document.querySelectorAll('.console-prompt input')])if(box.value===value)box.value=''}).catch(api.tell).finally(()=>{input.readOnly=false;const now=document.querySelector('.console-prompt input');(now&&now.isConnected?now:input).focus()});
    });
    root.append(api.part('prompt','label',{class:'console-prompt',style:{background:t.paper}},
      P.node('span',{style:{color:t.accent}},'›'),input));
  }
  requestAnimationFrame(()=>{log.scrollTop=log.scrollHeight});
  return root;
}};
