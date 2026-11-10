// Non-browser behaviour checks: actual component handlers, an in-memory DOM adapter.
// This does not establish layout, native selection, focus or browser interaction outcomes.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const lab=path.resolve(__dirname,'../../agora');
class Element{
  constructor(tag){this.tagName=tag;this.nodeType=1;this.children=[];this.attrs={};this.listeners={};this.style={setProperty(k,v){this[k]=v}};this.dataset={};this.value='';this.hidden=false;this.disabled=false;
    this.classList={add:()=>{},remove:()=>{},toggle:()=>{},contains:()=>false};}
  setAttribute(k,v){this.attrs[k]=String(v);if(k==='value')this.value=String(v);if(k==='hidden'||k==='disabled')this[k]=true}
  getAttribute(k){return this.attrs[k]}
  get lastChild(){return this.children.at(-1)} get firstChild(){return this.children[0]}
  append(...xs){for(const x of xs.flat()){if(x==null||x===false)continue;if(x instanceof Element){x.remove();x.parentNode=this}this.children.push(x)}}
  appendChild(x){this.append(x);return x}
  remove(){if(this.parentNode){const a=this.parentNode.children;a.splice(a.indexOf(this),1);this.parentNode=null}}
  replaceChildren(...xs){for(const x of this.children)if(x instanceof Element)x.parentNode=null;this.children=[];this.append(...xs)}
  insertBefore(x,before){x.remove();const i=this.children.indexOf(before);if(i<0)throw Error('missing insertion target');this.children.splice(i,0,x);x.parentNode=this}
  set textContent(x){this.replaceChildren(String(x))}
  get textContent(){return this.children.map(x=>x instanceof Element?x.textContent:String(x)).join('')}
  addEventListener(k,f){(this.listeners[k]??=[]).push(f)}
  removeEventListener(){}
  async event(k,extra={}){const e={target:this,currentTarget:this,preventDefault(){},stopPropagation(){},...extra};await Promise.all((this.listeners[k]||[]).map(f=>f(e)));if(this['on'+k])await this['on'+k](e)}
  async click(){if(!this.disabled)await this.event('click')}
  focus(){this.focused=true} scrollIntoView(){this.scrolled=true}
  setCustomValidity(){} getBoundingClientRect(){return {height:118,left:0,top:0,width:390}}
  querySelectorAll(q){return descendants(this).filter(x=>q[0]==='.'?(x.attrs.class||'').split(' ').includes(q.slice(1)):q==='input[name]'?x.tagName==='input'&&x.attrs.name:x.tagName===q)}
  querySelector(q){return this.querySelectorAll(q)[0]||null}
}
function descendants(n){return n.children.filter(x=>x instanceof Element).flatMap(x=>[x,...descendants(x)])}
function node(tag,attrs={},...kids){const n=new Element(tag);for(const [k,v]of Object.entries(attrs)){if(v==null||v===false)continue;if(k==='on')for(const [e,fn]of Object.entries(v))n.addEventListener(e,fn);else if(k==='style')Object.assign(n.style,v);else n.setAttribute(k,v)}n.append(...kids);return n}
const document={createElement:tag=>node(tag),createTextNode:s=>String(s),addEventListener(){},removeEventListener(){}};
const ctx={theme:{},el:node,css(){},document,console,Date,Intl,Map,Set,performance,setTimeout,clearTimeout,requestAnimationFrame:f=>f(),innerWidth:1440,innerHeight:900};
const feedbackHost={entries:new Map(),scopes:new Map(),listeners:new Set(),serial:0};
ctx[Symbol.for('agora.action-feedback.v2')]=feedbackHost;
const P=vm.runInNewContext(fs.readFileSync(path.join(lab,'painter/primitives.js'),'utf8')+'\nP',ctx);
P.selectionAction=(content,draft,key,activate)=>({quote:()=>activate('Exact passage'),dispose(){}});
P.overlay=(kind,body)=>({node:body,close(){}});P.submit=(form,fn)=>form.addEventListener('submit',fn);
function component(file,extra={}){return vm.runInNewContext(fs.readFileSync(file,'utf8').replace('export default','const component =')+'\nObject.assign(component,typeof actionFeedback==="function"?{feedback:actionFeedback,wrap:feedbackAPI}:{})',{...ctx,...extra})}
function api(kind,extra={}){
  let state={};const calls=[],draft={};
  return {P,node:{component:kind,path:'root/test',gestures:[]},facts:{},draft,children:[],calls,
    label:(k,f)=>f,display:()=>'',view:()=>state,select:async values=>{state={...state,...values}},guard:f=>f,cleanup(){},tell(){},
    part:(part,tag,attrs,...kids)=>{const n=node(tag,attrs,...kids);n.part=part;return n},
    fire:async(event,values)=>{calls.push({event,values});return {made:['new-thread']}},
    read:async()=>[],rows:async()=>[{id:'post1',rev:7}],format:(k,v)=>v,render:()=>node('div'),
    requestAnimationFrame:f=>f(),...extra};
}
function part(root,name){return [root,...descendants(root)].find(n=>n.part===name)}
function button(root,text){return descendants(root).find(n=>n.tagName==='button'&&n.textContent===text)}
const tick=()=>new Promise(resolve=>setImmediate(resolve));


module.exports={fs,path,vm,assert,lab,Element,descendants,node,ctx,P,component,api,part,button,tick};
