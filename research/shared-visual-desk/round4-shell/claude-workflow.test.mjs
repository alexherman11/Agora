// External pressure nominated by Jeff in Claude studio mailbox a532, 2026-09-18.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {initialState,dispatch,asText} from './model.mjs';
const program=JSON.parse(readFileSync(new URL('./program.json',import.meta.url),'utf8'));

test('Jeff workflow: dirty draft survives agent tag, while appearances/grouping/causal undo remain unsupported',()=>{
 let document={state:initialState(),program};
 const draft='Alex unsettled draft: preserve this exact text.';
 let result=dispatch(document,{type:'draft',text:draft},{actor:'alex'});
 assert.equal(result.ok,true);document=result.document;
 result=dispatch(document,{type:'tag',id:'n1',tags:['review']},{actor:'agent'});
 assert.equal(result.ok,true);document=result.document;
 assert.equal(document.state.events.at(-1).actor,'agent');
 result=dispatch(document,{type:'save'},{actor:'alex'});
 assert.equal(result.ok,false);
 assert.equal(result.diagnostics[0].code,'stale-draft');
 assert.equal(result.document.state.editor.draft,draft);
 assert.match(result.errors[0],/revision changed/);
 assert.doesNotMatch(result.errors[0],/agent/); // Numeric refusal lacks causal actor explanation.
 for(const action of [
  {type:'duplicate-appearance',id:'n1'},
  {type:'move-to-surface',id:'n1',surface:'other'},
  {type:'group',ids:['n1','n2'],as:'free'},
  {type:'undo-causal-chain',id:'n1'}
 ]){
  const refused=dispatch(document,action);
  assert.equal(refused.ok,false);assert.equal(refused.diagnostics[0].code,'unsupported');
  assert.equal(refused.document,document);
 }
 const editor=asText(document,'editor');
 assert.match(editor,/unsettled/);assert.match(editor,/Alex unsettled draft/);
 // There is no draft-owner field, scheduler, occurrence container or undo chain to verify.
 assert.equal(Object.hasOwn(document.state.editor,'actor'),false);
 assert.equal(Object.hasOwn(document.state.notes[0],'surface'),false);
});
