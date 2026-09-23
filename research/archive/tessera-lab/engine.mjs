// Tessera interpreter: unordered program claims, pure queries, atomic effect joins.
// Generated programs are data; this module never evaluates source strings.
export const clone = x => structuredClone(x);
export const canonical = x => JSON.stringify(normalize(x));
function normalize(x) {
  if (Array.isArray(x)) return x.map(normalize);
  if (x && typeof x === 'object') return Object.fromEntries(Object.keys(x).sort().map(k => [k, normalize(x[k])]));
  return x;
}
const equal = (a,b) => canonical(a) === canonical(b);
const kinds = new Set(['field','seed','query','derive','action','reaction','view','style','constraint','gesture','pulse']);
const cell = (c,id,f) => `${c}/${id}/${f}`;
const safe = s => typeof s === 'string' && s.length > 0 && !['__proto__','prototype','constructor'].includes(s);
// Open contributions may arrive independently. Unresolved behavior is retained as
// dormant data; mandatory constraints are never silently removed by this pass.
function closeDependencies(program,diagnostics){
  const dormant={},references=new Map();
  const walk=(value,refs)=>{
    if(Array.isArray(value)){
      if(value[0]==='lit')return;
      if(value[0]==='use'||value[0]==='query')refs.add(`${value[0]==='use'?'derive':'query'}:${value[1]}`);
      for(const child of value)walk(child,refs);
    }else if(value&&typeof value==='object')for(const child of Object.values(value))walk(child,refs);
  };
  for(const kind of ['query','derive','action','reaction','view','style','gesture','pulse'])for(const claim of Object.values(program[kind])){
    const refs=new Set();walk(claim,refs);
    if(kind==='view'&&claim.query)refs.add(`query:${claim.query}`);
    if(kind==='pulse')refs.add(`action:${claim.action}`);
    if(kind==='reaction')refs.add(`action:${claim.on}`);
    if(kind==='gesture'&&claim.commit)refs.add(`action:${claim.commit.action}`);
    references.set(`${kind}:${claim.id}`,refs);
  }
  const exists=address=>{const split=address.indexOf(':'),kind=address.slice(0,split),id=address.slice(split+1);return !!program[kind]?.[id];};
  while(true){
    const missing=[...references].filter(([address])=>exists(address)).map(([address,refs])=>({address,missing:[...refs].filter(ref=>!exists(ref)).sort()})).filter(x=>x.missing.length);
    if(!missing.length)break;
    for(const item of missing){const split=item.address.indexOf(':'),kind=item.address.slice(0,split),id=item.address.slice(split+1);dormant[item.address]=program[kind][id];delete program[kind][id];diagnostics.push({code:'dormant-dependency',...item});}
  }
  return dormant;
}
export function compose(modules) {
  const groups = new Map(), diagnostics = [], provenance = {};
  for (const mod of modules) {
    if (!safe(mod.id) || !Array.isArray(mod.claims)) throw Error('Module requires id and claims');
    for (const claim of mod.claims) {
      if (!kinds.has(claim.kind) || !safe(claim.id)) throw Error(`Invalid claim in ${mod.id}`);
      const key = `${claim.kind}:${claim.id}`;
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push({author:mod.id, claim});
    }
  }
  const program = Object.fromEntries([...kinds].map(k => [k,{}]));
  for (const [address, entries] of [...groups].sort(([a],[b]) => a.localeCompare(b))) {
    const {kind,id} = entries[0].claim, values = {}, authors = new Set();
    let blocked = false;
    const props = new Map();
    for (const {author,claim} of entries) {
      authors.add(author);
      for (const [key,value] of Object.entries(claim)) {
        if (key === 'kind' || key === 'id') continue;
        const parts = key === 'values' ? Object.entries(value).map(([k,v]) => [`values.${k}`,v]) : [[key,value]];
        for (const [p,v] of parts) {
          if (!props.has(p)) props.set(p,[]);
          props.get(p).push({author,value:v});
        }
      }
    }
    for (const [prop, claims] of [...props].sort(([a],[b]) => a.localeCompare(b))) {
      const unique = [...new Map(claims.map(c => [canonical(c),c])).values()].sort((a,b) => canonical(a).localeCompare(canonical(b)));
      provenance[`${address}.${prop}`] = unique;
      if (new Set(claims.map(c => canonical(c.value))).size > 1) {
        diagnostics.push({code:'claim-conflict',address,property:prop,claims:unique}); blocked = true; continue;
      }
      if (prop.startsWith('values.')) (values.values ??= {})[prop.slice(7)] = clone(claims[0].value);
      else values[prop] = clone(claims[0].value);
    }
    if (!blocked) program[kind][id] = {kind,id,...values,authors:[...authors].sort()};
  }
  const dormant=closeDependencies(program,diagnostics);
  for (const v of Object.values(program.view)) {
    if (v.parent && !program.view[v.parent]) diagnostics.push({code:'missing-parent',address:v.id,target:v.parent});
    const seen = new Set([v.id]); let p = v.parent;
    while (p && program.view[p]) {
      if (seen.has(p)) { diagnostics.push({code:'view-cycle',address:v.id}); break; }
      seen.add(p); p = program.view[p].parent;
    }
    if (v.action && !program.action[v.action]) diagnostics.push({code:'missing-action',address:v.id,target:v.action});
    if (v.query && !program.query[v.query]) diagnostics.push({code:'missing-query',address:v.id,target:v.query});
  }
  return {program,diagnostics,provenance,dormant};
}

