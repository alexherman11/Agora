// Exercises the production startup block with refused event hints. No browser paint claim.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(path.join(__dirname,'../../agora/painter/painter.js'),'utf8');
const block=source.slice(source.indexOf('const subscriptionFailures=[];'),source.indexOf('// A forgotten/private target'));
const views=source.slice(source.indexOf('async function hearViews()'),source.indexOf('// The theme changed'));
(async()=>{
  for(const refuses of [[],['make'],['make','set','forget','undo','component','component-action'],['view'],['make','set','forget','undo','component','component-action','view']]){
    const attempted=[],events=[],pendingObservations=new Map();
    const context={pendingObservations,currentPlan:{tree:{path:'root'}},console:{warn:()=>events.push('warning')},
      hearMotion:async word=>{attempted.push(word);if(refuses.includes(word))throw Error('no grant to hear '+word)},
      agora:{hear:async word=>{events.push('views');if(refuses.includes(word))throw Error('no grant to hear '+word)}},refresh:async()=>events.push('paint'),
      flushObservations:async()=>events.push('health')};
    await vm.runInNewContext('(async()=>{'+views+block+'})()',context);
    assert.equal(attempted.length,6);assert.ok(events.includes('paint'));
    assert.equal(pendingObservations.size,refuses.length?1:0);
    if(refuses.length){const report=pendingObservations.get('root');assert.equal(report.health,'healthy');assert.match(report.last_error,/Live updates limited/);assert.ok(events.indexOf('paint')<events.indexOf('health'))}
    console.log('PASS startup: '+refuses.length+' refused hints; paint still reached');
  }
  console.log('ROUND2 PAINTER CHECKS 5');
})().catch(e=>{console.error(e);process.exitCode=1});
