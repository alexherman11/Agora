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
  const make = (local, session, said = {}) => new Function("localStorage", "sessionStorage", "Style", "setInterval", src + "\nreturn Viewer;")(
    local, session, { roleClass: n => n }, undefined)("test", "codex", "review", said, {});
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

  // a6067 (Sable, a6067 c6106): the unsent words are the person's (one draft per field, the same in every window, kept
  // in step); the caret is the window's (its own, in its sessionStorage)
  {
    const K = "doc/a5/body", local = Store(), s1 = Store(), s2 = Store(), saidA = {}, saidB = {};
    const a = make(local, s1, saidA), b = make(local, s2, saidB);
    a.typed(K, "A's words", { key: K, fence: { at: 1 } }); a.textState(K, { sel: [3, 3] });
    b.textState(K, { sel: [9, 9] });
    check("each window keeps its own caret, in its own sessionStorage", a.textState(K).sel[0] === 3 && b.textState(K).sel[0] === 9 && ![...local.m.keys()].some(k => k.startsWith("lens-window")));
    check("the draft is the person's: one slot, the old one", local.getItem("lens-drafts:test:codex:review") && JSON.parse(local.getItem("lens-drafts:test:codex:review"))[0][1].text === "A's words");
    const c = make(local, Store());
    check("a window opened later shows the same unsent words (they outlive a closed tab)", c.drafts.get(K) && c.drafts.get(K).text === "A's words" && !c.textState(K));
    // kept in step: another window's change arrives as a storage event (every viewer made here hears this page's
    // events): b never typed here, so it takes the words and is told which field; a typed its own, so it keeps them
    let told = null; b.onDrafts(keys => { told = keys; });
    const next = JSON.stringify([[K, { text: "C's words", why: "typed here, not sent", seen: { key: K, fence: { at: 1 } } }]]);
    local.setItem("lens-drafts:test:codex:review", next);
    window.dispatchEvent(new StorageEvent("storage", { key: "lens-drafts:test:codex:review", newValue: next }));
    check("another window's words reach a window that did not type there, and it is told which field", b.drafts.get(K).text === "C's words" && JSON.stringify(told) === JSON.stringify([K]), told);
    check("a window that typed its own words there keeps them, and says another window is typing too",
      a.drafts.get(K).text === "A's words" && /another of your windows/.test(saidA.textContent || "") && !/another of your windows/.test(saidB.textContent || ""), [a.drafts.get(K).text, saidA.textContent]);
  }

  // a6067 (Codex c6203, Sable c6206): two windows on one shared store; a storage event reaches a window only when this
  // test delivers it (a browser sends it to the OTHER windows, a moment later). A send clears the shared draft only if
  // it still holds exactly the words sent.
  {
    const KEY = "lens-drafts:test:codex:review", K = "chat/say", K2 = "doc/a9/body", o = { key: K, fence: { at: 1 } };
    const pair = () => {
      const local = Store();
      const mk = () => {
        let h = null; const said = {};
        const v = new Function("localStorage", "sessionStorage", "Style", "setInterval", "addEventListener", src + "\nreturn Viewer;")(
          local, Store(), { roleClass: n => n }, undefined, (t, f) => { if (t === "storage") h = f; })("test", "codex", "review", said, {});
        v.deliver = () => h && h({ key: KEY, newValue: local.getItem(KEY) }); v.said = said; return v;
      };
      return [mk(), mk(), local];
    };
    const stored = (local, k) => { const d = (JSON.parse(local.getItem(KEY) || "[]")).find(e => e[0] === k); return d ? d[1].text : null; };
    const words = (v, k) => v.drafts.get(k) ? v.drafts.get(k).text : null;
    { // Codex's exact sequence
      const [A, B, L] = pair();
      A.typed(K, "First message", o); B.deliver();
      const tok = A.beginSend(K);
      B.typed(K, "New unsent words in B", o); A.deliver();
      A.answered(K, null, "First message", tok); B.deliver();
      check("Codex's sequence: A's sent answer does not erase B's newer words (A, B and the store all keep them)",
        words(A, K) === "New unsent words in B" && words(B, K) === "New unsent words in B" && stored(L, K) === "New unsent words in B", [words(A, K), words(B, K), stored(L, K)]);
      check("and the sending window says 'sent; newer words kept'", /sent; newer words kept/.test(A.said.textContent || ""), A.said.textContent);
    }
    { // the same, with B's storage event not yet delivered to A when A's answer comes
      const [A, B, L] = pair();
      A.typed(K, "First message", o); B.deliver();
      const tok = A.beginSend(K);
      B.typed(K, "New unsent words in B", o);
      A.answered(K, null, "First message", tok); B.deliver();
      check("answer before the other window's event arrives: B's words still kept (the store held newer words than A cleared)",
        words(A, K) === "New unsent words in B" && words(B, K) === "New unsent words in B" && stored(L, K) === "New unsent words in B", [words(A, K), words(B, K), stored(L, K)]);
    }
    for (const [name, err] of [["a refusal", "refused: k changed since this was painted"], ["a lost answer", "the answer was lost (net); whether it was done is unknown until the view repaints"]]) {
      const [A, B, L] = pair();
      A.typed(K, "First message", o); B.deliver();
      const tok = A.beginSend(K);
      B.typed(K, "New unsent words in B", o); A.deliver();
      A.answered(K, err, "First message", tok); B.deliver();
      check(`${name}: B's newer words are kept everywhere`, words(A, K) === "New unsent words in B" && words(B, K) === "New unsent words in B" && stored(L, K) === "New unsent words in B", [words(A, K), words(B, K), stored(L, K)]);
    }
    { // a send's publishing never touches an unrelated field another window changed
      const [A, B, L] = pair();
      A.typed(K, "First message", o); B.deliver();
      const tok = A.beginSend(K);
      B.typed(K2, "B's other field", { key: K2, fence: { at: 1 } });
      A.answered(K, null, "First message", tok); B.deliver();
      check("an unrelated field typed in B survives A's send being answered", stored(L, K2) === "B's other field" && words(B, K2) === "B's other field" && words(A, K2) === "B's other field" && stored(L, K) === null, [stored(L, K2), words(A, K2), stored(L, K)]);
    }
    // Codex c6224, Jeff c6229: newer words typed in the SAME window while a send is out, with caret state stored (as
    // every module text has), survive the send's success and a refusal; and a send that began with no draft
    for (const [name, err] of [["success", null], ["refusal", "refused: k changed since this was painted"], ["lost answer", "the answer was lost (net)"]]) {
      const [A, , L] = pair();
      A.typed(K, "First message", o); A.textState(K, { sel: [3, 3] });
      const tok = A.beginSend(K);
      A.typed(K, "Later typing in A", o);
      A.answered(K, err, "First message", tok);
      check(`one window, ${name}: words typed while the send was out survive (in the window and the store)`,
        words(A, K) === "Later typing in A" && stored(L, K) === "Later typing in A", [words(A, K), stored(L, K)]);
    }
    {
      const [A, B, L] = pair();
      A.textState(K, { sel: [0, 0] });
      const tok = A.beginSend(K);                     // a press with no draft (nothing typed when it was sent)
      A.typed(K, "Typed meanwhile", o); B.deliver();
      A.answered(K, null, undefined, tok); B.deliver();
      check("a send that began with no draft never clears words typed while it was out", words(A, K) === "Typed meanwhile" && stored(L, K) === "Typed meanwhile" && words(B, K) === "Typed meanwhile", [words(A, K), stored(L, K)]);
    }
    {
      const [A, B, L] = pair();
      A.typed(K, "First message", o); A.textState(K, { sel: [3, 3] }); B.deliver();
      const tok = A.beginSend(K);
      A.typed(K, "First message, and more", o); B.deliver();
      A.answered(K, null, "First message", tok); B.deliver();
      check("two windows, newer words typed in the sending window: kept in both windows and the store", words(A, K) === "First message, and more" && words(B, K) === "First message, and more" && stored(L, K) === "First message, and more", [words(A, K), words(B, K), stored(L, K)]);
    }
    {
      const [A, B, L] = pair();
      A.typed(K, "Sent words", o); A.textState(K, { sel: [3, 3] }); B.deliver();
      const tok = A.beginSend(K);
      A.rebased(K, "Sent words", { key: K, fence: { at: 2 } }, "base");      // the same words re-fenced: still the words sent
      A.answered(K, null, "Sent words", tok); B.deliver();
      check("the words sent, only re-fenced meanwhile, are cleared (equality by words, not by object)", words(A, K) === null && stored(L, K) === null && words(B, K) === null, [words(A, K), stored(L, K)]);
    }
    { // a plain send with nothing newer clears the draft everywhere
      const [A, B, L] = pair();
      A.typed(K, "Only this", o); B.deliver();
      const tok = A.beginSend(K); A.answered(K, null, "Only this", tok); B.deliver();
      check("a send with nothing newer clears the shared draft in every window", words(A, K) === null && words(B, K) === null && stored(L, K) === null, [words(A, K), words(B, K), stored(L, K)]);
    }
    { // both windows typing in one field: each keeps its own words, both say so; a later send keeps the other's
      const [A, B, L] = pair();
      A.typed(K, "A's words", o); B.typed(K, "B's words", o); A.deliver(); A.typed(K, "A's words, more", o); B.deliver();
      check("typed in one field in two windows at once: each keeps its own words", words(A, K) === "A's words, more" && words(B, K) === "B's words", [words(A, K), words(B, K)]);
      check("and both say so", /another of your windows/.test(A.said.textContent || "") && /another of your windows/.test(B.said.textContent || ""), [A.said.textContent, B.said.textContent]);
      const tok = A.beginSend(K); A.answered(K, null, "A's words, more", tok); B.deliver();
      check("A sends its words: B's competing words are kept, in B and in the store", words(B, K) === "B's words" && stored(L, K) === "B's words", [words(B, K), stored(L, K)]);
    }
  }

  const passed = out.filter(l => l.startsWith("ok")).length;
  return out.filter(l => !l.startsWith("ok")).concat([fails ? `${passed} passed, ${fails} FAILED` : `all ${passed} passed`]).join("\n");
})()
