// apps/editor.js : the Text editor. OWNER: Moss.
//
// Material: subjects of kind doc. A page, an outline rail of ## sections that follows the reader, comments in
// the margin, and typing that SETTLES into one command at a pause instead of one per keystroke.
//
// What this app keeps that the world does not have (all of it honestly view state, per the law of the house):
//   which doc is open, scroll position, which section the caret is in, the unsettled draft, and the local
//   moment an event was first seen by this page (the desk's clock is day-granular, so "12s ago" is this
//   page's observation, never the desk's fact, and is printed with ~ wherever it appears).
//
// Two things the desk cannot say yet; both are requested as to-jeff notes and worked around loudly here:
//   1. rewrite is whole-document. A settle therefore rewrites the WHOLE doc even when one section changed.
//   2. a comment cannot name the passage it is about. Every comment is shown "? unanchored" rather than
//      guessed at. Nothing here fakes an anchor in JavaScript.
(() => {
  const CSS = `
  .ed{display:grid;grid-template-columns:184px minmax(0,1fr) 248px;height:100%;background:var(--surface);
      font:14px/1.5 var(--font);color:var(--ink)}
  .ed-rail{border-right:1px solid var(--line);padding:14px 10px;overflow:auto}
  .ed-rail h3{margin:0 0 8px;font:500 11px/1.4 var(--font);color:var(--quiet);letter-spacing:.04em;
      text-transform:uppercase}
  .ed-docs{margin:0 0 16px;padding:0 0 14px;border-bottom:1px solid var(--line)}
  .ed-doc,.ed-sec{display:grid;grid-template-columns:14px 1fr auto;gap:6px;align-items:baseline;
      padding:4px 6px;border-radius:6px;cursor:pointer;color:var(--quiet)}
  .ed-doc:hover,.ed-sec:hover{background:var(--paper)}
  .ed-doc[aria-current=true]{background:var(--paper);color:var(--ink)}
  .ed-sec[data-here=reading]{color:var(--ink)}
  .ed-sec .m{color:var(--accent);font:12px/1.4 ui-monospace,Consolas,monospace}
  .ed-sec .n{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .ed-sec .w{font-size:11px;color:var(--quiet);font-variant-numeric:tabular-nums}
  .ed-where{margin-top:10px;font-size:11px;line-height:1.6;color:var(--quiet)}
  .ed-page{overflow:auto;padding:0 0 120px}
  .ed-sheet{max-width:640px;margin:0 auto;padding:40px 44px}
  .ed-title{font:500 26px/1.25 var(--font);margin:0 0 4px;outline:0}
  .ed-meta{color:var(--quiet);font-size:12px;margin:0 0 28px}
  .ed h2.ed-h{font:500 16px/1.4 var(--font);margin:26px 0 6px;outline:0}
  .ed-body{white-space:pre-wrap;outline:0;min-height:1.7em;margin:0 0 4px}
  .ed-body:focus,.ed-h:focus,.ed-title:focus{box-shadow:-10px 0 0 0 var(--paper),10px 0 0 0 var(--paper);
      background:var(--paper);border-radius:2px}
  .ed-sec-wrap[data-unsettled=true]{box-shadow:-14px 0 0 -12px var(--accent)}
  .ed-margin{border-left:1px solid var(--line);padding:14px 12px;overflow:auto}
  .ed-card{border:1px solid var(--line);border-radius:var(--radius);padding:8px 10px;margin:0 0 8px;
      background:var(--paper)}
  .ed-card .who{font-size:11px;color:var(--quiet);display:flex;gap:6px;align-items:baseline}
  .ed-card .body{margin:4px 0 6px;white-space:pre-wrap}
  .ed-card.resolved{opacity:.55}
  .ed-mark{font:11px/1.4 ui-monospace,Consolas,monospace;color:var(--quiet)}
  .ed-btn{border:0;background:transparent;color:var(--quiet);font:inherit;font-size:12px;padding:3px 7px;
      border-radius:6px;cursor:pointer}
  .ed-btn:hover{background:var(--paper);color:var(--ink)}
  .ed-btn.lead{color:var(--ink)}
  .ed-status{position:sticky;top:0;z-index:2;background:var(--surface);border-bottom:1px solid var(--line);
      padding:6px 14px;font-size:12px;color:var(--quiet);display:flex;gap:12px;align-items:baseline}
  .ed-fence{background:var(--paper);border:1px solid var(--accent);border-radius:var(--radius);
      margin:14px 44px 0;padding:10px 12px}
  .ed-fence b{font-weight:500;color:var(--ink)}
  .ed-fence code{font:12px ui-monospace,Consolas,monospace;color:var(--quiet)}
  .ed-fence .row{display:flex;gap:6px;margin-top:8px;flex-wrap:wrap}
  .ed-empty{padding:40px 44px;color:var(--quiet)}
  `;
  if (!document.getElementById("ed-css")) {
    const s = document.createElement("style"); s.id = "ed-css"; s.textContent = CSS; document.head.appendChild(s);
  }

  const SETTLE_MS = 2500;
  const seenAt = new Map();          // event id -> the local moment this page first saw it (view state, ~ not =)

  const esc = s => String(s).replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
  const q = s => '"' + String(s).replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\n/g, "\\n") + '"';
  const words = s => (String(s || "").trim().match(/\S+/g) || []).length;
  const ago = t => { const d = Math.round((Date.now() - t) / 1000);
    return d < 60 ? d + "s" : d < 3600 ? Math.round(d / 60) + "m" : Math.round(d / 3600) + "h"; };

  // ---- the material, read as sections -------------------------------------------------------------
  function parse(text) {
    const lines = String(text || "").split("\n");
    const secs = [{ name: null, lines: [] }];      // section 0 is the preamble: it has no ## heading
    for (const l of lines) {
      const m = /^##\s+(.*)$/.exec(l);
      if (m) secs.push({ name: m[1], lines: [] }); else secs[secs.length - 1].lines.push(l);
    }
    return secs.map((s, i) => ({ i, name: s.name, body: s.lines.join("\n").replace(/^\n+|\n+$/g, ""),
                                 words: words(s.lines.join(" ")) }));
  }
  const compose = secs => secs.map(s => (s.name === null ? s.body : "## " + s.name + "\n" + s.body))
                              .filter((t, i) => i > 0 || t.trim() !== "").join("\n");

  const docsInWorld = () => Object.values(Desk.snapshot.nodes)
    .filter(n => n.type === "appearance" && Desk.subject(n.subject)?.kind === "doc");

  // ---- per-window state (ctx) ---------------------------------------------------------------------
  let lastDrawn = null;   // if the shell calls text() without the ctx it opened with, answer about the window
  const LONE = {};        // that is actually on screen rather than inventing an empty one
  function state(ctx) {
    if (!ctx || typeof ctx !== "object") ctx = lastDrawn || LONE;
    if (!ctx.ed) ctx.ed = { id: null, secs: null, base: "", rev: null, caret: null, reading: 0,
                            shown: [0, 0], unsettled: false, lastKey: 0, timer: null, fence: null, note: null };
    return ctx.ed;
  }
  function load(st, id) {
    const s = Desk.subject(Desk.node(id).subject);
    st.id = id; st.secs = parse(s.text); st.base = s.text || ""; st.rev = s.rev;
    st.unsettled = false; st.fence = null; st.caret = null; st.reading = 0; st.shown = [0, 0];
  }
  // how many sections the desk itself would count: one per ## heading
  const headings = secs => secs.filter(s => s.name !== null).length;
  const plural = (n, w) => `${n} ${w}${n === 1 ? "" : "s"}`;

  // ---- settling ------------------------------------------------------------------------------------
  function arm(st, host, ctx) {
    st.unsettled = true; st.lastKey = Date.now();
    clearTimeout(st.timer);
    st.timer = setTimeout(() => settle(st, host, ctx, "the pause"), SETTLE_MS);
    status(host, st);
  }

  async function settle(st, host, ctx, why) {
    clearTimeout(st.timer);
    if (!st.unsettled || !st.id) return;
    const text = compose(st.secs);
    if (text === st.base) { st.unsettled = false; status(host, st); return; }
    st.note = `settling on ${why}`; status(host, st);
    // NOT `read ${id}; do rewrite ...`. The stub did that, and it is wrong: `read` refreshes what this
    // actor has seen, so the seen fence can never fire and the other inhabitant's change is overwritten
    // in silence. The fence is the feature. We rewrite straight away, and a refusal is the desk telling
    // us the truth; the draft is held, never dropped.
    const r = await Desk.do(`do rewrite ${st.id} text=${q(text)}`);
    const err = r.error || (/\bstale\b|not looked/i.test(r.text || "") ? r.text : null);
    if (err) {
      st.fence = { err: String(err).split("\n")[0], mine: text, at: Date.now() };
      st.note = null; draw(host, ctx);
      return;
    }
    st.unsettled = false; st.base = text; st.note = null;
    const s = Desk.subject(Desk.node(st.id).subject); if (s) st.rev = s.rev;
    status(host, st);
  }

  // ---- drawing --------------------------------------------------------------------------------------
  function status(host, st) {
    const el = host.querySelector(".ed-status"); if (!el || !st.id) return;
    const s = Desk.subject(Desk.node(st.id).subject); if (!s) return;
    const sec = st.secs[st.caret];
    const bits = [`${st.id} · rev ${s.rev}`,
      st.unsettled
        ? `unsettled in ${secName(sec)} · ${words(sec ? sec.body : "")}w · last key ~${ago(st.lastKey)} ago`
        : `settled`,
      st.note || ""];
    const other = otherTouch.get(st.id);
    if (other) bits.push(`~${other.by}: ${other.verb} here, ${ago(other.seen)} ago`);
    el.textContent = bits.filter(Boolean).join("   ·   ");
  }
  const secName = s => !s ? "(nowhere)" : s.name === null ? "the opening" : "§" + s.i + " " + s.name;

  const otherTouch = new Map();          // appearance id -> {by, verb, seen}; seen is THIS PAGE's clock
  function remember(events) {
    for (const e of events || []) {
      if (!seenAt.has(e.id)) seenAt.set(e.id, Date.now());
      if (e.by === Desk.actor) continue;
      for (const c of e.changed || []) otherTouch.set(c, { by: e.by, verb: e.verb, seen: seenAt.get(e.id) });
    }
  }

  function draw(host, ctx) {
    const st = state(ctx);
    lastDrawn = (ctx && typeof ctx === "object") ? ctx : lastDrawn;
    const list = docsInWorld();
    if (!st.id || !Desk.node(st.id)) { if (list[0]) load(st, list[0].id); }
    host.innerHTML = "";
    host.className = "ed";
    if (!st.id) { const e = document.createElement("div"); e.className = "ed-empty";
      e.textContent = "No documents in this world. A document is a subject of kind doc: "
        + 'do create Shared kind=doc title="Untitled" text="## First section"'; host.append(e); return; }

    const subj = Desk.subject(Desk.node(st.id).subject);
    const rail = document.createElement("div"); rail.className = "ed-rail";
    const mid = document.createElement("div"); mid.className = "ed-page";
    const marg = document.createElement("div"); marg.className = "ed-margin";

    // --- rail: documents, then the outline ---------------------------------------------------------
    const dh = document.createElement("h3"); dh.textContent = "documents";
    const dl = document.createElement("div"); dl.className = "ed-docs";
    list.forEach(n => {
      const row = document.createElement("div"); row.className = "ed-doc";
      row.setAttribute("aria-current", n.id === st.id);
      const t = otherTouch.get(n.id);
      row.innerHTML = `<span class="m">${n.id === st.id ? "▸" : ""}</span><span class="n"></span>`
        + `<span class="w">${t ? "warm" : ""}</span>`;
      row.querySelector(".n").textContent = Desk.title(n.id);
      row.onclick = async () => { if (st.unsettled) await settle(st, host, ctx, "leaving the document");
                                  load(st, n.id); await Desk.do(`read ${n.id}`); draw(host, ctx); };
      dl.append(row);
    });
    const oh = document.createElement("h3"); oh.textContent = "outline";
    rail.append(dh, dl, oh);
    st.secs.forEach(s => {
      const row = document.createElement("div"); row.className = "ed-sec";
      row.dataset.here = st.reading === s.i ? "reading" : "";
      const mark = st.caret === s.i && st.unsettled ? "✎" : st.caret === s.i ? "|" : st.reading === s.i ? "▸" : "";
      row.innerHTML = `<span class="m">${mark}</span><span class="n"></span><span class="w">${s.words}</span>`;
      row.querySelector(".n").textContent = s.name === null ? "(opening)" : s.name;
      row.onclick = () => { const el = host.querySelector(`[data-sec="${s.i}"]`);
                            el && el.scrollIntoView({ behavior: "smooth", block: "start" }); };
      rail.append(row);
    });
    const where = document.createElement("div"); where.className = "ed-where";
    where.textContent = `reading ${secName(st.secs[st.reading])} · caret ${secName(st.secs[st.caret])}`;
    rail.append(where);

    // --- the page ------------------------------------------------------------------------------------
    const bar = document.createElement("div"); bar.className = "ed-status"; mid.append(bar);
    if (st.fence) mid.append(fenceBar(st, host, ctx));
    const sheet = document.createElement("div"); sheet.className = "ed-sheet";
    const h1 = document.createElement("h1"); h1.className = "ed-title"; h1.textContent = subj.title;
    h1.contentEditable = "plaintext-only"; h1.spellcheck = false;
    h1.onblur = async () => { const t = h1.textContent.trim();
      if (t && t !== subj.title) await Desk.do(`look ${st.id}; do retitle ${st.id} title=${q(t)}`); };
    const meta = document.createElement("p"); meta.className = "ed-meta";
    meta.textContent = `${plural(words(subj.text), "word")} · ${plural(headings(st.secs), "section")} · `
      + `${plural((subj.comments || []).filter(c => !c.resolved).length, "open comment")}`;
    sheet.append(h1, meta);

    st.secs.forEach(s => {
      const wrap = document.createElement("div"); wrap.className = "ed-sec-wrap";
      wrap.dataset.sec = s.i;
      if (s.name !== null) {
        const h = document.createElement("h2"); h.className = "ed-h";
        h.contentEditable = "plaintext-only"; h.spellcheck = false; h.textContent = s.name;
        h.oninput = () => { s.name = h.textContent; st.caret = s.i; arm(st, host, ctx); outlineTick(host, st); };
        h.onfocus = () => { st.caret = s.i; outlineTick(host, st); };
        wrap.append(h);
      }
      const b = document.createElement("div"); b.className = "ed-body";
      b.contentEditable = "plaintext-only"; b.spellcheck = false; b.textContent = s.body;
      b.oninput = () => { s.body = b.textContent; s.words = words(b.textContent);
                          st.caret = s.i;   // typing is proof the caret is here, even if focus never fired
                          arm(st, host, ctx); outlineTick(host, st); };
      b.onfocus = () => { if (st.caret !== s.i && st.unsettled) settle(st, host, ctx, "the caret leaving a section");
                          st.caret = s.i; outlineTick(host, st); };
      b.onblur = () => { if (st.unsettled) settle(st, host, ctx, "leaving the text"); };
      b.onkeydown = e => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                             e.preventDefault(); settle(st, host, ctx, "you asked"); } };
      wrap.append(b);
      sheet.append(wrap);
    });
    mid.append(sheet);
    const measure = () => {
      const top = mid.scrollTop, bottom = top + mid.clientHeight;
      let now = 0, first = null, last = null;
      host.querySelectorAll("[data-sec]").forEach(el => {
        const i = +el.dataset.sec, a = el.offsetTop, b = a + el.offsetHeight;
        if (a <= top + 80) now = i;
        if (b > top && a < bottom) { if (first === null) first = i; last = i; }
      });
      st.shown = [first === null ? now : first, last === null ? now : last];
      if (now !== st.reading) { st.reading = now; outlineTick(host, st); }
    };
    mid.onscroll = measure;
    requestAnimationFrame(measure);

    // --- the margin ----------------------------------------------------------------------------------
    const mh = document.createElement("h3"); mh.textContent = "margin"; mh.className = "";
    mh.style.cssText = "margin:0 0 8px;font:500 11px/1.4 var(--font);color:var(--quiet);"
      + "letter-spacing:.04em;text-transform:uppercase";
    marg.append(mh);
    const cs = subj.comments || [];
    if (!cs.length) {
      const p = document.createElement("p"); p.className = "ed-mark";
      p.textContent = "no comments on this document."; marg.append(p);
    }
    cs.forEach((c, k) => {
      const id = c.id || `c${k + 1}`;
      const card = document.createElement("div");
      card.className = "ed-card" + (c.resolved ? " resolved" : "");
      const who = document.createElement("div"); who.className = "who";
      who.textContent = `${id}  ${c.by || c.actor || "?"}  ${c.resolved ? "resolved" : "open"}`;
      const body = document.createElement("div"); body.className = "body";
      body.textContent = c.line || c.text || "";
      const mark = document.createElement("div"); mark.className = "ed-mark";
      mark.textContent = "? unanchored — the desk cannot yet say which passage this is about";
      card.append(who, body, mark);
      if (!c.resolved) {
        const b = document.createElement("button"); b.className = "ed-btn";
        b.textContent = "resolve"; b.title = `do resolve ${id}`;
        b.onclick = () => Desk.do(`look ${st.id}; do resolve ${id}`);
        card.append(b);
      }
      marg.append(card);
    });
    const add = document.createElement("button"); add.className = "ed-btn lead";
    add.textContent = "+ comment"; add.title = `do comment ${st.id} line="…"`;
    add.onclick = () => { const line = prompt("comment on this document"); if (line)
      Desk.do(`look ${st.id}; do comment ${st.id} line=${q(line)}`); };
    marg.append(add);
    const gap = document.createElement("p"); gap.className = "ed-mark";
    gap.style.marginTop = "14px";
    gap.textContent = "! a settle rewrites the WHOLE document: the desk has no section-scoped rewrite yet. "
      + "Both gaps are filed as to-jeff notes on the studio desk.";
    marg.append(gap);

    host.append(rail, mid, marg);
    status(host, st);
  }

  // cheap redraw of just the rail marks, so typing never rebuilds the page under the caret
  function outlineTick(host, st) {
    const rows = host.querySelectorAll(".ed-sec");
    st.secs.forEach(s => {
      const row = rows[s.i]; if (!row) return;
      row.dataset.here = st.reading === s.i ? "reading" : "";
      row.querySelector(".m").textContent =
        st.caret === s.i && st.unsettled ? "✎" : st.caret === s.i ? "|" : st.reading === s.i ? "▸" : "";
      row.querySelector(".w").textContent = s.words;
    });
    const w = host.querySelector(".ed-where");
    if (w) w.textContent = `reading ${secName(st.secs[st.reading])} · caret ${secName(st.secs[st.caret])}`;
    const wrap = host.querySelector(`[data-sec="${st.caret}"]`);
    host.querySelectorAll("[data-sec]").forEach(e => e.dataset.unsettled = "false");
    if (wrap && st.unsettled) wrap.dataset.unsettled = "true";
    status(host, st);
  }

  function fenceBar(st, host, ctx) {
    const box = document.createElement("div"); box.className = "ed-fence";
    const t = otherTouch.get(st.id);
    box.innerHTML = `<b>${t ? t.by : "someone else"} changed this document while you were typing.</b>`
      + ` Your draft is safe here and nothing has been lost — it is the whole document (${words(st.fence.mine)}w), `
      + `because the desk has no section-scoped rewrite yet.`
      + `<div class="row"></div><div style="margin-top:6px"><code>${esc(st.fence.err)}</code></div>`;
    const row = box.querySelector(".row");
    const btn = (label, title, fn) => { const b = document.createElement("button");
      b.className = "ed-btn lead"; b.textContent = label; b.title = title; b.onclick = fn; row.append(b); };
    btn("read theirs first", `read ${st.id}`, async () => {
      await Desk.do(`read ${st.id}`);
      const s = Desk.subject(Desk.node(st.id).subject);
      st.secs = parse(s.text); st.base = s.text; st.rev = s.rev; st.fence = null; st.unsettled = false;
      draw(host, ctx);
    });
    btn("keep mine over theirs", `read ${st.id}; do rewrite ${st.id} text="…"`, async () => {
      const mine = st.fence.mine;
      await Desk.do(`read ${st.id}`);
      const r = await Desk.do(`do rewrite ${st.id} text=${q(mine)}`);
      if (!r.error) { st.base = mine; st.secs = parse(mine); st.unsettled = false; st.fence = null; }
      draw(host, ctx);
    });
    btn("what did they do?", `why ${st.id}`, async () => {
      const r = await Desk.do(`why ${st.id}`);
      alert(r.text || r.error || "");
    });
    const note = document.createElement("div"); note.className = "ed-mark"; note.style.marginTop = "6px";
    note.textContent = "keeping yours does not destroy theirs: their change stays in history "
      + "(why " + st.id + ", and undo is theirs to use).";
    box.append(note);
    return box;
  }

  // ---- what a text-only inhabitant reads ------------------------------------------------------------
  function asText(ctx) {
    const st = state(ctx);
    if (!Desk.snapshot) return "the desk has not answered yet";
    if (!st.id || !Desk.node(st.id)) return "no document open. The editor shows subjects of kind doc.";
    const n = Desk.node(st.id), s = Desk.subject(n.subject);
    const secs = st.unsettled ? st.secs : parse(s.text);
    const open = (s.comments || []).filter(c => !c.resolved).length;
    const out = [];
    out.push(`read ${st.id} "${s.title}" · rev ${s.rev} · ${words(s.text)}w · `
           + `${plural(headings(secs), "section")} · ${plural((s.comments || []).length, "comment")}, ${open} open`);
    const t = otherTouch.get(st.id);
    if (t) out.push(`  ~${t.by}: ${t.verb} here, ${ago(t.seen)} ago (seen by this page; the desk's clock`
                  + ` is day-granular, so this is an observation, not a desk fact)`);
    const [a, b] = st.shown;
    out.push(`  = you are ${Desk.actor}; the page shows ${a === b ? secName(secs[a])
      : secName(secs[a]) + " .. " + secName(secs[b])}`
      + (a > 0 ? `, ${a} above` : "") + (b < secs.length - 1 ? `, ${secs.length - 1 - b} below` : "")
      + ` (measured from the scroll box)`);
    out.push(`  = caret ${st.caret === null ? "nowhere — nobody is typing in this window" : secName(secs[st.caret])}`);
    if (st.unsettled) out.push(`  = unsettled draft in ${secName(secs[st.caret])}: `
      + `${words(secs[st.caret] ? secs[st.caret].body : "")}w, last key ~${ago(st.lastKey)} ago, `
      + `settles after ${SETTLE_MS / 1000}s of quiet or on leaving`);
    if (st.fence) out.push(`  ! REFUSED at the last settle: ${st.fence.err} — your draft is held, not lost`);
    out.push("  outline:");
    secs.forEach(x => out.push(`    ${st.reading === x.i ? "▸" : " "}${st.caret === x.i ? "|" : " "} `
      + `#${x.i} ${x.name === null ? "(opening)" : x.name}  ${x.words}w`));
    out.push("  ---");
    for (let i = a; i <= b && i < secs.length; i++) {
      const x = secs[i];
      out.push(`  ${x.name !== null ? "## " + x.name : "(opening)"}`);
      (x.body || "").split("\n").forEach(l => out.push("  " + l));
    }
    out.push("  ---");
    const hidden = secs.length - (b - a + 1);
    out.push(hidden > 0
      ? `  (${hidden} section(s) are off the top or bottom of this window — read ${st.id} :3 for all of it)`
      : `  (the whole document is on screen)`);
    if ((s.comments || []).length) {
      out.push("  comments:");
      (s.comments || []).forEach((c, k) => out.push(`    ${c.id || "c" + (k + 1)} ${c.by || c.actor || "?"}`
        + ` (${c.resolved ? "resolved" : "open"}) ? unanchored · "${(c.line || c.text || "").slice(0, 60)}"`));
    }
    out.push("  ! this editor settles the WHOLE document (do rewrite), not the section: the desk has no");
    out.push("    section-scoped rewrite. A comment cannot name its passage. Both are filed to-jeff.");
    return out.join("\n");
  }

  Desk.on((snap, events) => remember(events));

  Desk.registerApp({
    id: "editor", title: "Editor", glyph: "¶",
    accepts: (node, subject) => subject && subject.kind === "doc",
    open: (host, ctx) => { const st = state(ctx);
      if (ctx.id && Desk.node(ctx.id)) load(st, ctx.id);
      draw(host, ctx); if (st.id) Desk.do(`read ${st.id}`); },
    refresh: (host, ctx) => {
      const st = state(ctx);
      if (!st.id) { draw(host, ctx); return; }
      const n = Desk.node(st.id); if (!n) { st.id = null; draw(host, ctx); return; }
      const s = Desk.subject(n.subject);
      if (st.unsettled) {                       // never rebuild the page under a live caret
        if (s.rev !== st.rev && !st.fence) {
          st.fence = { err: `the document moved to rev ${s.rev} while you were typing`,
                       mine: compose(st.secs), at: Date.now() };
          const mid = host.querySelector(".ed-page");
          if (mid && !host.querySelector(".ed-fence")) mid.insertBefore(fenceBar(st, host, ctx),
            mid.querySelector(".ed-sheet"));
        }
        status(host, st); return;
      }
      if (s.rev !== st.rev || compose(st.secs) !== (s.text || "")) { load(st, st.id); draw(host, ctx); }
      else { status(host, st); }
    },
    text: asText,
  });
})();
