// a6109: press a part, as a click: window.PRESS (set in a js step before this) is the end of its key, or text:<words>
// for the innermost part whose words are exactly those (pressed on its nearest part that has a click). -> its key
(() => {
  const want = window.PRESS, all = [...document.querySelectorAll("[data-key]")].filter(e => e.getClientRects().length);
  let el = want.startsWith("text:") ? all.filter(e => e.textContent.trim() === want.slice(5)).pop()
    : want.startsWith("rx:") ? all.find(e => new RegExp(want.slice(3)).test(e.dataset.key))
    : all.find(e => e.dataset.key.endsWith(want));
  if (!el) return "none: " + want;
  el.click();
  return el.dataset.key;
})()
