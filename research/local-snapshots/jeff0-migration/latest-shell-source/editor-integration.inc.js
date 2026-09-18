
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
