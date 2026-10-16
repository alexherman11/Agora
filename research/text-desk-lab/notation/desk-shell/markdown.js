// markdown.js: a text part that says `markdown` (a5820, Alex 16 Oct: 'nice clean markdown formatting ... kinda like
// obsidian but better'). OWNER: worker-a5820 for JEFF; anyone may improve it.
//
// The words are one Markdown document (a4865: one plain text per document, never HTML). Read, it is drawn: headings,
// lists, tasks, quotes, code, tables, links, [[wikilinks]] and ![[embeds]]. Written, it is the same drawing with the
// marks of the line the caret is on shown (live preview, as Obsidian's), and Ctrl+E shows the whole source.
//
// How it holds together: the source string is the only truth. Every source character is in the DOM as text, the marks
// in spans (.md-syn) hidden on lines the caret is not on; what is only drawn (a checkbox, a table, an embed card) is
// marked data-deco or data-src and is never read back as text. Every change (a key, a paste, a cut, undo) is made on
// the string, through the range the browser says it would change (beforeinput's target range), and the document is
// drawn again with the caret put back by its count of characters. So nothing the browser does to the DOM can drift
// from what is saved. Keys: Ctrl+B bold, Ctrl+I italic, Ctrl+K link, Ctrl+E source, Ctrl+S save, Ctrl+Z / Ctrl+Y,
// Tab / Shift+Tab indent a list, Enter continues a list, [[ offers the documents the lens names.
(() => {
  const CSS = `
  .md-doc{white-space:pre-wrap;overflow-wrap:anywhere;outline:none;tab-size:4;caret-color:var(--t-accent,#0F6B57)}
  .md-doc .md-line{min-height:1lh;position:relative;padding-left:calc(var(--ind,0) * 1.6em)}
  .md-doc .md-line:not(.md-active) .md-syn{display:none}
  .md-doc .md-syn{color:var(--t-faint,#9aa);font-weight:400;font-style:normal}
  .md-doc .md-h1,.md-doc .md-h2,.md-doc .md-h3,.md-doc .md-h4,.md-doc .md-h5,.md-doc .md-h6{font-weight:650;line-height:1.25;letter-spacing:-.01em;color:var(--t-ink,#17231F)}
  .md-doc .md-h1{font-size:1.85em;margin:.9em 0 .35em}
  .md-doc .md-h2{font-size:1.45em;margin:1.1em 0 .3em}
  .md-doc .md-h3{font-size:1.2em;margin:1em 0 .2em}
  .md-doc .md-h4,.md-doc .md-h5,.md-doc .md-h6{font-size:1.02em;margin:.9em 0 .15em;color:var(--t-soft,#556)}
  .md-doc .md-line:first-child.md-h1,.md-doc .md-line:first-child.md-h2{margin-top:0}
  .md-doc .md-p{margin:0 0 .2em}
  .md-doc .md-blank{height:.7em;min-height:0}
  .md-doc .md-blank.md-active{height:auto;min-height:1lh}
  .md-doc.md-raw .md-blank{height:auto;min-height:1lh}
  .md-doc .md-li{padding-left:calc(var(--ind,0) * 1.6em + 1.4em)}
  .md-doc .md-li.md-active{padding-left:calc(var(--ind,0) * 1.6em)}
  .md-doc .md-bullet:not(.md-active)::before{content:"";position:absolute;left:calc(var(--ind,0) * 1.6em + .45em);top:.68em;width:.36em;height:.36em;border-radius:50%;background:var(--t-accent,#0F6B57);opacity:.75}
  .md-doc .md-num .md-numk{color:var(--t-accent,#0F6B57);font-variant-numeric:tabular-nums}
  .md-doc .md-num:not(.md-active){padding-left:calc(var(--ind,0) * 1.6em + .2em)}
  .md-doc .md-check{position:absolute;left:calc(var(--ind,0) * 1.6em + .1em);top:.28em;width:1em;height:1em;border:1.5px solid var(--t-hush,#889);border-radius:.25em;cursor:pointer;box-sizing:border-box;user-select:none}
  .md-doc .md-check:hover{border-color:var(--t-accent,#0F6B57)}
  .md-doc .md-task.md-done .md-check{background:var(--t-accent,#0F6B57);border-color:var(--t-accent,#0F6B57)}
  .md-doc .md-task.md-done .md-check::after{content:"";position:absolute;left:.27em;top:.08em;width:.28em;height:.52em;border:solid var(--t-card,#fff);border-width:0 .13em .13em 0;transform:rotate(45deg)}
  .md-doc .md-task.md-active .md-check{display:none}
  .md-doc .md-task.md-done:not(.md-active) .md-body{color:var(--t-hush,#889);text-decoration:line-through;text-decoration-color:var(--t-faint,#bbb)}
  .md-doc .md-quote{border-left:3px solid var(--t-accent,#0F6B57);padding-left:1em;color:var(--t-soft,#556);font-style:italic}
  .md-doc .md-quote.md-active{border-left-color:var(--t-faint,#ccc)}
  .md-doc .md-hr:not(.md-active){height:1lh;color:transparent}
  .md-doc .md-hr:not(.md-active)::after{content:"";position:absolute;left:0;right:0;top:50%;border-top:1px solid var(--t-faint,#ccc)}
  .md-doc .md-code,.md-doc .md-fence{font:.9em/1.55 var(--md-mono);background:var(--t-wash,#eef3f0);padding-left:1em;padding-right:1em}
  .md-doc .md-fence{color:var(--t-hush,#889);font-size:.78em}
  .md-doc .md-fence.md-open{border-radius:.4em .4em 0 0;padding-top:.3em}
  .md-doc .md-fence.md-close{border-radius:0 0 .4em .4em;padding-bottom:.3em}
  .md-doc .md-fence:not(.md-active) .md-syn{display:none}
  .md-doc .md-fence.md-close:not(.md-active){height:.5em;min-height:0;overflow:hidden}
  .md-doc code.md-ic{font:.88em var(--md-mono);background:var(--t-wash,#eef3f0);padding:.08em .32em;border-radius:.3em}
  .md-doc mark.md-hl{background:color-mix(in srgb,var(--t-mark,#B4571C) 22%,transparent);color:inherit;border-radius:.2em;padding:0 .1em}
  .md-doc .md-tag{color:var(--t-accent,#0F6B57);background:var(--t-wash,#eef3f0);border-radius:.6em;padding:0 .35em}
  .md-doc a.md-a,.md-doc .md-wl{color:var(--t-accent,#0F6B57);text-decoration:underline;text-decoration-color:color-mix(in srgb,var(--t-accent,#0F6B57) 35%,transparent);text-underline-offset:.18em;cursor:pointer}
  .md-doc .md-wl:hover,.md-doc a.md-a:hover{text-decoration-color:currentColor}
  .md-doc .md-wl.md-missing{color:var(--t-hush,#889);text-decoration-style:dashed}
  .md-doc .md-widget{position:relative;margin:.4em 0 .6em;cursor:text}
  .md-doc table.md-table{border-collapse:collapse;width:auto;min-width:50%;font-size:.95em}
  .md-doc .md-table th,.md-doc .md-table td{border:1px solid var(--t-ghost,#dde);padding:.35em .8em;text-align:left;vertical-align:top}
  .md-doc .md-table th{background:var(--t-wash,#eef3f0);font-weight:600}
  .md-doc .md-table tr:nth-child(even) td{background:color-mix(in srgb,var(--t-ink,#000) 2.5%,transparent)}
  .md-doc .md-embed{display:block;border:1px solid var(--t-ghost,#dde);border-left:3px solid var(--t-accent,#0F6B57);border-radius:.5em;padding:.6em .9em;background:var(--t-card,#fff);cursor:pointer}
  .md-doc .md-embed:hover{border-color:var(--t-faint,#ccc);border-left-color:var(--t-accent,#0F6B57)}
  .md-doc .md-embed .md-eh{display:flex;gap:.6em;align-items:baseline}
  .md-doc .md-embed .md-et{font-weight:600;color:var(--t-ink,#17231F);flex:1}
  .md-doc .md-embed .md-ek{font-size:.78em;color:var(--t-hush,#889);text-transform:lowercase}
  .md-doc .md-embed .md-es{font-size:.78em;padding:.05em .55em;border-radius:1em;background:var(--t-wash,#eef3f0);color:var(--t-accent,#0F6B57)}
  .md-doc .md-embed .md-es[data-s=done],.md-doc .md-embed .md-es[data-s=landed]{background:color-mix(in srgb,var(--t-accent,#0F6B57) 18%,transparent)}
  .md-doc .md-embed .md-es[data-s=doing],.md-doc .md-embed .md-es[data-s=working]{background:color-mix(in srgb,var(--t-mark,#B4571C) 18%,transparent);color:var(--t-mark,#B4571C)}
  .md-doc .md-embed .md-ex{font-size:.88em;color:var(--t-soft,#556);margin-top:.25em;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;white-space:normal}
  .md-doc .md-embed .md-eo{font-size:.75em;color:var(--t-hush,#889);margin-top:.3em}
  .md-doc .md-embed.md-missing{border-left-color:var(--t-faint,#ccc);color:var(--t-hush,#889);cursor:default}
  .md-doc.md-raw{font-family:var(--md-mono);font-size:.92em}
  .md-doc.md-raw .md-line{padding-left:0 !important;margin:0 !important;font:inherit !important;border:0 !important;background:none !important;color:inherit !important;height:auto !important}
  .md-doc.md-raw .md-line::before,.md-doc.md-raw .md-line::after{display:none !important}
  .md-doc.md-raw .md-syn{color:var(--t-accent,#0F6B57)}
  .md-doc[data-empty]:not(:focus)::before{content:attr(data-hint);color:var(--t-faint,#aab);position:absolute;pointer-events:none}
  .md-pop{position:fixed;z-index:60;min-width:18em;max-width:30em;max-height:18em;overflow:auto;background:var(--t-card,#fff);color:var(--t-ink,#17231F);border:1px solid var(--t-ghost,#dde);border-radius:.6em;box-shadow:0 .6em 2em rgba(0,0,0,.18);padding:.3em;font:14px/1.4 system-ui,sans-serif}
  .md-pop div{padding:.35em .6em;border-radius:.4em;cursor:pointer;display:flex;gap:.6em;align-items:baseline}
  .md-pop div[aria-selected=true]{background:var(--t-wash,#eef3f0)}
  .md-pop small{color:var(--t-hush,#889);margin-left:auto;font-size:.8em}
  .md-pop .md-none{color:var(--t-hush,#889);cursor:default}`;
  const style = document.createElement("style"); style.textContent = CSS; document.head.append(style);
  document.documentElement.style.setProperty("--md-mono", "'JetBrains Mono', 'Cascadia Code', Consolas, ui-monospace, monospace");

  const esc = s => s.replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  // ---- the grammar: what each line is ------------------------------------------------------------------------------
  const RX = {
    fence: /^(\s*)(```+|~~~+)(.*)$/,
    embed: /^\s*!\[\[([^\[\]\n]+?)\]\]\s*$/,
    head: /^(#{1,6})(\s+)/,
    hr: /^\s*(?:-\s*){3,}$|^\s*(?:\*\s*){3,}$|^\s*(?:_\s*){3,}$/,
    task: /^(\s*)([-*+])(\s+)\[([ xX])\](\s+|$)/,
    bullet: /^(\s*)([-*+])(\s+)/,
    num: /^(\s*)(\d{1,9})([.)])(\s+)/,
    quote: /^(\s*)(>\s?)/,
    row: /^\s*\|/,
    rule: /^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$/,
  };
  const indentOf = s => Math.floor(s.replace(/\t/g, "    ").length / 2);

  // lines -> one description each, and the blocks drawn as one widget (tables, embeds) with their first and last line
  function read(lines) {
    const out = [], widgets = [];
    let fence = null;
    for (let i = 0; i < lines.length; i++) {
      const s = lines[i];
      if (fence) {
        const m = RX.fence.exec(s);
        if (m && m[2][0] === fence[0] && m[2].length >= fence.length && !m[3].trim()) { out.push({ k: "fence", close: true, pre: s }); fence = null; }
        else out.push({ k: "code" });
        continue;
      }
      const f = RX.fence.exec(s);
      if (f) { fence = f[2]; out.push({ k: "fence", open: true, pre: f[1] + f[2], lang: f[3].trim() }); continue; }
      if (RX.row.test(s) && i + 1 < lines.length && RX.rule.test(lines[i + 1]) && lines[i + 1].includes("-")) {
        let j = i + 2; while (j < lines.length && RX.row.test(lines[j])) j++;
        widgets.push({ k: "table", from: i, to: j - 1 });
        for (let x = i; x < j; x++) out.push({ k: "trow", w: widgets.length - 1 });
        i = j - 1; continue;
      }
      let m;
      if ((m = RX.embed.exec(s))) { widgets.push({ k: "embed", from: i, to: i, target: m[1] }); out.push({ k: "embed", w: widgets.length - 1 }); continue; }
      if ((m = RX.head.exec(s))) { out.push({ k: "h", level: m[1].length, pre: m[0] }); continue; }
      if (RX.hr.test(s) && s.trim()) { out.push({ k: "hr" }); continue; }
      if ((m = RX.task.exec(s))) { out.push({ k: "task", ind: indentOf(m[1]), pre: m[0], done: m[4] !== " " }); continue; }
      if ((m = RX.bullet.exec(s))) { out.push({ k: "bullet", ind: indentOf(m[1]), pre: m[0] }); continue; }
      if ((m = RX.num.exec(s))) { out.push({ k: "num", ind: indentOf(m[1]), pre: m[1], mark: m[2] + m[3] + m[4] }); continue; }
      if ((m = RX.quote.exec(s))) { out.push({ k: "quote", pre: m[0] }); continue; }
      out.push({ k: s.trim() ? "p" : "blank" });
    }
    return { lines: out, widgets };
  }

  // ---- inline marks ------------------------------------------------------------------------------------------------
  // one alternation, first match wins; the order is the precedence (code keeps its stars, a link keeps its words)
  const INLINE = new RegExp([
    /(`+)([^`\n]+?)\1/.source,                                   // 1,2 code
    /(!?)\[\[([^\[\]|\n]+?)(?:\|([^\[\]\n]*))?\]\]/.source,      // 3,4,5 wikilink / inline embed
    /\[([^\[\]\n]+)\]\(([^()\s]+)\)/.source,                     // 6,7 link
    /\*\*(?=\S)(.+?)(?<=\S)\*\*/.source,                         // 8 strong
    /__(?=\S)(.+?)(?<=\S)__/.source,                             // 9 strong
    /~~(?=\S)(.+?)(?<=\S)~~/.source,                             // 10 strike
    /==(?=\S)(.+?)(?<=\S)==/.source,                             // 11 highlight
    /\*(?=[^\s*])([^*\n]+?)(?<=[^\s*])\*/.source,                // 12 stress
    /(?<![\w])_(?=[^\s_])([^_\n]+?)(?<=[^\s_])_(?![\w])/.source, // 13 stress
    /(https?:\/\/[^\s<>()]+[^\s<>().,;:!?'"])/.source,          // 14 bare address
    /(?<![\w&#])(#[A-Za-z][\w/-]*)/.source,                      // 15 tag
  ].join("|"), "g");

  function syn(t) { const s = document.createElement("span"); s.className = "md-syn"; s.textContent = t; return s; }
  function inline(text, ctx, into) {
    const rx = new RegExp(INLINE.source, "g");       // its own: marks inside marks read the same grammar again
    let at = 0, m;
    const put = (tag, cls, inner, before, after, extra) => {
      if (before) into.append(syn(before));
      const e = document.createElement(tag); if (cls) e.className = cls;
      if (extra) extra(e);
      inline(inner, ctx, e); into.append(e);
      if (after) into.append(syn(after));
    };
    while ((m = rx.exec(text))) {
      if (m.index > at) into.append(text.slice(at, m.index));
      if (m[2] != null) {
        into.append(syn(m[1])); const c = document.createElement("code"); c.className = "md-ic"; c.textContent = m[2]; into.append(c); into.append(syn(m[1]));
      } else if (m[4] != null) {
        const target = m[4].split("#")[0].trim(), hit = (ctx.links || {})[target] || null, alias = m[5];
        const shown = alias != null && alias !== "" ? alias : (hit && hit.id && /^[afs]\d+$/.test(target) ? hit.title : m[4]);
        const pre = (m[3] || "") + "[[" + (alias != null ? m[4] + "|" : "");
        into.append(syn(pre));
        const a = document.createElement("span"); a.className = "md-wl" + (hit && hit.id ? "" : " md-missing");
        a.dataset.target = target; if (hit && hit.id) { a.dataset.id = hit.id; a.title = `${hit.title} · ${hit.kind || ""} ${hit.id}`.trim(); } else a.title = `nothing is called “${target}” yet`;
        // an id with no words of its own shows the thing's title: the id lives in the hidden marks
        if (alias == null && hit && hit.id && /^[afs]\d+$/.test(target)) { a.append(syn(m[4])); const t = document.createElement("span"); t.dataset.deco = "1"; t.contentEditable = "false"; t.textContent = shown; a.append(t); }
        else a.textContent = shown;
        into.append(a); into.append(syn("]]"));
      } else if (m[6] != null) {
        into.append(syn("[")); const a = document.createElement("a"); a.className = "md-a"; a.dataset.href = m[7]; a.title = m[7]; inline(m[6], ctx, a); into.append(a); into.append(syn("](" + m[7] + ")"));
      } else if (m[8] != null) put("strong", "", m[8], "**", "**");
      else if (m[9] != null) put("strong", "", m[9], "__", "__");
      else if (m[10] != null) put("s", "", m[10], "~~", "~~");
      else if (m[11] != null) put("mark", "md-hl", m[11], "==", "==");
      else if (m[12] != null) put("em", "", m[12], "*", "*");
      else if (m[13] != null) put("em", "", m[13], "_", "_");
      else if (m[14] != null) { const a = document.createElement("a"); a.className = "md-a"; a.dataset.href = m[14]; a.textContent = m[14]; into.append(a); }
      else if (m[15] != null) { const t = document.createElement("span"); t.className = "md-tag"; t.textContent = m[15]; into.append(t); }
      at = rx.lastIndex;
    }
    if (at < text.length) into.append(text.slice(at));
    return into;
  }

  // ---- drawing -----------------------------------------------------------------------------------------------------
  function lineEl(src, d, i, ctx) {
    const el = document.createElement("div"); el.className = "md-line"; el.dataset.l = i;
    const add = c => el.classList.add(c);
    let rest = src;
    const lead = pre => { el.append(syn(pre)); rest = src.slice(pre.length); };
    if (d.k === "h") { add("md-h" + d.level); lead(d.pre); }
    else if (d.k === "task") {
      add("md-li"); add("md-task"); if (d.done) add("md-done"); el.style.setProperty("--ind", d.ind);
      const box = document.createElement("span"); box.className = "md-check"; box.dataset.deco = "1"; box.contentEditable = "false"; box.dataset.check = i;
      box.setAttribute("role", "checkbox"); box.setAttribute("aria-checked", String(d.done));
      el.append(box); lead(d.pre);
    }
    else if (d.k === "bullet") { add("md-li"); add("md-bullet"); el.style.setProperty("--ind", d.ind); lead(d.pre); }
    else if (d.k === "num") {
      add("md-num"); el.style.setProperty("--ind", d.ind);
      if (d.pre) el.append(syn(d.pre));
      const k = document.createElement("span"); k.className = "md-numk"; k.textContent = d.mark; el.append(k); rest = src.slice(d.pre.length + d.mark.length);
    }
    else if (d.k === "quote") { add("md-quote"); lead(d.pre); }
    else if (d.k === "hr") { add("md-hr"); el.append(syn(src)); rest = ""; }
    else if (d.k === "fence") {
      add("md-fence"); add(d.open ? "md-open" : "md-close");
      if (d.open) { el.append(syn(d.pre)); if (d.lang) el.append(document.createTextNode(src.slice(d.pre.length))); else rest = src.slice(d.pre.length); if (d.lang) rest = ""; }
      else { el.append(syn(src)); rest = ""; }
    }
    else if (d.k === "code") { add("md-code"); el.append(src); rest = ""; }
    else if (d.k === "blank") add("md-blank");
    else add("md-p");
    if (rest) { const body = document.createElement("span"); body.className = "md-body"; inline(rest, ctx, body); el.append(body); }
    if (!el.textContent) el.append(document.createElement("br"));
    return el;
  }

  function cells(row) {
    let s = row.trim(); if (s.startsWith("|")) s = s.slice(1); if (s.endsWith("|") && !s.endsWith("\\|")) s = s.slice(0, -1);
    return s.split(/(?<!\\)\|/).map(c => c.trim());
  }
  function widgetEl(lines, w, ctx) {
    const box = document.createElement("div"); box.className = "md-widget"; box.contentEditable = "false";
    box.dataset.from = w.from; box.dataset.to = w.to; box.dataset.src = lines.slice(w.from, w.to + 1).join("\n");
    if (w.k === "table") {
      const t = document.createElement("table"); t.className = "md-table";
      const aligns = cells(lines[w.from + 1]).map(c => c.startsWith(":") && c.endsWith(":") ? "center" : c.endsWith(":") ? "right" : "");
      const tr = (row, tag) => { const r = document.createElement("tr"); cells(row).forEach((c, j) => { const e = document.createElement(tag); if (aligns[j]) e.style.textAlign = aligns[j]; inline(c, ctx, e); r.append(e); }); return r; };
      const head = document.createElement("thead"); head.append(tr(lines[w.from], "th")); t.append(head);
      const body = document.createElement("tbody"); for (let i = w.from + 2; i <= w.to; i++) body.append(tr(lines[i], "td")); t.append(body);
      box.append(t);
    } else {
      const target = w.target.split("|")[0].split("#")[0].trim(), hit = (ctx.links || {})[target];
      const card = document.createElement("div"); card.className = "md-embed" + (hit && hit.id ? "" : " md-missing");
      if (hit && hit.id) {
        card.dataset.id = hit.id;
        const state = hit.commission || hit.status || "";
        card.innerHTML = `<div class="md-eh"><span class="md-et">${esc(hit.title || target)}</span>${state ? `<span class="md-es" data-s="${esc(state)}">${esc(state)}</span>` : ""}<span class="md-ek">${esc(hit.kind || "")} ${esc(hit.id)}</span></div>`
          + (hit.excerpt ? `<div class="md-ex">${esc(hit.excerpt)}</div>` : hit.inside != null ? `<div class="md-ex">${hit.inside} inside</div>` : "")
          + (hit.owner ? `<div class="md-eo">owner ${esc(hit.owner)}</div>` : "");
      } else card.textContent = `nothing is called “${target}” yet`;
      box.append(card);
    }
    return box;
  }

  // the whole document, every line drawn; `active` is a set of line numbers whose marks show and whose widget is lines
  function draw(root, src, ctx, active, raw) {
    const lines = src.split("\n"), r = read(lines), out = [];
    const open = w => raw || [...Array(w.to - w.from + 1).keys()].some(k => active.has(w.from + k));
    for (let i = 0; i < lines.length; i++) {
      const d = r.lines[i];
      if (d.w != null && !open(r.widgets[d.w])) { const w = r.widgets[d.w]; out.push(widgetEl(lines, w, ctx)); i = w.to; continue; }
      const el = lineEl(lines[i], d.w != null ? { k: "p" } : d, i, ctx);
      if (raw || active.has(i)) el.classList.add("md-active");
      // a fence's lines show their marks together: the caret anywhere in the block opens both ends
      out.push(el);
    }
    root.replaceChildren(...out);
    root.classList.toggle("md-raw", !!raw);
    if (!src) root.dataset.empty = "1"; else delete root.dataset.empty;
    return r;
  }

  // ---- characters <-> DOM points -----------------------------------------------------------------------------------
  function starts(src) { const s = [0]; for (let i = 0; i < src.length; i++) if (src[i] === "\n") s.push(i + 1); return s; }
  function textNodes(el) {
    const out = [], walk = n => { for (const c of n.childNodes) { if (c.nodeType === 3) out.push(c); else if (c.nodeType === 1 && !c.dataset.deco) walk(c); } };
    walk(el); return out;
  }
  function lineOf(root, node) {
    let x = node.nodeType === 1 ? node : node.parentElement;
    while (x && x.parentElement !== root) x = x.parentElement;
    return x;
  }
  function offsetOf(root, src, node, off) {
    const st = starts(src);
    if (node === root) {                                  // between lines: the start of the line at that index
      const kid = root.childNodes[Math.min(off, root.childNodes.length - 1)];
      if (!kid) return 0;
      const at = lineStart(kid, st);
      return off >= root.childNodes.length ? src.length : at;
    }
    const line = lineOf(root, node); if (!line) return 0;
    const base = lineStart(line, st);
    if (line.dataset.src != null) return base;            // inside a widget: its first character
    let n = 0;
    for (const t of textNodes(line)) {
      if (t === node) return base + n + off;
      if (node.nodeType === 1 && node.contains(t)) {       // an element point: count its children before off
        const before = [...node.childNodes].slice(0, off);
        if (!before.some(c => c === t || c.contains(t))) return base + n;
      }
      n += t.data.length;
    }
    return base + n;
  }
  function lineStart(el, st) { const l = +(el.dataset.l ?? el.dataset.from ?? 0); return st[l] ?? 0; }
  function pointAt(root, src, at) {
    const st = starts(src); let l = 0; while (l + 1 < st.length && st[l + 1] <= at) l++;
    const el = root.querySelector(`:scope > [data-l="${l}"]`);
    if (!el) { const w = [...root.children].find(c => c.dataset.from != null && +c.dataset.from <= l && +c.dataset.to >= l); return w ? [root, [...root.children].indexOf(w)] : [root, 0]; }
    let left = at - st[l];
    const ts = textNodes(el);
    for (let k = 0; k < ts.length; k++) {
      const t = ts[k], hidden = t.parentElement.closest(".md-syn") && !el.classList.contains("md-active");
      if (left < t.data.length || (left === t.data.length && (k === ts.length - 1 || !hidden))) return [t, left];
      left -= t.data.length;
    }
    return [el, 0];
  }

  // ---- the editor --------------------------------------------------------------------------------------------------
  // opts: { text, links, titles [{id,title,kind}], hint, editable, typed(src), save(src) -> Promise, follow(id, title) }
  function create(opts) {
    const root = document.createElement("div"); root.className = "md-doc";
    let src = opts.text || "", ctx = { links: opts.links || {} }, raw = false, active = new Set(), undo = [], redo = [], lastPush = 0, composing = false;
    if (opts.hint) root.dataset.hint = opts.hint;
    const ed = !!opts.editable;
    if (ed) { root.contentEditable = "true"; root.spellcheck = true; root.setAttribute("role", "textbox"); root.setAttribute("aria-multiline", "true"); }
    const sel = () => {
      const s = getSelection(); if (!s.rangeCount || !root.contains(s.anchorNode)) return null;
      const a = offsetOf(root, src, s.anchorNode, s.anchorOffset), f = offsetOf(root, src, s.focusNode, s.focusOffset);
      return { a: Math.min(a, f), b: Math.max(a, f), back: f < a };
    };
    const linesOf = (a, b) => { const st = starts(src), set = new Set(); let l = 0; while (l + 1 < st.length && st[l + 1] <= a) l++; set.add(l); while (l + 1 < st.length && st[l + 1] <= b) set.add(++l); return set; };
    const place = (a, b = a) => {
      const s = getSelection(), [n1, o1] = pointAt(root, src, a), [n2, o2] = pointAt(root, src, b);
      try { s.setBaseAndExtent(n1, o1, n2, o2); } catch (e) { /* a point that moved away */ }
    };
    function paint(a, b) {
      active = ed && document.activeElement === root && a != null ? linesOf(a, b) : new Set();
      // a fence opens as one: the caret on either end line shows both
      draw(root, src, ctx, active, raw);
      if (a != null && document.activeElement === root) place(a, b);
    }
    function change(a, b, text, how) {
      const now = Date.now();
      if (how !== "type" || now - lastPush > 900) { undo.push({ src, a, b }); if (undo.length > 300) undo.shift(); }
      lastPush = how === "type" ? now : 0; redo = [];
      src = src.slice(0, a) + text + src.slice(b);
      const c = a + text.length; paint(c, c); opts.typed && opts.typed(src);
      complete();
    }
    function restore(from, to) {
      const st = from.pop(); if (!st) return;
      to.push({ src, a: st.a, b: st.b }); src = st.src; paint(st.a, st.b); opts.typed && opts.typed(src);
    }
    function lineAround(at) { const s = src.lastIndexOf("\n", at - 1) + 1, e = src.indexOf("\n", at); return [s, e < 0 ? src.length : e]; }

    // Enter: a list goes on; an empty item ends it
    function enter(r) {
      const [ls] = lineAround(r.a), line = src.slice(ls, r.a);
      let m, more = "";
      if ((m = RX.task.exec(line))) more = m[1] + m[2] + " [ ] ";
      else if ((m = RX.bullet.exec(line))) more = m[1] + m[2] + " ";
      else if ((m = RX.num.exec(line))) more = m[1] + (+m[2] + 1) + m[3] + " ";
      else if ((m = RX.quote.exec(line))) more = m[1] + "> ";
      if (more && line.trim() === (m[0] || "").trim() && r.a === r.b) return change(ls, r.a, "", "enter");   // an empty item: the list ends
      change(r.a, r.b, "\n" + more, "enter");
    }
    function indent(r, out) {
      const st = starts(src), ls = linesOf(r.a, r.b);
      let shift = 0, first = 0, s2 = src;
      for (const l of [...ls].sort((x, y) => y - x)) {
        const at = st[l], line = s2.slice(at, s2.indexOf("\n", at) < 0 ? undefined : s2.indexOf("\n", at));
        if (out) { const k = line.startsWith("  ") ? 2 : line.startsWith("\t") ? 1 : line.startsWith(" ") ? 1 : 0; s2 = s2.slice(0, at) + s2.slice(at + k); shift -= k; if (l === Math.min(...ls)) first = -k; }
        else { s2 = s2.slice(0, at) + "  " + s2.slice(at); shift += 2; if (l === Math.min(...ls)) first = 2; }
      }
      undo.push({ src, a: r.a, b: r.b }); redo = []; src = s2;
      paint(Math.max(0, r.a + first), Math.max(0, r.b + shift)); opts.typed && opts.typed(src);
    }
    function wrap(r, w0, w1) {
      const words = src.slice(r.a, r.b);
      if (src.slice(r.a - w0.length, r.a) === w0 && src.slice(r.b, r.b + w1.length) === w1) {    // on already: take it off
        undo.push({ src, a: r.a, b: r.b }); redo = [];
        src = src.slice(0, r.a - w0.length) + words + src.slice(r.b + w1.length);
        paint(r.a - w0.length, r.b - w0.length); opts.typed && opts.typed(src); return;
      }
      undo.push({ src, a: r.a, b: r.b }); redo = [];
      src = src.slice(0, r.a) + w0 + words + w1 + src.slice(r.b);
      paint(r.a + w0.length, r.b + w0.length); opts.typed && opts.typed(src);
    }
    function toggle(l) {
      const st = starts(src), at = st[l], line = src.slice(at, src.indexOf("\n", at) < 0 ? undefined : src.indexOf("\n", at)), m = RX.task.exec(line);
      if (!m) return;
      const k = at + m[1].length + m[2].length + m[3].length + 1;
      undo.push({ src, a: k, b: k }); redo = [];
      src = src.slice(0, k) + (m[4] === " " ? "x" : " ") + src.slice(k + 1);
      paint(null); opts.typed && opts.typed(src); opts.save && opts.save(src);
    }

    // [[ offers what the lens names (opts.titles); the choice is written [[id|title]], so a rename never breaks it
    let pop = null, popAt = 0, popPick = 0, popHits = [];
    function closePop() { if (pop) pop.remove(); pop = null; }
    function complete() {
      const r = sel(); if (!r || r.a !== r.b || !opts.titles) return closePop();
      const [ls] = lineAround(r.a), m = /\[\[([^\[\]|\n]{0,60})$/.exec(src.slice(ls, r.a));
      if (!m) return closePop();
      popAt = r.a - m[1].length - 2;
      const q = m[1].toLowerCase().trim();
      popHits = opts.titles.filter(t => !q || t.title.toLowerCase().includes(q) || t.id === q)
        .sort((x, y) => (y.title.toLowerCase().startsWith(q) - x.title.toLowerCase().startsWith(q))).slice(0, 8);
      popPick = Math.min(popPick, Math.max(0, popHits.length - 1));
      if (!pop) { pop = document.createElement("div"); pop.className = "md-pop"; pop.setAttribute("role", "listbox"); document.body.append(pop);
        pop.addEventListener("mousedown", e => { e.preventDefault(); const d = e.target.closest("[data-i]"); if (d) choose(+d.dataset.i); }); }
      pop.replaceChildren(...(popHits.length ? popHits.map((t, i) => { const d = document.createElement("div"); d.dataset.i = i; d.setAttribute("role", "option"); d.setAttribute("aria-selected", String(i === popPick)); d.innerHTML = `<span>${esc(t.title)}</span><small>${esc(t.kind || "")} ${esc(t.id)}</small>`; return d; })
        : [Object.assign(document.createElement("div"), { className: "md-none", textContent: q ? `no document called “${m[1]}”: keep typing for a link to a title` : "type a title" })]));
      const rr = getSelection().getRangeAt(0).getBoundingClientRect();
      pop.style.left = Math.min(rr.left, innerWidth - 360) + "px"; pop.style.top = (rr.bottom + 6) + "px";
    }
    function choose(i) {
      const t = popHits[i]; if (!t) return;
      const r = sel(), end = src.slice(r.a, r.a + 2) === "]]" ? r.a + 2 : r.a;
      closePop(); change(popAt, end, `[[${t.id}|${t.title}]]`, "link");
    }

    function follow(target) {
      const hit = (ctx.links || {})[target];
      if (!hit || !hit.id) return opts.notify && opts.notify(`nothing is called “${target}” yet`);
      opts.follow && opts.follow(hit.id, hit.title);
    }
    root.addEventListener("click", e => {
      const box = e.target.closest(".md-check");
      if (box && ed) { e.preventDefault(); return toggle(+box.dataset.check); }
      const wl = e.target.closest(".md-wl"), emb = e.target.closest(".md-embed[data-id]"), a = e.target.closest("a.md-a");
      const line = (wl || a) && lineOf(root, wl || a), shown = !line || !line.classList.contains("md-active");
      if (emb && (!ed || !e.altKey)) { e.preventDefault(); return follow(emb.closest(".md-widget").dataset.src.replace(/^\s*!\[\[|\]\]\s*$/g, "").split("|")[0].split("#")[0].trim()); }
      // a link whose marks are hidden is followed; on the line being written a click places the caret (Ctrl+click follows)
      if (wl && (shown || e.ctrlKey || e.metaKey)) { e.preventDefault(); return follow(wl.dataset.target); }
      if (a && (shown || e.ctrlKey || e.metaKey) && /^https?:/.test(a.dataset.href || "")) { e.preventDefault(); window.open(a.dataset.href, "_blank", "noopener"); return; }
      const w = e.target.closest(".md-widget");
      if (w && ed) { root.focus(); const at = starts(src)[+w.dataset.from] || 0; paint(at, at); }
    });
    if (!ed) { paint(null); return { el: root, set(t, l) { src = t || ""; ctx = { links: l || {} }; paint(null); }, src: () => src }; }

    root.addEventListener("beforeinput", e => {
      if (composing || e.inputType === "insertCompositionText") return;
      const r0 = sel(); if (!r0) return;
      const tr = e.getTargetRanges && e.getTargetRanges()[0];
      const r = tr ? (() => { const a = offsetOf(root, src, tr.startContainer, tr.startOffset), b = offsetOf(root, src, tr.endContainer, tr.endOffset); return { a: Math.min(a, b), b: Math.max(a, b) }; })() : r0;
      const t = e.inputType;
      e.preventDefault();
      if (t === "insertText" || t === "insertReplacementText" || t === "insertFromPaste" || t === "insertFromDrop" || t === "insertFromYank") {
        const data = (e.data != null ? e.data : e.dataTransfer && e.dataTransfer.getData("text/plain")) || "";
        return change(r.a, r.b, data.replace(/\r\n?/g, "\n"), t === "insertText" ? "type" : "paste");
      }
      if (t === "insertParagraph" || t === "insertLineBreak") return pop && popHits.length ? choose(popPick) : enter(r0);
      if (t.startsWith("delete")) {
        let { a, b } = r;
        if (a === b) {                                      // no range given: one character
          if (t.includes("Backward")) a = Math.max(0, a - 1); else b = Math.min(src.length, b + 1);
        }
        // Backspace at the start of a list item or heading takes its mark off first, as Obsidian does
        if (t === "deleteContentBackward" && r0.a === r0.b) {
          const [ls] = lineAround(r0.a), line = src.slice(ls, src.indexOf("\n", ls) < 0 ? undefined : src.indexOf("\n", ls));
          const m = RX.task.exec(line) || RX.bullet.exec(line) || RX.num.exec(line) || RX.head.exec(line) || RX.quote.exec(line);
          if (m && r0.a === ls + m[0].length) return change(ls, ls + m[0].length, m[1] && /^\s+$/.test(m[1]) ? m[1].slice(0, -Math.min(2, m[1].length)) : "", "del");
        }
        return change(a, b, "", t.includes("Backward") ? "del" : "fwd");
      }
      if (t === "historyUndo") return restore(undo, redo);
      if (t === "historyRedo") return restore(redo, undo);
      if (t === "formatBold") return wrap(r0, "**", "**");
      if (t === "formatItalic") return wrap(r0, "*", "*");
    });
    root.addEventListener("compositionstart", () => { composing = true; });
    root.addEventListener("compositionend", e => {      // an input method's words, read back from the line they went into
      composing = false;
      const r = sel(); if (!r) return;
      const line = lineOf(root, getSelection().anchorNode); if (!line || line.dataset.l == null) return;
      const l = +line.dataset.l, st = starts(src), end = src.indexOf("\n", st[l]);
      const now = textNodes(line).map(t => t.data).join("");
      undo.push({ src, a: r.a, b: r.b }); src = src.slice(0, st[l]) + now + src.slice(end < 0 ? src.length : end);
      paint(r.a, r.a); opts.typed && opts.typed(src);
    });
    root.addEventListener("keydown", e => {
      const mod = e.ctrlKey || e.metaKey, k = e.key.toLowerCase(), r = sel();
      if (pop) {
        if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); popPick = (popPick + (e.key === "ArrowDown" ? 1 : popHits.length - 1)) % Math.max(1, popHits.length); return complete(); }
        if (e.key === "Tab" && popHits.length) { e.preventDefault(); return choose(popPick); }
        if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); return closePop(); }
      }
      if (!r) return;
      if (mod && k === "e") { e.preventDefault(); raw = !raw; return paint(r.a, r.b); }
      if (mod && k === "s") { e.preventDefault(); return opts.save && opts.save(src); }
      if (mod && e.key === "Enter") { e.preventDefault(); return opts.save && opts.save(src); }
      if (mod && k === "b") { e.preventDefault(); return wrap(r, "**", "**"); }
      if (mod && k === "i") { e.preventDefault(); return wrap(r, "*", "*"); }
      if (mod && k === "k") { e.preventDefault(); const words = src.slice(r.a, r.b) || "link"; undo.push({ src, a: r.a, b: r.b }); src = src.slice(0, r.a) + `[${words}](https://)` + src.slice(r.b); const at = r.a + words.length + 3; paint(at, at + 8); opts.typed && opts.typed(src); return; }
      if (mod && !e.shiftKey && k === "z") { e.preventDefault(); return restore(undo, redo); }
      if (mod && (k === "y" || (e.shiftKey && k === "z"))) { e.preventDefault(); return restore(redo, undo); }
      if (e.key === "Tab" && !mod) { e.preventDefault(); return indent(r, e.shiftKey); }
      if (e.key === "Escape") { e.preventDefault(); root.blur(); }
    });
    root.addEventListener("copy", e => { const r = sel(); if (!r || r.a === r.b) return; e.preventDefault(); e.clipboardData.setData("text/plain", src.slice(r.a, r.b)); });
    root.addEventListener("cut", e => { const r = sel(); if (!r || r.a === r.b) return; e.preventDefault(); e.clipboardData.setData("text/plain", src.slice(r.a, r.b)); change(r.a, r.b, "", "cut"); });
    // the caret moving shows the marks of the lines it is on, and opens a table it enters
    let was = "";
    const moved = () => {
      if (document.activeElement !== root || composing) return;
      const r = sel(); if (!r) return;
      const now = [...linesOf(r.a, r.b)].join(",");
      if (now === was) return; was = now;
      const next = linesOf(r.a, r.b), widgetTouched = [...root.children].some(c => c.dataset.from != null && [...next].some(l => l >= +c.dataset.from && l <= +c.dataset.to));
      const leftWidget = [...active].some(l => { const w = read(src.split("\n")).lines[l]; return w && w.w != null; });
      if (widgetTouched || leftWidget || raw) return paint(r.a, r.b);
      for (const c of root.children) if (c.dataset.l != null) c.classList.toggle("md-active", next.has(+c.dataset.l));
      active = next;
      if (pop) complete();
    };
    document.addEventListener("selectionchange", moved);
    root.addEventListener("focus", () => { was = ""; setTimeout(moved, 0); });
    root.addEventListener("blur", () => { closePop(); was = ""; active = new Set(); for (const c of root.querySelectorAll(".md-line.md-active")) if (!raw) c.classList.remove("md-active"); if (read(src.split("\n")).widgets.length) paint(null); });
    paint(null);
    return {
      el: root, src: () => src,
      // the world's words arrive: kept when they are what is here; drawn again (the caret kept) when only links changed
      set(t, l) { ctx = { links: l || {} }; const r = sel(); if (t != null) src = t; paint(r ? r.a : null, r ? r.b : null); },
      links(l) { ctx = { links: l || {} }; const r = sel(); paint(r ? r.a : null, r ? r.b : null); },
      press(key) { const k = key.split("+").pop().toLowerCase(), r = sel() || { a: src.length, b: src.length };
        const focused = document.activeElement === root;
        if (k === "e") { raw = !raw; return paint(focused ? r.a : null, focused ? r.b : null); }
        if (k === "s") return opts.save && opts.save(src);
        if (!focused) return;
        if (k === "b") return wrap(r, "**", "**"); if (k === "i") return wrap(r, "*", "*");
        if (k === "k") { const words = src.slice(r.a, r.b) || "link"; undo.push({ src, a: r.a, b: r.b }); src = src.slice(0, r.a) + `[${words}](https://)` + src.slice(r.b); const at = r.a + words.length + 3; paint(at, at + 8); opts.typed && opts.typed(src); } },
      raw: () => raw,
    };
  }

  window.Markdown = { create, read };
})();
