/* Shared visual desk round 3: bounded data interpreter, not an Agora runtime.
 * No eval, Function, imports of host code, network, timers or DOM effects.
 * Every rule reads the same input state. Steps only build proposed writes.
 */
const HARD = Object.freeze({operations:8192, writes:256, iterations:512, depth:24, jsonNodes:20000, string:16384});
const proposals = new WeakMap();
const receipts = new WeakMap();
const forbidden = new Set(['__proto__','prototype','constructor']);
const arities = {get:[1,1],var:[1,1],lit:[1,1],add:[2,16],sub:[2,2],mul:[2,16],div:[2,2],min:[1,16],max:[1,16],clamp:[3,3],round:[1,1],abs:[1,1],eq:[2,2],ne:[2,2],gt:[2,2],gte:[2,2],lt:[2,2],lte:[2,2],and:[2,16],or:[2,16],not:[1,1],if:[3,3],concat:[1,16]};
class Problem extends Error {
  constructor(code,message,path,ruleId){super(message);Object.assign(this,{code,path,ruleId});}
}
const fail=(code,message,path,ruleId)=>{throw new Problem(code,message,path,ruleId);};
const clone=x=>JSON.parse(JSON.stringify(x));
function canonical(x){
  if(Array.isArray(x)) return '['+x.map(canonical).join(',')+']';
  if(x!==null&&typeof x==='object')return '{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}';
  return JSON.stringify(x);
}
function jsonCheck(x,label){
  let count=0; const ancestors=new Set();
  function visit(v,path,depth){
    if(++count>HARD.jsonNodes||depth>HARD.depth)fail('json-limit','JSON size or depth limit exceeded',path);
    if(v===null||typeof v==='boolean')return;
    if(typeof v==='string'){if(v.length>HARD.string)fail('string-limit','String too long',path);return;}
    if(typeof v==='number'){if(!Number.isFinite(v))fail('number','Number must be finite',path);return;}
    if(typeof v!=='object')fail('json','Expected JSON-compatible value',path);
    if(ancestors.has(v))fail('json','Cyclic value is not JSON',path);
    if(!Array.isArray(v)&&![Object.prototype,null].includes(Object.getPrototypeOf(v)))fail('json','Expected plain JSON object',path);
    ancestors.add(v);
    for(const key of Object.keys(v)){
      if(forbidden.has(key))fail('unsafe-key','Reserved object key',path+'.'+key);
      visit(v[key],path+'.'+key,depth+1);
    }
    ancestors.delete(v);
  }
  visit(x,label,0);
}
function parts(path,where){
  if(typeof path!=='string'||!path.length)fail('path','Expected nonempty dotted path',where);
  const tokens=path.split('.');
  if(tokens.some(p=>forbidden.has(p)||!/^([A-Za-z_][A-Za-z0-9_-]*|0|[1-9][0-9]*)$/.test(p)))fail('path','Unsafe or malformed path',where);
  return tokens;
}
function read(root,tokens,where){
  let value=root;
  for(const token of tokens){
    if(value===null||typeof value!=='object'||!Object.hasOwn(value,token))fail('missing-path','Missing path '+tokens.join('.'),where);
    value=value[token];
  }
  return value;
}
function write(root,path,value){const p=path.split('.');const leaf=p.pop();read(root,p,'apply')[leaf]=clone(value);}
function assertBool(v,path){if(typeof v!=='boolean')fail('type','Condition requires a boolean',path);return v;}
function assertNum(v,path){if(typeof v!=='number'||!Number.isFinite(v))fail('type','Arithmetic requires finite numbers',path);return v;}
function validate(program){
  if(!program||typeof program!=='object'||program.version!==1||!Array.isArray(program.rules))fail('program','Expected {version:1,rules:[]}','program');
  if(program.rules.length>32)fail('program-limit','At most 32 rules','rules');
  const ids=new Set();
  function expr(e,path){
    if(!Array.isArray(e)){if(e!==null&&!['string','number','boolean'].includes(typeof e))fail('expression','Use ["lit",value] for compound literal',path);return;}
    const [op,...args]=e;
    if(!Object.hasOwn(arities,op))fail('operator','Unknown expression operator '+String(op),path);
    const [min,max]=arities[op];if(args.length<min||args.length>max)fail('arity',op+' has wrong argument count',path);
    if(op==='get'||op==='var'){parts(args[0],path);return;}
    if(op!=='lit')args.forEach((arg,i)=>expr(arg,path+'['+(i+1)+']'));
  }
  function steps(xs,path){
    if(!Array.isArray(xs))fail('steps','Expected step array',path);
    xs.forEach((s,i)=>{
      const p=path+'['+i+']';if(!s||typeof s!=='object'||Array.isArray(s))fail('step','Expected step object',p);
      if(s.op==='set'){parts(s.path,p+'.path');if(s.target!==undefined)parts(s.target,p+'.target');expr(s.value,p+'.value');}
      else if(s.op==='let'){if(typeof s.name!=='string'||!/^[_A-Za-z][_A-Za-z0-9]*$/.test(s.name)||forbidden.has(s.name))fail('variable','Invalid local name',p);expr(s.value,p+'.value');}
      else if(s.op==='if'){expr(s.test,p+'.test');steps(s.then,p+'.then');steps(s.else??[],p+'.else');}
      else if(s.op==='forEach'){parts(s.collection,p+'.collection');if(typeof s.as!=='string'||!/^[_A-Za-z][_A-Za-z0-9]*$/.test(s.as)||forbidden.has(s.as))fail('variable','Invalid iteration variable',p);if(s.where!==undefined)expr(s.where,p+'.where');steps(s.steps,p+'.steps');}
      else fail('step','Unknown step '+String(s.op),p);
    });
  }
  program.rules.forEach((r,i)=>{
    const p='rules['+i+']';
    if(!r||typeof r!=='object'||typeof r.id!=='string'||!r.id||ids.has(r.id))fail('rule-id','Rule ids must be unique nonempty strings',p);
    ids.add(r.id);
    if(r.on!==undefined&&typeof r.on!=='string')fail('event','Rule on must be a string',p+'.on');
    if(r.when!==undefined)expr(r.when,p+'.when');steps(r.steps,p+'.steps');
  });
}
function errorResult(error,extras={}){
  const d={code:error.code??'internal',message:error.message,path:error.path??'program',...(error.ruleId?{ruleId:error.ruleId}:{})};
  return {ok:false,errors:['['+d.code+'] '+d.path+': '+d.message],diagnostics:[d],...extras};
}
export function preview(program,state,options={}){
  const stats={operations:0,iterations:0,matchedRules:0,writes:0};
  let ruleId;
  try{
    jsonCheck(program,'program');jsonCheck(state,'state');validate(program);
    const limits={};
    for(const name of ['operations','writes','iterations']){
      const wanted=options.budget?.[name]??HARD[name];
      if(!Number.isInteger(wanted)||wanted<1||wanted>HARD[name])fail('budget','Budget must be positive and no larger than '+HARD[name],'budget.'+name);
      limits[name]=wanted;
    }
    const tick=path=>{if(++stats.operations>limits.operations)fail('operation-limit','Execution budget exhausted',path,ruleId);};
    const pending=new Map();
    function evaluate(e,vars,path){
      tick(path);if(!Array.isArray(e))return e;
      const [op,...args]=e;
      if(op==='lit')return clone(args[0]);
      if(op==='get')return read(state,parts(args[0],path),path);
      if(op==='var')return read(vars,parts(args[0],path),path);
      if(op==='if'){const yes=assertBool(evaluate(args[0],vars,path+'[1]'),path);return evaluate(args[yes?1:2],vars,path+(yes?'[2]':'[3]'));}
      if(op==='and'){for(let i=0;i<args.length;i++)if(!assertBool(evaluate(args[i],vars,path+'['+(i+1)+']'),path))return false;return true;}
      if(op==='or'){for(let i=0;i<args.length;i++)if(assertBool(evaluate(args[i],vars,path+'['+(i+1)+']'),path))return true;return false;}
      const v=args.map((a,i)=>evaluate(a,vars,path+'['+(i+1)+']'));
      if(op==='eq'||op==='ne')return (canonical(v[0])===canonical(v[1]))===(op==='eq');
      if(op==='not')return !assertBool(v[0],path);
      if(op==='concat'){
        if(v.some(x=>x!==null&&!['string','number','boolean'].includes(typeof x)))fail('type','concat accepts scalar values',path);
        const text=v.map(String).join('');if(text.length>HARD.string)fail('string-limit','Computed string too long',path);return text;
      }
      v.forEach(x=>assertNum(x,path));let result;
      switch(op){
        case 'add':result=v.reduce((a,b)=>a+b,0);break;
        case 'sub':result=v[0]-v[1];break;
        case 'mul':result=v.reduce((a,b)=>a*b,1);break;
        case 'div':if(v[1]===0)fail('division-zero','Cannot divide by zero',path);result=v[0]/v[1];break;
        case 'min':result=Math.min(...v);break;
        case 'max':result=Math.max(...v);break;
        case 'clamp':if(v[1]>v[2])fail('range','Clamp minimum exceeds maximum',path);result=Math.min(v[2],Math.max(v[1],v[0]));break;
        case 'round':result=Math.round(v[0]);break;
        case 'abs':result=Math.abs(v[0]);break;
        case 'gt':return v[0]>v[1];case 'gte':return v[0]>=v[1];case 'lt':return v[0]<v[1];case 'lte':return v[0]<=v[1];
        default:fail('operator','Unknown operator',path);
      }
      return assertNum(result,path);
    }
    function gather(xs,vars,targets,path){
      xs.forEach((s,i)=>{
        const p=path+'['+i+']';tick(p);
        if(s.op==='let'){vars[s.name]=evaluate(s.value,vars,p+'.value');return;}
        if(s.op==='if'){const yes=assertBool(evaluate(s.test,vars,p+'.test'),p);gather(yes?s.then:(s.else??[]),{...vars},targets,p+(yes?'.then':'.else'));return;}
        if(s.op==='forEach'){
          const rows=read(state,parts(s.collection,p),p);if(!Array.isArray(rows))fail('type','forEach collection must be an array',p);
          rows.forEach((row,index)=>{
            if(++stats.iterations>limits.iterations)fail('iteration-limit','Iteration budget exhausted',p,ruleId);
            const inner={...vars,[s.as]:row};
            if(s.where!==undefined&&!assertBool(evaluate(s.where,inner,p+'.where'),p))return;
            gather(s.steps,inner,{...targets,[s.as]:s.collection+'.'+index},p+'.steps');
          });return;
        }
        if(++stats.writes>limits.writes)fail('write-limit','Write budget exhausted',p,ruleId);
        if(s.target!==undefined&&!Object.hasOwn(targets,s.target))fail('target','Unknown iteration target '+s.target,p);
        const address=(s.target?targets[s.target]+'.':'')+s.path;
        const before=read(state,parts(address,p),p);
        const after=evaluate(s.value,vars,p+'.value');jsonCheck(after,p+'.value');
        for(const old of pending.keys())if(old!==address&&(old.startsWith(address+'.')||address.startsWith(old+'.')))fail('overlapping-write','Parent and child writes overlap: '+old+' / '+address,p,ruleId);
        const prior=pending.get(address);
        if(prior&&canonical(prior.after)!==canonical(after))fail('write-conflict','Rules propose different values for '+address+' ('+prior.ruleIds.join(', ')+' / '+ruleId+')',p,ruleId);
        if(prior){if(!prior.ruleIds.includes(ruleId))prior.ruleIds.push(ruleId);prior.origins.push(p);}
        else pending.set(address,{path:address,before:clone(before),after:clone(after),ruleIds:[ruleId],origins:[p]});
      });
    }
    program.rules.forEach((r,index)=>{
      ruleId=r.id;if(r.on!==undefined&&r.on!==(options.event??'run'))return;
      const vars=Object.create(null);
      if(r.when!==undefined&&!assertBool(evaluate(r.when,vars,'rules['+index+'].when'),'rules['+index+'].when'))return;
      stats.matchedRules++;gather(r.steps,vars,Object.create(null),'rules['+index+'].steps');
    });
    const changes=[...pending.values()].filter(c=>canonical(c.before)!==canonical(c.after));
    const result={ok:true,errors:[],diagnostics:[],changes:clone(changes),stats};
    proposals.set(result,{base:canonical(state),before:clone(state),changes:clone(changes)});
    return result;
  }catch(error){if(ruleId&&!error.ruleId)error.ruleId=ruleId;return errorResult(error,{changes:[],stats});}
}
export function apply(state,proposal){
  try{
    jsonCheck(state,'state');const p=proposals.get(proposal);
    if(!p)fail('proposal','Apply requires a successful live preview object','proposal');
    if(canonical(state)!==p.base)fail('stale-preview','State changed since preview; preview again','state');
    const next=clone(state);for(const c of p.changes)write(next,c.path,c.after);
    const receipt={changes:clone(p.changes),summary:p.changes.length+' field(s) changed'};
    receipts.set(receipt,{before:p.before,after:canonical(next)});
    proposals.delete(proposal);
    return {ok:true,state:next,receipt,errors:[],diagnostics:[]};
  }catch(error){return errorResult(error,{state});}
}
export function undo(state,receipt){
  try{
    jsonCheck(state,'state');const r=receipts.get(receipt);
    if(!r)fail('receipt','Undo requires a live, uncompensated receipt','receipt');
    if(canonical(state)!==r.after)fail('stale-undo','State changed since apply; this prototype refuses whole-state undo','state');
    receipts.delete(receipt);return {ok:true,state:clone(r.before),errors:[],diagnostics:[]};
  }catch(error){return errorResult(error,{state});}
}
export const limits=HARD;
