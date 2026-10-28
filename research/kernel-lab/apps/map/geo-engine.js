// The map surface's engine: a flat, tiled WebGL world in Web Mercator metres, a camera, picking, and a DOM overlay
// for names and pins. Tiles come from the map module (`map.tile z/x/y`) through the part's readings; nothing here
// touches the network. It lives in the geo-map part's api.draft, so a repaint moves it to the new part instead of
// rebuilding. It draws only when something changes (input, a tile arriving, a fly); there is no running loop.
const GEO_WORLD=2*Math.PI*6378137,GEO_R=6378137,GEO_FOV=40*Math.PI/180;
const GEO_AREAS_DAY={residential:'#efe9dc',commercial:'#f3e6dc',industrial:'#e9e3db',parking:'#e6e2da',school:'#f2e6c9',hospital:'#f4dfdc',
  cemetery:'#d5e4c8',farm:'#ece9cf',scrub:'#d9e4c0',rock:'#e2ded6',ice:'#f4f8fb',green:'#cfe7b6',wood:'#aed79a',park:'#c2e3a8',
  wetland:'#c0dfc8',beach:'#f5e6b8',pitch:'#b2dc98',play:'#ecdcb0',airport:'#e8e4ec',water:'#9fd5ec',sea:'#93cde6',pool:'#8fd6f2'};
const GEO_STYLES={
  day:{name:'Day',land:'#f1ebdf',sky:'#cfe8f2',haze:'#dde9ea',edge:[0.33,0.26,0.2,0.3],shadow:0.16,sun:[-0.55,-0.42,0.72],
    area:GEO_AREAS_DAY,road:{motorway:'#ffd89a',major:'#fff6e2',street:'#ffffff',service:'#fcfaf5',walk:'#f6eedf',path:'#cbb48a',cycle:'#9ccbb3',steps:'#c49c7c',rail:'#b3aaa0',runway:'#d9d6dc',taxiway:'#e1dee4'},
    casing:{motorway:'#dca866',major:'#d8c4a2',street:'#dbd2c2',service:'#e2d9ca'},ferry:'#6aaed0',bridge:'#9c8f80',railTie:'#7d746b',
    buildings:{plain:['#efd9c0','#ecd3b8','#f2e1cb','#e8d6c4'],home:['#f3d6b3','#efcaa4','#f6dfc0','#ecd0b5','#f1d2c4'],shop:['#e9dccd','#f0e3d3','#e3d8cc'],
      work:['#dcd8d2','#d4d0ca','#e2ddd5'],shed:['#d9cbb8','#cfc2b0'],civic:['#e7d3c7','#ead9c1','#e0cfd8'],faith:['#efe2cf','#e8dccb']},
    roofs:{plain:['#c98a6e','#b88a74','#a7978a','#c29275'],home:['#d9876b','#c97b62','#b8846c','#d39a72','#c56f5b'],shop:['#9aa3a8','#a7a09a','#8f9aa3'],
      work:['#8f979b','#9ba1a3','#a5a9a8'],shed:['#9c8b7a','#8a7a6a'],civic:['#7d8fa6','#8a7f9e','#6f8f8a'],faith:['#8c7a9e','#9a7f74']},
    label:'#463d33',halo:'#fffcf5',town:'#2f2a24'},
  dusk:{name:'Dusk',land:'#ecdcc7',sky:'#f2c9a7',haze:'#efd2bb',edge:[0.35,0.22,0.18,0.32],shadow:0.24,sun:[-0.8,-0.25,0.42],
    area:{...GEO_AREAS_DAY,residential:'#ecdccb',commercial:'#efd8c8',green:'#c9d9a6',park:'#bcd59a',wood:'#a3c88a',water:'#93bfd6',sea:'#86b3cf',beach:'#f1d7a8'},
    road:{motorway:'#ffc98a',major:'#fde9cf',street:'#fff3e4',service:'#f9ecdd',walk:'#f2e0cb',path:'#c3a37c',cycle:'#99bfa7',steps:'#bf9172',rail:'#ab9d92',runway:'#d6cdd2',taxiway:'#ddd3d6'},
    casing:{motorway:'#d1945a',major:'#d2b28e',street:'#d6c2ad',service:'#dccab8'},ferry:'#6a9ec0',bridge:'#93806f',railTie:'#76675c',
    buildings:{plain:['#f0cfae','#ecc6a2'],home:['#f4c9a0','#f0bd93','#f6d1ab','#eec3a6'],shop:['#ead2be','#f0d9c4'],work:['#dccfc6','#d6c9bf'],shed:['#d9c0a8'],civic:['#e9c7b8','#e3c3c9'],faith:['#ecd3bc']},
    roofs:{plain:['#b8745d','#a87562'],home:['#c96e55','#b8634e','#a96f5a','#c3805c'],shop:['#8f8d93','#9a8c85'],work:['#857f85','#918a8b'],shed:['#8c7565'],civic:['#6f7896','#7c6b8c'],faith:['#7f6690']},
    label:'#4a3428',halo:'#fff3e6',town:'#3a2418'},
  night:{name:'Night',land:'#232a2c',sky:'#121a24',haze:'#1b2530',edge:[0.02,0.03,0.05,0.55],shadow:0.3,sun:[-0.4,-0.3,0.85],
    area:{residential:'#272e30',commercial:'#2c2b31',industrial:'#292c2e',parking:'#2a2d2f',school:'#2f2d2a',hospital:'#322a2c',cemetery:'#26332b',farm:'#2b2e27',
      scrub:'#28322a',rock:'#2d2e2f',ice:'#3a4048',green:'#29372b',wood:'#233326',park:'#273a2b',wetland:'#25362f',beach:'#3b3a30',pitch:'#2b3d2c',play:'#363428',
      airport:'#2c2b33',water:'#183246',sea:'#14293b',pool:'#1f4560'},
    road:{motorway:'#8a6a3f',major:'#5b5b55',street:'#46494a',service:'#3d4041',walk:'#3e3d38',path:'#58503f',cycle:'#3d5649',steps:'#58483b',rail:'#5f5953',runway:'#3a393f',taxiway:'#353439'},
    casing:{motorway:'#3a2d1f',major:'#2a2b2a',street:'#2b2d2e',service:'#2a2c2d'},ferry:'#3c6a85',bridge:'#4d4a46',railTie:'#3f3a35',
    buildings:{plain:['#4a4a50','#45464c'],home:['#55504b','#4f4a45','#5a524b'],shop:['#4b4d55','#50525a'],work:['#45484c'],shed:['#4a4540'],civic:['#4c4a5a','#4a5257'],faith:['#544b5a']},
    roofs:{plain:['#3b3d44'],home:['#5e4038','#553a33','#4f3f37'],shop:['#3d4047'],work:['#3a3d41'],shed:['#43392f'],civic:['#3b4458'],faith:['#4a3b55']},
    label:'#e4ddcf',halo:'#141b20',town:'#f2ead9'},
  paper:{name:'Paper',land:'#f6f3ec',sky:'#f6f3ec',haze:'#f6f3ec',edge:[0.2,0.18,0.16,0.42],shadow:0,sun:[-0.3,-0.3,0.9],
    area:{residential:'#f6f3ec',commercial:'#f2eee6',industrial:'#efebe4',parking:'#efebe4',school:'#f2ece0',hospital:'#f2e9e6',cemetery:'#e8ede2',farm:'#f3f1e6',
      scrub:'#eaeee0',rock:'#ecebe7',ice:'#fafbfc',green:'#e6eedc',wood:'#dbe7d1',park:'#e0ebd6',wetland:'#dfeae3',beach:'#f6efdb',pitch:'#dce9d2',play:'#f1ebdb',
      airport:'#efedf1',water:'#d5e6ee',sea:'#d0e2eb',pool:'#cfe6f0'},
    road:{motorway:'#ffffff',major:'#ffffff',street:'#ffffff',service:'#ffffff',walk:'#fbf9f4',path:'#c9c0b2',cycle:'#b9cfc3',steps:'#c7b9ab',rail:'#bdb7b0',runway:'#e9e7ea',taxiway:'#efedf0'},
    casing:{motorway:'#bdb4a8',major:'#cfc8bd',street:'#dcd6cc',service:'#e2ddd4'},ferry:'#a4c3d3',bridge:'#b9b0a4',railTie:'#a19a92',
    buildings:{plain:['#e9e5de'],home:['#ece6dc'],shop:['#e6e2dc'],work:['#e2dfda'],shed:['#e4ded5'],civic:['#e4dfe6'],faith:['#e8e2da']},
    roofs:{plain:['#dcd6cd'],home:['#ddd4c8'],shop:['#d6d3cf'],work:['#d3d1ce'],shed:['#d6cec3'],civic:['#d4d0dc'],faith:['#dad1c6']},
    label:'#3d3a35',halo:'#f6f3ec',town:'#24221f'},
};
const GEO_HEAD=`precision highp float;`;
const GEO_SHADERS={
  flatV:`attribute vec3 aPos;attribute vec4 aCol;attribute float aPick;
uniform mat4 uMVP;uniform vec2 uOff;uniform vec3 uEye;varying vec4 vCol;varying float vPick;varying float vD;
void main(){vec3 p=vec3(aPos.xy+uOff,aPos.z);vCol=aCol;vPick=aPick;vD=distance(p,uEye);gl_Position=uMVP*vec4(p,1.0);}`,
  lineV:`attribute vec2 aPos;attribute vec2 aN;attribute vec2 aW;attribute float aZ;attribute vec3 aCol;attribute float aPick;
uniform mat4 uMVP;uniform vec2 uOff;uniform vec3 uEye;uniform float uPx;varying vec4 vCol;varying float vPick;varying float vD;
void main(){vec2 c=aPos+uOff;float D=distance(vec3(c,0.0),uEye);float hw=max(aW.x,aW.y*uPx*D);vec3 p=vec3(c+aN*hw,0.0);
vCol=vec4(aCol,1.0);vPick=aPick;vD=D;gl_Position=uMVP*vec4(p,1.0);}`,
  flatF:GEO_HEAD+`varying vec4 vCol;varying float vPick;varying float vD;
uniform float uMode;uniform float uAlpha;uniform vec2 uFog;uniform vec3 uHaze;uniform float uSel;uniform float uHover;uniform float uSlot;uniform vec4 uTint;
vec4 enc(float id){return vec4(mod(id,256.0)/255.0,mod(floor(id/256.0),256.0)/255.0,uSlot/255.0,1.0);}
void main(){if(uMode>0.5){if(vPick<0.5)discard;gl_FragColor=enc(vPick);return;}
vec3 c=vCol.rgb;if(uTint.a>0.0)c=uTint.rgb;
if(vPick>0.5&&abs(vPick-uSel)<0.5)c=mix(c,vec3(1.0,0.76,0.32),0.5);else if(vPick>0.5&&abs(vPick-uHover)<0.5)c=mix(c,vec3(1.0),0.22);
float f=smoothstep(uFog.x,uFog.y,vD);gl_FragColor=vec4(mix(c,uHaze,f),vCol.a*uAlpha);}`,
  bldV:`attribute vec3 aPos;attribute vec3 aNorm;attribute vec3 aCol;attribute float aPick;attribute float aPart;
uniform mat4 uMVP;uniform vec2 uOff;uniform vec3 uEye;uniform float uLift;
varying vec3 vCol;varying vec3 vN;varying float vPick;varying float vPart;varying float vD;varying float vZ;
void main(){vec3 p=vec3(aPos.xy+uOff,aPos.z*uLift);vCol=aCol;vN=aNorm;vPick=aPick;vPart=aPart;vZ=p.z;vD=distance(p,uEye);gl_Position=uMVP*vec4(p,1.0);}`,
  bldF:GEO_HEAD+`varying vec3 vCol;varying vec3 vN;varying float vPick;varying float vPart;varying float vD;varying float vZ;
uniform float uMode;uniform vec2 uFog;uniform vec3 uHaze;uniform float uSel;uniform float uHover;uniform vec3 uSun;uniform float uSlot;
vec4 enc(float id){return vec4(mod(id,256.0)/255.0,mod(floor(id/256.0),256.0)/255.0,uSlot/255.0,1.0);}
void main(){if(uMode>0.5){gl_FragColor=enc(vPick);return;}
float dif=max(dot(normalize(vN),uSun),0.0);vec3 c=vCol;
if(vPart>1.5)c=c*(0.9+0.12*dif);else{c=c*(0.6+0.5*dif);c*=mix(0.82,1.0,smoothstep(0.0,4.0,vZ));}
if(abs(vPick-uSel)<0.5)c=mix(c,vec3(1.0,0.78,0.36),0.55);else if(abs(vPick-uHover)<0.5)c=mix(c,vec3(1.0),0.22);
float f=smoothstep(uFog.x,uFog.y,vD);gl_FragColor=vec4(mix(c,uHaze,f),1.0);}`,
  edgeV:`attribute vec3 aPos;attribute float aKind;uniform mat4 uMVP;uniform vec2 uOff;uniform vec3 uEye;uniform float uLift;varying float vD;
void main(){vec3 p=vec3(aPos.xy+uOff,aPos.z*uLift);vD=distance(p,uEye);gl_Position=uMVP*vec4(p,1.0);gl_Position.z-=0.0004*gl_Position.w;}`,
  edgeF:GEO_HEAD+`varying float vD;uniform vec4 uCol;uniform vec2 uFog;void main(){float f=smoothstep(uFog.x*0.6,uFog.y*0.5,vD);gl_FragColor=vec4(uCol.rgb,uCol.a*(1.0-f));}`,
};
const geoMat={
  persp(fovy,a,n,f){const t=1/Math.tan(fovy/2),nf=1/(n-f);return [t/a,0,0,0,0,t,0,0,0,0,(f+n)*nf,-1,0,0,2*f*n*nf,0]},
  look(e,c,u){let z=[e[0]-c[0],e[1]-c[1],e[2]-c[2]];let l=Math.hypot(...z);z=z.map(v=>v/l);
    let x=[u[1]*z[2]-u[2]*z[1],u[2]*z[0]-u[0]*z[2],u[0]*z[1]-u[1]*z[0]];l=Math.hypot(...x)||1;x=x.map(v=>v/l);
    const y=[z[1]*x[2]-z[2]*x[1],z[2]*x[0]-z[0]*x[2],z[0]*x[1]-z[1]*x[0]];
    return [x[0],y[0],z[0],0,x[1],y[1],z[1],0,x[2],y[2],z[2],0,-(x[0]*e[0]+x[1]*e[1]+x[2]*e[2]),-(y[0]*e[0]+y[1]*e[1]+y[2]*e[2]),-(z[0]*e[0]+z[1]*e[1]+z[2]*e[2]),1]},
  mul(a,b){const o=new Array(16);for(let i=0;i<4;i++)for(let j=0;j<4;j++){let s=0;for(let k=0;k<4;k++)s+=a[k*4+j]*b[i*4+k];o[i*4+j]=s}return o},
};
const GEO_CATS={food:['cafe','restaurant','fast_food','bar','pub','ice_cream','biergarten','food_court','bakery','beer','wine','coffee'],
  nature:['park','garden','beach','playground','nature_reserve','dog_park','wood','water','viewpoint','pitch','wetland','peak','campsite','picnic_site'],
  community:['library','school','place_of_worship','community_centre','theatre','museum','arts_centre','town_hall','townhall','post','post_office','social_facility',
    'kindergarten','college','university','marina','harbor','cinema','music','art_gallery','police','fire_station','attraction','information','stadium'],
  health:['hospital','doctors','pharmacy','dentist','clinic','veterinary'],
  move:['bus','bus_stop','railway','fuel','parking','bicycle','bicycle_rental','boat_rental','car_rental','charging_station','ferry_terminal','airport','car']};
