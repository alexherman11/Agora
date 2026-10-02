// term.js : a desk terminal beside any painted lens. OWNER: Claude (command center, 28 Sep; see OWNERS.md).
// The right-hand pane is this terminal by default (Alex, 28 Sep); ?side=scene shows the scene's text there instead, and
// ?inspect=0 gives the painter the full width. Every line is a desk command sent as the viewer through /api/do,
// exactly what `explore.py <session> --as <who>` would do; the painter repaints from the world on its own. The
// scrollback and the command history are view state (this page, this browser), never the world's.
(() => {
  const q = new URLSearchParams(location.search);
  if (q.get("inspect") === "0" || q.get("side") === "scene") return;
  const session = q.get("session") || "lens", who = q.get("as") || "alex";
  document.body.dataset.inspector = "term";
  const R = n => (window.Style ? Style.roleClass(n) : "r-" + n);
  const box = document.createElement("section"); box.id = "term"; box.className = R("term");
  const out = document.createElement("pre"); out.className = "term-out";
  const form = document.createElement("form"); form.className = "term-line";
  const prompt = document.createElement("span"); prompt.textContent = who + "> "; prompt.className = R("term.prompt");
  const input = document.createElement("input");
  Object.assign(input, { autocomplete: "off", spellcheck: false, ariaLabel: "desk command" });
  form.append(prompt, input); box.append(out, form);
  document.body.appendChild(box);

  // Alex, 29 Sep: a way to close the terminal. × closes it and the painter takes the full width; "▸ terminal" (or
  // Ctrl+`) opens it again. Open or closed is this browser's choice for this world, never the world's.
  const openKey = `desk-term-open:${session}:${who}`;
  const head = document.createElement("div"); head.className = "term-head";
  const shut = document.createElement("button"); Object.assign(shut, { type: "button", textContent: "×", title: "close the terminal (Ctrl+`)" });
  shut.className = R("tool"); shut.setAttribute("aria-label", "close the terminal");
  head.append(shut); box.prepend(head);
  const reopen = document.createElement("button"); Object.assign(reopen, { type: "button", id: "term-open", textContent: "▸ terminal", title: "open the terminal (Ctrl+`)" });
  reopen.className = R("tool"); document.body.appendChild(reopen);
  function show(on, focus) {
    document.body.dataset.inspector = on ? "term" : "off"; reopen.hidden = on;
    try { localStorage.setItem(openKey, on ? "1" : "0"); } catch (e) { /* view state only */ }
    if (on && focus) input.focus();
  }
  shut.addEventListener("click", () => show(false));
  reopen.addEventListener("click", () => show(true, true));
  document.addEventListener("keydown", e => { if (e.key === "`" && e.ctrlKey) { show(document.body.dataset.inspector !== "term", true); e.preventDefault(); } });
  let startOpen = true; try { startOpen = localStorage.getItem(openKey) !== "0"; } catch (e) { startOpen = true; }
  show(startOpen, false);

  const key = `desk-term:${session}:${who}`;
  let hist = []; try { hist = JSON.parse(localStorage.getItem(key) || "[]"); } catch (e) { hist = []; }
  let at = hist.length, draft = "";
  function write(text, role) {
    const s = document.createElement("span"); if (role) { s.className = R(role); s.dataset.role = role; }
    s.textContent = text.endsWith("\n") ? text : text + "\n"; out.appendChild(s);
    while (out.childNodes.length > 600) out.removeChild(out.firstChild);
    out.scrollTop = out.scrollHeight;
  }
  // a1505: the scrollback outlives a reload of this tab (for new painter code); view state, this tab only
  const backKey = `desk-term-back:${session}:${who}`;
  let back = []; try { back = JSON.parse(sessionStorage.getItem(backKey) || "[]"); } catch (e) { back = []; }
  addEventListener("pagehide", () => {
    try { sessionStorage.setItem(backKey, JSON.stringify([...out.childNodes].slice(-300).map(s => [s.textContent, s.dataset.role || ""]))); } catch (e) { /* view state only */ }
  });
  if (back.length) back.forEach(([t, r]) => write(t, r || null));
  else write(`desk terminal · ${who} in ${session} · help for the manual, clear to clear`, "term.echo");

  // a1047: one intent, one event (a1008 gave the painter this). Enter on new words mints a gesture id. If the answer is
  // lost, the words go back into the line holding that id, kept over a reload: Enter on them, untouched, sends the
  // same press again, and deskd says "already done, as eN" if the first got through. Typing in the line or walking
  // the history lets go of the id, so the same words sent again on purpose are a new press and a new line.
  const heldKey = `desk-term-held:${session}:${who}`;
  let held = null; try { held = JSON.parse(localStorage.getItem(heldKey) || "null"); } catch (e) { held = null; }
  const hold = h => { held = h; try { h ? localStorage.setItem(heldKey, JSON.stringify(h)) : localStorage.removeItem(heldKey); } catch (e) { /* view state only */ } };
  if (held && held.line) { input.value = held.line; write(`"${held.line}" was sent and its answer was lost; Enter sends it again as the same press`, "term.err"); }
  input.addEventListener("input", () => { if (held) hold(null); });

  form.addEventListener("submit", async e => {
    e.preventDefault();
    const line = input.value.trim(); if (!line) return;
    const gesture = held && held.line === line ? held.id : `${who}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
    input.value = ""; draft = "";
    if (hist[hist.length - 1] !== line) hist.push(line);
    hist = hist.slice(-200); at = hist.length;
    try { localStorage.setItem(key, JSON.stringify(hist)); } catch (e2) { /* view state only */ }
    if (line === "clear") { out.replaceChildren(); return; }
    write(`${who}> ${line}`, "term.echo");
    input.disabled = true;
    let res = null;
    try { res = await fetch("/api/do", { method: "POST", body: JSON.stringify({ session, as: who, line, gesture }) }); }
    catch (e3) {
      hold({ line, id: gesture }); input.value = line;
      write(`the answer was lost (${e3.message}); whether it was done is unknown. The line is back below: Enter sends it again as the same press, and the desk says if it was already done`, "term.err");
    }
    if (res) {
      hold(null);                         // an answer came back: this press is finished, whatever it said
      let r; try { r = await res.json(); } catch (e4) { r = { error: `deskd answered ${res.status} without words` }; }
      const t = r.text || r.error || "(no answer)";
      write(t.replace(/^> .*\n/, ""), r.error || /^ERR/m.test(t) ? "term.err" : null);
      // a1505 (vii, Sable a1201): while two deskds overlap behind the door, a receipt from the code being replaced says so
      const now = window.DoorLine && DoorLine.status && DoorLine.status.code;
      if (r.code && now && r.code !== now) write(`(answered by ${r.code}, the code before the update to ${now})`, "meta");
    }
    input.disabled = false; input.focus();
  });
  input.addEventListener("keydown", e => {
    if ((e.key === "ArrowUp" || e.key === "ArrowDown") && held) hold(null);
    if (e.key === "ArrowUp" && at > 0) { if (at === hist.length) draft = input.value; input.value = hist[--at]; e.preventDefault(); }
    else if (e.key === "ArrowDown" && at < hist.length) { at++; input.value = at === hist.length ? draft : hist[at]; e.preventDefault(); }
    else if (e.key === "l" && e.ctrlKey) { out.replaceChildren(); e.preventDefault(); }
  });
  box.addEventListener("mouseup", () => { if (!getSelection().toString()) input.focus(); });
})();
