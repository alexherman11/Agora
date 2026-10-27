/* theme-live.js: a host page wears the theme and changes with it, without a reload.
 *
 * Every page links theme.css (the --ag-* variables; first paint) and loads this. It asks theme.json which theme this
 * viewer wears, and again whenever the kernel says `theme.changed` (or an `undo`), when the page comes back to the front,
 * when a theme being tried runs out, and every 15 s as a backstop. A new theme's CSS replaces the old in one <style>, so
 * the whole page repaints at once. Pages and widgets listen for the `ag-theme` event on window (detail: the theme).
 * One vocabulary: research/kernel-lab/theme/THEMES.md.
 */
(() => {
  "use strict";
  const here = new URL(document.currentScript.src, location.href);
  const base = here.pathname.slice(0, here.pathname.lastIndexOf("/") + 1);
  const state = { hash: null, theme: null };
  let sheet = null, timer = null, expiry = null, inflight = false, again = false;

  function apply(t) {
    if (!sheet) { sheet = document.createElement("style"); sheet.id = "ag-theme-live"; document.head.append(sheet); }
    if (sheet.textContent !== t.css) sheet.textContent = t.css;
    document.documentElement.dataset.agVariant = t.variant;
    state.hash = t.hash; state.theme = t;
    window.dispatchEvent(new CustomEvent("ag-theme", { detail: t }));
    clearTimeout(expiry);
    if (t.until) expiry = setTimeout(refresh, Math.max(250, new Date(t.until) - Date.now() + 350));
  }

  async function refresh() {
    if (inflight) { again = true; return; }
    inflight = true;
    try {
      const r = await fetch(base + "theme.json", { credentials: "same-origin", cache: "no-cache" });
      if (r.ok) { const t = await r.json(); if (t.hash !== state.hash) apply(t); }
    } catch (e) { /* the kernel is away; the next change or poll tries again */ }
    inflight = false;
    if (again) { again = false; refresh(); }
  }

  const heard = (h) => { if (h && (h.word === "theme.changed" || h.word === "undo")) { clearTimeout(timer); timer = setTimeout(refresh, 60); } };
  if (typeof KD !== "undefined" && KD.stream) KD.stream(heard);
  else try { const es = new EventSource("/door/stream"); es.addEventListener("happen", (ev) => { try { heard(JSON.parse(ev.data)); } catch (e) { /* */ } }); } catch (e) { /* */ }
  document.addEventListener("visibilitychange", () => { if (!document.hidden) refresh(); });
  setInterval(refresh, 15000);
  window.AgoraTheme = { get state() { return state; }, refresh };
  refresh();
})();
