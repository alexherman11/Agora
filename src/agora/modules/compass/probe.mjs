// Sensor/UI probe ONLY. The door below is a stand-in, not the kernel proof.
// Useful independently of Python: node modules/compass/probe.mjs <evidence-dir>
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import http from 'node:http';
import {spawn, spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const home=path.dirname(fileURLToPath(import.meta.url));
const out=path.resolve(process.argv[2]||path.join(home,'../../proof/evidence'));
fs.mkdirSync(out,{recursive:true});
const wait=ms=>new Promise(r=>setTimeout(r,ms));
let proc, profile, ws, server, seq=0;
const evidence={what:'Compass sensor/UI probe against a stand-in door; NOT the kernel proof',checks:[],error:null};
const check=(name,ok,detail)=>{evidence.checks.push({name,ok:!!ok,detail});console.log(`${ok?'ok':'FAIL'} ${name}`)};
try {
  const script=fs.readFileSync(path.join(home,'compass.html'),'utf8');
  new Function(script.match(/<script>([\s\S]*)<\/script>/)[1]);
  check('widget JavaScript parses',true);
  const requests=[];
  let solved=false, held=false;
  server=http.createServer(async(req,res)=>{
    if(req.method==='GET'){res.setHeader('Content-Type','text/html');res.end(script);return}
    let body='';for await(const chunk of req)body+=chunk;
    const line=JSON.parse(body).line;requests.push(line);
    let rows=[],text='';
    if(line==='look hh1')rows=[{title:'Hidden in plain sight',points_kind:'poll',collection:'block',in_group:'hh2',solved_word:'vote',action_word:'solve',board:'hh3'}];
    else if(line.startsWith('rows poll'))rows=[{id:'hh4',title:'Sidewalk sky',text:'What shape has five chalk points?',order:2,collection:'block',lat:36.9695,lon:-122.008,votes_solved:4}];
    else if(line.startsWith('test '))text=solved?'yes':'no';
    else if(line==='counts hh3')rows=[{bucket:'1',count:12},{bucket:'2',count:4},{bucket:'3',count:2}];
    else if(line==='compass.start')held=true;
    else if(line==='compass.stop')held=false;
    else if(line.startsWith('solve hh4 answer='))solved=true;
    else {res.statusCode=400;res.end(JSON.stringify({error:'unrecognized stand-in line'}));return}
    res.setHeader('Content-Type','application/json');res.end(JSON.stringify({ok:true,rows,text}));
  });
  await new Promise(r=>server.listen(0,'127.0.0.1',r));
  const url=`http://127.0.0.1:${server.address().port}`;
  const exe=['C:/Program Files/Google/Chrome/Application/chrome.exe','C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].find(fs.existsSync);
  if(!exe)throw Error('No Chrome/Edge installed');
  profile=fs.mkdtempSync(path.join(os.tmpdir(),'hunt-probe-'));
  proc=spawn(exe,['--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check',`--user-data-dir=${profile}`,'--remote-debugging-port=0','about:blank'],{windowsHide:true,stdio:'ignore'});
  let launchError;proc.on('error',e=>launchError=e);
  const active=path.join(profile,'DevToolsActivePort');
  for(let i=0;i<100&&!fs.existsSync(active)&&!launchError;i++)await wait(100);
  if(launchError)throw launchError;
  const port=fs.readFileSync(active,'utf8').split(/\s/)[0];
  const pages=await(await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  ws=new WebSocket(pages.find(p=>p.type==='page').webSocketDebuggerUrl);
  await new Promise((r,j)=>{ws.addEventListener('open',r,{once:true});ws.addEventListener('error',j,{once:true})});
  const pending=new Map();ws.addEventListener('message',e=>{const m=JSON.parse(e.data);if(pending.has(m.id)){const [r,j]=pending.get(m.id);pending.delete(m.id);m.error?j(Error(JSON.stringify(m.error))):r(m.result||{})}});
  const call=(method,params={})=>new Promise((r,j)=>{const id=++seq;pending.set(id,[r,j]);ws.send(JSON.stringify({id,method,params}));setTimeout(()=>{if(pending.delete(id))j(Error('CDP timed out: '+method))},10000).unref()});
  const js=async expression=>{const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result?.value};
  evidence.browser=await call('Browser.getVersion');
  console.log('headless browser protocol connected');
  await call('Emulation.setDeviceMetricsOverride',{width:390,height:1050,deviceScaleFactor:1,mobile:true});
  await call('Emulation.setGeolocationOverride',{latitude:36.968,longitude:-122.008,accuracy:1});
  await call('Browser.grantPermissions',{permissions:['geolocation']});
  for(const type of ['absolute-orientation','linear-acceleration'])await call('Emulation.setSensorOverrideEnabled',{enabled:true,type});
  await call('Emulation.setSensorOverrideReadings',{type:'absolute-orientation',reading:{quaternion:{x:0,y:0,z:0,w:1}}});
  await call('Emulation.setSensorOverrideReadings',{type:'linear-acceleration',reading:{xyz:{x:0,y:1,z:0}}});
  await call('Page.enable');await call('Page.navigate',{url:`${url}/?door=${encodeURIComponent(url)}&view=hh1`});
  for(let i=0;i<100;i++){if(await js('!!(window.compassEvidence?.orientation && window.compassEvidence?.motion && window.compassEvidence?.next)'))break;await wait(100)}
  const first=await js('window.compassEvidence');evidence.first=first;
  check('actual orientation and motion sensor readings arrive',first?.orientation>0&&first?.motion>0,first);
  await call('Emulation.setSensorOverrideReadings',{type:'absolute-orientation',reading:{quaternion:{x:0,y:0,z:Math.SQRT1_2,w:Math.SQRT1_2}}});
  for(let i=0;i<50;i++){if(await js('Math.abs((window.compassEvidence?.heading||0)-90)<1'))break;await wait(100)}
  const turned=await js('window.compassEvidence');evidence.turned=turned;
  check('a ninety-degree orientation turns the arrow ninety degrees',Math.abs(((first.angle-turned.angle+360)%360)-90)<1,turned);
  const shot=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});fs.writeFileSync(path.join(out,'hunt-widget-probe.png'),Buffer.from(shot.data,'base64'));
  await js("document.querySelector('#answer').value='star';document.querySelector('form').requestSubmit()");
  for(let i=0;i<50&&!solved;i++)await wait(100);
  check('answer form emits the composed solve word',requests.includes('solve hh4 answer="star" in=hh2'));
  await js("document.querySelector('#stop').click()");
  for(let i=0;i<50;i++){if(!held&&await js('window.compassEvidence?.held===false'))break;await wait(100)}
  check('stop emits stop and stops browser sensors',!held&&await js('window.compassEvidence?.held===false'));
  evidence.page=await js('document.body.innerText');
} catch(e){evidence.error=String(e);console.log(evidence.error)}
finally{
  ws?.close();server?.close();
  if(proc?.pid){if(process.platform==='win32')spawnSync('taskkill',['/PID',String(proc.pid),'/T','/F'],{windowsHide:true,stdio:'ignore'});else proc.kill()}
  if(profile){
    const target=path.resolve(profile), root=path.resolve(os.tmpdir());
    if(path.dirname(target)!==root||!path.basename(target).startsWith('hunt-probe-'))throw Error('Unexpected temporary profile path');
    await wait(300);fs.rmSync(target,{recursive:true,force:true,maxRetries:3,retryDelay:200});
  }
  const passed=evidence.checks.filter(c=>c.ok).length;
  console.log(`${passed} of ${evidence.checks.length} sensor/UI probe checks passed`);
  fs.writeFileSync(path.join(out,'hunt-sensor-probe.json'),JSON.stringify(evidence,null,1));
  process.exitCode=evidence.error||passed!==evidence.checks.length?1:0;
}
