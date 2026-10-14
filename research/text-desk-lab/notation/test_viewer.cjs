const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function viewer(saved = []) {
  const store = new Map([['lens-drafts:test:codex:review', JSON.stringify(saved)]]);
  const ctx = vm.createContext({
    localStorage: { getItem: key => store.get(key), setItem: (key, value) => store.set(key, value) },
    Style: { roleClass: name => name },
  });
  vm.runInContext(fs.readFileSync(path.join(__dirname, 'desk-shell/viewer.js'), 'utf8') +
    '\nthis.makeViewer = Viewer;', ctx);
  return ctx.makeViewer('test', 'codex', 'review', {}, {});
}

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
