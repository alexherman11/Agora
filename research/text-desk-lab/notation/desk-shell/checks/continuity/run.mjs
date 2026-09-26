// checks/continuity/run.mjs : an instrument for the painter-continuity exploration. Owner: Pike.
// It is evidence for reports about what a real browser does to a scene under change; it is not a gate.
//
// Real input into the real painter (lens.html + lens.js) against a real deskd, while other actors change the
// world and the lens underneath. Input is sent through the Chrome DevTools Protocol's Input domain (trusted
// mouse, key and text events through the browser's input pipeline), in headless Chrome. That is automation,
// not a person at a keyboard: IME, OS focus and physical timing are NOT covered.
//
//     node desk-shell/checks/continuity/run.mjs            (from research/text-desk-lab/notation)
//     node desk-shell/checks/continuity/run.mjs S2 S3      (only these scenarios)
//
// It starts its own deskd on a private port and a scratch session per scenario (`pike-continuity-s1` ...),
// all removed at the end. Chrome's profile lives in the OS temp directory.
// Results: desk-shell/checks/continuity/results/<date>.json and a table on stdout.
//
// What each scenario records:
//   delivered   the gesture reached the world as the command the scene printed
//   refused     deskd refused it, and why (read from the painter's own /api/do response, recorded in the page)
//   refusalShown the refusal is still on screen after the painter repaints (a refusal nobody sees is a silent drop)
//   draftLost   the person typed something that is now neither in the world nor anywhere on the page
//   phantom     the page shows text that is not in the world and not marked as unsent
//   wrongTarget a write landed on something the gesture did not name
//   pass        whether what I hoped for (`expect`) held; `verdict` sorts it as holds / wrong, silent / wrong, visible

import { spawn } from "node:child_process";
import { existsSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const NOTATION = resolve(HERE, "../../..");
const PY = "C:/Projects/Agora4/.venv/Scripts/python.exe";
const CHROME = ["C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"].find(existsSync);
const PORT = Number(process.env.PORT || 8871), CDP_PORT = 9333, BASE_SESSION = "pike-continuity";
let SESSION = BASE_SESSION;      // one scratch world per scenario: a closing tab's last request cannot touch the next world
const BASE = `http://127.0.0.1:${PORT}`;
const sleep = ms => new Promise(r => setTimeout(r, ms));

// ---------------------------------------------------------------- the world side: deskd over HTTP
async function act(as, line) {
  const r = await (await fetch(`${BASE}/api/do`, { method: "POST", body: JSON.stringify({ session: SESSION, as, line }) })).json();
  return r;
}
async function sceneText(lens, as = "observer") {
  const r = await (await fetch(`${BASE}/api/scene?session=${SESSION}&as=${as}&lens=${lens}`)).json();
  return r.text || r.refused || "";
}
async function titleOf(id) {
  const r = await act("observer", `read ${id}`);
  const m = (r.text || "").match(/note "([^"]*)"/);
  return m ? m[1] : null;
}
async function whereOf(id) {
  const r = await act("observer", `where ${id}`);
  const m = (r.text || "").match(/local (\d+),(\d+)/);
  return m ? [Number(m[1]), Number(m[2])] : null;
}

async function fixture() {
  const ids = {};
  const mk = async (line, name) => {
    const w = line.split(" "), looks = (w[1] === "link" ? [w[2], w[3]] : [w[2]]).map(t => `look ${t}; `).join("");
    const r = await act("fixture", looks + line);
    if (r.error) throw new Error(`fixture refused: ${line}\n${r.error}`);
    if (name) ids[name] = r.created[r.created.length - 1];
    return r;
  };
  await mk("do create f01 kind=surface title=Trip layout=free", "trip_f");
  await mk(`do create ${ids.trip_f} kind=note title="Big Sur trip" tags=trip start=2026-10-10 end=2026-10-12`, "trip");
  await mk(`do create ${ids.trip_f} kind=note title="Kirk Creek camp" tags=stop tripday=1 place="Kirk Creek"`, "kirk");
  await mk(`do create ${ids.trip_f} kind=note title="McWay Falls" tags=stop tripday=2 place="Julia Pfeiffer Burns"`, "mcway");
  await mk(`do link ${ids.kirk} ${ids.trip} as=part-of`);
  await mk(`do link ${ids.mcway} ${ids.trip} as=part-of`);
  await mk("do create f01 kind=surface title=Lenses layout=column", "lens_f");
  const cal = [
    "cal : row, the tag:trip as trip",
    "  days : row, derive days = days-from $trip.start $trip.end, over $days, each day",
    "day : column, role sheet, on drop item do prop $carried tripday=$it.n",
    "  h : role heading, derive wd = weekday $it.date, text \\\"$wd $it.date\\\"",
    "  items : column, of parts:$trip.item,prop:tripday=$it.n, each item",
    "item : role card, carry",
    "  t : role title, text $title, on edit do retitle $item title=\\\"$value\\\"",
    "  p : role meta, text $place",
  ].join("\\n");
  await mk(`do create ${ids.lens_f} kind=note title=cal tags=lens text="${cal}"`, "cal");
  const board = [
    "board : free, role sheet",
    `  cards : free, of in:${ids.trip_f}, each card`,
    "card : role card, at item, on drag do move $item to=$x,$y",
    "  t : role title, text $title",
  ].join("\\n");
  await mk(`do create ${ids.lens_f} kind=note title=board tags=lens text="${board}"`, "board");
  ids.calText = cal;

  // Alex's own workspace (named 25 Sep): a collapsed project bar, a chat column with code, a document column,
  // background tasks. Acceptance: an edit in the chat while a task finishes loses nothing, moves nothing untouched.
  await mk("do create f01 kind=surface title=Work layout=column", "work_f");
  for (const p of ["Agora4", "Canvas", "Resume"]) await mk(`do create ${ids.work_f} kind=note title="${p}" tags=project`);
  await mk(`do create ${ids.work_f} kind=note title="you" tags=chat text="Why does the fence refuse my edit?"`, "m1");
  await mk(`do create ${ids.work_f} kind=note title="claude" tags=chat text="Because def is per lens:\\n\\n    if d.rev != cur.rev:\\n        refuse()\\n\\nany lens edit moves it."`, "m2");
  await mk(`do create ${ids.work_f} kind=note title="draft" tags=chat text="(type here)"`, "draft");
  await mk(`do create ${ids.work_f} kind=note title="Painter continuity" tags=doc text="Every gesture works in a real browser.\\nNothing a person typed is lost."`, "page");
  await mk(`do create ${ids.work_f} kind=note title="run the suite" tags=bg`, "task1");
  await mk(`do prop ${ids.task1} status=running`);
  await mk(`do create ${ids.work_f} kind=note title="rebuild the index" tags=bg`, "task2");
  await mk(`do prop ${ids.task2} status=queued`);
  const work = [
    "work : grid 1 3 3 1, role sheet",      // pike-7 section 3, lowered in 5bb7f7f (S14 before run l drew a row)
    "  bar : column, role bar, fold, of tag:project, each proj",
    "  chat : column, scroll end, of tag:chat, each msg",
    "  doc : column, of tag:doc, each page",
    "  tasks : column, of tag:bg, each task",
    "proj : role meta, text $title",
    "msg : role card",
    "  who : role meta, text $title",
    "  b : role body, text $text, lines 1..8, on edit do rewrite $item text=\\\"$value\\\"",
    "page : role card",
    "  h : role heading, text $title",
    "  b : role body, text $text",
    "task : role card",
    "  t : role title, text \\\"$title · $status\\\"",
  ].join("\\n");
  await mk(`do create ${ids.lens_f} kind=note title=work tags=lens text="${work}"`, "work");
  return ids;
}

