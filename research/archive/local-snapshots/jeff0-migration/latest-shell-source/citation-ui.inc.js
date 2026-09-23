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
 const sig=selected+'|'+text+'|'+cs.map(o=>o.id+':'+o.revision+':'+sourceMap.get(o.facets['studio.citation'].source_id)?.revision).join('|');
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
