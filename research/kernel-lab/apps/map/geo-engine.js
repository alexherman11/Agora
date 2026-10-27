// The map surface's engine: WebGL drawing of a ground, a camera, picking, and a DOM overlay for names and pins.
// It lives in the geo-map part's api.draft, so a repaint of the window moves it to the new part instead of rebuilding.
// It draws only when something changes (input, data, a fly); there is no running loop.
const GEO_PALETTES={
  light:{land:'#efe8da',skyTop:'#bfe2f1',skyLow:'#eef2ea',haze:[0.93,0.95,0.92],edge:[0.33,0.26,0.2,0.32],shadow:0.15,
    area:{sea:'#8fcbe3',water:'#9bd3ea',pool:'#8ad3ef',marina:'#a6d6e8',beach:'#f3e2b0',park:'#bfe0a6',green:'#cbe6b4',wood:'#a3d18f',
      wetland:'#b9dcc2',pitch:'#acd893',play:'#ecdcb0',parking:'#e6e1d8',residential:'#efe8d9',commercial:'#f2e3d8',industrial:'#e7e0d8',school:'#f1e4c8'},
    road:{major:'#fffaf0',street:'#fffdf8',service:'#fbf7ef',walk:'#f7efe1',path:'#d6c4a0',cycle:'#b5d5c4',steps:'#c9a98a'},
    casing:{major:'#d6bf9b',street:'#dcd0bc',service:'#e2d8c8',walk:'#ddd0b8'},rail:'#a39a90',railTie:'#7d746b',chalk:'#ffffff',rim:'#86b56f',
    buildings:['#f2d7b8','#efcfa9','#f4e0c4','#e9d2bd','#f0d5c9','#e5d9bf','#f3dcb0','#ead0b3'],
    roof:['#d9876b','#c97b62','#b8846c','#a7907e','#d39a72','#8f9aa3','#c56f5b','#9c8b7a']},
  dark:{land:'#2b302d',skyTop:'#18202d',skyLow:'#2c3640',haze:[0.17,0.21,0.24],edge:[0.05,0.05,0.06,0.5],shadow:0.22,
    area:{sea:'#1d3a4e',water:'#24475c',pool:'#2a5d75',marina:'#244457',beach:'#5b5242',park:'#35503a',green:'#3a553e',wood:'#2f4a33',
      wetland:'#34503f',pitch:'#3b5a3b',play:'#4f4a3c',parking:'#353937',residential:'#2f3431',commercial:'#36322f',industrial:'#323432',school:'#38352d'},
    road:{major:'#5d6058',street:'#4f534d',service:'#474a45',walk:'#4a4a42',path:'#5a5243',cycle:'#3f5a4e',steps:'#5c4c3f'},
    casing:{major:'#3a3c37',street:'#383a35',service:'#353732',walk:'#383630'},rail:'#6b655f',railTie:'#4c4741',chalk:'#9fb59a',rim:'#4f6e46',
    buildings:['#6d6358','#665c52','#71675b','#5f5850','#6a5e57','#635d51'],
    roof:['#7a4f43','#6c4a3f','#5f5148','#55524f','#6e5648','#4d555c']},
};
const GEO_SHADERS={
  flatV:`attribute vec3 aPos;attribute vec4 aCol;attribute float aPick;
uniform mat4 uMVP;uniform vec2 uT;uniform float uR;uniform vec3 uEye;varying vec4 vCol;varying float vPick;varying float vD;
vec3 bend(vec3 p){if(uR<=0.0)return p;vec2 d=p.xy-uT;float L=length(d);if(L<0.001)return p;float th=L/uR;float r=uR+p.z;return vec3(uT+d/L*r*sin(th),r*cos(th)-uR);}
void main(){vec3 b=bend(aPos);vCol=aCol;vPick=aPick;vD=distance(b,uEye);gl_Position=uMVP*vec4(b,1.0);}`,
  flatF:`precision mediump float;varying vec4 vCol;varying float vPick;varying float vD;
uniform float uMode;uniform float uAlpha;uniform vec2 uFog;uniform vec3 uHaze;uniform float uSel;uniform float uHover;uniform vec4 uTint;
vec4 enc(float id){return vec4(mod(id,256.0)/255.0,mod(floor(id/256.0),256.0)/255.0,floor(id/65536.0)/255.0,1.0);}
void main(){if(uMode>0.5){if(vPick<0.5)discard;gl_FragColor=enc(vPick);return;}
vec3 c=vCol.rgb;if(uTint.a>0.0)c=uTint.rgb;
if(vPick>0.5&&abs(vPick-uSel)<0.5)c=mix(c,vec3(1.0,0.78,0.35),0.45);else if(vPick>0.5&&abs(vPick-uHover)<0.5)c=mix(c,vec3(1.0),0.25);
float f=smoothstep(uFog.x,uFog.y,vD);gl_FragColor=vec4(mix(c,uHaze,f*0.85),vCol.a*uAlpha);}`,
  bldV:`attribute vec3 aPos;attribute vec3 aNorm;attribute vec3 aCol;attribute float aPick;attribute float aPart;
uniform mat4 uMVP;uniform vec2 uT;uniform float uR;uniform vec3 uEye;uniform float uLift;
varying vec3 vCol;varying vec3 vN;varying float vPick;varying float vPart;varying float vD;varying float vZ;
vec3 bend(vec3 p){if(uR<=0.0)return p;vec2 d=p.xy-uT;float L=length(d);if(L<0.001)return p;float th=L/uR;float r=uR+p.z;return vec3(uT+d/L*r*sin(th),r*cos(th)-uR);}
void main(){vec3 p=aPos;p.z*=uLift;vec3 b=bend(p);vCol=aCol;vN=aNorm;vPick=aPick;vPart=aPart;vZ=p.z;vD=distance(b,uEye);gl_Position=uMVP*vec4(b,1.0);}`,
  bldF:`precision mediump float;varying vec3 vCol;varying vec3 vN;varying float vPick;varying float vPart;varying float vD;varying float vZ;
uniform float uMode;uniform vec2 uFog;uniform vec3 uHaze;uniform float uSel;uniform float uHover;uniform vec3 uSun;
vec4 enc(float id){return vec4(mod(id,256.0)/255.0,mod(floor(id/256.0),256.0)/255.0,floor(id/65536.0)/255.0,1.0);}
void main(){if(uMode>0.5){gl_FragColor=enc(vPick);return;}
float dif=max(dot(normalize(vN),uSun),0.0);vec3 c=vCol;
if(vPart>1.5)c=c*(0.9+0.12*dif);else{c=c*(0.62+0.48*dif);c*=mix(0.8,1.0,smoothstep(0.0,3.5,vZ));}
if(abs(vPick-uSel)<0.5)c=mix(c,vec3(1.0,0.8,0.4),0.5);else if(abs(vPick-uHover)<0.5)c=mix(c,vec3(1.0),0.22);
float f=smoothstep(uFog.x,uFog.y,vD);gl_FragColor=vec4(mix(c,uHaze,f*0.85),1.0);}`,
  edgeV:`attribute vec3 aPos;attribute float aKind;uniform mat4 uMVP;uniform vec2 uT;uniform float uR;uniform vec3 uEye;uniform float uLift;varying float vD;
vec3 bend(vec3 p){if(uR<=0.0)return p;vec2 d=p.xy-uT;float L=length(d);if(L<0.001)return p;float th=L/uR;float r=uR+p.z;return vec3(uT+d/L*r*sin(th),r*cos(th)-uR);}
void main(){vec3 p=aPos;p.z*=uLift;vec3 b=bend(p);vD=distance(b,uEye);gl_Position=uMVP*vec4(b,1.0);gl_Position.z-=0.0004*gl_Position.w;}`,
  edgeF:`precision mediump float;varying float vD;uniform vec4 uCol;uniform vec2 uFog;void main(){float f=smoothstep(uFog.x,uFog.y*0.7,vD);gl_FragColor=vec4(uCol.rgb,uCol.a*(1.0-f));}`,
};
const geoMat={
  persp(fovy,a,n,f){const t=1/Math.tan(fovy/2),nf=1/(n-f);return [t/a,0,0,0,0,t,0,0,0,0,(f+n)*nf,-1,0,0,2*f*n*nf,0]},
  look(e,c,u){let z=[e[0]-c[0],e[1]-c[1],e[2]-c[2]];let l=Math.hypot(...z);z=z.map(v=>v/l);
    let x=[u[1]*z[2]-u[2]*z[1],u[2]*z[0]-u[0]*z[2],u[0]*z[1]-u[1]*z[0]];l=Math.hypot(...x)||1;x=x.map(v=>v/l);
    const y=[z[1]*x[2]-z[2]*x[1],z[2]*x[0]-z[0]*x[2],z[0]*x[1]-z[1]*x[0]];
    return [x[0],y[0],z[0],0,x[1],y[1],z[1],0,x[2],y[2],z[2],0,-(x[0]*e[0]+x[1]*e[1]+x[2]*e[2]),-(y[0]*e[0]+y[1]*e[1]+y[2]*e[2]),-(z[0]*e[0]+z[1]*e[1]+z[2]*e[2]),1]},
  mul(a,b){const o=new Array(16);for(let i=0;i<4;i++)for(let j=0;j<4;j++){let s=0;for(let k=0;k<4;k++)s+=a[k*4+j]*b[i*4+k];o[i*4+j]=s}return o},
};
const GEO_CATS={food:['cafe','restaurant','fast_food','bar','pub','ice_cream','biergarten','food_court'],
  nature:['park','garden','beach','playground','nature_reserve','dog_park','wood','water','viewpoint','pitch','wetland'],
  community:['library','school','place_of_worship','community_centre','theatre','museum','arts_centre','townhall','post_office','social_facility','kindergarten','college','marina'],
  move:['bus_stop','fuel','parking','bicycle_rental','boat_rental','car_rental','charging_station']};
