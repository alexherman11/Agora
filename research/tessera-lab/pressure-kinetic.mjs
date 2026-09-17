import assert from 'node:assert/strict';
import fs from 'node:fs';
import {Engine,canonical} from './engine.mjs';
import {load,permutations} from './check.mjs';
import {PulseRunner} from './pulses.mjs';
const modules=load('trials/05-kinetic-loom');
const report={checks:[],benchmarks:[]};
const pass=name=>report.checks.push(name);
const select=ids=>modules.map(m=>({...m,claims:m.id==='base'||ids.includes(m.id)?m.claims:m.claims.filter(c=>c.kind==='field')}));
const base=new Engine(modules),snap=base.snapshot(),ember=base.state.bodies.ember;
assert(base.dispatch('sim.step',{dt:.05}).ok);
const dx=500-ember.x,dy=320-ember.y,denom=Math.max(6400,dx*dx+dy*dy);
assert(Math.abs(base.state.bodies.ember.vx-(ember.vx-.12*.05*ember.vx+.05*9000*dx/denom))<1e-9);
pass('Friction and attraction add on the same velocity field from one pre-step snapshot');
for(const order of permutations(modules)){
 const e=new Engine(order);for(let i=0;i<30;i++)assert(e.dispatch('sim.step',{dt:.05}).ok);
 report.reference??=canonical(e.state);assert.equal(canonical(e.state),report.reference);
}
delete report.reference;pass('24 module orders produce identical composed trajectories over 30 steps');
const authors=['motion','field','instrument'];
for(let mask=0;mask<8;mask++){
 const ids=authors.filter((_,i)=>mask&(1<<i)),fresh=new Engine(select(ids)),retired=new Engine(select(ids),snap);
 assert(fresh.dispatch('sim.step',{dt:.05}).ok);const retiredResult=retired.dispatch('sim.step',{dt:.05});assert(retiredResult.ok,canonical(retiredResult));
 const restored=new Engine(modules,retired.snapshot());assert.equal(Object.keys(restored.state.bodies).length,16);
 assert.deepEqual(restored.state.bodies,retired.state.bodies);
}
pass('All 8 active-author subsets admit; withdraw/restore preserves bodies and current state');
for(const order of permutations(authors)){
 let e=new Engine(select([]));const arrived=[];
 for(const id of order){arrived.push(id);e=new Engine(select(arrived),e.snapshot());}
 assert.equal(canonical(e.state),canonical(snap.state));
}
pass('All 6 incremental author arrival orders converge to the same initial state');
const e=new Engine(modules),clock=new PulseRunner();clock.pump(e,0);assert.equal(e.serial,0);
assert(e.dispatch('instrument.start').ok);clock.pump(e,0);assert.equal(clock.pump(e,49),null);
assert(clock.pump(e,50).result.ok);assert.equal(e.state.simulation.main.steps,1);
clock.pump(e,10000);assert.equal(e.state.simulation.main.steps,2);pass('One due step per wake; delayed clocks do not create catch-up bursts');
assert(e.dispatch('instrument.pause').ok);clock.pump(e,10001);clock.pump(e,20000);assert.equal(e.state.simulation.main.steps,2);
pass('Pause stops authoritative simulation mutations');
const bad={id:'adversary',claims:[{kind:'reaction',id:'adversary.step',on:'sim.step',effects:[{op:'set',collection:'bodies',id:'ember',field:'x',value:1}]}]};
const blocked=new Engine([...modules,bad]),blockedClock=new PulseRunner();blocked.dispatch('instrument.start');blockedClock.pump(blocked,0);
assert.equal(blockedClock.pump(blocked,50).result.ok,false);const serial=blocked.serial;
assert.equal(blockedClock.pump(blocked,100),null);assert.equal(blocked.serial,serial);assert.equal(blocked.conflicts.length,1);
pass('Conflicting contributed pulse effects refuse atomically and stop retrying');
for(const count of [20,80,160,200]){
 const extras={id:'load-fixture',claims:Array.from({length:count-16},(_,i)=>({kind:'seed',id:`bodies/load-${i}`,values:{label:`Load ${i}`,x:(i*137)%1000,y:(i*79)%640,vx:20,vy:15}}))};
 const engine=new Engine([...modules,extras]),times=[];let result;
 for(let i=0;i<30;i++){const start=performance.now();result=engine.dispatch('sim.step',{dt:.05});times.push(performance.now()-start);if(!result.ok)break;}
 times.sort((a,b)=>a-b);report.benchmarks.push({bodies:count,samples:times.length,p50Ms:times[Math.floor(times.length*.5)],p95Ms:times[Math.min(times.length-1,Math.floor(times.length*.95))],ok:result.ok,limit:result.ok?null:result.conflict});
}
report.ok=true;fs.writeFileSync('evidence/trial05-pressure.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
