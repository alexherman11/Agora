/* Round 4 adaptation. Host bridges are named below; no interpreter changes. */
import {preview,apply} from '../foundations/program.mjs';
const copy=x=>JSON.parse(JSON.stringify(x));
const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const MAX_NOTES=12, MAX_EVENTS=40, MAX_TEXT=8000;
const worldActions=new Set(['move','tag','save','arrange','window','create','remove','program']);
const ruleActions=new Set(['select','move','tag','draft','save','arrange','mark-seen','window','reload-editor']);
class Refusal extends Error {constructor(code,message){super(message);this.code=code;}}
const refuse=(code,message)=>{throw new Refusal(code,message);};
const string=(x,label,max=MAX_TEXT)=>{if(typeof x!=='string'||x.length>max)refuse('domain',label+' must be a bounded string');};
const num=(x,label,min=0,max=5000)=>{if(!Number.isFinite(x)||x<min||x>max)refuse('domain',label+' outside '+min+'..'+max);};
const note=(s,id)=>s.notes.find(n=>n.id===id);
export const hostPrimitives=Object.freeze(['event-input-and-admission','identity-create-remove','revision-and-save-CAS','event-history-append','program-install','projection']);
export function initialState(){
 const notes=[
  {id:'n1',title:'A shared garden',text:'## A place to think\nMove this note. Open it in Editor. Both views refer to n1.',tags:['priority'],x:20,y:35,color:'#f6b85d',rev:0,order:0},
  {id:'n2',title:'Rule workshop',text:'Arrangement lives in program.json. Change the 150 spacing expression, install, then Arrange.',tags:['idea'],x:200,y:80,color:'#b9dbe8',rev:0,order:1},
  {id:'n3',title:'Keep the evidence',text:'Drafts are local state in this model. Shared changes get actor, sequence and rule IDs; this is not presence.',tags:[],x:380,y:30,color:'#dbcaef',rev:0,order:2}
 ];
 return {revision:0,nextId:4,historyFloor:0,notes,selectedId:'n1',editor:{noteId:'n1',draft:notes[0].text,baseRev:0,dirty:false,status:'Reading shared subject'},windows:[{id:'notes',open:true,x:15,y:15,w:520,h:440},{id:'editor',open:true,x:550,y:15,w:390,h:440},{id:'together',open:true,x:955,y:15,w:270,h:440}],together:{seenSeq:0,summary:'No shared changes yet'},events:[],event:{type:'',id:'',x:0,y:0,text:'',tags:[],windowId:'',actor:''}};
}
function checkState(s){
 if(!s||!Array.isArray(s.notes)||s.notes.length>MAX_NOTES)refuse('domain','At most '+MAX_NOTES+' note subjects');
 const ids=new Set();
 for(const n of s.notes){
  string(n.id,'note.id',80);if(ids.has(n.id))refuse('identity','Duplicate subject id');ids.add(n.id);
  string(n.title,'note.title',200);string(n.text,'note.text');
  if(!Array.isArray(n.tags)||n.tags.length>12)refuse('domain','At most 12 tags');n.tags.forEach(t=>string(t,'tag',40));
  num(n.x,'note.x');num(n.y,'note.y');num(n.order,'note.order',0,1000000);num(n.rev,'note.rev',0,Number.MAX_SAFE_INTEGER);
  if(typeof n.color!=='string'||!/^#[0-9a-f]{6}$/i.test(n.color))refuse('domain','color must be a six-digit hex color');
 }
 if(s.selectedId!==''&&!ids.has(s.selectedId))refuse('identity','Selection names a missing subject');
 if(s.editor.noteId!==''&&!ids.has(s.editor.noteId))refuse('identity','Editor names a missing subject');
 string(s.editor.draft,'editor.draft');string(s.editor.status,'editor.status',1000);if(typeof s.editor.dirty!=='boolean')refuse('domain','editor.dirty must be boolean');
 num(s.editor.baseRev,'editor.baseRev',0,Number.MAX_SAFE_INTEGER);num(s.revision,'revision',0,Number.MAX_SAFE_INTEGER);
 num(s.nextId,'nextId',1,1000000);num(s.historyFloor,'historyFloor',0,Number.MAX_SAFE_INTEGER);
 if(!Array.isArray(s.windows)||s.windows.length!==3||new Set(s.windows.map(w=>w.id)).size!==3)refuse('domain','Three distinct app windows required');
 for(const w of s.windows){if(!['notes','editor','together'].includes(w.id))refuse('domain','Unknown window');for(const k of ['x','y','w','h'])num(w[k],'window.'+k);if(typeof w.open!=='boolean')refuse('domain','window.open must be boolean');}
 if(!Array.isArray(s.events)||s.events.length>MAX_EVENTS)refuse('domain','History retention limit');
 num(s.together.seenSeq,'seenSeq',0,Number.MAX_SAFE_INTEGER);string(s.together.summary,'summary',1000);
}
function admitAction(s,a,actor){
 if(!a||typeof a.type!=='string')refuse('action','Action needs type');string(actor,'actor',80);
 if(a.expectedRevision!==undefined&&a.expectedRevision!==s.revision)refuse('stale-event','Queued event expects revision '+a.expectedRevision+'; current '+s.revision);
 if(a.expectedSubjectRev!==undefined&&note(s,a.id??s.editor.noteId)?.rev!==a.expectedSubjectRev)refuse('stale-event','Queued event subject revision changed');
 if(!ruleActions.has(a.type)&&!['create','remove','program'].includes(a.type))refuse('unsupported','Unsupported action '+a.type);
 if(['select','move','tag','remove'].includes(a.type)&&!note(s,a.id))refuse('missing-subject','No current subject '+a.id);
 if(a.type==='select'&&s.editor.dirty)refuse('dirty-draft','Save or keep the current draft before opening another subject');
 if(a.type==='remove'&&s.editor.noteId===a.id&&s.editor.dirty)refuse('dirty-draft','Selected subject has an unresolved draft; removal refused');
 if(['draft','save','reload-editor'].includes(a.type)&&a.id!==undefined&&a.id!==s.editor.noteId)refuse('stale-editor-target','Queued editor action names another subject');
 if(a.type==='reload-editor'){if(a.discardDraft!==true)refuse('discard-required','Reopen saved requires explicit discardDraft:true');if(!note(s,s.editor.noteId))refuse('missing-subject','No editor subject');}
 if(a.type==='draft'){if(!note(s,s.editor.noteId))refuse('missing-subject','No editor subject');string(a.text,'draft');}
 if(a.type==='save'){
  const n=note(s,s.editor.noteId);if(!n)refuse('missing-subject','Editor subject removed');
  if(n.rev!==s.editor.baseRev)refuse('stale-draft','Subject revision changed from '+s.editor.baseRev+' to '+n.rev+'; exact draft retained');
 }
 if(['move','window'].includes(a.type)){num(a.x,'input x',-5000,5000);num(a.y,'input y',-5000,5000);}
 if(a.type==='window'&&!s.windows.some(w=>w.id===a.id))refuse('window','Unknown window');
 if(a.type==='tag'){if(!Array.isArray(a.tags)||a.tags.length>12)refuse('domain','tags must be an array up to 12');a.tags.forEach(t=>string(t,'tag',40));}
 if(a.type==='create'){if(s.notes.length>=MAX_NOTES)refuse('note-limit','Note capacity reached');string(a.title,'title',200);string(a.text??'','text');}
}
function admitRuleWrites(changes,local=false){
 for(const c of changes){
  const p=c.path;
  if(local&&(p.startsWith('notes.')||p.startsWith('windows.')))refuse('local-event-write','Local-view events cannot write shared material or windows');
  if(!/^notes\.\d+\.(title|text|tags|x|y|color)$/.test(p)&&!/^editor\.(noteId|draft|baseRev|dirty|status)$/.test(p)&&p!=='selectedId'&&!/^windows\.\d+\.(open|x|y|w|h)$/.test(p)&&!/^together\.(seenSeq|summary)$/.test(p))refuse('host-owned-path','Rules cannot write host-owned path '+p);
 }
}
function error(document,error,diagnostics){return {ok:false,document,receipt:null,errors:[error.message],diagnostics:diagnostics??[{code:error.code??'invalid',message:error.message}]};}
export function dispatch(document,action,{actor='alex'}={}){
 try{
  const original=document.state;checkState(original);admitAction(original,action,actor);
  let state=copy(original),program=document.program,changes=[],ruleIds=[],bridge=[];
  state.event={type:action.type,id:action.id??state.editor.noteId??'',x:action.x??0,y:action.y??0,text:action.text??'',tags:action.tags??[],windowId:action.id??'',actor};
  if(ruleActions.has(action.type)){
   const proposal=preview(program,state,{event:action.type});
   if(!proposal.ok)return error(document,new Refusal(proposal.diagnostics[0].code,proposal.errors.join('\n')),proposal.diagnostics);
   admitRuleWrites(proposal.changes,!worldActions.has(action.type));changes=proposal.changes;ruleIds=[...new Set(changes.flatMap(c=>c.ruleIds))];
   const applied=apply(state,proposal);if(!applied.ok)return error(document,new Refusal('apply',applied.errors.join('\n')),applied.diagnostics);state=applied.state;
  }else if(action.type==='create'){
   const id='n'+state.nextId++;state.event.id=id;state.notes.push({id,title:action.title,text:action.text??'',tags:[],x:40,y:40,color:'#dbcaef',rev:0,order:state.nextId-2});bridge.push('identity-create-remove');
  }else if(action.type==='remove'){
   state.notes=state.notes.filter(n=>n.id!==action.id);
   if(state.selectedId===action.id)state.selectedId='';
   if(state.editor.noteId===action.id)state.editor={noteId:'',draft:'',baseRev:0,dirty:false,status:'Subject removed'};
   bridge.push('identity-create-remove');
  }else if(action.type==='program'){
   const validation=preview(action.program,state,{event:'validate'});
   if(!validation.ok)return error(document,new Refusal('program',validation.errors.join('\n')),validation.diagnostics);
   program=copy(action.program);bridge.push('program-install');
  }
  if(action.type==='create'||action.type==='remove'){
   const proposal=preview(program,state,{event:action.type});
   if(!proposal.ok)return error(document,new Refusal(proposal.diagnostics[0].code,proposal.errors.join('\n')),proposal.diagnostics);
   admitRuleWrites(proposal.changes,!worldActions.has(action.type));changes=proposal.changes;ruleIds=[...new Set(changes.flatMap(c=>c.ruleIds))];
   const applied=apply(state,proposal);if(!applied.ok)return error(document,new Refusal('apply',applied.errors.join('\n')),applied.diagnostics);state=applied.state;
  }
  // Generic host metadata. No host branch computes authored placement/tag/draft output.
  const changed=[];
  for(const n of state.notes){const prior=note(original,n.id);if(!prior||!equal({...prior,rev:0},{...n,rev:0})){changed.push(n.id);n.rev=prior?prior.rev+1:0;}}
  for(const n of original.notes)if(!note(state,n.id))changed.push(n.id);
  if(action.type==='save')state.editor.baseRev=note(state,state.editor.noteId).rev;
  if(action.type==='program')changed.push('program');
  for(const w of state.windows)if(!equal(original.windows.find(old=>old.id===w.id),w))changed.push('window:'+w.id);
  const scope=worldActions.has(action.type)?'shared':'local-view';
  if(scope==='shared'){
   state.revision++;
   const event={seq:state.revision,actor,type:action.type,changed,ruleIds,mechanism:bridge.length?'host':'rules',summary:actor+' '+action.type+' '+(changed.join(', ')||'(no material change)')};
   state.events.push(event);if(state.events.length>MAX_EVENTS){const removed=state.events.shift();state.historyFloor=removed.seq;}
   bridge.push('revision-and-save-CAS','event-history-append');
  }
  checkState(state);
  // Reuse the frozen interpreter's JSON checks after every host transformation.
  const bounded=preview({version:1,rules:[]},state);
  if(!bounded.ok)return error(document,new Refusal('bounded-state',bounded.errors.join('\n')),bounded.diagnostics);
  return {ok:true,document:{...document,state,program},receipt:{action:action.type,scope,changes,changed,ruleIds,hostPrimitives:bridge,revision:state.revision},errors:[],diagnostics:[]};
 }catch(e){return error(document,e);}
}
export function project(document,app){
 const s=document.state;checkState(s);
 if(app==='notes')return {title:'Notes',rows:s.notes.map(n=>({id:n.id,kind:'subject',text:n.title+' ['+n.id+' rev '+n.rev+']\n'+n.text+'\nTags: '+n.tags.join(', ')+'; position '+n.x+', '+n.y+'; color '+n.color})),selection:s.selectedId};
 if(app==='editor'){
  const n=note(s,s.editor.noteId);
  return {title:'Editor',rows:[{id:'identity',kind:'context',text:n?'Shared subject '+n.id+'; current rev '+n.rev+'; draft base '+s.editor.baseRev:'No subject open'},{id:'draft',kind:'draft',text:s.editor.draft},{id:'status',kind:s.editor.dirty?'unsettled':'status',text:s.editor.status+(s.editor.dirty?' (unsettled; shared text unchanged)':'')},{id:'committed',kind:'committed',text:n?n.text:''}]};
 }
 if(app==='together')return {title:'Together',rows:[{id:'context',kind:'context',text:s.together.summary},{id:'limits',kind:'limit',text:'Retained events after sequence '+s.historyFloor+'; latest '+s.revision+'. Actor labels are attribution, not presence or authentication.'},...s.events.map(e=>({id:'e'+e.seq,kind:e.seq>s.together.seenSeq?'unread':'event',text:'#'+e.seq+' '+e.summary+'; '+e.mechanism+'; rules '+(e.ruleIds.join(', ')||'none')}))]};
 refuse('app','Unknown app '+app);
}
export function asText(document,app){const p=project(document,app);return p.title+'\n'+p.rows.map(r=>'['+r.kind+'] '+r.id+': '+r.text).join('\n');}
