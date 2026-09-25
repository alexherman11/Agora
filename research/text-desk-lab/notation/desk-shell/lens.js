// lens.js : the generic painter. OWNER: Pike (OWNERS.md, 25 Sep).
// LINE BUDGET (Wren's rule): 150 lines, ever. Each new scene word costs lines here; at the ceiling a word must
// be removed to add one. This is the guard against growing into a worse HTML that cannot be argued around.
// It paints a scene tree from /api/scene and sends gestures back as desk command lines. It knows the scene
// vocabulary (layout, role, text, clamp, box, acts) and nothing else: no app, no kind, no colour, no size.
// If a lens needs something this file cannot paint, the answer is a new scene word argued for on the studio
// desk, never a special case here.
(async () => {
  const q = new URLSearchParams(location.search);
  const session = q.get("session") || "lens", who = q.get("as") || "alex", lens = q.get("lens") || "notes";
  const paint = document.getElementById("paint"), said = document.getElementById("said");
  Style.install(await (await fetch("style/calm.style")).text(), q.get("theme") || undefined);

  let last = "", sceneAt = 0, def = null, text = "", notice = "", hold = null, repainting = false;
  // Pike (continuity run 1): a refused edit's words vanished, or stayed on screen looking saved. Now they stay where
  // they were typed, marked unsent, until the person sends them again (Enter) or drops them (Escape). Per viewer, never the world.
  const drafts = new Map(), show = () => { said.textContent = (notice ? notice + "\n\n" : "") + text; };
  const mark = (el, d) => { el.classList.toggle(Style.roleClass("mark"), !!d); if (d) el.dataset.unsent = d.why; else delete el.dataset.unsent; };

  // Astra: a gesture acts on the generation that was painted. It carries what was observed; the desk's fence judges that.
  async function send(n, line, draft) {
    const observed = { item: n.item, rev: n.rev, at: sceneAt, def: n.def, defpart: n.defpart, reads: n.reads };   // Jeff (a308): per part and per aspect
    const r = await (await fetch("/api/do", { method: "POST", body: JSON.stringify({ session, as: who, line, observed }) })).json();
    const t = r.text || r.error || "";
    hold = null;
    if (r.error || t.startsWith("ERR")) {
      // Pike (run 1): this refusal used to be overwritten by the repaint below (6 of 7 unseen); it stays until the next gesture.
      notice = (draft !== undefined ? `unsent: "${draft}" (Enter sends it again, Escape drops it)\n` : "") + "refused: " + t;
      if (draft !== undefined) drafts.set(n.key, { text: draft, why: t.split("\n").pop() });   // the repaint marks it
    } else { notice = ""; drafts.delete(n.key); }
    show();
    await refresh(true);
  }

  // Iris, Astra: replacing the whole tree destroyed a reader's selection whenever anyone else acted. A part whose
  // painting did not change keeps its element; only what changed is made again. Pike (run 1): the signature is what is
  // painted, not what a gesture carries (rev, reads, members, def move with every event); those are refreshed in place.
  let kept = new Map(), next = new Map();
  function make(n) {
    const old = kept.get(n.key); n.def = def;
    if (old && hold === n.key) { next.set(n.key, old); return old.el; }   // the part in a person's hands is not repainted under them
    const sig = JSON.stringify([n.role, n.layout, n.box, n.text, n.clamp, n.absent, n.acts, n.kids.map(k => k.key), drafts.get(n.key)]);
    if (old && old.sig === sig) { old.el._n = n;
      const els = n.kids.map(make), same = els.length === old.el.children.length && els.every((e, i) => old.el.children[i] === e);
      // a part with its own words cannot have its children swapped without losing the words: make it again
      if (same || n.text === null) {
        // place only what differs: re-inserting an untouched sibling would drop the reader's selection inside it
        els.forEach((e, i) => { if (old.el.children[i] !== e) old.el.insertBefore(e, old.el.children[i] || null); });
        while (old.el.children.length > els.length) old.el.lastChild.remove();
        next.set(n.key, old); return old.el;
      }
    }
    const el = document.createElement("div");
    el._n = n;
    if (n.absent) el.hidden = true;
    next.set(n.key, { el, sig });
    el.dataset.key = n.key;      // Iris: with the key on the paint, agreement is a join, not two trees walked side by side
    if (n.role) el.className = Style.roleClass(n.role);
    if (n.layout) el.classList.add("l-" + n.layout);
    if (n.box) { el.classList.add("boxed"); Object.assign(el.style, { left: n.box[0] + "px", top: n.box[1] + "px", width: n.box[2] + "px", height: n.box[3] + "px" }); }
    if (n.text !== null) {
      const d = drafts.get(n.key);
      if (d && d.text === n.text) drafts.delete(n.key);
      el.textContent = drafts.has(n.key) ? d.text : n.text;
      mark(el, drafts.get(n.key));
      if (n.clamp) { el.classList.add("clamp"); el.style.webkitLineClamp = n.clamp; }
    }
    for (const a of n.acts) {
      if (a.on === "click") el.addEventListener("click", e => {     // a click knows where it landed: $x $y in this part's own space
        if (e.target !== el && a.line.includes("$x")) return;
        const r = el.getBoundingClientRect();
        send(el._n, a.line.replace("$x", Math.round(e.clientX - r.left + el.scrollLeft)).replace("$y", Math.round(e.clientY - r.top + el.scrollTop)));
      });
      if (a.on === "edit") {
        el.contentEditable = "plaintext-only"; el.addEventListener("focus", () => { if (!repainting) hold = n.key; });
        el.addEventListener("keydown", e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); el.blur(); }
          if (e.key === "Escape") { drafts.delete(n.key); mark(el, null); el.textContent = el._n.text; notice = ""; show(); el.blur(); } });
        el.addEventListener("blur", () => { if (repainting) return;      // a repaint moved it; the person is still editing it
          // Rook: never show a person text they did not write. Escape for the desk's quoting; do not rewrite.
          const raw = el.textContent.trim(), v = raw.replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\r?\n/g, "\\n");
          if (raw && raw !== el._n.text) send(el._n, a.line.replace("$value", () => v), raw); else hold = null;
        });
      }
      if (a.on === "drag" && n.box) {
        // Pike (run 1, S9): only a pointer could move a card. It is a Tab stop now: arrows move it (Shift: bigger steps),
        // Enter or leaving puts it down, Escape puts it back. Pointer and keys take, move and put through the same three steps.
        el.dataset.drag = "1"; el.tabIndex = 0;
        let m0 = null, x = 0, y = 0;
        const to = (nx, ny) => { x = Math.max(0, Math.round(nx)); y = Math.max(0, Math.round(ny)); el.style.left = x + "px"; el.style.top = y + "px"; };
        const take = () => { m0 = el._n; hold = n.key; x = m0.box[0]; y = m0.box[1]; };
        const put = back => { const m = m0; m0 = null; if (back) to(m.box[0], m.box[1]);
          if (!back && (x !== m.box[0] || y !== m.box[1])) send(m, a.line.replace("$x", x).replace("$y", y)); else hold = null; };
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
        el.addEventListener("blur", () => { if (m0 && !repainting) put(false); });
      }
    }
    for (const k of n.kids) el.appendChild(make(k));
    return el;
  }

  // Pike (run 1, Alex's workspace): the whole page froze while any part was being edited, so a finished task did not
  // show while he typed. Now everything repaints except the part in hand; focus, caret and selection are put back.
  async function refresh(force) {
    const r = await (await fetch(`/api/scene?session=${encodeURIComponent(session)}&as=${who}&lens=${lens}`)).json();
    const key = JSON.stringify(r.scene || r.refused);
    if (key === last && !force) return;
    last = key; sceneAt = r.events_total; def = (r.scene && r.scene.def) || null;
    if (r.refused) { if (!hold) paint.replaceChildren(); text = "refused: " + r.refused; show(); return; }
    const ed = document.activeElement, s = getSelection(), sel = s.rangeCount ? [s.anchorNode, s.anchorOffset, s.focusNode, s.focusOffset] : null;
    repainting = true; try {
      next = new Map(); const root = make(r.scene); kept = next;
      if (paint.firstChild !== root) paint.replaceChildren(root);
      if (ed && ed !== document.body && ed.isConnected && document.activeElement !== ed) ed.focus();
      if (sel && sel[0].isConnected && sel[2].isConnected) s.setBaseAndExtent(...sel);
    } finally { repainting = false; }
    text = r.text; show(); report();
  }

  // Iris, Lark: only the painter knows what happened. It says so: which clamps bit, what is out of this viewer's view.
  let told = ""; function report() {
    const vp = paint.getBoundingClientRect(), facts = {};
    for (const el of paint.querySelectorAll("[data-key]")) {
      const r = el.getBoundingClientRect(), f = [];
      if (el.classList.contains("clamp") && el.scrollHeight > el.clientHeight + 1) f.push("cut by the clamp");
      if (el.classList.contains("boxed") && el.scrollHeight > el.clientHeight + 1) f.push("contents overflow the box");
      if (el.classList.contains("boxed") && (r.bottom < vp.top || r.top > vp.bottom || r.right < vp.left || r.left > vp.right)) f.push("out of view");
      if (el.dataset.unsent) f.push("unsent draft");
      if (f.length) facts[el.dataset.key] = f.join(", ");
    }
    const body = JSON.stringify({ session, as: who, lens, at: sceneAt, facts,
      viewport: { w: Math.round(vp.width), h: Math.round(vp.height), sx: Math.round(paint.scrollLeft), sy: Math.round(paint.scrollTop) } });
    if (body !== told) { told = body; fetch("/api/observe", { method: "POST", body }); }
  }
  let scrolling; paint.addEventListener("scroll", () => { clearTimeout(scrolling); scrolling = setTimeout(report, 400); });

  await refresh();
  setInterval(() => refresh().catch(() => {}), 1500);   // the server restarting is not an error worth a console line
})();
