css(`body{padding:38px 42px 24px;min-width:660px}.heading{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px}.mark{font-size:12px;display:flex;gap:7px;align-items:center;color:#7d8b83}.mark i{height:6px;width:6px;background:#85ad92;border-radius:50%}.sub{font-size:13px;color:#929b99}.tools{display:flex;gap:10px;align-items:center;margin:26px 0}.quick{flex:1;position:relative}.quick input{width:100%;padding:13px 15px 13px 39px;background:#fff;border-color:#e5e8e3;box-shadow:0 2px 4px #26382c03}.plus{position:absolute;left:15px;top:8px;font-size:23px;color:#99a99d}.key{font-size:10px;border:1px solid #dbe1dc;border-radius:4px;padding:1px 5px;color:#97a099}.filters{display:flex;gap:5px;margin:0 0 27px;align-items:center}.filters button{padding:5px 12px;border-radius:7px;color:#8b9591;font-size:12px}.filters button.selected{background:#e7eee8;color:#54745d;font-weight:600}.filters .space{flex:1}.board{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:22px}.lane{min-width:0;min-height:360px;padding:0 4px 50px;border-radius:12px;transition:background .2s}.lane.over{background:#e9f0eb}.lanehead{display:flex;align-items:center;gap:9px;margin:0 4px 16px;font-size:12px;font-weight:600}.dot{height:7px;width:7px;border-radius:50%;background:#c4c9c4}.dot.Now{background:#d7af72}.dot.Done{background:#89ad97}.count{font-size:11px;font-weight:400;color:#a0aaa3}.lanehead button{margin-left:auto;color:#a1aba5}.card{position:relative;background:white;border:1px solid #e5e8e2;border-radius:12px;padding:16px 16px 13px;margin-bottom:11px;box-shadow:0 2px 3px #273a2b04,0 6px 14px #273a2b02;cursor:grab;touch-action:none;transition:box-shadow .18s;user-select:none}.card:hover{box-shadow:0 6px 20px #25372b0c;border-color:#cfd8d0}.card.dragging{position:fixed;z-index:90;cursor:grabbing;box-shadow:0 20px 40px #243a292b;pointer-events:none;transform:rotate(-2deg)}.cardtitle{font-size:13px;line-height:1.6;font-weight:550;margin:9px 0 12px;overflow-wrap:anywhere}.cardtop{display:flex;justify-content:space-between;align-items:center}.cardtop button{color:#96a198;font-size:18px;line-height:1}.cardfoot{display:flex;gap:6px;align-items:center;font-size:10px;color:#919a94}.avatar{border-radius:50%;width:20px;height:20px;display:grid;place-items:center;font-size:8px;background:#ecede7;color:#7c8879;margin-left:auto}.notechip{font-size:10px;color:#809080}.noteexcerpt{margin:0 0 12px;padding:8px 10px;border-radius:6px;font-size:11px;color:#7d8278;white-space:pre-line;overflow:hidden;max-height:60px}.empty{font-size:12px;color:#a0aaa2;padding:24px 10px;border:1px dashed #dfe5dc;border-radius:10px;text-align:center}.menu{position:fixed;z-index:100;background:#fff;border:1px solid #e4e7e1;box-shadow:0 18px 50px #24302c22;border-radius:12px;padding:8px;width:230px;max-height:90vh;overflow:auto}.menu button{display:block;text-align:left;width:100%;font-size:12px;padding:7px 10px;border-radius:6px}.menu button:hover{background:#f1f4ef}.menulabel{font-size:9px;letter-spacing:1.4px;color:#9aa29a;margin:9px 10px 4px}.menu .swatches{padding:8px 10px}.menu .swatch{padding:0;width:22px;height:22px}.veil{position:fixed;inset:0;background:#2a3c2b18;backdrop-filter:blur(3px);z-index:110;display:flex;justify-content:flex-end}.drawer{width:460px;max-width:90vw;background:#fdfdfb;box-shadow:-12px 0 70px #233f3314;overflow:auto;padding:28px;animation:arrive .25s ease-out}.drawer label{display:block;color:#8f9a92;font-size:11px;margin:22px 0 8px}.drawer input,.drawer textarea{width:100%;font-size:13px}.drawer textarea{min-height:110px;line-height:1.7}.drawerhead{display:flex;justify-content:space-between;align-items:center}.editorbar{display:flex;gap:4px;align-items:center;margin-bottom:8px}.editorbar button{padding:4px 8px;border-radius:5px;background:#f0f3ed;font-size:11px}.history{font-size:11px;line-height:1.7;color:#8b978e;margin-top:12px}.history article{border-left:2px solid #e0e9df;padding:0 0 14px 12px}.history strong{display:block;font-weight:500;color:#5a6e60}.foot{border-top:1px solid #e8ebe5;margin-top:35px;padding-top:15px;font-size:10px;color:#a1aaa3;display:flex;justify-content:space-between}@keyframes arrive{from{transform:translateX(24px);opacity:0}to{transform:none;opacity:1}}`);
const app=el('main');document.body.append(app);
let tasks=[], settings, filter='all', selected, menu, dragging=false, doneOpen=true;
const lanes=['Backlog','Now','Done'];
const heading=el('div',{class:'heading'},el('div',{},el('div',{class:'eyebrow'},'A LITTLE SPACE FOR WHAT MATTERS'),el('h1',{},'Task board')),el('div',{class:'mark'},el('i'), 'Shared world'));
const input=el('input',{placeholder:'Add something worth doing…','aria-label':'Add a task',on:{keydown:async e=>{if(e.key==='Enter'&&input.value.trim()){await act('summarize.add text='+Q(input.value));input.value='';await refresh()}}}});
const filters=el('div',{class:'filters'}), board=el('div',{class:'board'});
app.append(heading,el('p',{class:'sub'},'A clear mind, one thing at a time.'),el('div',{class:'tools'},el('div',{class:'quick'},el('span',{class:'plus'},'+'),input),el('span',{class:'key'},'N'),button('Undo',async()=>{await act('undo');refresh()},'soft')),filters,board,el('footer',{class:'foot'},el('span',{},'Drag to move · right-click for actions'),el('span',{},'One world. Every change remembered.')));
const readSaw=t=>({[t.id]:t.rev});
async function change(t,line){await act(line,readSaw(t));await refresh()}
function closeMenu(){menu?.remove();menu=null}
function openMenu(t,x,y){
  closeMenu();menu=el('div',{class:'menu',role:'menu'});
  menu.append(el('div',{class:'menulabel'},'PRIORITY'));
  for(let p=1;p<=4;p++)menu.append(button('⚑  P'+p+([' · Urgent',' · High',' · Normal',' · Low'][p-1]),()=>{closeMenu();change(t,`task-priority ${t.id} priority=${p}`)}));
  menu.append(el('div',{class:'menulabel'},'CARD COLOUR'));
  const sw=el('div',{class:'swatches'});for(const [name,c]of Object.entries(palette))sw.append(button('',()=>{closeMenu();change(t,`task-colour ${t.id} colour=${name}`)},'swatch'));[...sw.children].forEach((b,i)=>{b.style.background=Object.values(palette)[i];b.title=Object.keys(palette)[i]});menu.append(sw);
  menu.append(el('div',{class:'menulabel'},'MOVE TO'));
  for(const lane of lanes)menu.append(button(lane,()=>{closeMenu();change(t,`task-move ${t.id} to=${lane}`)}));
  for(const who of ['Alex','JEFF'])menu.append(button('Assign to '+who,()=>{closeMenu();change(t,`task-assign ${t.id} who=${who}`)}));
  menu.append(button('Details & rename',()=>{closeMenu();details(t)}),button('Summarize',()=>{closeMenu();change(t,'summarize.task '+t.id)}),button('Remove',()=>{closeMenu();change(t,'task-remove '+t.id)}));
  document.body.append(menu);const r=menu.getBoundingClientRect();menu.style.left=Math.min(x,innerWidth-r.width-10)+'px';menu.style.top=Math.max(8,Math.min(y,innerHeight-r.height-10))+'px';
}
function draw(){
  filters.replaceChildren();for(const p of ['all','1','2','3','4'])filters.append(button(p==='all'?'All tasks':'P'+p,async()=>{await change(settings,`task-filter ${settings.id} priority=${p}`)},filter===p?'selected':''));
  filters.append(el('span',{class:'space'}),button('Summarize board',async()=>{await act('summarize.all');refresh()}));
  board.replaceChildren();
  for(const lane of lanes){
    const group=tasks.filter(t=>t.lane===lane).sort((a,b)=>(+a.priority||4)-(+b.priority||4));
    const column=el('section',{class:'lane','data-lane':lane},el('div',{class:'lanehead'},el('i',{class:'dot '+lane}),lane,el('span',{class:'count'},group.length),button(lane==='Done'?(doneOpen?'⌄':'›'):'+',()=>{if(lane==='Done'){doneOpen=!doneOpen;draw()}else input.focus()})));
    if(lane!=='Done'||doneOpen){
      for(const t of group.filter(t=>filter==='all'||String(t.priority)===filter)){
        const more=button('···',e=>{e.stopPropagation();const r=e.currentTarget.getBoundingClientRect();openMenu(t,r.right,r.bottom)});
        const card=el('article',{class:'card','data-task':t.id,tabindex:'0',style:{background:palette[t.colour]||palette.paper},on:{contextmenu:e=>{e.preventDefault();openMenu(t,e.clientX,e.clientY)},dblclick:()=>details(t),keydown:e=>{if(e.key==='Enter')details(t);if(/^[1-4]$/.test(e.key))change(t,`task-priority ${t.id} priority=${e.key}`);if(e.key.toLowerCase()==='d')change(t,`task-move ${t.id} to=Done`);if(e.key==='Delete')change(t,'task-remove '+t.id)}}},el('div',{class:'cardtop'},flag(t.priority||4),more),el('div',{class:'cardtitle'},t.short||t.title));
        if(t.note)card.append(el('div',{class:'noteexcerpt',style:{background:palette[t.note_colour]||'#f6f6f0'}},t.note.replace(/[*_#]/g,'').slice(0,130)));
        card.append(el('div',{class:'cardfoot'},el('span',{},t.short_source?.startsWith('local')?'✧ Summarized':t.note?'▤ Note':'○ Ready when you are'),el('span',{class:'avatar',title:t.who||'Unassigned'},(t.who||'A').slice(0,2).toUpperCase())));
        card.addEventListener('pointerdown',e=>beginDrag(e,card,t));column.append(card);
      }
      if(!group.length)column.append(el('div',{class:'empty'},lane==='Done'?'Good things take their time.':'Room for the next good idea.'));
    }
    board.append(column);
  }
}
function beginDrag(e,card,t){
  if(e.button!==0||e.target.closest('button'))return;
  const start={x:e.clientX,y:e.clientY},bounds=card.getBoundingClientRect();let ghost,target,active=false,px=bounds.x,py=bounds.y,vx=0,vy=0,tx=px,ty=py,raf;
  const tick=()=>{vx=(vx+(tx-px)*.24)*.65;vy=(vy+(ty-py)*.24)*.65;px+=vx;py+=vy;ghost.style.left=px+'px';ghost.style.top=py+'px';raf=requestAnimationFrame(tick)};
  card.setPointerCapture(e.pointerId);
  const move=ev=>{
    if(!active&&Math.hypot(ev.clientX-start.x,ev.clientY-start.y)>5){active=dragging=true;ghost=card.cloneNode(true);ghost.classList.add('dragging');ghost.style.width=bounds.width+'px';document.body.append(ghost);card.style.opacity='.25';tick()}
    if(!active)return;tx=bounds.x+ev.clientX-start.x;ty=bounds.y+ev.clientY-start.y;
    target=[...document.querySelectorAll('.lane')].find(l=>{const r=l.getBoundingClientRect();return ev.clientX>=r.left&&ev.clientX<=r.right&&ev.clientY>=r.top&&ev.clientY<=r.bottom});document.querySelectorAll('.lane').forEach(l=>l.classList.toggle('over',l===target));
  };
  const finish=async ev=>{card.removeEventListener('pointermove',move);card.removeEventListener('pointerup',finish);card.removeEventListener('pointercancel',cancel);cancelAnimationFrame(raf);ghost?.remove();card.style.opacity='';document.querySelectorAll('.over').forEach(l=>l.classList.remove('over'));dragging=false;if(active&&ev.type!=='pointercancel'&&target&&target.dataset.lane!==t.lane)await change(t,`task-move ${t.id} to=${target.dataset.lane}`)};
  const cancel=ev=>finish(ev);
  card.addEventListener('pointermove',move);card.addEventListener('pointerup',finish);card.addEventListener('pointercancel',cancel);
}
async function details(t){
  const veil=el('div',{class:'veil'}),drawer=el('section',{class:'drawer','aria-label':'Task details'});veil.append(drawer);document.body.append(veil);
  const close=()=>veil.remove();veil.addEventListener('click',e=>{if(e.target===veil)close()});
  const title=el('input',{value:t.title||'','aria-label':'Task title'}),full=el('textarea',{value:t.text||t.title||'','aria-label':'Full description'}),note=el('textarea',{value:t.note||'','aria-label':'Notes',style:{background:palette[t.note_colour]||'#fff'}});
  let current=t;
  async function save(){await change(current,'task-rename '+t.id+' title='+Q(title.value));current=tasks.find(x=>x.id===t.id);await change(current,'summarize.save '+t.id+' field=text text='+Q(full.value));current=tasks.find(x=>x.id===t.id);await change(current,'summarize.save '+t.id+' field=note text='+Q(note.value));current=tasks.find(x=>x.id===t.id);tell('Saved to the world')}
  function wrap(mark){const a=note.selectionStart,b=note.selectionEnd;note.setRangeText(mark+note.value.slice(a,b)+mark,a,b,'select');note.focus()}
  const tools=el('div',{class:'editorbar'},button('B',()=>wrap('**')),button('I',()=>wrap('_')),button('☐',()=>{note.setRangeText('- [ ] ',note.selectionStart,note.selectionStart,'end');note.focus()}));
  const sw=el('div',{class:'swatches'});for(const [name,c]of Object.entries(palette)){const b=button('',async()=>{await change(current,`task-note-colour ${t.id} colour=${name}`);current=tasks.find(x=>x.id===t.id);note.style.background=c},'swatch');b.title='Note '+name;b.style.background=c;sw.append(b)}
  note.addEventListener('keydown',e=>{if(e.ctrlKey||e.metaKey){if(e.key==='b'){e.preventDefault();wrap('**')}if(e.key==='i'){e.preventDefault();wrap('_')}if(e.key==='s'){e.preventDefault();save()}}});
  drawer.append(el('div',{class:'drawerhead'},el('span',{class:'eyebrow'},'THE WHOLE PICTURE'),button('×',close)),el('label',{},'Task'),title,el('label',{},'Full description'),full,el('label',{},'Notes'),tools,note,sw,el('div',{style:{marginTop:'24px',display:'flex',justifyContent:'space-between'}},button('Close',close,'soft'),button('Save changes',save,'primary')),el('label',{},'Recorded history'));
  const history=el('div',{class:'history'});drawer.append(history);
  const events=await rows('history '+t.id);for(const h of events.slice(-12).reverse())history.append(el('article',{},el('strong',{},h.word+' · '+h.by),h.changes,el('div',{},h.at)));
}
async function refresh(){if(dragging)return;try{[tasks,[settings]]=await Promise.all([rows('rows taskboard-task'),rows('rows taskboard-settings')]);filter=String(settings?.filter||'all');draw();await agora.describe(`Task board: ${tasks.length} tasks. ${lanes.map(l=>l+': '+tasks.filter(t=>t.lane===l).length).join('; ')}. Filter ${filter}.`)}catch(e){tell(e)}}
document.addEventListener('click',e=>{if(menu&&!menu.contains(e.target)&&!e.target.closest('.cardtop'))closeMenu()});
document.addEventListener('keydown',e=>{if(e.key==='Escape'){closeMenu();document.querySelector('.veil')?.remove()}const typing=e.target?.closest?.('input,textarea,select,[contenteditable]:not([contenteditable="false"])')||document.activeElement?.isContentEditable||['INPUT','TEXTAREA','SELECT'].includes(document.activeElement?.tagName);if(!typing&&!e.defaultPrevented&&e.key.toLowerCase()==='n'&&!e.ctrlKey&&!e.metaKey&&!e.altKey){e.preventDefault();input.focus()}});
for(const word of ['make','set','forget','undo'])await agora.hear(word,refresh);
await refresh();
