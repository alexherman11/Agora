// Source-only DOM/transport mocks. Executes the actual composer and preparation
// functions, not a mirror of their branch logic. No browser, world or clipboard.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const source = fs.readFileSync(path.join(__dirname, "../../text-desk-lab/notation/desk-shell/lens.js"), "utf8");
const prepare = source.slice(source.indexOf("  const quoteDrafts ="), source.indexOf("  // the selection as it was"));
const composer = source.slice(source.indexOf("  const openComposers ="), source.indexOf("  function edits("));

class Element {
  constructor(tag) {
    this.tagName = tag; this.children = []; this.dataset = {}; this.style = {};
    this.classList = {add() {}}; this.value = ""; this.isConnected = true;
    this.listeners = {};
  }
  append(...els) { this.children.push(...els); }
  replaceChildren(...els) { this.children = els; }
  setAttribute() {}
  addEventListener(name, f) { this.listeners[name] = f; }
  click() { return this.disabled ? undefined : this.onclick?.(); }
  blur() {}
}
function fixture({plainAbout = "", quotedAbout = "", plainLine, quotedLine, filtered = false, compiledNode, snapshot} = {}) {
  const sent = [], notices = [], drafts = new Map(), elements = new Map();
  let stale = false, captures = 0, transportError = false;
  const context = {
    console, URLSearchParams, Map, Set, JSON, CSS: {escape: x => x},
    innerHeight: 900, getComputedStyle: () => ({lineHeight: "20px", fontSize: "14px"}),
    session: "mock-copy", who: "fixture", lens: "fixture",
    document: {activeElement: null, createElement: tag => new Element(tag)},
    window: {}, Style: {roleClass: x => x}, settle() {},
    TEXT: {selected: () => "", esc: x => x.replaceAll("\\", "\\\\").replaceAll('"', '\\"')},
    SEL: {fresh: () => true},
    paint: {querySelector: q => elements.get(q.match(/data-key="(.*)"/)[1])},
    V: {
      drafts, notify: x => notices.push(x), mark() {},
      words: (key, baseline) => drafts.get(key)?.text ?? baseline,
      editOrigin: (key, node) => node,
      typed: (key, text) => drafts.set(key, {text, seen: true}),
      drop: key => drafts.delete(key),
    },
    fetch: async (url, opts) => {
      assert.equal(url, "/api/selection"); captures++;
      const p = JSON.parse(opts.body).selection;
      if (snapshot) {
        for (const key of ["item", "rev", "field", "start", "end", "quote", "context"])
          assert.deepEqual(p[key], snapshot[key]);
      }
      return {json: async () => stale ? {error: "stale source/context"} : {
        selection: snapshot || {...p, label: "Source", before: "", after: ""}
      }};
    },
    send: async (node, line, raw, unused, attachment) => {
      sent.push({line, raw, attachment});
      if (transportError) return {error: "append succeeded; cleanup refused"};
      drafts.delete(node.key); return {text: "ok"};
    },
  };
  vm.createContext(context);
  vm.runInContext(prepare + composer + "\nglobalThis.api={composer,prepareQuote,quoteDrafts};", context);
  const n = compiledNode || {key: "hud/talk/say", paint: {text: "", commit: "explicit"}, fence: {},
    acts: [
      {on: "edit", line: plainLine || `do append plain line="$value"${plainAbout}`},
      ...filtered ? [] : [{on: "edit-quoted", line: quotedLine || `do append quoted line="$value" quote="$quote_text" source="$quote_item"${quotedAbout}`}]
    ]};
  const el = new Element("div"); el._n = n; elements.set(n.key, el);
  context.api.composer(el, n, n.acts.find(a => a.on === "edit"));
  const input = el.children[1], actions = el.children[2];
  const post = actions.children[0], status = actions.children[3];
  const remove = el.children[0].children[1];
  function type(words) {
    context.document.activeElement = input; input.value = words;
    input.listeners.input();
  }
  async function quote(words = "source $value words", item = "source") {
    await context.api.prepareQuote(n.key + " context=topic", {
      item, rev: 5, field: "text", start: 0, end: words.length, quoted: words,
    }, {fence: {reads: [["topic", 7]]}});
  }
  return {sent, notices, drafts, n, el, input, post, remove, status,
    type, quote, api: context.api, context,
    stale: () => {stale = true;}, transportError: () => {transportError = true;},
    captures: () => captures};
}

