// menu.js: the one right-click menu every Agora window wears (card dk1344; Alex, 21–22 Oct: "right-click anything").
// Brought over from the old desk's lens.js menu (selection words, the part's own entries, the ask box), and made
// shared: no view wires it. A widget window's frame (widget-host.js bootstrap) says only where the press was, the
// words selected under it and the thing the pressed part shows (data-thing, or the painter's data-fact-id); this
// trusted page reads that thing again as the viewer, draws the menu, and runs a line only when the viewer presses an
// entry. The host's own pages (the strip, lines, help, thing) are read from their own DOM.
//
// What fits what:
//   selected words           Comment (quotes them into the Conversation, with your words and a link back), Copy
//   a Needs-you item         Delete (forget: undo brings it back). Needs you = its who is you and it is not Done,
//                            as the Work view's band says.
//   any thing                Look, Open in <each lens that shows it>, and its own words from `actions <thing>`
//                            that need nothing more than the thing (house.review, task.done…)
//   no thing (the window)    the window's own words (window.close, window.focus… from `actions <window>`)
//   always, last             Ask for a change… (the `ask` word, 26 Oct)
// A view that draws its own menu (preventDefault) keeps it; Shift+right-click, inputs and editable words keep the
// browser's.
"use strict";
const AgoraMenu = (() => {
  const ID = /^[a-z]{1,8}\d+$/;
  const readable = (...values) => values.map(v => String(v || "").replace(/\s+/g, " ").trim()).find(v => v && !ID.test(v)) || "Selected item";
  const Q = (s) => '"' + String(s ?? "").replace(/\\/g, "\\\\").replace(/"/g, '\\"') + '"';
  let box = null, back = null, conversation = null, shown = 0;

  function css() {
    if (document.getElementById("ag-menu-style")) return;
    const s = document.createElement("style"); s.id = "ag-menu-style";
    s.textContent = `.ag-menu{position:fixed;z-index:2147483000;min-width:220px;max-width:340px;padding:6px;box-sizing:border-box;
      font:13px/1.35 var(--ag-font-ui,'Segoe UI',sans-serif);color:var(--ag-ink,#2f3b35);background:var(--ag-raised,#fff);
      border:1px solid var(--ag-border,#e3e6e4);border-radius:var(--ag-radius-l,12px);box-shadow:var(--ag-shadow,0 12px 40px #24352c22)}
      .ag-menu .ag-head{padding:6px 10px 4px;display:flex;gap:8px;align-items:baseline;overflow:hidden}
      .ag-menu .ag-head strong{font-weight:620;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
      .ag-menu .ag-head small{color:var(--ag-ink-muted,#6b7a72);white-space:nowrap}
      .ag-menu .ag-quote{margin:2px 10px 6px;padding-left:8px;border-left:3px solid var(--ag-accent,#83a99a);color:var(--ag-ink-muted,#5b6a62);
        max-height:4.2em;overflow:hidden;white-space:pre-wrap}
      .ag-menu button{display:flex;width:100%;gap:10px;justify-content:space-between;align-items:baseline;text-align:left;border:0;background:none;
        color:inherit;font:inherit;padding:6px 10px;border-radius:var(--ag-radius-s,8px);cursor:pointer}
      .ag-menu button small{color:var(--ag-ink-muted,#6b7a72);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:55%}
      .ag-menu button:hover,.ag-menu button:focus-visible{background:var(--ag-hover,#eef3f1);outline:none}
      .ag-menu button.ag-danger{color:var(--ag-danger,#b4473f)}
      .ag-menu hr{border:0;border-top:1px solid var(--ag-border,#e3e6e4);margin:5px 4px}
      .ag-menu .ag-wait{padding:4px 10px;color:var(--ag-ink-muted,#6b7a72)}
      .ag-menu input{display:block;box-sizing:border-box;width:100%;margin-top:4px;padding:7px 10px;font:inherit;font-size:12px;
        border:1px solid var(--ag-border,#e3e6e4);border-radius:8px;background:var(--ag-surface,#fff);color:inherit}`;
    document.head.append(s);
  }
  const el = (tag, attrs = {}, ...kids) => {
    const n = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) if (v !== undefined && v !== null && v !== false) n.setAttribute(k, v);
    for (const k of kids.flat()) if (k !== null && k !== undefined && k !== false) n.append(k.nodeType ? k : String(k));
    return n;
  };
  async function post(route, line) {
    try {
      const r = await fetch(route, { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(route === "/do" ? { line, press: Math.random().toString(16).slice(2, 18) } : { line }) });
      const j = await r.json();
      if (!r.ok) return { ok: false, text: j.error || j.refused || `the door said ${r.status}`, rows: [] };
      return j;
    } catch (e) { return { ok: false, text: "the kernel is not answering", rows: [] }; }
  }
  const see = (line) => post("/see", line);
  function told(out, fallback) {
    if (window.KD && KD.receipt) KD.receipt({ ok: out.ok !== false, text: out.ok === false ? out.text : (fallback || out.text) });
    window.dispatchEvent(new CustomEvent("agora-menu-did", { detail: out }));
  }
  async function run(line, said) {
    close(true);
    const out = await post("/do", line);
    told(out, said);
    return out;
  }

  function close(refocus) {
    if (!box) return;
    box.remove(); box = null;
    if (refocus && back && back.isConnected && back.focus) back.focus();
    back = null;
  }
  function place(x, y) {
    if (!box) return;
    const r = box.getBoundingClientRect();
    box.style.left = Math.max(6, Math.min(x, innerWidth - r.width - 6)) + "px";
    box.style.top = Math.max(6, Math.min(y, innerHeight - r.height - 6)) + "px";
  }
  function item(label, key, fn, cls) {
    const b = el("button", { type: "button", role: "menuitem", class: cls }, el("span", {}, label), key ? el("small", {}, key) : null);
    // A frame chooses where its menu opens, so a menu that appeared under a press already on its way takes no click
    // in its first 300 ms (keys still reach it at once).
    b.addEventListener("click", (e) => { if (e.detail && performance.now() - shown < 300) return; fn(e); });
    return b;
  }
  function input(placeholder, label, send) {
    const i = el("input", { type: "text", placeholder, "aria-label": label });
    i.addEventListener("keydown", (e) => {
      e.stopPropagation();
      if (e.key === "Escape") { e.preventDefault(); close(true); return; }
      if (e.key !== "Enter" || e.isComposing) return;
      e.preventDefault(); send(i.value.trim());
    });
    return i;
  }

  // a word offered with one press needs nothing more than the thing: `word <thing> [optional…]: …`
  function oneClick(row) {
    const usage = String(row.usage || ""), head = usage.split(":")[0];
    if (!head.startsWith(row.word + " ")) return false;
    const rest = head.slice(row.word.length).trim().replace(/^<[^>]*>/, "").replace(/\[[^\]]*\]/g, "").trim();
    return rest === "";
  }
  async function words(thing) {
    const [look, acts] = await Promise.all([see("look " + thing), see("actions " + thing)]);
    const row = (look.rows || []).find((r) => r.id === thing) || null;
    const lenses = [];
    const m = /lenses that show it: (.*)/.exec(acts.text || "");
    if (m) for (const bit of m[1].split(/,\s*/)) { const n = /^([\w.-]+)/.exec(bit); if (n) lenses.push(n[1]); }
    return { row, me: look.as || acts.as || "", acts: (acts.rows || []).filter(oneClick), lenses };
  }
  async function conversationId() {
    if (conversation) return conversation;
    const out = await see("rows chat name=Conversation");
    conversation = ((out.rows || []).find((r) => r.kind === "chat" && r.name === "Conversation") || {}).id || null;
    return conversation;
  }

  // open({x, y, thing, quote, where, label, about, window}): x, y in this page's pixels. thing: what was pressed (an
  // id), quote: the words selected under the press, about: what an ask with no thing is about (the widget or lens),
  // window: this window's own thing.
  async function open(o) {
    close(); css();
    const thing = ID.test(o.thing || "") ? o.thing : "";
    const win = ID.test(o.window || "") ? o.window : "";
    const about = thing || [o.about, api.about].find((a) => ID.test(a || "")) || win;
    const quote = String(o.quote || "").replace(/\s+/g, " ").trim().slice(0, 2000);
    back = document.activeElement;
    box = el("div", { class: "ag-menu", role: "menu", "aria-label": "Menu", "data-thing": thing || undefined });
    const head = el("div", { class: "ag-head" }, el("strong", {}, readable(o.label, thing ? "Selected item" : "This window").slice(0, 120)));
    box.append(head);
    if (quote) box.append(el("div", { class: "ag-quote" }, quote.length > 220 ? quote.slice(0, 220) + "…" : quote));
    const wait = el("div", { class: "ag-wait" }, "…");
    box.append(wait);
    document.body.append(box); place(o.x, o.y);
    const mine = box;
    const read = thing ? await words(thing) : win ? await words(win) : { row: null, me: "", acts: [], lenses: [] };
    if (box !== mine) return;                                        // closed or replaced while reading
    wait.remove();
    const row = read.row, name = readable(row?.title, row?.name, String(row?.text || "").replace(/\s+/g, " ").trim().slice(0, 80), o.label);
    if (row) {
      const kind = readable(row.post_kind, row.kind, "Item").replace(/[-_]/g, " ").replace(/^./, c => c.toUpperCase());
      head.replaceChildren(el("strong", {}, name.slice(0, 120)), el("small", {}, thing ? kind : "Window"));
    }
    const list = [];
    if (quote) {
      list.push(item("Comment", "Conversation", () => composeComment(quote, thing, name)));
      list.push(item("Copy", "", async () => { close(true); told({ ok: await copy(quote) ? true : false, text: "Copy did not happen" }, "copied"); }));
    }
    if (thing && row) {
      const needsYou = read.me && String(row.who || "") === read.me && !/^done$/i.test(String(row.lane || row.status || ""));
      if (needsYou) list.push(item("Delete", "undo brings it back", () => run("forget " + thing, `deleted ${name} · undo brings it back`), "ag-danger"));
      list.push(item("Look", "", () => run("window.open thing " + thing)));
      for (const lens of read.lenses.slice(0, 3)) list.push(item("Open in " + lens.replace(/[-_]+/g, " "), "", () => run(`window.open ${lens} ${thing}`)));
    }
    const own = read.acts.filter((a) => a.word !== "forget").slice(0, 8);
    if (own.length) {
      if (list.length) list.push(el("hr"));
      for (const a of own) {
        const b = item(a.word, "", () => run(`${a.word} ${thing || win}`));
        b.title = a.usage || "";
        list.push(b);
      }
    }
    if (list.length) box.append(...list, el("hr"));
    box.append(input("Ask for a change…", "Ask for a change to this, in your own words", async (words) => {
      if (!words) return;
      const where = [o.label || name || "", o.where || ""].filter(Boolean).join(" · ") || "this window";
      await run(`ask ${about || "-"} text=${Q(words)} where=${Q(where)}`, "Asked — it is in the Conversation");
    }));
    place(o.x, o.y); shown = performance.now();
    (box.querySelector("button") || box.querySelector("input")).focus();
  }

  function composeComment(quote, thing, name) {
    if (!box) return;
    const x = parseFloat(box.style.left), y = parseFloat(box.style.top);
    [...box.children].forEach((c) => { if (!c.classList.contains("ag-head") && !c.classList.contains("ag-quote")) c.remove(); });
    box.querySelector(".ag-head strong").textContent = "Comment";
    const field = input("Your words (optional) · Enter sends", "Your comment on these words", async (words) => {
      const chat = await conversationId();
      if (!chat) { close(true); told({ ok: false, text: "Comment: there is no Conversation here" }); return; }
      const link = thing ? `— from [[${thing}|${String(name || "Selected item").replace(/[\[\]|]/g, "")}]]` : "";
      const text = [words, quote.split("\n").map((l) => "> " + l).join("\n"), link].filter(Boolean).join("\n\n");
      await run(`say ${chat} text=${Q(text)}` + (thing ? ` about=${thing}` : ""), "Commented · it is in the Conversation");
    });
    box.append(field);
    place(x, y); field.focus();
  }

  async function copy(text) {
    try { await navigator.clipboard.writeText(text); return true; } catch (e) { /* fall through */ }
    const t = el("textarea", { style: "position:fixed;left:-9999px" }); t.value = text; document.body.append(t); t.select();
    const ok = document.execCommand("copy"); t.remove(); return ok;
  }

  // The host page's own surface: the strip, the receipt, and the desktop's own pages (lines, help, thing).
  function selectedAt(x, y) {
    const s = getSelection();
    if (!s || s.isCollapsed || !s.rangeCount) return "";
    for (const r of s.getRangeAt(0).getClientRects()) if (x >= r.left - 3 && x <= r.right + 3 && y >= r.top - 3 && y <= r.bottom + 3) return String(s);
    return "";
  }
  document.addEventListener("contextmenu", (e) => {
    if (e.defaultPrevented || e.shiftKey || window.AGORA_SHELL) return;
    const t = e.target instanceof Element ? e.target : null;
    if (!t || t.closest("input, textarea, select, [contenteditable]:not([contenteditable=false]), .ag-menu, iframe")) return;
    e.preventDefault();
    const q = (window.KD && KD.q) || new URLSearchParams(location.search);
    const at = t.closest("[data-thing]");
    open({ x: e.clientX, y: e.clientY, thing: at ? at.dataset.thing : (q.get("target") || ""), quote: selectedAt(e.clientX, e.clientY),
           window: q.get("win") || "", label: at ? at.dataset.label || "" : "" });
  });
  document.addEventListener("pointerdown", (e) => { if (box && !box.contains(e.target)) close(); }, true);
  document.addEventListener("keydown", (e) => {
    if (!box) return;
    if (e.key === "Escape") { e.preventDefault(); close(true); return; }
    if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
    const all = [...box.querySelectorAll("button, input")], i = all.indexOf(document.activeElement);
    e.preventDefault();
    all[(i + (e.key === "ArrowDown" ? 1 : all.length - 1)) % all.length]?.focus();
  });
  addEventListener("blur", () => { if (box && !box.contains(document.activeElement)) close(); });
  // about: what an ask with no thing is about in this page (widget-host.js sets its widget)
  const api = { open, close, isOpen: () => !!box, about: "" };
  return api;
})();
window.AgoraMenu = AgoraMenu;
