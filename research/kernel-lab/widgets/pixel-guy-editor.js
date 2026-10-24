// Original art data is prepended by pixel_guy_install.py, from art and guy_looks.
css(`body{margin:0;padding:24px;background:#fff9eb;color:#343e49;font:14px/1.4 'Segoe UI',sans-serif}h1{font:700 26px/1.2 monospace;letter-spacing:-1px}.eyebrow{color:#966040}button,input,textarea{border-radius:2px}button{border:2px solid #46515a;box-shadow:2px 2px 0 #46515a;background:#fffdf5;padding:7px 12px;font-weight:700}button:disabled{opacity:.5;cursor:default}.preview{height:235px;margin:18px 0;background:#dff0ed;border:2px solid #46515a;position:relative;box-shadow:4px 4px 0 #aec9c0}.preview:after{content:'';position:absolute;bottom:28px;left:0;right:0;height:4px;background:#93b9a2}.preview canvas{position:absolute;width:240px;height:240px;left:50%;top:-15px;transform:translateX(-50%);image-rendering:pixelated;z-index:1}.caption{position:absolute;left:14px;top:12px;font:700 13px monospace}.pose{position:absolute;right:12px;bottom:6px;font:12px monospace}.pickers{display:grid;grid-template-columns:1fr 1fr;gap:10px 16px}.picker{display:grid;grid-template-columns:32px 1fr 32px;align-items:center;background:#ffefd2;border:1px solid #dcc5a3;padding:8px;gap:5px}.picker button{padding:4px;box-shadow:1px 1px 0 #46515a}.picker span{text-align:center;font:700 12px monospace}.picker small{display:block;font:11px 'Segoe UI';color:#7d5c46;margin-bottom:3px}.colours{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:18px 0}.colours label{font:12px monospace}.swatches{display:flex;flex-wrap:wrap;gap:5px;margin-top:8px}.swatches button{width:24px;height:24px;padding:0;box-shadow:1px 1px 0 #46515a}.swatches button[aria-pressed=true]{outline:2px solid #cf6855;outline-offset:2px}input[type=color]{padding:0;width:24px;height:24px;border:2px solid #46515a}.details{display:grid;grid-template-columns:1fr 1fr;gap:14px}.details label{display:flex;flex-direction:column;gap:5px;font-size:12px}.wide{grid-column:1/-1}textarea{height:58px;min-height:40px;font-size:13px;padding:8px}input{padding:8px}input[type=range]{padding:0;accent-color:#4f877e}.actions{display:flex;gap:10px;margin:18px 0 12px}.actions button:first-child{background:#ffd795}footer{font:11px monospace;color:#686357;min-height:30px;overflow-wrap:anywhere}details{margin-top:12px}summary{cursor:pointer;font:12px monospace}.hat-grid{display:grid;grid-template-columns:repeat(16,18px);gap:1px;margin:10px 0}.hat-grid button{width:18px;height:18px;padding:0;border:1px solid #a2a99d;box-shadow:none}.hint{font-size:11px;color:#74695c;margin:6px 0}@media(max-width:490px){body{padding:14px}.pickers{gap:8px}.picker{padding:5px}.actions{gap:7px}.actions button{padding:7px}}`);
let guy=(await rows('rows pixel-guy')).find(r=>r.id===GUY_ART.subject);
if(!guy)throw Error('The pixel guy is missing.');
const A=GUY_ART, defaults=A.defaults;
const read=()=>Object.assign({},defaults,guy);
const canvas=el('canvas',{width:80,height:80,'aria-label':'Original pixel guy preview'}),ctx=canvas.getContext('2d');
const caption=el('span',{class:'caption'}),poseCaption=el('span',{class:'pose'}),receipt=el('footer',{role:'status'},'Every pick is saved. Undo brings it back.');
const pickers=el('div',{class:'pickers'}),colours=el('div',{class:'colours'}),details=el('div',{class:'details'});
let pending=Promise.resolve(),lastRecord=null,dirtyHat=false;
const undoButton=button('Undo pick',async()=>{
  if(!lastRecord)return;
  await pending;
  try{await act('undo r'+lastRecord);lastRecord=null;await sync();receipt.textContent='Pick undone.'}catch(e){tell(e)}
});undoButton.disabled=true;
function save(values){
  pending=pending.then(async()=>{
    await sync();
    if(typeof values==='function')values=values(read());
    const line='set '+guy.id+' '+Object.entries(values).map(([k,v])=>k+'='+Q(v)).join(' ');
    const out=await act(line,{[guy.id]:guy.rev});
    // Receipt uses the ordinary kernel record, never a private undo stack.
    lastRecord=out.seq||out.record||Number(out.text?.match(/\[r(\d+)\]/)?.[1]);
    if(typeof lastRecord==='object')lastRecord=lastRecord.seq;
    receipt.textContent='Saved. Undo pick brings it back.';await sync();
  }).catch(tell);return pending;
}
const labels={hat:'Hat',hair:'Hair',eyes:'Eyes',accessory:'Accessory',chatty:'Chattiness'};
const choices={hat:Object.keys(A.hats).filter(x=>x!=='custom'),hair:['original','brown','gold','silver','red','none'],eyes:['dots','happy','sleepy','sunglasses'],accessory:Object.keys(A.accessories),chatty:['quiet','normal','chatty']};
const displays={};
for(const key of ['hat','hair','eyes','accessory']){
  const value=el('b');displays[key]=value;
  const step=delta=>save(f=>{const options=choices[key],i=options.indexOf(f[key]);return {[key]:options[(i+delta+options.length)%options.length]}});
  pickers.append(el('div',{class:'picker'},el('button',{'aria-label':'Previous '+labels[key],on:{click:()=>step(-1)}},'‹'),el('span',{},el('small',{},labels[key]),value),el('button',{'aria-label':'Next '+labels[key],on:{click:()=>step(1)}},'›')));
}
const swatchButtons={};
for(const [key,label,swatches]of [
  ['coat','Coat',['#3f5d73','#799c81','#a66259','#bd995a','#8c7da7']],
  ['skin','Skin',['#f2c894','#ffe1bc','#d6a477','#a76e4a','#704830']],
  ['shoes','Shoes',['#7a5c2e','#343e49','#a94c49','#e1c992','#506c81']]]){
  const group=el('div',{class:'swatches'});swatchButtons[key]=[];
  for(const colour of swatches){const b=el('button',{'aria-label':label+' '+colour,style:{background:colour},on:{click:()=>save({[key]:colour})}});swatchButtons[key].push([b,colour]);group.append(b)}
  const custom=el('input',{type:'color','aria-label':label+' custom colour',value:read()[key],on:{change:e=>save({[key]:e.target.value})}});group.append(custom);
  colours.append(el('label',{},label,group));
}
const inputs={};
for(const [key,label,tag,type]of [['name','His name','input','text'],['speed','Walking speed','input','range'],['chatty','How chatty?','select',''],['phrases','Things he says · one per line','textarea','']]){
  const input=el(tag,{'aria-label':label,...(type?{type}:{})});inputs[key]=input;
  if(key==='speed'){input.min=20;input.max=220;input.step=5}
  if(key==='chatty')for(const s of choices.chatty)input.append(el('option',{value:s},s));
  input.addEventListener('change',()=>save({[key]:input.value}));
  details.append(el('label',{class:key==='phrases'?'wide':''},label,input));
}
// Optional shared hat: eight slash-separated rows of the original palette.
let hatRows=Array(8).fill('................'),ink='b';
const grid=el('div',{class:'hat-grid'}),hatCells=[];
const pen=el('div',{class:'swatches'});
for(const c of ['.','k','o','b','r','s'])pen.append(el('button',{'aria-label':'Hat ink '+c,on:{click:()=>{ink=c}},style:{background:c==='.'?'#fff':A.palette[c]}},c==='.'?'×':''));
function paintHat(){hatCells.forEach((cell,i)=>{const c=hatRows[Math.floor(i/16)][i%16];cell.style.background=c==='.'?'#fff':A.palette[c]})}
for(let i=0;i<128;i++){const b=el('button',{'aria-label':'Hat pixel '+(i%16+1)+', '+(Math.floor(i/16)+1),on:{click:()=>{const y=Math.floor(i/16),x=i%16;hatRows[y]=hatRows[y].slice(0,x)+ink+hatRows[y].slice(x+1);dirtyHat=true;paintHat()}}});hatCells.push(b);grid.append(b)}paintHat();
const hatPanel=el('details',{},el('summary',{},'Draw a tiny hat'),el('p',{class:'hint'},'Pick ink, then pixels. Bottom two rows sit on his head.'),pen,grid,button('Wear this hat',()=>save({custom_hat:hatRows.join('/'),hat:'custom'})),el('p',{class:'hint'},'Saved as custom_hat: eight rows of palette letters. Copy that fact to share.'));
document.body.append(el('div',{class:'eyebrow'},'THE ORIGINAL LITTLE GUY'),el('h1',{},'A hat. A little personality.'),el('div',{class:'preview'},canvas,caption,poseCaption),pickers,colours,details,el('div',{class:'actions'},button('Surprise me',()=>{const f={};for(const k of ['hat','hair','eyes','accessory'])f[k]=choices[k][Math.floor(Math.random()*choices[k].length)];return save(f)}),button('Say hi',()=>act('guy.say '+Q('hi, Alex!'))),undoButton),receipt,hatPanel);
async function sync(){
  const next=(await rows('rows pixel-guy')).find(r=>r.id===A.subject);if(!next)return;guy=next;
  const f=read();caption.textContent=f.name;
  for(const [key,value]of Object.entries(displays))value.textContent=f[key];
  for(const [key,input]of Object.entries(inputs))if(document.activeElement!==input)input.value=f[key];
  for(const [key,buttons]of Object.entries(swatchButtons))for(const [b,c]of buttons)b.setAttribute('aria-pressed',String(f[key].toLowerCase()===c));
  if(!dirtyHat&&f.custom_hat.split('/').length===8&&f.custom_hat.split('/').every(r=>/^[.kobrs]{16}$/.test(r))){hatRows=f.custom_hat.split('/');paintHat()}
  undoButton.disabled=!lastRecord;
}
function previewPixels(pose,blink,f){
  const grid=new Map(),put=(x,y,c)=>grid.set(x+','+y,[x,y,c]);
  [...A.head,...A.body[pose]].forEach((row,y)=>[...row].forEach((c,x)=>{if(c!=='.')put(x,y,blink&&y===4&&c==='k'&&x>4&&x<12?'o':c)}));
  if(f.hair!=='original')for(const [y,xs]of [[1,[5,6,7,8,9,10]],[2,[4,11]],[3,[3,12]]])for(const x of xs)put(x,y,f.hair==='none'?'o':'h');
  if(f.eyes!=='dots'){
    for(const x of [6,10])put(x,4,'o');
    const marks={happy:[[5,4],[6,3],[7,4],[9,4],[10,3],[11,4]],sleepy:[[5,4],[6,4],[9,4],[10,4]],sunglasses:[...Array.from({length:10},(_,i)=>[i+3,4]),[5,5],[6,5],[9,5],[10,5]]};
    if(!blink||f.eyes==='sunglasses')for(const [x,y]of marks[f.eyes]||[])put(x,y,'k');
  }
  let hat=A.hats[f.hat]||A.hats.none;
  if(f.hat==='custom'&&f.custom_hat.split('/').length===8&&f.custom_hat.split('/').every(r=>/^[.kobrs]{16}$/.test(r)))hat=f.custom_hat.split('/');
  for(const [rows,dy]of [[A.accessories[f.accessory]||A.accessories.none,8],[hat,-5]])rows.forEach((r,y)=>[...r].forEach((c,x)=>{if(c!=='.')put(x,y+dy,c)}));
  return [...grid.values()];
}
function paint(t){
  const f=read(),poses=['stand','walk1','walk2','sit','jump'],pose=poses[Math.floor(t/900)%5];poseCaption.textContent=pose.startsWith('walk')?'walk':pose==='jump'?'hop':pose;
  const pal={...A.palette,b:f.coat,o:f.skin,s:f.shoes,h:{brown:'#63412a',gold:'#deb14e',silver:'#b9bfc6',red:'#a9472c'}[f.hair]||A.palette.k};
  ctx.clearRect(0,0,80,80);const bounce=pose==='jump'?-Math.round(Math.sin(t/150)*2)-2:0;
  for(const [x,y,c]of previewPixels(pose,(t%3700)<140,f)){ctx.fillStyle=pal[c];ctx.fillRect(16+x*3,25+y*3+bounce,3,3)}
  requestAnimationFrame(paint);
}
await sync();await agora.hear('set',sync);await agora.hear('undo',sync);setInterval(()=>sync().catch(tell),700);requestAnimationFrame(paint);
