// The map's geometry builder. Runs in a Worker (made from this text as a blob), so the window never waits on it.
// In: {id, chunk: <agora-tile/1 text>, palette, flags}. Out: typed arrays for one tile's GL passes, plus what picking
// and names need. Positions out are metres east/north of the tile's north-west corner, in Web Mercator metres; heights
// are true metres times the Mercator scale there, so buildings keep their shape at every latitude.
function geoWorkerMain(){
'use strict';
// ---- earcut (after Mapbox's earcut, ISC licence; reduced: no z-order hashing) ---------------------------------
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
const hex=(h,a=1)=>{h=String(h||'#888').replace('#','');if(h.length===3)h=h.split('').map(c=>c+c).join('');const n=parseInt(h,16)||0;return [(n>>16&255)/255,(n>>8&255)/255,(n&255)/255,a]};
function hash(s){let h=2166136261;for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619)}return (h>>>0)/4294967295}
const WORLD=2*Math.PI*6378137;

function polygon(buf,rings,u,z,col,pick){
  const flat=[],holes=[];
  rings.forEach((r,i)=>{if(r.length<6)return;if(i>0)holes.push(flat.length/2);for(let k=0;k<r.length;k+=2){flat.push(r[k]*u,-r[k+1]*u)}});
  if(flat.length<6)return 0;
  const t=earcut(flat,holes);
  for(let i=0;i<t.length;i++){const k=t[i];buf.push(flat[k*2],flat[k*2+1],z,col[0],col[1],col[2],col[3],pick)}
  return t.length/3;
}
// A line for the line program: each vertex is the centre point plus an offset direction (already mitred); the vertex
// shader widens it to max(half width in metres, a minimum in pixels), so a road stays a road at every zoom.
// Stride 11: x y nx ny halfW minPx z r g b pick.
function line(buf,pts,u,hw,minPx,z,col,pick,E){
  const P=[];for(let i=0;i<pts.length;i+=2){const x=pts[i]*u,y=-pts[i+1]*u;if(P.length){const [px,py]=P[P.length-1];if(Math.hypot(x-px,y-py)<u*0.5)continue}P.push([x,y,pts[i],pts[i+1]])}
  if(P.length<2)return;
  const N=[],M=[];
  for(let i=0;i<P.length;i++){
    const a=P[Math.max(0,i-1)],b=P[i],c=P[Math.min(P.length-1,i+1)];
    let d1=[b[0]-a[0],b[1]-a[1]],d2=[c[0]-b[0],c[1]-b[1]];
    const n1=Math.hypot(...d1)||1,n2=Math.hypot(...d2)||1;d1=[d1[0]/n1,d1[1]/n1];d2=[d2[0]/n2,d2[1]/n2];
    if(i===0)d1=d2;if(i===P.length-1)d2=d1;
    let tx=d1[0]+d2[0],ty=d1[1]+d2[1];const tl=Math.hypot(tx,ty);
    if(tl<1e-3){tx=d1[0];ty=d1[1]}else{tx/=tl;ty/=tl}
    const nx=-ty,ny=tx;const dot=nx*(-d1[1])+ny*d1[0];const m=Math.min(1/Math.max(dot,.4),2.5);
    N.push([nx*m,ny*m]);
  }
  const V=(p,n)=>buf.push(p[0],p[1],n[0],n[1],hw,minPx,z,col[0],col[1],col[2],pick);
  for(let i=0;i<P.length-1;i++){
    const a=P[i],b=P[i+1],na=N[i],nb=N[i+1],ma=[-na[0],-na[1]],mb=[-nb[0],-nb[1]];
    V(a,na);V(a,ma);V(b,nb);V(a,ma);V(b,mb);V(b,nb);
  }
  // round ends, except where the line was cut at the tile's edge (the next tile carries on)
  const edge=p=>p[2]<=0||p[3]<=0||p[2]>=E||p[3]>=E;
  for(const [end,dir] of [[0,1],[P.length-1,-1]]){
    const b=P[end];if(edge(b))continue;const o=P[end+dir];const ang=Math.atan2(b[1]-o[1],b[0]-o[0]);
    for(let s=0;s<4;s++){const a0=ang-Math.PI/2+s*Math.PI/4,a1=a0+Math.PI/4;
      V(b,[0,0]);V(b,[Math.cos(a0),Math.sin(a0)]);V(b,[Math.cos(a1),Math.sin(a1)])}
  }
}

