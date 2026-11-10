// shell-bar: the top bar's rail. Holds its parts (any parts: islands by default) and tells the window where it is solid
// and what strip to reserve. Nothing else lives here.
export default {mount(api, s) {
  const K = globalThis.ShellKit;
  document.body.dataset.page = 'top';
  const rail = api.part('rail', 'header', { class: 'rail', role: 'toolbar', 'aria-label': s.label || 'Agora top bar' });
  for (const child of api.children) rail.append(api.render(child));
  const rov = K.roving(rail);
  rov.refresh();
  const watch = new MutationObserver(() => rov.refresh());
  watch.observe(rail, { childList: true, subtree: true, attributes: true, attributeFilter: ['hidden'] });
  api.cleanup(() => watch.disconnect());
  // the window is solid over the rail and whatever is open (popovers, the ask menu, a toast): ShellKit adds those
  K.shape = () => {
    const r = rail.getBoundingClientRect();
    return { reserve: Math.ceil(r.bottom), shape: [{ x: 0, y: 0, w: innerWidth, h: Math.ceil(r.bottom), r: 0 }] };
  };
  return rail;
}};
