css('html,body{height:100%;overflow:hidden;background:transparent!important}canvas{position:absolute;inset:0;pointer-events:none}');
const canvas=el('canvas');document.body.append(canvas);const ctx=canvas.getContext('2d');
let profile={},windows=[],work={x:0,y:60,width:innerWidth,height:innerHeight-140};
let lastDescription='';
let x=innerWidth*.43,y=innerHeight-140,dir=1,platform,hop,last=0,hopAt=0,bubble='',bubbleUntil=0,speechAt=0;
function resize(){canvas.width=innerWidth;canvas.height=innerHeight}resize();addEventListener('resize',resize);
async function read(){
  profile=(await rows('rows guy-profile'))[0]||profile;
  const list=await rows('window.list all');
  const w=list.find(r=>r.kind==='work');if(w)work={x:w.box[0],y:w.box[1],width:w.box[2],height:w.box[3]};
  windows=list.filter(r=>r.box&&r.shown!==false&&['window','other'].includes(r.kind)&&!r.edge&&r.box[1]>work.y+100&&r.box[2]>160);
  const description=`${profile.name||'Moss'} walks over the desktop and hops onto real window tops. Mood ${profile.mood||'curious'}, speed ${profile.speed||75}. Clicks pass through. Coat ${profile.body}, face ${profile.face}, scarf ${profile.accent}.`;
  if(description!==lastDescription){lastDescription=description;await agora.describe(description)}
}
function jump(target){
  const chosen=windows.find(w=>w.id===target)||windows[Math.floor(Math.random()*windows.length)];
  if(!chosen)return;
  const [wx,wy,ww]=chosen.box;hop={x0:x,y0:y,x1:wx+Math.min(ww-50,Math.max(50,ww*.4)),y1:wy,t0:performance.now(),duration:1100};platform=chosen;
}
function speak(text){bubble=String(text).slice(0,100);bubbleUntil=performance.now()+6000}
await agora.hear('guy.say',h=>speak(h.text));
await agora.hear('guy.hop',h=>jump(h.target));
await agora.hear('window.opened',h=>{read().then(()=>jump(h.target));speak('Oh, a new place to sit.');});
await agora.hear('set',read);await agora.hear('undo',read);
await read();setInterval(()=>read().catch(()=>{}),3000);
await agora.hitAreas([]);
function frame(t){
  const dt=Math.min(.05,(t-last)/1000||0);last=t;
  if(t>hopAt){hopAt=t+(profile.mood==='playful'?8000:profile.mood==='sleepy'?40000:13000);if(profile.mood!=='sleepy')jump()}
  if(hop){const p=Math.min(1,(t-hop.t0)/hop.duration),ease=p*p*(3-2*p);x=hop.x0+(hop.x1-hop.x0)*ease;y=hop.y0+(hop.y1-hop.y0)*ease-Math.sin(p*Math.PI)*170;if(p===1)hop=null}
  else{
    const visible=platform&&windows.find(w=>w.id===platform.id&&w.box[1]===platform.box[1]);if(!visible)platform=null;
    const left=platform?platform.box[0]+40:work.x+40,right=platform?platform.box[0]+platform.box[2]-40:work.x+work.width-40;
    if(!platform)y=work.y+work.height-8;
    if(profile.mood!=='sleepy')x+=dir*(+profile.speed||75)*dt*(profile.mood==='calm'?.55:1);
    if(x>right){x=right;dir=-1}if(x<left){x=left;dir=1}
  }
  if(t>speechAt){speechAt=t+24000;const phrases=(profile.phrases||'A little room to think.').split('\n').filter(Boolean);if(phrases.length)speak(phrases[Math.floor(Math.random()*phrases.length)])}
  ctx.clearRect(0,0,canvas.width,canvas.height);
  drawGuy(ctx,x,y,t/1000,profile,dir,profile.mood!=='sleepy');
  ctx.font='10px Segoe UI';ctx.textAlign='center';ctx.fillStyle='#8A9C83';ctx.fillText((profile.name||'Moss').slice(0,24),x,y-88);ctx.textAlign='left';
  const showing=t<bubbleUntil;let bw=0;
  if(showing){ctx.font='12px Segoe UI';const words=bubble.split(' '),lines=[''];for(const w of words){const i=lines.length-1;if(ctx.measureText(lines[i]+' '+w).width>220)lines.push(w);else lines[i]+=(lines[i]?' ':'')+w}bw=Math.min(248,Math.max(...lines.map(l=>ctx.measureText(l).width))+28);const bh=lines.length*17+22,bx=Math.min(innerWidth-bw-8,Math.max(8,x-bw/2)),by=Math.max(work.y,y-97-bh);ctx.shadowColor='#283e2520';ctx.shadowBlur=14;ctx.fillStyle='#fffffc';ctx.beginPath();ctx.roundRect(bx,by,bw,bh,12);ctx.fill();ctx.shadowBlur=0;ctx.fillStyle='#657263';lines.forEach((l,i)=>ctx.fillText(l,bx+14,by+20+i*17))}
  const left=Math.max(0,x-150),top=Math.max(work.y,y-(showing?240:95));
  agora.paintArea({x:left,y:top,width:Math.min(300,innerWidth-left),height:Math.max(0,Math.min(innerHeight-top,y-top+12))}).catch(()=>{});
  requestAnimationFrame(frame);
}requestAnimationFrame(frame);
