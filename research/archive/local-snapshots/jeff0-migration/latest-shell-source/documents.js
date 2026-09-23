/* Documents: native content, per-document save queues, stable editing nodes. */
(function(){
'use strict';
const entries=new Map(); let selected='',opened=false,loaded=false,uiRevision=0,uiQueue=Promise.resolve(),refreshing=false;
const workspace=document.querySelector('.workspace');
const nav=element('button','nav-button','');nav.id='nav-documents';nav.setAttribute('aria-label','Documents');nav.title='Documents';
nav.innerHTML='<span aria-hidden="true">▤</span><span class="nav-label">Documents</span>';
$('nav-packages').before(nav);
const panel=element('section','documents');panel.id='documents-workspace';panel.hidden=true;panel.setAttribute('aria-label','Documents workspace');
panel.innerHTML='<header class="docs-heading"><div><h1>Documents</h1><p class="subtitle">Markdown, saved in your space.</p></div><button class="button" id="docs-desk">Back to desk</button></header><div class="docs-toolbar"><label for="docs-list">Document</label><select id="docs-list"></select><button class="button" id="docs-new">New document</button></div><div id="docs-error" role="alert" hidden></div><div id="docs-content" hidden><div class="docs-toolbar"><label for="docs-title">Document title</label><input id="docs-title" maxlength="500"><button class="button" id="docs-rename">Rename</button></div><div class="docs-toolbar"><button class="button" id="docs-bold" title="Bold (Ctrl+B)">Bold</button><button class="button" id="docs-save" title="Save (Ctrl+S)">Save now</button><span id="docs-status" role="status" aria-live="polite">Saved</span></div><div class="docs-columns"><div class="docs-source"><label for="docs-editor">Markdown editor</label><textarea id="docs-editor" maxlength="100000" spellcheck="true" aria-describedby="docs-help"></textarea><p id="docs-help">Ctrl+B: bold selection · Ctrl+S: save</p></div><div class="docs-reading"><nav id="docs-outline" aria-label="Heading outline"></nav><h2 class="docs-preview-label">Preview</h2><article id="docs-preview" aria-label="Markdown preview"></article></div></div></div>';
workspace.append(panel);
const editor=$('docs-editor'), title=$('docs-title'), list=$('docs-list');
function current(){return entries.get(selected);}
function error(e){$('docs-error').hidden=!e;$('docs-error').textContent=e?errorText(e):'';}
function status(){const e=current();$('docs-status').textContent=e?(e.error?'Error — '+e.error:e.promise?'Saving…':e.dirty?'Saving soon…':'Saved'):'No document selected';}
function rememberSelection(){const e=current();if(e){e.selection=[editor.selectionStart,editor.selectionEnd];e.scroll=editor.scrollTop;}}
function renderPreview(){renderMarkdown($('docs-preview'),editor.value);const out=$('docs-outline');out.replaceChildren(element('strong','','Outline'));
const headings=[...$('docs-preview').querySelectorAll('h1,h2,h3,h4,h5,h6')];
if(!headings.length)out.append(element('p','','No headings yet. Use # Heading.'));
headings.forEach((h,i)=>{h.id='docs-heading-'+i;h.tabIndex=-1;const b=element('button','',h.textContent);b.type='button';b.dataset.heading=String(i);b.style.paddingLeft=(8+(Number(h.tagName[1])-1)*10)+'px';b.onclick=()=>{rememberSelection();h.scrollIntoView({block:'nearest'});h.focus({preventScroll:true});};out.append(b);});
}
function drawList(){const old=list.value;list.replaceChildren();for(const [id,e] of entries)list.append(new Option(e.title+(e.object.facets['studio.packet-origin']?' (imported copy)':'')+(e.dirty?' •':''),id));list.value=selected||old;}
function display(){const e=current();$('docs-content').hidden=!e;if(!e)return;editor.readOnly=reviewLocks.has(selected);title.readOnly=editor.readOnly;editor.value=e.text;title.value=e.title;editor.setSelectionRange(...e.selection);editor.scrollTop=e.scroll||0;list.value=selected;renderPreview();status();}
function show(value,persist=true){opened=value;workspace.classList.toggle('documents-open',value);panel.hidden=!value;nav.classList.toggle('active',value);$('nav-desk').classList.toggle('active',!value);document.querySelector('.breadcrumb strong').textContent=value?'Documents':'Your desk';if(value)showPanel(false);if(persist)saveUI();}
function saveUI(){if(!loaded)return;const value={selected,open:opened};uiQueue=uiQueue.catch(()=>{}).then(async()=>{const r=await call('world.transact',{changes:[{id:'shell.documents-ui',expected_revision:uiRevision,facets:{'studio.documents-ui':value}}]});uiRevision=r.items[0].revision;}).catch(e=>{error(new Error('Workspace selection not saved: '+errorText(e)));throw e;});uiQueue.catch(()=>{});}
function choose(id,persist=true){trace('navigate',{from:selected,to:id});rememberSelection();const old=current();if(old?.dirty)save(old).catch(()=>{});selected=id;display();if(persist)saveUI();}
function save(e){
clearTimeout(e.timer);
if(e.promise)return e.promise.then(()=>e.dirty?save(e):undefined);
if(!e.dirty)return Promise.resolve();
const text=e.text,name=e.title,base=e.object,citations=[...(e.citations||[])].filter(c=>text.includes(c.facets['studio.citation'].citation_markdown));
trace('save-start',{document:e.object.id});
e.error='';
e.promise=(async()=>{
const latest=await call('world.get',{id:base.id});const obj=latest.item||latest;
if(facetText(obj,'core.text')!==facetText(base,'core.text')||facetText(obj,'core.title')!==facetText(base,'core.title'))throw new Error('Native document changed elsewhere. Your edits remain here; copy them before reloading.');
const result=await call('world.transact',{changes:[{id:obj.id,expected_revision:obj.revision,facets:{'core.text':{...obj.facets['core.text'],text},'core.title':{...obj.facets['core.title'],text:name}}},...citations]});
e.citations=(e.citations||[]).filter(c=>!citations.includes(c)&&e.text.includes(c.facets['studio.citation'].citation_markdown));trace('save-committed',{document:obj.id});
e.object=result.items.find(o=>o.id===obj.id);e.dirty=e.text!==text||e.title!==name;
})().catch(err=>{e.error=errorText(err);throw err;}).finally(()=>{e.promise=null;status();drawList();});
status();return e.promise.then(()=>e.dirty?save(e):undefined);
}
function edited(){trace('edit',{document:selected});const e=current();if(!e)return;e.text=editor.value;e.title=title.value;e.dirty=true;e.error='';rememberSelection();clearTimeout(e.timer);e.timer=setTimeout(()=>save(e).catch(()=>{}),550);status();renderPreview();}
editor.addEventListener('input',edited);title.addEventListener('input',edited);
function bold(){if(reviewLocks.has(selected))return;const e=current();if(!e)return;const start=editor.selectionStart,end=editor.selectionEnd;const word=editor.value.slice(start,end)||'bold text';editor.setRangeText('**'+word+'**',start,end,'select');editor.focus({preventScroll:true});editor.setSelectionRange(start+2,start+2+word.length);edited();}
$('docs-bold').onmousedown=e=>e.preventDefault();$('docs-bold').onclick=bold;
panel.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&!e.isComposing){const k=e.key.toLowerCase();if(k==='s'){e.preventDefault();if(current())save(current()).catch(()=>{});}if(k==='b'&&e.target===editor){e.preventDefault();bold();}}});
$('docs-save').onclick=()=>{if(current())save(current()).catch(()=>{});};
$('docs-rename').onclick=()=>{if(current())save(current()).then(()=>title.focus()).catch(()=>{});};
list.onchange=()=>choose(list.value);
nav.onclick=()=>{show(true);if(!loaded)refreshDocs();};
$('docs-desk').onclick=()=>{if(current()?.dirty)save(current()).catch(()=>{});show(false);};
const deskClick=$('nav-desk').onclick;$('nav-desk').onclick=()=>{show(false);deskClick();};
const tabClick=$('show-desk').onclick;$('show-desk').onclick=()=>{show(false);tabClick();};
$('docs-new').onclick=async()=>{const button=$('docs-new');button.disabled=true;error('');try{
const id='doc-'+crypto.randomUUID();const r=await call('world.transact',{changes:[{id,expected_revision:0,facets:{'core.title':{text:'Untitled document'},'core.text':{text:'# Untitled document\n\n'},'studio.document':{format:'markdown'}}}]});
ingest(r.items[0]);drawList();choose(id);title.focus();title.select();
}catch(e){error(e);}finally{button.disabled=false;}};
function ingest(o){let e=entries.get(o.id);if(!e){entries.set(o.id,{object:o,text:facetText(o,'core.text'),title:facetText(o,'core.title','Untitled'),selection:[0,0],scroll:0,dirty:false,promise:null,error:''});return true;}
if(!e.dirty&&!e.promise&&o.revision>e.object.revision){e.object=o;e.text=facetText(o,'core.text');e.title=facetText(o,'core.title');return true;}return false;}
async function refreshDocs(){if(refreshing)return;refreshing=true;try{let after,all=[];do{const r=await call('world.query',{facets:['studio.document'],limit:200,...(after?{after}:{})});all.push(...r.items);after=r.complete?null:r.next_after;}while(after);
let changed=false;for(const o of all)if(ingest(o)&&o.id===selected)changed=true;
if(!loaded){const r=await call('world.query',{facets:['studio.documents-ui'],limit:200});const ui=r.items.find(o=>o.id==='shell.documents-ui');uiRevision=ui?.revision||0;const v=ui?.facets['studio.documents-ui'];selected=entries.has(v?.selected)?v.selected:all[0]?.id||'';opened=!!v?.open;loaded=true;display();show(opened,false);}else if(changed){rememberSelection();display();}
drawList();error('');
}catch(e){error(e);}finally{refreshing=false;}}
window.flushDocuments=async()=>{if(importPromise)await importPromise;await saveSourceDraft();await Promise.all([...entries.values()].map(save));await uiQueue;};
window.addEventListener('beforeunload',e=>{if(draftDirty||[...entries.values()].some(v=>v.dirty||v.promise)){e.preventDefault();e.returnValue='';}});

