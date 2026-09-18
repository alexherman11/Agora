// Independent Media controller checks. No browser or persistent desk writes.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {dispatch,initialState,asText} from './model.mjs';
const program=JSON.parse(readFileSync(new URL('./program.json',import.meta.url)));
const doc=()=>({state:initialState(),program:structuredClone(program)});
let count=0;
function check(name,fn){fn();count++;console.log('PASS '+name);}
check('created object receives installed AST classification and full text projection',()=>{
 const r=dispatch(doc(),{type:'create',title:'Late arrival',text:'line one\nline two'});
 assert.equal(r.ok,true);const n=r.document.state.notes.at(-1);assert.deepEqual(n.tags,['new']);assert.equal(n.color,'#d1edbb');
 assert(asText(r.document,'notes').includes('line two'));assert(r.receipt.ruleIds.includes('classify-created-subject'));
});
check('dirty selected remove refuses and retains exact draft',()=>{
 const draft=dispatch(doc(),{type:'draft',text:'distinct unsaved text'}).document;
 const r=dispatch(draft,{type:'remove',id:'n1'});assert.equal(r.ok,false);assert.equal(r.diagnostics[0].code,'dirty-draft');assert.equal(r.document.state.editor.draft,'distinct unsaved text');
});
check('queued event with expected revision refuses after intervening shared action',()=>{
 const before=doc(),old=before.state.revision;
 const moved=dispatch(before,{type:'move',id:'n2',x:90,y:90}).document;
 const late=dispatch(moved,{type:'tag',id:'n1',tags:['late'],expectedRevision:old});assert.equal(late.ok,false);assert.equal(late.diagnostics[0].code,'stale-event');
});
check('empty program disables authored arrangement',()=>{
 const d=doc();d.program={version:1,rules:[]};const old=structuredClone(d.state.notes);
 const r=dispatch(d,{type:'arrange'});assert.equal(r.ok,true);assert.deepEqual(r.document.state.notes,old);
});
check('scope cannot hide shared writes under a local event',()=>{
 const d=doc();d.program={version:1,rules:[{id:'draft-writes-shared',on:'draft',steps:[{op:'set',path:'notes.0.text',value:'shared mutation from local event'}]}]};
 const r=dispatch(d,{type:'draft',text:'input'});
 // Both policies are honest: refusal, or shared scope with durable event metadata.
 if(!r.ok)return;
 assert.equal(r.receipt.scope,'shared','shared note write must not be reported local-view');
 assert(r.document.state.revision>d.state.revision);assert(r.document.state.events.length>d.state.events.length);
});
check('text projection exposes rendered note color',()=>{
 const d=doc();const r=dispatch(d,{type:'tag',id:'n1',tags:[]});assert.equal(r.ok,true);
 assert(asText(r.document,'notes').includes(r.document.state.notes[0].color),'visible authored color missing from text projection');
});
console.log(`${count} controller checks passed.`);
