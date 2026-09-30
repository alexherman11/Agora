// viewer.js : the viewer half of paint(scene, viewer). OWNER: Pike (pike-7 section 1).
// The scene is the same for everyone; the viewer is one person at one window: the part in hand, drafts typed and
// refused, the refusal on screen, focus, caret and selection. It is never the world and never history. Continuity
// is counted apart from vocabulary (a361, Jeff): this file holds the continuity rules, lens.js holds the paint kinds.
//   1. an element lives as long as its key            (lens.js: keyed reuse)
//   2. it changes only when its paint changes          (lens.js: the signature is paint, act shapes and kid keys)
//   3. the part in hand is drawn from the scene it was taken from until it is put down   (hold)
//   4. viewer marks are drawn in honesty roles, never silently   (mark: unsent, refused)
const Viewer = (session, who, lens, said, status) => {
  // Juniper c347 (7): typed words outlive a closed tab. localStorage stands in for the viewer store: this browser only,
  // one slot per session, viewer and lens (two windows of one viewer share it; the last writer wins).
  const store = `lens-drafts:${session}:${who}:${lens}`;
  let drafts;
  try { drafts = new Map(JSON.parse(localStorage.getItem(store)) || []); } catch { drafts = new Map(); }
  // codex team (pike-8 section 2): a saved draft with no record of what it was typed against is never sent against
  // today's paint. It stays, marked; the person copies it, drops it (Escape) and starts from the current text.
  const unknownOrigin = "origin unknown: this kept draft has no record of what it was typed against; copy it if you need it, then Escape and start from the current text";
  for (const d of drafts.values()) if (!d.seen && !d.shown) d.why = unknownOrigin;
  let notice = drafts.size ? `unsent: ${drafts.size} draft(s) kept from before, marked where they were typed (Enter sends, Escape drops)` : "";
  let text = "", told = "";
  const foldStore = `lens-folds:${session}:${who}:${lens}`;
  let folds; try { folds = JSON.parse(localStorage.getItem(foldStore)) || {}; } catch { folds = {}; }
  const pending = new Map();      // key -> the draft generation in flight (codex team: a request in flight is viewer state)
  const refusal = why => (/^refused/.test(why) ? "" : "refused: ") + why;      // deskd's own sentences already begin so
  const both = (key, d) => `${refusal(d.why)}\nunsent, yours: "${d.text}"\nnow in the world: "${d.shown.text}"\nEnter sends yours over what is now there; Escape keeps it and drops yours`;
  const v = {
    drafts, hold: null, repainting: false,
    // Pike (run 1): a refusal was written and then overwritten by the repaint (6 of 7 unseen). It stays until the next
    // gesture, in the inspector and in a live status region a screen reader announces (codex team, pike-8 section 2).
    show(t) {
      if (t !== undefined) text = t;
      said.textContent = (notice ? notice + "\n\n" : "") + text;
      if (status) { status.textContent = notice; status.hidden = !notice; }
      try { localStorage.setItem(store, JSON.stringify([...drafts])); } catch {}
    },
    // one send per key at a time; the token is the draft generation that was submitted
    beginSend(key) {
      if (pending.has(key)) return null;
      const token = { draft: drafts.get(key) };
      pending.set(key, token); return token;
    },
    // a1008: one intent, one event. A gesture's id is minted at the press and lives on its draft (kept with it, over
    // repaints and reloads) until the draft is answered or its words change (typed makes a new draft), so a retry of
    // the same words resends the same id and deskd acts at most once. A press with no draft (a click) is its own id.
    gesture(key, drafted) {
      const d = drafted ? drafts.get(key) : null;
      const id = (d && d.gesture) || `${who}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
      if (d && !d.gesture) { d.gesture = id; v.show(); }
      return id;
    },
    // Only the submitted generation is cleared or annotated: typing that arrived while the request was in flight stays,
    // with its own fence. A lost response says so; it claims neither success nor refusal.
    answered(key, err, draft, token) {
      if (token && pending.get(key) !== token) return;
      pending.delete(key);
      const cur = drafts.get(key), newer = token && token.draft !== undefined && cur !== token.draft;
      if (!newer) v.hold = null;
      if (err) {
        notice = refusal(err);
        // pike-8 section 3: a refused draft is kept, and the world's current value will be drawn beside it (both sides);
        // a resend is fenced on the value shown, never on a fresher one the person has not seen
        if (draft !== undefined && !newer) drafts.set(key, { text: draft, why: err.split("\n").pop(), refused: true, shown: null, gesture: token && token.draft && token.draft.gesture });
      } else if (newer) notice = "sent the earlier words; what you typed since is still unsent";
      else { notice = ""; drafts.delete(key); }
      v.show();
    },
    drop(key) {
      if (pending.has(key)) { notice = "a send is in flight; wait for its answer before dropping this draft"; v.show(); return false; }
      drafts.delete(key); notice = ""; v.show(); return true;
    },
    // a kept draft remembers what it was typed against, so sending it after a reload is fenced on that, not on today's paint
    typed(key, words, fence) {
      const d = drafts.get(key), seen = d ? (d.shown || d.seen) : fence;
      drafts.set(key, { text: words, why: seen ? "typed here, not sent" : unknownOrigin, seen }); v.show();
    },
    // the fence a draft is sent on: what it was typed against, or the value shown beside a refused draft; null means
    // nothing is sent (a refused draft whose world side has not been drawn yet, or an origin-unknown draft)
    editOrigin(key, current) {
      const d = drafts.get(key);
      if (!d) return current;
      if (d.refused) return d.shown;
      if (d.seen) return d.seen;
      d.why = unknownOrigin; notice = unknownOrigin; v.hold = null; v.show(); return null;
    },
    // what a text leaf shows: the draft if there is one; a refused draft records the world's value drawn beside it
    words(key, now, fence) {
      const d = drafts.get(key);
      if (!d) return now;
      if (!pending.has(key) && d.text === now) {      // the world already says what was typed (a lost answer that was done)
        drafts.delete(key); if (d.refused) { notice = ""; v.show(); } return now;
      }
      if (d.refused && (!d.shown || d.shown.text !== now)) { d.shown = { key, fence, text: now }; notice = both(key, d); v.show(); }
      return d.text;
    },
    mark(el, key) {
      const d = drafts.get(key);
      el.classList.toggle(Style.roleClass("mark"), !!d);
      if (d) el.dataset.unsent = d.why; else delete el.dataset.unsent;
      // Juniper c359: the other side is painted beside the kept words, not only in the notice, before a resend counts
      if (d && d.refused && d.shown) el.dataset.now = d.shown.text; else delete el.dataset.now;
    },
    // rules 1 and 2 (Iris, Astra): keep an element whose paint did not change, placing only the kids that differ;
    // re-inserting an untouched sibling would drop the reader's selection inside it. A part with its own words
    // cannot have its children swapped without losing the words (until the frame/leaf split, pike-7 section 4).
    reuse(el, els, words) {
      const keyed = () => [...el.children].filter(c => c.dataset.key);    // the painter's own chrome (a fold handle) is not a kid
      const same = els.length === keyed().length && els.every((e, i) => keyed()[i] === e);
      if (!same && words) return false;
      // Pike (S20): remove the leavers first. Placing first moved a kept sibling past a replaced one, and a moved element
      // loses the pointer capture of a card being carried inside it (and a selection inside it).
      const want = new Set(els);
      keyed().forEach(c => { if (!want.has(c)) c.remove(); });
      els.forEach((e, i) => { const k = keyed(); if (k[i] !== e) el.insertBefore(e, k[i] || null); });
      return true;
    },
    // a fold is the lens's default (paint.folded) with this viewer's override: never an event, never another viewer's
    folded(key, dflt) { return key in folds ? folds[key] : !!dflt; },
    fold(key, f) { folds[key] = f; try { localStorage.setItem(foldStore, JSON.stringify(folds)); } catch {} },
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
        if (attention && el.dataset.folded) f.push("folded");
        if (f.length) facts[el.dataset.key] = f.join(", ");
      }
      const view = attention ? { viewport: { w: Math.round(vp.width), h: Math.round(vp.height), sx: Math.round(paint.scrollLeft), sy: Math.round(paint.scrollTop) } } : {};
      const body = JSON.stringify({ session, as: who, lens, at, facts, ...view });
      if (body !== told) { told = body; fetch("/api/observe", { method: "POST", body }); }
    },
    // Pike (run 1, Alex's workspace): everything repaints but the part in hand; focus, caret and selection are put back
    keep(draw) {
      const ed = document.activeElement, s = getSelection(), sel = s.rangeCount ? [s.anchorNode, s.anchorOffset, s.focusNode, s.focusOffset] : null;
      // codex team (pike-8 section 2), generalised: if the focused element leaves, focus goes to the element that now
      // has its key, else to the one now at its place among its siblings, else to its parent; never to the page's top
      const fk = ed && ed.dataset && ed.dataset.key, up = fk && ed.parentElement, at = up ? [...up.children].indexOf(ed) : -1;
      const pk = up && up.dataset && up.dataset.key;
      // scroll end (chat): a frame this viewer had at its end stays at its end; one never seen before starts there
      const ends = new Set([...document.querySelectorAll('[data-scroll="end"]')].filter(e => e.scrollTop + e.clientHeight >= e.scrollHeight - 2).map(e => e.dataset.key));
      const seenBefore = new Set([...document.querySelectorAll('[data-scroll="end"]')].map(e => e.dataset.key));
      // a1134 (Alex, 30 Sep: "I keep getting jumped to the top of the conversation in shop talk"): a frame whose lines
      // changed is made again, and a new element starts at the top. Every scrolling frame the viewer wasn't at the end
      // of keeps its place by the line at its top: which child, and how far down the frame it sat.
      const places = new Map();
      for (const e of document.querySelectorAll("[data-scroll]")) {
        if (ends.has(e.dataset.key) || e.scrollHeight <= e.clientHeight) continue;
        const top = e.getBoundingClientRect().top, kid = [...e.children].find(c => c.dataset.key && c.getBoundingClientRect().bottom > top + 1);
        places.set(e.dataset.key, { y: e.scrollTop, kid: kid && kid.dataset.key, off: kid ? kid.getBoundingClientRect().top - top : 0 });
      }
      v.repainting = true;
      try {
        draw();
        if (ed && ed !== document.body && ed.isConnected && document.activeElement !== ed) ed.focus();
        else if (fk && !ed.isConnected) {
          const q = k => document.querySelector(`[data-key="${CSS.escape(k)}"]`), same = q(fk), parent = pk && q(pk);
          const next = same || (parent && (parent.children[at] || parent.children[at - 1])) || parent;
          if (next) { if (!next.hasAttribute("tabindex") && !next.isContentEditable && !/^(BUTTON|A|INPUT|TEXTAREA)$/.test(next.tagName)) next.tabIndex = -1; next.focus(); }
        }
        for (const e of document.querySelectorAll('[data-scroll="end"]')) if (ends.has(e.dataset.key) || !seenBefore.has(e.dataset.key)) e.scrollTop = e.scrollHeight;
        for (const e of document.querySelectorAll("[data-scroll]")) {
          const p = places.get(e.dataset.key); if (!p) continue;
          const kid = p.kid && [...e.children].find(c => c.dataset.key === p.kid);
          if (kid) e.scrollTop += kid.getBoundingClientRect().top - e.getBoundingClientRect().top - p.off;
          else e.scrollTop = p.y;
        }
        const moved = sel && (s.anchorNode !== sel[0] || s.anchorOffset !== sel[1] || s.focusNode !== sel[2] || s.focusOffset !== sel[3]);
        if (moved && sel[0].isConnected && sel[2].isConnected) s.setBaseAndExtent(...sel);   // only if the repaint moved it
      } finally { v.repainting = false; }
    },
  };
  return v;
};
