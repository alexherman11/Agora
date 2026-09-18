import {preview, apply} from '../../foundations/program.mjs';

const $ = (s) => document.querySelector(s);
const clone = (x) => structuredClone(x);
const pretty = (x) => JSON.stringify(x, null, 2);
const escapeHTML = (s) => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let accepted, draft, runtime, rendered, original, tab = 'write', sourceText = '', pendingErrors = new Map();
let edition = 1, ticks = 0, previewing = false, history = [], deskRevision = null, deskSubject = null;
let bridgeAvailable = true, busy = false, selectedObject = "field-notes", dragSession = null, viewZoom = 1, fitMode = true;

function validateDocument(doc) {
  const errors = [];
  if (!doc || typeof doc !== 'object' || !doc.state || !doc.program) return ['A document needs state and program.'];
  const {content:c, appearance:a, controls:k} = doc.state;
  if (!c || !a || !k) return ['State needs content, appearance and controls.'];
  for (const key of ['title','subtitle','body','kicker']) if (typeof c[key] !== 'string' || c[key].length > 6000) errors.push(`content.${key} must be text of at most 6,000 characters.`);
  for (const key of ['accent','paper','ink']) if (!/^#[0-9a-fA-F]{6}$/.test(a[key])) errors.push(`appearance.${key} must be a six-digit hex color.`);
  for (const [key,min,max] of [['headingSize',35,120],['bloom',0,1],['rotation',-360,360]]) if (!Number.isFinite(a[key]) || a[key]<min || a[key]>max) errors.push(`appearance.${key} must be a number from ${min} to ${max}.`);
  if (!['split','cover'].includes(a.layout)) errors.push('appearance.layout must be split or cover.');
  if (typeof a.caption !== 'string' || a.caption.length > 500) errors.push('appearance.caption must be text of at most 500 characters.');
  if (!Number.isFinite(k.light) || k.light < 0 || k.light > 1) errors.push('controls.light must be between 0 and 1.');
  if (!Array.isArray(doc.program.rules)) errors.push('program.rules must be a list.');
  else if(doc.program.rules.some(r=>!r || (r.on!==undefined && !['change','run'].includes(r.on))))errors.push('This workbench delivers change and run events only; omit on to match both.');
  if (!Array.isArray(doc.state.items) || doc.state.items.length>24) errors.push('World needs at most 24 objects.');
  else { const ids=new Set(); for (const item of doc.state.items) {
    if (!item || typeof item.id!=='string' || !/^[a-z0-9-]+$/.test(item.id) || ids.has(item.id)) {errors.push('World objects need unique simple identifiers.');continue;} ids.add(item.id);
    if (!['publication','note','token'].includes(item.kind)) errors.push('Supported world object kinds: publication, note, token.');
    for (const k of ['label','body','role']) if(typeof item[k]!=='string' || item[k].length>1000)errors.push('World object '+k+' must be bounded text.');
    if (!Number.isFinite(item.x)||item.x<0||item.x>900||!Number.isFinite(item.y)||item.y<0||item.y>720||!Number.isFinite(item.rotation)||Math.abs(item.rotation)>45)errors.push('Object position/rotation is outside this bounded clearing.');
    if(!item.style || !/^#[0-9a-fA-F]{6}$/.test(item.style.fill))errors.push('Object fill must be a six-digit color.');
  } if (doc.state.items.filter(i=>i.kind==='publication').length!==1)errors.push('This specimen needs exactly one publication object.'); }
  return errors;
}
function execute(doc, event = 'change') {
  const validation = validateDocument(doc);
  if (validation.length) return {ok:false,errors:validation};
  try {
    const proposal = preview(doc.program, doc.state, {event});
    if (!proposal.ok) return proposal;
    const result = apply(doc.state, proposal);
    if (!result.ok) return result;
    const errors = validateDocument({...doc,state:result.state});
    if (errors.length) return {ok:false,errors:errors.map(x=>'Rule result: '+x)};
    return {...result,changes:proposal.changes,stats:proposal.stats};
  } catch (e) { return {ok:false,errors:[e.message]}; }
}
function fail(errors) {
  if(runtime){showPreview(false);render(runtime);}
  $('#error-banner').hidden = false;
  $('#error-banner').textContent = `Kept the last working result. ${errors.join(' ')}`;
  $('#draft-status').textContent = 'Draft needs attention. Nothing was applied.';
  $('#draft-status').classList.add('save-error');
}
function clearError() { $('#error-banner').hidden = true; $('#draft-status').classList.remove('save-error'); }
function isDirty() { return pendingErrors.size > 0 || sourceText !== pretty(accepted); }
function draftChanged() {
  if (tab !== 'source') sourceText = pretty(draft);
  $('#draft-status').classList.remove('save-error');
  $('#draft-status').textContent = isDirty() ? 'Unapplied draft · preview it, then make it yours.' : 'Your working edition is up to date.';
}
function getCandidate() {
  if (pendingErrors.size) { fail([...pendingErrors.values()]); return null; }
  try {
    const doc = JSON.parse(sourceText);
    const errors = validateDocument(doc);
    if (errors.length) { fail(errors); return null; }
    return doc;
  } catch(e) { fail(['Source is not valid JSON: '+e.message]); return null; }
}
function receipt(message, details) {
  $('#receipt').textContent = message;
  $('#receipt-detail').textContent = typeof details === 'string' ? details : pretty(details);
  $('#revision-label').textContent = `edition ${edition} · runtime ${ticks}`;
}
function syncDraft() {
  draft = clone(accepted); sourceText = pretty(draft); pendingErrors.clear();
  renderEditor(); draftChanged();
}
function showPreview(on) {
  previewing = on;
  $('#preview-badge').hidden = !on;
  $('#mode-label').textContent = on ? 'Uncommitted preview' : 'Working edition';
  $('#light').disabled = on; $('#world-light').disabled=on;
}

function artwork(state) {
  const {accent,bloom,rotation,ink} = state.appearance;
  const leaves = [[180,350,-53,1],[198,305,54,.96],[175,263,-58,.83],[198,219,54,.79],[188,175,-44,.68],[211,133,52,.55],[210,91,-37,.42]];
  const leafMarkup = leaves.map(([x,y,angle,scale],i)=>`<g transform="translate(${x} ${y}) rotate(${angle+(bloom-.5)*15}) scale(${scale*(.65+bloom*.45)})"><path d="M0 0 C-34 -32 -29 -79 0 -113 C34 -77 36 -32 0 0Z" fill="${i%2?'url(#leaf2)':'url(#leaf1)'}"/><path d="M0 0 Q3 -53 0 -103" fill="none" stroke="#dedfc0" stroke-opacity=".45" stroke-width="1.1"/><path d="M0 -36 L-15 -57 M1 -58 L15 -77" fill="none" stroke="#eff0ce" stroke-opacity=".24" stroke-width=".8"/></g>`).join('');
  return `<svg viewBox="0 0 380 435" role="img" aria-label="Botanical light study with seven leaves. Leaf openness ${Math.round(bloom*100)} percent; light angle ${Math.round(rotation)} degrees."><defs><linearGradient id="leaf1" x1="0" y1="1" x2="1" y2="0"><stop stop-color="#315443"/><stop offset="1" stop-color="#8ba276"/></linearGradient><linearGradient id="leaf2" x1="0" y1="1" x2="1" y2="0"><stop stop-color="#536f4f"/><stop offset="1" stop-color="#b0b88a"/></linearGradient><radialGradient id="sun"><stop stop-color="#e6b77c"/><stop offset="1" stop-color="#dba467"/></radialGradient><filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".42" numOctaves="3" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/><feComponentTransfer><feFuncA type="linear" slope=".12"/></feComponentTransfer><feBlend in="SourceGraphic" mode="multiply"/></filter></defs><rect x="22" y="27" width="338" height="372" rx="170" fill="#e3dfc9"/><path d="M23 306 Q155 269 360 307 L360 400 L23 400Z" fill="#d4d2b9"/><g transform="rotate(${rotation} 198 159)"><circle cx="262" cy="119" r="68" fill="url(#sun)"/><circle cx="272" cy="110" r="76" fill="none" stroke="${accent}" stroke-opacity=".45" stroke-width=".7"/></g><path d="M173 424 C213 342 173 312 186 239 C194 182 204 123 220 55" fill="none" stroke="#536546" stroke-width="3"/>${leafMarkup}<ellipse cx="184" cy="416" rx="70" ry="7" fill="#64744b" opacity=".12"/><g fill="${accent}"><circle cx="47" cy="344" r="5"/><circle cx="325" cy="242" r="3"/><path d="M331 323 v22 M320 334 h22" stroke="${accent}" stroke-width="1" fill="none"/></g><path d="M28 92 h39 M48 72 v40" stroke="${ink}" opacity=".3" stroke-width=".6"/><text x="26" y="58" fill="${ink}" opacity=".6" font-family="monospace" font-size="7" letter-spacing="2">HERBARIUM / 04</text><text x="321" y="375" fill="${ink}" opacity=".5" font-family="monospace" font-size="8" transform="rotate(-90 321 375)">LIGHT / FORM / TIME</text><circle cx="69" cy="192" r="24" fill="none" stroke="${accent}" opacity=".4" stroke-width=".6" stroke-dasharray="2 4"/></svg>`;
}
function render(state) {
  rendered = clone(state);
  const p = $('#publication'), a = state.appearance;
  p.style.setProperty('--paper',a.paper); p.style.setProperty('--ink',a.ink); p.style.setProperty('--accent',a.accent); p.style.setProperty('--heading-size',a.headingSize+'px');
  p.classList.toggle('cover',a.layout==='cover');
  $('#pub-title').textContent = state.content.title;
  $('#pub-subtitle').textContent = state.content.subtitle;
  $('#pub-body').textContent = state.content.body;
  $('#pub-kicker').textContent = state.content.kicker;
  $('#pub-caption').textContent = a.caption;
  $('#artwork').innerHTML = artwork(state);
  $('#light').value = Math.round(state.controls.light*100);
  $('#light-value').textContent = Math.round(state.controls.light*100)+'%';
  $('#world-light').value=Math.round(state.controls.light*100);
  renderWorld(state);
}

function field(label, id, value, options={}) {
  let control;
  if (options.type==='textarea') control=`<textarea id="${id}" rows="${options.rows||3}">${escapeHTML(value)}</textarea>`;
  else if (options.type==='select') control=`<select id="${id}">${options.choices.map(([v,l])=>`<option value="${v}" ${v===value?'selected':''}>${l}</option>`).join('')}</select>`;
  else control=`<input id="${id}" type="${options.type||'text'}" value="${escapeHTML(value)}" ${options.attrs||''}>`;
  return `<div class="field"><label for="${id}">${label}</label>${control}${options.hint?`<small>${options.hint}</small>`:''}</div>`;
}
function onField(id, callback) { $('#'+id).addEventListener('input',e=>{callback(e.target.value);draftChanged();}); }
function renderEditor() {
  const box = $('#editor'); box.replaceChildren();
  if (tab==='write') {
    box.innerHTML=field('Small print','kicker',draft.state.content.kicker)+field('The headline','title',draft.state.content.title,{type:'textarea',rows:3,hint:'A line break is part of the composition.'})+field('A little context','subtitle',draft.state.content.subtitle,{type:'textarea',rows:2})+field('The observation','body',draft.state.content.body,{type:'textarea',rows:5});
    for (const k of ['kicker','title','subtitle','body']) onField(k,v=>draft.state.content[k]=v);
  } else if (tab==='style') {
    box.innerHTML=`<div class="field"><label for="accent">The accent</label><div class="color-field"><input id="accent" type="color" value="${draft.state.appearance.accent}"><span id="accent-code">${draft.state.appearance.accent}</span></div></div>`+field('The paper','paper',draft.state.appearance.paper,{type:'select',choices:[['#f4efe4','Warm linen'],['#e5e9de','Garden mist'],['#f1e5df','Soft clay'],['#f7f5f0','Chalk white']]})+field('The composition','layout',draft.state.appearance.layout,{type:'select',choices:[['split','Facing page'],['cover','Open cover']]})+field('Headline size <span id="size-value">'+draft.state.appearance.headingSize+' px</span>','headingSize',draft.state.appearance.headingSize,{type:'range',attrs:'min="35" max="120"',hint:'The page adapts to its viewport. This sets its maximum type size.'})+`<p class="editor-hint">Scope: this publication definition. These changes do not alter the studio controls.</p><p class="editor-hint">The leaf form and its caption are controlled by the authored light rule. Open Rules to change that relationship.</p>`;
    onField('accent',v=>{draft.state.appearance.accent=v;$('#accent-code').textContent=v;});
    for(const k of ['paper','layout']) onField(k,v=>draft.state.appearance[k]=v);
    onField('headingSize',v=>{draft.state.appearance.headingSize=Number(v);$('#size-value').textContent=v+' px';});
  } else if(tab==='rules') {
    box.innerHTML='<p class="rule-explainer">When the light moves, these instructions shape the page. Edit an expression, apply it, then try the control.</p><p class="editor-hint">Finite operations, no JavaScript. <span class="capsule">get</span> <span class="capsule">add</span> <span class="capsule">mul</span> <span class="capsule">if</span> and bounded steps.</p>';
    draft.program.rules.forEach((rule,ri)=>{
      const group=document.createElement('section');group.className='rule-group';
      group.innerHTML=`<div class="field" style="margin-top:22px"><label for="event-${ri}">${escapeHTML(rule.id)} · event</label><select id="event-${ri}"><option value="all" ${rule.on===undefined?'selected':''}>Every supported event</option><option value="change" ${rule.on==='change'?'selected':''}>When light changes</option><option value="run" ${rule.on==='run'?'selected':''}>When Run once is pressed</option></select></div>`;
      box.append(group);onField('event-'+ri,v=>{if(v==='all')delete rule.on;else rule.on=v;});
      const condition=document.createElement('div');condition.className='field';condition.innerHTML=`<label for="when-${ri}">Only when · expression, or leave empty</label><textarea id="when-${ri}" rows="2" spellcheck="false">${rule.when===undefined?'':escapeHTML(pretty(rule.when))}</textarea>`;group.append(condition);
      $('#when-'+ri).addEventListener('input',e=>{const key='when/'+ri;try{if(e.target.value.trim())rule.when=JSON.parse(e.target.value);else delete rule.when;pendingErrors.delete(key);e.target.classList.remove('parse-error');}catch{pendingErrors.set(key,'Rule condition is not valid JSON.');e.target.classList.add('parse-error');}draftChanged();});
      rule.steps.forEach((step,si)=>{
        const card=document.createElement('div');card.className='rule-card';
        if(step.op==='set' && !step.target) {
          card.innerHTML=`<div class="rule-top"><span><span class="rule-index">${si+1}</span> SET A PROPERTY</span><button class="rule-remove" aria-label="Remove step ${si+1} from ${escapeHTML(rule.id)}">Remove</button></div><label for="target-${ri}-${si}">Target in this publication</label><input id="target-${ri}-${si}" value="${escapeHTML(step.path)}"><div class="rule-arrow" aria-hidden="true">↑</div><label for="expression-${ri}-${si}">Expression · JSON</label><textarea id="expression-${ri}-${si}" spellcheck="false">${escapeHTML(pretty(step.value))}</textarea>`;
          group.append(card);onField(`target-${ri}-${si}`,v=>step.path=v);
          const exp=$(`#expression-${ri}-${si}`), key=`${ri}/${si}`;
          exp.addEventListener('input',()=>{try{step.value=JSON.parse(exp.value);pendingErrors.delete(key);exp.classList.remove('parse-error');}catch(e){pendingErrors.set(key,`Expression in step ${si+1} is not valid JSON.`);exp.classList.add('parse-error');}draftChanged();});
          card.querySelector('.rule-remove').addEventListener('click',()=>{rule.steps.splice(si,1);pendingErrors.clear();renderEditor();draftChanged();});
        } else {
          card.innerHTML=`<div class="rule-top">${escapeHTML(step.op)} · structured step</div><textarea aria-label="Structured step ${si+1}" spellcheck="false">${escapeHTML(pretty(step))}</textarea>`;group.append(card);
          card.querySelector('textarea').addEventListener('input',e=>{const key=`${ri}/${si}`;try{rule.steps[si]=JSON.parse(e.target.value);pendingErrors.delete(key);}catch{pendingErrors.set(key,'Structured step is not valid JSON.');}draftChanged();});
        }
      });
      const add=document.createElement('button');add.className='add-rule';add.textContent='+ Add a set step';group.append(add);
      add.addEventListener('click',()=>{rule.steps.push({op:'set',path:'content.subtitle',value:'A new way to notice.'});renderEditor();draftChanged();});
    });
    const extra=document.createElement('div');extra.innerHTML='<button id="add-rule" class="add-rule" style="margin-top:18px">+ Add an event rule</button><button id="run-once" class="outline" style="width:100%;margin-top:12px">Run once on working edition</button><p class="editor-hint">Try replacing the bloom expression with ["get", "controls.light"]. Apply, then move the light. The same rule is visible in Source.</p>';box.append(extra);
    $('#add-rule').onclick=()=>{draft.program.rules.push({id:'rule-'+(draft.program.rules.length+1),on:'run',steps:[{op:'set',path:'content.subtitle',value:'A new way to notice.'}]});renderEditor();draftChanged();};
    $('#run-once').onclick=()=>runEvent('run');
  } else if(tab==='world') {
    renderWorldEditor(box);
  } else {
    box.innerHTML='<p class="editor-hint" style="margin:0 0 12px">The complete authored document. Write and Style edit this same definition. Live light motion is local runtime state until you author a starting value here.</p><div class="source-state-label">AUTHORED STARTING VALUES · runtime lives on the canvas</div><textarea id="source" class="source-area" spellcheck="false" aria-label="Complete document source"></textarea><p class="editor-hint">JSON data and a bounded rule language. Unknown paths and operators are refused. Preview and Apply validate before changing the page.</p>';
    $('#source').value=sourceText;
    $('#source').addEventListener('input',e=>{sourceText=e.target.value;draftChanged();});
  }
}
function changeTab(next) {
  if(next===tab)return;
  if(pendingErrors.size){fail(['Fix the incomplete expression before switching views.']);return;}
  if(tab==='source') {
    const candidate=getCandidate();if(!candidate)return;draft=candidate;
  }
  tab=next;
  document.querySelectorAll('[data-tab]').forEach(b=>b.setAttribute('aria-selected',String(b.dataset.tab===tab)));
  renderEditor();
}
function runEvent(event='change',value) {
  if(previewing||dragSession)return;
  const candidate={...accepted,state:clone(runtime)};
  if(value!==undefined)candidate.state.controls.light=value;
  const result=execute(candidate,event);
  if(!result.ok){fail(result.errors);render(runtime);return;}
  clearError();runtime=result.state;ticks++;render(runtime);
  const targets=result.changes.map(c=>c.path);
  receipt(`${event==='change'?'Light moved to '+Math.round(runtime.controls.light*100)+'%.':'Run once accepted.'} ${targets.length} runtime ${targets.length===1?'property':'properties'} changed in this publication.`,{scope:'publication runtime only',event,changes:result.changes,stats:result.stats});
}
function applyDraft() {
  const candidate=getCandidate();if(!candidate)return;
  const result=execute(candidate);if(!result.ok){fail(result.errors);return;}
  history.push(clone(accepted));accepted=clone(candidate);runtime=result.state;edition++;showPreview(false);clearError();render(runtime);syncDraft();$('#undo').disabled=false;
  receipt(`Applied edition ${edition}. Content, appearance and rule definition belong to this publication. Save to desk to retain it.`,{scope:'publication definition',edition,ruleChanges:result.changes,definition:accepted});
  $('#save-state').textContent='Applied locally · not saved';
}
function previewDraft() {
  const candidate=getCandidate();if(!candidate)return;
  const result=execute(candidate);if(!result.ok){fail(result.errors);return;}
  clearError();showPreview(true);render(result.state);$('#draft-status').textContent='Preview only. Apply to accept this edition.';
}
function undoDesign() {
  if(!history.length)return;
  if(isDirty()){fail(['Your draft was retained. Apply or discard it before undoing the last applied design.']);return;}
  const prior=history[history.length-1], candidate=clone(prior);
  candidate.state.controls=clone(runtime.controls);
  const result=execute(candidate);if(!result.ok){fail(result.errors);return;}
  history.pop();accepted=clone(prior);runtime=result.state;edition++;showPreview(false);clearError();render(runtime);syncDraft();$('#undo').disabled=!history.length;
  receipt(`Undid the last local design apply. Current light position retained. Edition ${edition} is not yet saved.`,{scope:'publication definition',restored:accepted,retainedControls:runtime.controls});
  $('#save-state').textContent='Undo applied locally';
}
async function loadDesk(initial=false) {
  if(!initial && isDirty()){fail(['Draft retained. Apply or discard it before loading another desk revision.']);return;}
  try {
    const response=await fetch('/api/workbench',{cache:'no-store'});if(!response.ok)throw new Error('Desk bridge unavailable');
    const data=await response.json();bridgeAvailable=true;
    if(data.document){
      const result=execute(data.document);if(!result.ok)throw new Error('Saved document was not loaded: '+result.errors.join(' '));
      deskRevision=data.revision;deskSubject=data.subject;accepted=clone(data.document);runtime=result.state;history=[];edition++;$('#undo').disabled=true;showPreview(false);clearError();render(runtime);syncDraft();
      receipt(`Loaded desk subject ${data.subject||data.appearance} at revision ${data.revision}.`,{scope:'desk document',subject:data.subject,appearance:data.appearance,revision:data.revision});
      $('#save-state').textContent=`Desk r${deskRevision} · ${data.appearance||data.subject}`;
    }else{$('#save-state').textContent='New study · not saved';if(!initial)receipt('No saved desk study yet. Your local edition was retained.','Use Save to desk to create a study.');}
  }catch(e){bridgeAvailable=false;$('#save-state').textContent='Local mode';if(!initial)fail([e.message+'. Your current work was retained.']);}
}
async function saveDesk() {
  if(busy)return;
  if(isDirty()){fail(['Apply the draft before saving. Your applied edition and draft are both retained.']);return;}
  busy=true;$('#save').disabled=true;
  try{
    const response=await fetch('/api/workbench',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({baseRevision:deskRevision,document:accepted})});
    const data=await response.json();
    if(!response.ok){if(response.status===409)throw new Error('The desk changed since this edition was loaded. Your local work is retained. Copy Source before loading the newer revision.');throw new Error(data.error||data.message||'Desk save failed.');}
    deskRevision=data.revision;deskSubject=data.subject;bridgeAvailable=true;clearError();
    $('#save-state').textContent=`Saved r${deskRevision} · ${data.appearance||data.subject}`;
    receipt(`Saved the authored document to desk ${data.appearance||data.subject}, revision ${deskRevision}. Runtime light motion remains local.`,{scope:'desk publication definition',subject:data.subject,appearance:data.appearance,revision:data.revision,receipt:data.receipt});
  }catch(e){$('#save-state').textContent='Save not accepted';fail([e.message]);}finally{busy=false;$('#save').disabled=false;}
}


function applyViewZoom() {
  if(dragSession)return;
  const scene=$('.world-scene'),camera=$('.world-camera'),extents=$('.world-extents');
  if(!scene||!scene.style.width)return;
  const w=parseFloat(scene.style.width),h=parseFloat(scene.style.height);
  if(fitMode)viewZoom=Math.min(1,Math.max(.2,Math.min((camera.clientWidth-16)/w,(camera.clientHeight-16)/h)));
  scene.style.transform=`scale(${viewZoom})`;
  extents.style.width=w*viewZoom+'px';extents.style.height=h*viewZoom+'px';
  $('#view-zoom').textContent=Math.round(viewZoom*100)+'%';
}
function setViewZoom(value){if(dragSession)return;fitMode=false;viewZoom=Math.max(.2,Math.min(1.5,value));applyViewZoom();}
function renderWorld(state) {
  const pub=state.items.find(i=>i.kind==='publication'), p=$('#publication-object');
  p.dataset.object=pub.id;p.style.left=pub.x+'px';p.style.top=pub.y+'px';p.style.transform=`rotate(${pub.rotation}deg)`;
  p.querySelector('[data-move]').dataset.move=pub.id;
  $('#loose-objects').innerHTML=state.items.filter(i=>i.kind!=='publication').map(i=>`<section class="world-object ${i.kind==='note'?'thought-object':'token-object'}" data-object="${escapeHTML(i.id)}" style="left:${i.x}px;top:${i.y}px;transform:rotate(${i.rotation}deg)"><button class="move-handle" data-move="${escapeHTML(i.id)}" aria-label="Move ${escapeHTML(i.label)}; drag or use arrow keys"><span>⠿</span> ${i.kind==='note'?'A THOUGHT':'A FOUND THING'}</button>${i.kind==='note'?`<div class="thought-paper" style="background:${i.style.fill}"><span class="note-tag">${escapeHTML(i.id.toUpperCase())}</span><h3>${escapeHTML(i.label)}</h3><p>${escapeHTML(i.body)}</p></div>`:`<div class="token-disc" style="background:${i.style.fill}"><svg viewBox="0 0 100 90" aria-hidden="true"><path d="M50 83 Q15 55 28 15 Q66 20 50 83Z" fill="#f4d98b"/><path d="M50 83 Q89 64 81 28 Q51 33 50 83Z" fill="#cad294"/><path d="M50 86 L43 31 M51 78 L70 44" stroke="#814d34" stroke-width="1" fill="none"/></svg><h3>${escapeHTML(i.label)}</h3><p>${escapeHTML(i.body)}</p></div>`}</section>`).join('');
  $('#object-count').textContent=state.items.length+' things';
  $('.world-scene').style.width=Math.max(1050,...state.items.map(i=>i.x+(i.kind==='publication'?680:260)))+'px';
  $('.world-scene').style.height=Math.max(870,...state.items.map(i=>i.y+(i.kind==='publication'?760:300)))+'px';
  applyViewZoom();
}
function renderWorldEditor(box) {
  box.innerHTML='<p class="editor-hint" style="margin:0 0 15px">Every thing has a place in the source. Drag its handle, use arrow keys, or author it here. Shift + arrow moves one pixel.</p>';
  draft.state.items.forEach(item=>{const b=document.createElement('button');b.className='world-object-picker'+(item.id===selectedObject?' selected':'');b.textContent=item.label.replace(/\n/g,' ')+' · '+item.kind;b.onclick=()=>{selectedObject=item.id;renderEditor();};box.append(b);});
  const item=draft.state.items.find(i=>i.id===selectedObject)||draft.state.items[0];selectedObject=item.id;
  const fields=document.createElement('div');fields.style.marginTop='20px';fields.innerHTML=field('This thing','object-label',item.label,{type:'textarea',rows:2})+field('A little more','object-body',item.body,{type:'textarea',rows:2})+`<div class="two-col">${field('Across','object-x',item.x,{type:'number',attrs:'min="0" max="900"'})}${field('Down','object-y',item.y,{type:'number',attrs:'min="0" max="720"'})}</div>`+field('A little tilt','object-rotation',item.rotation,{type:'range',attrs:'min="-45" max="45" step="0.5"'})+`<p class="spatial-hint">Target: ${escapeHTML(item.id)}. The light rule recolors all objects with role signal, including thoughts you add later. Change that rule in Source or Rules.</p>`;box.append(fields);
  for(const k of ['label','body'])onField('object-'+k,v=>item[k]=v);
  for(const k of ['x','y','rotation'])onField('object-'+k,v=>item[k]=Number(v));
}
function commitSpatial(next, message) {
  const input=clone(next);input.state.controls=clone(runtime.controls);
  const result=execute(input);if(!result.ok){fail(result.errors);render(runtime);return false;}
  for(const item of next.state.items){const old=accepted.state.items.find(i=>i.id===item.id),effective=result.state.items.find(i=>i.id===item.id);if(old&&(old.x!==item.x||old.y!==item.y)&&(effective.x!==item.x||effective.y!==item.y)){fail(['This position is controlled by a rule. Edit the rule before moving its object directly.']);render(runtime);return false;}}
  history.push(clone(accepted));accepted=clone(next);runtime=result.state;edition++;clearError();render(runtime);syncDraft();$('#undo').disabled=false;
  receipt(message,{scope:'world object placement',items:accepted.state.items.map(({id,x,y,rotation})=>({id,x,y,rotation}))});$('#save-state').textContent='World changed locally';return true;
}
function addThought() {
  if(isDirty()||previewing){fail(['Apply or discard your draft before adding a world object.']);return;}
  const next=clone(accepted);let n=1;while(next.state.items.some(i=>i.id==='thought-'+n))n++;
  const id='thought-'+n;next.state.items.push({id,kind:'note',role:'signal',x:650+((n*33)%150),y:90+((n*71)%380),rotation:(n%5-2)*3,label:'An unfinished idea.',body:'Make something of me.',style:{fill:'#edc567'}});selectedObject=id;commitSpatial(next,'Created '+id+'. A new thought shares the light behavior and has its own position.');
}
function startMove(e) {
  const handle=e.target.closest('[data-move]');if(!handle||e.button!==0)return;
  if(isDirty()||previewing){fail(['Apply or discard the draft before moving objects. Your draft was retained.']);return;}
  const item=accepted.state.items.find(i=>i.id===handle.dataset.move);if(!item)return;e.preventDefault();handle.focus();selectedObject=item.id;
  const object=handle.closest('[data-object]');object.classList.add('is-moving');const start={clientX:e.clientX,clientY:e.clientY,x:item.x,y:item.y,zoom:viewZoom}, camera=$('.world-camera');
  dragSession={id:item.id,x:item.x,y:item.y};handle.setPointerCapture(e.pointerId);
  const move=event=>{dragSession.x=Math.round(Math.max(0,Math.min(900,start.x+(event.clientX-start.clientX)/start.zoom)));dragSession.y=Math.round(Math.max(0,Math.min(720,start.y+(event.clientY-start.clientY)/start.zoom)));object.style.left=dragSession.x+'px';object.style.top=dragSession.y+'px';};
  const end=event=>{handle.removeEventListener('pointermove',move);handle.removeEventListener('pointerup',end);handle.removeEventListener('pointercancel',cancel);if(handle.hasPointerCapture(event.pointerId))handle.releasePointerCapture(event.pointerId);const final=dragSession;dragSession=null;object.classList.remove('is-moving');if(final.x===item.x&&final.y===item.y)return;const next=clone(accepted),target=next.state.items.find(i=>i.id===item.id);target.x=final.x;target.y=final.y;commitSpatial(next,`Moved ${item.id} to (${final.x}, ${final.y}). One gesture, one placement edit.`);document.querySelector(`[data-move="${item.id}"]`)?.focus();};
  const cancel=()=>{handle.removeEventListener('pointermove',move);handle.removeEventListener('pointerup',end);handle.removeEventListener('pointercancel',cancel);dragSession=null;render(runtime);};
  handle.addEventListener('pointermove',move);handle.addEventListener('pointerup',end);handle.addEventListener('pointercancel',cancel);
}
function keyMove(e) {
  const handle=e.target.closest('[data-move]');if(!handle||!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key))return;e.preventDefault();
  if(isDirty()||previewing){fail(['Apply or discard the draft before moving objects.']);return;}
  const next=clone(accepted),item=next.state.items.find(i=>i.id===handle.dataset.move),amount=e.shiftKey?1:10;selectedObject=item.id;
  item.x=Math.max(0,Math.min(900,item.x+({'ArrowLeft':-amount,'ArrowRight':amount}[e.key]||0)));item.y=Math.max(0,Math.min(720,item.y+({'ArrowUp':-amount,'ArrowDown':amount}[e.key]||0)));commitSpatial(next,`Moved ${item.id} with the keyboard to (${item.x}, ${item.y}).`);document.querySelector(`[data-move="${item.id}"]`)?.focus();
}