/* Sources extends the existing editor, not a second document writer. */
const research=element('section','research-sources');
research.id='docs-sources';
research.setAttribute('aria-label','Research sources');
research.innerHTML=`<details id="sources-area" open><summary>Sources</summary>
<p class="subtitle">Retain a source, read it, then append a cited excerpt to your document.</p>
<form id="sources-form" class="docs-toolbar"><label for="sources-url">Source URL</label><input id="sources-url" type="url" required maxlength="2048" placeholder="http://127.0.0.1:8860/sources/coast"><button class="button" id="sources-import" type="submit">Import</button></form>
<p id="sources-status" role="status" aria-live="polite">Ready to import.</p>
<div class="docs-toolbar"><label for="sources-list">Retained source</label><select id="sources-list"><option value="">No sources yet</option></select></div>
<div id="sources-detail" hidden><p id="sources-meta"></p><article id="sources-preview" aria-label="Source preview"></article>
<details><summary>Select exact source text</summary><label for="sources-text">Retained Markdown (read only)</label><textarea id="sources-text" readonly></textarea><button type="button" class="button" id="sources-use">Use selected text</button></details>
<label for="sources-excerpt">Excerpt (exact text from source)</label><textarea id="sources-excerpt" maxlength="20000"></textarea>
<button type="button" class="button" id="sources-quote">Insert quotation at document end</button><p id="sources-quote-status" role="status" aria-live="polite"></p></div>
<details><summary>Recent workspace events (diagnostics)</summary><pre id="research-events"></pre></details>
</details>`;
$('docs-content').after(research);
const sourceMap=new Map();let sourceSelected='',importPromise=null;