function geoCat(c){c=String(c||'');if(c.startsWith('shop')||['grocery','clothing_store','shop','alcohol_shop','books','gift','jewelry','furniture','hardware','convenience','supermarket','laundry','hairdresser','bank','atm'].includes(c))return 'shop';
  for(const [k,v] of Object.entries(GEO_CATS))if(v.includes(c))return k;return 'other'}
const geoHex=(h,a=1)=>{h=String(h||'#888').replace('#','');if(h.length===3)h=h.split('').map(c=>c+c).join('');const n=parseInt(h,16)||0;return [(n>>16&255)/255,(n>>8&255)/255,(n&255)/255,a]};

class GeoEngine{
  constructor(workerSource){
    this.workerSource=workerSource;
    this.canvas=document.createElement('canvas');this.canvas.className='gm-canvas';this.canvas.tabIndex=0;
    this.canvas.setAttribute('aria-label','Map. Drag to move, scroll to zoom, right-drag to turn. Arrow keys move; + and - zoom; Q and E turn.');
    this.overlay=document.createElement('div');this.overlay.className='gm-overlay';
    const [x,y]=this.toXY(36.9672,-122.0088);
    this.cam={x,y,dist:1400,pitch:52,bearing:-12};this.lift=1;
    this.tiles=new Map();this.queue=[];this.inflight=0;this.drawList=[];this.serial=0;this.workers=[];this.waiting=new Map();
    this.layers=[];this.hidden=new Set();this.items=[];this.routes=[];this.preview=null;
    this.selRef='';this.selectedId='';this.hoverRef='';this.tool='look';this.stops=[];this.draft=null;
    this.labelEls=new Map();this.pinEls=new Map();this.frameAsked=false;this.status='';this.style='day';this.palette=GEO_STYLES.day;
    this.listeners=false;this.pointers=new Map();this.anim=null;this.stats={fetched:0,built:0,failed:0,buildMs:0};
  }
  get ready(){return !!this.gl&&this.drawList.length>0}
  // --- placing in the DOM ---------------------------------------------------------------------------------
  attach(root,api){
    this.api=api;this.root=root;root.append(this.canvas,this.overlay);
    // a repaint disposes the old part's timers, including a frame this engine had asked for: ask again
    this.frameAsked=false;
    if(!this.listeners){this.listen();this.listeners=true}
    if(this.ro)this.ro.disconnect();
    this.ro=new ResizeObserver(()=>this.resize());this.ro.observe(root);
    api.cleanup(()=>this.ro&&this.ro.disconnect());
    this.applyStyleCss();
    this.resize();
  }
  resize(){
    const r=this.root?.getBoundingClientRect();if(!r||!r.width)return;
    const dpr=Math.min(2,window.devicePixelRatio||1);this.dpr=dpr;this.w=r.width;this.h=r.height;
    const W=Math.round(r.width*dpr),H=Math.round(r.height*dpr);
    if(this.canvas.width!==W||this.canvas.height!==H){this.canvas.width=W;this.canvas.height=H;this.pickFb=null}
    this.ask();
  }
  setStyle(name){
    const s=GEO_STYLES[name]?name:'day';if(s===this.style&&this.palette)return;
    this.style=s;this.palette=GEO_STYLES[s];this.applyStyleCss();
    // every tile is rebuilt in the new colours; the old ones keep drawing until the new ones arrive
    for(const t of this.tiles.values())if(t.chunk&&t.state==='ready'){t.rebuild=true}
    this.ask();
  }
  applyStyleCss(){if(!this.root)return;const P=this.palette;const s=this.root.style;
    s.setProperty('--gm-label',P.label);s.setProperty('--gm-halo',P.halo);s.setProperty('--gm-town',P.town);s.setProperty('--gm-sky',P.sky);this.root.dataset.style=this.style}
  // --- GL ---------------------------------------------------------------------------------------------------
  initGL(){
    if(this.gl!==undefined)return !!this.gl;
    const opts={antialias:true,alpha:false,premultipliedAlpha:false,preserveDrawingBuffer:false,depth:true};
    const gl=this.canvas.getContext('webgl2',opts)||this.canvas.getContext('webgl',opts);this.gl=gl||null;
    if(!gl){this.status='This screen has no WebGL, so the map cannot draw here.';return false}
    const prog=(v,f,attrs)=>{const p=gl.createProgram();for(const [src,type] of [[v,gl.VERTEX_SHADER],[f,gl.FRAGMENT_SHADER]]){const s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error('Map shader: '+gl.getShaderInfoLog(s));gl.attachShader(p,s)}
      attrs.forEach((a,i)=>gl.bindAttribLocation(p,i,a));gl.linkProgram(p);if(!gl.getProgramParameter(p,gl.LINK_STATUS))throw Error('Map program: '+gl.getProgramInfoLog(p));
      const u={};const n=gl.getProgramParameter(p,gl.ACTIVE_UNIFORMS);for(let i=0;i<n;i++){const info=gl.getActiveUniform(p,i);u[info.name]=gl.getUniformLocation(p,info.name)}return {p,u}};
    this.pFlat=prog(GEO_SHADERS.flatV,GEO_SHADERS.flatF,['aPos','aCol','aPick']);
    this.pLine=prog(GEO_SHADERS.lineV,GEO_SHADERS.flatF,['aPos','aN','aW','aZ','aCol','aPick']);
    this.pBld=prog(GEO_SHADERS.bldV,GEO_SHADERS.bldF,['aPos','aNorm','aCol','aPick','aPart']);
    this.pEdge=prog(GEO_SHADERS.edgeV,GEO_SHADERS.edgeF,['aPos','aKind']);
    this.groundBuf=gl.createBuffer();
    this.canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();this.status='The map lost its drawing surface; it comes back by itself.';this.lost=true});
    this.canvas.addEventListener('webglcontextrestored',()=>{this.gl=undefined;this.lost=false;for(const t of this.tiles.values()){t.bufs=null;if(t.state==='ready')t.rebuild=true}this.initGL();this.buildRoutes();this.ask()});
    return true;
  }
  buffer(arr,stride){const gl=this.gl,b=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,b);gl.bufferData(gl.ARRAY_BUFFER,arr,gl.STATIC_DRAW);return {b,n:arr.length/stride,stride}}
  // --- tiles --------------------------------------------------------------------------------------------------
  worker(){
    if(this.workers.length<2){
      const url=URL.createObjectURL(new Blob(['('+this.workerSource+')()'],{type:'text/javascript'}));
      const w=new Worker(url);URL.revokeObjectURL(url);w.jobs=0;
      w.onmessage=e=>{w.jobs--;const cb=this.waiting.get(e.data.id);this.waiting.delete(e.data.id);cb?.(e.data)};
      w.onerror=e=>{this.status='The map builder stopped: '+(e.message||'error')};
      this.workers.push(w);
    }
    return this.workers.reduce((a,b)=>a.jobs<=b.jobs?a:b);
  }
  build(t){
    const id=++this.serial,w=this.worker();w.jobs++;t.state='building';
    this.waiting.set(id,out=>{
      if(out.error){t.state='error';t.error=out.error;this.stats.failed++;this.ask();return}
      if(!this.gl){t.state='new';return}
      this.freeBufs(t);const gl=this.gl;
      t.bufs={areas:this.buffer(out.areas,8),casings:this.buffer(out.casings,11),lines:this.buffer(out.lines,11),shadows:this.buffer(out.shadows,8),
        buildings:this.buffer(out.buildings,11),edges:this.buffer(out.edges,4)};
      t.picks=out.picks;t.labels=out.labels;t.places=out.places;t.origin=out.origin;t.counts=out.counts;t.style=this.style;
      t.ids=new Map();out.picks.forEach((p,i)=>{if(p&&p.ref)t.ids.set(p.ref,i)});
      t.state='ready';t.rebuild=false;this.stats.built++;this.stats.buildMs+=out.ms;this.labelsDirty=true;this.ask();
    });
    w.postMessage({id,chunk:t.chunk,palette:this.palette,flags:{noShadows:!this.palette.shadow}});
  }
  freeBufs(t){if(!t.bufs||!this.gl)return;for(const b of Object.values(t.bufs))this.gl.deleteBuffer(b.b);t.bufs=null}
  pump(){
    // ask for the most needed tiles first: lower zooms (they stand in for others), then nearest the centre
    this.queue=this.queue.filter(t=>t.state==='queued'&&t.wanted===this.frameNo);
    this.queue.sort((a,b)=>a.z-b.z||a.d-b.d);
    while(this.inflight<4&&this.queue.length&&this.fetchTile){
      const t=this.queue.shift();t.state='loading';this.inflight++;
      this.fetchTile(t.key).then(text=>{this.inflight--;t.chunk=text;this.stats.fetched++;this.build(t);this.pump()},
        err=>{this.inflight--;t.state='error';t.error=String(err?.message||err);t.failedAt=performance.now();this.stats.failed++;this.pump();this.ask()});
    }
  }
  tileRect(z,x,y){const s=GEO_WORLD/2**z;const x0=x*s-GEO_WORLD/2,y1=GEO_WORLD/2-y*s;return [x0,y1-s,x0+s,y1]}
  wanted(){
    const c=this.cam,E=[c.x+this.e[0],c.y+this.e[1],this.e[2]];
    const poly=[[0,0],[this.w/2,0],[this.w,0],[this.w,this.h],[0,this.h]].map(([sx,sy])=>this.groundClamped(sx,sy));
    const K=(this.h/2)/Math.tan(GEO_FOV/2);let detail=330/K;const out=[];
    const xs=poly.map(p=>p[0]),ys=poly.map(p=>p[1]);const bb=[Math.min(...xs),Math.min(...ys),Math.max(...xs),Math.max(...ys)];
    const walk=(lim)=>{out.length=0;const stack=[[0,0,0]];
      while(stack.length){const [z,x,y]=stack.pop();const r=this.tileRect(z,x,y);
        if(r[2]<bb[0]||r[0]>bb[2]||r[3]<bb[1]||r[1]>bb[3])continue;
        if(z>=3&&!geoRectPoly(r,poly))continue;
        const dx=Math.max(r[0]-E[0],0,E[0]-r[2]),dy=Math.max(r[1]-E[1],0,E[1]-r[3]);const d=Math.hypot(dx,dy,E[2]);
        const s=r[2]-r[0];
        if(z<14&&(z<3||s/d>lim)){for(const [ox,oy] of [[0,0],[1,0],[0,1],[1,1]])stack.push([z+1,x*2+ox,y*2+oy]);continue}
        out.push({z,x,y,d:Math.hypot((r[0]+r[2])/2-c.x,(r[1]+r[3])/2-c.y)});
        if(out.length>400)return false}
      return true};
    for(let i=0;i<6;i++){if(walk(detail)&&out.length<=90)break;detail*=1.45}
    return out;
  }
  update(){
    this.frameNo=(this.frameNo||0)+1;
    const want=this.wanted();const now=performance.now();const draw=[],fall=new Set();
    for(const w of want){
      const key=w.z+'/'+w.x+'/'+w.y;let t=this.tiles.get(key);
      if(!t){t={key,z:w.z,x:w.x,y:w.y,state:'new'};this.tiles.set(key,t)}
      t.used=now;t.d=w.d;t.wanted=this.frameNo;
      if(t.state==='error'&&now-(t.failedAt||0)>15000)t.state='new';
      if(t.state==='new'){t.state='queued';this.queue.push(t)}
      if(t.state==='ready'&&t.rebuild&&t.chunk)this.build(t);
      if(t.bufs){draw.push(t);continue}
      // not here yet: an ancestor that is stands in (without its buildings)
      for(let z=w.z-1,x=w.x>>1,y=w.y>>1;z>=0&&z>=w.z-8;z--,x>>=1,y>>=1){const a=this.tiles.get(z+'/'+x+'/'+y);if(a?.bufs){fall.add(a);a.used=now;break}}
    }
    for(const t of this.queue)if(t.wanted!==this.frameNo&&t.state==='queued')t.state='new';
    this.pump();
    const fallList=[...fall].filter(t=>!draw.includes(t)).sort((a,b)=>a.z-b.z);fallList.forEach(t=>t.fallback=true);draw.forEach(t=>t.fallback=false);
    draw.sort((a,b)=>a.z-b.z);
    this.drawList=[...fallList,...draw].slice(0,250);
    this.pending=want.length-draw.length;
    // forget tiles nobody has looked at for a while
    if(this.tiles.size>260){const old=[...this.tiles.values()].filter(t=>t.wanted!==this.frameNo&&!['loading','building'].includes(t.state)).sort((a,b)=>a.used-b.used);
      for(const t of old.slice(0,this.tiles.size-220)){this.freeBufs(t);this.tiles.delete(t.key)}}
  }
  // --- coordinates: Web Mercator metres; the camera's target is the origin of everything drawn ------------------
  toXY(lat,lon){const la=Math.max(-85.05,Math.min(85.05,lat))*Math.PI/180;return [GEO_R*lon*Math.PI/180,GEO_R*Math.log(Math.tan(Math.PI/4+la/2))]}
  toLL(x,y){return [+(Math.atan(Math.sinh(y/GEO_R))*180/Math.PI).toFixed(6),+(x/GEO_R*180/Math.PI).toFixed(6)]}
  scaleAt(y){return Math.cosh(y/GEO_R)}          // Mercator metres per true metre at this northing
  // --- the camera -------------------------------------------------------------------------------------------
  eyeRel(){const c=this.cam,p=c.pitch*Math.PI/180,b=c.bearing*Math.PI/180;const fx=Math.sin(b),fy=Math.cos(b);
    return [-fx*c.dist*Math.sin(p),-fy*c.dist*Math.sin(p),c.dist*Math.cos(p)]}
  matrices(){
    const c=this.cam,b=c.bearing*Math.PI/180,e=this.eyeRel();const a=(this.w||1)/(this.h||1);
    const pr=c.pitch*Math.PI/180;
    // how far the ground is seen: the ray at the top of the screen, or a horizon kept in haze
    const topAng=pr+GEO_FOV/2*1.05;const reach=topAng<Math.PI/2-0.02?c.dist*Math.sin(pr)+Math.cos(pr)*c.dist*Math.tan(topAng):c.dist*16;
    this.reach=Math.min(Math.max(c.dist*1.6,reach),c.dist*16);
    const near=Math.max(0.5,c.dist*0.015),far=Math.hypot(this.reach,c.dist)*1.2;
    this.view=geoMat.look(e,[0,0,0],[Math.sin(b),Math.cos(b),0]);this.proj=geoMat.persp(GEO_FOV,a,near,far);
    this.mvp=geoMat.mul(this.proj,this.view);this.e=e;this.inv=null;
    // haze only where the ground runs toward a horizon; looking down there is none
    if(c.pitch<25)this.fog=[far*4,far*6];else{const end=this.reach*0.97;this.fog=[Math.min(Math.max(c.dist*1.3,this.reach*0.5),end*0.9),end]}
    this.px=2*Math.tan(GEO_FOV/2)/Math.max(1,this.h);
  }
  project(x,y,z=0){const m=this.mvp,p=[x-this.cam.x,y-this.cam.y,z];const X=m[0]*p[0]+m[4]*p[1]+m[8]*p[2]+m[12],Y=m[1]*p[0]+m[5]*p[1]+m[9]*p[2]+m[13],W=m[3]*p[0]+m[7]*p[1]+m[11]*p[2]+m[15];
    if(W<=0.01)return null;return [(X/W+1)/2*this.w,(1-Y/W)/2*this.h,W]}
  ray(sx,sy){
    const inv=this.inv||(this.inv=geoInvert(this.mvp));if(!inv)return null;
    const nx=sx/this.w*2-1,ny=1-sy/this.h*2;
    const un=(z)=>{const v=[nx,ny,z,1];const o=[0,0,0,0];for(let i=0;i<4;i++)for(let k=0;k<4;k++)o[i]+=inv[k*4+i]*v[k];return [o[0]/o[3],o[1]/o[3],o[2]/o[3]]};
    const a=un(-1),b=un(1);const d=[b[0]-a[0],b[1]-a[1],b[2]-a[2]];const dl=Math.hypot(...d);return {a,d:[d[0]/dl,d[1]/dl,d[2]/dl]};
  }
  // screen point -> ground (x, y) in absolute Mercator metres, or null above the horizon
  ground(sx,sy){if(!this.mvp)this.matrices();const r=this.ray(sx,sy);if(!r||r.d[2]>-1e-6)return null;const t=-r.a[2]/r.d[2];if(t<0)return null;
    const gx=r.a[0]+r.d[0]*t,gy=r.a[1]+r.d[1]*t;if(Math.hypot(gx,gy)>this.reach*1.05)return null;return [gx+this.cam.x,gy+this.cam.y]}
  groundClamped(sx,sy){const r=this.ray(sx,sy);if(!r)return [this.cam.x,this.cam.y];let gx,gy;
    if(r.d[2]<-1e-6){const t=-r.a[2]/r.d[2];gx=r.a[0]+r.d[0]*t;gy=r.a[1]+r.d[1]*t}else{const h=Math.hypot(r.d[0],r.d[1])||1;gx=r.a[0]+r.d[0]/h*this.reach;gy=r.a[1]+r.d[1]/h*this.reach}
    const L=Math.hypot(gx,gy);if(L>this.reach){gx*=this.reach/L;gy*=this.reach/L}return [gx+this.cam.x,gy+this.cam.y]}
  maxPitch(){const d=this.cam.dist;return d<30000?72:d>1500000?38:72-34*Math.log(d/30000)/Math.log(50)}
  clampCam(){const c=this.cam;c.dist=Math.max(25,Math.min(4.5e6,c.dist));c.pitch=Math.max(0,Math.min(this.maxPitch(),c.pitch));
    c.x=Math.max(-GEO_WORLD/2,Math.min(GEO_WORLD/2,c.x));c.y=Math.max(-GEO_WORLD*0.42,Math.min(GEO_WORLD*0.42,c.y));
    c.bearing=((c.bearing+540)%360)-180}
  flyTo(to,ms=900){
    (this.flights=this.flights||[]).push({t:Math.round(performance.now()),to:JSON.stringify(to)});this.flights=this.flights.slice(-8);
    const from={...this.cam};const target={...from,...to};
    if(Math.abs(target.bearing-from.bearing)>180)target.bearing+=target.bearing>from.bearing?-360:360;
    const far=Math.hypot(target.x-from.x,target.y-from.y);const top=Math.max(from.dist,target.dist,far*1.1);
    if(far>from.dist*3)ms=Math.max(ms,Math.min(2600,900+400*Math.log2(far/from.dist)));
    const start=performance.now(),reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
    this.anim={tick:now=>{const t=reduce?1:Math.min(1,(now-start)/ms),e=t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2;
      for(const k of ['x','y','pitch','bearing'])this.cam[k]=from[k]+(target[k]-from[k])*e;
      // far flights rise and come down (in log distance), so the ground slides by at a speed you can follow
      const ld=Math.log(from.dist)+(Math.log(target.dist)-Math.log(from.dist))*e;const rise=far>from.dist*1.5?Math.sin(Math.PI*e)*(Math.log(top)-Math.max(Math.log(from.dist),Math.log(target.dist))):0;
      this.cam.dist=Math.exp(ld+rise);this.clampCam();return t<1}};
    this.ask();
  }
  // Fly so a point sits in the middle of the part of the map nobody's panel covers.
  focusOn(x,y,dist,ms){
    const d=dist||this.cam.dist;let inset=0;const side=this.root?.closest('.gm-shell')?.querySelector('.gm-side:not([hidden])');
    if(side&&this.w>700){const r=side.getBoundingClientRect(),m=this.root.getBoundingClientRect();if(r.width)inset=Math.max(0,r.right-m.left)}
    const mpp=2*d*Math.tan(GEO_FOV/2)/Math.max(1,this.h);const b=this.cam.bearing*Math.PI/180;const shift=inset/2*mpp;
    this.flyTo({x:x-Math.cos(b)*shift,y:y+Math.sin(b)*shift,dist:d},ms);
  }
  flyAlong(pts){
    if(pts.length<2)return;const acc=[0];for(let i=1;i<pts.length;i++)acc.push(acc[i-1]+Math.hypot(pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1]));
    const total=acc[acc.length-1];if(total<1)return;const k=this.scaleAt(pts[0][1]);
    const at=s=>{s=Math.max(0,Math.min(total,s));let i=1;while(i<acc.length-1&&acc[i]<s)i++;const t=(s-acc[i-1])/Math.max(1e-6,acc[i]-acc[i-1]);return [pts[i-1][0]+(pts[i][0]-pts[i-1][0])*t,pts[i-1][1]+(pts[i][1]-pts[i-1][1])*t]};
    const head=s=>{const a=at(s),b=at(s+70*k);return Math.atan2(b[0]-a[0],b[1]-a[1])*180/Math.PI};
    if(matchMedia('(prefers-reduced-motion: reduce)').matches){const m=at(total/2);this.flyTo({x:m[0],y:m[1],dist:Math.max(400,total*0.9),pitch:30},0);return}
    const from={...this.cam},lead=900,ride=Math.max(5000,Math.min(18000,total/k/70*1000)),D=300*k;let start=null;
    this.anim={tick:now=>{if(start===null)start=now;const el=now-start;
      if(el<lead){const q=el/lead,e=q<.5?2*q*q:1-Math.pow(-2*q+2,2)/2;const p=at(0);let b=head(0);if(Math.abs(b-from.bearing)>180)b+=b>from.bearing?-360:360;
        Object.assign(this.cam,{x:from.x+(p[0]-from.x)*e,y:from.y+(p[1]-from.y)*e,dist:from.dist+(D-from.dist)*e,pitch:from.pitch+(58-from.pitch)*e,bearing:from.bearing+(b-from.bearing)*e});this.clampCam();return true}
      const q=Math.min(1,(el-lead)/ride),s=total*(q<.5?2*q*q:1-Math.pow(-2*q+2,2)/2);const p=at(s);
      let d=head(s)-this.cam.bearing;d=((d+540)%360)-180;this.cam.bearing+=d*0.06;this.cam.x=p[0];this.cam.y=p[1];this.cam.dist=D;this.cam.pitch=58;this.clampCam();return q<1}};
    this.ask();
  }
  // --- drawing ----------------------------------------------------------------------------------------------
  ask(){if(this.frameAsked)return;this.frameAsked=true;requestAnimationFrame(now=>{this.frameAsked=false;let again=false;
    if(this.anim){again=this.anim.tick(now);if(!again)this.anim=null}
    if(this.inertia){again=this.inertia(now)||again}
    this.draw();if(again)this.ask()})}
  draw(){
    if(!this.root||!this.root.isConnected||!this.w)return;
    if(!this.gl){this.matrices();this.overlayDraw();return}
    if(this.lost)return;
    const t0=performance.now();
    this.matrices();this.update();
    const gl=this.gl,P=this.palette;const sky=geoHex(P.sky);
    gl.viewport(0,0,this.canvas.width,this.canvas.height);gl.clearColor(sky[0],sky[1],sky[2],1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
    gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);
    this.pass(false);
    this.overlayDraw();
    this.frameMs=performance.now()-t0;
  }
  uniforms(p,pick,t){
    const gl=this.gl,u=p.u;gl.useProgram(p.p);
    gl.uniformMatrix4fv(u.uMVP,false,new Float32Array(this.mvp));gl.uniform3f(u.uEye,...this.e);
    if(u.uFog)gl.uniform2f(u.uFog,...this.fog);if(u.uHaze){const h=geoHex(this.palette.haze);gl.uniform3f(u.uHaze,h[0],h[1],h[2])}
    if(u.uMode)gl.uniform1f(u.uMode,pick?1:0);if(u.uLift)gl.uniform1f(u.uLift,this.lift);if(u.uAlpha)gl.uniform1f(u.uAlpha,1);if(u.uTint)gl.uniform4f(u.uTint,0,0,0,0);
    if(u.uPx)gl.uniform1f(u.uPx,this.px);if(u.uSun)gl.uniform3f(u.uSun,...this.palette.sun);
    if(u.uOff)gl.uniform2f(u.uOff,0,0);if(u.uSel)gl.uniform1f(u.uSel,0);if(u.uHover)gl.uniform1f(u.uHover,0);if(u.uSlot)gl.uniform1f(u.uSlot,0);
  }
  tileU(p,t,slot,pick){const gl=this.gl,u=p.u;
    if(u.uOff)gl.uniform2f(u.uOff,t.origin[0]-this.cam.x,t.origin[1]-this.cam.y);
    if(u.uSlot)gl.uniform1f(u.uSlot,slot);
    if(u.uSel)gl.uniform1f(u.uSel,this.selRef?t.ids?.get(this.selRef)||0:0);
    if(u.uHover)gl.uniform1f(u.uHover,!pick&&this.hoverRef?t.ids?.get(this.hoverRef)||0:0)}
  bind(buf,layout){const gl=this.gl;gl.bindBuffer(gl.ARRAY_BUFFER,buf.b);let off=0;
    layout.forEach((n,i)=>{gl.enableVertexAttribArray(i);gl.vertexAttribPointer(i,n,gl.FLOAT,false,buf.stride*4,off*4);off+=n});
    for(let i=layout.length;i<6;i++)gl.disableVertexAttribArray(i)}
  pass(pick){
    const gl=this.gl,hide=this.hidden,list=this.drawList;
    const FLAT=[3,4,1],LINE=[2,2,2,1,3,1];
    gl.disable(gl.DEPTH_TEST);gl.depthMask(false);
    // 0. the ground itself, to the horizon: nothing behind the world shows through
    this.uniforms(this.pFlat,pick);
    if(!pick){const R=this.reach*1.3,l=geoHex(this.palette.land);const v=[];for(const [x,y] of [[-R,-R],[R,-R],[R,R],[-R,-R],[R,R],[-R,R]])v.push(x,y,0,l[0],l[1],l[2],1,0);
      gl.bindBuffer(gl.ARRAY_BUFFER,this.groundBuf);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(v),gl.DYNAMIC_DRAW);this.bind({b:this.groundBuf,stride:8},FLAT);gl.drawArrays(gl.TRIANGLES,0,6)}
    // 1. areas, tile by tile (stand-ins first, so the real tiles cover them)
    list.forEach((t,i)=>{this.tileU(this.pFlat,t,i+1,pick);this.bind(t.bufs.areas,FLAT);gl.drawArrays(gl.TRIANGLES,0,t.bufs.areas.n)});
    // 2. building shadows, soft and low
    if(!pick&&!hide.has('ground:buildings')&&!hide.has('ground:shadows')&&this.palette.shadow&&this.cam.dist<6000){
      gl.uniform1f(this.pFlat.u.uAlpha,this.palette.shadow);gl.uniform4f(this.pFlat.u.uTint,0.12,0.1,0.14,1);
      // depth keeps overlapping shadow pieces from darkening twice (all lie at z=0; the first one wins)
      gl.enable(gl.DEPTH_TEST);gl.depthFunc(gl.LESS);gl.depthMask(true);
      list.forEach((t,i)=>{if(t.fallback||!t.bufs.shadows.n)return;this.tileU(this.pFlat,t,i+1,pick);this.bind(t.bufs.shadows,FLAT);gl.drawArrays(gl.TRIANGLES,0,t.bufs.shadows.n)});
      gl.disable(gl.DEPTH_TEST);gl.depthMask(false);gl.uniform1f(this.pFlat.u.uAlpha,1);gl.uniform4f(this.pFlat.u.uTint,0,0,0,0);
    }
    // 3. roads and rivers: casings for all tiles, then fills for all tiles
    if(!hide.has('ground:streets')){
      this.uniforms(this.pLine,pick);
      list.forEach((t,i)=>{if(!t.bufs.casings.n)return;this.tileU(this.pLine,t,i+1,pick);this.bind(t.bufs.casings,LINE);gl.drawArrays(gl.TRIANGLES,0,t.bufs.casings.n)});
      list.forEach((t,i)=>{if(!t.bufs.lines.n)return;this.tileU(this.pLine,t,i+1,pick);this.bind(t.bufs.lines,LINE);gl.drawArrays(gl.TRIANGLES,0,t.bufs.lines.n)});
    }
    // 4. routes from layers (and the one being planned), above the streets
    if(this.routeBuf&&this.routeBuf.n&&!pick){this.uniforms(this.pLine,false);gl.uniform2f(this.pLine.u.uOff,this.routeOrigin[0]-this.cam.x,this.routeOrigin[1]-this.cam.y);
      this.bind(this.routeBuf,LINE);gl.drawArrays(gl.TRIANGLES,0,this.routeBuf.n)}
    // 5. buildings, with depth
    if(!hide.has('ground:buildings')&&this.cam.dist<30000){
      gl.enable(gl.DEPTH_TEST);gl.depthFunc(gl.LEQUAL);gl.depthMask(true);
      this.uniforms(this.pBld,pick);
      list.forEach((t,i)=>{if(t.fallback||!t.bufs.buildings.n)return;this.tileU(this.pBld,t,i+1,pick);this.bind(t.bufs.buildings,[3,3,3,1,1]);gl.drawArrays(gl.TRIANGLES,0,t.bufs.buildings.n)});
      if(!pick&&this.cam.dist<2600&&this.lift>0.2){this.uniforms(this.pEdge,false);gl.uniform4f(this.pEdge.u.uCol,...this.palette.edge);gl.depthMask(false);
        list.forEach((t,i)=>{if(t.fallback||!t.bufs.edges.n)return;this.tileU(this.pEdge,t,i+1,false);this.bind(t.bufs.edges,[3,1]);gl.drawArrays(gl.LINES,0,t.bufs.edges.n)})}
      // a route behind buildings shows faintly through them
      if(!pick&&this.routeBuf&&this.routeBuf.n){this.uniforms(this.pLine,false);gl.uniform2f(this.pLine.u.uOff,this.routeOrigin[0]-this.cam.x,this.routeOrigin[1]-this.cam.y);
        gl.depthFunc(gl.GREATER);gl.depthMask(false);gl.uniform1f(this.pLine.u.uAlpha,0.3);this.bind(this.routeBuf,LINE);gl.drawArrays(gl.TRIANGLES,0,this.routeBuf.n);gl.uniform1f(this.pLine.u.uAlpha,1)}
      gl.depthFunc(gl.LESS);gl.disable(gl.DEPTH_TEST);
    }
  }
  pickAt(sx,sy){
    if(!this.gl||!this.drawList.length)return null;const gl=this.gl;const W=this.canvas.width,H=this.canvas.height;
    if(!this.pickFb||this.pickFb.w!==W||this.pickFb.h!==H){
      if(this.pickFb){gl.deleteFramebuffer(this.pickFb.fb);gl.deleteTexture(this.pickFb.tex);gl.deleteRenderbuffer(this.pickFb.depth)}
      const fb=gl.createFramebuffer(),tex=gl.createTexture(),depth=gl.createRenderbuffer();
      gl.bindTexture(gl.TEXTURE_2D,tex);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,W,H,0,gl.RGBA,gl.UNSIGNED_BYTE,null);
      gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);
      gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
      gl.bindRenderbuffer(gl.RENDERBUFFER,depth);gl.renderbufferStorage(gl.RENDERBUFFER,gl.DEPTH_COMPONENT16,W,H);
      gl.bindFramebuffer(gl.FRAMEBUFFER,fb);gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.COLOR_ATTACHMENT0,gl.TEXTURE_2D,tex,0);
      gl.framebufferRenderbuffer(gl.FRAMEBUFFER,gl.DEPTH_ATTACHMENT,gl.RENDERBUFFER,depth);this.pickFb={fb,tex,depth,w:W,h:H};
      if(gl.checkFramebufferStatus(gl.FRAMEBUFFER)!==gl.FRAMEBUFFER_COMPLETE){gl.bindFramebuffer(gl.FRAMEBUFFER,null);this.pickFb=null;return null}
    }
    gl.bindFramebuffer(gl.FRAMEBUFFER,this.pickFb.fb);
    const px=Math.round(sx*this.dpr),py=Math.round(H-sy*this.dpr);
    gl.viewport(0,0,W,H);gl.enable(gl.SCISSOR_TEST);gl.scissor(px,py,1,1);gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
    gl.disable(gl.BLEND);this.matrices();this.pass(true);
    const out=new Uint8Array(4);gl.readPixels(px,py,1,1,gl.RGBA,gl.UNSIGNED_BYTE,out);
    gl.disable(gl.SCISSOR_TEST);gl.bindFramebuffer(gl.FRAMEBUFFER,null);gl.enable(gl.BLEND);
    if(!out[3]||!out[2])return null;const t=this.drawList[out[2]-1];const what=t?.picks?.[out[0]+out[1]*256];
    if(!what)return null;
    // a street's piece knows its class; its name is the nearest street name of that tile
    if(what.type==='street'&&!what.name&&t.labels){const g=this.ground(sx,sy);if(g){let best=null;
      for(const l of t.labels)if(l.type==='street'){const d=Math.hypot(t.origin[0]+l.x-g[0],t.origin[1]+l.y-g[1]);if(!best||d<best.d)best={d,name:l.text}}
      if(best&&best.d<400*this.scaleAt(g[1]))return {...what,name:best.name}}}
    return what;
  }
  // --- data from the world: layers and their placed things --------------------------------------------------
  setLayers(rows,hidden){
    this.hidden=new Set(String(hidden||'').split(/\s+/).filter(Boolean));
    this.head=rows.find(r=>r.kind==='map')||{};this.layers=rows.filter(r=>r.kind!=='map');
    this.items=[];this.routes=[];
    for(const L of this.layers){
      const off=this.hidden.has(L.id)||String(L.on||'yes')==='no'&&!this.hidden.has('show:'+L.id);
      for(const it of L.items||[]){
        if(off)continue;
        if(it.kind==='route'&&it.path){this.routes.push({...it,color:it.color||L.color||'#6c5bb3',layer:L})}
        this.items.push({...it,layer:L,color:it.color||L.color||'#cf5a3c',look:it.kind==='route'?'flag':(L.look==='path'?'pin':L.look||'pin')})
      }
    }
    this.buildRoutes();this.ask();
  }
  buildRoutes(){
    if(!this.gl)return;const out=[];
    const all=[...this.routes.map(r=>({pts:geoParsePath(r.path).map(([la,lo])=>this.toXY(la,lo)),col:geoHex(r.color),sel:r.id===this.selectedId}))];
    if(this.preview)all.push({pts:this.preview.map(([la,lo])=>this.toXY(la,lo)),col:geoHex('#2f7f8f'),sel:true});
    const o=all[0]?.pts[0]||[this.cam.x,this.cam.y];this.routeOrigin=o;
    for(const r of all){const rel=r.pts.map(([x,y])=>[x-o[0],y-o[1]]);const k=this.scaleAt(o[1]);
      geoLineJS(out,rel,(r.sel?6:4.5)*k,r.sel?4.2:3.2,[1,1,1]);geoLineJS(out,rel,(r.sel?4:3)*k,r.sel?2.8:2.1,r.col)}
    const gl=this.gl;if(this.routeBuf)gl.deleteBuffer(this.routeBuf.b);this.routeBuf=out.length?this.buffer(new Float32Array(out),11):null;
  }
  // --- the overlay: names and pins, placed each frame from the camera ----------------------------------------
  overlayDraw(){
    const ov=this.overlay;ov.dataset.state=this.drawList.length?'ready':'loading';
    const used=[],fits=(x,y,w,h)=>{for(const r of used)if(x<r[2]&&x+w>r[0]&&y<r[3]&&y+h>r[1])return false;used.push([x,y,x+w,y+h]);return true};
    const showNames=!this.hidden.has('ground:labels'),showPlaces=!this.hidden.has('ground:places');
    const k=this.scaleAt(this.cam.y),trueDist=this.cam.dist/k;
    // pins first: they always show, and claim their room
    const seenPins=new Set(),placedPins=[],buckets=new Map();
    for(const it of this.items){
      const [x,y]=this.toXY(it.lat,it.lon);const s=this.project(x,y,0);
      if(s&&s[0]>-40&&s[1]>-40&&s[0]<this.w+40&&s[1]<this.h+60){const key=Math.round(s[0]/9)+','+Math.round(s[1]/9);const b=buckets.get(key)||[];b.push(it.id);buckets.set(key,b);placedPins.push([it,s,b])}
      else placedPins.push([it,null,null]);
    }
    for(const [it,s,bucket] of placedPins){
      let el=this.pinEls.get(it.id);
      if(!el){el=this.pinEl(it);this.pinEls.set(it.id,el);ov.append(el)}else if(el._rev!==it.rev+'|'+it.color+'|'+(it.title||it.name)+'|'+it.look){const n=this.pinEl(it);el.replaceWith(n);this.pinEls.set(it.id,n);el=n}
      seenPins.add(it.id);
      if(!s||s[2]>this.reach*1.1||this.dragging===it.id){if(this.dragging!==it.id)el.style.display='none';continue}
      if(bucket.length>1){const i=bucket.indexOf(it.id);s[0]+=(i-(bucket.length-1)/2)*22}
      el.style.display='';el.style.transform=`translate(${s[0].toFixed(1)}px,${s[1].toFixed(1)}px)`;el.style.zIndex=String(Math.max(1,100000-Math.round(s[2])));
      el.classList.toggle('gm-selected',it.id===this.selectedId);
      el.classList.toggle('gm-near',trueDist<700&&(bucket.length<2||bucket.indexOf(it.id)===0&&!bucket.includes(this.selectedId)));
      el.classList.toggle('gm-far',trueDist>40000);
      used.push([s[0]-12,s[1]-34,s[0]+12,s[1]+2]);
    }
    for(const [id,el] of this.pinEls)if(!seenPins.has(id)){el.remove();this.pinEls.delete(id)}
    // names: towns, then streets (rotated), then places by kind; each only where it fits
    const cand=[];
    for(const t of this.drawList){if(t.fallback&&t.z<10)continue;const [ox,oy]=t.origin;
      if(showNames&&t.labels&&t.z>=13&&trueDist<4500)for(const l of t.labels){if(l.rank>2&&trueDist>1300)continue;if(l.rank>1&&trueDist>2600)continue;cand.push({...l,x:ox+l.x,y:oy+l.y,pri:2+l.rank,tile:t.key})}
      if(t.places)for(const p of t.places){
        if(p.kind==='town'){if(!showNames)continue;cand.push({...p,x:ox+p.x,y:oy+p.y,tile:t.key});continue}
        if(!showPlaces)continue;
        if(p.kind==='poi'){if(trueDist>1600||t.z<14)continue;const cat=geoCat(p.what);if(cat==='other'&&trueDist>700)continue;if(cat==='shop'&&trueDist>900)continue;
          cand.push({...p,x:ox+p.x,y:oy+p.y,pri:p.pri+(cat==='community'||cat==='nature'?-0.6:0),cat,tile:t.key});continue}
        if(trueDist<120000)cand.push({...p,x:ox+p.x,y:oy+p.y,cat:p.kind==='water'?'water':'nature',tile:t.key})}}
    cand.sort((a,b)=>a.pri-b.pri);
    const seen=new Set();let shown=0;
    for(const c of cand){
      if(shown>150)break;
      const key=c.type+':'+c.text+':'+(c.type==='street'?c.tile+':'+Math.round(c.x):Math.round(c.x/50)+':'+Math.round(c.y/50));
      if(seen.has(key))continue;
      const s=this.project(c.x,c.y,0);if(!s||s[2]>this.reach||s[0]<-50||s[1]<-20||s[0]>this.w+50||s[1]>this.h+20)continue;
      const big=c.kind==='town'&&c.what in {country:1,state:1,city:1};
      const w=c.text.length*(c.type==='street'?6.2:big?8.4:6.6)+(c.kind==='poi'?14:0),h=c.type==='street'?14:big?20:16;
      let ang=0;
      if(c.type==='street'){const d=20*this.scaleAt(c.y);const a=this.project(c.x+Math.cos(c.ang)*d,c.y+Math.sin(c.ang)*d,0),b=this.project(c.x-Math.cos(c.ang)*d,c.y-Math.sin(c.ang)*d,0);if(!a||!b)continue;ang=Math.atan2(a[1]-b[1],a[0]-b[0]);if(ang>Math.PI/2)ang-=Math.PI;if(ang<-Math.PI/2)ang+=Math.PI}
      const ext=Math.abs(Math.cos(ang))*w+Math.abs(Math.sin(ang))*h,exty=Math.abs(Math.sin(ang))*w+Math.abs(Math.cos(ang))*h;
      if(!fits(s[0]-ext/2-3,s[1]-exty/2-2,ext+6,exty+4))continue;
      let el=this.labelEls.get(key);
      if(!el){el=this.labelEl(c);this.labelEls.set(key,el);ov.append(el)}
      seen.add(key);shown++;el.style.display='';const far=this.reach;const fade=1-Math.max(0,Math.min(1,(s[2]-far*0.55)/(far*0.4)));el.style.opacity=fade.toFixed(2);
      el.style.transform=`translate(${s[0].toFixed(1)}px,${s[1].toFixed(1)}px) translate(-50%,-50%) rotate(${ang.toFixed(3)}rad)`;
    }
    for(const [k2,el] of this.labelEls)if(!seen.has(k2)){el.style.display='none';if(this.labelEls.size>600){el.remove();this.labelEls.delete(k2)}}
    this.overlayExtras?.();
  }
  labelEl(c){
    const el=document.createElement('div');
    if(c.type==='street'){el.className='gm-street';el.textContent=c.text;return el}
    if(c.kind==='town'){el.className='gm-town';el.dataset.what=c.what;el.textContent=c.text;return el}
    el.className='gm-place';el.dataset.cat=c.cat||'other';el.innerHTML='<i></i><span></span>';el.lastChild.textContent=c.text;el.title=c.text+' · '+String(c.what||'').replace(/_/g,' ');
    el._place=c;return el;
  }
  pinEl(it){
    const el=document.createElement('button');el.type='button';el.className='gm-pin gm-look-'+(it.look||'pin')+(it.approx?' gm-approx':'');
    el.dataset.component='geo-map';el.dataset.part='pin';el.dataset.path=this.api?.node?.path||'';
    const facts={kind:it.kind,layer:(it.layer&&it.layer.name||'').toLowerCase().replace(/[^a-z0-9-]+/g,'-'),look:it.look,approx:it.approx?'yes':'no'};
    for(const [k,v] of Object.entries(facts))if(v)el.setAttribute('data-fact-'+k,String(v));
    el.style.color=it.color;el._item=it;el._rev=it.rev+'|'+it.color+'|'+(it.title||it.name)+'|'+it.look;
    const label=it.title||it.name||it.label||(it.text?String(it.text).slice(0,40):'')||it.kind;
    el.setAttribute('aria-label',label+(it.layer?.name?' · '+it.layer.name:'')+(it.approx?' · approximate place':''));
    el.innerHTML='<span class="gm-pin-shadow"></span><span class="gm-pin-head"></span><span class="gm-pin-label"></span>';
    el.querySelector('.gm-pin-label').textContent=label;
    if(it.kind==='event'&&it.start){const when=geoWhen(it.start);if(when)el.querySelector('.gm-pin-label').textContent=label+' · '+when}
    return el;
  }
  // --- input ------------------------------------------------------------------------------------------------
  listen(){
    const cv=this.canvas,ov=this.overlay;
    cv.addEventListener('contextmenu',e=>e.preventDefault());
    cv.addEventListener('wheel',e=>{e.preventDefault();this.anim=null;const k=Math.exp(e.deltaY*(e.deltaMode?0.05:0.0015));
      const r=this.root.getBoundingClientRect();const before=this.ground(e.clientX-r.left,e.clientY-r.top);this.cam.dist*=k;this.clampCam();this.matrices();
      const after=this.ground(e.clientX-r.left,e.clientY-r.top);if(before&&after){this.cam.x+=before[0]-after[0];this.cam.y+=before[1]-after[1];this.clampCam()}this.ask()},{passive:false});
    cv.addEventListener('pointerdown',e=>this.down(e));cv.addEventListener('pointermove',e=>this.move(e));
    cv.addEventListener('pointerup',e=>this.up(e));cv.addEventListener('pointercancel',e=>this.up(e,true));
    cv.addEventListener('pointerleave',()=>{if(this.hoverRef){this.hoverRef='';this.ask()}this.tip(null)});
    cv.addEventListener('dblclick',e=>{const r=this.root.getBoundingClientRect();const g=this.ground(e.clientX-r.left,e.clientY-r.top);if(g)this.flyTo({x:g[0],y:g[1],dist:this.cam.dist*0.5},500)});
    cv.addEventListener('keydown',e=>this.key(e));
    ov.addEventListener('pointerdown',e=>{const pin=e.target.closest('.gm-pin');if(pin)this.pinDown(e,pin)});
    ov.addEventListener('click',e=>{const place=e.target.closest('.gm-place');if(!place||!place._place)return;const c=place._place;const [lat,lon]=this.toLL(c.x,c.y);
      this.onPress?.({type:'place',what:{type:'place',name:c.text,what:c.what,cat:c.cat},lat,lon})});
  }
  down(e){
    this.canvas.focus({preventScroll:true});this.anim=null;this.inertia=null;
    this.canvas.setPointerCapture(e.pointerId);this.pointers.set(e.pointerId,{x:e.clientX,y:e.clientY,sx:e.clientX,sy:e.clientY,t:performance.now()});
    this.mode=(e.button===2||e.ctrlKey||e.button===1)?'turn':'pan';this.moved=0;this.vel=[0,0];
    if(this.pointers.size===2){this.mode='pinch';const [a,b]=[...this.pointers.values()];this.pinch={d:Math.hypot(a.x-b.x,a.y-b.y),ang:Math.atan2(b.y-a.y,b.x-a.x),dist:this.cam.dist,bearing:this.cam.bearing}}
  }
  move(e){
    const p=this.pointers.get(e.pointerId);const r=this.root.getBoundingClientRect();
    if(!p){this.hoverAt(e.clientX-r.left,e.clientY-r.top);return}
    const dx=e.clientX-p.x,dy=e.clientY-p.y;this.moved+=Math.abs(dx)+Math.abs(dy);
    if(this.mode==='pinch'&&this.pointers.size===2){p.x=e.clientX;p.y=e.clientY;const [a,b]=[...this.pointers.values()];
      const d=Math.hypot(a.x-b.x,a.y-b.y),ang=Math.atan2(b.y-a.y,b.x-a.x);this.cam.dist=this.pinch.dist*this.pinch.d/Math.max(10,d);this.cam.bearing=this.pinch.bearing-(ang-this.pinch.ang)*180/Math.PI;this.clampCam();this.ask();return}
    if(this.mode==='turn'){this.cam.bearing-=dx*0.3;this.cam.pitch+=dy*0.25;this.clampCam()}
    else{const a=this.ground(p.x-r.left,p.y-r.top),b=this.ground(e.clientX-r.left,e.clientY-r.top);
      if(a&&b){this.cam.x+=a[0]-b[0];this.cam.y+=a[1]-b[1];const now=performance.now(),dt=Math.max(8,now-p.t);this.vel=[(a[0]-b[0])/dt,(a[1]-b[1])/dt];p.t=now;this.clampCam();this.matrices()}}
    p.x=e.clientX;p.y=e.clientY;this.ask();
  }
  up(e,cancel){
    const p=this.pointers.get(e.pointerId);this.pointers.delete(e.pointerId);if(!p)return;
    if(this.pointers.size)return;
    const r=this.root.getBoundingClientRect();
    if(!cancel&&this.moved<6&&this.mode!=='pinch'){this.press(e.clientX-r.left,e.clientY-r.top,e);return}
    if(this.mode==='pan'&&!matchMedia('(prefers-reduced-motion: reduce)').matches){let [vx,vy]=this.vel;let last=performance.now();
      if(Math.hypot(vx,vy)>0.05*this.cam.dist/1000)this.inertia=now=>{const dt=now-last;last=now;this.cam.x+=vx*dt;this.cam.y+=vy*dt;const k=Math.pow(0.992,dt);vx*=k;vy*=k;this.clampCam();
        if(Math.hypot(vx,vy)<0.01*this.cam.dist/1000){this.inertia=null;return false}return true};this.ask()}
  }
  hoverAt(x,y){const now=performance.now();if(now-(this.lastHover||0)<90)return;this.lastHover=now;
    const what=this.pickAt(x,y);const ref=what?.ref||'';if(ref!==this.hoverRef){this.hoverRef=ref;this.ask()}
    this.tip(what?{x,y,text:geoDescribe(what)}:null)}
  tip(t){let el=this.tipEl;if(!t){if(el)el.hidden=true;return}if(!el){el=this.tipEl=document.createElement('div');el.className='gm-tip';el.setAttribute('role','tooltip')}
    if(el.parentNode!==this.overlay)this.overlay.append(el);el.hidden=false;el.textContent=t.text;el.style.transform=`translate(${t.x+14}px,${t.y+12}px)`}
  press(x,y,e){
    const g=this.ground(x,y);const ll=g?this.toLL(g[0],g[1]):null;
    const what=this.pickAt(x,y);
    this.onPress?.({type:what?what.type:'ground',what,lat:ll?.[0],lon:ll?.[1],x,y,shift:e?.shiftKey});
  }
  pinDown(e,pin){
    e.stopPropagation();const it=pin._item;const start={x:e.clientX,y:e.clientY};let dragging=false;
    pin.setPointerCapture(e.pointerId);
    const r=this.root.getBoundingClientRect();
    const tip=pin.getBoundingClientRect();const grab={x:tip.left-e.clientX,y:tip.top-e.clientY};
    const canMove=it.kind!=='route'&&it.kind!=='structure'&&(it.lat!=null)&&!it.at;
    const mv=ev=>{if(!dragging&&Math.hypot(ev.clientX-start.x,ev.clientY-start.y)>6&&canMove){dragging=true;this.dragging=it.id;pin.classList.add('gm-dragging')}
      if(dragging){pin.style.transform=`translate(${ev.clientX+grab.x-r.left}px,${ev.clientY+grab.y-r.top}px)`}};
    const done=ev=>{pin.removeEventListener('pointermove',mv);pin.removeEventListener('pointerup',done);pin.removeEventListener('pointercancel',done);
      this.dragging=null;pin.classList.remove('gm-dragging');
      if(!dragging){this.onPin?.(it,ev);return}
      if(ev.type==='pointercancel'){this.ask();return}
      const g=this.ground(ev.clientX+grab.x-r.left,ev.clientY+grab.y-r.top);if(!g){this.ask();return}
      const [lat,lon]=this.toLL(g[0],g[1]);it.lat=lat;it.lon=lon;this.ask();this.onMove?.(it,lat,lon)};
    pin.addEventListener('pointermove',mv);pin.addEventListener('pointerup',done);pin.addEventListener('pointercancel',done);
  }
  key(e){
    const step=this.cam.dist*0.12,b=this.cam.bearing*Math.PI/180;let used=true;
    const pan=(f,s)=>{this.cam.x+=Math.sin(b)*f+Math.cos(b)*s;this.cam.y+=Math.cos(b)*f-Math.sin(b)*s};
    switch(e.key){case 'ArrowUp':case 'w':pan(step,0);break;case 'ArrowDown':case 's':pan(-step,0);break;case 'ArrowLeft':case 'a':pan(0,-step);break;case 'ArrowRight':case 'd':pan(0,step);break;
      case '+':case '=':this.flyTo({dist:this.cam.dist*0.7},250);break;case '-':case '_':this.flyTo({dist:this.cam.dist/0.7},250);break;
      case 'q':this.cam.bearing-=10;break;case 'e':this.cam.bearing+=10;break;case 'n':this.flyTo({bearing:0},400);break;
      case 't':this.flyTo({pitch:this.cam.pitch>10?0:52},450);break;case 'Escape':this.onEscape?.();break;default:used=false}
    if(used){e.preventDefault();this.clampCam();this.ask()}
  }
}
// a line for the line program, from JS (routes): points relative to an origin; stride 11 like the worker's
function geoLineJS(out,P,hw,minPx,col){
  if(P.length<2)return;const N=[];
  for(let i=0;i<P.length;i++){const a=P[Math.max(0,i-1)],b=P[i],c=P[Math.min(P.length-1,i+1)];
    let d1=[b[0]-a[0],b[1]-a[1]],d2=[c[0]-b[0],c[1]-b[1]];const n1=Math.hypot(...d1)||1,n2=Math.hypot(...d2)||1;d1=[d1[0]/n1,d1[1]/n1];d2=[d2[0]/n2,d2[1]/n2];
    if(i===0)d1=d2;if(i===P.length-1)d2=d1;let tx=d1[0]+d2[0],ty=d1[1]+d2[1];const tl=Math.hypot(tx,ty);if(tl<1e-3){tx=d1[0];ty=d1[1]}else{tx/=tl;ty/=tl}
    const nx=-ty,ny=tx;const dot=nx*(-d1[1])+ny*d1[0];const m=Math.min(1/Math.max(dot,.4),2.5);N.push([nx*m,ny*m])}
  const V=(p,n)=>out.push(p[0],p[1],n[0],n[1],hw,minPx,9,col[0],col[1],col[2],0);
  for(let i=0;i<P.length-1;i++){const a=P[i],b=P[i+1],na=N[i],nb=N[i+1];V(a,na);V(a,[-na[0],-na[1]]);V(b,nb);V(a,[-na[0],-na[1]]);V(b,[-nb[0],-nb[1]]);V(b,nb)}
  for(const p of [P[0],P[P.length-1]])for(let s=0;s<8;s++){const a0=s*Math.PI/4,a1=a0+Math.PI/4;V(p,[0,0]);V(p,[Math.cos(a0),Math.sin(a0)]);V(p,[Math.cos(a1),Math.sin(a1)])}
}
// does a rectangle [x0,y0,x1,y1] meet a convex polygon (screen corners on the ground)?
function geoRectPoly(r,poly){
  const inR=p=>p[0]>=r[0]&&p[0]<=r[2]&&p[1]>=r[1]&&p[1]<=r[3];if(poly.some(inR))return true;
  const corners=[[r[0],r[1]],[r[2],r[1]],[r[2],r[3]],[r[0],r[3]]];
  const inP=q=>{let s=0;for(let i=0;i<poly.length;i++){const a=poly[i],b=poly[(i+1)%poly.length];const c=(b[0]-a[0])*(q[1]-a[1])-(b[1]-a[1])*(q[0]-a[0]);if(c!==0){if(s===0)s=Math.sign(c);else if(Math.sign(c)!==s)return false}}return true};
  if(corners.some(inP))return true;
  const cross=(a,b,c,d)=>{const o=(p,q,r)=>Math.sign((q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0]));return o(a,b,c)!==o(a,b,d)&&o(c,d,a)!==o(c,d,b)};
  for(let i=0;i<poly.length;i++)for(let j=0;j<4;j++)if(cross(poly[i],poly[(i+1)%poly.length],corners[j],corners[(j+1)%4]))return true;
  return false;
}
function geoInvert(m){const inv=new Array(16);
  inv[0]=m[5]*m[10]*m[15]-m[5]*m[11]*m[14]-m[9]*m[6]*m[15]+m[9]*m[7]*m[14]+m[13]*m[6]*m[11]-m[13]*m[7]*m[10];
  inv[4]=-m[4]*m[10]*m[15]+m[4]*m[11]*m[14]+m[8]*m[6]*m[15]-m[8]*m[7]*m[14]-m[12]*m[6]*m[11]+m[12]*m[7]*m[10];
  inv[8]=m[4]*m[9]*m[15]-m[4]*m[11]*m[13]-m[8]*m[5]*m[15]+m[8]*m[7]*m[13]+m[12]*m[5]*m[11]-m[12]*m[7]*m[9];
  inv[12]=-m[4]*m[9]*m[14]+m[4]*m[10]*m[13]+m[8]*m[5]*m[14]-m[8]*m[6]*m[13]-m[12]*m[5]*m[10]+m[12]*m[6]*m[9];
  inv[1]=-m[1]*m[10]*m[15]+m[1]*m[11]*m[14]+m[9]*m[2]*m[15]-m[9]*m[3]*m[14]-m[13]*m[2]*m[11]+m[13]*m[3]*m[10];
  inv[5]=m[0]*m[10]*m[15]-m[0]*m[11]*m[14]-m[8]*m[2]*m[15]+m[8]*m[3]*m[14]+m[12]*m[2]*m[11]-m[12]*m[3]*m[10];
  inv[9]=-m[0]*m[9]*m[15]+m[0]*m[11]*m[13]+m[8]*m[1]*m[15]-m[8]*m[3]*m[13]-m[12]*m[1]*m[11]+m[12]*m[3]*m[9];
  inv[13]=m[0]*m[9]*m[14]-m[0]*m[10]*m[13]-m[8]*m[1]*m[14]+m[8]*m[2]*m[13]+m[12]*m[1]*m[10]-m[12]*m[2]*m[9];
  inv[2]=m[1]*m[6]*m[15]-m[1]*m[7]*m[14]-m[5]*m[2]*m[15]+m[5]*m[3]*m[14]+m[13]*m[2]*m[7]-m[13]*m[3]*m[6];
  inv[6]=-m[0]*m[6]*m[15]+m[0]*m[7]*m[14]+m[4]*m[2]*m[15]-m[4]*m[3]*m[14]-m[12]*m[2]*m[7]+m[12]*m[3]*m[6];
  inv[10]=m[0]*m[5]*m[15]-m[0]*m[7]*m[13]-m[4]*m[1]*m[15]+m[4]*m[3]*m[13]+m[12]*m[1]*m[7]-m[12]*m[3]*m[5];
  inv[14]=-m[0]*m[5]*m[14]+m[0]*m[6]*m[13]+m[4]*m[1]*m[14]-m[4]*m[2]*m[13]-m[12]*m[1]*m[6]+m[12]*m[2]*m[5];
  inv[3]=-m[1]*m[6]*m[11]+m[1]*m[7]*m[10]+m[5]*m[2]*m[11]-m[5]*m[3]*m[10]-m[9]*m[2]*m[7]+m[9]*m[3]*m[6];
  inv[7]=m[0]*m[6]*m[11]-m[0]*m[7]*m[10]-m[4]*m[2]*m[11]+m[4]*m[3]*m[10]+m[8]*m[2]*m[7]-m[8]*m[3]*m[6];
  inv[11]=-m[0]*m[5]*m[11]+m[0]*m[7]*m[9]+m[4]*m[1]*m[11]-m[4]*m[3]*m[9]-m[8]*m[1]*m[7]+m[8]*m[3]*m[5];
  inv[15]=m[0]*m[5]*m[10]-m[0]*m[6]*m[9]-m[4]*m[1]*m[10]+m[4]*m[2]*m[9]+m[8]*m[1]*m[6]-m[8]*m[2]*m[5];
  let det=m[0]*inv[0]+m[1]*inv[4]+m[2]*inv[8]+m[3]*inv[12];if(!det)return null;det=1/det;return inv.map(v=>v*det)}
function geoParsePath(text){return String(text||'').trim().split(/\s+/).map(p=>p.split(',').map(Number)).filter(p=>p.length===2&&p.every(Number.isFinite))}
function geoWhen(iso){const d=new Date(iso);if(isNaN(d))return '';const now=new Date();const days=Math.round((new Date(d.toDateString())-new Date(now.toDateString()))/864e5);
  const t=d.toLocaleTimeString([],{hour:'numeric',minute:'2-digit'});if(days===0)return 'today '+t;if(days===1)return 'tomorrow '+t;if(days>1&&days<7)return d.toLocaleDateString([],{weekday:'short'})+' '+t;return d.toLocaleDateString([],{month:'short',day:'numeric'})}
function geoDescribe(w){if(!w)return '';if(w.type==='building'){const n=w.name||(w.number?w.number+(w.street?' '+w.street:''):'');return (n||('A '+(String(w.what||'building').replace(/_/g,' '))))+(w.src&&!/OpenStreetMap/.test(w.src)?' · traced from imagery':'')}
  if(w.type==='street')return w.name||String(w.what||'a street');return (w.name||String(w.what||'')).replace(/_/g,' ')}
