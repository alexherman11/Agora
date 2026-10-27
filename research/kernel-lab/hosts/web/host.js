"use strict";
// Host chrome only. Every painted view remains the desk's unmodified lens.html/lens.js.
let state, mark = {}, busy = false;
const frames = new Map(), main = document.querySelector('#panes'), switcher = document.querySelector('#switcher');
const message = document.querySelector('#message');
const quote = s => JSON.stringify(s);
const leafs = n => n.id ? [n] : n.kids.flatMap(leafs);
const title = s => s.charAt(0).toUpperCase() + s.slice(1);
const paneName = p => p.name || title(p.lens);
function el(tag, cls, text) {
  const n = document.createElement(tag); if (cls) n.className = cls; if (text) n.textContent = text; return n;
}
async function request(line, read = false) {
  const r = await fetch(read ? '/see' : '/do', {method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({line, ...(read ? {} : {saw: mark, press: crypto.randomUUID()})})});
  const out = await r.json(); if (!r.ok || !out.ok) throw Error(out.text || out.error || 'The door is away'); return out;
}
async function load() {
  const out = await request('panes', true), row = out.rows[0];
  mark = row.id ? {[row.id]: row.rev} : {};
  const changed = !state || JSON.stringify(state.tree) !== JSON.stringify(row.layout.tree);
  state = row.layout; if (changed) render(); else selection();
}
async function say(line) {
  if (busy) return;
  busy = true;
  try { const out = await request(line); message.textContent = out.text; await load(); }
  catch (e) { message.textContent = e.message; await load().catch(() => {}); }
  finally { busy = false; }
}
function focus(id) { return say(`pane.focus ${quote(id)}`); }
function pane(p) {
  if (frames.has(p.id)) return frames.get(p.id);
  const box = el('section', 'pane'); box.dataset.pane = p.id; box.dataset.lens = p.lens;
  const head = el('div', 'pane-head');
  const name = el('button', 'title', paneName(p)); name.onclick = () => focus(p.id); head.append(name);
  const split = el('button', '', '+'); split.title = 'Split this pane'; split.setAttribute('aria-label', `Split ${title(p.lens)}`);
  split.onclick = () => { document.querySelector('#line').value = `pane.split ${quote(paneName(p))} lens=help`; document.querySelector('#line').focus(); };
  const close = el('button', '', '×'); close.setAttribute('aria-label', `Close ${title(p.lens)}`);
  close.onclick = () => say(`pane.close ${quote(p.id)}`); head.append(split, close);
  let grab;
  head.onpointerdown = e => { if (e.pointerType === 'mouse' && e.button === 0) { grab = {x:e.clientX,y:e.clientY}; head.setPointerCapture(e.pointerId); } };
  head.onpointerup = e => {
    if (!grab) return; const moved = Math.hypot(e.clientX-grab.x,e.clientY-grab.y)>10; grab = null;
    const target = document.elementFromPoint(e.clientX,e.clientY)?.closest('.pane-head')?.parentElement.dataset.pane;
    if (moved && target && target !== p.id) say(`pane.move ${quote(p.id)} to=${quote(target)}`);
  };
  head.onpointercancel = () => { grab = null; };
  box.append(head);
  const frame = el('iframe'); frame.title = title(p.lens); frame.src = `/lens.html?lens=${encodeURIComponent(p.lens)}&inspect=0`;
  frame.onload = () => swipeOn(frame.contentDocument, true);
  box.append(frame);
  if (p.lens.toLowerCase() === 'feed') {
    const form = el('form', 'compose'), input = el('input'); input.placeholder = 'Share with your neighbours…'; input.required = true;
    input.setAttribute('aria-label', 'Post to Feed'); const send = el('button', '', 'Post'); form.append(input, send);
    form.onsubmit = async e => { e.preventDefault(); try { await request(`post ${quote(input.value)}`); message.textContent = 'Shared with your neighbours.'; input.value = ''; }
      catch (err) { message.textContent = err.message; } }; box.append(form);
  }
  frames.set(p.id, box); return box;
}
function tree(n, path = '') {
  if (n.id) { const mount = el('div', 'mount'); mount.dataset.mount = n.id; return mount; }
  const box = el('div', `split ${n.axis}`), left = el('div', 'slot'), right = el('div', 'slot');
  left.style.flex = `${n.ratio} 1 0`; right.style.flex = `${100-n.ratio} 1 0`; left.append(tree(n.kids[0], path+'0')); right.append(tree(n.kids[1], path+'1'));
  const bar = el('button', 'divider'); bar.setAttribute('aria-label', 'Resize panes');
  bar.onpointerdown = e => {
    bar.setPointerCapture(e.pointerId); const rect = box.getBoundingClientRect(); let ratio = n.ratio;
    bar.onpointermove = m => { ratio = Math.max(10, Math.min(90, Math.round(100 * (n.axis === 'row' ? (m.clientX-rect.x)/rect.width : (m.clientY-rect.y)/rect.height))));
      left.style.flex = `${ratio} 1 0`; right.style.flex = `${100-ratio} 1 0`; };
    bar.onpointerup = () => { bar.onpointermove = null; say(`pane.resize ${quote(leafs(n.kids[0])[0].id)} ratio=${ratio} at=${path || 'root'}`); };
  };
  box.append(left, bar, right); return box;
}
function render() {
  const panes = leafs(state.tree), keep = new Set(panes.map(p => p.id));
  for (const [id, box] of frames) if (!keep.has(id)) { box.remove(); frames.delete(id); }
  const built = tree(state.tree); main.append(built);
  for (const p of panes) {
    const mount = built.dataset.mount === p.id ? built : built.querySelector(`[data-mount="${p.id}"]`), box = pane(p);
    box.classList.toggle('active', state.active === p.id);
    if (box.isConnected && mount.moveBefore) mount.moveBefore(box, null); else mount.append(box);
  }
  [...main.children].filter(n => n !== built).forEach(n => n.remove());
  switcher.querySelectorAll('button').forEach(b => b.remove());
  for (const p of panes) { const b = el('button', '', paneName(p)); b.setAttribute('aria-current', String(state.active === p.id)); b.onclick = () => focus(p.id); switcher.append(b); }
}
function selection() {
  for (const [id, box] of frames) box.classList.toggle('active', state.active === id);
  const panes = leafs(state.tree); switcher.querySelectorAll('button').forEach((b, i) => b.setAttribute('aria-current', String(panes[i].id === state.active)));
}
function swipe(delta) {
  const all = leafs(state.tree), at = all.findIndex(p => p.id === state.active);
  focus(all[(at + delta + all.length) % all.length].id);
}
let start;
function swipeOn(node, content = false) {
  let down;
  node.addEventListener('pointerdown', e => {
    if (content && (innerWidth > 600 || e.pointerType === 'mouse' || e.target.closest('input,textarea,button,[contenteditable=true]'))) return;
    down = {x: e.clientX, y: e.clientY};
    if (e.pointerType !== 'mouse') e.target.setPointerCapture?.(e.pointerId);
  });
  node.addEventListener('pointerup', e => { if (down && Math.abs(e.clientX-down.x) > 45 && Math.abs(e.clientY-down.y) < 60) swipe(e.clientX < down.x ? 1 : -1); down = null; });
  node.addEventListener('pointercancel', () => { down = null; });
}
swipeOn(document.querySelector('#swipe'));
// Headers and the strip also work without entering the painter.
main.addEventListener('pointerdown', e => { if (e.target.closest('.pane-head')) start = {x:e.clientX,y:e.clientY}; });
main.addEventListener('pointerup', e => { if (start && e.pointerType !== 'mouse' && Math.abs(e.clientX-start.x)>45) swipe(e.clientX < start.x ? 1 : -1); start = null; });
document.querySelector('#swipe').onkeydown = e => { if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') { e.preventDefault(); swipe(e.key === 'ArrowRight' ? 1 : -1); } };
document.querySelector('#words').onsubmit = e => { e.preventDefault(); say(document.querySelector('#line').value); };
document.querySelector('#help').onclick = async () => {
  try { const replies = await Promise.all(['panes','pane.split','pane.close','pane.move','pane.focus','pane.resize'].map(w => request(`help ${w}`, true))); message.textContent = replies.map(r => r.text).join('\n'); }
  catch (e) { message.textContent = e.message; }
};
load().catch(e => { message.textContent = e.message; });
const stream = new EventSource('/door/stream');
stream.addEventListener('world', () => { if (!busy) load().catch(e => { message.textContent = e.message; }); });
window.addEventListener('pagehide', () => stream.close(), {once: true});
