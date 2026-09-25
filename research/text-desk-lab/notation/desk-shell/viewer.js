// viewer.js : the viewer half of paint(scene, viewer). OWNER: Pike (pike-7 section 1).
// The scene is the same for everyone; the viewer is one person at one window: the part in hand, drafts typed and
// refused, the refusal on screen, focus, caret and selection. It is never the world and never history. Continuity
// is counted apart from vocabulary (a361, Jeff): this file holds the continuity rules, lens.js holds the paint kinds.
//   1. an element lives as long as its key            (lens.js: keyed reuse)
//   2. it changes only when its paint changes          (lens.js: the signature is paint, act shapes and kid keys)
//   3. the part in hand is drawn from the scene it was taken from until it is put down   (hold)
//   4. viewer marks are drawn in honesty roles, never silently   (mark: unsent, refused)
const Viewer = (session, who, lens, said) => {
  // Juniper c347 (7): typed words outlive a closed tab. localStorage stands in for the viewer store: this browser only,
  // one slot per session, viewer and lens (two windows of one viewer share it; the last writer wins).
  const store = `lens-drafts:${session}:${who}:${lens}`;
  let drafts;
  try { drafts = new Map(JSON.parse(localStorage.getItem(store)) || []); } catch { drafts = new Map(); }
  let notice = drafts.size ? `unsent: ${drafts.size} draft(s) kept from before, marked where they were typed (Enter sends, Escape drops)` : "";
  let text = "", told = "";
  const v = {
    drafts, hold: null, repainting: false,
    // Pike (run 1): a refusal was written and then overwritten by the repaint (6 of 7 unseen). It stays until the next gesture.
    show(t) {
      if (t !== undefined) text = t;
      said.textContent = (notice ? notice + "\n\n" : "") + text;
      try { localStorage.setItem(store, JSON.stringify([...drafts])); } catch {}
    },
    answered(key, err, draft) {
      v.hold = null;
      if (err) {
        notice = (draft !== undefined ? `unsent: "${draft}" (Enter sends it again, Escape drops it)\n` : "") + "refused: " + err;
        if (draft !== undefined) drafts.set(key, { text: draft, why: err.split("\n").pop() });   // the repaint marks it
      } else { notice = ""; drafts.delete(key); }
      v.show();
    },
    drop(key) { drafts.delete(key); notice = ""; v.show(); },
    // a kept draft remembers what it was typed against, so sending it after a reload is fenced on that, not on today's paint
    typed(key, words, fence) {
      const seen = (drafts.get(key) || {}).seen || fence;
      drafts.set(key, { text: words, why: "typed here, not sent", seen }); v.show();
    },
    words(key, now) { const d = drafts.get(key); if (d && d.text === now) drafts.delete(key); return drafts.has(key) ? d.text : now; },
    mark(el, key) {
      const d = drafts.get(key);
      el.classList.toggle(Style.roleClass("mark"), !!d);
      if (d) el.dataset.unsent = d.why; else delete el.dataset.unsent;
    },
    // rules 1 and 2 (Iris, Astra): keep an element whose paint did not change, placing only the kids that differ;
    // re-inserting an untouched sibling would drop the reader's selection inside it. A part with its own words
    // cannot have its children swapped without losing the words (until the frame/leaf split, pike-7 section 4).
    reuse(el, els, words) {
      const same = els.length === el.children.length && els.every((e, i) => el.children[i] === e);
      if (!same && words) return false;
      // Pike (S20): remove the leavers first. Placing first moved a kept sibling past a replaced one, and a moved element
      // loses the pointer capture of a card being carried inside it (and a selection inside it).
      const want = new Set(els);
      [...el.children].forEach(c => { if (!want.has(c)) c.remove(); });
      els.forEach((e, i) => { if (el.children[i] !== e) el.insertBefore(e, el.children[i] || null); });
      return true;
    },
    // Iris, Lark: only the painter knows what happened on this screen. It says so, as a viewer fact (~), never the world.
    // Sable c480: attention is private until the person publishes it. Paint facts (a clamp cut, a box overflowing) are
    // about the lens and always go; attention facts (viewport, out of view, unsent drafts, the thing carried) go only when
    // the person allows it, for now by share=attention in the page's address, until there is a control they can see.
    report(paint, at, extra, attention) {
      const vp = paint.getBoundingClientRect(), facts = attention ? { ...extra } : {};
      for (const el of paint.querySelectorAll("[data-key]")) {
        const r = el.getBoundingClientRect(), f = [];
        if (el.classList.contains("clamp") && el.scrollHeight > el.clientHeight + 1) f.push("cut by the clamp");
        if (el.classList.contains("boxed") && el.scrollHeight > el.clientHeight + 1) f.push("contents overflow the box");
        if (attention && el.classList.contains("boxed") && (r.bottom < vp.top || r.top > vp.bottom || r.right < vp.left || r.left > vp.right)) f.push("out of view");
        if (attention && el.dataset.unsent) f.push("unsent draft");
        if (f.length) facts[el.dataset.key] = f.join(", ");
      }
      const view = attention ? { viewport: { w: Math.round(vp.width), h: Math.round(vp.height), sx: Math.round(paint.scrollLeft), sy: Math.round(paint.scrollTop) } } : {};
      const body = JSON.stringify({ session, as: who, lens, at, facts, ...view });
      if (body !== told) { told = body; fetch("/api/observe", { method: "POST", body }); }
    },
    // Pike (run 1, Alex's workspace): everything repaints but the part in hand; focus, caret and selection are put back
    keep(draw) {
      const ed = document.activeElement, s = getSelection(), sel = s.rangeCount ? [s.anchorNode, s.anchorOffset, s.focusNode, s.focusOffset] : null;
      v.repainting = true;
      try {
        draw();
        if (ed && ed !== document.body && ed.isConnected && document.activeElement !== ed) ed.focus();
        const moved = sel && (s.anchorNode !== sel[0] || s.anchorOffset !== sel[1] || s.focusNode !== sel[2] || s.focusOffset !== sel[3]);
        if (moved && sel[0].isConnected && sel[2].isConnected) s.setBaseAndExtent(...sel);   // only if the repaint moved it
      } finally { v.repainting = false; }
    },
  };
  return v;
};