async function boot() {
  original=await (await fetch('document.json')).json();
  accepted=clone(original);const result=execute(accepted);
  if(!result.ok)throw new Error(result.errors.join(' '));runtime=result.state;
  render(runtime);syncDraft();
  document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>changeTab(b.dataset.tab));
  $('#preview').onclick=previewDraft;$('#apply').onclick=applyDraft;$('#undo').onclick=undoDesign;
  $('#discard').onclick=()=>{clearError();showPreview(false);render(runtime);syncDraft();};
  $('#exit-preview').onclick=()=>{showPreview(false);render(runtime);draftChanged();};
  $('#light').addEventListener('input',e=>runEvent('change',Number(e.target.value)/100));
  $('#world-light').addEventListener('input',e=>runEvent('change',Number(e.target.value)/100));
  $('#load').onclick=()=>loadDesk();$('#save').onclick=saveDesk;
  $('#add-thought').onclick=addThought;
  $('#toggle-tools').onclick=()=>{const hidden=$('.workspace').classList.toggle('tools-hidden');$('#toggle-tools').textContent=hidden?'Show tools ↙':'Hide tools ↗';$('#toggle-tools').setAttribute('aria-expanded',String(!hidden));requestAnimationFrame(applyViewZoom);};
  $('#fit-world').onclick=()=>{fitMode=true;applyViewZoom();$('.world-camera').scrollTo(0,0);};
  $('#zoom-in').onclick=()=>setViewZoom(viewZoom+.1);$('#zoom-out').onclick=()=>setViewZoom(viewZoom-.1);$('#zoom-reset').onclick=()=>setViewZoom(1);
  $('.world-scene').addEventListener('pointerdown',startMove);
  $('.world-scene').addEventListener('keydown',keyMove);
  const size=()=>{$('#viewport').textContent=`${innerWidth} × ${innerHeight}`;applyViewZoom();};size();addEventListener('resize',size);
  $('#runtime-label').textContent='SPATIAL STUDY / BOUNDED ENGINE R3.4';
  await loadDesk(true);
  // Read-only inspection for tests and future textual adapters, never a write API.
  Object.defineProperty(window,'fieldwork',{value:Object.freeze({inspect:()=>clone({definition:accepted,runtime,rendered,draftText:sourceText,edition,ticks,previewing,deskRevision,deskSubject,bridgeAvailable})})});
}
boot().catch(e=>{fail([e.message]);$('#runtime-label').textContent='INITIALIZATION FAILED';});
