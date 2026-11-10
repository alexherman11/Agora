// A compact album-and-song panel, brought from home-music-spotify/full.
// Time is a reported fact. Nothing here schedules or interpolates it.
const css=`
.music-panel{box-sizing:border-box;min-height:100vh;background:var(--paper,#f7f9f5);color:var(--ink,#243b30);display:grid;grid-template-columns:minmax(0,1fr);place-items:center;padding:24px;font:15px/1.5 system-ui}
.music-inner{width:min(760px,100%);min-width:0}
.music-brand{font-size:13px;font-weight:650;letter-spacing:.08em;text-transform:uppercase;color:var(--hush,#5f7168);margin-bottom:24px}
.music-empty{padding:40px 0;color:var(--hush,#5f7168)}
.music-panel:has(.music-song) .music-empty{display:none}
.music-song{display:grid;grid-template-columns:minmax(120px,42%) minmax(0,1fr);gap:30px;align-items:center}
.music-song>section{min-width:0}
.music-art{width:100%;aspect-ratio:1;border-radius:16px;background:#e1eee5;box-shadow:0 12px 28px #254a3318;object-fit:cover;display:grid;place-items:center;font-size:64px;color:#397456}
.music-source,.music-artist,.music-album,.music-times{color:var(--hush,#5f7168)}
.music-source{font-size:12px}
.music-title{font-size:clamp(20px,3vw,32px);line-height:1.2;margin:12px 0 8px;overflow-wrap:anywhere}
.music-artist,.music-album{overflow-wrap:anywhere}.music-album{font-size:12px;margin-top:4px}
.music-progress{width:100%;height:5px;accent-color:#287651;display:block;margin-top:24px}
.music-times{display:flex;justify-content:space-between;font-size:11px;margin-top:6px;font-variant-numeric:tabular-nums}
.music-controls{display:flex;align-items:center;justify-content:center;gap:10px;margin-top:18px;flex-wrap:wrap}
.music-controls button{border:0;border-radius:24px;padding:10px;background:transparent;color:inherit;cursor:pointer;font-size:18px;min-width:40px}
.music-controls button:hover{background:#28765118}.music-controls button:focus-visible{outline:2px solid #287651;outline-offset:2px}
.music-controls button[aria-pressed=true]{color:#227448;background:#28765118}
.music-controls button.music-toggle{background:#287651;color:white;width:48px;height:48px}
@media(max-width:560px){
  /* The shared painter adds 18px body padding on narrow screens. Music
     already owns its viewport padding; adding both makes it 36px too tall. */
  body:has(.music-panel){padding:0!important}
  .music-panel{padding:8px 16px;align-items:start}
  .music-song{grid-template-columns:minmax(0,1fr);gap:12px;min-width:0}
  .music-art{width:min(100%,180px,28vh);height:auto;min-width:0;margin:auto}
  .music-brand{margin-bottom:6px}
  .music-title{margin:8px 0 6px}
  .music-progress{margin-top:16px;min-width:0}
  .music-controls{gap:6px;margin-top:12px}
  .music-controls button{padding:8px;min-width:36px}
}
`;
const truth=v=>v===true||/^(true|yes|1)$/i.test(String(v));
const seconds=v=>Math.max(0,Number.isFinite(Number(v))?Number(v):0);
const stamp=v=>{v=Math.floor(seconds(v));return Math.floor(v/60)+':'+String(v%60).padStart(2,'0');};
export default {css,mount(api,s){
  const {P}=api;
  if(api.node.component==='music-panel'){
    const root=api.part('body','main',{class:'music-panel','aria-label':'Music'});
    const inner=P.node('div',{class:'music-inner'},P.node('header',{class:'music-brand'},'Music'),
      P.node('div',{class:'music-empty'},'Nothing playing. Play something in your music app.'));
    inner.append(...api.children.map(api.render));root.append(inner);return root;
  }
  const root=api.part('body','article',{class:'music-song'});
  const art=String(s.art||'');
  root.append(/^data:image\/(jpeg|png|webp);base64,/.test(art)
    ?api.part('art','img',{class:'music-art',src:art,alt:'Album artwork'})
    :api.part('art','div',{class:'music-art','aria-label':'No album artwork'},'♫'));
  const playing=truth(s.playing),can=typeof s.can==='object'&&s.can?s.can:{};
  const side=P.node('section',{},api.part('source','div',{class:'music-source'},
    `${playing?'Playing on':'Paused in'} ${s.player||'your music app'}`),
    api.part('title','h1',{class:'music-title'},s.title||'Unknown song'),
    api.part('artist','div',{class:'music-artist'},s.artist||''));
  if(s.album)side.append(P.node('div',{class:'music-album'},s.album));
  const duration=seconds(s.duration),position=Math.min(seconds(s.position),duration);
  if(duration>0){
    side.append(api.part('progress','progress',{class:'music-progress',max:duration,value:position,
      'aria-label':'Reported song position','aria-valuetext':`${stamp(position)} of ${stamp(duration)}`}),
      P.node('div',{class:'music-times'},P.node('span',{},stamp(position)),P.node('span',{},stamp(duration))));
  }
  const controls=api.part('controls','div',{class:'music-controls','aria-label':'Playback controls'});
  const button=(action,label,glyph,pressed)=>{
    const attrs={type:'button',title:label,'aria-label':label,'data-action':action,
      class:action==='pause'||action==='resume'?'music-toggle':'',on:{click:()=>api.fire(action,{})}};
    if(pressed!==undefined)attrs['aria-pressed']=String(pressed);
    controls.append(P.node('button',attrs,glyph));
  };
  if(truth(can.shuffle))button('shuffle','Shuffle','⤨',truth(s.shuffle));
  if(truth(can.prev))button('prev','Previous','⏮');
  if(truth(can[playing?'pause':'play']))button(playing?'pause':'resume',playing?'Pause':'Play',playing?'Ⅱ':'▶');
  if(truth(can.next))button('next','Next','⏭');
  if(truth(can.repeat))button('repeat',`Repeat: ${s.repeat||'off'}`,s.repeat==='Track'?'↻¹':'↻',
    !!s.repeat&&s.repeat!=='None');
  side.append(controls);root.append(side);return root;
}};
