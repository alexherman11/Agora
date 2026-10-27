// The map's geometry builder. Runs in a Worker (made from this text as a blob), so the window never waits on it.
// In: {ground: <agora-ground/1 text>, palette}. Out: typed arrays for the GL passes, plus what picking and labels need.
// Coordinates out are metres east/north of the ground's origin (the ground stores decimetres).
function geoWorkerMain(){
'use strict';
// ---- earcut (after Mapbox's earcut, ISC licence; reduced: no z-order hashing) ---------------------------------
function Node(i,x,y){this.i=i;this.x=x;this.y=y;this.prev=null;this.next=null;this.steiner=false}
function insertNode(i,x,y,last){const p=new Node(i,x,y);if(!last){p.prev=p;p.next=p}else{p.next=last.next;p.prev=last;last.next.prev=p;last.next=p}return p}
function removeNode(p){p.next.prev=p.prev;p.prev.next=p.next}
function signedArea(d,s,e){let sum=0;for(let i=s,j=e-2;i<e;i+=2){sum+=(d[j]-d[i])*(d[i+1]+d[j+1]);j=i}return sum}
function linkedList(d,s,e,cw){let last;if(cw===(signedArea(d,s,e)>0)){for(let i=s;i<e;i+=2)last=insertNode(i,d[i],d[i+1],last)}else{for(let i=e-2;i>=s;i-=2)last=insertNode(i,d[i],d[i+1],last)}if(last&&equals(last,last.next)){removeNode(last);last=last.next}return last}
function equals(a,b){return a.x===b.x&&a.y===b.y}
function area(p,q,r){return (q.y-p.y)*(r.x-q.x)-(q.x-p.x)*(r.y-q.y)}
function filterPoints(start,end){if(!start)return start;if(!end)end=start;let p=start,again;do{again=false;if(!p.steiner&&(equals(p,p.next)||area(p.prev,p,p.next)===0)){removeNode(p);p=end=p.prev;if(p===p.next)break;again=true}else p=p.next}while(again||p!==end);return end}
function pit(ax,ay,bx,by,cx,cy,px,py){return (cx-px)*(ay-py)>=(ax-px)*(cy-py)&&(ax-px)*(by-py)>=(bx-px)*(ay-py)&&(bx-px)*(cy-py)>=(cx-px)*(by-py)}
function isEar(ear){const a=ear.prev,b=ear,c=ear.next;if(area(a,b,c)>=0)return false;const x0=Math.min(a.x,b.x,c.x),y0=Math.min(a.y,b.y,c.y),x1=Math.max(a.x,b.x,c.x),y1=Math.max(a.y,b.y,c.y);let p=c.next;while(p!==a){if(p.x>=x0&&p.x<=x1&&p.y>=y0&&p.y<=y1&&pit(a.x,a.y,b.x,b.y,c.x,c.y,p.x,p.y)&&area(p.prev,p,p.next)>=0)return false;p=p.next}return true}
function sign(n){return n>0?1:n<0?-1:0}
function onSeg(p,q,r){return q.x<=Math.max(p.x,r.x)&&q.x>=Math.min(p.x,r.x)&&q.y<=Math.max(p.y,r.y)&&q.y>=Math.min(p.y,r.y)}
function intersects(p1,q1,p2,q2){const o1=sign(area(p1,q1,p2)),o2=sign(area(p1,q1,q2)),o3=sign(area(p2,q2,p1)),o4=sign(area(p2,q2,q1));if(o1!==o2&&o3!==o4)return true;if(o1===0&&onSeg(p1,p2,q1))return true;if(o2===0&&onSeg(p1,q2,q1))return true;if(o3===0&&onSeg(p2,p1,q2))return true;if(o4===0&&onSeg(p2,q1,q2))return true;return false}
function locallyInside(a,b){return area(a.prev,a,a.next)<0?area(a,b,a.next)>=0&&area(a,a.prev,b)>=0:area(a,b,a.prev)<0||area(a,a.next,b)<0}
function intersectsPolygon(a,b){let p=a;do{if(p.i!==a.i&&p.next.i!==a.i&&p.i!==b.i&&p.next.i!==b.i&&intersects(p,p.next,a,b))return true;p=p.next}while(p!==a);return false}
function middleInside(a,b){let p=a,inside=false;const px=(a.x+b.x)/2,py=(a.y+b.y)/2;do{if(((p.y>py)!==(p.next.y>py))&&p.next.y!==p.y&&(px<(p.next.x-p.x)*(py-p.y)/(p.next.y-p.y)+p.x))inside=!inside;p=p.next}while(p!==a);return inside}
function isValidDiagonal(a,b){return a.next.i!==b.i&&a.prev.i!==b.i&&!intersectsPolygon(a,b)&&(locallyInside(a,b)&&locallyInside(b,a)&&middleInside(a,b)&&(area(a.prev,a,b.prev)||area(a,b.prev,b))||equals(a,b)&&area(a.prev,a,a.next)>0&&area(b.prev,b,b.next)>0)}
function splitPolygon(a,b){const a2=new Node(a.i,a.x,a.y),b2=new Node(b.i,b.x,b.y),an=a.next,bp=b.prev;a.next=b;b.prev=a;a2.next=an;an.prev=a2;b2.next=a2;a2.prev=b2;bp.next=b2;b2.prev=bp;return b2}
function cure(start,tri){let p=start;do{const a=p.prev,b=p.next.next;if(!equals(a,b)&&intersects(a,p,p.next,b)&&locallyInside(a,b)&&locallyInside(b,a)){tri.push(a.i/2|0,p.i/2|0,b.i/2|0);removeNode(p);removeNode(p.next);p=start=b}p=p.next}while(p!==start);return filterPoints(p)}
function splitEarcut(start,tri,depth){let a=start;do{let b=a.next.next;while(b!==a.prev){if(a.i!==b.i&&isValidDiagonal(a,b)){let c=splitPolygon(a,b);a=filterPoints(a,a.next);c=filterPoints(c,c.next);linked(a,tri,0,depth+1);linked(c,tri,0,depth+1);return}b=b.next}a=a.next}while(a!==start)}
function linked(ear,tri,pass,depth=0){if(!ear||depth>60)return;let stop=ear,prev,next;while(ear.prev!==ear.next){prev=ear.prev;next=ear.next;if(isEar(ear)){tri.push(prev.i/2|0,ear.i/2|0,next.i/2|0);removeNode(ear);ear=next.next;stop=next.next;continue}ear=next;if(ear===stop){if(!pass)linked(filterPoints(ear),tri,1,depth);else if(pass===1){ear=cure(filterPoints(ear),tri);linked(ear,tri,2,depth)}else if(pass===2)splitEarcut(ear,tri,depth);break}}}
function leftmost(s){let p=s,l=s;do{if(p.x<l.x||(p.x===l.x&&p.y<l.y))l=p;p=p.next}while(p!==s);return l}
function sectorContains(m,p){return area(m.prev,m,p.prev)<0&&area(p.next,m,m.next)<0}
function bridge(hole,outer){let p=outer;const hx=hole.x,hy=hole.y;let qx=-Infinity,m;do{if(hy<=p.y&&hy>=p.next.y&&p.next.y!==p.y){const x=p.x+(hy-p.y)*(p.next.x-p.x)/(p.next.y-p.y);if(x<=hx&&x>qx){qx=x;m=p.x<p.next.x?p:p.next;if(x===hx)return m}}p=p.next}while(p!==outer);if(!m)return null;const stop=m,mx=m.x,my=m.y;let tmin=Infinity;p=m;do{if(hx>=p.x&&p.x>=mx&&hx!==p.x&&pit(hy<my?hx:qx,hy,mx,my,hy<my?qx:hx,hy,p.x,p.y)){const t=Math.abs(hy-p.y)/(hx-p.x);if(locallyInside(p,hole)&&(t<tmin||(t===tmin&&(p.x>m.x||(p.x===m.x&&sectorContains(m,p)))))){m=p;tmin=t}}p=p.next}while(p!==stop);return m}
function earcut(d,holes){const outerLen=holes&&holes.length?holes[0]*2:d.length;let outer=linkedList(d,0,outerLen,true);const tri=[];if(!outer||outer.next===outer.prev)return tri;if(holes&&holes.length){const q=[];for(let i=0;i<holes.length;i++){const s=holes[i]*2,e=i<holes.length-1?holes[i+1]*2:d.length;const l=linkedList(d,s,e,false);if(!l)continue;if(l===l.next)l.steiner=true;q.push(leftmost(l))}q.sort((a,b)=>a.x-b.x);for(const h of q){const b=bridge(h,outer);if(!b)continue;const br=splitPolygon(b,h);filterPoints(br,br.next);outer=filterPoints(b,b.next)}}linked(outer,tri,0);return tri}

// ---- buffers ----------------------------------------------------------------------------------------------------
class Buf{constructor(stride,cap=4096){this.s=stride;this.a=new Float32Array(cap*stride);this.n=0}
  push(...v){if((this.n+1)*this.s>this.a.length){const b=new Float32Array(this.a.length*2);b.set(this.a);this.a=b}this.a.set(v,this.n*this.s);this.n++}
  out(){return this.a.slice(0,this.n*this.s)}}
const hex=(h,a=1)=>{h=h.replace('#','');if(h.length===3)h=h.split('').map(c=>c+c).join('');const n=parseInt(h,16);return [(n>>16&255)/255,(n>>8&255)/255,(n&255)/255,a]};
function hash(s){let h=2166136261;for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619)}return (h>>>0)/4294967295}
const M=v=>v/10;           // decimetres -> metres