// ---------------------------------------------------------------- the person side: Chrome over CDP
let chrome;
async function startChrome() {
  const prof = join(tmpdir(), "pike-continuity-chrome");
  rmSync(prof, { recursive: true, force: true });
  chrome = spawn(CHROME, ["--headless=new", `--remote-debugging-port=${CDP_PORT}`, `--user-data-dir=${prof}`,
    "--window-size=1400,900", "--no-first-run", "--no-default-browser-check", "about:blank"], { stdio: "ignore" });
  for (let i = 0; i < 50; i++) {
    try { return await (await fetch(`http://127.0.0.1:${CDP_PORT}/json/version`)).json(); } catch { await sleep(200); }
  }
  throw new Error("Chrome did not open its debugging port");
}

class Tab {
  static async open(url) {
    const t = await (await fetch(`http://127.0.0.1:${CDP_PORT}/json/new?${encodeURIComponent(url)}`, { method: "PUT" })).json();
    const tab = new Tab(t.webSocketDebuggerUrl, t.id);
    await tab.ready;
    await tab.send("Runtime.enable");
    await tab.send("Page.enable");
    return tab;
  }
  constructor(ws, id) {
    this.id = id; this.n = 0; this.pending = new Map();
    this.ws = new WebSocket(ws);
    this.ready = new Promise(r => this.ws.addEventListener("open", r));
    this.ws.addEventListener("message", e => {
      const m = JSON.parse(e.data);
      if (m.id && this.pending.has(m.id)) { this.pending.get(m.id)(m); this.pending.delete(m.id); }
      if (m.method && this.events[m.method]) this.events[m.method](m.params);
    });
    this.events = {};
  }
  send(method, params = {}) {
    const id = ++this.n;
    this.ws.send(JSON.stringify({ id, method, params }));
    return new Promise(r => this.pending.set(id, r));
  }
  async eval(expr) {
    const r = await this.send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
    if (r.result && r.result.exceptionDetails) throw new Error(r.result.exceptionDetails.text + " in " + expr);
    return r.result && r.result.result ? r.result.result.value : undefined;
  }
  // the painter's own gestures, as deskd answered them (a refusal is recorded here even if the painter overwrites it)
  async dos() { return this.eval("window.__do || []"); }
  async lastDo() { const d = await this.dos(); return d[d.length - 1] || null; }
  async painted(min = 1, ms = 8000) {
    await this.eval(`if (!window.__do) { window.__do = []; const f = window.fetch;
      window.fetch = async (u, o) => { const r = await f(u, o);
        if (String(u).includes('/api/do')) { const j = await r.clone().json(); const b = JSON.parse(o.body);
          window.__do.push({ line: b.line, observed: b.observed, error: j.error, text: j.text }); }
        return r; }; }`);
    for (let t = 0; t < ms; t += 200) {
      if ((await this.eval("document.querySelectorAll('[data-key]').length")) >= min) return true;
      await sleep(200);
    }
    return false;
  }
  // an element by the end of its scene key; returns its centre and text
  async find(suffix) {
    return this.eval(`(() => { const el = [...document.querySelectorAll('[data-key]')].find(e => e.dataset.key.endsWith(${JSON.stringify(suffix)}));
      if (!el) return null; el.scrollIntoView({ block: "nearest", inline: "nearest" });
      const r = el.getBoundingClientRect(), p = document.getElementById("paint"), v = { right: p.getBoundingClientRect().left + p.clientWidth };
      return { x: Math.max(r.x + 4, Math.min(r.x + r.width / 2, v.right - 8)), y: r.y + Math.min(r.height / 2, 12), text: el.textContent, key: el.dataset.key }; })()`);
  }
  async click(x, y, clickCount = 1) {
    await this.send("Input.dispatchMouseEvent", { type: "mouseMoved", x, y });
    await this.send("Input.dispatchMouseEvent", { type: "mousePressed", x, y, button: "left", clickCount });
    await this.send("Input.dispatchMouseEvent", { type: "mouseReleased", x, y, button: "left", clickCount });
  }
  async drag(x0, y0, x1, y1, steps = 8) {
    await this.send("Input.dispatchMouseEvent", { type: "mouseMoved", x: x0, y: y0 });
    await this.send("Input.dispatchMouseEvent", { type: "mousePressed", x: x0, y: y0, button: "left", buttons: 1, clickCount: 1 });
    for (let i = 1; i <= steps; i++) {
      await this.send("Input.dispatchMouseEvent", { type: "mouseMoved", x: x0 + (x1 - x0) * i / steps, y: y0 + (y1 - y0) * i / steps, button: "left", buttons: 1 });
      await sleep(20);
    }
    await this.send("Input.dispatchMouseEvent", { type: "mouseReleased", x: x1, y: y1, button: "left", buttons: 0, clickCount: 1 });
  }
  async key(key, code, vk, modifiers = 0) {
    await this.send("Input.dispatchKeyEvent", { type: "rawKeyDown", key, code, windowsVirtualKeyCode: vk, modifiers });
    await this.send("Input.dispatchKeyEvent", { type: "keyUp", key, code, windowsVirtualKeyCode: vk, modifiers });
  }
  async type(text) { await this.send("Input.insertText", { text }); }
  async selectAll() { await this.key("a", "KeyA", 65, 2); }
  // Enter as a keyboard sends it: keyDown carries the character, so an editor that does not take the key gets a new line
  async enter() {
    const r = String.fromCharCode(13);
    await this.send("Input.dispatchKeyEvent", { type: "keyDown", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13, text: r, unmodifiedText: r });
    await this.send("Input.dispatchKeyEvent", { type: "keyUp", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13 });
  }
  async said() { return this.eval("document.getElementById('said').textContent"); }
  async pageHas(s) { return this.eval(`document.body.innerText.includes(${JSON.stringify(s)})`); }
  close() { this.ws.close(); return fetch(`http://127.0.0.1:${CDP_PORT}/json/close/${this.id}`); }
}

const lensUrl = (lens, as = "alex") => `${BASE}/lens.html?session=${SESSION}&as=${as}&lens=${lens}`;

// Type into a title and hold it (not yet sent). Returns the tab and the draft.
async function beginEdit(tab, id, draft) {
  const el = await tab.find(`/${id}/t`);
  if (!el) throw new Error(`no painted title for ${id}`);
  await tab.click(el.x, el.y);
  await tab.selectAll();
  await tab.type(draft);
  return el;
}

// After an edit was sent: did it land, was it refused, is the draft lost, is a phantom on screen?
async function judgeEdit(tab, id, draft, before) {
  await sleep(2500);
  const world = await titleOf(id);
  const said = await tab.said();
  const d = await tab.lastDo();
  const sent = !!d && d.line.includes(draft);
  const refused = sent && d.error ? d.error.slice(0, 200) : null;
  const refusalShown = !!refused && said.includes("refused:");
  const inWorld = world === draft;
  const onPage = await tab.pageHas(draft);
  const saidMarksIt = said.split("\n")[0].includes(draft) ||      // is the draft marked as unsent, in the panel or where it was typed?
    await tab.eval(`[...document.querySelectorAll("[data-unsent]")].some(e => e.textContent.includes(${JSON.stringify(draft)}))`);
  return {
    sent, delivered: inWorld, refused, refusalShown, world, before,
    draftLost: !inWorld && !onPage,
    phantom: !inWorld && onPage && !saidMarksIt,
  };
}

// ---------------------------------------------------------------- scenarios
const S = {};

