// viewer.js : the viewer half of paint(scene, viewer). OWNER: Pike (pike-7 section 1).
// The scene is the same for everyone; the viewer is one person at one window: the part in hand, drafts typed and
// refused, the refusal on screen, focus, caret and selection. It is never the world and never history. Continuity
// is counted apart from vocabulary (a361, Jeff): this file holds the continuity rules, lens.js holds the paint kinds.
//   1. an element lives as long as its key            (lens.js: keyed reuse)
//   2. it changes only when its paint changes          (lens.js: the signature is paint, act shapes and kid keys)
//   3. the part in hand is drawn from the scene it was taken from until it is put down   (hold)
//   4. viewer marks are drawn in honesty roles, never silently   (mark: unsent, refused)
const Viewer = (session, who, lens, said, status) => {
  // Juniper c347 (7): typed words outlive a closed tab. localStorage stands in for the viewer store: this browser only.
  // One slot per session, viewer and lens (two windows of one viewer share it).
  // a6067 (Sable, on a6067 c6106, sorting by whose a value is): the unsent WORDS of a field are the person's: one draft
  // per field, the same in every window that shows it, kept in step while both are open (the `storage` event), and
  // said in both when two windows type into one field at once. The caret, the selection and an input method's half-
  // typed words are the WINDOW's: kept in a slot of the window's own (its id in sessionStorage, under the frame's name,
  // so two named frames or pop-outs are two windows), never shared. Nothing precious lives in a window's slot, so a
  // new window takes no one's over: it starts with no caret, and a slot whose window is gone is only a stale caret.
  const store = `lens-drafts:${session}:${who}:${lens}`;
  let drafts;
  try { drafts = new Map(JSON.parse(localStorage.getItem(store)) || []); } catch { drafts = new Map(); }
  const widKey = "lens-window:" + (typeof window !== "undefined" && window.name || "");
  let wid = null;
  try { wid = sessionStorage.getItem(widKey); } catch {}
  if (!wid) { wid = Math.random().toString(36).slice(2, 10); try { sessionStorage.setItem(widKey, wid); } catch {} }
  const winStore = `lens-window:${session}:${who}:${lens}:${wid}`;          // in sessionStorage: it lives as the window does
  let texts; try { texts = JSON.parse(sessionStorage.getItem(winStore)) || {}; } catch { texts = {}; }
  const typedAt = new Map(), onDrafts = [], fromElsewhere = new Set();   // fields whose words last came from another window
  // codex team (pike-8 section 2): a saved draft with no record of what it was typed against is never sent against
  // today's paint. It stays, marked; the person copies it, drops it (Escape) and starts from the current text.
  const unknownOrigin = "origin unknown: this kept draft has no record of what it was typed against; copy it if you need it, then Escape and start from the current text";
  for (const d of drafts.values()) if (!d.seen && !d.shown) d.why = unknownOrigin;
  let notice = drafts.size ? `unsent: ${drafts.size} draft(s) kept from before, marked where they were typed` : "";
  let text = "", told = "", unheardIn = null, kept = null;
  let published = new Map([...drafts].map(([k, d]) => [k, JSON.stringify(d)]));   // the drafts as last agreed with the store
  let shownNotice = "", noticeTimer;
  const foldStore = `lens-folds:${session}:${who}:${lens}`;
  let folds; try { folds = JSON.parse(localStorage.getItem(foldStore)) || {}; } catch { folds = {}; }
  const pending = new Map();      // key -> the draft generation in flight (codex team: a request in flight is viewer state)
  const refusal = why => (/^refused/.test(why) ? "" : "refused: ") + why;      // deskd's own sentences already begin so
  const both = (key, d) => `${refusal(d.why)}\nunsent, yours: "${d.text}"\nnow in the world: "${d.shown.text}"\nReview the current version before sending again.`;
  const v = {
    drafts, hold: null, repainting: false,
    recoverLayout(root) {
      // A wrapper added to a lens changes path keys. Recover only a unique match
      // on the stable row/thing plus leaf path, and require review before sending.
      const nodes = [], walk = n => { nodes.push(n); (n.kids || []).forEach(walk); }; walk(root);
      const keys = new Set(nodes.map(n => n.key));
      const tail = key => { const parts = key.split('/'); let i = parts.length - 1;
        while (i >= 0 && !/^[asfcm]\d+$/.test(parts[i])) i--; return i >= 0 ? parts.slice(i).join('/') : null; };
      const missing = [...drafts].filter(([key]) => !keys.has(key) && !pending.has(key));
      let recovered = 0;
      for (const [key, draft] of missing) {
        const suffix = tail(key); if (!suffix || missing.filter(([k]) => tail(k) === suffix).length !== 1) continue;
        const item = (draft.shown || draft.seen)?.fence?.item;
        const matches = nodes.filter(n => tail(n.key) === suffix && (!item || n.fence?.item === item)
          && (n.acts || []).some(a => a.on === 'edit'));
        if (matches.length !== 1 || drafts.has(matches[0].key)) continue;
        const target = matches[0].key;
        drafts.set(target, { text: draft.text, previousOrigin: draft.shown || draft.seen || draft.previousOrigin,
          why: 'layout changed; review the current field before sending your kept words' });
        drafts.delete(key);
        for (const n of nodes) if (target.startsWith(n.key + '/') && n.paint?.fold) v.fold(n.key, false);
        recovered++;
      }
      if (recovered) { notice = `kept ${recovered} draft(s) through the layout change; review the current field before sending`; v.show(); }
    },
    // Keep the full refusal in the inspector and draft marker. Its brief notice
    // occupies a reserved footer row, never the words being read or edited.
    notify(message) { notice = message; shownNotice = ""; v.show(); },
    show(t) {
      if (t !== undefined) text = t;
      said.textContent = (notice ? notice + "\n\n" : "") + text;
      if (status && notice !== shownNotice) {
        clearTimeout(noticeTimer); shownNotice = notice;
        const lines = notice.split("\n").map(s => s.trim()).filter(Boolean);
        const summary = lines.find(s => /^(ERR|refused:)/.test(s) && !s.includes("since your last look")) || lines[0] || "";
        status.textContent = summary; status.title = notice; status.hidden = !notice;
        if (notice) noticeTimer = setTimeout(() => { status.hidden = true; }, 4500);
      }
      v.publish();
    },
    // a6067 (Codex c6203, Sable c6206): the store is shared by the person's windows, so a window writes only what IT
    // changed, into what the store holds now, never its whole map over another window's newer words. A draft it
    // cleared is removed only if the store still holds the very words it knew (the equality the desk keeps for text);
    // newer words from another window are kept, taken back here, and said. What other windows changed is taken in.
    publish() {
      let S; try { S = new Map(JSON.parse(localStorage.getItem(store)) || []); } catch { S = new Map(); }
      const J = x => x === undefined ? undefined : JSON.stringify(x), mineKeys = new Set(), keptBack = [], theirs = [], together = [];
      for (const k of new Set([...drafts.keys(), ...published.keys()])) {
        const mine = J(drafts.get(k)), was = published.get(k);
        if (mine === was) continue;                              // not changed in this window
        mineKeys.add(k);
        const there = J(S.get(k));
        if (mine !== undefined) S.set(k, drafts.get(k));
        else if (there === was) S.delete(k);                     // cleared here: the store still holds what was cleared
        else if (there !== undefined) { drafts.set(k, S.get(k)); keptBack.push(k); }   // newer words elsewhere: kept
      }
      // what another window changed that this one had not heard (a key with a send in flight here too: its answer
      // then sees newer words than it sent, and keeps them)
      for (const k of new Set([...S.keys(), ...drafts.keys()])) {
        if (mineKeys.has(k) || J(S.get(k)) === J(drafts.get(k))) continue;
        // this window has its own unsent words here too (typed here, not taken from another window, no send of them in
        // flight): both windows are typing in this field. Each keeps its own words, never the last keystroke over the
        // other's, and says so (Sable, Codex). A field with a send in flight takes the other's words, so its answer
        // sees them as newer than what it sent and keeps them
        if (drafts.has(k) && typedAt.has(k) && !fromElsewhere.has(k) && !pending.has(k)) {
          if (S.has(k)) together.push(k); else S.set(k, drafts.get(k));   // the other window sent ITS words: ours go back in
          continue;
        }
        if (S.has(k)) drafts.set(k, S.get(k)); else drafts.delete(k);
        theirs.push(k); fromElsewhere.add(k);
      }
      published = new Map([...S].map(([k, d]) => [k, J(d)]));
      for (const k of together) published.set(k, J(drafts.get(k)));     // kept as ours: a later clear here leaves theirs
      const want = JSON.stringify([...S]);
      if (want !== kept) { kept = want; try { localStorage.setItem(store, want); } catch {} }   // (an unchanged store tells no other window)
      if (keptBack.length) notice = "sent; newer words kept (typed since, in another of your windows)";
      if (together.length) notice = "you are typing in this field in another of your windows too: each window keeps what it typed; check both before sending";
      if (keptBack.length || together.length) said.textContent = notice + "\n\n" + text;
      const changed = [...keptBack, ...theirs];
      if (changed.length) for (const f of onDrafts) f(changed);
    },
    window: wid,
    // a6067: a typed text's window state (textedit.js): caret and selection, this window's only (Sable)
    textState(key, st) {
      if (st === undefined) return texts[key] || null;
      if (st === null) delete texts[key]; else texts[key] = st;
      try { sessionStorage.setItem(winStore, JSON.stringify(texts)); } catch {}
    },
    // a6067: the module fitted unsent words over newer words of the desk's: they are now typed against that version
    // (the fence they will be sent on) and those words (base); a refusal they had is answered by the fitting. The
    // words, their fence and their gesture id stay together (Codex, a6067 c6120)
    rebased(key, words, origin, base) {
      const d = drafts.get(key);
      if (d && !d.refused && d.text === words && d.base === base && JSON.stringify(d.seen) === JSON.stringify(origin)) return;
      typedAt.set(key, Date.now()); fromElsewhere.delete(key);
      drafts.set(key, { text: words, why: "typed here, not sent", seen: origin, base, gesture: d && d.text === words ? d.gesture : undefined });
      if (d && d.refused) notice = "";
      v.show();
    },
    // a6067: told when another window of this person changed a draft (keys); a part showing it draws it again
    onDrafts(f) { onDrafts.push(f); },
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
      // a6067 (Sable c6206, Codex c6224): the words are newer when the draft now holds anything but the words that were
      // sent (by their text, not by which object holds them); a send that began with no draft never clears words typed
      // while it was out. Newer words are ALWAYS kept, whatever is said about them below
      const cur = drafts.get(key), sent = draft !== undefined ? draft : token && token.draft ? token.draft.text : undefined;
      const newer = !!cur && cur.text !== sent;
      if (!newer) v.hold = null;
      if (err) {
        shownNotice = "";
        notice = refusal(err);
        // pike-8 section 3: a refused draft is kept, and the world's current value will be drawn beside it (both sides);
        // a resend is fenced on the value shown, never on a fresher one the person has not seen
        if (draft !== undefined && !newer) drafts.set(key, { text: draft, why: err.split("\n").pop(), refused: true, shown: null, gesture: token && token.draft && token.draft.gesture });
      } else if (newer) {                                   // kept; only what is said differs
        if (fromElsewhere.has(key)) notice = "sent; newer words kept (typed since, in another of your windows)";   // Sable c6206
        else if (!texts[key]) notice = "sent the earlier words; what you typed since is still unsent";   // a module text says so itself
      } else { notice = ""; drafts.delete(key); }
      v.show();
    },
    busy(key) { return pending.has(key); },      // a6067: is a send of this part's in flight
    drop(key) {
      if (pending.has(key)) { notice = "a send is in flight; wait for its answer before dropping this draft"; v.show(); return false; }
      drafts.delete(key); notice = ""; v.show(); return true;
    },
    // a kept draft remembers what it was typed against, so sending it after a reload is fenced on that, not on today's paint
    typed(key, words, fence) {
      const d = drafts.get(key), seen = d ? (d.shown || d.seen) : fence;
      if (d && d.refused && seen) notice = "draft kept; edited against the version shown";
      typedAt.set(key, Date.now()); fromElsewhere.delete(key);
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
    // An explicit composer can offer recovery against the version visibly shown here.
    // This is a person's separate review action, never an automatic rebase or send.
    useCurrent(key, current) {
      if (pending.has(key) || !current || !current.fence) return false;
      const d = drafts.get(key); if (!d) return false;
      drafts.set(key, { text: d.text, seen: current, why: "typed here, not sent" });
      notice = "draft kept; using the version shown here"; v.show(); return true;
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
    // a1473 (Sable's a1266: lanes shrank to their titles and no text could tell): each painted part's box goes too,
    // "WxH", with "sh=" / "sw=" when its contents are taller / wider than it, "cut=n/m" when n of its m parts are clipped
    // by a box that does not scroll, "out=n/m" (attention only: it depends on where it is scrolled) for one that does,
    // and "hidden" when it is not drawn (inside a fold). `painted` is the lens frame and style revision it was painted at.
    // a5047 (Alex e9743: a dragged rectangle must find the parts under it; a window manager places windows at the boxes
    // a page paints): "WxH@x,y", where x,y is the part's left and top in CSS pixels from the page's top left as laid out,
    // the scroll of every frame around it (the page's own too) taken back out, so a position never tells where anyone
    // has scrolled. The page's inner size and device pixel ratio go with every report: a page's size is not attention.
    report(paint, at, extra, attention, painted) {
      const vp = paint.getBoundingClientRect(), facts = attention ? { ...extra } : {}, boxes = {};
      // parts come in page order, so the scrolled frames around a part are a stack: [frame, its scroll and all above it]
      const frames = [[paint, scrollX + paint.scrollLeft, scrollY + paint.scrollTop]];
      for (const el of paint.querySelectorAll("[data-key]")) {
        const r = el.getBoundingClientRect(), f = [];
        if (!el.getClientRects().length) boxes[el.dataset.key] = "hidden";
        else {
          while (!frames.at(-1)[0].contains(el)) frames.pop();
          const [, dx, dy] = frames.at(-1);
          let b = `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.left + dx)},${Math.round(r.top + dy)}`;
          const tall = el.scrollHeight > el.clientHeight + 1, wide = el.scrollWidth > el.clientWidth + 1;
          if ((tall || wide) && (el.scrollTop || el.scrollLeft)) frames.push([el, dx + el.scrollLeft, dy + el.scrollTop]);
          if (tall || wide) {
            const s = getComputedStyle(el), o = s.overflowX + s.overflowY, scrolls = /auto|scroll/.test(o), clips = scrolls || /hidden|clip/.test(o);
            b += (scrolls ? " scroll" : clips ? " clip" : " spill") + (tall ? ` sh=${el.scrollHeight}` : "") + (wide ? ` sw=${el.scrollWidth}` : "");
            const kids = [...el.children].filter(c => c.dataset.key && c.getClientRects().length);
            const n = clips ? kids.filter(c => { const k = c.getBoundingClientRect(); return k.bottom > r.bottom + 1 || k.right > r.right + 1 || k.top < r.top - 1 || k.left < r.left - 1; }).length : 0;
            if (n && !scrolls) b += ` cut=${n}/${kids.length}`;
            if (n && scrolls && attention) b += ` out=${n}/${kids.length}`;
          }
          boxes[el.dataset.key] = b;
        }
        if (el.classList.contains("clamp") && el.scrollHeight > el.clientHeight + 1) f.push("cut by the clamp");
        if (el.classList.contains("boxed") && el.scrollHeight > el.clientHeight + 1) f.push("contents overflow the box");
        if (attention && el.classList.contains("boxed") && (r.bottom < vp.top || r.top > vp.bottom || r.right < vp.left || r.left > vp.right)) f.push("out of view");
        if (attention && el.dataset.unsent) f.push("unsent draft");
        if (attention && el.dataset.folded) f.push("folded");
        if (f.length) facts[el.dataset.key] = f.join(", ");
      }
      const view = attention ? { viewport: { w: Math.round(vp.width), h: Math.round(vp.height), sx: Math.round(paint.scrollLeft), sy: Math.round(paint.scrollTop) } } : {};
      const page = { w: innerWidth, h: innerHeight, dpr: devicePixelRatio };
      const body = JSON.stringify({ session, as: who, lens, at, facts, boxes, page, painted: painted || null, ...view });
      // a4869 (Sable c4900): a report does not outlive the house that kept it. When the scene's words name no report of
      // this viewer (`  ~ <who> ` heads each one), the house has none: the same report goes again, once per such text
      const unheard = !text.split("\n").some(l => l.startsWith(`  ~ ${String(who).toLowerCase()} `));
      if (body !== told || (unheard && text !== unheardIn)) {
        told = body; unheardIn = unheard ? text : null; fetch("/api/observe", { method: "POST", body });
      }
    },
    // where each scrolling frame is: plain data, so a page reloaded for new painter code (a1505) can carry it.
    // Scroll end (chat): a frame this viewer had at its end stays at its end; one never seen before starts there.
    // a1134 (Alex, 30 Sep: "I keep getting jumped to the top of the conversation in shop talk"): a frame whose lines
    // changed is made again, and a new element starts at the top. Every scrolling frame the viewer wasn't at the end
    // of keeps its place by the line at its top: which child, and how far down the frame it sat.
    places() {
      const all = [...document.querySelectorAll('[data-scroll="end"]')];
      const out = { ends: all.filter(e => e.scrollTop + e.clientHeight >= e.scrollHeight - 2).map(e => e.dataset.key), seen: all.map(e => e.dataset.key), at: {} };
      for (const e of document.querySelectorAll("[data-scroll]")) {
        if (out.ends.includes(e.dataset.key) || e.scrollHeight <= e.clientHeight) continue;
        const top = e.getBoundingClientRect().top, kid = [...e.children].find(c => c.dataset.key && c.getBoundingClientRect().bottom > top + 1);
        out.at[e.dataset.key] = { y: e.scrollTop, kid: kid && kid.dataset.key, off: kid ? kid.getBoundingClientRect().top - top : 0 };
      }
      return out;
    },
    place(pl) {
      const ends = new Set(pl.ends), seen = new Set(pl.seen);
      for (const e of document.querySelectorAll('[data-scroll="end"]')) if (ends.has(e.dataset.key) || !seen.has(e.dataset.key)) e.scrollTop = e.scrollHeight;
      for (const e of document.querySelectorAll("[data-scroll]")) {
        const p = pl.at[e.dataset.key]; if (!p) continue;
        const kid = p.kid && [...e.children].find(c => c.dataset.key === p.kid);
        if (kid) e.scrollTop += kid.getBoundingClientRect().top - e.getBoundingClientRect().top - p.off;
        else e.scrollTop = p.y;
      }
    },
    // Pike (run 1, Alex's workspace): everything repaints but the part in hand; focus, caret and selection are put back
    keep(draw) {
      const ed = document.activeElement, s = getSelection(), sel = s.rangeCount ? [s.anchorNode, s.anchorOffset, s.focusNode, s.focusOffset] : null;
      // codex team (pike-8 section 2), generalised: if the focused element leaves, focus goes to the element that now
      // has its key, else to the one now at its place among its siblings, else to its parent; never to the page's top
      const fk = ed && ed.dataset && ed.dataset.key, up = fk && ed.parentElement, at = up ? [...up.children].indexOf(ed) : -1;
      const pk = up && up.dataset && up.dataset.key;
      // 14 Oct (Alex: 'cursor keeps jumping to the beginning of the line'): a text being written that is made again
      // took focus at its start; the caret is carried as a count of characters into the words, so it lands where it was
      let off = null;
      if (ed && ed.isContentEditable && s.rangeCount && ed.contains(s.focusNode)) {
        const r = document.createRange(); r.selectNodeContents(ed); r.setEnd(s.focusNode, s.focusOffset); off = r.toString().length;
      }
      const places = v.places();
      v.repainting = true;
      try {
        draw();
        if (ed && ed !== document.body && ed.isConnected && document.activeElement !== ed) ed.focus();
        else if (fk && !ed.isConnected) {
          const q = k => document.querySelector(`[data-key="${CSS.escape(k)}"]`), same = q(fk), parent = pk && q(pk);
          const next = same || (parent && (parent.children[at] || parent.children[at - 1])) || parent;
          if (next) { if (!next.hasAttribute("tabindex") && !next.isContentEditable && !/^(BUTTON|A|INPUT|TEXTAREA)$/.test(next.tagName)) next.tabIndex = -1; next.focus(); }
          if (next && next === same && off != null && next.isContentEditable) {
            const w = document.createTreeWalker(next, NodeFilter.SHOW_TEXT); let t, left = off;
            while ((t = w.nextNode()) && left > t.length) left -= t.length;
            if (t) s.collapse(t, left); else { s.selectAllChildren(next); s.collapseToEnd(); }
            v.place(places);
            return;
          }
        }
        v.place(places);
        const moved = sel && (s.anchorNode !== sel[0] || s.anchorOffset !== sel[1] || s.focusNode !== sel[2] || s.focusOffset !== sel[3]);
        if (moved && sel[0].isConnected && sel[2].isConnected) s.setBaseAndExtent(...sel);   // only if the repaint moved it
      } finally { v.repainting = false; }
    },
  };
  // a6067 (Sable): another window of this person changed a draft: the same words here (publish takes them in), drawn
  // again by whoever shows them. Typed in both at once: said in both.
  if (typeof addEventListener === "function") addEventListener("storage", e => {
    if (e.key !== store || e.newValue === kept) return;
    const was = notice;
    v.publish();
    if (notice !== was) v.show();
  });
  return v;
};
