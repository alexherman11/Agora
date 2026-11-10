// shell-island: a rounded group of parts on the bar (left, middle, right). Any parts can go inside, in any order.
export default {mount(api, s) {
  const side = ['left', 'middle', 'right'].includes(s.side) ? s.side : 'left';
  const isle = api.part('body', 'div', { class: 'isle ' + (side === 'middle' ? 'mid' : side), role: 'group', 'aria-label': s.label || side });
  for (const child of api.children) isle.append(api.render(child));
  return isle;
}};
