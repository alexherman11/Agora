export default {mount(api,s){
  const {el,button}=api;
  const column=api.part('body','section',{class:'lane','data-lane':s.name,'data-drop':'card'});
  column._node=api.node;
  const children=api.children.map(api.render),count=children.reduce((n,c)=>n+c.querySelectorAll('.card').length,0);
  const content=el('div',{},...children);let open=true;
  column.append(api.part('heading','div',{class:'lanehead'},el('i',{class:'dot '+s.name}),api.display('name'),el('span',{class:'count'},count),button(s.name==='Done'?'⌄':'+',()=>{if(s.name==='Done'){open=!open;content.hidden=!open}else document.querySelector('[aria-label="Add a task"]').focus()})),content);
  if(!count)content.append(el('div',{class:'empty'},s.name==='Done'?'Good things take their time.':'Room for the next good idea.'));
  return column;
}};
