// lens.js : the generic painter, by paint kind. OWNER: Pike (OWNERS.md, 25 Sep).
// LINE BUDGET (Wren's rule, counted apart from continuity since a361): 150 lines of vocabulary, a guard against growing
// into a worse HTML. Under review: the codex team reports Alex rejected the cap [read: their BRIDGE-NOTES], and pike-8
// proposes admission tests in its place (a general scene contract, an honest text account, one addressed action path,
// preserved viewer state, performance, reuse across unlike tasks, not composable from existing kinds, semantics and
// look only through paint.semantic and style roles). Until Alex decides, lines over 150 are named here: the send's
// in-flight token and lost-answer handling (4 lines). viewer.js holds continuity.
// It paints the scene's painter contract (pike-7 section 6: key, paint, acts, fence, kids) and sends gestures back as
// desk command lines. It knows paint kinds, roles and interaction primitives, and nothing else: no app, no kind, no
// colour, no size. `fence` is opaque: returned with a gesture, never drawn, never compared.
(async () => {
  const q = new URLSearchParams(location.search);
  const session = q.get("session") || "lens", who = q.get("as") || "alex", lens = q.get("lens") || "notes";
  const paint = document.getElementById("paint"), said = document.getElementById("said");
  document.body.dataset.inspector = q.get("inspect") === "0" ? "off" : "on";   // codex team: inspect=0 gives the painter the full width
  // F7: the style is world data. The lens names it (def.style_name); the painter installs it from the world and again
  // whenever its revision changes, so restyling is a desk edit and repaints live. calm, the seed file, until a lens says.
  let styled = "";
  async function restyle(name, rev) {
    if (styled === name + "@" + rev) return;
    const st = await (await fetch(`/api/style?session=${encodeURIComponent(session)}&name=${encodeURIComponent(name)}`)).json();
    if (st.text != null) { try { Style.install(st.text, q.get("theme") || undefined); styled = name + "@" + rev; } catch (e) { V.show("style " + name + " refused: " + (e.message || e)); } }
    // Alex, 30 Sep (scrollbars that fit the theme): a style with a `scrollbar` token draws its own bars (lens.html)
    document.documentElement.toggleAttribute("data-bars", !!Style.token("scrollbar"));
    // Alex, 7 Oct ('not everything should be highlighted text boxes'): a style with a `focus` token (a colour) draws
    // the ring round the text being written in that colour; the sheet's own colour makes it nothing
    document.documentElement.toggleAttribute("data-focus", !!Style.token("focus"));
  }
  const V = Viewer(session, who, lens, said, document.getElementById("status"));
  let last = "", sceneAt = 0, def = null;

  // a key's gesture (TEXT.key): sent as the text's own, and the answer comes back so the caret can follow what was made
  async function sendKey(n, line) {
    const observed = { ...(n.fence || {}), at: sceneAt, def }, gesture = V.gesture(n.key, false);
    let r;
    try { r = await (await fetch("/api/do", { method: "POST", body: JSON.stringify({ session, as: who, line, observed, gesture }) })).json(); }
    catch (e) { V.show(`the answer was lost (${e.message})`); last = ""; await refresh(true); return null; }
    const t = r.text || r.error || ""; if (r.error || t.startsWith("ERR")) V.show(t);
    last = ""; await refresh(true); return r;
  }

  // Astra: a gesture acts on the generation that was painted. It carries what was observed; the desk's fence judges that.
  async function send(n, line, draft, more) {
    const token = V.beginSend(n.key); if (!token) return;       // one send per part at a time (viewer.js)
    const observed = { ...(n.fence || {}), at: sceneAt, def, ...more }, gesture = V.gesture(n.key, draft !== undefined);   // a1008
    let r;
    try { r = await (await fetch("/api/do", { method: "POST", body: JSON.stringify({ session, as: who, line, observed, gesture }) })).json(); }
    catch (e) {      // a1008: the next scene is painted even if it is unchanged, so the kept draft can be sent again (same id)
      last = ""; V.answered(n.key, `the answer was lost (${e.message}); whether it was done is unknown until the view repaints`, draft, token); return refresh(true);
    }
    const t = r.text || r.error || ""; V.answered(n.key, r.error || t.startsWith("ERR") ? t : null, draft, token);
    await refresh(true);
    // a1008, the cause of e1851/e1852: typed words live in the element, not in its signature, so a composer whose
    // line was sent was reused still showing it, and its next blur sent it again. Once no draft holds them, they go.
    const k = kept.get(n.key), p = k && k.el._n.paint;
    if (p && p.text != null && draft !== undefined && !V.drafts.has(n.key) && k.el.textContent !== (p.runs ? p.runs.map(x => x.text).join("") : p.text)) {
      if (p.runs) runs(k.el, p.runs); else k.el.textContent = p.text; V.mark(k.el, n.key);
    }
  }

  // Iris, Astra: a part whose painting did not change keeps its element; only what changed is made again. Pike (run 1):
  // the signature is what is drawn (paint, the shapes of the acts, the kids' keys), never the fence.
  let kept = new Map(), next = new Map();
  function make(n) {
    const old = kept.get(n.key), p = n.paint || {};
    if (old && V.hold === n.key) { next.set(n.key, old); return old.el; }   // the part in a person's hands is not repainted under them
    const sig = JSON.stringify([p, n.acts.map(a => [a.on, a.line, a.part, a.label]), n.kids.map(k => k.key), V.drafts.get(n.key)]);
    if (old && old.sig === sig) { old.el._n = n; if (V.reuse(old.el, n.kids.map(make), p.text != null)) { tracks(old.el); next.set(n.key, old); return old.el; } }
    const el = document.createElement("div");
    el._n = n; el.hidden = !!p.absent; el.dataset.key = n.key;   // Iris: with the key on the paint, agreement is a join
    next.set(n.key, { el, sig }); if (p.why) el.dataset.why = p.why;
    const role = p.role || (p.state || p.cut ? "cut" : null);    // a bind that is not live, or a clamp's leaf, says so in `cut`
    if (role) el.className = Style.roleClass(role);
    if (p.kind === "frame") el.classList.add("l-" + p.flow);
    if (p.box) { el.classList.add("boxed"); Object.assign(el.style, { left: p.box[0] + "px", top: p.box[1] + "px", width: p.box[2] + "px", height: p.box[3] + "px" }); }
    if (p.text != null) {
      const words = V.words(n.key, p.text, n.fence);
      if (p.runs && words === p.text) runs(el, p.runs); else el.textContent = words;
      V.mark(el, n.key);
      if (p.wrap === "verbatim") el.classList.add("t-verbatim");
      if (p.clamp) { el.classList.add("clamp"); el.style.webkitLineClamp = p.clamp; }
    }
    if (p.semantic) semantic(el, p.semantic);                 // before frames: a fold's own state wins over the default
    if (p.kind === "frame") frames(el, n, p);
    // a weight, as a track is; in a row, a share also fills the row's height (lens.html: .l-row > [data-share]). 1 Oct:
    // Sable's a1266 made the Board's lanes a row of shares (was grid 1 1 1), rows align on baselines, and every lane
    // shrank to its title, so each lane's scrolling list was 0 high and Alex's Board looked empty
    if (p.share != null) { el.style.flex = `${p.share} 1 0`; el.style.minWidth = el.style.minHeight = "0"; el.dataset.share = "1"; }
    // a grid given a share is bounded, so it divides its height among its rows and its cells fill them; a cell with
    // `scroll` then scrolls inside the window instead of the page growing (Alex, 29 Sep: the window is bounded)
    if (p.share != null && p.tracks) { el.dataset.bounded = "1"; el.style.gridAutoRows = "minmax(0, 1fr)"; el.style.alignItems = "stretch"; }
    if (p.lines) { el.style.minHeight = p.lines[0] + "lh"; if (p.lines[1]) el.style.maxHeight = p.lines[1] + "lh"; el.style.overflowY = "auto"; }
    if (p.hint) el.dataset.hint = p.hint;       // Juniper: what an empty input is for; paint only, never content
    if (p.peek) el.dataset.peek = "1";          // a1032: stays shown while its parent is folded (lens.html)
    for (const a of n.acts) {
      // Alex, 7 Oct (buttons on top of a document): a button that presses a key, or names $focus, acts on the text the
      // caret is in. It must not take the caret, and its gesture is the text's own: sent with what that text showed.
      const onText = a.on === "click" && (a.line.startsWith("press ") || a.line.includes("$focus"));
      if (onText) { el.dataset.tool = "1"; el.addEventListener("mousedown", e => e.preventDefault()); }
      if (onText) el.addEventListener("click", () => {
        const t = TEXT.last && TEXT.last.isConnected ? TEXT.last : null;
        if (!t) return V.show("put the caret in a text first: this button acts on the text being written");
        if (a.line.startsWith("press ")) { t.focus(); return TEXT.press(t, a.line.slice(6)); }
        send(t._n, a.line.replace("$focus", () => (t._n.fence || {}).item || ""));
      });
      else if (a.on === "click") el.addEventListener("click", e => {     // a click knows where it landed: $x $y in this part's own space
        if (e.target !== el && a.line.includes("$x")) return;
        const r = el.getBoundingClientRect();
        send(el._n, a.line.replace("$x", Math.round(e.clientX - r.left + el.scrollLeft)).replace("$y", Math.round(e.clientY - r.top + el.scrollTop)));
      });
      if (a.on === "edit") edits(el, n, a);
      if (a.on === "drag" && p.box) drags(el, n, a);
      if (a.on === "carry") carries(el, n);
      if (a.on === "drop") { el.dataset.drop = a.part; el._drop = a; }
      if (a.on === "menu") el.dataset.menu = "1";                 // its entries are read from el._n when the menu opens
    }
    for (const k of n.kids) el.appendChild(make(k));
    if (p.tracks) tracks(el);
    return el;
  }

  // pike-7 section 9, lowered by Jeff (5bb7f7f): a grid's tracks hold its direct children in fixed slots, and a folded
  // child's track shrinks to its handle; gap, scroll and measure on any frame; fold is the lens's default, overridden by
  // this viewer only, never an event. The fold handle is the one control the painter draws itself (role tool).
  function frames(el, n, p) {
    if (p.gap != null) el.style.gap = typeof p.gap === "number" ? p.gap + "px" : p.gap[0] === "/" ? `calc(var(--t-gap) / ${p.gap.slice(1)})` : `calc(${p.gap.slice(1)} * var(--t-gap))`;   // F10: steps of the style's gap
    if (p.scroll && p.scroll !== "none") { el.style.overflow = "auto"; el.dataset.scroll = p.scroll; }
    if (p.measure) { el.style.maxWidth = p.measure; el.style.marginInline = "auto"; }
    if (!n.acts.some(a => a.on === "fold")) return;
    // Alex, 29 Sep: a floating fold is a menu. Its open contents are drawn over the page below the handle, it opens for
    // a moment (not remembered), and Escape or a press outside closes it. Its handle's look is role `menu`, a plain
    // fold's is `fold`, each over `tool`, so a style that names neither keeps the tool look.
    const float = !!(p.fold && p.fold.float);
    const h = document.createElement("button"); h.type = "button";
    h.className = Style.roleClass("tool") + " " + Style.roleClass((p.fold && p.fold.handle) || (float ? "menu" : "fold"));
    h.setAttribute("aria-label", (p.fold && p.fold.label) || n.part || "section");
    const dflt = p.fold ? p.fold.folded : !!p.folded;          // Jeff 75e39d8: fold is {folded, label}; 5bb7f7f emitted folded: true
    const lab = (p.fold && p.fold.label) || "";                  // the lens's handle label is drawn, not only announced
    const set = f => { el.dataset.folded = f ? "1" : ""; el.setAttribute("aria-expanded", String(!f)); h.textContent = (f ? "▸" : "▾") + (lab ? " " + lab : ""); h.setAttribute("aria-expanded", String(!f)); if (el.parentElement) tracks(el.parentElement); };
    if (float) { el.classList.add("l-float"); el._close = () => set(true); }
    el._fold = f => { V.fold(n.key, f); set(f); };
    const group = p.fold && p.fold.group;
    if (group) el.dataset.foldGroup = group;
    h.addEventListener("click", () => {
      if (float) { set(el.dataset.folded !== "1"); return; }
      const f = !V.folded(n.key, dflt); V.fold(n.key, f); set(f);
      // `fold ... group <name>` (Alex, 30 Sep): opening one folds its open siblings in the same group, an accordion
      if (!f && group && el.parentElement)
        [...el.parentElement.children].forEach(s => { if (s !== el && s.dataset.foldGroup === group && s.dataset.folded !== "1" && s._fold) s._fold(true); });
    });
    el.prepend(h); set(float ? dflt : V.folded(n.key, dflt));
  }
  const closeFloats = keep => document.querySelectorAll('.l-float:not([data-folded="1"])').forEach(m => { if (!m.contains(keep)) m._close(); });
  document.addEventListener("pointerdown", e => closeFloats(e.target));
  document.addEventListener("keydown", e => { if (e.key === "Escape") closeFloats(null); });

  // Alex, 29 Sep ("native right click behavior"): a part's own menu, from its `on menu "<label>" do ...` entries, opened
  // by a right-click or the menu key anywhere on it (the innermost part that has entries). Text being edited, a part
  // with no entries, and a right-click with Shift keep the browser's own menu. An entry sends its line as a click does.
  let pop = null;
  function closeMenu(refocus) { if (!pop) return; const back = pop._from; pop.remove(); pop = null; if (refocus && back && back.focus) back.focus(); }
  document.addEventListener("contextmenu", e => {
    const t = e.target instanceof Element ? e.target : null;
    if (e.shiftKey || !t || t.isContentEditable || t.closest("input, textarea")) return;
    const el = t.closest("[data-menu]");
    const entries = el && paint.contains(el) && el._n ? el._n.acts.filter(a => a.on === "menu") : [];
    if (!entries.length) return;
    e.preventDefault(); closeMenu();
    const box = document.createElement("div"); box.id = "menu-pop"; box.setAttribute("role", "menu");
    box.className = Style.roleClass("sheet") + " " + Style.roleClass("popup");
    for (const a of entries) {
      const b = document.createElement("button"); Object.assign(b, { type: "button", textContent: a.label });
      b.className = Style.roleClass("tool") + " " + Style.roleClass("menu.item"); b.setAttribute("role", "menuitem");
      b.addEventListener("click", () => { closeMenu(); send(el._n, a.line); });
      box.append(b);
    }
    document.body.append(box);
    let x = e.clientX, y = e.clientY;
    if (!x && !y) { const r = el.getBoundingClientRect(); x = r.left + 8; y = r.top + 8; }        // the menu key: at the part
    box.style.left = Math.max(0, Math.min(x, innerWidth - box.offsetWidth - 4)) + "px";
    box.style.top = Math.max(0, Math.min(y, innerHeight - box.offsetHeight - 4)) + "px";
    box._from = document.activeElement; pop = box; box.querySelector("button").focus();
  });
  document.addEventListener("pointerdown", e => { if (pop && !pop.contains(e.target)) closeMenu(); }, true);
  document.addEventListener("scroll", () => closeMenu(), true);
  addEventListener("blur", () => closeMenu());
  document.addEventListener("keydown", e => {
    if (!pop) return;
    if (e.key === "Escape") { closeMenu(true); e.preventDefault(); e.stopPropagation(); return; }
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      const bs = [...pop.querySelectorAll("button")], i = bs.indexOf(document.activeElement);
      bs[(i + (e.key === "ArrowDown" ? 1 : -1) + bs.length) % bs.length].focus(); e.preventDefault();
    }
  }, true);
  // paint.semantic (pike-8 section 4): what assistive technology is told, on the node's one element. A press leaf is a
  // button: a Tab stop that Enter and Space activate (the codex team's finding: a clickable div is not a control).
  function semantic(el, s) {
    el.setAttribute("role", s.role);
    if (s.label) el.setAttribute("aria-label", s.label);
    for (const k of ["expanded", "value", "min", "max"]) if (s[k] != null) el.setAttribute(k === "expanded" ? "aria-expanded" : `aria-value${k === "value" ? "now" : k}`, String(s[k]));
    if (s.role === "button") {
      el.tabIndex = 0;
      el.addEventListener("keydown", e => { if ((e.key === "Enter" || e.key === " ") && e.target === el) { e.preventDefault(); el.click(); } });
    }
  }
  function tracks(el) {
    const p = el._n && el._n.paint; if (!p || !p.tracks) return;
    const kids = [...el.children].filter(c => c.dataset.key);
    el.style.gridTemplateColumns = p.tracks.map((t, i) => kids[i] && kids[i].dataset.folded ? "auto" : t === "fit" ? "max-content" : /gap$/.test(t) ? `calc(${parseFloat(t)} * var(--t-gap))` : `minmax(0, ${t})`).join(" ");
    kids.forEach((c, i) => { if (i < p.tracks.length) c.style.gridColumn = String(i + 1); });
  }

  function edits(el, n, a) {
    el.contentEditable = "plaintext-only";
    // Juniper a559 (870ec2d): a part with runs is read as runs and edited as its source, so what is written is what is
    // drawn. Pike (S28): swapping on focus put the caret at the end, because focus comes before the click places it, and
    // the delimiters appearing moved the words under the pointer. So the swap waits for the first change (a key that
    // writes, a paste, a cut), and maps the caret and selection the browser has already placed to the same characters.
    el.addEventListener("focus", () => { TEXT.last = el; if (!V.repainting) V.hold = n.key; });
    const toSource = () => { if (el._runs) source(el); };
    el._toSource = toSource;
    el.addEventListener("keydown", e => TEXT.key(el, e));
    el.addEventListener("keydown", e => { if ((e.ctrlKey || e.metaKey) && !e.altKey && e.key.length === 1) MARKS.key(el, e, toSource); });
    el.addEventListener("keydown", e => { if (!e.ctrlKey && !e.metaKey && (e.key.length === 1 || /^(Backspace|Delete|Enter)$/.test(e.key))) toSource(); });
    const multi = () => { const pp = el._n.paint; return pp.commit ? pp.commit === "ctrl-enter" : !!pp.lines && (pp.lines[1] == null || pp.lines[1] > 1); };
    // Pike (S29): a pasted line break showed on screen and vanished from what was sent ("CampgroundHighway"). The value is
    // read as it is drawn (innerText), and a one-line part takes a paste as one line, which it shows before it is sent.
    el.addEventListener("paste", e => {
      toSource(); if (multi()) return;
      e.preventDefault(); document.execCommand("insertText", false, (e.clipboardData.getData("text/plain") || "").split(String.fromCharCode(10)).map(l => l.trim()).join(" "));
    });
    el.addEventListener("cut", toSource);
    el.addEventListener("input", () => V.typed(n.key, el.innerText, { key: n.key, fence: el._n.fence }));
    el.addEventListener("keydown", e => {
      if (e.key === "Enter" && !e.shiftKey && (!multi() || e.ctrlKey || e.metaKey)) { e.preventDefault(); el.blur(); }   // commit is emitted (75e39d8)
      if (e.key === "Escape") { e.preventDefault(); if (!V.drop(n.key)) return; V.mark(el, n.key); el.textContent = el._n.paint.text; el.blur(); }
    });
    el.addEventListener("blur", () => {
      if (V.repainting) return;      // a repaint moved it; the person is still editing it
      // Rook: never show a person text they did not write. Escape for the desk's quoting; do not rewrite.
      const raw = el.innerText.trim(), v = raw.replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\r?\n/g, "\\n");
      const seen = V.editOrigin(n.key, el._n); if (!seen) { V.hold = null; return; }   // pike-8: never a fresher fence than was shown
      if (raw !== (el._n.paint.text || "").trim()) send(seen, a.line.replace("$value", () => v), raw); else { V.hold = null; V.drop(n.key); if (el._n.paint.runs) runs(el, el._n.paint.runs); }
    });
  }

  // a text's keys (Alex, 7 Oct: 'Enter should create a new line, tab should indent'). A lens gives a text `on key
  // Enter|Tab|Shift+Tab|Backspace do ...`; the command may name $head and $tail, the words either side of the caret.
  // The words typed and not yet sent go with it (the command is told them), so nothing is sent twice. Afterwards the
  // caret follows the text: into the same part of a thing the command made, or onto the end of the one above when
  // this one is gone, or it stays.
  const TEXT = {
    last: null,
    esc: v => v.replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\r?\n/g, "\\n"),
    caret(el) {                               // the caret as a count of characters of the source
      const sel = getSelection(); if (!sel.rangeCount || !el.contains(sel.anchorNode)) return null;
      const r = document.createRange(); r.selectNodeContents(el); r.setEnd(sel.focusNode, sel.focusOffset);
      return { at: r.toString().length, wide: !sel.isCollapsed };
    },
    put(el, at) {                             // the caret at a count of characters (past the end: the end)
      el.focus(); if (el._toSource) el._toSource();
      const t = el.firstChild, sel = getSelection();
      if (t && t.nodeType === 3) sel.setBaseAndExtent(t, Math.min(at, t.data.length), t, Math.min(at, t.data.length)); else sel.selectAllChildren(el), sel.collapseToStart();
    },
    press(el, key) { if (el._toSource) MARKS.key(el, { key: key.split("+").pop().toLowerCase(), preventDefault() {} }, el._toSource); },
    key(el, e) {
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      const name = (e.shiftKey ? "Shift+" : "") + e.key, a = el._n.acts.find(x => x.on === "key" && x.label === name);
      if (!a) return;
      el._toSource(); const c = this.caret(el); if (!c) return;
      if (name === "Backspace" && (c.at > 0 || c.wide)) return;        // only at the very start does it join
      e.preventDefault(); e.stopImmediatePropagation();
      const src = el.innerText.replace(/\n$/, ""), seen = V.editOrigin(el._n.key, el._n) || el._n, key = el._n.key, item = (el._n.fence || {}).item;
      const before = [...paint.querySelectorAll("[contenteditable]")].filter(x => x._n && x._n.part === el._n.part);
      const prev = before[before.indexOf(el) - 1], prevLen = prev ? (prev._n.paint.text || "").length : 0, prevKey = prev && prev._n.key;
      const whole = /[$](head|tail)/.test(a.line);       // a command told the words takes them: the draft is not sent again
      if (whole) { V.drop(key); V.hold = null; }
      const line = a.line.replace("$head", () => this.esc(src.slice(0, c.at))).replace("$tail", () => this.esc(src.slice(c.at)));
      sendKey(seen, line).then(r => {
        const made = r && (r.created || [])[0], find = k => paint.querySelector(`[data-key="${CSS.escape(k)}"]`);
        const same = find(key), born = made && item && find(key.split(item).join(made));
        if (born) this.put(born, 0);
        else if (!same && prevKey && find(prevKey)) this.put(find(prevKey), prevLen);
        else if (same) this.put(same, name === "Backspace" ? 0 : c.at);
      });
    },
  };

  // marks (Editor board a3486, 7 Oct): the words a text part carries marks in, when its lens says `marks`. One table
  // holds each mark's element, the source written around it and its key, so a new mark is one more line here and one
  // more arm in scene.marks_of. Read, a mark is drawn; edited, it is its source, as a code run is.
  const MARKS = {
    kinds: { strong: { tag: "strong", wrap: ["**", "**"], key: "b" }, stress: { tag: "em", wrap: ["*", "*"], key: "i" },
             both: { tag: "strong", look: "t-mark-strong t-mark-stress" }, link: { tag: "a", wrap: ["[", "](https://)"], key: "k" } },
    draw(r) {
      const m = document.createElement(this.kinds[r.mark].tag); m.className = "t-mark " + (this.kinds[r.mark].look || "t-mark-" + r.mark); m.textContent = r.text;
      if (r.mark === "link") { m.dataset.href = r.href; m.title = r.href + "  (Ctrl+click opens it)"; }
      return m;
    },
    // Ctrl+B and the like, in the source: wrap what is selected, or take the mark off when it is already there
    key(el, e, toSource) {
      const kind = Object.values(this.kinds).find(k => k.key === e.key.toLowerCase());
      if (!kind || !el._n.paint.marks) return false;
      e.preventDefault(); toSource();
      const sel = getSelection(), t = el.firstChild;
      if (!t || t.nodeType !== 3 || !sel.rangeCount || !el.contains(sel.anchorNode)) return true;
      const a = Math.min(sel.anchorOffset, sel.focusOffset), f = Math.max(sel.anchorOffset, sel.focusOffset), src = t.data, [w0, w1] = kind.wrap;
      const count = (i, d) => { let c = 0; while (src[i] === "*") { c++; i += d; } return c; };
      const stars = Math.min(count(a - 1, -1), count(f, 1));   // the stars around the words: 1 stress, 2 strong, 3 both
      const on = kind.tag !== "a" && (w0 === "**" ? stars >= 2 : stars % 2 === 1);
      if (on) sel.setBaseAndExtent(t, a - w0.length, t, f + w1.length);
      const words = src.slice(a, f) || (kind.tag === "a" ? "link" : "");
      document.execCommand("insertText", false, on ? words : w0 + words + w1);
      // the words stay selected, so the same key again takes the mark off; a new link leaves its address selected to type over
      el.normalize(); const t2 = el.firstChild, from = on ? a - w0.length : a + w0.length;
      if (t2 && t2.nodeType === 3) {
        if (kind.tag === "a") sel.setBaseAndExtent(t2, a + words.length + 3, t2, a + words.length + 3 + "https://".length);
        else sel.setBaseAndExtent(t2, from, t2, from + words.length);
      }
      return true;
    },
  };
  document.addEventListener("click", e => {
    const a = e.target.closest && e.target.closest(".t-mark-link");
    if (!a || !/^https?:/.test(a.dataset.href || "")) return;
    if (a.closest("[contenteditable]") && !(e.ctrlKey || e.metaKey)) return;     // in a text being written, a click places the caret
    e.preventDefault(); window.open(a.dataset.href, "_blank", "noopener");
  });

  // runs inside one text leaf: plain words as text, a code run in its role (a block run keeps its lines, verbatim)
  function runs(el, rs) {
    el._runs = rs;
    el.replaceChildren(...rs.map(r => {
      if (r.mark) return MARKS.draw(r);
      if (!r.role) return document.createTextNode(r.text);
      const s = document.createElement(r.block ? "div" : "span"); s.className = Style.roleClass(r.role);
      if (r.block) s.classList.add("t-verbatim");
      s.textContent = r.text; return s;
    }));
  }
  function source(el) {
    const src = el._n.paint.text, rs = el._runs, kids = [...el.childNodes], sel = getSelection();
    let pos = 0; const starts = rs.map(r => { const i = src.indexOf(r.text, pos); pos = i + r.text.length; return i; });
    const map = (node, off) => {
      if (node === el) return off >= kids.length ? src.length : starts[off];
      const i = kids.findIndex(k => k === node || k.contains(node));
      return i < 0 ? src.length : starts[i] + (node.nodeType === 3 ? off : 0);
    };
    const inside = sel.rangeCount && el.contains(sel.anchorNode) && el.contains(sel.focusNode);
    const a = inside ? map(sel.anchorNode, sel.anchorOffset) : src.length, f = inside ? map(sel.focusNode, sel.focusOffset) : a;
    el._runs = null; el.textContent = src;
    const t = el.firstChild; if (t) sel.setBaseAndExtent(t, Math.min(a, src.length), t, Math.min(f, src.length));
  }

  // drag is geometry: $x $y in the free parent. Pointer and keys take, move and put through the same three steps (S9).
  function drags(el, n, a) {
    el.dataset.drag = "1"; el.tabIndex = 0;
    let m0 = null, x = 0, y = 0;
    const to = (nx, ny) => { x = Math.max(0, Math.round(nx)); y = Math.max(0, Math.round(ny)); el.style.left = x + "px"; el.style.top = y + "px"; };
    const take = () => { m0 = el._n; V.hold = n.key; x = m0.paint.box[0]; y = m0.paint.box[1]; };
    const put = back => {
      const m = m0; m0 = null; if (back) to(m.paint.box[0], m.paint.box[1]);
      if (!back && (x !== m.paint.box[0] || y !== m.paint.box[1])) send(m, a.line.replace("$x", x).replace("$y", y)); else V.hold = null;
    };
    el.addEventListener("pointerdown", e => {
      if (e.target.isContentEditable && e.target !== el) return;
      take(); el.setPointerCapture(e.pointerId);
      const x0 = e.clientX - x, y0 = e.clientY - y, move = m => to(m.clientX - x0, m.clientY - y0);
      const up = () => { el.removeEventListener("pointermove", move); el.removeEventListener("pointerup", up); put(false); };
      el.addEventListener("pointermove", move); el.addEventListener("pointerup", up);
    });
    el.addEventListener("keydown", e => {
      const d = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] }[e.key], step = e.shiftKey ? 40 : 8;
      if (e.target !== el || !(d || m0)) return;
      if (d) { e.preventDefault(); if (!m0) take(); to(x + d[0] * step, y + d[1] * step); }
      if (e.key === "Enter" || e.key === "Escape") { e.preventDefault(); put(e.key === "Escape"); }
    });
    el.addEventListener("blur", () => { if (m0 && !V.repainting) put(false); });
  }

  // carry is relation (pike-3): pick a thing up, put it down on a part that says `on drop <its part>`; the receiver says
  // what that means, and both are fenced. Pointer: press, move, release over a receiver. Keys: Space takes it, Tab
  // reaches the receivers that accept it, Enter puts it down, Escape cancels. Nothing is sent onto the receiver it came from.
  let carrying = null; const receivers = part => [...paint.querySelectorAll(`[data-drop="${CSS.escape(part)}"]`)];
  const over = r => { const c = Style.roleClass("tool.on"); if (carrying.over) carrying.over.classList.remove(c); carrying.over = r; if (r) r.classList.add(c); };
  // a receiver is judged on what it meant at pick-up (pike-3), though the view keeps repainting while a card is in the air
  function take(el) { const rs = receivers(el._n.part); carrying = { el, n: el._n, over: null, seen: new Map(rs.map(r => [r.dataset.key, r._n.fence])) }; V.hold = el._n.key; rs.forEach(r => { r.tabIndex = 0; }); }
  function put(r) {
    const c = carrying; if (!c) return;
    over(null); carrying = null; c.el.style.transform = ""; c.el.style.opacity = ""; c.el.style.animation = "";
    if (c.ghost) { c.ghost.remove(); document.body.style.userSelect = ""; }
    receivers(c.n.part).forEach(x => x.removeAttribute("tabindex"));
    if (!r || r.contains(c.el)) { V.hold = null; c.el.focus(); return; }
    const f = c.seen.get(r.dataset.key) || r._n.fence || {};
    send({ key: r._n.key, fence: f }, r._drop.line, undefined, { carried: c.n.fence, receiver: f });
  }
  // a copy of the card follows the pointer, fixed to the window, so a lane that scrolls (and so clips) can't hide it
  function ghost(el) {
    const b = el.getBoundingClientRect(), g = el.cloneNode(true);
    g.querySelectorAll("[data-key]").forEach(x => x.removeAttribute("data-key")); g.removeAttribute("data-key");
    Object.assign(g.style, { position: "fixed", left: b.left + "px", top: b.top + "px", width: b.width + "px", margin: 0,
      pointerEvents: "none", zIndex: 30, opacity: .92, animation: "none", boxShadow: "0 6px 18px rgba(0,0,0,.25)" });
    document.body.appendChild(g); return g;
  }
  function carries(el, n) {
    el.tabIndex = 0; el.dataset.carry = n.part;
    el.addEventListener("pointerdown", e => {
      // 30 Sep (Alex: dragging cards didn't work): the card's title is its fold handle, a button covering most of the
      // card, and a press on a control was never a carry. Now a press becomes a carry only once it moves a few pixels,
      // from anywhere on the card, the title included; a press that doesn't move stays that control's click. The right
      // button opens the menu, and a press in text being typed stays typing.
      if (e.target.isContentEditable || e.button !== 0) return;
      const x0 = e.clientX, y0 = e.clientY, pid = e.pointerId;
      let c = null;
      const at = m => document.elementsFromPoint(m.clientX, m.clientY).find(x => x.dataset && x.dataset.drop === n.part) || null;
      const move = m => {
        if (m.pointerId !== pid) return;
        if (!c) {
          if (Math.hypot(m.clientX - x0, m.clientY - y0) < 5 || carrying) return;
          take(el); c = carrying; c.ghost = ghost(el); el.style.opacity = ".35"; el.style.animation = "none";   // a1140: the dim wins over a pulse
          document.body.style.userSelect = "none"; getSelection().removeAllRanges();
        }
        c.ghost.style.transform = `translate(${m.clientX - x0}px, ${m.clientY - y0}px)`; over(at(m));
      };
      const up = m => {
        if (m.pointerId !== pid) return;
        document.removeEventListener("pointermove", move); document.removeEventListener("pointerup", up);
        document.removeEventListener("pointercancel", up);
        if (!c) return;
        // the release after a carry is not a click on the control it began on (it would fold or start the card)
        const eat = k => { k.stopPropagation(); k.preventDefault(); };
        window.addEventListener("click", eat, { capture: true, once: true });
        setTimeout(() => window.removeEventListener("click", eat, { capture: true }), 0);
        put(m.type === "pointercancel" ? null : at(m));
      };
      document.addEventListener("pointermove", move); document.addEventListener("pointerup", up);
      document.addEventListener("pointercancel", up);
    });
    el.addEventListener("keydown", e => { if (e.key === " " && e.target === el && !carrying) { e.preventDefault(); take(el); } });
  }
  document.addEventListener("keydown", e => {
    if (!carrying) return;
    const r = document.activeElement && document.activeElement.dataset.drop === carrying.n.part ? document.activeElement : null;
    if (e.key === "Escape") { e.preventDefault(); put(null); }
    else if (e.key === "Enter" && r) { e.preventDefault(); put(r); }
    else if (e.key === "Tab") setTimeout(() => over(document.activeElement.dataset.drop === carrying?.n.part ? document.activeElement : null));
  });

  let held = null;                               // the last scene answer painted, carried over a reload for new painter code
  async function refresh(force) {
    const have = !force && /^(\d+-\d+|g[0-9a-f]+)$/.test(last) ? `&have=${last}` : "";      // a build name, never the fallback text
    const r = await (await fetch(`/api/scene?session=${encodeURIComponent(session)}&as=${who}&lens=${lens}&view=painter${have}`)).json();
    if (r.same) return;                          // deskd: nothing changed since the build this page has
    return paintAnswer(r, force);
  }
  async function paintAnswer(r, force) {
    const key = r.gen || JSON.stringify(r.scene || r.refused);      // deskd names each scene by its content (a1505); comparing 700 KB was the fallback
    if (key === last && !force) return;
    last = key; sceneAt = r.events_total; def = (r.scene && r.scene.def) || r.def || null; if (r.scene) held = r;
    await restyle((def && def.style_name) || "calm", (def && def.style_rev) || "seed");
    // 30 Sep (Alex: the Desktop kept going blank over the node budget): a refused scene keeps the last good paint on
    // screen and says why, as a refused style keeps the last good look; a page with nothing painted yet shows the reason
    if (r.refused) { V.show("refused: " + r.refused + (paint.firstChild ? "\n(showing the last good paint until the lens compiles again)" : "")); return; }
    V.keep(() => { next = new Map(); const root = make(r.scene); kept = next; if (paint.firstChild !== root) paint.replaceChildren(root); });
    V.show(r.text); report();
  }

  const report = () => V.report(paint, sceneAt, carrying ? { [carrying.n.key]: "carried" + (carrying.over ? " over " + carrying.over.dataset.key : "") } : {}, q.get("share") === "attention",
    def && { frame: def.frame, style: def.style_rev || "seed" });
  // a1473: boxes change without a new scene (a fold, the window, the fonts arriving), so those report too
  let scrolling; const later = () => { clearTimeout(scrolling); scrolling = setTimeout(report, 400); };
  paint.addEventListener("scroll", later); addEventListener("resize", later); paint.addEventListener("click", later);
  if (document.fonts) document.fonts.ready.then(later);

  // 30 Sep: a page that loads while deskd restarts (it reloads itself for new code, just as the keeper restarts the
  // server) got a failed first fetch; unguarded, it threw before the repaint loop below was set, and stayed blank
  // a1505: a page reloaded for new painter code (Alex pressed the quiet line, or the scene shape changed) carries its
  // view: the scene it showed (painted at once, before anything is fetched), each frame's scroll, focus and caret, and
  // the floats that were open. Only this tab reads it.
  const carryKey = `lens-carry:${session}:${who}:${lens}`;
  let carried = null; try { carried = JSON.parse(sessionStorage.getItem(carryKey) || "null"); sessionStorage.removeItem(carryKey); } catch (e) { carried = null; }
  if (carried && carried.answer) {
    await paintAnswer(carried.answer, true).catch(() => {});
    const q = k => paint.querySelector(`[data-key="${CSS.escape(k)}"]`);
    (carried.floats || []).forEach(k => { const el = q(k), h = el && el.querySelector(":scope > button"); if (h && el.dataset.folded === "1") h.click(); });
    if (carried.places) V.place(carried.places);
    const f = carried.focus && q(carried.focus.key);
    if (f) { f.focus(); const t = f.firstChild; if (t && t.nodeType === 3 && carried.focus.caret != null) getSelection().collapse(t, Math.min(carried.focus.caret, t.length)); }
  }
  await refresh().catch(() => {});
  setInterval(() => refresh().catch(() => {}), 1500);   // the server restarting is not an error worth a console line
  // a1505: the door (door.py) holds one long connection per page. A world event repaints at once (the 1.5 s poll stays
  // for what changes without an event: the clock, the house); the door's news feeds the quiet line (door.js).
  if (window.EventSource) {
    let soon = null;
    const es = new EventSource(`/door/stream?session=${encodeURIComponent(session)}`);
    es.addEventListener("world", () => { clearTimeout(soon); soon = setTimeout(() => refresh().catch(() => {}), 60); });
    es.addEventListener("door", m => { try { if (window.DoorLine) DoorLine.show(JSON.parse(m.data)); } catch (e) {} });
    es.onerror = () => { if (es.readyState === EventSource.CLOSED) es.close(); };   // no door (a bare deskd): the polls carry on
  }
  // live building (tier 2). a1505: a landing that changes only Python reloads nothing; deskd is swapped behind the door
  // and the next scene shows what it changed. When the PAINTER's own files change, the page keeps the painter it has
  // and the quiet line offers the new one ("new screen code: click to use it"); Alex chooses when (Juniper, e3746:
  // reading is not a keystroke, so no pause is safe to reload in). Only when deskd sends a scene shape this lens.js
  // can't read (scene.PAINTER_SHAPE) does the page reload on its own, and the line says why. Either way the reload
  // carries the view (above), and the terminal keeps its lines (term.js).
  const SHAPE = 1;                                  // the scene shape this file reads: scene.PAINTER_SHAPE
  let painter = null, leaving = false;
  function reloadKeeping() {
    const a = document.activeElement, s = getSelection();
    const focus = a && a.dataset && a.dataset.key ? { key: a.dataset.key, caret: s.rangeCount && a.contains(s.focusNode) ? s.focusOffset : null } : null;
    const floats = [...paint.querySelectorAll('.l-float:not([data-folded="1"])')].map(e => e.dataset.key);
    try { sessionStorage.setItem(carryKey, JSON.stringify({ answer: held, places: V.places(), focus, floats })); }
    catch (e) { try { sessionStorage.setItem(carryKey, JSON.stringify({ places: V.places(), focus, floats })); } catch (e2) {} }
    location.reload();
  }
  function versionIs(v) {
    if (v.shape != null && v.shape !== SHAPE) {
      if (leaving) return; leaving = true;
      if (window.DoorLine) DoorLine.note(`the new code sends screens this page can't read (shape ${v.shape}; it reads ${SHAPE}): reloading, keeping your view`);
      return setTimeout(reloadKeeping, 1500);
    }
    const p = v.painter || v.code; if (!p) return;
    if (painter === null) { painter = p; return; }
    if (p === painter) { if (window.DoorLine) DoorLine.note(""); return; }
    // Alex, 7 Oct: "I want painter edits live immediately, at least for now." New screen code loads on its own, keeping
    // the view (reloadKeeping), as soon as the person's hands are free: nothing carried, no part held, no composer with
    // the caret in it. While hands are busy the line says it is waiting, and the next tick asks again. (Until today the
    // line offered a click and the person chose when; Juniper's e3746 argued that reading has no safe pause.)
    const a = document.activeElement, typing = a && a.isContentEditable && paint.contains(a);
    if (carrying || V.hold || typing) { if (window.DoorLine) DoorLine.note("new screen code: it will load when your hands are free"); return; }
    if (leaving) return; leaving = true;
    if (window.DoorLine) DoorLine.note("new screen code: loading it, keeping your view");
    setTimeout(reloadKeeping, 200);
  }
  setInterval(async () => {
    let v; try { v = await (await fetch("/api/version")).json(); } catch (e) { return; }
    versionIs(v);
  }, 5000);
})();
