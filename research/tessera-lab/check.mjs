import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {Engine,canonical,compose} from './engine.mjs';
import {fileURLToPath} from 'node:url';
export function load(dir) { return fs.readdirSync(dir).filter(f => f.endsWith('.tessera.json')).sort().map(f => JSON.parse(fs.readFileSync(path.join(dir,f),'utf8'))); }
export function permutations(xs) { return xs.length ? xs.flatMap((x,i) => permutations(xs.filter((_,j) => j!==i)).map(p => [x,...p])) : [[]]; }
export function check(dir) {
  const modules = load(dir), engine = new Engine(modules), cases = [];
  const report = {trial:path.basename(dir),modules:modules.map(m=>m.id),claims:modules.reduce((s,m)=>s+m.claims.length,0),diagnostics:engine.diagnostics,cases:[],permutations:0};
  for (const f of fs.readdirSync(dir).filter(f=>f.endsWith('.cases.json'))) {
    for (const [i,c] of JSON.parse(fs.readFileSync(path.join(dir,f),'utf8')).entries()) cases.push({name:`${f}:${i+1}`,c});
  }
  for (const {name,c} of cases) {
    const e = new Engine(modules);
    try {
      for (const step of c.steps ?? []) {
        const result = e.dispatch(step.action,step.args,step.options);
        assert.equal(result.ok,step.ok ?? true,canonical(result));
      }
      for (const a of c.assert ?? []) assert.deepEqual(e.eval(a.expr,{local:c.local ?? {}}),a.equals,canonical(a.expr));
      report.cases.push({name,ok:true});
    } catch(error) { report.cases.push({name,ok:false,error:error.message}); }
  }
  const baseline = canonical(compose(modules));
  const orders = modules.length <= 6 ? permutations(modules) : Array.from({length:120},(_,i)=> modules.map((m,j)=>({m,k:((j+1)*(i+7)*2654435761)>>>0})).sort((a,b)=>a.k-b.k).map(x=>x.m));
  for (const order of orders) { assert.equal(canonical(compose([...order,...order])),baseline); assert.equal(canonical(new Engine(order).state),canonical(engine.state)); report.permutations++; }
  report.ok = !report.diagnostics.length && report.cases.every(c=>c.ok);
  return report;
}
if (process.argv[1]?.endsWith('check.mjs')) {
  const dir = process.argv[2] ?? 'trials/01-workspace';
  const report = check(dir); console.log(JSON.stringify(report,null,2));
  const evidence=path.join(path.dirname(fileURLToPath(import.meta.url)),'evidence');
  fs.mkdirSync(evidence,{recursive:true}); fs.writeFileSync(path.join(evidence,`${path.basename(dir)}-checks.json`),JSON.stringify(report,null,2));
  if (!report.ok) process.exitCode = 1;
}
