// shell-focused-app: the app in front, with its window menu (pin in place, minimise, close, keep in dock, leave alone).
// Handles: max (width, css px, default 250); parts body, icon, name, menu.
export default {mount(api, s) {
  const K = globalThis.ShellKit, { Icon, Pop, Menu, Data } = K;
  const icon = api.part('icon', 'span', { class: 'fi' });
  const name = api.part('name', 'span', { class: 'fn' });
  const body = api.part('body', 'button', { class: 'btn focus', 'aria-label': 'Focused app', 'aria-haspopup': 'dialog', 'aria-expanded': 'false' }, icon, name);
  if (s.max) body.style.maxWidth = K.num(s.max, 250) + 'px';
  body.hidden = true;
  let focused = null, lastKey = null, pins = [];
  K.watch(api, 'pins', 4000, (v) => { pins = v; });
  K.watch(api, 'windows', 2500, (wins) => {
    let f = wins.find((w) => w.focused) || null;
    if (f) lastKey = f.key; else f = wins.find((w) => w.key === lastKey) || null;   // while a bar has the focus, the app before it stays shown
    focused = f;
    body.hidden = !f;
    if (!f) return;
    if (icon.dataset.ref !== f.icon) { icon.dataset.ref = f.icon; icon.replaceChildren(Icon(f.icon, f.app, 'bar')); }
    if (name.textContent !== f.app) name.textContent = f.app;
    body.setAttribute('aria-label', `${f.app}, focused app. Open its window menu`);
  });
  const keep = async (f) => {
    await K.ran(Data.act(`make kind=button bar=taskbar label=${JSON.stringify(f.app)} path=${JSON.stringify(f.exe)} does=${JSON.stringify('window.launch path=' + f.exe)}`));
    K.toast(`${f.app} stays in the dock`);
    K.poke('pins');
  };
  body.addEventListener('click', () => {
    const f = focused;
    if (!f) return;
    const pinned = f.state === 'pinned';
    const inDock = !!f.exe && pins.some((p) => (p.path || '').toLowerCase() === f.exe.toLowerCase());
    Pop.open('app', body, () => Menu([
      { head: f.app, icon: Icon(f.icon, f.app, 26), note: f.managed === false && Data.wmOK ? 'left alone' : '' },
      '-',
      { label: pinned ? 'Unpin from its place' : 'Pin in place', glyph: pinned ? 'pin-off' : 'pin',
        run: () => K.ran(Data.act(`${pinned ? 'wm.unpin' : 'wm.pin'} ${f.key}`)), disabled: !Data.wmOK && !f.agora,
        hint: Data.wmOK ? '' : 'needs the window manager' },
      { label: 'Minimise', glyph: 'minus', run: () => K.ran(Data.minimise(f)) },
      { label: 'Close', glyph: 'x', danger: true, run: () => K.ran(Data.close(f)) },
      '-',
      { label: 'Keep in dock', glyph: 'grid', run: () => keep(f), disabled: !f.exe || inDock },
      ...(Data.wmOK && f.exe ? [{ label: f.managed === false ? 'Arrange this app again' : 'Leave this app alone', glyph: 'settings',
        run: () => K.ran(Data.act(`${f.managed === false ? 'wm.manage' : 'wm.leave-alone'} ${f.app}`)) }] : []),
    ], api.askBox()), { label: `${f.app} window menu`, align: 'left', cls: 'narrow', card: api.part('menu', 'div') });
  });
  return body;
}};
