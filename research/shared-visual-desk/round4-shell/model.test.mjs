import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {initialState,dispatch,project,asText} from './model.mjs';
import {preview} from '../foundations/program.mjs';
const program=JSON.parse(readFileSync(new URL('./program.json',import.meta.url),'utf8'));
const fresh=()=>({state:initialState(),program:structuredClone(program)});
const go=(d,a,opts)=>{const r=dispatch(d,a,opts);assert.equal(r.ok,true,JSON.stringify(r.errors));return r;};
const fail=(r,code)=>{assert.equal(r.ok,false);assert.equal(r.diagnostics[0].code,code);};

test('frozen interpreter hash remains the round-three hash',()=>{
 const hash=createHash('sha256').update(readFileSync(new URL('../foundations/program.mjs',import.meta.url))).digest('hex').toUpperCase();
 assert.equal(hash,'7535FFBD340AB39BA9540C0FF521F676FC7C991513D2084859622E970762F4CE');
});
test('notes select editor shared identity and hold literal draft until save',()=>{
 let d=fresh();d=go(d,{type:'select',id:'n2'}).document;
 const literal='## Literal\nQuotes "here", <tag>, backslash \\ and $literal';
 const draft=go(d,{type:'draft',text:literal});assert.equal(draft.receipt.scope,'local-view');assert.equal(draft.document.state.events.length,0);assert.notEqual(draft.document.state.notes[1].text,literal);
 const saved=go(draft.document,{type:'save'},{actor:'researcher'});d=saved.document;
 assert.equal(d.state.notes[1].text,literal);assert.equal(d.state.editor.noteId,'n2');assert.equal(d.state.editor.baseRev,1);assert.equal(d.state.editor.dirty,false);
 assert.match(asText(d,'notes'),/<tag>/);assert.equal(project(d,'editor').rows.find(r=>r.kind==='committed').text,literal);assert.match(asText(d,'together'),/researcher save n2/);assert.ok(saved.receipt.ruleIds.includes('save-shared-subject'));
});
test('placement and tags computed by authored rules with provenance',()=>{
 let d=fresh();const moved=go(d,{type:'move',id:'n2',x:900,y:-30});d=moved.document;assert.deepEqual([d.state.notes[1].x,d.state.notes[1].y],[440,0]);assert.ok(moved.receipt.ruleIds.includes('place-note'));
 d=go(d,{type:'tag',id:'n2',tags:['priority']}).document;assert.deepEqual(d.state.notes[1].tags,['priority']);assert.equal(d.state.notes[1].color,'#f6b85d');
});
test('source edit changes arrangement without adapter branch or interpreter change',()=>{
 let d=fresh();const altered=structuredClone(program);const x=altered.rules.find(r=>r.id==='arrange-notes').steps[0].steps[0];x.value=['add',12,['mul',['var','note.order'],75]];
 const install=go(d,{type:'program',program:altered});assert.ok(install.receipt.hostPrimitives.includes('program-install'));assert.equal(install.document.state.notes[1].x,200);
 const arranged=go(install.document,{type:'arrange'});assert.deepEqual(arranged.document.state.notes.map(n=>n.x),[12,87,162]);assert.ok(arranged.receipt.ruleIds.includes('arrange-notes'));
});
test('new subject allocated by host receives existing authored classification',()=>{
 let d=fresh();const created=go(d,{type:'create',title:'New field',text:'Real shared content'});d=created.document;const n=d.state.notes.at(-1);
 assert.equal(n.id,'n4');assert.deepEqual(n.tags,['new']);assert.equal(n.color,'#d1edbb');assert.ok(created.receipt.hostPrimitives.includes('identity-create-remove'));assert.ok(created.receipt.ruleIds.includes('classify-created-subject'));
 d=go(d,{type:'select',id:n.id}).document;assert.equal(d.state.editor.draft,'Real shared content');
 d=go(d,{type:'remove',id:n.id}).document;d=go(d,{type:'create',title:'Replacement',text:''}).document;assert.equal(d.state.notes.at(-1).id,'n5');fail(dispatch(d,{type:'move',id:'n4',x:1,y:1}),'missing-subject');
});
test('failed creation rule leaves no allocated identity or partial subject',()=>{
 const d=fresh();d.program.rules.push({id:'bad-create',on:'create',steps:[{op:'set',path:'together.summary',value:['div',1,0]}]});
 const r=dispatch(d,{type:'create',title:'Rejected',text:''});fail(r,'division-zero');assert.strictEqual(r.document,d);assert.equal(d.state.nextId,4);assert.equal(d.state.notes.length,3);
});
test('dirty draft survives rule installation and arrange; save conservatively refuses changed subject revision',()=>{
 let d=go(fresh(),{type:'draft',text:'UNSAVED exact\ntext'}).document;
 d=go(d,{type:'program',program:structuredClone(program)}).document;d=go(d,{type:'arrange'}).document;
 assert.equal(d.state.editor.draft,'UNSAVED exact\ntext');assert.equal(d.state.editor.dirty,true);assert.equal(d.state.editor.baseRev,0);
 const r=dispatch(d,{type:'save'});fail(r,'stale-draft');assert.strictEqual(r.document,d);assert.equal(r.document.state.editor.draft,'UNSAVED exact\ntext');
});
test('dirty selected subject cannot be removed or replaced by selecting another',()=>{
 const d=go(fresh(),{type:'draft',text:'keep this'}).document;fail(dispatch(d,{type:'remove',id:'n1'}),'dirty-draft');fail(dispatch(d,{type:'select',id:'n2'}),'dirty-draft');assert.equal(d.state.editor.draft,'keep this');
});
test('delayed events with expected revision refuse even with a fresh preview',()=>{
 const queued={type:'move',id:'n2',x:17,y:28,expectedRevision:0};const d=go(fresh(),{type:'tag',id:'n2',tags:['later']}).document;
 fail(dispatch(d,queued),'stale-event');fail(dispatch(d,{type:'move',id:'n2',x:17,y:28,expectedSubjectRev:0}),'stale-event');assert.equal(d.state.notes[1].x,200);
});
test('invalid program retains installed source and exact draft',()=>{
 const d=go(fresh(),{type:'draft',text:'draft stays'}).document;const bad=structuredClone(program);bad.rules[0].steps=[{op:'append',collection:'notes',value:['lit',{}]}];
 const r=dispatch(d,{type:'program',program:bad});assert.equal(r.ok,false);assert.strictEqual(r.document,d);assert.equal(d.state.editor.draft,'draft stays');assert.deepEqual(d.program,program);
});
test('frozen language refuses append and arbitrary tag membership operators',()=>{
 const s=initialState();const p={version:1,rules:[{id:'grow',steps:[{op:'append',collection:'notes',value:['lit',{}]}]}]};assert.equal(preview(p,s).diagnostics[0].code,'step');
 p.rules[0].steps=[{op:'set',path:'together.summary',value:['contains',['get','notes.0.tags'],'priority']}];assert.equal(preview(p,s).diagnostics[0].code,'operator');
});
test('whole array literal replacement is expressible but lifecycle admission rejects it',()=>{
 const d=fresh(),p={version:1,rules:[{id:'literal-delete',on:'arrange',steps:[{op:'set',path:'notes',value:['lit',[]]}]}]};assert.equal(preview(p,d.state,{event:'arrange'}).ok,true);
 d.program=p;fail(dispatch(d,{type:'arrange'}),'host-owned-path');assert.equal(d.state.notes.length,3);
});
test('history is bounded and text projection discloses omitted prefix; acknowledgement is local',()=>{
 let d=fresh();for(let i=0;i<43;i++)d=go(d,{type:'tag',id:'n2',tags:[String(i)]}).document;
 assert.equal(d.state.events.length,40);assert.equal(d.state.historyFloor,3);assert.match(asText(d,'together'),/after sequence 3/);
 const seen=go(d,{type:'mark-seen'});assert.equal(seen.document.state.revision,43);assert.equal(seen.document.state.together.seenSeq,43);assert.equal(project(seen.document,'together').rows.filter(r=>r.kind==='unread').length,0);
});
test('window changes are authored and text API rejects unknown app',()=>{
 const r=go(fresh(),{type:'window',id:'editor',x:333,y:222});assert.equal(r.document.state.windows[1].x,333);assert.ok(r.receipt.ruleIds.includes('position-window'));assert.throws(()=>asText(r.document,'unknown'),/Unknown app/);
});
test('capacity refusal retains all existing subjects',()=>{
 let d=fresh();for(let i=0;i<9;i++)d=go(d,{type:'create',title:'Note '+i,text:''}).document;fail(dispatch(d,{type:'create',title:'Too many',text:''}),'note-limit');assert.equal(d.state.notes.length,12);
});
test('independent appearances and rich text spans explicitly unsupported',()=>{
 const d=fresh();fail(dispatch(d,{type:'duplicate-appearance',id:'n1'}),'unsupported');fail(dispatch(d,{type:'format-range',start:0,end:4,bold:true}),'unsupported');
});


