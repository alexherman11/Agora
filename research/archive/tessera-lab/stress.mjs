import fs from 'node:fs';
import assert from 'node:assert/strict';
import {Engine,canonical,compose} from './engine.mjs';
import {load,permutations} from './check.mjs';
const report={checks:[],limitations:[]};
function test(name,fn) {try{fn();report.checks.push({name,ok:true});}catch(e){report.checks.push({name,ok:false,error:e.message});}}
const modules=load('trials/02-expedition');
const fresh=()=>new Engine(modules);
function call(e,action,args,ok=true,options={}) {const before=canonical(e.state),r=e.dispatch(action,args,options);assert.equal(r.ok,ok,canonical(r));if(!ok)assert.equal(canonical(e.state),before,'Refusal changed state');return r;}
test('All program orders produce the same complete dispatch and refund',()=>{
 const states=[];for(const order of permutations(modules)){const e=new Engine(order);call(e,'mission.dispatch',{id:'ridge',eventId:'a'});call(e,'mission.cancel',{id:'ridge',eventId:'b'});call(e,'mission.dispatch',{id:'coast',eventId:'c'});states.push(canonical(e.state));}assert.equal(new Set(states).size,1);
});
test('Two dispatches from the same snapshot cannot oversell in either arrival order',()=>{
 for(const order of [['ridge','coast'],['coast','ridge']]){const e=fresh(),expected={...e.versions};const a=call(e,'mission.dispatch',{id:order[0],eventId:'a'},true,{expected});const b=call(e,'mission.dispatch',{id:order[1],eventId:'b'},false,{expected});assert.equal(a.handlers.length,3);assert.equal(Object.keys(e.state.ledger).length,1);assert(e.state.stock.radio.available>=0);}
});
test('Counter deltas from two packing lines with the same SKU sum rather than overwrite',()=>{
 const e=fresh();call(e,'line.add',{id:'ridge-more',missionId:'ridge',sku:'radio',qty:1});call(e,'mission.dispatch',{id:'ridge',eventId:'a'});assert.equal(e.state.stock.radio.available,0);assert.equal(e.state.missions.ridge.charged,660);
});
test('Arbitrary new SKU participates without any renderer or reaction change',()=>{
 const e=new Engine([...modules,{id:'new-equipment',claims:[{kind:'seed',id:'stock/drone',values:{name:'Survey drone',available:2,unitCost:50}}]}]);
 call(e,'line.add',{id:'ridge-drone',missionId:'ridge',sku:'drone',qty:2});call(e,'mission.dispatch',{id:'ridge',eventId:'a'});assert.equal(e.state.stock.drone.available,0);assert.equal(e.state.missions.ridge.charged,640);call(e,'mission.cancel',{id:'ridge',eventId:'b'});assert.equal(e.state.stock.drone.available,2);assert.equal(e.state.projects.alpine.available,1000);
});
test('Duplicate event identity cannot partially reserve stock or spend funds',()=>{
 const e=fresh();call(e,'mission.dispatch',{id:'ridge',eventId:'same'});call(e,'mission.cancel',{id:'ridge',eventId:'same'},false);assert.equal(e.state.missions.ridge.status,'dispatched');
});
test('Different field stale edits commute; same field stale edits preserve a conflict',()=>{
 const e=new Engine(load('trials/01-workspace')),expected={...e.versions};call(e,'item.rename',{id:'welcome',title:'Writer A'},true,{expected});call(e,'notes.editBody',{id:'welcome',body:'Writer B'},true,{expected});call(e,'item.rename',{id:'welcome',title:'Writer C'},false,{expected});assert.equal(e.state.items.welcome.title,'Writer A');assert.equal(e.state.items.welcome.body,'Writer B');assert.equal(e.conflicts.at(-1).code,'stale-read-or-write');
});
test('Overlapping handler intent refuses atomically with both proposals',()=>{
 const extra={id:'conflicting-extension',claims:[{kind:'reaction',id:'conflicting.status',on:'mission.dispatch',effects:[{op:'set',collection:'missions',id:['arg','id'],field:'status',value:'cancelled'}]}]};
 const e=new Engine([...modules,extra]);const r=call(e,'mission.dispatch',{id:'ridge',eventId:'a'},false);assert.equal(r.conflict.code,'effect-conflict');assert.equal(r.conflict.detail.proposals.length,2);assert.equal(Object.keys(e.state.ledger??{}).length,0);
});
test('Disjoint authors may edit the same view; disagreement never uses file order',()=>{
 const xs=[{id:'layout',claims:[{kind:'view',id:'shared',widget:'panel'}]},{id:'copy',claims:[{kind:'view',id:'shared',title:'Hello'}]}];assert.equal(compose(xs).program.view.shared.title,'Hello');xs.push({id:'other-copy',claims:[{kind:'view',id:'shared',title:'Goodbye'}]});assert.equal(compose(xs).diagnostics[0].code,'claim-conflict');assert.equal(compose(xs).program.view.shared,undefined);
});
test('Same-priority styling disagreement stays visible, explicit precedence works',()=>{
 const xs=[{id:'s',claims:[{kind:'view',id:'x',widget:'panel',role:'card'},{kind:'style',id:'a',selector:'role:card',priority:1,values:{color:'red'}},{kind:'style',id:'b',selector:'role:card',priority:1,values:{color:'blue'}}]}];
 const e=new Engine(xs),s=e.styleFor(e.program.view.x);assert.equal(s.values.color,undefined);assert.equal(s.conflicts.length,1);xs[0].claims[2].priority=2;const e2=new Engine(xs);assert.equal(e2.styleFor(e2.program.view.x).values.color,'blue');
});
test('Missing structure targets and graph cycles are diagnosed',()=>{
 const e=new Engine([{id:'x',claims:[{kind:'view',id:'a',parent:'b',widget:'panel'},{kind:'view',id:'b',parent:'a',widget:'panel'},{kind:'view',id:'late',parent:'future',widget:'text'}]}]);assert.equal(e.diagnostics.filter(d=>d.code==='view-cycle').length,2);assert(e.diagnostics.some(d=>d.code==='missing-parent'));
});
test('Replay from persisted state preserves dispatch and exact refunds',()=>{
 const e=fresh();call(e,'mission.dispatch',{id:'ridge',eventId:'a'});const next=new Engine(modules,JSON.parse(JSON.stringify(e.snapshot())));call(next,'mission.cancel',{id:'ridge',eventId:'b'});assert.equal(next.state.projects.alpine.available,1000);assert.equal(next.state.stock.radio.available,3);
});
// A counterexample, recorded as a limitation rather than quietly making the test green.
{
 const extension={id:'late-editor',claims:[{kind:'action',id:'line.changeQty',effects:[{op:'set',collection:'lines',id:['arg','id'],field:'qty',value:['arg','qty']}]}]};
 const e=new Engine([...modules,extension]);call(e,'mission.dispatch',{id:'ridge',eventId:'a'});const edited=e.dispatch('line.changeQty',{id:'ridge-radio',qty:5});const cancelled=e.dispatch('mission.cancel',{id:'ridge',eventId:'b'});
 report.limitations.push({name:'New action bypasses planner-only lifecycle precondition',reproduced:edited.ok&&cancelled.ok&&e.state.stock.radio.available===6,excessStock:e.state.stock.radio.available-3,needed:'Transition invariant or immutable reservation snapshot independent of action name'});
}
report.ok=report.checks.every(x=>x.ok);fs.writeFileSync('evidence/stress-v1.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));if(!report.ok)process.exitCode=1;
