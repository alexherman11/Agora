function drawGuy(ctx,x,y,time,profile={},facing=1,walking=true,scale=1){
  ctx.save();ctx.translate(x,y);ctx.scale(scale*facing,scale);
  const bob=walking?Math.sin(time*7)*2:Math.sin(time*2)*1.3;
  ctx.translate(0,bob);
  ctx.fillStyle='#3b51441a';ctx.beginPath();ctx.ellipse(0,0,23,4,0,0,Math.PI*2);ctx.fill();
  ctx.lineCap='round';ctx.lineWidth=7;ctx.strokeStyle=profile.body||'#9EBDA7';
  const step=walking?Math.sin(time*8)*8:0;
  ctx.beginPath();ctx.moveTo(-8,-17);ctx.lineTo(-10-step,-4);ctx.moveTo(8,-17);ctx.lineTo(11+step,-4);ctx.stroke();
  ctx.strokeStyle=profile.accent||'#D9A689';ctx.lineWidth=6;ctx.beginPath();ctx.moveTo(-17,-36);ctx.lineTo(-25+step/3,-24);ctx.moveTo(17,-36);ctx.lineTo(24-step/3,-24);ctx.stroke();
  ctx.fillStyle=profile.body||'#9EBDA7';ctx.beginPath();ctx.roundRect(-20,-48,40,32,15);ctx.fill();
  ctx.fillStyle=profile.face||'#F3DEC0';ctx.beginPath();ctx.roundRect(-23,-79,46,40,18);ctx.fill();
  ctx.fillStyle=profile.body||'#9EBDA7';ctx.beginPath();ctx.ellipse(0,-76,24,10,0,Math.PI,Math.PI*2);ctx.lineTo(24,-71);ctx.quadraticCurveTo(-1,-64,-24,-71);ctx.closePath();ctx.fill();
  ctx.fillStyle=profile.accent||'#D9A689';ctx.beginPath();ctx.roundRect(-20,-43,40,7,3);ctx.fill();ctx.beginPath();ctx.roundRect(8,-40,7,16,3);ctx.fill();
  const blink=Math.sin(time*.8)>.994;
  ctx.fillStyle='#3F5145';ctx.beginPath();ctx.ellipse(-8,-58,2.2,blink?.6:2.6,0,0,7);ctx.ellipse(8,-58,2.2,blink?.6:2.6,0,0,7);ctx.fill();
  ctx.strokeStyle='#916F58';ctx.lineWidth=1.7;ctx.beginPath();ctx.arc(0,-55,5,.2,Math.PI-.2);ctx.stroke();
  ctx.fillStyle='#DBA79566';ctx.beginPath();ctx.ellipse(-14,-53,3.4,2,0,0,7);ctx.ellipse(14,-53,3.4,2,0,0,7);ctx.fill();ctx.restore();
}
