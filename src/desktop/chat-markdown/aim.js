(() => {
  // a6452: bring the every-construct message's open task box into view and say where it and the names film's play button are
  const docs = [...document.querySelectorAll('.md-part')];
  const rel = docs.find(e => e.textContent.includes('Release notes'));
  const box = rel.querySelector('.md-task:not(.md-done) .md-check');
  box.scrollIntoView({ block: 'center' });
  const c = e => { const r = e.getBoundingClientRect(); return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)]; };
  return { box: c(box) };
})()