S.S1 = { what: "plain edit of a card title, mouse and keys", expect: "delivered",
  async run(ids) {
    const tab = await Tab.open(lensUrl("cal")); await tab.painted(5);
    const before = await titleOf(ids.kirk);
    await beginEdit(tab, ids.kirk, "Kirk Creek campground"); await tab.enter();
    const r = await judgeEdit(tab, ids.kirk, "Kirk Creek campground", before);
    await tab.close();
    return { ...r, pass: r.delivered };
  } };

S.S2 = { what: "edit while another actor retitles the same card", expect: "refused, draft kept and resendable",
  async run(ids) {
    const tab = await Tab.open(lensUrl("cal")); await tab.painted(5);
    const before = await titleOf(ids.mcway);
    await beginEdit(tab, ids.mcway, "McWay Falls overlook");
    await act("other", `look ${ids.mcway}; do retitle ${ids.mcway} title="McWay Falls (closed)"`);
    await tab.enter();
    const r = await judgeEdit(tab, ids.mcway, "McWay Falls overlook", before);
    // pike-8 section 3: the peer's words must be on screen before a resend may go (both sides), not only a refusal
    const bothShown = (await tab.said()).split(NOTICE_END)[0].includes("McWay Falls (closed)");   // in the notice, not only in the scene print
    // resendable: the person reads both sides, clicks their kept words and presses Enter again
    const el = await tab.find(`/${ids.mcway}/t`);
    if (el) { await tab.click(el.x, el.y); await tab.enter(); await sleep(2500); }
    const resent = (await titleOf(ids.mcway)) === "McWay Falls overlook";
    await tab.close();
    return { ...r, bothShown, resent, pass: !!r.refused && r.refusalShown && bothShown && !r.draftLost && !r.phantom && resent };
  } };

S.S3 = { what: "edit while the lens changes in an unrelated part (the day heading)", expect: "delivered: the title's meaning did not change",
  async run(ids) {
    const tab = await Tab.open(lensUrl("cal")); await tab.painted(5);
    const before = await titleOf(ids.kirk);
    await beginEdit(tab, ids.kirk, "Kirk Creek (walk-in)");
    const newText = ids.calText.replace("$wd $it.date", "Day $it.n · $wd $it.date");
    await act("other", `read ${ids.cal}; do rewrite ${ids.cal} text="${newText}"`);
    await tab.enter();
    const r = await judgeEdit(tab, ids.kirk, "Kirk Creek (walk-in)", before);
    await tab.close();
    return { ...r, pass: r.delivered };
  } };

S.S4 = { what: "edit while another actor retitles a different card", expect: "delivered",
  async run(ids) {
    const tab = await Tab.open(lensUrl("cal")); await tab.painted(5);
    const before = await titleOf(ids.kirk);
    await beginEdit(tab, ids.kirk, "Kirk Creek (site 4)");
    await act("other", `look ${ids.mcway}; do retitle ${ids.mcway} title="McWay Falls"`);
    await tab.enter();
    const r = await judgeEdit(tab, ids.kirk, "Kirk Creek (site 4)", before);
    await tab.close();
    return { ...r, pass: r.delivered };
  } };

S.S5 = { what: "edit a title while another actor changes an unrelated prop of the same card (not shown)", expect: "delivered: the title's inputs did not change",
  async run(ids) {
    const tab = await Tab.open(lensUrl("cal")); await tab.painted(5);
    const before = await titleOf(ids.kirk);
    await beginEdit(tab, ids.kirk, "Kirk Creek (booked)");
    await act("other", `look ${ids.kirk}; do prop ${ids.kirk} booking=confirmed`);
    await tab.enter();
    const r = await judgeEdit(tab, ids.kirk, "Kirk Creek (booked)", before);
    await tab.close();
    return { ...r, pass: r.delivered };
  } };

S.S6 = { what: "keyboard only: Tab to a card title, type, Enter", expect: "reachable and delivered",
  async run(ids) {
    const tab = await Tab.open(lensUrl("cal")); await tab.painted(5);
    const before = await titleOf(ids.mcway);
    let reached = null, presses = 0;
    for (; presses < 30; presses++) {
      await tab.key("Tab", "Tab", 9);
      const k = await tab.eval("document.activeElement && document.activeElement.dataset ? document.activeElement.dataset.key || '' : ''");
      if (k && k.endsWith(`/${ids.mcway}/t`)) { reached = k; break; }
    }
    if (!reached) { await tab.close(); return { reached: false, presses, pass: false, note: "no Tab stop reached the title" }; }
    await tab.selectAll(); await tab.type("McWay Falls by keyboard"); await tab.enter();
    const r = await judgeEdit(tab, ids.mcway, "McWay Falls by keyboard", before);
    await tab.close();
    return { ...r, reached: true, presses: presses + 1, pass: r.delivered };
  } };

S.S7 = { what: "drag a card on the free board", expect: "delivered: the world position follows",
  async run(ids) {
    const tab = await Tab.open(lensUrl("board")); await tab.painted(3);
    const before = await whereOf(ids.kirk);
    const el = await tab.find(`/cards/${ids.kirk}`);
    await tab.drag(el.x, el.y, el.x + 120, el.y + 60);
    await sleep(2500);
    const after = await whereOf(ids.kirk);
    const d = await tab.lastDo();
    await tab.close();
    const moved = before && after && (after[0] !== before[0] || after[1] !== before[1]);
    return { before, after, sent: d && d.line, refused: d && d.error, delivered: moved, pass: moved };
  } };

S.S8 = { what: "drag a card another actor moved after it was painted", expect: "refused, card shows the world's position, nothing written",
  async run(ids) {
    const tab = await Tab.open(lensUrl("board")); await tab.painted(3);
    const el = await tab.find(`/cards/${ids.mcway}`);
    const hit = await tab.eval(`document.elementsFromPoint(${el.x}, ${el.y}).map(e => e.tagName + (e.id ? "#" + e.id : "") + (e.dataset.key ? "[" + e.dataset.key + "]" : ""))`);
    // the person has the card in hand when the other actor moves it
    await tab.send("Input.dispatchMouseEvent", { type: "mouseMoved", x: el.x, y: el.y });
    await tab.send("Input.dispatchMouseEvent", { type: "mousePressed", x: el.x, y: el.y, button: "left", buttons: 1, clickCount: 1 });
    await tab.send("Input.dispatchMouseEvent", { type: "mouseMoved", x: el.x + 20, y: el.y + 10, button: "left", buttons: 1 });
    await act("other", `look ${ids.mcway}; do move ${ids.mcway} to=600,300`);
    await sleep(2000);
    await tab.send("Input.dispatchMouseEvent", { type: "mouseMoved", x: el.x + 80, y: el.y + 40, button: "left", buttons: 1 });
    await tab.send("Input.dispatchMouseEvent", { type: "mouseReleased", x: el.x + 80, y: el.y + 40, button: "left", buttons: 0, clickCount: 1 });
    await sleep(3200);
    const world = await whereOf(ids.mcway);
    const said = await tab.said();
    const painted = await tab.eval(`(() => { const el = [...document.querySelectorAll('[data-key]')].find(e => e.dataset.key.endsWith('/cards/${ids.mcway}'));
      return el ? [parseInt(el.style.left), parseInt(el.style.top)] : null; })()`);
    const d = await tab.lastDo();
    await tab.close();
    const refused = d && d.error ? d.error.slice(0, 200) : null;
    const refusalShown = !!refused && said.includes("refused:");
    const agrees = painted && world && painted[0] === world[0] && painted[1] === world[1];
    return { hit, at: [Math.round(el.x), Math.round(el.y)], sent: d && d.line, world, painted, refused, refusalShown, wrongTarget: !refused && (world[0] !== 600 || world[1] !== 300), pass: !!refused && refusalShown && agrees };
  } };

