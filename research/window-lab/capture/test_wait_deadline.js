// Deterministic execution of the actual painter helper. No DOM/browser/host.
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const source = fs.readFileSync(path.join(__dirname, "../../text-desk-lab/notation/desk-shell/lens.js"), "utf8");
const start = source.indexOf("  async function waitUntilClear(");
const end = source.indexOf("\n  function composer(", start);
assert(start >= 0 && end > start);

function clock() {
  let now = 0, serial = 0;
  const timers = new Map();
  const context = vm.createContext({
    WAIT_MS: 6000,
    setTimeout(fn, ms) { const id = ++serial; timers.set(id, {at: now + ms, fn}); return id; },
    clearTimeout(id) { timers.delete(id); }
  });
  const wait = vm.runInContext(source.slice(start, end) + "\nwaitUntilClear", context);
  const flush = async () => { for (let i = 0; i < 20; ++i) await Promise.resolve(); };
  return {wait, timers, flush, async tick(ms) {
    now += ms;
    for (const [id, timer] of [...timers]) if (timer.at <= now && timers.delete(id)) timer.fn();
    await flush();
  }};
}

(async () => {
  let c = clock(), calls = 0;
  assert.equal(await c.wait(() => false, () => { ++calls; }), true);
  assert.equal(calls, 0); assert.equal(c.timers.size, 0);

  c = clock(); let pending = true;
  let result = c.wait(() => pending, async () => { ++calls; pending = false; });
  await c.tick(250);
  assert.equal(await result, true); assert.equal(calls, 1); assert.equal(c.timers.size, 0);

  c = clock(); let finish;
  result = c.wait(() => true, () => new Promise(resolve => { finish = resolve; }));
  await c.tick(250); await c.tick(5750);
  assert.equal(await result, false); assert.equal(c.timers.size, 0);
  finish(); await c.flush();
  assert.equal(c.timers.size, 0); // a late shared refresh cannot resume the loop

  c = clock();
  result = c.wait(() => true, async () => { throw new Error("fixture refresh refused"); });
  const rejected = assert.rejects(result, /fixture refresh refused/);
  await c.tick(250); await rejected;
  assert.equal(c.timers.size, 0);

  c = clock();
  result = c.wait(() => true, () => { throw new Error("must not update after deadline"); }, 100);
  await c.tick(100);
  assert.equal(await result, false); assert.equal(c.timers.size, 0);
  console.log("5 painter wait/deadline cases passed (fake clock; no browser)");
})().catch(error => { console.error(error); process.exitCode = 1; });
