export default {mount(api,s){
  const f=api.facts,L=api.label,full=Number(f.seats_left||0)===0,root=api.part('body','section',{class:'nb-slots'});
  if(!f.id){root.append(api.P.node('p',{class:'nb-meta'},L('empty','Available places will appear here.')));return root}
  const description=api.P.node('div',{}),name=s.label||(f.event?(f.title||f.name):'');
  if(name)description.append(api.part('label','strong',{},L(name,name)),api.P.node('br',{}));
  const total=Number(f.seats||1),left=Number(f.seats_left||0);
  description.append(api.part('meter','meter',{min:0,max:total,value:total-left,'aria-label':L('filledplaces','Filled places')}),api.part('count','span',{},full?(total===1?L('onefilled','Place filled'):L('all','All')+' '+total+' '+L('filled','places filled')):left+' '+L('of','of')+' '+total+' '+L(total===1?'one-left':'left',total===1?'place left':'places left')));root.append(description);
  const closed=f.closes&&new Date(f.closes)<=new Date();
  if(!full&&!closed){const b=api.part('claim','button',{type:'button',class:'nb-primary',on:{click:async()=>{try{await api.fire('claim')}catch(e){api.tell(e)}}}},L('claim','Take a place'));root.append(b)}return root;
}};
