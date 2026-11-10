// shell-reading: one machine reading as text (CPU 14%). Handles: key (a system.now key), label, show setting|always.
// With show=setting (the default) it appears only while shell-settings says show_<key>=yes (the quick settings switch).
export default {mount(api, s) {
  const K = globalThis.ShellKit;
  const key = String(s.key || 'cpu');
  const body = api.part('body', 'span', { class: 'read', 'aria-hidden': 'true' });
  body.hidden = true;
  let sys = {}, settings = {};
  const paint = () => {
    const on = s.show === 'always' || K.yes(settings['show_' + key]);
    const r = sys[key];
    body.hidden = !(on && r && r.value);
    if (!body.hidden) body.textContent = `${s.label || key.toUpperCase()} ${r.value}`;
  };
  K.watch(api, 'system', 2500, (v) => { sys = v; paint(); });
  K.watch(api, 'settings', 4000, (v) => { settings = v; paint(); });
  return body;
}};
