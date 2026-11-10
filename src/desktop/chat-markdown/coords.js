(() => {
  // a6452: where the parts the walk presses are, in CSS pixels, in the HUD's chat (jeff-chat inside home-base)
  const c = r => r ? [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] : null;
  const docs = [...document.querySelectorAll('.md-part')].filter(e => e.closest('[data-key*="said"]') || e.dataset.key.includes('body'));
  const plain = docs.find(e => e.textContent.includes('Plain words still read'));
  const said = plain && plain.closest('[data-key$="/said"], [data-key*="said"]');
  const thing = plain && plain.querySelector('.md-thing');
  const answer = said && [...said.parentElement.querySelectorAll('[data-key]')].find(e => e.textContent.trim() === 'Answer' && e.getClientRects().length && said.contains(e));
  const ta = document.querySelector('.explicit-composer textarea');
  return { plain: plain && plain.dataset.key, thing: c(thing && thing.getBoundingClientRect()), answer: c(answer && answer.getBoundingClientRect()),
    answerKey: answer && answer.dataset.key, composer: c(ta && ta.getBoundingClientRect()), docs: docs.length };
})()