test('local-view event cannot smuggle shared writes past history',()=>{
 const d=fresh();d.program.rules.push({id:'smuggled-write',on:'draft',steps:[{op:'set',path:'notes.0.text',value:'silent overwrite'}]});
 const r=dispatch(d,{type:'draft',text:'my draft'});fail(r,'local-event-write');assert.strictEqual(r.document,d);assert.equal(d.state.notes[0].rev,0);assert.equal(d.state.events.length,0);
});
test('notes text projection includes authored color as well as content and position',()=>{
 assert.match(asText(fresh(),'notes'),/color #f6b85d/);
});


test('explicit discard/reopen recovers stale editor; omission preserves exact draft',()=>{
 let d=go(fresh(),{type:'draft',text:'retain me exactly\n$\\'}).document;d=go(d,{type:'arrange'}).document;
 const before=d.state.editor.draft;const refused=dispatch(d,{type:'reload-editor'});fail(refused,'discard-required');assert.equal(refused.document.state.editor.draft,before);
 const reopened=go(d,{type:'reload-editor',discardDraft:true});assert.equal(reopened.receipt.scope,'local-view');assert.equal(reopened.document.state.editor.draft,reopened.document.state.notes[0].text);assert.equal(reopened.document.state.editor.baseRev,reopened.document.state.notes[0].rev);assert.equal(reopened.document.state.editor.dirty,false);assert.ok(reopened.receipt.ruleIds.includes('reopen-saved-subject'));
});
test('queued editor actions cannot silently switch target after a local selection',()=>{
 const d=go(fresh(),{type:'select',id:'n2'}).document;assert.equal(d.state.revision,0);
 fail(dispatch(d,{type:'draft',id:'n1',text:'old target text',expectedRevision:0}),'stale-editor-target');fail(dispatch(d,{type:'save',id:'n1',expectedSubjectRev:0}),'stale-editor-target');
});
test('shared rule window changes appear in event identity evidence for any shared event',()=>{
 const d=fresh();d.program.rules.push({id:'save-window-policy',on:'save',steps:[{op:'set',path:'windows.2.x',value:77}]});const saved=go(d,{type:'save'});assert.ok(saved.document.state.events.at(-1).changed.includes('window:together'));
});
