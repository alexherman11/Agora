const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

test('actual read-only text listener routes Agora deep links through the lens hook, never external-open', () => {
  const elements = [], followed = [], external = [];
  const document = { head: { append() {} }, createElement() {
    const el = { dataset: {}, children: [], classList: { add() {} }, handlers: {},
      append(k) { this.children.push(k); },
      addEventListener(k, f) { this.handlers[k] = f; } };
    elements.push(el); return el;
  } };
  const ctx = vm.createContext({ document, window: { open: (...a) => external.push(a) },
    Markdown: { draw() {}, lightUp() {}, lineOf: () => null } });
  vm.runInContext(fs.readFileSync(path.join(__dirname, 'desk-shell/textedit.js'), 'utf8'), ctx);
  ctx.TextEdit.create({ text: '[First](agora://current/item/a1)', editable: false,
    hooks: { follow: (...a) => followed.push(a) } });
  function click(href) {
    let prevented = false;
    const a = { dataset: { href }, textContent: 'First' };
    elements.find(e => e.className === 'md-doc').handlers.click({ target: { closest: s => s === 'a.md-a' ? a : null },
      preventDefault() { prevented = true; } });
    return prevented;
  }
  assert.equal(click('agora://current/item/a1'), true);
  assert.deepEqual(followed, [['agora://current/item/a1', 'First']]);
  assert.equal(external.length, 0);
  assert.equal(click('https://example.test/'), true);
  assert.deepEqual(external, [['https://example.test/', '_blank', 'noopener']]);
  assert.equal(click('file:///C:/private'), false);
  assert.equal(click('javascript:alert(1)'), false);
  assert.equal(external.length, 1);
  assert.equal(followed.length, 1);
});

function viewer(saved = [], document = undefined, backing = undefined) {
  const store = backing || new Map([['lens-drafts:test:codex:review', JSON.stringify(saved)]]);
  const ctx = vm.createContext({
    document,
    setTimeout: () => 0, clearTimeout: () => {},
    localStorage: { getItem: key => store.get(key), setItem: (key, value) => store.set(key, value) },
    Style: { roleClass: name => name },
  });
  vm.runInContext(fs.readFileSync(path.join(__dirname, 'desk-shell/viewer.js'), 'utf8') +
    '\nthis.makeViewer = Viewer;', ctx);
  return ctx.makeViewer('test', 'codex', 'review', {}, {});
}

test('reading scopes retain independent tab positions and survive a viewer reload without touching drafts', () => {
  const store = new Map();
  const scope = { dataset: { key: 'viewer/first', remember: 'tab-1-entry-0' } };
  const frame = { dataset: { key: 'viewer/first/body', scroll: 'scroll' }, scrollTop: 320,
    closest: () => scope };
  const doc = { querySelectorAll: () => [frame] };
  const v = viewer([], doc, store);
  v.typed('composer', 'Unsent words', { key: 'composer', fence: { at: 1 } });
  const draft = store.get('lens-drafts:test:codex:review');
  v.captureReading();
  scope.dataset.remember = 'tab-2-entry-0';
  v.restoreReading();
  assert.equal(frame.scrollTop, 0, 'new tab must not inherit old DOM scrollTop');
  frame.scrollTop = 91; v.captureReading();
  scope.dataset.remember = 'tab-1-entry-0'; v.restoreReading();
  assert.equal(frame.scrollTop, 320);
  const reload = viewer([], doc, store);
  frame.scrollTop = 0; reload.restoreReading();
  assert.equal(frame.scrollTop, 320);
  scope.dataset.remember = 'tab-2-entry-0'; reload.restoreReading();
  assert.equal(frame.scrollTop, 91);
  assert.equal(store.get('lens-drafts:test:codex:review'), draft);
  assert.equal(reload.drafts.get('composer').text, 'Unsent words');
  // Folding/hiding a reader must not overwrite its saved position with the
  // zero that browsers report for an element without layout boxes.
  frame.getClientRects = () => [];
  frame.scrollTop = 0; reload.captureReading();
  frame.getClientRects = () => [{}];
  reload.restoreReading();
  assert.equal(frame.scrollTop, 91);
  const serialized = store.get('lens-reading:test:codex:review');
  assert.ok(!serialized.includes('Unsent words'));
  assert.ok(!serialized.includes('fence'));
});

