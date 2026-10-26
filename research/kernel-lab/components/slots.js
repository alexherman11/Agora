export default {mount(api,s){
  const f=api.facts,L=api.label,full=Number(f.seats_left||0)===0,root=api.part('body','section',{class:'nb-slots'});
  if(!f.id){root.append(api.P.node('p',{class:'nb-meta'},L('empty','Available places will appear here.')));return root}
  const description=api.P.node('div',{}),name=s.label||(f.event?(f.title||f.name):'');
  if(name)description.append(api.part('label','strong',{},L(name,name)),api.P.node('br',{}));
  description.append(api.part('count','span',{},full?L('filled','All places filled'):String(f.seats_left)+' '+(Number(f.seats_left)===1?L('one-left','place left'):L('left','places left'))));root.append(description);
  const b=api.part('claim','button',{type:'button',class:'nb-soft',on:{click:async()=>{try{await api.fire('claim')}catch(e){api.tell(e)}}}},L('claim','Take a place'));b.disabled=full;root.append(b);return root;
}};
