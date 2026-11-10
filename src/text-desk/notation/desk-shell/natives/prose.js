// natives/prose.js : the first native. OWNER: Moss. A caret in a value the world does not have yet.
// Placed by a lens as `native prose` on a part with `text` and `on settle do <command>`: opaque inside,
// obliged outside. What `publish` sends IS what a text-only inhabitant reads about this hole.
// Host: Natives.prose(el, n, host) -> {update(n), release()}; host.send(n, line, why), host.publish(key, lines).
window.Natives = window.Natives || {};
window.Natives.prose = (el, node, host) => {
  const SETTLE = 2500;                                    // the settle law, in the lens one day; here a constant
  let n = node, base = n.text || "", armed = 0, timer = null, sel = null, shown = n.rev;
  const act = (n.acts || []).find(a => a.on === "settle") || (n.acts || []).find(a => a.on === "edit");
  const heading = (/section="([^"]*)"/.exec(act ? act.line : "") || [])[1] || null;
  const where = heading ? `§${heading}` : "this text";
  const clock = t => new Date(t).toTimeString().slice(0, 8);
  const words = s => (String(s).trim().match(/\S+/g) || []).length;
  const cmd = v => act ? act.line.replace("$value", String(v).replace(/"/g, "'")) : null;

  el.contentEditable = "plaintext-only"; el.spellcheck = false; el.textContent = base; el.dataset.native = "prose";

  function mark() {                                        // caret/selection in the material's coordinates, never pixels
    const s = document.getSelection();
    if (!s || !s.anchorNode || !el.contains(s.anchorNode)) { sel = null; return publish(); }
    const r = s.getRangeAt(0), pre = r.cloneRange();
    pre.selectNodeContents(el); pre.setEnd(r.startContainer, r.startOffset);
    const at = pre.toString().length, t = r.toString();
    sel = { at, len: t.length, quote: t.slice(0, 24) };
    publish();
  }

  function shape() {                                       // the draft as SHAPE: content is the person's
    const v = el.textContent;
    if (!armed || v === base) return null;
    const s = (v.match(/[.!?](\s|$)/g) || []).length, d = words(v) - words(base);
    return `${d >= 0 ? "+" : ""}${d}w, ${words(v)}w total, ${s} sentence${s === 1 ? "" : "s"}`
      + (/\w$/.test(v) ? ", ends mid-word" : "");
  }

  function publish() {                                     // all this hole says of itself; it does nothing absent here
    const r = el.getBoundingClientRect(), d = shape();
    const lines = [
      `native prose · ${Math.round(r.width)}x${Math.round(r.height)} · opaque inside`,
      `=shows ${n.item} rev ${shown} · ${where} · ${words(base)}w`,
      sel ? `=caret ${where} char ${sel.at} · ${host.actor}`
          + (sel.len ? ` · =select ${sel.at}-${sel.at + sel.len} "${sel.quote}"` : "")
          : `=caret nowhere · nobody is typing here`,
      d ? `=draft unsettled ${d} · since ${clock(armed)}` : `=draft none · settled at rev ${shown}`,
      d ? `=settles at ${clock(armed + SETTLE)}, or when the caret leaves, or on ctrl+enter` : `=settles n/a`,
      n.rev !== shown ? `!fence ${n.item} moved to rev ${n.rev} under this draft · held, not lost` : `=fence ok at rev ${shown}`,
      `acts settle: ${cmd("$value") || "(none: this lens gave me no settle command)"}`,
      `acts escape: (nothing — an abandoned draft leaves no trace)`,
    ];
    host.publish(n.key, lines);
  }

  function settle(why) {
    clearTimeout(timer);
    const v = el.textContent;
    if (!armed || v === base || !act) { armed = 0; return publish(); }
    armed = 0; base = v; shown = n.rev;
    host.send(n, cmd(v), why);                            // the command published above, character for character
    publish();
  }

  const arm = () => { armed = armed || Date.now(); clearTimeout(timer);
                      timer = setTimeout(() => settle("the pause"), SETTLE); publish(); };
  el.addEventListener("input", () => { arm(); mark(); });
  for (const e of ["keyup", "mouseup", "focus"]) el.addEventListener(e, mark);
  el.addEventListener("blur", () => { settle("leaving the text"); sel = null; publish(); });
  el.addEventListener("keydown", e => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); settle("you asked"); }
    if (e.key === "Escape") { e.preventDefault(); el.textContent = base; armed = 0; clearTimeout(timer); publish(); }
  });
  publish();
  return {
    update(fresh) {                                       // the painter repainted: the world may have moved
      n = fresh;
      if (!armed) { base = n.text || ""; shown = n.rev; if (el.textContent !== base) el.textContent = base; }
      publish();                                          // if armed, keep the draft and let !fence say so
    },
    release() { clearTimeout(timer); host.publish(n.key, null); },
  };
};
