// Actual lens.js handlers under a minimal controlled DOM/transport, not browser evidence.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const source=readFileSync(new URL('../../../text-desk-lab/notation/desk-shell/lens.js',import.meta.url),'utf8');
class Element {
 constructor(){this.textContent='';this.style={};this.dataset={};this.children=[];this.handlers=new Map();this.classList={add(){}};}
 addEventListener(k,f){this.handlers.set(k,[...(this.handlers.get(k)||[]),f]);}
 removeEventListener(k,f){this.handlers.set(k,(this.handlers.get(k)||[]).filter(x=>x!==f));}
 appendChild(e){this.children.push(e);}
 replaceChildren(...es){this.children=es;}
 setPointerCapture(){}
 fire(k,event={}){for(const f of this.handlers.get(k)||[])f(event);}
}
const scene=(acts,text='original')=>({role:null,layout:null,box:[0,0,100,100],item:'a1',text,clamp:null,acts,kids:[]});
async function harness(initial){
 const paint=new Element(),said=new Element(),requests=[];let response={scene:initial,text:'scene fixture'},poll;
 const context=vm.createContext({URLSearchParams,location:{search:''},document:{getElementById:id=>id==='paint'?paint:said,createElement:()=>new Element()},Style:{install(){},roleClass:x=>x},setInterval:fn=>{poll=fn;},fetch:async(url,options)=>{
  if(url==='style/calm.style')return{text:async()=>''};
  if(url==='/api/do'){requests.push(JSON.parse(options.body));return{json:async()=>({text:'ok'})};}
  return{json:async()=>response};
 }});
 await vm.runInContext(source,context);
 return{paint,said,requests,element:paint.children[0],poll:()=>poll(),setResponse:r=>{response=r;}};
}
const edit=[{on:'edit',line:'do rewrite a1 text="$value"'}];
let count=0;
async function check(name,fn){await fn();count++;console.log('PASS counterexample '+name);}
await check('edit destroys leading/trailing whitespace and double quotes',async()=>{
 const h=await harness(scene(edit));h.element.fire('focus');h.element.textContent='  print("hi")  ';h.element.fire('blur');
 assert.equal(h.requests[0].line,'look a1; do rewrite a1 text="print(\'hi\')"');
});
await check('empty string deletion emits no command',async()=>{
 const h=await harness(scene(edit));h.element.fire('focus');h.element.textContent='';h.element.fire('blur');assert.equal(h.requests.length,0);
});
await check('replacement metacharacter dollar ampersand corrupts literal input',async()=>{
 const h=await harness(scene(edit));h.element.textContent='a$&b';h.element.fire('blur');assert.equal(h.requests[0].line,'look a1; do rewrite a1 text="a$valueb"');
});
await check('declared drop action has no installed listener',async()=>{
 const h=await harness(scene([{on:'drop',line:'do link a1 $other'}]));assert.equal(h.element.handlers.has('drop'),false);
});
await check('drag installs no pointercancel handler and leaves refresh blocked',async()=>{
 const h=await harness(scene([{on:'drag',line:'do move a1 to=$x,$y'}]));h.element.fire('pointerdown',{target:h.element,pointerId:1,clientX:0,clientY:0});
 assert.equal(h.element.handlers.has('pointercancel'),false);h.setResponse({scene:scene([], 'new scene'),text:'new scene'});await h.poll();assert.equal(h.paint.children[0].textContent,'original');
});
await check('a refused lens removes previous working picture',async()=>{
 const h=await harness(scene([]));assert.equal(h.paint.children.length,1);h.setResponse({refused:'bad candidate lens'});await h.poll();assert.equal(h.paint.children.length,0);assert.match(h.said.textContent,/refused/);
});
console.log(`${count} source-handler counterexamples reproduced. No browser, HTTP, live desk, or source modification.`);
