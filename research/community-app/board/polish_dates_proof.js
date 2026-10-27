// No DOM, network, model or wall-clock-dependent assertions.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const P=vm.runInNewContext(fs.readFileSync('research/kernel-lab/painter/primitives.js','utf8')+';P',{theme:{},css(){},Date,Intl});
const monday=new Date(2026,9,26,12);
for(const [input,weekday,hour,minute] of [['Thu 6pm',4,18,0],['tomorrow 9:30am',2,9,30],['today 12am',1,0,0],['2026-11-04 18:00',3,18,0]]){
  const result=P.parseDateEntry(input,monday);assert(result.ok,input);const date=new Date(result.iso);assert.equal(date.getDay(),weekday);assert.equal(date.getHours(),hour);assert.equal(date.getMinutes(),minute);assert(result.label.includes('2026'));
}
for(const input of ['Feb 31','2026-02-30 12:00','Thu 29pm','tomorrow 9:99am','sometime soon'])assert(!P.parseDateEntry(input,monday).ok,input);
assert.equal(P.formatValue('Neighbour 02','initials'),'N');assert.equal(P.formatValue('Maya Lopez','initials'),'ML');
const today=new Date(2026,9,26,18);assert.equal(P.formatValue(new Date(2026,9,26,16),'short-relative',today),'2h');
console.log('POLISH DATES: 12/12 checks passed; local=True; model=False');
