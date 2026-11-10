const assert = require("node:assert/strict");
const {allocation, pair, samePart} = require("../../text-desk/notation/desk-shell/dividers.js");
let checks = 0;
function near(a, b) { assert.ok(Math.abs(a - b) < .01, `${a} != ${b}`); checks++; }
// Both axes have the same bounded geometry. Sizes include border/padding.
for (const space of [2300, 1200, 900, 500, 180, 0]) {
  const minima = [240, 240, 240], weights = [1, 2, 1];
  const fit = allocation(space, minima, weights);
  near(fit.sizes.reduce((a,b) => a+b, 0), space);
  fit.sizes.forEach((s,i) => { assert.ok(s >= fit.bases[i]); checks++; });
  for (const delta of [-10000, -90, 90, 10000]) {
    const [a,b] = pair(fit.sizes[0], fit.sizes[1], fit.bases[0], fit.bases[1], 1, 2, delta);
    near(a+b, 3); assert.ok(a>0 && b>0); checks++;
    const after = allocation(space, minima, [a,b,1]);
    near(after.sizes[2], fit.sizes[2]);
    near(after.sizes[0] + after.sizes[1], fit.sizes[0] + fit.sizes[1]);
    assert.ok(after.sizes[0] >= after.bases[0] && after.sizes[1] >= after.bases[1]); checks++;
    if (space > 720 && Math.abs(delta) === 90) {
      const clamped = Math.max(fit.bases[0], Math.min(fit.sizes[0]+fit.sizes[1]-fit.bases[1], fit.sizes[0]+delta));
      near(after.sizes[0], clamped);
    }
  }
}
const initial = allocation(1100, [140,140], [1,1]);
const saved = pair(...initial.sizes, 140,140,1,1,100);
near(allocation(1100,[140,140],saved).sizes[0], initial.sizes[0]+100);
near(allocation(700,[140,140],saved).sizes.reduce((a,b)=>a+b),700);
assert.ok(samePart({path:"col",hash:"a",lens:"x"},{path:"col",hash:"a",lens:"x"})); checks++;
assert.ok(!samePart({path:"col",hash:"a"},{path:"col",hash:"b"})); checks++;
assert.ok(!samePart(null,{})); checks++;
console.log(`${checks} divider geometry checks passed`);
