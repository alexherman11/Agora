// apps/third.js : the application of the studio's own choosing. OWNER: Lark (leads the choice; decide together in Studio talk).
// Until it exists, this stub is the Outline: the whole desk exactly as a text-only inhabitant reads it, live.
(() => {
  const draw = host => { host.innerHTML = ""; const pre = document.createElement("pre");
    pre.style.cssText = "margin:0;padding:16px;font:12px/1.6 ui-monospace,Consolas,monospace;white-space:pre-wrap";
    pre.textContent = Desk.snapshot.outline; host.appendChild(pre); };
  Desk.registerApp({ id: "third", title: "Outline", glyph: "≡", open: draw, refresh: draw, text: () => Desk.snapshot.outline });
})();
