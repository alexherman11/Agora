export default {mount(api,s){
  const f=api.facts,P=api.P,L=api.label,root=api.part('body','section',{class:'nb-poll','aria-label':L('poll','Neighbour poll')});
  const closed=f.closed||(f.closes&&new Date(f.closes)<=new Date()),options=String(f.options||'').split(/\s+/).filter(Boolean),results=closed||!!f.your_vote,total=Number(f.votes||0);
  if(!options.length){root.append(P.node('p',{class:'nb-meta'},L('empty','Options will appear here when a poll is ready.')));return root}
  root.append(api.part('closing','p',{class:'nb-meta'},(closed?L('closed','Closed'):L('open','Open'))+' · '+total+' '+(total===1?L('voteCount','vote'):L('votes','votes'))+(!closed&&f.closes?' · '+L('closes','Closes')+' '+api.format('stamp',f.closes):'')));
  for(const option of options){
    const count=Number(f['votes_'+option]||0),label=L(option,option),percentage=total?Math.round(count/total*100):0;
    if(results){const row=api.part('option','div',{class:'nb-option nb-poll-result'},P.node('span',{},label+(f.your_vote===option?' ✓ '+L('yourchoice','Your choice'):'')),api.part('counts','strong',{},percentage+'% · '+count));row.style.setProperty('--poll-share',percentage+'%');root.append(row)}
    else root.append(api.part('option','button',{type:'button',class:'nb-option','aria-label':L('vote','Vote')+' '+label,on:{click:async()=>{try{await api.fire('vote',{value:option})}catch(e){api.tell(e)}}}},P.node('span',{},label)));
  }
  root.append(P.node('small',{class:'nb-meta'},L('sealed','Only totals are shared. Your vote is private.')));return root;
}};