let draftRevision=0,draftLoaded=false,draftDirty=false,draftTimer=null,draftQueue=Promise.resolve(),draftLast='';
function draftValue(){return {url:$('sources-url').value,excerpt:$('sources-excerpt').value,source:sourceSelected};}
function retainDraft(){draftDirty=true;clearTimeout(draftTimer);draftTimer=setTimeout(()=>saveSourceDraft().catch(e=>sourceStatus('Source draft not saved: '+errorText(e),true)),250);}
function saveSourceDraft(){clearTimeout(draftTimer);if(!draftLoaded)return Promise.resolve();const value=draftValue(),serialized=JSON.stringify(value);
draftQueue=draftQueue.catch(()=>{}).then(async()=>{if(serialized===draftLast){draftDirty=JSON.stringify(draftValue())!==serialized;return;}
const r=await call('world.transact',{changes:[{id:'shell.sources-ui',expected_revision:draftRevision,facets:{'studio.sources-ui':value}}]});
draftRevision=r.items[0].revision;draftLast=serialized;draftDirty=JSON.stringify(draftValue())!==serialized;});return draftQueue;}
async function loadSourceDraft(){const r=await call('world.query',{facets:['studio.sources-ui'],limit:200});const o=r.items.find(o=>o.id==='shell.sources-ui');draftRevision=o?.revision||0;const v=o?.facets['studio.sources-ui'];
if(v&&!draftDirty){$('sources-url').value=v.url;$('sources-excerpt').value=v.excerpt;sourceSelected=v.source;draftLast=JSON.stringify(v);}draftLoaded=true;await refreshSources();}
$('sources-url').oninput=retainDraft;$('sources-excerpt').oninput=retainDraft;
const events=[];function trace(kind,extra={}){events.push({at:new Date().toISOString(),ms:Math.round(performance.now()*10)/10,event:kind,importPending:!!importPromise,...extra});if(events.length>50)events.shift();if($('research-events'))$('research-events').textContent=JSON.stringify(events,null,2);}
function sourceStatus(message,bad=false){$('sources-status').textContent=message;$('sources-status').classList.toggle('research-error',bad);}
function sourceDisplay(){const s=sourceMap.get(sourceSelected)?.facets['studio.source'];$('sources-detail').hidden=!s;if(!s)return;
$('sources-meta').textContent=s.title+' — '+s.author+' · '+s.published+' · revision '+s.source_revision+' · retrieved '+s.retrieved_at;
renderMarkdown($('sources-preview'),s.content);$('sources-text').value=s.content;$('sources-preview').dataset.sourceId=sourceSelected;}
async function refreshSources(prefer){let after,all=[];do{const r=await call('world.query',{facets:['studio.source'],limit:200,...(after?{after}:{})});all.push(...r.items);after=r.complete?null:r.next_after;}while(after);
const old=sourceMap.get(sourceSelected);for(const o of all)sourceMap.set(o.id,o);
if(prefer)sourceSelected=prefer;if(!sourceMap.has(sourceSelected))sourceSelected=all[0]?.id||'';
const sl=$('sources-list');const signature=all.map(o=>o.id+':'+o.revision).join('|');
if(sl.dataset.signature!==signature){sl.replaceChildren();for(const o of all)sl.append(new Option(o.facets['studio.source'].title+(o.facets['studio.packet-origin']?' (imported '+o.id.slice(12,20)+')':''),o.id));if(!all.length)sl.append(new Option('No sources yet',''));sl.dataset.signature=signature;}
sl.value=sourceSelected;if(prefer||!old||old.revision!==sourceMap.get(sourceSelected)?.revision)sourceDisplay();retainDraft();}
$('sources-list').onchange=()=>{sourceSelected=$('sources-list').value;sourceDisplay();retainDraft();$('sources-quote-status').textContent='';};
$('sources-form').onsubmit=e=>{e.preventDefault();if(importPromise)return;
const url=$('sources-url').value.trim();if(!url){sourceStatus('Enter a source URL first.',true);return;}
$('sources-import').disabled=true;sourceStatus('Importing from the guest… You can keep writing or switch documents.');
importPromise=(async()=>{trace('import-start',{url,importPending:true});try{await saveSourceDraft();const registry=await call('tools.list');const tool=registry.actions.find(t=>t.package==='studio.research'&&t.action==='import_source');if(!tool)throw new Error('Research importer is not installed.');
let r;for(let attempt=0;attempt<2;attempt++){try{r=await call('action.invoke',{package:tool.package,revision:tool.revision,action:tool.action,args:{url}});break;}catch(err){if(attempt===0&&/snapshot is stale/i.test(errorText(err))){sourceStatus('Your writing was saved during import. Retrying once with a fresh snapshot…');trace('import-retry');continue;}throw err;}}const v=r.result||r;if(!v.ok)throw new Error(v.error||'Import failed.');
await refreshSources(v.source_id);sourceStatus(v.reused?'Source refreshed — existing identity reused.':'Source imported and retained.');trace('import-success',{source:v.source_id});
}catch(err){sourceStatus(errorText(err)+' You can retry Import; your document and retained sources are unchanged by this failure.',true);trace('import-error',{error:errorText(err)});}finally{$('sources-import').disabled=false;importPromise=null;}})();
};
$('sources-use').onclick=()=>{const t=$('sources-text');$('sources-excerpt').value=t.value.slice(t.selectionStart,t.selectionEnd);retainDraft();$('sources-quote-status').textContent=$('sources-excerpt').value.trim()?'Excerpt ready.':'Select some source text first.';};
$('sources-quote').onclick=()=>{if(reviewLocks.has(selected))return;const e=current(),s=sourceMap.get(sourceSelected)?.facets['studio.source'],quote=$('sources-excerpt').value.trim(),feedback=$('sources-quote-status');
if(!e){feedback.textContent='Choose a document first.';return;}if(!quote){feedback.textContent='Choose a non-blank excerpt first.';return;}if(!s||!s.content.includes(quote)){feedback.textContent='Excerpt must be exact text from the retained source.';return;}
const esc=x=>x.replace(/[\\`*_[\]<>]/g,ch=>'\\'+ch);
const citation='> '+quote.split('\n').join('\n> ')+'\n\n— '+esc(s.author)+', ['+esc(s.title)+'](<'+s.final_url.replace(/>/g,'%3E')+'>), '+esc(s.published)+'; revision '+esc(s.source_revision)+'.';
const addition='\n\n'+citation+'\n';if(editor.value.length+addition.length>100000){feedback.textContent='This quotation would exceed the document size limit.';return;}
e.citations=e.citations||[];e.citations.push({id:'citation-'+crypto.randomUUID(),expected_revision:0,facets:{'studio.citation':{document_id:selected,source_id:sourceSelected,source_revision:s.source_revision,content_hash:s.content_hash,quoted_text:quote,citation_markdown:citation,created_at:new Date().toISOString()}}});
editor.value+=addition;edited();editor.setSelectionRange(editor.value.length,editor.value.length);rememberSelection();feedback.textContent='Quotation appended to '+e.title+'. Saving with the document…';trace('quote',{document:selected,source:sourceSelected});};

/* Explicit source review. Durable proposals; stable editor and input nodes. */
const review=element('section','research-review');review.id='docs-review';review.setAttribute('aria-label','Citation review');
review.innerHTML=`<h2 tabindex="-1" id="review-heading">Citation review</h2><button class="button" id="review-to-sources">Choose source / URL</button>
<p>1. Choose a retained source above and enter its refresh URL in Source URL. Refresh never changes documents or old citations.</p>
<button class="button" id="review-refresh">Refresh selected source</button>
<p id="review-status" role="status" aria-live="polite">Ready to review.</p>
<p id="review-current-meta"></p>
<label for="review-source-text">Current retained source (read only)</label><textarea id="review-source-text" readonly></textarea>
<button class="button" id="review-use">Use selected source text as replacement</button>
<p>2. Choose an outdated citation from any document. Select or paste an exact excerpt of the current source, then prepare a saved preview.</p>
<div class="docs-toolbar"><label for="review-citation">Outdated citation</label><select id="review-citation"></select></div>
<h3>Old quotation and attribution</h3><pre id="review-old"></pre>
<label for="review-excerpt">Proposed excerpt (exact source text)</label><textarea id="review-excerpt" maxlength="20000"></textarea>
<button class="button" id="review-prepare">Prepare replacement preview</button>
<p>3. Read the old and proposed quotations below. Check the proposals you approve, then apply the selected batch. A conflict stops the entire batch; dismiss and prepare again to renew review.</p>
<p id="review-batch-status"></p><div class="docs-toolbar"><button class="button" id="review-apply">Apply selected proposals</button><button class="button" id="review-dismiss">Dismiss selected proposals</button></div>
<div id="review-proposals"></div>`;
research.after(review);
const reviewJump=element('button','button','Review citations');reviewJump.id='docs-review-open';$('docs-new').after(reviewJump);
reviewJump.onclick=()=>{$('review-heading').scrollIntoView({block:'start'});$('review-heading').focus({preventScroll:true});};
$('review-to-sources').onclick=()=>{$('sources-list').scrollIntoView({block:'center'});$('sources-list').focus({preventScroll:true});};
const reviewLocks=new Set(),reviewCitations=new Map(),reviewProposals=new Map(),reviewChecks=new Set();
let reviewPromise=null,reviewRefreshing=false,reviewSignature='',reviewDraftLoaded=false,reviewDraftRevision=0,reviewDraftLast='',reviewDraftTimer=null,reviewDraftQueue=Promise.resolve(),reviewDraftDirty=false,reviewCitationDraft='';
function reviewStatus(s,bad=false){for(const id of ['review-status','review-batch-status']){$(id).textContent=s;$(id).classList.toggle('research-error',bad);}}
function reviewDraft(){return {citation:$('review-citation').value||reviewCitationDraft,excerpt:$('review-excerpt').value};}
function retainReviewDraft(){reviewDraftDirty=true;reviewCitationDraft=$('review-citation').value;clearTimeout(reviewDraftTimer);reviewDraftTimer=setTimeout(()=>saveReviewDraft().catch(e=>reviewStatus('Review draft not saved: '+errorText(e),true)),250);}
function saveReviewDraft(){clearTimeout(reviewDraftTimer);if(!reviewDraftLoaded)return Promise.resolve();const v=reviewDraft(),s=JSON.stringify(v);
reviewDraftQueue=reviewDraftQueue.catch(()=>{}).then(async()=>{if(s!==reviewDraftLast){const r=await call('world.transact',{changes:[{id:'shell.review-ui',expected_revision:reviewDraftRevision,facets:{'studio.review-ui':v}}]});reviewDraftRevision=r.items[0].revision;reviewDraftLast=s;}reviewDraftDirty=JSON.stringify(reviewDraft())!==s;});return reviewDraftQueue;}
async function loadReviewDraft(){const r=await call('world.query',{facets:['studio.review-ui'],limit:200});const o=r.items.find(x=>x.id==='shell.review-ui');reviewDraftRevision=o?.revision||0;const v=o?.facets['studio.review-ui'];if(v&&!reviewDraftDirty){reviewCitationDraft=v.citation;$('review-excerpt').value=v.excerpt;reviewDraftLast=JSON.stringify(v);}reviewDraftLoaded=true;await refreshReview();}
async function reviewInvoke(action,args){const r=await call('tools.list');const t=r.actions.find(x=>x.package==='studio.research'&&x.action===action);if(!t)throw new Error('Research review action is not installed: '+action);const response=await call('action.invoke',{package:t.package,revision:t.revision,action,args});const v=response.result||response;if(!v.ok)throw new Error(v.error||'Review failed; no changes applied.');return v;}
async function reviewQuery(facet){let after,all=[];do{const r=await call('world.query',{facets:[facet],limit:200,...(after?{after}:{})});all.push(...r.items);after=r.complete?null:r.next_after;}while(after);return all;}
function reviewOld(){const c=reviewCitations.get($('review-citation').value)?.facets['studio.citation'];$('review-old').textContent=c?c.citation_markdown+'\n\nOriginal source revision '+c.source_revision+' · SHA-256 '+c.content_hash:'No outdated citation for this source.';}
function drawReview(){
 const so=sourceMap.get(sourceSelected),s=so?.facets['studio.source'];
 const meta=s?s.title+' — '+s.author+' · '+s.published+' · current revision '+s.source_revision+' · '+s.final_url:'Select a retained source above.';
 $('review-current-meta').textContent=meta;if($('review-source-text').value!==(s?.content||''))$('review-source-text').value=s?.content||'';
 const signature=selected+'|'+$('review-scope')?.value+'|'+sourceSelected+':'+so?.revision+'|'+[...reviewCitations.values(),...reviewProposals.values()].map(o=>o.id+':'+o.revision).join('|')+'|'+[...reviewCitations.values()].map(o=>o.id+':'+citationActive(o.facets['studio.citation'])).join('|');
 if(signature===reviewSignature)return;reviewSignature=signature;
 const select=$('review-citation'),prior=select.value||reviewCitationDraft;select.replaceChildren();
 for(const o of reviewCitations.values()){const c=o.facets['studio.citation'];if(s&&reviewInScope(c.document_id)&&citationActive(c)&&c.source_id===sourceSelected&&(c.source_revision!==s.source_revision||c.content_hash!==s.content_hash))select.append(new Option((entries.get(c.document_id)?.title||c.document_id)+' · revision '+c.source_revision+' · '+o.id,o.id));}
 if(!select.options.length)select.append(new Option('No active outdated citations in this scope',''));
 if([...select.options].some(o=>o.value===prior))select.value=prior;
 reviewOld();
 const holder=$('review-proposals'),activeProposal=holder.contains(document.activeElement)?document.activeElement.dataset.proposalId:null;holder.replaceChildren();
 for(const id of [...reviewChecks]){const p=reviewProposals.get(id)?.facets['studio.citation-proposal'];if(!p||!proposalActive(p)||!reviewInScope(p.document_id))reviewChecks.delete(id);}
 const pending=[...reviewProposals.values()].filter(o=>{const p=o.facets['studio.citation-proposal'];return p.status==='prepared'&&proposalActive(p)&&reviewInScope(p.document_id);});
 if(!pending.length)holder.append(element('p','','No prepared proposals. Preparation never edits documents.'));
 const renderCard=o=>{const p=o.facets['studio.citation-proposal'];const card=element('article','review-card');card.dataset.proposalId=o.id;
 const label=element('label','review-check');const check=document.createElement('input');check.type='checkbox';check.dataset.proposalId=o.id;check.checked=reviewChecks.has(o.id);check.disabled=p.status!=='prepared'||!proposalActive(p);check.setAttribute('aria-label','Select proposal for '+(entries.get(p.document_id)?.title||p.document_id)+' '+o.id);check.onchange=()=>{if(check.checked)reviewChecks.add(o.id);else reviewChecks.delete(o.id);};label.append(check,document.createTextNode(' '+(entries.get(p.document_id)?.title||p.document_id)+' — '+p.status));card.append(label);
 card.append(element('p','review-id',o.id+' · document revision '+p.document_revision+' / citation revision '+p.citation_revision));
 if(p.status==='prepared'&&!proposalActive(p)){card.append(element('p','','Inactive: cited text was removed, edited or is ambiguous. This preview cannot be applied.'));const dismiss=element('button','button','Dismiss inactive preview');dismiss.onclick=()=>reviewBusy(async()=>{await reviewInvoke('dismiss',{proposal_ids:[o.id]});reviewStatus('Inactive preview dismissed; historical evidence kept.');});card.append(dismiss);}
 for(const [heading,c] of [['Old — revision '+p.old_citation.source_revision,p.old_citation],['Proposed — revision '+p.proposed_citation.source_revision,p.proposed_citation]]){card.append(element('h3','',heading),element('pre','',c.citation_markdown));}
 holder.append(card);};
 pending.forEach(renderCard);
 const resolved=[...reviewProposals.values()].filter(o=>{const p=o.facets['studio.citation-proposal'];return reviewInScope(p.document_id)&&(p.status!=='prepared'||!proposalActive(p));});
 if(resolved.length){const details=element('details','');details.append(element('summary','',resolved.length+' inactive / resolved previews (historical evidence)'));holder.append(details);for(const o of resolved){renderCard(o);details.append(holder.lastElementChild);}}
 if(activeProposal){const input=[...holder.querySelectorAll('input')].find(x=>x.dataset.proposalId===activeProposal&&!x.disabled);if(input)input.focus({preventScroll:true});}
}
async function refreshReview(){if(reviewRefreshing||!reviewDraftLoaded)return;reviewRefreshing=true;try{const cs=await reviewQuery('studio.citation'),ps=await reviewQuery('studio.citation-proposal');reviewCitations.clear();reviewProposals.clear();cs.forEach(o=>reviewCitations.set(o.id,o));ps.forEach(o=>reviewProposals.set(o.id,o));drawReview();}catch(e){reviewStatus(errorText(e),true);}finally{reviewRefreshing=false;}}
function reviewBusy(task){
 if(reviewPromise)return;
 for(const id of ['review-refresh','review-prepare','review-apply','review-dismiss'])$(id).disabled=true;
 reviewPromise=(async()=>{try{await task();}catch(e){reviewStatus(errorText(e),true);trace('review-error',{error:errorText(e)});}finally{reviewPromise=null;reviewLocks.clear();editor.readOnly=false;title.readOnly=false;for(const id of ['review-refresh','review-prepare','review-apply','review-dismiss'])$(id).disabled=false;await refreshReview();}})();
}
$('review-citation').onchange=()=>{reviewOld();retainReviewDraft();};
$('review-excerpt').oninput=retainReviewDraft;
$('review-use').onclick=()=>{const t=$('review-source-text');$('review-excerpt').value=t.value.slice(t.selectionStart,t.selectionEnd);retainReviewDraft();reviewStatus($('review-excerpt').value.trim()?'Exact excerpt selected. Prepare to preview.':'Select source text first.');};
$('review-refresh').onclick=()=>reviewBusy(async()=>{
 const sid=sourceSelected,url=$('sources-url').value.trim();if(!sid||!url)throw new Error('Select a retained source and enter a Source URL above.');
 await saveSourceDraft();reviewStatus('Refreshing selected source… You can keep editing or switch documents.');trace('refresh-start',{source:sid,url});
 const v=await reviewInvoke('refresh_source',{source_id:sid,url});await refreshSources();reviewStatus('Source retained at revision '+v.source_revision+'. Documents and citations were not changed.');trace('refresh-success',{source:sid});});
$('review-prepare').onclick=()=>reviewBusy(async()=>{
 const citation_id=$('review-citation').value,excerpt=$('review-excerpt').value;if(!citation_id)throw new Error('Choose an outdated citation.');
 const c=reviewCitations.get(citation_id)?.facets['studio.citation'],e=entries.get(c?.document_id);
 await saveReviewDraft();if(e)await save(e);const v=await reviewInvoke('prepare',{citation_id,excerpt});
 reviewStatus('Prepared preview saved. Read both quotations, check the proposal, then Apply to approve.');trace('review-prepared',{proposal:v.proposal_id});});
function selectedProposals(){return [...reviewChecks].filter(id=>reviewProposals.get(id)?.facets['studio.citation-proposal'].status==='prepared');}
$('review-apply').onclick=()=>reviewBusy(async()=>{
 const proposal_ids=selectedProposals();if(!proposal_ids.length)throw new Error('Check at least one prepared proposal first.');
 for(const id of proposal_ids)reviewLocks.add(reviewProposals.get(id).facets['studio.citation-proposal'].document_id);
 editor.readOnly=reviewLocks.has(selected);title.readOnly=editor.readOnly;
 await Promise.all([...reviewLocks].map(id=>entries.get(id)).filter(Boolean).map(save));
 reviewStatus('Checking revisions and applying the whole selected batch…');const v=await reviewInvoke('apply',{proposal_ids});
 proposal_ids.forEach(id=>reviewChecks.delete(id));await refreshDocs();reviewStatus('Applied '+v.applied.length+' proposal(s) atomically across '+v.documents.length+' document(s). Original evidence retained.');trace('review-applied',{proposals:proposal_ids});});
$('review-dismiss').onclick=()=>reviewBusy(async()=>{
 const proposal_ids=selectedProposals();if(!proposal_ids.length)throw new Error('Check a prepared proposal to dismiss.');
 await reviewInvoke('dismiss',{proposal_ids});proposal_ids.forEach(id=>reviewChecks.delete(id));reviewStatus('Selected proposals dismissed. No documents or citations changed.');});
const oldFlushDocuments=window.flushDocuments;window.flushDocuments=async()=>{if(reviewPromise)await reviewPromise;await saveReviewDraft();await oldFlushDocuments();};
window.addEventListener('beforeunload',e=>{if(reviewDraftDirty||reviewPromise){e.preventDefault();e.returnValue='';}});
loadReviewDraft().catch(e=>reviewStatus(errorText(e),true));setInterval(()=>{if(!reviewPromise)refreshReview();},2000);


loadSourceDraft().catch(e=>sourceStatus('Source drafts unavailable: '+errorText(e),true));
setInterval(()=>{if(draftLoaded&&!importPromise)refreshSources().catch(()=>{});},4000);

refreshDocs();setInterval(refreshDocs,4000);
/* Research packets: independent async workflow; never rebuild editor or chat. */
const packetPanel=element('section','research-packets');packetPanel.id='docs-packets';
packetPanel.innerHTML=`<details id="packets-area"><summary>Research packet · export / import</summary>
<p>Copy 1–8 documents with citations and old evidence into a new collection. No web fetches or pending proposals. Originals stay unchanged.</p>
<fieldset><legend>Select documents to export (maximum 8)</legend><div id="packets-documents"></div></fieldset>
<button class="button" id="packets-export">Export selected documents</button>
<div class="docs-toolbar"><label for="packets-retained">Retained packet</label><select id="packets-retained"><option value="">Choose a saved packet</option></select><button class="button" id="packets-load">Load JSON</button></div>
<label for="packets-json">Packet JSON — paste here or export above</label><textarea id="packets-json" maxlength="2097152" spellcheck="false" aria-describedby="packets-limits"></textarea>
<div class="docs-toolbar"><button class="button" id="packets-copy">Select JSON for copying</button><label for="packets-name">New collection name</label><input id="packets-name" maxlength="120" placeholder="Research handoff"></div>
<p id="packets-limits">v2 (v1 accepted) · 32 threads · 2 MiB UTF-8 · 8 documents · 16 sources · 64 citations · 64 history entries · 64 source versions (16/source). SHA-256 detects inconsistency, not author authenticity. Documents/source text ≤100,000 characters each.</p>
<div class="docs-toolbar"><button class="button" id="packets-preview">Validate / preview</button><button class="button" id="packets-new-attempt">New copy / attempt</button></div>
<p id="packets-attempt"></p><p id="packets-status" role="status" aria-live="polite">Export or paste a packet, then preview. Nothing is imported until Apply.</p>
<div id="packets-preview-detail" hidden><pre id="packets-summary"></pre><div class="docs-toolbar"><button class="button" id="packets-apply" disabled>Apply import</button><button class="button" id="packets-cancel" disabled>Cancel preview</button></div></div>
<div class="docs-toolbar"><label for="packets-collections">Imported collection</label><select id="packets-collections"><option value="">No imported collections</option></select></div><div id="packets-imported-documents"></div>
</details>`;
$('docs-content').before(packetPanel);
const packetJump=element('button','button','Research packet');packetJump.id='packets-open';$('docs-new').after(packetJump);
packetJump.onclick=()=>{$('packets-area').open=true;$('docs-packets').scrollIntoView({block:'start'});$('packets-export').focus({preventScroll:true});};
const evidencePanel=element('details','packet-evidence');evidencePanel.id='docs-citation-evidence';evidencePanel.innerHTML='<summary>Citations & retained history for this document</summary><div id="packets-evidence"></div>';$('docs-content').after(evidencePanel);
let packetChecks=new Set(),packetToken=crypto.randomUUID(),packetPreview=null,packetPromise=null,packetDraftRevision=0,packetDraftLoaded=false,packetDraftLast='',packetDraftQueue=Promise.resolve(),packetDraftTimer=null,packetDraftDirty=false,packetDocSignature='',packetEvidenceSignature='',packetCollectionMap=new Map();
function packetStatus(s,bad=false){$('packets-status').textContent=s;$('packets-status').classList.toggle('research-error',bad);}
function packetValue(){return {json:$('packets-json').value,name:$('packets-name').value,token:packetToken,attempt:packetPreview?.attempt_id||'',selected:[...packetChecks],open:$('packets-area').open};}
function packetRetain(){packetDraftDirty=true;clearTimeout(packetDraftTimer);packetDraftTimer=setTimeout(()=>savePacketDraft().catch(e=>packetStatus('Packet draft not saved: '+errorText(e),true)),700);}
function savePacketDraft(){clearTimeout(packetDraftTimer);if(!packetDraftLoaded)return Promise.resolve();const v=packetValue(),s=JSON.stringify(v);packetDraftQueue=packetDraftQueue.catch(()=>{}).then(async()=>{if(s!==packetDraftLast){const r=await call('world.transact',{changes:[{id:'shell.packet-ui',expected_revision:packetDraftRevision,facets:{'studio.packet-ui':v}}]});packetDraftRevision=r.items[0].revision;packetDraftLast=s;}packetDraftDirty=JSON.stringify(packetValue())!==s;});return packetDraftQueue;}
async function packetInvoke(action,args){const registry=await call('tools.list');const t=registry.actions.find(x=>x.package==='studio.packets'&&x.action===action);if(!t)throw new Error('Research packet action is not installed: '+action);const r=await call('action.invoke',{package:t.package,action,revision:t.revision,args});const v=r.result||r;if(!v.ok)throw new Error(v.error||'Packet operation refused; no documents imported.');return v;}
function packetFresh(){return packetPreview&&packetPreview._raw===$('packets-json').value&&packetPreview.collection_name===$('packets-name').value.trim();}
function packetButtons(){const fresh=packetFresh();$('packets-apply').disabled=!!packetPromise||!fresh||packetPreview.status==='cancelled';$('packets-cancel').disabled=!!packetPromise||!packetPreview||packetPreview.status!=='previewed';$('packets-attempt').textContent='Attempt token: '+packetToken+' · Retries reuse the same copy. “New copy / attempt” permits a separate copy.';}
function packetShow(v,raw){packetPreview={...v,_raw:raw};$('packets-preview-detail').hidden=false;$('packets-summary').textContent=JSON.stringify({format:v.format,version:v.version,status:v.status,collection:v.collection_name,titles:v.titles,counts:v.counts,new_native_objects:v.new_native_objects,creates:'1 collection + documents + sources + citation objects + inert history-event objects + comment threads; no active proposals',attempt_id:v.attempt_id,preview_revision:v.preview_revision,checksum:v.checksum,provenance:v.provenance,mapping:v.mapping,notice:v.notice},null,2);packetButtons();}
function packetBusy(task){if(packetPromise)return;for(const id of ['packets-export','packets-load','packets-preview','packets-new-attempt'])$(id).disabled=true;packetPromise=(async()=>{try{await task();}catch(e){packetStatus(errorText(e),true);}finally{packetPromise=null;for(const id of ['packets-export','packets-load','packets-preview','packets-new-attempt'])$(id).disabled=false;packetButtons();}})();packetButtons();}
function packetChanged(){packetRetain();packetButtons();if(packetPreview&&!packetFresh())packetStatus('Input changed after preview. Start a New copy / attempt, then validate again. Apply is disabled.');}
$('packets-json').oninput=packetChanged;$('packets-name').oninput=packetChanged;$('packets-area').ontoggle=packetRetain;
$('packets-copy').onclick=()=>{$('packets-json').focus();$('packets-json').select();packetStatus('JSON selected. Press Ctrl+C (or use your device Copy command).');};
$('packets-new-attempt').onclick=()=>{if(packetPreview?.status==='previewed'){packetStatus('Cancel the current preview before starting a separate attempt.',true);return;}packetToken=crypto.randomUUID();packetPreview=null;$('packets-preview-detail').hidden=true;packetRetain();packetButtons();packetStatus('New attempt created. Choose an unused collection name and validate.');};
$('packets-export').onclick=()=>packetBusy(async()=>{const ids=[...packetChecks];if(!ids.length||ids.length>8)throw new Error('Select 1–8 documents.');packetStatus('Saving selected editor drafts, then exporting retained evidence… You can keep writing.');await Promise.all(ids.map(id=>entries.get(id)).filter(Boolean).map(save));const v=await packetInvoke('export_packet',{document_ids:ids});$('packets-json').value=v.packet_json;packetChanged();await savePacketDraft();await packetRefreshLists();packetStatus('Exported '+v.counts.documents+' documents, '+v.counts.sources+' shared source(s), '+v.counts.history+' history entries. Native packet: '+v.packet_id);});
$('packets-load').onclick=()=>packetBusy(async()=>{const id=$('packets-retained').value;if(!id)throw new Error('Choose a retained packet.');const r=await call('world.get',{id}),o=r.item||r;$('packets-json').value=o.facets['studio.research-packet'].packet_json;packetChanged();await savePacketDraft();packetStatus('Retained JSON loaded. Choose a collection name, then validate.');});
$('packets-preview').onclick=()=>packetBusy(async()=>{const raw=$('packets-json').value,name=$('packets-name').value.trim();packetStatus('Validating packet and evidence… Editor and navigation remain available.');const v=await packetInvoke('preview',{packet_json:raw,collection_name:name,attempt_token:packetToken});packetShow(v,raw);await savePacketDraft();packetStatus('Preview only: '+v.new_native_objects+' new native objects will be made. Review the details; Apply import or Cancel.');});
$('packets-cancel').onclick=()=>packetBusy(async()=>{if(!packetPreview)return;await packetInvoke('cancel',{attempt_id:packetPreview.attempt_id});packetPreview.status='cancelled';packetShow(packetPreview,packetPreview._raw);await savePacketDraft();packetStatus('Cancelled. No collection or documents created. This attempt cannot be applied.');});
$('packets-apply').onclick=()=>packetBusy(async()=>{if(!packetFresh())throw new Error('Input changed; validate a fresh attempt before applying.');const p=packetPreview;packetStatus('Revalidating and importing atomically… You can keep writing.');const v=await packetInvoke('apply_import',{attempt_id:p.attempt_id,preview_revision:p.preview_revision,checksum:p.checksum});packetShow(v,p._raw);await savePacketDraft();await refreshDocs();await refreshSources();await refreshReview();await packetRefreshLists(v.collection_id);packetStatus(v.already_applied?'Already applied: the original mapping was reused; no duplicate documents.':'Imported into “'+v.collection_name+'”. Open a copy below. Originals are unchanged.');});
function packetDrawDocuments(){if(loaded&&packetDraftLoaded){let removed=0;for(const id of packetChecks)if(!entries.has(id)){packetChecks.delete(id);removed++;}if(removed){packetRetain();packetStatus('Unavailable documents removed from export selection.');}}const sig=[...entries].map(([id,e])=>id+':'+e.title).join('|');if(sig===packetDocSignature)return;packetDocSignature=sig;const root=$('packets-documents');const active=document.activeElement?.dataset.packetDocument;root.replaceChildren();for(const [id,e] of entries){const label=element('label','packet-check');const check=document.createElement('input');check.type='checkbox';check.dataset.packetDocument=id;check.checked=packetChecks.has(id);check.setAttribute('aria-label','Export '+e.title+' '+id);check.onchange=()=>{if(check.checked&&packetChecks.size>=8){check.checked=false;packetStatus('Maximum 8 documents per packet.',true);return;}if(check.checked)packetChecks.add(id);else packetChecks.delete(id);packetRetain();};label.append(check,document.createTextNode(e.title+(e.object.facets['studio.packet-origin']?' (imported copy)':'')));root.append(label);}if(active)[...root.querySelectorAll('input')].find(x=>x.dataset.packetDocument===active)?.focus({preventScroll:true});}
function packetDrawCollection(){const o=packetCollectionMap.get($('packets-collections').value),root=$('packets-imported-documents');root.replaceChildren();if(!o)return;for(const id of o.facets['core.collection'].entries){const b=element('button','button',entries.get(id)?.title||id);b.dataset.packetOpen=id;b.onclick=()=>{choose(id);$('docs-content').scrollIntoView({block:'start'});editor.focus({preventScroll:true});};root.append(b);}}
$('packets-collections').onchange=packetDrawCollection;
async function packetRefreshLists(prefer){const packets=await reviewQuery('studio.research-packet'),collections=await reviewQuery('studio.packet-collection');const sl=$('packets-retained'),old=sl.value;sl.replaceChildren(new Option('Choose a saved packet',''));for(const o of packets){const v=o.facets['studio.research-packet'];sl.append(new Option(v.created_at+' · '+v.checksum.slice(0,12),o.id));}sl.value=old;packetCollectionMap=new Map(collections.map(o=>[o.id,o]));const cl=$('packets-collections'),prior=prefer||cl.value;cl.replaceChildren();for(const o of collections)cl.append(new Option(o.facets['core.collection'].name,o.id));if(!collections.length)cl.append(new Option('No imported collections',''));if(packetCollectionMap.has(prior))cl.value=prior;packetDrawCollection();}
function citationPresence(c,text){
 const block=c?.citation_markdown||'';if(!block)return {state:'detached',matches:0,reason:'No recorded citation text.'};
 const hits=[];for(let i=0;(i=text.indexOf(block,i))>=0;i++)hits.push(i);
 if(!hits.length)return {state:'detached',matches:0,reason:'Cited block was removed or edited. Original evidence is retained.'};
 if(hits.length!==1)return {state:'ambiguous',matches:hits.length,reason:'The cited block occurs more than once; no single location was chosen.'};
 return {state:'active',matches:1,start:hits[0],end:hits[0]+block.length};
}
function citationActive(c){const e=entries.get(c?.document_id);return !!e&&citationPresence(c,e.text).state==='active';}
function reviewInScope(did){return $('review-scope')?.value==='all'||did===selected;}
function proposalActive(p){return citationActive(reviewCitations.get(p.citation_id)?.facets['studio.citation']);}
function packetDrawEvidence(){
 const cs=[...reviewCitations.values()].filter(o=>o.facets['studio.citation'].document_id===selected),text=current()?.text||'';
 const sig=selected+'|'+text+'|'+!!current()?.dirty+'|'+cs.map(o=>o.id+':'+o.revision+':'+sourceMap.get(o.facets['studio.citation'].source_id)?.revision).join('|');
 if(sig===packetEvidenceSignature)return;packetEvidenceSignature=sig;
 const root=$('packets-evidence'),historyOpen=root.querySelector('#citation-inactive')?.open||false;
 root.replaceChildren();
 const groups={active:[],detached:[],ambiguous:[]};
 for(const o of cs){const loc=citationPresence(o.facets['studio.citation'],text);groups[loc.state].push([o,loc]);}
 const summary=element('p','citation-summary',groups.active.length+' active citation'+(groups.active.length===1?'':'s')+' in this document'+(current()?.dirty?' · based on your unsaved text':''));
 summary.id='citations-summary';root.append(summary);
 const active=element('section','citation-active');active.id='citations-active';root.append(active);
 if(!groups.active.length)active.append(element('p','','No active citations. Deleted or edited quotations are not counted here.'));
 const render=(o,loc,target)=>{
  const c=o.facets['studio.citation'],source=sourceMap.get(c.source_id)?.facets['studio.source'];
  const card=element('article','review-card citation-card');card.dataset.citationId=o.id;card.dataset.citationState=loc.state;
  card.append(element('h3','',(source?.title||'Retained source')+' · revision '+c.source_revision),element('blockquote','citation-quote',c.quoted_text));
  if(loc.state==='active'){
   const jump=element('button','button','Go to cited text');jump.dataset.citationJump=o.id;
   jump.onclick=()=>{if(c.document_id!==selected)return;const now=citationPresence(c,current()?.text||'');if(now.state!=='active'){liveFeedback.textContent=now.reason;packetDrawEvidence();return;}goToDocumentRange(now.start,now.end);};
   card.append(jump);
  }else card.append(element('p','citation-location',loc.reason));
  const details=element('details','citation-provenance');details.append(element('summary','','Source evidence & citation history'),element('pre','',c.citation_markdown),element('p','packet-id','Source '+c.source_id+' · SHA-256 '+c.content_hash));
  for(const h of o.facets['studio.citation-history']?.entries||[]){
   const d=element('details','');d.append(element('summary','','Previous source revision '+h.citation.source_revision+' · replaced '+h.replaced_at),element('pre','',h.citation.citation_markdown),element('p','packet-id','Source '+h.citation.source_id+' · SHA-256 '+h.citation.content_hash+' · history event '+h.proposal_id));details.append(d);
  }
  card.append(details);target.append(card);
 };
 groups.active.forEach(([o,loc])=>render(o,loc,active));
 const inactive=[...groups.detached,...groups.ambiguous];
 if(inactive.length){
  const history=element('details','citation-inactive');history.id='citation-inactive';history.open=historyOpen;
  history.append(element('summary','',inactive.length+' inactive citation'+(inactive.length===1?'':'s')+' · retained history'),
   element('p','','Removed, edited or ambiguous text is not an active reference. Source evidence stays here; restoring the exact unique cited block makes it active again.'));
  inactive.forEach(([o,loc])=>render(o,loc,history));root.append(history);
 }
}
async function loadPacketDraft(){try{const rows=await reviewQuery('studio.packet-ui'),o=rows.find(o=>o.id==='shell.packet-ui');packetDraftRevision=o?.revision||0;const v=o?.facets['studio.packet-ui'];if(v&&!packetDraftDirty){$('packets-json').value=v.json;$('packets-name').value=v.name;packetToken=v.token;packetChecks=new Set(v.selected);$('packets-area').open=v.open;if(v.attempt){const r=await call('world.get',{id:v.attempt}),attempt=(r.item||r).facets['studio.packet-attempt'];if(attempt&&attempt.status==='cancelled'){packetPreview={attempt_id:v.attempt,status:'cancelled',collection_name:attempt.collection_name,_raw:attempt.packet_json};packetStatus('Previous preview was cancelled. Use New copy / attempt to begin again.');}else if(attempt){const p=await packetInvoke('preview',{packet_json:attempt.packet_json,collection_name:attempt.collection_name,attempt_token:packetToken});packetShow(p,attempt.packet_json);}}packetDraftLast=JSON.stringify(packetValue());}}catch(e){packetStatus('Preview restoration: '+errorText(e),true);}finally{packetDraftLoaded=true;packetDocSignature='';packetDrawDocuments();packetButtons();await packetRefreshLists();}}
const packetOldFlush=window.flushDocuments;window.flushDocuments=async()=>{if(packetPromise)await packetPromise;await savePacketDraft();await packetOldFlush();};
window.addEventListener('beforeunload',e=>{if(packetDraftDirty||packetPromise){e.preventDefault();e.returnValue='';}});
loadPacketDraft();setInterval(()=>{packetDrawDocuments();packetDrawEvidence();},1000);

/* Comments extend the existing stable editor/save path. */
const commentsPanel=element('section','research-comments');commentsPanel.id='docs-comments';
commentsPanel.innerHTML=`<h2>Comments</h2><p>16 threads/document · 8 messages/thread · 3000 characters/message. Resolved and orphaned discussions remain here.</p>
<button class="button" id="comments-capture">Use editor selection</button><pre id="comments-selection">Select Markdown, then use editor selection.</pre>
<label for="comments-new-message">New thread message</label><textarea id="comments-new-message" rows="3" maxlength="6000"></textarea><button class="button" id="comments-create">Create thread on selected text</button>
<p id="comments-status" role="status" aria-live="polite"></p><label for="comments-list">Threads in this document</label><select id="comments-list"></select>
<div id="comments-detail" hidden><p id="comments-state"></p><blockquote id="comments-quote"></blockquote><div class="docs-toolbar"><button class="button" id="comments-jump">Go to anchor (select text)</button><button class="button" id="comments-resolve">Resolve</button><button class="button" id="comments-reanchor">Reanchor to captured selection</button></div><details><summary>Original anchor evidence</summary><pre id="comments-original"></pre></details><ol id="comments-messages"></ol><label for="comments-reply-message">Reply message</label><textarea id="comments-reply-message" rows="3" maxlength="6000"></textarea><button class="button" id="comments-reply">Add reply</button></div>`;
$('docs-content').after(commentsPanel);
const commentsShortcut=element('button','button','Comments');commentsShortcut.id='docs-comments-open';panel.querySelector('.docs-toolbar').append(commentsShortcut);commentsShortcut.onclick=()=>commentsPanel.scrollIntoView({block:'start'});
let commentRows=[],commentDoc='',commentThread='',commentCapture=null,commentCaptureText='',commentBusyPromise=null,commentRefreshing=false,commentLoaded=false,commentDrafts={},commentDraftRev=0,commentDraftQueue=Promise.resolve(),commentDraftTimer,commentDraftDirty=false,commentDrawSig='';
$('comments-new-message').disabled=true;$('comments-reply-message').disabled=true;
function commentStatus(s){$('comments-status').textContent=s;}
function commentDraftKey(){return selected+'|'+commentThread;}
function commentRetain(){if(!commentLoaded)return;commentDrafts[selected+'|new']=$('comments-new-message').value;commentDrafts[commentDraftKey()]=$('comments-reply-message').value;commentDraftDirty=true;clearTimeout(commentDraftTimer);commentDraftTimer=setTimeout(()=>commentSaveDraft().catch(e=>commentStatus(errorText(e))),250);}
function commentSaveDraft(){clearTimeout(commentDraftTimer);if(!commentLoaded||!commentDraftDirty)return commentDraftQueue;const drafts={...commentDrafts};commentDraftDirty=false;commentDraftQueue=commentDraftQueue.catch(()=>{}).then(async()=>{try{const r=await call('world.transact',{changes:[{id:'shell.comment-ui',expected_revision:commentDraftRev,facets:{'studio.comment-ui':{drafts}}}]});commentDraftRev=r.items[0].revision;}catch(e){commentDraftDirty=true;throw e;}});return commentDraftQueue;}
function commentLocation(a,text){if(text===a.snapshot)return {state:'attached',start:a.start,end:a.end};const hits=[];for(let i=0;(i=text.indexOf(a.quote,i))>=0;i++)hits.push(i);if(!hits.length)return {state:'orphaned',reason:'Quotation was deleted or replaced'};if(hits.length!==1||a.occurrences!==1)return {state:'ambiguous',reason:'Duplicate quotation after document changed; explicitly reanchor'};const i=hits[0],j=i+a.quote.length;if((a.prefix&&!text.slice(0,i).endsWith(a.prefix))||(a.suffix&&!text.slice(j).startsWith(a.suffix)))return {state:'orphaned',reason:'Surrounding evidence changed; explicitly reanchor'};return {state:'attached',start:i,end:j};}
function commentCurrent(){return commentRows.find(o=>o.id===commentThread);}
function commentRender(){const e=current();commentsPanel.hidden=!e;if(!e)return;
 if(commentDoc!==selected){commentDoc=selected;commentThread='';commentCapture=null;commentDrawSig='';$('comments-new-message').value=commentDrafts[selected+'|new']||'';$('comments-reply-message').value='';$('comments-selection').textContent='Select Markdown, then use editor selection.';}
 const rows=commentRows.filter(o=>o.facets['studio.comment-thread'].document_id===selected),sl=$('comments-list');const sig=rows.map(o=>o.id+':'+o.revision).join('|');
 if(sl.dataset.sig!==selected+sig){sl.dataset.sig=selected+sig;sl.replaceChildren(new Option('Choose a thread',''));for(const o of rows){const t=o.facets['studio.comment-thread'];sl.append(new Option(t.status+' · '+t.anchor.quote.slice(0,60)+' · '+o.id.slice(-6),o.id));}sl.value=commentThread;}
 const o=commentCurrent();$('comments-detail').hidden=!o;if(!o)return;const t=o.facets['studio.comment-thread'],loc=commentLocation(t.anchor,e.text);$('comments-state').textContent=t.status+' · '+loc.state+(loc.reason?' — '+loc.reason:' · UTF-16 '+loc.start+'–'+loc.end)+(e.dirty?' · local unsaved text':'');$('comments-quote').textContent=t.anchor.quote;$('comments-resolve').textContent=t.status==='open'?'Resolve':'Reopen';$('comments-jump').disabled=loc.state!=='attached';
 if(commentDrawSig!==o.id+':'+o.revision){commentDrawSig=o.id+':'+o.revision;$('comments-messages').replaceChildren(...t.messages.map(m=>element('li','',m.text+' — '+m.created_at)));const a=t.original_anchor;$('comments-original').textContent='Selected at native revision '+a.document_revision+' · UTF-16 '+a.start+'–'+a.end+'\n'+a.quote+'\nBefore: '+a.prefix+'\nAfter: '+a.suffix+'\nSHA-256 '+a.sha256;}
}
async function commentRefresh(){if(commentRefreshing)return;commentRefreshing=true;try{commentRows=await reviewQuery('studio.comment-thread');commentRender();}catch(e){commentStatus(errorText(e));}finally{commentRefreshing=false;}}
async function commentInvoke(action,args){const registry=await call('tools.list'),tool=registry.actions.find(t=>t.package==='studio.comments'&&t.action===action);if(!tool)throw new Error('Comments action is not installed');const r=await call('action.invoke',{package:tool.package,revision:tool.revision,action,args});const v=r.result||r;if(!v.ok)throw new Error(v.error||'Comment refused');return v;}
function commentBusy(task){if(commentBusyPromise)return;commentStatus('Working… Your editor and drafts remain available.');for(const id of ['comments-create','comments-reply','comments-reanchor','comments-resolve','comments-capture'])$(id).disabled=true;commentBusyPromise=(async()=>{try{await task();}catch(e){commentStatus('Refused: '+errorText(e)+' Drafts retained.');}finally{commentBusyPromise=null;for(const id of ['comments-create','comments-reply','comments-reanchor','comments-resolve','comments-capture'])$(id).disabled=false;await commentRefresh();}})();}
$('comments-capture').onmousedown=e=>e.preventDefault();$('comments-capture').onclick=()=>{const e=current(),did=selected,text=editor.value,start=editor.selectionStart,end=editor.selectionEnd;commentBusy(async()=>{if(!e||start===end)throw new Error('Select a nonempty range in the Markdown editor first');await save(e);if(selected!==did||e.text!==text)throw new Error('Selection changed while saving; select again');commentCaptureText=text;commentCapture={document_id:did,document_revision:e.object.revision,start,end,quote:text.slice(start,end)};$('comments-selection').textContent='Captured revision '+e.object.revision+' · UTF-16 '+start+'–'+end+'\n'+commentCapture.quote;commentStatus('Selection captured. Write a message or explicitly reanchor a thread.');});};
function commentSelection(){if(!commentCapture||commentCapture.document_id!==selected)throw new Error('Use editor selection first');const e=current();if(!e||e.dirty||e.promise||e.text!==commentCaptureText||e.object.revision!==commentCapture.document_revision)throw new Error('Captured selection is stale; save and use editor selection again');return {...commentCapture};}
$('comments-new-message').oninput=commentRetain;$('comments-reply-message').oninput=commentRetain;
$('comments-create').onclick=()=>{let args;try{args={...commentSelection(),message:$('comments-new-message').value};}catch(e){commentStatus(errorText(e));return;}const did=selected;commentBusy(async()=>{const v=await commentInvoke('create',args);if(commentDrafts[did+'|new']===args.message)commentDrafts[did+'|new']='';if(selected===did){if($('comments-new-message').value===args.message)$('comments-new-message').value='';commentThread=v.thread_id;$('comments-reply-message').value=commentDrafts[commentDraftKey()]||'';commentRetain();}commentStatus('Thread created.');});};
$('comments-list').onchange=()=>{commentRetain();commentThread=$('comments-list').value;$('comments-reply-message').value=commentDrafts[commentDraftKey()]||'';commentDrawSig='';commentRender();};
$('comments-reply').onclick=()=>{const o=commentCurrent();if(!o)return;const key=commentDraftKey(),message=$('comments-reply-message').value;commentBusy(async()=>{await commentInvoke('reply',{thread_id:o.id,thread_revision:o.revision,message});if(commentDrafts[key]===message)commentDrafts[key]='';if(key===commentDraftKey()){if($('comments-reply-message').value===message)$('comments-reply-message').value='';commentRetain();}commentStatus('Reply added.');});};
$('comments-resolve').onclick=()=>{const o=commentCurrent();if(o)commentBusy(async()=>{await commentInvoke('set_status',{thread_id:o.id,thread_revision:o.revision,status:o.facets['studio.comment-thread'].status==='open'?'resolved':'open'});commentStatus('Thread state saved.');});};
$('comments-reanchor').onclick=()=>{const o=commentCurrent();if(!o)return;let a;try{a=commentSelection();}catch(e){commentStatus(errorText(e));return;}commentBusy(async()=>{await commentInvoke('reanchor',{thread_id:o.id,thread_revision:o.revision,...a});commentStatus('Reanchored same thread. Original evidence retained.');});};
$('comments-jump').onclick=()=>{const o=commentCurrent(),e=current();if(!o||!e)return;const loc=commentLocation(o.facets['studio.comment-thread'].anchor,e.text);if(loc.state!=='attached')return;editor.focus();editor.setSelectionRange(loc.start,loc.end);rememberSelection();editor.scrollTop=Math.max(0,(editor.value.slice(0,loc.start).split('\n').length-3)*24);editor.scrollIntoView({block:'center'});};
const commentOldChoose=choose;choose=function(id,persist=true){commentRetain();commentOldChoose(id,persist);commentRender();};
const commentOldFlush=window.flushDocuments;window.flushDocuments=async()=>{if(commentBusyPromise)await commentBusyPromise;await commentSaveDraft();await commentOldFlush();};
window.addEventListener('beforeunload',e=>{if(commentDraftDirty||commentBusyPromise){e.preventDefault();e.returnValue='';}});
(async()=>{try{const rows=await reviewQuery('studio.comment-ui'),o=rows.find(o=>o.id==='shell.comment-ui');commentDraftRev=o?.revision||0;commentDrafts=o?.facets['studio.comment-ui'].drafts||{};}catch(e){commentStatus('Draft loading failed: '+errorText(e));}commentLoaded=true;$('comments-new-message').disabled=false;$('comments-reply-message').disabled=false;commentDoc='';await commentRefresh();})();
setInterval(()=>{commentRender();},500);setInterval(commentRefresh,2500);

/* Document-first layout. Move existing nodes once; never replace an editor or draft. */
const chrome=element('header','docs-chrome');
chrome.innerHTML='<div class="docs-title-row"><span class="docs-file-icon" aria-hidden="true">▤</span><div class="docs-title-stack"></div><button class="button" id="docs-focus" aria-pressed="false" title="Hide navigation and chat while writing">Focus</button></div><div class="docs-menu-row"><button class="button" id="docs-files-open" aria-expanded="false">Documents ▾</button><button class="button" id="docs-sources-open" aria-expanded="false">Sources</button><button class="button" id="docs-evidence-open" aria-expanded="false">Citation history</button></div>';
const oldHeading=panel.querySelector('.docs-heading'), oldPicker=list.parentElement,deskButton=$('docs-desk');
const titleRow=title.parentElement, formatRow=$('docs-bold').parentElement;
titleRow.querySelector('label').classList.add('sr-only');
title.setAttribute('aria-label','Document title');title.placeholder='Untitled document';
chrome.querySelector('.docs-title-stack').append(titleRow);
chrome.querySelector('.docs-title-row').append($('docs-status'));
chrome.querySelector('.docs-menu-row').append($('docs-review-open'),$('packets-open'),$('docs-comments-open'));
oldHeading.replaceWith(chrome);
const drawer=element('aside','docs-drawer');drawer.id='docs-drawer';drawer.setAttribute('aria-label','Document tools');
drawer.innerHTML='<header class="docs-drawer-heading"><h2 id="docs-drawer-title">Document tools</h2><button class="button" id="docs-drawer-close" aria-label="Close document tools">✕</button></header><div class="docs-drawer-body"></div>';
const filePanel=element('section','docs-file-panel');filePanel.id='docs-files';
filePanel.append(element('p','subtitle','Open a document or start a new one.'),oldPicker,deskButton);
const drawerBody=drawer.querySelector('.docs-drawer-body');
drawerBody.append(filePanel,commentsPanel,research,review,packetPanel,evidencePanel);
panel.append(drawer);
formatRow.classList.add('docs-formatbar');formatRow.setAttribute('role','group');formatRow.setAttribute('aria-label','Formatting and view');
$('docs-bold').textContent='B';$('docs-bold').setAttribute('aria-label','Bold (Ctrl+B)');$('docs-bold').classList.add('docs-format-icon');
const italic=element('button','button docs-format-icon','I');italic.id='docs-italic';italic.title='Italic (Ctrl+I)';italic.setAttribute('aria-label',italic.title);
const heading=element('button','button','Heading');heading.id='docs-heading-format';heading.title='Toggle heading on selected lines';
const bullet=element('button','button','• List');bullet.id='docs-bullet';bullet.title='Toggle bulleted list on selected lines';
const quoteButton=element('button','button','❝ Quote');quoteButton.id='docs-blockquote';quoteButton.title='Toggle block quote on selected lines';
$('docs-bold').after(italic,heading,bullet,quoteButton);
const modeLabel=element('label','sr-only','Document view');modeLabel.htmlFor='docs-view';
const mode=document.createElement('select');mode.id='docs-view';mode.setAttribute('aria-label','Document view');
for(const [value,label] of [['edit','Editing · Markdown'],['preview','Reading preview'],['split','Side-by-side']])mode.append(new Option(label,value));
formatRow.append(modeLabel,mode);
chrome.append(formatRow);
const stage=element('div','docs-stage');stage.id='docs-stage';
$('docs-content').before(stage);stage.append($('docs-content'));
const sourceLabel=panel.querySelector('label[for="docs-editor"]');sourceLabel.classList.add('sr-only');
$('docs-help').textContent='Markdown · Ctrl+B bold · Ctrl+I italic · Ctrl+S save';
$('docs-save').textContent='Save';$('docs-rename').textContent='Done';$('docs-rename').title='Save document title';
const outline=$('docs-outline');const outlineDetails=element('details','docs-outline-disclosure');outlineDetails.innerHTML='<summary>Document outline</summary>';
outline.before(outlineDetails);outlineDetails.append(outline);
panel.querySelector('.docs-preview-label').classList.add('sr-only');
let view='edit',drawerName='',drawerTrigger=null;
const drawerSections={files:filePanel,comments:commentsPanel,sources:research,review,packets:packetPanel,evidence:evidencePanel};
const drawerButtons={files:$('docs-files-open'),comments:$('docs-comments-open'),sources:$('docs-sources-open'),review:$('docs-review-open'),packets:$('packets-open'),evidence:$('docs-evidence-open')};
const drawerNames={files:'Documents',comments:'Comments',sources:'Sources',review:'Citation review',packets:'Research packets',evidence:'Citation history'};
function setDocView(value){view=value;mode.value=value;panel.dataset.view=value;rememberSelection();}
mode.onchange=()=>setDocView(mode.value);setDocView('edit');
function openDocDrawer(name,trigger){
 rememberSelection();drawerName=name;drawerTrigger=trigger||drawerButtons[name];panel.dataset.drawer=name;
 $('docs-drawer-title').textContent=drawerNames[name]||'Document tools';
 for(const [key,node] of Object.entries(drawerSections))node.classList.toggle('docs-drawer-active',key===name);
 for(const [key,node] of Object.entries(drawerButtons)){node.setAttribute('aria-expanded',String(key===name));node.setAttribute('aria-controls','docs-drawer');}
 if(name==='sources')$('sources-area').open=true;
 if(name==='packets')$('packets-area').open=true;
 if(name==='evidence')evidencePanel.open=true;
 drawerBody.scrollTop=0;
}
function closeDocDrawer(){drawerName='';panel.dataset.drawer='';for(const node of Object.values(drawerButtons))node.setAttribute('aria-expanded','false');drawerTrigger?.focus({preventScroll:true});}
for(const [name,node] of Object.entries(drawerButtons)){
 node.setAttribute('aria-expanded','false');node.onmousedown=e=>e.preventDefault();
 node.onclick=()=>drawerName===name?closeDocDrawer():openDocDrawer(name,node);
}
$('docs-drawer-close').onclick=closeDocDrawer;
drawer.addEventListener('keydown',e=>{if(e.key==='Escape'){e.preventDefault();closeDocDrawer();}});
$('review-to-sources').onclick=()=>{openDocDrawer('sources');$('sources-list').focus({preventScroll:true});};
const previousJump=$('comments-jump').onclick;
$('comments-jump').onclick=()=>{setDocView('edit');previousJump();};
filePanel.addEventListener('change',e=>{if(e.target===list)closeDocDrawer();});
const previousNew=$('docs-new').onclick;
$('docs-new').onclick=async()=>{editor.readOnly=true;title.readOnly=true;try{await previousNew();closeDocDrawer();setDocView(liveEditor?'live':'edit');title.focus();title.select();}finally{editor.readOnly=reviewLocks.has(selected);title.readOnly=editor.readOnly;}};
drawer.addEventListener('click',e=>{if(e.target.closest('[data-packet-open]')){closeDocDrawer();setDocView(liveEditor?'live':'edit');if(liveEditor)liveEditor.focus();else editor.focus({preventScroll:true});}});
function wrapDocText(mark,fallback){
 if(editor.readOnly||!current())return;setDocView('edit');
 const start=editor.selectionStart,end=editor.selectionEnd,word=editor.value.slice(start,end)||fallback;
 editor.setRangeText(mark+word+mark,start,end,'select');editor.focus({preventScroll:true});editor.setSelectionRange(start+mark.length,start+mark.length+word.length);edited();
}
function prefixDocLines(prefix){
 if(editor.readOnly||!current())return;setDocView('edit');
 const start=editor.value.lastIndexOf('\n',Math.max(0,editor.selectionStart-1))+1;
 let end=editor.value.indexOf('\n',editor.selectionEnd);if(end<0)end=editor.value.length;
 const lines=editor.value.slice(start,end).split('\n'),remove=lines.every(x=>x.startsWith(prefix));
 editor.setRangeText(lines.map(x=>remove?x.slice(prefix.length):prefix+x).join('\n'),start,end,'select');editor.focus({preventScroll:true});edited();
}
for(const b of [italic,heading,bullet,quoteButton])b.onmousedown=e=>e.preventDefault();
italic.onclick=()=>wrapDocText('*','italic text');heading.onclick=()=>prefixDocLines('## ');bullet.onclick=()=>prefixDocLines('- ');quoteButton.onclick=()=>prefixDocLines('> ');
const priorBold=$('docs-bold').onclick;$('docs-bold').onclick=()=>{setDocView('edit');priorBold();};
panel.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&!e.isComposing&&e.key.toLowerCase()==='i'&&e.target===editor){e.preventDefault();wrapDocText('*','italic text');}});
$('docs-focus').onclick=()=>{const on=$('app').classList.toggle('docs-focus');$('docs-focus').setAttribute('aria-pressed',String(on));$('docs-focus').textContent=on?'Exit focus':'Focus';};
panel.dataset.drawer='';
new ResizeObserver(rows=>panel.classList.toggle('docs-narrow',rows[0].contentRect.width<=650)).observe(panel);

/* Live Markdown and explicit selection-to-JEFF, retaining the original data/save path. */
let liveEditor=null,fromLiveEditor=false,liveDocumentId='';
const liveHost=element('div','docs-live');liveHost.id='docs-live';editor.before(liveHost);
const liveFeedback=element('p','docs-context-feedback');liveFeedback.id='docs-context-status';liveFeedback.setAttribute('role','status');liveFeedback.setAttribute('aria-live','polite');chrome.append(liveFeedback);
const askJeff=element('button','button','Ask JEFF');askJeff.id='docs-ask-jeff';askJeff.title='Add the editor selection to your chat draft (Ctrl+Shift+Enter). Nothing is sent automatically.';askJeff.setAttribute('aria-label','Ask JEFF about selected text');chrome.querySelector('.docs-menu-row').append(askJeff);
let contextBusy=false;
async function stageDocumentContext(){
 if(contextBusy)return;
 if(view==='preview'||$('docs-preview').contains(document.getSelection()?.anchorNode)){liveFeedback.textContent='Select text in Live formatting or Markdown source, then Ask JEFF.';return;}
 const e=current(),did=selected,range=view==='live'&&liveEditor?liveEditor.selection():[editor.selectionStart,editor.selectionEnd],text=editor.value;
 if(!e||range[0]===range[1]){liveFeedback.textContent='Select a passage first, then Ask JEFF. Nothing has been sent.';return;}
 if(range[1]-range[0]>12000){liveFeedback.textContent='Select at most 12,000 UTF-16 characters. Your draft is unchanged.';return;}
 contextBusy=true;askJeff.disabled=true;liveFeedback.textContent='Saving and checking your selected passage…';
 try{
  await save(e);
  if(selected!==did||e.text!==text)throw new Error('Document changed while preparing context. Select again.');
  const registry=await call('tools.list'),tool=registry.actions.find(t=>t.package==='studio.documents'&&t.action==='selection_context');
  if(!tool)throw new Error('Document context action is not installed.');
  const r=await call('action.invoke',{package:tool.package,revision:tool.revision,action:tool.action,args:{document_id:did,document_revision:e.object.revision,start:range[0],end:range[1],quote:text.slice(...range)}});
  const v=r.result||r;if(!v.ok)throw new Error(v.error||'Selection was refused.');
  if(selected!==did||e.text!==text)throw new Error('Document changed while checking context. Select again.');
  const input=$('chat-input'),block=v.message,existing=input.value;
  if(!existing.includes(block)){
   const value=existing+(existing?'\n\n':'')+block;
   if(value.length>100000)throw new Error('Chat draft would be too long. Shorten it before adding this selection.');
   input.value=value;input.dispatchEvent(new Event('input',{bubbles:true}));
  }
  await saveDraft();
  if($('app').classList.contains('docs-focus'))$('docs-focus').click();
  showPanel(true);input.focus();input.setSelectionRange(input.value.length,input.value.length);
  liveFeedback.textContent='Selection added to your chat draft. Review it and press Send when ready. Your earlier draft was kept.';
 }catch(e){liveFeedback.textContent='Not sent: '+errorText(e);}
 finally{contextBusy=false;askJeff.disabled=false;}
}
askJeff.onmousedown=e=>e.preventDefault();askJeff.onclick=stageDocumentContext;
panel.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.shiftKey&&e.key==='Enter'&&e.target===editor&&!e.isComposing){e.preventDefault();stageDocumentContext();}});
try{
 if(typeof AgoraMarkdown==='undefined')throw new Error('Live editor bundle unavailable; Markdown source remains available.');
 liveEditor=AgoraMarkdown.create({parent:liveHost,text:editor.value,
  onChange:value=>{fromLiveEditor=true;try{editor.value=value;editor.setSelectionRange(...liveEditor.selection());edited();}finally{fromLiveEditor=false;}},
  onSelection:range=>{editor.setSelectionRange(...range);const e=current();if(e)e.selection=range;},
  onAsk:stageDocumentContext,onError:message=>{liveFeedback.textContent=message;}
 });
 const liveOption=new Option('Live formatting','live');mode.insertBefore(liveOption,mode.firstChild);
 [...mode.options].find(o=>o.value==='edit').textContent='Markdown source';
 [...mode.options].find(o=>o.value==='split').textContent='Source + preview';
 const rawDisplay=display;
 display=function(){rawDisplay();const e=current();if(!e)return;const switched=liveDocumentId!==selected;liveEditor.load(selected,editor.value,e.selection,editor.readOnly);liveDocumentId=selected;if(switched)stage.scrollTop=e.stageScroll||0;};
 const rawRemember=rememberSelection;
 rememberSelection=function(){if(view==='live'){const e=current();if(e){e.selection=liveEditor.selection();editor.setSelectionRange(...e.selection);e.stageScroll=stage.scrollTop;}}rawRemember();};
 const rawEdited=edited;
 edited=function(){rawEdited();if(!fromLiveEditor)liveEditor.sync(editor.value,[editor.selectionStart,editor.selectionEnd]);};
 const rawSetView=setDocView;
 setDocView=function(value){
  if(view==='live')rememberSelection();
  rawSetView(value);
  if(value==='live'){liveEditor.load(selected,editor.value,[editor.selectionStart,editor.selectionEnd],editor.readOnly);liveDocumentId=selected;}
  $('docs-help').textContent=value==='live'?'Live Markdown · Syntax appears near your cursor · Ctrl+B bold · Ctrl+I italic · Ctrl+Shift+Enter Ask JEFF':'Markdown source · Ctrl+B bold · Ctrl+I italic · Ctrl+Shift+Enter Ask JEFF';
 };
 for(const [id,run] of [['docs-bold',()=>liveEditor.inline('**','bold text')],['docs-italic',()=>liveEditor.inline('*','italic text')],['docs-heading-format',()=>liveEditor.prefix('## ')],['docs-bullet',()=>liveEditor.prefix('- ')],['docs-blockquote',()=>liveEditor.prefix('> ')]]){
  const old=$(id).onclick;$(id).onclick=()=>{if(view==='live')run();else old();};
 }
 const oldSourceQuote=$('sources-quote').onclick;
 $('sources-quote').onclick=()=>{oldSourceQuote();if(view==='live')liveEditor.sync(editor.value,[editor.selectionStart,editor.selectionEnd]);};
 $('comments-jump').onclick=()=>{const o=commentCurrent(),e=current();if(!o||!e)return;const loc=commentLocation(o.facets['studio.comment-thread'].anchor,e.text);if(loc.state!=='attached')return;goToDocumentRange(loc.start,loc.end);};
 new MutationObserver(()=>liveEditor.setReadonly(editor.readOnly)).observe(editor,{attributes:true,attributeFilter:['readonly']});
 const oldLiveFlush=window.flushDocuments;
 window.flushDocuments=async()=>{if(liveEditor.composing)throw new Error('Finish composing the current character before updating the editor.');await oldLiveFlush();};
 setDocView('live');
}catch(e){liveHost.hidden=true;liveFeedback.textContent=errorText(e);setDocView('edit');}
function goToDocumentRange(start,end){
 if(liveEditor){setDocView('live');liveEditor.reveal(start,end);editor.setSelectionRange(start,end);rememberSelection();}
 else{setDocView('edit');editor.focus();editor.setSelectionRange(start,end);rememberSelection();}
}

/* Citation presence is derived from current text in both native actions and UI. */
$('docs-evidence-open').textContent='Citations';
drawerNames.evidence='Citations';
evidencePanel.querySelector('summary').textContent='Citations in this document';
$('docs-sources-open').textContent='Source library';drawerNames.sources='Source library';
$('sources-area').querySelector('summary').textContent='Source library';
research.querySelector('.subtitle').textContent='Sources stay in your library when a quotation is deleted. Citations shows only references still tied to this document’s text.';
const reviewScopeRow=element('div','docs-toolbar');
reviewScopeRow.innerHTML='<label for="review-scope">Review scope</label><select id="review-scope"><option value="document">This document</option><option value="all">All documents</option></select>';
$('review-current-meta').before(reviewScopeRow);
$('review-scope').onchange=()=>{reviewChecks.clear();reviewSignature='';drawReview();};
const citationOldChoose=choose;
choose=function(id,persist=true){citationOldChoose(id,persist);reviewSignature='';drawReview();packetDrawEvidence();};

})();