export class Engine {
  constructor(modules, saved) {
    this.modules = clone(modules); Object.assign(this,compose(modules));
    this.state = saved ? clone(saved.state) : {};
    this.versions = saved ? clone(saved.versions) : {};
    this.serial = saved?.serial ?? 0; this.conflicts = saved?.conflicts ? clone(saved.conflicts) : [];
    this.seeded = new Set(saved?.seeded ?? (saved ? Object.keys(this.program.seed) : []));
    for (const seed of Object.values(this.program.seed)) {
      const [c,id,...rest] = seed.id.split('/');
      if (!safe(c) || !safe(id) || rest.length) throw Error(`Invalid seed ${seed.id}`);
      this.state[c] ??= {};
      if (!this.seeded.has(seed.id) && !this.state[c][id]) this.state[c][id] = clone(seed.values ?? {});
      this.seeded.add(seed.id);
    }
    this.fillDefaults(this.state); this.validate(this.state);
    for(const constraint of Object.values(this.program.constraint)) if(!this.eval(constraint.check,{before:this.state},this.state)) throw Error(`Admission invariant: ${constraint.id}`);
  }
  snapshot() { return clone({state:this.state,versions:this.versions,serial:this.serial,conflicts:this.conflicts,seeded:[...this.seeded].sort()}); }
  fillDefaults(state) {
    for (const f of Object.values(this.program.field)) {
      const [c,key] = f.id.split('.'); state[c] ??= {};
      for (const record of Object.values(state[c])) if (!(key in record)) record[key] = clone(f.default ?? null);
    }
  }
  validate(state) {
    for (const [c,records] of Object.entries(state)) for (const [id,record] of Object.entries(records)) {
      if (!safe(c) || !safe(id)) throw Error('Invalid record address');
      for (const [key,value] of Object.entries(record)) {
        const f = this.program.field[`${c}.${key}`];
        if (!safe(key) || !f) throw Error(`Undeclared field ${c}.${key}`);
        const type = Array.isArray(value) ? 'array' : typeof value;
        if (type !== f.type || value === null || (type === 'number' && !Number.isFinite(value))) throw Error(`Type mismatch ${c}/${id}/${key}: expected ${f.type}`);
      }
    }
  }
  eval(expr, ctx = {}, state = this.state, stack = []) {
    if (stack.length > 48) throw Error('Expression/query nesting limit');
    if (!Array.isArray(expr)) {
      if (expr && typeof expr === 'object') return Object.fromEntries(Object.entries(expr).map(([k,v]) => [k,this.eval(v,ctx,state,stack)]));
      return expr;
    }
    const [op,...a] = expr, ev = x => this.eval(x,ctx,state,[...stack,'expr']);
    if (op === 'lit') return clone(a[0]);
    if(['eq','ne'].includes(op)&&a.length===2){
      const recordExpr=a[0]===null?a[1]:a[1]===null?a[0]:null;
      if(Array.isArray(recordExpr)&&recordExpr[0]==='record'){
        const c=recordExpr[1],id=ev(recordExpr[2]);ctx.reads?.add(cell(c,id,'$exists'));
        return op==='ne'?!!state[c]?.[id]:!state[c]?.[id];
      }
    }
    if(op==='measure'){
      if(!ctx.geometry)throw Error('Measurement is only available during vector painting');
      return ctx.geometry[`${a[0]}|${ev(a[1])}`]?.[a[2]]??null;
    }
    if (op === 'before') return this.eval(a[0],ctx,ctx.before??state,[...stack,'before']);
    if (op === 'use') {
      const d=this.program.derive[a[0]], mark=`derive:${a[0]}`;
      if(!d)throw Error(`Missing derivation ${a[0]}`);
      if(stack.includes(mark))throw Error(`Derivation cycle ${a[0]}`);
      return this.eval(d.value,{...ctx,arg:ev(a[1]??{})},state,[...stack,mark]);
    }
    if (['arg','row','local','parent','gesture','env','event','frame'].includes(op)) return ctx[op]?.[a[0]] ?? null;
    if (op === 'if') return ev(a[0]) ? ev(a[1]) : ev(a[2]);
    if (op === 'and') return a.every(ev);
    if (op === 'or') return a.some(ev);
    if (op === 'coalesce') { for (const v of a) { const x = ev(v); if (x !== null && x !== undefined) return x; } return null; }
    if (op === 'get') {
      if (Array.isArray(a[0]) && a[0][0] === 'record') {
        const c = a[0][1], id = ev(a[0][2]), field = a[1];
        ctx.reads?.add(cell(c,id,field)); return state[c]?.[id]?.[field] ?? (field === 'id' && state[c]?.[id] ? id : null);
      }
      return ev(a[0])?.[a[1]] ?? null;
    }
    if (op === 'record') {
      const [c,id] = [a[0],ev(a[1])], r = state[c]?.[id];
      ctx.reads?.add(cell(c,id,'$exists'));
      if (!r) return null;
      for (const f of Object.keys(r)) ctx.reads?.add(cell(c,id,f));
      return {id,...clone(r)};
    }
    if (op === 'all') {
      ctx.reads?.add(`$collection/${a[0]}`);
      return Object.entries(state[a[0]] ?? {}).sort(([x],[y]) => x.localeCompare(y)).map(([id,r]) => ({id,...clone(r)}));
    }
    if (op === 'query') {
      const name = a[0], q = this.program.query[name];
      if (!q) throw Error(`Missing query ${name}`);
      if (stack.includes(`query:${name}`)) throw Error(`Query cycle ${name}`);
      const qs = [...stack,`query:${name}`];
      let rows = this.eval(['all',q.from],ctx,state,qs);
      if (q.where !== undefined) rows = rows.filter(row => this.eval(q.where,{...ctx,parent:ctx.row??ctx.parent,row},state,qs));
      if (q.sort) rows.sort((x,y) => (typeof x[q.sort]==='number'&&typeof y[q.sort]==='number' ? x[q.sort]-y[q.sort] : String(x[q.sort]).localeCompare(String(y[q.sort]))) || x.id.localeCompare(y.id));
      return rows;
    }
    if (op === 'filter' || op === 'map') {
      const rows = ev(a[0]) ?? [];
      return rows[op](row => this.eval(a[1],{...ctx,parent:ctx.row??ctx.parent,row},state,[...stack,'iteration']));
    }
    const v = a.map(ev);
    switch(op) {
      case 'eq': return equal(v[0],v[1]); case 'ne': return !equal(v[0],v[1]);
      case 'gt': return v[0] > v[1]; case 'gte': return v[0] >= v[1];
      case 'lt': return v[0] < v[1]; case 'lte': return v[0] <= v[1];
      case 'not': return !v[0]; case 'concat': return v.map(x => x ?? '').join('');
      case 'lower': return String(v[0] ?? '').toLowerCase(); case 'trim': return String(v[0] ?? '').trim();
      case 'includes': return (v[0] ?? '').includes(v[1]);
      case 'startsWith': return String(v[0] ?? '').startsWith(v[1]);
      case 'number': return Number(v[0]); case 'round': return Math.round(v[0]);
      case 'floor': return Math.floor(v[0]); case 'mod': return v[0]%v[1];
      case 'abs': return Math.abs(v[0]); case 'sqrt': return Math.sqrt(v[0]);
      case 'sin': return Math.sin(v[0]); case 'cos': return Math.cos(v[0]); case 'pow': return Math.pow(v[0],v[1]);
      case 'min': return Math.min(...v); case 'max': return Math.max(...v);
      case 'add': return v.reduce((x,y) => x+y,0); case 'sub': return v[0]-v[1];
      case 'mul': return v.reduce((x,y) => x*y,1); case 'div': return v[1] === 0 ? 0 : v[0]/v[1];
      case 'count': return v[0]?.length ?? 0; case 'sum': return (v[0] ?? []).reduce((s,r) => s+Number(v.length>1 ? r[v[1]]??0 : r),0);
      case 'unique': return [...new Map((v[0] ?? []).map(x => [canonical(x),x])).values()];
      case 'join': return (v[0] ?? []).join(v[1]);
      default: throw Error(`Unknown expression operator ${op}`);
    }
  }
  dispatch(actionId,args = {}, options = {}) {
    const requests=Array.isArray(actionId)?[...new Map(actionId.map(r=>[canonical(r),r])).values()]:[{action:actionId,args}];
    const before = this.snapshot();
    const label=requests.map(r=>r.action).join(' + ');
    const fail = (code,detail) => {
      const conflict = {id:`conflict-${this.conflicts.length+1}`,code,action:label,detail,serial:this.serial};
      this.conflicts.push(conflict); return {ok:false,conflict};
    };
    if (!requests.length || requests.some(r=>!this.program.action[r.action])) return fail('missing-action',label);
    try {
      const reads = new Set(), ctx = {arg:args,reads,before:this.state};
      const handlers=[];
      for(const request of requests){
        const action=this.program.action[request.action],scope={...ctx,arg:request.args??{}};
        if(action.requires!==undefined&&!this.eval(action.requires,scope))return fail('precondition',action.message??request.action);
        handlers.push({...action,callArgs:scope.arg},...Object.values(this.program.reaction).filter(r=>r.on===request.action&&(r.when===undefined||this.eval(r.when,scope))).map(r=>({...r,callArgs:scope.arg})));
      }
      const proposals = [], deletes = new Map(), creates = new Set();
      let expanded = 0;
      const gather = (effects,h,scope=ctx,depth=0) => { for (const e of effects) {
        if(depth>8 || ++expanded>1000) throw Error('Effect expansion limit');
        if(e.op==='foreach') {
          const rows=this.eval(e.in,scope);if(!Array.isArray(rows))throw Error('Foreach requires an array');
          for(const row of rows)gather(e.effects??[],h,{...scope,parent:scope.row??scope.parent,row},depth+1);
          continue;
        }
        const id = this.eval(e.id,scope), c = e.collection;
        if (!safe(c) || !safe(id) || id.includes('/')) throw Error('Effects require nonempty string ids without slash');
        const base = {c,id,by:h.id};
        if (e.op === 'delete') { deletes.set(`${c}/${id}`,base); continue; }
        if (e.op === 'create') {
          if (this.state[c]?.[id]) throw Error(`Record already exists ${c}/${id}`);
          creates.add(`${c}/${id}`);
          for (const [f,value] of Object.entries(e.values ?? {})) proposals.push({...base,f,op:'set',value:this.eval(value,scope),create:true});
          continue;
        }
        if (!['set','add','union'].includes(e.op)) throw Error(`Unknown effect ${e.op}`);
        proposals.push({...base,f:e.field,op:e.op,value:this.eval(e.value,scope)});
      }};
      for(const h of handlers)gather(h.effects??[],h,{...ctx,arg:h.callArgs});
      const grouped = new Map();
      for (const p of proposals) {
        const address = cell(p.c,p.id,p.f);
        if (deletes.has(`${p.c}/${p.id}`)) return fail('delete-write-conflict',address);
        if (!this.state[p.c]?.[p.id] && !creates.has(`${p.c}/${p.id}`)) throw Error(`Missing record ${p.c}/${p.id}`);
        if (!grouped.has(address)) grouped.set(address,[]); grouped.get(address).push(p);
      }
      const expected = options.expected;
      if (expected) {
        const checked = new Set(reads);
        for (const [address,ps] of grouped) if (ps[0].op === 'set' && !ps[0].create && !equal(this.state[ps[0].c]?.[ps[0].id]?.[ps[0].f],ps[0].value)) checked.add(address);
        for (const [address] of deletes) {
          const [c,id] = address.split('/');
          for (const f of Object.keys(this.state[c]?.[id] ?? {})) checked.add(cell(c,id,f));
          checked.add(`${address}/$exists`);
        }
        const stale = [...checked].filter(k => (expected[k] ?? 0) !== (this.versions[k] ?? 0));
        if (stale.length) return fail('stale-read-or-write',{cells:stale,args,proposals});
      }
      const candidate = clone(this.state);
      for (const address of creates) { const [c,id] = address.split('/'); (candidate[c] ??= {})[id] = {}; }
      for (const [address,ps] of grouped) {
        const p = ps[0], schema = this.program.field[`${p.c}.${p.f}`];
        if (!schema) throw Error(`Undeclared field ${p.c}.${p.f}`);
        if (new Set(ps.map(x => x.op)).size !== 1) return fail('effect-conflict',{address,proposals:ps});
        let value;
        if (p.op === 'set') {
          if (new Set(ps.map(x => canonical(x.value))).size !== 1) return fail('effect-conflict',{address,proposals:ps});
          if (!p.create && (schema.merge ?? 'register') !== 'register') throw Error(`Use ${schema.merge} operations for ${address}`);
          value = p.value;
        } else if (p.op === 'add') {
          if (schema.merge !== 'counter' || ps.some(x => typeof x.value !== 'number')) throw Error(`Add needs counter at ${address}`);
          value = (candidate[p.c][p.id][p.f] ?? schema.default ?? 0) + ps.reduce((s,x) => s+x.value,0);
        } else {
          if (schema.merge !== 'set' || ps.some(x => !Array.isArray(x.value))) throw Error(`Union needs set at ${address}`);
          value = [...new Map([...(candidate[p.c][p.id][p.f] ?? schema.default ?? []),...ps.flatMap(x => x.value)].map(x => [canonical(x),x])).entries()].sort(([a],[b]) => a.localeCompare(b)).map(([,x]) => x);
        }
        candidate[p.c][p.id][p.f] = clone(value);
      }
      for (const {c,id} of deletes.values()) {
        if (!candidate[c]?.[id]) throw Error(`Missing record ${c}/${id}`); delete candidate[c][id];
      }
      this.fillDefaults(candidate); this.validate(candidate);
      for (const constraint of Object.values(this.program.constraint)) if (!this.eval(constraint.check,ctx,candidate)) return fail('invariant',{id:constraint.id,message:constraint.message});
      this.serial++;
      for (const c of new Set([...Object.keys(this.state),...Object.keys(candidate)])) {
        for (const id of new Set([...Object.keys(this.state[c] ?? {}),...Object.keys(candidate[c] ?? {})])) {
          const a = this.state[c]?.[id], b = candidate[c]?.[id];
          if (!!a !== !!b) this.versions[cell(c,id,'$exists')] = this.serial;
          for (const f of new Set([...Object.keys(a ?? {}),...Object.keys(b ?? {})])) if (!equal(a?.[f],b?.[f])) this.versions[cell(c,id,f)] = this.serial;
        }
        if (!equal(this.state[c],candidate[c])) this.versions[`$collection/${c}`] = this.serial;
      }
      this.state = candidate;
      return {ok:true,serial:this.serial,handlers:handlers.map(h => h.id),writes:[...grouped.keys()].sort()};
    } catch (error) {
      this.state = before.state; this.versions = before.versions; this.serial = before.serial;
      return fail('invalid-operation',String(error.message));
    }
  }
  children(id) { return Object.values(this.program.view).filter(v => v.parent === id).sort((a,b) => (a.order ?? 0)-(b.order ?? 0) || a.id.localeCompare(b.id)); }
  styleFor(view,ctx={},expand=(key,value)=>({[key]:value})) {
    const claims = new Map(), result = {}, conflicts = [];
    this.styleMatches??=new Map();const matchKey=canonical([view.id,view.role,view.widget]);
    if(!this.styleMatches.has(matchKey)){const selectors=[`id:${view.id}`,...String(view.role??'').split(' ').map(r=>`role:${r}`),`widget:${view.widget}`];this.styleMatches.set(matchKey,Object.values(this.program.style).filter(s=>selectors.includes(s.selector)));}
    for (const s of this.styleMatches.get(matchKey)) {
      if(s.when!==undefined&&!this.eval(s.when,ctx))continue;
      const local=new Map();
      for(const[sourceKey,expr]of Object.entries(s.values??{})){
        const expanded=expand(sourceKey,this.eval(expr,ctx)),breadth=Object.keys(expanded).length;
        for(const[key,value]of Object.entries(expanded)){if(!local.has(key))local.set(key,[]);local.get(key).push({id:s.id,priority:s.priority??0,value,authors:s.authors,sourceProperty:sourceKey,breadth});}
      }
      for(const[key,ps]of local){const narrowest=Math.min(...ps.map(p=>p.breadth));if(!claims.has(key))claims.set(key,[]);claims.get(key).push(...ps.filter(p=>p.breadth===narrowest));}
    }
    for (const [key,ps] of claims) {
      const top = Math.max(...ps.map(p => p.priority)), winners = ps.filter(p => p.priority === top);
      if (new Set(winners.map(p => canonical(p.value))).size > 1) conflicts.push({code:'style-conflict',view:view.id,property:key,claims:winners});
      else result[key] = winners[0].value;
    }
    return {values:result,conflicts,provenance:Object.fromEntries(claims)};
  }
}
