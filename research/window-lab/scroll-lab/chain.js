// chain.js (a6549): from the painted part whose words begin with window.__needle, walk up to the page and say, per
// ancestor, its key, overflow-y, its height and its content's height, and min-height / flex: which one cuts.
(() => {
  const needle = window.__needle || "Juniper, 29 Sep";
  const all = [...document.querySelectorAll("[data-key]")].filter(e => e.getClientRects().length && (e.textContent || "").trim().startsWith(needle));
  let el = all[all.length - 1];
  if (!el) return "no part begins with " + needle;
  const out = [];
  while (el && el !== document.documentElement) {
    const cs = getComputedStyle(el);
    out.push([el.dataset.key || el.tagName, cs.overflowY, el.clientHeight, el.scrollHeight, cs.minHeight, cs.flex, cs.display].join(" | "));
    el = el.parentElement;
  }
  return out;
})()
