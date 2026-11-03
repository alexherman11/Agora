// New in-memory component contract checks, no browser, temp files or live desktop.
// Mock readings exercise UI plumbing only; they do not establish semantic quality.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const source=await readFile(new URL('../kernel-lab/apps/smart-search/search.js',import.meta.url),'utf8');
const component=(await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'))).default;
class Element {
  constructor(tag,attrs={},kids=[]){this.tag=tag;this.attrs=attrs;this.children=kids;this.value=attrs.value||'';this.disabled=false;this.textContent='';}
  append(...kids){this.children.push(...kids);}
  replaceChildren(...kids){this.children=kids;}
}
const all=(node)=>node instanceof Element?[node,...node.children.flatMap(all)]:[];
const node=(tag,attrs,...kids)=>new Element(tag,attrs,kids);
let checks=0;
const check=(label,fn)=>{fn();checks++;console.log('PASS '+label);};
const row={id:'ss1',rev:4,title:'Larch',text:'Synthetic descriptor',source:'Apps',match:'lexical',evidence:'Synthetic evidence',app:'larch'};
const response={state:'Exact words',hits:[row],coverage:[{source:'Web',state:'Not connected'}],constraints:[]};
function mount(read){
  const calls=[],draft={query:'delete old photos'},cleanup=[];
  const api={P:{node},part:(_name,...args)=>node(...args),draft,Q:JSON.stringify,
    read,fire:async(...args)=>calls.push(args),cleanup:fn=>cleanup.push(fn)};
  const root=component.mount(api);
  const get=tag=>all(root).find(n=>n.tag===tag);
  const button=label=>all(root).find(n=>n.tag==='button'&&n.children.includes(label));
  return {root,get,button,calls,draft,cleanup};
}
{
  const modes=[];
  const ui=mount(async line=>{modes.push(line.match(/mode=(\w+)/)[1]);return [response];});
  await ui.get('form').onsubmit({preventDefault(){}});
  await new Promise(r=>setImmediate(r));
  check('Enter submits lexical then semantic, never executes query',()=>{
    assert.deepEqual(modes,['lexical','semantic']);assert.deepEqual(ui.calls,[]);
  });
  check('Coverage labels disconnected Web',()=>{
    assert(all(ui.root).some(n=>n.textContent.includes('Web · Not connected')));
  });
}
{
  const modes=[];
  const ui=mount(async line=>{modes.push(line.match(/mode=(\w+)/)[1]);return [response];});
  await ui.button('Exact words only').onclick();
  check('Exact mode requests no inference',()=>assert.deepEqual(modes,['lexical']));
}
{
  let finish;
  const ui=mount(line=>line.includes('mode=lexical')?Promise.resolve([response]):new Promise(r=>{finish=r;}));
  const pending=ui.get('form').onsubmit({preventDefault(){}});
  // Event handlers intentionally return void in browsers; settle microtasks.
  await new Promise(r=>setImmediate(r));
  const input=ui.get('input');input.value='new private query';input.oninput();
  finish([{...response,state:'STALE'}]);
  await new Promise(r=>setImmediate(r));
  check('Input edits invalidate in-flight results',()=>{
    assert(!all(ui.root).some(n=>n.textContent.includes('STALE')));
    assert.equal(ui.draft.query,'new private query');
    assert(!all(ui.root).some(n=>n.attrs.class==='search-hit'));
  });
}
{
  const ui=mount(async line=>line.includes('mode=check')?[]:[response]);
  ui.get('form').onsubmit({preventDefault(){}});
  await new Promise(r=>setImmediate(r));
  await ui.button('View evidence').attrs.on.click();
  check('Revoked or stale click performs no action',()=>assert.deepEqual(ui.calls,[]));
}
{
  const ui=mount(async line=>line.includes('mode=check')?[{id:'ss1',rev:4,app:'larch'}]:[response]);
  ui.get('form').onsubmit({preventDefault(){}});
  await new Promise(r=>setImmediate(r));
  await ui.button('Open app').attrs.on.click();
  check('App action carries exact source revision fence',()=>{
    assert.deepEqual(ui.calls,[['app',{app:'larch',saw:{ss1:4}}]]);
  });
}
console.log(`SURFACE CONTRACTS: ${checks}/${checks} passed (mock readings, no inference or browser)`);
