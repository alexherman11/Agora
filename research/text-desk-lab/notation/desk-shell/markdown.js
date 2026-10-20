// markdown.js: a text part that says `markdown` (a5820, Alex 16 Oct: 'nice clean markdown formatting ... kinda like
// obsidian but better'). OWNER: worker-a5820 for JEFF; anyone may improve it.
//
// The words are one Markdown document (a4865: one plain text per document, never HTML). Read, it is drawn: headings,
// lists, tasks, quotes, code, tables, links, [[wikilinks]] and ![[embeds]]. Written, it is the same drawing with the
// marks of the line the caret is on shown (live preview, as Obsidian's), and Ctrl+E shows the whole source.
//
// How it holds together: the source string is the only truth. Every source character is in the DOM as text, the marks
// in spans (.md-syn) hidden on lines the caret is not on; what is only drawn (a checkbox, a table, an embed card) is
// marked data-deco or data-src and is never read back as text.
// a6067: this file is now the Markdown GRAMMAR and its DRAWING only: what each line is, how it is drawn, characters <->
// DOM points, lit passages, and what Enter, Backspace, Tab, Ctrl+B/I/K and a task box mean as edits of the source. The
// editing (caret, selection, composition, undo, keys, sending to the desk) is textedit.js's, the one module every
// typed text uses; it draws a Markdown text through Markdown.draw.
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
  .md-doc .md-fence.md-close:not(.md-active),.md-doc .md-fence.md-bare:not(.md-active){height:.5em;min-height:0;overflow:hidden}
  .md-doc code.md-ic{font:.88em var(--md-mono);background:var(--t-wash,#eef3f0);padding:.08em .32em;border-radius:.3em}
  .md-doc mark.md-hl{background:color-mix(in srgb,var(--t-mark,#B4571C) 22%,transparent);color:inherit;border-radius:.2em;padding:0 .1em}
  .md-doc img.md-img{display:block;max-width:100%;max-height:24em;border-radius:.4em;margin:.3em 0}
  .md-doc .md-imgalt{color:var(--t-hush,#889);border-bottom:1px dashed var(--t-faint,#ccc)}
  .md-doc:not([contenteditable]) .md-check{cursor:default}
  .md-doc:not([contenteditable]) .md-check:hover{border-color:var(--t-hush,#889)}
  .md-doc .md-tag{color:var(--t-accent,#0F6B57);background:var(--t-wash,#eef3f0);border-radius:.6em;padding:0 .35em}
  .md-doc a.md-a,.md-doc .md-wl{color:var(--t-accent,#0F6B57);text-decoration:underline;text-decoration-color:color-mix(in srgb,var(--t-accent,#0F6B57) 35%,transparent);text-underline-offset:.18em;cursor:pointer}
  .md-doc .md-wl:hover,.md-doc a.md-a:hover{text-decoration-color:currentColor}
  .md-doc .md-wl.md-missing{color:var(--t-hush,#889);text-decoration-style:dashed}
  .md-doc .md-widget .md-syn{display:none}
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
  if (typeof document !== "undefined") {          // a6067: node tests read the grammar's edits without a page
    const style = document.createElement("style"); style.textContent = CSS; document.head.append(style);
    document.documentElement.style.setProperty("--md-mono", "'JetBrains Mono', 'Cascadia Code', Consolas, ui-monospace, monospace");
  }

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
    /(?<![\w/\\-])((?:worker-)?(?:[afscep]\d{2,}|m\d{2,}))(?![\w/\\-])/.source,  // 16 a bare id (a6109): drawn as its name; not in a path (a6452)
    /!\[([^\[\]\n]*)\]\(([^()\s]+)\)/.source,                    // 17,18 picture (a6452): last, it is the only one that starts at its `!`
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
      } else if (m[8] != null && m[8].length > 1 && m[8][0] === "*" && text[rx.lastIndex] === "*") {
        // ***both*** (a6452): the lazy ** took '*both' and left a star; it is strong and stressed at once
        // the same characters as **, *both*, **: the source stays every character, in order
        put("strong", "", m[8] + "*", "**", "**"); rx.lastIndex++;
      } else if (m[8] != null) put("strong", "", m[8], "**", "**");
      else if (m[9] != null) put("strong", "", m[9], "__", "__");
      else if (m[10] != null) put("s", "", m[10], "~~", "~~");
      else if (m[11] != null) put("mark", "md-hl", m[11], "==", "==");
      else if (m[12] != null) put("em", "", m[12], "*", "*");
      else if (m[13] != null) put("em", "", m[13], "_", "_");
      else if (m[14] != null) { const a = document.createElement("a"); a.className = "md-a"; a.dataset.href = m[14]; a.textContent = m[14]; into.append(a); }
      else if (m[15] != null) { const t = document.createElement("span"); t.className = "md-tag"; t.textContent = m[15]; into.append(t); }
      else if (m[16] != null) {
        // a6109: an id the scene names (ctx.things) shows the name, the id kept as the hidden source; any other stays words
        const hit = (ctx.things || {})[m[16]];
        if (!hit) into.append(m[16]);
        else {
          const a = document.createElement("span"); a.className = "md-wl md-thing"; a.dataset.target = m[16]; a.title = hit.title;
          a.append(syn(m[16])); const t = document.createElement("span"); t.dataset.deco = "1"; t.contentEditable = "false"; t.textContent = hit.name; a.append(t);
          into.append(a);
        }
      } else if (m[18] != null) {
        // a6452: a picture is drawn only when the scene showed its path (ctx.media, media_links' judgement): no address
        // in someone's words is fetched by the page. Any other stays its words, the address on hover
        into.append(syn(m[0]));
        const hit = (ctx.media || []).find(x => x.path === m[18] && x.kind === "image" && x.src);
        const e = document.createElement(hit ? "img" : "span"); e.dataset.deco = "1"; e.contentEditable = "false";
        if (hit) { e.className = "md-img"; e.src = hit.src; e.alt = m[17] || hit.name; e.title = m[17] || hit.name; e.draggable = false; e.dataset.media = hit.src; }
        else { e.className = "md-imgalt"; e.textContent = m[17] || m[18]; e.title = `a picture this page does not show: ${m[18]}`; }
        into.append(e);
      }
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
      add("md-fence"); add(d.open ? "md-open" : "md-close"); if (d.open && !d.lang) add("md-bare");
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

  // ---- lit passages (a5949: `light` on a document, the words its comments quote) -------------------------------------
  // A passage is found in the source as expr.find_words finds it on the desk (white space however it falls, the case as
  // written), so the page lights what the desk judges is still there; each text node it covers is wrapped in a <mark>.
  function spaced(s) {
    let out = "", gap = false; const at = [];
    for (let i = 0; i < s.length; i++) {
      if (/\s/.test(s[i])) { gap = out.length > 0; continue; }
      if (gap) { out += " "; at.push(i - 1); gap = false; }
      out += s[i]; at.push(i);
    }
    return [out, at];
  }
  function findWords(text, words) {
    const [t, at] = spaced(text), w = spaced(words)[0];
    const i = w ? t.indexOf(w) : -1;
    return i < 0 ? null : [at[i], at[i + w.length - 1] + 1];
  }
  function lightUp(root, src, passages, cls) {
    const st = starts(src);
    for (const want of passages || []) {
      const hit = findWords(src, want.replace(/^[“"]|[”"]$/g, "")); if (!hit) continue;
      const [a, b] = hit, nodes = [];
      for (const line of root.children) {
        if (line.dataset.l == null) continue;                  // a table or an embed is drawn, not lit
        const l = +line.dataset.l, ls = st[l], le = l + 1 < st.length ? st[l + 1] : src.length + 1;
        if (le <= a || ls >= b) continue;
        let n = 0;
        for (const t of textNodes(line)) { nodes.push([t, ls + n]); n += t.data.length; }
      }
      for (const [t, o] of nodes.reverse()) {
        const s = Math.max(a, o) - o, e = Math.min(b, o + t.data.length) - o; if (e <= s) continue;
        const mid = s > 0 ? t.splitText(s) : t; if (e - s < mid.data.length) mid.splitText(e - s);
        const m = document.createElement("mark"); m.className = cls || ""; m.dataset.light = want; mid.replaceWith(m); m.append(mid);
      }
    }
  }
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

  // ---- what a key means in Markdown (a6067) -------------------------------------------------------------------------
  // The grammar's own edits, as plain data: each takes the source and a range and gives the edit to make, {a, b, s}
  // (replace a..b by s) with where the selection goes after, or null when the key means nothing special here. The
  // editing itself (caret, undo, sending) is textedit.js's: this file only knows what Markdown says.
  function lineAround(src, at) { const s = src.lastIndexOf("\n", at - 1) + 1, e = src.indexOf("\n", at); return [s, e < 0 ? src.length : e]; }
  // Enter: a list goes on; an empty item ends it
  function enter(src, a, b) {
    const [ls] = lineAround(src, a), line = src.slice(ls, a);
    let m, more = "";
    if ((m = RX.task.exec(line))) more = m[1] + m[2] + " [ ] ";
    else if ((m = RX.bullet.exec(line))) more = m[1] + m[2] + " ";
    else if ((m = RX.num.exec(line))) more = m[1] + (+m[2] + 1) + m[3] + " ";
    else if ((m = RX.quote.exec(line))) more = m[1] + "> ";
    if (more && line.trim() === (m[0] || "").trim() && a === b) return { a: ls, b: a, s: "", at: ls };   // an empty item: the list ends
    return { a, b, s: "\n" + more, at: a + 1 + more.length };
  }
  // Backspace at the start of a list item or heading takes its mark off first, as Obsidian does
  function unmark(src, at) {
    const [ls, le] = lineAround(src, at), line = src.slice(ls, le);
    const m = RX.task.exec(line) || RX.bullet.exec(line) || RX.num.exec(line) || RX.head.exec(line) || RX.quote.exec(line);
    if (!m || at !== ls + m[0].length) return null;
    const keep = m[1] && /^\s+$/.test(m[1]) ? m[1].slice(0, -Math.min(2, m[1].length)) : "";
    return { a: ls, b: ls + m[0].length, s: keep, at: ls + keep.length };
  }
  // Tab / Shift+Tab: the lines of the range in or out by two spaces; one edit over the whole lines
  function indent(src, a, b, out) {
    const ls = lineAround(src, a)[0], le = lineAround(src, b)[1], lines = src.slice(ls, le).split("\n");
    let first = 0, shift = 0;
    const moved = lines.map((line, i) => {
      if (!out) { if (i === 0) first = 2; shift += 2; return "  " + line; }
      const k = line.startsWith("  ") ? 2 : line.startsWith("\t") || line.startsWith(" ") ? 1 : 0;
      if (i === 0) first = -k; shift -= k; return line.slice(k);
    });
    return { a: ls, b: le, s: moved.join("\n"), sel: [Math.max(ls, a + first), Math.max(ls, b + shift)] };
  }
  // Ctrl+B and the like: wrap the words, or take the marks off when they are already round them
  function wrap(src, a, b, w0, w1) {
    if (src.slice(a - w0.length, a) === w0 && src.slice(b, b + w1.length) === w1)
      return { a: a - w0.length, b: b + w1.length, s: src.slice(a, b), sel: [a - w0.length, b - w0.length] };
    return { a, b, s: w0 + src.slice(a, b) + w1, sel: [a + w0.length, b + w0.length] };
  }
  function link(src, a, b) { const words = src.slice(a, b) || "link"; const at = a + words.length + 3; return { a, b, s: `[${words}](https://)`, sel: [at, at + 8] }; }
  // a task box pressed: [ ] <-> [x] on line l
  function toggle(src, l) {
    const st = starts(src), at = st[l], end = src.indexOf("\n", at), m = RX.task.exec(src.slice(at, end < 0 ? undefined : end));
    if (!m) return null;
    const k = at + m[1].length + m[2].length + m[3].length + 1;
    return { a: k, b: k + 1, s: m[4] === " " ? "x" : " " };
  }

  globalThis.Markdown = { read, draw, inline, starts, textNodes, lineOf, offsetOf, pointAt, lightUp, findWords,
    enter, unmark, indent, wrap, link, toggle, lineAround };
})();
