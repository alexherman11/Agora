// a6109: press the first person's name drawn on the page; -> [its words, what it opens, its hover] or "none"
(() => {
  const a = [...document.querySelectorAll(".t-mark-thing[data-kind=person]")].find(x => x.getClientRects().length);
  if (!a) return "none";
  a.click();
  return [a.textContent, a.dataset.thing, a.title, document.querySelectorAll(".t-mark-thing[data-kind=person]").length];
})()
