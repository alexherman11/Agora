import test from 'node:test';
import assert from 'node:assert/strict';
import {preview,apply,undo} from './program.mjs';
const base=()=>({content:{title:'An inhabited garden'},appearance:{bloom:0,caption:'dormant'},controls:{light:.6},items:[{id:'a',role:'signal',value:4,style:{fill:'#ccc',size:10}},{id:'b',role:'decoration',value:2,style:{fill:'#ccc',size:10}},{id:'c',role:'signal',value:8,style:{fill:'#ccc',size:10}}]});
const rule=(steps,id='r')=>({id,steps});
const program=(...rules)=>({version:1,rules});
const set=(path,value)=>({op:'set',path,value});
const err=(p,code)=>{assert.equal(p.ok,false);assert.equal(p.diagnostics[0].code,code);assert.ok(p.errors[0].includes(code));};

test('multi-step semantic selection computes styles and a separate rule composes',()=>{
 const s=base(),original=structuredClone(s);
 const p=preview(program(rule([{op:'forEach',collection:'items',as:'item',where:['eq',['var','item.role'],'signal'],steps:[
  {op:'let',name:'size',value:['mul',['var','item.value'],3]},
  {op:'set',target:'item',path:'style.size',value:['var','size']},
  {op:'if',test:['gt',['var','item.value'],5],then:[{op:'set',target:'item',path:'style.fill',value:'#fc0'}],else:[{op:'set',target:'item',path:'style.fill',value:'#05a'}]}
 ]}],'style-signals'),rule([set('appearance.caption',['concat','Light ',['get','controls.light']])],'caption')),s);
 assert.equal(p.ok,true);assert.equal(p.changes.length,5);assert.equal(p.stats.iterations,3);assert.deepEqual(s,original);
 const a=apply(s,p);assert.equal(a.ok,true);assert.deepEqual(a.state.items.map(x=>x.style.size),[12,10,24]);assert.deepEqual(a.state.items.map(x=>x.style.fill),['#05a','#ccc','#fc0']);assert.equal(a.state.appearance.caption,'Light 0.6');assert.deepEqual(undo(a.state,a.receipt).state,original);
});

test('composed rules read before-state independently of rule order',()=>{
 const rules=[rule([set('controls.light',.9)],'input'),rule([set('appearance.bloom',['get','controls.light'])],'derive')];
 for(const rs of [rules,[...rules].reverse()]){const s=base(),a=apply(s,preview(program(...rs),s));assert.equal(a.state.controls.light,.9);assert.equal(a.state.appearance.bloom,.6);}
});

test('same-value writes coalesce and preserve both contributors',()=>{
 const p=preview(program(rule([set('appearance.bloom',.8)],'a'),rule([set('appearance.bloom',.8)],'b')),base());assert.equal(p.ok,true);assert.equal(p.changes.length,1);assert.deepEqual(p.changes[0].ruleIds,['a','b']);
});

test('conflicting writes refuse the whole proposal',()=>{
 const s=base(),original=structuredClone(s);const p=preview(program(rule([set('appearance.bloom',.8)],'a'),rule([set('content.title','changed'),set('appearance.bloom',.7)],'b')),s);err(p,'write-conflict');assert.deepEqual(p.changes,[]);assert.deepEqual(s,original);
});

test('parent child overlap refuses regardless of order',()=>{
 const xs=[set('appearance',['lit',{bloom:1,caption:'new'}]),set('appearance.caption','other')];for(const steps of [xs,[...xs].reverse()])err(preview(program(rule(steps)),base()),'overlapping-write');
});

test('bad second step leaves input and published changes untouched',()=>{
 const s=base();const p=preview(program(rule([set('content.title','new'),set('appearance.bloom',['div',1,0])])),s);err(p,'division-zero');assert.deepEqual(p.changes,[]);assert.equal(s.content.title,'An inhabited garden');assert.match(p.diagnostics[0].path,/steps\[1\]\.value/);
});

test('if evaluates only selected branch and condition once',()=>{
 const p=preview(program(rule([set('appearance.bloom',['if',true,1,['div',1,0]])])),base(),{budget:{operations:4}});assert.equal(p.ok,true);assert.equal(p.stats.operations,4);
});

test('unknown syntax is rejected even in inactive event and branch',()=>{
 const p=program({id:'inactive',on:'never',steps:[{op:'if',test:false,then:[set('appearance.bloom',['execute','danger'])]}]});err(preview(p,base()),'operator');
});

test('event changes select which rule executes',()=>{
 const p=program({id:'run',on:'run',steps:[set('appearance.bloom',.2)]},{id:'change',on:'change',steps:[set('appearance.bloom',.9)]});assert.equal(preview(p,base()).changes[0].after,.2);assert.equal(preview(p,base(),{event:'change'}).changes[0].after,.9);
});