S.S9 = { what: "keyboard only: move a card on the board", expect: "a keyboard path exists",
  async run(ids) {
    const tab = await Tab.open(lensUrl("board")); await tab.painted(3);
    const before = await whereOf(ids.kirk);
    let reached = false;
    for (let i = 0; i < 20 && !reached; i++) {
      await tab.key("Tab", "Tab", 9);
      const k = await tab.eval("document.activeElement && document.activeElement.dataset ? document.activeElement.dataset.key || '' : ''");
      reached = k.endsWith(`/cards/${ids.kirk}`);
    }
    if (reached) { for (let i = 0; i < 5; i++) await tab.key("ArrowRight", "ArrowRight", 39); await tab.enter(); await sleep(2500); }
    const after = await whereOf(ids.kirk);
    await tab.close();
    const moved = before && after && (after[0] !== before[0] || after[1] !== before[1]);
    return { reached, before, after, pass: reached && moved, note: reached ? "" : "the card is not a Tab stop" };
  } };

S.S10 = { what: "a reader's text selection in one card while another actor retitles a different card", expect: "selection survives",
  async run(ids) {
    const tab = await Tab.open(lensUrl("cal")); await tab.painted(5);
    const el = await tab.find(`/${ids.mcway}/p`);
    await tab.click(el.x, el.y, 2);
    const sel0 = await tab.eval("String(getSelection())");
    await tab.eval("document.querySelectorAll('[data-key]').forEach(e => { e.__old = 1; })");
    await act("other", `look ${ids.kirk}; do retitle ${ids.kirk} title="Kirk Creek"`);
    await sleep(3500);
    const sel1 = await tab.eval("String(getSelection())");
    const remade = await tab.eval("[...document.querySelectorAll('[data-key]')].filter(e => !e.__old).map(e => e.dataset.key)");
    await tab.close();
    return { before: sel0, after: sel1, remade: remade.slice(0, 8), remadeCount: remade.length, pass: !!sel0 && sel0 === sel1 };
  } };

S.S11 = { what: "two windows, one person: edit in window 1 after window 2 changed the same title", expect: "refused, draft kept and resendable",
  async run(ids) {
    const w1 = await Tab.open(lensUrl("cal")); await w1.painted(5);
    const w2 = await Tab.open(lensUrl("cal")); await w2.painted(5);
    const before = await titleOf(ids.mcway);
    await beginEdit(w1, ids.mcway, "McWay Falls (window one)");
    await beginEdit(w2, ids.mcway, "McWay Falls (window two)"); await w2.enter(); await sleep(1500);
    await w1.enter();
    const r = await judgeEdit(w1, ids.mcway, "McWay Falls (window one)", before);
    r.w1dos = (await w1.dos()).map(d => [d.line, d.observed && d.observed.rev, d.error ? d.error.slice(0, 80) : "ok"]); r.w2dos = (await w2.dos()).map(d => [d.line, d.observed && d.observed.rev, d.error ? d.error.slice(0, 80) : "ok"]);
    await w1.close(); await w2.close();
    return { ...r, pass: !!r.refused && r.refusalShown && !r.draftLost && !r.phantom };
  } };

S.S12 = { what: "the lens stops compiling while a person edits; then they edit again on the fallback", expect: "first refused with the draft kept; second refused as a read-only fallback",
  async run(ids) {
    const tab = await Tab.open(lensUrl("cal")); await tab.painted(5);
    const before = await titleOf(ids.kirk);
    await beginEdit(tab, ids.kirk, "Kirk Creek (first try)");
    const broken = ids.calText + "\\nbad : role card, wobble";
    await act("other", `read ${ids.cal}; do rewrite ${ids.cal} text="${broken}"`);
    await tab.enter();
    const r1 = await judgeEdit(tab, ids.kirk, "Kirk Creek (first try)", before);
    await sleep(2000);
    await beginEdit(tab, ids.kirk, "Kirk Creek (second try)"); await tab.enter();
    const r2 = await judgeEdit(tab, ids.kirk, "Kirk Creek (second try)", before);
    const fallbackShown = (await tab.said()).includes("no longer compiles");
    await act("other", `read ${ids.cal}; do rewrite ${ids.cal} text="${ids.calText}"`);   // repair for later scenarios
    await tab.close();
    return { first: r1, second: r2, fallbackShown, pass: [r1, r2].every(r => r.refused && r.refusalShown && !r.draftLost && !r.phantom) };
  } };

// which day column of the calendar lens a card is painted under, read from the scene the server serves
async function dayOf(id) {
  const r = await (await fetch(`${BASE}/api/scene?session=${SESSION}&as=observer&lens=cal`)).json();
  let found = null;
  const walk = n => { if (n.key.endsWith(`/${id}`)) found = n.key.split("/")[2]; (n.kids || []).forEach(walk); };
  if (r.scene) walk(r.scene);
  return found;
}
const dayCol = (tab, n) => tab.eval(`(() => { const e = document.querySelector('[data-key="cal/days/${n}"]'); if (!e) return null;
  const r = e.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + Math.min(r.height - 10, 60) }; })()`);

S.S13 = { what: "carry a card to another day with the pointer (drop)", expect: "the card lands on day 2 through the receiver's own line",
  async run(ids) {
    const tab = await Tab.open(lensUrl("cal")); await tab.painted(5);
    const before = await dayOf(ids.kirk), card = await tab.find(`/items/${ids.kirk}`), to = await dayCol(tab, 2);
    if (!card || !to) return { card, to, keys: await tab.eval("[...document.querySelectorAll('[data-key]')].map(e => e.dataset.key).slice(0, 12)"), said: (await tab.said()).slice(0, 300), pass: false };
    await tab.drag(card.x, card.y + 30, to.x, to.y, 10);
    await sleep(2500);
    const d = await tab.lastDo(), after = await dayOf(ids.kirk), said = await tab.said();
    await tab.close();
    return { before, after, sent: d && d.line, observed: process.env.DEBUG ? d && d.observed : undefined, refused: d && d.error, refusalShown: !!(d && d.error) && said.includes("refused:"), pass: before === "1" && after === "2" };
  } };

S.S19 = { what: "carry a card to another day with keys only: Space, Tab to a day, Enter", expect: "the card lands on the day chosen",
  async run(ids) {
    const tab = await Tab.open(lensUrl("cal")); await tab.painted(5);
    const before = await dayOf(ids.kirk);
    let reached = false;
    for (let i = 0; i < 30 && !reached; i++) {
      await tab.key("Tab", "Tab", 9);
      reached = (await tab.eval("document.activeElement.dataset.key || ''")).endsWith(`/items/${ids.kirk}`);
    }
    await tab.key(" ", "Space", 32);
    let onDay = null;
    for (let i = 0; i < 30 && onDay !== "cal/days/2"; i++) { await tab.key("Tab", "Tab", 9); onDay = await tab.eval("document.activeElement.dataset.key || ''"); }
    await tab.enter(); await sleep(2500);
    const d = await tab.lastDo(), after = await dayOf(ids.kirk), said = await tab.said();
    await tab.close();
    return { reached, onDay, before, after, sent: d && d.line, refused: d && d.error, refusalShown: !!(d && d.error) && said.includes("refused:"), pass: reached && after === "2" };
  } };

