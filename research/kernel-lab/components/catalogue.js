// Catalogue pieces compose core primitives. They have no private fact store.
export default {mount(api,s){
  const {P}=api,kind=api.node.component,children=()=>api.children.map(api.render);
  const root=api.part('body','section',{'aria-label':s.label||kind});
  const label=s.label||kind;
  const fire=event=>values=>api.fire(event,values).catch(api.tell);
  if(kind==='button')return api.part('control','button',{type:'button',on:{click:()=>fire('press')({})}},label);
  if(['input','editor','choice','switch'].includes(kind)){
    const type=kind==='editor'?'multiline':kind==='choice'?'choice':kind==='switch'?'toggle':'text';
    const n=api.part('control',type==='multiline'?'textarea':type==='choice'?'select':'input',{'aria-label':label,value:s.value||'',placeholder:s.hint||'',...(type==='toggle'?{type:'checkbox'}:{})});
    if(type==='choice')for(const value of String(s.options).split('|'))n.append(P.node('option',{value},value));
    if(type==='toggle')n.checked=!!s.checked;
    const commit=()=>fire('change')({value:type==='toggle'?(n.checked?'yes':'no'):n.value});
    n.addEventListener('change',commit);root.append(P.node('label',{},label),n);return root;
  }
  if(['text-block','markdown','code','icon','image','avatar','player'].includes(kind)){
    const type=({'text-block':'text',player:'media'})[kind]||kind;
    root.append(P.content(type,s.value||s.label,{'aria-label':label}));return root;
  }
  if(['badge','progress','empty-state'].includes(kind)){
    if(kind==='progress')root.append(P.node('progress',{max:s.max,value:s.value,'aria-label':label}),P.content('text',label));
    else root.append(P.content('text',label));return root;
  }
  if(['dialog','popover','tooltip','toast','drawer'].includes(kind)){
    root.append(P.press(label,()=>P.overlay(kind,P.layout('stack',{},P.content('text',s.text||label),...children()),{label,anchor:{x:80,y:80}})));
    return root;
  }
  if(kind==='palette'){
    const input=P.input('text',{'aria-label':label,placeholder:'Find a command…'}),list=P.layout('stack',{},...children());
    input.addEventListener('input',()=>{for(const n of list.children)n.hidden=!n.textContent.toLowerCase().includes(input.value.toLowerCase())});
    return P.navigation(P.layout('stack',{},input,list));
  }
  if(['chart','map','pixel-surface'].includes(kind)){
    const data=s.data||[];
    const surface=P.canvas({width:s.width,height:s.height,label,pixels:kind==='pixel-surface'?s.pixels:null,series:kind==='chart'?data:null});
    if(kind==='map'){
      const ctx=surface.getContext('2d');ctx.fillStyle=P.tokens.accent;
      for(const point of data){ctx.beginPath();ctx.arc(+point.x||0,+point.y||0,5,0,Math.PI*2);ctx.fill()}
    }
    surface.addEventListener('click',e=>{if(api.node.gestures.some(g=>g.event==='press')){const r=surface.getBoundingClientRect();fire('press')({x:(e.clientX-r.left)*surface.width/r.width,y:(e.clientY-r.top)*surface.height/r.height})}});
    root.append(surface,P.content('text',s.caption||''));return root;
  }
  if(kind==='table'){
    const table=P.node('table',{'aria-label':label}),cols=String(s.columns).split('|');
    table.append(P.node('thead',{},P.node('tr',{},...cols.map(x=>P.node('th',{scope:'col'},x)))));
    const body=P.node('tbody');for(const row of s.data||[])body.append(P.node('tr',{},...cols.map(c=>P.node('td',{},row[c]??''))));
    table.append(body);root.append(table,...children());return root;
  }
  if(kind==='calendar'){
    const [year,month]=s.month.split('-').map(Number),start=new Date(Date.UTC(year,month-1,1)),days=new Date(Date.UTC(year,month,0)).getUTCDate();
    const grid=P.layout('grid',{role:'grid','aria-label':label});grid.style.gridTemplateColumns='repeat(7,minmax(0,1fr))';
    for(const name of ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'])grid.append(P.content('text',name));
    for(let i=0;i<start.getUTCDay();i++)grid.append(P.content('text',''));
    for(let day=1;day<=days;day++)grid.append(P.press(String(day),()=>fire('select')({value:`${s.month}-${String(day).padStart(2,'0')}`})));
    root.append(P.content('text',s.month),grid,...children());return P.navigation(root);
  }
  if(kind==='tree'){
    root.setAttribute('role','tree');for(const child of children()){const d=P.node('details',{},P.node('summary',{},child.getAttribute('aria-label')||child.dataset.component||'Item'),child);root.append(d)}
    return P.navigation(root);
  }
  if(kind==='virtual-list')return P.virtual(api.children.map(n=>()=>api.render(n)),{height:s.height,rowHeight:s.row_height});
  const mode=kind==='gallery'?'grid':kind==='timeline'?'row':kind==='toolbar'||kind==='tabs'?'row':kind==='split-pane'?'split':'stack';
  root.append(P.layout(mode,{},...children()));return P.navigation(root);
}};