function geoCat(c){c=String(c||'');if(c.startsWith('shop:'))return 'shop';for(const [k,v] of Object.entries(GEO_CATS))if(v.includes(c))return k;return 'other'}

class GeoEngine{
  constructor(workerSource){
    this.workerSource=workerSource;
    this.canvas=document.createElement('canvas');this.canvas.className='gm-canvas';this.canvas.tabIndex=0;
    this.canvas.setAttribute('aria-label','Map. Drag to move, scroll to zoom, right-drag to turn. Arrow keys move; + and - zoom; Q and E turn.');
    this.overlay=document.createElement('div');this.overlay.className='gm-overlay';
    this.cam={x:0,y:0,dist:1150,pitch:50,bearing:-12};this.curve=2400;this.lift=1;
    this.data=null;this.layers=[];this.hidden=new Set();this.items=[];this.routes=[];this.preview=null;
    this.sel=0;this.hover=0;this.selectedId='';this.tool='look';this.stops=[];this.draft=null;
    this.labelEls=new Map();this.pinEls=new Map();this.dirty=true;this.frameAsked=false;this.status='Drawing the map…';
    this.dark=false;this.palette=GEO_PALETTES.light;this.listeners=false;this.pointers=new Map();this.anim=null;
  }
  // --- placing in the DOM ---------------------------------------------------------------------------------
  attach(root,api){
    this.api=api;this.root=root;root.append(this.canvas,this.overlay);
    // a repaint disposes the old part's timers, including a frame this engine had asked for: ask again
    this.frameAsked=false;
    if(!this.listeners){this.listen();this.listeners=true}
    if(this.ro)this.ro.disconnect();
    this.ro=new ResizeObserver(()=>this.resize());this.ro.observe(root);
    api.cleanup(()=>this.ro&&this.ro.disconnect());
    this.resize();
  }
  resize(){
    const r=this.root?.getBoundingClientRect();if(!r||!r.width)return;
    const dpr=Math.min(2,window.devicePixelRatio||1);this.dpr=dpr;this.w=r.width;this.h=r.height;
    const W=Math.round(r.width*dpr),H=Math.round(r.height*dpr);
    if(this.canvas.width!==W||this.canvas.height!==H){this.canvas.width=W;this.canvas.height=H;this.pickFb=null}
    this.ask();
  }
  // --- GL ---------------------------------------------------------------------------------------------------
  initGL(){
    if(this.gl!==undefined)return !!this.gl;
    const opts={antialias:true,alpha:true,premultipliedAlpha:false,preserveDrawingBuffer:false};
    const gl=this.canvas.getContext('webgl2',opts)||this.canvas.getContext('webgl',opts);this.gl=gl||null;
    if(!gl){this.status='This screen has no WebGL, so the map cannot draw in 3D here.';return false}
    const prog=(v,f,attrs)=>{const p=gl.createProgram();for(const [src,type] of [[v,gl.VERTEX_SHADER],[f,gl.FRAGMENT_SHADER]]){const s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error('Map shader: '+gl.getShaderInfoLog(s));gl.attachShader(p,s)}
      attrs.forEach((a,i)=>gl.bindAttribLocation(p,i,a));gl.linkProgram(p);if(!gl.getProgramParameter(p,gl.LINK_STATUS))throw Error('Map program: '+gl.getProgramInfoLog(p));
      const u={};const n=gl.getProgramParameter(p,gl.ACTIVE_UNIFORMS);for(let i=0;i<n;i++){const info=gl.getActiveUniform(p,i);u[info.name]=gl.getUniformLocation(p,info.name)}return {p,u}};
    this.pFlat=prog(GEO_SHADERS.flatV,GEO_SHADERS.flatF,['aPos','aCol','aPick']);
    this.pBld=prog(GEO_SHADERS.bldV,GEO_SHADERS.bldF,['aPos','aNorm','aCol','aPick','aPart']);
    this.pEdge=prog(GEO_SHADERS.edgeV,GEO_SHADERS.edgeF,['aPos','aKind']);
    this.canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();this.status='The map lost its drawing surface; it comes back by itself.';this.lost=true});
    this.canvas.addEventListener('webglcontextrestored',()=>{this.gl=undefined;this.lost=false;this.buffers=null;this.initGL();if(this.data)this.upload(this.data);this.ask()});
    return true;
  }
  buffer(arr,stride){const gl=this.gl,b=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,b);gl.bufferData(gl.ARRAY_BUFFER,arr,gl.STATIC_DRAW);return {b,n:arr.length/stride,stride}}
  upload(d){
    if(!this.gl)return;const B=this.buffers={};
    B.areas=this.buffer(d.areas,8);B.roads=this.buffer(d.roads,8);B.shadows=this.buffer(d.shadows,8);
    B.buildings=this.buffer(d.buildings,11);B.edges=this.buffer(d.edges,4);
  }
  // --- loading a ground -------------------------------------------------------------------------------------
  load(text,dark){
    if(this.loading)return this.loading;
    this.dark=!!dark;this.palette=dark?GEO_PALETTES.dark:GEO_PALETTES.light;
    this.loadCount=(this.loadCount||0)+1;
    this.loading=new Promise((resolve,reject)=>{
      const url=URL.createObjectURL(new Blob(['('+this.workerSource+')()'],{type:'text/javascript'}));
      let worker;try{worker=new Worker(url)}catch(e){URL.revokeObjectURL(url);reject(e);return}
      worker.onmessage=e=>{URL.revokeObjectURL(url);worker.terminate();
        if(e.data.error){this.status='The ground could not be read: '+e.data.error;reject(Error(e.data.error));return}
        this.data=e.data;this.status='';resolve(e.data)};
      worker.onerror=e=>{URL.revokeObjectURL(url);worker.terminate();this.status='The map builder stopped: '+(e.message||'error');reject(Error(e.message))};
      worker.postMessage({ground:text,palette:this.palette});
    });
    return this.loading;
  }
  frame0(){const b=this.data.bounds;return {x:(b[0]+b[2])/2,y:(b[1]+b[3])/2}}
  toXY(lat,lon){const f=this.data.frame;return [(lon-f.origin.lon)*f.m_per_deg_lon,(lat-f.origin.lat)*f.m_per_deg_lat]}
  toLL(x,y){const f=this.data.frame;return [+(f.origin.lat+y/f.m_per_deg_lat).toFixed(6),+(f.origin.lon+x/f.m_per_deg_lon).toFixed(6)]}
  // --- the camera -------------------------------------------------------------------------------------------
  eye(){const c=this.cam,p=c.pitch*Math.PI/180,b=c.bearing*Math.PI/180;const fx=Math.sin(b),fy=Math.cos(b);
    return [c.x-fx*c.dist*Math.sin(p),c.y-fy*c.dist*Math.sin(p),c.dist*Math.cos(p)]}
  matrices(){
    const c=this.cam,b=c.bearing*Math.PI/180,e=this.eye();const a=(this.w||1)/(this.h||1);
    const near=Math.max(2,c.dist*0.03),far=c.dist*8+6000;
    this.view=geoMat.look(e,[c.x,c.y,0],[Math.sin(b),Math.cos(b),0]);this.proj=geoMat.persp(40*Math.PI/180,a,near,far);
    this.mvp=geoMat.mul(this.proj,this.view);this.e=e;this.R=this.curve>0?this.curve*Math.max(1,c.dist/1500):0;
    this.fog=[c.dist*1.15,c.dist*4.2];
  }
  bend(x,y,z=0){if(!this.R)return [x,y,z];const dx=x-this.cam.x,dy=y-this.cam.y,L=Math.hypot(dx,dy);if(L<1e-3)return [x,y,z];const th=L/this.R,r=this.R+z;return [this.cam.x+dx/L*r*Math.sin(th),this.cam.y+dy/L*r*Math.sin(th),r*Math.cos(th)-this.R]}
  project(x,y,z=0){const p=this.bend(x,y,z),m=this.mvp;const X=m[0]*p[0]+m[4]*p[1]+m[8]*p[2]+m[12],Y=m[1]*p[0]+m[5]*p[1]+m[9]*p[2]+m[13],W=m[3]*p[0]+m[7]*p[1]+m[11]*p[2]+m[15];
    if(W<=0.01)return null;return [(X/W+1)/2*this.w,(1-Y/W)/2*this.h,W]}
  // screen point -> ground (x, y): a ray against the curved ground (a sphere under the camera's target), or the plane
  ground(sx,sy){
    const c=this.cam;const inv=geoInvert(this.mvp);if(!inv)return null;
    const nx=sx/this.w*2-1,ny=1-sy/this.h*2;
    const un=(z)=>{const v=[nx,ny,z,1];const o=[0,0,0,0];for(let i=0;i<4;i++)for(let k=0;k<4;k++)o[i]+=inv[k*4+i]*v[k];return [o[0]/o[3],o[1]/o[3],o[2]/o[3]]};
    const a=un(-1),b=un(1);const d=[b[0]-a[0],b[1]-a[1],b[2]-a[2]];const dl=Math.hypot(...d);d[0]/=dl;d[1]/=dl;d[2]/=dl;
    if(!this.R){if(Math.abs(d[2])<1e-6)return null;const t=-a[2]/d[2];if(t<0)return null;return [a[0]+d[0]*t,a[1]+d[1]*t]}
    const C=[c.x,c.y,-this.R],o=[a[0]-C[0],a[1]-C[1],a[2]-C[2]];const B=o[0]*d[0]+o[1]*d[1]+o[2]*d[2],CC=o[0]**2+o[1]**2+o[2]**2-this.R*this.R;const disc=B*B-CC;if(disc<0)return null;
    const t=-B-Math.sqrt(disc);if(t<0)return null;const s=[o[0]+d[0]*t,o[1]+d[1]*t,o[2]+d[2]*t];const hz=Math.hypot(s[0],s[1]);const th=Math.atan2(hz,s[2]);const L=this.R*th;
    return hz<1e-6?[c.x,c.y]:[c.x+s[0]/hz*L,c.y+s[1]/hz*L];
  }
  clampCam(){const c=this.cam;c.dist=Math.max(70,Math.min(5200,c.dist));c.pitch=Math.max(0,Math.min(68,c.pitch));
    if(this.data){const [x0,y0,x1,y1]=this.data.bounds;c.x=Math.max(x0-300,Math.min(x1+300,c.x));c.y=Math.max(y0-300,Math.min(y1+300,c.y))}
    c.bearing=((c.bearing+540)%360)-180}
  flyTo(to,ms=900){
    (this.flights=this.flights||[]).push({t:Math.round(performance.now()),to:JSON.stringify(to),why:String(new Error().stack).split(/\n/)[2]?.trim().slice(0,90)});this.flights=this.flights.slice(-8);
    const from={...this.cam};const target={...from,...to};
    if(Math.abs(target.bearing-from.bearing)>180)target.bearing+=target.bearing>from.bearing?-360:360;
    const start=performance.now(),reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
    this.anim={tick:now=>{const t=reduce?1:Math.min(1,(now-start)/ms),e=t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2;
      // arc: rise a little mid-flight when travelling far
      const far=Math.hypot(target.x-from.x,target.y-from.y);const lift=Math.sin(Math.PI*e)*Math.min(far*0.6,900);
      for(const k of ['x','y','dist','pitch','bearing'])this.cam[k]=from[k]+(target[k]-from[k])*e;this.cam.dist+=lift*(1-Math.abs(target.dist-from.dist)/Math.max(target.dist,from.dist));
      this.clampCam();return t<1}};
    this.ask();
  }
  // Fly so a point sits in the middle of the part of the map nobody's panel covers (the shell's side column).
  focusOn(x,y,dist,ms){
    const d=dist||this.cam.dist;let inset=0;const side=this.root?.closest('.gm-shell:not(.gm-folded)')?.querySelector('.gm-side');
    if(side&&this.w>700){const r=side.getBoundingClientRect(),m=this.root.getBoundingClientRect();inset=Math.max(0,r.right-m.left)}
    const mpp=2*d*Math.tan(20*Math.PI/180)/Math.max(1,this.h);const b=this.cam.bearing*Math.PI/180;const shift=inset/2*mpp;
    this.flyTo({x:x-Math.cos(b)*shift,y:y+Math.sin(b)*shift,dist:d},ms);
  }
  flyAlong(pts){
    if(pts.length<2)return;const acc=[0];for(let i=1;i<pts.length;i++)acc.push(acc[i-1]+Math.hypot(pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1]));
    const total=acc[acc.length-1];if(total<1)return;
    const at=s=>{s=Math.max(0,Math.min(total,s));let i=1;while(i<acc.length-1&&acc[i]<s)i++;const t=(s-acc[i-1])/Math.max(1e-6,acc[i]-acc[i-1]);return [pts[i-1][0]+(pts[i][0]-pts[i-1][0])*t,pts[i-1][1]+(pts[i][1]-pts[i-1][1])*t]};
    const head=s=>{const a=at(s),b=at(s+70);return Math.atan2(b[0]-a[0],b[1]-a[1])*180/Math.PI};
    if(matchMedia('(prefers-reduced-motion: reduce)').matches){const m=at(total/2);this.flyTo({x:m[0],y:m[1],dist:Math.max(400,total*0.9),pitch:30},0);return}
    const from={...this.cam},lead=900,ride=Math.max(5000,Math.min(18000,total/70*1000));let start=null;
    this.anim={tick:now=>{if(start===null)start=now;const el=now-start;
      if(el<lead){const k=el/lead,e=k<.5?2*k*k:1-Math.pow(-2*k+2,2)/2;const p=at(0);let b=head(0);if(Math.abs(b-from.bearing)>180)b+=b>from.bearing?-360:360;
        Object.assign(this.cam,{x:from.x+(p[0]-from.x)*e,y:from.y+(p[1]-from.y)*e,dist:from.dist+(280-from.dist)*e,pitch:from.pitch+(58-from.pitch)*e,bearing:from.bearing+(b-from.bearing)*e});this.clampCam();return true}
      const k=Math.min(1,(el-lead)/ride),s=total*(k<.5?2*k*k:1-Math.pow(-2*k+2,2)/2);const p=at(s);
      let d=head(s)-this.cam.bearing;d=((d+540)%360)-180;this.cam.bearing+=d*0.06;this.cam.x=p[0];this.cam.y=p[1];this.cam.dist=280;this.cam.pitch=58;this.clampCam();return k<1}};
    this.ask();
  }
  // --- drawing ----------------------------------------------------------------------------------------------
  ask(){if(this.frameAsked)return;this.frameAsked=true;requestAnimationFrame(now=>{this.frameAsked=false;let again=false;
    if(this.anim){again=this.anim.tick(now);if(!again)this.anim=null}
    if(this.inertia){again=this.inertia(now)||again}
    this.draw();if(again)this.ask()})}
  draw(){
    if(!this.root||!this.root.isConnected)return;
    if(!this.gl||!this.buffers||this.lost){this.overlayDraw();return}
    const gl=this.gl,P=this.palette;this.matrices();
    gl.viewport(0,0,this.canvas.width,this.canvas.height);gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
    gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);
    this.pass(false);
    this.overlayDraw();
  }
  uniforms(p,pick){
    const gl=this.gl,u=p.u;gl.useProgram(p.p);
    gl.uniformMatrix4fv(u.uMVP,false,new Float32Array(this.mvp));gl.uniform2f(u.uT,this.cam.x,this.cam.y);gl.uniform1f(u.uR,this.R||0);
    gl.uniform3f(u.uEye,...this.e);if(u.uFog)gl.uniform2f(u.uFog,...this.fog);if(u.uHaze)gl.uniform3f(u.uHaze,...this.palette.haze);
    if(u.uMode)gl.uniform1f(u.uMode,pick?1:0);if(u.uSel)gl.uniform1f(u.uSel,this.sel||0);if(u.uHover)gl.uniform1f(u.uHover,pick?0:this.hover||0);
    if(u.uLift)gl.uniform1f(u.uLift,this.lift);if(u.uAlpha)gl.uniform1f(u.uAlpha,1);if(u.uTint)gl.uniform4f(u.uTint,0,0,0,0);
  }
  bind(buf,layout){const gl=this.gl;gl.bindBuffer(gl.ARRAY_BUFFER,buf.b);let off=0;
    layout.forEach((n,i)=>{gl.enableVertexAttribArray(i);gl.vertexAttribPointer(i,n,gl.FLOAT,false,buf.stride*4,off*4);off+=n});
    for(let i=layout.length;i<6;i++)gl.disableVertexAttribArray(i)}
  pass(pick){
    const gl=this.gl,B=this.buffers,hide=this.hidden;
    const FLAT=[3,4,1];
    this.uniforms(this.pFlat,pick);gl.disable(gl.DEPTH_TEST);gl.depthMask(false);
    if(!hide.has('ground:green')||true){this.bind(B.areas,FLAT);gl.drawArrays(gl.TRIANGLES,0,B.areas.n)}
    if(!hide.has('ground:streets')){this.bind(B.roads,FLAT);gl.drawArrays(gl.TRIANGLES,0,B.roads.n)}
    // routes from layers, under the buildings, then a faint ghost where buildings hide them
    if(this.routeBuf&&this.routeBuf.n){this.bind(this.routeBuf,FLAT);gl.drawArrays(gl.TRIANGLES,0,this.routeBuf.n)}
    if(!pick&&!hide.has('ground:buildings')){
      gl.enable(gl.DEPTH_TEST);gl.depthFunc(gl.LESS);gl.depthMask(true);
      gl.uniform1f(this.pFlat.u.uAlpha,this.palette.shadow);gl.uniform4f(this.pFlat.u.uTint,0.12,0.1,0.14,1);
      this.bind(B.shadows,FLAT);gl.drawArrays(gl.TRIANGLES,0,B.shadows.n);
      gl.uniform1f(this.pFlat.u.uAlpha,1);gl.uniform4f(this.pFlat.u.uTint,0,0,0,0);
    }
    if(!hide.has('ground:buildings')){
      gl.enable(gl.DEPTH_TEST);gl.depthFunc(gl.LEQUAL);gl.depthMask(true);
      this.uniforms(this.pBld,pick);gl.uniform3f(this.pBld.u.uSun,-0.55,-0.42,0.72);
      this.bind(B.buildings,[3,3,3,1,1]);gl.drawArrays(gl.TRIANGLES,0,B.buildings.n);
      if(!pick&&this.cam.dist<2600){this.uniforms(this.pEdge,false);gl.uniform4f(this.pEdge.u.uCol,...this.palette.edge);
        gl.depthMask(false);this.bind(B.edges,[3,1]);gl.drawArrays(gl.LINES,0,B.edges.n)}
      if(!pick&&this.routeBuf&&this.routeBuf.n){this.uniforms(this.pFlat,false);gl.depthFunc(gl.GREATER);gl.depthMask(false);
        gl.uniform1f(this.pFlat.u.uAlpha,0.28);this.bind(this.routeBuf,FLAT);gl.drawArrays(gl.TRIANGLES,0,this.routeBuf.n);gl.uniform1f(this.pFlat.u.uAlpha,1)}
      gl.depthFunc(gl.LESS);
    }
  }
  pickAt(sx,sy){
    if(!this.gl||!this.buffers)return 0;const gl=this.gl;const W=this.canvas.width,H=this.canvas.height;
    if(!this.pickFb||this.pickFb.w!==W||this.pickFb.h!==H){
      if(this.pickFb){gl.deleteFramebuffer(this.pickFb.fb);gl.deleteTexture(this.pickFb.tex);gl.deleteRenderbuffer(this.pickFb.depth)}
      const fb=gl.createFramebuffer(),tex=gl.createTexture(),depth=gl.createRenderbuffer();
      gl.bindTexture(gl.TEXTURE_2D,tex);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,W,H,0,gl.RGBA,gl.UNSIGNED_BYTE,null);
      gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);
      gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
      gl.bindRenderbuffer(gl.RENDERBUFFER,depth);gl.renderbufferStorage(gl.RENDERBUFFER,gl.DEPTH_COMPONENT16,W,H);
      gl.bindFramebuffer(gl.FRAMEBUFFER,fb);gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.COLOR_ATTACHMENT0,gl.TEXTURE_2D,tex,0);
      gl.framebufferRenderbuffer(gl.FRAMEBUFFER,gl.DEPTH_ATTACHMENT,gl.RENDERBUFFER,depth);this.pickFb={fb,tex,depth,w:W,h:H};
      if(gl.checkFramebufferStatus(gl.FRAMEBUFFER)!==gl.FRAMEBUFFER_COMPLETE){gl.bindFramebuffer(gl.FRAMEBUFFER,null);this.pickFb=null;return 0}
    }
    gl.bindFramebuffer(gl.FRAMEBUFFER,this.pickFb.fb);
    const px=Math.round(sx*this.dpr),py=Math.round(H-sy*this.dpr);
    gl.viewport(0,0,W,H);gl.enable(gl.SCISSOR_TEST);gl.scissor(px,py,1,1);gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
    gl.disable(gl.BLEND);this.matrices();this.pass(true);
    const out=new Uint8Array(4);gl.readPixels(px,py,1,1,gl.RGBA,gl.UNSIGNED_BYTE,out);
    gl.disable(gl.SCISSOR_TEST);gl.bindFramebuffer(gl.FRAMEBUFFER,null);gl.enable(gl.BLEND);
    return out[3]?out[0]+out[1]*256+out[2]*65536:0;
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
    if(!this.gl||!this.data)return;const out=[];
    const push=(pts,w,col,z)=>{if(pts.length<2)return;const h=w/2;
      for(let i=0;i<pts.length-1;i++){const [ax,ay]=pts[i],[bx,by]=pts[i+1];const dx=bx-ax,dy=by-ay,l=Math.hypot(dx,dy)||1;const nx=-dy/l*h,ny=dx/l*h;
        const q=[[ax+nx,ay+ny],[ax-nx,ay-ny],[bx+nx,by+ny],[ax-nx,ay-ny],[bx-nx,by-ny],[bx+nx,by+ny]];for(const p of q)out.push(p[0],p[1],z,...col,0)}
      for(const [x,y] of pts)for(let s=0;s<8;s++){const a0=s*Math.PI/4,a1=a0+Math.PI/4;out.push(x,y,z,...col,0,x+Math.cos(a0)*h,y+Math.sin(a0)*h,z,...col,0,x+Math.cos(a1)*h,y+Math.sin(a1)*h,z,...col,0)}};
    const hex=h=>{h=String(h).replace('#','');if(h.length===3)h=h.split('').map(c=>c+c).join('');const n=parseInt(h,16)||0;return [(n>>16&255)/255,(n>>8&255)/255,(n&255)/255,1]};
    const all=[...this.routes.map(r=>({pts:geoParsePath(r.path).map(([la,lo])=>this.toXY(la,lo)),col:hex(r.color),sel:r.id===this.selectedId}))];
    if(this.preview)all.push({pts:this.preview.map(([la,lo])=>this.toXY(la,lo)),col:hex('#2f7f8f'),sel:true});
    for(const r of all){push(r.pts,r.sel?11:9,[1,1,1,0.95],0.5);push(r.pts,r.sel?7:5.5,r.col,0.55)}
    const gl=this.gl;if(this.routeBuf)gl.deleteBuffer(this.routeBuf.b);this.routeBuf=out.length?this.buffer(new Float32Array(out),8):null;
  }
  // --- the overlay: names and pins, placed each frame from the camera ----------------------------------------
  overlayDraw(){
    const ov=this.overlay;if(!this.data){ov.dataset.state='loading';return}
    ov.dataset.state='ready';if(!this.mvp)this.matrices();
    const used=[],fits=(x,y,w,h)=>{for(const r of used)if(x<r[2]&&x+w>r[0]&&y<r[3]&&y+h>r[1])return false;used.push([x,y,x+w,y+h]);return true};
    const far=this.fog[1]*0.75,showNames=!this.hidden.has('ground:labels'),showPlaces=!this.hidden.has('ground:places');
    // pins first: they always show, and claim their room
    const seenPins=new Set(),placedPins=[],buckets=new Map();
    for(const it of this.items){
      const [x,y]=this.toXY(it.lat,it.lon);const s=this.project(x,y,0);
      if(s){const k=Math.round(s[0]/9)+','+Math.round(s[1]/9);const b=buckets.get(k)||[];b.push(it.id);buckets.set(k,b);placedPins.push([it,s,b])}
      else placedPins.push([it,null,null]);
    }
    for(const [it,s,bucket] of placedPins){
      let el=this.pinEls.get(it.id);
      if(!el){el=this.pinEl(it);this.pinEls.set(it.id,el);ov.append(el)}else if(el._rev!==it.rev+'|'+it.color+'|'+(it.title||it.name)){const n=this.pinEl(it);el.replaceWith(n);this.pinEls.set(it.id,n);el=n}
      seenPins.add(it.id);
      if(!s||s[2]>far*1.4||this.dragging===it.id){if(this.dragging!==it.id)el.style.display='none';continue}
      // things at the same spot fan out side by side, so each can be pressed
      if(bucket.length>1){const i=bucket.indexOf(it.id);s[0]+=(i-(bucket.length-1)/2)*22}
      el.style.display='';el.style.transform=`translate(${s[0].toFixed(1)}px,${s[1].toFixed(1)}px)`;el.style.zIndex=String(10000-Math.round(s[2]));
      el.classList.toggle('gm-selected',it.id===this.selectedId);
      // in a fanned group only the first (or the selected) shows its name, so names never pile up
      el.classList.toggle('gm-near',this.cam.dist<650&&(bucket.length<2||bucket.indexOf(it.id)===0&&!bucket.includes(this.selectedId)));
      used.push([s[0]-12,s[1]-34,s[0]+12,s[1]+2]);
    }
    for(const [id,el] of this.pinEls)if(!seenPins.has(id)){el.remove();this.pinEls.delete(id)}
    // route ends get a flag each
    // names: streets (rotated), then places by kind, then small streets; each only where it fits
    const cand=[];
    if(showNames)for(const l of this.data.labels){if(l.rank>2&&this.cam.dist>900)continue;if(l.rank>1&&this.cam.dist>2200)continue;cand.push({...l,pri:l.rank})}
    if(showPlaces&&this.cam.dist<1300)for(const p of this.data.places){const cat=geoCat(p.what);if(cat==='other'&&this.cam.dist>650)continue;if(cat==='shop'&&this.cam.dist>800)continue;
      if(/^\d+$/.test(p.text)||/ & /.test(p.text)&&p.what==='place')continue;cand.push({...p,pri:cat==='nature'||cat==='community'?1.5:2.5,cat})}
    cand.sort((a,b)=>a.pri-b.pri);
    const seen=new Set();
    for(const c of cand){
      const key=c.type+':'+c.text+':'+Math.round(c.x)+':'+Math.round(c.y);
      const s=this.project(c.x,c.y,0);if(!s||s[2]>far||s[0]<-50||s[1]<-20||s[0]>this.w+50||s[1]>this.h+20)continue;
      let el=this.labelEls.get(key);
      const w=c.text.length*(c.type==='street'?6.2:6.6)+(c.type==='place'?14:0),h=c.type==='street'?14:16;
      let ang=0;
      if(c.type==='street'){const a=this.project(c.x+Math.cos(c.ang)*20,c.y+Math.sin(c.ang)*20,0),b=this.project(c.x-Math.cos(c.ang)*20,c.y-Math.sin(c.ang)*20,0);if(!a||!b)continue;ang=Math.atan2(a[1]-b[1],a[0]-b[0]);if(ang>Math.PI/2)ang-=Math.PI;if(ang<-Math.PI/2)ang+=Math.PI}
      const ext=Math.abs(Math.cos(ang))*w+Math.abs(Math.sin(ang))*h,exty=Math.abs(Math.sin(ang))*w+Math.abs(Math.cos(ang))*h;
      if(!fits(s[0]-ext/2,s[1]-exty/2,ext,exty))continue;
      if(!el){el=this.labelEl(c);this.labelEls.set(key,el);ov.append(el)}
      seen.add(key);el.style.display='';const fade=1-Math.max(0,Math.min(1,(s[2]-far*0.6)/(far*0.4)));el.style.opacity=fade.toFixed(2);
      el.style.transform=`translate(${s[0].toFixed(1)}px,${s[1].toFixed(1)}px) translate(-50%,-50%) rotate(${ang.toFixed(3)}rad)`;
    }
    for(const [k,el] of this.labelEls)if(!seen.has(k))el.style.display='none';
    // the draft spot and route stops being placed
    this.overlayExtras?.();
  }
  labelEl(c){
    const el=document.createElement('div');el.className=c.type==='street'?'gm-street':'gm-place';
    if(c.type==='place'){el.dataset.cat=c.cat;el.innerHTML='<i></i><span></span>';el.lastChild.textContent=c.text;el.title=c.text+(c.address?' · '+c.address:'');
      el._place=c}else el.textContent=c.text;
    return el;
  }
  pinEl(it){
    const el=document.createElement('button');el.type='button';el.className='gm-pin gm-look-'+(it.look||'pin')+(it.approx?' gm-approx':'');
    el.dataset.component='geo-map';el.dataset.part='pin';el.dataset.path=this.api?.node?.path||'';
    const facts={kind:it.kind,layer:(it.layer&&it.layer.name||'').toLowerCase().replace(/[^a-z0-9-]+/g,'-'),look:it.look,approx:it.approx?'yes':'no'};
    for(const [k,v] of Object.entries(facts))if(v)el.setAttribute('data-fact-'+k,String(v));
    el.style.color=it.color;el._item=it;el._rev=it.rev+'|'+it.color+'|'+(it.title||it.name);
    const label=it.title||it.name||it.label||it.kind;
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
    cv.addEventListener('pointerleave',()=>{if(this.hover){this.hover=0;this.ask()}this.api?.node&&this.tip(null)});
    cv.addEventListener('dblclick',e=>{const r=this.root.getBoundingClientRect();const g=this.ground(e.clientX-r.left,e.clientY-r.top);if(g)this.flyTo({x:g[0],y:g[1],dist:this.cam.dist*0.55},500)});
    cv.addEventListener('keydown',e=>this.key(e));
    ov.addEventListener('pointerdown',e=>{const pin=e.target.closest('.gm-pin');if(pin)this.pinDown(e,pin)});
    ov.addEventListener('click',e=>{const place=e.target.closest('.gm-place');if(!place||!place._place)return;const c=place._place;const [lat,lon]=this.toLL(c.x,c.y);
      this.onPress?.({type:'place',what:{type:'place',name:c.text,id:c.id,what:c.what,address:c.address||''},lat,lon})});
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
      if(a&&b){this.cam.x+=a[0]-b[0];this.cam.y+=a[1]-b[1];const now=performance.now(),dt=Math.max(8,now-p.t);this.vel=[(a[0]-b[0])/dt,(a[1]-b[1])/dt];p.t=now;this.clampCam()}}
    p.x=e.clientX;p.y=e.clientY;this.ask();
  }
  up(e,cancel){
    const p=this.pointers.get(e.pointerId);this.pointers.delete(e.pointerId);if(!p)return;
    if(this.pointers.size)return;
    const r=this.root.getBoundingClientRect();
    if(!cancel&&this.moved<6&&this.mode!=='pinch'){this.press(e.clientX-r.left,e.clientY-r.top,e);return}
    if(this.mode==='pan'&&!matchMedia('(prefers-reduced-motion: reduce)').matches){let [vx,vy]=this.vel;let last=performance.now();
      if(Math.hypot(vx,vy)>0.05)this.inertia=now=>{const dt=now-last;last=now;this.cam.x+=vx*dt;this.cam.y+=vy*dt;const k=Math.pow(0.992,dt);vx*=k;vy*=k;this.clampCam();
        if(Math.hypot(vx,vy)<0.01){this.inertia=null;return false}return true};this.ask()}
  }
  hoverAt(x,y){const now=performance.now();if(now-(this.lastHover||0)<90)return;this.lastHover=now;
    const id=this.pickAt(x,y);if(id!==this.hover){this.hover=id;this.ask()}
    const what=this.data?.picks?.[id];this.tip(what?{x,y,text:geoDescribe(what)}:null)}
  tip(t){let el=this.tipEl;if(!t){if(el)el.hidden=true;return}if(!el){el=this.tipEl=document.createElement('div');el.className='gm-tip';el.setAttribute('role','tooltip')}
    if(el.parentNode!==this.overlay)this.overlay.append(el);el.hidden=false;el.textContent=t.text;el.style.transform=`translate(${t.x+14}px,${t.y+12}px)`}
  press(x,y,e){
    const g=this.ground(x,y);const ll=g?this.toLL(g[0],g[1]):null;
    const id=this.pickAt(x,y);const what=id?this.data.picks[id]:null;
    this.onPress?.({type:what?what.type:'ground',what,lat:ll?.[0],lon:ll?.[1],x,y,pickId:id,shift:e?.shiftKey});
  }
  pinDown(e,pin){
    e.stopPropagation();const it=pin._item;const start={x:e.clientX,y:e.clientY};let dragging=false;
    pin.setPointerCapture(e.pointerId);
    const r=this.root.getBoundingClientRect();
    // keep where the pin was taken hold of: the point under the pin's tip, not under the pointer, is where it lands
    const tip=pin.getBoundingClientRect();const grab={x:tip.left-e.clientX,y:tip.top-e.clientY};
    const mv=ev=>{if(!dragging&&Math.hypot(ev.clientX-start.x,ev.clientY-start.y)>6&&it.kind!=='route'){dragging=true;this.dragging=it.id;pin.classList.add('gm-dragging')}
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
      case 't':this.flyTo({pitch:this.cam.pitch>10?0:48},450);break;case 'Escape':this.onEscape?.();break;default:used=false}
    if(used){e.preventDefault();this.clampCam();this.ask()}
  }
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
function geoDescribe(w){if(!w)return '';if(w.type==='building')return (w.name||w.address||'A building')+(w.name&&w.address?' · '+w.address:'');if(w.type==='street')return w.name;return (w.name||w.what||'').replace(/_/g,' ')}
