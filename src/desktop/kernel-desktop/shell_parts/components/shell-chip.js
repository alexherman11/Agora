// shell-chip: one machine reading as a glyph in the tray (network, volume, battery, or any system.now key), with its
// value when `value` is yes (battery shows its percentage by default). Hidden while the machine has no such reading.
// Gesture press: what its row in the quick settings says (default window.settings which=<key>).
export default {mount(api, s) {
  const K = globalThis.ShellKit, { h, glyph } = K;
  const key = String(s.key || 'network');
  const body = api.part('body', 'span', { class: 'q-chip q-' + key.replace(/[^\w-]/g, '') });
  body.dataset.factKey = key;
  const showValue = s.value === undefined || s.value === '' ? key === 'battery' : s.value === true || K.yes(s.value);
  const pick = (r) => {
    if (key === 'network') return r ? 'wifi' : 'wifi-off';
    if (key === 'volume') { const v = r ? r.value : ''; return v === 'muted' ? 'volume-x' : parseInt(v, 10) < 34 ? 'volume-low' : 'volume'; }
    if (key === 'battery') return /charging/.test((r && r.detail) || '') ? 'battery-charging' : 'battery';
    return key === 'memory' ? 'memory' : 'cpu';
  };
  let last = '';
  K.watch(api, 'system', 2500, (sys) => {
    const r = sys[key];
    const absent = (key === 'battery' || key !== 'network') && !(r && r.value);
    body.hidden = absent;
    if (absent) return;
    const g = pick(r), text = showValue ? r.value : '';
    const sig = g + '|' + text;
    if (sig === last) return;
    last = sig;
    body.replaceChildren(api.part('glyph', 'span', {}, glyph(g)), text ? api.part('value', 'span', { class: 'q-pct' }, text) : '');
    body.dataset.low = key === 'battery' && parseInt(r.value, 10) <= 15 && !/charging/.test(r.detail || '') ? 'yes' : 'no';
  });
  return body;
}};