S.S20 = { what: "carry a card while another actor moves the trip a week (the day now means another date)", expect: "refused and shown; the card stays on day 1",
  async run(ids) {
    const tab = await Tab.open(lensUrl("cal")); await tab.painted(5);
    const card = await tab.find(`/items/${ids.kirk}`), to = await dayCol(tab, 2);
    await tab.send("Input.dispatchMouseEvent", { type: "mouseMoved", x: card.x, y: card.y + 30 });
    await tab.send("Input.dispatchMouseEvent", { type: "mousePressed", x: card.x, y: card.y + 30, button: "left", buttons: 1, clickCount: 1 });
    await tab.send("Input.dispatchMouseEvent", { type: "mouseMoved", x: card.x + 20, y: card.y + 40, button: "left", buttons: 1 });
    await tab.eval("document.querySelectorAll('[data-key]').forEach(e => { e.__old = 1; })");
    const moved = await act("other", `look ${ids.trip}; do prop ${ids.trip} start=2026-10-17 end=2026-10-19`);
    if (moved.error) throw new Error("the interfering move was refused: " + moved.error.slice(0, 160));
    await sleep(2000);
    const remade = await tab.eval("[...document.querySelectorAll('[data-key]')].filter(e => !e.__old).map(e => e.dataset.key).slice(0, 8)");
    await tab.send("Input.dispatchMouseEvent", { type: "mouseMoved", x: to.x, y: to.y, button: "left", buttons: 1 });
    await tab.send("Input.dispatchMouseEvent", { type: "mouseReleased", x: to.x, y: to.y, button: "left", buttons: 0, clickCount: 1 });
    await sleep(2500);
    const d = await tab.lastDo(), said = await tab.said(), after = await dayOf(ids.kirk);
    const stuck = await tab.eval(`(document.querySelector('[data-carry]') || {style: {}}).style.transform || ""`);
    await tab.close();
    const refused = d && d.error ? d.error.slice(0, 200) : null;
    return { remade, stuck, sent: d && d.line, refused, refusalShown: !!refused && said.includes("refused:"), after, pass: !!refused && said.includes("refused:") && after === "1" };
  } };

S.S14 = { what: "Alex's workspace: type in the chat while a background task finishes and its column repaints",
  expect: "the task column shows the finish while he types; the draft, caret and every untouched element stay put; the message is delivered",
  async run(ids) {
    const tab = await Tab.open(lensUrl("work")); await tab.painted(10);
    const geo = () => tab.eval(`Object.fromEntries([...document.querySelectorAll('[data-key]')].filter(e => !e.dataset.key.includes('/tasks'))
      .map(e => { const r = e.getBoundingClientRect(); return [e.dataset.key, [Math.round(r.x), Math.round(r.y)]]; }))`);
    const code = await tab.eval(`(() => { const el = [...document.querySelectorAll('[data-key]')].find(e => e.dataset.key.endsWith('/${ids.m2}/b'));
      return el ? el.innerText : null; })()`);
    const codeIndentPx = await tab.eval(`(() => { const el = [...document.querySelectorAll('[data-key]')].find(e => e.dataset.key.endsWith('/${ids.m2}/b'));
      const t = el && el.firstChild; if (!t) return null; const i = t.data.indexOf("if d.rev"); const r = document.createRange();
      r.setStart(t, i); r.setEnd(t, i + 1); const x = r.getBoundingClientRect().left; r.setStart(t, 0); r.setEnd(t, 1); return Math.round(x - r.getBoundingClientRect().left); })()`);
    const codeKeepsIndent = !!code && code.includes("    if d.rev") && codeIndentPx > 8;
    const g0 = await geo();
    const el = await tab.find(`/${ids.draft}/b`);
    await tab.click(el.x, el.y); await tab.selectAll();
    await tab.type("Can the fence be per part");
    await act("worker", `look ${ids.task1}; do prop ${ids.task1} status=done`);      // the background task finishes
    await sleep(3500);                                                               // two refresh ticks
    const taskSeen = await tab.pageHas("run the suite · done");
    const focusKept = await tab.eval(`(document.activeElement.dataset.key || '').endsWith('/${ids.draft}/b')`);
    await tab.type(" instead of per lens?");
    const gTyping = await geo();
    const draft = "Can the fence be per part instead of per lens?";
    const typedWhole = await tab.eval(`document.activeElement.textContent`);
    await tab.key("Enter", "Enter", 13, 2);      // lines 1..8: Ctrl+Enter sends; Enter would be a new line
    await sleep(2500);
    const r = await act("observer", `read ${ids.draft}`);
    const delivered = (r.text || "").includes(draft);
    const g1 = await geo();
    const moved = Object.keys(g0).filter(k => g1[k] && !k.includes(`/${ids.draft}/`) && (g0[k][0] !== g1[k][0] || g0[k][1] !== g1[k][1]));
    const deltas = {};      // per region: the largest shift while typing, and after the send and repaint
    for (const k of moved) {
      const reg = k.split("/").slice(0, 2).join("/"), d = deltas[reg] || (deltas[reg] = { n: 0, typing: 0, after: 0 });
      d.n++; d.typing = Math.max(d.typing, Math.abs(gTyping[k][0] - g0[k][0]) + Math.abs(gTyping[k][1] - g0[k][1]));
      d.after = Math.max(d.after, Math.abs(g1[k][0] - g0[k][0]) + Math.abs(g1[k][1] - g0[k][1]));
    }
    const said = await tab.said();
    const collapsible = await tab.eval(`!!document.querySelector('[data-key$="/bar"] > button[aria-expanded]')`);
    if (process.env.SHOTS) writeFileSync(join(HERE, "results", `${process.env.RUN_NAME || "shot"}-S14.png`), Buffer.from((await tab.send("Page.captureScreenshot", { format: "png" })).result.data, "base64"));
    const d = await tab.lastDo();
    await tab.close();
    return { taskSeenWhileTyping: taskSeen, focusKept, typedWhole, delivered, sent: d && d.line, refused: d && d.error,
      movedUntouched: deltas, movedCount: moved.length, codeKeepsIndent, codeIndentPx, barCollapses: collapsible,
      draftLost: !delivered && !(typedWhole || "").includes(draft),
      pass: taskSeen && focusKept && delivered && moved.length === 0 };
  } };

S.S15 = { what: "clear a title to nothing and press Enter (Juniper c347, moment 2)", expect: "sent: delivered, or refused with the refusal shown; never an empty title on screen that the world does not have",
  async run(ids) {
    const tab = await Tab.open(lensUrl("cal")); await tab.painted(5);
    const el = await tab.find(`/${ids.kirk}/t`);
    await tab.click(el.x, el.y); await tab.selectAll(); await tab.key("Backspace", "Backspace", 8); await tab.enter();
    await sleep(2500);
    const world = await titleOf(ids.kirk), d = await tab.lastDo(), said = await tab.said();
    const shown = await tab.eval(`(() => { const e = [...document.querySelectorAll('[data-key]')].find(e => e.dataset.key.endsWith('/${ids.kirk}/t'));
      return e ? { text: e.textContent, unsent: !!e.dataset.unsent } : null; })()`);
    await tab.close();
    const refused = d && d.error ? d.error.slice(0, 200) : null, refusalShown = !!refused && said.includes("refused:");
    const phantom = !!shown && shown.text !== world && !shown.unsent;
    return { sent: d && d.line, world, shown, refused, refusalShown, phantom, pass: !!d && !phantom && (!refused || refusalShown) };
  } };