// How each line class is drawn: half width in metres, minimum half width in pixels, casing, order
const LINES={
  motorway:{w:9,px:1.7,case:true,z:9},major:{w:6.5,px:1.25,case:true,z:8},street:{w:4.2,px:0.8,case:true,z:7},
  service:{w:2.4,px:0.55,case:true,z:6},walk:{w:1.3,px:0.5,z:5},path:{w:0.9,px:0.55,z:4},cycle:{w:1.2,px:0.6,z:4},
  steps:{w:1.1,px:0.6,z:4},rail:{w:1.5,px:0.8,z:3},runway:{w:22,px:1.4,z:2},taxiway:{w:7,px:0.7,z:2},
  river:{w:9,px:1.1,z:1},stream:{w:2.2,px:0.6,z:1},ferry:{w:1,px:0.6,z:1}};
const CLASS_BUILDING={residential:'home',house:'home',detached:'home',semidetached_house:'home',apartments:'home',terrace:'home',bungalow:'home',
  commercial:'shop',retail:'shop',office:'shop',supermarket:'shop',hotel:'shop',kiosk:'shop',
  industrial:'work',warehouse:'work',factory:'work',manufacture:'work',service:'work',garage:'shed',garages:'shed',shed:'shed',carport:'shed',
  civic:'civic',government:'civic',townhall:'civic',public:'civic',school:'civic',university:'civic',college:'civic',kindergarten:'civic',library:'civic',
  hospital:'civic',fire_station:'civic',police:'civic',church:'faith',chapel:'faith',cathedral:'faith',religious:'faith',mosque:'faith',temple:'faith',synagogue:'faith'};

