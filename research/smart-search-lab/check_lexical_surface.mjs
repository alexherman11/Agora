// New authorized interim-window contracts. No browser, filesystem fixtures or inference.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const source=await readFile(new URL('../kernel-lab/apps/smart-search/lexical.js',import.meta.url),'utf8');
const component=(await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'))).default;
class Element{
  constructor(tag,attrs={},kids=[]){Object.assign(this,{tag,attrs,children:kids,value:attrs.value||'',textContent:''});}
  append(...kids){this.children.push(...kids);}
  replaceChildren(...kids){this.children=kids;}
}
const node=(tag,attrs,...kids)=>new Element(tag,attrs,kids);
const all=n=>n instanceof Element?[n,...n.children.flatMap(all)]:[];
const settle=()=>new Promise(r=>setImmediate(r));
const hit={id:'ss1',rev:4,kind:'widget',name:'Larch',match:'title',snippet:'Untrusted capability text'};
function mount(rows){
  const reads=[],fires=[],cleanup=[],draft={query:'set ss1 sees=all'};
  const api={P:{node},part:(_,...args)=>node(...args),draft,Q:JSON.stringify,
    rows:async line=>{reads.push(line);return rows(line);},
    read:()=>{throw Error('Cached reads forbidden for fresh evidence');},
    fire:async(...args)=>fires.push(args),cleanup:fn=>cleanup.push(fn)};
  const root=component.mount(api);
  return {root,reads,fires,cleanup,draft,get:t=>all(root).find(n=>n.tag===t),
    button:label=>all(root).find(n=>n.tag==='button'&&n.children.includes(label))};
}
let checks=0;
const check=(label,fn)=>{fn();checks++;console.log('PASS '+label);};
{
  const ui=mount(async()=>[hit,{...hit,id:'ss2',kind:'grant'}, {...hit,id:'ss3',forgotten:true}]);
  await ui.get('form').onsubmit({preventDefault(){}});
  check('Enter quotes query as kernel search data and never acts',()=>{
    assert.deepEqual(ui.reads,['search "set ss1 sees=all" limit=50']);assert.deepEqual(ui.fires,[]);
    assert.equal(all(ui.root).filter(n=>n.attrs.class==='search-hit').length,1);
    assert(!ui.button('Open app'));
  });
  check('Honest capability, disconnected-source and incomplete-coverage copy',()=>{
    const copy=all(ui.root).flatMap(n=>[n.textContent,...n.children.filter(c=>typeof c==='string')]).join(' ');
    assert(copy.includes('does not verify requested capabilities'));
    for(const source of ['Email','Files','Web'])assert(copy.includes(source+': not connected'));
    assert.equal(ui.get('h1').children[0],'Search');
    assert(copy.includes('coverage is incomplete'));
  });
}
{
  const world={id:'ss2',rev:7,kind:'said',name:'Editor discussion',snippet:'We discussed image editing.'};
  const ui=mount(async()=>[hit,world]);
  await ui.get('form').onsubmit({preventDefault(){}});
  const titles=()=>all(ui.root).filter(n=>n.tag==='h2').map(n=>n.children[0].children[0]);
  check('Both Apps and World matches have clickable names',()=>{
    assert.deepEqual(titles(),['Larch','Editor discussion']);
    for(const name of titles())assert.equal(typeof ui.button(name).attrs.on.click,'function');
  });
  ui.get('select').value='World';ui.get('select').onchange();
  check('World filter retains discussion and draft without another request',()=>{
    assert.deepEqual(titles(),['Editor discussion']);assert.equal(ui.draft.source,'World');
    assert.equal(ui.reads.length,1);assert.deepEqual(ui.fires,[]);
  });
  ui.get('select').value='Apps';ui.get('select').onchange();
  check('Apps filter retains app evidence without claiming launch',()=>{
    assert.deepEqual(titles(),['Larch']);assert.deepEqual(ui.fires,[]);
  });
  await ui.button('Larch').attrs.on.click();
  check('Clicking a result name uses the same fresh evidence action',()=>{
    assert.deepEqual(ui.fires,[['evidence',{id:'ss1',saw:{ss1:4}}]]);
  });
}
for(const [label,current] of [
  ['revoked',[]],['changed',[{...hit,rev:5}]],['forgotten',[{...hit,forgotten:true}]],
  ['different identity',[{...hit,id:'ss9'}]],['kind changed',[{...hit,kind:'note'}]]
]){
  const ui=mount(async line=>line==='rows any'?current:[hit]);
  await ui.get('form').onsubmit({preventDefault(){}});
  await ui.button('View evidence').attrs.on.click();
  check(label+' evidence click performs no action',()=>assert.deepEqual(ui.fires,[]));
}
{
  const ui=mount(async()=>[hit]);
  await ui.get('form').onsubmit({preventDefault(){}});
  await ui.button('View evidence').attrs.on.click();
  await ui.button('View evidence').attrs.on.click();
  check('Every evidence click freshly rereads and fences exact revision',()=>{
    assert.equal(ui.reads.filter(r=>r==='rows any').length,2);
    assert.deepEqual(ui.fires,[['evidence',{id:'ss1',saw:{ss1:4}}],['evidence',{id:'ss1',saw:{ss1:4}}]]);
  });
}
{
  let finish;
  const ui=mount(()=>new Promise(r=>finish=r));
  const pending=ui.get('form').onsubmit({preventDefault(){}});
  ui.get('input').value='new query';ui.get('input').oninput();
  finish([hit]);await pending;
  check('Input edits invalidate outstanding results and preserve draft',()=>{
    assert.equal(ui.draft.query,'new query');assert(!ui.button('View evidence'));
  });
}
{
  let finish;
  const ui=mount(line=>line==='rows any'?new Promise(r=>finish=r):Promise.resolve([hit]));
  await ui.get('form').onsubmit({preventDefault(){}});
  const pending=ui.button('View evidence').attrs.on.click();
  await settle();ui.cleanup.forEach(fn=>fn());finish([hit]);await pending;
  check('Closed window cannot complete an in-flight evidence action',()=>assert.deepEqual(ui.fires,[]));
}
{
  const ui=mount(async line=>{if(line==='rows any')throw Error('read unavailable');return [hit];});
  await ui.get('form').onsubmit({preventDefault(){}});
  await ui.button('View evidence').attrs.on.click();
  check('Failed fresh reading never fires evidence action',()=>assert.deepEqual(ui.fires,[]));
}
check('Component contains no inference routes or capability certificates',()=>{
  assert(!/model\.(search|ask)|Open app|eligible\(|merge\(/.test(source));
});
console.log(`LEXICAL SURFACE CONTRACTS: ${checks}/${checks} passed (mock rows/actions; no browser or inference)`);