S.S16 = { what: "a reader's place in a long list while another actor inserts rows above it (Juniper c347, moment 9)", expect: "the card being read stays where it was on screen",
  async run(ids) {
    for (let i = 0; i < 24; i++) await act("fixture", `look ${ids.trip_f}; do create ${ids.trip_f} kind=note title="Stop ${i}" tags=stop`);
    const list = ["list : column, role sheet", `  items : column, of in:${ids.trip_f}, each item`, "item : role card", "  t : role title, text $title"].join("\\n");
    const r = await act("fixture", `look ${ids.lens_f}; do create ${ids.lens_f} kind=note title=list tags=lens text="${list}"`);
    if (r.error) throw new Error(r.error);
    const tab = await Tab.open(lensUrl("list")); await tab.painted(20);
    const target = "Stop 15";
    const at = () => tab.eval(`(() => { const e = [...document.querySelectorAll('[data-key]')].find(e => e.textContent === ${JSON.stringify(target)});
      return e ? Math.round(e.getBoundingClientRect().top) : null; })()`);
    await tab.eval(`(() => { const e = [...document.querySelectorAll('[data-key]')].find(e => e.textContent === ${JSON.stringify(target)});
      const p = document.getElementById('paint'); p.scrollTop += e.getBoundingClientRect().top - p.getBoundingClientRect().top - 100; })()`);
    const y0 = await at();
    const first = (await act("observer", `find tag:stop`)).text.match(/(a\d+) note/)[1];
    for (const t of ["Pfeiffer Beach", "Nepenthe"]) {
      const c = await act("other", `look ${ids.trip_f}; do create ${ids.trip_f} kind=note title="${t}" tags=stop`);
      await act("other", `look ${c.created.at(-1)}; look ${first}; do move ${c.created.at(-1)} before=${first}`);
    }
    await sleep(3500);
    const y1 = await at(), inserted = await tab.pageHas("Nepenthe");
    await tab.close();
    return { target, y0, y1, inserted, pass: inserted && y0 !== null && Math.abs(y1 - y0) <= 2 };
  } };

S.S17 = { what: "coming back: half a title typed, the tab closed, a new tab opened (Juniper c347, moment 7)", expect: "the words are shown where they were typed, marked unsent, and Enter sends them",
  async run(ids) {
    let tab = await Tab.open(lensUrl("cal")); await tab.painted(5);
    const before = await titleOf(ids.kirk), draft = "Kirk Creek, site 4 (ask about";
    await beginEdit(tab, ids.kirk, draft);
    await tab.close(); await sleep(1000);
    const afterClose = await titleOf(ids.kirk);
    tab = await Tab.open(lensUrl("cal")); await tab.painted(5);
    const shown = await tab.eval(`(() => { const e = [...document.querySelectorAll('[data-key]')].find(e => e.dataset.key.endsWith('/${ids.kirk}/t'));
      return e ? { text: e.textContent, unsent: e.dataset.unsent || null } : null; })()`);
    const said = (await tab.said()).split("\n")[0];
    const el = await tab.find(`/${ids.kirk}/t`);
    await tab.click(el.x, el.y); await tab.key("End", "End", 35); await tab.type(" late arrival)"); await tab.enter(); await sleep(2500);
    const world = await titleOf(ids.kirk);
    await tab.close();
    const kept = !!shown && shown.text === draft && !!shown.unsent;
    return { before, afterClose, shown, said, world, kept, pass: kept && world === draft + " late arrival)" };
  } };

S.S18 = { what: "coming back after someone else retitled the card while the tab was closed", expect: "the kept draft is fenced on what it was typed against: refused and shown first, then sent on a second Enter",
  async run(ids) {
    let tab = await Tab.open(lensUrl("cal")); await tab.painted(5);
    const draft = "McWay Falls at sunset";
    await beginEdit(tab, ids.mcway, draft);
    await tab.close(); await sleep(1000);
    await act("other", `look ${ids.mcway}; do retitle ${ids.mcway} title="McWay Falls (trail closed)"`);
    tab = await Tab.open(lensUrl("cal")); await tab.painted(5);
    let el = await tab.find(`/${ids.mcway}/t`);
    await tab.click(el.x, el.y); await tab.enter(); await sleep(2500);
    const first = await tab.lastDo(), said = await tab.said(), mid = await titleOf(ids.mcway), bothShown = said.split(NOTICE_END)[0].includes("McWay Falls (trail closed)");
    el = await tab.find(`/${ids.mcway}/t`);
    await tab.click(el.x, el.y); await tab.enter(); await sleep(2500);
    const world = await titleOf(ids.mcway);
    await tab.close();
    const refused = first && first.error ? first.error.slice(0, 160) : null;
    return { refused, refusalShown: !!refused && said.includes("refused:"), bothShown, mid, world,
      pass: !!refused && said.includes("refused:") && bothShown && mid === "McWay Falls (trail closed)" && world === draft };
  } };

// a request held in the browser's network layer (CDP Fetch), to make an answer slow or lose it (codex team's cases)
async function holdRequests(tab, stage) {
  const paused = [];
  tab.events["Fetch.requestPaused"] = p => paused.push(p);
  await tab.send("Fetch.enable", { patterns: [{ urlPattern: "*/api/do*", requestStage: stage }] });
  return paused;
}
const NOTICE_END = String.fromCharCode(10, 10);   // the notice ends at the first blank line of the inspector
const titleEl = (tab, id) => tab.eval(`(() => { const e = [...document.querySelectorAll('[data-key]')].find(e => e.dataset.key.endsWith('/${id}/t'));
  return e ? { text: e.textContent, unsent: e.dataset.unsent || null } : null; })()`);

S.S21 = { what: "typing more while the first save is still in flight (codex team's delayed answer, on a one-line title)", expect: "nothing typed is lost; the later words go out after the earlier ones, with nothing silent",
  async run(ids) {
    const tab = await Tab.open(lensUrl("cal")); await tab.painted(5);
    await beginEdit(tab, ids.kirk, "Kirk A");
    const paused = await holdRequests(tab, "Request");
    await tab.enter(); await sleep(500);
    const inFlight = paused.length;
    let el = await tab.find(`/${ids.kirk}/t`);
    await tab.click(el.x, el.y); await tab.key("End", "End", 35); await tab.type(" B");
    const typedDuring = (await titleEl(tab, ids.kirk)).text;
    await tab.send("Fetch.disable");
    for (const p of paused) await tab.send("Fetch.continueRequest", { requestId: p.requestId });
    await sleep(2500);
    const afterFirst = await titleOf(ids.kirk), shown = await titleEl(tab, ids.kirk), said1 = (await tab.said()).split("\n")[0];
    let tries = 0;
    while ((await titleOf(ids.kirk)) !== "Kirk A B" && tries < 2) {
      el = await tab.find(`/${ids.kirk}/t`); await tab.click(el.x, el.y); await tab.enter(); await sleep(2500); tries++;
    }
    const world = await titleOf(ids.kirk), dos = (await tab.dos()).map(d => [d.line, d.error ? d.error.slice(0, 90) : "ok"]);
    await tab.close();
    return { inFlight, typedDuring, afterFirst, shown, said1, tries, world, dos,
      pass: inFlight === 1 && afterFirst === "Kirk A" && shown && shown.text === "Kirk A B" && world === "Kirk A B" };
  } };

S.S22 = { what: "the answer to a save is lost after the desk did it (codex team's unknown outcome)", expect: "no claim either way while unknown; once the view repaints and shows the words, nothing is marked unsent and nothing is resent",
  async run(ids) {
    const tab = await Tab.open(lensUrl("cal")); await tab.painted(5);
    await beginEdit(tab, ids.kirk, "Kirk lost answer");
    const paused = await holdRequests(tab, "Response");
    await tab.enter(); await sleep(800);
    await tab.send("Fetch.disable");
    for (const p of paused) await tab.send("Fetch.failRequest", { requestId: p.requestId, errorReason: "ConnectionClosed" });
    await sleep(3500);
    const world = await titleOf(ids.kirk), shown = await titleEl(tab, ids.kirk), said = (await tab.said()).split("\n")[0], sends = (await tab.dos()).length;
    await tab.close();
    return { lost: paused.length, world, shown, said, sends,
      pass: paused.length === 1 && world === "Kirk lost answer" && shown && shown.text === world && !shown.unsent && !/refused/.test(said) };
  } };