// Split long triangle edges so a curved ground bends smoothly (the tiny-earth view moves vertices, not pixels).
function addTri(buf,a,b,c,z,col,pick,maxEdge){
  const d2=(p,q)=>(p[0]-q[0])**2+(p[1]-q[1])**2,L=maxEdge*maxEdge;
  if(d2(a,b)>L||d2(b,c)>L||d2(c,a)>L){
    const ab=[(a[0]+b[0])/2,(a[1]+b[1])/2],bc=[(b[0]+c[0])/2,(b[1]+c[1])/2],ca=[(c[0]+a[0])/2,(c[1]+a[1])/2];
    addTri(buf,a,ab,ca,z,col,pick,maxEdge);addTri(buf,ab,b,bc,z,col,pick,maxEdge);addTri(buf,ca,bc,c,z,col,pick,maxEdge);addTri(buf,ab,bc,ca,z,col,pick,maxEdge);return}
  for(const p of [a,b,c])buf.push(p[0],p[1],z,col[0],col[1],col[2],col[3],pick);
}
function polygon(buf,rings,z,col,pick,maxEdge=70){
  const flat=[],holes=[];
  rings.forEach((r,i)=>{if(r.length<6)return;if(i>0)holes.push(flat.length/2);for(let k=0;k<r.length;k++)flat.push(M(r[k]))});
  if(flat.length<6)return 0;
  const t=earcut(flat,holes);
  for(let i=0;i<t.length;i+=3){const P=j=>[flat[t[i+j]*2],flat[t[i+j]*2+1]];addTri(buf,P(0),P(1),P(2),z,col,pick,maxEdge)}
  return t.length/3;
}
// A line as a ribbon with mitred joins (clamped), resampled every `step` metres so it bends with the ground.
function ribbon(buf,pts,width,z,col,pick,step=35){
  const P=[];for(let i=0;i<pts.length;i+=2){const x=M(pts[i]),y=M(pts[i+1]);if(P.length){const [px,py]=P[P.length-1];const d=Math.hypot(x-px,y-py);if(d<0.05)continue;const n=Math.floor(d/step);for(let k=1;k<=n;k++)P.push([px+(x-px)*k/(n+1),py+(y-py)*k/(n+1)])}P.push([x,y])}
  if(P.length<2)return;
  const h=width/2,L=[],R=[];
  for(let i=0;i<P.length;i++){
    const a=P[Math.max(0,i-1)],b=P[i],c=P[Math.min(P.length-1,i+1)];
    let d1=[b[0]-a[0],b[1]-a[1]],d2=[c[0]-b[0],c[1]-b[1]];
    const n1=Math.hypot(...d1)||1,n2=Math.hypot(...d2)||1;d1=[d1[0]/n1,d1[1]/n1];d2=[d2[0]/n2,d2[1]/n2];
    if(i===0)d1=d2;if(i===P.length-1)d2=d1;
    let tx=d1[0]+d2[0],ty=d1[1]+d2[1];const tl=Math.hypot(tx,ty)||1;tx/=tl;ty/=tl;
    const nx=-ty,ny=tx;const dot=nx*(-d1[1])+ny*d1[0];const m=Math.min(h/Math.max(dot,.35),h*2.6);
    L.push([b[0]+nx*m,b[1]+ny*m]);R.push([b[0]-nx*m,b[1]-ny*m]);
  }
  for(let i=0;i<P.length-1;i++){
    const v=[L[i],R[i],L[i+1],R[i],R[i+1],L[i+1]];
    for(const p of v)buf.push(p[0],p[1],z,col[0],col[1],col[2],col[3],pick);
  }
  // round the two ends a little, so lone paths do not stop square
  for(const [end,dir] of [[0,1],[P.length-1,-1]]){
    const b=P[end],o=P[end+dir];const ang=Math.atan2(b[1]-o[1],b[0]-o[0]);
    for(let s=0;s<4;s++){const a0=ang-Math.PI/2+s*Math.PI/4,a1=a0+Math.PI/4;
      buf.push(b[0],b[1],z,...col,pick);buf.push(b[0]+Math.cos(a0)*h,b[1]+Math.sin(a0)*h,z,...col,pick);buf.push(b[0]+Math.cos(a1)*h,b[1]+Math.sin(a1)*h,z,...col,pick)}
  }
}

