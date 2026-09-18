// Media independent boundary probes. No browser, controller, or Claude runtime.
import assert from 'node:assert/strict';
import {preview, apply} from '../foundations/program.mjs';
const clone = x => structuredClone(x);
const base = () => ({notes:[{id:'n1',title:'One',text:'old',x:0},{id:'n2',title:'Two',text:'other',x:40}]});
const program = {version:1,rules:[{id:'edit-n1',on:'save',steps:[{op:'forEach',collection:'notes',as:'note',where:['eq',['var','note.id'],'n1'],steps:[{op:'set',target:'note',path:'text',value:'new'}]}]}]};
let count = 0;
function check(name, fn) { fn(); count++; console.log('PASS '+name); }
check('existing-id selection works across reordered input when preview is fresh', () => {
  const state=base(); state.notes.reverse();
  const p=preview(program,state,{event:'save'}); assert.equal(p.ok,true);
  const r=apply(state,p); assert.equal(r.ok,true); assert.equal(r.state.notes[1].text,'new'); assert.equal(r.state.notes[0].text,'other');
});
check('reorder after preview is refused by whole-state guard', () => {
  const state=base(), p=preview(program,state,{event:'save'}); state.notes.reverse();
  assert.equal(apply(state,p).diagnostics[0].code,'stale-preview');
});
check('identical deletion/recreation is invisible without an incarnation in state', () => {
  const state=base(), p=preview(program,state,{event:'save'});
  state.notes.splice(0,1); state.notes.unshift({id:'n1',title:'One',text:'old',x:0});
  const r=apply(state,p); assert.equal(r.ok,true); assert.equal(r.state.notes[0].text,'new');
});
check('explicit incarnation lets unchanged interpreter reject that replacement', () => {
  const state=base(); state.notes[0].incarnation=1;
  const p=preview(program,state,{event:'save'});
  state.notes[0]={...state.notes[0],incarnation:2};
  assert.equal(apply(state,p).diagnostics[0].code,'stale-preview');
});
check('whole-collection literal can create/delete data but has no allocation semantics', () => {
  const state=base();
  const next=[...clone(state.notes),{id:'n3',title:'Third',text:'fresh',x:80}];
  const replace={version:1,rules:[{id:'literal-list',steps:[{op:'set',path:'notes',value:['lit',next]}]}]};
  const r=apply(state,preview(replace,state)); assert.equal(r.ok,true); assert.equal(r.state.notes.length,3);
  const remove={version:1,rules:[{id:'literal-list',steps:[{op:'set',path:'notes',value:['lit',next.slice(1)]}]}]};
  assert.equal(apply(r.state,preview(remove,r.state)).state.notes[0].id,'n2');
});
check('fresh preview of delayed command does not supply event freshness', () => {
  const state=base(); state.notes[0].text='newer accepted edit';
  // The event was queued before that edit, but only its name is supplied here.
  const r=apply(state,preview(program,state,{event:'save'}));
  assert.equal(r.ok,true); assert.equal(r.state.notes[0].text,'new');
});
console.log(`${count} boundary probes passed. Two passes deliberately demonstrate missing host guarantees.`);