S.S23 = { what: "full width (inspect=0): a refusal reaches the live status region when the inspector is hidden (codex team)", expect: "the refusal is visible in a role=status region, and the painter has the whole width",
  async run(ids) {
    const tab = await Tab.open(lensUrl("cal") + "&inspect=0"); await tab.painted(5);
    const widths = await tab.eval("[document.getElementById('paint').clientWidth, window.innerWidth]");
    await beginEdit(tab, ids.mcway, "McWay Falls, full width");
    await act("other", `look ${ids.mcway}; do retitle ${ids.mcway} title="McWay Falls (fog)"`);
    await tab.enter(); await sleep(2500);
    const st = await tab.eval(`(() => { const s = document.getElementById('status'); if (!s) return null; const r = s.getBoundingClientRect();
      return { role: s.getAttribute('role'), live: s.getAttribute('aria-live'), hidden: s.hidden, text: s.textContent.slice(0, 800), w: Math.round(r.width) }; })()`);
    await tab.close();
    return { widths, status: st, pass: widths[0] >= widths[1] - 20 && !!st && st.role === "status" && !st.hidden && st.w > 0 && /refused/.test(st.text) && st.text.includes("McWay Falls (fog)") };
  } };

S.S24 = { what: "keyboard focus on a card that another actor removes (codex team's focus successor, generalised)", expect: "focus lands on a neighbour in the same view, not on the page's top",
  async run(ids) {
    const tab = await Tab.open(lensUrl("board")); await tab.painted(3);
    let reached = false;
    for (let i = 0; i < 20 && !reached; i++) {
      await tab.key("Tab", "Tab", 9);
      reached = (await tab.eval("document.activeElement.dataset.key || ''")).endsWith(`/cards/${ids.kirk}`);
    }
    const r = await act("other", `look ${ids.kirk}; do remove ${ids.kirk}`);
    if (r.error) throw new Error("the interfering remove was refused: " + r.error.slice(0, 160));
    await sleep(3500);
    const after = await tab.eval("document.activeElement === document.body ? 'body' : (document.activeElement.dataset.key || document.activeElement.tagName)");
    await tab.close();
    return { reached, after, pass: reached && after !== "body" && after.startsWith("board") };
  } };

S.S25 = { what: "Alex's collapsed bar: folded by the lens, opened by him, kept across a reload and another person's act, never an event, never another viewer's", expect: "each of those holds",
  async run(ids) {
    const total = async () => (await (await fetch(`${BASE}/api/scene?session=${SESSION}&as=observer&lens=work`)).json()).events_total;
    const barState = tab => tab.eval(`(() => { const b = document.querySelector('[data-key$="/bar"]'); if (!b) return null;
      const h = b.querySelector(':scope > button[aria-expanded]'), items = [...b.children].filter(c => c.dataset.key);
      return { folded: !!b.dataset.folded, expanded: h && h.getAttribute('aria-expanded'), visible: items.filter(c => c.offsetParent).length, w: Math.round(b.getBoundingClientRect().width) }; })()`);
    const e0 = await total();
    let tab = await Tab.open(lensUrl("work") + "&inspect=0"); await tab.painted(8);
    const start = await barState(tab);
    await tab.eval(`document.querySelector('[data-key$="/bar"] > button').focus()`);
    await tab.key(" ", "Space", 32); await sleep(300);                       // a real control: Space opens it
    const opened = await barState(tab);
    await act("other", `find tag:project`).then(async r => { const id = r.text.match(/(a\d+) note/)[1]; await act("other", `look ${id}; do retitle ${id} title="Agora4 (renamed)"`); });
    await sleep(3200);
    const afterAct = await barState(tab);
    await tab.close();
    tab = await Tab.open(lensUrl("work") + "&inspect=0"); await tab.painted(8);
    const reloaded = await barState(tab);
    await tab.close();
    const other = await Tab.open(lensUrl("work", "juniper") + "&inspect=0"); await other.painted(8);
    const othersView = await barState(other);
    await other.close();
    const events = (await total()) - e0 - 1;                                  // minus the one retitle
    return { start, opened, afterAct, reloaded, othersView, foldEvents: events,
      pass: !!start && start.folded && start.visible === 0 && opened.expanded === "true" && opened.visible === 3 && afterAct.visible === 3
        && reloaded.visible === 3 && othersView.folded && events === 0 };
  } };

S.S26 = { what: "Juniper's c359 sequence: a held title, a peer retitles it, Enter (refused), Enter again with no typing, then a letter and Enter", expect: "the peer's title is painted beside the kept words before the second Enter counts; no step overwrites words the person was not shown",
  async run(ids) {
    const tab = await Tab.open(lensUrl("cal")); await tab.painted(5);
    const mine = "McWay Falls, mine", theirs = "McWay Falls, theirs";
    await beginEdit(tab, ids.mcway, mine);
    await act("other", `look ${ids.mcway}; do retitle ${ids.mcway} title="${theirs}"`);
    await tab.enter(); await sleep(2500);
    const step1 = { world: await titleOf(ids.mcway), refused: !!(await tab.lastDo()).error };
    const card = () => tab.eval(`(() => { const e = [...document.querySelectorAll('[data-key]')].find(e => e.dataset.key.endsWith('/${ids.mcway}/t'));
      return e ? { text: e.textContent, after: getComputedStyle(e, '::after').content, unsent: !!e.dataset.unsent } : null; })()`);
    const beside = await card();
    let el = await tab.find(`/${ids.mcway}/t`);
    await tab.click(el.x, el.y); await tab.enter(); await sleep(2500);
    const step2 = { world: await titleOf(ids.mcway), refused: !!(await tab.lastDo()).error };
    el = await tab.find(`/${ids.mcway}/t`);
    await tab.click(el.x, el.y); await tab.key("End", "End", 35); await tab.type("!"); await tab.enter(); await sleep(2500);
    const step3 = { world: await titleOf(ids.mcway), refused: !!(await tab.lastDo()).error };
    await tab.close();
    const theirsBeside = !!beside && beside.text === mine && beside.after.includes(theirs);
    return { step1, beside, theirsBeside, step2, step3,
      pass: step1.refused && step1.world === theirs && theirsBeside && step2.world === mine && step3.world === mine + "!" };
  } };

S.S27 = { what: "the chat input with lines 1..8: Enter makes a new line, Ctrl+Enter sends both lines", expect: "one send, with both lines, only on Ctrl+Enter",
  async run(ids) {
    const tab = await Tab.open(lensUrl("work") + "&inspect=0"); await tab.painted(8);
    const el = await tab.find(`/${ids.draft}/b`);
    await tab.click(el.x, el.y); await tab.selectAll(); await tab.type("line one");
    await tab.enter(); await tab.type("line two"); await sleep(400);
    const sentAfterEnter = (await tab.dos()).length;
    await tab.key("Enter", "Enter", 13, 2); await sleep(2500);
    const d = await tab.lastDo(), r = await act("observer", `read ${ids.draft}`);
    const lines = ((r.text || "").split("---")[1] || "").trim().split("\n");
    await tab.close();
    return { sentAfterEnter, sent: d && d.line, lines, pass: sentAfterEnter === 0 && lines[0] === "line one" && lines[1] === "line two" };
  } };

