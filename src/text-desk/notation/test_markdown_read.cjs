// Actual grammar/text/media modules on a small DOM stand-in. No browser/layout claims.
const test = require('node:test'), assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
function page() {
  const selection = { isCollapsed: true, anchorNode: null, rangeCount: 0 };
  class El {
    constructor(tag = 'div', text = null) {
      this.tagName = tag.toUpperCase(); this.nodeType = text === null ? 1 : 3;
      this.data = text; this.dataset = {}; this.childNodes = []; this.className = '';
      this.handlers = {}; this.attrs = {}; this.style = { setProperty() {} };
      this.classList = {
        add: (...xs) => { this.className = [...new Set([...this.className.split(' '), ...xs])].join(' ').trim(); },
        remove: x => { this.className = this.className.split(' ').filter(c => c !== x).join(' '); },
        contains: x => this.className.split(' ').includes(x),
        toggle: (x, on) => { if (on) this.classList.add(x); else this.classList.remove(x); }
      };
    }
    get children() { return this.childNodes.filter(c => c.nodeType === 1); }
    get textContent() { return this.nodeType === 3 ? this.data : this.childNodes.map(c => c.textContent).join(''); }
    set textContent(t) { this.replaceChildren(String(t)); }
    append(...xs) {
      for (let x of xs) { if (typeof x === 'string') x = new El('', x); x.parentElement = this; this.childNodes.push(x); }
    }
    replaceChildren(...xs) { this.childNodes = []; this.append(...xs); }
    after(x) { x.parentElement = this.parentElement; const a = this.parentElement.childNodes; a.splice(a.indexOf(this) + 1, 0, x); }
    setAttribute(k, v) { this.attrs[k] = String(v); }
    getAttribute(k) { return this.attrs[k] ?? null; }
    contains(x) { return x === this || this.children.some(c => c.contains(x)) || this.childNodes.includes(x); }
    matches(s) {
      return s.split(',').some(raw => {
        let q = raw.trim(), ok = true;
        q = q.replace(/:not\(([^)]+)\)/g, (_, n) => { if (this.matches(n)) ok = false; return ''; });
        q = q.replace(/\[([^\]=]+)(?:=["']?([^\]"']+)["']?)?\]/g, (_, a, v) => {
          const got = a.startsWith('data-') ? this.dataset[a.slice(5).replace(/-([a-z])/g, (_, c) => c.toUpperCase())] : this.attrs[a];
          if (got == null || (v != null && got !== v)) ok = false; return '';
        });
        const tag = q.match(/^[a-z]+/i);
        if (tag && this.tagName !== tag[0].toUpperCase()) ok = false;
        for (const c of q.matchAll(/\.([\w-]+)/g)) if (!this.classList.contains(c[1])) ok = false;
        return ok;
      });
    }
    closest(s) { return this.matches(s) ? this : this.parentElement?.closest(s) || null; }
    querySelectorAll(s) { return this.children.flatMap(c => [...(c.matches(s) ? [c] : []), ...c.querySelectorAll(s)]); }
    querySelector(s) { return this.querySelectorAll(s)[0] || null; }
    addEventListener(k, f) { (this.handlers[k] ||= []).push(f); }
    dispatch(k, extra = {}) {
      const e = { target: this, key: '', preventDefault() { this.defaultPrevented = true; }, stopPropagation() { this.stopped = true; }, ...extra };
      for (let p = this; p; p = e.stopped ? null : p.parentElement) for (const f of p.handlers[k] || []) f(e);
      return e;
    }
    click() { this.dispatch('click'); }
  }
  const document = { head: new El('head'), documentElement: new El('html'), activeElement: null, createElement: t => new El(t),
    createTextNode: t => new El('', t), addEventListener() {},
    createTreeWalker(root) {
      const all = [], walk = n => { for (const c of n.childNodes) { if (c.nodeType === 3) all.push(c); else walk(c); } };
      walk(root); return { nextNode: () => all.shift() || null };
    } };
  const external = [], sent = [];
  const ctx = vm.createContext({ document, NodeFilter: { SHOW_TEXT: 4 }, console,
    getSelection: () => selection, setTimeout: () => 0, clearTimeout() {},
    Style: { roleClass: s => s }, V: { notify() {}, show() {} },
    textOf: () => null, textConf: () => '', TEXT: { esc: s => s },
    linkFor: el => ({ _n: { acts: [{ on: 'link', line: 'view $value' }] } }),
    send: async (n, line) => sent.push(line), host: async line => sent.push('host ' + line) });
  ctx.window = ctx; ctx.open = (...a) => external.push(a);
  for (const f of ['markdown.js', 'textedit.js', 'media.js'])
    vm.runInContext(fs.readFileSync(path.join(__dirname, 'desk-shell', f), 'utf8'), ctx);
  const lens = fs.readFileSync(path.join(__dirname, 'desk-shell/lens.js'), 'utf8');
  vm.runInContext(lens.slice(lens.indexOf('  async function popMedia('), lens.indexOf('  function textFresh(')), ctx);
  vm.runInContext(lens.slice(lens.indexOf('  function textFresh('), lens.indexOf("  // a text's keys")), ctx);
  vm.runInContext('this.paintMedia = (el,n,p) => {\n'
    + lens.slice(lens.indexOf('    const inline = p.media'), lens.indexOf('    if (p.semantic)')) + '\n}', ctx);
  return { ...ctx, selection, external, sent, El };
}

