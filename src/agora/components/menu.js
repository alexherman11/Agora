export default {mount(api,s){
  const menu=api.part('body','div',{class:'menu',role:'menu'});menu.hidden=true;
  for(const g of api.node.gestures){
    const match=/^menu "(.*)"$/.exec(g.event);if(!match)continue;
    menu.append(api.part('item','button',{on:{click:()=>{api.closeMenu();api.fire(g.event).catch(api.tell)}}},match[1]));
  }
  return menu;
}};
