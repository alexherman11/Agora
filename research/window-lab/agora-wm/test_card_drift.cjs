// Async lifetime checks only. This does not replace the hidden browser proof.
const assert=require('node:assert/strict');
const {drift}=require('../../text-desk-lab/notation/desk-shell/carry-targets.js');
global.getComputedStyle=()=>({rowGap:'0'});
function element(x,y){
  return {style:{transform:''},parentElement:{},contains:()=>false,
    getBoundingClientRect(){const dy=Number(/translateY\(([-.\d]+)px\)/.exec(this.style.transform)?.[1]||0);return {x,y:y+dy,width:200,height:160}},
    animate(){return {cancel(){}}}};
}
const source=element(0,0),card=element(300,0);
const lane={getBoundingClientRect:()=>({x:300,y:0,width:200,height:600}),querySelectorAll:()=>[card]};
card.parentElement=lane;
const pointer=x=>({clientX:x,clientY:20,startX:50,startY:20});
const yes={allowed:true,landing:[300,0,200,160],placements:[[300,160,200,160]],motion_ms:250};
(async()=>{
  const pending=[];let calls=0,painted=0;
  const d=drift(source,'x',()=>{calls++;return new Promise(resolve=>pending.push(resolve))});
  d.move(lane,pointer(351),()=>painted++);
  d.move(lane,pointer(352),()=>painted++);
  assert.equal(calls,1,'one outstanding geometry read');
  pending.shift()(yes);
  await new Promise(setImmediate);
  assert.equal(painted,0,'old response cannot repaint a newer hand position');
  assert.equal(calls,2,'latest position is requested after the old response');
  pending.shift()(yes);await d.flush();
  assert.equal(card.style.transform,'translateY(160px)');
  assert.equal(painted,1);
  d.move(null);
  assert.equal(card.style.transform,'','leaving a receiver restores its cards');
  d.move(lane,pointer(351),()=>painted++);
  d.close();pending.shift()(yes);await d.flush();
  assert.equal(card.style.transform,'','late result after cancel cannot displace a card');
  assert.equal(painted,1);
  const order=tie=>({keys:['priority'],values:[[0,2,'']],tie});
  source._n={tiling_order:order(0)};card._n={tiling_order:order(1)};
  let geometry;
  const sorted=drift(source,'x',async body=>{geometry=body;return {...yes,motion_ms:420}});
  sorted.move(lane,{...pointer(351),clientY:500});await sorted.flush();
  assert.equal(geometry.neighbours.length,1,'sorted lane sends all cards, not a pointer-selected suffix');
  assert.deepEqual(geometry.orders,[source._n.tiling_order,card._n.tiling_order]);
  assert.equal(sorted.duration,420,'motion follows the world setting returned by the host');
  sorted.close(true);
  assert.equal(card.style.transform,'','handoff clears temporary transforms before final layout');
  console.log('card drift lifetime: 12 checks passed');
})().catch(e=>{console.error(e);process.exitCode=1});
