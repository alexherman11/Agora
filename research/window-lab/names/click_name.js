// a6109: press the drawn name of window.NAME (an id), as a click on it; -> its words, or "none"
(() => {
  const a = [...document.querySelectorAll(".t-mark-thing, .md-thing")].find(x => (x.dataset.id || x.dataset.target) === window.NAME && x.getClientRects().length);
  if (!a) return "none: " + window.NAME;
  a.scrollIntoView({ block: "center" });
  a.click();
  return a.innerText;
})()
