// term.js : a desk terminal beside any painted lens. OWNER: Claude (command center, 28 Sep; see OWNERS.md).
// ?side=term puts it where the inspector would be. Every line is a desk command sent as the viewer through /api/do,
// exactly what `explore.py <session> --as <who>` would do; the painter repaints from the world on its own. The
// scrollback and the command history are view state (this page, this browser), never the world's.
(() => {
  const q = new URLSearchParams(location.search);
  if (q.get("side") !== "term") return;
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
