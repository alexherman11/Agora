import {initialState,dispatch,project,asText} from './model.mjs';
const $=s=>document.querySelector(s), clone=x=>structuredClone(x), pretty=x=>JSON.stringify(x,null,2);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let current, checkpoint=null, checkpointSubject=null, scale=1, fitMode=true, activeDrag=null, loading=false, installedDraft='', lastReceipt=null;
const shownText=new Set(), actor='alex';
function notify(text,error=true){$('#notice').textContent=text;$('#notice').hidden=false;$('#notice').classList.toggle('error',error);}
function clearNotice(){$('#notice').hidden=true;}
function dispatchAction(action,{quiet=false}={}){
  const result=dispatch(current,action,{actor});
  if(!result.ok){notify(result.errors.join(' '));render();return false;}
  current=result.document;lastReceipt=result.receipt;clearNotice();
  if(result.receipt.scope==='shared')$('#connection').textContent='Unsaved desk checkpoint';
  if(!quiet){const changed=result.receipt.changed.length?result.receipt.changed.join(', '):'view state';$('#last-receipt').textContent=`${action.type} accepted · ${changed} · revision ${result.receipt.revision}${result.receipt.ruleIds.length?' · '+result.receipt.ruleIds.join(', '):''}`;}
  render();return true;
}
function noteById(id){return current.state.notes.find(n=>n.id===id);}
function render(){
  if(!current)return;
  const s=current.state;
  for(const w of s.windows){const el=$(`[data-window="${w.id}"]`);el.style.left=w.x+'px';el.style.top=w.y+'px';el.style.width=w.w+'px';el.style.height=w.h+'px';el.hidden=!w.open;}
  $('#revision').textContent='revision '+s.revision;
  $('#note-count').textContent=s.notes.length+' shared '+(s.notes.length===1?'note':'notes');
  const notesProjection=project(current,'notes');
  $('#notes-plane').innerHTML=notesProjection.rows.map(row=>{const n=noteById(row.id),excerpt=n.text.length>145?n.text.slice(0,145)+'…':n.text;return `<article class="note ${s.selectedId===n.id?'selected':''}" data-note="${esc(n.id)}" style="left:${n.x}px;top:${n.y}px;background:${n.color}"><button class="note-drag" data-move-note="${esc(n.id)}" aria-label="Move ${esc(n.title)}; drag or use arrow keys"><span>${esc(n.id)} · r${n.rev}</span><span class="grab">⠿</span></button><button class="note-content" data-select="${esc(n.id)}" aria-label="Open ${esc(n.title)} in Editor" aria-pressed="${s.selectedId===n.id}"><h2>${esc(n.title)}</h2><div class="note-line"></div><p>${esc(excerpt)}</p><div class="note-tags">${n.tags.length?n.tags.map(t=>'#'+esc(t)).join(' '):'An open thought'}</div></button></article>`;}).join('');
  $('#notes-plane').style.width=Math.max(530,...s.notes.map(n=>n.x+175))+'px';$('#notes-plane').style.height=Math.max(330,...s.notes.map(n=>n.y+260))+'px';
  $('#notes-caption').textContent=s.selectedId?`${s.selectedId} is open in Editor · ${s.notes.length} subjects, one placement each`:'Select a note to open the same subject in Editor.';
  const n=noteById(s.editor.noteId), stale=n&&n.rev!==s.editor.baseRev;
  $('#editor-title').textContent=n?n.title:'A place to begin.';
  $('#editor-identity').textContent=n?`${n.id.toUpperCase()} / SHARED SUBJECT · r${n.rev}`:'NO NOTE SELECTED';
  $('#editor-status').textContent=stale?'New revision · draft held':s.editor.dirty?'Unsettled draft':'Reading shared text';
  $('#editor-status').classList.toggle('dirty',s.editor.dirty||stale);
  const textarea=$('#editor-draft');
  // The editor input node is never reconstructed on another application's update.
  if(textarea.value!==s.editor.draft){const focused=document.activeElement===textarea,start=textarea.selectionStart,end=textarea.selectionEnd;textarea.value=s.editor.draft;if(focused)textarea.setSelectionRange(Math.min(start,textarea.value.length),Math.min(end,textarea.value.length));}
  textarea.disabled=!n;
  $('#priority').checked=!!n?.tags.includes('priority');$('#priority').disabled=!n;
  $('#save-note').disabled=!n||!s.editor.dirty;$('#reopen-note').disabled=!n;$('#remove-note').disabled=!n;
  $('#draft-status').textContent=stale?'Source changed. Your exact draft is held.':s.editor.dirty?'Draft only · note unchanged':'Accepted locally · checkpoint with Save desk';
  $('#draft-status').classList.toggle('dirty',s.editor.dirty||stale);
  const act=project(current,'together'),rows=act.rows.filter(r=>!['context','limit'].includes(r.kind));
  $('#activity-summary').textContent=s.events.at(-1)?.summary||'A quiet beginning.';
  $('#activity-rows').innerHTML=rows.length?rows.slice().reverse().map(r=>`<div class="activity-row" data-row="${esc(r.id)}" data-kind="${esc(r.kind)}"><span class="event-dot"></span><div><small>${esc(r.id)}${r.kind==='unread'?' · NEW':''}</small><p>${esc(r.text)}</p></div></div>`).join(''):'<div class="activity-row"><span class="event-dot"></span><p>Nothing accepted yet. Your first edit will leave a trace here.</p></div>';
  $('#event-count').textContent=s.events.length+' retained events';
  for(const app of ['notes','editor','together']){$('#'+app+'-text').textContent=asText(current,app);$('#'+app+'-text').hidden=!shownText.has(app);$(`[data-window="${app}"] .window-body`).hidden=shownText.has(app);}
  if($('#text-dialog').open)renderAllText();
  applyCamera();
}
function renderAllText(){
  $('#all-text-content').textContent=`COMMONPLACE · checkpoint ${checkpoint??'not saved'} · model revision ${current.state.revision}\n\n`+['notes','editor','together'].map(app=>asText(current,app)).join('\n\n────────────────────────────\n\n');
}
function applyCamera(){
  if(activeDrag||!current)return;
  const w=Math.max(1245,...current.state.windows.map(w=>w.x+w.w+25)),h=Math.max(480,...current.state.windows.map(w=>w.y+w.h+25));
  $('#plane').style.width=w+'px';$('#plane').style.height=h+'px';
  if(fitMode)scale=Math.max(.2,Math.min(1,($('#desktop').clientWidth-12)/w,($('#desktop').clientHeight-12)/h));
  $('#plane').style.transform=`scale(${scale})`;$('#desk-extents').style.width=w*scale+'px';$('#desk-extents').style.height=h*scale+'px';$('#zoom').textContent=Math.round(scale*100)+'%';
}
function selectNote(id){const n=noteById(id);if(!n)return;if(dispatchAction({type:'select',id,expectedSubjectRev:n.rev})){const w=$('#editor-window');w.style.zIndex='5';$('#editor-draft').focus({preventScroll:true});}}
function beginDrag(e){
  const target=e.target.closest('[data-move-note],[data-move-window]');if(!target||e.button!==0)return;
  const kind=target.hasAttribute('data-move-note')?'move':'window',id=target.dataset.moveNote||target.dataset.moveWindow;
  const value=kind==='move'?noteById(id):current.state.windows.find(w=>w.id===id);if(!value)return;
  e.preventDefault();target.focus();const element=kind==='move'?target.closest('.note'):target.closest('.app-window');
  activeDrag={kind,id,x:value.x,y:value.y,startX:e.clientX,startY:e.clientY,baseX:value.x,baseY:value.y,scale,expectedRevision:current.state.revision,expectedSubjectRev:kind==='move'?value.rev:undefined};
  target.setPointerCapture(e.pointerId);element.classList.add('dragging');
  const move=ev=>{if(!activeDrag)return;activeDrag.x=Math.round(activeDrag.baseX+(ev.clientX-activeDrag.startX)/activeDrag.scale);activeDrag.y=Math.round(activeDrag.baseY+(ev.clientY-activeDrag.startY)/activeDrag.scale);element.style.left=activeDrag.x+'px';element.style.top=activeDrag.y+'px';$('#last-receipt').textContent=`Preview only: ${kind} ${id} to (${activeDrag.x}, ${activeDrag.y}) · release to request`;};
  const cleanup=ev=>{target.removeEventListener('pointermove',move);target.removeEventListener('pointerup',end);target.removeEventListener('pointercancel',cancel);if(target.hasPointerCapture(ev.pointerId))target.releasePointerCapture(ev.pointerId);element.classList.remove('dragging');};
  const end=ev=>{const a=activeDrag;cleanup(ev);activeDrag=null;if(a.x!==a.baseX||a.y!==a.baseY)dispatchAction({type:a.kind,id:a.id,x:a.x,y:a.y,expectedRevision:a.expectedRevision,...(a.expectedSubjectRev===undefined?{}:{expectedSubjectRev:a.expectedSubjectRev})});else render();document.querySelector(kind==='move'?`[data-move-note="${id}"]`:`[data-move-window="${id}"]`)?.focus();};
  const cancel=ev=>{cleanup(ev);activeDrag=null;render();$('#last-receipt').textContent='Gesture cancelled. Accepted positions retained.';};
  target.addEventListener('pointermove',move);target.addEventListener('pointerup',end);target.addEventListener('pointercancel',cancel);
}
function keyMove(e){
  const target=e.target.closest('[data-move-note],[data-move-window]');if(!target||!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key))return;e.preventDefault();
  const kind=target.hasAttribute('data-move-note')?'move':'window',id=target.dataset.moveNote||target.dataset.moveWindow,value=kind==='move'?noteById(id):current.state.windows.find(w=>w.id===id),step=e.shiftKey?1:10;
  dispatchAction({type:kind,id,x:value.x+({'ArrowLeft':-step,'ArrowRight':step}[e.key]||0),y:value.y+({'ArrowUp':-step,'ArrowDown':step}[e.key]||0),expectedRevision:current.state.revision,...(kind==='move'?{expectedSubjectRev:value.rev}:{})});
  document.querySelector(kind==='move'?`[data-move-note="${id}"]`:`[data-move-window="${id}"]`)?.focus();
}
function openRules(){installedDraft=pretty(current.program);$('#program-source').value=installedDraft;$('#rule-status').textContent='A draft does not change your working desk.';$('#rule-list').innerHTML=current.program.rules.map(r=>`<section class="rule-item"><h3>${esc(r.id)}</h3><p>when ${esc(r.on||'any event')} · ${r.steps.length} top-level steps</p></section>`).join('');$('#rules-dialog').showModal();}
function programCandidate(){try{return JSON.parse($('#program-source').value);}catch(e){$('#rule-status').textContent='Not installed: '+e.message;return null;}}
function checkProgram(){const p=programCandidate();if(!p)return;const check=dispatch(current,{type:'program',program:p},{actor});$('#rule-status').textContent=check.ok?'Valid on this state. Check did not install or run it.':check.errors.join(' ');}
function installProgram(){const p=programCandidate();if(!p)return;if(dispatchAction({type:'program',program:p,expectedRevision:current.state.revision})){$('#rule-status').textContent='Installed. Arrange and future actions use this program. Save desk to retain it.';installedDraft=pretty(p);}else $('#rule-status').textContent='Not installed. The working program and editor draft were retained.';}
function validateLoaded(d){try{project(d,'notes');const result=dispatch(d,{type:'program',program:d.program},{actor:'validation-only'});return result.ok?[]:result.errors;}catch(e){return[e.message];}}
async function loadDesk(initial=false){
  if(loading)return;
  if(!initial&&current.state.editor.dirty){notify('Your editor draft is retained. Save the note or explicitly reopen its saved text before loading a checkpoint.');return;}
  loading=true;const startingDocument=current;try{const response=await fetch('/api/round4',{cache:'no-store'});if(!response.ok)throw new Error('Checkpoint bridge unavailable');const data=await response.json();
    if(current!==startingDocument){notify('The desk changed while the checkpoint was loading. Your newer work was retained; load again when ready.');return;}
    if(data.document){const errors=validateLoaded(data.document);if(errors.length)throw new Error(errors.join(' '));current=clone(data.document);checkpoint=data.revision;checkpointSubject=data.subject;clearNotice();render();$('#connection').textContent='Checkpoint r'+checkpoint;$('#last-receipt').textContent='Loaded one desk checkpoint. Notes, Editor and Activity read the same document.';}
    else{$('#connection').textContent='New local desk';if(!initial)notify('No stored checkpoint yet. Your local desk was retained.',false);}
  }catch(e){$('#connection').textContent='Local mode';if(!initial)notify(e.message+' Current work was retained.');}finally{loading=false;}
}
async function saveDesk(){
  if(loading)return;loading=true;const savedDocument=current;$('#save-desk').disabled=true;
  try{const response=await fetch('/api/round4',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({baseRevision:checkpoint,document:savedDocument})});const data=await response.json();if(!response.ok)throw new Error(response.status===409?'A newer checkpoint exists. This local desk and its draft were retained.':data.error||'Checkpoint save failed');checkpoint=data.revision;checkpointSubject=data.subject;clearNotice();const unchanged=current===savedDocument;$('#connection').textContent=unchanged?'Checkpoint r'+checkpoint:'Newer local work · checkpoint r'+checkpoint;$('#last-receipt').textContent=unchanged?`Saved the whole desk checkpoint ${data.appearance||data.subject} r${checkpoint}, including its explicitly marked editor draft.`:`Saved the requested snapshot at r${checkpoint}. Edits made during the save remain local and need another Save desk.`;}catch(e){notify(e.message);}finally{loading=false;$('#save-desk').disabled=false;}
}
function bind(){
  $('#notes-plane').addEventListener('click',e=>{const b=e.target.closest('[data-select]');if(b)selectNote(b.dataset.select);});
  $('#plane').addEventListener('pointerdown',beginDrag);$('#plane').addEventListener('keydown',keyMove);
  $('#editor-draft').addEventListener('input',e=>dispatchAction({type:'draft',id:current.state.editor.noteId,text:e.target.value},{quiet:true}));
  $('#save-note').onclick=()=>dispatchAction({type:'save',id:current.state.editor.noteId,expectedRevision:current.state.revision});
  $('#reopen-note').onclick=()=>dispatchAction({type:'reload-editor',id:current.state.editor.noteId,discardDraft:true,expectedRevision:current.state.revision});
  document.querySelectorAll('[data-front]').forEach(b=>b.onclick=()=>{const el=$(`[data-window="${b.dataset.front}"]`);document.querySelectorAll('.app-window').forEach(w=>w.style.zIndex='');el.style.zIndex='6';const camera=$('#desktop');camera.scrollTo({left:Math.max(0,parseFloat(el.style.left)*scale-20),top:Math.max(0,parseFloat(el.style.top)*scale-20),behavior:'smooth'});el.querySelector('.window-grip').focus({preventScroll:true});});
  $('#priority').onchange=e=>{const id=current.state.editor.noteId,n=noteById(id);if(n)dispatchAction({type:'tag',id,tags:e.target.checked?['priority']:[],expectedSubjectRev:n.rev});};
  $('#remove-note').onclick=()=>{const id=current.state.editor.noteId,n=noteById(id);if(n)dispatchAction({type:'remove',id,expectedSubjectRev:n.rev});};
  $('#arrange').onclick=()=>dispatchAction({type:'arrange',expectedRevision:current.state.revision});$('#mark-seen').onclick=()=>dispatchAction({type:'mark-seen'});
  $('#new-note').onclick=()=>{$('#new-note-form').hidden=false;$('#new-title').focus();};$('#cancel-new').onclick=()=>$('#new-note-form').hidden=true;
  $('#create-note').onclick=()=>{const title=$('#new-title').value.trim();if(!title){notify('Give the new note a title.');return;}if(dispatchAction({type:'create',title,text:$('#new-text').value,expectedRevision:current.state.revision})){$('#new-note-form').hidden=true;$('#new-title').value='';$('#new-text').value='';}};
  document.querySelectorAll('[data-text]').forEach(b=>b.onclick=()=>{const id=b.dataset.text;if(shownText.has(id))shownText.delete(id);else shownText.add(id);b.setAttribute('aria-pressed',String(shownText.has(id)));render();});
  $('#all-text').onclick=()=>{renderAllText();$('#text-dialog').showModal();};$('#rules-open').onclick=openRules;$('#check-program').onclick=checkProgram;$('#install-program').onclick=installProgram;
  $('#rules-code-tab').onclick=()=>{$('#rule-code').hidden=false;$('#rule-guide').hidden=true;$('#rules-code-tab').classList.add('active');$('#rules-guide-tab').classList.remove('active');};
  $('#rules-guide-tab').onclick=()=>{$('#rule-code').hidden=true;$('#rule-guide').hidden=false;$('#rules-guide-tab').classList.add('active');$('#rules-code-tab').classList.remove('active');};
  $('#fit').onclick=()=>{fitMode=true;applyCamera();$('#desktop').scrollTo(0,0);};$('#full-size').onclick=()=>{fitMode=false;scale=1;applyCamera();};addEventListener('resize',applyCamera);
  $('#save-desk').onclick=saveDesk;$('#load-desk').onclick=()=>loadDesk();
}
async function boot(){const program=await(await fetch('program.json')).json();current={state:initialState(),program};bind();render();await loadDesk(true);Object.defineProperty(window,'commonplace',{value:Object.freeze({inspect:()=>clone({document:current,checkpoint,checkpointSubject,lastReceipt,scale,fitMode})})});}
boot().catch(e=>notify('The desk could not start: '+e.message));
