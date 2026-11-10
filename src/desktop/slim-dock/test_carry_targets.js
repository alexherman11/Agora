// DOM stand-ins and real transport plans. No browser or host.
const assert = require("node:assert/strict");
const T = require("../../text-desk/notation/desk-shell/carry-targets.js");
let checks = 0;
function check(value) { assert.ok(value); checks++; }
function receiver(key, acts, contains = false) {
  return { dataset: { drop: acts.at(-1).part, key }, _drops: acts,
    _n: { fence: { item: key, rev: 3 } }, contains: () => contains,
    getBoundingClientRect: () => ({ left: 10, top: 100, width: 120, height: 36 }) };
}
async function main() {
  const dock = receiver("dock", [{ part: "any", line: "do pin $carried" }]);
  const named = receiver("pin", [{ part: "app", line: "do reorder $carried" }]);
  const paint = { querySelectorAll: () => [dock, named] };
  const source = { el: {}, part: "grip" }, point = { clientX: 30, clientY: 116 };
  const seen = T.snapshot(paint, source.part);
  check(seen.size === 1);
  const p = T.plan(dock, source, seen, point);
  assert.deepEqual(p.box, [10, 100, 120, 36]); checks++;
  dock._n.fence = { item: "dock", rev: 99 };
  dock._drops = [{ part: "any", line: "do different" }];
  const held = T.plan(dock, source, seen, point);
  check(held.fence.rev === 3 && held.act.line === "do pin $carried");
  const added = receiver("late", [{ part: "any", line: "do surprise" }]);
  check(T.plan(added, source, seen, point) === null);
  check(T.at([named, dock], source, seen, point).receiver === dock);
  const src = { item: "panel", rev: 7 };
  let sent;
  await T.submit((...args) => { sent = args; }, held, src);
  check(sent[0].fence.rev === 3 && sent[3].carried === src && sent[3].receiver === held.fence);
  check(sent[1] === held.act.line);
  const own = receiver("own", [{ part: "any", line: "do self" }], true);
  check(T.plan(own, source, T.snapshot({ querySelectorAll: () => [own] }, "grip"), point) === null);
  const multi = receiver("multi", [{ part: "app", line: "reorder" }, { part: "any", line: "pin" }]);
  const multiSeen = T.snapshot({ querySelectorAll: () => [multi] }, "app");
  check(T.plan(multi, { el: {}, part: "app" }, multiSeen, point).act.line === "reorder");
  let boxes = [], hits = [dock], calls = 0;
  const doc = { elementsFromPoint: () => hits,
    body: { appendChild: b => boxes.push(b) },
    createElement: () => ({ style: {}, remove() { boxes = boxes.filter(b => b !== this); } }) };
  const s = T.session(paint, { el: {}, n: { part: "appgrip", fence: src } },
    (...args) => { calls++; check(args[3].carried === src); }, null, doc);
  check(s.move(point) !== null && boxes.length === 1);
  check(boxes[0].style.height === "36px" && boxes[0].style.transition === "none");
  hits = []; check(s.move(point) === null && boxes.length === 0);
  hits = [dock]; s.move(point); await s.release();
  check(calls === 1 && boxes.length === 0);
  const cancelled = T.session(paint, { el: {}, n: { part: "grip", fence: src } },
    () => { calls++; }, null, doc);
  cancelled.move(point); cancelled.cancel(); await cancelled.release();
  check(calls === 1 && boxes.length === 0);
  const excluded = T.session(paint, { el: {}, n: { part: "grip", fence: src } },
    () => {}, { contains: () => true }, doc);
  check(excluded.move(point) === null);
  console.log(`${checks} carry target checks passed (DOM stand-ins; no browser)`);
}
main().catch(e => { console.error(e); process.exitCode = 1; });
