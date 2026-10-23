// Actual sender + Viewer; mocked door/storage only. No browser or live send.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const base = path.join(__dirname, "../../text-desk-lab/notation/desk-shell");
const lens = fs.readFileSync(path.join(base, "lens.js"), "utf8");
const sender = lens.slice(lens.indexOf("  async function send(n,"), lens.indexOf("  let imageCommentsBusy"));
function fixture(replies) {
  const storage = () => {const m = new Map(); return {getItem: k => m.get(k), setItem: (k,v) => m.set(k,v)};};
  const requests = [];
  const c = {console, Map, Set, JSON, Date, Math,
    localStorage: storage(), sessionStorage: storage(), window: {},
    document: {}, setTimeout: () => 1, clearTimeout() {},
    session: "mock", who: "fixture", lens: "fixture", said: {},
    kept: new Map(), paint: {querySelectorAll: () => []}, sceneAt: 1, def: null, last: "",
    refresh: async () => undefined,
    fetch: async (url, opts) => {
      assert.equal(url, "/api/do"); requests.push(JSON.parse(opts.body));
      const r = replies.shift();
      if (r instanceof Error) throw r;
      return {json: async () => r};
    }};
  vm.createContext(c);
  vm.runInContext(fs.readFileSync(path.join(base, "viewer.js"), "utf8") +
    '\nglobalThis.V=Viewer(session,who,lens,said,null);' + sender +
    '\nglobalThis.send=send;', c);
  return {c, requests};
}
(async () => {
  for (const first of [{text: "appended\nERR cleanup refused", error: "ERR cleanup refused"},
                        new Error("lost answer after commit")]) {
    const {c, requests} = fixture([first, {text: "already done (gesture receipt)"}]);
    const n = {key: "one/composer", fence: {}, paint: {text: ""}};
    c.V.typed(n.key, "words", n);
    const batch = 'do append disposable line="words"; read draft; do prop draft topic=""';
    await c.send(n, batch, "words");
    assert.equal(c.V.drafts.get(n.key).text, "words");
    assert.equal(c.V.drafts.get(n.key).refused, true);
    assert.equal(c.V.busy(n.key), false);
    const gid = c.V.drafts.get(n.key).gesture;
    assert.equal(gid, requests[0].gesture);
    await c.send(n, batch, "words");
    assert.equal(requests.length, 2);
    assert.equal(requests[1].gesture, gid);
    assert.equal(requests[0].line, batch);
    assert.equal(requests[1].line, batch);
    assert.equal(c.V.drafts.size, 0);
    console.log("PASS " + (first instanceof Error ? "lost answer" : "partial batch") +
      " retains draft/id; same-id dedup receipt clears draft without cleanup recovery");
  }
  console.log("2 sender receipt scenarios passed (actual sender/Viewer, mocked door)");
})().catch(e => {console.error(e); process.exitCode = 1;});
