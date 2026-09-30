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
    const s = document.createElement("span"); if (role) s.className = R(role);
    s.textContent = text.endsWith("\n") ? text : text + "\n"; out.appendChild(s);
    while (out.childNodes.length > 600) out.removeChild(out.firstChild);
    out.scrollTop = out.scrollHeight;
  }
  write(`desk terminal · ${who} in ${session} · help for the manual, clear to clear`, "term.echo");

  form.addEventListener("submit", async e => {
    e.preventDefault();
    const line = input.value.trim(); if (!line) return;
    input.value = ""; draft = "";
    if (hist[hist.length - 1] !== line) hist.push(line);
    hist = hist.slice(-200); at = hist.length;
    try { localStorage.setItem(key, JSON.stringify(hist)); } catch (e2) { /* view state only */ }
    if (line === "clear") { out.replaceChildren(); return; }
    write(`${who}> ${line}`, "term.echo");
    input.disabled = true;
    try {
      const r = await (await fetch("/api/do", { method: "POST", body: JSON.stringify({ session, as: who, line }) })).json();
      const t = r.text || r.error || "(no answer)";
      write(t.replace(/^> .*\n/, ""), r.error || /^ERR/m.test(t) ? "term.err" : null);
    } catch (e3) {
      write(`the answer was lost (${e3.message}); whether it was done is unknown until the view repaints`, "term.err");
    } finally { input.disabled = false; input.focus(); }
  });
  input.addEventListener("keydown", e => {
    if (e.key === "ArrowUp" && at > 0) { if (at === hist.length) draft = input.value; input.value = hist[--at]; e.preventDefault(); }
    else if (e.key === "ArrowDown" && at < hist.length) { at++; input.value = at === hist.length ? draft : hist[at]; e.preventDefault(); }
    else if (e.key === "l" && e.ctrlKey) { out.replaceChildren(); e.preventDefault(); }
  });
  box.addEventListener("mouseup", () => { if (!getSelection().toString()) input.focus(); });
})();