test('read grammar composes safe formatting, inline image, film and keyboard links', () => {
  const p = page(), pops = [], follows = [];
  const source = '# Heading\n**bold** *italic*\n- nested\n  - child\n- [ ] unchanged\n> quoted\n---\n'
    + '```js\nconst raw = "a123";\n```\n| Key | Value |\n| --- | --- |\n| a123 | works |\n'
    + '![Cover](media/cover.png)\nmedia/film.mp4\n[Web](https://example.test/) [[a123]]';
  const te = p.TextEdit.create({ text: source, editable: false,
    links: { a123: { id: 'a123', title: 'Plan' } },
    things: { a123: { name: 'Plan', kind: 'note', open: 'a123' } },
    media: [{ kind: 'image', path: 'media/cover.png', src: '/media/cover.png', name: 'Cover' }],
    hooks: { pop: i => pops.push(i.path), follow: id => follows.push(id) } });
  const root = te.el.querySelector('.md-doc');
  for (const s of ['.md-h1', 'strong', 'em', '.md-li', '.md-check', '.md-quote', '.md-hr', '.md-code', 'table', 'img'])
    assert.ok(root.querySelector(s), s);
  assert.equal(root.contentEditable, undefined);
  assert.equal(root.querySelector('.md-check').getAttribute('aria-disabled'), 'true');
  root.querySelector('.md-check').click();
  assert.equal(te.src(), source);
  assert.equal(root.querySelector('.md-code').textContent, 'const raw = "a123";');
  assert.equal(root.querySelector('img').src, '/media/cover.png');
  assert.equal(root.querySelectorAll('.media-pop').length, 1);
  root.querySelector('.media-pop').click(); assert.deepEqual(pops, ['media/cover.png']);
  const named = root.querySelector('.md-wl');
  assert.equal(named.tabIndex, 0);
  assert.equal(named.dispatch('keydown', { key: 'Enter' }).defaultPrevented, true);
  assert.deepEqual(follows, ['a123']);
  const web = root.querySelector('a.md-a'); web.dispatch('keydown', { key: 'Enter' });
  assert.deepEqual(p.external, [['https://example.test/', '_blank', 'noopener']]);
  p.selection.isCollapsed = false; p.selection.anchorNode = named;
  named.click(); assert.equal(follows.length, 1, 'selection must not navigate');
  p.selection.isCollapsed = true;
  te.links({ a123: { id: 'a123', title: 'Revised plan' } });
  assert.equal(root.querySelectorAll('.media-pop').length, 1, 'one control after repaint');
});

