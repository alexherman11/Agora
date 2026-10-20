// Highlight a phrase in the painted page as a person's drag would leave it, then let go (pointerup): lens.js sends the
// nearest `on select`. Headless drags over a contenteditable Markdown text left no selection (a6638), so the range is
// set directly. The phrase is window.PHRASE, else the default below.
(() => {
  const phrase = window.PHRASE || "Builders keep real tools, and reach both the code and the things in the world";
  const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = walk.nextNode())) {
    const i = n.textContent.indexOf(phrase);
    if (i < 0) continue;
    const r = document.createRange();
    r.setStart(n, i);
    r.setEnd(n, i + phrase.length);
    const s = getSelection();
    s.removeAllRanges();
    s.addRange(r);
    const box = r.getBoundingClientRect();
    document.dispatchEvent(new PointerEvent("pointerup", { bubbles: true, clientX: box.right, clientY: box.bottom }));
    return "selected: " + String(s);
  }
  return "phrase not found";
})()
