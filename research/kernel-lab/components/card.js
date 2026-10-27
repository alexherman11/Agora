export default {mount(api,s){
  const {el,button}=api,t=api.facts;
  const menu=api.children.find(n=>n.component==='menu');
  const showMenu=(x,y)=>api.openMenu(menu,x,y);
  const card=api.part('body','article',{class:'card','data-task':t.id,'data-carry':'card',tabindex:'0',style:{background:api.palette[s.colour]||api.palette.paper},on:{
    contextmenu:e=>{e.preventDefault();showMenu(e.clientX,e.clientY)},dblclick:details,keydown:e=>{if(e.target.closest('input,textarea,select,[contenteditable=true]'))return;if(e.key==='Enter')details();else{const key=e.key.length===1?e.key.toLowerCase():e.key;const gesture=api.node.gestures.find(g=>g.event==='key '+key);if(gesture){e.preventDefault();api.fire(gesture.event).catch(api.tell)}}}
  }});
  const more=button('···',e=>{e.stopPropagation();const r=e.currentTarget.getBoundingClientRect();showMenu(r.right,r.bottom)});
  card.append(api.part('top','div',{class:'cardtop'},...api.children.filter(n=>n.component==='flag').map(api.render),more),api.part('title','div',{class:'cardtitle'},s.title||t.title));
  if(s.note)card.append(api.part('note','div',{class:'noteexcerpt',style:{background:api.palette[s.note_colour]||'var(--ag-hover,#f6f6f0)'}},s.note.replace(/[*_#]/g,'').slice(0,130)));
  card.append(api.part('footer','div',{class:'cardfoot'},el('span',{},t.short_source?.startsWith('local')?'✧ Summarized':s.note?'▤ Note':'○ Ready when you are'),api.part('avatar','span',{class:'avatar',title:s.who||'Unassigned'},api.display('who')!==s.who?api.display('who'):(s.who||'A').slice(0,2).toUpperCase())));
  for(const child of api.children.filter(n=>!['flag','menu'].includes(n.component)))card.append(api.render(child));
  card.addEventListener('pointerdown',e=>api.beginDrag(e,card));
  if(t.editing==='yes')queueMicrotask(()=>{if(!document.querySelector('.drawer'))details()});
  return card;
  async function details(){
    const drawer=el('section',{class:'drawer','aria-label':'Task details'});
    const shown=api.P.overlay('drawer',drawer,{label:'Task details',close:()=>{if(api.latest().facts.editing==='yes')currentFire('close',{}).catch(api.tell)}});
    const close=()=>shown.close();
    const title=el('input',{value:t.title||'','aria-label':'Task title'}),full=el('textarea',{value:t.text||t.title||'','aria-label':'Full description'}),note=el('textarea',{value:t.note||'','aria-label':'Notes',style:{background:api.palette[t.note_colour]||'var(--card,#fff)'}});
    let edits=Promise.resolve();
    function currentFire(event,values){
      const result=edits.then(()=>{const n=api.latest();const g=n.gestures.find(g=>g.event===event);if(!g)throw Error('Missing '+event);return api.fireLatest(n,event,values)});
      edits=result.catch(()=>{});return result;
    }
    async function save(){for(const [event,value]of [['title',title.value],['text',full.value],['note',note.value]]){await currentFire(event,{value})}api.tell('Saved to the world')}
    function wrap(mark){const a=note.selectionStart,b=note.selectionEnd;note.setRangeText(mark+note.value.slice(a,b)+mark,a,b,'select');note.focus()}
    const tools=el('div',{class:'editorbar'},button('B',()=>wrap('**')),button('I',()=>wrap('_')),button('☐',()=>{note.setRangeText('- [ ] ',note.selectionStart,note.selectionStart,'end');note.focus()}));
    const sw=el('div',{class:'swatches'});for(const [name,c]of Object.entries(api.palette)){const b=button('',async()=>{await currentFire('note-colour',{value:name});note.style.background=c},'swatch');b.title='Note '+name;b.style.background=c;sw.append(b)}
    const setStyle=style=>{note.style.fontWeight=style==='strong'?'bold':'normal';note.style.fontStyle=style==='slant'?'italic':'normal'};setStyle(s.note_style);
    for(const style of ['normal','strong','slant'])tools.append(button(style,async()=>{await currentFire('note-style',{value:style});setStyle(style)}));
    note.addEventListener('keydown',e=>{if(e.ctrlKey||e.metaKey){if(e.key==='b'){e.preventDefault();wrap('**')}if(e.key==='i'){e.preventDefault();wrap('_')}if(e.key==='s'){e.preventDefault();save()}}});
    drawer.append(el('div',{class:'drawerhead'},el('span',{class:'eyebrow'},'THE WHOLE PICTURE'),button('×',close)),el('label',{},'Task'),title,el('label',{},'Full description'),full,el('label',{},'Notes'),tools,note,sw,el('div',{style:{marginTop:'24px',display:'flex',justifyContent:'space-between'}},button('Close',close,'soft'),button('Save changes',save,'primary')),el('label',{},'Recorded history'));
    const history=el('div',{class:'history'});drawer.append(history);for(const h of (await api.rows('history '+t.id)).slice(-12).reverse())history.append(el('article',{},el('strong',{},h.word+' · '+h.by),h.changes,el('div',{},h.at)));
  }
}};
