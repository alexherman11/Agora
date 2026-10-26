export default {mount(api,s){
  const f=api.facts,P=api.P,L=api.label,root=api.part('body','section',{class:'nb-poll','aria-label':L('poll','Neighbour poll')});
  const closed=f.closes&&new Date(f.closes)<=new Date(),options=String(f.options||'').split(/\s+/).filter(Boolean);
  if(!options.length){root.append(P.node('p',{class:'nb-meta'},L('empty','Options will appear here when a poll is ready.')));return root}
  if(f.closes)root.append(api.part('closing','p',{class:'nb-meta'},closed?L('closed','Poll closed'):L('closes','Closes')+' '+new Date(f.closes).toLocaleString()));
  for(const option of options){
    const count=Number(f['votes_'+option]||0),label=L(option,option),b=api.part('option','button',{type:'button',class:'nb-option','aria-label':L('vote','Vote')+' '+label,on:{click:async()=>{try{await api.fire('vote',{value:option})}catch(e){api.tell(e)}}}},P.node('span',{},label),api.part('counts','strong',{},String(count)));
    b.disabled=!!closed;root.append(b);
  }
  root.append(P.node('small',{class:'nb-meta'},L('sealed','Only totals are shared. Your vote is private.')));return root;
}};
