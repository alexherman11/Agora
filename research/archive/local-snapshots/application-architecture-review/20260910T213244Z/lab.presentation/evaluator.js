(function(root) {
  'use strict';
  const palette = {paper:'#fffaf0',sage:'#e6f1df',blue:'#e2eff9',rose:'#fae6ed',white:'#ffffff'};
  function selected(rule, row) {
    const s=rule.select || {};
    return (!s.ids || s.ids.includes(row.id)) && (!s.type || s.type==='all' || s.type===row.type) && (!s.tag || (row.tags||[]).includes(s.tag));
  }
  function evaluate(input) {
    const rows=JSON.parse(JSON.stringify(input.rows||[]));
    const rules=(input.rules||[]).filter(r=>r.enabled!==false).sort((a,b)=>(a.priority||0)-(b.priority||0)||a.id.localeCompare(b.id));
    const results=rows.map(r=>({...r,style:{},sources:{},geometry:{...r.geometry},layout:null}));
    let shell={chat:'right',height:300,composer:82}; const shellSources={}; const diagnostics=[];
    for(const rule of rules) {
      if(rule.shell) for(const [key,value] of Object.entries(rule.shell)) {shell[key]=value;shellSources[key]=rule.id;}
      const targets=results.filter(row=>selected(rule,row));
      if(!targets.length && !rule.shell) diagnostics.push({rule:rule.id,state:'empty',reason:'No current matching surfaces; live rule retained.'});
      for(const row of targets) {
        for(const [key,value] of Object.entries(rule.style||{})) {row.style[key]=value;row.sources['style.'+key]=rule.id;}
        if(rule.layout) {row.layout={...rule.layout};row.sources.layout=rule.id;}
      }
    }
    for(const rule of rules.filter(r=>r.layout)) {
      let targets=results.filter(r=>r.sources.layout===rule.id);
      const p=rule.layout;
      if(p.order==='title') targets.sort((a,b)=>a.title.localeCompare(b.title)||a.id.localeCompare(b.id));
      else if(p.order==='date') targets.sort((a,b)=>(a.date||'').localeCompare(b.date||'')||a.id.localeCompare(b.id));
      else targets.sort((a,b)=>a.id.localeCompare(b.id));
      if(p.kind==='grid') {
        const gap=p.gap??24, width=p.width??245,height=p.height??205;
        const available=Math.max(0,(input.viewport?.width??900)-(p.x??16)-16);
        const requested=p.columns??2;
        const columns=p.responsive===false?requested:Math.max(1,Math.min(requested,Math.floor((available+gap)/(width+gap))));
        if(available<width || (p.responsive===false && columns*width+(columns-1)*gap>available)) {
          diagnostics.push({rule:rule.id,state:'overflow',reason:'Requested fixed card widths exceed the available view; horizontal scrolling is required.'});
        }
        targets.forEach((row,i)=>row.geometry={x:(p.x??16)+(i%columns)*(width+gap),y:(p.y??16)+Math.floor(i/columns)*(height+gap),width,height});
      } else if(p.kind==='circle') {
        const cx=p.center_x??500,cy=p.center_y??350,radius=p.radius??260;
        const width=p.width??190,height=p.height??170;
        targets.forEach((row,i)=>{
          const angle=-Math.PI/2+2*Math.PI*i/targets.length;
          row.geometry={x:cx+radius*Math.cos(angle)-width/2,y:cy+radius*Math.sin(angle)-height/2,width,height};
        });
        const overlaps=(a,b)=>a.x<b.x+b.width&&a.x+a.width>b.x&&a.y<b.y+b.height&&a.y+a.height>b.y;
        const collisions=[];
        for(let i=0;i<targets.length;i++)for(let j=i+1;j<targets.length;j++)
          if(overlaps(targets[i].geometry,targets[j].geometry))collisions.push([targets[i].id,targets[j].id]);
        if(collisions.length)diagnostics.push({rule:rule.id,state:'overlap',pairs:collisions,reason:'Fixed circle and card sizes crowd these reading surfaces; no automatic shrinking or collision avoidance.'});
        if(targets.some(r=>r.geometry.x<0||r.geometry.y<0||r.geometry.x+r.geometry.width>(input.viewport?.width??900)))
          diagnostics.push({rule:rule.id,state:'overflow',reason:'Fixed circle extends beyond the available desk viewport; it is not shrunk. Mobile uses the existing stacked layout.'});
      } else if(p.kind==='align') {
        for(const row of targets) row.geometry[p.axis??'x']=p.position??16;
      } else if(p.kind==='snap') {
        const pitch=p.pitch??24;
        for(const row of targets) for(const k of ['x','y']) row.geometry[k]=Math.round(row.geometry[k]/pitch)*pitch;
      }
    }
    return {rows:results,shell,shellSources,diagnostics,palette,ruleOrder:rules.map(r=>r.id)};
  }
  const api={evaluate,selected,palette};
  if(typeof module!=='undefined' && module.exports) module.exports=api;
  root.AgoraPresentation=api;
})(typeof globalThis!=='undefined'?globalThis:this);