test('reading scopes reject corrupt positions and do not remember clip-only frames', () => {
  const store = new Map([['lens-reading:test:codex:review', JSON.stringify([['bad', -4], ['worse', 'secret']])]]);
  const scope = { dataset: { key: 's', remember: 'one' } };
  const frame = { dataset: { key: 's/body', scroll: 'none' }, scrollTop: 55, closest: () => scope };
  const v = viewer([], { querySelectorAll: () => [frame] }, store);
  v.captureReading();
  assert.equal(v.reading().size, 0);
  v.restoreReading();
  assert.equal(frame.scrollTop, 55);
});

test('refused reply keeps its words and uses the refreshed view on an explicit retry', () => {
  const v = viewer(), original = { key: 'thread/reply', fence: { at: 1 } };
  v.typed(original.key, 'My unsent words', original);
  const token = v.beginSend(original.key);
  v.answered(original.key, 'definition changed', 'My unsent words', token);
  assert.equal(v.editOrigin(original.key, original), null);
  assert.equal(v.words(original.key, '', { at: 2 }), 'My unsent words');
  assert.equal(v.editOrigin(original.key, original).fence.at, 2);
  v.typed(original.key, 'My unsent words, continued', { key: original.key, fence: { at: 3 } });
  assert.equal(v.editOrigin(original.key, original).fence.at, 2);
  assert.equal(v.drafts.get(original.key).text, 'My unsent words, continued');
});

test('legacy unknown-origin text can be explicitly recovered without copying or sending it', () => {
  const v = viewer([['thread/reply', { text: 'Keep this text' }]]);
  const current = { key: 'thread/reply', fence: { at: 9 }, text: '' };
  assert.equal(v.words(current.key, '', current.fence), 'Keep this text');
  assert.equal(v.editOrigin(current.key, current), null);
  assert.equal(v.useCurrent(current.key, current), true);
  assert.equal(v.drafts.get(current.key).text, 'Keep this text');
  assert.equal(v.editOrigin(current.key, current).fence.at, 9);
  assert.equal(v.drafts.get(current.key).gesture, undefined);
});

test('recovery cannot replace an in-flight draft; successful send preserves later typing', () => {
  const v = viewer(), n = { key: 'thread/reply', fence: { at: 1 } };
  v.typed(n.key, 'First', n);
  const token = v.beginSend(n.key);
  assert.equal(v.useCurrent(n.key, { ...n, fence: { at: 2 } }), false);
  v.typed(n.key, 'Second', n);
  v.answered(n.key, null, 'First', token);
  assert.equal(v.drafts.get(n.key).text, 'Second');
  assert.equal(v.editOrigin(n.key, n).fence.at, 1);
});

test('a moved editor field keeps its draft but requires explicit origin recovery', () => {
  const v = viewer(), old = 'page/doc/a12/comments/c34/answer', current = 'page/wrapper/doc/a12/comments/c34/answer';
  const origin = { key: old, fence: { item: 'a12', at: 1 } };
  v.typed(old, 'Unsent before the layout change', origin);
  const node = { key: current, fence: { item: 'a12', at: 2 }, acts: [{ on: 'edit' }], kids: [] };
  v.recoverLayout({ key: 'page', kids: [node] });
  assert.equal(v.drafts.has(old), false);
  assert.equal(v.drafts.get(current).text, 'Unsent before the layout change');
  assert.equal(v.editOrigin(current, node), null);
  assert.equal(v.useCurrent(current, node), true);
  assert.equal(v.editOrigin(current, node).fence.at, 2);
});

test('layout recovery refuses ambiguous locations and never moves an in-flight send', () => {
  const v = viewer(), old = 'old/a12/c34/answer';
  v.typed(old, 'Keep', { key: old, fence: { item: 'a12' } });
  const n = key => ({ key, fence: { item: 'a12' }, acts: [{ on: 'edit' }], kids: [] });
  v.recoverLayout({ key: 'root', kids: [n('one/a12/c34/answer'), n('two/a12/c34/answer')] });
  assert.equal(v.drafts.has(old), true);
  v.beginSend(old);
  v.recoverLayout({ key: 'root', kids: [n('one/a12/c34/answer')] });
  assert.equal(v.drafts.has(old), true);
});