test('unknown writes refuse instead of silently creating typo properties',()=>err(preview(program(rule([set('appearance.blom',1)])),base()),'missing-path'));

test('prototype paths and dangerous object keys refuse',()=>{
 err(preview(program(rule([set('__proto__.polluted',true)])),base()),'path');
 err(preview(JSON.parse('{"version":1,"rules":[],"__proto__":{"polluted":true}}'),base()),'unsafe-key');assert.equal({}.polluted,undefined);
});

test('functions cyclic state and nonfinite numbers refuse',()=>{
 err(preview(program(rule([set('appearance.bloom',()=>1)])),base()),'json');const s=base();s.loop=s;err(preview(program(),s),'json');err(preview(program(rule([set('appearance.bloom',Infinity)])),base()),'number');
});

test('operation write and iteration bounds refuse atomically',()=>{
 const s=base();err(preview(program(rule([set('appearance.bloom',['add',1,2])])),s,{budget:{operations:2}}),'operation-limit');
 err(preview(program(rule([set('appearance.bloom',.7),set('appearance.caption','x')])),s,{budget:{writes:1}}),'write-limit');
 err(preview(program(rule([{op:'forEach',collection:'items',as:'item',steps:[]}])),s,{budget:{iterations:2}}),'iteration-limit');assert.equal(s.appearance.bloom,0);
});

test('an enormous program rejects before execution and budget cannot be raised',()=>{
 err(preview({version:1,rules:Array.from({length:33},(_,i)=>rule([],String(i)))},base()),'program-limit');err(preview(program(),base(),{budget:{operations:10000000}}),'budget');
});

test('stale preview and stale undo refuse without discarding later work',()=>{
 const s=base(),p=preview(program(rule([set('appearance.bloom',.8)])),s);s.content.title='new human text';err(apply(s,p),'stale-preview');assert.equal(s.appearance.bloom,0);
 const a=apply(s,preview(program(rule([set('appearance.bloom',.8)])),s));a.state.content.title='even newer';const u=undo(a.state,a.receipt);err(u,'stale-undo');assert.equal(u.state.content.title,'even newer');assert.equal(u.state.appearance.bloom,.8);
});

test('preview and undo handles are single-use and serialized forgeries refuse',()=>{
 const s=base(),p=preview(program(rule([set('appearance.bloom',.8)])),s);err(apply(s,structuredClone(p)),'proposal');const a=apply(s,p);err(apply(s,p),'proposal');assert.equal(undo(a.state,a.receipt).ok,true);err(undo(a.state,a.receipt),'receipt');
});

test('mutating public preview changes cannot alter retained writes',()=>{
 const s=base(),p=preview(program(rule([set('appearance.bloom',.8)])),s);p.changes[0].path='content.title';p.changes[0].after='tampered';const a=apply(s,p);assert.equal(a.state.appearance.bloom,.8);assert.equal(a.state.content.title,s.content.title);
});

test('type errors and result overflow are visible',()=>{
 err(preview(program(rule([set('appearance.bloom',['add','2',3])])),base()),'type');err(preview(program(rule([set('appearance.bloom',['mul',1e308,1e308])])),base()),'type');err(preview(program(rule([{op:'if',test:1,then:[]}])),base()),'type');
});

test('newly added world objects are selected by semantic fields on the next event',()=>{
 const s=base();s.controls.activeId='new';s.controls.dragX=47;s.controls.dragY=63;
 s.items.push({id:'new',role:'movable',x:0,y:0,style:{fill:'#9f8'}});
 const p=program({id:'drag-active',on:'drag',steps:[{op:'forEach',collection:'items',as:'object',where:['eq',['var','object.id'],['get','controls.activeId']],steps:[
  {op:'set',target:'object',path:'x',value:['clamp',['get','controls.dragX'],0,100]},
  {op:'set',target:'object',path:'y',value:['clamp',['get','controls.dragY'],0,100]}
 ]}]});
 const result=apply(s,preview(p,s,{event:'drag'}));assert.equal(result.ok,true);assert.deepEqual([result.state.items[3].x,result.state.items[3].y],[47,63]);assert.deepEqual(result.state.items.slice(0,3),s.items.slice(0,3));
});

test('a previously successful program refuses future invalid data without partial effects',()=>{
 const s=base();s.controls.denominator=2;
 const p=program(rule([set('content.title','evaluated'),set('appearance.bloom',['div',1,['get','controls.denominator']])]));
 assert.equal(preview(p,s).ok,true);
 s.controls.denominator=0;const failed=preview(p,s);err(failed,'division-zero');assert.deepEqual(failed.changes,[]);assert.equal(s.content.title,'An inhabited garden');assert.equal(p.rules[0].steps.length,2);
 delete s.controls.denominator;err(preview(p,s),'missing-path');assert.equal(s.appearance.bloom,0);
});