S.S28 = { what: "a message with a code run: click inside the code, type, send, and take it in hand again (Jeff and Juniper, 870ec2d)", expect: "runs while reading, source in hand, and the caret and a selection land on the same characters across the swap",
  async run(ids) {
    const src = "Try `do prop a31` first, then look.";
    const c = await act("fixture", `look ${ids.work_f}; do create ${ids.work_f} kind=note title="you" tags=chat text="${src}"`);
    const msg = c.created.at(-1);
    const tab = await Tab.open(lensUrl("work") + "&inspect=0"); await tab.painted(8);
    const drawn = await tab.eval(`(() => { const e = [...document.querySelectorAll('[data-key]')].find(e => e.dataset.key.endsWith('/${msg}/b')); const s = e && e.querySelector('span');
      return e ? { text: e.textContent, code: s ? s.textContent : null, codeClass: s ? s.className : null } : null; })()`);
    // 1. a click on the "p" of "prop", inside the code run, then one typed letter
    const pt = await tab.eval(`(() => { const e = [...document.querySelectorAll('[data-key]')].find(e => e.dataset.key.endsWith('/${msg}/b')); const s = e.querySelector('span'); if (!s) return null;
      const r = document.createRange(); r.setStart(s.firstChild, 3); r.setEnd(s.firstChild, 4); const b = r.getBoundingClientRect(); return { x: b.left + 1, y: b.top + b.height / 2 }; })()`);
    if (!pt) return { drawn, pass: false, note: "no code run drawn" };
    await tab.click(pt.x, pt.y);
    const inHand = await tab.eval(`(() => { const s = getSelection(); return { text: document.activeElement.textContent, offset: s.anchorOffset }; })()`);
    await tab.key("X", "KeyX", 88); await tab.type("X");      // a key that writes (the swap happens here), then its character
    const typed = await tab.eval(`[document.activeElement.textContent, getSelection().anchorOffset]`);
    await tab.key("Enter", "Enter", 13, 2); await sleep(2500);   // this message has lines 1..8: Ctrl+Enter sends
    const r = await act("observer", `read ${msg}`), world = ((r.text || "").split("---")[1] || "").trim();
    const again = await tab.eval(`(() => { const e = [...document.querySelectorAll('[data-key]')].find(e => e.dataset.key.endsWith('/${msg}/b')); const s = e && e.querySelector('span'); return s ? s.textContent : null; })()`);
    // 2. a double-click selects "first" while reading; taking it in hand keeps the same selection on the source
    const w = await tab.eval(`(() => { const e = [...document.querySelectorAll('[data-key]')].find(e => e.dataset.key.endsWith('/${msg}/b'));
      const t = [...e.childNodes].find(n => n.nodeType === 3 && n.data.includes('first')); if (!t) return null; const i = t.data.indexOf('first');
      const r = document.createRange(); r.setStart(t, i + 1); r.setEnd(t, i + 2); const b = r.getBoundingClientRect(); return { x: b.left + 1, y: b.top + b.height / 2 }; })()`);
    let sel = null;
    if (w) { await tab.click(w.x, w.y, 2); await sleep(200); sel = await tab.eval(`[String(getSelection()), document.activeElement.textContent]`); }
    await tab.close();
    const expected = "Try `do Xprop a31` first, then look.";
    return { drawn, inHand, typed, world, again, selection: sel,
      pass: !!drawn && drawn.code === "do prop a31" && typed[0] === expected && world === expected
        && inHand.offset === 3 && again === "do Xprop a31" && !!sel && sel[0].trim() === "first" };
  } };

// Juniper's three classes (a313), so the suite's runner can count these beside its CLI readers:
// holds; wrong and silent (the person is not told: a lost draft, a phantom, an unseen refusal, a selection or a
// newer fact quietly gone); wrong but visible (the gap is plain on screen: no Tab stop, no word for it, a refusal shown).
function verdict(r) {
  if (r.pass) return "holds";
  const parts = [r, r.first, r.second].filter(Boolean);
  const silent = parts.some(p => p.draftLost || p.phantom || (p.refused && !p.refusalShown)) ||
    (r.before && r.after === "") || r.taskSeenWhileTyping === false || r.movedCount > 0;
  return r.error ? "harness error" : silent ? "wrong, silent" : "wrong, visible";
}

// ---------------------------------------------------------------- run
async function main() {
  const only = process.argv.slice(2);
  mkdirSync(join(HERE, "results"), { recursive: true });
  // Pike (run h): another deskd was already listening on this suite's old port 8795 with older code and its own worlds;
  // on Windows a second server can bind the same port (SO_REUSEADDR), so the suite talked to it unknowingly.
  // The port must be free before this deskd starts, and must be this deskd's.
  const busy = await fetch(`${BASE}/lens.html`).then(() => true, () => false);
  if (busy) throw new Error(`port ${PORT} already has a server; this suite needs its own deskd (set PORT=...)`);
  const deskd = spawn(PY, ["deskd.py", String(PORT)], { cwd: NOTATION, stdio: ["ignore", "ignore", "pipe"] });
  let exited = false; deskd.on("exit", () => { exited = true; });
  let deskdErr = ""; deskd.stderr.on("data", d => { deskdErr += d; });
  for (let i = 0; i < 50; i++) { try { await fetch(`${BASE}/lens.html`); break; } catch { await sleep(200); } }
  if (exited) throw new Error("this suite's deskd exited at start (see its stderr)");
  const out = { when: new Date().toISOString(), chrome: CHROME, session: BASE_SESSION + "-<scenario>", scenarios: {} };
  try {
    const v = await startChrome();
    out.browser = v.Browser;
    const names = Object.keys(S).filter(k => !only.length || only.includes(k));
    for (const name of names) {
      let r;
      SESSION = `${BASE_SESSION}-${name.toLowerCase()}`;
      rmSync(join(NOTATION, "sessions", `${SESSION}.pickle`), { force: true });   // left by a run that crashed
      try { r = await S[name].run(await fixture()); }       // every scenario starts from the same world
      catch (e) { r = { error: String(e.message || e) + (e.cause ? " / " + e.cause.message : ""), pass: false }; }
      out.scenarios[name] = { what: S[name].what, expect: S[name].expect, verdict: verdict(r), ...r };
      const flag = verdict(r).padEnd(14);
      console.log(`${name.padEnd(4)} ${flag}  ${S[name].what}\n      ${JSON.stringify(r)}`);
    }
  } finally {
    if (chrome) chrome.kill();
    deskd.kill();
    await sleep(500);
    if (!process.env.KEEP) for (const name of Object.keys(S)) for (const ext of ["pickle", "lock"])      // the suite's worlds are scratch (KEEP=1 keeps them)
      rmSync(join(NOTATION, "sessions", `${BASE_SESSION}-${name.toLowerCase()}.${ext}`), { force: true });
  }
  out.deskdStderr = deskdErr.slice(-4000);
  if (deskdErr) console.log("deskd stderr (tail): " + deskdErr.slice(-1500));
  const f = join(HERE, "results", (process.env.RUN_NAME || out.when.slice(0, 16).replace(":", "")) + ".json");
  writeFileSync(f, JSON.stringify(out, null, 2));
  const all = Object.values(out.scenarios);
  console.log(`\n${all.filter(s => s.pass).length} of ${all.length} hold · lost drafts ${all.filter(s => s.draftLost || (s.first && s.first.draftLost)).length}` +
    ` · phantoms ${all.filter(s => s.phantom || (s.first && s.first.phantom)).length}` +
    ` · refusals not shown ${all.flatMap(s => [s, s.first, s.second]).filter(s => s && s.refused && !s.refusalShown).length} · results ${f}`);
}
main().catch(e => { console.error(e); process.exit(1); });
