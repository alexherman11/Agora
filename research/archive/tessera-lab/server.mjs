import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Engine,canonical} from './engine.mjs';
import {load} from './check.mjs';
import {PulseRunner} from './pulses.mjs';
const root = path.dirname(fileURLToPath(import.meta.url));
const trialsRoot = process.env.TESSERA_TRIALS_DIR ?? path.join(root,'trials');
const dataRoot = process.env.TESSERA_DATA_DIR ?? path.join(root,'evidence');
fs.mkdirSync(dataRoot,{recursive:true});
const engines = new Map(), runners = new Map(), streams = new Map(), port = Number(process.env.TESSERA_PORT ?? 4381);
function trials() { return fs.readdirSync(trialsRoot).filter(f=>fs.statSync(path.join(trialsRoot,f)).isDirectory()).sort(); }
function getEngine(name) {
  if (!trials().includes(name)) throw Error('Unknown trial');
  const policyPath=path.join(dataRoot,`${name}-layers.json`);
  const enabled=fs.existsSync(policyPath)?JSON.parse(fs.readFileSync(policyPath,'utf8')).enabled:null;
  const modules = load(path.join(trialsRoot,name)).map(m=>({...m,enabled:!enabled||enabled.includes(m.id)||m.id==='base',claims:!enabled||enabled.includes(m.id)||m.id==='base'?m.claims:m.claims.filter(c=>c.kind==='field')}));
  const signature = canonical(modules), prior = engines.get(name);
  if (prior?.signature === signature) return prior.engine;
  const savePath = path.join(dataRoot,`${name}-live-state.json`);
  const saved = prior?.engine.snapshot() ?? (fs.existsSync(savePath) ? JSON.parse(fs.readFileSync(savePath,'utf8')) : undefined);
  const engine = new Engine(modules,saved); engines.set(name,{engine,signature}); return engine;
}
function persist(trial,engine,receipt){
  fs.writeFileSync(path.join(dataRoot,`${trial}-live-state.json`),JSON.stringify(engine.snapshot(),null,2));
  fs.appendFileSync(path.join(dataRoot,`${trial}-live-events.jsonl`),JSON.stringify({at:new Date().toISOString(),...receipt})+'\n');
  const data=receipt.layerChange?current(trial,engine):{...engine.snapshot(),diagnostics:[...engine.diagnostics,...(runners.get(trial)?.diagnostics??[])]};
  for(const stream of streams.get(trial)??[])stream.write(`data: ${JSON.stringify(data)}\n\n`);
}
function current(trial,engine){return {modules:engine.modules,...engine.snapshot(),diagnostics:[...engine.diagnostics,...(runners.get(trial)?.diagnostics??[])]};}
const server = http.createServer(async(req,res)=>{
  const url = new URL(req.url,'http://localhost');
  const json = (value,status=200) => {res.writeHead(status,{'Content-Type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify(value));};
  try {
    if (req.headers.origin && ![`http://127.0.0.1:${port}`,`http://localhost:${port}`].includes(req.headers.origin)) return json({error:'Local origin required'},403);
    if (url.pathname === '/api/trials') return json(trials());
    if (url.pathname.startsWith('/api/')) {
      const trial = url.searchParams.get('trial') ?? trials()[0], engine = getEngine(trial);
      if(req.method==='GET'&&url.pathname==='/api/stream'){
        res.writeHead(200,{'Content-Type':'text/event-stream','Cache-Control':'no-cache','Connection':'keep-alive'});
        if(!streams.has(trial))streams.set(trial,new Set());streams.get(trial).add(res);
        res.write(`data: ${JSON.stringify(current(trial,engine))}\n\n`);req.on('close',()=>streams.get(trial)?.delete(res));return;
      }
      if (req.method === 'GET' && url.pathname === '/api/state') return json(current(trial,engine));
      if(req.method==='POST'&&url.pathname==='/api/layers'){
        let body='';for await(const chunk of req){body+=chunk;if(body.length>20000)throw Error('Request too large');}
        const {enabled}=JSON.parse(body),ids=load(path.join(trialsRoot,trial)).map(m=>m.id);
        if(!Array.isArray(enabled)||enabled.some(id=>!ids.includes(id)))throw Error('Layer switch requires known module IDs');
        const next=load(path.join(trialsRoot,trial)).map(m=>({...m,enabled:enabled.includes(m.id)||m.id==='base',claims:enabled.includes(m.id)||m.id==='base'?m.claims:m.claims.filter(c=>c.kind==='field')}));
        const candidate=new Engine(next,engine.snapshot());
        fs.writeFileSync(path.join(dataRoot,`${trial}-layers.json`),JSON.stringify({enabled:[...new Set([...enabled,'base'])].sort()}));
        engines.set(trial,{engine:candidate,signature:canonical(next)});
        persist(trial,candidate,{layerChange:enabled});return json(current(trial,candidate));
      }
      if (req.method === 'POST' && url.pathname === '/api/action') {
        let body = ''; for await (const chunk of req) { body += chunk; if(body.length>200000) throw Error('Request too large'); }
        const {action,args,commands,expected} = JSON.parse(body), result = engine.dispatch(commands??action,args,{expected});
        persist(trial,engine,{action,args,commands,result});
        return json({result,...engine.snapshot()});
      }
      return json({error:'Unknown endpoint'},404);
    }
    const files = {'/':'index.html','/scene':'scene.html','/scene.mjs':'scene.mjs','/app.mjs':'app.mjs','/engine.mjs':'engine.mjs','/style.css':'style.css'};
    const file = files[url.pathname]; if (!file) return json({error:'Not found'},404);
    res.writeHead(200,{'Content-Type':file.endsWith('.mjs')?'text/javascript':file.endsWith('.css')?'text/css':'text/html','Cache-Control':'no-store'});
    res.end(fs.readFileSync(path.join(root,file)));
  } catch(error) {json({error:error.message},400);}
});
setInterval(()=>{
  for(const trial of engines.keys())try{
    const engine=engines.get(trial).engine;if(!Object.keys(engine.program.pulse).length&&!runners.has(trial))continue;
    if(!runners.has(trial))runners.set(trial,new PulseRunner());
    const receipt=runners.get(trial).pump(engine,performance.now());if(receipt)persist(trial,engine,receipt);
  }catch(error){if(runners.has(trial))runners.get(trial).diagnostics=[{code:'program-admission',message:error.message}];}
},25).unref();
server.listen(port,'127.0.0.1',()=>console.log(`Tessera listening at http://127.0.0.1:${port}`));