test('untrusted syntax never gains executable elements, remote images or protocol actions', () => {
  const p = page(), followed = [];
  const te = p.TextEdit.create({ editable: false,
    text: '<script>alert(1)</script>\n![Remote](https://example.test/secret)\n[Bad](javascript:alert)\n[File](file:///secret)\n`<img onerror=run>`',
    hooks: { follow: id => followed.push(id) } });
  const root = te.el.querySelector('.md-doc');
  assert.equal(root.querySelectorAll('script,img').length, 0);
  for (const a of root.querySelectorAll('a')) { assert.equal(a.tabIndex, undefined); a.click(); a.dispatch('keydown', { key: 'Enter' }); }
  assert.equal(p.external.length, 0); assert.equal(followed.length, 0);
  assert.ok(root.textContent.includes('<script>alert(1)</script>'));
});

test('actual lens fallback keeps text on throw or invisible malformed Markdown, media remains separate', () => {
  const p = page(), el = new p.El();
  const n = { key: 'message', acts: [], fence: {} };
  p.markdown(el, n, { text: '```' });
  assert.equal(el.dataset.mdFailed, '1'); assert.equal(el.textContent, '```');
  p.TextEdit.create = () => { throw new Error('fake renderer failure'); };
  const failed = new p.El(); p.markdown(failed, n, { text: 'Readable fallback' });
  assert.equal(failed.textContent, 'Readable fallback');
  p.Media.draw(failed, { mode: 'embed', items: [{ kind: 'video', src: '/media/film.mp4', path: 'media/film.mp4', name: 'Film' }] });
  assert.ok(failed.querySelector('video'));
  assert.ok(failed.textContent.includes('Readable fallback'));
});

test('inline native Pop out routes the authored actions and original path only', async () => {
  const p = page(), el = new p.El(), n = { key: 'message', fence: {}, acts: [
    { on: 'pop', line: 'set src="$value"' }, { on: 'pop', line: 'host window media-player' }] };
  el._n = n;
  p.markdown(el, n, { text: '![Cover](media/cover.png)', media: { items: [
    { kind: 'image', path: 'media/cover.png', src: '/media/cover.png', name: 'Cover' }] } });
  assert.ok(el.querySelector('.media-pop')); el.querySelector('.media-pop').click();
  await new Promise(r => setImmediate(r));
  assert.deepEqual(p.sent, ['set src="media/cover.png"', 'host window media-player']);
});

test('actual painter media composition and read update retain one picture, film node and prose', () => {
  const p = page(), el = new p.El(), n = { key: 'message', fence: {}, acts: [
    { on: 'pop', line: 'host window media-player' }] };
  el._n = n;
  const paint = { text: 'One prose paragraph.\n![Cover](media/cover.png)\nmedia/film.mp4',
    media: { mode: 'embed', items: [
      { kind: 'image', path: 'media/cover.png', src: '/media/cover.png', name: 'Cover' },
      { kind: 'video', path: 'media/film.mp4', src: '/media/film.mp4', name: 'Film' }] } };
  p.markdown(el, n, paint); p.paintMedia(el, n, paint);
  const film = el.querySelector('video');
  assert.equal(el.querySelectorAll('img').length, 1);
  assert.equal(el.querySelectorAll('video').length, 1);
  assert.equal(el.textContent.split('One prose paragraph.').length - 1, 1);
  p.textFresh(el, n, { ...paint, text: paint.text + '\nIncoming formatted **update**.' });
  assert.equal(el.querySelector('video'), film);
  assert.equal(el.querySelectorAll('img').length, 1);
  assert.equal(el.querySelectorAll('.media-pop').length, 2);
  assert.ok(el.textContent.includes('Incoming formatted **update**.'));
});