function build(chunkText,pal,flags){
  const c=JSON.parse(chunkText);
  if(c.f!=='agora-tile/1')throw Error('not an agora-tile/1 chunk');
  const z=c.z,n=2**z,E=c.e||4096,size=WORLD/n,u=size/E;
  const ox=c.x/n*WORLD-WORLD/2,oy=WORLD/2-c.y/n*WORLD;
  const latC=Math.atan(Math.sinh(Math.PI*(1-2*(c.y+0.5)/n)));const k=1/Math.cos(latC);
  const areas=new Buf(8,1<<12),lines=new Buf(11,1<<13),casings=new Buf(11,1<<12),shadows=new Buf(8,1<<11),bld=new Buf(11,1<<12),edges=new Buf(4,1<<12);
  const picks=[null];
  // 1. areas, in the chunk's order (lowest first), each class drawn over the last
  const AREA_PICK={park:1,wood:1,beach:1,water:1,sea:0,pitch:1,play:1,school:1,hospital:1,cemetery:1,airport:1,wetland:1,green:1};
  for(const a of c.a){
    const col=hex(pal.area[a[0]]||pal.land);
    const pick=AREA_PICK[a[0]]&&(z>=11||a[2])?picks.push({type:'area',what:a[0],name:a[2]||''})-1:0;
    polygon(areas,a[1],u,0,col,pick);
  }
  // 2. lines: casings under fills, by class
  const named={};for(const s of c.s)if(!named[s[0]])named[s[0]]=s[1];
  const order=c.l.map((_,i)=>i).sort((a,b)=>(LINES[c.l[a][0]]?.z||0)-(LINES[c.l[b][0]]?.z||0));
  for(const i of order){
    const [cls,pts,fl]=c.l[i];const L=LINES[cls];if(!L)continue;
    if(fl.includes('t')&&cls!=='rail')continue;           // tunnels are not drawn on top of the ground
    const fill=hex(cls==='river'||cls==='stream'?pal.area.water:cls==='ferry'?pal.ferry:(pal.road[cls]||pal.road.street));
    const pick=['motorway','major','street','service','walk','path','cycle','steps'].includes(cls)?picks.push({type:'street',what:cls,name:''})-1:0;
    if(L.case){const cc=hex(fl.includes('b')?pal.bridge:(pal.casing[cls]||pal.casing.street));line(casings,pts,u,L.w+1.1,L.px+0.75,L.z,cc,pick,E)}
    line(lines,pts,u,L.w,L.px,L.z+0.5,fill,pick,E);
    if(cls==='rail'){line(lines,pts,u,0.45,0.35,L.z+0.6,hex(pal.railTie),0,E)}
  }
  // 3. buildings: walls and roofs, lit in the shader; shadows below; outlines as lines
  const sun=[-0.52,-0.42];const idOf=new Map();const shadowsOn=z>=14&&!flags?.noShadows;
  for(const b of c.b){
    const [id,h0,mh0,cls,rings,name,extra]=b;
    let pick=idOf.get(id);
    if(!pick){pick=picks.push({type:'building',id,ref:id.startsWith('osm-')?'':'overture:'+id,name:name||'',h:h0,what:cls,
      number:extra.number||'',osm:extra.osm||'',src:extra.src||'',floors:extra.num_floors||'',roof:extra.roof_shape||''})-1;idOf.set(id,pick)}
    const h=Math.max(1.5,h0)*k,mh=(mh0||0)*k;
    const group=CLASS_BUILDING[cls]||CLASS_BUILDING[extra.subtype]||'plain';
    const set=pal.buildings[group]||pal.buildings.plain;
    let base=extra.facade_color&&/^#?[0-9a-f]{6}$/i.test(extra.facade_color)?hex(extra.facade_color):hex(set[Math.floor(hash(id)*set.length)]);
    const jitter=0.95+0.08*hash(id+'j');const col=[base[0]*jitter,base[1]*jitter,base[2]*jitter];
    const rs=pal.roofs[group]||pal.roofs.plain;
    const roof=extra.roof_color&&/^#?[0-9a-f]{6}$/i.test(extra.roof_color)?hex(extra.roof_color):hex(rs[Math.floor(hash(id+'r')*rs.length)]);
    const onEdge=(ax,ay,bx,by)=>(ax<=0&&bx<=0)||(ay<=0&&by<=0)||(ax>=E&&bx>=E)||(ay>=E&&by>=E);
    for(const ring of rings){
      const m=ring.length/2;if(m<3)continue;
      let sa=0;for(let i=0;i<m;i++){const j=(i+1)%m;sa+=ring[i*2]*ring[j*2+1]-ring[j*2]*ring[i*2+1]}
      const cw=sa>0;    // y down in tile units: positive area is clockwise on the ground
      for(let i=0;i<m;i++){
        const j=(i+1)%m;const rax=ring[i*2],ray=ring[i*2+1],rbx=ring[j*2],rby=ring[j*2+1];
        if(rax===rbx&&ray===rby)continue;
        if(onEdge(rax,ray,rbx,rby))continue;               // a cut along the tile edge is not a wall
        const ax=rax*u,ay=-ray*u,bx=rbx*u,by=-rby*u;
        let nx=by-ay,ny=-(bx-ax);const nl=Math.hypot(nx,ny)||1;nx/=nl;ny/=nl;if(cw){nx=-nx;ny=-ny}
        const v=[[ax,ay,mh],[bx,by,mh],[bx,by,h],[ax,ay,mh],[bx,by,h],[ax,ay,h]];
        for(const p of v)bld.push(p[0],p[1],p[2],nx,ny,0,col[0],col[1],col[2],pick,p[2]>mh?1:0);
        edges.push(ax,ay,h,0);edges.push(bx,by,h,0);
        edges.push(ax,ay,mh,1);edges.push(ax,ay,h,1);
      }
    }
    const flat=[],holes=[];rings.forEach((r,i)=>{if(i>0)holes.push(flat.length/2);for(let q=0;q<r.length;q+=2)flat.push(r[q]*u,-r[q+1]*u)});
    const tri=earcut(flat,holes);
    for(let i=0;i<tri.length;i++){const q=tri[i];bld.push(flat[q*2],flat[q*2+1],h,0,0,1,roof[0],roof[1],roof[2],pick,2)}
    if(shadowsOn&&mh0<=0.5){
      const ring=rings[0];const kk=Math.min(h0,16)*0.55*k;const fp=[],sh=[];
      for(let i=0;i<ring.length;i+=2){fp.push(ring[i]*u,-ring[i+1]*u);sh.push(ring[i]*u-sun[0]*kk,-ring[i+1]*u-sun[1]*kk)}
      const put=(pts)=>{const t=earcut(pts);for(let i=0;i<t.length;i++)shadows.push(pts[t[i]*2],pts[t[i]*2+1],0,0,0,0,1,0)};
      put(fp);put(sh);
      for(let i=0;i<fp.length;i+=2){const j=(i+2)%fp.length;const a=[fp[i],fp[i+1]],b=[fp[j],fp[j+1]],cc=[sh[j],sh[j+1]],d=[sh[i],sh[i+1]];
        for(const p of [a,b,cc,a,cc,d])shadows.push(p[0],p[1],0,0,0,0,1,0)}
    }
  }
  // 4. names: streets along their longest pieces, then points
  const labels=[];
  if(z>=13){
    const byName={};for(const [name,cls,pts] of c.s)(byName[name]=byName[name]||{cls,runs:[]}).runs.push(pts);
    for(const [name,{cls,runs}] of Object.entries(byName)){
      const segs=[];for(const p of runs)for(let i=0;i<p.length-2;i+=2){const ax=p[i]*u,ay=-p[i+1]*u,bx=p[i+2]*u,by=-p[i+3]*u;segs.push({x:(ax+bx)/2,y:(ay+by)/2,len:Math.hypot(bx-ax,by-ay),ang:Math.atan2(by-ay,bx-ax)})}
      segs.sort((a,b)=>b.len-a.len);const kept=[];
      for(const s of segs){if(s.len<25)break;if(kept.every(q=>Math.hypot(q.x-s.x,q.y-s.y)>330))kept.push(s);if(kept.length>3)break}
      const rank=cls==='motorway'||cls==='major'?1:cls==='street'?2:3;
      for(const s of kept)labels.push({type:'street',text:name,x:s.x,y:s.y,ang:s.ang,rank,cls});
    }
  }
  const PLACE_RANK={country:0,state:1,city:2,town:3,village:4,suburb:5,quarter:6,neighbourhood:6,hamlet:7,island:5,isolated_dwelling:9,locality:8};
  const places=[];
  for(const [name,cls,sub,rank,px,py] of c.p){
    const x=px*u,y=-py*u;
    if(cls==='place')places.push({type:'place',kind:'town',text:name,what:sub,x,y,pri:(PLACE_RANK[sub]??8)+(rank||0)*0.05,town:true});
    else if(cls==='peak'||cls==='water'||cls==='airport')places.push({type:'place',kind:cls,text:name,what:cls==='water'?'water':sub||cls,x,y,pri:9+(rank||0)*0.05});
    else places.push({type:'place',kind:'poi',text:name,what:sub||cls,cls,x,y,pri:12+(rank||5)*0.1});
  }
  return {key:c.z+'/'+c.x+'/'+c.y,z,origin:[ox,oy],size,
    areas:areas.out(),casings:casings.out(),lines:lines.out(),shadows:shadows.out(),buildings:bld.out(),edges:edges.out(),
    picks,labels,places,counts:{buildings:c.b.length,lines:c.l.length,areas:c.a.length,places:c.p.length}};
}
self.onmessage=e=>{
  const {id,chunk,palette,flags}=e.data;
  try{const t0=Date.now();const out=build(chunk,palette,flags);out.ms=Date.now()-t0;out.id=id;
    self.postMessage(out,[out.areas.buffer,out.casings.buffer,out.lines.buffer,out.shadows.buffer,out.buildings.buffer,out.edges.buffer])}
  catch(err){self.postMessage({id,error:String(err&&err.message||err)})}
};
}
