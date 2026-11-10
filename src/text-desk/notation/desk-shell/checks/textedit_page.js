// checks/textedit_page.js (a6067): the continuous-text module in the real painter, on a page showing lens te-probe
// (made by test_textedit_paint.py: one document, `markdown` with `on edit` = whole-text rewrite, and a chat composer).
// One expression for screen.py's `js @<this file>`; it answers the lines it printed. A resident (pike) acts through
// the same door as the page, at the moments a person types.
(async () => {
  const q = new URLSearchParams(location.search), session = q.get("session"), out = [];
  let fails = 0;
  const check = (name, ok, detail = "") => { out.push((ok ? "ok   " : "FAIL ") + name + (ok ? "" : "\n     " + JSON.stringify(detail).slice(0, 700))); if (!ok) fails++; };
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const desk = async (as, line) => (await fetch("/api/do", { method: "POST", body: JSON.stringify({ session, as, line }) })).json();
  const until = async (test, ms = 6000) => { const t0 = Date.now(); while (Date.now() - t0 < ms) { if (test()) return true; await sleep(100); } return false; };
  const part = (d = document) => d.querySelector(".md-part"), md = (d = document) => d.querySelector(".md-doc");
  const painted = (d = document) => part(d)._n.paint.text, mine = (d = document) => part(d)._te.doc.text;
  const said = () => (document.getElementById("said").textContent || "") + " " + (document.getElementById("status").textContent || "");
  const caret = (at, to = at, d = document) => { const el = md(d); el.focus(); const src = mine(d), M = d.defaultView.Markdown;
    const [n1, o1] = M.pointAt(el, src, at), [n2, o2] = M.pointAt(el, src, to); d.getSelection().setBaseAndExtent(n1, o1, n2, o2); };
  // a key's words as the browser offers them to an editor (beforeinput insertText); a textarea takes execCommand
  const write = (s, d = document) => { const t = d.activeElement;
    if (t && t.isContentEditable) return t.dispatchEvent(new d.defaultView.InputEvent("beforeinput", { inputType: "insertText", data: s, bubbles: true, cancelable: true }));
    return d.execCommand("insertText", false, s); };
  const id = part()._n.fence.item;
  const pike = async line => { await desk("pike", `read ${id}`); return desk("pike", line); };

  // 1. a real key path: the words typed are sent as the person pauses (whole text, fenced)
  caret(6); write(" Written by Alex.");
  check("typed words are unsent at first, kept in the module", mine().includes("Written by Alex.") && !painted().includes("Written"));
  // 2. the resident replaces other words while those are still unsent
  const r1 = await pike('do replace ' + id + ' old="bild" new="build"');
  check("the resident's replace is done in the world", !r1.error, r1);
  await until(() => painted() === "Intro. Written by Alex.\n\nThe plan is to build it.\n");
  check("both edits stand in the world: his fitted over Pike's, sent against the new version",
    painted() === "Intro. Written by Alex.\n\nThe plan is to build it.\n", painted());
  check("the page draws the same words", md().textContent.includes("Written by Alex.") && md().textContent.includes("build it"));

  // 3. the resident replaces the very words he is changing: a conflict, loud, nothing sent until he chooses
  const at = mine().indexOf("build"); caret(at, at + 5); write("make");
  const r2 = await pike('do replace ' + id + ' old="build it" new="ship it"');
  await until(() => !document.querySelector(".te-conflict").hidden);
  check("a conflict bar shows, his words kept", !document.querySelector(".te-conflict").hidden && mine().includes("make it"), [r2, mine()]);
  const bt = document.querySelector(".te-conflict span").textContent;
  check("the bar names the words in dispute: what was there, theirs, his", /“build”/.test(bt) && /theirs: “ship”/.test(bt) && /yours \(unsent\): “make”/.test(bt), bt);
  await sleep(1500);
  check("nothing of his is sent over Pike's while it stands", painted().includes("ship it") && !painted().includes("make"), painted());
  [...document.querySelectorAll(".te-conflict button")].find(b => b.textContent === "Take theirs").click();
  check("Take theirs: his words are the world's again", mine() === painted() && document.querySelector(".te-conflict").hidden, mine());
  // and Keep mine: his words go over Pike's, and the thing says so, so Pike learns his words did not stand (Pike c6122)
  const at2 = mine().indexOf("ship"); caret(at2, at2 + 4); write("launch");
  await pike('do replace ' + id + ' old="ship it" new="send it"');
  await until(() => !document.querySelector(".te-conflict").hidden);
  [...document.querySelectorAll(".te-conflict button")].find(b => b.textContent === "Keep mine").click();
  await until(() => painted().includes("launch it"));
  await sleep(800);
  const ex = await desk("pike", `examine ${id}`);
  check("Keep mine: his words stand, and a comment on the document tells what was set aside",
    painted().includes("launch it") && /kept their own words over a change/.test(ex.text || "") && /“ship” → “send”/.test(ex.text || ""), [painted(), (ex.text || "").slice(0, 600)]);
  caret(mine().indexOf("launch"), mine().indexOf("launch") + 6); write("ship"); await until(() => painted().includes("ship it"));

  // 4. an input method: the composed words stay while it composes; the desk's words wait, then are fitted
  caret(mine().length); const el = md();
  el.dispatchEvent(new CompositionEvent("compositionstart", { bubbles: true, data: "" }));
  const line = [...el.children].filter(c => c.dataset.l != null).at(-1), tn = document.createTextNode("日本");
  (line.querySelector(".md-body") || line).append(tn);                         // what the input method writes
  await pike('do replace ' + id + ' old="Intro." new="Intro:"');
  await sleep(1800);
  check("while composing, the page is not drawn again under the input method", tn.isConnected && md().textContent.includes("日本") && !md().textContent.includes("Intro:"));
  el.dispatchEvent(new CompositionEvent("compositionend", { bubbles: true, data: "日本" }));
  await until(() => painted().includes("日本") && painted().includes("Intro:"));
  check("at its end the composed words and Pike's both stand", painted().includes("日本") && painted().startsWith("Intro:"), painted());

  // 5. AltGr (Ctrl+Alt on Windows): never a shortcut; its character is text
  caret(mine().length);
  const k1 = new KeyboardEvent("keydown", { key: "€", ctrlKey: true, altKey: true, bubbles: true, cancelable: true });
  const k2 = new KeyboardEvent("keydown", { key: "e", ctrlKey: true, altKey: true, bubbles: true, cancelable: true });
  md().dispatchEvent(k1); md().dispatchEvent(k2);
  check("AltGr+E and Ctrl+Alt+E are not taken (Source did not toggle)", !k1.defaultPrevented && !k2.defaultPrevented && !md().classList.contains("md-raw"));
  write("€");
  check("the € arrives as text", mine().endsWith("€") || mine().includes("€"), mine());

  // 6. two undos and their seam
  await until(() => painted() === mine());
  write("XYZ");
  md().dispatchEvent(new KeyboardEvent("keydown", { key: "z", ctrlKey: true, bubbles: true, cancelable: true }));
  check("Ctrl+Z takes away the unsent typing, and says so", !mine().includes("XYZ") && /undid unsent typing/.test(said()), said().slice(0, 200));
  write("Q"); await until(() => painted().endsWith("Q") || painted().includes("€Q"));
  const before = painted();
  md().dispatchEvent(new KeyboardEvent("keydown", { key: "z", ctrlKey: true, bubbles: true, cancelable: true }));
  check("with nothing unsent, Ctrl+Z asks the desk to undo his sent edit, and says which", /asked the desk to undo e\d+/.test(said()), said().slice(0, 200));
  await until(() => painted() !== before);
  check("the world's undo took the sent Q away", !painted().includes("€Q") && painted() === mine(), painted());
  await until(() => /undid e\d+, your last sent edit, through the desk/.test(said()));
  check("and its answer stays said (which undo it was)", /undid e\d+, your last sent edit, through the desk/.test(said()), said().slice(0, 200));

  // 6b. a change the browser makes with no beforeinput (execCommand: the painter's own key queue) is read back
  await until(() => painted() === mine());
  caret(mine().length); document.execCommand("insertText", false, "+");
  check("words written with no beforeinput are read back into the source, not lost", mine().endsWith("+"), mine().slice(-20));
  md().dispatchEvent(new KeyboardEvent("keydown", { key: "z", ctrlKey: true, bubbles: true, cancelable: true }));

  // 7. each drawn line carries its anchor id for the control screen
  const ids = [...md().children].map(c => c.id);
  check("lines are named part:<key>::<line>", ids.length > 1 && ids.every(i => i.startsWith("part:" + part().dataset.key + "::")), ids.slice(0, 3));
  const sel0 = mine().indexOf("plan"); caret(sel0, sel0 + 4);
  const an = part()._te.anchor();
  const textRead = part()._n.fence.reads.find(e => (e[2] || []).includes("text"))[0];      // the document's words: its subject
  check("a selection's anchor: document, version, words, words either side", an.item === textRead && an.quote === "plan" && /The$/.test(an.before) && /^is/.test(an.after) && an.version && an.version.rev, an);

  // 8. two windows of one person on one document: their own carets and unsent words; both edits stand
  const fr = document.createElement("iframe"); fr.name = "second-window"; fr.style.cssText = "width:700px;height:500px";
  fr.src = location.href; document.body.append(fr);
  await until(() => fr.contentDocument && fr.contentDocument.querySelector(".md-part") && fr.contentDocument.querySelector(".md-part")._te, 12000);
  const d2 = fr.contentDocument;
  caret(0, 0, d2); write("B: ", d2);
  caret(mine().length); write(" End.");
  await until(() => painted().startsWith("B: ") && painted().endsWith(" End.") && painted(d2) === painted(), 9000);
  const st2 = part(d2)._te.doc;
  check("both windows' edits stand in the world", painted().startsWith("B: ") && painted().endsWith(" End."),
    [painted(), { held: st2.held, inflight: !!st2.inflight, version: st2.version, conflict: !!st2.conflict, dirty: st2.dirty, said: (d2.getElementById("said").textContent || "").slice(0, 300) }]);
  check("and both windows show it", mine() === painted() && mine(d2) === painted(), [mine(), mine(d2)]);
  const slots = Object.keys(localStorage).filter(k => k.startsWith(`lens-drafts:${session}:`) && k.includes(":w:"));
  check("each window keeps its state in its own slot of the viewer's store", slots.length >= 2 || new Set([document, d2].map(d => d.defaultView.sessionStorage.getItem("lens-window:" + (d.defaultView.name || "")))).size === 2, slots);
  check("each window's caret is its own (one at the start, one at the end)", part(d2)._te.doc.sel[0] <= 3 && part()._te.doc.sel[0] === mine().length, [part(d2)._te.doc.sel, part()._te.doc.sel]);
  fr.remove();

  // 9. the chat composer: Codex's draft rules, through the module's keys
  const box = document.querySelector(".explicit-composer textarea");
  if (box) {
    box.focus(); write("Hello JEFF"); await sleep(50);
    const k = box.closest("[data-key]").dataset.key;
    const draft = () => { try { const d = (JSON.parse(localStorage.getItem(`lens-drafts:${session}:${q.get("as")}:${q.get("lens")}`)) || []).find(e => e[0] === k); return d ? d[1].text : null; } catch (e) { return null; } };
    check("the composer's words are a kept draft (with what they were typed on)", draft() === "Hello JEFF", draft());
    box.dispatchEvent(new KeyboardEvent("keydown", { key: "z", ctrlKey: true, bubbles: true, cancelable: true }));
    check("Ctrl+Z in the composer is the module's undo, and the draft follows it", box.value === "" && !draft(), [box.value, draft()]);
    const ag = new KeyboardEvent("keydown", { key: "@", ctrlKey: true, altKey: true, bubbles: true, cancelable: true });
    box.dispatchEvent(ag);
    check("AltGr in the composer is not a shortcut", !ag.defaultPrevented);
    write("Sent through the composer");
    box.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true, cancelable: true }));
    await until(() => box.value === "");
    const chat = await desk("worker-a6067", "find title:te-chat");
    check("Enter sends; the box empties and keeps no draft", box.value === "" && !draft(), [box.value, draft()]);
    const cid = (/(a\d+) chat/.exec(chat.text || "") || [])[1], read = cid ? await desk("worker-a6067", `read ${cid}`) : {};
    check("the line is in the chat", /Sent through the composer/.test(read.text || ""), (read.text || chat.text || "").slice(0, 300));
    write("half a thought"); box.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", isComposing: true, bubbles: true, cancelable: true }));
    check("Enter while composing does not send", box.value === "half a thought");
    // 10. (Jeff c6229, Codex c6224) words typed while a send is on its way are never lost: the answer is slowed so the
    // typing lands while the send is out, then the answer is a success, then (again) a refusal
    box.value = ""; box.dispatchEvent(new Event("input", { bubbles: true }));
    const real = window.fetch; let refuse = false;
    window.fetch = async (u, o) => {
      if (String(u).includes("/api/do")) { await sleep(900); if (refuse) { refuse = false; return new Response(JSON.stringify({ text: null, error: "refused: test refusal (nothing was done)" })); } }
      return real(u, o);
    };
    try {
      box.focus(); write("Message one");
      box.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true, cancelable: true }));
      await sleep(200); box.focus(); box.setSelectionRange(box.value.length, box.value.length); write(" and more");
      await sleep(2500);
      check("composer, success: words typed while the send was out stay in the box and the draft", box.value.endsWith(" and more") && (draft() || "").endsWith(" and more"), [box.value, draft()]);
      box.value = ""; box.dispatchEvent(new Event("input", { bubbles: true })); await sleep(50);
      refuse = true; box.focus(); write("Second try");
      box.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true, cancelable: true }));
      await sleep(200); box.focus(); box.setSelectionRange(box.value.length, box.value.length); write(" plus");
      await sleep(2500);
      check("composer, refusal: words typed while the send was out stay", box.value === "Second try plus" && draft() === "Second try plus", [box.value, draft()]);
      // the document: a pause sends; more words land while it is out; the answer keeps them, and they go next
      await until(() => painted() === mine());
      caret(mine().length); write(" Alpha.");
      await sleep(900);                                          // the pause's send is now out (slowed)
      caret(mine().length); write(" Beta.");
      await until(() => painted().endsWith(" Alpha. Beta."), 9000);
      check("document: words typed while a send was out are kept and sent next", mine().endsWith(" Alpha. Beta.") && painted().endsWith(" Alpha. Beta."), [mine().slice(-30), painted().slice(-30)]);
      refuse = true; caret(mine().length); write(" Gamma.");
      await sleep(900); caret(mine().length); write(" Delta.");
      await sleep(2500);
      check("document, refusal: words typed while the refused send was out are still there", mine().endsWith(" Gamma. Delta."), mine().slice(-30));
    } finally { window.fetch = real; }
  } else check("the probe has a composer", false);

  const passed = out.filter(l => l.startsWith("ok")).length;
  return out.filter(l => !l.startsWith("ok")).concat([fails ? `${passed} passed, ${fails} FAILED` : `all ${passed} passed`]).join("\n");
})()
