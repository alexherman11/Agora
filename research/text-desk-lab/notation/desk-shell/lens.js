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

  let last = "", busy = false, sceneAt = 0, def = null;

  // Astra: a gesture acts on the generation that was painted. It carries what was observed; the desk's fence judges that.
  async function send(n, line) {
    const observed = { item: n.item, rev: n.rev, at: sceneAt, def, defpart: n.defpart, reads: n.reads };   // Jeff (a308): fenced per part and per aspect
    const r = await (await fetch("/api/do", { method: "POST", body: JSON.stringify({ session, as: who, line, observed }) })).json();
    const t = r.text || r.error || "";
    if (r.error || t.startsWith("ERR")) said.textContent = "refused: " + t + "\n\n" + said.textContent;
    busy = false;
    await refresh(true);
  }

  // Iris, Astra: replacing the whole tree destroyed a reader's selection whenever anyone else acted. A part whose
  // own facts did not change keeps its element; only what changed is made again.
  let kept = new Map(), next = new Map();
  function make(n) {
    const sig = JSON.stringify({ ...n, kids: n.kids.map(k => k.key) }), old = kept.get(n.key);
    if (old && old.sig === sig) {
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
    if (n.absent) el.hidden = true;
    next.set(n.key, { el, sig });
    el.dataset.key = n.key;      // Iris: with the key on the paint, agreement is a join, not two trees walked side by side
    if (n.role) el.className = Style.roleClass(n.role);
    if (n.layout) el.classList.add("l-" + n.layout);
    if (n.box) { el.classList.add("boxed"); Object.assign(el.style, { left: n.box[0] + "px", top: n.box[1] + "px", width: n.box[2] + "px", height: n.box[3] + "px" }); }
    if (n.text !== null) {
      el.textContent = n.text;
      if (n.clamp) { el.classList.add("clamp"); el.style.webkitLineClamp = n.clamp; }
    }
    for (const a of n.acts) {
      if (a.on === "click") el.addEventListener("click", e => {     // a click knows where it landed: $x $y in this part's own space
        if (e.target !== el && a.line.includes("$x")) return;
        const r = el.getBoundingClientRect();
        send(n, a.line.replace("$x", Math.round(e.clientX - r.left + el.scrollLeft)).replace("$y", Math.round(e.clientY - r.top + el.scrollTop)));
      });
      if (a.on === "edit") {
        el.contentEditable = "plaintext-only";
        el.addEventListener("focus", () => { busy = true; });
        el.addEventListener("keydown", e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); el.blur(); } if (e.key === "Escape") { el.textContent = n.text; el.blur(); } });
        el.addEventListener("blur", () => {
          // Rook: never show a person text they did not write. Escape for the desk's quoting; do not rewrite.
          const v = el.textContent.trim().replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\r?\n/g, "\\n");
          if (v && v !== n.text) send(n, a.line.replace("$value", () => v)); else busy = false;
        });
      }
      if (a.on === "drag" && n.box) {
        el.dataset.drag = "1";
        el.addEventListener("pointerdown", e => {
          if (e.target.isContentEditable && e.target !== el) return;
          busy = true; el.setPointerCapture(e.pointerId);
          const x0 = e.clientX, y0 = e.clientY; let x = n.box[0], y = n.box[1];
          const move = m => { x = Math.max(0, n.box[0] + m.clientX - x0); y = Math.max(0, n.box[1] + m.clientY - y0); el.style.left = x + "px"; el.style.top = y + "px"; };
          const up = () => {
            el.removeEventListener("pointermove", move); el.removeEventListener("pointerup", up);
            if (x !== n.box[0] || y !== n.box[1]) send(n, a.line.replace("$x", Math.round(x)).replace("$y", Math.round(y))); else busy = false;
          };
          el.addEventListener("pointermove", move); el.addEventListener("pointerup", up);
        });
      }
    }
    for (const k of n.kids) el.appendChild(make(k));
    return el;
  }

  async function refresh(force) {
    if (busy && !force) return;
    const r = await (await fetch(`/api/scene?session=${encodeURIComponent(session)}&as=${who}&lens=${lens}`)).json();
    const key = JSON.stringify(r.scene || r.refused);
    if (key === last) return;
    last = key;
    sceneAt = r.events_total;
    def = (r.scene && r.scene.def) || null;
    if (r.refused) { paint.replaceChildren(); said.textContent = "refused: " + r.refused; return; }
    next = new Map();
    const root = make(r.scene);
    kept = next;
    if (paint.firstChild !== root) paint.replaceChildren(root);
    said.textContent = r.text;
    report();
  }

  // Iris, Lark: only the painter knows what happened. It says so: which clamps bit, what is out of this viewer's view.
  let told = "";
  function report() {
    const vp = paint.getBoundingClientRect(), facts = {};
    for (const el of paint.querySelectorAll("[data-key]")) {
      const r = el.getBoundingClientRect(), f = [];
      if (el.classList.contains("clamp") && el.scrollHeight > el.clientHeight + 1) f.push("cut by the clamp");
      if (el.classList.contains("boxed") && el.scrollHeight > el.clientHeight + 1) f.push("contents overflow the box");
      if (el.classList.contains("boxed") && (r.bottom < vp.top || r.top > vp.bottom || r.right < vp.left || r.left > vp.right)) f.push("out of view");
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
