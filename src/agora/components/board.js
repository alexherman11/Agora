export default {mount(api,s){
  const {el,button}=api;
  const app=api.part('body','main');
  const input=api.part('input','input',{placeholder:s.hint,'aria-label':'Add a task',on:{keydown:async e=>{if(e.key==='Enter'&&e.currentTarget.value.trim()){const value=e.currentTarget.value;e.currentTarget.value='';await api.fire('add',{value})}}}});
  const filters=api.part('filters','div',{class:'filters'});
  for(const p of ['all','1','2','3','4'])filters.append(button(p==='all'?'All tasks':'P'+p,()=>api.fire('filter',{value:p}),s.filter===p?'selected':''));
  filters.append(el('span',{class:'space'}),button('Summarize board',()=>api.fire('summarize')));
  app.append(el('div',{class:'heading'},el('div',{},el('div',{class:'eyebrow'},s.eyebrow),el('h1',{},s.title)),el('div',{class:'mark'},el('i'),'Shared world')),el('p',{class:'sub'},s.subtitle),el('div',{class:'tools'},el('div',{class:'quick'},el('span',{class:'plus'},'+'),input),el('span',{class:'key'},'N'),button('Undo',()=>api.fire('undo'),'soft')),filters);
  const lanes=api.part('lanes','div',{class:'board'});for(const child of api.children)lanes.append(api.render(child));
  // A collection is only an arrangement wrapper; its children share the grid.
  for(const wrapper of lanes.querySelectorAll('.column'))if(wrapper.parentElement===lanes)wrapper.style.display='contents';
  lanes.style.gridTemplateColumns=`repeat(${lanes.querySelectorAll('.lane').length},minmax(0,1fr))`;
  app.append(lanes,el('footer',{class:'foot'},el('span',{},'Drag to move · right-click for actions'),el('span',{},'One world. Every change remembered.')));return app;
}};
