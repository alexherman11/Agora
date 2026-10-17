// checks/textedit_core.js (a6067): the continuous-text module's core and its plain surface, in a real page (its own
// events), against a stand-in desk that orders whole-text rewrites fenced by version (what the real seam does today;
// test_textedit.py checks deskd itself refuses a stale rewrite). One expression, for screen.py's `js @<this file>`;
// it answers the lines it printed. test_textedit_paint.py runs it.
//
// Imagined use: Alex writes in a document in two windows of his home base while Pike, a resident, fixes a word in it
// with `do replace`; Alex types Japanese through an input method, € with AltGr, and presses Ctrl+Z twice.
(async () => {
const T = globalThis.TextEdit, M = globalThis.Markdown, out = [];
let fails = 0;
const check = (name, ok, detail = "") => { out.push((ok ? "ok   " : "FAIL ") + name + (ok ? "" : "\n     " + JSON.stringify(detail).slice(0, 900))); if (!ok) fails++; };
const tick = (ms = 15) => new Promise(r => setTimeout(r, ms));

// ---- a stand-in desk: one text, a version, whole-text rewrites fenced by it, a resident's replace of quoted words
function Desk(text) {
  return { text, version: 1, n: 0, log: [],
    send(out) {
      if (out.version !== this.version) return { ok: false, error: `refused: the document changed since this was painted (you saw ${out.version}, it is now ${this.version})` };
      this.text = out.text; this.version++; const e = "e" + (100 + ++this.n); this.log.push([e, out.text]); return { ok: true, event: e };
    },
    replace(old, nw) {
      const i = this.text.indexOf(old);
      if (i < 0) return "ERR the words are not in it";
      if (this.text.indexOf(old, i + 1) >= 0) return "ERR the words stand twice";
      this.text = this.text.slice(0, i) + nw + this.text.slice(i + old.length); this.version++; return "ok";
    } };
}
class Input extends EventTarget {
  constructor(v = "") { super(); this.value = v; this.selectionStart = this.selectionEnd = v.length; }
  setSelectionRange(a, b) { this.selectionStart = a; this.selectionEnd = b; }
}
const ev = (t, p = {}) => Object.assign(new Event(t, { cancelable: true }), p);
// as a browser types: beforeinput, the box changes, input
function type(inp, s, extra = {}) {
  for (const ch of s) {
    const a = inp.selectionStart, b = inp.selectionEnd;
    if (!inp.dispatchEvent(ev("beforeinput", { inputType: "insertText", data: ch }))) continue;
    inp.value = inp.value.slice(0, a) + ch + inp.value.slice(b); inp.selectionStart = inp.selectionEnd = a + ch.length;
    inp.dispatchEvent(ev("input", { inputType: "insertText", ...extra }));
  }
}
const caretAt = (inp, n) => { inp.selectionStart = inp.selectionEnd = n; inp.dispatchEvent(ev("select")); };
// one window: its own keeper slot (a Map standing in for viewer.js's per-window store), its own words said
function Window(desk, name, gate) {
  const slot = new Map(), said = [], undone = [];
  const inp = new Input(desk.text);
  const te = T.attach(inp, { text: desk.text, version: desk.version, pause: 1,
    keep: { load: () => slot.get("doc") || {}, save: st => slot.set("doc", st) },
    seam: { send: async out => { if (gate) await gate(); return desk.send(out); } },
    hooks: { notify: t => said.push(t), undoSent: e => undone.push(e) } });
  return { name, inp, te, slot, said, undone, show: () => te.receive(desk.text, desk.version) };
}

// ---- 1. the difference of two texts: two edits on two lines stay two
{
  const a = "# Plan\nWe build it.\nThen we test it.\n", b = "# Plan\nWe build it today.\nThen we test it well.\n";
  const d = T.diff(a, b);
  check("diff: two edits on two lines are two edits", d.length === 2 && T.apply(a, d) === b, d);
  const big = Array.from({ length: 400 }, (_, i) => `line ${i}\n`).join(""), big2 = big.replace("line 7\n", "line seven\n").replace("line 390\n", "");
  const d2 = T.diff(big, big2);
  check("diff: a long text, an edit near each end", d2.length === 2 && T.apply(big, d2) === big2, d2);
}
// ---- 2. fitting: apart, at one point, overlapping
{
  const base = "The cat sat on the mat.";
  const r = T.fit(base, base.replace("cat", "dog"), base + " It purred", [base.length + 10, base.length + 10]);
  check("fit: the desk's edit elsewhere goes in, mine stay, the caret moves with my words",
    r.text === "The dog sat on the mat. It purred" && r.sel[0] === r.text.length, r);
  const r2 = T.fit(base, base + " (Pike)", base + " Mine", [base.length + 5, base.length + 5]);
  check("fit: both writing at one point: the desk's first, mine after, the caret after mine", r2.text === base + " (Pike) Mine" && r2.sel[0] === r2.text.length, r2);
  const r3 = T.fit(base, base.replace("sat on", "lay on"), base.replace("sat", "stood"), null);
  check("fit: the same words changed by both: a conflict, never a merged guess", !!r3.conflict, r3);
}

// ---- 3. a resident's replace over live typing, words apart: fitted, then sent against the new version
{
  const desk = Desk("Intro.\n\nThe plan is to bild it.\n");
  const A = Window(desk, "A");
  caretAt(A.inp, 6); type(A.inp, " Written by Alex.");
  check("typing: unsent words held, nothing sent yet", A.te.doc.dirty && desk.text === "Intro.\n\nThe plan is to bild it.\n");
  const pike = desk.replace("bild", "build");            // Pike fixes a typo while Alex types
  check("the resident's replace is done in the world", pike === "ok" && desk.version === 2);
  A.show();
  check("Alex's window fits it: both edits in his words", A.inp.value === "Intro. Written by Alex.\n\nThe plan is to build it.\n", A.inp.value);
  check("his caret stayed at the end of his own words", A.te.doc.sel[0] === "Intro. Written by Alex.".length, A.te.doc.sel);
  check("he is told it was fitted", A.said.some(s => /fitted over yours/.test(s)), A.said);
  await A.te.flush();
  check("then sent against version 2, and the desk holds both", desk.text === "Intro. Written by Alex.\n\nThe plan is to build it.\n" && desk.version === 3, desk);
}

// ---- 4. the resident's replace lands while Alex's send is on its way: refused, fitted, sent again
{
  const desk = Desk("Alpha beta gamma.\nDelta.\n");
  let open; const held = new Promise(r => { open = r; });
  let first = true;
  const A = Window(desk, "A", async () => { if (first) { first = false; await held; } });
  caretAt(A.inp, "Alpha beta gamma.\nDelta".length); type(A.inp, " epsilon");
  const out = A.te.flush();                               // on its way
  desk.replace("beta", "BETA");                           // Pike's lands first
  open(); const r = await out;
  check("the stale send is refused by the fence", r && !r.ok && /refused/.test(r.error), r);
  check("nothing of Alex's was lost", A.inp.value.includes(" epsilon"));
  A.show(); await tick(); await A.te.flush();
  check("fitted and sent again: the desk has both", desk.text === "Alpha BETA gamma.\nDelta epsilon.\n", desk.text);
}

// ---- 5. the resident replaces the very words Alex is typing in: refused loudly, nothing sent until he chooses
{
  const desk = Desk("We will ship on Friday.\n");
  const A = Window(desk, "A");
  caretAt(A.inp, "We will ship on Fri".length); A.inp.selectionStart = "We will ship on ".length; A.inp.selectionEnd = "We will ship on Friday".length;
  type(A.inp, "Monday");
  desk.replace("on Friday", "next week");
  A.show();
  check("a conflict: his words kept, unsent", A.te.doc.conflict && A.inp.value === "We will ship on Monday.\n", A.te.doc);
  check("said loudly", A.said.some(s => /^CONFLICT/.test(s)), A.said);
  const r = await A.te.flush();
  check("nothing is sent over a conflict", r === null && desk.text === "We will ship next week.\n");
  A.te.resolve("theirs");
  check("Take theirs: his unsent words go, the box shows the desk's", A.inp.value === desk.text && !A.te.doc.dirty);
  // typing just after the words a resident replaced is not in them: fitted, not a conflict
  caretAt(A.inp, "We will ship next week".length); type(A.inp, "!");
  desk.replace("next week", "soon"); A.show();
  check("typing right after the replaced words is fitted (it touched none of them)", !A.te.doc.conflict && A.inp.value === "We will ship soon!.\n", A.inp.value);
  await A.te.flush();
  // and the other choice, in a second round: he writes over "soon" while Pike changes it
  A.inp.selectionStart = "We will ship ".length; A.inp.selectionEnd = "We will ship soon".length; type(A.inp, "today");
  desk.replace("soon!", "in May!"); A.show();
  check("a second conflict", !!A.te.doc.conflict);
  A.te.resolve("mine"); await tick(); await A.te.flush();
  check("Keep mine: his words are sent over theirs, as he chose", desk.text === "We will ship today!.\n", desk.text);
}

// ---- 6. two windows on one document: their own carets and unsent words, both edits kept
{
  const desk = Desk("Top.\nBottom.\n");
  const A = Window(desk, "A"), B = Window(desk, "B");
  caretAt(A.inp, 0); type(A.inp, "A: ");
  caretAt(B.inp, desk.text.length); type(B.inp, "B was here.\n");
  await A.te.flush();
  check("A's edit is in the world", desk.text === "A: Top.\nBottom.\n");
  const r = await B.te.flush();
  check("B's send, typed on the old version, is refused (fenced), not written over A's", !r.ok && desk.text === "A: Top.\nBottom.\n", r);
  B.show(); A.show(); await tick(); await B.te.flush(); A.show(); B.show();
  check("B fits A's edit and sends: both in the world", desk.text === "A: Top.\nBottom.\nB was here.\n", desk.text);
  check("both windows show the world's words", A.inp.value === desk.text && B.inp.value === desk.text);
  check("each window's caret is its own (A at its start, B at the end)", A.te.doc.sel[0] === 3 && B.te.doc.sel[0] === desk.text.length, [A.te.doc.sel, B.te.doc.sel]);
  check("each window kept its state in its own slot", A.slot.get("doc").sel[0] === 3 && B.slot.get("doc").sel[0] === desk.text.length);
}

// ---- 7. an input method (IME): the composed words go in as one edit; the desk's words wait for it
{
  const desk = Desk("Notes:\n");
  const A = Window(desk, "A");
  caretAt(A.inp, desk.text.length);
  A.inp.dispatchEvent(ev("compositionstart"));
  for (const step of ["に", "にほ", "にほん", "日本"]) {      // the input method rewrites its own words
    const at = "Notes:\n".length; A.inp.value = "Notes:\n" + step; A.inp.selectionStart = A.inp.selectionEnd = at + step.length;
    A.inp.dispatchEvent(ev("input", { inputType: "insertCompositionText", isComposing: true }));
  }
  desk.replace("Notes:", "Notes (Pike):"); A.show();
  check("while composing, the desk's words wait (the box is not rewritten under the input method)", A.inp.value === "Notes:\n日本", A.inp.value);
  check("and nothing is sent mid-composition", (await A.te.flush()) === null);
  A.inp.dispatchEvent(ev("compositionend", { data: "日本" }));
  check("at its end: the composed words, then the desk's fitted", A.inp.value === "Notes (Pike):\n日本", A.inp.value);
  const u = A.te.doc.undo.length;
  A.inp.dispatchEvent(ev("keydown", { key: "z", ctrlKey: true }));
  check("one Ctrl+Z takes the composed word away whole", A.inp.value === "Notes (Pike):\n" && u >= 1, A.inp.value);
}

// ---- 8. AltGr: Ctrl+Alt is never a shortcut; its character arrives as text
{
  const desk = Desk("Price: ");
  const A = Window(desk, "A");
  type(A.inp, "5");
  const k = ev("keydown", { key: "€", ctrlKey: true, altKey: true, getModifierState: m => m === "AltGraph" });
  A.inp.dispatchEvent(k);
  check("AltGr+E (€) is not taken as a shortcut", !k.defaultPrevented);
  type(A.inp, "€");
  check("the € arrives as text", A.inp.value === "Price: 5€", A.inp.value);
  const z = ev("keydown", { key: "z", ctrlKey: true, altKey: true });
  A.inp.dispatchEvent(z);
  check("Ctrl+Alt+Z does nothing here (Ctrl+Alt belongs to the window manager)", !z.defaultPrevented && A.inp.value === "Price: 5€");
  check("shortcut(): AltGraph held with Ctrl is null; plain Ctrl+B is Ctrl+b",
    T.shortcut({ key: "b", ctrlKey: true, getModifierState: () => true }) === null && T.shortcut({ key: "b", ctrlKey: true }) === "Ctrl+b");
}

// ---- 9. two undos and their seam: unsent keys first, then the desk's undo of the last sent edit, each said
{
  const desk = Desk("Hello");
  const A = Window(desk, "A");
  type(A.inp, " world");
  A.inp.dispatchEvent(ev("keydown", { key: "z", ctrlKey: true }));
  check("Ctrl+Z undoes the unsent typing", A.inp.value === "Hello" && /unsent typing/.test(A.said.at(-1)), A.said.at(-1));
  type(A.inp, "!"); await A.te.flush();
  A.inp.dispatchEvent(ev("keydown", { key: "z", ctrlKey: true }));
  check("with nothing unsent, Ctrl+Z asks the desk to undo the sent edit, and says so", A.undone[0] === "e101" && /asked the desk to undo e101/.test(A.said.at(-1)), [A.undone, A.said.at(-1)]);
  A.inp.dispatchEvent(ev("keydown", { key: "z", ctrlKey: true }));
  check("and then says there is nothing left of its own to undo", /nothing to undo/.test(A.said.at(-1)), A.said.at(-1));
}

// ---- 10. a window closed with unsent words, opened after a resident's edit: kept, fitted
{
  const desk = Desk("One.\nTwo.\n");
  const slot = new Map([["doc", { text: "One.\nTwo.\nThree.\n", base: "One.\nTwo.\n", version: 1, sel: [16, 16] }]]);
  desk.replace("One.", "Uno.");
  const te = T.attach(new Input(desk.text), { text: desk.text, version: desk.version, keep: { load: () => slot.get("doc"), save: st => slot.set("doc", st) } });
  check("a kept draft is fitted over what changed while the window was closed", te.src() === "Uno.\nTwo.\nThree.\n", te.src());
  const slot2 = new Map([["doc", { text: "Draft from before" }]]);
  const te2 = T.attach(new Input("Now"), { text: "Now", version: 4, keep: { load: () => slot2.get("doc"), save: () => {} } });
  check("a draft with no record of what it was typed on is a conflict, never sent as it is", !!te2.doc.conflict && te2.doc.outgoing() === null);
}

// ---- 11. the Markdown grammar's edits (markdown.js, now edits only)
{
  const e = M.enter("- one", 5, 5);
  check("Enter continues a list", e.s === "\n- " && e.at === 8, e);
  const t = M.toggle("- [ ] milk", 0);
  check("a task box toggles [ ] to [x]", T.apply("- [ ] milk", [t]) === "- [x] milk");
  const w = M.wrap("a word here", 2, 6, "**", "**"), back = T.apply("a word here", [w]);
  check("Ctrl+B wraps, and again unwraps", back === "a **word** here" && T.apply(back, [M.wrap(back, 4, 8, "**", "**")]) === "a word here");
}

const passed = out.filter(l => l.startsWith("ok")).length;
return out.filter(l => !l.startsWith("ok")).concat([fails ? `${passed} passed, ${fails} FAILED` : `all ${passed} passed`]).join("\n");
})()
