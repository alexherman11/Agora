// Execute the actual painter functions with controlled style/geometry doubles.
// This proves admission/order invariants, not browser layout cost or pixels.
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const source = fs.readFileSync(path.join(__dirname,
  "../../text-desk-lab/notation/desk-shell/lens.js"), "utf8");
const between = (a, b) => {
  const start = source.indexOf(a), end = source.indexOf(b, start);
  assert.ok(start >= 0 && end > start, "actual painter function boundaries");
  return source.slice(start, end);
};
let checks = 0;
function check(fn) { fn(); checks++; }

async function admission() {
  let release, rejectStyle, paints = 0, recoveries = 0;
  let style = new Promise((resolve, reject) => { release = resolve; rejectStyle = reject; });
  const scene = { def: { style_name: "test", style_rev: "2" } };
  const prior = { gen: "old", scene: {} };
  const c = vm.createContext({
    resizing: false, last: "old", sceneAt: 1, def: { old: true }, held: prior,
    restyle: () => style,
    V: { recoverLayout: () => recoveries++, keep: fn => fn(), show: () => {} },
    glideRects: () => null, make: () => { paints++; return {}; }, next: null, kept: null,
    paint: { firstChild: null, replaceChildren() {} },
    dividers: { sync() {} }, partitions: { sync() {} },
    settle() {}, glideFrom() {}, followEnds() {}, placeMenuDrafts() {}, report() {}
  });
  vm.runInContext(between("  async function paintAnswer(", "  // a5504"), c);
  const answer = { gen: "new", events_total: 2, scene };
  const waiting = c.paintAnswer(answer, false);
  c.resizing = true;
  release();
  await waiting;
  check(() => assert.equal(paints, 0, "style wait cannot cross a new geometry hold"));
  check(() => assert.equal(recoveries, 0, "held scene cannot remap drafts"));
  check(() => assert.equal(c.last, "old", "unpainted answer is not acknowledged"));
  check(() => assert.equal(c.held, prior, "reload retains actually painted answer"));
  check(() => assert.equal(c.sceneAt, 1, "reported event remains painted event"));
  check(() => assert.equal(c.def.old, true, "held definition remains authoritative"));

  c.resizing = false;
  await c.paintAnswer(answer, false);
  check(() => assert.equal(paints, 1, "next ordinary refresh can converge after release"));
  check(() => assert.equal(c.last, "new"));
  check(() => assert.equal(c.held, answer));
  await c.paintAnswer(answer, false);
  check(() => assert.equal(paints, 1, "same generation still skips work"));
  await c.paintAnswer(answer, true);
  check(() => assert.equal(paints, 2, "forced fenced refresh is not dropped"));

  style = new Promise((resolve, reject) => { rejectStyle = reject; });
  const failed = c.paintAnswer({ ...answer, gen: "later" }, false);
  rejectStyle(new Error("style fixture"));
  await assert.rejects(failed, /style fixture/);
  check(() => assert.equal(c.last, "new", "failed style does not acknowledge unseen scene"));
  check(() => assert.equal(paints, 2));
  c.resizing = true;
  await c.paintAnswer({ ...answer, gen: "held" }, true);
  check(() => assert.equal(c.last, "new", "entry hold still refuses even forced paint"));
}

function overflow() {
  const reads = [], writes = [];
  const make = (name, height, client, head = 0, clamp = true) => {
    const e = {
      classList: { contains: () => clamp },
      get scrollHeight() { reads.push({ name, afterWrite: writes.length }); return height; },
      get clientHeight() { reads.push({ name, afterWrite: writes.length }); return client; },
      dataset: new Proxy({ atEnd: head ? "1" : "" }, {
        set(o, k, v) { writes.push([name, k, v]); o[k] = v; return true; }
      }),
      getBoundingClientRect() { reads.push({ name, afterWrite: writes.length }); return { top: head }; },
      firstElementChild: { getBoundingClientRect() { return { top: 0 }; } }
    };
    return e;
  };
  const clamps = [make("clamp", 102, 100), make("exact", 101, 100), make("plain", 200, 100, 0, false)];
  const frames = [make("tail", 109, 100), make("hair", 108, 100), make("head", 100, 100, 9)];
  const c = vm.createContext({
    Style: { afloat: [] }, watchedFloats: new Set(),
    paint: { querySelectorAll: s => s === "[data-clamped]" ? clamps
      : s === '[data-scroll="none"]' ? frames : [] }
  });
  vm.runInContext(between("  function settle() {", "  // `tip`"), c);
  c.settle();
  check(() => assert.deepEqual(clamps.map(e => e.dataset.cut), ["1", "", ""]));
  check(() => assert.deepEqual(frames.map(e => e.dataset.cut), ["1", "", "1"]));
  check(() => assert.ok(reads.every(r => r.afterWrite === 0),
    "overflow geometry reads precede all cut-attribute writes"));
  check(() => assert.equal(writes.length, 6, "every overflow indicator still updates"));
}

(async () => {
  await admission();
  overflow();
  console.log(`repaint races: ${checks} assertions passed (controlled doubles; no browser timing proof)`);
})().catch(error => { console.error(error); process.exitCode = 1; });