const ROAD_W={major:13,street:8.5,service:4.6,walk:5,path:2.2,cycle:2.8,steps:2.4};
const ROAD_ORDER=['path','steps','cycle','service','walk','street','major'];

function build(ground,pal){
  const g=JSON.parse(ground);
  if(g.format!=='agora-ground/1')throw Error('not an agora-ground/1 file');
  const areas=new Buf(8,1<<15),roads=new Buf(8,1<<15),shadows=new Buf(8,1<<13),bld=new Buf(11,1<<16),edges=new Buf(4,1<<15);
  const picks=[null];     // index -> what was pressed
  // 1. areas, in the ground's own order (sea first), each class a little above the last
  // 0. the land itself: a slab a little past the ground's box, with earth sides, like a diorama piece
  {const [bx0,by0,bx1,by1]=g.bounds.map(M);const pad=120,X0=bx0-pad,Y0=by0-pad,X1=bx1+pad,Y1=by1+pad;
    const soil=hex(pal.soil||'#c8ae86'),deep=hex(pal.soilDeep||'#9c8262');
    const edge=(ax,ay,bx,by)=>{const n=Math.max(1,Math.ceil(Math.hypot(bx-ax,by-ay)/40));for(let i=0;i<n;i++){
      const x0=ax+(bx-ax)*i/n,y0=ay+(by-ay)*i/n,x1=ax+(bx-ax)*(i+1)/n,y1=ay+(by-ay)*(i+1)/n;
      for(const [x,y,z,c] of [[x0,y0,0,soil],[x1,y1,0,soil],[x1,y1,-36,deep],[x0,y0,0,soil],[x1,y1,-36,deep],[x0,y0,-36,deep]])areas.push(x,y,z,c[0],c[1],c[2],1,0)}};
    edge(X0,Y0,X1,Y0);edge(X1,Y0,X1,Y1);edge(X1,Y1,X0,Y1);edge(X0,Y1,X0,Y0);
    polygon(areas,[[X0*10,Y0*10,X1*10,Y0*10,X1*10,Y1*10,X0*10,Y1*10]],-0.01,hex(pal.land),0,150);}
  const AREA_Z={sea:0,residential:.02,commercial:.02,industrial:.02,school:.03,green:.05,park:.06,wood:.07,wetland:.07,beach:.08,pitch:.09,play:.09,parking:.1,marina:.11,water:.12,pool:.13};
  for(const a of g.areas){
    const col=hex(pal.area[a.k]||'#e9e3d6');
    const pick=a.k==='sea'||a.k==='residential'||a.k==='commercial'||a.k==='industrial'?0:picks.push({type:'area',id:a.id,name:a.n||'',what:a.k})-1;
    polygon(areas,a.r,AREA_Z[a.k]||.04,col,pick,a.k==='sea'?150:110);
  }
  // pitches get a chalk line, parks a darker rim: drawn as thin ribbons along the outer ring
  for(const a of g.areas)if(a.k==='pitch'||a.k==='park'||a.k==='play'){const r=a.r[0];ribbon(areas,r,a.k==='pitch'?.6:1.1,.15,hex(a.k==='pitch'?pal.chalk:pal.rim,a.k==='pitch'?.85:.55),0,60)}
  // 2. streams and the river's line
  for(const s of g.streams)ribbon(areas,s.p,s.c==='river'?6:2.2,.14,hex(pal.area.water),0);
  // 3. building shadows: the footprint pushed away from the sun, soft and low
  const sun=[-0.52,-0.42];   // the light comes from the south-west; shadows fall north-east
  for(const b of g.buildings){
    const k=Math.min(b.h,14)*0.55;const ring=b.r[0];const sh=[];
    for(let i=0;i<ring.length;i+=2)sh.push(ring[i]-sun[0]*k*10,ring[i+1]-sun[1]*k*10);
    polygon(shadows,[ring],.16,[0,0,0,1],0,1e9);polygon(shadows,[sh],.16,[0,0,0,1],0,1e9);
    for(let i=0;i<ring.length-2;i+=2){       // the sides the shadow sweeps between footprint and its cast copy
      const a=[M(ring[i]),M(ring[i+1])],b=[M(ring[i+2]),M(ring[i+3])],c=[M(sh[i+2]),M(sh[i+3])],d=[M(sh[i]),M(sh[i+1])];
      for(const p of [a,b,c,a,c,d])shadows.push(p[0],p[1],.16,0,0,0,1,0);
    }
  }
  // 4. roads: casings, then fills, by class (small under big)
  const labels=[],roadPick=new Map();
  for(const r of g.roads)if(r.n)roadPick.set(r.id,picks.push({type:'street',id:r.id,name:r.n,what:r.c})-1);
  for(const cls of ROAD_ORDER)for(const r of g.roads)if(r.c===cls&&cls!=='path'&&cls!=='steps'&&cls!=='cycle'){
    const w=ROAD_W[cls]*(r.x?0.8:1);
    ribbon(roads,r.p,w+2.2,.2+ROAD_ORDER.indexOf(cls)*.01,hex(pal.casing[cls]||pal.casing.street),roadPick.get(r.id)||0);
  }
  for(const cls of ROAD_ORDER)for(const r of g.roads)if(r.c===cls){
    const w=ROAD_W[cls]*(r.x?0.8:1);
    ribbon(roads,r.p,w,.3+ROAD_ORDER.indexOf(cls)*.01,hex(pal.road[cls]),roadPick.get(r.id)||0);
  }
  for(const r of g.rail){ribbon(roads,r.p,3.2,.42,hex(pal.rail),0);ribbon(roads,r.p,1.1,.43,hex(pal.railTie),0,12)}
  // street names: one candidate every ~260 m of each named street, on its longest straight runs
  const byName={};for(const r of g.roads)if(r.n&&r.c!=='path'&&r.c!=='cycle'&&r.c!=='steps')(byName[r.n]=byName[r.n]||[]).push(r);
  for(const [name,rs] of Object.entries(byName)){
    const segs=[];for(const r of rs){const p=r.p;for(let i=0;i<p.length-2;i+=2){const ax=M(p[i]),ay=M(p[i+1]),bx=M(p[i+2]),by=M(p[i+3]);segs.push({x:(ax+bx)/2,y:(ay+by)/2,len:Math.hypot(bx-ax,by-ay),ang:Math.atan2(by-ay,bx-ax),cls:r.c})}}
    segs.sort((a,b)=>b.len-a.len);const kept=[];
    for(const s of segs){if(s.len<22)break;if(kept.every(k=>Math.hypot(k.x-s.x,k.y-s.y)>260))kept.push(s);if(kept.length>6)break}
    for(const s of kept)labels.push({type:'street',text:name,x:s.x,y:s.y,ang:s.ang,rank:s.cls==='major'?1:s.cls==='street'?2:3});
  }
  // 5. buildings: walls and roofs, lit in the shader; outlines as lines
  const meta=[];
  for(const b of g.buildings){
    const pick=picks.push({type:'building',id:b.id,name:b.n||'',address:b.a||'',h:b.h,hs:b.hs,what:b.k})-1;
    meta.push(pick);
    const t=hash(b.id),base=hex(pal.buildings[Math.floor(t*pal.buildings.length)]);
    const jitter=0.94+0.1*hash(b.id+'j');const col=[base[0]*jitter,base[1]*jitter,base[2]*jitter];
    const roof=hex(pal.roof[Math.floor(hash(b.id+'r')*pal.roof.length)]);
    const h=b.h;
    // walls
    for(const ring of b.r){
      const n=ring.length/2;if(n<3)continue;
      let sa=0;for(let i=0;i<n;i++){const j=(i+1)%n;sa+=ring[i*2]*ring[j*2+1]-ring[j*2]*ring[i*2+1]}
      const ccw=sa>0;
      for(let i=0;i<n;i++){
        const j=(i+1)%n;let ax=M(ring[i*2]),ay=M(ring[i*2+1]),bx=M(ring[j*2]),by=M(ring[j*2+1]);
        if(ax===bx&&ay===by)continue;
        let nx=by-ay,ny=-(bx-ax);const nl=Math.hypot(nx,ny);nx/=nl;ny/=nl;if(!ccw){nx=-nx;ny=-ny}
        const v=[[ax,ay,0],[bx,by,0],[bx,by,h],[ax,ay,0],[bx,by,h],[ax,ay,h]];
        for(const p of v)bld.push(p[0],p[1],p[2],nx,ny,0,col[0],col[1],col[2],pick,p[2]>0?1:0);
        edges.push(ax,ay,h,0);edges.push(bx,by,h,0);
        edges.push(ax,ay,0,1);edges.push(ax,ay,h,1);
      }
    }
    // roof
    const flat=[],holes=[];b.r.forEach((r,i)=>{if(i>0)holes.push(flat.length/2);for(const v of r)flat.push(M(v))});
    const tri=earcut(flat,holes);
    for(let i=0;i<tri.length;i++){const k=tri[i];bld.push(flat[k*2],flat[k*2+1],h,0,0,1,roof[0],roof[1],roof[2],pick,2)}
  }
  // 6. named places and small things for the overlay
  const places=g.pois.map(p=>({type:'place',text:p.n,x:M(p.x),y:M(p.y),what:p.c,id:p.id,address:p.a||''}));
  const props=(g.props||[]).map(p=>({type:'prop',what:p.k,x:M(p.x),y:M(p.y),id:p.id,text:p.n||''}));
  const [x0,y0,x1,y1]=g.bounds.map(M);
  return {areas:areas.out(),roads:roads.out(),shadows:shadows.out(),buildings:bld.out(),edges:edges.out(),
    picks,labels,places,props,bounds:[x0,y0,x1,y1],frame:g.frame,name:g.name,attribution:g.attribution,
    counts:{buildings:g.buildings.length,roads:g.roads.length,areas:g.areas.length,places:g.pois.length}};
}
self.onmessage=e=>{
  try{const t0=Date.now();const out=build(e.data.ground,e.data.palette);out.ms=Date.now()-t0;
    self.postMessage(out,[out.areas.buffer,out.roads.buffer,out.shadows.buffer,out.buildings.buffer,out.edges.buffer])}
  catch(err){self.postMessage({error:String(err&&err.message||err)})}
};
}
