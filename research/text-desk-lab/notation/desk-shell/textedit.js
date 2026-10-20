// textedit.js: the continuous-text module (a6067). OWNER: worker-a6067 for JEFF (a6067); Sable holds the painter's
// modules and keys (c5977), Pike documents (c5974); anyone may improve it, telling them by Shop talk first.
//
// ONE module for every text a person types into: a document (Markdown, drawn live) and a plain box (the chat composer,
// a comment or reply box, the find box). One behaviour everywhere: the same keys, the same undo, the same composition.
// THE BOUNDARY (Pike c5974): the module owns one person's moment of typing; the world owns everything another person
// or an agent might read, answer or rely on.
//   module (this window, never history): caret, selection, IME composition, live Markdown, the person's unsent edits
//     and fitting them over what the desk sends, undo of unsent keys, hooks that ASK the world.
//   world: the one text and its log, undo of a sent edit (`undo eN`), links, comments and their anchors, ticks.
//
// THE INTERFACE (small, on purpose)
//   TextEdit.create(opts) -> editor           a Markdown document: opts.surface = "markdown" (default)
//   TextEdit.attach(textarea, opts) -> editor a plain box: the textarea stays the browser's (IME, AltGr, spelling)
//   opts:  text, version          the desk's words and the version they are at (opaque: the painter gives its fence)
//          editable, hint, key    key: the part's scene key, for ids the control screen reads (part:<key>::<line>)
//          keep {load(), save(st)} the viewer's keeper (viewer.js): the unsent words and what they were typed on are
//                                 the PERSON's draft (one per field, the same in all their windows); the caret and
//                                 selection are THIS WINDOW's (Sable, a6067)
//          seam {send(out)}       out = {text, version, edits}; resolves {ok, event, error}. Without a seam the
//                                 customer sends (a composer's Enter: no autosave, no fitting, no desk undo there)
//          hooks                  pick(q) [[ picker titles, follow(id), capture(anchor, data), undoSent(event),
//                                 overrode(changes, event) after "Keep mine" was sent over someone's edit,
//                                 notify(words), changed(st) after any change (the customer's own bookkeeping)
//          links, things, titles, light, lightClass     Markdown only: [[link]] targets, ids drawn as names (a6109),
//                                 picker titles, lit passages
//   editor: el, src(), receive(text, version), adopt(text, base, version) (another window's unsent words), flush(),
//           anchor(), picked(), press(key), lights(l), links(l), titles(t), resolve("mine"|"theirs"), composing(),
//           state(), doc
//
// THE SEAM (Pike c5974; a4865 is Alex's choice and this file does not make it): 'send an edit against a version,
// receive ordered edits'. The module sends {version, edits, text} as the person pauses and receives the desk's words
// with their version; each new text is turned into ordered edits (the difference from the last one), and the
// person's unsent edits are fitted over them. Behind the seam TODAY: the whole text, fenced by that version (the
// painter sends the part's `on edit` with $value the text and the fence it was fitted to; a stale fence is refused,
// the next words received are fitted, and it goes again). Yjs, Loro or an ordering of our own can sit behind the
// same two calls.
//
// FITTING (a resident's `do replace` over live typing): the desk's edit and the person's unsent edits are compared
// as ranges of the text both started from. Apart: the desk's goes in, the person's stay, the caret moves with its
// words. Both inserting at one point: the desk's first (it was ordered first), the person's after. Overlapping the
// same words: a CONFLICT, said loudly; nothing is sent until the person chooses: keep mine (sent over theirs) or
// take theirs. Never a guess at a merge of the same words.
//
// UNDO, two with a seam (Sable c5977): Ctrl+Z undoes keys not yet sent; with none left, it asks the desk to undo the
// person's last sent edit (`undo eN`, the world's undo); each press says which it did.
// KEYS (Sable c5977): Enter, Tab, Ctrl+B/I/K/E/S/Z/Y are the text's. No Ctrl+Alt combination is bound at all (the
// window manager, the home base and the control screen hold them); AltGr is Ctrl+Alt on Windows, so a key with Alt or
// AltGraph held is never a shortcut here: its character arrives as text.
(() => {
  // ---- the core: texts, edits, fitting (no page needed; test_textedit.mjs runs it in node) -----------------------
  // an edit is {a, b, s}: the characters a..b of the text it is against become s

  // the differences between two texts as edits against the first, in order: by lines (Myers), each changed run of
  // lines narrowed to the characters that differ, so two edits on two lines stay two edits
  function diff(x, y) {
    if (x === y) return [];
    // the lines both share at the start and the end are set aside, whole lines, so lines are compared as lines
    const X = lines(x), Y = lines(y);
    let i = 0; while (i < X.length && i < Y.length && X[i] === Y[i]) i++;
    let j = 0; while (j < X.length - i && j < Y.length - i && X[X.length - 1 - j] === Y[Y.length - 1 - j]) j++;
    const p = X.slice(0, i).join("").length;
    const xm = X.slice(i, X.length - j).join(""), ym = Y.slice(i, Y.length - j).join("");
    const narrow = (a0, sa, sb) => {
      let k = 0; while (k < sa.length && k < sb.length && sa[k] === sb[k]) k++;
      let r = 0; while (r < sa.length - k && r < sb.length - k && sa[sa.length - 1 - r] === sb[sb.length - 1 - r]) r++;
      return k === sa.length && k === sb.length ? null : { a: a0 + k, b: a0 + sa.length - r, s: sb.slice(k, sb.length - r) };
    };
    const A = X.slice(i, X.length - j), B = Y.slice(i, Y.length - j), runs = myers(A, B);
    if (!runs) return [narrow(p, xm, ym)].filter(Boolean);
    const out = [];
    let ax = 0, ai = 0, by = 0, bi = 0;
    const offA = i => { while (ai < i) ax += A[ai++].length; return ax; }, offB = j => { while (bi < j) by += B[bi++].length; return by; };
    for (const [i0, i1, j0, j1] of runs) {
      const a0 = offA(i0), b0 = offB(j0);
      // as many lines changed as there were: line by line, so edits on neighbouring lines stay apart
      if (i1 - i0 === j1 - j0) {
        let a = p + a0;
        for (let i = 0; i < i1 - i0; i++) { const e = narrow(a, A[i0 + i], B[j0 + i]); if (e) out.push(e); a += A[i0 + i].length; }
      } else { const e = narrow(p + a0, A.slice(i0, i1).join(""), B.slice(j0, j1).join("")); if (e) out.push(e); }
    }
    return out;
  }
  const lines = s => s.match(/[^\n]*\n|[^\n]+$/g) || [];
  // Myers' O(ND) difference of two lists, as runs [i0, i1, j0, j1] (A[i0..i1] became B[j0..j1]); null past a budget
  function myers(A, B) {
    const N = A.length, M = B.length, MAX = Math.min(N + M, 4000), V = new Map([[1, 0]]), trace = [];
    for (let d = 0; d <= MAX; d++) {
      trace.push(new Map(V));
      for (let k = -d; k <= d; k += 2) {
        let i = k === -d || (k !== d && (V.get(k - 1) ?? -1) < (V.get(k + 1) ?? -1)) ? V.get(k + 1) ?? 0 : (V.get(k - 1) ?? 0) + 1;
        let j = i - k;
        while (i < N && j < M && A[i] === B[j]) { i++; j++; }
        V.set(k, i);
        if (i >= N && j >= M) return runsOf(trace, A, B, d, k);
      }
    }
    return null;
  }
  function runsOf(trace, A, B, D, kEnd) {
    const steps = []; let i = A.length, j = B.length, k = kEnd;
    for (let d = D; d > 0; d--) {
      const V = trace[d], down = k === -d || (k !== d && (V.get(k - 1) ?? -1) < (V.get(k + 1) ?? -1)), pk = down ? k + 1 : k - 1;
      const pi = V.get(pk) ?? 0, pj = pi - pk;
      while (i > (down ? pi : pi + 1) && j > (down ? pj + 1 : pj)) { i--; j--; }
      steps.push(down ? ["ins", pi, pj] : ["del", pi, pj]);
      i = pi; j = pj; k = pk;
    }
    const runs = [];
    for (const [t, pi, pj] of steps.reverse()) {
      const r = t === "ins" ? [pi, pi, pj, pj + 1] : [pi, pi + 1, pj, pj];
      const last = runs[runs.length - 1];
      if (last && last[1] === r[0] && last[3] === r[2]) { last[1] = r[1]; last[3] = r[3]; } else runs.push(r);
    }
    return runs;
  }
  const apply = (t, es) => { for (const e of [...es].sort((u, v) => v.a - u.a)) t = t.slice(0, e.a) + e.s + t.slice(e.b); return t; };
  // do two edits of one text touch the same words? (both inserting at one point do not: the desk's goes first)
  const clash = (w, l) => (w.a < l.b && l.a < w.b) || (w.a === w.b && l.a < w.a && w.a < l.b) || (l.a === l.b && w.a < l.a && l.a < w.b);

  // fit the desk's new words over the person's: base is what both started from, next the desk's, local the person's.
  // -> {text, sel, theirs} with the selection carried, or {conflict, theirs, mine} when they touch the same words
  function fit(base, next, local, sel) {
    let W = diff(base, next), L = diff(base, local);
    // the same edit on both sides (another window of the person's already holding mine) is one edit, not a clash
    const same = (u, v) => u.a === v.a && u.b === v.b && u.s === v.s;
    const both = W.filter(w => L.some(l => same(w, l)));
    if (both.length) { W = W.filter(w => !both.some(x => same(w, x))); }
    const hit = W.find(w => L.some(l => clash(w, l)));
    if (hit) return { conflict: true, theirs: W, mine: L, at: hit, with: L.find(l => clash(hit, l)) };
    // the desk's edits in the person's text: shifted by the person's edits before them (one at the same point
    // inserting is after the desk's, so it does not shift it)
    const shift = pos => pos + L.filter(l => l.b <= pos && !(l.a === l.b && l.a === pos)).reduce((n, l) => n + l.s.length - (l.b - l.a), 0);
    const Wl = W.map(w => ({ a: shift(w.a), b: shift(w.a) + (w.b - w.a), s: w.s }));
    const move = c => { for (const w of [...Wl].sort((u, v) => v.a - u.a)) { if (c >= w.b && c > w.a) c += w.s.length - (w.b - w.a); else if (c > w.a) c = w.a + w.s.length; } return c; };
    return { text: apply(local, Wl), sel: sel ? [move(sel[0]), move(sel[1])] : null, theirs: W };
  }

  // one text being typed: what the desk last said (base, at version), the person's words (text), and the edits between
  class Doc {
    constructor({ text = "", version = null, local = null, base = null } = {}) {
      this.base = base != null ? base : text; this.version = version; this.text = local != null ? local : this.base;
      this.sel = [this.text.length, this.text.length]; this.undo = []; this.redo = []; this.last = 0;
      this.inflight = null; this.conflict = null; this.sent = [];
      // a kept draft whose base is not the desk's words now (the window was closed while someone else wrote)
      if (base != null && base !== text) this.receive(text, version);
    }
    get dirty() { return this.text !== this.base; }
    edits() { return diff(this.base, this.text); }
    // the person's edit. how: type (runs of typing undo as one), paste, del, compose, key, undo
    edit(a, b, s, how = "key", sel = null) {
      const now = Date.now();
      if (how !== "type" || now - this.last > 900 || !this.undo.length) { this.undo.push({ text: this.text, sel: this.sel }); if (this.undo.length > 300) this.undo.shift(); }
      this.last = how === "type" ? now : 0; this.redo = []; this.held = null;
      this.text = this.text.slice(0, a) + s + this.text.slice(b);
      this.sel = sel || [a + s.length, a + s.length];
      return this;
    }
    // a whole new text the surface read back (a plain box after the browser changed it, a composition's line)
    became(text, sel, how = "type") {
      if (text === this.text) { if (sel) this.sel = sel; return this; }
      const [e] = diff(this.text, text).length === 1 ? diff(this.text, text) : [{ a: 0, b: this.text.length, s: text }];
      return this.edit(e.a, e.b, e.s, how, sel);
    }
    undoLocal() { const st = this.undo.pop(); if (!st) return false; this.redo.push({ text: this.text, sel: this.sel }); this.text = st.text; this.sel = st.sel; this.last = 0; return true; }
    redoLocal() { const st = this.redo.pop(); if (!st) return false; this.undo.push({ text: this.text, sel: this.sel }); this.text = st.text; this.sel = st.sel; return true; }
    // what goes to the seam now, or null: nothing unsent, a send already out, a conflict waiting, a version not known
    outgoing() {
      if (!this.dirty || this.inflight || this.conflict || this.held || this.version == null) return null;
      return { text: this.text, version: this.version, edits: this.edits() };
    }
    began(out) { this.inflight = out; }
    // the seam's answer. Accepted: what was sent is the base (its version comes with the desk's next words); the
    // keys typed before it are the desk's to undo now, so they leave this undo. Refused: held, not sent again, until
    // the person types, the desk's words or version move (a stale version is fitted and goes again), or a choice
    answered(ok, event) {
      const out = this.inflight; this.inflight = null;
      // (the desk's newer words may already have been fitted while the refusal was on its way: then it goes again)
      if (!ok) { const at = JSON.stringify(out ? out.version : null); if (JSON.stringify(this.version) === at) this.held = { at }; return; }
      if (!out) return;
      if (event) this.sent.push(event);
      // the desk's words may have come back (with their version) before the answer did: keep that version
      const known = this.base === out.text && this.version != null && JSON.stringify(this.version) !== JSON.stringify(out.version);
      this.base = out.text; if (!known) this.version = null; this.undo = []; this.redo = [];
    }
    // the desk's words arrive, at a version. -> {kind: same|confirmed|fitted|conflict, theirs}
    receive(text, version) {
      text = text == null ? "" : text;
      if (this.held && JSON.stringify(version) !== this.held.at) this.held = null;     // the desk moved: try again
      if (this.conflict) { this.conflict.theirs = text; this.conflict.version = version; return { kind: "conflict" }; }
      if (this.inflight && text === this.inflight.text) {      // our own send came back before its answer
        this.base = text; this.version = version; return { kind: "confirmed" };
      }
      if (text === this.base) { this.version = version; return { kind: "same" }; }
      if (text === this.text) { this.base = text; this.version = version; this.undo = []; this.redo = []; return { kind: "confirmed" }; }
      const r = fit(this.base, text, this.text, this.sel);
      if (r.conflict) {
        // what each side did to the words in dispute, in whole words, for the person to choose by
        const b = this.base, wide = e => { let a = e.a, z = e.b; while (a > 0 && !/\s/.test(b[a - 1])) a--; while (z < b.length && !/\s/.test(b[z])) z++; return [a, z]; };
        const [ta, tz] = wide(r.at), [ma, mz] = wide(r.with);
        const seen = { was: b.slice(Math.min(ta, ma), Math.max(tz, mz)), theirs: b.slice(ta, r.at.a) + r.at.s + b.slice(r.at.b, tz), mine: b.slice(ma, r.with.a) + r.with.s + b.slice(r.with.b, mz) };
        this.conflict = { theirs: text, version, base: this.base, seen };
        return { kind: "conflict", theirs: r.theirs };
      }
      // the person's own undo steps are fitted too; a step that touches the desk's words is dropped (said)
      const keepSteps = list => list.map(st => { const f = fit(this.base, text, st.text, st.sel); return f.conflict ? null : { text: f.text, sel: f.sel }; });
      const u = keepSteps(this.undo), dropped = u.filter(x => !x).length;
      this.undo = u.filter(Boolean); this.redo = keepSteps(this.redo).filter(Boolean);
      const had = this.dirty;
      this.base = text; this.version = version; this.text = r.text; this.sel = r.sel;
      return { kind: had ? "fitted" : "adopted", theirs: r.theirs, dropped };   // adopted: nothing of the person's was unsent
    }
    // the person's choice in a conflict: mine (my words stand, sent over theirs) or theirs (my unsent words go)
    resolve(which) {
      const c = this.conflict; if (!c) return false;
      this.conflict = null; this.held = null; this.base = c.theirs; this.version = c.version;
      // Pike (a6067 c6122): keeping mine undoes what someone else's edit did; once sent, the world is told what was
      // set aside (the customer's hooks.overrode), so a resident learns its words did not stand
      if (which === "mine" && c.base != null) {          // said in whole words: "ship" -> "send", not "hip" -> "end"
        let d = 0;
        this.overrode = diff(c.base, c.theirs).map(e => {
          let a = e.a, b = e.b; while (a > 0 && !/\s/.test(c.base[a - 1])) a--; while (b < c.base.length && !/\s/.test(c.base[b])) b++;
          const grow = e.s.length - (e.b - e.a), out = { was: c.base.slice(a, b), now: c.theirs.slice(a + d, b + d + grow) };
          d += grow; return out;
        });
      }
      if (which === "theirs") { this.text = c.theirs; this.undo = []; this.redo = []; const n = Math.min(this.sel[0], this.text.length); this.sel = [n, n]; }
      return true;
    }
    // a passage, as the world keeps a comment's anchor (Pike c5974): position at a version, the words, words either side
    anchor(a = this.sel[0], b = this.sel[1]) {
      const t = this.text, words = (s, end) => (end ? s.split(/\s+/).filter(Boolean).slice(-6) : s.split(/\s+/).filter(Boolean).slice(0, 6)).join(" ");
      return { version: this.version, start: a, end: b, quote: t.slice(a, b), before: words(t.slice(Math.max(0, a - 200), a), true),
        after: words(t.slice(b, b + 200), false), unsent: this.dirty };
    }
    state() { return { text: this.text, base: this.base, version: this.version, sel: this.sel, conflict: this.conflict && { theirs: this.conflict.theirs } }; }
  }

  // ---- keys ------------------------------------------------------------------------------------------------------
  // a key's name as a shortcut of the text ("Ctrl+b", "Shift+Ctrl+z", "Ctrl+Enter"), or null: not while composing,
  // never with Alt or AltGraph held (AltGr is Ctrl+Alt on Windows: its character is text), never Ctrl+Alt anything
  function shortcut(e) {
    if (e.isComposing || e.keyCode === 229) return null;
    if (e.altKey || (e.getModifierState && e.getModifierState("AltGraph"))) return null;
    if (!(e.ctrlKey || e.metaKey)) return null;
    const k = e.key.length === 1 ? e.key.toLowerCase() : e.key;
    return (e.shiftKey ? "Shift+" : "") + "Ctrl+" + k;
  }
  const SAYS = {        // what each undo press did, said where the person is looking (the two undos' seam)
    local: "undid unsent typing (this window's own undo)",
    redo: "redid unsent typing",
    desk: e => `asked the desk to undo ${e}, your last sent edit (the world's undo: it shows for everyone)`,
    none: "nothing to undo: no unsent typing here, and no sent edit of yours from this window",
  };

  // the part every editor shares: a Doc, the keeper, the seam as the person pauses, the undo seam
  function common(opts, render) {
    const kept = (opts.keep && opts.keep.load && opts.keep.load()) || {};
    const doc = new Doc({ text: opts.text || "", version: opts.version ?? null, local: kept.text != null ? kept.text : null, base: kept.text != null ? (kept.base != null ? kept.base : null) : null });
    if (kept.text != null && kept.base == null && kept.text !== (opts.text || "")) doc.conflict = { theirs: opts.text || "", version: opts.version ?? null, base: null };  // a draft from before: origin unknown
    if (kept.sel && kept.text === doc.text) doc.sel = kept.sel.map(n => Math.min(n, doc.text.length));
    let timer = 0, composing = false, queued = null;
    const E = { doc, composing: () => composing };
    const notify = t => opts.hooks && opts.hooks.notify && opts.hooks.notify(t);
    E.save = () => { if (opts.keep && opts.keep.save) opts.keep.save(doc.state()); if (opts.hooks && opts.hooks.changed) opts.hooks.changed(doc.state()); };
    E.changed = () => { E.save(); if (opts.seam) { clearTimeout(timer); timer = setTimeout(E.flush, opts.pause || 700); } };
    // as the person pauses: one send at a time, never mid-composition, never over a conflict
    E.flush = async () => {
      clearTimeout(timer);
      if (!opts.seam || composing) return null;
      const out = doc.outgoing(); if (!out) return null;
      doc.began(out);
      let r; try { r = await opts.seam.send(out); } catch (err) { r = { ok: false, error: String(err && err.message || err) }; }
      doc.answered(!!(r && r.ok), r && r.event);
      if (r && r.ok && doc.overrode) { const o = doc.overrode; doc.overrode = null; if (opts.hooks && opts.hooks.overrode) opts.hooks.overrode(o, r.event); }
      E.save();
      if (doc.outgoing()) E.changed();       // typed while it was out, or fitted over newer words: that goes next
      return r;
    };
    E.undo = redo => {
      if (redo ? doc.redoLocal() : doc.undoLocal()) { render(); E.changed(); notify(redo ? SAYS.redo : SAYS.local); return "local"; }
      if (redo) return null;
      const ev = doc.sent.pop();
      if (ev && opts.hooks && opts.hooks.undoSent) { opts.hooks.undoSent(ev); notify(SAYS.desk(ev)); return "desk"; }
      notify(SAYS.none); return null;
    };
    E.receive = (text, version) => {
      if (composing) { queued = [text, version]; return null; }        // the input method's words first
      const r = doc.receive(text, version);
      if (r.kind === "fitted") {
        notify("the desk's words changed while you typed (someone else's edit): fitted over yours; your unsent words are kept" + (r.dropped ? `; ${r.dropped} undo step(s) that touched their words are gone` : ""));
        render(); E.changed();
      } else if (r.kind === "conflict") { render(); E.save(); if (r.theirs) notify("CONFLICT: someone changed the words you are typing in. Yours are kept, unsent: Keep mine (sends yours over theirs) or Take theirs"); }
      else if (r.kind === "adopted") { render(); E.save(); }
      else if (r.kind === "confirmed") { E.save(); if (doc.dirty) E.changed(); }     // the words on screen are already these
      else if (doc.dirty && doc.version != null && !doc.inflight) E.changed();   // a version learnt: unsent words can go
      return r;
    };
    E.compose = on => {
      composing = on;
      if (!on && queued) { const q = queued; queued = null; E.receive(q[0], q[1]); }
    };
    // another window of this person changed these unsent words (the viewer's draft is the person's, Sable): the same
    // words here, this window's caret carried over them; nothing is sent from here for it (the typing window sends)
    // Typed in both windows at once: the other's edits are fitted over this window's (same words: kept apart and said)
    E.adopt = (text, base, version) => {
      if (composing || doc.conflict || text == null || text === doc.text) return false;
      let f;
      if (!doc.dirty || base == null || base !== doc.base) {
        if (doc.dirty && base != null && base !== doc.base) { notify("typed in two of your windows at once, on words the desk has moved since: this window keeps its own; the desk will order them"); return false; }
        f = { text, sel: fit(doc.text, text, doc.text, doc.sel).sel };
      } else {
        f = fit(doc.base, text, doc.text, doc.sel);
        if (f.conflict) { notify("typed in two of your windows at once, in the same words: this window keeps its own; look at both before sending"); return false; }
      }
      doc.text = f.text; doc.sel = f.sel || doc.sel;
      if (base != null) { doc.base = base; if (version != null) doc.version = version; }
      render(); E.save(); return true;
    };
    E.resolve = which => { if (!doc.resolve(which)) return false; render(); E.changed(); notify(which === "mine" ? "kept yours: sending it over theirs" : "took theirs: your unsent words are gone"); return true; };
    return E;
  }

  // the conflict bar, drawn by the module above its text (an honest mark: never silently)
  function conflictBar(E) {
    const bar = document.createElement("div"); bar.className = "te-conflict"; bar.setAttribute("role", "alert"); bar.hidden = true;
    const say = document.createElement("span"), mine = document.createElement("button"), theirs = document.createElement("button");
    mine.type = theirs.type = "button"; mine.textContent = "Keep mine"; theirs.textContent = "Take theirs";
    mine.onclick = () => E.resolve("mine"); theirs.onclick = () => E.resolve("theirs");
    bar.append(say, mine, theirs);
    return { bar, show() {
      const c = E.doc.conflict; bar.hidden = !c;
      if (c) {
        const s = c.seen;
        say.textContent = s ? `Someone changed these words while you typed: “${clip(s.was)}” — theirs: “${clip(s.theirs)}”, yours (unsent): “${clip(s.mine)}”.`
          : "These unsent words were typed on a version not shown here (a kept draft): keep them over the text now, or take the text now.";
        bar.title = c.theirs;
      }
    } };
  }
  const clip = s => { s = String(s || "").replace(/\s+/g, " ").trim(); return s.length > 160 ? s.slice(0, 157) + "…" : s; };
  if (typeof document !== "undefined") {
    const st = document.createElement("style");
    st.textContent = `.te-conflict{display:flex;flex-wrap:wrap;gap:.5em;align-items:center;margin:0 0 .5em;padding:.45em .7em;border-radius:.4em;
      border:1px solid var(--t-mark,#B4571C);background:color-mix(in srgb,var(--t-mark,#B4571C) 12%,transparent);font-size:.9em}
      .te-conflict[hidden]{display:none}.te-conflict button{font:inherit;cursor:pointer}`;
    document.head.append(st);
  }

  // ---- the Markdown surface: a document drawn live (moved here from markdown.js, a5820) --------------------------
  function create(opts) {
    const M = globalThis.Markdown;
    const root = document.createElement("div"); root.className = "md-doc";
    const wrapEl = document.createElement("div"); wrapEl.className = "te-wrap"; wrapEl.append(root);
    // media (a6452): the pictures the scene showed for these words, which a ![picture](path) may draw in its place
    let ctx = { links: opts.links || {}, things: opts.things || {}, media: opts.media || [] }, raw = false, active = new Set(), lit = opts.light || [];
    if (opts.hint) root.dataset.hint = opts.hint;
    const ed = !!opts.editable;
    if (ed) { root.contentEditable = "true"; root.spellcheck = true; root.setAttribute("role", "textbox"); root.setAttribute("aria-multiline", "true"); }
    const focused = () => document.activeElement === root;
    const src = () => E.doc.text;
    const sel = () => {
      const s = getSelection(); if (!s.rangeCount || !root.contains(s.anchorNode)) return null;
      const a = M.offsetOf(root, src(), s.anchorNode, s.anchorOffset), f = M.offsetOf(root, src(), s.focusNode, s.focusOffset);
      return { a: Math.min(a, f), b: Math.max(a, f), back: f < a };
    };
    const linesOf = (a, b) => { const st = M.starts(src()), set = new Set(); let l = 0; while (l + 1 < st.length && st[l + 1] <= a) l++; set.add(l); while (l + 1 < st.length && st[l + 1] <= b) set.add(++l); return set; };
    const place = (a, b = a) => {
      const s = getSelection(), [n1, o1] = M.pointAt(root, src(), a), [n2, o2] = M.pointAt(root, src(), b);
      try { s.setBaseAndExtent(n1, o1, n2, o2); } catch (e) { /* a point that moved away */ }
    };
    // each drawn line carries an id the control screen reads (Sable c5977 (3)): the part, then the line
    const name = () => { if (!opts.key) return; for (const c of root.children) { const l = c.dataset.l ?? c.dataset.from; if (l != null) c.id = `part:${opts.key}::${l}`; } };
    function paint(a, b) {
      active = ed && focused() && a != null ? linesOf(a, b) : new Set();
      M.draw(root, src(), ctx, active, raw);
      if (!raw) M.lightUp(root, src(), lit, opts.lightClass);
      name(); bar && bar.show();
      if (a != null && focused()) place(a, b);
    }
    const render = () => { const [a, b] = E.doc.sel; paint(focused() ? a : null, b); };
    const E = common(opts, render);
    const bar = ed ? conflictBar(E) : null;
    if (bar) wrapEl.prepend(bar.bar);
    // one edit of the person's, through the Doc: drawn again, the caret put back by its count of characters
    function change(e, how) {
      if (!e) return;
      E.doc.edit(e.a, e.b, e.s, how, e.sel || (e.at != null ? [e.at, e.at] : null));
      const [a, b] = E.doc.sel; paint(a, b); E.changed(); complete();
    }
    // the words highlighted here, as the source says them (marks and all), so a comment quotes the text's own words
    const picked = () => { const r = sel(); return r && r.b > r.a ? src().slice(r.a, r.b) : null; };
    const anchor = () => { const r = sel(); return r ? { item: opts.item || null, ...E.doc.anchor(r.a, r.b) } : null; };
    const setLights = l => { const want = JSON.stringify(l || []); if (want === JSON.stringify(lit)) return; lit = l || []; const r = ed && focused() ? sel() : null; paint(r ? r.a : null, r ? r.b : null); };

    // [[ asks the world what may be linked (hooks.pick, else opts.titles); the choice is written [[id|title]]
    let pop = null, popAt = 0, popPick = 0, popHits = [];
    function closePop() { if (pop) pop.remove(); pop = null; }
    function complete() {
      const titles = (opts.hooks && opts.hooks.pick) ? null : opts.titles;
      const r = sel(); if (!r || r.a !== r.b || !(titles || (opts.hooks && opts.hooks.pick))) return closePop();
      const [ls] = M.lineAround(src(), r.a), m = /\[\[([^\[\]|\n]{0,60})$/.exec(src().slice(ls, r.a));
      if (!m) return closePop();
      popAt = r.a - m[1].length - 2;
      const q = m[1].toLowerCase().trim();
      popHits = (titles ? titles.filter(t => !q || t.title.toLowerCase().includes(q) || t.id === q)
        .sort((x, y) => (y.title.toLowerCase().startsWith(q) - x.title.toLowerCase().startsWith(q)) || x.title.length - y.title.length) : opts.hooks.pick(q)).slice(0, 8);
      popPick = Math.min(popPick, Math.max(0, popHits.length - 1));
      if (!pop) { pop = document.createElement("div"); pop.className = "md-pop"; pop.setAttribute("role", "listbox"); document.body.append(pop);
        pop.addEventListener("mousedown", e => { e.preventDefault(); const d = e.target.closest("[data-i]"); if (d) choose(+d.dataset.i); }); }
      const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
      pop.replaceChildren(...(popHits.length ? popHits.map((t, i) => { const d = document.createElement("div"); d.dataset.i = i; d.setAttribute("role", "option"); d.setAttribute("aria-selected", String(i === popPick)); d.innerHTML = `<span>${esc(t.title)}</span><small>${esc(t.kind || "")} ${esc(t.id)}</small>`; return d; })
        : [Object.assign(document.createElement("div"), { className: "md-none", textContent: q ? `no document called “${m[1]}”: keep typing for a link to a title` : "type a title" })]));
      const rr = getSelection().getRangeAt(0).getBoundingClientRect();
      pop.style.left = Math.min(rr.left, innerWidth - 360) + "px"; pop.style.top = (rr.bottom + 6) + "px";
    }
    function choose(i) {
      const t = popHits[i]; if (!t) return;
      const r = sel(), end = src().slice(r.a, r.a + 2) === "]]" ? r.a + 2 : r.a, s = `[[${t.id}|${t.title}]]`;
      closePop(); change({ a: popAt, b: end, s, at: popAt + s.length }, "link");
    }
    function follow(target) {
      const named = (ctx.things || {})[target];                  // a6109: a bare id, named by the scene
      if (named && named.open) return opts.hooks && opts.hooks.follow && opts.hooks.follow(named.open, named.name);
      const hit = (ctx.links || {})[target];
      if (!hit || !hit.id) return opts.hooks && opts.hooks.notify && opts.hooks.notify(`nothing is called “${target}” yet`);
      opts.hooks && opts.hooks.follow && opts.hooks.follow(hit.id, hit.title);
    }
    root.addEventListener("click", e => {
      const box = e.target.closest(".md-check");
      if (box && ed) { e.preventDefault(); change(M.toggle(src(), +box.dataset.check), "key"); E.flush(); return; }
      const wl = e.target.closest(".md-wl"), emb = e.target.closest(".md-embed[data-id]"), a = e.target.closest("a.md-a");
      const line = (wl || a) && M.lineOf(root, wl || a), shown = !line || !line.classList.contains("md-active");
      if (emb && (!ed || !e.altKey)) { e.preventDefault(); return follow(emb.closest(".md-widget").dataset.src.replace(/^\s*!\[\[|\]\]\s*$/g, "").split("|")[0].split("#")[0].trim()); }
      // a link whose marks are hidden is followed; on the line being written a click places the caret (Ctrl+click follows)
      if (wl && (shown || e.ctrlKey || e.metaKey)) { e.preventDefault(); return follow(wl.dataset.target); }
      if (a && (shown || e.ctrlKey || e.metaKey) && /^https?:/.test(a.dataset.href || "")) { e.preventDefault(); window.open(a.dataset.href, "_blank", "noopener"); return; }
      const w = e.target.closest(".md-widget");
      if (w && ed) { root.focus(); const at = M.starts(src())[+w.dataset.from] || 0; E.doc.sel = [at, at]; paint(at, at); }
    });
    const api = {
      el: wrapEl, doc: E.doc, src, picked, anchor, lights: setLights, raw: () => raw, state: () => E.doc.state(),
      receive: (t, v) => E.receive(t, v), flush: () => E.flush(), resolve: w => E.resolve(w), adopt: (t, b, v) => E.adopt(t, b, v),
      composing: () => E.composing(),
      titles(t) { opts.titles = t; },
      links(l, th) { ctx = { ...ctx, links: l || {}, things: th || {} }; const r = focused() ? sel() : null; paint(r ? r.a : null, r ? r.b : null); },
      // compatibility with the painter's old document part: set(words, links, things) draws the words as the desk's
      set(t, l, th) { if (l) ctx = { ...ctx, links: l, things: th || ctx.things }; if (t != null) E.receive(t, E.doc.version); else render(); },
      press(key) {
        const k = key.split("+").pop().toLowerCase(), r = sel() || { a: E.doc.sel[0], b: E.doc.sel[1] };
        if (k === "e") { raw = !raw; return paint(focused() ? r.a : null, focused() ? r.b : null); }
        if (k === "s") return E.flush();
        if (!focused() || !ed) return;
        if (k === "b") return change(M.wrap(src(), r.a, r.b, "**", "**"), "key");
        if (k === "i") return change(M.wrap(src(), r.a, r.b, "*", "*"), "key");
        if (k === "k") return change(M.link(src(), r.a, r.b), "key");
        if (k === "z") return E.undo(false);
      },
    };
    if (!ed) { paint(null); return api; }

    // a change the browser made with no beforeinput first (document.execCommand fires none in Chrome; the painter's key
    // queue uses it) is read back from the line it went into, as a composition's words are, so the drawing never
    // drifts from the source
    // (every beforeinput the module takes is prevented, so an input event is always one it did not make)
    function readBack(l, how) {
      const line = l != null && root.querySelector(`:scope > [data-l="${l}"]`); if (!line) return false;
      const st = M.starts(src()), end = src().indexOf("\n", st[l]), now = M.textNodes(line).map(t => t.data).join("").replace(/\n$/, "");
      const s0 = st[l], old = src().slice(s0, end < 0 ? src().length : end);
      const s = getSelection(), caret = s.rangeCount && line.contains(s.focusNode) ? M.offsetOf(root, src(), s.focusNode, s.focusOffset) : s0 + now.length;
      if (now !== old) E.doc.edit(s0, s0 + old.length, now, how, [caret, caret]);
      return now !== old;
    }
    root.addEventListener("input", e => {
      if (E.composing() || e.isComposing) return;
      const s = getSelection(), line = s.anchorNode && M.lineOf(root, s.anchorNode);
      if (line && line.dataset.l != null && readBack(+line.dataset.l, "type")) { const [a, b] = E.doc.sel; paint(a, b); E.changed(); }
      else render();                                            // what cannot be read back is drawn again from the source
    });
    root.addEventListener("beforeinput", e => {
      if (E.composing() || e.inputType === "insertCompositionText") return;
      const r0 = sel(); if (!r0) return;
      const tr = e.getTargetRanges && e.getTargetRanges()[0];
      const r = tr ? (() => { const a = M.offsetOf(root, src(), tr.startContainer, tr.startOffset), b = M.offsetOf(root, src(), tr.endContainer, tr.endOffset); return { a: Math.min(a, b), b: Math.max(a, b) }; })() : r0;
      const t = e.inputType;
      e.preventDefault();
      if (t === "insertText" || t === "insertReplacementText" || t === "insertFromPaste" || t === "insertFromDrop" || t === "insertFromYank") {
        const data = (e.data != null ? e.data : e.dataTransfer && e.dataTransfer.getData("text/plain")) || "";
        return change({ a: r.a, b: r.b, s: data.replace(/\r\n?/g, "\n") }, t === "insertText" ? "type" : "paste");
      }
      if (t === "insertParagraph" || t === "insertLineBreak") return pop && popHits.length ? choose(popPick) : change(M.enter(src(), r0.a, r0.b), "key");
      if (t.startsWith("delete")) {
        let { a, b } = r;
        if (a === b) { if (t.includes("Backward")) a = Math.max(0, a - 1); else b = Math.min(src().length, b + 1); }
        if (t === "deleteContentBackward" && r0.a === r0.b) { const u = M.unmark(src(), r0.a); if (u) return change(u, "del"); }
        return change({ a, b, s: "" }, "del");
      }
      if (t === "historyUndo") return E.undo(false);
      if (t === "historyRedo") return E.undo(true);
      if (t === "formatBold") return change(M.wrap(src(), r0.a, r0.b, "**", "**"), "key");
      if (t === "formatItalic") return change(M.wrap(src(), r0.a, r0.b, "*", "*"), "key");
    });
    // an input method's words (IME): the browser writes them into the drawn line; nothing is drawn again, sent or
    // received while it does (the desk's words wait); at its end the line is read back as one edit
    let composeLine = null;
    root.addEventListener("compositionstart", () => {
      const r = sel(); const line = getSelection().anchorNode && M.lineOf(root, getSelection().anchorNode);
      composeLine = line && line.dataset.l != null ? +line.dataset.l : (r ? linesOf(r.a, r.a).values().next().value : null);
      E.compose(true); E.save();
    });
    root.addEventListener("compositionend", () => {
      const l = composeLine; composeLine = null;
      readBack(l, "compose");
      E.compose(false);
      const [a, b] = E.doc.sel; paint(a, b); E.changed();
    });
    root.addEventListener("keydown", e => {
      if (pop) {
        if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); popPick = (popPick + (e.key === "ArrowDown" ? 1 : popHits.length - 1)) % Math.max(1, popHits.length); return complete(); }
        if (e.key === "Tab" && popHits.length) { e.preventDefault(); return choose(popPick); }
        if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); return closePop(); }
      }
      const r = sel(); if (!r) return;
      const k = shortcut(e);
      if (k) {
        const act = {
          "Ctrl+e": () => { raw = !raw; paint(r.a, r.b); }, "Ctrl+s": () => E.flush(), "Ctrl+Enter": () => E.flush(),
          "Ctrl+b": () => change(M.wrap(src(), r.a, r.b, "**", "**"), "key"), "Ctrl+i": () => change(M.wrap(src(), r.a, r.b, "*", "*"), "key"),
          "Ctrl+k": () => change(M.link(src(), r.a, r.b), "key"),
          "Ctrl+z": () => E.undo(false), "Ctrl+y": () => E.undo(true), "Shift+Ctrl+z": () => E.undo(true),
        }[k];
        if (act) { e.preventDefault(); act(); }
        return;
      }
      if (e.ctrlKey || e.metaKey || e.altKey || E.composing()) return;
      if (e.key === "Tab") { e.preventDefault(); return change(M.indent(src(), r.a, r.b, e.shiftKey), "key"); }
      if (e.key === "Escape") { e.preventDefault(); root.blur(); }
    });
    root.addEventListener("copy", e => { const r = sel(); if (!r || r.a === r.b) return; e.preventDefault(); e.clipboardData.setData("text/plain", src().slice(r.a, r.b)); });
    root.addEventListener("cut", e => { const r = sel(); if (!r || r.a === r.b) return; e.preventDefault(); e.clipboardData.setData("text/plain", src().slice(r.a, r.b)); change({ a: r.a, b: r.b, s: "" }, "del"); });
    // a dropped capture asks the world (hooks.capture): where it was dropped, as an anchor, and what it carries
    root.addEventListener("dragover", e => { if ([...(e.dataTransfer && e.dataTransfer.types || [])].includes("application/x-agora-capture")) e.preventDefault(); });
    root.addEventListener("drop", e => {
      const data = e.dataTransfer && e.dataTransfer.getData("application/x-agora-capture"); if (!data) return;
      e.preventDefault();
      if (opts.hooks && opts.hooks.capture) opts.hooks.capture(anchor() || { item: opts.item || null, ...E.doc.anchor() }, data);
    });
    // the caret moving shows the marks of the lines it is on, opens a table it enters, and is kept (this window's)
    let was = "";
    const moved = () => {
      if (!focused() || E.composing()) return;
      const r = sel(); if (!r) return;
      E.doc.sel = r.back ? [r.b, r.a] : [r.a, r.b]; E.save();
      const now = [...linesOf(r.a, r.b)].join(",");
      if (now === was) return; was = now;
      const next = linesOf(r.a, r.b), widgetTouched = [...root.children].some(c => c.dataset.from != null && [...next].some(l => l >= +c.dataset.from && l <= +c.dataset.to));
      const leftWidget = [...active].some(l => { const w = M.read(src().split("\n")).lines[l]; return w && w.w != null; });
      if (widgetTouched || leftWidget || raw) return paint(r.a, r.b);
      for (const c of root.children) if (c.dataset.l != null) c.classList.toggle("md-active", next.has(+c.dataset.l));
      active = next;
      if (pop) complete();
    };
    document.addEventListener("selectionchange", moved);
    root.addEventListener("focus", () => { was = ""; setTimeout(() => { if (!sel()) { const [a, b] = E.doc.sel; place(a, b); } moved(); }, 0); });
    root.addEventListener("blur", () => { closePop(); was = ""; active = new Set(); for (const c of root.querySelectorAll(".md-line.md-active")) if (!raw) c.classList.remove("md-active"); if (M.read(src().split("\n")).widgets.length) paint(null); });
    api.focus = () => { root.focus(); const [a, b] = E.doc.sel; place(a, b); };
    paint(null);
    return api;
  }

  // ---- the plain surface: a textarea the browser keeps (a composer, a comment box, the find box) -----------------
  // The browser makes each change (so input methods, AltGr, spelling and the platform's keys behave as everywhere);
  // the module reads each change back as an edit of its Doc, so undo, the keeper, composition and the seam are the
  // same as a document's. Enter's meaning (send, or a new line) stays the customer's.
  function attach(input, opts = {}) {
    const render = () => { if (input.value !== E.doc.text) input.value = E.doc.text; const [a, b] = E.doc.sel; if (typeof document === "undefined" || document.activeElement === input) try { input.setSelectionRange(Math.min(a, b), Math.max(a, b)); } catch (e) {} };
    const E = common({ ...opts, text: opts.text != null ? opts.text : input.value }, render);
    if (input.value !== E.doc.text) input.value = E.doc.text;
    const selNow = () => [input.selectionStart, input.selectionEnd];
    let lastType = "";
    input.addEventListener("beforeinput", e => {
      lastType = e.inputType;
      if (e.inputType === "historyUndo" || e.inputType === "historyRedo") { e.preventDefault(); E.undo(e.inputType === "historyRedo"); }
    });
    input.addEventListener("input", e => {
      if (e.isComposing || E.composing()) return;           // read at the composition's end
      E.doc.became(input.value, selNow(), /^insertText$/.test(lastType) ? "type" : /^delete/.test(lastType) ? "del" : "paste");
      E.changed();
    });
    input.addEventListener("compositionstart", () => { E.compose(true); });
    input.addEventListener("compositionend", () => { E.doc.became(input.value, selNow(), "compose"); E.compose(false); E.changed(); });
    input.addEventListener("keydown", e => {
      const k = shortcut(e);
      if (k === "Ctrl+z") { e.preventDefault(); E.undo(false); }
      else if (k === "Ctrl+y" || k === "Shift+Ctrl+z") { e.preventDefault(); E.undo(true); }
    });
    input.addEventListener("select", () => { E.doc.sel = selNow(); E.save(); });
    input.addEventListener("keyup", () => { E.doc.sel = selNow(); });
    input.addEventListener("mouseup", () => { E.doc.sel = selNow(); E.save(); });
    return { el: input, doc: E.doc, src: () => E.doc.text, state: () => E.doc.state(), receive: (t, v) => E.receive(t, v), flush: () => E.flush(),
      composing: () => E.composing(), adopt: (t, b, v) => E.adopt(t, b, v),
      resolve: w => E.resolve(w), anchor: () => ({ item: opts.item || null, ...E.doc.anchor(input.selectionStart, input.selectionEnd) }),
      picked: () => input.selectionEnd > input.selectionStart ? input.value.slice(input.selectionStart, input.selectionEnd) : null,
      // the customer set the box's words (a send cleared it, Discard): the desk's words now, nothing unsent
      reset(text, version) { E.doc.base = E.doc.text = text || ""; E.doc.version = version ?? E.doc.version; E.doc.undo = []; E.doc.redo = []; E.doc.conflict = null; E.doc.sel = [E.doc.text.length, E.doc.text.length]; render(); E.save(); } };
  }

  const TextEdit = { Doc, diff, fit, apply, shortcut, create, attach, SAYS };
  globalThis.TextEdit = TextEdit;
  if (typeof module !== "undefined") module.exports = TextEdit;
})();
