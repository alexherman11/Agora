// kd.js: what the desktop's own pages share (the taskbar, the frame around a lens, lines, help, thing). A page speaks
// only lines through the kernel's door: POST /see, POST /do, and GET /door/stream for what happens. It holds no power
// of its own: who acts is the session (an HttpOnly cookie the door's /dev/signin set when the window host opened the
// page), and what it may do is what the kernel's dictionary says that person may do.
//
// App windows are lenses painted by lens.js itself (frame.html holds one). These pages are the host's chrome, and
// draw a few rows themselves where the lens language has no word yet (a ticking clock, which window is in front).
"use strict";
const KD = (() => {
  const q = new URLSearchParams(location.search);
  const win = q.get("win"), target = q.get("target");

  async function post(route, body) {
    try {
      const r = await fetch(route, { method: "POST", headers: { "Content-Type": "application/json" },
                                     body: JSON.stringify(body) });
      const j = await r.json();
      if (!r.ok) return { ok: false, text: j.error || j.refused || `the door said ${r.status}`, rows: [] };
      return j;
    } catch (e) {
      return { ok: false, text: "the kernel is not answering (is it off?)", rows: [] };
    }
  }
  const see = (line) => post("/see", { line });
  const press = () => (crypto.randomUUID ? crypto.randomUUID() : String(Math.random())).replace(/-/g, "").slice(0, 16);
  const act = (line) => post("/do", { line, press: press() });

  const listeners = [];
  let es = null;
  function stream(fn) {
    listeners.push(fn);
    if (es) return;
    // the kernel's stream: `world` (a record was written: its number) and `happen` (what the reader may hear)
    es = new EventSource("/door/stream");
    const tell = (h) => { for (const f of listeners) f(h); };
    es.addEventListener("world", (ev) => { try { tell({ word: "world", seq: JSON.parse(ev.data).seq }); } catch (e) { /* */ } });
    es.addEventListener("happen", (ev) => { try { tell(JSON.parse(ev.data)); } catch (e) { /* */ } });
    es.onerror = () => { document.body.classList.add("away"); };
    es.onopen = () => { document.body.classList.remove("away"); for (const f of listeners) f({ word: "hello" }); };
  }

  function el(tag, attrs, ...kids) {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (k === "on") for (const [ev, f] of Object.entries(v)) e.addEventListener(ev, f);
      else if (k === "cls") e.className = v;
      else if (v !== undefined && v !== null && v !== false) e.setAttribute(k, v);
    }
    for (const k of kids.flat()) if (k !== null && k !== undefined && k !== false) e.append(k.nodeType ? k : String(k));
    return e;
  }

  // the receipt line at a page's foot: what the kernel said to the last press
  function receipt(out) {
    let r = document.getElementById("receipt");
    if (!r) return;
    r.textContent = out.text || (out.ok ? "ok" : "refused");
    r.className = out.ok === false || /^refused/.test(out.text || "") ? "receipt refused" : "receipt";
    clearTimeout(receipt.t);
    receipt.t = setTimeout(() => { r.textContent = ""; }, 9000);
  }

  async function doLine(line) {
    const out = await act(line);
    receipt(out);
    return out;
  }

  // a window's own strip: its name (drag to move), tuck away, close. Closing is a line, so undo opens it again.
  function chrome(name) {
    document.title = `${name} · Agora`;
    const api = () => window.pywebview && window.pywebview.api;
    const strip = el("header", { cls: "strip" },
      el("span", { cls: "name pywebview-drag-region" }, name),
      el("span", { cls: "grow pywebview-drag-region" }),
      el("button", { title: "tuck away", on: { click: () => api() && api().minimize() } }, "–"),
      el("button", { title: "close (undo opens it again)", on: { click: () => win && doLine(`window.close ${win}`) } }, "×"));
    document.body.prepend(strip);
    const grip = el("div", { cls: "grip", title: "drag to resize", on: { mousedown: (e) => { e.preventDefault(); api() && api().resize(); } } });
    document.body.append(grip, el("div", { id: "receipt", cls: "receipt" }));
    return strip;
  }

  function ago(sec) {
    if (sec < 60) return "just now";
    if (sec < 3600) return `${Math.floor(sec / 60)} min ago`;
    if (sec < 86400) return `${Math.floor(sec / 3600)} h ago`;
    return `${Math.floor(sec / 86400)} d ago`;
  }

  return { see, act, doLine, stream, el, chrome, receipt, win, target, ago, q };
})();
