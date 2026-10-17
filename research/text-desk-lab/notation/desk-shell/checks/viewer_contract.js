// checks/viewer_contract.js (a6067): viewer.js's draft contract (test_viewer.cjs, the codex team's, run here in a page
// because a worker may not run node) and the per-window store a6067 added (Sable c5977). One expression for screen.py's
// `js @<this file>`; test_textedit_paint.py runs it.
(async () => {
  const src = await (await fetch("viewer.js")).text(), out = [];
  let fails = 0;
  const check = (name, ok, detail = "") => { out.push((ok ? "ok   " : "FAIL ") + name + (ok ? "" : "\n     " + JSON.stringify(detail).slice(0, 600))); if (!ok) fails++; };
  const Store = (init = []) => { const m = new Map(init); return { m, getItem: k => m.has(k) ? m.get(k) : null, setItem: (k, v) => m.set(k, String(v)),
    removeItem: k => m.delete(k), key: i => [...m.keys()][i], get length() { return m.size; } }; };
  // as test_viewer.cjs: a localStorage with only getItem and setItem, no sessionStorage, no timers
  const make = (local, session) => new Function("localStorage", "sessionStorage", "Style", "setInterval", src + "\nreturn Viewer;")(
    local, session, { roleClass: n => n }, undefined)("test", "codex", "review", {}, {});
  const legacy = saved => { const m = new Map([["lens-drafts:test:codex:review", JSON.stringify(saved)]]);
    return make({ getItem: k => m.has(k) ? m.get(k) : null, setItem: (k, v) => m.set(k, v) }, undefined); };
  const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);
  const run = (name, f) => { try { f(); check(name, true); } catch (e) { check(name, false, String(e && e.stack || e)); } };
  const assert = { equal: (a, b) => { if (!eq(a, b)) throw new Error(`${JSON.stringify(a)} != ${JSON.stringify(b)}`); } };

  run("refused reply keeps its words and uses the refreshed view on an explicit retry", () => {
    const v = legacy([]), original = { key: "thread/reply", fence: { at: 1 } };
    v.typed(original.key, "My unsent words", original);
    const token = v.beginSend(original.key);
    v.answered(original.key, "definition changed", "My unsent words", token);
    assert.equal(v.editOrigin(original.key, original), null);
    assert.equal(v.words(original.key, "", { at: 2 }), "My unsent words");
    assert.equal(v.editOrigin(original.key, original).fence.at, 2);
    v.typed(original.key, "My unsent words, continued", { key: original.key, fence: { at: 3 } });
    assert.equal(v.editOrigin(original.key, original).fence.at, 2);
    assert.equal(v.drafts.get(original.key).text, "My unsent words, continued");
  });
  run("legacy unknown-origin text can be explicitly recovered without copying or sending it", () => {
    const v = legacy([["thread/reply", { text: "Keep this text" }]]);
    const current = { key: "thread/reply", fence: { at: 9 }, text: "" };
    assert.equal(v.words(current.key, "", current.fence), "Keep this text");
    assert.equal(v.editOrigin(current.key, current), null);
    assert.equal(v.useCurrent(current.key, current), true);
    assert.equal(v.drafts.get(current.key).text, "Keep this text");
    assert.equal(v.editOrigin(current.key, current).fence.at, 9);
    assert.equal(v.drafts.get(current.key).gesture, undefined);
  });
  run("recovery cannot replace an in-flight draft; successful send preserves later typing", () => {
    const v = legacy([]), n = { key: "thread/reply", fence: { at: 1 } };
    v.typed(n.key, "First", n);
    const token = v.beginSend(n.key);
    assert.equal(v.useCurrent(n.key, { ...n, fence: { at: 2 } }), false);
    v.typed(n.key, "Second", n);
    v.answered(n.key, null, "First", token);
    assert.equal(v.drafts.get(n.key).text, "Second");
    assert.equal(v.editOrigin(n.key, n).fence.at, 1);
  });
  run("a moved editor field keeps its draft but requires explicit origin recovery", () => {
    const v = legacy([]), old = "page/doc/a12/comments/c34/answer", current = "page/wrapper/doc/a12/comments/c34/answer";
    v.typed(old, "Unsent before the layout change", { key: old, fence: { item: "a12", at: 1 } });
    const node = { key: current, fence: { item: "a12", at: 2 }, acts: [{ on: "edit" }], kids: [] };
    v.recoverLayout({ key: "page", kids: [node] });
    assert.equal(v.drafts.has(old), false);
    assert.equal(v.drafts.get(current).text, "Unsent before the layout change");
    assert.equal(v.editOrigin(current, node), null);
    assert.equal(v.useCurrent(current, node), true);
    assert.equal(v.editOrigin(current, node).fence.at, 2);
  });
  run("layout recovery refuses ambiguous locations and never moves an in-flight send", () => {
    const v = legacy([]), old = "old/a12/c34/answer";
    v.typed(old, "Keep", { key: old, fence: { item: "a12" } });
    const n = key => ({ key, fence: { item: "a12" }, acts: [{ on: "edit" }], kids: [] });
    v.recoverLayout({ key: "root", kids: [n("one/a12/c34/answer"), n("two/a12/c34/answer")] });
    assert.equal(v.drafts.has(old), true);
    v.beginSend(old);
    v.recoverLayout({ key: "root", kids: [n("one/a12/c34/answer")] });
    assert.equal(v.drafts.has(old), true);
  });

  // a6067: the store is the window's
  {
    const local = Store(), s1 = Store(), s2 = Store();
    const a = make(local, s1), b = make(local, s2);
    a.typed("doc/a5/body", "A's words", { key: "doc/a5/body", fence: { at: 1 } }); a.textState("doc/a5/body", { sel: [3, 3] });
    b.typed("doc/a5/body", "B's words", { key: "doc/a5/body", fence: { at: 1 } }); b.textState("doc/a5/body", { sel: [9, 9] });
    check("two windows on one document keep their own drafts and carets", a.drafts.get("doc/a5/body").text === "A's words" && b.drafts.get("doc/a5/body").text === "B's words"
      && a.textState("doc/a5/body").sel[0] === 3 && b.textState("doc/a5/body").sel[0] === 9);
    const slots = [...local.m.keys()].filter(k => k.includes(":w:"));
    check("in two slots of the one store", slots.length === 2, slots);
    // a's window closes; a slot not heard from for 20 s is taken over by the next new window
    const ka = "lens-drafts:test:codex:review:w:" + a.window, va = JSON.parse(local.getItem(ka)); va.alive = Date.now() - 60000; local.setItem(ka, JSON.stringify(va));
    const c = make(local, Store());
    check("a new window takes over a closed window's words (they outlive the tab)", c.drafts.get("doc/a5/body") && c.drafts.get("doc/a5/body").text === "A's words" && !local.m.has(ka));
    check("but never a window that is still open", b.drafts.get("doc/a5/body").text === "B's words" && c.drafts.get("doc/a5/body").text !== "B's words");
    const again = make(local, s2);
    check("a window reloaded keeps its own slot", again.drafts.get("doc/a5/body").text === "B's words");
    const d = make(local, Store());
    d.drop("x"); check("an empty window leaves no slot behind", !local.m.has("lens-drafts:test:codex:review:w:" + d.window));
  }

  const passed = out.filter(l => l.startsWith("ok")).length;
  return out.filter(l => !l.startsWith("ok")).concat([fails ? `${passed} passed, ${fails} FAILED` : `all ${passed} passed`]).join("\n");
})()