(async () => {
  let f = fixture(); f.type("ordinary");
  await f.post.click();
  assert.equal(f.sent.length, 1); assert.match(f.sent[0].line, /append plain/);
  assert.equal(f.sent[0].attachment, undefined);
  console.log("PASS plain Send dispatches exactly one plain action");

  f = fixture(); f.type("kept words"); await f.quote();
  assert.equal(f.input.value, "kept words"); assert.equal(f.sent.length, 0);
  await Promise.all([f.post.onclick(), f.post.onclick()]);
  assert.equal(f.sent.length, 1); assert.match(f.sent[0].line, /append quoted/);
  assert.match(f.sent[0].line, /source \$value words/); // no second expansion
  assert.equal(f.sent[0].attachment.quote.rev, 5);
  assert.equal(f.api.quoteDrafts.size, 0);
  console.log("PASS prepared quoted Send dispatches exactly one quoted action");

  f = fixture(); f.type("keep after removal"); await f.quote();
  f.remove.click();
  assert.equal(f.input.value, "keep after removal"); assert.equal(f.api.quoteDrafts.size, 0);
  const before = f.captures(); await f.post.click();
  assert.equal(f.sent.length, 1); assert.match(f.sent[0].line, /append plain/);
  assert.equal(f.captures(), before);
  console.log("PASS Remove quote restores plain Send without changing words");

  f = fixture(); f.type("keep"); await f.quote("first"); await f.quote("second");
  assert.equal(f.api.quoteDrafts.get(f.n.key).quote, "first");
  assert.match(f.notices.at(-1), /already attached/); assert.equal(f.sent.length, 0);
  for (const options of [{plainAbout: ' about="other"'}, {quotedAbout: ' about="other"'}]) {
    f = fixture(options); f.type("keep"); await f.quote();
    assert.equal(f.api.quoteDrafts.size, 0); assert.equal(f.input.value, "keep");
    assert.match(f.notices.at(-1), /another topic/); assert.equal(f.sent.length, 0);
  }
  console.log("PASS conflicting existing quote or plain/quoted About refuses preparation");

  f = fixture(); f.type("kept stale"); await f.quote(); f.stale(); await f.post.click();
  assert.equal(f.sent.length, 0); assert.equal(f.input.value, "kept stale");
  assert.equal(f.api.quoteDrafts.size, 1); assert.equal(f.drafts.get(f.n.key).text, "kept stale");
  assert.match(f.status.textContent, /stale source\/context/);
  console.log("PASS stale pre-Send refusal retains draft and quote, dispatches nothing");

  f = fixture(); f.type("kept partial"); await f.quote(); f.transportError(); await f.post.click();
  assert.equal(f.sent.length, 1); assert.match(f.sent[0].line, /append quoted/);
  assert.equal(f.api.quoteDrafts.size, 1); assert.equal(f.input.value, "kept partial");
  f.remove.click(); await f.post.click();
  assert.equal(f.sent.length, 2); assert.match(f.sent[1].line, /append plain/);
  console.log("PASS partial-batch error retains quote and words; removal chooses plain");

  const native = JSON.parse(fs.readFileSync(path.join(__dirname, "NATIVE-SEND-INSPECTION.json"), "utf8"));
  for (const a of native.edit_parts[0].actions.filter(a => [3, 5].includes(a.commands))) {
    // These are the exact authored existing-Talk batches. The mock intentionally
    // leaves world substitutions intact, testing that the composer keeps suffixes.
    const quotedLine = a.line.replace('quote="$(held)"', 'quote="$quote_text"');
    f = fixture({plainLine: a.line, quotedLine}); f.type("native words");
    await f.post.click();
    assert.equal(f.sent.length, 1);
    assert.equal(f.sent[0].line, a.line.replaceAll("$value", "native words"));
    // An empty context here avoids treating the deliberately unexpanded
    // $(pointing) test input as a real existing topic.
    f = fixture({plainLine: a.line.replace("about=$(pointing)", 'about=""'),
      quotedLine: quotedLine.replace("about=$(pointing)", 'about=""')}); f.type("native quote");
    await f.quote("excerpt"); await f.post.click();
    assert.equal(f.sent.length, 1);
    assert.equal(f.sent[0].line, quotedLine.replace("about=$(pointing)", 'about=""').replaceAll("$value", "native quote").replaceAll("$quote_text", "excerpt"));
  }
  console.log("PASS native 3/5-command batches survive plain/quoted selection as one complete action");
  f = fixture({filtered: true}); f.type("ordinary retained"); await f.quote();
  assert.equal(f.api.quoteDrafts.size, 0); assert.equal(f.sent.length, 0);
  await f.post.click(); assert.equal(f.sent.length, 1);
  assert.match(f.sent[0].line, /append plain/);
  console.log("PASS filtered quoted branch refuses preparation and retains ordinary Send");
  console.log("8 composer quote scenarios passed (source mocks only)");

  const paired = JSON.parse(fs.readFileSync(path.join(__dirname, "PAIRED-MENU-COPY.json"), "utf8"));
  const snapshot = paired.snapshot_for_isolated_consumer_test;
  f = fixture({compiledNode: paired.consumer, snapshot}); f.type("Keep existing words");
  const menu = paired.origin.acts.find(a => a.label === "Comment");
  const snap = {...paired.origin.paint.source, start: 5, end: 9, quoted: "same"};
  await f.api.prepareQuote(menu.line.slice(8), snap, paired.origin);
  assert.equal(f.sent.length, 0);
  assert.equal(f.input.value, "Keep existing words");
  assert.equal(f.api.quoteDrafts.get(f.n.key).context.destination.item, paired.fixture.talk_subject);
  assert.equal(f.api.quoteDrafts.get(f.n.key).context.item.item, paired.fixture.source_subject);
  assert.equal(f.captures(), 1);
  // Same mounted key after world viewer and To chips change. Actual compiler
  // artifacts, actual composer/prepare, mocked DOM/transport only.
  const repaint = paired.navigated_consumer;
  assert.equal(repaint.key, f.n.key);
  f.el._n = repaint;
  f.context.api.composer(f.el, repaint, repaint.acts.find(a => a.on === "edit"));
  const repaintedInput = f.el.children[1], repaintedPost = f.el.children[2].children[0];
  assert.equal(repaintedInput.value, "Keep existing words");
  assert.equal(f.api.quoteDrafts.size, 1);
  await repaintedPost.click();
  assert.equal(f.sent.length, 1);
  assert.ok(f.sent[0].line.startsWith("do append " + paired.fixture.talk_subject + " "));
  assert.ok(f.sent[0].line.includes('captures="' + paired.fixture.capture_ids + '"'));
  assert.ok(!f.sent[0].line.startsWith("do append " + paired.fixture.other_talk + " "));
  assert.equal(f.sent[0].attachment.quote.context.destination.item, paired.fixture.talk_subject);
  console.log("PASS exact canonical world menu prepares existing words/captures; same-key repaint/To change keeps captured Talk; one mocked dispatch");

  f = fixture({compiledNode: paired.consumer, snapshot}); f.type("Keep on removal");
  await f.api.prepareQuote(menu.line.slice(8), snap, paired.origin);
  f.remove.click(); await f.post.click();
  assert.equal(f.sent.length, 1);
  assert.equal(f.sent[0].line, paired.consumer.acts.find(a => a.on === "edit").line.replaceAll("$value", "Keep on removal"));
  assert.equal(f.sent[0].attachment, undefined);
  f = fixture({compiledNode: paired.consumer, snapshot}); f.type("Keep on stale");
  await f.api.prepareQuote(menu.line.slice(8), snap, paired.origin);
  f.stale(); await f.post.click();
  assert.equal(f.sent.length, 0); assert.equal(f.input.value, "Keep on stale");
  assert.equal(f.api.quoteDrafts.size, 1);
  console.log("PASS exact paired consumer Remove quote restores native plain action; stale refusal retains words/quote");
  console.log("2 exact compiled paired-menu scenarios passed (source mocks only)");
})().catch(e => { console.error(e); process.exitCode = 1; });
