// band: a titled band of rows with a count, folding to one quiet line when it holds nothing (the old desk's home-board
// bands: NEEDS YOU 2, IN MOTION 5 ...). Settings: name, tone (amber, mint, lilac, rose or grey: whose move it is),
// empty (the quiet words when there are no rows), folded (yes: starts folded; pressing the head opens it, for this view).
export default {css:`
.band{display:flex;flex-direction:column;gap:2px}
.band-head{all:unset;display:flex;align-items:center;gap:8px;padding:4px 2px 5px;font-size:11px;font-weight:650;letter-spacing:.08em;text-transform:uppercase;cursor:default;border-bottom:1px solid var(--band-rule)}
.band-head.foldable{cursor:pointer}
.band-count{font-variant-numeric:tabular-nums;border-radius:999px;padding:0 7px;line-height:17px;font-size:11px;letter-spacing:0}
.band-quiet{font-weight:400;letter-spacing:0;text-transform:none;font-size:12px}
.band-chev{margin-left:auto;font-size:12px;opacity:.7}
.band-rows{display:flex;flex-direction:column;gap:1px;padding-top:2px}
.band.band-folded .band-rows,.band.band-empty .band-rows{display:none}
`,mount(api,s){
  const {P}=api,t=P.tokens;
  const tone={amber:t.orange,mint:t.accent,lilac:t.blue,rose:t.red,grey:t.muted}[s.tone]||t.ink;
  const kids=api.children.map(api.render);
  const count=kids.reduce((n,k)=>n+(k.children?k.children.length:0),0);
  const key='fold-'+String(s.name||'band').toLowerCase().replace(/[^a-z0-9]+/g,'-');
  const view=api.view?api.view():{};
  const folded=count>0&&(view[key]!==undefined?view[key]==='yes':String(s.folded)==='yes'||s.folded===true);
  const root=api.part('body','section',{class:'band'+(count?'':' band-empty')+(folded?' band-folded':''),'aria-label':s.name,
    style:{'--band-rule':t.muted+'33'}});
  const head=api.part('heading','button',{class:'band-head'+(count?' foldable':''),type:'button','aria-expanded':String(!folded),
    style:{color:count?tone:t.muted}},P.node('span',{},s.name||''));
  if(count)head.append(api.part('count','span',{class:'band-count',style:{background:tone+'22',color:tone}},String(count)),
    P.node('span',{class:'band-chev'},folded?'▸':'▾'));
  else head.append(api.part('quiet','span',{class:'band-quiet',style:{color:t.muted}},'· '+(s.empty||'nothing here')));
  if(count)head.addEventListener('click',()=>api.select({[key]:folded?'no':'yes'}));
  root.append(head,P.node('div',{class:'band-rows'},...kids));
  return root;
}};
