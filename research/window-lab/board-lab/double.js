// double.js (a6010): a double press on a needs-you card's Looks good, 40 ms apart at one point, as a quick double-click
// would land: what did the second press hit? With `leaves` drawn as visibility:hidden the card keeps its room, so the
// second press must not land on the next card's answer (it did, in a draft that took the card out of the layout).
(async () => {
  const at = (x, y) => document.elementFromPoint(x, y);
  const b = [...document.querySelectorAll("[data-key]")].find(e => /\/reviews\/a\d+\/line\/ok$/.test(e.dataset.key) && e.getClientRects().length);
  if (!b) return "no Looks good on the page";
  const r = b.getBoundingClientRect(), x = r.left + r.width / 2, y = r.top + r.height / 2;
  at(x, y).click();
  await new Promise(res => setTimeout(res, 40));
  const s = at(x, y), k = s && s.closest("[data-key]");
  if (s) s.click();
  return { first: b.dataset.key, second: k ? k.dataset.key : "nothing" };
})()
