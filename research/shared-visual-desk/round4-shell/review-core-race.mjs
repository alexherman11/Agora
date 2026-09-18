// Runs Claude's unchanged core.js functions in a VM with controlled fetch.
// No HTTP, browser, desk state, or live-world mutation occurs.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const source = readFileSync(new URL('../../text-desk-lab/notation/desk-shell/core.js',import.meta.url),'utf8');
const requests=[];
const context=vm.createContext({URLSearchParams,location:{search:'?session=fixture&as=media'},fetch:(url)=>new Promise(resolve=>requests.push({url,resolve})),console});
vm.runInContext(source+'\n globalThis.reviewDesk=Desk;',context);
const desk=context.reviewDesk, observed=[];
desk.on(snapshot=>observed.push(snapshot.events_total));
const first=desk.refresh();
const second=desk.refresh();
assert.equal(requests.length,2);
const snapshot=n=>({events_total:n,nodes:{},subjects:{},links:[]});
requests[1].resolve({json:async()=>snapshot(11)});
await second;
assert.equal(desk.snapshot.events_total,11);
requests[0].resolve({json:async()=>snapshot(10)});
await first;
assert.deepEqual(observed,[11,10]);
assert.equal(desk.snapshot.events_total,10);
console.log('PASS counterexample: concurrent core refresh delivered observations 11 then10 and retained stale snapshot10.');
console.log('Controlled-fetch source execution only; no claim this schedule was observed in the live browser.');
